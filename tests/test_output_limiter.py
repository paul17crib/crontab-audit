"""Tests for crontab_audit.output_limiter."""

import pytest
from crontab_audit.output_limiter import paginate, truncate, filter_lines, PagedOutput


LINES = [f"line {i}" for i in range(1, 11)]  # 10 lines


# --- paginate ---

def test_paginate_first_page():
    result = paginate(LINES, page=1, page_size=3)
    assert isinstance(result, PagedOutput)
    assert result.lines == ["line 1", "line 2", "line 3"]
    assert result.page == 1
    assert result.total_pages == 4
    assert result.total_lines == 10


def test_paginate_last_page_partial():
    result = paginate(LINES, page=4, page_size=3)
    assert result.lines == ["line 10"]
    assert result.page == 4
    assert not result.has_next()
    assert result.has_prev()


def test_paginate_page_beyond_max_clamps():
    result = paginate(LINES, page=99, page_size=5)
    assert result.page == result.total_pages


def test_paginate_page_below_one_clamps():
    result = paginate(LINES, page=-5, page_size=5)
    assert result.page == 1


def test_paginate_empty_lines():
    result = paginate([], page=1, page_size=10)
    assert result.lines == []
    assert result.total_pages == 1
    assert result.total_lines == 0


def test_paginate_invalid_page_size_raises():
    with pytest.raises(ValueError):
        paginate(LINES, page=1, page_size=0)


def test_paginate_str_contains_header():
    result = paginate(LINES, page=2, page_size=5)
    text = str(result)
    assert "Page 2/2" in text
    assert "10 total lines" in text


# --- truncate ---

def test_truncate_no_truncation_needed():
    result = truncate(LINES, max_lines=20)
    assert result == LINES


def test_truncate_truncates_correctly():
    result = truncate(LINES, max_lines=4)
    assert len(result) == 5  # 4 lines + ellipsis
    assert result[-1].startswith("...")
    assert "6 more" in result[-1]


def test_truncate_custom_ellipsis():
    result = truncate(LINES, max_lines=3, ellipsis_msg="[truncated]")
    assert result[-1] == "[truncated]"


def test_truncate_invalid_max_raises():
    with pytest.raises(ValueError):
        truncate(LINES, max_lines=0)


def test_truncate_exact_boundary():
    result = truncate(LINES, max_lines=10)
    assert result == LINES


# --- filter_lines ---

def test_filter_lines_basic():
    lines = ["hello world", "foo bar", "hello again"]
    result = filter_lines(lines, "hello")
    assert result == ["hello world", "hello again"]


def test_filter_lines_case_insensitive_default():
    lines = ["HELLO world", "foo bar"]
    result = filter_lines(lines, "hello")
    assert result == ["HELLO world"]


def test_filter_lines_case_sensitive():
    lines = ["HELLO world", "hello again"]
    result = filter_lines(lines, "hello", case_sensitive=True)
    assert result == ["hello again"]


def test_filter_lines_no_match():
    result = filter_lines(LINES, "zzz")
    assert result == []


def test_filter_lines_all_match():
    result = filter_lines(LINES, "line")
    assert len(result) == len(LINES)
