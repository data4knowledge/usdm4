"""Plan — issue 63, part 63.6; issue 65; issue 66 (single cycles).

The straight chain and its one anchor: anchor choice, the crossing-zero rule,
mixed units (kept from before the restructure); and from issue 65 the U4-2
warnings, the zero-timing chain for columns with no readable timing (U4-3),
``≤N`` (U4-18) and time ranges (U4-4, U4-20).
"""

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.columns import parse_timeline
from src.usdm4.assembler.timeline.plan import AFTER, BEFORE, FIXED, Planner
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

    def test_no_correction_when_the_table_has_a_day_zero(self):
        plan = _plan(["Day -7", "Day 0", "Day 7"])
        assert [n.duration for n in plan.nodes] == [7, 0, 7]

    def test_a_day_zero_anywhere_stops_the_correction(self):
        """The anchor is the first non-negative column, so a Day 0 printed
        after it still says the table counts from zero."""
        plan = _plan(["Day -7", "Day 1", "Day 0"])
        assert plan.anchor == 1
        assert plan.nodes[0].duration == 8

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
        _plan(["Day 1", "Day 540", "Day 0"], errors)
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


class TestUpTo:
    """U4-18: ``≤N`` is read only before the anchor."""

    def test_before_the_anchor_is_a_time_range(self):
        plan = _plan([_text("≤42"), _text("≤21"), "Day 1"], rows={"timing": "Days"})
        first = plan.nodes[0]
        assert (first.column.time_range.start, first.column.time_range.end) == (
            -42,
            -1,
        )
        assert _links(plan)[:2] == [(BEFORE, 2, 42), (BEFORE, 2, 21)]
        assert (first.window.lower, first.window.upper) == (0, 41)
        assert first.window_from == "range"

    def test_after_the_anchor_is_not_read(self):
        errors = Errors()
        plan = _plan(["Day 1", _text("≤30")], errors, rows={"timing": "Days"})
        assert _links(plan)[1] == (AFTER, 0, 0)
        assert any(
            "'≤30' is read only before the anchor" in m for m in _messages(errors)
        )


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
        plan = _plan(["Day -3 to Day 2", "Day 0"])
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
    return [n.key for n in plan.nodes if n.column is None]


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
            (AFTER, 1, 21),  # C2D1 from C1D1 by cycle 1's length
            (AFTER, 4, 7),  # C2D8 from C2D1
            (AFTER, 4, 14),
            (AFTER, 4, 21),  # C3D1 from C2D1 by cycle 2's length
            (AFTER, 7, 7),
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
        assert _links(plan)[1] == (AFTER, 0, 21)

    def test_a_length_that_does_not_convert_is_a_zero_timing(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "1 month"), ("Day 1", "Cycle 2", "1 month")], errors
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
        assert _links(plan)[1] == (AFTER, 0, 21)
        assert _messages(errors) == []

    def test_a_length_on_one_column_serves_the_cycle(self):
        plan = _cycle_plan(
            [
                ("Day 1", "Cycle 1", None),
                ("Day 8", "Cycle 1", "21 days"),
                ("Day 1", "Cycle 2", None),
            ]
        )
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 7), (AFTER, 0, 21)]

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
        assert _links(plan) == [(FIXED, 0, 0), (BEFORE, 2, 1), (AFTER, 0, 21)]
        assert _marker_keys(plan) == []

    def test_a_negative_day_with_no_day_one_is_before_the_marker(self):
        """U4-22, U4-24."""
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day -1", "Cycle 2", "21 days")]
        )
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 21), (BEFORE, "C2D1", 1)]

    def test_a_range_column_is_a_zero_timing(self):
        """U4-25. A range is R5's; it gets no start marker."""
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 1", "Cycle 2+", "21 days")], errors
        )
        assert _links(plan)[1] == (AFTER, 0, 0)
        assert not plan.nodes[1].timed
        assert _marker_keys(plan) == []
        assert (
            "Timeline 1, column 'c2': cycle ranges are timed with R5; a zero timing "
            "is used"
        ) in _messages(errors)

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
        assert _links(plan)[:2] == [(FIXED, 0, 0), (AFTER, 0, 2)]
        assert plan.nodes[1].unit == "week"
        assert not plan.nodes[2].timed
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
        assert _links(plan)[1:] == [(AFTER, 0, 1), (BEFORE, "C1D1", 1)]

    def test_a_unit_other_than_the_anchor_is_warned(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Week 0", None, None), ("Day 8", "Cycle 1", "21 days")], errors
        )
        assert _links(plan)[1:] == [(AFTER, 0, 1), (AFTER, "C1D1", 7)]
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
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 21), (AFTER, 1, 28)]
        assert _day_one_at(plan, 2) == 49

    def test_equal_lengths_keep_every_day_one_where_it_was(self):
        """Must not move: with equal lengths each Day 1 lands where the old
        (n - 1) x length rule put it; only its reference changes."""
        specs = [
            (f"Day {d}", f"Cycle {n}", "21 days") for n in (1, 2, 3, 4) for d in (1, 8)
        ]
        plan = _cycle_plan(specs)
        day_ones = [n.key for n in plan.nodes if n.column.cycle_day.value == 1]
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
        assert len(plan.nodes) == 3
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
        assert [n.key for n in plan.nodes] == [0, 1, "C2D1", 2, 3]
        marker = plan.nodes[2]
        assert (marker.cycle, marker.epoch_column) == (2, 2)
        assert _links(plan)[2:] == [
            (AFTER, 0, 21),
            (AFTER, "C2D1", 7),
            (AFTER, "C2D1", 14),
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
        assert [n.key for n in plan.nodes] == [0, "C1D1", 1, 2, 3]
        assert _links(plan) == [
            (BEFORE, "C1D1", 28),
            (FIXED, "C1D1", 0),
            (AFTER, "C1D1", 7),
            (AFTER, "C1D1", 14),
            (AFTER, "C1D1", 89),
        ]

    def test_a_previous_cycle_not_in_the_timeline_is_a_zero_timing(self):
        errors = Errors()
        plan = _cycle_plan(
            [("Day 1", "Cycle 1", "21 days"), ("Day 8", "Cycle 3", "21 days")], errors
        )
        assert _links(plan) == [(FIXED, 0, 0), (AFTER, 0, 0), (AFTER, "C3D1", 7)]
        assert not plan.nodes[1].timed
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
            (AFTER, "C2D1", 7),
            (AFTER, "C2D1", 28),
        ]
        assert _day_one_at(plan, 2) == 49
