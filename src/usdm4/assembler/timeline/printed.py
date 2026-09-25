"""The printed-text reader — issue 65.

A caller may hand a header value over as printed text only, as a pattern
only, or both; with both the pattern is used (design § 3.2). This module
reads the printed text when there is no usable pattern. It returns the same
typed values the pattern grammar does (``TimingPoint``, ``TimeRange``,
``Window``), plus ``UpTo`` for a printed ``≤N``, which only the plan can place
(U4-18). It returns ``None`` for text it cannot read; it never guesses a number.

Pure functions, no errors object: the caller (``columns.py``) raises the
warnings (U4-16), using the flags returned here.

Forms read — timing:

- a point with a unit word: ``D8``, ``Day 8``, ``Wk 12``, ``Week 12``,
  ``Month 6``, ``Hour 4``, ``2 hr``, ``30 min``;
- a bare number (``15``, ``-7``): unit from the timing row label, else days
  with ``unit_defaulted`` set (U4-15);
- a time range: ``-28 to -1``, ``Days -14 to -1``, ``3-5``, ``Between Day 2
  and Day 4``, ``Day -28 to Day -1``;
- ``≤N`` (``<=N``): an ``UpTo`` for the plan (U4-18);
- a point that prints its own window: ``15 ± 3``, ``30 (±3)``,
  ``Day 8 ±3 days`` (U4-16).

Forms read — window: ``±3``, ``(±3 days)``, ``±15 min``, ``±1 hr``, ``+/-3``,
``-1/+2 days``, and the pattern form ``-3..+3 days``. A window with no unit
takes the window row label's unit, else the timing's unit, else days with
``unit_defaulted`` set (U4-19).

Text is normalised first: the Unicode minus and hyphens become ``-``,
``+/-`` becomes ``±``, ``<=`` becomes ``≤``, runs of space become one.
"""

import re
from dataclasses import dataclass

from usdm4.assembler.timeline.grammar import (
    PatternError,
    TimeRange,
    TimingPoint,
    Window,
    parse_window,
)

# Unit words as printed, longest first within each unit so the alternation
# never stops on a prefix.
_UNIT_WORDS = {
    "day": ("days", "day", "dys", "dy", "d"),
    "week": ("weeks", "week", "wks", "wk", "w"),
    "month": ("months", "month", "mths", "mth", "mo"),
    "year": ("years", "year", "yrs", "yr"),
    "hour": ("hours", "hour", "hrs", "hr", "h"),
    "minute": ("minutes", "minute", "mins", "min"),
}
_WORD_TO_UNIT = {word: unit for unit, words in _UNIT_WORDS.items() for word in words}
_UNIT = "|".join(sorted(_WORD_TO_UNIT, key=len, reverse=True))

_POINT = rf"(?:(?P<{{p}}u1>{_UNIT})\.?\s*)?(?P<{{p}}n>[-+]?\d+)(?:\s*(?P<{{p}}u2>{_UNIT})\b)?"


def _point(prefix: str) -> str:
    return _POINT.format(p=prefix)


_POINT_RE = re.compile(rf"^{_point('a')}$", re.IGNORECASE)
_RANGE_RE = re.compile(
    rf"^(?:between\s+)?{_point('a')}\s*(?:to|and|-)\s*{_point('b')}$",
    re.IGNORECASE,
)
_UP_TO_RE = re.compile(rf"^≤\s*(?P<n>\d+)(?:\s*(?P<u>{_UNIT}))?$", re.IGNORECASE)
_POINT_WINDOW_RE = re.compile(
    rf"^{_point('a')}\s*\(?\s*±\s*(?P<w>\d+)(?:\s*(?P<wu>{_UNIT}))?\s*\)?$",
    re.IGNORECASE,
)
_SYMMETRIC_RE = re.compile(
    rf"^\(?\s*±\s*(?P<w>\d+)(?:\s*(?P<u>{_UNIT}))?\s*\)?$", re.IGNORECASE
)
_ASYMMETRIC_RE = re.compile(
    rf"^\(?\s*-\s*(?P<lo>\d+)(?:\s*(?P<lu>{_UNIT}))?\s*/\s*\+\s*(?P<hi>\d+)"
    rf"(?:\s*(?P<hu>{_UNIT}))?\s*\)?$",
    re.IGNORECASE,
)
_LABEL_UNIT_RE = re.compile(rf"\b({_UNIT})\b", re.IGNORECASE)
_BLANK_RE = re.compile(r"^[\s\-–—]*$")


@dataclass(frozen=True)
class UpTo:
    """A printed ``≤N``: up to N units. Only a column before the anchor can
    be read, as ``Day -N to Day -1`` (U4-18) — the plan decides."""

    unit: str
    n: int


@dataclass(frozen=True)
class ReadTiming:
    """What a printed timing held. ``window`` is a window printed in the
    timing cell itself (``15 ± 3``). ``unit_defaulted`` is set when a bare
    number took days for want of a stated unit (U4-15)."""

    timing: TimingPoint | TimeRange | UpTo
    window: Window | None = None
    unit_defaulted: bool = False


@dataclass(frozen=True)
class ReadWindow:
    window: Window
    unit_defaulted: bool = False


def normalise(text: str) -> str:
    text = text.replace("−", "-").replace("‐", "-").replace("‑", "-")
    text = text.replace("+/-", "±").replace("+/−", "±").replace("<=", "≤")
    return " ".join(text.split())


def is_blank(text: str | None) -> bool:
    """Nothing printed: empty, or only dashes."""
    return text is None or bool(_BLANK_RE.match(text))


def unit_of_label(label: str | None) -> str | None:
    """The unit a header row label states (``Days from randomization``,
    ``Timing of Visit (Weeks)``, ``Time point (hours)``), else ``None``."""
    if not label:
        return None
    match = _LABEL_UNIT_RE.search(label)
    return _WORD_TO_UNIT[match.group(1).lower()] if match else None


def _unit_word(word: str | None) -> str | None:
    return _WORD_TO_UNIT[word.lower()] if word else None


def _one_unit(*words: str | None) -> tuple[bool, str | None]:
    """The single unit named by any of ``words``; ``(False, None)`` when two
    different units are named."""
    units = {_unit_word(w) for w in words if w}
    if len(units) > 1:
        return False, None
    return True, (units.pop() if units else None)


def _resolve(unit: str | None, row_unit: str | None) -> tuple[str, bool]:
    if unit:
        return unit, False
    if row_unit:
        return row_unit, False
    return "day", True


def _int(text: str) -> int:
    return int(text.lstrip("+"))


def read_timing(text: str | None, row_label: str | None = None) -> ReadTiming | None:
    """Read a printed timing. ``row_label`` is the timeline's timing row label
    (``rows.timing``), where a bare number's unit is stated."""
    if is_blank(text):
        return None
    text = normalise(text)
    row_unit = unit_of_label(row_label)

    match = _POINT_RE.match(text)
    if match:
        ok, unit = _one_unit(match.group("au1"), match.group("au2"))
        if not ok:
            return None
        unit, defaulted = _resolve(unit, row_unit)
        return ReadTiming(TimingPoint(unit, _int(match.group("an"))), None, defaulted)

    match = _RANGE_RE.match(text)
    if match:
        ok, unit = _one_unit(
            match.group("au1"),
            match.group("au2"),
            match.group("bu1"),
            match.group("bu2"),
        )
        start, end = _int(match.group("an")), _int(match.group("bn"))
        if not ok or end < start:
            return None
        unit, defaulted = _resolve(unit, row_unit)
        return ReadTiming(TimeRange(unit, start, end), None, defaulted)

    match = _UP_TO_RE.match(text)
    if match:
        unit, defaulted = _resolve(_unit_word(match.group("u")), row_unit)
        return ReadTiming(UpTo(unit, int(match.group("n"))), None, defaulted)

    match = _POINT_WINDOW_RE.match(text)
    if match:
        ok, unit = _one_unit(match.group("au1"), match.group("au2"))
        if not ok:
            return None
        unit, defaulted = _resolve(unit, row_unit)
        width = int(match.group("w"))
        window_unit = _unit_word(match.group("wu")) or unit
        return ReadTiming(
            TimingPoint(unit, _int(match.group("an"))),
            Window(width, width, window_unit),
            defaulted,
        )
    return None


def read_window(
    text: str | None,
    row_label: str | None = None,
    timing_unit: str | None = None,
) -> ReadWindow | None:
    """Read a printed window. A window with no unit takes the window row
    label's unit, else ``timing_unit``, else days (U4-19)."""
    if is_blank(text):
        return None
    text = normalise(text)
    try:
        return ReadWindow(parse_window(text))
    except PatternError:
        pass
    fallback = unit_of_label(row_label) or timing_unit

    match = _SYMMETRIC_RE.match(text)
    if match:
        unit, defaulted = _resolve(_unit_word(match.group("u")), fallback)
        width = int(match.group("w"))
        return ReadWindow(Window(width, width, unit), defaulted)

    match = _ASYMMETRIC_RE.match(text)
    if match:
        ok, unit = _one_unit(match.group("lu"), match.group("hu"))
        if not ok:
            return None
        unit, defaulted = _resolve(unit, fallback)
        return ReadWindow(
            Window(int(match.group("lo")), int(match.group("hi")), unit), defaulted
        )
    return None
