"""The pattern grammar for schedule header values — issue 63, part 63.2.

A caller hands the timeline assembler every header value twice: the text as
printed (for labels) and its *pattern form* (for parsing). This module reads
the pattern form. It is strict on purpose: one way to write each thing, and a
value outside the grammar is refused with ``PatternError`` — never guessed at.
Turning printed text into a pattern is the caller's job.

Specified in ``docs/timeline_assembler_design.md`` § 4. Covered here: timing
points, windows, and the free-text labels used for epochs and visits. Timing
spans and cycles are added with rule R4.

Rules common to every pattern:

- surrounding whitespace is trimmed; inside, parts are separated by exactly
  one space;
- keywords (``Day``, ``days`` …) are matched ignoring case;
- ASCII only — digits are ``0``-``9``, the sign is ``-`` (a window is written
  ``-3..+3 days``, never with ``±``).

A redacted value — the sponsor printed ``CCI`` in place of it — has the
pattern ``CCI`` in every field (issue 64). It is a statement that the value
exists and was withheld, which is not the same as ``pattern: null`` (the
value is there but the grammar cannot express it). ``is_redacted`` tests for
it; the parse functions below never see it.
"""

import re
from dataclasses import dataclass

UNITS = ("day", "week", "month", "year", "hour", "minute")

REDACTED = "CCI"

_UNIT_KEYWORDS = "|".join(UNITS)
_UNIT_PLURALS = "|".join(f"{unit}s" for unit in UNITS)
_INT = r"0|[1-9][0-9]*"

_TIMING_POINT = re.compile(
    rf"^({_UNIT_KEYWORDS}) (0|-?[1-9][0-9]*)$", re.IGNORECASE | re.ASCII
)
_WINDOW = re.compile(
    rf"^-({_INT})\.\.\+({_INT}) ({_UNIT_PLURALS})$", re.IGNORECASE | re.ASCII
)


class PatternError(ValueError):
    """A value is not in the pattern grammar.

    Carries what was being parsed (``kind``) and the value as given, so the
    caller can report the timeline, column and field it came from.
    """

    def __init__(self, kind: str, value, expected: str):
        self.kind = kind
        self.value = value
        self.expected = expected
        super().__init__(f"{kind} pattern {value!r} is not valid; expected {expected}")


@dataclass(frozen=True)
class TimingPoint:
    """A timing point, ``Day -7`` → ``TimingPoint(unit="day", value=-7)``."""

    unit: str
    value: int


@dataclass(frozen=True)
class Window:
    """A window, ``-3..+3 days`` → ``Window(lower=3, upper=3, unit="day")``.

    ``lower`` and ``upper`` are distances from the scheduled time, both
    non-negative: ``lower`` before it, ``upper`` after it.
    """

    lower: int
    upper: int
    unit: str


_TIMING_EXPECTED = "'<Unit> <int>', Unit one of " + ", ".join(
    unit.capitalize() for unit in UNITS
)
_WINDOW_EXPECTED = "'-<int>..+<int> <units>', units one of " + ", ".join(
    f"{unit}s" for unit in UNITS
)


def _text(kind: str, value, expected: str) -> str:
    if not isinstance(value, str):
        raise PatternError(kind, value, expected)
    return value.strip()


def is_redacted(value) -> bool:
    """True when a pattern is the redaction ``CCI`` (any case, trimmed).
    Valid in every field."""
    return isinstance(value, str) and value.strip().upper() == REDACTED


def parse_timing(value: str) -> TimingPoint:
    """Parse a timing point: ``Day 1``, ``Day -7``, ``Week 12``, ``Hour 4``."""
    text = _text("timing", value, _TIMING_EXPECTED)
    match = _TIMING_POINT.match(text)
    if not match:
        raise PatternError("timing", value, _TIMING_EXPECTED)
    return TimingPoint(unit=match.group(1).lower(), value=int(match.group(2)))


def parse_window(value: str) -> Window:
    """Parse a window: ``-3..+3 days``, ``-0..+2 hours``, ``-7..+0 days``."""
    text = _text("window", value, _WINDOW_EXPECTED)
    match = _WINDOW.match(text)
    if not match:
        raise PatternError("window", value, _WINDOW_EXPECTED)
    return Window(
        lower=int(match.group(1)),
        upper=int(match.group(2)),
        unit=match.group(3).lower()[:-1],
    )


def parse_label(value: str, kind: str = "label") -> str:
    """An epoch or visit label: free text, trimmed, never empty.

    ``kind`` names the field in the error (``epoch``, ``visit``).
    """
    expected = "non-empty text"
    text = _text(kind, value, expected)
    if not text:
        raise PatternError(kind, value, expected)
    return text
