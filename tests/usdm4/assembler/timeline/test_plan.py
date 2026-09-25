"""Plan — issue 63, part 63.6.

The straight chain and its one anchor, kept exactly as before the
restructure: anchor choice, the crossing-zero rule, mixed units, and columns
with no parseable timing.
"""

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.columns import parse_timeline
from src.usdm4.assembler.timeline.plan import AFTER, BEFORE, FIXED, Planner
from tests.usdm4.assembler.timeline.helpers import column, timeline


def _plan(timings: list, errors: Errors | None = None):
    columns = [column(f"c{i + 1}", timing=t) for i, t in enumerate(timings)]
    parsed = parse_timeline(timeline(columns))
    return Planner(errors or Errors()).plan(parsed)


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
