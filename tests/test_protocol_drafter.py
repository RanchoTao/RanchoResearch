"""Agent-drafted pre-registration before Stage 12 (software checks only)."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from researchclaw.adapters import AdapterBundle
from researchclaw.config import ExperimentConfig, LlmConfig, RCConfig, SandboxConfig
from researchclaw.pipeline import executor, protocol_drafter
from researchclaw.pipeline.evidence_gate import evaluate, read_json
from researchclaw.pipeline.stages import Stage, StageStatus

ROOT = Path(__file__).parents[1]

CONTRACT_CODE = '''import json
from pathlib import Path
xs = list(range(-8, 8))
truth = [2*x + 3 for x in xs]
conditions = {"exact_formula": [2*x + 3 for x in xs], "no_intercept_baseline": [2*x for x in xs]}
metrics = {}
for name, pred in conditions.items():
    metrics[name] = {"neg_mse": -sum((a - b) ** 2 for a, b in zip(pred, truth)) / len(xs)}
result = {"data_origin": "SYNTHETIC", "n_samples": len(xs), "valid": True, "metrics": metrics}
Path("results.json").write_text(json.dumps(result), encoding="utf-8")
print("neg_mse: 0.0")
'''

GOOD_DRAFT = {
    "claim": {"definition": "On 16 fixed synthetic integers, the exact formula beats the no-intercept baseline "
                            "in negative MSE by at least 0.5.",
              "scope": "Fixed synthetic integers only.", "research_value": "Engineering fixture; no novelty.",
              "falsification": "Improvement below 0.5.", "known_work": ["elementary arithmetic"]},
    "proposed_condition": "exact_formula", "baseline_condition": "no_intercept_baseline", "metric": "neg_mse",
    "direction": "maximize", "min_effect": 0.5, "min_samples": 16,
    "measurement_method": "Negative mean squared error over the 16 integers.",
    "data_contract": "Integers -8..7 generated in code; y = 2x + 3.", "data_origin": "SYNTHETIC",
    "rationale": "fixture",
}


class FakeLLM:
    def __init__(self, draft: dict, verdict: dict):
        self.draft, self.verdict, self.calls = draft, verdict, []

    def chat(self, messages, system="", **kwargs):
        self.calls.append(system)
        body = self.draft if system == protocol_drafter.DRAFT_SYSTEM else self.verdict
        return SimpleNamespace(content=json.dumps(body), model="fake-model", prompt_tokens=0, completion_tokens=0)


def make_run(root: Path, mode: str, code: str = CONTRACT_CODE) -> RCConfig:
    project = root / "stage-10" / "experiment"
    project.mkdir(parents=True)
    (project / "main.py").write_text(code, encoding="utf-8")
    (root / "stage-09").mkdir()
    (root / "stage-09" / "exp_plan.yaml").write_text("conditions: [exact_formula, no_intercept_baseline]\n",
                                                     encoding="utf-8")
    (root / "stage-11").mkdir()
    (root / "stage-11" / "schedule.json").write_text('{"tasks": [{"id": "t"}]}', encoding="utf-8")
    exp = ExperimentConfig(mode="sandbox", time_budget_sec=10, max_iterations=1, metric_key="neg_mse",
                           metric_direction="maximize", protocol_author=mode,
                           sandbox=SandboxConfig(python_path=sys.executable, gpu_required=False))
    base = RCConfig.load(ROOT / "config.researchclaw.example.yaml", check_paths=False)
    return replace(base, experiment=exp, llm=LlmConfig(provider="offline-test"),
                   research=replace(base.research, topic="Linear fit fixture"))


def run12(root: Path, config: RCConfig):
    return executor.execute_stage(Stage.EXPERIMENT_RUN, run_dir=root, run_id="drafter", config=config,
                                  adapters=AdapterBundle())


def test_agent_mode_drafts_reviews_seals_and_runs(tmp_path, monkeypatch):
    config = make_run(tmp_path, "agent")
    llm = FakeLLM(GOOD_DRAFT, {"approve": True, "issues": [], "notes": "ok"})
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: llm)
    result = run12(tmp_path, config)
    assert result.status == StageStatus.DONE, result.error
    assert llm.calls == [protocol_drafter.DRAFT_SYSTEM, protocol_drafter.REVIEW_SYSTEM]
    bundle = read_json(tmp_path / "research_evidence.json")
    assert bundle["authorization"]["actor"].startswith("protocol-reviewer(same-model):")
    assert {r["path"] for r in bundle["inputs"]["code"]} == {"stage-10/experiment/main.py"}
    report = evaluate(tmp_path)
    assert report.promotion_allowed and report.axes["measurement_validity"] == "VALID"
    meta = json.loads((protocol_drafter.latest_draft(tmp_path) / "meta.json").read_text(encoding="utf-8"))
    assert meta["review"]["approve"] is True and "installed_at" in meta


def test_reviewer_rejection_pauses_without_bundle(tmp_path, monkeypatch):
    config = make_run(tmp_path, "agent")
    llm = FakeLLM(GOOD_DRAFT, {"approve": False, "issues": ["baseline is a straw man"]})
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: llm)
    result = run12(tmp_path, config)
    assert result.status == StageStatus.PAUSED and "straw man" in result.error
    assert not (tmp_path / "research_evidence.json").exists()
    assert not (tmp_path / "stage-12" / "runs").exists()


def test_human_review_mode_pauses_then_approval_runs(tmp_path, monkeypatch):
    config = make_run(tmp_path, "agent_with_human_review")
    llm = FakeLLM(GOOD_DRAFT, {"approve": True})
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: llm)
    first = run12(tmp_path, config)
    assert first.status == StageStatus.PAUSED and "--approve-draft" in first.error
    assert llm.calls == [protocol_drafter.DRAFT_SYSTEM]
    protocol_drafter.install(tmp_path, config, protocol_drafter.latest_draft(tmp_path),
                             actor="human-reviewer", reason="reviewed in test")
    second = run12(tmp_path, config)
    assert second.status == StageStatus.DONE, second.error
    assert read_json(tmp_path / "research_evidence.json")["authorization"]["actor"] == "human-reviewer"
    assert evaluate(tmp_path).promotion_allowed


@pytest.mark.parametrize("change,needle", [
    ({"proposed_condition": "invented_method"}, "invented_method"),
    ({"direction": "up"}, "direction"),
    ({"min_effect": 0}, "min_effect"),
    ({"baseline_condition": "exact_formula"}, "同一个条件"),
])
def test_static_check_blocks_bad_drafts(tmp_path, monkeypatch, change, needle):
    config = make_run(tmp_path, "agent")
    llm = FakeLLM({**GOOD_DRAFT, **change}, {"approve": True})
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: llm)
    result = run12(tmp_path, config)
    assert result.status == StageStatus.PAUSED and "静态检查" in result.error and needle in result.error
    assert llm.calls == [protocol_drafter.DRAFT_SYSTEM]
    assert not (tmp_path / "research_evidence.json").exists()


def test_code_without_output_contract_is_not_guessed(tmp_path, monkeypatch):
    legacy = 'import json\nopen("out.json","w").write(json.dumps({"exact_formula": 1, "no_intercept_baseline": 0, "neg_mse": 1}))\n'
    config = make_run(tmp_path, "agent", code=legacy)
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: FakeLLM(GOOD_DRAFT, {"approve": True}))
    result = run12(tmp_path, config)
    assert result.status == StageStatus.PAUSED and "证据输出约定" in result.error


def test_no_llm_pauses_and_manual_mode_is_unchanged(tmp_path, monkeypatch):
    config = make_run(tmp_path, "agent")
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: None)
    assert "LLM" in run12(tmp_path, config).error
    manual = make_run(tmp_path / "m", "manual")
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: pytest.fail("manual mode must not draft"))
    result = run12(tmp_path / "m", manual)
    assert result.status == StageStatus.PAUSED and "协议" in result.error


def test_install_refuses_to_overwrite(tmp_path, monkeypatch):
    config = make_run(tmp_path, "agent")
    monkeypatch.setattr(executor, "_make_llm", lambda cfg: FakeLLM(GOOD_DRAFT, {"approve": True}))
    assert run12(tmp_path, config).status == StageStatus.DONE
    with pytest.raises(Exception, match="拒绝覆盖"):
        protocol_drafter.install(tmp_path, config, protocol_drafter.latest_draft(tmp_path),
                                 actor="x", reason="y")


def test_code_generation_gets_output_contract():
    for key in ('"data_origin"', '"n_samples"', '"valid"', '"metrics"', "baseline"):
        assert key in protocol_drafter.OUTPUT_CONTRACT
