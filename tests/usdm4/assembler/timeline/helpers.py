"""Small builders for timeline-assembler test input (issue 63).

Every helper returns the dict ``Assembler`` hands on: validated against
``ScheduleTimelineInput`` and dumped.
"""

import os
import pathlib

from src.usdm4.assembler.schema.schedule_timeline_schema import ScheduleTimelineInput


def root_path() -> str:
    base = pathlib.Path(__file__).parent.parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


def value(
    text: str | None = None,
    pattern: str | None = None,
    markers: list[str] | None = None,
) -> dict:
    """A header value. ``value("Day 1")`` is printed text and pattern alike."""
    if pattern is None and text is not None:
        pattern = text
    data = {"text": text or "", "pattern": pattern}
    if markers:
        data["markers"] = list(markers)
    return data


def column(
    id: str,
    epoch: str | None = None,
    visit: str | dict | None = None,
    timing: str | dict | None = None,
    window: str | dict | None = None,
    markers: list[str] | None = None,
    **extra,
) -> dict:
    """A column. String arguments are used as printed text and pattern.

    ``markers`` is a shorthand for markers on the VISIT value (issue 64 moved
    them off the column); it needs a visit."""

    def _v(x):
        if x is None or isinstance(x, dict):
            return x
        return value(x)

    data = {
        "id": id,
        "epoch": _v(epoch),
        "visit": _v(visit),
        "timing": _v(timing),
        "window": _v(window),
    }
    if markers:
        assert data["visit"] is not None, "markers= needs a visit"
        data["visit"] = {**data["visit"], "markers": list(markers)}
    data.update(extra)
    return data


def activity(
    name: str,
    cells: list[str | dict] | None = None,
    parent: str | None = None,
    markers: list[str] | None = None,
    bcs: list[str] | None = None,
) -> dict:
    """An activity row. A cell given as a string is that column, marked X."""
    return {
        "name": name,
        "parent": parent,
        "markers": markers or [],
        "bcs": bcs or [],
        "cells": [
            {"column": c, "text": "X", "markers": []} if isinstance(c, str) else c
            for c in (cells or [])
        ],
    }


def timeline(
    columns: list[dict],
    activities: list[dict] | None = None,
    footnotes: list[dict] | None = None,
    type: str = "main",
    **extra,
) -> dict:
    data = {
        "type": type,
        "columns": columns,
        "activities": activities or [],
        "footnotes": footnotes or [],
    }
    data.update(extra)
    return ScheduleTimelineInput.model_validate(data).model_dump()


def simple(type: str = "main", title: str | None = None, **extra) -> dict:
    """Two columns, two activities — the minimal useful timeline."""
    return timeline(
        [
            column("c1", "Screening", "Visit 1", "Day 1", "-0..+0 days"),
            column("c2", "Treatment", "Visit 2", "Day 7", "-1..+1 days"),
        ],
        [activity("Consent", ["c1"]), activity("Blood Draw", ["c2"])],
        type=type,
        title=title,
        **extra,
    )
