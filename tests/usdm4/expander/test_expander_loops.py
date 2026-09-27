"""The expander on loops, gates and second anchors (design § 7, U4-11).

A loop is run twice, so its decision goes each way once; a loop whose condition
states a minimum (``≥ 7 days …``) is run until the minimum has passed. A second
pass is timed so the loop's start falls at the decision's time; an instance hung
from a different anchor starts at the time the walk reaches it.

Hand-written USDM states the rules; the R5, R7 and R8 pin outputs show them on
USDM the assembler builds.
"""

import json

import pytest
from simple_error_log import Errors

from tests.usdm4.helpers.files import read_json_file
from usdm4.api.population_definition import StudyDesignPopulation
from usdm4.api.study_design import InterventionalStudyDesign
from usdm4.expander.expander import Expander
from usdm4.expander.timepoint import Timepoint

DAY = 86400
TYPES = {"before": "C201357", "after": "C201356", "fixed": "C201358"}


def _code(code: str) -> dict:
    return {
        "id": f"Code_{code}",
        "code": code,
        "codeSystem": "http://www.cdisc.org",
        "codeSystemVersion": "1",
        "decode": code,
        "instanceType": "Code",
    }


def _design(
    timelines: list[dict],
    activities: list[dict] | None = None,
    encounters: list[dict] | None = None,
):
    return InterventionalStudyDesign(
        id="sd",
        name="sd",
        rationale="r",
        arms=[],
        studyCells=[],
        epochs=[],
        encounters=encounters or [],
        activities=activities or [{"id": "A", "name": "A", "instanceType": "Activity"}],
        scheduleTimelines=timelines,
        population=StudyDesignPopulation(
            id="p",
            name="p",
            includesHealthySubjects=True,
            instanceType="StudyDesignPopulation",
        ),
        model=_code("C82639"),
        instanceType="InterventionalStudyDesign",
    )


def _sai(id: str, next: str | None = None, activities=("A",), timeline=None) -> dict:
    result = {
        "id": id,
        "name": id,
        "label": id,
        "activityIds": list(activities),
        "instanceType": "ScheduledActivityInstance",
    }
    if next:
        result["defaultConditionId"] = next
    else:
        result["timelineExitId"] = "X"
    if timeline:
        result["timelineId"] = timeline
    return result


def _decision(id: str, default: str, condition: str, target: str) -> dict:
    return {
        "id": id,
        "name": id,
        "defaultConditionId": default,
        "conditionAssignments": [
            {
                "id": f"{id}_CA",
                "condition": condition,
                "conditionTargetId": target,
                "instanceType": "ConditionAssignment",
            }
        ],
        "instanceType": "ScheduledDecisionInstance",
    }


def _timing(frm: str, kind: str, value: str, to: str) -> dict:
    return {
        "id": f"T_{frm}",
        "name": f"T_{frm}",
        "type": _code(TYPES[kind]),
        "value": value,
        "valueLabel": value,
        "relativeToFrom": _code("C201355"),
        "relativeFromScheduledInstanceId": frm,
        "relativeToScheduledInstanceId": to,
        "instanceType": "Timing",
    }


def _timeline(id: str, instances, timings, main=True) -> dict:
    return {
        "id": id,
        "name": id,
        "mainTimeline": main,
        "entryCondition": "e",
        "entryId": instances[0]["id"],
        "instances": instances,
        "timings": timings,
        "exits": [{"id": "X", "instanceType": "ScheduleTimelineExit"}],
        "instanceType": "ScheduleTimeline",
    }


def _expand(design, timeline_index: int = 0):
    errors = Errors()
    expander = Expander(design, design.scheduleTimelines[timeline_index], errors)
    expander.process()
    return expander, errors


def _seen(expander) -> list[tuple]:
    return [
        (n.to_dict()["label"], n.tick // DAY, n.pass_number) for n in expander.nodes
    ]


def _cycle(condition: str, back_on_default: bool = True):
    """D1 anchor; C3 at day 56, C3D15 14 days after it, a decision 14 days later
    looping back to C3; exit to FU 7 days after the decision."""
    decision = (
        _decision("DEC", "C3", condition, "FU")
        if back_on_default
        else _decision("DEC", "FU", condition, "C3")
    )
    instances = [
        _sai("D1", "C3"),
        _sai("C3", "C3D15"),
        _sai("C3D15", "DEC"),
        decision,
        _sai("FU"),
    ]
    timings = [
        _timing("D1", "fixed", "PT0M", "D1"),
        _timing("C3", "after", "P56D", "D1"),
        _timing("C3D15", "after", "P14D", "C3"),
        _timing("DEC", "after", "P14D", "C3D15"),
        _timing("FU", "after", "P7D", "DEC"),
    ]
    return _design([_timeline("TL", instances, timings)])


def _gate(condition: str):
    """D1 anchor; a washout GATE 1 day after; a decision 1 day after the gate
    looping back to it; period 2 hangs from its own anchor P2D1, entered at P2DM1."""
    instances = [
        _sai("D1", "GATE"),
        _sai("GATE", "DEC"),
        _decision("DEC", "GATE", condition, "P2DM1"),
        _sai("P2DM1", "P2D1"),
        _sai("P2D1", "P2D2"),
        _sai("P2D2"),
    ]
    timings = [
        _timing("D1", "fixed", "PT0M", "D1"),
        _timing("GATE", "after", "P1D", "D1"),
        _timing("DEC", "after", "P1D", "GATE"),
        _timing("P2DM1", "before", "P1D", "P2D1"),
        _timing("P2D1", "fixed", "PT0M", "P2D1"),
        _timing("P2D2", "after", "P1D", "P2D1"),
    ]
    return _design([_timeline("TL", instances, timings)])


class TestLoopRunTwice:
    def test_no_minimum_goes_back_once_then_out(self):
        expander, errors = _expand(_cycle("cycle exit condition"))
        assert _seen(expander) == [
            ("D1", 0, 1),
            ("C3", 56, 1),
            ("C3D15", 70, 1),
            ("C3", 84, 2),
            ("C3D15", 98, 2),
            ("FU", 119, 1),
        ]
        assert errors.count() == 0

    def test_the_loop_may_be_the_condition_branch(self):
        expander, errors = _expand(_cycle("cycle continues", back_on_default=False))
        assert [x[1] for x in _seen(expander)] == [0, 56, 70, 84, 98, 119]
        assert errors.count() == 0

    def test_a_minimum_the_first_pass_meets_leaves_at_once(self):
        expander, errors = _expand(_cycle("≥ 2 weeks and no progression"))
        assert [x[1] for x in _seen(expander)] == [0, 56, 70, 91]
        assert errors.count() == 0


class TestGate:
    def test_the_gate_is_run_until_the_minimum_has_passed(self):
        expander, errors = _expand(_gate("≥ 7 days and washed out, or 28 days"))
        assert _seen(expander) == [
            ("D1", 0, 1),
            ("GATE", 1, 1),
            ("GATE", 2, 2),
            ("GATE", 3, 3),
            ("GATE", 4, 4),
            ("GATE", 5, 5),
            ("GATE", 6, 6),
            ("GATE", 7, 7),
            ("P2DM1", 8, 1),
            ("P2D1", 9, 1),
            ("P2D2", 10, 1),
        ]
        assert errors.count() == 0

    @pytest.mark.parametrize(
        "condition, passes",
        [
            (">= 3 days", 3),
            ("≥ 36 hours", 2),
            ("≥ 1 week", 7),
            ("≥ 2880 minutes", 2),
        ],
    )
    def test_minimum_units(self, condition, passes):
        expander, _ = _expand(_gate(condition))
        assert [x[2] for x in _seen(expander) if x[0] == "GATE"][-1] == passes

    def test_no_minimum_runs_the_gate_twice(self):
        expander, _ = _expand(_gate("washed out"))
        assert [x[:2] for x in _seen(expander)] == [
            ("D1", 0),
            ("GATE", 1),
            ("GATE", 2),
            ("P2DM1", 3),
            ("P2D1", 4),
            ("P2D2", 5),
        ]

    @pytest.mark.parametrize("condition", ["≥ 1 month", "≥ 1 year"])
    def test_long_minimums(self, condition):
        expander, errors = _expand(_gate(condition))
        assert errors.count() == 0
        assert len([x for x in _seen(expander) if x[0] == "GATE"]) > 28


class TestAnchors:
    def test_a_new_anchor_reached_without_a_decision_starts_at_the_previous_time(
        self,
    ):
        instances = [_sai("D1", "D8"), _sai("D8", "P2D1"), _sai("P2D1")]
        timings = [
            _timing("D1", "fixed", "PT0M", "D1"),
            _timing("D8", "after", "P7D", "D1"),
            _timing("P2D1", "fixed", "PT0M", "P2D1"),
        ]
        expander, _ = _expand(_design([_timeline("TL", instances, timings)]))
        assert [x[1] for x in _seen(expander)] == [0, 7, 7]

    def test_a_sub_timeline_is_timed_from_the_instance_that_calls_it(self):
        main = _timeline(
            "TL",
            [_sai("D1", "D8"), _sai("D8", timeline="SUB")],
            [
                _timing("D1", "fixed", "PT0M", "D1"),
                _timing("D8", "after", "P7D", "D1"),
            ],
        )
        sub = _timeline(
            "SUB",
            [_sai("H0", "H1"), _sai("H1", "H2"), _sai("H2")],
            [
                _timing("H0", "fixed", "PT0M", "H0"),
                _timing("H1", "after", "PT1H", "H0"),
                _timing("H2", "after", "PT2H", "H0"),
            ],
            main=False,
        )
        expander, _ = _expand(_design([main, sub]))
        assert [n.tick for n in expander.nodes] == [
            0,
            7 * DAY,
            7 * DAY,
            7 * DAY + 3600,
            7 * DAY + 7200,
        ]


class TestGuards:
    def test_a_decision_whose_both_branches_go_back_is_not_a_loop(self, monkeypatch):
        monkeypatch.setattr(Expander, "STEP_LIMIT", 50)
        instances = [
            _sai("D1", "D2"),
            _sai("D2", "DEC"),
            _decision("DEC", "D1", "whatever", "D2"),
        ]
        timings = [
            _timing("D1", "fixed", "PT0M", "D1"),
            _timing("D2", "after", "P1D", "D1"),
            _timing("DEC", "after", "P1D", "D2"),
        ]
        _, errors = _expand(_design([_timeline("TL", instances, timings)]))
        messages = [e["message"] for e in errors.to_dict()]
        assert "No day condition encountered, being ignored." in messages
        assert any("Expansion stopped after 50 steps" in m for m in messages)

    def test_hop_without_a_timing(self):
        design = _cycle("x")
        expander = Expander(design, design.scheduleTimelines[0], Errors())
        assert expander._hop(design.scheduleTimelines[0], "NONE") is None

    def test_hop_on_a_circular_timing_chain(self):
        timings = [
            _timing("A", "after", "P1D", "B"),
            _timing("B", "after", "P1D", "A"),
        ]
        design = _design([_timeline("TL", [_sai("A", "B"), _sai("B")], timings)])
        expander = Expander(design, design.scheduleTimelines[0], Errors())
        assert expander._hop(design.scheduleTimelines[0], "A") is None

    def test_hop_on_an_unreadable_duration(self):
        timings = [
            _timing("A", "fixed", "PT0M", "A"),
            _timing("B", "after", "bad", "A"),
        ]
        design = _design([_timeline("TL", [_sai("A", "B"), _sai("B")], timings)])
        expander = Expander(design, design.scheduleTimelines[0], Errors())
        assert expander._hop(design.scheduleTimelines[0], "B") == (0, "A")

    @pytest.mark.parametrize("text", [None, "", "cycle exit condition", "≥ days"])
    def test_no_minimum(self, text):
        expander = Expander(None, None, Errors())
        assert expander._minimum(text) is None


class TestPassOnTheTimepoint:
    def test_pass_defaults_to_one_and_is_in_the_dict(self):
        design = _cycle("x")
        timeline = design.scheduleTimelines[0]
        sai = timeline.find_timepoint("C3")
        assert Timepoint(design, timeline, sai, Errors(), 1, 0).pass_number == 1
        tp = Timepoint(design, timeline, sai, Errors(), 1, 0, 2)
        assert tp.to_dict()["pass"] == 2


def _pin(name: str):
    data = json.loads(read_json_file("timeline_pin", f"expected_{name}.json"))
    return _design(
        data["timelines"],
        activities=data["activities"],
        encounters=data["encounters"],
    )


class TestPins:
    def test_r5_cycle_3_and_beyond_twice(self):
        expander, errors = _expand(_pin("nct05197426"))
        assert errors.count() == 0
        assert [(n.tick // DAY, n.pass_number) for n in expander.nodes][-4:] == [
            (56, 1),
            (70, 1),
            (84, 2),
            (98, 2),
        ]

    def test_r8_washout_then_period_2(self):
        expander, errors = _expand(_pin("nct03069989_r8"))
        assert errors.count() == 0
        assert [(n.tick // DAY, n.pass_number) for n in expander.nodes] == [
            (-30, 1),
            (-1, 1),
            (0, 1),
            (1, 1),
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (7, 7),
            (8, 1),
            (8, 1),
            (9, 1),
            (10, 1),
            (16, 1),
        ]

    def test_r7_profile_times_are_from_the_calling_visit(self):
        expander, errors = _expand(_pin("nct02674152_r7"))
        assert errors.count() == 0
        profile = sorted(
            {n.tick for n in expander.nodes if not n.to_dict()["main_timeline"]}
        )
        assert profile[:6] == [-300, 5400, 7200, 10800, 18000, 28800]
