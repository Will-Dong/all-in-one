from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from app.models import now_ms


class Store:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists snapshots (
                    id integer primary key autoincrement,
                    captured_at_ms integer not null,
                    payload text not null
                );

                create table if not exists opportunities (
                    id text primary key,
                    snapshot_id integer not null,
                    detected_at_ms integer not null,
                    kind text not null,
                    title text not null,
                    expected_apr real,
                    edge_bps real not null,
                    capacity_usd real not null,
                    risk text not null,
                    action text not null,
                    source text not null
                );

                create table if not exists bot_events (
                    id integer primary key autoincrement,
                    bot_id text not null,
                    event_type text not null,
                    message text not null,
                    created_at_ms integer not null
                );

                create table if not exists paper_trades (
                    id integer primary key autoincrement,
                    bot_id text not null,
                    opportunity_id text not null,
                    kind text not null,
                    notional_usd real not null,
                    expected_apr real,
                    edge_bps real not null,
                    status text not null,
                    created_at_ms integer not null,
                    payload text not null
                );
                """
            )

    def _connect(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def save_snapshot(self, snapshot: dict[str, Any]) -> int:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "insert into snapshots (captured_at_ms, payload) values (?, ?)",
                (snapshot["captured_at_ms"], json.dumps(snapshot, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def save_opportunities(self, snapshot_id: int, opportunities: list[dict[str, Any]]):
        with self._lock, self._connect() as conn:
            for op in opportunities:
                conn.execute(
                    """
                    insert or replace into opportunities (
                        id, snapshot_id, detected_at_ms, kind, title, expected_apr,
                        edge_bps, capacity_usd, risk, action, source
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        op["id"],
                        snapshot_id,
                        op["detected_at_ms"],
                        op["kind"],
                        op["title"],
                        op["expected_apr"],
                        op["edge_bps"],
                        op["capacity_usd"],
                        op["risk"],
                        op["action"],
                        json.dumps(op["source"], ensure_ascii=False),
                    ),
                )

    def list_opportunities(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select * from opportunities
                order by detected_at_ms desc, edge_bps desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [self._op_from_row(row) for row in rows]

    def add_event(self, bot_id: str, event_type: str, message: str):
        with self._lock, self._connect() as conn:
            conn.execute(
                "insert into bot_events (bot_id, event_type, message, created_at_ms) values (?, ?, ?, ?)",
                (bot_id, event_type, message, now_ms()),
            )

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select * from bot_events order by created_at_ms desc limit ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_trade(self, bot_id: str, opportunity: dict[str, Any], notional_usd: float, status: str = "paper_filled"):
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                insert into paper_trades (
                    bot_id, opportunity_id, kind, notional_usd, expected_apr,
                    edge_bps, status, created_at_ms, payload
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bot_id,
                    opportunity["id"],
                    opportunity["kind"],
                    notional_usd,
                    opportunity["expected_apr"],
                    opportunity["edge_bps"],
                    status,
                    now_ms(),
                    json.dumps(opportunity, ensure_ascii=False),
                ),
            )

    def list_trades(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select * from paper_trades order by created_at_ms desc limit ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _op_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["source"] = json.loads(data["source"])
        return data
