"""Tests for crontab_audit.differ module."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.loader import HostCrontab
from crontab_audit.differ import (
    CrontabDiff,
    diff_host,
    diff_all,
    _entry_key,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="echo hi", host="web1"):
    return CrontabEntry(
        minute=minute, hour=hour, day_of_month=dom,
        month=month, day_of_week=dow, command=command,
        raw=f"{minute} {hour} {dom} {month} {dow} {command}",
        hostname=host,
    )


def make_host(hostname, entries):
    return HostCrontab(hostname=hostname, entries=entries, parse_errors=[])


def test_entry_key_uses_schedule_and_command():
    e = make_entry(minute="5", hour="3", command="backup.sh")
    key = _entry_key(e)
    assert key == ("5 3 * * *", "backup.sh")


def test_diff_host_detects_added_entry():
    before = make_host("web1", [])
    after = make_host("web1", [make_entry(command="new_job.sh")])
    diff = diff_host(before, after)
    assert len(diff.added) == 1
    assert diff.added[0].command == "new_job.sh"
    assert diff.removed == []


def test_diff_host_detects_removed_entry():
    entry = make_entry(command="old_job.sh")
    before = make_host("web1", [entry])
    after = make_host("web1", [])
    diff = diff_host(before, after)
    assert len(diff.removed) == 1
    assert diff.removed[0].command == "old_job.sh"
    assert diff.added == []


def test_diff_host_unchanged_entry():
    entry = make_entry(command="stable.sh")
    before = make_host("web1", [entry])
    after = make_host("web1", [make_entry(command="stable.sh")])
    diff = diff_host(before, after)
    assert len(diff.unchanged) == 1
    assert diff.added == []
    assert diff.removed == []


def test_diff_host_has_changes_true():
    before = make_host("web1", [])
    after = make_host("web1", [make_entry()])
    diff = diff_host(before, after)
    assert diff.has_changes() is True


def test_diff_host_has_changes_false():
    entry = make_entry()
    before = make_host("web1", [entry])
    after = make_host("web1", [make_entry()])
    diff = diff_host(before, after)
    assert diff.has_changes() is False


def test_diff_host_str_no_changes():
    entry = make_entry(command="job.sh")
    before = make_host("web1", [entry])
    after = make_host("web1", [make_entry(command="job.sh")])
    diff = diff_host(before, after)
    assert "no changes" in str(diff)


def test_diff_all_covers_all_hostnames():
    before = [make_host("web1", [make_entry(command="a.sh")])]
    after = [
        make_host("web1", [make_entry(command="b.sh")]),
        make_host("web2", [make_entry(command="c.sh")]),
    ]
    diffs = diff_all(before, after)
    hostnames = {d.hostname for d in diffs}
    assert "web1" in hostnames
    assert "web2" in hostnames


def test_diff_all_new_host_all_added():
    before = []
    after = [make_host("db1", [make_entry(command="backup.sh")])]
    diffs = diff_all(before, after)
    assert len(diffs) == 1
    assert len(diffs[0].added) == 1
    assert diffs[0].removed == []


def test_diff_all_removed_host_all_removed():
    before = [make_host("old", [make_entry(command="gone.sh")])]
    after = []
    diffs = diff_all(before, after)
    assert len(diffs) == 1
    assert len(diffs[0].removed) == 1
    assert diffs[0].added == []
