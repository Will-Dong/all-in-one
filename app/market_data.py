from __future__ import annotations

import math
import random

from app.models import MarketSnapshot, now_ms


def collect_market_snapshot() -> dict:
    """Collect a normalized market snapshot.

    The MVP uses deterministic mock adapters so the dashboard and bots can run
    without API keys. Replace individual adapter functions with live API calls
    as each venue is integrated.
    """
    seed = int(now_ms() / 45000)
    rng = random.Random(seed)
    snapshot = MarketSnapshot(
        captured_at_ms=now_ms(),
        rwa=_mock_rwa(rng),
        pendle=_mock_pendle(rng),
        funding=_mock_funding(rng),
        stablecoins=_mock_stablecoins(rng),
        prediction_markets=_mock_prediction_markets(rng),
    )
    return snapshot.to_dict()


def _wave(rng: random.Random, base: float, width: float) -> float:
    return base + width * (rng.random() - 0.5)


def _mock_rwa(rng: random.Random):
    return [
        {
            "asset": "USDY",
            "chain": "Mantle",
            "native_apr": round(_wave(rng, 3.55, 0.45), 2),
            "defi_apr": round(_wave(rng, 5.1, 2.2), 2),
            "liquidity_usd": 1_800_000,
            "exit_cost_bps": 18,
        },
        {
            "asset": "USYC",
            "chain": "Ethereum",
            "native_apr": round(_wave(rng, 4.15, 0.35), 2),
            "defi_apr": round(_wave(rng, 4.7, 1.1), 2),
            "liquidity_usd": 850_000,
            "exit_cost_bps": 28,
        },
        {
            "asset": "OUSG",
            "chain": "Ethereum",
            "native_apr": round(_wave(rng, 4.05, 0.25), 2),
            "defi_apr": round(_wave(rng, 4.3, 0.9), 2),
            "liquidity_usd": 420_000,
            "exit_cost_bps": 40,
        },
    ]


def _mock_pendle(rng: random.Random):
    markets = [
        ("PT-sUSDe-2026-06", "Ethereum", 14.8, 11.2, 9_200_000),
        ("PT-eUSDe-2026-07", "Ethereum", 13.2, 10.5, 5_700_000),
        ("PT-USDY-2026-09", "Mantle", 6.4, 4.1, 2_300_000),
        ("YT-sUSDe-2026-06", "Ethereum", None, 11.2, 3_100_000),
    ]
    out = []
    for name, chain, implied, underlying, liquidity in markets:
        item = {
            "market": name,
            "chain": chain,
            "underlying_apr": round(_wave(rng, underlying, 1.4), 2),
            "liquidity_usd": liquidity,
            "days_to_maturity": rng.choice([28, 45, 62, 91, 125]),
        }
        if implied is not None:
            item["implied_fixed_apr"] = round(_wave(rng, implied, 2.4), 2)
        else:
            item["yt_price"] = round(_wave(rng, 0.034, 0.018), 4)
            item["break_even_apr"] = round(_wave(rng, 8.8, 3.0), 2)
        out.append(item)
    return out


def _mock_funding(rng: random.Random):
    symbols = ["HYPE", "JUP", "ENA", "WIF", "TIA", "SOL"]
    venues = ["Hyperliquid", "Drift", "dYdX", "Binance"]
    rows = []
    for symbol in symbols:
        base = _wave(rng, 18.0 if symbol != "SOL" else 7.0, 22.0)
        for venue in venues:
            skew = {"Hyperliquid": 8, "Drift": -3, "dYdX": 1, "Binance": -5}[venue]
            rows.append(
                {
                    "symbol": symbol,
                    "venue": venue,
                    "funding_apr": round(base + skew + _wave(rng, 0, 8), 2),
                    "open_interest_usd": int(_wave(rng, 4_000_000, 5_000_000)),
                    "depth_10bps_usd": int(max(50_000, _wave(rng, 250_000, 300_000))),
                }
            )
    return rows


def _mock_stablecoins(rng: random.Random):
    pools = [
        ("Base", "USDC/USDbC", "Aerodrome", 0.9996, 3_500_000),
        ("Arbitrum", "USDC/USDT", "Curve", 1.0008, 8_900_000),
        ("Mantle", "USDT/USDY", "MerchantMoe", 0.9978, 1_200_000),
        ("Solana", "USDC/USDT", "Orca", 1.0012, 6_400_000),
    ]
    return [
        {
            "chain": chain,
            "pool": pair,
            "venue": venue,
            "price": round(price + _wave(rng, 0, 0.0018), 5),
            "liquidity_usd": liquidity,
            "bridge_eta_min": rng.choice([4, 8, 15, 30, 60]),
        }
        for chain, pair, venue, price, liquidity in pools
    ]


def _mock_prediction_markets(rng: random.Random):
    markets = [
        ("Fed cuts rates by July?", ["Yes", "No"], [0.47, 0.54]),
        ("AI model launches before June", ["Yes", "No"], [0.36, 0.61]),
        ("Election turnout range", ["Low", "Mid", "High"], [0.21, 0.52, 0.25]),
        ("BTC above 100k on expiry", ["Yes", "No"], [0.44, 0.57]),
    ]
    out = []
    for title, outcomes, prices in markets:
        noisy = [max(0.01, min(0.99, p + _wave(rng, 0, 0.04))) for p in prices]
        out.append(
            {
                "market": title,
                "venue": "Polymarket-like",
                "outcomes": [
                    {"name": name, "yes_price": round(price, 3)}
                    for name, price in zip(outcomes, noisy)
                ],
                "liquidity_usd": int(_wave(rng, 65_000, 75_000)),
                "days_to_resolution": rng.choice([3, 9, 21, 48]),
            }
        )
    return out
