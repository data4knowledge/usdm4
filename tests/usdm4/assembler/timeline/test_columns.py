"""Parse — issue 63, part 63.6; structured input, issue 73 (U4-35).

Every value arrives structured; parse copies it across. Printed text is never
read — it is the label, and with no text the label is rendered from the
structure. A value sent as text only is carried as its label and not read.

The fixtures here are written in the structured form itself, not the tests'
compact notation, so what is tested is the contract.
"""

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.columns import parse_column, parse_timeline
from tests.usdm4.assembler.timeline.helpers import activity, timeline

DAY_1 = {"text": "Day 1", "value": 1, "unit": "days"}


def _column(**values) -> dict:
    return timeline([{"id": "c1", **values}])["columns"][0]


def _messages(errors: Errors) -> list[str]:
    return [item["message"] for item in errors.to_dict(0)]


class TestColumn:
    def test_full_column(self):
        data = _column(
            epoch={"text": "Screening"},
            visit={"text": "V 1", "markers": ["a"]},
            timing={"text": "D 15", "value": 15, "unit": "days"},
            window={"text": "(±3 days)", "before": 3, "after": 3, "unit": "days"},
            cycle={"text": "Cycle 1", "first": 1, "last": 1},
            cycle_length={"text": "Cycle = 21 days", "value": 21, "unit": "days"},
            notes=[{"role": "timing_clarification", "text": "pre-dose"}],
        )
        errors = Errors()
        parsed = parse_column(4, data, errors)
        assert parsed.index == 4
        assert parsed.id == "c1"
        assert parsed.epoch_label == "Screening"
        assert parsed.visit_label == "V 1"
        assert parsed.markers == {"visit": ["a"]}
        assert parsed.all_markers == ["a"]
        assert parsed.redacted == set()
        assert parsed.timing_label == "D 15"
        assert (parsed.timing.unit, parsed.timing.value) == ("day", 15)
        assert parsed.time_range is None
        assert parsed.window_label == "(±3 days)"
        window = parsed.window
        assert (window.lower, window.upper, window.unit) == (3, 3, "day")
        assert parsed.window_from == "window"
        assert parsed.cycle_label == "Cycle 1"
        assert parsed.cycle.n == 1
        assert parsed.cycle_length_label == "Cycle = 21 days"
        assert (parsed.cycle_length.n, parsed.cycle_length.unit) == (21, "day")
        assert parsed.notes == [{"role": "timing_clarification", "text": "pre-dose"}]
        assert _messages(errors) == []

    def test_empty_column(self):
        parsed = parse_column(0, _column())
        assert parsed.epoch_label is None
        assert parsed.visit_label is None
        assert parsed.timing_label is None
        assert parsed.timing is None
        assert parsed.window is None
        assert parsed.window_label is None
        assert parsed.cycle is None
        assert parsed.delay is None

    @pytest.mark.parametrize(
        "unit, held", [("minutes", "minute"), ("hours", "hour"), ("weeks", "week")]
    )
    def test_units_are_held_singular(self, unit, held):
        parsed = parse_column(0, _column(timing={"value": 4, "unit": unit}))
        assert parsed.timing.unit == held

    def test_a_time_range_sets_the_range_and_its_start(self):
        parsed = parse_column(
            0, _column(timing={"text": "≤28", "start": -28, "end": -1, "unit": "days"})
        )
        assert parsed.timing_label == "≤28"
        r = parsed.time_range
        assert (r.unit, r.start, r.end) == ("day", -28, -1)
        assert (parsed.timing.unit, parsed.timing.value) == ("day", -28)

    def test_a_cycle_range_and_an_open_one(self):
        bounded = parse_column(0, _column(cycle={"first": 2, "last": 3}))
        open_ = parse_column(0, _column(cycle={"text": "Cycle 3-n", "first": 3}))
        assert (bounded.cycle.start, bounded.cycle.end) == (2, 3)
        assert (open_.cycle.start, open_.cycle.end) == (3, None)
        assert open_.cycle_label == "Cycle 3-n"


class TestRenderedLabels:
    """U4-35: no printed text → the label is rendered from the structure, in
    the retired pattern grammar's form, so labels do not move."""

    @pytest.mark.parametrize(
        "field, value, label",
        [
            ("timing", {"value": -7, "unit": "days"}, "Day -7"),
            ("timing", {"start": -28, "end": -1, "unit": "days"}, "Day -28 to Day -1"),
            ("window", {"before": 0, "after": 2, "unit": "hours"}, "-0..+2 hours"),
            ("cycle", {"first": 2, "last": 2}, "Cycle 2"),
            ("cycle", {"first": 1, "last": 6}, "Cycle 1-6"),
            ("cycle", {"first": 3, "last": None}, "Cycle 3+"),
            ("cycle_length", {"value": 4, "unit": "weeks"}, "4 weeks"),
            ("delay", {"min": 2, "max": 10, "unit": "days"}, "2 to 10 days"),
            ("delay", {"min": 7, "unit": "days"}, "7+ days"),
        ],
    )
    def test_rendered(self, field, value, label):
        parsed = parse_column(0, _column(**{field: value}))
        assert getattr(parsed, f"{field}_label") == label


class TestTextOnly:
    """A value the caller could not structure is carried as its label and
    never read."""

    def test_a_text_only_timing_is_carried_with_no_value(self):
        errors = Errors()
        parsed = parse_column(
            0, _column(timing={"text": "As clinically indicated"}), errors, t=1
        )
        assert parsed.timing_label == "As clinically indicated"
        assert parsed.timing is None
        # The plan warns: no readable timing (U4-3).
        assert _messages(errors) == []

    def test_text_that_looks_readable_is_still_not_read(self):
        parsed = parse_column(0, _column(timing={"text": "Day 8"}))
        assert parsed.timing is None
        assert parsed.timing_label == "Day 8"

    @pytest.mark.parametrize("field", ["window", "cycle", "cycle_length", "delay"])
    def test_a_text_only_value_is_warned(self, field):
        errors = Errors()
        parsed = parse_column(0, _column(**{field: {"text": "See 1.3"}}), errors, t=2)
        assert getattr(parsed, field) is None
        assert getattr(parsed, f"{field}_label") == "See 1.3"
        assert _messages(errors) == [
            f"Timeline 2, column 'c1', {field}: sent as text only ('See 1.3'); not read"
        ]


class TestDelay:
    """R8 (#72) builds it; issue 73 accepts and carries it."""

    def test_a_delay_is_carried_and_warned(self):
        errors = Errors()
        parsed = parse_column(
            0,
            _column(
                visit={"text": "(7-28 days between doses)"},
                delay={"text": "7-28 days", "min": 7, "max": 28, "unit": "days"},
            ),
            errors,
            t=1,
        )
        assert (parsed.delay.min, parsed.delay.max, parsed.delay.unit) == (
            7,
            28,
            "day",
        )
        assert parsed.delay_label == "7-28 days"
        assert parsed.timing is None
        assert _messages(errors) == [
            "Timeline 1, column 'c1', delay: a delay is not built until R8; "
            "carried only"
        ]


class TestRedaction:
    """Issue 64 — ``redacted: true`` in any field; never read, the printed
    text stays the label."""

    @pytest.mark.parametrize(
        "field",
        ["epoch", "visit", "cycle", "cycle_length", "timing", "window", "delay"],
    )
    def test_redacted_is_accepted_in_every_field(self, field):
        errors = Errors()
        parsed = parse_column(
            0, _column(**{field: {"text": "CCI", "redacted": True}}), errors
        )
        assert parsed.redacted == {field}
        assert parsed.is_redacted(field)
        assert getattr(parsed, f"{field}_label") == "CCI"
        assert _messages(errors) == []

    def test_redacted_timing_and_window_make_no_value(self):
        parsed = parse_column(
            0,
            _column(
                timing={"text": "[CCI]", "redacted": True},
                window={"text": "Redacted", "redacted": True},
            ),
        )
        assert parsed.timing is None
        assert parsed.window is None
        assert parsed.timing_label == "[CCI]"
        assert parsed.window_label == "Redacted"

    def test_printed_cci_that_is_not_flagged_is_text_only(self):
        # Only the flag states a redaction.
        parsed = parse_column(0, _column(timing={"text": "CCI"}))
        assert parsed.redacted == set()
        assert parsed.timing is None

    def test_other_fields_still_parse(self):
        parsed = parse_column(
            0, _column(visit={"text": "CCI", "redacted": True}, timing=DAY_1)
        )
        assert parsed.redacted == {"visit"}
        assert parsed.timing.value == 1


class TestMarkers:
    """Issue 64 — markers are carried per value."""

    def test_markers_by_field(self):
        parsed = parse_column(
            0,
            _column(
                epoch={"text": "Screening", "markers": ["e"]},
                visit={"text": "V1", "markers": ["1", "2"]},
                timing={**DAY_1, "markers": ["t"]},
            ),
        )
        assert parsed.markers == {"epoch": ["e"], "visit": ["1", "2"], "timing": ["t"]}
        assert parsed.all_markers == ["e", "1", "2", "t"]

    def test_a_marker_on_two_values_is_listed_once(self):
        parsed = parse_column(
            0,
            _column(
                visit={"text": "V1", "markers": ["a"]},
                timing={**DAY_1, "markers": ["a"]},
            ),
        )
        assert parsed.all_markers == ["a"]

    def test_a_redacted_value_and_a_delay_keep_their_markers(self):
        parsed = parse_column(
            0,
            _column(
                visit={"text": "CCI", "redacted": True, "markers": ["x"]},
                delay={"min": 2, "unit": "days", "markers": ["y"]},
            ),
        )
        assert parsed.all_markers == ["x", "y"]


class TestTimeline:
    def test_rows_are_carried_and_not_read(self):
        data = timeline(
            [{"id": "c1", "timing": {"text": "15", "value": 15, "unit": "days"}}],
            rows={"timing": "Hours post dose"},
        )
        parsed = parse_timeline(data)
        assert parsed.rows == {"timing": "Hours post dose"}
        assert parsed.columns[0].timing.unit == "day"

    def test_rows_default_empty(self):
        assert parse_timeline(timeline([{"id": "c1", "timing": DAY_1}])).rows == {}

    @pytest.mark.parametrize(
        "flag, expected", [({}, False), ({"day_zero": True}, True)]
    )
    def test_day_zero_is_carried_default_day_1(self, flag, expected):
        data = timeline([{"id": "c1", "timing": DAY_1}], **flag)
        assert parse_timeline(data).day_zero is expected

    def test_parse_timeline(self):
        data = timeline(
            [
                {
                    "id": "c1",
                    "epoch": {"text": "Screening"},
                    "visit": {"text": "V1"},
                    "timing": DAY_1,
                },
                {"id": "c2", "visit": {"text": "V2"}},
            ],
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
