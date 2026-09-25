"""Plan — issue 63, part 63.4.

From a ``ParsedTimeline``, the ordered sequence of nodes for one timeline, each
with its timing reference. Pure: no builder, no USDM objects.

Issue 63 keeps today's behaviour: a straight chain, one activity-instance node
per column, every node timed from ONE anchor. Delays, decisions (the cycle
loop) and exits other than the last node come with rules R4 and R5
(``docs/timeline_assembler_design.md`` § 6).
"""

from dataclasses import dataclass

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.assembler.timeline.columns import Column, ParsedTimeline

BEFORE = "Before"
FIXED = "Fixed Reference"
AFTER = "After"

_DAY_UNITS = ("day",)


@dataclass
class InstanceNode:
    """One scheduled activity instance and how it is timed.

    ``relative_to`` is the column index it is measured from; ``duration`` and
    ``unit`` give the distance, always non-negative."""

    column: Column
    timing_type: str
    relative_to: int
    duration: int
    unit: str


@dataclass
class TimelinePlan:
    anchor: int
    nodes: list[InstanceNode]


class Planner:
    MODULE = "usdm4.assembler.timeline.plan.Planner"

    def __init__(self, errors: Errors):
        self._errors = errors

    def plan(self, timeline: ParsedTimeline) -> TimelinePlan:
        columns = timeline.columns
        anchor = self.find_anchor(columns)
        nodes = []
        for column in columns:
            if column.index < anchor:
                timing_type = BEFORE
            elif column.index == anchor:
                timing_type = FIXED
            else:
                timing_type = AFTER
            nodes.append(
                InstanceNode(
                    column=column,
                    timing_type=timing_type,
                    relative_to=anchor,
                    duration=self.interval_from_anchor(columns, column.index, anchor),
                    unit=column.timing.unit if column.timing else "day",
                )
            )
        return TimelinePlan(anchor=anchor, nodes=nodes)

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
    def find_anchor(cls, columns: list[Column]) -> int:
        """Position of the anchor: the first real (non-blank) column with a
        value >= 0 — Day 0 or Day 1 in a typical SoA. Else the first column."""
        for column in columns:
            if cls.is_placeholder(column):
                continue
            value = cls._value(column)
            if value is not None and value >= 0:
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
        day. Falls back to the absolute value when either value is missing or
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
