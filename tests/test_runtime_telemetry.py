"""Event log, cost tracker and experiment-memory wiring (software checks)."""
from __future__ import annotations

import json
from types import SimpleNamespace

from researchclaw.cost_tracker import CostTracker
from researchclaw.memory.experiment_memory import ExperimentMemory
from researchclaw.memory.retriever import MemoryRetriever
from researchclaw.memory.store import MemoryStore
from researchclaw.pipeline.event_log import EventLog, EventType, create_event
from researchclaw.pipeline.runner import _record_experiment_memory


def test_event_log_roundtrip(tmp_path):
    log = EventLog(tmp_path)
    log.append(create_event(EventType.STAGE_START, run_id="r", stage="TOPIC_INIT"))
    log.append(create_event(EventType.STAGE_END, run_id="r", stage="TOPIC_INIT", status="done"))
    events = log.read()
    assert [e["event"] for e in events] == ["stage_start", "stage_end"]


def test_cost_unknown_without_prices(monkeypatch):
    monkeypatch.delenv("RANCHO_PRICE_INPUT_PER_MTOK", raising=False)
    monkeypatch.delenv("RANCHO_PRICE_OUTPUT_PER_MTOK", raising=False)
    tracker = CostTracker()
    tracker.record("m", 1000, 500)
    assert tracker.prompt_tokens == 1000 and not tracker.cost_known
    assert tracker.summary()["cost_usd"] == "UNKNOWN_PRICES_NOT_CONFIGURED"


def test_cost_budget_with_prices(monkeypatch):
    monkeypatch.setenv("RANCHO_PRICE_INPUT_PER_MTOK", "2")
    monkeypatch.setenv("RANCHO_PRICE_OUTPUT_PER_MTOK", "8")
    tracker = CostTracker()
    tracker.record("m", 1_000_000, 1_000_000)
    assert abs(tracker.total_cost_usd - 10.0) < 1e-9
    assert tracker.check_budget(20) and not tracker.check_budget(5)


def test_experiment_memory_records_finite_stage12_metrics(tmp_path):
    runs = tmp_path / "run" / "stage-12" / "runs"
    runs.mkdir(parents=True)
    (runs / "run-1.json").write_text(json.dumps({"status": "completed", "metrics": {"acc": 0.8}}), encoding="utf-8")
    (runs / "run-2.json").write_text(json.dumps({"status": "failed", "metrics": {"acc": "nan"}}), encoding="utf-8")
    store = MemoryStore(tmp_path / "mem")
    memory = ExperimentMemory(store, MemoryRetriever(store))
    config = SimpleNamespace(experiment=SimpleNamespace(metric_key="acc"), research=SimpleNamespace(topic="t"))
    assert _record_experiment_memory(memory, tmp_path / "run", config, "r") == 1
    reloaded = MemoryStore(tmp_path / "mem")
    assert reloaded.load() == 1
