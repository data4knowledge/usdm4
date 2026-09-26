"""The parsed header values the plan and build work on — issue 73 (U4-35).

The caller hands every value over structured (``schedule_timeline_schema``);
parse (``columns.py``) copies it into these. Units are held singular
(``day``). ``render_*`` give a value's label when the caller sent no printed
text (U4-35: the label is the text, else rendered from the structure), in the
form the retired pattern grammar used, so labels do not move.
"""

from dataclasses import dataclass


def singular(unit: str) -> str:
    """``days`` → ``day``: the schema's plural unit, as held here."""
    return unit.removesuffix("s")


@dataclass(frozen=True)
class TimingPoint:
    """A timing point, ``Day -7`` → ``TimingPoint(unit="day", value=-7)``."""

    unit: str
    value: int


@dataclass(frozen=True)
class Window:
    """A window, ``±3 days`` → ``Window(lower=3, upper=3, unit="day")``.

    ``lower`` and ``upper`` are distances from the scheduled time, both
    non-negative: ``lower`` before it, ``upper`` after it.
    """

    lower: int
    upper: int
    unit: str


@dataclass(frozen=True)
class TimeRange:
    """A time range, ``Day -28 to Day -1`` →
    ``TimeRange(unit="day", start=-28, end=-1)``: the visit falls anywhere in
    the span. Stored in USDM as a timing at its start and a window forward to
    its end (U4-4, U4-20, U4-35)."""

    unit: str
    start: int
    end: int


@dataclass(frozen=True)
class CycleNumber:
    """A single cycle, ``Cycle 2`` → ``CycleNumber(n=2)`` (issue 66). In its
    columns the timing is the day within the cycle."""

    n: int


@dataclass(frozen=True)
class CycleRange:
    """A cycle range, ``Cycle 3-6`` → ``CycleRange(start=3, end=6)``,
    ``Cycle 3+`` → ``CycleRange(start=3, end=None)`` (open-ended). Planned by
    R5 (U4-25)."""

    start: int
    end: int | None


@dataclass(frozen=True)
class CycleLength:
    """A cycle length, ``21 days`` → ``CycleLength(n=21, unit="day")``."""

    n: int
    unit: str


@dataclass(frozen=True)
class Delay:
    """A variable delay (R8, U4-10), ``Washout 2-10 days`` →
    ``Delay(min=2, max=10, unit="day")``. Carried; built by R8."""

    min: int
    max: int | None
    unit: str


def render_timing(point: TimingPoint) -> str:
    return f"{point.unit.capitalize()} {point.value}"


def render_time_range(time_range: TimeRange) -> str:
    unit = time_range.unit.capitalize()
    return f"{unit} {time_range.start} to {unit} {time_range.end}"


def render_window(window: Window) -> str:
    return f"-{window.lower}..+{window.upper} {window.unit}s"


def render_cycle(cycle: CycleNumber | CycleRange) -> str:
    if isinstance(cycle, CycleNumber):
        return f"Cycle {cycle.n}"
    if cycle.end is None:
        return f"Cycle {cycle.start}+"
    return f"Cycle {cycle.start}-{cycle.end}"


def render_cycle_length(length: CycleLength) -> str:
    return f"{length.n} {length.unit}s"


def render_delay(delay: Delay) -> str:
    if delay.max is None:
        return f"{delay.min}+ {delay.unit}s"
    return f"{delay.min} to {delay.max} {delay.unit}s"
