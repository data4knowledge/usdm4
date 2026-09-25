"""Plan — issue 63, part 63.6; issue 65.

The straight chain and its one anchor: anchor choice, the crossing-zero rule,
mixed units (kept from before the restructure); and from issue 65 the D2
warnings, the zero-timing chain for columns with no readable timing (D3),
``≤N`` (D18) and time ranges (D4, D20).
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
    """D2."""

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
            column("c1", timing="Day 1", cycle=value("Cycle 1")),
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
    """D3: every instance timed — zero from the neighbour toward the anchor."""

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
    """D18: ``≤N`` is read only before the anchor."""

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
    """D4, D20: timed at the start, window forward to the end."""

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
