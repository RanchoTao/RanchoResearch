"""Offline, fixed-plan evidence comparison for ARC-Bench (no execution authority).

Reuses config/*/{manifests,rubrics}; does not import runners or provider clients.
Records are audit attestations, not proof that a research experiment happened.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SYSTEMS = ("autoresearchclaw", "rancho_baseline", "rancho_upgraded")
REPOS = {
    "autoresearchclaw": "https://github.com/aiming-lab/AutoResearchClaw",
    "rancho_baseline": "https://github.com/RanchoTao/RanchoResearch",
    "rancho_upgraded": "https://github.com/RanchoTao/RanchoResearch",
}
BOOL_FIELDS = ("valid_task_completed", "evidence_complete", "reproduced_independently")
COUNT_PAIRS = {
    "false_promotion_rate": ("false_promotions", "audited_promotions"),
    "false_rejection_rate": ("false_rejections", "audited_unresolved_claims"),
    "invalid_detection_rate": ("invalid_detected", "invalid_results"),
    "negative_retention_rate": ("negative_preserved", "valid_negative_results"),
}
MEASURE_FIELDS = ("cost_usd", "wall_time_sec", "cpu_seconds", "gpu_seconds", "api_calls", "output_tokens", "human_review_minutes", "human_interventions")
COUNT_FIELDS = tuple(dict.fromkeys(k for pair in COUNT_PAIRS.values() for k in pair))
METRIC_DEFINITIONS = {
    "completion_rate": "valid_task_completed / all planned runs, including resource failures",
    "evidence_completeness_rate": "evidence_complete / completed runs",
    "independent_reproduction_rate": "reproduced_independently / all planned runs (preselected)",
    **{name: f"{a} / {b}" for name, (a, b) in COUNT_PAIRS.items()},
    "means": "sum actual measurement / all attempted runs; missing is UNKNOWN, never zero",
}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _number(value: Any, *, integer: bool = False, positive: bool = False) -> bool:
    return (type(value) in ((int,) if integer else (int, float))
            and math.isfinite(value) and (value > 0 if positive else value >= 0))


def _hash(value: Any, length: int = 64) -> bool:
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None and set(value) != {"0"}


def _artifact(ref: dict, root: Path) -> Path:
    _require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "工件必须有 path/sha256")
    _require(isinstance(ref["path"], str) and _hash(ref["sha256"]), "工件路径或哈希无效")
    base = root.resolve()
    path = (base / ref["path"]).resolve()
    _require(path.is_relative_to(base), "工件必须在指定证据根目录内")
    _require(path.is_file(), f"工件不存在：{ref['path']}")
    _require(hashlib.sha256(path.read_bytes()).hexdigest() == ref["sha256"], f"工件哈希不符：{ref['path']}")
    return path


def artifact_ref(path: Path, root: Path = ROOT) -> dict:
    path = path.resolve()
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def make_plan(systems: dict, model: dict, budget: dict, task_ids: list[str], seeds: list[int], *, root: Path = ROOT) -> dict:
    """Freeze existing ARC inputs. Caller must supply actual version fingerprints."""
    tasks = []
    for task_id in task_ids:
        _require(isinstance(task_id, str) and re.fullmatch(r"[A-Z]+[0-9]+", task_id) is not None, "任务 ID 无效")
        manifests = list((root / "experiments/arc_bench/config").glob(f"*/manifests/{task_id}.yaml"))
        _require(len(manifests) == 1, f"任务 manifest 不唯一或不存在：{task_id}")
        rubric = manifests[0].parents[1] / "rubrics" / f"{task_id}.json"
        _require(rubric.is_file(), f"任务 rubric 不存在：{task_id}")
        tasks.append({"task_id": task_id, "manifest": artifact_ref(manifests[0], root), "rubric": artifact_ref(rubric, root)})
    plan = {"schema_version": 1, "systems": systems, "model": model, "budget": budget,
            "tasks": tasks, "seeds": seeds,
            "protocol": {"scope": "EXPLORATORY_PUBLIC_TASKS", "reproduce_all": True,
                         "metric_definition_sha256": digest(METRIC_DEFINITIONS),
                         "grader": "independent-human-audit-v1", "selection": "all runs; no best-of or rollback selection"}}
    plan["plan_sha256"] = digest(plan)
    validate_plan(plan, root=root)
    return plan


def validate_plan(plan: dict, *, root: Path = ROOT) -> None:
    _require(isinstance(plan, dict) and set(plan) == {"schema_version", "systems", "model", "budget", "tasks", "seeds", "protocol", "plan_sha256"}, "计划 schema 不符")
    _require(type(plan["schema_version"]) is int and plan["schema_version"] == 1, "不支持的计划 schema_version")
    _require(_hash(plan["plan_sha256"]) and digest({k: v for k, v in plan.items() if k != "plan_sha256"}) == plan["plan_sha256"], "计划已修改或未冻结")
    systems = plan["systems"]
    _require(isinstance(systems, dict) and set(systems) == set(SYSTEMS), "必须固定原版、当前基线、升级后三个系统")
    for name, identity in systems.items():
        _require(isinstance(identity, dict) and set(identity) == {"repository", "commit", "patch_sha256"}, "系统身份 schema 不符")
        _require(identity["repository"] == REPOS[name], f"系统 repository 身份错误：{name}")
        _require(_hash(identity["commit"], 40), f"必须固定实际完整提交：{name}")
        _require(identity["patch_sha256"] is None or _hash(identity["patch_sha256"]), "工作树补丁必须固定 SHA256 或明确为 null（干净提交）")
    _require(systems["rancho_baseline"] != systems["rancho_upgraded"], "基线与升级版身份相同，无法对照")
    model = plan["model"]
    _require(isinstance(model, dict) and set(model) == {"provider", "model_id", "settings"}, "模型 schema 不符")
    _require(all(isinstance(model[k], str) and model[k].strip() for k in ("provider", "model_id")) and isinstance(model["settings"], dict), "模型身份或参数未固定")
    budget = plan["budget"]
    expected = {"wall_time_sec", "max_api_calls", "max_output_tokens", "max_cost_usd", "max_gpu_seconds", "max_memory_mb"}
    _require(isinstance(budget, dict) and set(budget) == expected, "预算 schema 不符")
    for name, value in budget.items():
        _require(_number(value, integer=name in {"max_api_calls", "max_output_tokens", "max_memory_mb"}, positive=name in {"wall_time_sec", "max_memory_mb"}), f"预算非法：{name}")
    _require(budget["max_gpu_seconds"] == 0, "本最小方案只支持 CPU；GPU 评测需另定授权协议")
    seeds = plan["seeds"]
    _require(isinstance(seeds, list) and seeds and all(_number(s, integer=True) for s in seeds) and len(set(seeds)) == len(seeds), "随机种子必须是非空、无重复的非负整数列表")
    protocol = plan["protocol"]
    _require(isinstance(protocol, dict) and protocol == {"scope": "EXPLORATORY_PUBLIC_TASKS", "reproduce_all": True, "metric_definition_sha256": digest(METRIC_DEFINITIONS), "grader": "independent-human-audit-v1", "selection": "all runs; no best-of or rollback selection"}, "评分协议未固定或不支持")
    _require(isinstance(plan["tasks"], list) and plan["tasks"], "任务集为空")
    ids = []
    for task in plan["tasks"]:
        _require(isinstance(task, dict) and set(task) == {"task_id", "manifest", "rubric"}, "任务 schema 不符")
        _require(isinstance(task["task_id"], str) and re.fullmatch(r"[A-Z]+[0-9]+", task["task_id"]) is not None, "任务 ID 无效")
        ids.append(task["task_id"])
        for kind in ("manifest", "rubric"):
            path = _artifact(task[kind], root)
            suffix = ".yaml" if kind == "manifest" else ".json"
            _require(path.name == task["task_id"] + suffix, "任务与输入工件不匹配")
    _require(len(set(ids)) == len(ids), "任务重复")


def dry_run(plan: dict, *, root: Path = ROOT) -> list[dict]:
    """Only verify local files and emit NOT_RUN records; never launches a runner."""
    validate_plan(plan, root=root)
    return [{"schema_version": 1, "plan_sha256": plan["plan_sha256"], "system_id": system,
             "system_sha256": digest(plan["systems"][system]), "task_id": task["task_id"], "seed": seed,
             "status": "NOT_RUN", "actual_model": None, "audit_refs": [],
             "observations": {k: None for k in (*BOOL_FIELDS, *COUNT_FIELDS, *MEASURE_FIELDS)}}
            for system in SYSTEMS for task in plan["tasks"] for seed in plan["seeds"]]


def _ratio(numerator: int, denominator: int, unknown: int) -> dict:
    return {"state": "UNKNOWN" if unknown else ("MEASURED" if denominator else "NOT_APPLICABLE"),
            "numerator": numerator, "denominator": denominator, "unknown_runs": unknown,
            "value": numerator / denominator if denominator and not unknown else None}


def summarize(plan: dict, records: list[dict], *, root: Path = ROOT, evidence_root: Path | None = None) -> dict:
    validate_plan(plan, root=root)
    _require(isinstance(records, list), "运行记录必须为逐 run JSON 数组")
    templates = dry_run(plan, root=root)
    cells = {(r["system_id"], r["task_id"], r["seed"]): r for r in templates}
    seen = set()
    reasons = []
    for record in records:
        _require(isinstance(record, dict) and set(record) == set(templates[0]), "运行记录 schema 不符")
        _require(type(record["seed"]) is int and isinstance(record["system_id"], str) and isinstance(record["task_id"], str), "运行单元身份类型不符")
        key = (record["system_id"], record["task_id"], record["seed"])
        _require(key in cells and key not in seen, "运行记录不属于冻结计划或重复")
        seen.add(key)
        _require(type(record["schema_version"]) is int and record["schema_version"] == 1 and record["plan_sha256"] == plan["plan_sha256"] and record["system_sha256"] == cells[key]["system_sha256"], "记录版本或计划/系统身份哈希不符")
        _require(record["status"] in {"NOT_RUN", "COMPLETED", "BLOCKED", "FAILED"}, "运行状态非法")
        obs = record["observations"]
        _require(isinstance(obs, dict) and set(obs) == set(cells[key]["observations"]), "观测字段 schema 不符")
        for name in BOOL_FIELDS:
            _require(obs[name] is None or type(obs[name]) is bool, f"观测必须是 bool/null：{name}")
        for name in (*COUNT_FIELDS, *MEASURE_FIELDS):
            _require(obs[name] is None or _number(obs[name], integer=name in COUNT_FIELDS or name in {"human_interventions", "api_calls", "output_tokens"}), f"观测必须是有限非负数/null：{name}")
        for a, b in COUNT_PAIRS.values():
            _require(obs[a] is None or obs[b] is None or obs[a] <= obs[b], "计数分子超过分母")
        _require(not(record["status"] != "COMPLETED" and any(obs[k] is True for k in BOOL_FIELDS)), "未完成运行不能宣称任务、证据或复现成功")
        _require(record["status"] != "NOT_RUN" or all(v is None for v in obs.values()), "NOT_RUN 不得含实测观测")
        _require(isinstance(record["audit_refs"], list), "audit_refs 必须为列表")
        for ref in record["audit_refs"]:
            _artifact(ref, evidence_root or root)
        if record["status"] != "NOT_RUN":
            if record["actual_model"] != plan["model"]:
                reasons.append(f"{key}: 实际模型或参数未记录/不一致")
            if not record["audit_refs"]:
                reasons.append(f"{key}: 缺少可核验审核工件")
            if obs["wall_time_sec"] is None:
                reasons.append(f"{key}: 实际耗时未记录")
            elif obs["wall_time_sec"] > plan["budget"]["wall_time_sec"]:
                reasons.append(f"{key}: 墙钟预算超出")
            if obs["cost_usd"] is None:
                reasons.append(f"{key}: 实际成本未记录")
            elif obs["cost_usd"] > plan["budget"]["max_cost_usd"]:
                reasons.append(f"{key}: 成本预算超出")
            if obs["gpu_seconds"] != 0:
                reasons.append(f"{key}: CPU 约束未满足或 GPU 用量未知")
            for field, limit in (("api_calls", "max_api_calls"), ("output_tokens", "max_output_tokens")):
                if obs[field] is None:
                    reasons.append(f"{key}: {field} 实际用量未记录")
                elif obs[field] > plan["budget"][limit]:
                    reasons.append(f"{key}: {field} 预算超出")
        cells[key] = record
    out = {"schema_version": 1, "plan_sha256": plan["plan_sha256"], "benchmark_status": "NOT_RUN" if all(r["status"] == "NOT_RUN" for r in cells.values()) else "RECORDED_NOT_INDEPENDENTLY_VERIFIED",
           "comparison_status": "NOT_RUN", "incomparable_reasons": reasons,
           "metric_definitions": METRIC_DEFINITIONS, "systems": {}, "runs": list(cells.values()),
           "explanation_zh": "仅统计本地审核记录；记录和哈希不能证明科学成立。公开任务结果为探索性，未运行单元不按零计。"}
    for system in SYSTEMS:
        rows = [r for r in cells.values() if r["system_id"] == system]
        n = len(rows)
        status = Counter(r["status"] for r in rows)
        metrics = {}
        for metric, field in (("completion_rate", "valid_task_completed"), ("independent_reproduction_rate", "reproduced_independently")):
            # Resource failures stay in the denominator, without becoming a scientific KILL.
            values = [False if r["status"] in {"FAILED", "BLOCKED"} else r["observations"][field] for r in rows]
            metrics[metric] = _ratio(sum(v is True for v in values), n, sum(v is None for v in values))
        completed = [r for r in rows if r["status"] == "COMPLETED"]
        values = [r["observations"]["evidence_complete"] for r in completed]
        metrics["evidence_completeness_rate"] = _ratio(sum(v is True for v in values), len(completed), sum(v is None for v in values) + status["NOT_RUN"])
        for metric, (a, b) in COUNT_PAIRS.items():
            known = [r for r in rows if r["observations"][a] is not None and r["observations"][b] is not None]
            metrics[metric] = _ratio(sum(r["observations"][a] for r in known), sum(r["observations"][b] for r in known), n - len(known))
        attempted = [r for r in rows if r["status"] != "NOT_RUN"]
        for field in MEASURE_FIELDS:
            values = [r["observations"][field] for r in attempted]
            known = [v for v in values if v is not None]
            metrics[f"mean_{field}"] = {"state": "MEASURED" if values and len(known) == len(values) else "UNKNOWN",
                "value": sum(known) / len(values) if values and len(known) == len(values) else None,
                "sum_recorded": sum(known), "denominator": len(values), "observed_n": len(known), "unknown_runs": len(values) - len(known)}
        out["systems"][system] = {"planned_n": n, "recorded_n": sum((r["system_id"] == system) for r in records), "status_counts": dict(status), "metrics": metrics}
    if any(r["status"] == "NOT_RUN" for r in cells.values()):
        reasons.append("计划单元尚未全部运行；不得比较总体性能")
    if out["benchmark_status"] != "NOT_RUN":
        out["comparison_status"] = "INCOMPARABLE" if reasons else "DESCRIPTIVE_ONLY"
    return out


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(f"非法 JSON 数值：{s}")))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ARC-Bench 离线证据对照：只验证/统计，不执行代理或调用 API")
    ap.add_argument("--root", type=Path, default=ROOT)
    sub = ap.add_subparsers(dest="command", required=True)
    create = sub.add_parser("freeze", help="从实际系统指纹和共享预算配置冻结计划")
    create.add_argument("--settings", type=Path, required=True, help="JSON: systems/model/budget/task_ids/seeds")
    create.add_argument("--output", type=Path, required=True)
    dry = sub.add_parser("dry-run", help="校验计划及输入哈希，生成 NOT_RUN 记录")
    dry.add_argument("--plan", type=Path, required=True)
    dry.add_argument("--output", type=Path, required=True)
    report = sub.add_parser("summarize", help="逐运行 JSON 数组 -> 含 n/UNKNOWN/不可比原因的 JSON")
    report.add_argument("--plan", type=Path, required=True)
    report.add_argument("--records", type=Path, required=True)
    report.add_argument("--evidence-root", type=Path)
    report.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        if args.command == "freeze":
            result = make_plan(**_load(args.settings), root=args.root)
        elif args.command == "dry-run":
            result = dry_run(_load(args.plan), root=args.root)
        else:
            result = summarize(_load(args.plan), _load(args.records), root=args.root, evidence_root=args.evidence_root)
        # Never overwrite a receipt or frozen plan silently.
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        print("离线检查完成；没有执行模型、实验、GPU 或外部命令。")
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"HOLD：{exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
