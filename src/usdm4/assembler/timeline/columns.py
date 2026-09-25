"""Parse — issue 63, part 63.4.

Turns one validated ``ScheduleTimelineInput`` (as a dict, the way the
Assembler hands its input on) into a ``ParsedTimeline``: one ``Column`` record
per column, every pattern read with the grammar. Pure: no builder, no USDM
objects. A pattern the grammar refuses raises ``PatternError`` and the
timeline is not built.

Until rule R4 (``docs/timeline_assembler_plan.md``) a timing span
(``Day -28 to Day -1``) is carried as text only, and ``cycle`` /
``cycle_length`` are carried as text and not parsed.
"""

from dataclasses import dataclass, field

from usdm4.assembler.schema.schedule_timeline_schema import family_of
from usdm4.assembler.timeline.grammar import (
    TimingPoint,
    Window,
    parse_label,
    parse_timing,
    parse_window,
)


@dataclass
class Column:
    """One column, parsed."""

    index: int
    id: str
    epoch_label: str | None = None
    visit_label: str | None = None
    visit_markers: list[str] = field(default_factory=list)
    timing_label: str | None = None
    timing: TimingPoint | None = None
    window_label: str | None = None
    window: Window | None = None
    cycle_label: str | None = None
    cycle_length_label: str | None = None
    notes: list[dict] = field(default_factory=list)


@dataclass
class ParsedTimeline:
    """One timeline, parsed. Activities and footnotes are carried as the
    validated dicts; they hold no patterns."""

    type: str
    family: str
    title: str | None
    description: str | None
    classification: dict
    columns: list[Column]
    activities: list[dict]
    footnotes: list[dict]

    @property
    def column_index(self) -> dict[str, int]:
        return {column.id: column.index for column in self.columns}


def _label(value: dict | None) -> str | None:
    if value is None:
        return None
    return (value.get("text") or "").strip() or (value.get("pattern") or "").strip()


def _pattern(value: dict | None) -> str | None:
    if value is None:
        return None
    pattern = value.get("pattern")
    return pattern if pattern is not None and pattern.strip() else None


def _is_span(pattern: str) -> bool:
    return " to " in pattern.strip().lower()


def parse_column(index: int, data: dict) -> Column:
    """Read one column's header values."""
    column = Column(index=index, id=data["id"])

    for name in ("epoch", "visit"):
        value = data.get(name)
        pattern = _pattern(value)
        if pattern is not None:
            parse_label(pattern, kind=name)
    column.epoch_label = _label(data.get("epoch"))
    column.visit_label = _label(data.get("visit"))
    column.visit_markers = list(data.get("markers") or [])

    timing = data.get("timing")
    column.timing_label = _label(timing)
    pattern = _pattern(timing)
    if pattern is not None and not _is_span(pattern):
        column.timing = parse_timing(pattern)

    window = data.get("window")
    column.window_label = _label(window)
    pattern = _pattern(window)
    if pattern is not None:
        column.window = parse_window(pattern)

    column.cycle_label = _label(data.get("cycle"))
    column.cycle_length_label = _label(data.get("cycle_length"))
    column.notes = list(data.get("notes") or [])
    return column


def parse_timeline(data: dict) -> ParsedTimeline:
    """Read one timeline. Raises ``PatternError`` on the first bad pattern."""
    return ParsedTimeline(
        type=data["type"],
        family=family_of(data["type"]),
        title=data.get("title"),
        description=data.get("description"),
        classification=dict(data.get("classification") or {}),
        columns=[parse_column(i, c) for i, c in enumerate(data.get("columns") or [])],
        activities=list(data.get("activities") or []),
        footnotes=list(data.get("footnotes") or []),
    )
