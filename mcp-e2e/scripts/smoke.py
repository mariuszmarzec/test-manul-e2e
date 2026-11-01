#!/usr/bin/env python3
"""Read-only MCP Streamable HTTP smoke checks for the three independent services.

The script never reads ~/.manul/.env itself. Export the required environment
variables in the operator shell, then run this script. Token values and full
endpoint URLs are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from contract import load_contract, resolve_endpoint  # noqa: E402

DEFAULT_PROTOCOL_VERSION = "2025-06-18"
TIMEOUT_SECONDS = 20


class SmokeFailure(RuntimeError):
    pass


def _decode_response(content_type: str, body: bytes) -> list[dict[str, Any]]:
    text = body.decode("utf-8", errors="replace")
    if "text/event-stream" in content_type.lower():
        messages: list[dict[str, Any]] = []
        data_lines: list[str] = []
        for line in text.splitlines() + [""]:
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
            elif not line and data_lines:
                payload = "\n".join(data_lines)
                data_lines.clear()
                if payload and payload != "[DONE]":
                    try:
                        parsed = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(parsed, dict):
                        messages.append(parsed)
        return messages

    if not text.strip():
        return []
    parsed = json.loads(text)
    if isinstance(parsed, dict):
        return [parsed]
    raise SmokeFailure("MCP server returned an unexpected JSON response shape")


def _post(
    endpoint: str,
    method: str,
    request_id: int | None,
    params: dict[str, Any] | None,
    token: str | None,
    session_id: str | None = None,
    protocol_version: str | None = None,
) -> tuple[int, dict[str, str], list[dict[str, Any]]]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if request_id is not None:
        payload["id"] = request_id
    if params is not None:
        payload["params"] = params

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    if protocol_version:
        headers["MCP-Protocol-Version"] = protocol_version

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        response = urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        # Authentication failures often have a plain-text body. The HTTP
        # status is the evidence needed for the unauthenticated probe.
        # Never decode or echo that body because gateways may include details.
        return exc.code, dict(exc.headers.items()), []
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        # Do not include the URL or request headers: either can contain credentials.
        raise SmokeFailure(f"transport failed ({type(exc).__name__})") from None

    with response:
        body = response.read()
        return response.status, dict(response.headers.items()), _decode_response(
            response.headers.get("Content-Type", ""), body
        )


def _rpc_result(messages: list[dict[str, Any]], request_id: int, label: str) -> dict[str, Any]:
    for message in messages:
        if message.get("id") == request_id:
            if "error" in message:
                error = message["error"]
                code = error.get("code") if isinstance(error, dict) else "unknown"
                raise SmokeFailure(f"{label} returned JSON-RPC error code {code}")
            result = message.get("result")
            if isinstance(result, dict):
                return result
    raise SmokeFailure(f"{label} did not return a matching JSON-RPC result")


def smoke_service(name: str, endpoint: str, token: str, protocol_version: str) -> list[str]:
    init_params = {
        "protocolVersion": protocol_version,
        "capabilities": {},
        "clientInfo": {"name": "manul-mcp-e2e", "version": "0.1.0"},
    }

    # Authentication is tested independently from MCP initialization.
    unauth_status, _, _ = _post(
        endpoint, "initialize", 1, init_params, token=None
    )
    if unauth_status != 401:
        raise SmokeFailure(
            f"unauthenticated probe expected HTTP 401, received HTTP {unauth_status}"
        )

    status, headers, messages = _post(
        endpoint, "initialize", 2, init_params, token=token
    )
    if status != 200:
        raise SmokeFailure(
            f"authenticated initialize expected HTTP 200, received HTTP {status}"
        )
    init_result = _rpc_result(messages, 2, "initialize")
    negotiated_version = init_result.get("protocolVersion")
    if not negotiated_version:
        raise SmokeFailure("initialize response omitted protocolVersion")

    session_id = next(
        (value for key, value in headers.items() if key.lower() == "mcp-session-id"),
        None,
    )
    common = {
        "token": token,
        "session_id": session_id,
        "protocol_version": negotiated_version,
    }
    notify_status, _, _ = _post(
        endpoint, "notifications/initialized", None, {}, **common
    )
    if notify_status not in (200, 202, 204):
        raise SmokeFailure(
            f"initialized notification returned HTTP {notify_status}"
        )

    tools_status, _, tools_messages = _post(
        endpoint, "tools/list", 3, {}, **common
    )
    if tools_status != 200:
        raise SmokeFailure(
            f"tools/list expected HTTP 200, received HTTP {tools_status}"
        )
    tools_result = _rpc_result(tools_messages, 3, "tools/list")
    tools = tools_result.get("tools")
    if not isinstance(tools, list):
        raise SmokeFailure("tools/list response omitted the tools array")
    tool_names = sorted(
        tool["name"]
        for tool in tools
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    )

    ping_status, _, ping_messages = _post(
        endpoint, "ping", 4, {}, **common
    )
    if ping_status != 200:
        raise SmokeFailure(f"ping expected HTTP 200, received HTTP {ping_status}")
    _rpc_result(ping_messages, 4, "ping")
    return tool_names


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--service",
        choices=("all", "caracal-rag", "todo-local", "fiteo-backend"),
        default="all",
    )
    parser.add_argument(
        "--protocol-version",
        default=os.environ.get("MCP_E2E_PROTOCOL_VERSION", DEFAULT_PROTOCOL_VERSION),
    )
    args = parser.parse_args()

    services = load_contract()["services"]
    selected = (
        services if args.service == "all" else {args.service: services[args.service]}
    )
    failures = 0
    checked = 0

    for name, service in selected.items():
        endpoint = resolve_endpoint(service, os.environ)
        token_name = service["authentication"]["tokenEnv"]
        token = os.environ.get(token_name, "")
        if not endpoint or not token:
            if service["required"]:
                print(f"FAIL {name}: required endpoint/token environment is missing")
                failures += 1
            else:
                print(f"SKIP {name}: optional endpoint/token environment is missing")
            continue

        checked += 1
        try:
            tool_names = smoke_service(
                name, endpoint, token, args.protocol_version
            )
        except SmokeFailure as exc:
            print(f"FAIL {name}: {exc}")
            failures += 1
        except (ValueError, json.JSONDecodeError):
            print(f"FAIL {name}: invalid JSON or MCP response")
            failures += 1
        else:
            print(
                f"PASS {name}: HTTP 401 without credentials; initialize, "
                "tools/list and ping succeeded"
            )
            print(
                f"  tools ({len(tool_names)}): "
                f"{', '.join(tool_names) if tool_names else '(none advertised)'}"
            )

    print(f"Summary: checked={checked}, failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
