"""Tests for crontab_audit.output_router."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from crontab_audit.output_router import (
    OutputRoute,
    RoutingResult,
    build_routes_from_args,
    route_output,
)


# ---------------------------------------------------------------------------
# OutputRoute
# ---------------------------------------------------------------------------

def test_output_route_str_write():
    r = OutputRoute(dest="stdout", fmt="text", append=False)
    assert "write" in str(r)
    assert "stdout" in str(r)


def test_output_route_str_append():
    r = OutputRoute(dest="/tmp/out.txt", fmt="json", append=True)
    assert "append" in str(r)


# ---------------------------------------------------------------------------
# RoutingResult
# ---------------------------------------------------------------------------

def test_routing_result_no_errors():
    rr = RoutingResult(succeeded=["stdout"])
    assert not rr.has_errors


def test_routing_result_has_errors():
    rr = RoutingResult(failed=["/bad/path: Permission denied"])
    assert rr.has_errors


def test_routing_result_str():
    rr = RoutingResult(succeeded=["stdout"], failed=[])
    assert "ok=1" in str(rr)
    assert "failed=0" in str(rr)


# ---------------------------------------------------------------------------
# route_output — stdout
# ---------------------------------------------------------------------------

def test_route_output_to_stdout(capsys):
    routes = [OutputRoute(dest="stdout", fmt="text")]
    result = route_output("hello world", routes)
    captured = capsys.readouterr()
    assert "hello world" in captured.out
    assert not result.has_errors
    assert "stdout" in result.succeeded


def test_route_output_to_stderr(capsys):
    routes = [OutputRoute(dest="stderr", fmt="text")]
    result = route_output("err msg", routes)
    captured = capsys.readouterr()
    assert "err msg" in captured.err
    assert not result.has_errors


def test_route_output_appends_newline_if_missing(capsys):
    routes = [OutputRoute(dest="stdout", fmt="text")]
    route_output("no newline", routes)
    captured = capsys.readouterr()
    assert captured.out.endswith("\n")


def test_route_output_does_not_double_newline(capsys):
    routes = [OutputRoute(dest="stdout", fmt="text")]
    route_output("already\n", routes)
    captured = capsys.readouterr()
    assert captured.out == "already\n"


# ---------------------------------------------------------------------------
# route_output — file
# ---------------------------------------------------------------------------

def test_route_output_to_file(tmp_path):
    out = tmp_path / "result.txt"
    routes = [OutputRoute(dest=str(out), fmt="text")]
    result = route_output("file content", routes)
    assert not result.has_errors
    assert out.read_text() == "file content\n"


def test_route_output_to_file_append(tmp_path):
    out = tmp_path / "log.txt"
    out.write_text("first\n")
    routes = [OutputRoute(dest=str(out), fmt="text", append=True)]
    route_output("second", routes)
    assert "first" in out.read_text()
    assert "second" in out.read_text()


def test_route_output_multiple_routes(tmp_path, capsys):
    out = tmp_path / "multi.txt"
    routes = [
        OutputRoute(dest="stdout", fmt="text"),
        OutputRoute(dest=str(out), fmt="text"),
    ]
    result = route_output("multi", routes)
    assert len(result.succeeded) == 2
    captured = capsys.readouterr()
    assert "multi" in captured.out
    assert "multi" in out.read_text()


# ---------------------------------------------------------------------------
# build_routes_from_args
# ---------------------------------------------------------------------------

def test_build_routes_no_file():
    routes = build_routes_from_args(output_file=None)
    assert len(routes) == 1
    assert routes[0].dest == "stdout"


def test_build_routes_with_file():
    routes = build_routes_from_args(output_file="/tmp/out.txt", fmt="json")
    assert len(routes) == 1
    assert routes[0].dest == "/tmp/out.txt"
    assert routes[0].fmt == "json"


def test_build_routes_also_stdout():
    routes = build_routes_from_args(
        output_file="/tmp/out.txt", also_stdout=True
    )
    dests = [r.dest for r in routes]
    assert "/tmp/out.txt" in dests
    assert "stdout" in dests


def test_build_routes_append_flag():
    routes = build_routes_from_args(output_file="/tmp/out.txt", append=True)
    assert routes[0].append is True
