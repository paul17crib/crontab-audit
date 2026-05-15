"""Tests for whitelist_cli.py."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from crontab_audit.whitelist import Whitelist, WhitelistEntry, save_whitelist
from crontab_audit.whitelist_cli import build_parser, cmd_add, cmd_apply, cmd_list


def _make_args(**kwargs):
    defaults = {"whitelist": "", "cmd": None, "input": "",
                "command": None, "schedule": None, "host": None, "reason": None}
    defaults.update(kwargs)
    import argparse
    ns = argparse.Namespace(**defaults)
    return ns


def _write_whitelist(entries, tmp_path):
    wl = Whitelist(entries=entries)
    p = str(tmp_path / "whitelist.json")
    save_whitelist(wl, p)
    return p


def test_build_parser_returns_parser():
    p = build_parser()
    assert p is not None


def test_cmd_list_empty_whitelist(tmp_path, capsys):
    wl_path = str(tmp_path / "whitelist.json")
    args = _make_args(whitelist=wl_path)
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "empty" in out.lower()


def test_cmd_list_shows_entries(tmp_path, capsys):
    wl_path = _write_whitelist(
        [WhitelistEntry(command_contains="backup", reason="safe")], tmp_path
    )
    args = _make_args(whitelist=wl_path)
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out


def test_cmd_add_creates_entry(tmp_path, capsys):
    wl_path = str(tmp_path / "whitelist.json")
    args = _make_args(whitelist=wl_path, command="cleanup", reason="routine")
    rc = cmd_add(args)
    assert rc == 0
    loaded = json.loads(Path(wl_path).read_text())
    assert loaded["whitelist"][0]["command_contains"] == "cleanup"


def test_cmd_add_appends_to_existing(tmp_path):
    wl_path = _write_whitelist(
        [WhitelistEntry(command_contains="backup")], tmp_path
    )
    args = _make_args(whitelist=wl_path, command="report", reason="")
    cmd_add(args)
    loaded = json.loads(Path(wl_path).read_text())
    assert len(loaded["whitelist"]) == 2


def test_cmd_apply_returns_0(tmp_path, capsys):
    cron_file = tmp_path / "crontab.txt"
    cron_file.write_text("0 * * * * /usr/bin/backup.sh\n")
    wl_path = _write_whitelist(
        [WhitelistEntry(command_contains="backup")], tmp_path
    )
    args = _make_args(whitelist=wl_path, input=str(cron_file))
    rc = cmd_apply(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "suppressed" in out


def test_cmd_apply_no_whitelist_file(tmp_path, capsys):
    cron_file = tmp_path / "crontab.txt"
    cron_file.write_text("0 * * * * /usr/bin/report.sh\n")
    wl_path = str(tmp_path / "missing.json")
    args = _make_args(whitelist=wl_path, input=str(cron_file))
    rc = cmd_apply(args)
    assert rc == 0
