"""Regression E2E for Manul's isolated Todo report-only workspace.

The tests clone the selected Manul ref and execute its real workspace helper
and OpenCode adapter preflight in disposable directories. They use a fake
OpenCode executable and never start Manul's daemon, mutate Todo data, or touch
the operator's runtime.
"""
from __future__ import annotations

import json
import os
import re
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
    checkout = tmp_path_factory.mktemp("manul-report-only") / "manul"
    run(
        [
            "git",
            "clone",
            "--quiet",
            "--depth",
            "1",
            "--branch",
            MANUL_REF,
            MANUL_REPOSITORY,
            str(checkout),
        ]
    )
    skill = checkout / SKILL_RELATIVE
    assert (skill / "manul-daemon.sh").is_file()
    assert (skill / "opencode-adapter.sh").is_file()
    return skill


def test_manul_runtime_entrypoint_scripts_remain_executable(manul_skill: Path) -> None:
    for script_name in ("manul-daemon.sh", "opencode-adapter.sh"):
        script = manul_skill / script_name
        assert script.stat().st_mode & 0o111, (
            f"{script_name} lost its executable bit in the Manul Git tree"
        )


def extract_function(source: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(name)}\(\) \{{\n.*?^\}}$",
        source,
    )
    assert match is not None, f"Could not find {name}() in Manul daemon"
    return match.group(0)


def test_report_only_allocator_uses_private_non_pool_namespace_and_cleans(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")
    create_function = extract_function(daemon, "report_only_workspace_create")
    cleanup_function = extract_function(daemon, "report_only_workspace_cleanup")
    workspace_base = tmp_path / "workspace"
    workspace_base.mkdir()

    script = f"""
set -euo pipefail
{create_function}
{cleanup_function}
scratch="$(report_only_workspace_create)"
[[ "$scratch" == "$MANUL_WORKSPACE/report-only/ws-"* ]]
[[ "$(dirname -- "$scratch")" == "$MANUL_WORKSPACE/report-only" ]]
[[ "$(stat -c '%a' "$scratch")" == "700" ]]
report_only_workspace_cleanup "$scratch"
[[ ! -e "$scratch" ]]
printf '%s\\n' "$scratch"
"""
    env = os.environ.copy()
    env["MANUL_WORKSPACE"] = str(workspace_base)
    result = run(["bash", "-c", script], env=env)
    scratch = Path(result.stdout.strip())
    assert scratch.parent == workspace_base / "report-only"
    assert not scratch.exists()
    assert not (workspace_base / scratch.name).exists()


def test_report_only_allocator_rejects_symlinked_parent(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")
    create_function = extract_function(daemon, "report_only_workspace_create")
    workspace_base = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace_base.mkdir()
    outside.mkdir()
    (workspace_base / "report-only").symlink_to(outside, target_is_directory=True)

    script = f"""
{create_function}
report_only_workspace_create
"""
    env = os.environ.copy()
    env["MANUL_WORKSPACE"] = str(workspace_base)
    result = run(["bash", "-c", script], env=env, check=False)
    assert result.returncode != 0
    assert list(outside.iterdir()) == []


def adapter_environment(
    *,
    fixture_root: Path,
    skill: Path,
    workspace_base: Path,
    task_workspace: Path,
    execution_kind: str,
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

    opencode = fake_bin / "opencode"
    opencode.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    opencode.chmod(0o755)

    prompt = fixture_root / "prompt.md"
    prompt.write_text("Preflight only; do not start a model.\n", encoding="utf-8")
    operator_config = config_dir / "opencode.json"
    operator_config.write_text(
        json.dumps({"permissions": [], "mcp": {"servers": {}}}),
        encoding="utf-8",
    )
    manul_config = runtime / "config.json"
    manul_config.write_text("{}", encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "PATH": f"{fake_bin}{os.pathsep}{env.get('PATH', '')}",
            "TMPDIR": str(tmp_dir),
            "OPENCODE_BIN": str(opencode),
            "OPENCODE_CONFIG": str(operator_config),
            "AGENT_RUNTIME": "opencode",
            "MANUL_DIR": str(runtime),
            "MANUL_CONFIG": str(manul_config),
            "MANUL_WORKSPACE": str(workspace_base),
            "MANUL_TASKS_DIR": str(tasks),
            "MANUL_TASK_LOG_DIR": str(logs),
            "MANUL_TASK_WORKSPACE_ROOT": str(task_workspace),
            "MANUL_TASK_WORKDIR": "",
            "MANUL_TASK_EXECUTION_KIND": execution_kind,
        }
    )
    return env, prompt, fixture_root


def run_adapter_preflight(
    *,
    skill: Path,
    fixture_root: Path,
    env: dict[str, str],
    prompt: Path,
    task_workspace: Path,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "bash",
            str(skill / "opencode-adapter.sh"),
            "--task-id",
            "report-only-regression",
            "--prompt",
            str(prompt),
            "--workspace",
            str(task_workspace),
            "--attempt",
            "1",
            "--timeout",
            "30",
            "--session-id",
            "",
            "--stdout-file",
            str(fixture_root / "adapter.stdout"),
            "--stderr-file",
            str(fixture_root / "adapter.stderr"),
            "--preflight-only",
        ],
        env=env,
        check=False,
    )


def test_opencode_adapter_accepts_explicit_report_only_scratch_root(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    workspace_base = tmp_path / "workspace"
    report_root = workspace_base / "report-only"
    report_root.mkdir(parents=True)
    report_workspace = report_root / "ws-report-only-fixture"
    report_workspace.mkdir()
    env, prompt, fixture_root = adapter_environment(
        fixture_root=tmp_path / "fixture",
        skill=manul_skill,
        workspace_base=workspace_base,
        task_workspace=report_workspace,
        execution_kind="report_only",
    )

    result = run_adapter_preflight(
        skill=manul_skill,
        fixture_root=fixture_root,
        env=env,
        prompt=prompt,
        task_workspace=report_workspace,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "READY"
    assert payload["diagnostics"]["agent_started"] is False


def test_opencode_adapter_preserves_regular_workspace_lease_validation(
    manul_skill: Path,
    tmp_path: Path,
) -> None:
    workspace_base = tmp_path / "workspace"
    regular_workspace = workspace_base / "ws-regular-lease"
    regular_workspace.mkdir(parents=True)
    env, prompt, fixture_root = adapter_environment(
        fixture_root=tmp_path / "fixture",
        skill=manul_skill,
        workspace_base=workspace_base,
        task_workspace=regular_workspace,
        execution_kind="repository",
    )

    result = run_adapter_preflight(
        skill=manul_skill,
        fixture_root=fixture_root,
        env=env,
        prompt=prompt,
        task_workspace=regular_workspace,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "READY"


@pytest.mark.parametrize(
    ("workspace_location", "execution_kind", "expected_summary"),
    [
        ("tmp", "report_only", "report-only workspace is not a direct scratch directory"),
        ("report_only", "repository", "not a direct lease under the configured MANUL_WORKSPACE"),
        ("nested_report_only", "report_only", "report-only workspace is not a direct scratch directory"),
    ],
)
def test_opencode_adapter_rejects_wrong_workspace_boundaries(
    manul_skill: Path,
    tmp_path: Path,
    workspace_location: str,
    execution_kind: str,
    expected_summary: str,
) -> None:
    workspace_base = tmp_path / "workspace"
    (workspace_base / "report-only").mkdir(parents=True)
    tmp_workspace = tmp_path / "manul-report-only.fixture"
    tmp_workspace.mkdir()
    report_workspace = workspace_base / "report-only" / "ws-report-only-fixture"
    report_workspace.mkdir()
    nested_report_workspace = (
        workspace_base / "report-only" / "nested" / "ws-report-only-fixture"
    )
    nested_report_workspace.mkdir(parents=True)
    workspace = {
        "tmp": tmp_workspace,
        "report_only": report_workspace,
        "nested_report_only": nested_report_workspace,
    }[workspace_location]

    env, prompt, fixture_root = adapter_environment(
        fixture_root=tmp_path / "fixture",
        skill=manul_skill,
        workspace_base=workspace_base,
        task_workspace=workspace,
        execution_kind=execution_kind,
    )
    result = run_adapter_preflight(
        skill=manul_skill,
        fixture_root=fixture_root,
        env=env,
        prompt=prompt,
        task_workspace=workspace,
    )

    assert result.returncode == 66, result.stdout
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "FAILED"
    assert expected_summary in payload["summary"]
