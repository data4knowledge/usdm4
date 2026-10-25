"""Plan — issue 63, part 63.6; issue 65; issue 66 (single cycles); issue 68
(cycle reading, NCT02107703's header shape).

The straight chain and its one anchor: anchor choice, the crossing-zero rule,
mixed units (kept from before the restructure); and from issue 65 the U4-2
warnings, the zero-timing chain for columns with no readable timing (U4-3)
and time ranges (U4-4, U4-20). Issue 73 (U4-35): Day 0 comes from the
timeline's ``day_zero`` flag; ``≤N`` is the caller's to structure.
"""

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.columns import parse_timeline
from src.usdm4.assembler.timeline.plan import (
    AFTER,
    BEFORE,
    DECISION,
    END,
    ENTRY,
    FIXED,
    GATE,
    PAD,
    START,
    START_KEY,
    Planner,
)
from tests.usdm4.assembler.timeline.helpers import column, timeline, value


def _plan(timings: list, errors: Errors | None = None, **extra):
    columns = [column(f"c{i + 1}", timing=t) for i, t in enumerate(timings)]
    parsed = parse_timeline(timeline(columns, **extra))
    return Planner(errors or Errors()).plan(parsed, 1)


def _text(text: str) -> dict:
    return {"text": text, "pattern": None}


def _messages(errors: Errors) -> list[str]:
    return [item["message"] for item in errors.to_dict(0)]


def _links(plan):
    return [(n.timing_type, n.relative_to, n.duration) for n in plan.nodes]


def _summary(plan):
    return [(n.timing_type, n.duration, n.unit) for n in plan.nodes]


class TestAnchor:
    def test_first_non_negative_day(self):
        plan = _plan(["Day -7", "Day 1", "Day 8"])
        assert plan.anchor == 1

    def test_day_zero_is_an_anchor(self):
        assert _plan(["Day -1", "Day 0", "Day 1"]).anchor == 1

    def test_blank_columns_are_skipped(self):
        assert _plan([None, "Day 1"]).anchor == 1

    def test_text_only_columns_are_not_anchors(self):
        assert (
            _plan([{"text": "Screening visit", "pattern": None}, "Day 1"]).anchor == 1
        )

    def test_no_candidate_falls_back_to_the_first_column(self):
        assert _plan(["Day -14", "Day -7"]).anchor == 0
        assert _plan([None, None]).anchor == 0

    def test_node_types_around_the_anchor(self):
        plan = _plan(["Day -7", "Day 1", "Day 8"])
        assert [n.timing_type for n in plan.nodes] == [BEFORE, FIXED, AFTER]
        assert all(n.relative_to == 1 for n in plan.nodes)


class TestIntervals:
    def test_relative_to_the_anchor_with_the_crossing_zero_rule(self):
        """Day 1 numbering: Day -7 to Day 1 is 7 days, Day 1 to Day 8 is 7."""
        plan = _plan(["Day -7", "Day 1", "Day 8"])
        assert _summary(plan) == [
            (BEFORE, 7, "day"),
            (FIXED, 0, "day"),
            (AFTER, 7, "day"),
        ]

    def test_no_correction_when_the_protocol_has_a_day_zero(self):
        plan = _plan(["Day -7", "Day 0", "Day 7"], day_zero=True)
        assert [n.duration for n in plan.nodes] == [7, 0, 7]

    def test_the_flag_not_the_columns_stops_the_correction(self):
        """U4-35: ``day_zero`` says the protocol counts from zero, whether or
        not a Day 0 column is printed."""
        plan = _plan(["Day -7", "Day 1"], day_zero=True)
        assert plan.nodes[0].duration == 8

    def test_a_printed_day_zero_with_the_flag_at_day_1_is_warned(self):
        """U4-35: warned, and the flag is used — the correction still applies."""
        errors = Errors()
        plan = _plan(["Day -7", "Day 1", "Day 0"], errors)
        assert plan.anchor == 1
        assert plan.nodes[0].duration == 7
        assert (
            "Timeline 1, column 'c3': Day 0 printed but the timeline numbers "
            "from Day 1 (day_zero false); the flag is used"
        ) in _messages(errors)

    def test_a_blank_column_does_not_count_as_day_zero(self):
        plan = _plan(["Day -7", None, "Day 1", "Day 8"])
        assert [n.duration for n in plan.nodes] == [7, 0, 0, 7]

    def test_no_correction_for_other_units(self):
        plan = _plan(["Week -2", "Week 1", "Week 4"])
        assert [n.duration for n in plan.nodes] == [3, 0, 3]

    def test_mixed_units_use_the_absolute_value_and_warn(self):
        errors = Errors()
        plan = _plan(["Day 1", "Week 2"], errors)
        assert _summary(plan)[1] == (AFTER, 2, "week")
        assert errors.count() > 0

    def test_a_column_with_no_parsed_timing_is_zero(self):
        plan = _plan(["Day 1", {"text": "Cycle 2 Day 1", "pattern": None}])
        assert _summary(plan)[1] == (AFTER, 0, "day")

    def test_an_anchor_with_no_value_gives_the_absolute_value(self):
        plan = _plan([None, "Day -3"])
        assert plan.anchor == 0
        assert _summary(plan)[1] == (AFTER, 3, "day")

    @pytest.mark.parametrize(
        "timings, expected",
        [
            (["Day -1", "Day 1"], [1, 0]),
            (["Day -42", "Day 1"], [42, 0]),
            (["Day 1", "Day 16"], [0, 15]),
        ],
    )
    def test_interval_examples(self, timings, expected):
        assert [n.duration for n in _plan(timings).nodes] == expected


class TestAnchorWarnings:
    """U4-2."""

    def test_no_column_at_or_after_zero_is_warned(self):
        errors = Errors()
        _plan(["Day -14", "Day -7"], errors)
        assert any(
            "no column has a timing of 0 or more" in m for m in _messages(errors)
        )

    def test_an_anchor_found_is_not_warned(self):
        errors = Errors()
        _plan(["Day -7", "Day 1"], errors)
        assert _messages(errors) == []

    def test_a_restart_outside_a_cycle_is_warned(self):
        errors = Errors()
        _plan(["Day 1", "Day 540", "Day 0"], errors, day_zero=True)
        (message,) = _messages(errors)
        assert "column 'c3': timing restarts (day 0 after day 540)" in message

    def test_a_restart_in_a_cycle_column_is_not_warned(self):
        errors = Errors()
        columns = [
            column(
                "c1",
                timing="Day 1",
                cycle=value("Cycle 1"),
                cycle_length=value("21 days"),
            ),
            column("c2", timing="Day 8", cycle=value("Cycle 1")),
            column("c3", timing="Day 1", cycle=value("Cycle 2")),
        ]
        Planner(errors).plan(parse_timeline(timeline(columns)))
        assert _messages(errors) == []

    def test_different_units_are_not_a_restart(self):
        errors = Errors()
        _plan(["Day 1", "Day 8", "Week 1"], errors)
        assert not any("restarts" in m for m in _messages(errors))


class TestNoReadableTiming:
    """U4-3: every instance timed — zero from the neighbour toward the anchor."""

    def test_after_the_anchor_is_after_the_previous_column(self):
        errors = Errors()
        plan = _plan(["Day 1", "Day 8", _text("ET")], errors)
        assert _links(plan)[2] == (AFTER, 1, 0)
        assert plan.nodes[2].timed is False
        assert (
            "column 'c3': no readable timing; a zero timing is used"
            in (_messages(errors)[-1])
        )

    def test_before_the_anchor_is_before_the_next_column(self):
        plan = _plan([None, _text("Screening"), "Day 1", "Day 8"])
        assert _links(plan) == [
            (BEFORE, 1, 0),
            (BEFORE, 2, 0),
            (FIXED, 2, 0),
            (AFTER, 2, 7),
        ]

    def test_nothing_timed_chains_from_the_first_column(self):
        errors = Errors()
        plan = _plan([None, _text("V2"), None], errors)
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 0), (AFTER, 1, 0)]
        messages = _messages(errors)
        assert any("the anchor is a zero timing" in m for m in messages)
        assert any("no column has a timing of 0 or more" in m for m in messages)


class TestTimeRange:
    """U4-4, U4-20: timed at the start, window forward to the end."""

    def _window(self, node):
        return (node.window.lower, node.window.upper, node.window.unit)

    def test_timed_at_its_start(self):
        plan = _plan(["Day -28 to Day -1", "Day 1"])
        assert _links(plan)[0] == (BEFORE, 1, 28)
        assert self._window(plan.nodes[0]) == (0, 27, "day")

    def test_crossing_zero_with_no_day_zero_loses_a_day(self):
        plan = _plan(["Day -3 to Day 2", "Day 8"])
        assert self._window(plan.nodes[0]) == (0, 4, "day")

    def test_crossing_zero_with_a_day_zero_does_not(self):
        plan = _plan(["Day -3 to Day 2", "Day 1"], day_zero=True)
        assert self._window(plan.nodes[0]) == (0, 5, "day")

    def test_other_units_never_lose_one(self):
        plan = _plan(["Week -1 to Week 2"])
        assert self._window(plan.nodes[0]) == (0, 3, "week")

    def test_a_time_range_can_be_the_anchor(self):
        plan = _plan(["Day -7", "Day 1 to Day 3", "Day 8"])
        assert plan.anchor == 1
        assert _links(plan) == [(BEFORE, 1, 7), (FIXED, 1, 0), (AFTER, 1, 7)]

    def test_a_window_field_is_kept(self):
        columns = [column("c1", timing="Day 1 to Day 3", window="-1..+1 days")]
        plan = Planner(Errors()).plan(parse_timeline(timeline(columns)))
        assert plan.nodes[0].window_from == "window"
        assert self._window(plan.nodes[0]) == (1, 1, "day")


def _cycle_column(id, timing, cycle=None, length=None):
    extra = {}
    if cycle is not None:
        extra["cycle"] = value(cycle)
    if length is not None:
        extra["cycle_length"] = value(length)
    return column(id, timing=timing, **extra)


def _cycle_plan(specs, errors=None):
    """``specs``: (timing, cycle, length) per column."""
    columns = [_cycle_column(f"c{i + 1}", *spec) for i, spec in enumerate(specs)]
    return Planner(errors or Errors()).plan(parse_timeline(timeline(columns)), 1)


def _marker_keys(plan):
    """Start markers only (U4-22) — not a range's decision or end node."""
    return [n.key for n in plan.nodes if n.column is None and n.kind is None]


def _day_one_at(plan, key) -> int:
    """A ``Day 1`` node's place on the timeline, in days from the anchor,
    by walking its chain of ``After`` links back to the anchor."""
    nodes = {n.key: n for n in plan.nodes}
    total = 0
    while key != plan.anchor:
        node = nodes[key]
        assert node.timing_type == AFTER
        total += node.duration
        key = node.relative_to
    return total


class TestSingleCycles:
    """Issue 66 — design § 6 R4.3, U4-23–U4-26; issue 67 — U4-22, U4-27."""

    def test_three_cycles_chain_from_each_day_one(self):
        errors = Errors()
        plan = _cycle_plan(
            [
                ("Day -28 to Day -1", None, None),
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 15", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2", "21 days"),
                ("Day 8", "Cycle 2", "21 days"),
                ("Day 15", "Cycle 2", "21 days"),
                ("Day 1", "Cycle 3", "21 days"),
                ("Day 8", "Cycle 3", "21 days"),
                ("Day 90", None, None),
            ],
            errors,
        )
        assert plan.anchor == 1
        assert _links(plan) == [
            (BEFORE, 1, 28),
            (FIXED, 1, 0),
            (AFTER, 1, 7),
            (AFTER, 1, 14),
            (AFTER, 1, 21),  # C1PAD: cycle 1's full length (U4-39)
            (AFTER, 1, 21),  # C2D1 from C1D1 by cycle 1's length
            (AFTER, 4, 7),  # C2D8 from C2D1
            (AFTER, 4, 14),
            (AFTER, 4, 21),  # C2PAD
            (AFTER, 4, 21),  # C3D1 from C2D1 by cycle 2's length
            (AFTER, 7, 7),
            (AFTER, 7, 21),  # C3PAD
            (AFTER, 1, 89),
        ]
        assert _messages(errors) == []

    def test_cycle_one_needs_no_length(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", None), ("Day 8", "Cycle 1", None)], errors
        )
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 7)]
        assert _messages(errors) == []

    def test_a_length_in_weeks_is_converted(self):
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "3 weeks"), ("Day 1", "Cycle 2", "3 weeks")]
        )
        assert _links(plan)[1:3] == [(AFTER, 0, 21), (AFTER, 0, 21)]

    def test_a_length_that_does_not_convert_is_a_zero_timing(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "1 months"), ("Day 1", "Cycle 2", "1 months")], errors
        )
        assert _links(plan)[1] == (AFTER, 0, 0)
        assert not plan.nodes[1].timed
        assert (
            "Timeline 1, cycle 2 Day 1: cycle 1's length 1 months does not convert "
            "exactly to days; a zero timing is used"
        ) in _messages(errors)

    def test_a_missing_length_is_a_zero_timing(self):
        """U4-23: the length that is missing is the PREVIOUS cycle's."""
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", None), ("Day 1", "Cycle 2", "21 days")], errors
        )
        assert _links(plan)[1] == (AFTER, 0, 0)
        assert not plan.nodes[1].timed
        assert plan.nodes[1].column.cycle_day.value == 1
        assert (
            "Timeline 1, cycle 2 Day 1: cycle 1 has no readable length; a zero "
            "timing is used"
        ) in _messages(errors)

    def test_a_cycles_own_length_does_not_place_its_day_one(self):
        """Must not fire: cycle 2's length is not used for cycle 2's Day 1."""
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 1", "Cycle 2", None)], errors
        )
        assert _links(plan)[2] == (AFTER, 0, 21)
        assert _messages(errors) == []

    def test_a_length_on_one_column_serves_the_cycle(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", None),
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2", None),
            ]
        )
        assert _links(plan) == [
            (FIXED, 0, 0),
            (AFTER, 0, 7),
            (AFTER, 0, 21),
            (AFTER, 0, 21),
        ]

    def test_a_second_length_in_a_cycle_is_warned(self):
        errors = Errors()
        _cycle_plan(
            [
                ("Day 1", "Cycle 1", None),
                ("Day 1", "Cycle 2", "21 days"),
                ("Day 8", "Cycle 2", "28 days"),
            ],
            errors,
        )
        assert any(
            "cycle 2 prints a second length (28 days); the first is used" in m
            for m in _messages(errors)
        )

    def test_a_negative_day_is_one_before_day_one(self):
        """U4-24."""
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day -1", "Cycle 2", "21 days"),
                ("Day 1", "Cycle 2", "21 days"),
            ]
        )
        assert _links(plan) == [
            (FIXED, 0, 0),
            (AFTER, 0, 21),
            (BEFORE, 2, 1),
            (AFTER, 0, 21),
            (AFTER, 2, 21),
        ]
        assert _marker_keys(plan) == []

    def test_a_negative_day_with_no_day_one_is_before_the_marker(self):
        """U4-22, U4-24."""
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day -1", "Cycle 2", "21 days")]
        )
        assert _links(plan) == [
            (FIXED, 0, 0),
            (AFTER, 0, 21),
            (AFTER, 0, 21),
            (BEFORE, "C2D1", 1),
            (AFTER, "C2D1", 21),
        ]

    def test_the_day_is_read_from_timing_only(self):
        """U4-26: a day printed in the visit row is not read, and a cycle with
        no readable day gets no start marker."""
        columns = [
            column("c1", visit="D1", cycle=value("Cycle 1")),
            column("c2", visit="D8", cycle=value("Cycle 1")),
        ]
        plan = Planner(Errors()).plan(parse_timeline(timeline(columns)), 1)
        assert [n.timed for n in plan.nodes] == [False, False]
        assert _marker_keys(plan) == []

    def test_a_length_in_days_converts_to_weeks_only_when_exact(self):
        errors = Errors()
        plan = _cycle_plan(
            [
                ("Week 1", "Cycle 1", "14 days"),
                ("Week 1", "Cycle 2", "15 days"),
                ("Week 1", "Cycle 3", "14 days"),
            ],
            errors,
        )
        assert _links(plan)[:3] == [(FIXED, 0, 0), (AFTER, 0, 2), (AFTER, 0, 2)]
        assert plan.nodes[2].unit == "week"
        assert not plan.nodes[3].timed
        assert any("does not convert exactly to weeks" in m for m in _messages(errors))
        assert _marker_keys(plan) == []

    def test_a_non_cycle_anchor(self):
        plan = _cycle_plan(
            [
                ("Day 1", None, None),
                ("Day 1", "Cycle 1", None),
                ("Day 8", "Cycle 1", None),
            ]
        )
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 0), (AFTER, 1, 7)]

    def test_an_anchor_with_no_timing(self):
        columns = [
            column("c1", visit="V1"),
            _cycle_column("c2", "Day -1", "Cycle 1", "21 days"),
        ]
        plan = Planner(Errors()).plan(parse_timeline(timeline(columns)), 1)
        assert plan.anchor == 0
        assert _links(plan)[1:] == [
            (AFTER, 0, 1),
            (BEFORE, "C1D1", 1),
            (AFTER, "C1D1", 21),
        ]

    def test_a_unit_other_than_the_anchor_is_warned(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Week 0", None, None), ("Day 8", "Cycle 1", "21 days")], errors
        )
        assert _links(plan)[1:] == [
            (AFTER, 0, 1),
            (AFTER, "C1D1", 7),
            (AFTER, "C1D1", 21),
        ]
        assert any(
            "cycle 1 Day 1: timing unit 'day' differs from anchor unit 'week'; "
            "using 1" in m
            for m in _messages(errors)
        )


class TestCycleDayOne:
    """Issue 67. Every cycle has a ``Day 1`` node — its printed ``Day 1``
    column, else a start marker (U4-22) — and cycle n's ``Day 1`` is timed
    from cycle n - 1's by cycle n - 1's length (U4-27)."""

    def test_cycles_of_different_lengths(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2", "28 days"),
                ("Day 1", "Cycle 3", "28 days"),
            ]
        )
        assert _links(plan) == [
            (FIXED, 0, 0),
            (AFTER, 0, 21),
            (AFTER, 0, 21),
            (AFTER, 1, 28),
            (AFTER, 1, 28),
            (AFTER, 2, 28),
        ]
        assert _day_one_at(plan, 2) == 49

    def test_equal_lengths_keep_every_day_one_where_it_was(self):
        """Must not move: with equal lengths each Day 1 lands where the old
        (n - 1) x length rule put it; only its reference changes."""
        specs = [
            (f"Day {d}", f"Cycle {n}", "21 days") for n in (1, 2, 3, 4) for d in (1, 8)
        ]
        plan = _cycle_plan(specs)
        day_ones = [
            n.key for n in plan.nodes if n.column and n.column.cycle_day.value == 1
        ]
        assert [_day_one_at(plan, k) for k in day_ones] == [0, 21, 42, 63]
        assert _marker_keys(plan) == []

    def test_a_printed_day_one_gets_no_marker(self):
        errors = Errors()
        plan = _cycle_plan(
            [
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 15", "Cycle 1", "21 days"),
            ],
            errors,
        )
        assert _marker_keys(plan) == []
        assert [n.key for n in plan.nodes] == [0, 1, 2, "C1PAD"]
        assert not any("start marker" in m for m in _messages(errors))

    def test_no_cycles_no_markers(self):
        plan = _plan(["Day -7", "Day 1", "Day 8", "Day 15"])
        assert _marker_keys(plan) == []

    def test_a_cycle_with_no_day_one_gets_a_marker_before_its_first_column(self):
        errors = Errors()
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 8", "Cycle 2", "21 days"),
                ("Day 15", "Cycle 2", "21 days"),
            ],
            errors,
        )
        assert [n.key for n in plan.nodes] == [0, 1, "C1PAD", "C2D1", 2, 3, "C2PAD"]
        marker = plan.nodes[3]
        assert (marker.cycle, marker.epoch_column) == (2, 2)
        assert _links(plan)[3:] == [
            (AFTER, 0, 21),
            (AFTER, "C2D1", 7),
            (AFTER, "C2D1", 14),
            (AFTER, "C2D1", 21),
        ]
        assert (
            "Timeline 1, cycle 2: no Day 1 column is printed; a start marker C2D1 "
            "is added"
        ) in _messages(errors)

    def test_the_marker_is_the_anchor_when_the_anchor_falls_in_its_cycle(self):
        plan = _cycle_plan(
            [
                ("Day -28 to Day -1", None, None),
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 15", "Cycle 1", "21 days"),
                ("Day 90", None, None),
            ]
        )
        assert plan.anchor == "C1D1"
        assert [n.key for n in plan.nodes] == [0, "C1D1", 1, 2, "C1PAD", 3]
        assert _links(plan) == [
            (BEFORE, "C1D1", 28),
            (FIXED, "C1D1", 0),
            (AFTER, "C1D1", 7),
            (AFTER, "C1D1", 14),
            (AFTER, "C1D1", 21),
            (AFTER, "C1D1", 89),
        ]

    def test_a_previous_cycle_not_in_the_timeline_is_a_zero_timing(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 8", "Cycle 3", "21 days")], errors
        )
        assert _links(plan) == [
            (FIXED, 0, 0),
            (AFTER, 0, 21),
            (AFTER, 0, 0),
            (AFTER, "C3D1", 7),
            (AFTER, "C3D1", 21),
        ]
        assert not plan.nodes[2].timed
        assert (
            "Timeline 1, cycle 3 Day 1: cycle 2 is not in the timeline; a zero timing "
            "is used"
        ) in _messages(errors)

    def test_a_marker_chains_to_the_next_cycle(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 8", "Cycle 2", "28 days"),
                ("Day 1", "Cycle 3", "21 days"),
            ]
        )
        assert _links(plan) == [
            (FIXED, 0, 0),
            (AFTER, 0, 21),
            (AFTER, 0, 21),
            (AFTER, "C2D1", 7),
            (AFTER, "C2D1", 28),
            (AFTER, "C2D1", 28),
            (AFTER, 2, 21),
        ]
        assert _day_one_at(plan, 2) == 49


class TestNct02107703Headers:
    """Issue 68: NCT02107703's cycle headers. Since issue 73 the caller
    structures them (U4-35): ``≤28`` → a range, ``15±3`` → a timing and a
    window, ``2-3`` → cycles 2 to 3, ``4 and Beyond`` → cycle 4 open-ended,
    the bare ``28`` → 28 days from the row label."""

    ROWS = {
        "cycle": "Cycle",
        "cycle_length": "Approximate Duration (days)",
        "timing": "Relative day within a cycle",
    }

    def _parsed(self, errors):
        def col(id, cycle, timing, window=None):
            data = {"id": id, "timing": timing}
            if cycle:
                data["cycle"] = cycle
                data["cycle_length"] = {"text": "28", "value": 28, "unit": "days"}
            if window:
                data["window"] = window
            return data

        day_1 = {"text": "1", "value": 1, "unit": "days"}
        columns = [
            col("c1", None, {"text": "≤28", "start": -28, "end": -1, "unit": "days"}),
            col("c2", {"text": "1", "first": 1, "last": 1}, day_1),
            col(
                "c3",
                {"text": "1", "first": 1, "last": 1},
                {"text": "15±3", "value": 15, "unit": "days"},
                {"text": "", "before": 3, "after": 3, "unit": "days"},
            ),
            col("c4", {"text": "2-3", "first": 2, "last": 3}, day_1),
            col("c5", {"text": "4 and Beyond (if Applicable)", "first": 4}, day_1),
        ]
        return parse_timeline(timeline(columns, rows=self.ROWS), errors, 1)

    def test_the_ranges_are_timed_and_loop(self):
        """Issue 69: ``2-3`` is timed from cycle 1's Day 1, ``4 and Beyond``
        from the ``2-3`` range (it covers cycle 3); each is a loop (U4-39), and
        the last range has an end node."""
        errors = Errors()
        plan = Planner(errors).plan(self._parsed(errors), 1)
        keys = [n.key for n in plan.nodes]
        assert keys == [
            0,
            1,
            2,
            "C1PAD",
            "C2ENTRY",
            3,
            "C2PAD",
            "C2DEC",
            "C4ENTRY",
            4,
            "C4PAD",
            "C4DEC",
            "C4END",
        ]
        nodes = {n.key: n for n in plan.nodes}
        entry = nodes["C2ENTRY"]
        assert (entry.timing_type, entry.relative_to, entry.duration) == (
            AFTER,
            1,
            28,
        )
        assert (nodes["C4ENTRY"].relative_to, nodes["C4ENTRY"].duration) == (3, 28)
        assert nodes["C2DEC"].loop_to == 3 and nodes["C4DEC"].loop_to == 4
        assert (nodes["C2PAD"].relative_to, nodes["C2PAD"].duration) == (3, 28)
        assert (nodes["C4END"].relative_to, nodes["C4END"].duration) == ("C4PAD", 0)
        assert [m for m in _messages(errors) if "cycle" in m] == []


class TestRanges:
    """Issue 69 (R5): cycle ranges. Issue 95 (U4-39): a range is a loop —
    an entry, its days, a pad and an untimed decision."""

    def test_the_entry_is_timed_from_the_previous_cycle(self):
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 1", "Cycle 2+", "21 days")]
        )
        nodes = {n.key: n for n in plan.nodes}
        entry = nodes["C2ENTRY"]
        assert (entry.kind, entry.cycle, entry.epoch_column) == (ENTRY, 2, 1)
        assert (entry.timing_type, entry.relative_to, entry.duration) == (
            AFTER,
            0,
            21,
        )
        assert entry.timed

    def test_day_one_is_zero_after_the_entry(self):
        """Pattern B: a pass that loops back is not timed again from outside."""
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 1", "Cycle 2+", "21 days")]
        )
        nodes = {n.key: n for n in plan.nodes}
        assert (nodes[1].timing_type, nodes[1].relative_to, nodes[1].duration) == (
            AFTER,
            "C2ENTRY",
            0,
        )

    def test_pad_after_day_one_by_the_length(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "28 days"),
                ("Day 1", "Cycle 2+", "28 days"),
                ("Day 15", "Cycle 2+", "28 days"),
            ]
        )
        assert [n.key for n in plan.nodes] == [
            0,
            "C1PAD",
            "C2ENTRY",
            1,
            2,
            "C2PAD",
            "C2DEC",
            "C2END",
        ]
        pad = plan.nodes[5]
        assert (pad.kind, pad.cycle, pad.epoch_column) == (PAD, 2, 2)
        assert (pad.timing_type, pad.relative_to, pad.duration) == (AFTER, 1, 28)
        assert pad.timed

    def test_the_decision_has_no_timing_and_loops_back(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "28 days"),
                ("Day 1", "Cycle 2+", "28 days"),
                ("Day 15", "Cycle 2+", "28 days"),
            ]
        )
        decision = plan.nodes[6]
        assert decision.kind == DECISION and decision.key == "C2DEC"
        assert (decision.timing_type, decision.relative_to) == (None, None)
        assert decision.loop_to == 1 and decision.epoch_column == 2

    def test_end_node_only_when_the_range_is_last(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2-4", "21 days"),
                ("Day 30", None, None),
            ]
        )
        assert [n.key for n in plan.nodes] == [
            0,
            "C1PAD",
            "C2ENTRY",
            1,
            "C2PAD",
            "C2DEC",
            2,
        ]
        last = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 1", "Cycle 2-4", "21 days")]
        )
        end = last.nodes[-1]
        assert (end.kind, end.key, end.relative_to, end.duration) == (
            END,
            "C2END",
            "C2PAD",
            0,
        )

    def test_a_range_with_no_day_1_loops_to_its_marker(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 8", "Cycle 2+", "21 days"),
            ]
        )
        assert [n.key for n in plan.nodes] == [
            0,
            "C1PAD",
            "C2ENTRY",
            "C2D1",
            1,
            "C2PAD",
            "C2DEC",
            "C2END",
        ]
        nodes = {n.key: n for n in plan.nodes}
        assert nodes["C2DEC"].loop_to == "C2D1"
        assert (nodes["C2D1"].relative_to, nodes["C2D1"].duration) == ("C2ENTRY", 0)
        assert (nodes["C2PAD"].relative_to, nodes["C2PAD"].duration) == ("C2D1", 21)

    def test_a_range_that_is_the_anchor_moves_it_to_the_entry(self):
        plan = _cycle_plan(
            [("Day 1", "Cycle 1+", "28 days"), ("Day 15", "Cycle 1+", "28 days")]
        )
        assert plan.anchor == "C1ENTRY" and plan.anchors == ["C1ENTRY"]
        assert _links(plan)[:3] == [
            (FIXED, "C1ENTRY", 0),
            (AFTER, "C1ENTRY", 0),
            (AFTER, 0, 14),
        ]

    def test_no_length_takes_the_largest_day(self):
        """U4-8: Day 1, Day 8, Day 15 → a 15-day cycle; the pad is on Day 15."""
        errors = Errors()
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "28 days"),
                ("Day 1", "Cycle 2+", None),
                ("Day 8", "Cycle 2+", None),
                ("Day 15", "Cycle 2+", None),
            ],
            errors,
        )
        nodes = {n.key: n for n in plan.nodes}
        assert (nodes["C2PAD"].relative_to, nodes["C2PAD"].duration) == (1, 15)
        assert (
            "Timeline 1, cycle 2: the range has no readable length; the largest "
            "day printed in it is used (15 days)"
        ) in _messages(errors)

    def test_no_length_and_no_positive_day_is_a_zero_delay(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "28 days"), ("Day -1", "Cycle 2+", None)], errors
        )
        pad = plan.nodes[-3]
        assert (pad.key, pad.relative_to, pad.duration, pad.timed) == (
            "C2PAD",
            1,
            0,
            False,
        )
        assert (
            "Timeline 1, cycle 2 pad: the range has no readable length; a zero "
            "delay is used"
        ) in _messages(errors)

    def test_a_length_that_does_not_convert_is_a_zero_delay(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Week 1", "Cycle 1", "2 weeks"), ("Week 1", "Cycle 2+", "10 days")],
            errors,
        )
        assert plan.nodes[-3].key == "C2PAD" and plan.nodes[-3].duration == 0
        assert (
            "Timeline 1, cycle 2 pad: the range's length 10 days does not "
            "convert exactly to weeks; a zero delay is used"
        ) in _messages(errors)

    def test_a_last_day_beyond_the_length_is_a_zero_delay(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 29", "Cycle 2+", "21 days")],
            errors,
        )
        assert plan.nodes[-3].key == "C2PAD" and plan.nodes[-3].duration == 0
        assert (
            "Timeline 1, cycle 2 pad: the last day (29) is beyond the length "
            "(21 days); a zero delay is used"
        ) in _messages(errors)

    def test_the_largest_day_ignores_other_units(self):
        errors = Errors()
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "28 days"),
                ("Day 1", "Cycle 2+", None),
                ("Week 3", "Cycle 2+", None),
                ("Day 8", "Cycle 2+", None),
            ],
            errors,
        )
        assert "largest day printed in it is used (8 days)" in _messages(errors)[0]
        assert plan.nodes[3].key == 1


class TestSingleCyclePad:
    """Issue 95 (U4-39): a single cycle gets a pad so it has its full
    length; it does not loop — no entry, no decision."""

    def test_a_pad_after_the_cycles_last_column(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", "21 days"),
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2", "21 days"),
            ]
        )
        assert [n.key for n in plan.nodes] == [0, 1, "C1PAD", 2, "C2PAD"]
        pad = plan.nodes[2]
        assert (pad.kind, pad.cycle, pad.epoch_column) == (PAD, 1, 1)
        assert (pad.timing_type, pad.relative_to, pad.duration) == (AFTER, 0, 21)
        assert not any(n.kind in (ENTRY, DECISION) for n in plan.nodes)

    def test_no_length_no_pad(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", None), ("Day 8", "Cycle 1", None)], errors
        )
        assert not any(n.kind == PAD for n in plan.nodes)
        assert _messages(errors) == []

    def test_a_length_that_does_not_convert_no_pad(self):
        plan = _cycle_plan([("Day 1", "Cycle 1", "1 months")])
        assert not any(n.kind == PAD for n in plan.nodes)

    def test_a_last_day_beyond_the_length_no_pad(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 29", "Cycle 1", "21 days")],
            errors,
        )
        assert not any(n.kind == PAD for n in plan.nodes)
        assert _messages(errors) == []


# ----------------------------------------------------------------------
# Gates — issue 74 (R8, U4-10, U4-36)


def _gated(timings: list, errors: Errors | None = None, **extra):
    """Columns in compact notation; a ``("delay", "7 to 28 days")`` entry is a
    gate column."""
    columns = []
    for i, t in enumerate(timings):
        if isinstance(t, tuple) and t[0] == "delay":
            columns.append(column(f"c{i + 1}", visit="Washout", delay=value(t[1])))
        else:
            columns.append(column(f"c{i + 1}", timing=t))
    parsed = parse_timeline(timeline(columns, **extra))
    return Planner(errors or Errors()).plan(parsed, 1)


class TestGates:
    WASHOUT = ("delay", "7 to 28 days")

    def test_entry_gate_pad_decision_and_loop(self):
        """U4-10 (a), U4-39."""
        plan = _gated(["Day 1", "Day 2", self.WASHOUT, "Day 1", "Day 2"])
        entry, gate, pad, decision = plan.nodes[2:6]
        assert (entry.kind, entry.gate, entry.key) == (ENTRY, 1, "G1ENTRY")
        assert (entry.timing_type, entry.relative_to, entry.duration) == (AFTER, 1, 0)
        assert (gate.kind, gate.gate, gate.key) == (GATE, 1, 2)
        assert (gate.timing_type, gate.relative_to, gate.duration) == (
            AFTER,
            "G1ENTRY",
            0,
        )
        assert (pad.kind, pad.gate, pad.key) == (PAD, 1, "G1PAD")
        assert (pad.timing_type, pad.relative_to, pad.duration, pad.unit) == (
            AFTER,
            2,
            1,
            "day",
        )
        assert (decision.kind, decision.gate, decision.key) == (DECISION, 1, "G1DEC")
        assert (decision.timing_type, decision.relative_to) == (None, None)
        assert (decision.loop_to, decision.epoch_column) == (2, 2)

    def test_the_period_after_a_gate_has_its_own_anchor(self):
        plan = _gated(["Day -1", "Day 1", "Day 2", self.WASHOUT, "Day -1", "Day 1"])
        assert plan.anchor == 1
        assert plan.anchors == [1, 5]
        assert _links(plan)[7:] == [(BEFORE, 5, 1), (FIXED, 5, 0)]

    def test_no_timing_links_the_second_period_to_the_first(self):
        plan = _gated(["Day 1", "Day 8", self.WASHOUT, "Day 1", "Day 8"])
        second = [n for n in plan.nodes if n.column and n.column.index > 2]
        assert {n.relative_to for n in second} == {3}

    def test_no_timing_before_the_new_anchor_is_before_the_next_column(self):
        plan = _gated(["Day 1", self.WASHOUT, _text("Baseline PET"), "Day -1", "Day 1"])
        assert _links(plan)[5:] == [(BEFORE, 3, 0), (BEFORE, 4, 1), (FIXED, 4, 0)]

    def test_a_restart_after_a_gate_is_not_warned(self):
        errors = Errors()
        _gated(["Day 1", "Day 8", self.WASHOUT, "Day 1", "Day 8"], errors)
        assert not any("restarts" in m for m in _messages(errors))

    def test_a_restart_with_no_gate_is_warned(self):
        errors = Errors()
        _gated(["Day 1", "Day 8", "Day 1"], errors)
        assert (
            "Timeline 1, column 'c3': timing restarts (day 1 after day 8) with no "
            "gate before it"
        ) in _messages(errors)

    def test_a_period_with_no_anchor_is_warned_by_number(self):
        errors = Errors()
        plan = _gated(["Day 1", self.WASHOUT, "Day -7", "Day -1"], errors)
        assert plan.anchors == [0, 2]
        assert (
            "Timeline 1, period 2: no column has a timing of 0 or more; the first "
            "column is the anchor"
        ) in _messages(errors)

    def test_a_gate_as_the_last_column_has_an_end_node(self):
        plan = _gated(["Day 1", self.WASHOUT])
        assert [n.kind for n in plan.nodes] == [None, ENTRY, GATE, PAD, DECISION, END]
        end = plan.nodes[5]
        assert (end.key, end.relative_to, end.duration, end.gate) == (
            "G1END",
            "G1PAD",
            0,
            1,
        )

    def test_a_gate_as_the_first_column_is_the_anchor_warned(self):
        errors = Errors()
        plan = _gated([self.WASHOUT, "Day 1"], errors)
        assert _links(plan)[:2] == [(FIXED, "G1ENTRY", 0), (AFTER, "G1ENTRY", 0)]
        assert (
            "Timeline 1, column 'c1': a gate with no column before it; it is the anchor"
        ) in _messages(errors)

    def test_two_gates_three_periods(self):
        plan = _gated(["Day 1", self.WASHOUT, "Day 1", ("delay", "3+ days"), "Day 1"])
        assert plan.anchors == [0, 2, 4]
        assert [n.key for n in plan.nodes if n.kind == DECISION] == [
            "G1DEC",
            "G2DEC",
        ]

    def test_only_a_gate(self):
        plan = _gated([self.WASHOUT])
        assert [n.kind for n in plan.nodes] == [ENTRY, GATE, PAD, DECISION, END]
        assert plan.anchors == [0]

    def test_a_text_only_delay_is_not_a_gate(self):
        errors = Errors()
        columns = [
            column("c1", timing="Day 1"),
            column("c2", visit="Washout", delay=_text("7-28 days")),
            column("c3", timing="Day 8"),
        ]
        plan = Planner(errors).plan(parse_timeline(timeline(columns)), 1)
        assert [n.kind for n in plan.nodes] == [None, None, None]
        assert _links(plan)[1] == (AFTER, 0, 0)

    def test_no_gate_one_anchor(self):
        plan = _gated(["Day -1", "Day 1"])
        assert plan.anchors == [1]

    def test_no_columns(self):
        plan = Planner(Errors()).plan(parse_timeline(timeline([])), 1)
        assert (plan.anchor, plan.nodes, plan.anchors) == (0, [], [])

    def test_a_gate_column_is_not_a_cycle_loop(self):
        """A gate and a cycle range in one timeline: each gets its decision."""
        columns = [
            column(
                "c1",
                timing="Day 1",
                cycle=value("Cycle 1"),
                cycle_length=value("21 days"),
            ),
            column("c2", timing="Day 1", cycle=value("Cycle 2+")),
            column("c3", visit="Washout", delay=value("7 to 28 days")),
            column("c4", timing="Day 1"),
        ]
        plan = Planner(Errors()).plan(parse_timeline(timeline(columns)), 1)
        assert [n.key for n in plan.nodes if n.kind == DECISION] == [
            "C2DEC",
            "G1DEC",
        ]


class TestTimingFromAColumn:
    """Issue 91: a timing measured from a named column is an ``After`` delay
    from that column's instance, whatever the anchor."""

    @staticmethod
    def _from(value, source, unit="days", text=None):
        return {
            "text": text or f"{value} {unit} after {source}",
            "value": value,
            "unit": unit,
            "from": source,
        }

    def _plan(self, columns, errors=None):
        return Planner(errors or Errors()).plan(parse_timeline(timeline(columns)), 1)

    def test_delay_after_the_named_column(self):
        plan = self._plan(
            [
                column("c1", timing="Day 1"),
                column("c2", timing="Day 8"),
                column("c3", timing=self._from(30, "c2")),
            ]
        )
        assert _links(plan)[2] == (AFTER, 1, 30)
        assert plan.nodes[2].unit == "day"
        assert plan.nodes[2].timed is True

    def test_from_a_column_before_the_anchor(self):
        plan = self._plan(
            [
                column("c1", timing="Day -7"),
                column("c2", timing="Day 1"),
                column("c3", timing=self._from(2, "c1", unit="weeks")),
            ]
        )
        assert plan.anchor == 1
        assert _links(plan)[2] == (AFTER, 0, 2)
        assert plan.nodes[2].unit == "week"

    def test_either_of_two_visits_is_two_columns(self):
        plan = self._plan(
            [
                column("c1", timing="Day 1"),
                column("eot", timing="Day 85"),
                column("ed", visit="ED"),
                column("fu1", timing=self._from(30, "eot")),
                column("fu2", timing=self._from(30, "ed")),
            ]
        )
        assert _links(plan)[3] == (AFTER, 1, 30)
        assert _links(plan)[4] == (AFTER, 2, 30)

    def test_window_is_kept(self):
        columns = [
            column("c1", timing="Day 1"),
            column("c2", timing=self._from(30, "c1"), window="-7..+7 days"),
        ]
        plan = self._plan(columns)
        assert plan.nodes[1].window is not None
        assert (plan.nodes[1].window.lower, plan.nodes[1].window.upper) == (7, 7)

    def test_label_keeps_the_printed_text(self):
        parsed = parse_timeline(
            timeline(
                [
                    column("c1", timing="Day 1"),
                    column(
                        "c2",
                        timing=self._from(30, "c1", text="30 days after last dose"),
                    ),
                ]
            )
        )
        assert parsed.columns[1].timing_label == "30 days after last dose"
        assert parsed.columns[1].timing is None

    # must not fire

    def test_a_delay_column_is_never_the_anchor(self):
        plan = self._plan(
            [column("c1", timing=self._from(5, "c2")), column("c2", timing="Day 1")]
        )
        assert plan.anchor == 1

    def test_a_timing_without_from_is_unchanged(self):
        plan = self._plan([column("c1", timing="Day 1"), column("c2", timing="Day 31")])
        assert _links(plan)[1] == (AFTER, 0, 30)

    def test_untimed_column_is_still_zero_from_its_neighbour(self):
        plan = self._plan(
            [
                column("c1", timing="Day 1"),
                column("c2", timing=self._from(30, "c1")),
                column("c3", visit="ET"),
            ]
        )
        assert _links(plan)[2] == (AFTER, 1, 0)

    def test_no_warning_for_a_resolved_delay(self):
        errors = Errors()
        self._plan(
            [column("c1", timing="Day 1"), column("c2", timing=self._from(30, "c1"))],
            errors,
        )
        assert _messages(errors) == []


class TestTimingFromTheStart:
    """Issue 92: a first column timed from the timeline's start is a delay
    from a start node of its own, not the anchor."""

    @staticmethod
    def _start(value, unit="days", text=None):
        return {
            "text": text or f"{value} {unit} after last dose",
            "value": value,
            "unit": unit,
            "from": "start",
        }

    def _plan(self, columns, errors=None):
        return Planner(errors or Errors()).plan(
            parse_timeline(timeline(columns, type="follow_up")), 1
        )

    def test_start_node_then_the_delay(self):
        plan = self._plan([column("fu", timing=self._start(30))])
        start, visit = plan.nodes
        assert start.column is None and start.kind == START
        assert (start.timing_type, start.relative_to, start.duration) == (
            FIXED,
            START_KEY,
            0,
        )
        assert (visit.timing_type, visit.relative_to, visit.duration) == (
            AFTER,
            START_KEY,
            30,
        )
        assert plan.anchor == START_KEY

    def test_later_columns_follow_as_now(self):
        plan = self._plan(
            [column("fu1", timing=self._start(30)), column("fu2", visit="FU2")]
        )
        assert _links(plan)[2] == (AFTER, 0, 0)

    def test_a_later_delay_from_the_first_visit(self):
        plan = self._plan(
            [
                column("fu1", timing=self._start(30)),
                column(
                    "fu2",
                    timing={
                        "text": "90 days",
                        "value": 60,
                        "unit": "days",
                        "from": "fu1",
                    },
                ),
            ]
        )
        assert _links(plan)[2] == (AFTER, 0, 60)

    def test_with_a_timed_column_the_start_is_zero_before_the_anchor(self):
        plan = self._plan(
            [column("fu", timing=self._start(30)), column("d1", timing="Day 1")]
        )
        assert plan.anchor == 1
        assert (plan.nodes[0].timing_type, plan.nodes[0].relative_to) == (BEFORE, 1)
        assert _links(plan)[1] == (AFTER, START_KEY, 30)

    def test_no_anchor_warning(self):
        errors = Errors()
        self._plan([column("fu", timing=self._start(30))], errors)
        assert _messages(errors) == []

    # must not fire

    def test_a_first_column_without_from_start_has_no_start_node(self):
        plan = self._plan([column("c1", timing="Day 1"), column("c2", timing="Day 8")])
        assert all(n.kind != START for n in plan.nodes)

    def test_a_delay_from_a_column_has_no_start_node(self):
        plan = self._plan(
            [
                column("c1", timing="Day 1"),
                column(
                    "c2", timing={"text": "x", "value": 5, "unit": "days", "from": "c1"}
                ),
            ]
        )
        assert all(n.kind != START for n in plan.nodes)
