#!/usr/bin/env python3
"""Read-only MCP Streamable HTTP smoke checks for the three independent services.

The script never reads ~/.manul/.env itself. Export the required environment
variables in the operator shell, then run this script. Token values and full
endpoint URLs are never printed.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from contract import load_contract, resolve_endpoint  # noqa: E402

DEFAULT_PROTOCOL_VERSION = "2025-06-18"
TIMEOUT_SECONDS = 20

# Patterns that must never appear in JSON output reasons.
_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"Bearer\s+[^\s\"'<>]+", re.IGNORECASE)


def _sanitize_reason(reason: str) -> str:
    """Remove any potentially sensitive data from a reason string."""
    sanitized = _URL_PATTERN.sub("[redacted]", reason)
    sanitized = _BEARER_PATTERN.sub("[redacted]", sanitized)
    return sanitized


class SmokeFailure(RuntimeError):
    pass


@dataclass
class ServiceResult:
    """Structured result for a single service smoke check."""

    name: str
    status: str  # "PASS", "SKIP", or "FAIL"
    tools: list[str]
    reason: str | None  # null on PASS; sanitized error detail on FAIL/SKIP


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


def is_loopback_http_url(endpoint: str) -> bool:
    """Return true only for an absolute HTTP URL whose host is loopback."""
    try:
        parsed = urlsplit(endpoint)
        host = parsed.hostname
        if parsed.scheme != "http" or not host:
            return False
        if parsed.username or parsed.password or parsed.fragment:
            return False
        if host.casefold() == "localhost":
            return True
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def smoke_service(
    name: str,
    endpoint: str,
    token: str | None,
    protocol_version: str,
    authentication_scheme: str = "Bearer",
) -> list[str]:
    init_params = {
        "protocolVersion": protocol_version,
        "capabilities": {},
        "clientInfo": {"name": "manul-mcp-e2e", "version": "0.1.0"},
    }

    # Local Todo Desktop MCP is intentionally unauthenticated and loopback-only.
    # Remote services use an independent Bearer token and must reject an
    # unauthenticated initialize request before the authenticated handshake.
    if authentication_scheme == "none":
        status, headers, messages = _post(
            endpoint, "initialize", 1, init_params, token=None
        )
        if status != 200:
            raise SmokeFailure(
                f"unauthenticated initialize expected HTTP 200, received HTTP {status}"
            )
        initialize_id = 1
        request_token = None
    elif authentication_scheme == "Bearer":
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
        initialize_id = 2
        request_token = token
    else:
        raise SmokeFailure("unsupported MCP authentication scheme")

    init_result = _rpc_result(messages, initialize_id, "initialize")
    negotiated_version = init_result.get("protocolVersion")
    if not negotiated_version:
        raise SmokeFailure("initialize response omitted protocolVersion")

    session_id = next(
        (value for key, value in headers.items() if key.lower() == "mcp-session-id"),
        None,
    )
    common = {
        "token": request_token,
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

    tools_id = initialize_id + 1
    tools_status, _, tools_messages = _post(
        endpoint, "tools/list", tools_id, {}, **common
    )
    if tools_status != 200:
        raise SmokeFailure(
            f"tools/list expected HTTP 200, received HTTP {tools_status}"
        )
    tools_result = _rpc_result(tools_messages, tools_id, "tools/list")
    tools = tools_result.get("tools")
    if not isinstance(tools, list):
        raise SmokeFailure("tools/list response omitted the tools array")
    tool_names = sorted(
        tool["name"]
        for tool in tools
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    )

    if name == "todo-local":
        # Exercise the exact read-only business tool used by Manul's poller.
        # No Authorization header is sent and no task mutation is performed.
        if "list_tasks" not in tool_names:
            raise SmokeFailure("Todo Desktop MCP does not advertise the required list_tasks tool")
        list_tasks_id = initialize_id + 2
        list_status, _, list_messages = _post(
            endpoint,
            "tools/call",
            list_tasks_id,
            {"name": "list_tasks", "arguments": {}},
            **common,
        )
        if list_status != 200:
            raise SmokeFailure(
                f"read-only list_tasks expected HTTP 200, received HTTP {list_status}"
            )
        list_result = _rpc_result(list_messages, list_tasks_id, "list_tasks")
        if list_result.get("isError") is True:
            raise SmokeFailure("read-only list_tasks returned an MCP tool error")
        content = list_result.get("content")
        text_items = [
            item["text"]
            for item in (content if isinstance(content, list) else [])
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ]
        if not text_items:
            raise SmokeFailure("read-only list_tasks returned no text content")
        try:
            tasks = json.loads(text_items[0])
        except json.JSONDecodeError:
            raise SmokeFailure("read-only list_tasks returned invalid JSON") from None
        if not isinstance(tasks, list):
            raise SmokeFailure("read-only list_tasks did not return a task array")
        ping_id = initialize_id + 3
    else:
        ping_id = initialize_id + 2

    ping_status, _, ping_messages = _post(
        endpoint, "ping", ping_id, {}, **common
    )
    if ping_status != 200:
        raise SmokeFailure(f"ping expected HTTP 200, received HTTP {ping_status}")
    _rpc_result(ping_messages, ping_id, "ping")
    return tool_names


def _check_service(
    name: str,
    service: dict[str, Any],
    protocol_version: str,
    env: dict[str, str],
) -> ServiceResult:
    """Run the smoke check for a single service and return a ServiceResult."""
    endpoint = resolve_endpoint(service, env)
    authentication = service.get("authentication", {})
    authentication_scheme = authentication.get("scheme", "Bearer")
    token_name = authentication.get("tokenEnv")
    token = env.get(token_name, "") if token_name else None
    missing_credentials = authentication_scheme == "Bearer" and not token

    if not endpoint or missing_credentials:
        missing = "endpoint" if not endpoint else "Bearer token"
        if service["required"]:
            return ServiceResult(
                name=name,
                status="FAIL",
                tools=[],
                reason=_sanitize_reason(f"required MCP {missing} environment is missing"),
            )
        return ServiceResult(
            name=name,
            status="SKIP",
            tools=[],
            reason=_sanitize_reason(f"optional MCP {missing} environment is missing"),
        )

    if authentication_scheme == "none" and not is_loopback_http_url(endpoint):
        return ServiceResult(
            name=name,
            status="FAIL",
            tools=[],
            reason="unauthenticated local MCP endpoint must be an HTTP loopback URL",
        )

    try:
        tool_names = smoke_service(
            name, endpoint, token, protocol_version, authentication_scheme
        )
    except SmokeFailure as exc:
        return ServiceResult(
            name=name,
            status="FAIL",
            tools=[],
            reason=_sanitize_reason(str(exc)),
        )
    except (ValueError, json.JSONDecodeError):
        return ServiceResult(
            name=name,
            status="FAIL",
            tools=[],
            reason=_sanitize_reason("invalid JSON or MCP response"),
        )

    return ServiceResult(
        name=name,
        status="PASS",
        tools=tool_names,
        reason=None,
    )


def _build_summary(results: list[ServiceResult]) -> dict[str, int]:
    """Build summary counts.

    ``checked`` is the total number of selected services. The remaining
    counts partition that total: ``checked == passed + skipped + failed``.
    """
    return {
        "checked": len(results),
        "passed": sum(1 for r in results if r.status == "PASS"),
        "skipped": sum(1 for r in results if r.status == "SKIP"),
        "failed": sum(1 for r in results if r.status == "FAIL"),
    }


def _print_human(results: list[ServiceResult]) -> None:
    """Print the existing human-readable output, preserving the original format."""
    for result in results:
        if result.status == "PASS":
            if result.name == "todo-local":
                print(
                    "PASS todo-local: unauthenticated initialize, tools/list, "
                    "read-only list_tasks and ping succeeded"
                )
            else:
                print(
                    f"PASS {result.name}: MCP initialize, tools/list and ping succeeded"
                )
            print(
                f"  tools ({len(result.tools)}): "
                f"{', '.join(result.tools) if result.tools else '(none advertised)'}"
            )
        elif result.status == "FAIL":
            print(f"FAIL {result.name}: {result.reason}")
        elif result.status == "SKIP":
            print(f"SKIP {result.name}: {result.reason}")

    # Preserve the original summary semantics: ``checked`` counts only the
    # services that actually ran (i.e. were not skipped).
    ran = sum(1 for r in results if r.status != "SKIP")
    failures = sum(1 for r in results if r.status == "FAIL")
    print(f"Summary: checked={ran}, failures={failures}")


def _print_json(results: list[ServiceResult]) -> None:
    """Print exactly one valid JSON document to stdout."""
    document = {
        "services": [
            {
                "name": result.name,
                "status": result.status,
                "tools": result.tools,
                "reason": result.reason,
            }
            for result in results
        ],
        "summary": _build_summary(results),
    }
    print(json.dumps(document, sort_keys=False))


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
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON document to stdout instead of "
        "human-readable status lines",
    )
    args = parser.parse_args()

    services = load_contract()["services"]
    selected = (
        services if args.service == "all" else {args.service: services[args.service]}
    )

    results = [
        _check_service(name, service, args.protocol_version, os.environ)
        for name, service in selected.items()
    ]

    if args.json:
        _print_json(results)
    else:
        _print_human(results)

    summary = _build_summary(results)
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
