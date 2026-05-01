from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def now_ms() -> int:
    import time

    return int(time.time() * 1000)


@dataclass
class MarketSnapshot:
    captured_at_ms: int
    rwa: list[dict[str, Any]] = field(default_factory=list)
    pendle: list[dict[str, Any]] = field(default_factory=list)
    funding: list[dict[str, Any]] = field(default_factory=list)
    stablecoins: list[dict[str, Any]] = field(default_factory=list)
    prediction_markets: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Opportunity:
    id: str
    kind: str
    title: str
    expected_apr: float | None
    edge_bps: float
    capacity_usd: float
    risk: str
    action: str
    source: dict[str, Any]
    detected_at_ms: int = field(default_factory=now_ms)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
