"""Standalone Manul extraction E2E contract tests.

The tests inspect the standalone Manul repository and run its real install/repair
helpers only in a disposable HOME with fake host tools. They never touch the
operator's ~/.manul, credentials, running daemon or DB.
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


def run(command: list[str], *, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, env=env, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}"
        )
    return result


def clone_manul(destination: Path) -> Path:
    run(["git", "clone", "--quiet", "--depth", "1", "--branch", MANUL_REF,
         MANUL_REPOSITORY, str(destination)])
    skill = destination / SKILL_RELATIVE
    assert (skill / "install-manul.sh").is_file()
    return skill


def make_fake_bin(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    scripts = {
        "gh": "#!/usr/bin/env bash\nexit 0\n",
        "crontab": """#!/usr/bin/env bash
state="${FAKE_CRONTAB_STATE:?}"
if [[ "${1:-}" == "-l" ]]; then
  [[ -f "$state" ]] && cat "$state"
  exit 0
fi
if [[ "${1:-}" == "-" ]]; then
  cat > "$state"
  exit 0
fi
exit 0
""",
        "opencode": "#!/usr/bin/env bash\nexit 0\n",
        "openclaw": "#!/usr/bin/env bash\nexit 0\n",
    }
    for name, body in scripts.items():
        path = bin_dir / name
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)


def installer_env(home: Path, skill: Path, bin_dir: Path,
                  crontab_state: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "HOME": str(home),
        "PATH": f"{bin_dir}:{env.get('PATH', '')}",
        "MANUL_CANONICAL_DIR": str(skill),
        "MANUL_CANONICAL_ROOT": str(skill.parents[1]),
        "MANUL_CANONICAL_BRANCH": "master",
        "MANUL_RUNTIME_DIR": str(home / ".manul"),
        "FAKE_CRONTAB_STATE": str(crontab_state),
        "OPENCODE_CONFIG": str(home / ".config" / "opencode" / "opencode.json"),
        "CARACAL_MCP_URL": "http://127.0.0.1:3500/mcp",
        "CARACAL_ACCESS_TOKEN": "legacy-caracal-placeholder-not-a-real-secret",
        "TODO_LOCAL_MCP_TOKEN": "legacy-todo-placeholder-not-a-real-secret",
        "FITEO_BASE_URL": "https://fiteo.invalid",
        "FITEO_MANUL_PAT": "dedicated-fiteo-placeholder-not-a-real-secret",
        "FITEO_MANUL_SHARE_USER_ID": "3",
        "FITEO_PAT": "operator-fiteo-placeholder-not-a-real-secret",
    })
    return env


def seed_minimal_valid_db(db_path: Path) -> None:
    import sqlite3

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE processed_comments (commentId TEXT PRIMARY KEY);
            CREATE TABLE conversations (conversationId TEXT PRIMARY KEY);
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE workspaces (workspaceId TEXT PRIMARY KEY);
            INSERT INTO processed_comments VALUES ('preserve-this-task');
            INSERT INTO conversations VALUES ('preserve-this-conversation');
            INSERT INTO meta VALUES ('baseline', '2026-10-01T00:00:00Z');
            INSERT INTO workspaces VALUES ('preserve-this-workspace');
        """)


def database_snapshot(db_path: Path) -> dict[str, object]:
    import sqlite3

    with sqlite3.connect(db_path) as connection:
        return {
            "processed_comments": connection.execute(
                "SELECT commentId FROM processed_comments ORDER BY commentId"
            ).fetchall(),
            "conversations": connection.execute(
                "SELECT conversationId FROM conversations ORDER BY conversationId"
            ).fetchall(),
            "meta": connection.execute(
                "SELECT key, value FROM meta ORDER BY key"
            ).fetchall(),
            "workspaces": connection.execute(
                "SELECT workspaceId FROM workspaces ORDER BY workspaceId"
            ).fetchall(),
        }


def test_standalone_repository_has_runtime_not_operator_config(tmp_path: Path) -> None:
    skill = clone_manul(tmp_path / "manul")
    assert (skill / "install-manul.sh").is_file()
    assert (skill / "manul-shell.zsh").is_file()
    assert (skill / "manul-env.sh").is_file()
    # Shared Todo transport and unit tests are owned by globalskills/aicode.
    assert not (skill / "todo-mcp-client.py").exists()
    assert not (skill / "todo-local-mcp-url.sh").exists()
    assert not (skill / "test_todo_mcp_client.py").exists()
    assert not (skill / "config.json").exists()
    assert (skill / "config.json.example").is_file()


def test_installer_preserves_existing_database_and_uses_standalone_source(tmp_path: Path) -> None:
    skill = clone_manul(tmp_path / "manul")
    home = tmp_path / "home"
    bin_dir = tmp_path / "fake-bin"
    crontab_state = tmp_path / "crontab"
    home.mkdir()
    make_fake_bin(bin_dir)

    runtime = home / ".manul"
    db = runtime / "state" / "manul.db"
    seed_minimal_valid_db(db)
    before = database_snapshot(db)

    env = installer_env(home, skill, bin_dir, crontab_state)
    env_file = runtime / ".env"
    env_file.write_text(
        "OPENCODE_CONFIG=/operator/custom-opencode.json\n"
        "KEEP_ME=preserved\n"
        "CARACAL_MCP_URL=http://127.0.0.1:3500/mcp\n"
        "CARACAL_ACCESS_TOKEN=legacy-caracal-placeholder\n"
        "TODO_LOCAL_MCP_TOKEN=legacy-todo-placeholder\n"
        "FITEO_PAT=legacy-operator-pat-placeholder\n",
        encoding="utf-8",
    )
    env_file.chmod(0o600)
    import json
    config = runtime / "config.json"
    config.write_text(json.dumps({
        "repositories": [],
        "taskSources": [{
            "type": "todo_remote_mcp", "enabled": True,
            "url": "https://fiteo.invalid/mcp", "tokenEnv": "FITEO_MANUL_PAT"
        }]
    }), encoding="utf-8")
    result = run(
        ["bash", str(skill / "install-manul.sh"), "--runtime-dir", str(runtime),
         "--canonical-dir", str(skill)],
        env=env, check=False,
    )

    assert result.returncode == 0, result.stdout
    assert database_snapshot(db) == before
    assert not (runtime / ".enabled").exists()
    for name in ("manul-daemon.sh", "manul-status.sh", "manul-comments-remove.sh"):
        link = runtime / name
        assert link.is_symlink()
        assert link.resolve().is_relative_to(skill.resolve())
    assert env_file.exists()
    assert env_file.stat().st_mode & 0o777 == 0o600
    contents = env_file.read_text(encoding="utf-8")
    assert "OPENCODE_CONFIG=/operator/custom-opencode.json" in contents
    assert "KEEP_ME=preserved" in contents
    assert f"MANUL_CANONICAL_DIR={skill}" in contents
    assert f"MANUL_CANONICAL_ROOT={skill.parents[1]}" in contents
    assert "MANUL_CANONICAL_BRANCH=master" in contents
    assert "MANUL_HOST_SKILLS_DIR=" not in contents
    assert "CARACAL_MCP_URL=" not in contents
    assert "CARACAL_ACCESS_TOKEN=" not in contents
    assert "TODO_LOCAL_MCP_TOKEN=" not in contents
    assert "FITEO_PAT=" not in contents
    assert "FITEO_BASE_URL=https://fiteo.invalid" in contents
    assert "FITEO_MANUL_PAT=dedicated-fiteo-placeholder-not-a-real-secret" in contents
    assert "FITEO_MANUL_SHARE_USER_ID=3" in contents
    assert "not-a-real-secret" not in result.stdout


def test_installer_refuses_missing_database_without_explicit_init(tmp_path: Path) -> None:
    skill = clone_manul(tmp_path / "manul")
    home = tmp_path / "home"
    bin_dir = tmp_path / "fake-bin"
    make_fake_bin(bin_dir)
    runtime = home / ".manul"
    home.mkdir()
    env = installer_env(home, skill, bin_dir, tmp_path / "crontab")

    result = run(
        ["bash", str(skill / "install-manul.sh"), "--runtime-dir", str(runtime),
         "--canonical-dir", str(skill)],
        env=env, check=False,
    )
    assert result.returncode != 0
    assert "Refusing to create a fresh DB implicitly" in result.stdout
    assert not (runtime / "state" / "manul.db").exists()


def test_repair_refuses_to_fabricate_state_when_no_backup_exists(tmp_path: Path) -> None:
    skill = clone_manul(tmp_path / "manul")
    home = tmp_path / "home"
    bin_dir = tmp_path / "fake-bin"
    make_fake_bin(bin_dir)
    runtime = home / ".manul"
    home.mkdir()
    env = installer_env(home, skill, bin_dir, tmp_path / "crontab")

    result = run(
        ["bash", str(skill / "repair-manul-runtime.sh"), "--runtime-dir", str(runtime)],
        env=env, check=False,
    )
    assert result.returncode != 0
    assert "No valid backup DB found" in result.stdout
    assert not (runtime / "state" / "manul.db").exists()


def test_env_bootstrap_is_atomic_scoped_and_preserves_existing_values(tmp_path: Path) -> None:
    skill = clone_manul(tmp_path / "manul")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    env_file = runtime / ".env"
    env_file.write_text(
        "OPENCODE_CONFIG=/operator/custom-opencode.json\n"
        "KEEP_ME=present\n"
        "CARACAL_MCP_URL=http://127.0.0.1:3500/mcp\n"
        "CARACAL_ACCESS_TOKEN=legacy-caracal-placeholder\n"
        "TODO_LOCAL_MCP_TOKEN=legacy-todo-placeholder\n"
        "FITEO_PAT=legacy-operator-pat-placeholder\n",
        encoding="utf-8",
    )
    env_file.chmod(0o600)

    env = os.environ.copy()
    env.update({
        "HOME": str(tmp_path / "home"),
        "MANUL_CANONICAL_DIR": str(skill),
        "MANUL_CANONICAL_ROOT": str(skill.parents[1]),
        "MANUL_CANONICAL_BRANCH": "master",
        "CARACAL_MCP_URL": "http://127.0.0.1:3500/mcp",
        "CARACAL_ACCESS_TOKEN": "legacy-caracal-placeholder-not-real",
        "TODO_LOCAL_MCP_TOKEN": "legacy-todo-placeholder-not-real",
        "FITEO_BASE_URL": "https://fiteo.invalid",
        "FITEO_MANUL_PAT": "dedicated-fiteo-placeholder-not-real",
        "FITEO_MANUL_SHARE_USER_ID": "3",
        "FITEO_PAT": "operator-fiteo-placeholder-not-real",
    })
    # The token allowlist is configuration-driven. Only the dedicated
    # FITEO_MANUL_PAT configured for the enabled remote source may be persisted;
    # the operator's FITEO_PAT must be stripped and never used as a fallback.
    import json
    config = runtime / "config.json"
    config.write_text(json.dumps({
        "repositories": [],
        "taskSources": [{
            "type": "todo_remote_mcp", "enabled": True,
            "url": "https://fiteo.invalid/mcp", "tokenEnv": "FITEO_MANUL_PAT"
        }]
    }), encoding="utf-8")
    run(["bash", str(skill / "manul-env.sh"), "--bootstrap", str(runtime)], env=env)

    contents = env_file.read_text(encoding="utf-8")
    assert "OPENCODE_CONFIG=/operator/custom-opencode.json" in contents
    assert "KEEP_ME=present" in contents
    assert f"MANUL_CANONICAL_DIR={skill}" in contents
    assert "MANUL_CANONICAL_BRANCH=master" in contents
    assert "MANUL_HOST_SKILLS_DIR=" not in contents
    assert "CARACAL_MCP_URL=" not in contents
    assert "CARACAL_ACCESS_TOKEN=" not in contents
    assert "TODO_LOCAL_MCP_TOKEN=" not in contents
    assert "FITEO_PAT=" not in contents
    assert "FITEO_BASE_URL=https://fiteo.invalid" in contents
    assert "FITEO_MANUL_PAT=dedicated-fiteo-placeholder-not-real" in contents
    assert "FITEO_MANUL_SHARE_USER_ID=3" in contents
    assert env_file.stat().st_mode & 0o777 == 0o600
    assert list(runtime.glob(".env.*")) == []


def test_host_integration_uses_standalone_checkout_and_host_skills() -> None:
    import urllib.request

    base = (
        GLOBALSKILLS_REPOSITORY
        .replace("https://github.com/", "https://raw.githubusercontent.com/")
        .removesuffix(".git")
        + f"/{GLOBALSKILLS_REF}/aicode/"
    )
    with urllib.request.urlopen(base + "aicode", timeout=20) as response:
        source = response.read().decode("utf-8")
    assert ".globalskills/skills/manul-github-bot" not in source
    assert 'MANUL_CANONICAL_BRANCH="${MANUL_CANONICAL_BRANCH:-master}"' in source
    assert 'TODO_LOCAL_MCP_URL_HELPER="$AICODE_SOURCE_DIR/todo-local-mcp-url.sh"' in source
    assert 'TODO_MCP_CLIENT="${TODO_MCP_CLIENT:-$AICODE_SOURCE_DIR/todo-mcp-client.py}"' in source
    assert "export TODO_MCP_CLIENT TODO_LOCAL_MCP_URL_HELPER" in source

    for relative_path in (
        "todo-mcp-client.py",
        "todo-local-mcp-url.sh",
        "test_todo_mcp_client.py",
    ):
        with urllib.request.urlopen(base + relative_path, timeout=20) as response:
            payload = response.read()
        assert payload, f"globalskills/aicode/{relative_path} must exist"
