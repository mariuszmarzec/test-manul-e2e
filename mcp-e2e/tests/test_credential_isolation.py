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

TOKEN_A = "e2e-caracal-token-A"
TOKEN_B = "e2e-fiteo-token-B"
PROTOCOL_VERSION = "2025-06-18"
EXPECTED_TOOLS = ["ping", "read_status"]
SESSION_ID_A = "session-a"
SESSION_ID_B = "session-b"


class _RecordingMCPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        pass

    def _send(
        self, status: int, body: dict | None = None, headers: dict | None = None
    ) -> None:
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

        auth = self.headers.get("Authorization")
        self.server.auth_headers.append(auth)

        expected = f"Bearer {self.server.accepted_token}"
        if auth != expected:
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
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": self.server.server_label,
                            "version": "0.0.1",
                        },
                    },
                },
                {"Mcp-Session-Id": self.server.session_id},
            )
            return

        if self.headers.get("Mcp-Session-Id") != self.server.session_id:
            self._send(400, {"error": "missing session"})
            return
        if self.headers.get("MCP-Protocol-Version") != PROTOCOL_VERSION:
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
                    "result": {
                        "tools": [{"name": name} for name in self.server.tool_names]
                    },
                },
            )
        elif method == "ping":
            self._send(200, {"jsonrpc": "2.0", "id": request["id"], "result": {}})
        else:
            self._send(400, {"error": "unexpected method"})


class _IsolatedServer:
    def __init__(
        self,
        accepted_token: str,
        tool_names: list[str],
        server_label: str,
        session_id: str,
    ) -> None:
        self.accepted_token = accepted_token
        self.tool_names = tool_names
        self.server_label = server_label
        self.session_id = session_id
        self.auth_headers: list[str | None] = []

        self._http_server = ThreadingHTTPServer(
            ("127.0.0.1", 0), _RecordingMCPHandler
        )
        self._http_server.accepted_token = accepted_token
        self._http_server.tool_names = tool_names
        self._http_server.server_label = server_label
        self._http_server.session_id = session_id
        self._http_server.auth_headers = self.auth_headers

        self._thread = threading.Thread(
            target=self._http_server.serve_forever, daemon=True
        )
        self._thread.start()
        self.endpoint = (
            f"http://127.0.0.1:{self._http_server.server_port}/mcp"
        )

    def shutdown(self) -> None:
        self._http_server.shutdown()
        self._http_server.server_close()
        self._thread.join(timeout=2)


class CredentialIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.servers: list[_IsolatedServer] = []
        self.server_a = self._start_server(
            TOKEN_A, EXPECTED_TOOLS, "mock-caracal", SESSION_ID_A
        )
        self.server_b = self._start_server(
            TOKEN_B, EXPECTED_TOOLS, "mock-fiteo", SESSION_ID_B
        )

    def _start_server(
        self,
        accepted_token: str,
        tool_names: list[str],
        server_label: str,
        session_id: str,
    ) -> _IsolatedServer:
        server = _IsolatedServer(
            accepted_token, tool_names, server_label, session_id
        )
        self.servers.append(server)
        self.addCleanup(server.shutdown)
        return server

    def test_smoke_client_does_not_mix_credentials(self) -> None:
        tools_a = smoke_service(
            "mock-caracal", self.server_a.endpoint, TOKEN_A, PROTOCOL_VERSION
        )
        tools_b = smoke_service(
            "mock-fiteo", self.server_b.endpoint, TOKEN_B, PROTOCOL_VERSION
        )

        self.assertEqual(tools_a, EXPECTED_TOOLS)
        self.assertEqual(tools_b, EXPECTED_TOOLS)

        self._assert_server_isolation(self.server_a, "A")
        self._assert_server_isolation(self.server_b, "B")
        self._assert_no_cross_contamination(self.server_a, self.server_b)

    def _assert_server_isolation(self, server: _IsolatedServer, label: str) -> None:
        headers = server.auth_headers
        none_count = sum(1 for h in headers if h is None)
        auth_headers = [h for h in headers if h is not None]

        self.assertEqual(
            none_count,
            1,
            f"server {label} should receive exactly one unauthenticated probe",
        )
        self.assertEqual(
            len(auth_headers),
            4,
            f"server {label} should receive four authenticated requests",
        )
        self.assertEqual(
            len(set(auth_headers)),
            1,
            f"server {label} authenticated requests should carry a uniform token",
        )
        for auth in auth_headers:
            self.assertTrue(
                auth.startswith("Bearer "),
                f"server {label} auth header should use Bearer scheme",
            )

    def _assert_no_cross_contamination(
        self, server_a: _IsolatedServer, server_b: _IsolatedServer
    ) -> None:
        auth_a = {h for h in server_a.auth_headers if h is not None}
        auth_b = {h for h in server_b.auth_headers if h is not None}
        self.assertEqual(
            len(auth_a & auth_b),
            0,
            "servers must not share any Authorization header value",
        )


if __name__ == "__main__":
    unittest.main()