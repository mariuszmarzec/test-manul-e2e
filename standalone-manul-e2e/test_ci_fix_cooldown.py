"""CI-fix waiting and cooldown contract against an isolated Manul checkout."""
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
    checkout = tmp_path_factory.mktemp("manul-ci-fix-cooldown") / "manul"
    run([
        "git", "clone", "--quiet", "--depth", "1", "--branch", MANUL_REF,
        MANUL_REPOSITORY, str(checkout),
    ])
    skill = checkout / SKILL_RELATIVE
    for name in ("poll.sh", "config.json.example", "ci_fix_contract.sh"):
        assert (skill / name).is_file(), (
            f"Missing CI-fix component {name} from Manul ref {MANUL_REF}"
        )
    return skill


def test_ci_fix_activity_wait_cooldown_and_upgrade_contract(manul_skill: Path) -> None:
    config = json.loads(
        (manul_skill / "config.json.example").read_text(encoding="utf-8")
    )
    assert config["ciFix"]["cooldownMinutes"] == 60
    assert config["ciFix"]["waitBeforeFirstMinutes"] == 30

    poller = (manul_skill / "poll.sh").read_text(encoding="utf-8")
    assert "ci_fix_attempts" in poller
    assert ".ciFix.waitBeforeFirstMinutes // 30" in poller
    assert 'check_ci_fix_eligible "$repo" "$pr_num" "$run_id" "$latest_failure_at" "$pr_updated_at"' in poller
    assert "--json state,headRefOid,updatedAt" in poller
    assert "failing CI changed during eligibility check" in poller

    result = run(["bash", "-x", str(manul_skill / "ci_fix_contract.sh")], cwd=manul_skill)
    assert "All CI-fix cooldown contract tests passed." in result.stdout
