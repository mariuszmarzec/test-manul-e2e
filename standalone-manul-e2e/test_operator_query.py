"""E2E coverage for Manul's isolated one-shot operator query mode.

The selected Manul ref is cloned into pytest's temporary directory. All runtime
files, logs, databases and fake CLIs are isolated; no operator ~/.manul state or
live daemon/Gateway is read or modified.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

MANUL_REPOSITORY = "https://github.com/mariuszmarzec/manul.git"
MANUL_REF = os.environ.get("MANUL_E2E_REF", "master")
SKILL_RELATIVE = Path("skills/manul-github-bot")


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}"
        )
    return result


@pytest.fixture(scope="session")
def manul_skill(tmp_path_factory: pytest.TempPathFactory) -> Path:
    checkout = tmp_path_factory.mktemp("manul-operator-query") / "manul"
    run(
        [
            "git", "clone", "--quiet", "--depth", "1", "--branch",
            MANUL_REF, MANUL_REPOSITORY, str(checkout),
        ]
    )
    skill = checkout / SKILL_RELATIVE
    assert (skill / "manul-query.sh").is_file()
    assert (skill / "manul-operator-context.py").is_file()
    assert (skill / "agent-executor.sh").is_file()
    return skill


def make_opencode_fixture(
    *,
    skill: Path,
    fixture_root: Path,
    workspace_base: Path,
    task_workspace: Path,
) -> tuple[dict[str, str], Path, Path]:
    home = fixture_root / "home"
    runtime = fixture_root / "runtime"
    fake_bin = fixture_root / "bin"
    tmp_dir = fixture_root / "tmp"
    logs = fixture_root / "logs"
    tasks = fixture_root / "tasks"
    config_dir = home / ".config" / "opencode"
    for directory in (home, runtime, fake_bin, tmp_dir, logs, tasks, config_dir):
        directory.mkdir(parents=True, exist_ok=True)

    fake_opencode = fake_bin / "opencode"
    fake_opencode.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_opencode.chmod(0o755)

    prompt = fixture_root / "prompt.md"
    prompt.write_text("Use the supplied snapshot only.\n", encoding="utf-8")
    operator_config = config_dir / "opencode.json"
    operator_config.write_text(
        json.dumps({"permissions": [], "mcp": {"servers": {}}}),
        encoding="utf-8",
    )
    manul_config = runtime / "config.json"
    manul_config.write_text('{"agents":["researcher"]}', encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "PATH": f"{fake_bin}{os.pathsep}{env.get('PATH', '')}",
            "TMPDIR": str(tmp_dir),
            "OPENCODE_BIN": str(fake_opencode),
            "OPENCODE_CONFIG": str(operator_config),
            "AGENT_RUNTIME": "opencode",
            "MANUL_DIR": str(runtime),
            "MANUL_CONFIG": str(manul_config),
            "MANUL_WORKSPACE": str(workspace_base),
            "MANUL_TASKS_DIR": str(tasks),
            "MANUL_TASK_LOG_DIR": str(logs),
            "MANUL_TASK_WORKSPACE_ROOT": str(task_workspace),
            "MANUL_TASK_WORKDIR": "",
            "MANUL_TASK_EXECUTION_KIND": "operator_query",
            "FITEO_BASE_URL": "",
            "FITEO_MANUL_PAT": "",
            "TODO_LOCAL_MCP_URL": "",
        }
    )
    return env, prompt, operator_config


def run_opencode_preflight(
    *,
    skill: Path,
    fixture_root: Path,
    task_workspace: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "bash", str(skill / "opencode-adapter.sh"),
            "--task-id", "operator-query-e2e",
            "--prompt", str(fixture_root / "prompt.md"),
            "--workspace", str(task_workspace),
            "--attempt", "1",
            "--timeout", "30",
            "--session-id", "",
            "--stdout-file", str(fixture_root / "adapter.stdout"),
            "--stderr-file", str(fixture_root / "adapter.stderr"),
            "--preflight-only",
        ],
        env=env,
        check=False,
    )


def test_operator_query_unit_regressions_run_in_isolated_checkout(
    manul_skill: Path,
) -> None:
    run(["python3", str(manul_skill / "test_manul_operator_context.py")])
    run(["bash", str(manul_skill / "test_manul_operator_query.sh")])


def test_opencode_adapter_accepts_only_operator_query_scratch_root(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    workspace_base = tmp_path / "workspace"
    operator_root = workspace_base / "operator-query"
    task_workspace = operator_root / "oq-e2e"
    task_workspace.mkdir(parents=True)
    env, prompt, operator_config = make_opencode_fixture(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        workspace_base=workspace_base,
        task_workspace=task_workspace,
    )
    before = hashlib.sha256(operator_config.read_bytes()).hexdigest()

    result = run_opencode_preflight(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        task_workspace=task_workspace,
        env=env,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "READY"
    assert payload["diagnostics"]["agent_started"] is False
    assert hashlib.sha256(operator_config.read_bytes()).hexdigest() == before


def test_opencode_adapter_rejects_workspace_outside_operator_query_namespace(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    workspace_base = tmp_path / "workspace"
    invalid_workspace = workspace_base / "ws-regular"
    invalid_workspace.mkdir(parents=True)
    env, prompt, _ = make_opencode_fixture(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        workspace_base=workspace_base,
        task_workspace=invalid_workspace,
    )

    result = run_opencode_preflight(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        task_workspace=invalid_workspace,
        env=env,
    )
    assert result.returncode == 66, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "FAILED"
    assert "operator query workspace" in payload["summary"]


def test_opencode_adapter_fails_closed_on_reserved_agent_collision(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    workspace_base = tmp_path / "workspace"
    task_workspace = workspace_base / "operator-query" / "oq-e2e"
    task_workspace.mkdir(parents=True)
    env, prompt, operator_config = make_opencode_fixture(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        workspace_base=workspace_base,
        task_workspace=task_workspace,
    )
    operator_config.write_text(
        json.dumps({
            "permissions": [],
            "mcp": {"servers": {}},
            "agent": {
                "manul-operator-query": {
                    "mode": "primary",
                    "tools": {"*": True},
                }
            },
        }),
        encoding="utf-8",
    )
    before = hashlib.sha256(operator_config.read_bytes()).hexdigest()

    result = run_opencode_preflight(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        task_workspace=task_workspace,
        env=env,
    )
    assert result.returncode == 65, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "FAILED"
    assert "reserved OpenCode agent" in payload["summary"]
    assert hashlib.sha256(operator_config.read_bytes()).hexdigest() == before


def test_opencode_adapter_rejects_symlinked_operator_query_parent(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    workspace_base = tmp_path / "workspace"
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace_base).mkdir()
    (workspace_base / "operator-query").symlink_to(outside, target_is_directory=True)
    task_workspace = outside / "oq-e2e"
    task_workspace.mkdir()
    env, prompt, _ = make_opencode_fixture(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        workspace_base=workspace_base,
        task_workspace=task_workspace,
    )

    result = run_opencode_preflight(
        skill=manul_skill,
        fixture_root=tmp_path / "fixture",
        task_workspace=task_workspace,
        env=env,
    )
    assert result.returncode == 66, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "FAILED"
    assert "operator query workspace" in payload["summary"]
    assert list(outside.iterdir()) == [task_workspace]
