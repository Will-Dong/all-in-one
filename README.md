# Web3 Arbitrage Monitor

Local MVP for monitoring long-tail Web3 arbitrage ideas and managing paper-mode bots.

## What is included

- Standard-library Python HTTP server, no package install required.
- SQLite persistence for snapshots, opportunities, bot events, and paper trades.
- Mock market adapters for the first runnable version:
  - RWA yield spreads
  - Pendle PT/YT yield spreads
  - Perp DEX funding spreads
  - Stablecoin basis
  - Prediction market outcome sums
- Bot management API:
  - Start, pause, stop
  - Paper/live mode flag, with live execution disabled in this MVP
  - Heartbeats, logs, simulated trades, opportunity history
- Static dashboard UI.

## Run

```powershell
python .\server.py
```

Open:

```text
http://127.0.0.1:8787
```

The app creates `data/arbitrage_monitor.sqlite3` on first run.

## Smoke test

```powershell
python .\scripts\smoke_test.py
```

## Safety

This MVP never sends transactions and never stores private keys. Bots only run in paper mode unless you explicitly extend the execution adapters.
