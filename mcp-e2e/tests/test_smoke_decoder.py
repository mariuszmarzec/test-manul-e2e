from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from smoke import _decode_response  # noqa: E402


class MCPResponseDecoderTests(unittest.TestCase):
    def test_decodes_json_response(self) -> None:
        messages = _decode_response(
            "application/json",
            b'{"jsonrpc":"2.0","id":7,"result":{"tools":[]}}',
        )
        self.assertEqual(messages[0]["result"], {"tools": []})

    def test_decodes_server_sent_events(self) -> None:
        body = b'event: message\ndata: {"jsonrpc":"2.0","id":8,"result":{}}\n\n'
        messages = _decode_response("text/event-stream", body)
        self.assertEqual(messages[0]["id"], 8)

    def test_ignores_keepalive_and_done_events(self) -> None:
        body = b': keepalive\n\ndata: [DONE]\n\n'
        self.assertEqual(_decode_response("text/event-stream", body), [])


if __name__ == "__main__":
    unittest.main()
