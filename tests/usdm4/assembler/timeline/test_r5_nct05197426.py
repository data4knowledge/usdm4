"""R5 — cycle ranges, on NCT05197426 (test case ruled by Dave, 2026-09-26).

The input is ``tests/usdm4/test_files/timeline_pin/input_nct05197426.json``:
what a correct stage 1 would hand ``usdm4`` — Cycle 1 and Cycle 2 on Days 1, 8,
15 and 22, then ``Cycle 3+`` on Days 1 and 15, cycle length 4 weeks, the range
as the last column. These tests state the structures R5 must build from good
cycle data (design § 6 R5, U4-7, U4-27, and the end instance for a range that
is the last column).

Issue 69. The single-cycle tests held before R5; the range tests were
``xfail(strict=True)`` until R5 was built. Issue 95 (U4-39): the range is a
loop — an entry, its days, a pad and an untimed decision — and each single
cycle has a pad.
"""

import json

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.schema.schedule_timeline_schema import (
    ScheduleTimelineInput,
)
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder
from tests.usdm4.assembler.timeline.helpers import root_path
from tests.usdm4.assembler.timeline.structure import convert_column
from tests.usdm4.helpers.files import read_json_file


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


@pytest.fixture
def timeline(builder):
    builder.clear()
    data = json.loads(read_json_file("timeline_pin", "input_nct05197426.json"))
    soa = [ScheduleTimelineInput.model_validate(t).model_dump() for t in data["soa"]]
    assembler = TimelineAssembler(builder, Errors())
    assembler.execute(soa)
    return assembler.timelines[0]


def _by_label(tl) -> dict:
    """Activity instances by their printed timing text and cycle, keyed as
    the column ids of the input (``c3pd15``)."""
    keys = [
        "scr",
        "rand",
        "c1d1",
        "c1d8",
        "c1d15",
        "c1d22",
        "c2d1",
        "c2d8",
        "c2d15",
        "c2d22",
        "c3pd1",
        "c3pd15",
    ]
    visits = [
        i
        for i in tl.instances
        if i.instanceType == "ScheduledActivityInstance" and i.encounterId is not None
    ]
    assert len(visits) == len(keys)
    return dict(zip(keys, visits))


def _timing_of(tl, instance):
    found = [t for t in tl.timings if t.relativeFromScheduledInstanceId == instance.id]
    assert len(found) == 1
    return found[0]


def _link(tl, instance, to=None) -> tuple:
    timing = _timing_of(tl, instance)
    return (
        timing.type.decode.replace(" Timing Type", ""),
        timing.relativeToScheduledInstanceId if to is None else to,
        timing.value,
    )


def _decisions(tl) -> list:
    return [i for i in tl.instances if i.instanceType == "ScheduledDecisionInstance"]


# ----------------------------------------------------------------------
# Before the range — R4, U4-27


class TestSingleCycles:
    def test_cycle_1_day_1_is_the_anchor(self, timeline):
        v = _by_label(timeline)
        assert _link(timeline, v["c1d1"]) == ("Fixed Reference", v["c1d1"].id, "PT0M")

    def test_screening_and_randomization_before_the_anchor(self, timeline):
        v = _by_label(timeline)
        assert _link(timeline, v["scr"]) == ("Before", v["c1d1"].id, "P28D")
        assert _link(timeline, v["rand"]) == ("Before", v["c1d1"].id, "P3D")

    def test_days_within_a_cycle_from_its_day_1(self, timeline):
        v = _by_label(timeline)
        for n in (1, 2):
            d1 = v[f"c{n}d1"].id
            assert _link(timeline, v[f"c{n}d8"]) == ("After", d1, "P7D")
            assert _link(timeline, v[f"c{n}d15"]) == ("After", d1, "P14D")
            assert _link(timeline, v[f"c{n}d22"]) == ("After", d1, "P21D")

    def test_cycle_2_day_1_is_4_weeks_after_cycle_1_day_1(self, timeline):
        v = _by_label(timeline)
        assert _link(timeline, v["c2d1"]) == ("After", v["c1d1"].id, "P28D")

    def test_each_cycle_has_a_pad_at_its_full_length(self, timeline):
        """Issue 95: the pad is the length less one after Day 1, between the
        cycle's last day and the next cycle."""
        v = _by_label(timeline)
        n = _named(timeline)
        for c in (1, 2):
            pad = n[f"C{c}PAD"]
            assert pad.encounterId is None and pad.activityIds == []
            assert _link(timeline, pad) == ("After", v[f"c{c}d1"].id, "P27D")
            assert v[f"c{c}d22"].defaultConditionId == pad.id


# ----------------------------------------------------------------------
# The range — R5 (issue 69)


class TestRange:
    def test_the_entry_is_4_weeks_after_cycle_2_day_1(self, timeline):
        """Issue 95: the entry takes the range's timing in from outside."""
        v = _by_label(timeline)
        entry = _named(timeline)["C3+ENTRY"]
        assert entry.encounterId is None and entry.activityIds == []
        assert _link(timeline, entry) == ("After", v["c2d1"].id, "P28D")
        assert entry.defaultConditionId == v["c3pd1"].id

    def test_range_day_1_is_zero_after_the_entry(self, timeline):
        v = _by_label(timeline)
        entry = _named(timeline)["C3+ENTRY"]
        assert _link(timeline, v["c3pd1"]) == ("After", entry.id, "PT0M")

    def test_range_day_15_from_the_range_day_1(self, timeline):
        v = _by_label(timeline)
        assert _link(timeline, v["c3pd15"]) == ("After", v["c3pd1"].id, "P14D")

    def test_the_pad_then_one_decision_follow_the_last_day(self, timeline):
        v = _by_label(timeline)
        pad = _named(timeline)["C3+PAD"]
        decisions = _decisions(timeline)
        assert len(decisions) == 1
        assert v["c3pd15"].defaultConditionId == pad.id
        assert pad.defaultConditionId == decisions[0].id

    def test_the_pad_is_the_length_less_one(self, timeline):
        """28-day cycle: the pad is 27 days after the range's Day 1."""
        v = _by_label(timeline)
        pad = _named(timeline)["C3+PAD"]
        assert pad.encounterId is None and pad.activityIds == []
        assert _link(timeline, pad) == ("After", v["c3pd1"].id, "P27D")

    def test_the_decision_has_no_timing(self, timeline):
        decision = _decisions(timeline)[0]
        assert [
            t
            for t in timeline.timings
            if t.relativeFromScheduledInstanceId == decision.id
        ] == []

    def test_the_default_loops_back_to_the_range_day_1(self, timeline):
        v = _by_label(timeline)
        assert _decisions(timeline)[0].defaultConditionId == v["c3pd1"].id

    def test_the_exit_condition(self, timeline):
        """U4-7: one assignment, fixed text, to the end instance."""
        decision = _decisions(timeline)[0]
        assert len(decision.conditionAssignments) == 1
        assignment = decision.conditionAssignments[0]
        assert assignment.condition == "cycle exit condition"
        target = timeline.find_timepoint(assignment.conditionTargetId)
        assert target.instanceType == "ScheduledActivityInstance"
        assert target.encounterId is None
        assert target.activityIds == []

    def test_the_end_instance_carries_the_exit(self, timeline):
        """The range is the last column; a decision cannot target the exit,
        so the end instance after it does."""
        decision = _decisions(timeline)[0]
        end = timeline.find_timepoint(
            decision.conditionAssignments[0].conditionTargetId
        )
        assert end.timelineExitId == timeline.exits[0].id
        assert end.defaultConditionId is None
        with_exit = [
            i
            for i in timeline.instances
            if i.instanceType == "ScheduledActivityInstance" and i.timelineExitId
        ]
        assert with_exit == [end]

    def test_the_range_instances_are_in_the_range_epoch(self, timeline):
        v = _by_label(timeline)
        decision = _decisions(timeline)[0]
        assert decision.epochId == v["c3pd1"].epochId == v["c3pd15"].epochId


# ----------------------------------------------------------------------
# Other range shapes, structured input (issue 69)


def _col(i, timing, cycle=None, length=None, epoch="Treatment"):
    data = {"id": f"c{i}", "epoch": {"text": epoch, "pattern": epoch}}
    for key, text in (("timing", timing), ("cycle", cycle), ("cycle_length", length)):
        if text:
            data[key] = {"text": text, "pattern": text}
    return data


def _build(builder, specs):
    builder.clear()
    columns = [convert_column(_col(i + 1, *spec)) for i, spec in enumerate(specs)]
    soa = {
        "type": "main",
        "columns": columns,
        "activities": [
            {"name": "X", "cells": [{"column": c["id"], "text": "X"} for c in columns]}
        ],
    }
    assembler = TimelineAssembler(builder, Errors())
    assembler.execute([ScheduleTimelineInput.model_validate(soa).model_dump()])
    return assembler.timelines[0]


def _day(tl, instance) -> int:
    """Days from the anchor on the first pass, following the timings."""
    timing = _timing_of(tl, instance)
    kind = timing.type.decode
    if kind.startswith("Fixed"):
        return 0
    days = 0 if timing.value == "PT0M" else int(timing.value[1:-1])
    base = _day(tl, tl.find_timepoint(timing.relativeToScheduledInstanceId))
    return base + days if kind.startswith("After") else base - days


def _named(tl) -> dict:
    return {i.name: i for i in tl.instances}


class TestOtherShapes:
    def test_a_bounded_range_then_an_open_one(self, builder):
        tl = _build(
            builder,
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2-3", "21 days"),
                ("Day 8", "Cycle 2-3", "21 days"),
                ("Day 1", "Cycle 4+", "21 days"),
            ],
        )
        n = _named(tl)
        assert [i.name for i in tl.instances] == [
            "C1D1",
            "C1PAD",
            "C2-3ENTRY",
            "C2-3D1",
            "C2-3D8",
            "C2-3PAD",
            "C2-3DEC",
            "C4+ENTRY",
            "C4+D1",
            "C4+PAD",
            "C4+DEC",
            "T1-END",
        ]
        assert [_day(tl, n[k]) for k in ("C2-3D1", "C2-3D8", "C2-3PAD")] == [21, 28, 41]
        assert [_day(tl, n[k]) for k in ("C4+ENTRY", "C4+D1", "C4+PAD")] == [42, 42, 62]
        first = n["C2-3DEC"]
        assert first.defaultConditionId == n["C2-3D1"].id
        assert first.conditionAssignments[0].conditionTargetId == n["C4+ENTRY"].id
        assert n["C4+DEC"].defaultConditionId == n["C4+D1"].id

    def test_a_range_with_no_day_1_loops_to_its_marker(self, builder):
        tl = _build(
            builder,
            [
                ("Day 1", "Cycle 1", "28 days"),
                ("Day 8", "Cycle 2+", "28 days"),
                ("Day 15", "Cycle 2+", "28 days"),
            ],
        )
        n = _named(tl)
        assert [i.name for i in tl.instances] == [
            "C1D1",
            "C1PAD",
            "C2+ENTRY",
            "C2+D1",
            "C2+D8",
            "C2+D15",
            "C2+PAD",
            "C2+DEC",
            "T1-END",
        ]
        assert n["C2+D1"].encounterId is None
        assert n["C2+DEC"].defaultConditionId == n["C2+D1"].id
        assert [_day(tl, n[k]) for k in ("C2+D1", "C2+D15", "C2+PAD")] == [28, 42, 55]

    def test_a_predose_day_is_inside_the_loop(self, builder):
        """The pass starts at the range's first column, before ``Day 1``."""
        tl = _build(
            builder,
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day -1", "Cycle 2+", "21 days"),
                ("Day 1", "Cycle 2+", "21 days"),
                ("Day 15", "Cycle 2+", "21 days"),
            ],
        )
        n = _named(tl)
        assert n["C2+DEC"].defaultConditionId == n["C2+D-1"].id
        assert [_day(tl, n[k]) for k in ("C2+D-1", "C2+D1", "C2+PAD")] == [20, 21, 41]

    def test_weeks(self, builder):
        tl = _build(
            builder,
            [
                ("Week 1", "Cycle 1", "4 weeks"),
                ("Week 1", "Cycle 2+", "4 weeks"),
                ("Week 3", "Cycle 2+", "4 weeks"),
            ],
        )
        pad = [i for i in tl.instances if i.name == "C2+PAD"][0]
        assert _timing_of(tl, pad).value == "P3W"
