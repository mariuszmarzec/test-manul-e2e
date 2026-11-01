#!/usr/bin/env python3
"""Load and validate the secret-free MCP E2E service contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "fixtures" / "service-contract.json"
EXPECTED_SERVICES = {"caracal-rag", "todo-local", "fiteo-backend"}


def load_contract() -> dict[str, Any]:
    with CONTRACT_PATH.open(encoding="utf-8") as handle:
        contract = json.load(handle)
    validate_contract(contract)
    return contract


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("contractVersion") != 1:
        raise ValueError("unsupported MCP E2E contract version")
    if contract.get("transport") != "streamable-http":
        raise ValueError("all configured services must use Streamable HTTP")

    services = contract.get("services")
    if not isinstance(services, dict) or set(services) != EXPECTED_SERVICES:
        raise ValueError("service names must be exactly caracal-rag, todo-local and fiteo-backend")

    endpoint_envs: set[str] = set()
    token_envs: set[str] = set()
    for name, service in services.items():
        endpoint = service.get("endpoint", {})
        auth = service.get("authentication", {})
        endpoint_env = endpoint.get("env")
        token_env = auth.get("tokenEnv")
        if not endpoint_env or not token_env:
            raise ValueError(f"{name} must define separate endpoint and token environment variables")
        if endpoint_env in endpoint_envs or token_env in token_envs:
            raise ValueError("endpoint and token environment variables must be unique per service")
        endpoint_envs.add(endpoint_env)
        token_envs.add(token_env)
        if auth.get("header") != "Authorization" or auth.get("scheme") != "Bearer":
            raise ValueError(f"{name} must use an explicit Bearer Authorization header")
        if not isinstance(service.get("required"), bool):
            raise ValueError(f"{name} must declare whether it is required")

    if services["caracal-rag"]["required"] is not True:
        raise ValueError("Caracal must remain a required dependency")
    if services["todo-local"]["required"] is not False:
        raise ValueError("Todo Local must remain optional")
    if services["fiteo-backend"]["required"] is not False:
        raise ValueError("Fiteo Backend must remain optional")
    if services["fiteo-backend"]["endpoint"].get("suffix") != "/mcp":
        raise ValueError("Fiteo Backend endpoint must append /mcp to FITEO_BASE_URL")


def resolve_endpoint(service: dict[str, Any], environ: dict[str, str]) -> str | None:
    endpoint = service["endpoint"]
    base = environ.get(endpoint["env"], "").strip()
    if not base:
        return None
    suffix = endpoint.get("suffix", "")
    if suffix and base.rstrip("/").endswith(suffix):
        return base.rstrip("/")
    return f"{base.rstrip('/')}{suffix}"
