"""Plan — issue 63, part 63.4; issue 65 (R4, timing without cycles).

From a ``ParsedTimeline``, the ordered sequence of nodes for one timeline, each
with its timing reference. Pure: no builder, no USDM objects.

A straight chain, one activity-instance node per column. Issue 65 (design
§ 6 R4, decisions D2, D3, D4, D18, D20):

- **Anchor (D2).** The first column whose timing point is ≥ 0; if none, the
  first column, with a warning. A restart outside a cycle (a timing point
  lower than an earlier one, same unit, no cycle text) is warned (D14).
- **Timed columns** are measured from the anchor, with today's crossing-zero
  and mixed-unit rules.
- **Columns with no readable timing (D3)** get a zero duration: ``After`` the
  previous column, or ``Before`` the next when they precede the anchor, and a
  warning. So every instance is timed.
- **``≤N`` (D18)** is read as ``Day -N to Day -1`` only before the anchor;
  anywhere else it has no readable timing.
- **Time ranges (D4, D20)** are timed at their start with a window forward to
  their end; crossing zero loses a day when the table has no Day 0.

Delays, decisions (the cycle loop) and other exits come with later issues.
"""

from dataclasses import dataclass

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.assembler.timeline.columns import Column, ParsedTimeline
from usdm4.assembler.timeline.grammar import TimeRange, TimingPoint, Window

BEFORE = "Before"
FIXED = "Fixed Reference"
AFTER = "After"

_DAY_UNITS = ("day",)


@dataclass
class InstanceNode:
    """One scheduled activity instance and how it is timed.

    ``relative_to`` is the column index it is measured from; ``duration`` and
    ``unit`` give the distance, always non-negative. ``window`` is the node's
    window, from the window field, the timing cell, or a decoded time range
    (``window_from`` says which: ``"window"``, ``"timing"``, ``"range"``).
    ``timed`` is False for a column with no readable timing (D3)."""

    column: Column
    timing_type: str
    relative_to: int
    duration: int
    unit: str
    window: Window | None = None
    window_from: str | None = None
    timed: bool = True


@dataclass
class TimelinePlan:
    anchor: int
    nodes: list[InstanceNode]


class Planner:
    MODULE = "usdm4.assembler.timeline.plan.Planner"

    def __init__(self, errors: Errors):
        self._errors = errors

    def _warn(self, message: str, method: str) -> None:
        self._errors.warning(message, KlassMethodLocation(self.MODULE, method))

    def plan(self, timeline: ParsedTimeline, t: int | None = None) -> TimelinePlan:
        where = f"Timeline {t}" if t else "Timeline"
        columns = timeline.columns
        anchor = self.find_anchor(columns)
        if not any(self._is_candidate(c) for c in columns):
            self._warn(
                f"{where}: no column has a timing of 0 or more; the first column "
                "is the anchor",
                "plan",
            )
        self._resolve_up_to(columns, anchor, where)
        self._warn_restarts(columns, where)
        has_zero = self.has_zero_timepoint(columns)
        nodes = [self._node(columns, c, anchor, has_zero, where) for c in columns]
        return TimelinePlan(anchor=anchor, nodes=nodes)

    def _node(
        self,
        columns: list[Column],
        column: Column,
        anchor: int,
        has_zero: bool,
        where: str,
    ) -> InstanceNode:
        window, window_from = column.window, column.window_from
        if window is None and column.time_range is not None:
            window, window_from = (
                self.range_window(column.time_range, has_zero),
                "range",
            )
        if column.index == anchor:
            timing_type, relative_to = FIXED, anchor
            if column.timing is None:
                self._warn(
                    f"{where}, column '{column.id}': no readable timing; the "
                    "anchor is a zero timing",
                    "plan",
                )
        elif column.timing is None:
            # D3: no readable timing — zero from the neighbour toward the anchor.
            self._warn(
                f"{where}, column '{column.id}': no readable timing; a zero "
                "timing is used",
                "plan",
            )
            if column.index < anchor:
                timing_type, relative_to = BEFORE, column.index + 1
            else:
                timing_type, relative_to = AFTER, column.index - 1
            return InstanceNode(
                column, timing_type, relative_to, 0, "day", window, window_from, False
            )
        else:
            timing_type = BEFORE if column.index < anchor else AFTER
            relative_to = anchor
        return InstanceNode(
            column=column,
            timing_type=timing_type,
            relative_to=relative_to,
            duration=self.interval_from_anchor(columns, column.index, anchor),
            unit=column.timing.unit if column.timing else "day",
            window=window,
            window_from=window_from,
            timed=column.timing is not None,
        )

    def _resolve_up_to(self, columns: list[Column], anchor: int, where: str) -> None:
        """D18: ``≤N`` before the anchor is ``Day -N to Day -1``; elsewhere it
        is not read."""
        for column in columns:
            up_to = column.up_to
            if up_to is None:
                continue
            if column.index < anchor:
                column.time_range = TimeRange(up_to.unit, -up_to.n, -1)
                column.timing = TimingPoint(up_to.unit, -up_to.n)
            else:
                self._warn(
                    f"{where}, column '{column.id}', timing: '≤{up_to.n}' is read "
                    "only before the anchor",
                    "plan",
                )

    def _warn_restarts(self, columns: list[Column], where: str) -> None:
        """D14: a timing lower than an earlier one in the same unit, outside a
        cycle, is two periods and should be two timelines."""
        highest: dict[str, int] = {}
        for column in columns:
            if column.timing is None or column.cycle_label:
                continue
            unit, value = column.timing.unit, column.timing.value
            if unit in highest and value < highest[unit]:
                self._warn(
                    f"{where}, column '{column.id}': timing restarts "
                    f"({unit} {value} after {unit} {highest[unit]}); this may be "
                    "two periods that should be two timelines",
                    "plan",
                )
            highest[unit] = max(value, highest.get(unit, value))

    @staticmethod
    def range_window(time_range: TimeRange, has_zero: bool) -> Window:
        """The window forward from a time range's start to its end (D4, D20)."""
        length = time_range.end - time_range.start
        if (
            time_range.unit in _DAY_UNITS
            and time_range.start < 0 < time_range.end
            and not has_zero
        ):
            length -= 1
        return Window(lower=0, upper=length, unit=time_range.unit)

    @staticmethod
    def _value(column: Column) -> int | None:
        return column.timing.value if column.timing else None

    @classmethod
    def is_placeholder(cls, column: Column) -> bool:
        """A blank SoA column: no timing text and no (or zero) value. These
        carry no timing information — e.g. an unlabelled ET/unscheduled
        column."""
        return not (column.timing_label or "").strip() and not cls._value(column)

    @classmethod
    def _is_candidate(cls, column: Column) -> bool:
        if cls.is_placeholder(column):
            return False
        value = cls._value(column)
        return value is not None and value >= 0

    @classmethod
    def find_anchor(cls, columns: list[Column]) -> int:
        """Position of the anchor: the first real (non-blank) column with a
        value >= 0 — Day 0 or Day 1 in a typical SoA. Else the first column."""
        for column in columns:
            if cls._is_candidate(column):
                return column.index
        return 0

    @classmethod
    def has_zero_timepoint(cls, columns: list[Column]) -> bool:
        """True if the table numbers days from zero (an explicit Day 0 column
        exists), in which case no crossing-zero correction applies."""
        for column in columns:
            if cls.is_placeholder(column):
                continue
            if cls._value(column) == 0:
                return True
        return False

    def interval_from_anchor(
        self, columns: list[Column], index: int, anchor_index: int
    ) -> int:
        """Duration between a column and the anchor.

        USDM ``Timing.value`` is the interval relative to the referenced
        instance, NOT the protocol's day number: Day 16 relative to a Day 1
        anchor is 15 days. When day numbering is 1-based (no Day 0 in the
        table), an interval crossing zero loses a day: Day -1 to Day 1 is 1
        day. Falls back to the absolute value when the anchor has no value or
        the units differ."""
        column = columns[index]
        anchor = columns[anchor_index]
        value = self._value(column)
        anchor_value = self._value(anchor)
        if value is None:
            return 0
        if anchor_value is None:
            return abs(value)
        unit = column.timing.unit
        anchor_unit = anchor.timing.unit
        if unit != anchor_unit:
            self._errors.warning(
                f"Timing unit '{unit}' differs from anchor unit '{anchor_unit}'; "
                f"using absolute value {abs(value)} for '{column.timing_label}'",
                KlassMethodLocation(self.MODULE, "interval_from_anchor"),
            )
            return abs(value)
        delta = abs(value - anchor_value)
        if (
            unit in _DAY_UNITS
            and (value < 0 < anchor_value or anchor_value < 0 < value)
            and not self.has_zero_timepoint(columns)
        ):
            delta -= 1
        return delta
