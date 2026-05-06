"""Tests for crontab_audit.command_stats."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.command_stats import (
    _command_key,
    build_command_stats,
    top_commands,
    commands_by_host,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0", hour="*", dom="*", month="*", dow="*",
        command=command, host=host, raw=f"0 * * * * {command}",
    )


def test_command_key_simple():
    assert _command_key("/usr/bin/python3 script.py") == "python3"


def test_command_key_bare():
    assert _command_key("backup.sh") == "backup.sh"


def test_command_key_with_env_prefix():
    assert _command_key("FOO=bar /usr/bin/rsync -a /src /dst") == "rsync"


def test_command_key_empty():
    assert _command_key("") == ""


def test_build_command_stats_basic():
    entries = [
        make_entry("/usr/bin/rsync -a /src /dst", "host1"),
        make_entry("/usr/bin/rsync -a /src /dst", "host2"),
        make_entry("/usr/bin/python3 job.py", "host1"),
    ]
    stats = build_command_stats(entries)
    assert "rsync" in stats
    assert stats["rsync"].count == 2
    assert set(stats["rsync"].hosts) == {"host1", "host2"}
    assert "python3" in stats
    assert stats["python3"].count == 1


def test_build_command_stats_empty():
    assert build_command_stats([]) == {}


def test_top_commands_ordering():
    entries = [
        make_entry("rsync -a /src /dst"),
        make_entry("rsync -a /src /dst"),
        make_entry("rsync -a /src /dst"),
        make_entry("python3 job.py"),
        make_entry("python3 job.py"),
        make_entry("bash cleanup.sh"),
    ]
    top = top_commands(entries, n=2)
    assert top[0].command == "rsync"
    assert top[0].count == 3
    assert top[1].command == "python3"
    assert len(top) == 2


def test_top_commands_n_larger_than_results():
    entries = [make_entry("rsync")]
    top = top_commands(entries, n=100)
    assert len(top) == 1


def test_commands_by_host():
    entries = [
        make_entry("rsync -a /src", "hostA"),
        make_entry("python3 job.py", "hostA"),
        make_entry("bash cleanup.sh", "hostB"),
    ]
    result = commands_by_host(entries)
    assert "hostA" in result
    assert "rsync" in result["hostA"]
    assert "python3" in result["hostA"]
    assert result["hostB"] == ["bash"]


def test_command_stats_str():
    entries = [make_entry("rsync -a", "host1"), make_entry("rsync -b", "host2")]
    stats = build_command_stats(entries)
    s = str(stats["rsync"])
    assert "rsync" in s
    assert "2" in s
