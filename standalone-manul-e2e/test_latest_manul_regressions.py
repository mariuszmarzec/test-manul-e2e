"""Run Manul's latest protocol/recovery/Todo regressions from the E2E repo.

The selected Manul ref is cloned once into pytest's disposable workspace. Each
canonical shell suite then runs with a private HOME/TMPDIR and fake provider
boundaries defined by that suite. No operator runtime, database, daemon,
credentials, live Todo/Fiteo MCP, or production GitHub writes are involved.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

MANUL_REPOSITORY = "https://github.com/mariuszmarzec/manul.git"
MANUL_REF = os.environ.get("MANUL_E2E_REF", "master")
SKILL_RELATIVE = Path("skills/manul-github-bot")

SENSITIVE_PREFIXES = (
    "GH_", "GITHUB_", "FITEO_", "TODO_", "MANUL_", "OPENCODE_",
    "OPENAI_", "ANTHROPIC_", "AWS_", "AZURE_", "GOOGLE_",
)


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    timeout: int = 240,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )
    if result.returncode:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}"
        )
    return result


@pytest.fixture(scope="session")
def manul_skill(tmp_path_factory: pytest.TempPathFactory) -> Path:
    checkout = tmp_path_factory.mktemp("latest-manul-regressions") / "manul"
    run(
        [
            "git", "clone", "--quiet", "--depth", "1", "--branch",
            MANUL_REF, MANUL_REPOSITORY, str(checkout),
        ],
        timeout=120,
    )
    skill = checkout / SKILL_RELATIVE
    assert (skill / "manul-daemon.sh").is_file()
    assert (skill / "task-process-control.sh").is_file()
    sha = run(["git", "-C", str(checkout), "rev-parse", "HEAD"]).stdout.strip()
    assert len(sha) == 40 and all(char in "0123456789abcdef" for char in sha)
    print(f"MANUL_E2E_REF={MANUL_REF} resolved_sha={sha}")
    return skill


def isolated_env(tmp_path: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(SENSITIVE_PREFIXES)
    }
    home = tmp_path / "home"
    temp = tmp_path / "tmp"
    home.mkdir(parents=True)
    temp.mkdir(parents=True)
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "TMPDIR": str(temp),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def run_manul_suite(
    skill: Path,
    script_name: str,
    tmp_path: Path,
    *,
    timeout: int = 240,
) -> str:
    script = skill / script_name
    assert script.is_file(), f"Required Manul regression suite is missing: {script_name}"
    result = run(
        ["bash", str(script)],
        env=isolated_env(tmp_path),
        cwd=skill,
        timeout=timeout,
    )
    return result.stdout


def test_colon_delimited_task_done_marker_is_normalized_once(
    manul_skill: Path, tmp_path: Path
) -> None:
    output = run_manul_suite(
        manul_skill, "test_opencode_marker_recovery.sh", tmp_path
    )
    assert "TASK_DONE remains successful" in output
    assert "one TASK_DONE output marker" in output


def test_investigate_command_is_normalized_as_report_only_verify(
    manul_skill: Path, tmp_path: Path
) -> None:
    output = run_manul_suite(manul_skill, "test_task_sources.sh", tmp_path)
    assert "investigate command is mapped to VERIFY" in output
    assert "investigate prefix is removed from the task prompt" in output


def test_retry_pr_verification_reuses_only_one_verified_open_pr(
    manul_skill: Path, tmp_path: Path
) -> None:
    output = run_manul_suite(manul_skill, "test_existing_task_pr.sh", tmp_path)
    assert "Results:" in output or "All " in output


def test_heartbeat_lease_recovery_and_process_tree_cleanup(
    manul_skill: Path, tmp_path: Path
) -> None:
    output = run_manul_suite(
        manul_skill, "test_worker_lease_recovery.sh", tmp_path, timeout=300
    )
    assert "executor recovery kills the runner tree" in output
    assert "dead worker task requeued" in output
    assert "live worker and heartbeat with fresh lease preserved" in output


def test_todo_markdown_report_delivery_is_formatted_and_idempotent(
    manul_skill: Path, tmp_path: Path
) -> None:
    output = run_manul_suite(
        manul_skill, "test_todo_task_sources.sh", tmp_path, timeout=300
    )
    assert "ordinary line breaks become hard Markdown breaks" in output
    assert "fenced code block content is preserved" in output
    assert "local report creates only one output child across retry" in output
    assert "remote retry returns the exact previously persisted answer" in output
