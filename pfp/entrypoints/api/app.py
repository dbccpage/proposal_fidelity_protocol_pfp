"""Lightweight HTTP server host for Symbol Game API router.

Can run as `python -m pfp.entrypoints.api.app --port 8080`.
AuthorityEffect: None (const).
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .router import SymbolGameApiRouter


class SymbolGameHttpHandler(BaseHTTPRequestHandler):
    def _send_response(self, status: int, data: dict[str, Any]) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        body = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        resp = SymbolGameApiRouter.dispatch("GET", self.path, None)
        self._send_response(resp.status_code, resp.data)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body_dict = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            self._send_response(400, {"error": "Invalid JSON payload", "authority_effect": "None"})
            return
        resp = SymbolGameApiRouter.dispatch("POST", self.path, body_dict)
        self._send_response(resp.status_code, resp.data)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = HTTPServer((host, port), SymbolGameHttpHandler)
    print(f"Symbol Game API server running at http://{host}:{port} (AuthorityEffect: None)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Symbol Game API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
