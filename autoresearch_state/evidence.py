"""Additive, immutable claim revisions and evidence decisions for v0.1 states.

This file store supplements existing IDs/checkpoints; it never migrates or
rewrites historical state. Local files are an audit trail, not a signature or
a security boundary against an actor who can rewrite the whole run directory.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def claim_path(root: Path, claim_id: str, version: int) -> Path:
    if not re.fullmatch(r"claim_[A-Za-z0-9_-]+", claim_id):
        raise ValueError("claim_id 必须是稳定的 claim_ 标识，不能使用论文标题")
    if type(version) is not int or version < 1:
        raise ValueError("claim_version 必须是正整数")
    return root / "evidence" / "claims" / claim_id / f"v{version}.json"


def freeze_claim(root: Path, claim: dict) -> Path:
    """Create once; changed scope/protocol requires an explicit new revision."""
    path = claim_path(root, claim["claim_id"], claim["claim_version"])
    payload = canonical(claim)
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise ValueError("同一 claim_id/version 已冻结，禁止覆盖；请创建带理由的新版本")
        return path
    if claim["claim_version"] > 1:
        previous = claim_path(root, claim["claim_id"], claim["claim_version"] - 1)
        if not previous.is_file() or not claim.get("revision_reason"):
            raise ValueError("新版本必须保留上一版本，并记录 revision_reason（含纠错/撤销范围）")
    parent = claim.get("parent")
    if parent and not claim_path(root, parent["claim_id"], parent["claim_version"]).is_file():
        raise ValueError("研究分支的 parent 版本不存在")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != payload:
            raise ValueError("并发写入了冲突的主张版本") from None
    return path


def append_record(root: Path, kind: str, payload: dict) -> Path:
    if kind not in {"decisions", "receipts", "explorations"}:
        raise ValueError("unsupported evidence record kind")
    folder = root / "evidence" / kind
    folder.mkdir(parents=True, exist_ok=True)
    record = {"recorded_at": datetime.now(timezone.utc).isoformat(), **payload}
    path = folder / f"{uuid4().hex}.json"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(canonical(record))
    return path
