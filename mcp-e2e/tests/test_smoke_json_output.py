"""Tests for the --json machine-readable output mode of the MCP smoke runner.

These tests use the Python standard library only and never contact a live
service. They drive smoke.main() directly with a controlled sys.argv, a cleared
os.environ and a mocked smoke.smoke_service, then assert on the captured
stdout and exit code.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import smoke  # noqa: E402

# Secret-looking values that must never leak into machine-readable output.
CARACAL_ENV = {
    "CARACAL_MCP_URL": "https://caracal.example.invalid/mcp",
    "CARACAL_ACCESS_TOKEN": "caracal-secret-token",
}
TODO_ENV = {
    "TODO_LOCAL_MCP_URL": "http://127.0.0.1:9999/todo",
    "TODO_LOCAL_MCP_TOKEN": "todo-secret-token",
}
FITEO_ENV = {
    "FITEO_BASE_URL": "https://fiteo.example.invalid",
    "FITEO_PAT": "fiteo-secret-pat",
}


def _run_main(argv: list[str], environ: dict[str, str]) -> tuple[int, str]:
    """Run smoke.main() with controlled argv/environ and return (code, stdout)."""
    captured = io.StringIO()
    with (
        mock.patch.object(sys, "argv", ["smoke.py", *argv]),
        mock.patch.dict(os.environ, environ, clear=True),
        contextlib.redirect_stdout(captured),
    ):
        exit_code = smoke.main()
    return exit_code, captured.getvalue()


def _services_by_name(doc: dict) -> dict[str, dict]:
    return {service["name"]: service for service in doc["services"]}


class JsonOutputTests(unittest.TestCase):
    def test_all_pass_json_is_single_valid_document(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["alpha", "beta"]):
            exit_code, out = _run_main(
                ["--json"], {**CARACAL_ENV, **TODO_ENV, **FITEO_ENV}
            )
        self.assertEqual(exit_code, 0)
        doc = json.loads(out)  # raises if the output is not exactly one JSON doc
        self.assertEqual(
            doc["summary"],
            {"checked": 3, "passed": 3, "skipped": 0, "failed": 0},
        )
        by_name = _services_by_name(doc)
        for name in ("caracal-rag", "todo-local", "fiteo-backend"):
            self.assertEqual(by_name[name]["status"], "PASS")
            self.assertEqual(by_name[name]["tools"], ["alpha", "beta"])
            self.assertIsNone(by_name[name]["reason"])

    def test_required_caracal_missing_is_fail(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["t"]) as svc:
            exit_code, out = _run_main(["--json"], {**TODO_ENV, **FITEO_ENV})
        self.assertEqual(exit_code, 1)
        doc = json.loads(out)
        caracal = _services_by_name(doc)["caracal-rag"]
        self.assertEqual(caracal["status"], "FAIL")
        self.assertIsNotNone(caracal["reason"])
        self.assertEqual(doc["summary"]["failed"], 1)
        # Caracal must not be probed live, but the optional services are.
        self.assertEqual(svc.call_count, 2)

    def test_optional_missing_is_skip_and_does_not_fail(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["x"]):
            exit_code, out = _run_main(["--json"], {**CARACAL_ENV})
        self.assertEqual(exit_code, 0)
        doc = json.loads(out)
        by_name = _services_by_name(doc)
        self.assertEqual(by_name["caracal-rag"]["status"], "PASS")
        self.assertEqual(by_name["todo-local"]["status"], "SKIP")
        self.assertEqual(by_name["fiteo-backend"]["status"], "SKIP")
        self.assertEqual(
            doc["summary"], {"checked": 3, "passed": 1, "skipped": 2, "failed": 0}
        )

    def test_optional_live_error_is_fail_not_skip(self) -> None:
        def fake_smoke(name, endpoint, token, protocol_version):
            if name == "todo-local":
                raise smoke.SmokeFailure(
                    "transport failed at https://todo.example.invalid/mcp "
                    "with Bearer todo-secret-token"
                )
            return ["ok"]

        with mock.patch.object(smoke, "smoke_service", side_effect=fake_smoke):
            exit_code, out = _run_main(
                ["--json"], {**CARACAL_ENV, **TODO_ENV, **FITEO_ENV}
            )
        self.assertEqual(exit_code, 1)
        doc = json.loads(out)
        by_name = _services_by_name(doc)
        todo = by_name["todo-local"]
        self.assertEqual(todo["status"], "FAIL")
        self.assertIn("<redacted-url>", todo["reason"])
        self.assertIn("Bearer <redacted-token>", todo["reason"])
        self.assertNotIn("https://todo.example.invalid", todo["reason"])
        self.assertNotIn("todo-secret-token", todo["reason"])
        self.assertEqual(doc["summary"]["failed"], 1)
        self.assertEqual(doc["summary"]["passed"], 2)

    def test_json_never_contains_credentials_or_endpoints(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["t"]):
            _exit_code, out = _run_main(
                ["--json"], {**CARACAL_ENV, **TODO_ENV, **FITEO_ENV}
            )
        for secret in (
            "caracal-secret-token",
            "todo-secret-token",
            "fiteo-secret-pat",
            "caracal.example.invalid",
            "127.0.0.1:9999",
            "fiteo.example.invalid",
        ):
            self.assertNotIn(secret, out)
        self.assertNotIn("Authorization", out)
        self.assertNotIn("Bearer", out)

    def test_service_selection_limits_json(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["t"]):
            exit_code, out = _run_main(
                ["--service", "todo-local", "--json"],
                {**CARACAL_ENV, **TODO_ENV, **FITEO_ENV},
            )
        self.assertEqual(exit_code, 0)
        doc = json.loads(out)
        self.assertEqual([s["name"] for s in doc["services"]], ["todo-local"])
        self.assertEqual(doc["summary"]["checked"], 1)


class HumanOutputRegressionTests(unittest.TestCase):
    def test_human_default_is_unchanged(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["alpha", "beta"]):
            exit_code, out = _run_main(
                [], {**CARACAL_ENV, **TODO_ENV, **FITEO_ENV}
            )
        self.assertEqual(exit_code, 0)
        lines = out.splitlines()
        self.assertEqual(
            lines[0],
            "PASS caracal-rag: HTTP 401 without credentials; initialize, "
            "tools/list and ping succeeded",
        )
        self.assertEqual(lines[1], "  tools (2): alpha, beta")
        self.assertEqual(lines[-1], "Summary: checked=3, failures=0")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(out)

    def test_mixed_status_human_output(self) -> None:
        with mock.patch.object(smoke, "smoke_service", return_value=["t"]):
            exit_code, out = _run_main([], {**CARACAL_ENV})
        self.assertEqual(exit_code, 0)
        self.assertIn("PASS caracal-rag:", out)
        self.assertIn(
            "SKIP todo-local: optional endpoint/token environment is missing", out
        )
        self.assertIn(
            "SKIP fiteo-backend: optional endpoint/token environment is missing", out
        )
        self.assertIn("Summary: checked=1, failures=0", out)


if __name__ == "__main__":
    unittest.main()
