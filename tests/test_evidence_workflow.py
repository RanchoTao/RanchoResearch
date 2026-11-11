"""Workflow regressions: Stage13 exploration, receipt selection, reviewer
independence, bundle sealing. Software checks only, not research quality."""
from __future__ import annotations

import json

import pytest

from researchclaw.adapters import AdapterBundle
from researchclaw.cli import main
from researchclaw.pipeline import executor
from researchclaw.pipeline.evidence_gate import (EvidenceError, evaluate, read_json, seal_bundle,
                                                 write_template)
from researchclaw.pipeline.stages import Stage, StageStatus
from scripts.evidence_smoke import prepare_run, ref, run_prepared, write_json


def _drop_receipt_choice(root):
    bundle = read_json(root / "research_evidence.json")
    bundle.pop("receipt", None)
    write_json(root / "research_evidence.json", bundle)


def test_stage13_unauthorized_is_skipped_not_paused(tmp_path, monkeypatch):
    config = prepare_run(tmp_path)
    run_prepared(tmp_path, config)
    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.ITERATIVE_REFINE,
                        lambda *a, **k: pytest.fail("unauthorized optimizer must not run"))
    result = executor.execute_stage(Stage.ITERATIVE_REFINE, run_dir=tmp_path, run_id="r", config=config,
                                    adapters=AdapterBundle())
    assert result.status == StageStatus.DONE and result.decision == "skip_exploration"
    assert (tmp_path / "stage-13" / "exploration_skipped.json").is_file()
    assert evaluate(tmp_path).promotion_allowed


def test_stage13_authorized_exploration_never_counts_as_evidence(tmp_path, monkeypatch):
    config = prepare_run(tmp_path)
    run_prepared(tmp_path, config)
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["authorization"]["allow_exploration"] = True
    write_json(tmp_path / "research_evidence.json", bundle)
    before = evaluate(tmp_path).metrics

    def optimizer(stage_dir, *args, **kwargs):
        write_json(stage_dir / "refinement_log.json", {"best": 999})
        (stage_dir / "experiment_final").mkdir()
        (stage_dir / "experiment_final" / "main.py").write_text("print(1)", encoding="utf-8")
        return executor.StageResult(stage=Stage.ITERATIVE_REFINE, status=StageStatus.DONE,
                                    artifacts=("refinement_log.json", "experiment_final/"))

    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.ITERATIVE_REFINE, optimizer)
    result = executor.execute_stage(Stage.ITERATIVE_REFINE, run_dir=tmp_path, run_id="r", config=config,
                                    adapters=AdapterBundle())
    assert result.status == StageStatus.DONE
    assert any(ref_.startswith("evidence/explorations/") for ref_ in result.evidence_refs)
    assert len(list((tmp_path / "evidence" / "receipts").glob("*.json"))) == 1
    assert evaluate(tmp_path).metrics == before


def test_unique_receipt_is_used_without_manual_selection(tmp_path):
    config = prepare_run(tmp_path)
    run_prepared(tmp_path, config)
    _drop_receipt_choice(tmp_path)
    report = evaluate(tmp_path)
    assert report.promotion_allowed and any("自动选用" in r for r in report.reasons)


def test_multiple_receipts_still_require_explicit_choice(tmp_path):
    config = prepare_run(tmp_path)
    run_prepared(tmp_path, config)
    run_prepared(tmp_path, config)
    _drop_receipt_choice(tmp_path)
    report = evaluate(tmp_path)
    assert not report.promotion_allowed and report.decision == "HOLD"
    receipts = sorted((tmp_path / "evidence" / "receipts").glob("*.json"))
    assert main(["evidence", str(tmp_path), "--select-receipt",
                 receipts[0].relative_to(tmp_path).as_posix()]) == 0
    assert evaluate(tmp_path).promotion_allowed


def _paper_ready(root, review):
    write_json(root / "review.json", {"note": "fixture"})
    paper = root / "paper.md"
    paper.write_text("有限对象数量为 16。", encoding="utf-8")
    bundle = read_json(root / "research_evidence.json")
    bundle["review"] = {"novelty": "PLAUSIBLE_INCREMENT", "explanation_zh": "测试字段。",
                        "source": ref(root, "review.json"), "independent_check": "PASSED",
                        "independent_source": ref(root, "review.json"), **review}
    bundle["test_exposure"] = "NOT_APPLICABLE"
    bundle["papers"] = [{**ref(root, "paper.md"), "bindings": [{"start": paper.read_text(encoding="utf-8").index("16"), "token": "16", "source":
        {"path": "stage-12/runs/sandbox/_project_1/results.json", "pointer": "/n"}}]}]
    write_json(root / "research_evidence.json", bundle)
    return evaluate(root, papers=["paper.md"])


@pytest.mark.parametrize("review,allowed", [
    ({"reviewer": "novelty-agent", "independent_reviewer": "replication-agent"}, True),
    ({"reviewer": "Local-Controlled-Smoke", "independent_reviewer": "replication-agent"}, False),
    ({"reviewer": "novelty-agent", "independent_reviewer": "local-controlled-smoke"}, False),
    ({"reviewer": "novelty-agent"}, False),
])
def test_self_review_does_not_count(tmp_path, review, allowed):
    config = prepare_run(tmp_path)
    run_prepared(tmp_path, config)
    assert _paper_ready(tmp_path, review).paper_allowed is allowed


def test_template_and_seal(tmp_path):
    write_template(tmp_path)
    with pytest.raises(EvidenceError, match="TODO"):
        seal_bundle(tmp_path)
    with pytest.raises(EvidenceError, match="拒绝覆盖"):
        write_template(tmp_path)


def test_seal_auto_binds_selected_code_and_new_version(tmp_path):
    config = prepare_run(tmp_path)
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["inputs"]["code"] = "auto"
    write_json(tmp_path / "research_evidence.json", bundle)
    sealed, warnings = seal_bundle(tmp_path)
    assert not warnings
    paths = {r["path"] for r in sealed["inputs"]["code"]}
    assert paths == {"stage-10/experiment/main.py", "stage-10/experiment/data.json"}
    first = run_prepared(tmp_path, config)
    assert first["evidence"]["promotion_allowed"]
    # Changing code after freezing: same version is rejected, new version runs.
    with (tmp_path / "stage-10" / "experiment" / "main.py").open("a", encoding="utf-8") as stream:
        stream.write("\n# revised\n")
    bundle = read_json(tmp_path / "research_evidence.json")
    bundle["inputs"]["code"] = "auto"
    write_json(tmp_path / "research_evidence.json", bundle)
    _, warnings = seal_bundle(tmp_path)
    assert warnings
    sealed, warnings = seal_bundle(tmp_path, new_version_reason="修正实验代码注释")
    assert sealed["claim"]["claim_version"] == 2 and "receipt" not in sealed and not warnings
    second = run_prepared(tmp_path, config)
    assert second["evidence"]["promotion_allowed"] and second["evidence"]["claim_version"] == 2
    assert (tmp_path / "evidence" / "claims" / "claim_finite_arithmetic" / "v1.json").is_file()


def test_pipeline_runs_from_execution_to_decision_without_stalling(tmp_path, monkeypatch):
    """Before v0.6.1 a real-mode run always paused at Stage13."""
    from researchclaw.pipeline.runner import execute_pipeline
    config = prepare_run(tmp_path)

    def analysis(stage_dir, *args, **kwargs):
        (stage_dir / "analysis.md").write_text("analysis", encoding="utf-8")
        return executor.StageResult(stage=Stage.RESULT_ANALYSIS, status=StageStatus.DONE, artifacts=("analysis.md",))

    def decision(stage_dir, *args, **kwargs):
        (stage_dir / "decision.md").write_text("PROCEED", encoding="utf-8")
        return executor.StageResult(stage=Stage.RESEARCH_DECISION, status=StageStatus.DONE,
                                    artifacts=("decision.md",), decision="proceed")

    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.RESULT_ANALYSIS, analysis)
    monkeypatch.setitem(executor._STAGE_EXECUTORS, Stage.RESEARCH_DECISION, decision)
    results = execute_pipeline(run_dir=tmp_path, run_id="flow", config=config, adapters=AdapterBundle(),
                               from_stage=Stage.EXPERIMENT_RUN, to_stage=Stage.RESEARCH_DECISION)
    statuses = {r.stage: r.status for r in results}
    assert statuses[Stage.ITERATIVE_REFINE] == StageStatus.DONE
    assert statuses.get(Stage.RESEARCH_DECISION) == StageStatus.DONE, [(r.stage, r.status, r.error) for r in results]
    assert (tmp_path / "events.jsonl").is_file() and (tmp_path / "cost_summary.json").is_file()
