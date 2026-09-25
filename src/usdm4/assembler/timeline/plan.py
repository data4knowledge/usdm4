"""Plan — issue 63, part 63.4; issue 65 (R4, timing without cycles); issue 66
(R4 part 2, single cycles).

From a ``ParsedTimeline``, the ordered sequence of nodes for one timeline, each
with its timing reference. Pure: no builder, no USDM objects.

A straight chain, one activity-instance node per column. Issue 65 (design
§ 6 R4, decisions U4-2, U4-3, U4-4, U4-18, U4-20):

- **Anchor (U4-2).** The first column whose timing point is ≥ 0; if none, the
  first column, with a warning. A restart outside a cycle (a timing point
  lower than an earlier one, same unit, no cycle text) is warned (U4-14).
- **Timed columns** are measured from the anchor, with today's crossing-zero
  and mixed-unit rules.
- **Columns with no readable timing (U4-3)** get a zero duration: ``After`` the
  previous column, or ``Before`` the next when they precede the anchor, and a
  warning. So every instance is timed.
- **``≤N`` (U4-18)** is read as ``Day -N to Day -1`` only before the anchor;
  anywhere else it has no readable timing.
- **Time ranges (U4-4, U4-20)** are timed at their start with a window forward to
  their end; crossing zero loses a day when the table has no Day 0.

Issue 66 (design § 6 R4.3, U4-22–U4-26). In a single-cycle column (``Cycle
n``) the timing is the day within the cycle (U4-26: from the timing field
only). Cycle *n*'s ``Day 1`` sits (*n* − 1) × cycle *n*'s length after Cycle
1's ``Day 1``, and is timed from the anchor. Every other column of the cycle
is timed from its cycle's ``Day 1`` column — a chain — or, when the cycle
prints no ``Day 1`` column, from the anchor (U4-22). A cycle's length is its
own columns' (the first readable one); a length is converted to the day's
unit only where exact. Cycle *n* > 1 with no readable or convertible length
(U4-23), and a cycle-range column (U4-25, ranges come with R5), get a zero
timing and a warning. A negative day in a cycle follows the crossing-zero
rule (U4-24).

Delays, decisions (the cycle loop) and other exits come with later issues.
"""

from dataclasses import dataclass

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.assembler.timeline.columns import Column, ParsedTimeline
from usdm4.assembler.timeline.grammar import (
    CycleNumber,
    CycleRange,
    TimeRange,
    TimingPoint,
    Window,
)

BEFORE = "Before"
FIXED = "Fixed Reference"
AFTER = "After"

_DAY_UNITS = ("day",)

# Exact conversions only: (from, to) -> factor. Months and years have none.
_EXACT = {
    ("week", "day"): 7,
    ("week", "hour"): 7 * 24,
    ("week", "minute"): 7 * 24 * 60,
    ("day", "hour"): 24,
    ("day", "minute"): 24 * 60,
    ("hour", "minute"): 60,
}


def _convert(n: int, unit: str, to: str) -> int | None:
    """``n`` ``unit`` in ``to`` units, or ``None`` when not exact."""
    if unit == to:
        return n
    factor = _EXACT.get((unit, to))
    if factor is not None:
        return n * factor
    factor = _EXACT.get((to, unit))
    if factor is not None and n % factor == 0:
        return n // factor
    return None


@dataclass
class _CycleSlot:
    """A single-cycle column the plan can time: its cycle number, the day
    within the cycle, and the offset of the cycle's ``Day 1`` from Cycle 1's
    ``Day 1`` in the day's unit."""

    n: int
    day: TimingPoint
    offset: int


@dataclass
class InstanceNode:
    """One scheduled activity instance and how it is timed.

    ``relative_to`` is the column index it is measured from; ``duration`` and
    ``unit`` give the distance, always non-negative. ``window`` is the node's
    window, from the window field, the timing cell, or a decoded time range
    (``window_from`` says which: ``"window"``, ``"timing"``, ``"range"``).
    ``timed`` is False for a column with no readable timing (U4-3)."""

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
        slots = self._resolve_cycles(columns, where)
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
        nodes = [
            self._node(columns, c, anchor, has_zero, where, slots) for c in columns
        ]
        return TimelinePlan(anchor=anchor, nodes=nodes)

    def _node(
        self,
        columns: list[Column],
        column: Column,
        anchor: int,
        has_zero: bool,
        where: str,
        slots: dict[int, "_CycleSlot"] | None = None,
    ) -> InstanceNode:
        slots = slots or {}
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
            # U4-3: no readable timing — zero from the neighbour toward the anchor.
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
        elif column.index in slots:
            return self._cycle_node(
                columns, column, anchor, has_zero, slots, window, window_from, where
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

    # ------------------------------------------------------------------
    # Cycles — issue 66

    def _resolve_cycles(
        self, columns: list[Column], where: str
    ) -> dict[int, _CycleSlot]:
        """Place every single-cycle column (U4-22–U4-26). Columns that cannot
        be timed — a cycle range (U4-25), a cycle with no usable length
        (U4-23) — lose their timing (kept as ``cycle_day``) and so take the
        zero timing of U4-3."""
        lengths = self._cycle_lengths(columns, where)
        slots: dict[int, _CycleSlot] = {}
        for column in columns:
            cycle = column.cycle
            if cycle is None or column.timing is None:
                continue
            day = column.timing
            if isinstance(cycle, CycleRange):
                column.cycle_day, column.timing, column.time_range = day, None, None
                self._warn(
                    f"{where}, column '{column.id}': cycle ranges are timed with "
                    "R5; a zero timing is used",
                    "plan",
                )
                continue
            offset = self._cycle_offset(cycle, day, lengths, column, where)
            column.cycle_day = day
            if offset is None:
                column.timing, column.time_range = None, None
                continue
            slots[column.index] = _CycleSlot(cycle.n, day, offset)
        return slots

    def _cycle_lengths(self, columns: list[Column], where: str) -> dict:
        """Each single cycle's length: the first readable one among its own
        columns. A second, different length in the same cycle is warned."""
        lengths: dict[int, object] = {}
        for column in columns:
            if not isinstance(column.cycle, CycleNumber) or not column.cycle_length:
                continue
            n = column.cycle.n
            if n not in lengths:
                lengths[n] = column.cycle_length
            elif column.cycle_length != lengths[n]:
                self._warn(
                    f"{where}, column '{column.id}': cycle {n} prints a second "
                    f"length ({column.cycle_length.n} {column.cycle_length.unit}s); "
                    "the first is used",
                    "plan",
                )
        return lengths

    def _cycle_offset(
        self,
        cycle: CycleNumber,
        day: TimingPoint,
        lengths: dict,
        column: Column,
        where: str,
    ) -> int | None:
        """Cycle *n*'s ``Day 1`` from Cycle 1's, in the day's unit:
        (*n* − 1) × cycle *n*'s length. ``None`` (with a warning) when cycle
        *n* > 1 has no length, or one that does not convert exactly."""
        if cycle.n == 1:
            return 0
        length = lengths.get(cycle.n)
        if length is None:
            self._warn(
                f"{where}, column '{column.id}': cycle {cycle.n} has no readable "
                "length; a zero timing is used",
                "plan",
            )
            return None
        converted = _convert(length.n, length.unit, day.unit)
        if converted is None:
            self._warn(
                f"{where}, column '{column.id}': cycle length {length.n} "
                f"{length.unit}s does not convert exactly to {day.unit}s; a zero "
                "timing is used",
                "plan",
            )
            return None
        return (cycle.n - 1) * converted

    @staticmethod
    def _collapse(value: int, unit: str, has_zero: bool) -> int:
        """A day number on a line with no Day 0 when the table prints none:
        ``Day -1`` is one day before ``Day 1`` (crossing-zero rule, U4-24)."""
        if unit in _DAY_UNITS and value < 0 and not has_zero:
            return value + 1
        return value

    def _position(
        self, column: Column, slots: dict[int, _CycleSlot], has_zero: bool
    ) -> int:
        """A column's place on the timeline's own line, in its timing unit:
        for a cycle column the cycle's offset plus the day within it."""
        slot = slots.get(column.index)
        if slot is not None:
            return slot.offset + self._collapse(slot.day.value, slot.day.unit, has_zero)
        return self._collapse(column.timing.value, column.timing.unit, has_zero)

    @staticmethod
    def _day_one(
        columns: list[Column], slot: _CycleSlot, slots: dict[int, _CycleSlot]
    ) -> int | None:
        """The index of the first ``Day 1`` column of the slot's cycle."""
        for column in columns:
            other = slots.get(column.index)
            if (
                other is not None
                and other.n == slot.n
                and other.day.unit in _DAY_UNITS
                and other.day.value == 1
            ):
                return column.index
        return None

    def _cycle_node(
        self,
        columns: list[Column],
        column: Column,
        anchor: int,
        has_zero: bool,
        slots: dict[int, _CycleSlot],
        window: Window | None,
        window_from: str | None,
        where: str,
    ) -> InstanceNode:
        """A single-cycle column: from its cycle's ``Day 1`` column, else from
        the anchor (U4-22)."""
        slot = slots[column.index]
        unit = slot.day.unit
        day_one = self._day_one(columns, slot, slots)
        if day_one is not None and day_one != column.index:
            relative_to = day_one
            here = self._collapse(slot.day.value, unit, has_zero)
            duration = abs(here - 1)
            timing_type = AFTER if here >= 1 else BEFORE
        else:
            relative_to = anchor
            anchor_column = columns[anchor]
            here = self._position(column, slots, has_zero)
            if anchor_column.timing is None:
                duration = abs(here)
            elif anchor_column.timing.unit != unit:
                self._warn(
                    f"{where}, column '{column.id}': timing unit '{unit}' differs "
                    f"from anchor unit '{anchor_column.timing.unit}'; using "
                    f"{abs(here)}",
                    "plan",
                )
                duration = abs(here)
            else:
                duration = abs(here - self._position(anchor_column, slots, has_zero))
            timing_type = BEFORE if column.index < anchor else AFTER
        return InstanceNode(
            column=column,
            timing_type=timing_type,
            relative_to=relative_to,
            duration=duration,
            unit=unit,
            window=window,
            window_from=window_from,
            timed=True,
        )

    def _resolve_up_to(self, columns: list[Column], anchor: int, where: str) -> None:
        """U4-18: ``≤N`` before the anchor is ``Day -N to Day -1``; elsewhere it
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
        """U4-14: a timing lower than an earlier one in the same unit, outside a
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
        """The window forward from a time range's start to its end (U4-4, U4-20)."""
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
