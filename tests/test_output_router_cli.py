"""Tests for crontab_audit.output_router_cli."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from crontab_audit.output_router_cli import build_parser, cmd_route, main


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "paths": [],
        "output": None,
        "format": "text",
        "append": False,
        "also_stdout": False,
        "verbose": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_defaults():
    p = build_parser()
    args = p.parse_args(["somefile"])
    assert args.format == "text"
    assert args.append is False
    assert args.also_stdout is False


def test_cmd_route_to_stdout(tmp_path, capsys):
    cron = tmp_path / "host1"
    cron.write_text("* * * * * echo hi\n")
    args = _make_args(paths=[str(cron)])
    rc = cmd_route(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_cmd_route_to_file(tmp_path):
    cron = tmp_path / "host1"
    cron.write_text("0 * * * * /usr/bin/backup.sh\n")
    out = tmp_path / "result.txt"
    args = _make_args(paths=[str(cron)], output=str(out))
    rc = cmd_route(args)
    assert rc == 0
    assert out.exists()
    assert len(out.read_text()) > 0


def test_cmd_route_directory(tmp_path):
    d = tmp_path / "hosts"
    d.mkdir()
    (d / "web01").write_text("5 4 * * * /bin/clean\n")
    out = tmp_path / "out.txt"
    args = _make_args(paths=[str(d)], output=str(out))
    rc = cmd_route(args)
    assert rc == 0


def test_cmd_route_returns_1_on_error(tmp_path):
    cron = tmp_path / "host1"
    cron.write_text("* * * * * echo hi\n")
    bad_out = "/no_such_dir/output.txt"
    args = _make_args(paths=[str(cron)], output=bad_out)
    with patch("crontab_audit.output_router_cli.route_output") as mock_route:
        mock_route.return_value = MagicMock(
            has_errors=True, failed=[f"{bad_out}: Permission denied"]
        )
        rc = cmd_route(args)
    assert rc == 1


def test_main_no_args_exits(monkeypatch):
    monkeypatch.setattr("sys.argv", ["output-router"])
    with pytest.raises(SystemExit):
        main()
