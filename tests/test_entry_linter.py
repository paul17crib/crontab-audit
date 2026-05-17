"""Tests for entry_linter and entry_linter_report."""
import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_linter import (
    lint_entry,
    lint_entries,
    LintIssue,
    _NO_REDIRECT,
    _MISSING_USER,
    _ABSOLUTE_PATH,
    _TRAILING_WHITESPACE,
    _EMPTY_COMMAND,
    _DUPLICATE_SPACES,
)
from crontab_audit.entry_linter_report import (
    format_lint_issues,
    format_lint_by_severity,
    format_lint_summary,
    format_lint_by_code,
)


def make_entry(command="/usr/bin/backup.sh", user="root", host="host1",
               minute="0", hour="2", dom="*", month="*", dow="*"):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command, user=user, host=host, raw_line="",
    )


# --- lint_entry tests ---

def test_empty_command_flagged():
    entry = make_entry(command="   ")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _EMPTY_COMMAND in codes


def test_trailing_whitespace_flagged():
    entry = make_entry(command="  /usr/bin/backup.sh  ")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _TRAILING_WHITESPACE in codes


def test_duplicate_spaces_flagged():
    entry = make_entry(command="/usr/bin/backup.sh  --verbose")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _DUPLICATE_SPACES in codes


def test_missing_user_flagged():
    entry = make_entry(command="/usr/bin/backup.sh", user=None)
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _MISSING_USER in codes


def test_user_present_no_missing_user_issue():
    entry = make_entry(command="/usr/bin/backup.sh", user="root")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _MISSING_USER not in codes


def test_relative_command_flagged():
    entry = make_entry(command="backup.sh")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _ABSOLUTE_PATH in codes


def test_absolute_command_not_flagged_for_path():
    entry = make_entry(command="/usr/bin/backup.sh")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _ABSOLUTE_PATH not in codes


def test_env_var_command_not_flagged_for_path():
    entry = make_entry(command="$SCRIPTS_DIR/backup.sh")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _ABSOLUTE_PATH not in codes


def test_noisy_command_without_redirect_flagged():
    entry = make_entry(command="/usr/bin/curl https://example.com")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _NO_REDIRECT in codes


def test_noisy_command_with_redirect_not_flagged():
    entry = make_entry(command="/usr/bin/curl https://example.com > /dev/null 2>&1")
    issues = lint_entry(entry)
    codes = [i.code for i in issues]
    assert _NO_REDIRECT not in codes


def test_clean_entry_produces_no_issues():
    entry = make_entry(command="/usr/bin/backup.sh > /dev/null 2>&1", user="root")
    issues = lint_entry(entry)
    assert issues == []


# --- lint_entries tests ---

def test_lint_entries_aggregates_across_entries():
    entries = [
        make_entry(command="/usr/bin/backup.sh", user=None),
        make_entry(command="relative_script.sh"),
    ]
    issues = lint_entries(entries)
    codes = [i.code for i in issues]
    assert _MISSING_USER in codes
    assert _ABSOLUTE_PATH in codes


def test_lint_entries_empty_list():
    assert lint_entries([]) == []


# --- report formatting tests ---

def test_format_lint_issues_empty():
    result = format_lint_issues([])
    assert "No lint issues" in result


def test_format_lint_issues_includes_severity():
    entry = make_entry(command="   ")
    issues = lint_entry(entry)
    result = format_lint_issues(issues)
    assert "ERROR" in result


def test_format_lint_by_severity_groups_correctly():
    entries = [
        make_entry(command="   "),
        make_entry(command="relative.sh"),
    ]
    issues = lint_entries(entries)
    result = format_lint_by_severity(issues)
    assert "ERRORS" in result or "WARNINGS" in result


def test_format_lint_summary_zero():
    result = format_lint_summary([])
    assert "0 issues" in result


def test_format_lint_summary_nonzero():
    entry = make_entry(command="   ")
    issues = lint_entry(entry)
    result = format_lint_summary(issues)
    assert "issue(s)" in result
    assert "error" in result


def test_format_lint_by_code_groups_by_code():
    entries = [
        make_entry(command="relative.sh"),
        make_entry(command="another_relative.sh"),
    ]
    issues = lint_entries(entries)
    result = format_lint_by_code(issues)
    assert "L003" in result
    assert "2 occurrence" in result
