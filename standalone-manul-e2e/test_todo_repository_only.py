"""Regression E2E for repository-backed and direct-answer Todo MCP execution.

This suite clones the selected Manul ref and inspects the production shell
contracts. The full adapter regression harness is executed separately by
test_todo_repository_routing.py with fixture MCP responses.
"""
from __future__ import annotations

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
    checkout = tmp_path_factory.mktemp("manul-todo-repository-only") / "manul"
    run([
        "git", "clone", "--quiet", "--depth", "1",
        "--branch", MANUL_REF, MANUL_REPOSITORY, str(checkout),
    ])
    skill = checkout / SKILL_RELATIVE
    assert (skill / "manul-daemon.sh").is_file()
    assert (skill / "manul-daemon.sh").stat().st_mode & 0o111
    assert (skill / "todo-task-source-utils.sh").is_file()
    return skill


def test_todo_sources_use_repository_or_answer_execution(manul_skill: Path) -> None:
    utils = (manul_skill / "todo-task-source-utils.sh").read_text(encoding="utf-8")
    local = (manul_skill / "task-source-todo-local.sh").read_text(encoding="utf-8")
    remote = (manul_skill / "task-source-todo-remote.sh").read_text(encoding="utf-8")
    poller = (manul_skill / "poll.sh").read_text(encoding="utf-8")

    assert "todo_task_is_report_only()" not in utils
    assert 'execution:{kind:$executionKind}' in utils
    assert "todo_task_is_answer_request()" in utils
    assert "reportOnly" not in utils
    assert "todo_task_publish_update" in utils

    for adapter in (local, remote):
        assert "todo_task_is_report_only" not in adapter
        assert "todo_task_is_answer_request" in adapter
        assert "reportOnly" not in adapter
        assert "execution:{kind:" not in adapter
        assert "todo_task_publish_update" in adapter

    assert "disabled report-only execution" in poller
    assert "IMPLEMENT|REVIEW_FIX|VERIFY|ANSWER)" in poller
    assert 'if [ "$execution_kind" = "answer" ]; then' in poller
    assert 'elif [ "$execution_kind" != "repository" ]; then' in poller


def test_missing_or_ambiguous_repository_is_saved_as_an_open_subtask(manul_skill: Path) -> None:
    utils = (manul_skill / "todo-task-source-utils.sh").read_text(encoding="utf-8")
    local = (manul_skill / "task-source-todo-local.sh").read_text(encoding="utf-8")
    remote = (manul_skill / "task-source-todo-remote.sh").read_text(encoding="utf-8")
    source = (manul_skill / "task-source.sh").read_text(encoding="utf-8")

    assert "todo_task_publish_update()" in utils
    assert "todo_task_markdown_format" in utils
    assert "Todo status update was not readable after creation" in utils
    assert "MANUL_TASK_UPDATE:v1" in utils
    assert "source-version" in utils
    assert "task_source_publish_update()" in source
    assert 'update_status="needs_input"' in local
    assert 'update_status="needs_input"' in remote
    assert "owner/repo" in local
    assert "owner/repo" in remote


def test_user_questions_and_failures_are_published_to_todo(manul_skill: Path) -> None:
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")
    source = (manul_skill / "task-source.sh").read_text(encoding="utf-8")

    assert "task_source_publish_update" in source
    assert 'task_source_publish_update "$CONFIG" "$TASK_SOURCE_TYPE" "$TASK_SOURCE_ID" needs_input "$USER_QUESTION"' in daemon
    assert 'task_source_publish_update "$CONFIG" "$TASK_SOURCE_TYPE" "$TASK_SOURCE_ID" failed "$todo_failure_summary"' in daemon
    assert "TODO_TASK_FAILURE_UPDATE_CONFIRMED" in daemon
    assert "TASK_NEEDS_USER" in daemon
    assert "verified open subtask was saved" in daemon
    assert "task_source_report_deliver" not in daemon
    assert "Report-only Todo tasks persist their final answer" not in daemon



def test_clear_questions_without_repository_use_answer_execution(manul_skill: Path) -> None:
    utils = (manul_skill / "todo-task-source-utils.sh").read_text(encoding="utf-8")
    local = (manul_skill / "task-source-todo-local.sh").read_text(encoding="utf-8")
    remote = (manul_skill / "task-source-todo-remote.sh").read_text(encoding="utf-8")
    executor = (manul_skill / "agent-executor.sh").read_text(encoding="utf-8")
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")

    assert "todo_task_is_answer_request" in local
    assert "todo_task_is_answer_request" in remote
    assert "question_without_repository" in local
    assert "question_without_repository" in remote
    assert "Europe/Warsaw" in utils
    assert "This is a normal informational answer" in utils
    assert 'adapter_execution_kind="operator_query"' in executor
    assert 'if [ "$execution_kind" = "answer" ]; then' in executor
    assert "ANSWER_RUNTIME_UNSUPPORTED" in executor
    assert 'if [ "$execution_kind" != "answer" ] && { [ "$agent" = "sdd" ] || [ "$sdd_policy" = "true" ]; }; then' in executor
    opencode = (manul_skill / "opencode-adapter.sh").read_text(encoding="utf-8")
    claude = (manul_skill / "claude-code-adapter.sh").read_text(encoding="utf-8")
    openclaw = (manul_skill / "openclaw-adapter.sh").read_text(encoding="utf-8")
    assert '"tools": {"*": False}' in opencode
    assert '--tools "" --disallowedTools "mcp__*"' in claude
    assert 'tools.deny' in openclaw or '"tools":{"deny":["*"]}' in openclaw
    assert "answer_workspace_create()" in daemon
    assert 'TASK_EXECUTION_KIND" = "answer"' in daemon
    assert "TODO_ANSWER_SOURCE_PROMPT" in daemon
    assert 'task_source_publish_update "$CONFIG" "$TASK_SOURCE_TYPE" "$answer_source_id" answered "$answer_text"' in daemon
    assert "TODO_ANSWER_PUBLISHED" in daemon
    assert "answer_workspace_cleanup" in daemon
    assert "Current date/time at answer execution" in daemon


def test_answer_child_is_persisted_before_todo_tree_completion(manul_skill: Path) -> None:
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")
    utils = (manul_skill / "todo-task-source-utils.sh").read_text(encoding="utf-8")

    answer_publish = daemon.index('task_source_publish_update "$CONFIG" "$TASK_SOURCE_TYPE" "$answer_source_id" answered "$answer_text"')
    tree_complete = daemon.index('if [ "$SUCCESS" = "true" ] && task_source_is_todo_type "$TASK_SOURCE_TYPE"; then', answer_publish)
    assert answer_publish < tree_complete
    assert "status=(?:needs_input|failed|answered)" in utils
    assert "heading=\"Odpowiedź\"" in utils
    assert "todo_task_strip_verified_generated_update" in utils

def test_legacy_report_only_todo_entries_are_blocked_before_agent_start(manul_skill: Path) -> None:
    daemon = (manul_skill / "manul-daemon.sh").read_text(encoding="utf-8")
    marker = 'if [ "$TASK_EXECUTION_KIND" = "report_only" ] && task_source_is_todo_type "$TASK_SOURCE_TYPE"; then'
    start = daemon.index(marker)
    block = daemon[start:daemon.index('    local TASK_AUTO_ACCEPT', start)]

    assert "task_source_publish_update" in block
    assert '"needs_input"' not in block  # status is passed as a bare shell argument
    assert "needs_input" in block
    assert "mark_task_stale" in block
    assert "requeue_task" in block
    assert "task_source_report_deliver" not in daemon
