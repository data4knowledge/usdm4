"""Repeating visit columns — issue 84.

A column can print a visit that repeats. Explicit visits (``Treatment (Week
3-11)`` over visits ``2-17``) are expanded into one visit each; an open repeat
(``Q12 Wks``, ``Every 6 months``) is one visit and a loop — a decision after it
by the period, looping back to it, like a gate or a cycle range.
"""

import pytest
from pydantic import ValidationError
from simple_error_log.errors import Errors

from src.usdm4.assembler.schema.schedule_timeline_schema import ColumnInput
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder
from tests.usdm4.assembler.timeline.helpers import (
    activity,
    column,
    root_path,
    timeline,
)


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


def _assemble(builder, soa: list[dict]):
    builder.clear()
    errors = Errors()
    assembler = TimelineAssembler(builder, errors)
    assembler.execute(soa)
    return assembler, errors


def _activity_instances(tl) -> list:
    return [i for i in tl.instances if i.instanceType == "ScheduledActivityInstance"]


def _decisions(tl) -> list:
    return [i for i in tl.instances if i.instanceType == "ScheduledDecisionInstance"]


def _timing_of(tl, instance):
    (found,) = [
        t for t in tl.timings if t.relativeFromScheduledInstanceId == instance.id
    ]
    return found


def _messages(errors: Errors) -> list[str]:
    return [item["message"] for item in errors.to_dict(0)]


def _explicit(period=None) -> list[dict]:
    repeat = {"text": "2-4", "visits": {"first": 2, "last": 4}}
    if period:
        repeat["period"] = period
    return [
        timeline(
            [
                column("c1", epoch="Screen", visit="1", timing="Week 1"),
                column(
                    "c2",
                    epoch="Treatment",
                    visit="2-4",
                    timing="Week 3 to Week 5",
                    repeat=repeat,
                ),
                column("c3", epoch="Follow-up", visit="5", timing="Week 8"),
            ],
            [activity("Dose", ["c2"]), activity("Consent", ["c1"])],
        )
    ]


class TestExplicitVisits:
    def test_one_encounter_per_visit_number(self, builder):
        assembler, _ = _assemble(builder, _explicit())
        assert [e.label for e in assembler.encounters] == ["1", "2", "3", "4", "5"]

    def test_each_visit_carries_the_columns_activities(self, builder):
        assembler, _ = _assemble(builder, _explicit())
        tl = assembler.timelines[0]
        names = {a.id: a.label for a in assembler.activities}
        sais = _activity_instances(tl)
        assert [[names[a] for a in s.activityIds] for s in sais] == [
            ["Consent"],
            ["Dose"],
            ["Dose"],
            ["Dose"],
            [],
        ]

    def test_with_no_period_each_visit_takes_the_range_and_a_warning(self, builder):
        assembler, errors = _assemble(builder, _explicit())
        tl = assembler.timelines[0]
        sais = _activity_instances(tl)
        for sai in sais[1:4]:
            timing = _timing_of(tl, sai)
            assert timing.value == "P2W"
            assert timing.windowUpper == "P2W"
        assert any("no period is given" in m for m in _messages(errors))

    def test_with_a_period_each_visit_is_timed_by_it(self, builder):
        assembler, errors = _assemble(builder, _explicit({"value": 1, "unit": "weeks"}))
        tl = assembler.timelines[0]
        sais = _activity_instances(tl)
        assert [_timing_of(tl, s).value for s in sais[1:4]] == ["P2W", "P3W", "P4W"]
        assert not any("no period" in m for m in _messages(errors))

    def test_no_loop_is_built(self, builder):
        assembler, _ = _assemble(builder, _explicit())
        assert _decisions(assembler.timelines[0]) == []


def _open(period, end=None, last=False) -> list[dict]:
    repeat = {"text": "Q12 Wks", "period": period}
    if end:
        repeat["end"] = end
    columns = [
        column("c1", epoch="Treatment", visit="Day 1", timing="Day 1"),
        column(
            "c2", epoch="Treatment", visit="Q12 Wks", timing="Week 48", repeat=repeat
        ),
    ]
    if not last:
        columns.append(column("c3", epoch="End", visit="EOS", timing="Week 100"))
    return [timeline(columns, [activity("Labs", ["c1", "c2"])])]


class TestOpenRepeat:
    def test_one_encounter_and_a_decision_after_it_by_the_period(self, builder):
        assembler, _ = _assemble(builder, _open({"value": 12, "unit": "weeks"}))
        tl = assembler.timelines[0]
        assert [e.label for e in assembler.encounters] == ["Day 1", "Q12 Wks", "EOS"]
        (decision,) = _decisions(tl)
        repeat = _activity_instances(tl)[1]
        assert decision.name == "REPEAT1DEC"
        timing = _timing_of(tl, decision)
        assert timing.value == "P12W"
        assert timing.relativeToScheduledInstanceId == repeat.id
        assert repeat.defaultConditionId == decision.id

    def test_the_decision_loops_back_and_exits_to_the_next_column(self, builder):
        assembler, _ = _assemble(builder, _open({"value": 12, "unit": "weeks"}))
        tl = assembler.timelines[0]
        (decision,) = _decisions(tl)
        sais = _activity_instances(tl)
        assert decision.defaultConditionId == sais[1].id
        (assignment,) = decision.conditionAssignments
        assert assignment.conditionTargetId == sais[2].id
        assert assignment.condition == "repeat exit condition"

    def test_a_printed_bound_is_the_exit_condition(self, builder):
        assembler, _ = _assemble(
            builder,
            _open(
                {"value": 7, "unit": "days"}, end={"text": "until discharge or Day 60"}
            ),
        )
        (decision,) = _decisions(assembler.timelines[0])
        (assignment,) = decision.conditionAssignments
        assert assignment.condition == "until discharge or Day 60"

    def test_as_the_last_column_it_exits_through_an_end_instance(self, builder):
        assembler, _ = _assemble(
            builder, _open({"value": 12, "unit": "weeks"}, last=True)
        )
        tl = assembler.timelines[0]
        (decision,) = _decisions(tl)
        end = tl.instances[-1]
        assert end.name == "REPEAT1END"
        assert end.encounterId is None
        assert end.timelineExitId is not None
        (assignment,) = decision.conditionAssignments
        assert assignment.conditionTargetId == end.id

    def test_a_series_run_on_is_open(self, builder):
        soa = [
            timeline(
                [
                    column("c1", visit="V1", timing="Week 0"),
                    column(
                        "c2",
                        visit="V2, V3 ... VX",
                        timing="Week 26",
                        repeat={
                            "text": "W26, W52 ... WX",
                            "visits": {"first": 2, "last": None},
                            "period": {"value": 26, "unit": "weeks"},
                        },
                    ),
                ],
                [activity("Scan", ["c2"])],
            )
        ]
        assembler, _ = _assemble(builder, soa)
        assert len(assembler.encounters) == 2
        assert len(_decisions(assembler.timelines[0])) == 1

    # must not fire

    def test_no_period_builds_no_loop_and_warns(self, builder):
        soa = [
            timeline(
                [
                    column("c1", visit="Day 1", timing="Day 1"),
                    column(
                        "c2",
                        visit="Every 6 months",
                        timing="Month 6",
                        repeat={"text": "Every 6 months", "visits": {"first": 3}},
                    ),
                ],
                [activity("Labs", ["c2"])],
            )
        ]
        assembler, errors = _assemble(builder, soa)
        assert _decisions(assembler.timelines[0]) == []
        assert any("a repeat with no period" in m for m in _messages(errors))


class TestTextOnly:
    def test_a_repeat_sent_as_text_only_is_not_read(self, builder):
        soa = [
            timeline(
                [
                    column("c1", visit="Day 1", timing="Day 1"),
                    column(
                        "c2",
                        visit="Every 6 months",
                        timing="Month 6",
                        repeat={"text": "Every 6 months"},
                    ),
                ],
                [activity("Labs", ["c2"])],
            )
        ]
        assembler, errors = _assemble(builder, soa)
        assert _decisions(assembler.timelines[0]) == []
        assert len(assembler.encounters) == 2
        assert any("repeat: sent as text only" in m for m in _messages(errors))


class TestUnchanged:
    def test_a_timeline_with_no_repeat_builds_as_before(self, builder):
        soa = [
            timeline(
                [
                    column("c1", visit="1", timing="Day 1"),
                    column("c2", visit="2", timing="Day 8"),
                ],
                [activity("Dose", ["c1", "c2"])],
            )
        ]
        assembler, _ = _assemble(builder, soa)
        tl = assembler.timelines[0]
        assert _decisions(tl) == []
        assert [e.label for e in assembler.encounters] == ["1", "2"]


class TestInput:
    def test_a_repeat_and_a_cycle_are_refused_together(self):
        with pytest.raises(ValidationError, match="a repeat is not a cycle"):
            ColumnInput.model_validate(
                {
                    "id": "c1",
                    "cycle": {"first": 3, "last": None},
                    "repeat": {"text": "Q3W", "period": {"value": 3, "unit": "weeks"}},
                }
            )

    def test_a_repeat_and_a_delay_are_refused_together(self):
        with pytest.raises(ValidationError, match="cannot repeat"):
            ColumnInput.model_validate(
                {
                    "id": "c1",
                    "delay": {"min": 7, "unit": "days"},
                    "repeat": {"text": "Q3W", "period": {"value": 3, "unit": "weeks"}},
                }
            )

    def test_a_visit_range_ending_before_it_starts_is_refused(self):
        with pytest.raises(ValidationError, match="before its first"):
            ColumnInput.model_validate(
                {"id": "c1", "repeat": {"text": "x", "visits": {"first": 5, "last": 2}}}
            )

    def test_a_repeat_with_no_structure_needs_its_text(self):
        with pytest.raises(ValidationError):
            ColumnInput.model_validate({"id": "c1", "repeat": {"text": ""}})
