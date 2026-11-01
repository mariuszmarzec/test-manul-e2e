from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from contract import load_contract, resolve_endpoint, validate_contract  # noqa: E402


class ServiceContractTests(unittest.TestCase):
    def test_contract_declares_three_independent_services(self) -> None:
        contract = load_contract()
        self.assertEqual(
            set(contract["services"]),
            {"caracal-rag", "todo-local", "fiteo-backend"},
        )

    def test_endpoint_and_token_environment_variables_are_unique(self) -> None:
        services = load_contract()["services"]
        endpoints = [s["endpoint"]["env"] for s in services.values()]
        tokens = [s["authentication"]["tokenEnv"] for s in services.values()]
        self.assertEqual(len(endpoints), len(set(endpoints)))
        self.assertEqual(len(tokens), len(set(tokens)))
        self.assertTrue(set(endpoints).isdisjoint(tokens))

    def test_caracal_is_required_and_other_services_are_optional(self) -> None:
        services = load_contract()["services"]
        self.assertTrue(services["caracal-rag"]["required"])
        self.assertFalse(services["todo-local"]["required"])
        self.assertFalse(services["fiteo-backend"]["required"])

    def test_fiteo_endpoint_appends_mcp_once(self) -> None:
        service = load_contract()["services"]["fiteo-backend"]
        self.assertEqual(
            resolve_endpoint(service, {"FITEO_BASE_URL": "https://fiteo.example.invalid/"}),
            "https://fiteo.example.invalid/mcp",
        )
        self.assertEqual(
            resolve_endpoint(service, {"FITEO_BASE_URL": "https://fiteo.example.invalid/mcp"}),
            "https://fiteo.example.invalid/mcp",
        )

    def test_fixture_contains_no_credential_values_or_live_endpoints(self) -> None:
        raw = (ROOT / "fixtures" / "service-contract.json").read_text(encoding="utf-8")
        contract = json.loads(raw)
        for service in contract["services"].values():
            self.assertIn("env", service["endpoint"])
            self.assertIn("tokenEnv", service["authentication"])
            self.assertNotIn("token", service["authentication"])
            self.assertNotIn("value", service["authentication"])
        self.assertNotIn("Bearer ", raw)
        self.assertNotIn("https://", raw)

    def test_invalid_shared_token_variable_is_rejected(self) -> None:
        contract = load_contract()
        contract["services"]["todo-local"]["authentication"]["tokenEnv"] = "FITEO_PAT"
        with self.assertRaises(ValueError):
            validate_contract(contract)


if __name__ == "__main__":
    unittest.main()
