"""R8 — gates, on NCT03069989 (issue 74).

The input is ``tests/usdm4/test_files/timeline_pin/input_nct03069989_r8.json``:
the protocol's header written by hand in the structured form — two dosing
periods joined by a washout of 7 to 28 days. These tests state what R8 builds
(design § 6 R8, U4-10, U4-36): the washout column is the gate's instance, with
no encounter; a decision one day after it loops back to it and exits to
period 2 on ``≥ 7 days and washed out, or 28 days``; period 2 is timed from its
own ``Day 1``, a second Fixed Reference, and no timing joins it to period 1.
"""

import json

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.schema.schedule_timeline_schema import (
    ScheduleTimelineInput,
)
from src.usdm4.assembler.timeline.build import TimelineBuild
from src.usdm4.assembler.timeline.values import Delay
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder
from tests.usdm4.assembler.timeline.helpers import (
    activity,
    column,
    root_path,
    timeline,
    value,
)
from tests.usdm4.helpers.files import read_json_file

KEYS = ["scr", "p1dm1", "p1d1", "p1d2", "wash", "p2pet", "p2dm1", "p2d1", "p2d2", "fu"]


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


def _assemble(builder, soa: list[dict]):
    builder.clear()
    errors = Errors()
    assembler = TimelineAssembler(builder, errors)
    assembler.execute(soa)
    return assembler, errors


@pytest.fixture
def built(builder):
    data = json.loads(read_json_file("timeline_pin", "input_nct03069989_r8.json"))
    soa = [ScheduleTimelineInput.model_validate(t).model_dump() for t in data["soa"]]
    assembler, errors = _assemble(builder, soa)
    return assembler, errors


@pytest.fixture
def tl(built):
    return built[0].timelines[0]


def _activity_instances(tl) -> dict:
    """Activity instances in column order, keyed as the input's column ids."""
    found = [i for i in tl.instances if i.instanceType == "ScheduledActivityInstance"]
    assert len(found) == len(KEYS)
    return dict(zip(KEYS, found))


def _decisions(tl) -> list:
    return [i for i in tl.instances if i.instanceType == "ScheduledDecisionInstance"]


def _timing_of(tl, instance):
    found = [t for t in tl.timings if t.relativeFromScheduledInstanceId == instance.id]
    assert len(found) == 1
    return found[0]


def _link(tl, instance) -> tuple:
    timing = _timing_of(tl, instance)
    return (
        timing.type.decode.replace(" Timing Type", ""),
        timing.relativeToScheduledInstanceId,
        timing.value,
    )


def _messages(errors: Errors) -> list[str]:
    return [item["message"] for item in errors.to_dict(0)]


class TestGate:
    def test_the_washout_column_is_an_instance_with_no_encounter(self, tl):
        gate = _activity_instances(tl)["wash"]
        assert gate.name == "GATE1"
        assert gate.label == "(7-28 days between doses)"
        assert gate.encounterId is None

    def test_its_cells_attach_to_it(self, built, tl):
        gate = _activity_instances(tl)["wash"]
        names = {a.id: a.label for a in built[0].activities}
        assert [names[a] for a in gate.activityIds] == ["Adverse event review"]

    def test_it_is_zero_after_the_last_day_of_period_1(self, tl):
        v = _activity_instances(tl)
        assert _link(tl, v["wash"]) == ("After", v["p1d2"].id, "PT0M")

    def test_one_decision_one_day_after_the_gate(self, tl):
        v = _activity_instances(tl)
        (decision,) = _decisions(tl)
        assert decision.name == "GATE1DEC"
        assert _link(tl, decision) == ("After", v["wash"].id, "P1D")
        assert v["wash"].defaultConditionId == decision.id

    def test_the_decision_loops_back_to_the_gate(self, tl):
        v = _activity_instances(tl)
        (decision,) = _decisions(tl)
        assert decision.defaultConditionId == v["wash"].id

    def test_the_exit_leads_to_period_2(self, tl):
        v = _activity_instances(tl)
        (decision,) = _decisions(tl)
        (assignment,) = decision.conditionAssignments
        assert assignment.condition == "≥ 7 days and washed out, or 28 days"
        assert assignment.conditionTargetId == v["p2pet"].id

    def test_in_the_washout_epoch(self, built, tl):
        v = _activity_instances(tl)
        (decision,) = _decisions(tl)
        epochs = {e.id: e.label for e in built[0].epochs}
        assert epochs[v["wash"].epochId] == "Wash-out"
        assert epochs[decision.epochId] == "Wash-out"

    def test_nine_encounters_none_for_the_gate(self, built):
        assert [e.label for e in built[0].encounters] == [
            "",
            "",
            "",
            "",
            "Baseline PET",
            "",
            "",
            "",
            "",
        ]

    def test_markers_on_header_values_link(self, built, tl):
        v = _activity_instances(tl)
        by_label = {c.label: c for c in built[0].conditions}
        assert set(by_label["1"].contextIds) == {v["p1dm1"].id, v["p2dm1"].id}
        assert set(by_label["2"].contextIds) == {
            v["p2pet"].id,
            v["p2d1"].id,
            v["p2d2"].id,
        }


class TestPeriods:
    def test_period_1_from_its_day_1(self, tl):
        v = _activity_instances(tl)
        d1 = v["p1d1"].id
        assert _link(tl, v["scr"]) == ("Before", d1, "P30D")
        assert _link(tl, v["p1dm1"]) == ("Before", d1, "P1D")
        assert _link(tl, v["p1d1"]) == ("Fixed Reference", d1, "PT0M")
        assert _link(tl, v["p1d2"]) == ("After", d1, "P1D")

    def test_screening_window_to_day_minus_1(self, tl):
        timing = _timing_of(tl, _activity_instances(tl)["scr"])
        assert (timing.windowLower, timing.windowUpper) == ("", "P29D")

    def test_period_2_from_its_own_day_1(self, tl):
        v = _activity_instances(tl)
        d1 = v["p2d1"].id
        assert _link(tl, v["p2pet"]) == ("Before", v["p2dm1"].id, "PT0M")
        assert _link(tl, v["p2dm1"]) == ("Before", d1, "P1D")
        assert _link(tl, v["p2d1"]) == ("Fixed Reference", d1, "PT0M")
        assert _link(tl, v["p2d2"]) == ("After", d1, "P1D")

    def test_follow_up_is_a_range_in_period_2(self, tl):
        v = _activity_instances(tl)
        timing = _timing_of(tl, v["fu"])
        assert _link(tl, v["fu"]) == ("After", v["p2d1"].id, "P7D")
        assert (timing.windowLower, timing.windowUpper) == ("", "P7D")

    def test_two_anchors(self, tl):
        fixed = [t for t in tl.timings if t.type.decode.startswith("Fixed")]
        assert len(fixed) == 2

    def test_no_timing_joins_period_2_to_period_1(self, tl):
        v = _activity_instances(tl)
        period_1 = {v[k].id for k in ("scr", "p1dm1", "p1d1", "p1d2")}
        for key in ("p2pet", "p2dm1", "p2d1", "p2d2", "fu"):
            assert _timing_of(tl, v[key]).relativeToScheduledInstanceId not in period_1

    def test_the_chain_runs_through_the_gate_to_the_exit(self, tl):
        v = _activity_instances(tl)
        assert v["p2d2"].defaultConditionId == v["fu"].id
        assert v["fu"].timelineExitId is not None

    def test_only_baseline_pet_is_warned(self, built):
        warnings = [m for m in _messages(built[1]) if "restarts" in m or "R8" in m]
        assert warnings == []
        assert (
            "Timeline 1, column 'p2pet': no readable timing; a zero timing is used"
            in _messages(built[1])
        )


class TestOtherShapes:
    def test_must_not_fire_a_washout_timed_as_a_range(self, builder):
        """A washout printed at an anchored time (``Week 1-2``) is an ordinary
        timing, not a gate."""
        soa = [
            timeline(
                [
                    column("c1", epoch="Treatment", timing="Day 1"),
                    column("c2", epoch="Washout", timing="Week 1 to Week 2"),
                    column("c3", epoch="Treatment", timing="Week 3"),
                ],
                [activity("Dose", ["c1", "c3"])],
            )
        ]
        assembler, _ = _assemble(builder, soa)
        tl = assembler.timelines[0]
        assert _decisions(tl) == []
        assert len(assembler.encounters) == 3
        fixed = [t for t in tl.timings if t.type.decode.startswith("Fixed")]
        assert len(fixed) == 1

    def test_a_gate_as_the_last_column_exits_through_an_end_instance(self, builder):
        soa = [
            timeline(
                [
                    column("c1", epoch="Treatment", timing="Day 1"),
                    column(
                        "c2", epoch="Washout", visit="Washout", delay=value("3+ days")
                    ),
                ],
                [activity("Dose", ["c1"])],
            )
        ]
        assembler, _ = _assemble(builder, soa)
        tl = assembler.timelines[0]
        (decision,) = _decisions(tl)
        end = tl.instances[-1]
        assert end.name == "GATE1END"
        assert end.timelineExitId is not None
        assert end.encounterId is None
        (assignment,) = decision.conditionAssignments
        assert assignment.conditionTargetId == end.id
        assert assignment.condition == "≥ 3 days and washed out"


class TestGateCondition:
    @pytest.mark.parametrize(
        "delay, expected",
        [
            (Delay(7, 28, "day"), "≥ 7 days and washed out, or 28 days"),
            (Delay(2, None, "day"), "≥ 2 days and washed out"),
            (Delay(1, 2, "week"), "≥ 1 weeks and washed out, or 2 weeks"),
        ],
    )
    def test_filled_from_the_delay(self, delay, expected):
        assert TimelineBuild.gate_condition(delay) == expected
