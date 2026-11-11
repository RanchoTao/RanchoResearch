"""Research Evidence Runtime Gate: one fail-closed contract for the engine.

The MVP verifies local empirical/computational evidence. It does not certify
literature completeness, measurement semantics, causal identification, or
theory proofs. Those require source-backed review; unknown stays unknown.
"""
from __future__ import annotations

import json
import math
import platform
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path, PureWindowsPath
from typing import Any
from uuid import uuid4

from autoresearch_state.evidence import append_record, fingerprint, freeze_claim
from researchclaw.hitl.checksums import compute_sha256
from researchclaw.pipeline.verified_registry import VerifiedRegistry

BUNDLE = "research_evidence.json"
EXECUTION_STAGES = {12, 13}
SCIENCE_STAGES = {15, 16, 17, 18, 19, 20, 22, 23}
PAPER_STAGES = {20, 22, 23}
AXES = {
    "scientific_claim": ("SUPPORTED", "CONTRADICTED_IN_SCOPE", "INCONCLUSIVE", "NOT_TESTED"),
    "measurement_validity": ("VALID", "INVALID", "UNKNOWN"),
    "novelty": ("PLAUSIBLE_INCREMENT", "PARTIAL_OVERLAP", "EXACT_COLLISION", "THIN_CONTRIBUTION", "UNKNOWN"),
    "execution": ("PLANNED", "ACTIVE", "BLOCKED", "STOPPED", "ARCHIVED"),
    "paper_readiness": ("NOT_READY", "NEEDS_INDEPENDENT_CHECK", "READY_FOR_HUMAN_AUDIT"),
}


class EvidenceError(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise EvidenceError(f"非有限数值 {value}，测量无效")


def _unique_pairs(pairs: list) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"JSON 重复字段 {key}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant,
                      object_pairs_hook=_unique_pairs)


def local_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or PureWindowsPath(name).drive or PureWindowsPath(name).is_absolute():
        raise EvidenceError("证据必须使用 run_dir 内的相对路径")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise EvidenceError(f"证据缺失或越界：{name}")
    return path


def artifact(root: Path, ref: dict) -> Path:
    path = local_path(root, ref["path"])
    if not re.fullmatch(r"[a-f0-9]{64}", ref.get("sha256", "")):
        raise EvidenceError(f"证据缺少 SHA256：{ref['path']}")
    if compute_sha256(path) != ref["sha256"]:
        raise EvidenceError(f"证据哈希不一致：{ref['path']}")
    return path


def pointer(value: Any, expression: str) -> Any:
    if not isinstance(expression, str) or (expression and not expression.startswith("/")):
        raise EvidenceError("指标必须使用 JSON Pointer")
    for part in expression.split("/")[1:]:
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def finite(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _finite_tree(value: Any) -> None:
    if type(value) is float and not math.isfinite(value):
        raise EvidenceError("数值溢出/NaN/Inf，测量无效")
    if isinstance(value, dict):
        for child in value.values():
            _finite_tree(child)
    elif isinstance(value, list):
        for child in value:
            _finite_tree(child)


def load_bundle(root: Path) -> tuple[dict, dict]:
    bundle = read_json(root / BUNDLE)
    if bundle.get("schema_version") != "0.6.0":
        raise EvidenceError("证据契约版本缺失/不支持（要求 0.6.0）；旧档不自动升级")
    claim = bundle["claim"]
    for key in ("definition", "scope", "research_value", "falsification"):
        if not isinstance(claim.get(key), str) or not claim[key].strip():
            raise EvidenceError(f"主张缺少 {key}")
    if not isinstance(claim.get("known_work"), list):
        raise EvidenceError("known_work 必须记录来源；空列表只表示未记录，不证明原创")
    protocol = read_json(artifact(root, claim["protocol"]))
    if (protocol["claim_id"], protocol["claim_version"]) != (claim["claim_id"], claim["claim_version"]):
        raise EvidenceError("冻结协议与主张身份不一致")
    if protocol.get("purpose") not in {"science", "calibration"}:
        raise EvidenceError("协议必须区分 science 与 calibration")
    for key in ("measurement_method", "data_contract", "decision_rule"):
        if not protocol.get(key):
            raise EvidenceError(f"冻结协议缺少 {key}")
    if not protocol.get("checks") or not protocol.get("metrics"):
        raise EvidenceError("冻结协议必须将有效性条件映射到实际输出字段")
    if not isinstance(protocol.get("origin_source"), dict):
        raise EvidenceError("协议必须将数据来源标签绑定到实际输出 origin_source")
    if type(protocol.get("min_samples")) is not int or protocol["min_samples"] < 1:
        raise EvidenceError("min_samples 必须为正整数；非法样本规则不能作科学证伪")
    rule = protocol["decision_rule"]
    if rule.get("kind") not in {"finite_computation", "interval"}:
        raise EvidenceError("尚未实现此类判决，保留 UNKNOWN")
    if not finite(rule.get("min_effect")) or rule["min_effect"] <= 0:
        raise EvidenceError("须冻结正的最小实际增量")
    if rule["kind"] == "finite_computation":
        if rule.get("direction") not in {"maximize", "minimize"}:
            raise EvidenceError("direction 必须严格为 maximize/minimize，禁止默认反向造成误杀")
        if rule.get("baseline") not in protocol.get("baselines", []):
            raise EvidenceError("判决基线必须在冻结 baselines 中声明")
        if rule.get("metric") == rule.get("baseline"):
            raise EvidenceError("候选与基线指标不能用同一名称替代比较")
        if any(rule.get(key) not in protocol["metrics"] for key in ("metric", "baseline")):
            raise EvidenceError("判决引用不存在的指标")
    else:
        if any(rule.get(key) not in protocol["metrics"] for key in ("lower", "upper")):
            raise EvidenceError("区间判决须绑定实际上下界指标")
        if not rule.get("contrast_definition"):
            raise EvidenceError("区间必须定义相对简单基线的增量估计目标，不能用方法总收益替代")
    _finite_tree(bundle)
    _finite_tree(protocol)
    return bundle, protocol


def input_hashes(root: Path, bundle: dict) -> dict[str, str]:
    inputs = bundle["inputs"]
    hashes = {bundle["claim"]["protocol"]["path"]: bundle["claim"]["protocol"]["sha256"]}
    for key in ("code", "data", "configuration"):
        refs = inputs[key]
        if not isinstance(refs, list) or not refs:
            raise EvidenceError(f"输入 {key} 不能为空；不适用须提供说明工件")
        for ref in refs:
            artifact(root, ref)
            hashes[ref["path"]] = ref["sha256"]
    if inputs.get("data_origin") not in {"REAL", "SYNTHETIC", "NOT_APPLICABLE"}:
        raise EvidenceError("必须声明数据为 REAL/SYNTHETIC/NOT_APPLICABLE，不能混称")
    return hashes


def _config_snapshot(config: Any) -> dict:
    exp = config.experiment
    # Never serialize provider credentials or machine-local python paths.
    return {"mode": exp.mode, "time_budget_sec": exp.time_budget_sec,
            "max_iterations": exp.max_iterations, "metric_key": exp.metric_key,
            "metric_direction": exp.metric_direction}


def preflight(root: Path, config: Any, stage: int) -> dict:
    bundle, protocol = load_bundle(root)
    hashes = input_hashes(root, bundle)
    snapshot = _config_snapshot(config)
    if snapshot["mode"] != "sandbox":
        raise EvidenceError("本轮真实收据仅验证 sandbox；Docker 可能回退本机，远程及领域代理保持 HOLD")
    permission = bundle["authorization"]
    if not permission.get("actor") or not permission.get("reason"):
        raise EvidenceError("执行前缺少可追溯授权人/授权范围说明")
    if snapshot["mode"] not in permission["allowed_modes"]:
        raise EvidenceError("实际执行模式不在明确授权范围内")
    if stage == 13:
        # The old optimizer can change code/protocol and call remote models.
        # The bounded MVP does not claim to supervise all its internal jobs.
        raise EvidenceError("迭代优化尚未逐子任务记录冻结收据；请创建新版本后受控执行 Stage12")
    limit = permission["max_time_budget_sec"]
    if not finite(limit) or not 0 < snapshot["time_budget_sec"] <= limit:
        raise EvidenceError("实际执行时间配置超出授权上限")
    if protocol["execution_config"] != snapshot:
        raise EvidenceError("实际执行配置与冻结协议不一致")
    # Bind the engine's actual selected source, not an unrelated approved file.
    from researchclaw.pipeline._helpers import _read_prior_artifact
    selected = _read_prior_artifact(root, "experiment/")
    approved = {ref["path"]: ref["sha256"] for ref in bundle["inputs"]["code"]}
    if selected and Path(selected).is_dir():
        actual = {p.relative_to(root).as_posix(): compute_sha256(p)
                  for p in Path(selected).rglob("*") if p.is_file()}
        if not actual or any(approved.get(name) != digest for name, digest in actual.items()):
            raise EvidenceError("实际选中的实验目录含未冻结/改变的文件")
    else:
        source = _read_prior_artifact(root, "experiment.py")
        if not source or not any(local_path(root, name).read_text(encoding="utf-8") == source for name in approved):
            raise EvidenceError("实际选中的 experiment.py 未绑定冻结输入")
    frozen = {**bundle["claim"], "input_fingerprint": fingerprint(hashes),
              "data_origin": bundle["inputs"]["data_origin"]}
    freeze_claim(root, frozen)
    # Preserve frozen input bytes, including failed attempts, outside stage dirs.
    for name, digest in hashes.items():
        stored = root / "evidence" / "blobs" / digest
        stored.parent.mkdir(parents=True, exist_ok=True)
        if stored.exists():
            if compute_sha256(stored) != digest:
                raise EvidenceError("已保存输入工件被修改")
        else:
            with stored.open("xb") as stream:
                stream.write(local_path(root, name).read_bytes())
    return {"claim_id": frozen["claim_id"], "claim_version": frozen["claim_version"],
            "claim_fingerprint": fingerprint(frozen), "inputs": hashes,
            "config": snapshot, "authorization": permission,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "monotonic_start": time.monotonic()}


def exploration_preflight(root: Path, config: Any) -> dict:
    """Authorize Stage13 as *exploration only*; it can never produce evidence.

    The optimizer may rewrite code and call remote models, so its output is not
    bound to a frozen claim. It runs only when explicitly authorized and its
    record is stored under ``evidence/explorations``; ``evaluate`` accepts only
    Stage12 receipts. To adopt improved code, seal a new claim version and
    re-run Stage12.
    """
    bundle, _protocol = load_bundle(root)
    snapshot = _config_snapshot(config)
    permission = bundle["authorization"]
    if not permission.get("allow_exploration"):
        raise EvidenceError("未授权 Stage13 探索性优化（authorization.allow_exploration 未设为 true）")
    if not permission.get("actor") or not permission.get("reason"):
        raise EvidenceError("执行前缺少可追溯授权人/授权范围说明")
    if snapshot["mode"] != "sandbox" or snapshot["mode"] not in permission["allowed_modes"]:
        raise EvidenceError("探索性优化仅允许已授权的 sandbox 模式")
    limit = permission["max_time_budget_sec"]
    if not finite(limit) or not 0 < snapshot["time_budget_sec"] <= limit:
        raise EvidenceError("实际执行时间配置超出授权上限")
    return {"claim_id": bundle["claim"]["claim_id"], "claim_version": bundle["claim"]["claim_version"],
            "purpose": "exploration_not_evidence", "config": snapshot, "authorization": permission,
            "started_at": datetime.now(timezone.utc).isoformat(), "monotonic_start": time.monotonic()}


def preserve_prior_stage(root: Path, stage_dir: Path) -> None:
    """Keep previous files, but never stamp pre-existing results as new output."""
    if not stage_dir.exists():
        return
    if stage_dir.is_symlink() or not stage_dir.resolve().is_relative_to(root.resolve()):
        raise EvidenceError("执行目录为链接或越界，拒绝覆盖")
    if not stage_dir.is_dir():
        raise EvidenceError("执行阶段路径不是目录")
    if any(stage_dir.iterdir()):
        target = root / "evidence" / "unbound_prior" / uuid4().hex / stage_dir.name
        target.parent.mkdir(parents=True, exist_ok=False)
        stage_dir.rename(target)


def finish_execution(root: Path, stage_dir: Path, ticket: dict, status: str, *, stage: int = 12) -> Path:
    """Called only around the actual executor, never around HITL SKIP.

    Stage12 writes an evidence receipt. Stage13 (exploration) writes an
    exploration record that ``evaluate`` never accepts as evidence.
    """
    receipt = dict(ticket)
    elapsed = time.monotonic() - receipt.pop("monotonic_start")
    outputs = {}
    locations = {}
    attempt = uuid4().hex
    for path in sorted(stage_dir.rglob("*")):
        if path.is_file():
            name = path.relative_to(root).as_posix()
            digest = compute_sha256(path)
            stored = root / "evidence" / "attempts" / attempt / name
            stored.parent.mkdir(parents=True, exist_ok=True)
            with stored.open("xb") as stream:
                stream.write(path.read_bytes())
            if compute_sha256(stored) != digest:
                raise EvidenceError("保存原始实验输出时发生变化")
            outputs[name] = digest
            locations[name] = stored.relative_to(root).as_posix()
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parents[2],
                                  capture_output=True, text=True, timeout=5, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        revision = "NOT_RECORDED"
    exploratory = stage != 12
    receipt.update({"observer": ("researchclaw.execute_stage/v0.6-exploration" if exploratory
                                 else "researchclaw.execute_stage/v0.6"), "stage": stage,
                    "status": status, "outputs": outputs, "output_snapshot": locations, "elapsed_sec": elapsed,
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "environment": {"python": sys.version.split()[0], "platform": platform.system()},
                    "engine_commit": revision or "NOT_RECORDED",
                    "resource_cost": {"wall_seconds": elapsed, "api_cost": "NOT_RECORDED",
                                      "gpu_seconds": "NOT_RECORDED"}})
    return append_record(root, "explorations" if exploratory else "receipts", receipt)


@dataclass
class GateReport:
    review_allowed: bool = False
    promotion_allowed: bool = False
    paper_allowed: bool = False
    claim_id: str = "UNKNOWN"
    claim_version: int | None = None
    axes: dict = field(default_factory=lambda: {
        "scientific_claim": "NOT_TESTED", "measurement_validity": "UNKNOWN", "novelty": "UNKNOWN",
        "execution": "BLOCKED", "paper_readiness": "NOT_READY"})
    reasons: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    explanation: dict = field(default_factory=dict)
    decision: str = "HOLD"
    evidence_refs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        self.explanation = {
            "scientific_claim": "仅针对冻结主张及适用范围；工程或校准成功不替代科学实验。",
            "measurement_validity": "依据原始运行、哈希、有效性检查和样本门；领域语义仍需审查。",
            "novelty": "只记录有来源的逐主张文献审查，未检索到不等于原创。",
            "execution": "记录实际观察到的执行；异常与资源不足不作科学证伪。",
            "paper_readiness": "本地真实性审核不授权投稿/公开发布；独立性和人工审核另行记录。",
        }
        return dict(vars(self))


def _source(root: Path, spec: dict, hashes: dict, locations: dict | None = None) -> Any:
    name = spec["path"]
    if name not in hashes:
        raise EvidenceError(f"指标来源不在原始执行/冻结输入收据中：{name}")
    path = artifact(root, {"path": (locations or {}).get(name, name), "sha256": hashes[name]})
    data = read_json(path)
    _finite_tree(data)
    return pointer(data, spec["pointer"])


def _same_identity(left: Any, right: Any) -> bool:
    """Plain-label comparison. Not a signature: it only blocks literal self-review."""
    norm = lambda value: re.sub(r"\s+", "", str(value or "")).casefold()
    return bool(norm(left)) and norm(left) == norm(right)


def _compare(value: Any, op: str, expected: Any) -> bool:
    if op == "eq":
        return type(value) is type(expected) and value == expected
    if not finite(value) or not finite(expected):
        raise EvidenceError("数值检查字段不是有限数")
    if op == "ge":
        return value >= expected
    if op == "le":
        return value <= expected
    raise EvidenceError(f"未实现的冻结检查操作 {op}")


def _bound_papers(root: Path, bundle: dict, hashes: dict, papers: list[str], locations: dict) -> None:
    """Every numeric token needs an exact location and explicit source.

    Reuse the upstream tokenizer, not its permissive constant whitelist. This
    conservative contract may HOLD normal prose until source bindings are added.
    """
    from researchclaw.pipeline.paper_verifier import _NUMBER_RE
    entries = {item["path"]: item for item in bundle.get("papers", [])}
    for name in papers:
        entry = entries.get(name)
        if entry is None:
            raise EvidenceError(f"论文没有数值绑定清单：{name}")
        path = artifact(root, entry)
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?<![A-Za-z])(?:nan|[+-]?inf(?:inity)?)(?![A-Za-z])", text, re.IGNORECASE):
            raise EvidenceError("论文含 NaN/Inf 非法结果，必须明确修正后再审核")
        bindings = entry.get("bindings", [])
        by_start = {item["start"]: item for item in bindings}
        matches = list(_NUMBER_RE.finditer(text))
        if len(by_start) != len(bindings) or set(by_start) != {m.start() for m in matches}:
            raise EvidenceError(f"论文数值绑定有遗漏/重复/失效：{name}")
        registry = VerifiedRegistry()
        for match in matches:
            binding = by_start[match.start()]
            if binding["token"] != match.group():
                raise EvidenceError("论文绑定位置与文本不一致")
            value = _source(root, binding["source"], hashes, locations)
            if not finite(value):
                raise EvidenceError("论文数字的来源不是有限数值")
            transformed = Decimal(str(value)) * Decimal(str(binding.get("scale", 1)))
            if "decimals" in binding:
                decimals = binding["decimals"]
                if type(decimals) is not int or not 0 <= decimals <= 12:
                    raise EvidenceError("论文四舍五入精度非法")
                transformed = transformed.quantize(Decimal(1).scaleb(-decimals))
            if Decimal(match.group()) != transformed:
                raise EvidenceError(f"论文数字与指定来源不一致：{match.group()}")
            registry.add_value(float(transformed), f"{binding['source']['path']}#{binding['source']['pointer']}")
        if any(not registry.is_verified(float(m.group()), tolerance=0) for m in matches):
            raise EvidenceError("论文数值未通过 VerifiedRegistry")


def evaluate(root: Path, *, papers: list[str] | None = None) -> GateReport:
    report = GateReport()
    try:
        bundle, protocol = load_bundle(root)
        claim = bundle["claim"]
        report.claim_id, report.claim_version = claim["claim_id"], claim["claim_version"]
        inputs = input_hashes(root, bundle)
        report.provenance = {key: bundle.get("provenance", {}).get(key, "NOT_RECORDED")
                             for key in ("model", "parameters", "seed", "api_cost", "gpu_cost")}
        frozen = {**claim, "input_fingerprint": fingerprint(inputs), "data_origin": bundle["inputs"]["data_origin"]}
        # Evaluate never creates a frozen preflight retroactively.
        from autoresearch_state.evidence import claim_path
        recorded = read_json(claim_path(root, report.claim_id, report.claim_version))
        if recorded != frozen:
            raise EvidenceError("主张版本/输入与实验前冻结快照不一致")
        receipts = []
        for path in sorted((root / "evidence" / "receipts").glob("*.json")):
            receipt = read_json(path)
            if receipt.get("claim_fingerprint") == fingerprint(frozen):
                receipts.append((path, receipt))
        if not receipts:
            raise EvidenceError("没有实验前冻结且由执行器观察的真实运行收据；报告不等于实验")
        # One explicit receipt avoids silently choosing best or merging attempts.
        # With exactly one receipt for this frozen version there is nothing to
        # choose from, so it is used without a manual step.
        selected = bundle.get("receipt")
        if selected is None and len(receipts) == 1:
            selected = receipts[0][0].relative_to(root).as_posix()
            report.reasons.append("该主张版本只有一个执行收据，已自动选用（无挑选空间）。")
        elif selected is None:
            raise EvidenceError(f"该主张版本有 {len(receipts)} 个执行收据；必须显式选择一个，禁止自动挑最佳"
                                "（ranchoresearch evidence RUN_DIR --select-receipt PATH）")
        matches = [(p, r) for p, r in receipts if p.relative_to(root).as_posix() == selected]
        if len(matches) != 1:
            raise EvidenceError("必须显式选择一个该主张版本的 receipt；禁止混合/自动挑最佳")
        path, receipt = matches[0]
        report.evidence_refs.append(path.relative_to(root).as_posix())
        report.provenance["observed_execution"] = {key: receipt.get(key, "NOT_RECORDED") for key in
            ("started_at", "ended_at", "elapsed_sec", "engine_commit", "environment", "inputs", "output_snapshot", "resource_cost", "authorization")}
        if receipt["observer"] != "researchclaw.execute_stage/v0.6" or receipt["stage"] != 12:
            raise EvidenceError("不支持的执行观察者/阶段")
        if receipt["config"]["mode"] == "simulated":
            raise EvidenceError("模拟流水线结果不能表示为真实实验")
        if receipt["config"]["mode"] != "sandbox":
            raise EvidenceError("未验证的实际后端，不能晋级科学状态")
        if receipt["status"] != "done":
            raise EvidenceError("实验执行异常/资源阻塞；科学命题仍未解决")
        if receipt["inputs"] != inputs or receipt["config"] != protocol["execution_config"]:
            raise EvidenceError("收据中的输入/配置与冻结协议不一致")
        hashes = {**inputs, **receipt["outputs"]}
        locations = receipt["output_snapshot"]
        if set(locations) != set(receipt["outputs"]):
            raise EvidenceError("收据没有完整的不可覆盖原始输出快照")
        for name, digest in receipt["outputs"].items():
            artifact(root, {"path": locations[name], "sha256": digest})
        for name, digest in inputs.items():
            artifact(root, {"path": name, "sha256": digest})
        report.axes["execution"] = "STOPPED"
        # A sandbox copies inputs into its workspace before running. Merely
        # observing that copied file there is not an experimental measurement.
        measurement_outputs = {name: digest for name, digest in receipt["outputs"].items()
                               if digest not in set(inputs.values())}
        raw_runs = [name for name in receipt["outputs"]
                    if re.fullmatch(r"stage-12/runs/run-[^/]+\.json", name)]
        if not raw_runs:
            raise EvidenceError("没有可核验的原始 run 状态/输出，摘要不能代替原始运行")
        for name in raw_runs:
            raw = read_json(local_path(root, locations[name]))
            _finite_tree(raw)
            if raw.get("status") != "completed" or raw.get("timed_out") or raw.get("error"):
                report.axes["execution"] = "BLOCKED"
                raise EvidenceError("原始实验未完整成功；异常/超时不构成科学证伪")
        origin = _source(root, protocol["origin_source"], measurement_outputs, locations)
        if origin != bundle["inputs"]["data_origin"]:
            report.axes["measurement_validity"] = "INVALID"
            raise EvidenceError("数据合同来源不一致：实际输出 REAL/SYNTHETIC 标签与冻结输入矛盾")
        for check in protocol["checks"]:
            if not _compare(_source(root, check, measurement_outputs, locations), check["op"], check["expected"]):
                report.axes["measurement_validity"] = "INVALID"
                raise EvidenceError(f"冻结有效性/数据合同未满足：{check['name']}")
        for name, spec in protocol["metrics"].items():
            value = _source(root, spec, measurement_outputs, locations)
            if not finite(value):
                report.axes["measurement_validity"] = "INVALID"
                raise EvidenceError(f"指标 {name} 非有限数值")
            if ("min" in spec and value < spec["min"]) or ("max" in spec and value > spec["max"]):
                report.axes["measurement_validity"] = "INVALID"
                raise EvidenceError(f"指标 {name} 越界")
            report.metrics[name] = value
            report.sources[name] = {**spec, "sha256": hashes[spec["path"]], "snapshot_path": locations[spec["path"]]}
        n = _source(root, protocol["sample_count"], measurement_outputs, locations)
        if type(n) is not int or n < protocol["min_samples"]:
            raise EvidenceError("有效独立样本不足；不能作出强科学结论，也不能据此 KILL")
        report.axes["measurement_validity"] = "VALID"
        report.review_allowed = True
        if protocol["purpose"] == "calibration":
            report.reasons.append("测量校准通过，主科学实验未执行；科学状态仍 NOT_TESTED。")
        else:
            rule = protocol["decision_rule"]
            baselines = protocol.get("baselines", [])
            if not baselines or any(name not in report.metrics for name in baselines):
                raise EvidenceError("缺少冻结的简单基线，禁止将总收益归因为新机制")
            if rule["kind"] == "finite_computation":
                if protocol.get("scope_type") != "fixed_finite_population":
                    raise EvidenceError("确定性判决只能用于明确的固定有限对象，不能外推总体")
                metric = report.metrics[rule["metric"]]
                baseline = report.metrics[rule["baseline"]]
                delta = (metric - baseline) * (1 if rule["direction"] == "maximize" else -1)
                lower = upper = delta
            elif rule["kind"] == "interval":
                lower, upper = report.metrics[rule["lower"]], report.metrics[rule["upper"]]
                if lower > upper:
                    report.axes["measurement_validity"] = "INVALID"
                    raise EvidenceError("统计区间上下界错位")
            else:
                raise EvidenceError("尚未实现此类科学判决；保留 UNKNOWN，需领域审查")
            threshold = rule["min_effect"]
            if not finite(threshold) or threshold <= 0:
                raise EvidenceError("须冻结正的最小实际增量")
            report.axes["scientific_claim"] = ("SUPPORTED" if lower >= threshold else
                "CONTRADICTED_IN_SCOPE" if upper < threshold else "INCONCLUSIVE")
            report.promotion_allowed = True
            report.reasons.append(f"冻结范围内增量区间 [{lower}, {upper}]，阈值 {threshold}；不作范围外推。")
        review = bundle.get("review", {})
        novelty = review.get("novelty", "UNKNOWN")
        if novelty not in AXES["novelty"]:
            raise EvidenceError("非法原创性标签")
        if novelty != "UNKNOWN":
            artifact(root, review["source"])
            if not review.get("reviewer") or not review.get("explanation_zh"):
                raise EvidenceError("原创性审查缺审核者及中文作用域解释")
            if _same_identity(review["reviewer"], bundle["authorization"].get("actor")):
                raise EvidenceError("原创性审核者不能是执行授权人本身（自审无效）")
            if novelty == "EXACT_COLLISION" and not review.get("collision_scope"):
                raise EvidenceError("精确先例必须注明覆盖范围，不能由部分相关工作推断")
            report.axes["novelty"] = novelty
            report.reasons.append(review["explanation_zh"])
        independent = review.get("independent_check") == "PASSED"
        if independent:
            artifact(root, review["independent_source"])
            checker = review.get("independent_reviewer")
            if not checker:
                raise EvidenceError("独立复核必须记录 independent_reviewer（另一模型/进程/人员的身份）")
            if _same_identity(checker, bundle["authorization"].get("actor")):
                raise EvidenceError("独立复核者不能是执行授权人本身；同一 Agent 自己复核不算独立")
        exposed = bundle.get("test_exposure", "UNKNOWN")
        if exposed not in {"UNEXPOSED", "EXPOSED", "UNKNOWN", "NOT_APPLICABLE"}:
            raise EvidenceError("缺少可识别的测试集曝光状态")
        if exposed in {"EXPOSED", "UNKNOWN"}:
            independent = False
            report.reasons.append("测试集已曝光或历史未知：仅探索性结果，不计独立确认。")
        report.axes["paper_readiness"] = ("NEEDS_INDEPENDENT_CHECK" if report.promotion_allowed else "NOT_READY")
        if papers:
            _bound_papers(root, bundle, hashes, papers, locations)
            report.paper_allowed = (report.promotion_allowed and independent and
                novelty in {"PLAUSIBLE_INCREMENT", "PARTIAL_OVERLAP"})
            if report.paper_allowed:
                report.axes["paper_readiness"] = "READY_FOR_HUMAN_AUDIT"
            else:
                report.reasons.append("尚不满足独立复核/原创性审查条件，不能交付可信论文。")
        report.decision = ("KILL" if report.axes["scientific_claim"] == "CONTRADICTED_IN_SCOPE" else
                           "GO" if report.paper_allowed else "HOLD")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, ArithmeticError) as exc:
        report.review_allowed = report.promotion_allowed = report.paper_allowed = False
        report.decision = "HOLD"
        if isinstance(exc, EvidenceError) and any(word in str(exc) for word in ("NaN", "Inf", "非有限", "溢出")):
            report.axes["measurement_validity"] = "INVALID"
        if report.axes["measurement_validity"] != "VALID":
            report.axes["scientific_claim"] = "NOT_TESTED"
        report.reasons.append(f"证据门暂停：{type(exc).__name__}: {exc}")
    report.as_dict()
    return report


def persist_report(root: Path, report: GateReport, *, stage: int, phase: str) -> Path:
    return append_record(root, "decisions", {"stage": stage, "phase": phase, **report.as_dict()})


def paper_paths(root: Path, stage: int, *, after: bool) -> list[str]:
    if stage not in PAPER_STAGES:
        return []
    if (after and stage == 22) or stage == 23:
        candidates = [root / "stage-22" / name for name in ("paper.tex", "paper_final.md", "paper_final_latex.md")]
        if after and stage == 23:
            candidates.append(root / "stage-23" / "paper_final_verified.md")
        candidates = [p for p in candidates if p.is_file()]
    else:
        candidates = [root / "stage-19" / "paper_revised.md", root / "stage-17" / "paper_draft.md"]
        candidates = [p for p in candidates if p.is_file()][:1]
    if not candidates:
        raise EvidenceError("论文真实性检查找不到实际论文文件")
    return [p.relative_to(root).as_posix() for p in candidates]


def stage_report(root: Path, stage: int, *, after: bool = False) -> GateReport:
    try:
        return evaluate(root, papers=paper_paths(root, stage, after=after))
    except (OSError, ValueError) as exc:
        report = GateReport(reasons=[f"论文证据门暂停：{exc}"])
        report.as_dict()
        return report


def render_zh(root: Path, report: GateReport) -> str:
    try:
        bundle = read_json(root / BUNDLE)
        claim = bundle.get("claim", {})
    except (OSError, ValueError):
        claim = {}
    lines = [f"研究目标：{claim.get('definition', '未记录')} ({report.claim_id}/v{report.claim_version})",
             f"研究意义：{claim.get('research_value', '未记录')}",
             "当前进度：" + ("已核对实际执行收据及冻结协议" if report.review_allowed else "证据未满足运行门要求"),
             f"证据情况：{len(report.sources)} 个有原始来源的指标；收据 {report.evidence_refs}",
             f"工程状态：{report.axes['execution']}；软件测试不替代科学成立。"]
    for axis, value in report.axes.items():
        lines.append(f"{axis}: {value} — {report.explanation.get(axis, '')}")
    lines += ["剩余问题：" + "；".join(report.reasons),
              "下一步行动：补齐最早缺失的冻结协议/原始来源/独立复核；保留全部失败资料。",
              f"操作判断：{report.decision}（仅此主张版本；不授权发表或扩大计算）"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bundle preparation helpers (used by ``ranchoresearch evidence --seal``).
# They only compute hashes of files that already exist; they never invent
# claims, protocols, metrics or review results.
# ---------------------------------------------------------------------------

TEMPLATE_MARK = "TODO"


def _selected_code_refs(root: Path) -> list[dict]:
    from researchclaw.pipeline._helpers import _find_prior_file, _read_prior_artifact
    selected = _read_prior_artifact(root, "experiment/")
    if selected and Path(selected).is_dir():
        files = sorted(p for p in Path(selected).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    else:
        found = _find_prior_file(root, "experiment.py")
        files = [found] if found else []
    if not files:
        raise EvidenceError("找不到实际选中的实验代码（stage-*/experiment/ 或 experiment.py）；请先完成 Stage10")
    return [{"path": p.relative_to(root).as_posix(), "sha256": compute_sha256(p)} for p in files]


def _contains_todo(value: Any) -> bool:
    if isinstance(value, str):
        return TEMPLATE_MARK in value
    if isinstance(value, dict):
        return any(_contains_todo(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_todo(v) for v in value)
    return False


def write_template(root: Path) -> list[Path]:
    """Write fill-in templates; refuse to overwrite anything."""
    bundle_path, protocol_path = root / BUNDLE, root / "protocol.json"
    for path in (bundle_path, protocol_path):
        if path.exists():
            raise EvidenceError(f"{path.name} 已存在，拒绝覆盖")
    protocol = {
        "claim_id": "claim_TODO", "claim_version": 1, "purpose": "science",
        "scope_type": "fixed_finite_population",
        "execution_config": {"mode": "sandbox", "time_budget_sec": 300, "max_iterations": 1,
                             "metric_key": "primary_metric", "metric_direction": "maximize"},
        "measurement_method": "TODO: 测量方法", "data_contract": "TODO: 数据合同",
        "origin_source": {"path": "stage-12/runs/TODO.json", "pointer": "/data_origin"},
        "checks": [{"name": "TODO", "path": "stage-12/runs/TODO.json", "pointer": "/TODO", "op": "eq", "expected": True}],
        "metrics": {"proposed": {"path": "stage-12/runs/TODO.json", "pointer": "/TODO"},
                    "simple_baseline": {"path": "stage-12/runs/TODO.json", "pointer": "/TODO"}},
        "baselines": ["simple_baseline"],
        "sample_count": {"path": "stage-12/runs/TODO.json", "pointer": "/n"}, "min_samples": 1,
        "decision_rule": {"kind": "finite_computation", "metric": "proposed", "baseline": "simple_baseline",
                          "direction": "maximize", "min_effect": 0.01}}
    bundle = {"schema_version": "0.6.0", "claim": {
        "claim_id": "claim_TODO", "claim_version": 1, "definition": "TODO: 可检验陈述",
        "scope": "TODO: 适用范围", "research_value": "TODO: 研究价值", "known_work": [],
        "falsification": "TODO: 什么结果会推翻它", "protocol": {"path": "protocol.json", "sha256": ""}},
        "inputs": {"code": "auto", "data": [], "configuration": [], "data_origin": "TODO: REAL/SYNTHETIC/NOT_APPLICABLE"},
        "authorization": {"actor": "TODO: 执行授权人", "reason": "TODO: 授权范围", "allowed_modes": ["sandbox"],
                          "max_time_budget_sec": 300, "allow_exploration": False},
        "provenance": {"model": "NOT_RECORDED", "parameters": "NOT_RECORDED", "seed": "NOT_RECORDED",
                       "api_cost": "NOT_RECORDED", "gpu_cost": "NOT_RECORDED"},
        "test_exposure": "UNKNOWN", "review": {"novelty": "UNKNOWN"}, "papers": []}
    for path, data in ((protocol_path, protocol), (bundle_path, bundle)):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return [bundle_path, protocol_path]


def seal_bundle(root: Path, *, new_version_reason: str | None = None) -> tuple[dict, list[str]]:
    """Recompute SHA256 for protocol/code/data/config refs of research_evidence.json.

    ``inputs.code == "auto"`` binds the code the engine will actually select.
    With ``new_version_reason`` the claim version is bumped (old version kept)
    and the receipt choice is cleared. Returns the bundle and warnings.
    """
    bundle = read_json(root / BUNDLE)
    warnings: list[str] = []
    if _contains_todo(bundle) or _contains_todo(read_json(local_path(root, bundle["claim"]["protocol"]["path"]))):
        raise EvidenceError("证据包或协议仍含 TODO 占位符；请先填写真实内容")
    claim = bundle["claim"]
    if new_version_reason:
        if not new_version_reason.strip():
            raise EvidenceError("新版本必须给出 revision_reason")
        protocol_file = local_path(root, claim["protocol"]["path"])
        protocol = read_json(protocol_file)
        claim["claim_version"] += 1
        claim["revision_reason"] = new_version_reason.strip()
        protocol["claim_version"] = claim["claim_version"]
        protocol_file.write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8")
        bundle.pop("receipt", None)
    claim["protocol"] = {"path": claim["protocol"]["path"],
                         "sha256": compute_sha256(local_path(root, claim["protocol"]["path"]))}
    inputs = bundle["inputs"]
    if inputs.get("code") in ("auto", None, []):
        inputs["code"] = _selected_code_refs(root)
    for key in ("code", "data", "configuration"):
        refs = inputs.get(key)
        if not isinstance(refs, list) or not refs:
            raise EvidenceError(f"inputs.{key} 不能为空；不适用时请指向一个说明文件")
        inputs[key] = [{"path": ref["path"] if isinstance(ref, dict) else ref,
                        "sha256": compute_sha256(local_path(root, ref["path"] if isinstance(ref, dict) else ref))}
                       for ref in refs]
    (root / BUNDLE).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    from autoresearch_state.evidence import claim_path
    try:
        frozen_path = claim_path(root, claim["claim_id"], claim["claim_version"])
    except ValueError as exc:
        raise EvidenceError(str(exc)) from exc
    if frozen_path.is_file():
        hashes = input_hashes(root, bundle)
        frozen = {**claim, "input_fingerprint": fingerprint(hashes), "data_origin": inputs["data_origin"]}
        if read_json(frozen_path) != frozen:
            warnings.append("该版本已在执行前冻结且内容已变化；Stage12 会拒绝。请用 --new-version 说明原因后再执行。")
    load_bundle(root)  # full structural validation of the sealed result
    return bundle, warnings


def select_receipt(root: Path, receipt: str) -> None:
    bundle = read_json(root / BUNDLE)
    path = local_path(root, receipt)
    if not path.is_relative_to((root / "evidence" / "receipts").resolve()):
        raise EvidenceError("只能选择 evidence/receipts/ 下的执行收据")
    bundle["receipt"] = path.relative_to(root.resolve()).as_posix()
    (root / BUNDLE).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
