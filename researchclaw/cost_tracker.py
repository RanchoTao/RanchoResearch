"""Process-wide LLM usage tracker.

Token counts come from provider responses. USD cost is computed only when
prices are configured via ``RANCHO_PRICE_INPUT_PER_MTOK`` and
``RANCHO_PRICE_OUTPUT_PER_MTOK`` (USD per million tokens). Without prices the
cost is unknown, and budget checks say so instead of pretending it is $0.
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


def _price(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        logger.warning("Ignoring invalid %s=%r", name, raw)
        return None
    return value if value >= 0 else None


@dataclass
class CostTracker:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost_usd: float = 0.0
    unpriced_calls: int = 0
    by_model: dict[str, dict[str, int]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _warned: bool = field(default=False, repr=False)

    def record(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        price_in = _price("RANCHO_PRICE_INPUT_PER_MTOK")
        price_out = _price("RANCHO_PRICE_OUTPUT_PER_MTOK")
        with self._lock:
            self.calls += 1
            self.prompt_tokens += int(prompt_tokens or 0)
            self.completion_tokens += int(completion_tokens or 0)
            entry = self.by_model.setdefault(model or "unknown", {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0})
            entry["calls"] += 1
            entry["prompt_tokens"] += int(prompt_tokens or 0)
            entry["completion_tokens"] += int(completion_tokens or 0)
            if price_in is None or price_out is None:
                self.unpriced_calls += 1
            else:
                self.total_cost_usd += (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000

    @property
    def cost_known(self) -> bool:
        return self.unpriced_calls == 0

    def check_budget(self, budget_usd: float) -> bool:
        """False once the *known* cost exceeds the budget."""
        if not self.cost_known and not self._warned:
            self._warned = True
            logger.warning("LLM prices not configured (RANCHO_PRICE_*_PER_MTOK); USD budget cannot be enforced, "
                           "only token usage is tracked.")
        return self.total_cost_usd <= budget_usd

    def summary(self) -> dict:
        return {"calls": self.calls, "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "cost_usd": round(self.total_cost_usd, 6) if self.cost_known else "UNKNOWN_PRICES_NOT_CONFIGURED",
                "by_model": self.by_model}


_GLOBAL = CostTracker()


def get_global_tracker() -> CostTracker:
    return _GLOBAL


def reset_global_tracker() -> None:
    global _GLOBAL
    _GLOBAL = CostTracker()
