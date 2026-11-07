# MCP E2E harness

This suite is isolated from the repository's Flask/WebFrame examples and from
standalone-manul-e2e/. It verifies three independent MCP dependencies used by
the Manul/OpenCode path.

| Server ID | Purpose | Endpoint environment | Credential environment | Required |
|---|---|---|---|---|
| caracal-rag | Manul retrieval/context service | CARACAL_MCP_URL | CARACAL_ACCESS_TOKEN | Yes |
| todo-local | Todo Desktop local MCP, direct or WSL bridge | TODO_LOCAL_MCP_URL | TODO_LOCAL_MCP_TOKEN | No |
| fiteo-backend | Remote Fiteo backend MCP, under /mcp | FITEO_BASE_URL | FITEO_PAT | No |

The service contract fixture contains no endpoint or token values. It is
deliberately not an OpenCode config template: the supported OpenCode schema and
OPENCODE_CONFIG_CONTENT behavior must first be verified against the exact
OpenCode executable installed on the operator host.

## Offline checks

Run from the repository root with Python 3 standard library only:

    python3 -m unittest discover -s mcp-e2e/tests -v

These checks validate service separation, required/optional semantics, unique
credential environment names, Fiteo endpoint construction and JSON/SSE response
decoding. They do not contact any live service.

## Read-only live MCP smoke checks

The smoke client checks each configured endpoint in this order:

1. An unauthenticated initialize request must receive HTTP 401.
2. A request with that service's own Bearer token must initialize successfully.
3. notifications/initialized, tools/list and ping must succeed.
4. The script prints server/tool names and HTTP outcomes, but never prints
   tokens or full endpoint URLs.

It does not call business tools or mutate Todo data.

The script does not read .env files. Export approved operator variables in the
current shell using the operator's normal secret-handling procedure, then run:

    python3 mcp-e2e/scripts/smoke.py

To check a single service:

    python3 mcp-e2e/scripts/smoke.py --service caracal-rag
    python3 mcp-e2e/scripts/smoke.py --service todo-local
    python3 mcp-e2e/scripts/smoke.py --service fiteo-backend

### Machine-readable JSON output

Add `--json` to emit a single JSON document to stdout instead of human-readable
status lines. The JSON contains no endpoint URLs, tokens, Authorization headers,
request bodies, or raw server responses. Error reasons are sanitized.

    python3 mcp-e2e/scripts/smoke.py --json

Example output (secret-free):

```json
{
  "services": [
    {
      "name": "caracal-rag",
      "status": "PASS",
      "tools": ["search", "fetch"],
      "reason": null
    },
    {
      "name": "todo-local",
      "status": "SKIP",
      "tools": [],
      "reason": "optional endpoint/token environment is missing"
    },
    {
      "name": "fiteo-backend",
      "status": "FAIL",
      "tools": [],
      "reason": "unauthenticated probe expected HTTP 401, received HTTP 200"
    }
  ],
  "summary": {
    "checked": 3,
    "passed": 1,
    "skipped": 1,
    "failed": 1
  }
}
```

Status values:
- `PASS`: service responded correctly to unauthenticated probe, initialize, tools/list, and ping.
- `SKIP`: optional service (Todo Local or Fiteo Backend) missing its endpoint or token.
- `FAIL`: required service missing its endpoint/token, or any service returned an MCP/transport/protocol error.

Exit code is `1` if any selected service has status `FAIL`; otherwise `0`. Optional
services being skipped do not cause a failure exit code.

TODO_LOCAL_MCP_URL is normally exported by Aicode after it determines whether
the direct Todo Desktop endpoint or WSL bridge is usable. The Fiteo URL is
built as FITEO_BASE_URL plus /mcp; do not put the PAT in the URL. The default
MCP protocol version is 2025-06-18; override it with
MCP_E2E_PROTOCOL_VERSION only when the installed OpenCode/client contract
requires another negotiated version.

## Test phases and safety boundaries

- Contract/mock tests: run in CI without credentials or network access.
- Live read-only MCP smoke: run only after the clean Manul installation gate is
  fully green. Uses separate credentials per server; validates unauthenticated
  rejection, authenticated transport, initialization and tool discovery.
- Service-specific integration: later phase for Fiteo Todo CRUD, PAT
  identity/expiry/revocation, Todo Desktop token rotation, and service
  independence. It requires a dedicated test account/environment. Cleanup may
  delete only records created by that exact test run.
- Host-specific: WSL/Windows bridge, native Linux/macOS behavior, daemon task
  freshness and task isolation. These cannot be represented as successful by
  ordinary Linux CI.

Never pass secrets on command-line arguments, write them to fixtures, print
request headers, upload .env, or store runtime logs containing credentials as
CI artifacts. Do not execute create/update/delete business tools until a
separate dedicated test-account CRUD suite and cleanup guard are reviewed.

## Runtime contract checks still pending

The E2E plan also requires verifying that Aicode leaves the global OpenCode
config unchanged, that Fiteo has the distinct server identity fiteo-backend,
and that task-scoped configuration is supported by the exact installed
OpenCode version. Any runtime fixes belong in a separate PR; this harness PR
does not modify globalskills or Manul runtime code.
