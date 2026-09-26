"""Parse — issue 63, part 63.6.

The code under test imports ``usdm4.*`` while these tests import ``src.usdm4.*``,
so grammar classes are compared by field and ``PatternError`` is caught as the
``ValueError`` it is.

Issue 65: each of timing and window is read from its pattern, else from its
printed text, else nothing; a refused pattern is a warning and falls back to
the text (U4-17).

Issue 66: cycle and cycle length are read the same way — pattern, else
printed text, else nothing.
"""

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.columns import parse_column, parse_timeline
from tests.usdm4.assembler.timeline.helpers import activity, column, timeline, value


def _column(**kwargs) -> dict:
    return timeline([column("c1", **kwargs)])["columns"][0]


class TestColumn:
    def test_full_column(self):
        data = _column(
            epoch=value("Screening"),
            visit=value("V 1", "V1"),
            timing=value("D 15", "Day 15"),
            window=value("(±3 days)", "-3..+3 days"),
            markers=["a"],
            cycle=value("Cycle 1"),
            cycle_length=value("Cycle = 21 days", "21 days"),
            notes=[{"role": "timing_clarification", "text": "pre-dose"}],
        )
        parsed = parse_column(4, data)
        assert parsed.index == 4
        assert parsed.id == "c1"
        assert parsed.epoch_label == "Screening"
        assert parsed.visit_label == "V 1"
        assert parsed.markers == {"visit": ["a"]}
        assert parsed.all_markers == ["a"]
        assert parsed.redacted == set()
        assert parsed.timing_label == "D 15"
        assert (parsed.timing.unit, parsed.timing.value) == ("day", 15)
        assert parsed.window_label == "(±3 days)"
        window = parsed.window
        assert (window.lower, window.upper, window.unit) == (3, 3, "day")
        assert parsed.cycle_label == "Cycle 1"
        assert parsed.cycle_length_label == "Cycle = 21 days"
        assert parsed.notes == [{"role": "timing_clarification", "text": "pre-dose"}]

    def test_empty_column(self):
        parsed = parse_column(0, _column())
        assert parsed.epoch_label is None
        assert parsed.visit_label is None
        assert parsed.timing_label is None
        assert parsed.timing is None
        assert parsed.window is None
        assert parsed.window_label is None

    def test_pattern_only_labels_with_the_pattern(self):
        parsed = parse_column(0, _column(timing={"text": "", "pattern": "Day 3"}))
        assert parsed.timing_label == "Day 3"
        assert parsed.timing.value == 3

    def test_unreadable_text_is_carried_with_no_value(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(timing={"text": "As clinically indicated", "pattern": None}),
            errors=errors,
        )
        parsed_none = parse_column(
            0, _column(timing={"text": "As needed", "pattern": "   "})
        )
        assert parsed.timing_label == "As clinically indicated"
        assert parsed.timing is None
        assert parsed_none.timing is None
        assert "'As clinically indicated' not read" in _messages(errors)[0]

    def test_a_time_range_pattern_sets_the_range_and_its_start(self):
        parsed = parse_column(0, _column(timing=value("≤28", "Day -28 to Day -1")))
        assert parsed.timing_label == "≤28"
        assert _range(parsed) == ("day", -28, -1)
        assert (parsed.timing.unit, parsed.timing.value) == ("day", -28)

    def test_cycle_fields_from_the_pattern(self):
        parsed = parse_column(
            0,
            _column(
                cycle=value("Cycle 3-n", "Cycle 3+"),
                cycle_length=value("Cycle = 21 days", "21 days"),
            ),
        )
        assert parsed.cycle_label == "Cycle 3-n"
        assert (parsed.cycle.start, parsed.cycle.end) == (3, None)
        assert (parsed.cycle_length.n, parsed.cycle_length.unit) == (21, "day")

    def test_cycle_fields_from_the_printed_text(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(
                cycle={"text": "C2", "pattern": None},
                cycle_length={"text": "21-day cycle", "pattern": None},
            ),
            errors=errors,
        )
        assert parsed.cycle.n == 2
        assert (parsed.cycle_length.n, parsed.cycle_length.unit) == (21, "day")
        assert errors.to_dict(0) == []

    def test_a_refused_cycle_pattern_falls_back_to_the_text(self):
        errors = Errors()
        parsed = parse_column(
            0, _column(cycle=value("Cycle 2", "C2")), errors=errors, t=1
        )
        assert parsed.cycle.n == 2
        (item,) = errors.to_dict(0)
        assert item["message"].startswith("Timeline 1, column 'c1', cycle: ")

    def test_unreadable_cycle_fields_are_warned(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(
                cycle={"text": "Subsequent Cycles", "pattern": None},
                cycle_length={"text": "x", "pattern": None},
            ),
            errors=errors,
            t=1,
        )
        assert parsed.cycle is None and parsed.cycle_length is None
        messages = [item["message"] for item in errors.to_dict(0)]
        assert messages == [
            "Timeline 1, column 'c1', cycle: printed text 'Subsequent Cycles' not read",
            "Timeline 1, column 'c1', cycle_length: printed text 'x' not read",
        ]

    def test_a_bare_cycle_length_takes_its_row_label_unit(self):
        """Issue 68, U4-28."""
        errors = Errors()
        data = timeline(
            [
                column(
                    "c1",
                    cycle={"text": "2-3", "pattern": None},
                    cycle_length={"text": "28", "pattern": None},
                )
            ],
            rows={"cycle_length": "Approximate Duration (days)"},
        )
        parsed = parse_timeline(data, errors, 1).columns[0]
        assert (parsed.cycle.start, parsed.cycle.end) == (2, 3)
        assert (parsed.cycle_length.n, parsed.cycle_length.unit) == (28, "day")
        assert errors.to_dict(0) == []

    def test_a_bare_cycle_length_falls_back_to_the_timing_row_label(self):
        """U4-28."""
        errors = Errors()
        data = timeline(
            [column("c1", cycle_length={"text": "4", "pattern": None})],
            rows={"cycle_length": "Duration", "timing": "Week of cycle"},
        )
        parsed = parse_timeline(data, errors, 1).columns[0]
        assert (parsed.cycle_length.n, parsed.cycle_length.unit) == (4, "week")
        assert errors.to_dict(0) == []

    def test_a_bare_cycle_length_with_no_unit_anywhere_is_warned(self):
        """U4-28: not read, and the warning says why."""
        errors = Errors()
        data = timeline(
            [column("c1", cycle_length={"text": "28", "pattern": None})],
            rows={"cycle_length": "Duration"},
        )
        parsed = parse_timeline(data, errors, 1).columns[0]
        assert parsed.cycle_length is None
        assert [item["message"] for item in errors.to_dict(0)] == [
            "Timeline 1, column 'c1', cycle_length: no unit stated for '28' in the "
            "value, the cycle length row label or the timing row label; not read"
        ]

    def test_a_cycle_length_pattern_still_wins_over_the_row_label(self):
        data = timeline(
            [column("c1", cycle_length=value("28", "4 weeks"))],
            rows={"cycle_length": "Approximate Duration (days)"},
        )
        parsed = parse_timeline(data).columns[0]
        assert (parsed.cycle_length.n, parsed.cycle_length.unit) == (4, "week")

    def test_a_redacted_cycle_is_not_read(self):
        parsed = parse_column(0, _column(cycle=value("CCI", "CCI")))
        assert parsed.cycle is None and parsed.cycle_label == "CCI"

    def test_a_refused_pattern_falls_back_to_the_text(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(timing=value("D8", "D8"), window=value("±3 days", "±3 days")),
            errors=errors,
            t=2,
        )
        assert (parsed.timing.unit, parsed.timing.value) == ("day", 8)
        assert (parsed.window.lower, parsed.window.upper) == (3, 3)
        messages = _messages(errors)
        assert len(messages) == 2
        assert messages[0].startswith("Timeline 2, column 'c1', timing:")
        assert "reading the printed text instead" in messages[0]
        assert messages[1].startswith("Timeline 2, column 'c1', window:")

    def test_a_refused_pattern_with_unreadable_text_has_no_value(self):
        errors = Errors()
        parsed = parse_column(
            0, _column(timing=value("Predose", "Predose")), errors=errors
        )
        assert parsed.timing is None
        assert len(_messages(errors)) == 2
        assert _messages(errors)[0].startswith("Column 'c1', timing:")

    def test_a_refused_pattern_with_no_text_has_no_value(self):
        errors = Errors()
        parsed = parse_column(
            0, _column(timing={"text": "", "pattern": "D8"}), errors=errors
        )
        assert parsed.timing is None
        assert len(_messages(errors)) == 1

    def test_a_blank_epoch_pattern_is_no_pattern(self):
        data = _column(epoch={"text": "Screening", "pattern": "\t"})
        assert parse_column(0, data).epoch_label == "Screening"


class TestPrintedText:
    """Issue 65 — text only, pattern only, or both; the pattern wins."""

    def test_text_only_timing(self):
        parsed = parse_column(0, _column(timing={"text": "D8", "pattern": None}))
        assert (parsed.timing.unit, parsed.timing.value) == ("day", 8)
        assert parsed.timing_label == "D8"

    def test_text_only_window(self):
        parsed = parse_column(
            0,
            _column(
                timing={"text": "Week 4", "pattern": None},
                window={"text": "±3", "pattern": None},
            ),
        )
        assert (parsed.window.lower, parsed.window.unit) == (3, "week")
        assert parsed.window_from == "window"

    def test_the_pattern_wins(self):
        parsed = parse_column(0, _column(timing=value("Day 9", "Day 8")))
        assert parsed.timing.value == 8

    def test_blank_or_dashes_are_nothing_and_not_warned(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(
                timing={"text": "—", "pattern": None},
                window={"text": "---", "pattern": None},
            ),
            errors=errors,
        )
        assert parsed.timing is None and parsed.window is None
        assert _messages(errors) == []

    def test_a_bare_number_takes_the_row_label_unit(self):
        parsed = parse_column(
            0,
            _column(timing={"text": "4", "pattern": None}),
            rows={"timing": "Timing of Visit (Weeks)"},
        )
        assert (parsed.timing.unit, parsed.timing.value) == ("week", 4)

    def test_a_bare_number_with_no_unit_is_days_with_a_warning(self):
        errors = Errors()
        parsed = parse_column(
            0, _column(timing={"text": "15", "pattern": None}), errors=errors
        )
        assert (parsed.timing.unit, parsed.timing.value) == ("day", 15)
        assert "no unit stated for '15'; read as days" in _messages(errors)[0]

    def test_a_bare_window_with_no_unit_is_days_with_a_warning(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(window={"text": "±3", "pattern": None}),
            errors=errors,
        )
        assert parsed.window.unit == "day"
        assert "window: no unit stated" in _messages(errors)[0]

    def test_a_bare_window_takes_the_window_row_label(self):
        parsed = parse_column(
            0,
            _column(
                timing={"text": "Week 4", "pattern": None},
                window={"text": "±3", "pattern": None},
            ),
            rows={"window": "Visit interval tolerance (days)"},
        )
        assert parsed.window.unit == "day"

    def test_unreadable_window_text_is_warned(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(window={"text": "See Section 1.3", "pattern": None}),
            errors=errors,
        )
        assert parsed.window is None
        assert parsed.window_label == "See Section 1.3"
        assert "'See Section 1.3' not read" in _messages(errors)[0]

    def test_a_printed_time_range(self):
        parsed = parse_column(0, _column(timing={"text": "-28 to -1", "pattern": None}))
        assert _range(parsed) == ("day", -28, -1)
        assert parsed.timing.value == -28

    def test_up_to_is_carried_for_the_plan(self):
        parsed = parse_column(0, _column(timing={"text": "≤21", "pattern": None}))
        assert parsed.timing is None
        assert (parsed.up_to.unit, parsed.up_to.n) == ("day", 21)

    def test_a_window_in_the_timing_cell(self):
        parsed = parse_column(0, _column(timing={"text": "15 ± 3", "pattern": None}))
        assert parsed.timing.value == 15
        assert (parsed.window.lower, parsed.window.upper) == (3, 3)
        assert parsed.window_from == "timing"

    def test_the_window_field_beats_the_timing_cell_with_a_warning(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(
                timing={"text": "15 ± 3", "pattern": None},
                window=value("±7", "-7..+7 days"),
            ),
            errors=errors,
        )
        assert parsed.window.lower == 7
        assert parsed.window_from == "window"
        assert any(
            "the timing cell prints a window too" in m for m in _messages(errors)
        )

    def test_the_window_field_beats_a_time_range_with_a_warning(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(timing=value("Day -3 to Day 3"), window=value("-1..+1 days")),
            errors=errors,
        )
        assert parsed.window.lower == 1
        assert "the timing is a time range" in _messages(errors)[0]

    def test_a_redacted_value_is_never_read(self):
        errors = Errors()
        parsed = parse_column(0, _column(timing=value("Day 8", "CCI")), errors=errors)
        assert parsed.timing is None
        assert _messages(errors) == []


class TestRedaction:
    """Issue 64 — ``CCI`` is a valid pattern in every field and is never
    parsed; the printed text stays the label."""

    @pytest.mark.parametrize(
        "field", ["epoch", "visit", "cycle", "cycle_length", "timing", "window"]
    )
    def test_cci_is_accepted_in_every_field(self, field):
        parsed = parse_column(0, _column(**{field: value("CCI")}))
        assert parsed.redacted == {field}
        assert parsed.is_redacted(field)

    @pytest.mark.parametrize("pattern", ["CCI", "cci", "  CCI  "])
    def test_cci_matches_ignoring_case_and_space(self, pattern):
        parsed = parse_column(0, _column(timing=value("[CCI]", pattern)))
        assert parsed.redacted == {"timing"}

    def test_redacted_timing_and_window_make_no_value(self):
        parsed = parse_column(
            0, _column(timing=value("[CCI]", "CCI"), window=value("Redacted", "CCI"))
        )
        assert parsed.timing is None
        assert parsed.window is None
        assert parsed.timing_label == "[CCI]"
        assert parsed.window_label == "Redacted"

    def test_pattern_only_cci_labels_with_cci(self):
        parsed = parse_column(0, _column(timing={"text": "", "pattern": "CCI"}))
        assert parsed.timing_label == "CCI"

    def test_text_cci_with_null_pattern_is_not_a_redaction(self):
        # Only the PATTERN states a redaction; printed `CCI` is unreadable text.
        parsed = parse_column(0, _column(timing={"text": "CCI", "pattern": None}))
        assert parsed.redacted == set()

    def test_other_fields_still_parse(self):
        parsed = parse_column(0, _column(visit=value("CCI"), timing=value("Day 8")))
        assert parsed.redacted == {"visit"}
        assert parsed.timing.value == 8


class TestMarkers:
    """Issue 64 — markers are carried per header value."""

    def test_markers_by_field(self):
        parsed = parse_column(
            0,
            _column(
                epoch=value("Screening", markers=["e"]),
                visit=value("V1", markers=["1", "2"]),
                timing=value("Day 1", markers=["t"]),
            ),
        )
        assert parsed.markers == {"epoch": ["e"], "visit": ["1", "2"], "timing": ["t"]}
        assert parsed.all_markers == ["e", "1", "2", "t"]

    def test_a_marker_on_two_values_is_listed_once(self):
        parsed = parse_column(
            0,
            _column(
                visit=value("V1", markers=["a"]), timing=value("Day 1", markers=["a"])
            ),
        )
        assert parsed.all_markers == ["a"]

    def test_a_redacted_value_keeps_its_markers(self):
        parsed = parse_column(0, _column(timing=value("CCI", markers=["x"])))
        assert parsed.all_markers == ["x"]


class TestTimeline:
    def test_rows_are_carried(self):
        data = timeline(
            [column("c1", timing="Day 1")],
            rows={"timing": "Days from randomization"},
        )
        assert parse_timeline(data).rows == {"timing": "Days from randomization"}

    def test_rows_default_empty(self):
        assert parse_timeline(timeline([column("c1", timing="Day 1")])).rows == {}

    def test_parse_timeline(self):
        data = timeline(
            [column("c1", "Screening", "V1", "Day 1"), column("c2", visit="V2")],
            [activity("Consent", ["c1"])],
            [{"marker": "a", "text": "Note."}],
            type="profile",
            title="PK",
            description="Sampling",
            classification={"orientation": "transposed", "unit": None},
        )
        parsed = parse_timeline(data)
        assert parsed.type == "profile"
        assert parsed.family == "profile"
        assert parsed.title == "PK"
        assert parsed.description == "Sampling"
        assert parsed.classification["orientation"] == "transposed"
        assert [c.id for c in parsed.columns] == ["c1", "c2"]
        assert parsed.column_index == {"c1": 0, "c2": 1}
        assert parsed.activities[0]["name"] == "Consent"
        assert parsed.footnotes[0]["marker"] == "a"

    def test_a_bad_pattern_does_not_stop_the_timeline(self):
        errors = Errors()
        data = timeline([column("c1", timing="Day 1"), column("c2", timing="Wk 2")])
        parsed = parse_timeline(data, errors, 3)
        assert (parsed.columns[1].timing.unit, parsed.columns[1].timing.value) == (
            "week",
            2,
        )
        assert _messages(errors)[0].startswith("Timeline 3, column 'c2', timing:")

    def test_rows_reach_the_columns(self):
        data = timeline(
            [column("c1", timing={"text": "15", "pattern": None})],
            rows={"timing": "Hours post dose"},
        )
        assert parse_timeline(data).columns[0].timing.unit == "hour"


def _messages(errors: Errors) -> list[str]:
    return [item["message"] for item in errors.to_dict(0)]


def _range(parsed) -> tuple:
    r = parsed.time_range
    return (r.unit, r.start, r.end)
