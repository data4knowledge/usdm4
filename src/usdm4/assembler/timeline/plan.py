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
- **Time ranges (U4-4, U4-20)** are timed at their start with a window forward to
  their end; crossing zero loses a day when the protocol has no Day 0.
- **Day 0 (U4-35)** comes from the timeline's ``day_zero`` flag, never from the
  columns; a ``Day 0`` timing when the flag says Day 1 is warned and the flag
  is used. ``≤N`` and windows printed in the timing cell are the caller's to
  structure (issue 73).

Issue 66 (design § 6 R4.3, U4-23–U4-26), issue 67 (U4-22, U4-27). In a
single-cycle column (``Cycle n``) the timing is the day within the cycle
(U4-26: from the timing field only). Every cycle has a ``Day 1`` node: its
printed ``Day 1`` column, else a start marker — an instance node with no
column, placed before the cycle's first column, which becomes a
``ScheduledActivityInstance`` with no encounter and no activities (U4-22).
Cycle *n*'s ``Day 1`` is timed from cycle *n* − 1's ``Day 1`` by cycle
*n* − 1's length — a chain (U4-27); Cycle 1's ``Day 1`` is Day 1 of the
timeline, timed from the anchor, and when the anchor falls on a Cycle 1
column with no printed ``Day 1`` the marker is the anchor. Every other
column of a cycle is timed from its cycle's ``Day 1``. A cycle's length is
its own columns' (the first readable one), converted to the cycle's unit
only where exact. A ``Day 1`` whose previous cycle is not in the timeline, or
has no readable or convertible length (U4-23), gets a zero timing and a
warning. A negative day in a cycle follows the crossing-zero rule (U4-24).

Issue 69 (R5, design § 6 R5, U4-7, U4-8). A cycle range (``Cycle n-m``,
``Cycle n+``) is timed like a single cycle numbered ``n``: its ``Day 1`` from
the previous cycle's ``Day 1`` — a range covering cycle *n* − 1 counts — and
its other days from its own ``Day 1``. A range with no readable length takes
the largest day printed in it, with a warning (U4-8). After the range's last
column come a decision node — timed ``After`` that column by the rest of the
cycle, looping back to the range's ``Day 1`` — and, when the range is the
last column, an end node (a decision cannot target the timeline exit).
"""

from dataclasses import dataclass

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.assembler.timeline.columns import Column, ParsedTimeline
from usdm4.assembler.timeline.values import (
    CycleLength,
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

# The units a cycle can be counted in from a first value of 1: ``Day 1`` and
# ``Week 1`` both mark the start of a cycle.
_START_UNITS = ("day", "week")

# Exact conversions only: (from, to) -> factor. Months and years have none.
_EXACT = {
    ("week", "day"): 7,
    ("week", "hour"): 7 * 24,
    ("week", "minute"): 7 * 24 * 60,
    ("day", "hour"): 24,
    ("day", "minute"): 24 * 60,
    ("hour", "minute"): 60,
}


def _cycle_n(cycle) -> int | None:
    """A cycle's number — a range's first cycle — or ``None``."""
    if isinstance(cycle, CycleNumber):
        return cycle.n
    if isinstance(cycle, CycleRange):
        return cycle.start
    return None


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
    """A cycle column the plan can time: its cycle number (a range's first
    cycle), the day within the cycle and, for a range, the range."""

    n: int
    day: TimingPoint
    range: CycleRange | None = None


@dataclass
class _CycleStart:
    """Cycle ``n``'s ``Day 1`` node. ``column`` is the index of its printed
    ``Day 1`` column, else ``None`` for a start marker. ``key`` is the node's
    key: the column index, or ``C{n}D1`` for a marker. ``first`` is the index
    of the cycle's first column — where a marker is placed and whose epoch it
    takes. ``unit`` is the cycle's timing unit."""

    n: int
    key: int | str
    first: int
    unit: str
    column: int | None = None
    range: CycleRange | None = None

    def covers(self, n: int) -> bool:
        """True when cycle ``n`` is this cycle, or inside this range."""
        if self.range is None:
            return self.n == n
        return self.range.start <= n and (self.range.end is None or n <= self.range.end)


DECISION = "decision"
END = "end"


@dataclass
class InstanceNode:
    """One scheduled activity instance and how it is timed.

    ``relative_to`` is the key of the node it is measured from: a column
    index, or a start marker's key (``C2D1``). ``duration`` and ``unit`` give
    the distance, always non-negative. ``window`` is the node's window, from
    the window field or a time range's span (``window_from`` says which:
    ``"window"``, ``"range"``).
    ``timed`` is False for a node with no readable timing (U4-3).

    A cycle's start marker (U4-22) has no ``column``: ``marker`` is its key,
    ``cycle`` its cycle number and ``epoch_column`` the column whose epoch it
    takes.

    A range's decision and end nodes (R5) have no column either; ``kind`` is
    ``DECISION`` or ``END``. A decision's ``loop_to`` is the key of the
    range's ``Day 1`` node, its default; its exit is the next node."""

    column: Column | None
    timing_type: str
    relative_to: int | str
    duration: int
    unit: str
    window: Window | None = None
    window_from: str | None = None
    timed: bool = True
    marker: str | None = None
    cycle: int | None = None
    epoch_column: int | None = None
    kind: str | None = None
    loop_to: int | str | None = None

    @property
    def key(self) -> int | str:
        return self.marker if self.marker is not None else self.column.index


@dataclass
class TimelinePlan:
    anchor: int | str
    nodes: list[InstanceNode]


@dataclass
class _Context:
    """What planning one timeline's nodes needs. ``anchor`` is the anchor
    node's key; ``anchor_position`` its place in the column order (a
    marker's is its cycle's first column); ``anchor_point`` its timing."""

    columns: list[Column]
    slots: dict[int, _CycleSlot]
    starts: dict[int, _CycleStart]
    lengths: dict
    has_zero: bool
    where: str
    anchor: int | str
    anchor_position: int
    anchor_point: TimingPoint | None


class Planner:
    MODULE = "usdm4.assembler.timeline.plan.Planner"

    def __init__(self, errors: Errors):
        self._errors = errors

    def _warn(self, message: str, method: str) -> None:
        self._errors.warning(message, KlassMethodLocation(self.MODULE, method))

    def plan(self, timeline: ParsedTimeline, t: int | None = None) -> TimelinePlan:
        where = f"Timeline {t}" if t else "Timeline"
        columns = timeline.columns
        slots, lengths = self._resolve_cycles(columns, where)
        self._range_lengths(columns, slots, lengths, where)
        starts = self._cycle_starts(columns, slots, where)
        anchor_column = self.find_anchor(columns)
        if not any(self._is_candidate(c) for c in columns):
            self._warn(
                f"{where}: no column has a timing of 0 or more; the first column "
                "is the anchor",
                "plan",
            )
        self._warn_restarts(columns, where)
        has_zero = timeline.day_zero
        self._warn_day_zero(columns, has_zero, where)
        ctx = _Context(
            columns=columns,
            slots=slots,
            starts=starts,
            lengths=lengths,
            has_zero=has_zero,
            where=where,
            **self._anchor(columns, anchor_column, slots, starts),
        )
        markers = {s.first: s for s in starts.values() if s.column is None}
        nodes: list[InstanceNode] = []
        for column in columns:
            start = markers.get(column.index)
            if start is not None:
                previous = nodes[-1].key if nodes else None
                nodes.append(self._marker_node(ctx, start, previous))
            nodes.append(self._node(ctx, column, nodes[-1].key if nodes else None))
        return TimelinePlan(anchor=ctx.anchor, nodes=self._add_loops(ctx, nodes))

    # ------------------------------------------------------------------
    # Cycle ranges — issue 69 (R5)

    def _add_loops(
        self, ctx: "_Context", nodes: list[InstanceNode]
    ) -> list[InstanceNode]:
        """After each range's last column, its decision node; and when that
        column is the timeline's last, an end node after the decision."""
        last_of: dict[int, int] = {}
        for column in ctx.columns:
            slot = ctx.slots.get(column.index)
            if slot is not None and slot.range is not None:
                last_of[slot.n] = column.index
        if not last_of:
            return nodes
        result: list[InstanceNode] = []
        for node in nodes:
            result.append(node)
            if node.column is None:
                continue
            slot = ctx.slots.get(node.column.index)
            if slot is None or last_of.get(slot.n) != node.column.index:
                continue
            decision = self._decision_node(ctx, ctx.starts[slot.n], node.column)
            result.append(decision)
            if node is nodes[-1]:
                result.append(
                    InstanceNode(
                        column=None,
                        timing_type=AFTER,
                        relative_to=decision.key,
                        duration=0,
                        unit=decision.unit,
                        marker=f"C{slot.n}END",
                        cycle=slot.n,
                        epoch_column=node.column.index,
                        kind=END,
                    )
                )
        return result

    def _decision_node(
        self, ctx: "_Context", start: _CycleStart, last: Column
    ) -> InstanceNode:
        """The range's decision, ``After`` its last column by the rest of the
        cycle: the length less the last day's offset in the cycle (28 days,
        last day ``Day 15``: 14 days)."""
        what = f"cycle {start.n} decision"
        length = ctx.lengths.get(start.n)
        day = ctx.slots[last.index].day
        delay, timed = 0, False
        if length is None:
            reason = "the range has no readable length"
        else:
            converted = _convert(length.n, length.unit, start.unit)
            offset = self._collapse(day.value, day.unit, ctx.has_zero) - 1
            if converted is None:
                reason = (
                    f"the range's length {length.n} {length.unit}s does not "
                    f"convert exactly to {start.unit}s"
                )
            elif converted < offset:
                reason = (
                    f"the last day ({day.value}) is beyond the length "
                    f"({converted} {start.unit}s)"
                )
            else:
                delay, timed, reason = converted - offset, True, None
        if reason:
            self._warn(f"{ctx.where}, {what}: {reason}; a zero delay is used", "plan")
        return InstanceNode(
            column=None,
            timing_type=AFTER,
            relative_to=last.index,
            duration=delay,
            unit=start.unit,
            timed=timed,
            marker=f"C{start.n}DEC",
            cycle=start.n,
            epoch_column=last.index,
            kind=DECISION,
            # The pass starts at the range's first node: its start marker,
            # else its first column — a predose ``Day -1`` before ``Day 1``.
            loop_to=start.key if start.column is None else start.first,
        )

    def _range_lengths(
        self,
        columns: list[Column],
        slots: dict[int, _CycleSlot],
        lengths: dict,
        where: str,
    ) -> None:
        """U4-8: a range with no readable length takes the largest day
        printed in it (``Day 15`` → 15 days), with a warning."""
        largest: dict[int, TimingPoint] = {}
        for column in columns:
            slot = slots.get(column.index)
            if slot is None or slot.range is None or slot.n in lengths:
                continue
            best = largest.get(slot.n)
            if best is None or (
                slot.day.unit == best.unit and slot.day.value > best.value
            ):
                largest[slot.n] = slot.day
        for n, day in largest.items():
            if day.value < 1:
                continue
            lengths[n] = CycleLength(day.value, day.unit)
            self._warn(
                f"{where}, cycle {n}: the range has no readable length; the "
                f"largest day printed in it is used ({day.value} {day.unit}s)",
                "plan",
            )

    def _anchor(
        self,
        columns: list[Column],
        anchor_column: int,
        slots: dict[int, _CycleSlot],
        starts: dict[int, _CycleStart],
    ) -> dict:
        """The anchor's key, its place in the column order and its timing
        point. When the anchor falls on a column of a cycle that prints no
        ``Day 1``, the cycle's start marker is the anchor, at Day 1."""
        slot = slots.get(anchor_column)
        if slot is not None:
            start = starts[slot.n]
            if start.column is None:
                return {
                    "anchor": start.key,
                    "anchor_position": start.first,
                    "anchor_point": TimingPoint(start.unit, 1),
                }
        anchor_point = columns[anchor_column].timing if columns else None
        return {
            "anchor": anchor_column,
            "anchor_position": anchor_column,
            "anchor_point": anchor_point,
        }

    def _node(
        self, ctx: "_Context", column: Column, previous: int | str | None = None
    ) -> InstanceNode:
        window, window_from = column.window, column.window_from
        if window is None and column.time_range is not None:
            window, window_from = (
                self.range_window(column.time_range, ctx.has_zero),
                "range",
            )
        columns, anchor, where = ctx.columns, ctx.anchor, ctx.where
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
            if column.index < ctx.anchor_position:
                timing_type, relative_to = BEFORE, column.index + 1
            else:
                timing_type, relative_to = AFTER, column.index - 1
            return InstanceNode(
                column, timing_type, relative_to, 0, "day", window, window_from, False
            )
        elif column.index in ctx.slots:
            return self._cycle_node(ctx, column, window, window_from, previous)
        else:
            timing_type = BEFORE if column.index < ctx.anchor_position else AFTER
            relative_to = anchor
        if isinstance(anchor, int):
            duration = self.interval_from_anchor(
                columns, column.index, anchor, ctx.has_zero
            )
        else:
            duration = self._interval(
                column.timing, ctx, f"column '{column.id}'", column.timing_label
            )
        return InstanceNode(
            column=column,
            timing_type=timing_type,
            relative_to=relative_to,
            duration=duration,
            unit=column.timing.unit if column.timing else "day",
            window=window,
            window_from=window_from,
            timed=column.timing is not None,
        )

    def _interval(
        self,
        point: TimingPoint | None,
        ctx: "_Context",
        what: str,
        label: str | None = None,
    ) -> int:
        """Duration between a timing point and the anchor's, with the
        crossing-zero rule; the absolute value when the anchor has no timing
        or the units differ (warned)."""
        if point is None:
            return 0
        anchor_point = ctx.anchor_point
        if anchor_point is None:
            return abs(point.value)
        if point.unit != anchor_point.unit:
            self._warn(
                f"{ctx.where}, {what}: timing unit '{point.unit}' differs from "
                f"anchor unit '{anchor_point.unit}'; using {abs(point.value)}",
                "plan",
            )
            return abs(point.value)
        here = self._collapse(point.value, point.unit, ctx.has_zero)
        there = self._collapse(anchor_point.value, anchor_point.unit, ctx.has_zero)
        return abs(here - there)

    # ------------------------------------------------------------------
    # Cycles — issue 66, issue 67

    def _resolve_cycles(
        self, columns: list[Column], where: str
    ) -> tuple[dict[int, _CycleSlot], dict]:
        """Find every cycle column the plan can time (U4-26) — a single cycle
        or a range (R5), a range numbered by its first cycle — and each
        cycle's length."""
        lengths = self._cycle_lengths(columns, where)
        slots: dict[int, _CycleSlot] = {}
        for column in columns:
            cycle = column.cycle
            if cycle is None or column.timing is None:
                continue
            day = column.timing
            column.cycle_day = day
            if isinstance(cycle, CycleRange):
                slots[column.index] = _CycleSlot(cycle.start, day, cycle)
            else:
                slots[column.index] = _CycleSlot(cycle.n, day)
        return slots, lengths

    def _cycle_starts(
        self, columns: list[Column], slots: dict[int, _CycleSlot], where: str
    ) -> dict[int, _CycleStart]:
        """Each timed cycle's ``Day 1`` node (U4-22): its first printed
        ``Day 1`` (or ``Week 1``) column, else a start marker placed before
        the cycle's first column. A cycle none of whose columns has a
        readable day gets no node."""
        first: dict[int, int] = {}
        for column in columns:
            n = _cycle_n(column.cycle)
            if n is not None:
                first.setdefault(n, column.index)
        starts: dict[int, _CycleStart] = {}
        for column in columns:
            slot = slots.get(column.index)
            if slot is None:
                continue
            start = starts.get(slot.n)
            if start is None:
                start = _CycleStart(
                    n=slot.n,
                    key=f"C{slot.n}D1",
                    first=first[slot.n],
                    unit=slot.day.unit,
                    range=slot.range,
                )
                starts[slot.n] = start
            if (
                start.column is None
                and slot.day.value == 1
                and slot.day.unit in _START_UNITS
            ):
                start.column, start.key = column.index, column.index
        for start in starts.values():
            if start.column is None:
                self._errors.info(
                    f"{where}, cycle {start.n}: no Day 1 column is printed; a "
                    f"start marker {start.key} is added",
                    KlassMethodLocation(self.MODULE, "plan"),
                )
        return starts

    def _cycle_lengths(self, columns: list[Column], where: str) -> dict:
        """Each cycle's length — a range's keyed by its first cycle: the first
        readable one among its own columns. A second, different length in the
        same cycle is warned."""
        lengths: dict[int, object] = {}
        for column in columns:
            n = _cycle_n(column.cycle)
            if n is None or not column.cycle_length:
                continue
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

    @staticmethod
    def _collapse(value: int, unit: str, has_zero: bool) -> int:
        """A day number on a line with no Day 0 when the table prints none:
        ``Day -1`` is one day before ``Day 1`` (crossing-zero rule, U4-24)."""
        if unit in _DAY_UNITS and value < 0 and not has_zero:
            return value + 1
        return value

    def _start_timing(
        self, ctx: "_Context", start: _CycleStart, previous: int | str | None
    ) -> tuple[str, int | str, int, str, bool]:
        """How cycle ``n``'s ``Day 1`` node is timed: (type, relative to,
        duration, unit, timed). The anchor is fixed. Cycle *n* > 1 is timed
        from cycle *n* − 1's ``Day 1`` by cycle *n* − 1's length (U4-27);
        when that cycle is not in the timeline, or its length cannot be read
        or converted exactly (U4-23), a zero timing after the previous node
        and a warning. Cycle 1 is Day 1 of the timeline, timed from the
        anchor."""
        what = f"cycle {start.n} Day 1"
        if start.key == ctx.anchor:
            return FIXED, ctx.anchor, 0, start.unit, True
        if start.n > 1:
            before = next(
                (s for s in ctx.starts.values() if s.covers(start.n - 1)), None
            )
            length = ctx.lengths.get(before.n) if before is not None else None
            reason = None
            if before is None:
                reason = f"cycle {start.n - 1} is not in the timeline"
            elif length is None:
                reason = f"cycle {start.n - 1} has no readable length"
            else:
                converted = _convert(length.n, length.unit, start.unit)
                if converted is None:
                    reason = (
                        f"cycle {start.n - 1}'s length {length.n} {length.unit}s "
                        f"does not convert exactly to {start.unit}s"
                    )
                else:
                    return AFTER, before.key, converted, start.unit, True
            self._warn(f"{ctx.where}, {what}: {reason}; a zero timing is used", "plan")
            if previous is None:
                return BEFORE, ctx.anchor, 0, start.unit, False
            return AFTER, previous, 0, start.unit, False
        timing_type = BEFORE if start.first < ctx.anchor_position else AFTER
        duration = self._interval(TimingPoint(start.unit, 1), ctx, what)
        return timing_type, ctx.anchor, duration, start.unit, True

    def _marker_node(
        self, ctx: "_Context", start: _CycleStart, previous: int | str | None
    ) -> InstanceNode:
        """A cycle's start marker (U4-22): its ``Day 1`` when none is
        printed. Not a visit — no column, so no encounter and no cells."""
        timing_type, relative_to, duration, unit, timed = self._start_timing(
            ctx, start, previous
        )
        return InstanceNode(
            column=None,
            timing_type=timing_type,
            relative_to=relative_to,
            duration=duration,
            unit=unit,
            timed=timed,
            marker=start.key,
            cycle=start.n,
            epoch_column=start.first,
        )

    def _cycle_node(
        self,
        ctx: "_Context",
        column: Column,
        window: Window | None,
        window_from: str | None,
        previous: int | str | None,
    ) -> InstanceNode:
        """A single-cycle column: its cycle's ``Day 1`` is timed by the chain;
        any other column from its cycle's ``Day 1`` node."""
        slot = ctx.slots[column.index]
        start = ctx.starts[slot.n]
        if start.column == column.index:
            timing_type, relative_to, duration, unit, timed = self._start_timing(
                ctx, start, previous
            )
        else:
            unit = slot.day.unit
            here = self._collapse(slot.day.value, unit, ctx.has_zero)
            timing_type = AFTER if here >= 1 else BEFORE
            relative_to, duration, timed = start.key, abs(here - 1), True
        return InstanceNode(
            column=column,
            timing_type=timing_type,
            relative_to=relative_to,
            duration=duration,
            unit=unit,
            window=window,
            window_from=window_from,
            timed=timed,
        )

    def _warn_day_zero(self, columns: list[Column], has_zero: bool, where: str) -> None:
        """U4-35: a ``Day 0`` timing when the flag says the protocol numbers
        from Day 1 is warned; the flag is used."""
        if has_zero:
            return
        for column in columns:
            timing = column.timing
            if timing is not None and timing.unit in _DAY_UNITS and timing.value == 0:
                self._warn(
                    f"{where}, column '{column.id}': Day 0 printed but the "
                    "timeline numbers from Day 1 (day_zero false); the flag is used",
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
        """A column with no readable timing — e.g. an unlabelled
        ET/unscheduled column, or one sent as text only."""
        return column.timing is None

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

    def interval_from_anchor(
        self, columns: list[Column], index: int, anchor_index: int, has_zero: bool
    ) -> int:
        """Duration between a column and the anchor.

        USDM ``Timing.value`` is the interval relative to the referenced
        instance, NOT the protocol's day number: Day 16 relative to a Day 1
        anchor is 15 days. When day numbering is 1-based (``day_zero``
        false, U4-35), an interval crossing zero loses a day: Day -1 to Day 1 is 1
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
            and not has_zero
        ):
            delta -= 1
        return delta
