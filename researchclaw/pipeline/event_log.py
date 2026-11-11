"""Append-only JSONL event log for pipeline runs (``run_dir/events.jsonl``).

Operational telemetry for unattended monitoring. It is *not* scientific
evidence; authoritative evidence lives under ``run_dir/evidence``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class EventType(str, Enum):
    PIPELINE_START = "pipeline_start"
    PIPELINE_END = "pipeline_end"
    STAGE_START = "stage_start"
    STAGE_END = "stage_end"
    STAGE_FAIL = "stage_fail"


def create_event(event_type: EventType, **fields: Any) -> dict[str, Any]:
    return {"ts": datetime.now(timezone.utc).isoformat(), "event": EventType(event_type).value, **fields}


class EventLog:
    def __init__(self, log_dir: str | Path, filename: str = "events.jsonl") -> None:
        self.path = Path(log_dir) / filename
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    def read(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
