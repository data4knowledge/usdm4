"""Parse — issue 63, part 63.6.

The code under test imports ``usdm4.*`` while these tests import ``src.usdm4.*``,
so grammar classes are compared by field and ``PatternError`` is caught as the
``ValueError`` it is.

``parse_timeline`` reads every pattern with the grammar and refuses the first
bad one; until R4 a timing span is carried as text only, and cycle fields are
never parsed.
"""

import pytest

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
        assert parsed.visit_markers == ["a"]
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

    def test_text_only_is_carried_and_not_parsed(self):
        parsed = parse_column(
            0, _column(timing={"text": "As clinically indicated", "pattern": None})
        )
        parsed_none = parse_column(
            0, _column(timing={"text": "As needed", "pattern": "   "})
        )
        assert parsed.timing_label == "As clinically indicated"
        assert parsed.timing is None
        assert parsed_none.timing is None

    def test_a_span_is_carried_as_text_until_r4(self):
        parsed = parse_column(0, _column(timing=value("≤28", "Day -28 to Day -1")))
        assert parsed.timing_label == "≤28"
        assert parsed.timing is None

    def test_cycle_fields_are_not_parsed(self):
        parsed = parse_column(
            0, _column(cycle=value("Cycle 3-n", "Cycle 3+"), cycle_length=value("x"))
        )
        assert parsed.cycle_label == "Cycle 3-n"
        assert parsed.cycle_length_label == "x"

    @pytest.mark.parametrize(
        "field, bad, kind",
        [
            ("timing", value("D8", "D8"), "timing"),
            ("window", value("±3 days", "±3 days"), "window"),
            ("epoch", {"text": "Screening", "pattern": "\t"}, None),
        ],
    )
    def test_a_bad_pattern_is_refused(self, field, bad, kind):
        data = _column(**{field: bad})
        if kind is None:
            # A blank pattern is no pattern: the text is the label.
            assert parse_column(0, data).epoch_label == "Screening"
            return
        with pytest.raises(ValueError) as error:
            parse_column(0, data)
        assert error.value.kind == kind


class TestTimeline:
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

    def test_the_first_bad_pattern_stops_the_timeline(self):
        data = timeline([column("c1", timing="Day 1"), column("c2", timing="Wk 2")])
        with pytest.raises(ValueError):
            parse_timeline(data)
