"""Offline software checks, not agent benchmark performance measurements."""
import copy
import json
import socket
import subprocess

import pytest

from experiments.arc_bench.evidence_comparison import (
    SYSTEMS, REPOS, artifact_ref, digest, dry_run, main, make_plan, summarize, validate_plan,
)


@pytest.fixture
def setup_plan(tmp_path):
    domain = tmp_path / "experiments/arc_bench/config/ml"
    (domain / "manifests").mkdir(parents=True)
    (domain / "rubrics").mkdir()
    (domain / "manifests/ML01.yaml").write_text("id: ML01\n", encoding="utf-8")
    (domain / "rubrics/ML01.json").write_text('{"synthetic_fixture": true}', encoding="utf-8")
    systems = {name: {"repository": REPOS[name], "commit": "a" * 40, "patch_sha256": None} for name in SYSTEMS}
    systems["rancho_upgraded"]["patch_sha256"] = "b" * 64
    plan = make_plan(systems, {"provider": "test-no-api", "model_id": "fixture", "settings": {"temperature": 0}},
                     {"wall_time_sec": 10, "max_api_calls": 2, "max_output_tokens": 100, "max_cost_usd": 1,
                      "max_gpu_seconds": 0, "max_memory_mb": 512}, ["ML01"], [0], root=tmp_path)
    return tmp_path, plan


def measured_records(root, plan):
    audit = root / "audit.json"
    audit.write_text('{"synthetic_fixture": true, "not_real_benchmark": true}', encoding="utf-8")
    records = dry_run(plan, root=root)
    for record in records:
        record.update(status="COMPLETED", actual_model=plan["model"], audit_refs=[artifact_ref(audit, root)])
        obs = record["observations"]
        for name in obs:
            obs[name] = 0
        obs.update(valid_task_completed=True, evidence_complete=True, reproduced_independently=True,
                   cost_usd=0.1, wall_time_sec=1, audited_promotions=1, audited_unresolved_claims=1,
                   invalid_results=1, invalid_detected=1, valid_negative_results=1, negative_preserved=1)
    return records


def refreeze(plan):
    plan["plan_sha256"] = digest({k: v for k, v in plan.items() if k != "plan_sha256"})


def test_three_versions_and_frozen_inputs(setup_plan):
    root, plan = setup_plan
    validate_plan(plan, root=root)
    assert set(plan["systems"]) == set(SYSTEMS)
    plan["budget"]["wall_time_sec"] = 11
    with pytest.raises(ValueError, match="未冻结"):
        validate_plan(plan, root=root)


def test_actual_artifact_hash_checked(setup_plan):
    root, plan = setup_plan
    (root / plan["tasks"][0]["manifest"]["path"]).write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="哈希不符"):
        validate_plan(plan, root=root)


@pytest.mark.parametrize("mutation", ["missing_system", "same_version", "wrong_repo", "short_sha", "bad_budget", "gpu", "unknown_schema"])
def test_rejects_unfixed_or_wrong_identity_schema_budget(setup_plan, mutation):
    root, plan = setup_plan
    if mutation == "missing_system":
        plan["systems"].pop("autoresearchclaw")
    elif mutation == "same_version":
        plan["systems"]["rancho_upgraded"] = copy.deepcopy(plan["systems"]["rancho_baseline"])
    elif mutation == "wrong_repo":
        plan["systems"]["autoresearchclaw"]["repository"] = REPOS["rancho_baseline"]
    elif mutation == "short_sha":
        plan["systems"]["autoresearchclaw"]["commit"] = "abcdef"
    elif mutation == "bad_budget":
        plan["budget"]["max_api_calls"] = -1
    elif mutation == "gpu":
        plan["budget"]["max_gpu_seconds"] = 3
    else:
        plan["schema_version"] = 2
    refreeze(plan)
    with pytest.raises(ValueError):
        validate_plan(plan, root=root)


def test_dryrun_cli_never_launches_or_calls_network(setup_plan, monkeypatch):
    root, plan = setup_plan
    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run must not start external work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    source = root / "plan.json"
    source.write_text(json.dumps(plan), encoding="utf-8")
    output = root / "not-run.json"
    assert main(["--root", str(root), "dry-run", "--plan", str(source), "--output", str(output)]) == 0
    records = json.loads(output.read_text(encoding="utf-8"))
    assert len(records) == 3
    assert all(r["status"] == "NOT_RUN" and all(v is None for v in r["observations"].values()) for r in records)
    report = summarize(plan, records, root=root)
    assert report["comparison_status"] == "NOT_RUN"
    assert all(s["metrics"]["completion_rate"]["value"] is None for s in report["systems"].values())
    # Existing frozen records may not be silently overwritten.
    assert main(["--root", str(root), "dry-run", "--plan", str(source), "--output", str(output)]) == 2


def test_complete_fixture_is_descriptive_only(setup_plan):
    root, plan = setup_plan
    report = summarize(plan, measured_records(root, plan), root=root)
    assert report["comparison_status"] == "DESCRIPTIVE_ONLY"
    assert not report["incomparable_reasons"]
    assert report["systems"]["rancho_upgraded"]["metrics"]["completion_rate"] == {
        "state": "MEASURED", "numerator": 1, "denominator": 1, "unknown_runs": 0, "value": 1.0}


def test_missing_metrics_remain_unknown_not_zero(setup_plan):
    root, plan = setup_plan
    records = measured_records(root, plan)
    obs = records[0]["observations"]
    obs.update(cost_usd=None, false_promotions=None)
    report = summarize(plan, records, root=root)
    metrics = report["systems"]["autoresearchclaw"]["metrics"]
    assert metrics["mean_cost_usd"]["value"] is None
    assert metrics["mean_cost_usd"]["observed_n"] == 0
    assert metrics["false_promotion_rate"]["state"] == "UNKNOWN"
    assert report["comparison_status"] == "INCOMPARABLE"


def test_resource_failure_stays_in_completion_and_cost_denominator(setup_plan):
    root, plan = setup_plan
    plan["seeds"] = [0, 1]
    refreeze(plan)
    records = measured_records(root, plan)
    records[1]["status"] = "BLOCKED"
    records[1]["observations"].update(valid_task_completed=None, evidence_complete=None, reproduced_independently=None, cost_usd=0.3)
    report = summarize(plan, records, root=root)
    metrics = report["systems"]["autoresearchclaw"]["metrics"]
    assert metrics["completion_rate"]["numerator"] == 1
    assert metrics["completion_rate"]["denominator"] == 2
    assert metrics["completion_rate"]["value"] == 0.5
    assert metrics["mean_cost_usd"]["value"] == 0.2


def test_missing_run_not_dropped_from_planned_n(setup_plan):
    root, plan = setup_plan
    records = measured_records(root, plan)
    report = summarize(plan, records[1:], root=root)
    group = report["systems"]["autoresearchclaw"]
    assert group["planned_n"] == 1 and group["recorded_n"] == 0
    assert group["metrics"]["completion_rate"]["value"] is None
    assert report["comparison_status"] == "INCOMPARABLE"


@pytest.mark.parametrize("mutation", ["duplicate", "nan", "wrong_model", "exceed_budget", "forged_identity", "audit_changed"])
def test_bad_records_fail_closed_or_mark_incomparable(setup_plan, mutation):
    root, plan = setup_plan
    records = measured_records(root, plan)
    if mutation == "duplicate":
        records.append(copy.deepcopy(records[0]))
    elif mutation == "nan":
        records[0]["observations"]["cost_usd"] = float("nan")
    elif mutation == "wrong_model":
        records[0]["actual_model"] = {"model_id": "other"}
    elif mutation == "exceed_budget":
        records[0]["observations"]["api_calls"] = 99
    elif mutation == "forged_identity":
        records[0]["system_sha256"] = "c" * 64
    else:
        (root / "audit.json").write_text("tampered", encoding="utf-8")
    if mutation in {"wrong_model", "exceed_budget"}:
        assert summarize(plan, records, root=root)["comparison_status"] == "INCOMPARABLE"
    else:
        with pytest.raises(ValueError):
            summarize(plan, records, root=root)


def test_no_relevant_negative_examples_is_not_applicable(setup_plan):
    root, plan = setup_plan
    records = measured_records(root, plan)
    for r in records:
        r["observations"].update(valid_negative_results=0, negative_preserved=0)
    rate = summarize(plan, records, root=root)["systems"]["autoresearchclaw"]["metrics"]["negative_retention_rate"]
    assert rate["state"] == "NOT_APPLICABLE" and rate["value"] is None
