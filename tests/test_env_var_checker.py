"""Tests for crontab_audit.env_var_checker."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.env_var_checker import (
    find_risky_env_refs,
    find_hardcoded_secrets,
    check_entries,
    EnvVarIssue,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
        host=host,
        raw_line=f"0 1 * * * {command}",
    )


def test_risky_ref_path_detected():
    entry = make_entry("/usr/bin/env $PATH/mytool")
    issues = find_risky_env_refs(entry)
    assert len(issues) == 1
    assert issues[0].issue_type == "risky_ref"
    assert "$PATH" in issues[0].detail


def test_risky_ref_home_detected():
    entry = make_entry("bash $HOME/scripts/backup.sh")
    issues = find_risky_env_refs(entry)
    assert any("$HOME" in i.detail for i in issues)


def test_no_risky_ref_for_safe_command():
    entry = make_entry("/usr/bin/find /var/log -name '*.log' -delete")
    issues = find_risky_env_refs(entry)
    assert issues == []


def test_hardcoded_password_detected():
    entry = make_entry("mysql -u root --password=supersecret -e 'SELECT 1'")
    issues = find_hardcoded_secrets(entry)
    assert len(issues) >= 1
    assert issues[0].issue_type == "hardcoded_secret"


def test_hardcoded_token_detected():
    entry = make_entry("/usr/bin/deploy.sh token=abc123xyz")
    issues = find_hardcoded_secrets(entry)
    assert len(issues) == 1
    assert "hardcoded_secret" == issues[0].issue_type


def test_hardcoded_api_key_detected():
    entry = make_entry("curl -H 'api_key=mysecretkey' https://example.com")
    issues = find_hardcoded_secrets(entry)
    assert len(issues) >= 1


def test_no_secret_for_safe_command():
    entry = make_entry("/usr/bin/rsync -av /src/ /dst/")
    issues = find_hardcoded_secrets(entry)
    assert issues == []


def test_check_entries_combines_all_issues():
    entries = [
        make_entry("bash $HOME/run.sh"),
        make_entry("mysql --password=secret db"),
        make_entry("/bin/safe_script.sh"),
    ]
    issues = check_entries(entries)
    types = {i.issue_type for i in issues}
    assert "risky_ref" in types
    assert "hardcoded_secret" in types


def test_check_entries_empty_list():
    assert check_entries([]) == []


def test_env_var_issue_str_includes_host():
    entry = make_entry("bash $HOME/run.sh", host="webserver")
    issue = EnvVarIssue(entry=entry, issue_type="risky_ref", detail="References '$HOME'")
    result = str(issue)
    assert "webserver" in result
    assert "risky_ref" in result


def test_env_var_issue_str_no_host():
    entry = make_entry("bash $HOME/run.sh", host="")
    issue = EnvVarIssue(entry=entry, issue_type="risky_ref", detail="References '$HOME'")
    result = str(issue)
    assert "[" not in result
