"""Generates a heatmap of cron activity across hours and weekdays."""

from dataclasses import dataclass, field
from typing import Dict, List
from crontab_audit.parser import CrontabEntry
from crontab_audit.overlap import _expand_field

HOURS = list(range(24))
WEEKDAYS = list(range(7))
WEEKDAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


@dataclass
class HeatmapCell:
    hour: int
    weekday: int
    count: int = 0
    commands: List[str] = field(default_factory=list)


@dataclass
class ScheduleHeatmap:
    """2D heatmap: weekday (0=Sun) x hour (0-23)."""
    cells: Dict[tuple, HeatmapCell] = field(default_factory=dict)

    def get(self, weekday: int, hour: int) -> HeatmapCell:
        key = (weekday, hour)
        if key not in self.cells:
            self.cells[key] = HeatmapCell(hour=hour, weekday=weekday)
        return self.cells[key]

    def peak_cells(self, top_n: int = 5) -> List[HeatmapCell]:
        sorted_cells = sorted(self.cells.values(), key=lambda c: c.count, reverse=True)
        return sorted_cells[:top_n]

    def total_scheduled_runs(self) -> int:
        return sum(c.count for c in self.cells.values())


def build_heatmap(entries: List[CrontabEntry]) -> ScheduleHeatmap:
    """Build a heatmap from a list of CrontabEntry objects."""
    heatmap = ScheduleHeatmap()
    for entry in entries:
        fields = entry.schedule_fields()
        if len(fields) < 5:
            continue
        _, hour_f, _, _, dow_f = fields[:5]
        try:
            hours = _expand_field(hour_f, 0, 23)
            weekdays = _expand_field(dow_f, 0, 6)
        except Exception:
            continue
        for wd in weekdays:
            for hr in hours:
                cell = heatmap.get(wd, hr)
                cell.count += 1
                cell.commands.append(entry.command)
    return heatmap


def format_heatmap(heatmap: ScheduleHeatmap) -> str:
    """Render heatmap as an ASCII grid (weekday rows x hour columns)."""
    header = "     " + "".join(f"{h:>3}" for h in HOURS)
    lines = [header, "     " + "---" * 24]
    for wd in WEEKDAYS:
        row = f"{WEEKDAY_NAMES[wd]:>4} |"
        for hr in HOURS:
            key = (wd, hr)
            count = heatmap.cells[key].count if key in heatmap.cells else 0
            row += f"{count:>3}" if count > 0 else "  ."
        lines.append(row)
    lines.append(f"\nTotal scheduled runs (per week): {heatmap.total_scheduled_runs()}")
    return "\n".join(lines)
