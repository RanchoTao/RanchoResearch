"""Adversarial gate regressions, including real bounded subprocess execution.

These are software reliability tests; they do not measure research-agent quality.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from autoresearch_state.evidence import claim_path, freeze_claim
from researchclaw.adapters import AdapterBundle
from researchclaw.cli import main
from researchclaw.pipeline import executor
from researchclaw.pipeline.evidence_gate import evaluate, preflight, read_json, local_path
from researchclaw.pipeline.stages import Stage, StageStatus
from scripts.evidence_smoke import prepare_run, ref, run_prepared, write_json


def real_case(root, case="positive"):
    config = prepare_run(root, case)
    result = run_prepared(root, config)
    return config, result


@pytest.mark.parametrize("case,validity,science,allowed", [
    ("positive", "VALID", "SUPPORTED", True),
    ("negative", "VALID", "CONTRADICTED_IN_SCOPE", True),
    ("nan", "INVALID", "NOT_TESTED", False),
    ("misaligned", "INVALID", "NOT_TESTED", False),
    ("resource_error", "UNKNOWN", "NOT_TESTED", False),
    ("small_sample", "UNKNOWN", "NOT_TESTED", False),
    ("calibration", "VALID", "NOT_TESTED", False),
    ("no_baseline", "UNKNOWN", "NOT_TESTED", False),
])
def test_required_cases_real_cpu(tmp_path, case, validity, science, allowed):
    _, result = real_case(tmp_path, case)
    report = result["evidence"]
    assert report["axes"]["measurement_validity"] == validity
    assert report["axes"]["scientific_claim"] == science
    assert report["promotion_allowed"] is allowed
    if science != "CONTRADICTED_IN_SCOPE":
        assert report["decision"] != "KILL"
    if case != "no_baseline":
        assert list((tmp_path / "evidence" / "receipts").glob("*.json"))
        assert (tmp_path / "stage-12" / "runs").is_dir()


def test_pretty_report_without_execution_and_autoapprove_cannot_pass(tmp_path, monkeypatch):
    config = prepare_run(tmp_path)
    write_json(tmp_path / "stage-14" / "experiment_summary.json", {"best_run": {"metrics": {"accuracy": 0.99}}})
    (tmp_path / "analysis.md").write_text("漂亮报告：成功", encoding="utf-8")
    monkeypatch.setattr(executor, "_run_hitl_pre_stage", lambda *a, **k: pytest.fail("must block before HITL skip"))
    for stage in (Stage.RESEARCH_DECISION, Stage.PAPER_DRAFT, Stage.EXPORT_PUBLISH):
        result = executor.execute_stage(stage, run_dir=tmp_path, run_id="missing", config=config,
                                        adapters=AdapterBundle(), auto_approve_gates=True)
        assert result.status == StageStatus.PAUSED
    assert evaluate(tmp_path).axes["scientific_claim"] == "NOT_TESTED"


def test_permissions_before_any_execution(tmp_path, monkeypatch):
    config = prepare_run(tmp_path)
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["authorization"]["max_time_budget_sec"] = 1
    write_json(tmp_path / "research_evidence.json", bundle)
    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.EXPERIMENT_RUN,
                        lambda *a, **kw: pytest.fail("unauthorized executor called"))
    result = executor.execute_stage(Stage.EXPERIMENT_RUN, run_dir=tmp_path, run_id="denied", config=config, adapters=AdapterBundle())
    assert result.status == StageStatus.PAUSED
    assert not list((tmp_path / "evidence" / "receipts").glob("*.json"))


def test_hitl_skip_is_not_execution(tmp_path, monkeypatch):
    config = prepare_run(tmp_path)
    monkeypatch.setattr(executor, "_run_hitl_pre_stage", lambda *a, **kw:
                        executor.StageResult(stage=Stage.EXPERIMENT_RUN, status=StageStatus.DONE, artifacts=()))
    result = executor.execute_stage(Stage.EXPERIMENT_RUN, run_dir=tmp_path, run_id="skip", config=config, adapters=AdapterBundle())
    assert result.status == StageStatus.PAUSED
    assert not evaluate(tmp_path).promotion_allowed


def test_simulated_mode_cannot_relabel_real_receipt(tmp_path):
    _, _ = real_case(tmp_path)
    bundle = read_json(tmp_path / "research_evidence.json")
    receipt_path = tmp_path / bundle["receipt"]
    receipt = read_json(receipt_path)
    receipt["config"]["mode"] = "simulated"  # adversarial contract fixture
    write_json(receipt_path, receipt)
    report = evaluate(tmp_path)
    assert not report.promotion_allowed and report.decision == "HOLD"


@pytest.mark.parametrize("target", ["protocol.json", "stage-10/experiment/data.json"])
def test_protocol_data_and_output_tampering_holds(tmp_path, target):
    real_case(tmp_path)
    with (tmp_path / target).open("a", encoding="utf-8") as stream:
        stream.write(" ")
    assert not evaluate(tmp_path).promotion_allowed


def test_snapshot_tampering_holds_but_repeat_keeps_original_evidence(tmp_path):
    config, _ = real_case(tmp_path)
    bundle = read_json(tmp_path / "research_evidence.json")
    first_receipt = bundle["receipt"]
    receipt = read_json(tmp_path / first_receipt)
    snapshot = tmp_path / receipt["output_snapshot"]["stage-12/runs/run-1.json"]
    original = snapshot.read_bytes()
    run_prepared(tmp_path, config)
    assert snapshot.read_bytes() == original
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["receipt"] = first_receipt
    write_json(tmp_path / "research_evidence.json", bundle)
    assert evaluate(tmp_path).promotion_allowed
    snapshot.write_bytes(original + b" ")
    assert not evaluate(tmp_path).promotion_allowed


def test_precomputed_input_is_not_experimental_measurement(tmp_path):
    config = prepare_run(tmp_path)
    write_json(tmp_path / "pretty_input.json", {"proposed_score": 99, "baseline_score": 0, "n": 100, "aligned": True, "data_origin": "SYNTHETIC"})
    bundle = read_json(tmp_path / "research_evidence.json")
    protocol = read_json(tmp_path / "protocol.json")
    for spec in [*protocol["metrics"].values(), *protocol["checks"], protocol["sample_count"]]:
        spec["path"] = "pretty_input.json"
    write_json(tmp_path / "protocol.json", protocol)
    bundle["claim"]["protocol"] = ref(tmp_path, "protocol.json")
    bundle["inputs"]["configuration"].append(ref(tmp_path, "pretty_input.json"))
    write_json(tmp_path / "research_evidence.json", bundle)
    report = run_prepared(tmp_path, config)["evidence"]
    assert not report["promotion_allowed"] and report["axes"]["scientific_claim"] == "NOT_TESTED"


def test_preexisting_stage_result_cannot_get_new_receipt(tmp_path):
    config = prepare_run(tmp_path, "negative")
    write_json(tmp_path / "stage-12" / "fake-results.json", {"proposed_score": 0, "baseline_score": -999, "n": 100, "aligned": True, "data_origin": "SYNTHETIC"})
    protocol = read_json(tmp_path / "protocol.json")
    for spec in [*protocol["metrics"].values(), *protocol["checks"], protocol["sample_count"]]:
        spec["path"] = "stage-12/fake-results.json"
    write_json(tmp_path / "protocol.json", protocol)
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["claim"]["protocol"] = ref(tmp_path, "protocol.json")
    write_json(tmp_path / "research_evidence.json", bundle)
    report = run_prepared(tmp_path, config)["evidence"]
    assert not report["promotion_allowed"]
    assert list((tmp_path / "evidence" / "unbound_prior").rglob("fake-results.json"))


def test_input_copied_into_sandbox_is_not_measurement(tmp_path):
    config = prepare_run(tmp_path, "negative")
    name = "stage-10/experiment/copied-metrics.json"
    write_json(tmp_path / name, {"proposed_score": 0, "baseline_score": -100, "n": 100, "aligned": True, "data_origin": "SYNTHETIC"})
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["inputs"]["code"].append(ref(tmp_path, name))
    protocol = read_json(tmp_path / "protocol.json")
    for spec in [*protocol["metrics"].values(), *protocol["checks"], protocol["sample_count"], protocol["origin_source"]]:
        spec["path"] = "stage-12/runs/sandbox/_project_1/copied-metrics.json"
    write_json(tmp_path / "protocol.json", protocol)
    bundle["claim"]["protocol"] = ref(tmp_path, "protocol.json")
    write_json(tmp_path / "research_evidence.json", bundle)
    report = run_prepared(tmp_path, config)["evidence"]
    assert not report["promotion_allowed"] and report["decision"] != "KILL"


@pytest.mark.parametrize("field,value", [("direction", "maxmize"), ("min_samples", 0), ("min_samples", True), ("baseline", "undeclared")])
def test_invalid_protocol_cannot_kill_science(tmp_path, field, value):
    config = prepare_run(tmp_path)
    protocol = read_json(tmp_path / "protocol.json")
    (protocol if field == "min_samples" else protocol["decision_rule"])[field] = value
    write_json(tmp_path / "protocol.json", protocol)
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["claim"]["protocol"] = ref(tmp_path, "protocol.json")
    write_json(tmp_path / "research_evidence.json", bundle)
    report = run_prepared(tmp_path, config)["evidence"]
    assert report["decision"] == "HOLD" and report["axes"]["scientific_claim"] == "NOT_TESTED"


def test_docker_fallback_does_not_expand_authorization(tmp_path):
    config = prepare_run(tmp_path)
    config = replace(config, experiment=replace(config.experiment, mode="docker"))
    with pytest.raises(ValueError, match="回退"):
        preflight(tmp_path, config, 12)


def test_synthetic_data_cannot_be_labeled_real(tmp_path):
    config = prepare_run(tmp_path)
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["inputs"]["data_origin"] = "REAL"
    write_json(tmp_path / "research_evidence.json", bundle)
    report = run_prepared(tmp_path, config)["evidence"]
    assert report["axes"]["measurement_validity"] == "INVALID"
    assert not report["promotion_allowed"] and report["decision"] != "KILL"


@pytest.mark.parametrize("token", ["NaN", "Inf", "Infinity"])
def test_paper_nonfinite_text_is_held(tmp_path, token):
    real_case(tmp_path)
    paper = tmp_path / "paper.md"
    paper.write_text(f"实际结果为 {token}。", encoding="utf-8")
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["papers"] = [{**ref(tmp_path, "paper.md"), "bindings": []}]
    write_json(tmp_path / "research_evidence.json", bundle)
    report = evaluate(tmp_path, papers=["paper.md"])
    assert not report.paper_allowed and "非法结果" in "".join(report.reasons)


@pytest.mark.parametrize("novelty", ["EXACT_COLLISION", "PARTIAL_OVERLAP"])
def test_novelty_scope_is_preserved(tmp_path, novelty):
    real_case(tmp_path)
    write_json(tmp_path / "review.json", {"kind": "synthetic review fixture", "scope": "fixed arithmetic only"})
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["review"] = {"novelty": novelty, "reviewer": "test-only", "explanation_zh": "仅覆盖冻结算术对象。",
                        "source": ref(tmp_path, "review.json"), "collision_scope": "冻结算术公式"}
    write_json(tmp_path / "research_evidence.json", bundle)
    report = evaluate(tmp_path)
    assert report.axes["novelty"] == novelty
    assert report.axes["scientific_claim"] == "SUPPORTED"
    assert not report.paper_allowed


def test_exposed_test_set_is_exploratory(tmp_path):
    real_case(tmp_path)
    report = evaluate(tmp_path)
    assert report.axes["paper_readiness"] == "NEEDS_INDEPENDENT_CHECK"
    assert "探索性" in "".join(report.reasons)


def test_revisions_never_overwrite_history_and_can_retract(tmp_path):
    real_case(tmp_path)
    first = claim_path(tmp_path, "claim_finite_arithmetic", 1)
    original = first.read_bytes()
    claim = read_json(first)
    claim["definition"] = "新的反证纠正了旧范围"
    with pytest.raises(ValueError, match="禁止覆盖"):
        freeze_claim(tmp_path, claim)
    claim["claim_version"] = 2
    claim["revision_reason"] = "新反证；撤销 v1 在扩展对象上的解释，原记录保留"
    second = freeze_claim(tmp_path, claim)
    assert first.read_bytes() == original and second.is_file()


def test_actual_selected_source_must_be_frozen(tmp_path):
    config = prepare_run(tmp_path)
    (tmp_path / "stage-10" / "experiment" / "extra.py").write_text("print('unfrozen')", encoding="utf-8")
    with pytest.raises(ValueError, match="未冻结"):
        preflight(tmp_path, config, 12)


def test_optimizer_expansion_is_explicitly_held(tmp_path):
    config = prepare_run(tmp_path)
    with pytest.raises(ValueError, match="逐子任务"):
        preflight(tmp_path, config, 13)


def test_paper_unbound_number_including_old_whitelist_is_blocked(tmp_path):
    real_case(tmp_path)
    paper = tmp_path / "paper.md"
    paper.write_text("结果为 0.5；另有 123.456。", encoding="utf-8")
    assert not evaluate(tmp_path, papers=["paper.md"]).paper_allowed
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["papers"] = [{**ref(tmp_path, "paper.md"), "bindings": []}]
    write_json(tmp_path / "research_evidence.json", bundle)
    report = evaluate(tmp_path, papers=["paper.md"])
    assert not report.paper_allowed and "绑定" in "".join(report.reasons)


def test_exact_numeric_binding_and_mismatch(tmp_path):
    real_case(tmp_path)
    paper = tmp_path / "paper.md"
    paper.write_text("有限对象数量为 16。", encoding="utf-8")
    bundle = read_json(tmp_path / "research_evidence.json")
    source = {"path": "stage-12/runs/sandbox/_project_1/results.json", "pointer": "/n"}
    write_json(tmp_path / "review.json", {"note": "fixture only; not real independent audit"})
    bundle["review"] = {"novelty": "PLAUSIBLE_INCREMENT", "reviewer": "synthetic-fixture",
        "explanation_zh": "仅模拟审查字段完整性，不代表真实原创。", "source": ref(tmp_path, "review.json"),
        "independent_check": "PASSED", "independent_source": ref(tmp_path, "review.json"),
        "independent_reviewer": "fixture-replicator"}
    bundle["test_exposure"] = "NOT_APPLICABLE"
    bundle["papers"] = [{**ref(tmp_path, "paper.md"), "bindings": [{"start": paper.read_text(encoding="utf-8").index("16"), "token": "16", "source": source}]}]
    write_json(tmp_path / "research_evidence.json", bundle)
    assert evaluate(tmp_path, papers=["paper.md"]).paper_allowed
    bundle["papers"][0]["bindings"][0]["source"]["pointer"] = "/proposed_score"
    write_json(tmp_path / "research_evidence.json", bundle)
    assert not evaluate(tmp_path, papers=["paper.md"]).paper_allowed


def test_cli_recovery_new_process_and_real_repeat(tmp_path, capsys):
    real_case(tmp_path / "first")
    real_case(tmp_path / "second")
    assert evaluate(tmp_path / "first").metrics == evaluate(tmp_path / "second").metrics
    assert main(["evidence", str(tmp_path / "first")]) == 0
    assert "研究意义" in capsys.readouterr().out
    code = "import sys,json; from pathlib import Path; from researchclaw.pipeline.evidence_gate import evaluate; print(json.dumps(evaluate(Path(sys.argv[1])).as_dict()))"
    process = subprocess.run([sys.executable, "-c", code, str(tmp_path / "first")], capture_output=True, text=True, check=True, timeout=15)
    assert json.loads(process.stdout)["axes"]["scientific_claim"] == "SUPPORTED"


def test_archive_retains_unresolved_science_without_blocking_preservation(tmp_path, monkeypatch):
    config = prepare_run(tmp_path)
    def archive(stage_dir, *args, **kwargs):
        (stage_dir / "archive.md").write_text("未执行实验的原始归档", encoding="utf-8")
        write_json(stage_dir / "bundle_index.json", {"status": "raw_unreviewed"})
        return executor.StageResult(stage=Stage.KNOWLEDGE_ARCHIVE, status=StageStatus.DONE,
                                    artifacts=("archive.md", "bundle_index.json"))
    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.KNOWLEDGE_ARCHIVE, archive)
    result = executor.execute_stage(Stage.KNOWLEDGE_ARCHIVE, run_dir=tmp_path, run_id="archive", config=config, adapters=AdapterBundle())
    assert result.status == StageStatus.DONE
    report = read_json(tmp_path / "stage-21" / "evidence_review.json")
    assert report["decision"] == "HOLD" and report["axes"]["scientific_claim"] == "NOT_TESTED"


def test_final_verified_paper_is_rechecked_after_stage23(tmp_path, monkeypatch):
    config, _ = real_case(tmp_path)
    write_json(tmp_path / "review.json", {"note": "synthetic review fixture"})
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["review"] = {"novelty": "PLAUSIBLE_INCREMENT", "reviewer": "fixture",
        "explanation_zh": "测试人工字段，不是实际科研审查。", "source": ref(tmp_path, "review.json"),
        "independent_check": "PASSED", "independent_source": ref(tmp_path, "review.json"),
        "independent_reviewer": "fixture-replicator"}
    bundle["test_exposure"] = "NOT_APPLICABLE"
    paper = tmp_path / "stage-22" / "paper_final.md"
    paper.parent.mkdir(parents=True)
    paper.write_text("有限对象数量为 16。", encoding="utf-8")
    bundle["papers"] = [{**ref(tmp_path, "stage-22/paper_final.md"), "bindings": [
        {"start": paper.read_text(encoding="utf-8").index("16"), "token": "16", "source":
            {"path": "stage-12/runs/sandbox/_project_1/results.json", "pointer": "/n"}}]}]
    write_json(tmp_path / "research_evidence.json", bundle)
    def citation(stage_dir, *args, **kwargs):
        write_json(stage_dir / "verification_report.json", {"fixture": True})
        (stage_dir / "references_verified.bib").write_text("@article{fixture, title={fixture}}", encoding="utf-8")
        (stage_dir / "paper_final_verified.md").write_text("无来源的最终数值 999。", encoding="utf-8")
        return executor.StageResult(stage=Stage.CITATION_VERIFY, status=StageStatus.DONE,
                                    artifacts=("verification_report.json", "references_verified.bib"))
    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.CITATION_VERIFY, citation)
    result = executor.execute_stage(Stage.CITATION_VERIFY, run_dir=tmp_path, run_id="final", config=config,
                                    adapters=AdapterBundle(), auto_approve_gates=True)
    assert result.status == StageStatus.PAUSED
    assert (tmp_path / "stage-23" / "paper_final_verified.md").is_file()


@pytest.mark.parametrize("name", ["../outside.json", "C:/outside.json", "C:outside.json"])
def test_evidence_paths_cannot_escape(tmp_path, name):
    with pytest.raises(ValueError):
        local_path(tmp_path, name)
