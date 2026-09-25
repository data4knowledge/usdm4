"""The printed-text reader — issue 65; cycles and cycle lengths, issue 66.

The code under test imports ``usdm4.*`` while these tests import
``src.usdm4.*``, so returned values are compared by field.
"""

import pytest

from src.usdm4.assembler.timeline.printed import (
    is_blank,
    normalise,
    read_cycle,
    read_cycle_length,
    read_timing,
    read_window,
    unit_of_label,
)


def _kind(read) -> str:
    return type(read.timing).__name__


def _point(read) -> tuple:
    return (_kind(read), read.timing.unit, read.timing.value)


def _range(read) -> tuple:
    return (_kind(read), read.timing.unit, read.timing.start, read.timing.end)


def _window(window) -> tuple:
    return (window.lower, window.upper, window.unit)


class TestNormalise:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Days −14 to −1", "Days -14 to -1"),
            ("‐3", "-3"),
            ("‑3", "-3"),
            ("+/-3 days", "±3 days"),
            ("+/−3", "±3"),
            ("<=28", "≤28"),
            ("  Day   8 ", "Day 8"),
        ],
    )
    def test_normalise(self, text, expected):
        assert normalise(text) == expected


class TestBlank:
    @pytest.mark.parametrize("text", [None, "", "  ", "—", "---", "–", "- -"])
    def test_blank(self, text):
        assert is_blank(text)

    @pytest.mark.parametrize("text", ["0", "D1", "n/a"])
    def test_not_blank(self, text):
        assert not is_blank(text)


class TestUnitOfLabel:
    @pytest.mark.parametrize(
        "label, unit",
        [
            ("Days from randomization", "day"),
            ("Study Day", "day"),
            ("Visit interval tolerance (days)", "day"),
            ("Timing of Visit (Weeks)", "week"),
            ("Weeks after randomization", "week"),
            ("Time point (hours)a", "hour"),
            ("Planned Time [h:min]", "hour"),
            ("Minutes post dose", "minute"),
            ("Month", "month"),
            ("Years", "year"),
        ],
    )
    def test_stated(self, label, unit):
        assert unit_of_label(label) == unit

    @pytest.mark.parametrize("label", [None, "", "Time", "Timing", "Day1"])
    def test_not_stated(self, label):
        assert unit_of_label(label) is None


class TestTimingPoint:
    @pytest.mark.parametrize(
        "text, unit, value",
        [
            ("D8", "day", 8),
            ("Day 8", "day", 8),
            ("day -7", "day", -7),
            ("Dy 3", "day", 3),
            ("Wk 12", "week", 12),
            ("w4", "week", 4),
            ("Week 12", "week", 12),
            ("Month 6", "month", 6),
            ("Mo 6", "month", 6),
            ("Yr 1", "year", 1),
            ("Hour 4", "hour", 4),
            ("2 hr", "hour", 2),
            ("30 min", "minute", 30),
            ("12 weeks", "week", 12),
            ("Day +8", "day", 8),
            ("D.8", "day", 8),
        ],
    )
    def test_with_a_unit_word(self, text, unit, value):
        read = read_timing(text)
        assert _point(read) == ("TimingPoint", unit, value)
        assert read.window is None
        assert not read.unit_defaulted

    def test_the_unit_word_beats_the_row_label(self):
        assert read_timing("Week 2", "Days from randomization").timing.unit == "week"

    def test_two_different_units_are_not_read(self):
        assert read_timing("Day 8 weeks") is None


class TestBareNumber:
    def test_unit_from_the_row_label(self):
        read = read_timing("15", "Days from randomization")
        assert _point(read) == ("TimingPoint", "day", 15)
        assert not read.unit_defaulted

    def test_week_row_label(self):
        assert read_timing("4", "Timing of Visit (Weeks)").timing.unit == "week"

    @pytest.mark.parametrize("label", [None, "Time", ""])
    def test_no_unit_is_days_and_flagged(self, label):
        read = read_timing("-7", label)
        assert _point(read) == ("TimingPoint", "day", -7)
        assert read.unit_defaulted


class TestTimeRange:
    @pytest.mark.parametrize(
        "text, unit, start, end",
        [
            ("-28 to -1", "day", -28, -1),
            ("Days −14 to −1", "day", -14, -1),
            ("3-5", "day", 3, 5),
            ("Between Day 2 and Day 4", "day", 2, 4),
            ("Day -28 to Day -1", "day", -28, -1),
            ("D1-D3", "day", 1, 3),
            ("2 to 4 hours", "hour", 2, 4),
            ("Week 1 to Week 4", "week", 1, 4),
        ],
    )
    def test_read(self, text, unit, start, end):
        assert _range(read_timing(text, "Days")) == ("TimeRange", unit, start, end)

    def test_bare_range_unit_from_the_row_label(self):
        read = read_timing("1 to 3", "Weeks after randomization")
        assert read.timing.unit == "week"

    def test_bare_range_with_no_unit_is_days_and_flagged(self):
        read = read_timing("1 to 3")
        assert read.timing.unit == "day"
        assert read.unit_defaulted

    @pytest.mark.parametrize("text", ["5 to 2", "Day 1 to Week 2"])
    def test_not_read(self, text):
        assert read_timing(text) is None


class TestUpTo:
    @pytest.mark.parametrize(
        "text, unit, n",
        [("≤28", "day", 28), ("<= 21", "day", 21), ("≤ 4 weeks", "week", 4)],
    )
    def test_read(self, text, unit, n):
        read = read_timing(text, "Days from randomization")
        assert (_kind(read), read.timing.unit, read.timing.n) == ("UpTo", unit, n)

    def test_no_unit_is_days_and_flagged(self):
        assert read_timing("≤28").unit_defaulted

    def test_with_trailing_words_is_not_read(self):
        assert read_timing("≤30 Days after Last Dose") is None


class TestWindowInTheTimingCell:
    @pytest.mark.parametrize(
        "text, value, window",
        [
            ("15 ± 3", 15, (3, 3, "day")),
            ("15±3", 15, (3, 3, "day")),
            ("30 (±3)", 30, (3, 3, "day")),
            ("Day 8 ±3 days", 8, (3, 3, "day")),
            ("Week 12 (±1 wk)", 12, (1, 1, "week")),
            ("Week 12 ± 3 days", 12, (3, 3, "day")),
            ("8 +/- 2", 8, (2, 2, "day")),
        ],
    )
    def test_read(self, text, value, window):
        read = read_timing(text, "Days")
        assert read.timing.value == value
        assert _window(read.window) == window

    def test_two_different_units_are_not_read(self):
        assert read_timing("Day 8 weeks ± 3") is None


class TestTimingNotRead:
    @pytest.mark.parametrize(
        "text",
        [
            None,
            "",
            "—",
            "Predose a",
            "Imaging",
            "At visit",
            "Cycle 2 Day 1",
            "C2D8",
            "CCI",
            "Every 12 weeks",
            "+30 (+7) after EOT",
            "9s",
            "Day 8.5",
        ],
    )
    def test_not_read(self, text):
        assert read_timing(text, "Days") is None


class TestWindow:
    @pytest.mark.parametrize(
        "text, window",
        [
            ("(±3 days)", (3, 3, "day")),
            ("±15 min", (15, 15, "minute")),
            ("±1 hr", (1, 1, "hour")),
            ("-1/+2 days", (1, 2, "day")),
            ("-1 d/+2 d", (1, 2, "day")),
            ("-3..+3 days", (3, 3, "day")),
            ("- 0 / + 2 hours", (0, 2, "hour")),
        ],
    )
    def test_with_a_unit(self, text, window):
        read = read_window(text, None, "week")
        assert _window(read.window) == window
        assert not read.unit_defaulted

    def test_no_unit_takes_the_window_row_label(self):
        read = read_window("±3", "Visit interval tolerance (days)", "week")
        assert _window(read.window) == (3, 3, "day")

    def test_no_unit_takes_the_timing_unit(self):
        read = read_window("+/-3", None, "week")
        assert _window(read.window) == (3, 3, "week")

    def test_no_unit_at_all_is_days_and_flagged(self):
        read = read_window("±3")
        assert _window(read.window) == (3, 3, "day")
        assert read.unit_defaulted

    def test_asymmetric_with_no_unit_takes_the_fallback(self):
        assert read_window("-1/+2", None, "hour").window.unit == "hour"

    @pytest.mark.parametrize(
        "text",
        [
            None,
            "---",
            "See Section 1.3",
            "Predose a",
            "±3 (28 to 34)",
            "d8; -1/+2d",
            "-1 d/+2 wk",
        ],
    )
    def test_not_read(self, text):
        assert read_window(text, None, "day") is None


class TestCycle:
    """Issue 66."""

    @pytest.mark.parametrize("text", ["Cycle 2", "Cycle2", "C2", "c 2", "2"])
    def test_single(self, text):
        cycle = read_cycle(text)
        assert type(cycle).__name__ == "CycleNumber" and cycle.n == 2

    @pytest.mark.parametrize(
        "text, start, end",
        [
            ("Cycle 3-6", 3, 6),
            ("Cycles 3-6", 3, 6),
            ("C3-C6", 3, 6),
            ("Cycle 3-n", 3, None),
            ("Cycle 3 - N", 3, None),
            ("Cycle 3+", 3, None),
            ("Cycles 2 and beyond", 2, None),
            ("Cycle 3 onwards", 3, None),
            ("Cycle 3 and subsequent", 3, None),
            ("Cycle 2-n (If combo therapy is held)", 2, None),
        ],
    )
    def test_range(self, text, start, end):
        cycle = read_cycle(text)
        assert type(cycle).__name__ == "CycleRange"
        assert (cycle.start, cycle.end) == (start, end)

    @pytest.mark.parametrize(
        "text",
        [
            None,
            "",
            "-",
            "Subsequent Cycles",
            "Short-term follow-up",
            "Study Cycle",
            "Cycle 6-3",
            "Cycle 1 Day 1",
            "D1",
        ],
    )
    def test_not_read(self, text):
        assert read_cycle(text) is None


class TestCycleLength:
    """Issue 66."""

    @pytest.mark.parametrize(
        "text, n, unit",
        [
            ("21 days", 21, "day"),
            ("21 day", 21, "day"),
            ("21-day", 21, "day"),
            ("21-day cycle", 21, "day"),
            ("28-day cycles", 28, "day"),
            ("Cycle = 21 days", 21, "day"),
            ("Cycle length: 21 days", 21, "day"),
            ("(21 days)", 21, "day"),
            ("4 weeks", 4, "week"),
            ("1 month", 1, "month"),
        ],
    )
    def test_read(self, text, n, unit):
        length = read_cycle_length(text)
        assert (length.n, length.unit) == (n, unit)

    @pytest.mark.parametrize(
        "text",
        [
            None,
            "",
            "21",
            "0 days",
            "Cycle = 21 days (or 28 days for Cohorts B & C per combination regimen)",
        ],
    )
    def test_not_read(self, text):
        assert read_cycle_length(text) is None
