"""Tests for dependency_checker and dependency_report."""

import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.dependency_checker import (
    DependencyHint,
    _extract_tokens,
    find_dependencies,
)
from crontab_audit.dependency_report import (
    format_dependency_hints,
    format_dependencies_by_token,
    format_dependency_summary,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
        raw=f"0 1 * * * {command}",
        host=host,
    )


# --- _extract_tokens ---

def test_extract_tokens_finds_path():
    tokens = _extract_tokens("/var/log/app.log")
    assert "/var/log/app.log" in tokens


def test_extract_tokens_finds_env_var():
    tokens = _extract_tokens("echo $HOME/data")
    assert "$HOME" in tokens


def test_extract_tokens_empty_command():
    assert _extract_tokens("") == set()


def test_extract_tokens_multiple():
    tokens = _extract_tokens("/opt/scripts/run.sh $APP_ENV")
    assert "/opt/scripts/run.sh" in tokens
    assert "$APP_ENV" in tokens


# --- find_dependencies ---

def test_find_dependencies_no_shared_tokens():
    entries = [
        make_entry("echo hello"),
        make_entry("date"),
    ]
    assert find_dependencies(entries) == []


def test_find_dependencies_shared_path():
    entries = [
        make_entry("/var/data/backup.sh", host="host1"),
        make_entry("/var/data/cleanup.sh", host="host2"),
    ]
    hints = find_dependencies(entries)
    tokens = {h.shared_token for h in hints}
    assert "/var/data" in tokens or any("/var" in t for t in tokens)


def test_find_dependencies_shared_env_var():
    entries = [
        make_entry("$DEPLOY_DIR/start.sh", host="host1"),
        make_entry("$DEPLOY_DIR/stop.sh", host="host2"),
    ]
    hints = find_dependencies(entries)
    tokens = {h.shared_token for h in hints}
    assert "$DEPLOY_DIR" in tokens


def test_find_dependencies_no_self_pairs():
    entry = make_entry("/shared/path/script.sh")
    hints = find_dependencies([entry])
    assert hints == []


def test_find_dependencies_hint_str():
    a = make_entry("/data/run.sh", host="alpha")
    b = make_entry("/data/clean.sh", host="beta")
    hints = find_dependencies([a, b])
    assert hints
    s = str(hints[0])
    assert "alpha" in s or "beta" in s
    assert "shared" in s


# --- report formatting ---

def test_format_dependency_hints_empty():
    result = format_dependency_hints([])
    assert "No" in result


def test_format_dependency_hints_lists_entries():
    a = make_entry("/data/run.sh", host="h1")
    b = make_entry("/data/clean.sh", host="h2")
    hints = find_dependencies([a, b])
    result = format_dependency_hints(hints)
    assert "hint" in result.lower() or "<->" in result


def test_format_dependency_summary_empty():
    result = format_dependency_summary([])
    assert "none" in result.lower()


def test_format_dependency_summary_with_hints():
    a = make_entry("/srv/scripts/deploy.sh", host="h1")
    b = make_entry("/srv/scripts/rollback.sh", host="h2")
    hints = find_dependencies([a, b])
    result = format_dependency_summary(hints)
    assert "hint" in result.lower()


def test_format_dependencies_by_token_groups_correctly():
    a = make_entry("/opt/app/run.sh", host="h1")
    b = make_entry("/opt/app/stop.sh", host="h2")
    hints = find_dependencies([a, b])
    result = format_dependencies_by_token(hints)
    assert "/opt/app" in result or "Shared token" in result
