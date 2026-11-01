from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from smoke import SmokeFailure, smoke_service  # noqa: E402


class _MCPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        pass

    def _send(self, status: int, body: dict | None = None, headers: dict | None = None) -> None:
        payload = b"" if body is None else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        method = request["method"]
        if self.headers.get("Authorization") != "Bearer test-only-token":
            self.send_response(401)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", "12")
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        if method == "initialize":
            self._send(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "mcp-test", "version": "0.0.1"},
                    },
                },
                {"Mcp-Session-Id": "test-session"},
            )
            return

        if self.headers.get("Mcp-Session-Id") != "test-session":
            self._send(400, {"error": "missing session"})
            return
        if self.headers.get("MCP-Protocol-Version") != "2025-06-18":
            self._send(400, {"error": "missing protocol version"})
            return

        if method == "notifications/initialized":
            self._send(202)
        elif method == "tools/list":
            self._send(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"tools": [{"name": "ping"}, {"name": "read_status"}]},
                },
            )
        elif method == "ping":
            self._send(200, {"jsonrpc": "2.0", "id": request["id"], "result": {}})
        else:
            self._send(400, {"error": "unexpected method"})


class MCPClientSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _MCPHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.endpoint = f"http://127.0.0.1:{cls.server.server_port}/mcp"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_smoke_performs_auth_initialize_discovery_and_ping(self) -> None:
        tools = smoke_service(
            "mock-service", self.endpoint, "test-only-token", "2025-06-18"
        )
        self.assertEqual(tools, ["ping", "read_status"])

    def test_wrong_token_is_rejected_without_leaking_it(self) -> None:
        secret = "wrong-secret-that-must-not-be-printed"
        with self.assertRaises(SmokeFailure) as raised:
            smoke_service("mock-service", self.endpoint, secret, "2025-06-18")
        self.assertNotIn(secret, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
