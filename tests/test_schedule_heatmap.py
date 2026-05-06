"""Tests for crontab_audit.schedule_heatmap."""

import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.schedule_heatmap import (
    build_heatmap,
    format_heatmap,
    ScheduleHeatmap,
    WEEKDAY_NAMES,
)


def make_entry(minute="0", hour="6", dom="*", month="*", dow="*", command="echo hi", host="host1"):
    return CrontabEntry(
        minute=minute, hour=hour, dom=dom, month=month,
        dow=dow, command=command, host=host, raw=f"{minute} {hour} {dom} {month} {dow} {command}"
    )


def test_build_heatmap_single_entry():
    entry = make_entry(hour="6", dow="1")  # Mon at 06:xx
    heatmap = build_heatmap([entry])
    cell = heatmap.get(1, 6)
    assert cell.count == 1
    assert "echo hi" in cell.commands


def test_build_heatmap_star_dow_increments_all_weekdays():
    entry = make_entry(hour="12", dow="*")
    heatmap = build_heatmap([entry])
    for wd in range(7):
        assert heatmap.get(wd, 12).count == 1


def test_build_heatmap_star_hour_increments_all_hours():
    entry = make_entry(hour="*", dow="0")  # every hour on Sunday
    heatmap = build_heatmap([entry])
    for hr in range(24):
        assert heatmap.get(0, hr).count == 1


def test_build_heatmap_range_fields():
    entry = make_entry(hour="8-10", dow="1-3")
    heatmap = build_heatmap([entry])
    for wd in [1, 2, 3]:
        for hr in [8, 9, 10]:
            assert heatmap.get(wd, hr).count == 1
    assert heatmap.get(0, 8).count == 0


def test_build_heatmap_step_fields():
    entry = make_entry(hour="*/6", dow="*")  # hours 0,6,12,18
    heatmap = build_heatmap([entry])
    for wd in range(7):
        for hr in [0, 6, 12, 18]:
            assert heatmap.get(wd, hr).count == 1
        assert heatmap.get(wd, 1).count == 0


def test_build_heatmap_multiple_entries_accumulate():
    entries = [
        make_entry(hour="9", dow="1"),
        make_entry(hour="9", dow="1", command="backup.sh"),
    ]
    heatmap = build_heatmap(entries)
    cell = heatmap.get(1, 9)
    assert cell.count == 2
    assert len(cell.commands) == 2


def test_peak_cells_returns_top_n():
    entries = [
        make_entry(hour="9", dow="1"),
        make_entry(hour="9", dow="1", command="b.sh"),
        make_entry(hour="12", dow="3"),
    ]
    heatmap = build_heatmap(entries)
    peaks = heatmap.peak_cells(top_n=1)
    assert len(peaks) == 1
    assert peaks[0].count == 2


def test_total_scheduled_runs():
    entry = make_entry(hour="0", dow="0")  # 1 run per week
    heatmap = build_heatmap([entry])
    assert heatmap.total_scheduled_runs() == 1


def test_format_heatmap_contains_weekday_names():
    entry = make_entry(hour="8", dow="2")
    heatmap = build_heatmap([entry])
    output = format_heatmap(heatmap)
    for name in WEEKDAY_NAMES:
        assert name in output


def test_format_heatmap_contains_total():
    entry = make_entry(hour="*", dow="*")
    heatmap = build_heatmap([entry])
    output = format_heatmap(heatmap)
    assert "Total scheduled runs" in output


def test_build_heatmap_empty_entries():
    heatmap = build_heatmap([])
    assert heatmap.total_scheduled_runs() == 0
    assert len(heatmap.cells) == 0
