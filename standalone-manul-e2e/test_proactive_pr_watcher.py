"""E2E the proactive PR watcher against the selected isolated Manul ref.

The nested Manul regression script uses fixture GitHub responses and a
throwaway SQLite database. This suite never starts the operator's daemon,
connects to Todo MCP, or touches an installed Manul runtime.
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
    checkout = tmp_path_factory.mktemp("manul-proactive-pr") / "manul"
    run([
        "git", "clone", "--quiet", "--depth", "1", "--branch", MANUL_REF,
        MANUL_REPOSITORY, str(checkout),
    ])
    skill = checkout / SKILL_RELATIVE
    for name in (
        "manul-pr-watcher.sh",
        "manul-pr-review.sh",
        "poll.sh",
        "config.json.example",
        "install-manul-symlinks.sh",
        "test_pr_watcher.sh",
    ):
        assert (skill / name).is_file(), (
            f"Missing proactive PR component {name} from Manul ref {MANUL_REF}"
        )
    return skill


def test_proactive_pr_watcher_fixture_regressions(manul_skill: Path) -> None:
    result = run(["bash", "-x", str(manul_skill / "test_pr_watcher.sh")], cwd=manul_skill)
    assert "All proactive PR watcher tests passed." in result.stdout


def test_proactive_pr_configuration_and_runtime_wiring(manul_skill: Path) -> None:
    config = json.loads((manul_skill / "config.json.example").read_text(encoding="utf-8"))
    proactivity = config["proactivity"]
    assert proactivity["prAuthorAllowed"] == []
    assert proactivity["fixAndAnswerComments"] == {
        "enabled": True,
        "prScope": "OnlyManulPr",
    }
    assert config["ciFix"]["prScope"] == "OnlyManulPr"

    poller = (manul_skill / "poll.sh").read_text(encoding="utf-8")
    symlinks = (manul_skill / "install-manul-symlinks.sh").read_text(encoding="utf-8")
    assert 'source "$SCRIPT_DIR/manul-pr-watcher.sh"' in poller
    assert "scan_proactive_pr_comments \"$repo\"" in poller
    assert '"manul-pr-watcher.sh"' in symlinks
