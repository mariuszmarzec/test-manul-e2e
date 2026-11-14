"""Integration tests for Manul's Specification-Driven Development workflow.

All commands run in a disposable checkout cloned at MANUL_E2E_REF. Tests never
connect to the operator's Manul runtime or start the daemon.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

MANUL_REPOSITORY = "https://github.com/mariuszmarzec/manul.git"
MANUL_REF = os.environ.get("MANUL_E2E_REF", "master")
GLOBALSKILLS_REPOSITORY = "https://github.com/mariuszmarzec/globalskills.git"
GLOBALSKILLS_REF = os.environ.get("GLOBALSKILLS_E2E_REF", "master")
SKILL_RELATIVE = Path("skills/manul-github-bot")


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
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
    checkout = tmp_path_factory.mktemp("manul-sdd") / "manul"
    run([
        "git", "clone", "--quiet", "--depth", "1", "--branch", MANUL_REF,
        MANUL_REPOSITORY, str(checkout),
    ])
    skill = checkout / SKILL_RELATIVE
    for name in (
        "sdd-policy.py",
        "workflow-state.py",
        "migrate-sdd-agent-config.sh",
        "test_sdd_workflow.sh",
        "test_sdd_agent_config_migration.sh",
        "test_caracal_opencode_runtime.sh",
    ):
        assert (skill / name).is_file(), f"Missing SDD runtime component: {name}"
    return skill


def test_sdd_policy_routing_and_checkpoint_contract(manul_skill: Path) -> None:
    result = run(["bash", str(manul_skill / "test_sdd_workflow.sh")])
    assert "SDD workflow tests:" in result.stdout
    assert "0 failed" in result.stdout


def test_existing_manul_config_migration_is_safe_and_idempotent(
    manul_skill: Path,
) -> None:
    result = run(["bash", str(manul_skill / "test_sdd_agent_config_migration.sh")])
    assert "SDD agent config migration:" in result.stdout
    assert "0 failed" in result.stdout


def test_sdd_command_parser_regressions(manul_skill: Path) -> None:
    result = run(["bash", str(manul_skill / "test_github_control_protocol.sh")])
    assert "Test 50: /manul sdd command is parsed" in result.stdout
    assert "Test 51: /manul sdd bootstrap is parsed explicitly" in result.stdout
    assert "0 failed" in result.stdout


def test_shared_globalskills_sdd_agent_and_skill_are_available(
    tmp_path: Path,
) -> None:
    checkout = tmp_path / "globalskills"
    run([
        "git", "clone", "--quiet", "--depth", "1", "--branch", GLOBALSKILLS_REF,
        GLOBALSKILLS_REPOSITORY, str(checkout),
    ])
    agent = checkout / "agents" / "sdd.md"
    skill = checkout / "skills" / "specification-driven-development" / "SKILL.md"
    readme = (checkout / "README.md").read_text(encoding="utf-8")
    assert agent.is_file()
    assert skill.is_file()
    assert "Specification-Driven Development (SDD)" in readme
    assert "/manul sdd bootstrap" in readme
    assert "human approval" in skill.read_text(encoding="utf-8").lower()


def test_manul_caracal_provider_environment_is_refreshed_for_opencode_tasks(
    manul_skill: Path,
) -> None:
    result = run(["bash", str(manul_skill / "test_caracal_opencode_runtime.sh")])
    assert "Caracal OpenCode runtime tests: passed" in result.stdout
    assert "process-scoped" in result.stdout


def test_sdd_runtime_entrypoints_keep_executable_modes(manul_skill: Path) -> None:
    for name in (
        "manul-daemon.sh",
        "poll.sh",
        "opencode-adapter.sh",
        "manul-github-events.sh",
        "install-manul.sh",
        "install-manul-symlinks.sh",
        "migrate-sdd-agent-config.sh",
        "test_sdd_workflow.sh",
        "test_sdd_agent_config_migration.sh",
    ):
        assert (manul_skill / name).stat().st_mode & 0o111, (
            f"{name} must remain executable in the Manul Git tree"
        )


def test_manul_installer_and_dispatcher_wire_sdd_before_agent_execution(
    manul_skill: Path,
) -> None:
    installer = (manul_skill / "install-manul.sh").read_text(encoding="utf-8")
    symlinks = (manul_skill / "install-manul-symlinks.sh").read_text(encoding="utf-8")
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")
    executor = (manul_skill / "agent-executor.sh").read_text(encoding="utf-8")

    assert "migrate-sdd-agent-config.sh" in installer
    assert '"sdd-policy.py"' in symlinks
    assert '"workflow-state.py"' in symlinks
    policy_position = daemon.index("Apply repository-level SDD policy")
    invocation_position = daemon.index("# 6. Invoke implementation agent")
    assert policy_position < invocation_position
    assert "SDD_PREVIOUS_STATE=" in daemon
    assert "Required SDD agent definition missing" in executor
    assert "SDD_POLICY_BYPASS" in executor
