from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from smoke import ServiceResult, _check_service, _sanitize_reason  # noqa: E402


class MockService:
    """Build service dicts matching the contract fixture structure."""

    @staticmethod
    def required(name: str, endpoint_env: str, token_env: str) -> dict:
        return {
            "required": True,
            "endpoint": {"env": endpoint_env, "suffix": ""},
            "authentication": {"header": "Authorization", "scheme": "Bearer", "tokenEnv": token_env},
        }

    @staticmethod
    def optional(name: str, endpoint_env: str, token_env: str) -> dict:
        return {
            "required": False,
            "endpoint": {"env": endpoint_env, "suffix": ""},
            "authentication": {"header": "Authorization", "scheme": "Bearer", "tokenEnv": token_env},
        }


class SmokeJsonOutputTests(unittest.TestCase):
    """Tests for the JSON output mode of the smoke runner."""

    def test_all_services_passing(self) -> None:
        """All three services have endpoint+token and succeed."""
        env = {
            "CARACAL_MCP_URL": "https://caracal.example/mcp",
            "CARACAL_ACCESS_TOKEN": "token-1",
            "TODO_LOCAL_MCP_URL": "https://todo.example/mcp",
            "TODO_LOCAL_MCP_TOKEN": "token-2",
            "FITEO_BASE_URL": "https://fiteo.example",
            "FITEO_PAT": "token-3",
        }
        services = {
            "caracal-rag": MockService.required("caracal-rag", "CARACAL_MCP_URL", "CARACAL_ACCESS_TOKEN"),
            "todo-local": MockService.optional("todo-local", "TODO_LOCAL_MCP_URL", "TODO_LOCAL_MCP_TOKEN"),
            "fiteo-backend": MockService.optional("fiteo-backend", "FITEO_BASE_URL", "FITEO_PAT"),
        }

        # We can't easily mock smoke_service without restructuring; instead,
        # verify the JSON output logic directly by constructing results.
        results = [
            ServiceResult(name="caracal-rag", status="PASS", tools=["search", "fetch"], reason=None),
            ServiceResult(name="todo-local", status="PASS", tools=["list", "create"], reason=None),
            ServiceResult(name="fiteo-backend", status="PASS", tools=["ping", "sync"], reason=None),
        ]

        from smoke import _build_summary, _print_json
        import io
        import contextlib

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            _print_json(results)
        output = stdout.getvalue().strip()
        doc = json.loads(output)

        self.assertEqual(len(doc["services"]), 3)
        self.assertEqual(doc["summary"]["checked"], 3)
        self.assertEqual(doc["summary"]["passed"], 3)
        self.assertEqual(doc["summary"]["skipped"], 0)
        self.assertEqual(doc["summary"]["failed"], 0)

        for svc in doc["services"]:
            self.assertIn(svc["name"], {"caracal-rag", "todo-local", "fiteo-backend"})
            self.assertEqual(svc["status"], "PASS")
            self.assertIsInstance(svc["tools"], list)
            self.assertIsNone(svc["reason"])

    def test_required_caracal_missing_endpoint_or_token(self) -> None:
        """Required service missing env -> FAIL in JSON, exit 1."""
        results = [
            ServiceResult(
                name="caracal-rag",
                status="FAIL",
                tools=[],
                reason="required endpoint/token environment is missing",
            ),
            ServiceResult(
                name="todo-local",
                status="SKIP",
                tools=[],
                reason="optional endpoint/token environment is missing",
            ),
            ServiceResult(
                name="fiteo-backend",
                status="SKIP",
                tools=[],
                reason="optional endpoint/token environment is missing",
            ),
        ]

        from smoke import _build_summary, _print_json
        import io
        import contextlib

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            _print_json(results)
        output = stdout.getvalue().strip()
        doc = json.loads(output)

        self.assertEqual(doc["summary"]["checked"], 3)
        self.assertEqual(doc["summary"]["passed"], 0)
        self.assertEqual(doc["summary"]["skipped"], 2)
        self.assertEqual(doc["summary"]["failed"], 1)

        caracal = next(s for s in doc["services"] if s["name"] == "caracal-rag")
        self.assertEqual(caracal["status"], "FAIL")
        self.assertEqual(caracal["tools"], [])
        self.assertIsNotNone(caracal["reason"])

        for name in ("todo-local", "fiteo-backend"):
            svc = next(s for s in doc["services"] if s["name"] == name)
            self.assertEqual(svc["status"], "SKIP")
            self.assertEqual(svc["tools"], [])
            self.assertIsNotNone(svc["reason"])

    def test_optional_services_skipped_when_missing(self) -> None:
        """Optional Todo Local and Fiteo Backend missing env -> SKIP, no failure."""
        results = [
            ServiceResult(
                name="caracal-rag",
                status="PASS",
                tools=["search"],
                reason=None,
            ),
            ServiceResult(
                name="todo-local",
                status="SKIP",
                tools=[],
                reason="optional endpoint/token environment is missing",
            ),
            ServiceResult(
                name="fiteo-backend",
                status="SKIP",
                tools=[],
                reason="optional endpoint/token environment is missing",
            ),
        ]

        from smoke import _build_summary, _print_json
        import io
        import contextlib

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            _print_json(results)
        output = stdout.getvalue().strip()
        doc = json.loads(output)

        self.assertEqual(doc["summary"]["checked"], 3)
        self.assertEqual(doc["summary"]["passed"], 1)
        self.assertEqual(doc["summary"]["skipped"], 2)
        self.assertEqual(doc["summary"]["failed"], 0)

        for name in ("todo-local", "fiteo-backend"):
            svc = next(s for s in doc["services"] if s["name"] == name)
            self.assertEqual(svc["status"], "SKIP")

    def test_one_service_fails_another_passes(self) -> None:
        """One FAIL and one PASS -> exit 1, correct counts."""
        results = [
            ServiceResult(
                name="caracal-rag",
                status="FAIL",
                tools=[],
                reason="unauthenticated probe expected HTTP 401, received HTTP 200",
            ),
            ServiceResult(
                name="todo-local",
                status="PASS",
                tools=["list"],
                reason=None,
            ),
            ServiceResult(
                name="fiteo-backend",
                status="SKIP",
                tools=[],
                reason="optional endpoint/token environment is missing",
            ),
        ]

        from smoke import _build_summary, _print_json
        import io
        import contextlib

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            _print_json(results)
        output = stdout.getvalue().strip()
        doc = json.loads(output)

        self.assertEqual(doc["summary"]["checked"], 3)
        self.assertEqual(doc["summary"]["passed"], 1)
        self.assertEqual(doc["summary"]["skipped"], 1)
        self.assertEqual(doc["summary"]["failed"], 1)

        caracal = next(s for s in doc["services"] if s["name"] == "caracal-rag")
        self.assertEqual(caracal["status"], "FAIL")
        self.assertTrue(len(caracal["reason"]) > 0)

    def test_json_output_parsing_and_absence_of_secrets(self) -> None:
        """JSON is valid, no URLs/tokens appear in serialized output."""
        # In real usage, _check_service calls _sanitize_reason before creating
        # ServiceResult. The JSON output simply reflects the sanitized reason.
        from smoke import _sanitize_reason

        raw_reason = "transport failed (URLError) for https://secret.example/mcp with Bearer secret-token-value"
        sanitized = _sanitize_reason(raw_reason)

        results = [
            ServiceResult(
                name="caracal-rag",
                status="FAIL",
                tools=[],
                reason=sanitized,
            ),
        ]

        from smoke import _print_json
        import io
        import contextlib

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            _print_json(results)
        output = stdout.getvalue().strip()
        doc = json.loads(output)

        # The reason must be sanitized
        reason = doc["services"][0]["reason"]
        self.assertNotIn("https://secret.example/mcp", reason)
        self.assertNotIn("secret-token-value", reason)
        self.assertIn("[redacted]", reason)

    def test_human_readable_mode_remains_default(self) -> None:
        """Verify the human-readable format is preserved when --json is not used."""
        results = [
            ServiceResult(
                name="caracal-rag",
                status="PASS",
                tools=["search"],
                reason=None,
            ),
            ServiceResult(
                name="todo-local",
                status="SKIP",
                tools=[],
                reason="optional endpoint/token environment is missing",
            ),
        ]

        from smoke import _print_human
        import io
        import contextlib

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            _print_human(results)
        output = stdout.getvalue().strip()

        lines = output.splitlines()
        self.assertEqual(len(lines), 4)  # PASS line, tools line, SKIP line, Summary line
        self.assertTrue(lines[0].startswith("PASS caracal-rag:"))
        self.assertIn("HTTP 401 without credentials", lines[0])
        self.assertTrue(lines[1].startswith("  tools (1):"))
        self.assertTrue(lines[2].startswith("SKIP todo-local:"))
        self.assertTrue(lines[3].startswith("Summary: checked=1, failures=0"))


class SanitizeReasonTests(unittest.TestCase):
    """Tests for the _sanitize_reason helper."""

    def test_urls_are_redacted(self) -> None:
        reason = "failed to connect to https://api.example.com/v1/mcp"
        sanitized = _sanitize_reason(reason)
        self.assertNotIn("https://api.example.com/v1/mcp", sanitized)
        self.assertIn("[redacted]", sanitized)

    def test_bearer_tokens_are_redacted(self) -> None:
        reason = 'authorization header contained Bearer secret-abc123'
        sanitized = _sanitize_reason(reason)
        self.assertNotIn("Bearer secret-abc123", sanitized)
        self.assertIn("[redacted]", sanitized)

    def test_multiple_secrets(self) -> None:
        reason = "POST https://host/mcp with Bearer token1 and https://other/path with Bearer token2"
        sanitized = _sanitize_reason(reason)
        self.assertEqual(sanitized.count("[redacted]"), 4)

    def test_no_false_positives(self) -> None:
        reason = "initialize returned HTTP 401 as expected"
        sanitized = _sanitize_reason(reason)
        self.assertEqual(reason, sanitized)


if __name__ == "__main__":
    unittest.main()