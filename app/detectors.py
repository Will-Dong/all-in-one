from __future__ import annotations

import hashlib
from collections import defaultdict

from app.models import Opportunity, now_ms


def detect_opportunities(snapshot: dict) -> list[dict]:
    opportunities: list[Opportunity] = []
    opportunities.extend(_detect_rwa(snapshot.get("rwa", [])))
    opportunities.extend(_detect_pendle(snapshot.get("pendle", [])))
    opportunities.extend(_detect_funding(snapshot.get("funding", [])))
    opportunities.extend(_detect_stablecoins(snapshot.get("stablecoins", [])))
    opportunities.extend(_detect_prediction_markets(snapshot.get("prediction_markets", [])))
    return sorted(
        [op.to_dict() for op in opportunities],
        key=lambda item: (item["risk"], -item["edge_bps"]),
    )


def _id(kind: str, key: str) -> str:
    digest = hashlib.sha1(f"{kind}:{key}:{int(now_ms() / 60000)}".encode()).hexdigest()[:12]
    return f"{kind}-{digest}"


def _detect_rwa(rows: list[dict]) -> list[Opportunity]:
    out = []
    for row in rows:
        spread = row["defi_apr"] - row["native_apr"]
        net_bps = spread * 100 - row["exit_cost_bps"]
        if net_bps >= 120:
            out.append(
                Opportunity(
                    id=_id("rwa", f"{row['asset']}:{row['chain']}"),
                    kind="rwa",
                    title=f"{row['asset']} on {row['chain']} DeFi yield spread",
                    expected_apr=round(net_bps / 100, 2),
                    edge_bps=round(net_bps, 1),
                    capacity_usd=min(row["liquidity_usd"] * 0.08, 150_000),
                    risk="medium",
                    action="Rotate idle stablecoins into RWA yield position, keep exit inventory.",
                    source=row,
                )
            )
    return out


def _detect_pendle(rows: list[dict]) -> list[Opportunity]:
    out = []
    for row in rows:
        if "implied_fixed_apr" in row:
            spread = row["implied_fixed_apr"] - row["underlying_apr"]
            if spread >= 2.5 and row["liquidity_usd"] >= 1_000_000:
                out.append(
                    Opportunity(
                        id=_id("pendle", row["market"]),
                        kind="pendle",
                        title=f"{row['market']} fixed yield rich vs underlying",
                        expected_apr=round(row["implied_fixed_apr"], 2),
                        edge_bps=round(spread * 100, 1),
                        capacity_usd=min(row["liquidity_usd"] * 0.05, 200_000),
                        risk="medium",
                        action="Buy PT or compare against stablecoin borrow/funding alternatives.",
                        source=row,
                    )
                )
        else:
            spread = row["underlying_apr"] - row["break_even_apr"]
            if spread >= 2.0:
                out.append(
                    Opportunity(
                        id=_id("pendle-yt", row["market"]),
                        kind="pendle",
                        title=f"{row['market']} YT break-even below current yield",
                        expected_apr=round(spread, 2),
                        edge_bps=round(spread * 100, 1),
                        capacity_usd=min(row["liquidity_usd"] * 0.03, 75_000),
                        risk="high",
                        action="Paper-buy YT only; require manual review of points and yield source.",
                        source=row,
                    )
                )
    return out


def _detect_funding(rows: list[dict]) -> list[Opportunity]:
    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_symbol[row["symbol"]].append(row)

    out = []
    for symbol, venues in by_symbol.items():
        high = max(venues, key=lambda item: item["funding_apr"])
        low = min(venues, key=lambda item: item["funding_apr"])
        spread = high["funding_apr"] - low["funding_apr"]
        if spread >= 18:
            depth = min(high["depth_10bps_usd"], low["depth_10bps_usd"])
            out.append(
                Opportunity(
                    id=_id("funding", symbol),
                    kind="funding",
                    title=f"{symbol} funding spread: short {high['venue']} / long {low['venue']}",
                    expected_apr=round(spread - 4.0, 2),
                    edge_bps=round((spread - 4.0) * 100, 1),
                    capacity_usd=min(depth * 0.35, 100_000),
                    risk="high" if symbol not in {"SOL"} else "medium",
                    action="Open delta-neutral paper trade; confirm borrow, index, and liquidation buffer.",
                    source={"high": high, "low": low},
                )
            )
    return out


def _detect_stablecoins(rows: list[dict]) -> list[Opportunity]:
    out = []
    for row in rows:
        deviation_bps = abs(row["price"] - 1.0) * 10_000
        if deviation_bps >= 18 and row["liquidity_usd"] >= 800_000:
            side = "sell rich side" if row["price"] > 1 else "buy discounted side"
            out.append(
                Opportunity(
                    id=_id("stable", f"{row['chain']}:{row['pool']}"),
                    kind="stablecoin",
                    title=f"{row['pool']} basis on {row['chain']} ({row['venue']})",
                    expected_apr=None,
                    edge_bps=round(deviation_bps, 1),
                    capacity_usd=min(row["liquidity_usd"] * 0.04, 120_000),
                    risk="medium",
                    action=f"Inventory-based rebalance: {side}; use official bridge only.",
                    source=row,
                )
            )
    return out


def _detect_prediction_markets(rows: list[dict]) -> list[Opportunity]:
    out = []
    for row in rows:
        total = sum(item["yes_price"] for item in row["outcomes"])
        deviation_bps = abs(total - 1.0) * 10_000
        if deviation_bps >= 180:
            if total < 1:
                action = "Buy all YES outcomes in paper mode; verify resolution rules first."
            else:
                action = "Evaluate all-NO or sell basket; verify shorting mechanics and fees."
            out.append(
                Opportunity(
                    id=_id("prediction", row["market"]),
                    kind="prediction",
                    title=f"Outcome sum {total:.3f}: {row['market']}",
                    expected_apr=None,
                    edge_bps=round(deviation_bps, 1),
                    capacity_usd=min(row["liquidity_usd"] * 0.05, 25_000),
                    risk="high",
                    action=action,
                    source=row,
                )
            )
    return out
