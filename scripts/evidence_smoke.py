"""Bounded CPU integration check. No model/API/GPU; no scientific novelty.

Usage: python scripts/evidence_smoke.py --output artifacts/evidence-smoke
The finite arithmetic task uses explicitly synthetic data. It checks that the
existing sandbox really executes and that results survive process recovery.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from researchclaw.adapters import AdapterBundle
from researchclaw.config import RCConfig, LlmConfig, ExperimentConfig, SandboxConfig
from researchclaw.hitl.checksums import compute_sha256
from researchclaw.pipeline.evidence_gate import evaluate, read_json, render_zh
from researchclaw.pipeline.executor import execute_stage
from researchclaw.pipeline.stages import Stage


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ref(root: Path, name: str) -> dict:
    return {"path": name, "sha256": compute_sha256(root / name)}


def prepare_run(root: Path, case: str = "positive") -> RCConfig:
    root.mkdir(parents=True, exist_ok=True)
    project = root / "stage-10" / "experiment"
    project.mkdir(parents=True, exist_ok=True)
    write_json(project / "data.json", {"x": list(range(-8, 8)), "origin": "SYNTHETIC"})
    code = '''import json
from pathlib import Path
data = json.loads(Path("data.json").read_text(encoding="utf-8"))
xs = data["x"]
truth = [2*x+3 for x in xs]
proposed = [2*x+3 for x in xs]
baseline = [2*x for x in xs]
if CASE == "negative":
    baseline = list(proposed)
if CASE == "resource_error":
    raise RuntimeError("controlled resource failure; not scientific refutation")
score = lambda predicted: -sum((a-b)**2 for a,b in zip(predicted,truth))/len(xs)
result = {"proposed_score": score(proposed), "baseline_score": score(baseline),
          "n": len(xs), "aligned": CASE != "misaligned", "data_origin": "SYNTHETIC"}
if CASE == "nan":
    result["proposed_score"] = float("nan")
Path("results.json").write_text(json.dumps(result), encoding="utf-8")
print("primary_metric: 1.0")
'''.replace("CASE", repr(case))
    (project / "main.py").write_text(code, encoding="utf-8")
    exp = ExperimentConfig(mode="sandbox", time_budget_sec=10, max_iterations=1,
                           metric_key="primary_metric", metric_direction="maximize",
                           sandbox=SandboxConfig(python_path=sys.executable, gpu_required=False))
    # Explicit empty provider prevents accidental use of ambient API credentials.
    config = replace(RCConfig.load(Path(__file__).parents[1] / "config.researchclaw.example.yaml", check_paths=False),
                     experiment=exp, llm=LlmConfig(provider="offline-evidence-smoke"))
    snapshot = {"mode": exp.mode, "time_budget_sec": exp.time_budget_sec,
                "max_iterations": exp.max_iterations, "metric_key": exp.metric_key,
                "metric_direction": exp.metric_direction}
    write_json(root / "frozen_config.json", snapshot)
    source = "stage-12/runs/sandbox/_project_1/results.json"
    protocol = {
        "claim_id": "claim_finite_arithmetic", "claim_version": 1,
        "purpose": "calibration" if case == "calibration" else "science",
        "scope_type": "fixed_finite_population", "execution_config": snapshot,
        "measurement_method": "对冻结16个合成整数，逐项计算负均方误差；不外推总体。",
        "data_contract": "固定整数序列，y=2x+3；同索引比较；数据为 SYNTHETIC。",
        "origin_source": {"path": source, "pointer": "/data_origin"},
        "checks": [{"name": "index alignment", "path": source, "pointer": "/aligned", "op": "eq", "expected": True},
                   {"name": "synthetic label", "path": source, "pointer": "/data_origin", "op": "eq", "expected": "SYNTHETIC"}],
        "metrics": {"proposed": {"path": source, "pointer": "/proposed_score", "max": 0},
                    "simple_baseline": {"path": source, "pointer": "/baseline_score", "max": 0}},
        "baselines": [] if case == "no_baseline" else ["simple_baseline"],
        "sample_count": {"path": source, "pointer": "/n"}, "min_samples": 32 if case == "small_sample" else 16,
        "decision_rule": {"kind": "finite_computation", "metric": "proposed", "baseline": "simple_baseline",
                          "direction": "maximize", "min_effect": 0.5}}
    write_json(root / "protocol.json", protocol)
    code_refs = [ref(root, "stage-10/experiment/main.py"), ref(root, "stage-10/experiment/data.json")]
    bundle = {"schema_version": "0.6.0", "claim": {
        "claim_id": "claim_finite_arithmetic", "claim_version": 1,
        "definition": "对冻结16个整数，精确公式相对少截距公式的负均方误差增量至少为0.5。",
        "scope": "仅固定合成整数；不涉及真实数据或新机制。", "research_value": "已知算术关系，用于门禁与复现验收；没有原创科学贡献。",
        "known_work": ["Elementary arithmetic; constructed integration check"],
        "falsification": "冻结对象上的增量小于0.5。", "protocol": ref(root, "protocol.json")},
        "inputs": {"code": code_refs, "data": [code_refs[1]], "configuration": [ref(root, "frozen_config.json")],
                   "data_origin": "SYNTHETIC"},
        "authorization": {"actor": "local-controlled-smoke", "reason": "用户授权的本地低成本工程验收，最多10秒，无模型服务。",
                          "allowed_modes": ["sandbox"], "max_time_budget_sec": 10},
        "provenance": {"model": "NOT_APPLICABLE: arithmetic only", "seed": "NOT_APPLICABLE: deterministic",
                       "parameters": "RECORDED: frozen_config.json", "api_cost": "NOT_APPLICABLE: no API calls"},
        "test_exposure": "EXPOSED", "review": {"novelty": "UNKNOWN"}, "papers": []}
    write_json(root / "research_evidence.json", bundle)
    write_json(root / "stage-11" / "schedule.json", {"tasks": [{"id": "finite"}]})
    return config


def run_prepared(root: Path, config: RCConfig) -> dict:
    result = execute_stage(Stage.EXPERIMENT_RUN, run_dir=root, run_id="controlled-cpu", config=config,
                           adapters=AdapterBundle(), auto_approve_gates=False)
    receipts = [name for name in result.evidence_refs if name.startswith("evidence/receipts/")]
    if receipts:
        bundle = read_json(root / "research_evidence.json")
        # Explicitly choose this attempt, never choose the highest metric.
        bundle["receipt"] = receipts[-1]
        write_json(root / "research_evidence.json", bundle)
    return {"stage_status": result.status.value, "stage_error": result.error,
            "evidence": evaluate(root).as_dict()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("输出目录已存在，拒绝覆盖；请选择新目录")
    results = []
    for name in ("first", "reproduction"):
        root = args.output / name
        results.append(run_prepared(root, prepare_run(root)))
    repeat = results[0]["evidence"]["metrics"] == results[1]["evidence"]["metrics"]
    payload = {"kind": "CONTROLLED_SYNTHETIC_CPU_INTEGRATION_NOT_AGENT_BENCHMARK",
               "reproduced": repeat, "runs": results, "scientific_novelty": "NOT_CLAIMED"}
    write_json(args.output / "smoke.json", payload)
    print(render_zh(args.output / "first", evaluate(args.output / "first")))
    print(f"确定性复跑一致：{repeat}。这不是代理科研基准或原创性证明。")
    return 0 if repeat and all(r["evidence"]["promotion_allowed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
