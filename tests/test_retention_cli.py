"""Tests for crontab_audit.retention_cli."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from crontab_audit.retention_cli import build_parser, cmd_check
from crontab_audit.parser import CrontabEntry
from crontab_audit.retention import RetentionIssue


def make_entry(command: str, host: str = "h1") -> CrontabEntry:
    return CrontabEntry(
        minute="0", hour="2", dom="*", month="*", dow="*",
        command=command, raw=f"0 2 * * * {command}", host=host,
    )


def _make_args(path="/fake", by_host=False, summary=False):
    parser = build_parser()
    argv = [path]
    if by_host:
        argv.append("--by-host")
    if summary:
        argv.append("--summary")
    return parser.parse_args(argv)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_cmd_check_no_issues_returns_0(tmp_path, capsys):
    crontab = tmp_path / "host1.crontab"
    crontab.write_text("0 1 * * * echo hello\n")
    args = _make_args(path=str(crontab))
    result = cmd_check(args)
    assert result == 0


def test_cmd_check_with_issues_returns_1(tmp_path, capsys):
    crontab = tmp_path / "host1.crontab"
    crontab.write_text("0 1 * * * pg_dump mydb >> /backups/db.sql\n")
    args = _make_args(path=str(crontab))
    result = cmd_check(args)
    assert result == 1


def test_cmd_check_summary_flag(tmp_path, capsys):
    crontab = tmp_path / "host1.crontab"
    crontab.write_text("0 1 * * * pg_dump mydb >> /backups/db.sql\n")
    args = _make_args(path=str(crontab), summary=True)
    cmd_check(args)
    captured = capsys.readouterr()
    assert "retention:" in captured.out


def test_cmd_check_by_host_flag(tmp_path, capsys):
    crontab = tmp_path / "host1.crontab"
    crontab.write_text("0 1 * * * pg_dump mydb >> /backups/db.sql\n")
    args = _make_args(path=str(crontab), by_host=True)
    cmd_check(args)
    captured = capsys.readouterr()
    # by-host output should mention the host name (derived from filename)
    assert len(captured.out) > 0


def test_cmd_check_directory(tmp_path, capsys):
    (tmp_path / "a.crontab").write_text("0 1 * * * echo safe\n")
    (tmp_path / "b.crontab").write_text("0 2 * * * pg_dump db >> /bak/out.sql\n")
    args = _make_args(path=str(tmp_path))
    result = cmd_check(args)
    assert result == 1
