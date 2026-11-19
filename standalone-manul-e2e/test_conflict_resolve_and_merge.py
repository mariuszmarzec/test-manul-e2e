"""E2E the opt-in conflict resolver against an isolated Manul source ref.

The nested shell test uses fake GitHub CLI responses and a throwaway SQLite DB.
It never contacts the live GitHub PR merge endpoint or the operator runtime.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

MANUL_REPOSITORY = "https://github.com/mariuszmarzec/manul.git"
MANUL_REF = os.environ.get("MANUL_E2E_REF", "master")
SKILL_RELATIVE = Path("skills/manul-github-bot")


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=240,
    )
    if result.returncode:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}"
        )
    return result


@pytest.fixture(scope="session")
def manul_skill(tmp_path_factory: pytest.TempPathFactory) -> Path:
    checkout = tmp_path_factory.mktemp("manul-conflict-resolve") / "manul"
    run([
        "git", "clone", "--quiet", "--depth", "1", "--branch", MANUL_REF,
        MANUL_REPOSITORY, str(checkout),
    ])
    skill = checkout / SKILL_RELATIVE
    for name in (
        "manul-pr-watcher.sh",
        "poll.sh",
        "config.json.example",
        "test_conflict_resolve_and_merge.sh",
    ):
        assert (skill / name).is_file(), (
            f"Missing conflict resolver component {name} from Manul ref {MANUL_REF}"
        )
    return skill


def test_conflict_resolve_and_merge_fixture_regressions(manul_skill: Path) -> None:
    result = run(
        ["bash", "-x", str(manul_skill / "test_conflict_resolve_and_merge.sh")],
        cwd=manul_skill,
    )
    assert "All conflict resolve-and-merge tests passed." in result.stdout


def test_conflict_resolve_and_merge_configuration_and_polling(manul_skill: Path) -> None:
    config = json.loads((manul_skill / "config.json.example").read_text(encoding="utf-8"))
    assert config["conflictResolveAndMerge"] == {
        "enabled": False,
        "prScope": "OnlyManulPr",
    }

    watcher = (manul_skill / "manul-pr-watcher.sh").read_text(encoding="utf-8")
    poller = (manul_skill / "poll.sh").read_text(encoding="utf-8")
    assert "conflict_resolve_and_merge_enabled()" in watcher
    assert "conflict_resolve_and_merge_scope()" in watcher
    assert "scan_conflicted_prs()" in watcher
    assert 'source "$SCRIPT_DIR/manul-pr-watcher.sh"' in poller
    assert 'scan_conflicted_prs "$repo"' in poller
    assert "headRefOid,baseRefOid" in watcher
    assert "Do not use" in watcher and "--admin" in watcher
