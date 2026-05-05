"""Tests for crontab_audit.loader."""

import os
import textwrap
import tempfile

import pytest

from crontab_audit.loader import (
    HostCrontab,
    load_from_text,
    load_from_file,
    load_from_directory,
)


SIMPLE_CRONTAB = textwrap.dedent("""\
    # daily backup
    0 2 * * * /usr/bin/backup.sh
    # weekly cleanup
    0 3 * * 0 /usr/bin/cleanup.sh
""")

INVALID_CRONTAB = textwrap.dedent("""\
    0 2 * * * /usr/bin/backup.sh
    not_a_valid_crontab_line_at_all
    */5 * * * * /usr/bin/check.sh
""")


def test_load_from_text_returns_host_crontab():
    result = load_from_text("web01", SIMPLE_CRONTAB)
    assert isinstance(result, HostCrontab)
    assert result.hostname == "web01"


def test_load_from_text_parses_entries():
    result = load_from_text("web01", SIMPLE_CRONTAB)
    assert len(result.entries) == 2
    assert result.entries[0].command == "/usr/bin/backup.sh"
    assert result.entries[1].command == "/usr/bin/cleanup.sh"


def test_load_from_text_skips_comments_and_blanks():
    result = load_from_text("web01", SIMPLE_CRONTAB)
    assert len(result.parse_errors) == 0


def test_load_from_text_records_parse_errors():
    result = load_from_text("web01", INVALID_CRONTAB)
    assert len(result.parse_errors) == 1
    assert "line 2" in result.parse_errors[0]


def test_load_from_text_hostname_attached_to_entries():
    result = load_from_text("db01", SIMPLE_CRONTAB)
    for entry in result.entries:
        assert entry.hostname == "db01"


def test_load_from_file_uses_filename_as_hostname():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".crontab", prefix="myhost", delete=False
    ) as tmp:
        tmp.write(SIMPLE_CRONTAB)
        tmp_path = tmp.name
    try:
        result = load_from_file(tmp_path)
        assert result.hostname == os.path.splitext(os.path.basename(tmp_path))[0]
        assert len(result.entries) == 2
    finally:
        os.unlink(tmp_path)


def test_load_from_file_explicit_hostname():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as tmp:
        tmp.write(SIMPLE_CRONTAB)
        tmp_path = tmp.name
    try:
        result = load_from_file(tmp_path, hostname="custom-host")
        assert result.hostname == "custom-host"
    finally:
        os.unlink(tmp_path)


def test_load_from_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        for name, content in [
            ("host-a.crontab", SIMPLE_CRONTAB),
            ("host-b.txt", "*/10 * * * * /usr/bin/poll.sh\n"),
            ("ignored.cfg", "some=config"),
        ]:
            with open(os.path.join(tmpdir, name), "w") as fh:
                fh.write(content)

        results = load_from_directory(tmpdir)

    assert set(results.keys()) == {"host-a", "host-b"}
    assert len(results["host-a"].entries) == 2
    assert len(results["host-b"].entries) == 1
