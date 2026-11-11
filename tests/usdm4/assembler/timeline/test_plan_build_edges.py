"""Planner and TimelineBuild branches the timeline fixtures do not reach,
driven directly on the private helpers with stubs: a delay measured from a
column that is not in the timeline, an interval with no timing point, a
later cycle whose previous cycle is missing with no previous node, a window
label with no column / no window / a zero window, and an epoch term that the
epoch type code list does not hold."""

from types import SimpleNamespace as NS
from unittest.mock import MagicMock

from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.build import TimelineBuild
from src.usdm4.assembler.timeline.plan import BEFORE, Planner


def _warnings(errors: Errors) -> list[str]:
    return [e["message"] for e in errors.to_dict(level=Errors.WARNING)]


class TestPlanner:
    def test_from_index_unknown_column_warns(self):
        errors = Errors()
        column = NS(id="c2", timing_from="c9", index=1)
        ctx = NS(columns=[NS(id="c1", index=0), column], where="Timeline 1")
        assert Planner(errors)._from_index(ctx, column) is None
        assert "timing from 'c9', which is not a column here" in _warnings(errors)[0]

    def test_from_index_found(self):
        column = NS(id="c2", timing_from="c1", index=1)
        ctx = NS(columns=[NS(id="c1", index=0), column], where="Timeline 1")
        assert Planner(Errors())._from_index(ctx, column) == 0

    def test_interval_without_point_is_zero(self):
        assert Planner(Errors())._interval(None, NS(), "column c1") == 0

    def test_later_cycle_without_previous_cycle_or_node(self):
        errors = Errors()
        ctx = NS(anchor="a", starts={}, lengths={}, where="Timeline 1")
        start = NS(key="k", n=2, unit="day")
        result = Planner(errors)._start_timing(ctx, start, None)
        assert result == (BEFORE, "a", 0, "day", False)
        assert "cycle 1 is not in the timeline" in _warnings(errors)[0]


class TestWindowLabel:
    def test_no_column(self):
        assert TimelineBuild._window_label(NS(column=None, window=None)) is None

    def test_no_window_uses_printed_text(self):
        node = NS(column=NS(window_label="±2 days"), window=None)
        assert TimelineBuild._window_label(node) == "±2 days"

    def test_no_window_and_no_text(self):
        node = NS(column=NS(window_label=""), window=None)
        assert TimelineBuild._window_label(node) is None

    def test_zero_window_is_empty(self):
        node = NS(
            column=NS(window_label="0 days"),
            window=NS(lower=0, upper=0, unit="day"),
            window_from="field",
        )
        assert TimelineBuild._window_label(node) == ""


class TestEpochType:
    def test_term_not_in_code_list_warns_and_defaults(self):
        build = TimelineBuild.__new__(TimelineBuild)
        build._errors = Errors()
        build._naming = MagicMock()
        build._naming.epoch_term.return_value = "SCREENING"
        build._builder = MagicMock()
        default = object()
        build._builder.klass_and_attribute_value.side_effect = [None, default]
        assert build._epoch_type("Screening", False) is default
        assert "which is not in the epoch type code list" in _warnings(build._errors)[0]
