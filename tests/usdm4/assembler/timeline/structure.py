"""Test fixtures in compact notation — issue 73.

Since issue 73 (U4-35) a caller hands ``usdm4`` every header value
structured. The tests still write fixtures compactly — ``"Day 1"``,
``"-3..+3 days"``, ``"Cycle 3+"`` — and this module turns that notation into
the structured objects. It is test code only: ``usdm4`` itself never reads
text. The notation is the retired pattern grammar's.

A value written ``{"text": ..., "pattern": ...}`` (the old input shape) is
converted: the pattern, when given, gives the structure; ``text`` stays the
label; a ``None`` pattern is text only; ``"CCI"`` is redacted.
"""

import re

_UNIT = r"(day|week|month|year|hour|minute)"
_UNITS = r"(days|weeks|months|years|hours|minutes)"
_INT = r"(-?\d+)"

_POINT = re.compile(rf"^{_UNIT} {_INT}$", re.IGNORECASE)
_RANGE = re.compile(rf"^{_UNIT} {_INT} to {_UNIT} {_INT}$", re.IGNORECASE)
_WINDOW = re.compile(rf"^-(\d+)\.\.\+(\d+) {_UNITS}$", re.IGNORECASE)
_CYCLE = re.compile(r"^cycle (\d+)(?:-(\d+)|(\+))?$", re.IGNORECASE)
_LENGTH = re.compile(rf"^(\d+) {_UNITS}$", re.IGNORECASE)
_DELAY = re.compile(rf"^(\d+)(?: to (\d+)|(\+)) {_UNITS}$", re.IGNORECASE)

VALUE_FIELDS = ("epoch", "visit", "cycle", "cycle_length", "timing", "window", "delay")


def _structure(field: str, pattern: str) -> dict:
    """The structured fields for ``pattern`` in ``field``. A pattern outside
    the notation is a test-writing error."""
    p = pattern.strip()
    if field == "timing":
        m = _RANGE.match(p)
        if m:
            return {
                "start": int(m.group(2)),
                "end": int(m.group(4)),
                "unit": m.group(1).lower() + "s",
            }
        m = _POINT.match(p)
        if m:
            return {"value": int(m.group(2)), "unit": m.group(1).lower() + "s"}
    elif field == "window":
        m = _WINDOW.match(p)
        if m:
            return {
                "before": int(m.group(1)),
                "after": int(m.group(2)),
                "unit": m.group(3).lower(),
            }
    elif field == "cycle":
        m = _CYCLE.match(p)
        if m:
            first = int(m.group(1))
            if m.group(3):
                return {"first": first, "last": None}
            last = int(m.group(2)) if m.group(2) else first
            return {"first": first, "last": last}
    elif field == "cycle_length":
        m = _LENGTH.match(p)
        if m:
            return {"value": int(m.group(1)), "unit": m.group(2).lower()}
    elif field == "delay":
        m = _DELAY.match(p)
        if m:
            return {
                "min": int(m.group(1)),
                "max": int(m.group(2)) if m.group(2) else None,
                "unit": m.group(4).lower(),
            }
    raise ValueError(f"test notation: {field} {pattern!r} not understood")


def structured(field: str, text: str | None, pattern: str | None, markers=None) -> dict:
    """One value in the structured form."""
    out: dict = {"text": text or ""}
    if markers:
        out["markers"] = list(markers)
    if pattern is not None and pattern.strip().upper() == "CCI":
        out["redacted"] = True
        if not out["text"]:
            out["text"] = pattern.strip()
        return out
    if field in ("epoch", "visit"):
        if not out["text"]:
            out["text"] = (pattern or "").strip()
        return out
    if pattern is not None and pattern.strip():
        out.update(_structure(field, pattern))
    return out


def convert_value(field: str, value):
    """A value in the old ``{text, pattern}`` shape → structured; anything
    else (``None``, already structured) as is."""
    if not isinstance(value, dict) or "pattern" not in value:
        return value
    return structured(
        field, value.get("text"), value.get("pattern"), value.get("markers")
    )


def convert_column(data: dict) -> dict:
    out = dict(data)
    for field in VALUE_FIELDS:
        if field in out:
            out[field] = convert_value(field, out[field])
    return out
