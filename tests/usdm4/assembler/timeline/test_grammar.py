"""The pattern grammar — issue 63, part 63.2.

Weighted to refusals: a grammar that accepts too much turns back into the
heuristic parsing the rebuild replaces. Specification:
``docs/timeline_assembler_design.md`` § 4.
"""

import pytest

from src.usdm4.assembler.timeline.grammar import (
    REDACTED,
    UNITS,
    PatternError,
    TimeRange,
    TimingPoint,
    Window,
    is_redacted,
    is_time_range,
    parse_label,
    parse_time_range,
    parse_timing,
    parse_window,
)


class TestRedacted:
    """Issue 64 — the redaction pattern."""

    def test_the_constant(self):
        assert REDACTED == "CCI"

    @pytest.mark.parametrize("value", ["CCI", "cci", "Cci", " CCI ", "\tCCI\n"])
    def test_accepted(self, value):
        assert is_redacted(value)

    @pytest.mark.parametrize(
        "value", [None, "", "  ", "[CCI]", "CCI 1", "Redacted", "C C I", 3, ["CCI"]]
    )
    def test_refused(self, value):
        assert not is_redacted(value)

    def test_the_parsers_still_refuse_it(self):
        # A redaction is caught before parsing; the parsers never accept it.
        with pytest.raises(PatternError):
            parse_timing("CCI")
        with pytest.raises(PatternError):
            parse_window("CCI")


class TestTiming:
    @pytest.mark.parametrize(
        "pattern, unit, value",
        [
            ("Day 1", "day", 1),
            ("Day 0", "day", 0),
            ("Day -7", "day", -7),
            ("Day -28", "day", -28),
            ("Day 365", "day", 365),
            ("Week 12", "week", 12),
            ("Month 6", "month", 6),
            ("Year 2", "year", 2),
            ("Hour 4", "hour", 4),
            ("Minute 30", "minute", 30),
            ("Hour -1", "hour", -1),
        ],
    )
    def test_accepted(self, pattern, unit, value):
        assert parse_timing(pattern) == TimingPoint(unit=unit, value=value)

    @pytest.mark.parametrize("pattern", ["day 8", "DAY 8", "dAy 8"])
    def test_keyword_ignores_case(self, pattern):
        assert parse_timing(pattern) == TimingPoint(unit="day", value=8)

    @pytest.mark.parametrize("pattern", ["  Day 8", "Day 8  ", " Day 8 "])
    def test_surrounding_whitespace_trimmed(self, pattern):
        assert parse_timing(pattern) == TimingPoint(unit="day", value=8)

    def test_every_unit_is_a_keyword(self):
        for unit in UNITS:
            assert parse_timing(f"{unit.capitalize()} 3").unit == unit

    @pytest.mark.parametrize(
        "pattern",
        [
            "",  # empty
            "   ",  # blank
            "D8",  # abbreviation
            "D 8",
            "Wk 4",
            "Days 8",  # plural keyword
            "Day",  # no number
            "8",  # no keyword
            "8 days",  # window/length form, not a timing
            "Day8",  # no space
            "Day  8",  # two spaces
            "Day\t8",  # tab
            "Day 8.5",  # not an integer
            "Day +8",  # explicit plus
            "Day -0",  # negative zero
            "Day 08",  # leading zero
            "Day −8",  # unicode minus
            "Day ٨",  # non-ASCII digit
            "Day 1 to Day 7",  # a time range, not a point
            "Cycle 1",  # cycle — R4
            "C2D8",  # printed cycle-day form
            "Day 8 (±3 days)",  # window glued on
            "Fortnight 2",  # unknown unit
            "Screening",  # a label, not a timing
        ],
    )
    def test_refused(self, pattern):
        with pytest.raises(PatternError) as error:
            parse_timing(pattern)
        assert error.value.kind == "timing"
        assert error.value.value == pattern

    @pytest.mark.parametrize("value", [None, 8, 8.0, ["Day 8"]])
    def test_non_text_refused(self, value):
        with pytest.raises(PatternError):
            parse_timing(value)


class TestTimeRange:
    """Issue 65 — a scheduled time printed as a range (D4)."""

    @pytest.mark.parametrize(
        "pattern, unit, start, end",
        [
            ("Day -28 to Day -1", "day", -28, -1),
            ("Day -3 to Day 2", "day", -3, 2),
            ("Day 1 to Day 1", "day", 1, 1),
            ("Week 1 to Week 4", "week", 1, 4),
            ("hour 0 to HOUR 2", "hour", 0, 2),
            ("  Day 2 to Day 4 ", "day", 2, 4),
            ("Day 2 TO Day 4", "day", 2, 4),
        ],
    )
    def test_accepted(self, pattern, unit, start, end):
        assert parse_time_range(pattern) == TimeRange(unit=unit, start=start, end=end)

    @pytest.mark.parametrize(
        "pattern, expected",
        [
            ("Day -28 to Week 1", "same unit"),
            ("Day 5 to Day 2", "not before the start"),
            ("Day 1 to Day 7 to Day 9", "<Unit> <int> to"),
            ("Day 1", "<Unit> <int> to"),
            ("-28 to -1", "<Unit> <int> to"),
            ("Day -28 to -1", "<Unit> <int> to"),
            ("Day 1  to Day 7", "<Unit> <int> to"),
            ("Day −28 to Day −1", "<Unit> <int> to"),
        ],
    )
    def test_refused(self, pattern, expected):
        with pytest.raises(PatternError) as error:
            parse_time_range(pattern)
        assert error.value.kind == "time range"
        assert expected in error.value.expected

    @pytest.mark.parametrize("value", [None, 3, ["Day 1 to Day 2"]])
    def test_non_text_refused(self, value):
        with pytest.raises(PatternError):
            parse_time_range(value)

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("Day -28 to Day -1", True),
            ("day 1 TO day 2", True),
            ("Day 1", False),
            (None, False),
        ],
    )
    def test_is_time_range(self, value, expected):
        assert is_time_range(value) is expected


class TestWindow:
    @pytest.mark.parametrize(
        "pattern, lower, upper, unit",
        [
            ("-3..+3 days", 3, 3, "day"),
            ("-0..+2 hours", 0, 2, "hour"),
            ("-7..+0 days", 7, 0, "day"),
            ("-0..+0 days", 0, 0, "day"),
            ("-1..+2 weeks", 1, 2, "week"),
            ("-1..+1 months", 1, 1, "month"),
            ("-1..+1 years", 1, 1, "year"),
            ("-15..+15 minutes", 15, 15, "minute"),
            ("-14..+14 DAYS", 14, 14, "day"),
            (" -3..+3 days ", 3, 3, "day"),
        ],
    )
    def test_accepted(self, pattern, lower, upper, unit):
        assert parse_window(pattern) == Window(lower=lower, upper=upper, unit=unit)

    def test_every_unit_has_a_plural(self):
        for unit in UNITS:
            assert parse_window(f"-1..+1 {unit}s").unit == unit

    @pytest.mark.parametrize(
        "pattern",
        [
            "",
            "±3 days",  # printed form
            "+/-3 days",
            "(±3 days)",
            "-3..+3 day",  # singular
            "-3..+3",  # no unit
            "3..3 days",  # no signs
            "-3..3 days",
            "+3..-3 days",  # signs reversed
            "-3 .. +3 days",  # spaces inside
            "-3..+3  days",  # two spaces
            "-3..+3days",  # no space
            "-3.5..+3 days",  # not an integer
            "-03..+3 days",  # leading zero
            "-3..+3 d",  # abbreviation
            "-3 to +3 days",
            "−3..+3 days",  # unicode minus
            "Day -3 to Day 3",  # a time range, not a window
            "Day 8",  # a timing, not a window
        ],
    )
    def test_refused(self, pattern):
        with pytest.raises(PatternError) as error:
            parse_window(pattern)
        assert error.value.kind == "window"

    @pytest.mark.parametrize("value", [None, 3, {"before": 3, "after": 3}])
    def test_non_text_refused(self, value):
        with pytest.raises(PatternError):
            parse_window(value)


class TestLabel:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("Screening", "Screening"),
            ("  Screening  ", "Screening"),
            ("V1", "V1"),
            ("D8", "D8"),
            ("Period III — Treatment", "Period III — Treatment"),
            ("End of Study/ Visit 6", "End of Study/ Visit 6"),
        ],
    )
    def test_accepted(self, value, expected):
        assert parse_label(value) == expected

    @pytest.mark.parametrize("value", ["", "   ", "\t", None, 1])
    def test_refused(self, value):
        with pytest.raises(PatternError):
            parse_label(value)

    def test_kind_names_the_field(self):
        with pytest.raises(PatternError) as error:
            parse_label("", kind="epoch")
        assert error.value.kind == "epoch"
        assert "epoch" in str(error.value)


class TestPatternError:
    def test_is_a_value_error(self):
        assert issubclass(PatternError, ValueError)

    def test_message_names_value_and_expected_form(self):
        with pytest.raises(PatternError) as error:
            parse_timing("D8")
        message = str(error.value)
        assert "'D8'" in message
        assert "<Unit> <int>" in message
