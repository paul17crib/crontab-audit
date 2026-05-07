"""Tests for crontab_audit.output_formatter."""

import csv
import io
import json

import pytest

from crontab_audit.output_formatter import (
    format_as_csv,
    format_as_json,
    format_as_text,
    render,
)

ROWS = [
    {"host": "web01", "command": "/usr/bin/backup", "count": 3},
    {"host": "db01", "command": "/usr/bin/vacuum", "count": 1},
]


# ---------------------------------------------------------------------------
# format_as_text
# ---------------------------------------------------------------------------

def test_format_as_text_includes_headers():
    out = format_as_text(ROWS)
    assert "host" in out
    assert "command" in out
    assert "count" in out


def test_format_as_text_includes_values():
    out = format_as_text(ROWS)
    assert "web01" in out
    assert "/usr/bin/vacuum" in out


def test_format_as_text_with_title():
    out = format_as_text(ROWS, title="My Report")
    assert out.startswith("My Report")


def test_format_as_text_empty_rows():
    out = format_as_text([], title="Empty")
    assert "(no results)" in out


def test_format_as_text_no_title_no_leading_blank():
    out = format_as_text(ROWS)
    assert out.startswith("host") or out.startswith(" ")


# ---------------------------------------------------------------------------
# format_as_json
# ---------------------------------------------------------------------------

def test_format_as_json_is_valid_json():
    out = format_as_json(ROWS)
    parsed = json.loads(out)
    assert "results" in parsed


def test_format_as_json_row_count():
    out = format_as_json(ROWS)
    parsed = json.loads(out)
    assert len(parsed["results"]) == 2


def test_format_as_json_includes_title():
    out = format_as_json(ROWS, title="Audit")
    parsed = json.loads(out)
    assert parsed["title"] == "Audit"


def test_format_as_json_no_title_key_absent():
    out = format_as_json(ROWS)
    parsed = json.loads(out)
    assert "title" not in parsed


def test_format_as_json_empty_rows():
    out = format_as_json([])
    parsed = json.loads(out)
    assert parsed["results"] == []


# ---------------------------------------------------------------------------
# format_as_csv
# ---------------------------------------------------------------------------

def test_format_as_csv_has_header_row():
    out = format_as_csv(ROWS)
    reader = csv.DictReader(io.StringIO(out))
    assert set(reader.fieldnames or []) == {"host", "command", "count"}


def test_format_as_csv_data_rows():
    out = format_as_csv(ROWS)
    reader = csv.DictReader(io.StringIO(out))
    data = list(reader)
    assert len(data) == 2
    assert data[0]["host"] == "web01"


def test_format_as_csv_empty_rows_returns_empty_string():
    assert format_as_csv([]) == ""


# ---------------------------------------------------------------------------
# render dispatcher
# ---------------------------------------------------------------------------

def test_render_text_mode():
    out = render(ROWS, mode="text", title="T")
    assert "web01" in out
    assert not out.startswith("{")


def test_render_json_mode():
    out = render(ROWS, mode="json")
    parsed = json.loads(out)
    assert "results" in parsed


def test_render_csv_mode():
    out = render(ROWS, mode="csv")
    assert "host" in out.splitlines()[0]


def test_render_defaults_to_text():
    out = render(ROWS)
    assert "host" in out
    assert not out.strip().startswith("{")
