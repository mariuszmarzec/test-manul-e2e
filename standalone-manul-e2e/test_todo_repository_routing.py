"""E2E the Manul Todo repository resolver against the selected Manul ref.

The real shell regression harness uses fixture MCP responses and disposable
files only. It never connects to Todo Desktop, Fiteo, or the operator runtime.
"""
from __future__ import annotations

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
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
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
            f"Command failed ({result.returncode}): {' '.join(command)}\\n{result.stdout}"
        )
    return result


@pytest.fixture(scope="session")
def manul_skill(tmp_path_factory: pytest.TempPathFactory) -> Path:
    checkout = tmp_path_factory.mktemp("manul-todo-routing") / "manul"
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
        ],
    )
    skill = checkout / SKILL_RELATIVE
    regression_script = skill / "test_todo_task_sources.sh"
    assert regression_script.is_file(), (
        f"Todo source regression harness is missing from Manul ref {MANUL_REF}"
    )
    return skill


def test_todo_task_source_routing_regressions(manul_skill: Path, tmp_path: Path) -> None:
    regression_script = manul_skill / "test_todo_task_sources.sh"
    isolated_home = tmp_path / "home"
    isolated_home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(isolated_home)
    env.pop("TODO_TASK_REPOSITORY_CATALOG", None)
    result = run(
        ["bash", str(regression_script)],
        cwd=manul_skill,
        env=env,
    )
    assert "Results:" in result.stdout
    assert "0 failed" in result.stdout, result.stdout
