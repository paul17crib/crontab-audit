"""Tests for whitelist.py and whitelist_report.py."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from crontab_audit.parser import CrontabEntry
from crontab_audit.whitelist import (
    Whitelist,
    WhitelistEntry,
    load_whitelist,
    save_whitelist,
)
from crontab_audit.whitelist_report import (
    format_whitelist_entries,
    format_whitelist_summary,
    format_whitelisted_entries,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*",
               command="/usr/bin/backup.sh", host="web1") -> CrontabEntry:
    e = CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=command,
    )
    e.host = host
    return e


# --- WhitelistEntry.matches ---

def test_matches_command_contains():
    w = WhitelistEntry(command_contains="backup")
    assert w.matches(make_entry(command="/usr/bin/backup.sh"))


def test_no_match_command_contains_absent():
    w = WhitelistEntry(command_contains="restore")
    assert not w.matches(make_entry(command="/usr/bin/backup.sh"))


def test_matches_host_scoped():
    w = WhitelistEntry(command_contains="backup", host="web1")
    assert w.matches(make_entry(host="web1"))
    assert not w.matches(make_entry(host="db1"))


def test_empty_whitelist_entry_never_matches():
    w = WhitelistEntry()
    assert not w.matches(make_entry())


# --- Whitelist ---

def test_is_whitelisted_true():
    wl = Whitelist(entries=[WhitelistEntry(command_contains="backup")])
    assert wl.is_whitelisted(make_entry(command="/usr/bin/backup.sh"))


def test_is_whitelisted_false():
    wl = Whitelist(entries=[WhitelistEntry(command_contains="restore")])
    assert not wl.is_whitelisted(make_entry(command="/usr/bin/backup.sh"))


def test_filter_removes_whitelisted():
    wl = Whitelist(entries=[WhitelistEntry(command_contains="backup")])
    entries = [make_entry(command="/usr/bin/backup.sh"), make_entry(command="/usr/bin/report.sh")]
    result = wl.filter(entries)
    assert len(result) == 1
    assert result[0].command == "/usr/bin/report.sh"


# --- Persistence ---

def test_save_and_load_whitelist():
    wl = Whitelist(entries=[
        WhitelistEntry(command_contains="backup", host="web1", reason="legacy")
    ])
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    save_whitelist(wl, path)
    loaded = load_whitelist(path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].command_contains == "backup"
    assert loaded.entries[0].host == "web1"
    assert loaded.entries[0].reason == "legacy"


# --- Report formatting ---

def test_format_whitelist_entries_empty():
    out = format_whitelist_entries([])
    assert "empty" in out.lower()


def test_format_whitelist_entries_shows_command():
    entries = [WhitelistEntry(command_contains="backup", reason="nightly")]
    out = format_whitelist_entries(entries)
    assert "backup" in out
    assert "nightly" in out


def test_format_whitelisted_entries_none_matched():
    wl = Whitelist(entries=[WhitelistEntry(command_contains="restore")])
    out = format_whitelisted_entries([make_entry()], wl)
    assert "No entries" in out


def test_format_whitelisted_entries_shows_match():
    wl = Whitelist(entries=[WhitelistEntry(command_contains="backup")])
    out = format_whitelisted_entries([make_entry(command="/usr/bin/backup.sh")], wl)
    assert "backup" in out


def test_format_whitelist_summary():
    out = format_whitelist_summary(10, 3)
    assert "10" in out
    assert "3" in out
    assert "7" in out
