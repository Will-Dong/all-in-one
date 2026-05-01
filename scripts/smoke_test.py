from __future__ import annotations

import json
import sys
import threading
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def post_json(url: str, payload: dict):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read())


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, json.loads(response.read())


def main():
    server.store.initialize()
    server.bot_manager.initialize()

    httpd = server.ThreadingHTTPServer(("127.0.0.1", 8899), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        health_status, health = get_json("http://127.0.0.1:8899/api/health")
        start_status, _ = post_json(
            "http://127.0.0.1:8899/api/bots/funding_arbitrage/start",
            {"mode": "paper"},
        )
        scan_status, scan = post_json("http://127.0.0.1:8899/api/scan", {})
        bots_status, bots = get_json("http://127.0.0.1:8899/api/bots")
        trades_status, trades = get_json("http://127.0.0.1:8899/api/trades")
        with urllib.request.urlopen("http://127.0.0.1:8899/", timeout=5) as response:
            page_status = response.status

        assert health_status == 200 and health["ok"] is True
        assert start_status == 200
        assert scan_status == 200
        assert "opportunities" in scan
        assert bots_status == 200
        assert any(
            bot["bot_id"] == "funding_arbitrage" and bot["status"] == "running"
            for bot in bots["bots"]
        )
        assert trades_status == 200
        assert "trades" in trades
        assert page_status == 200

        print("health=ok")
        print(f"opportunities={len(scan['opportunities'])}")
        print(f"paper_trades={len(trades['trades'])}")
        print("static_page=ok")
    finally:
        httpd.shutdown()
        server.bot_manager.shutdown()


if __name__ == "__main__":
    main()
