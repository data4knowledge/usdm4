"""Parse — issue 63, part 63.4; issue 65.

Turns one validated ``ScheduleTimelineInput`` (as a dict, the way the
Assembler hands its input on) into a ``ParsedTimeline``: one ``Column`` record
per column. Pure: no builder, no USDM objects.

Issue 65 (design § 3.2, U4-16, U4-17): each of timing and window is read the same
way — the pattern when there is one; else the printed text, read by
``printed.py``; else nothing. A pattern the grammar refuses is a warning and
is set aside, and the field falls back to its printed text: the timeline is
always built if at all possible. Every problem found reading a value is a
warning naming the timeline, column and field. A time range
(``Day -28 to Day -1``) sets ``time_range`` and, as the timing point, its
start.

Issue 66 (R4 part 2): ``cycle`` and ``cycle_length`` are read the same way —
the pattern, else the printed text, else nothing — into ``Column.cycle``
(a single cycle or a range) and ``Column.cycle_length``. The plan times them.

Issue 64: a field whose pattern is the redaction ``CCI`` is never read; its
name is recorded in ``Column.redacted`` and its printed text kept as the
label. Footnote markers are carried per header value (``Column.markers``),
and the timeline's header row labels are carried as ``ParsedTimeline.rows``.
"""

from dataclasses import dataclass, field

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.assembler.schema.schedule_timeline_schema import (
    HEADER_FIELDS,
    family_of,
)
from usdm4.assembler.timeline.grammar import (
    CycleLength,
    CycleNumber,
    CycleRange,
    PatternError,
    TimeRange,
    TimingPoint,
    Window,
    is_redacted,
    is_time_range,
    parse_cycle,
    parse_cycle_length,
    parse_time_range,
    parse_timing,
    parse_window,
)
from usdm4.assembler.timeline.printed import (
    UpTo,
    is_blank,
    read_cycle,
    read_cycle_length,
    read_timing,
    read_window,
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
    # A scheduled time printed as a range; ``timing`` is then its start.
    time_range: TimeRange | None = None
    # A printed ``≤N``, placed by the plan (U4-18).
    up_to: UpTo | None = None
    window_label: str | None = None
    window: Window | None = None
    # Where ``window`` came from: ``"window"`` (the window field) or
    # ``"timing"`` (a window printed in the timing cell, U4-16).
    window_from: str | None = None
    cycle_label: str | None = None
    cycle_length_label: str | None = None
    cycle: CycleNumber | CycleRange | None = None
    cycle_length: CycleLength | None = None
    # The day within the cycle as parsed, kept when the plan replaces
    # ``timing`` with the timing from the start of the timeline (issue 66).
    cycle_day: TimingPoint | None = None
    notes: list[dict] = field(default_factory=list)
    # Header field name -> footnote markers printed on that value.
    markers: dict[str, list[str]] = field(default_factory=dict)
    # Header field names whose value the sponsor redacted (pattern ``CCI``).
    redacted: set[str] = field(default_factory=set)

    @property
    def all_markers(self) -> list[str]:
        """Every marker on this column's header, each once, in field order."""
        return list(
            dict.fromkeys(
                m for name in HEADER_FIELDS for m in self.markers.get(name, [])
            )
        )

    def is_redacted(self, name: str) -> bool:
        return name in self.redacted


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
    rows: dict[str, str] = field(default_factory=dict)
    # Printed text; the schema accepts it for conditional timelines only (R6).
    entry_condition: str | None = None
    # The name of the activity a profile hangs off; the schema accepts it for
    # profile timelines only (R7). Resolved once every timeline is built.
    attaches_to: str | None = None

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


class _Reader:
    """Reads one column's header values, raising the warnings (U4-16)."""

    def __init__(self, data: dict, rows: dict, errors: Errors | None, t):
        self._data = data
        self._rows = rows
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

    def text(self, name: str) -> str | None:
        value = self._data.get(name)
        return None if value is None else (value.get("text") or "")

    def row(self, name: str) -> str | None:
        return self._rows.get(name)


def _read_timing(column: Column, reader: _Reader, pattern: str | None) -> Window | None:
    """Timing: the pattern, else the printed text, else nothing. Returns a
    window printed in the timing cell, if any."""
    if pattern is not None:
        try:
            if is_time_range(pattern):
                column.time_range = parse_time_range(pattern)
                column.timing = TimingPoint(
                    column.time_range.unit, column.time_range.start
                )
            else:
                column.timing = parse_timing(pattern)
            return None
        except PatternError as e:
            reader.warn("timing", f"{e}; reading the printed text instead")
    text = reader.text("timing")
    if is_blank(text):
        return None
    read = read_timing(text, reader.row("timing"))
    if read is None:
        reader.warn("timing", f"printed text {text!r} not read")
        return None
    if read.unit_defaulted:
        reader.warn("timing", f"no unit stated for {text!r}; read as days")
    if isinstance(read.timing, TimeRange):
        column.time_range = read.timing
        column.timing = TimingPoint(read.timing.unit, read.timing.start)
    elif isinstance(read.timing, UpTo):
        column.up_to = read.timing
    else:
        column.timing = read.timing
    return read.window


def _timing_unit(column: Column) -> str | None:
    if column.timing:
        return column.timing.unit
    return column.up_to.unit if column.up_to else None


def _read_window(column: Column, reader: _Reader, pattern: str | None) -> Window | None:
    """Window field: the pattern, else the printed text, else nothing."""
    if pattern is not None:
        try:
            return parse_window(pattern)
        except PatternError as e:
            reader.warn("window", f"{e}; reading the printed text instead")
    text = reader.text("window")
    if is_blank(text):
        return None
    read = read_window(text, reader.row("window"), _timing_unit(column))
    if read is None:
        reader.warn("window", f"printed text {text!r} not read")
        return None
    if read.unit_defaulted:
        reader.warn("window", f"no unit stated for {text!r}; read as days")
    return read.window


_WARNED = object()  # a reader that has already warned why it read nothing


def _read_cycle_field(reader: _Reader, name: str, pattern: str | None, parse, read):
    """A cycle or cycle length: the pattern, else the printed text, else
    nothing. Problems are warnings naming the field."""
    if pattern is not None:
        try:
            return parse(pattern)
        except PatternError as e:
            reader.warn(name, f"{e}; reading the printed text instead")
    text = reader.text(name)
    if is_blank(text):
        return None
    value = read(text)
    if value is _WARNED:
        return None
    if value is None:
        reader.warn(name, f"printed text {text!r} not read")
    return value


def _read_cycle_length(reader: _Reader, text: str):
    """A printed cycle length; a bare number takes its unit from the cycle
    length row label, else the timing row label (issue 68, U4-28). A bare
    number with no unit stated anywhere is warned as such and not read."""
    length = read_cycle_length(text, reader.row("cycle_length"), reader.row("timing"))
    if length is None and read_cycle_length(text, "days") is not None:
        reader.warn(
            "cycle_length",
            f"no unit stated for {text!r} in the value, the cycle length row "
            "label or the timing row label; not read",
        )
        return _WARNED
    return length


def parse_column(
    index: int,
    data: dict,
    rows: dict | None = None,
    errors: Errors | None = None,
    t: int | None = None,
) -> Column:
    """Read one column's header values. ``rows`` are the timeline's header
    row labels, where a bare number's unit is stated. Problems are warnings
    on ``errors``; nothing here stops the timeline (U4-17)."""
    column = Column(index=index, id=data["id"])
    reader = _Reader(data, rows or {}, errors, t)

    # Redaction and markers first: both apply to every field alike.
    for name in HEADER_FIELDS:
        value = data.get(name)
        if value is None:
            continue
        if is_redacted(_pattern(value)):
            column.redacted.add(name)
        markers = list(value.get("markers") or [])
        if markers:
            column.markers[name] = markers

    def pattern_of(name: str) -> str | None:
        return _pattern(data.get(name))

    # Epoch and visit are free text: a pattern, when given, is the label only
    # where no text was printed (``_label``); there is nothing to refuse.
    column.epoch_label = _label(data.get("epoch"))
    column.visit_label = _label(data.get("visit"))

    column.timing_label = _label(data.get("timing"))
    cell_window = None
    if not column.is_redacted("timing"):
        cell_window = _read_timing(column, reader, pattern_of("timing"))

    column.window_label = _label(data.get("window"))
    field_window = None
    if not column.is_redacted("window"):
        field_window = _read_window(column, reader, pattern_of("window"))

    if field_window is not None:
        column.window, column.window_from = field_window, "window"
        if cell_window is not None:
            reader.warn(
                "window",
                "the timing cell prints a window too; the window field is used",
            )
        elif column.time_range is not None:
            reader.warn(
                "window",
                "the timing is a time range; the window field is used",
            )
    elif cell_window is not None:
        column.window, column.window_from = cell_window, "timing"

    column.cycle_label = _label(data.get("cycle"))
    column.cycle_length_label = _label(data.get("cycle_length"))
    if not column.is_redacted("cycle"):
        column.cycle = _read_cycle_field(
            reader, "cycle", pattern_of("cycle"), parse_cycle, read_cycle
        )
    if not column.is_redacted("cycle_length"):
        column.cycle_length = _read_cycle_field(
            reader,
            "cycle_length",
            pattern_of("cycle_length"),
            parse_cycle_length,
            lambda text: _read_cycle_length(reader, text),
        )
    column.notes = list(data.get("notes") or [])
    return column


def parse_timeline(
    data: dict, errors: Errors | None = None, t: int | None = None
) -> ParsedTimeline:
    """Read one timeline. Never raises for a bad value: problems are
    warnings on ``errors`` (U4-17)."""
    rows = dict(data.get("rows") or {})
    return ParsedTimeline(
        type=data["type"],
        family=family_of(data["type"]),
        title=data.get("title"),
        description=data.get("description"),
        classification=dict(data.get("classification") or {}),
        columns=[
            parse_column(i, c, rows, errors, t)
            for i, c in enumerate(data.get("columns") or [])
        ],
        activities=list(data.get("activities") or []),
        footnotes=list(data.get("footnotes") or []),
        rows=rows,
        entry_condition=data.get("entry_condition"),
        attaches_to=data.get("attaches_to"),
    )
