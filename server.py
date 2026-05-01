from __future__ import annotations

import json
import mimetypes
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.bot_manager import BotManager
from app.detectors import detect_opportunities
from app.market_data import collect_market_snapshot
from app.store import Store


ROOT = Path(__file__).parent
STATIC_ROOT = ROOT / "static"
DB_PATH = ROOT / "data" / "arbitrage_monitor.sqlite3"


store = Store(DB_PATH)
bot_manager = BotManager(store)


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


def json_response(handler: BaseHTTPRequestHandler, payload, status: int = 200):
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError(400, f"Invalid JSON: {exc}") from exc


class Handler(BaseHTTPRequestHandler):
    server_version = "ArbMonitor/0.1"

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self.handle_api_get(parsed.path)
            else:
                self.handle_static(parsed.path)
        except ApiError as exc:
            json_response(self, {"error": exc.message}, exc.status)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, 500)

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            body = read_json(self)
            self.handle_api_post(parsed.path, body)
        except ApiError as exc:
            json_response(self, {"error": exc.message}, exc.status)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, 500)

    def handle_api_get(self, path: str):
        if path == "/api/health":
            json_response(self, {"ok": True, "time": time.time()})
            return

        if path == "/api/snapshot":
            snapshot = collect_market_snapshot()
            snapshot_id = store.save_snapshot(snapshot)
            opportunities = detect_opportunities(snapshot)
            store.save_opportunities(snapshot_id, opportunities)
            json_response(self, {"snapshot": snapshot, "opportunities": opportunities})
            return

        if path == "/api/opportunities":
            json_response(self, {"opportunities": store.list_opportunities(limit=100)})
            return

        if path == "/api/bots":
            json_response(self, {"bots": bot_manager.list_bots()})
            return

        if path == "/api/trades":
            json_response(self, {"trades": store.list_trades(limit=100)})
            return

        if path == "/api/logs":
            json_response(self, {"logs": store.list_events(limit=200)})
            return

        raise ApiError(404, "Unknown API route")

    def handle_api_post(self, path: str, body: dict):
        parts = [part for part in path.split("/") if part]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "bots":
            bot_id = parts[2]
            action = parts[3]
            if action == "start":
                result = bot_manager.start(bot_id, mode=body.get("mode", "paper"))
            elif action == "pause":
                result = bot_manager.pause(bot_id)
            elif action == "stop":
                result = bot_manager.stop(bot_id)
            else:
                raise ApiError(404, "Unknown bot action")
            json_response(self, result)
            return

        if path == "/api/scan":
            snapshot = collect_market_snapshot()
            snapshot_id = store.save_snapshot(snapshot)
            opportunities = detect_opportunities(snapshot)
            store.save_opportunities(snapshot_id, opportunities)
            bot_manager.ingest_opportunities(opportunities)
            json_response(self, {"snapshot_id": snapshot_id, "opportunities": opportunities})
            return

        raise ApiError(404, "Unknown API route")

    def handle_static(self, path: str):
        if path == "/":
            path = "/index.html"
        target = (STATIC_ROOT / path.lstrip("/")).resolve()
        if not str(target).startswith(str(STATIC_ROOT.resolve())):
            raise ApiError(403, "Forbidden")
        if not target.exists() or not target.is_file():
            raise ApiError(404, "Not found")
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


def background_scanner():
    while True:
        try:
            snapshot = collect_market_snapshot()
            snapshot_id = store.save_snapshot(snapshot)
            opportunities = detect_opportunities(snapshot)
            store.save_opportunities(snapshot_id, opportunities)
            bot_manager.ingest_opportunities(opportunities)
        except Exception as exc:
            store.add_event("system", "scanner_error", str(exc))
        time.sleep(45)


def main():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    store.initialize()
    bot_manager.initialize()
    threading.Thread(target=background_scanner, daemon=True).start()

    server = ThreadingHTTPServer(("127.0.0.1", 8787), Handler)
    print("Web3 Arbitrage Monitor running at http://127.0.0.1:8787")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        bot_manager.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
