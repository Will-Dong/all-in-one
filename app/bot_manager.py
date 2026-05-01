from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from app.models import now_ms


BOT_CONFIGS = {
    "funding_arbitrage": {
        "name": "Funding Arbitrage",
        "kinds": {"funding"},
        "min_edge_bps": 1200,
        "max_notional_usd": 25_000,
    },
    "pendle_yield": {
        "name": "Pendle Yield",
        "kinds": {"pendle", "rwa"},
        "min_edge_bps": 220,
        "max_notional_usd": 20_000,
    },
    "prediction_sum": {
        "name": "Prediction Sum",
        "kinds": {"prediction"},
        "min_edge_bps": 250,
        "max_notional_usd": 2_500,
    },
    "stablecoin_basis": {
        "name": "Stablecoin Basis",
        "kinds": {"stablecoin"},
        "min_edge_bps": 25,
        "max_notional_usd": 15_000,
    },
}


@dataclass
class BotState:
    bot_id: str
    name: str
    status: str = "stopped"
    mode: str = "paper"
    last_heartbeat_ms: int | None = None
    last_opportunity_id: str | None = None
    scans: int = 0
    paper_trades: int = 0
    config: dict[str, Any] = field(default_factory=dict)


class BotManager:
    def __init__(self, store):
        self.store = store
        self._lock = threading.Lock()
        self._bots: dict[str, BotState] = {}

    def initialize(self):
        with self._lock:
            for bot_id, config in BOT_CONFIGS.items():
                self._bots[bot_id] = BotState(
                    bot_id=bot_id,
                    name=config["name"],
                    config={
                        "min_edge_bps": config["min_edge_bps"],
                        "max_notional_usd": config["max_notional_usd"],
                        "kinds": sorted(config["kinds"]),
                    },
                )
        self.store.add_event("system", "startup", "Bot manager initialized")

    def shutdown(self):
        with self._lock:
            for bot in self._bots.values():
                bot.status = "stopped"
        self.store.add_event("system", "shutdown", "Bot manager stopped")

    def list_bots(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._to_dict(bot) for bot in self._bots.values()]

    def start(self, bot_id: str, mode: str = "paper") -> dict[str, Any]:
        if mode != "paper":
            mode = "paper"
            self.store.add_event(bot_id, "safety", "Live mode requested but disabled; using paper mode")
        bot = self._require_bot(bot_id)
        with self._lock:
            bot.status = "running"
            bot.mode = mode
            bot.last_heartbeat_ms = now_ms()
        self.store.add_event(bot_id, "start", f"Started in {mode} mode")
        return {"bot": self._to_dict(bot)}

    def pause(self, bot_id: str) -> dict[str, Any]:
        bot = self._require_bot(bot_id)
        with self._lock:
            bot.status = "paused"
            bot.last_heartbeat_ms = now_ms()
        self.store.add_event(bot_id, "pause", "Paused")
        return {"bot": self._to_dict(bot)}

    def stop(self, bot_id: str) -> dict[str, Any]:
        bot = self._require_bot(bot_id)
        with self._lock:
            bot.status = "stopped"
            bot.last_heartbeat_ms = now_ms()
        self.store.add_event(bot_id, "stop", "Stopped")
        return {"bot": self._to_dict(bot)}

    def ingest_opportunities(self, opportunities: list[dict[str, Any]]):
        with self._lock:
            bots = list(self._bots.values())

        for bot in bots:
            if bot.status != "running":
                continue
            config = BOT_CONFIGS[bot.bot_id]
            matches = [
                op
                for op in opportunities
                if op["kind"] in config["kinds"] and op["edge_bps"] >= config["min_edge_bps"]
            ]
            with self._lock:
                bot.scans += 1
                bot.last_heartbeat_ms = now_ms()
            for op in matches[:2]:
                notional = min(op["capacity_usd"], config["max_notional_usd"])
                self.store.add_trade(bot.bot_id, op, notional_usd=notional)
                self.store.add_event(
                    bot.bot_id,
                    "paper_trade",
                    f"Paper-filled {op['title']} at ${notional:,.0f} notional",
                )
                with self._lock:
                    bot.paper_trades += 1
                    bot.last_opportunity_id = op["id"]

    def _require_bot(self, bot_id: str) -> BotState:
        with self._lock:
            bot = self._bots.get(bot_id)
        if bot is None:
            raise ValueError(f"Unknown bot: {bot_id}")
        return bot

    def _to_dict(self, bot: BotState) -> dict[str, Any]:
        return {
            "bot_id": bot.bot_id,
            "name": bot.name,
            "status": bot.status,
            "mode": bot.mode,
            "last_heartbeat_ms": bot.last_heartbeat_ms,
            "last_opportunity_id": bot.last_opportunity_id,
            "scans": bot.scans,
            "paper_trades": bot.paper_trades,
            "config": bot.config,
        }
