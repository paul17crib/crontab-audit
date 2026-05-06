"""Tests for crontab_audit.output_limiter_cli."""

import pytest
from unittest.mock import patch, mock_open
from crontab_audit.output_limiter_cli import cmd_page, cmd_truncate, cmd_filter, build_parser


SAMPLE_LINES = "\n".join(f"line {i}" for i in range(1, 21))  # 20 lines


def _make_args(**kwargs):
    import argparse
    defaults = {"file": "fake.txt", "page": 1, "page_size": 10,
                "max_lines": 5, "keyword": "line", "case_sensitive": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@patch("builtins.open", mock_open(read_data=SAMPLE_LINES))
def test_cmd_page_returns_0(capsys):
    args = _make_args(page=1, page_size=10)
    rc = cmd_page(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Page 1" in out


@patch("builtins.open", mock_open(read_data=SAMPLE_LINES))
def test_cmd_page_shows_next_hint(capsys):
    args = _make_args(page=1, page_size=10)
    cmd_page(args)
    out = capsys.readouterr().out
    assert "--page 2" in out


@patch("builtins.open", mock_open(read_data=SAMPLE_LINES))
def test_cmd_truncate_returns_0(capsys):
    args = _make_args(max_lines=5)
    rc = cmd_truncate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "line 1" in out


@patch("builtins.open", mock_open(read_data=SAMPLE_LINES))
def test_cmd_truncate_truncates_output(capsys):
    args = _make_args(max_lines=3)
    cmd_truncate(args)
    out = capsys.readouterr().out
    assert "more lines not shown" in out


@patch("builtins.open", mock_open(read_data=SAMPLE_LINES))
def test_cmd_filter_returns_0_on_match(capsys):
    args = _make_args(keyword="line 1", case_sensitive=False)
    rc = cmd_filter(args)
    assert rc == 0


@patch("builtins.open", mock_open(read_data=SAMPLE_LINES))
def test_cmd_filter_returns_1_on_no_match(capsys):
    args = _make_args(keyword="zzznomatch", case_sensitive=False)
    rc = cmd_filter(args)
    assert rc == 1


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_build_parser_page_subcommand():
    parser = build_parser()
    args = parser.parse_args(["page", "some_file.txt", "--page", "2", "--page-size", "25"])
    assert args.command == "page"
    assert args.page == 2
    assert args.page_size == 25


def test_build_parser_filter_subcommand():
    parser = build_parser()
    args = parser.parse_args(["filter", "out.txt", "error", "--case-sensitive"])
    assert args.command == "filter"
    assert args.keyword == "error"
    assert args.case_sensitive is True
