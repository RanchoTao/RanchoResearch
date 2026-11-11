"""Agent-drafted pre-registration for the v0.6 evidence gate.

Before Stage 12, a drafting agent reads the Stage 9 experiment design and the
Stage 10 code and proposes the claim and frozen protocol. The protocol's field
pointers are built deterministically from the evidence output contract that
Stage 10 is told to follow, so the agent only chooses scientific content
(claim, conditions, metric, direction, minimum effect).

Three modes (``experiment.protocol_author``):

- ``manual``: unchanged behaviour; a person writes research_evidence.json.
- ``agent_with_human_review``: the draft is written under evidence/drafts and
  the run pauses until ``ranchoresearch evidence RUN --approve-draft``.
- ``agent``: a reviewing agent with a distinct identity checks the draft; on
  approval it is installed and sealed and Stage 12 proceeds.

The draft is written before any Stage 12 output exists, so it cannot be fitted
to results. Identities are labels, not signatures.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from researchclaw.pipeline.evidence_gate import (BUNDLE, EvidenceError, _config_snapshot, compute_sha256,
                                                 seal_bundle)

MODES = ("manual", "agent", "agent_with_human_review")
RESULTS_PATH = "stage-12/runs/sandbox/_project_1/results.json"
DRAFTS = Path("evidence") / "drafts"

# Appended to the Stage 10 code-generation guidance (all domains).
OUTPUT_CONTRACT = (
    "\n\nEVIDENCE OUTPUT CONTRACT (REQUIRED, machine-checked before results count):\n"
    "results.json MUST contain these top-level keys, written by main.py from the actual runs:\n"
    '- "data_origin": "SYNTHETIC" if all data is generated in code, "REAL" if loaded from a real dataset\n'
    '- "n_samples": integer number of independent evaluation units (e.g. seeds x instances) behind the reported values\n'
    '- "valid": true only if every condition finished without NaN/Inf or errors, otherwise false\n'
    '- "metrics": {"<condition_name>": {"<metric_name>": <float>, ...}, ...} with one entry per condition,\n'
    '  including at least one simple, honest baseline condition whose name contains "baseline"\n'
    "Use plain condition names made of letters, digits, '_' or '-'. Never write a value you did not compute.\n"
)

_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")


def _identity(config: Any, role: str, model: str = "") -> str:
    llm = config.llm
    label = model or llm.primary_model or (getattr(getattr(llm, "acp", None), "agent", "") if llm.provider == "acp" else "")
    return f"{role}:{llm.provider}/{label or 'unknown-model'}"


def _reviewer_client(config: Any, llm: Any) -> tuple[Any, str]:
    model = getattr(config.experiment, "protocol_reviewer_model", "")
    if model and config.llm.provider != "acp":
        from researchclaw.llm.client import LLMClient
        client = LLMClient.from_rc_config(config)
        client.config.primary_model = model
        client.config.fallback_models = []
        return client, _identity(config, "protocol-reviewer", model)
    # Same model as the drafter: a different role and prompt, but not an
    # independent model. The label says so.
    return llm, _identity(config, "protocol-reviewer(same-model)")


def _context(run_dir: Path, config: Any) -> dict:
    from researchclaw.pipeline._helpers import _read_prior_artifact
    plan = _read_prior_artifact(run_dir, "exp_plan.yaml") or ""
    selected = _read_prior_artifact(run_dir, "experiment/")
    files: dict[str, str] = {}
    if selected and Path(selected).is_dir():
        for path in sorted(Path(selected).rglob("*.py")):
            if "__pycache__" not in path.parts:
                files[path.relative_to(run_dir).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    if not files:
        raise EvidenceError("找不到 Stage10 生成的实验代码，无法起草协议")
    return {"topic": config.research.topic, "plan": plan if isinstance(plan, str) else str(plan),
            "files": files, "metric_key": config.experiment.metric_key,
            "metric_direction": config.experiment.metric_direction}


def _code_block(ctx: dict, limit: int = 24000) -> str:
    parts, used = [], 0
    for name, text in ctx["files"].items():
        chunk = f"### {name}\n{text}\n"
        if used + len(chunk) > limit:
            parts.append(f"### {name}\n[truncated]\n")
            continue
        parts.append(chunk)
        used += len(chunk)
    return "\n".join(parts)


DRAFT_SYSTEM = (
    "You are pre-registering one falsifiable experimental claim BEFORE the experiment runs. "
    "You have not seen and must not guess any results. Be conservative: a weak but honest claim "
    "is better than an impressive one the code cannot test. Reply with one JSON object only."
)


def _draft_prompt(ctx: dict) -> str:
    return (
        f"Research topic: {ctx['topic']}\n\nExperiment plan (Stage 9):\n{ctx['plan'][:8000]}\n\n"
        f"Experiment code (Stage 10). main.py writes results.json with top-level data_origin, n_samples, "
        f"valid and metrics[<condition>][<metric>]:\n{_code_block(ctx)}\n\n"
        f"Configured primary metric: {ctx['metric_key']} ({ctx['metric_direction']}).\n\n"
        "Return JSON with exactly these keys:\n"
        '{"claim": {"definition": str, "scope": str, "research_value": str, "falsification": str, '
        '"known_work": [str]}, "proposed_condition": str, "baseline_condition": str, "metric": str, '
        '"direction": "maximize"|"minimize", "min_effect": number>0, "min_samples": int>=1, '
        '"measurement_method": str, "data_contract": str, "data_origin": "SYNTHETIC"|"REAL", '
        '"rationale": str}\n'
        "proposed_condition and baseline_condition must be condition names the code actually writes into "
        "metrics; metric must be a metric name it writes for both. The claim is that the proposed condition "
        "beats the baseline on that metric by at least min_effect in the stated direction."
    )


REVIEW_SYSTEM = (
    "You are an independent reviewer of a pre-registered experimental protocol. You did not write it. "
    "Approve only if it is honest and testable as written. Reply with one JSON object only."
)


def _review_prompt(ctx: dict, draft: dict) -> str:
    return (
        f"Research topic: {ctx['topic']}\n\nExperiment plan:\n{ctx['plan'][:6000]}\n\n"
        f"Experiment code:\n{_code_block(ctx, 16000)}\n\nProposed pre-registration:\n"
        f"{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        "Check each item and block approval if any fails: (1) the claim is falsifiable and matches the plan; "
        "(2) the baseline is a genuine simple baseline, not a straw man; (3) the direction is correct for the "
        "metric; (4) min_effect is a meaningful practical difference, not a trivially small number; "
        "(5) both conditions and the metric are really computed and written by the code; (6) data_origin "
        "matches how the code obtains data; (7) min_samples is achievable by the code.\n"
        'Return {"approve": bool, "issues": [str], "notes": str}.'
    )


def _ask_json(llm: Any, system: str, user: str) -> dict:
    from researchclaw.pipeline._helpers import _chat_with_prompt, _safe_json_loads
    resp = _chat_with_prompt(llm, system, user, json_mode=True, retries=1)
    text = getattr(resp, "content", resp)
    data = _safe_json_loads(text if isinstance(text, str) else str(text), None)
    if not isinstance(data, dict):
        raise EvidenceError("Agent 没有返回可解析的 JSON 协议草稿")
    return data


def static_check(ctx: dict, draft: dict) -> list[str]:
    """Deterministic sanity checks; any issue blocks automatic approval."""
    issues: list[str] = []
    code = "\n".join(ctx["files"].values())
    for key in ("data_origin", "n_samples", "valid", "metrics", "results.json"):
        if key not in code:
            issues.append(f"代码中找不到证据输出约定字段 {key!r}；需在新的代码生成约定下重新生成 Stage10")
    for key in ("proposed_condition", "baseline_condition", "metric"):
        value = draft.get(key)
        if not isinstance(value, str) or not _NAME.match(value):
            issues.append(f"{key} 缺失或含非法字符")
        elif value not in code:
            issues.append(f"{key}={value!r} 未在代码中出现，指针可能落空")
    if draft.get("proposed_condition") == draft.get("baseline_condition"):
        issues.append("候选与基线不能是同一个条件")
    if draft.get("direction") not in ("maximize", "minimize"):
        issues.append("direction 必须是 maximize 或 minimize")
    effect = draft.get("min_effect")
    if type(effect) not in (int, float) or not effect > 0:
        issues.append("min_effect 必须是正数")
    if type(draft.get("min_samples")) is not int or draft["min_samples"] < 1:
        issues.append("min_samples 必须是正整数")
    if draft.get("data_origin") not in ("SYNTHETIC", "REAL"):
        issues.append("data_origin 必须是 SYNTHETIC 或 REAL")
    claim = draft.get("claim")
    if not isinstance(claim, dict):
        issues.append("缺少 claim")
    else:
        for key in ("definition", "scope", "research_value", "falsification"):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                issues.append(f"claim.{key} 为空")
    for key in ("measurement_method", "data_contract"):
        if not isinstance(draft.get(key), str) or not draft[key].strip():
            issues.append(f"{key} 为空")
    if any("TODO" in json.dumps(v, ensure_ascii=False) for v in draft.values()):
        issues.append("草稿含 TODO 占位符")
    return issues


def _claim_id(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:40] or "claim"
    return f"claim_{slug}"


def build_files(config: Any, draft: dict, *, actor: str, reason: str) -> tuple[dict, dict, dict]:
    """Bundle, protocol and data statement from a checked draft."""
    proposed, baseline, metric = draft["proposed_condition"], draft["baseline_condition"], draft["metric"]
    claim_id = _claim_id(config.research.topic)
    protocol = {
        "claim_id": claim_id, "claim_version": 1, "purpose": "science",
        "scope_type": "fixed_finite_population",
        "execution_config": _config_snapshot(config),
        "measurement_method": draft["measurement_method"], "data_contract": draft["data_contract"],
        "origin_source": {"path": RESULTS_PATH, "pointer": "/data_origin"},
        "checks": [{"name": "all_conditions_valid", "path": RESULTS_PATH, "pointer": "/valid",
                    "op": "eq", "expected": True}],
        "metrics": {"proposed": {"path": RESULTS_PATH, "pointer": f"/metrics/{proposed}/{metric}"},
                    "simple_baseline": {"path": RESULTS_PATH, "pointer": f"/metrics/{baseline}/{metric}"}},
        "baselines": ["simple_baseline"],
        "sample_count": {"path": RESULTS_PATH, "pointer": "/n_samples"},
        "min_samples": int(draft["min_samples"]),
        "decision_rule": {"kind": "finite_computation", "metric": "proposed", "baseline": "simple_baseline",
                          "direction": draft["direction"], "min_effect": float(draft["min_effect"])},
    }
    claim = dict(draft["claim"])
    known = claim.get("known_work")
    bundle = {
        "schema_version": "0.6.0",
        "claim": {"claim_id": claim_id, "claim_version": 1, "definition": claim["definition"],
                  "scope": claim["scope"], "research_value": claim["research_value"],
                  "known_work": known if isinstance(known, list) else [],
                  "falsification": claim["falsification"],
                  "protocol": {"path": "protocol.json", "sha256": ""}},
        "inputs": {"code": "auto", "data": ["data_statement.json"], "configuration": ["execution_config.json"],
                   "data_origin": draft["data_origin"]},
        "authorization": {"actor": actor, "reason": reason, "allowed_modes": ["sandbox"],
                          "max_time_budget_sec": config.experiment.time_budget_sec,
                          "allow_exploration": bool(getattr(config.experiment, "allow_exploration", False))},
        "provenance": {"model": "NOT_RECORDED", "parameters": "NOT_RECORDED", "seed": "NOT_RECORDED",
                       "api_cost": "NOT_RECORDED", "gpu_cost": "NOT_RECORDED"},
        "test_exposure": "UNKNOWN", "review": {"novelty": "UNKNOWN"}, "papers": [],
    }
    data_statement = {"data_origin": draft["data_origin"], "data_contract": draft["data_contract"],
                      "note": "Data are produced or loaded by the frozen Stage 10 code; this file records the contract."}
    return bundle, protocol, data_statement


def write_draft(run_dir: Path, draft: dict, meta: dict) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = run_dir / DRAFTS / stamp
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "draft.json").write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return folder


def latest_draft(run_dir: Path) -> Path:
    drafts = sorted(p for p in (run_dir / DRAFTS).glob("*") if (p / "draft.json").is_file())
    if not drafts:
        raise EvidenceError("没有可批准的协议草稿")
    return drafts[-1]


def install(run_dir: Path, config: Any, draft_dir: Path, *, actor: str, reason: str) -> list[str]:
    """Write bundle/protocol/config/data files from a draft and seal them."""
    draft = json.loads((draft_dir / "draft.json").read_text(encoding="utf-8"))
    for name in (BUNDLE, "protocol.json"):
        if (run_dir / name).exists():
            raise EvidenceError(f"{name} 已存在，拒绝覆盖；修改请用 --seal --new-version")
    bundle, protocol, data_statement = build_files(config, draft, actor=actor, reason=reason)
    (run_dir / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "execution_config.json").write_text(json.dumps(_config_snapshot(config), indent=2), encoding="utf-8")
    (run_dir / "data_statement.json").write_text(json.dumps(data_statement, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")
    (run_dir / BUNDLE).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    _, warnings = seal_bundle(run_dir)
    meta_path = draft_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update({"installed_at": datetime.now(timezone.utc).isoformat(), "approved_by": actor,
                 "bundle_sha256": compute_sha256(run_dir / BUNDLE)})
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return warnings


def ensure_protocol(run_dir: Path, config: Any, llm: Any) -> tuple[bool, str]:
    """Called before Stage 12 when no bundle exists. Returns (proceed, message)."""
    mode = getattr(config.experiment, "protocol_author", "manual")
    if mode == "manual" or (run_dir / BUNDLE).exists():
        return True, ""
    if llm is None:
        return False, "协议起草需要可用的 LLM 客户端，但当前不可用"
    ctx = _context(run_dir, config)
    drafter = _identity(config, "protocol-drafter")
    draft = _ask_json(llm, DRAFT_SYSTEM, _draft_prompt(ctx))
    issues = static_check(ctx, draft)
    meta: dict[str, Any] = {"mode": mode, "drafter": drafter, "static_issues": issues,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "code_files": {name: compute_sha256(run_dir / name) for name in ctx["files"]}}
    if issues:
        folder = write_draft(run_dir, draft, meta)
        return False, ("协议草稿未通过静态检查，已保存到 " + folder.relative_to(run_dir).as_posix()
                       + "：\n- " + "\n- ".join(issues))
    if mode == "agent_with_human_review":
        folder = write_draft(run_dir, draft, meta)
        return False, ("协议草稿已生成：" + folder.relative_to(run_dir).as_posix()
                       + "/draft.json。审阅后运行 ranchoresearch evidence RUN_DIR --approve-draft 继续。")
    reviewer_llm, reviewer = _reviewer_client(config, llm)
    verdict = _ask_json(reviewer_llm, REVIEW_SYSTEM, _review_prompt(ctx, draft))
    meta["review"] = {"reviewer": reviewer, **verdict}
    folder = write_draft(run_dir, draft, meta)
    if verdict.get("approve") is not True or verdict.get("issues"):
        return False, ("审稿 Agent 未批准协议草稿（" + folder.relative_to(run_dir).as_posix() + "）：\n- "
                       + "\n- ".join(str(i) for i in (verdict.get("issues") or ["未给出批准"])))
    warnings = install(run_dir, config, folder, actor=reviewer,
                       reason=f"自动预注册：{drafter} 起草，{reviewer} 审查批准；依据 Stage9 设计与 Stage10 代码")
    if warnings:
        return False, "协议已安装但封存有警告：" + "；".join(warnings)
    return True, "协议由 Agent 起草并经独立审查后封存"
