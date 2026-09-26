"""Parse — issue 63, part 63.4; structured input, issue 73 (U4-35).

Turns one validated ``ScheduleTimelineInput`` (as a dict, the way the
Assembler hands its input on) into a ``ParsedTimeline``: one ``Column`` record
per column. Pure: no builder, no USDM objects.

Every header value arrives structured (U4-35); parse copies it across. Printed
text is never read: it is kept only as the value's label, and when the caller
sent none the label is rendered from the structure. A value sent as text only
(the caller could not structure it) is carried as its label and not read —
a warning naming the timeline, column and field. A redacted value
(``redacted: true``) is recorded in ``Column.redacted`` and its text kept as
the label (issue 64). Footnote markers are carried per value
(``Column.markers``); the timeline's header row labels are carried as
``ParsedTimeline.rows`` and never read.
"""

from dataclasses import dataclass, field

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.assembler.schema.schedule_timeline_schema import (
    VALUE_FIELDS,
    family_of,
)
from usdm4.assembler.timeline.values import (
    CycleLength,
    CycleNumber,
    CycleRange,
    Delay,
    TimeRange,
    TimingPoint,
    Window,
    render_cycle,
    render_cycle_length,
    render_delay,
    render_time_range,
    render_timing,
    render_window,
    singular,
)

MODULE = "usdm4.assembler.timeline.columns"


@dataclass
class Column:
    """One column, parsed."""

    index: int
    id: str
    epoch_label: str | None = None
    visit_label: str | None = None
    timing_label: str | None = None
    timing: TimingPoint | None = None
    # A scheduled time that is a range; ``timing`` is then its start.
    time_range: TimeRange | None = None
    window_label: str | None = None
    window: Window | None = None
    # Where ``window`` came from: ``"window"`` (the window field) or, set by
    # the plan, ``"range"`` (a time range's span, U4-4).
    window_from: str | None = None
    cycle_label: str | None = None
    cycle_length_label: str | None = None
    cycle: CycleNumber | CycleRange | None = None
    cycle_length: CycleLength | None = None
    # The day within the cycle, kept when the plan replaces ``timing`` with
    # the timing from the start of the timeline (issue 66).
    cycle_day: TimingPoint | None = None
    delay_label: str | None = None
    delay: Delay | None = None
    notes: list[dict] = field(default_factory=list)
    # Value field name -> footnote markers printed on that value.
    markers: dict[str, list[str]] = field(default_factory=dict)
    # Value field names whose value the sponsor redacted.
    redacted: set[str] = field(default_factory=set)

    @property
    def all_markers(self) -> list[str]:
        """Every marker on this column's header, each once, in field order."""
        return list(
            dict.fromkeys(
                m for name in VALUE_FIELDS for m in self.markers.get(name, [])
            )
        )

    def is_redacted(self, name: str) -> bool:
        return name in self.redacted


@dataclass
class ParsedTimeline:
    """One timeline, parsed. Activities and footnotes are carried as the
    validated dicts."""

    type: str
    family: str
    title: str | None
    description: str | None
    classification: dict
    columns: list[Column]
    activities: list[dict]
    footnotes: list[dict]
    rows: dict[str, str] = field(default_factory=dict)
    # Printed text; the schema accepts it for conditional timelines only (R6).
    entry_condition: str | None = None
    # The name of the activity a profile hangs off; the schema accepts it for
    # profile timelines only (R7). Resolved once every timeline is built.
    attaches_to: str | None = None
    # Whether the protocol numbers a Day 0 (U4-35); default Day 1.
    day_zero: bool = False

    @property
    def column_index(self) -> dict[str, int]:
        return {column.id: column.index for column in self.columns}


def _text(value: dict) -> str:
    return (value.get("text") or "").strip()


def _structured(value: dict, *names: str) -> bool:
    return not value.get("redacted") and all(
        value.get(name) is not None for name in names
    )


class _Reader:
    """Reads one column's values, raising the warnings."""

    def __init__(self, data: dict, errors: Errors | None, t):
        self._data = data
        self._errors = errors
        self._where = (
            f"Timeline {t}, column '{data['id']}'" if t else f"Column '{data['id']}'"
        )

    def warn(self, name: str, message: str) -> None:
        if self._errors is not None:
            self._errors.warning(
                f"{self._where}, {name}: {message}",
                KlassMethodLocation(MODULE, "parse_column"),
            )

    def text_only(self, name: str, value: dict) -> None:
        self.warn(name, f"sent as text only ({_text(value)!r}); not read")


def _read_timing(column: Column, value: dict, reader: _Reader) -> None:
    unit = value.get("unit")
    if _structured(value, "start", "unit"):
        column.time_range = TimeRange(singular(unit), value["start"], value["end"])
        column.timing = TimingPoint(column.time_range.unit, column.time_range.start)
        rendered = render_time_range(column.time_range)
    elif _structured(value, "value", "unit"):
        column.timing = TimingPoint(singular(unit), value["value"])
        rendered = render_timing(column.timing)
    else:
        # Text only: no readable timing; the plan gives it a zero timing (U4-3).
        column.timing_label = _text(value)
        return
    column.timing_label = _text(value) or rendered


def _read_window(column: Column, value: dict, reader: _Reader) -> None:
    if _structured(value, "before", "after", "unit"):
        column.window = Window(value["before"], value["after"], singular(value["unit"]))
        column.window_from = "window"
        column.window_label = _text(value) or render_window(column.window)
    else:
        column.window_label = _text(value)
        reader.text_only("window", value)


def _read_cycle(column: Column, value: dict, reader: _Reader) -> None:
    if _structured(value, "first"):
        first, last = value["first"], value.get("last")
        column.cycle = CycleNumber(first) if last == first else CycleRange(first, last)
        column.cycle_label = _text(value) or render_cycle(column.cycle)
    else:
        column.cycle_label = _text(value)
        reader.text_only("cycle", value)


def _read_cycle_length(column: Column, value: dict, reader: _Reader) -> None:
    if _structured(value, "value", "unit"):
        column.cycle_length = CycleLength(value["value"], singular(value["unit"]))
        column.cycle_length_label = _text(value) or render_cycle_length(
            column.cycle_length
        )
    else:
        column.cycle_length_label = _text(value)
        reader.text_only("cycle_length", value)


def _read_delay(column: Column, value: dict, reader: _Reader) -> None:
    if _structured(value, "min", "unit"):
        column.delay = Delay(value["min"], value.get("max"), singular(value["unit"]))
        column.delay_label = _text(value) or render_delay(column.delay)
        reader.warn("delay", "a delay is not built until R8; carried only")
    else:
        column.delay_label = _text(value)
        reader.text_only("delay", value)


_READERS = {
    "timing": _read_timing,
    "window": _read_window,
    "cycle": _read_cycle,
    "cycle_length": _read_cycle_length,
    "delay": _read_delay,
}


def parse_column(
    index: int,
    data: dict,
    errors: Errors | None = None,
    t: int | None = None,
) -> Column:
    """Copy one column's structured values across. Problems are warnings on
    ``errors``; nothing here stops the timeline (U4-17)."""
    column = Column(index=index, id=data["id"])
    reader = _Reader(data, errors, t)

    for name in VALUE_FIELDS:
        value = data.get(name)
        if value is None:
            continue
        markers = list(value.get("markers") or [])
        if markers:
            column.markers[name] = markers
        if value.get("redacted"):
            column.redacted.add(name)
            setattr(column, f"{name}_label", _text(value))
            continue
        if name in ("epoch", "visit"):
            setattr(column, f"{name}_label", _text(value))
            continue
        _READERS[name](column, value, reader)

    column.notes = list(data.get("notes") or [])
    return column


def parse_timeline(
    data: dict, errors: Errors | None = None, t: int | None = None
) -> ParsedTimeline:
    """Read one timeline. Never raises for a bad value: problems are
    warnings on ``errors`` (U4-17)."""
    return ParsedTimeline(
        type=data["type"],
        family=family_of(data["type"]),
        title=data.get("title"),
        description=data.get("description"),
        classification=dict(data.get("classification") or {}),
        columns=[
            parse_column(i, c, errors, t)
            for i, c in enumerate(data.get("columns") or [])
        ],
        activities=list(data.get("activities") or []),
        footnotes=list(data.get("footnotes") or []),
        rows=dict(data.get("rows") or {}),
        entry_condition=data.get("entry_condition"),
        attaches_to=data.get("attaches_to"),
        day_zero=bool(data.get("day_zero")),
    )
