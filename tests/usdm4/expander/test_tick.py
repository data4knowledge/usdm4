from usdm4.expander.tick import Tick
import pytest


class TestTick:
    def test_init_with_duration_years(self):
        """Test initialization with years duration (P1Y)."""
        tick = Tick(duration="P1Y")
        # 1 year = 365 days * 24 hours * 60 minutes * 60 seconds
        assert tick.tick == 365 * 24 * 60 * 60

    def test_init_with_duration_multiple_years(self):
        """Test initialization with multiple years duration (P5Y)."""
        tick = Tick(duration="P5Y")
        assert tick.tick == 5 * 365 * 24 * 60 * 60

    def test_init_with_duration_months(self):
        """Test initialization with months duration (P1M)."""
        tick = Tick(duration="P1M")
        # 1 month = 30 days * 24 hours * 60 minutes * 60 seconds
        assert tick.tick == 30 * 24 * 60 * 60

    def test_init_with_duration_multiple_months(self):
        """Test initialization with multiple months duration (P6M)."""
        tick = Tick(duration="P6M")
        assert tick.tick == 6 * 30 * 24 * 60 * 60

    def test_init_with_duration_weeks(self):
        """Test initialization with weeks duration (P1W)."""
        tick = Tick(duration="P1W")
        # 1 week = 7 days * 24 hours * 60 minutes * 60 seconds
        assert tick.tick == 7 * 24 * 60 * 60

    def test_init_with_duration_multiple_weeks(self):
        """Test initialization with multiple weeks duration (P4W)."""
        tick = Tick(duration="P4W")
        assert tick.tick == 4 * 7 * 24 * 60 * 60

    def test_init_with_duration_days(self):
        """Test initialization with days duration (P1D)."""
        tick = Tick(duration="P1D")
        # 1 day = 24 hours * 60 minutes * 60 seconds
        assert tick.tick == 24 * 60 * 60

    def test_init_with_duration_multiple_days(self):
        """Test initialization with multiple days duration (P7D)."""
        tick = Tick(duration="P7D")
        assert tick.tick == 7 * 24 * 60 * 60

    def test_init_with_duration_hours(self):
        """Test initialization with hours duration (PT1H)."""
        tick = Tick(duration="PT1H")
        # 1 hour = 60 minutes * 60 seconds
        assert tick.tick == 60 * 60

    def test_init_with_duration_multiple_hours(self):
        """Test initialization with multiple hours duration (PT12H)."""
        tick = Tick(duration="PT12H")
        assert tick.tick == 12 * 60 * 60

    def test_init_with_duration_minutes(self):
        """Test initialization with minutes duration (PT1M)."""
        tick = Tick(duration="PT1M")
        # 1 minute = 60 seconds
        assert tick.tick == 60

    def test_init_with_duration_multiple_minutes(self):
        """Test initialization with multiple minutes duration (PT30M)."""
        tick = Tick(duration="PT30M")
        assert tick.tick == 30 * 60

    def test_init_with_duration_seconds(self):
        """Test initialization with seconds duration (PT1S)."""
        tick = Tick(duration="PT1S")
        assert tick.tick == 1

    def test_init_with_duration_multiple_seconds(self):
        """Test initialization with multiple seconds duration (PT90S)."""
        tick = Tick(duration="PT90S")
        assert tick.tick == 90

    def test_init_with_value(self):
        """Test initialization with tick value."""
        tick = Tick(value=1000)
        assert tick.tick == 1000

    def test_init_with_zero_value(self):
        """Test initialization with zero value."""
        tick = Tick(value=0)
        assert tick.tick == 0

    def test_init_with_large_value(self):
        """Test initialization with large tick value."""
        tick = Tick(value=1000000)
        assert tick.tick == 1000000

    def test_init_with_no_parameters(self):
        """Test initialization with no parameters defaults to 0."""
        tick = Tick()
        assert tick.tick == 0

    def test_init_duration_takes_precedence(self):
        """Test that duration parameter takes precedence over value."""
        tick = Tick(duration="P1D", value=1000)
        # Should use duration, not value
        assert tick.tick == 24 * 60 * 60

    def test_tick_property(self):
        """Test tick property getter."""
        tick = Tick(value=500)
        assert tick.tick == 500

    def test_str_with_zero(self):
        """Test string representation of zero ticks."""
        tick = Tick(value=0)
        assert str(tick) == ""

    def test_str_with_one_second(self):
        """Test string representation of 1 second."""
        tick = Tick(value=1)
        assert str(tick) == "1 second"

    def test_str_with_multiple_seconds(self):
        """Test string representation of multiple seconds."""
        tick = Tick(value=45)
        assert str(tick) == "45 seconds"

    def test_str_with_one_minute(self):
        """Test string representation of 1 minute."""
        tick = Tick(value=60)
        assert str(tick) == "1 minute"

    def test_str_with_multiple_minutes(self):
        """Test string representation of multiple minutes."""
        tick = Tick(value=300)  # 5 minutes
        assert str(tick) == "5 minutes"

    def test_str_with_one_hour(self):
        """Test string representation of 1 hour."""
        tick = Tick(value=3600)
        assert str(tick) == "1 hour"

    def test_str_with_multiple_hours(self):
        """Test string representation of multiple hours."""
        tick = Tick(value=7200)  # 2 hours
        assert str(tick) == "2 hours"

    def test_str_with_one_day(self):
        """Test string representation of 1 day."""
        tick = Tick(value=86400)
        assert str(tick) == "1 day"

    def test_str_with_multiple_days(self):
        """Test string representation of multiple days."""
        tick = Tick(value=259200)  # 3 days
        assert str(tick) == "3 days"

    def test_str_with_one_week(self):
        """Test string representation of 1 week."""
        tick = Tick(value=604800)
        assert str(tick) == "1 week"

    def test_str_with_multiple_weeks(self):
        """Test string representation of multiple weeks."""
        tick = Tick(value=1209600)  # 2 weeks
        assert str(tick) == "2 weeks"

    def test_str_with_mixed_units(self):
        """Test string representation with mixed time units."""
        # 1 week + 2 days + 3 hours + 4 minutes + 5 seconds
        tick = Tick(value=604800 + 172800 + 10800 + 240 + 5)
        assert str(tick) == "1 week, 2 days, 3 hours, 4 minutes, 5 seconds"

    def test_str_with_weeks_and_days(self):
        """Test string representation with weeks and days."""
        tick = Tick(value=604800 + 86400)  # 1 week + 1 day
        assert str(tick) == "1 week, 1 day"

    def test_str_with_days_and_hours(self):
        """Test string representation with days and hours."""
        tick = Tick(value=86400 + 3600)  # 1 day + 1 hour
        assert str(tick) == "1 day, 1 hour"

    def test_str_with_hours_and_minutes(self):
        """Test string representation with hours and minutes."""
        tick = Tick(value=3600 + 60)  # 1 hour + 1 minute
        assert str(tick) == "1 hour, 1 minute"

    def test_str_with_minutes_and_seconds(self):
        """Test string representation with minutes and seconds."""
        tick = Tick(value=60 + 1)  # 1 minute + 1 second
        assert str(tick) == "1 minute, 1 second"

    def test_str_with_complex_duration(self):
        """Test string representation with complex duration."""
        # 2 weeks + 5 days + 12 hours + 30 minutes + 45 seconds
        tick = Tick(value=1209600 + 432000 + 43200 + 1800 + 45)
        assert str(tick) == "2 weeks, 5 days, 12 hours, 30 minutes, 45 seconds"

    def test_str_singular_plural_handling(self):
        """Test that singular/plural forms are handled correctly."""
        tick1 = Tick(value=1)
        tick2 = Tick(value=2)
        assert "second" in str(tick1) and "seconds" not in str(tick1)
        assert "seconds" in str(tick2)

    def test_duration_to_ticks_invalid_pt_format(self):
        """Test _duration_to_ticks with invalid PT format."""
        tick = Tick()
        with pytest.raises(Exception) as excinfo:
            tick._duration_to_ticks("PT1X")
        assert "Failed to decode duration" in str(excinfo.value)

    def test_duration_to_ticks_invalid_p_format(self):
        """Test _duration_to_ticks with invalid P format."""
        tick = Tick()
        with pytest.raises(Exception) as excinfo:
            tick._duration_to_ticks("P1X")
        assert "Failed to decode duration" in str(excinfo.value)

    def test_duration_to_ticks_missing_pt_prefix(self):
        """Test _duration_to_ticks with time unit but missing PT prefix."""
        tick = Tick()
        with pytest.raises(Exception) as excinfo:
            tick._duration_to_ticks("1H")
        assert "Failed to decode duration" in str(excinfo.value)

    def test_duration_to_ticks_zero_years(self):
        """Test _duration_to_ticks with P0Y."""
        tick = Tick(duration="P0Y")
        assert tick.tick == 0

    def test_duration_to_ticks_zero_days(self):
        """Test _duration_to_ticks with P0D."""
        tick = Tick(duration="P0D")
        assert tick.tick == 0

    def test_duration_to_ticks_zero_hours(self):
        """Test _duration_to_ticks with PT0H."""
        tick = Tick(duration="PT0H")
        assert tick.tick == 0

    def test_duration_years_calculation(self):
        """Test year calculation accuracy."""
        tick = Tick(duration="P2Y")
        assert tick.tick == 2 * 365 * 24 * 60 * 60

    def test_duration_months_calculation(self):
        """Test month calculation accuracy."""
        tick = Tick(duration="P3M")
        assert tick.tick == 3 * 30 * 24 * 60 * 60

    def test_duration_weeks_calculation(self):
        """Test week calculation accuracy."""
        tick = Tick(duration="P2W")
        assert tick.tick == 2 * 7 * 24 * 60 * 60

    def test_duration_days_calculation(self):
        """Test day calculation accuracy."""
        tick = Tick(duration="P10D")
        assert tick.tick == 10 * 24 * 60 * 60

    def test_duration_hours_calculation(self):
        """Test hour calculation accuracy."""
        tick = Tick(duration="PT24H")
        assert tick.tick == 24 * 60 * 60

    def test_duration_minutes_calculation(self):
        """Test minute calculation accuracy."""
        tick = Tick(duration="PT120M")
        assert tick.tick == 120 * 60

    def test_duration_seconds_calculation(self):
        """Test second calculation accuracy."""
        tick = Tick(duration="PT3600S")
        assert tick.tick == 3600

    def test_round_trip_conversion_days(self):
        """Test converting from duration to ticks and back to string."""
        tick = Tick(duration="P7D")
        assert str(tick) == "1 week"

    def test_round_trip_conversion_hours(self):
        """Test converting from duration to ticks and back to string."""
        tick = Tick(duration="PT24H")
        assert str(tick) == "1 day"

    def test_round_trip_conversion_minutes(self):
        """Test converting from duration to ticks and back to string."""
        tick = Tick(duration="PT60M")
        assert str(tick) == "1 hour"

    def test_edge_case_large_year(self):
        """Test with a large number of years."""
        tick = Tick(duration="P100Y")
        expected = 100 * 365 * 24 * 60 * 60
        assert tick.tick == expected

    def test_edge_case_large_seconds(self):
        """Test with a large number of seconds."""
        tick = Tick(duration="PT1000000S")
        assert tick.tick == 1000000

    def test_immutability_of_tick_property(self):
        """Test that tick property returns consistent value."""
        tick = Tick(value=12345)
        first_call = tick.tick
        second_call = tick.tick
        assert first_call == second_call == 12345

    def test_string_representation_consistency(self):
        """Test that string representation is consistent."""
        tick = Tick(value=90061)  # 1 day + 1 hour + 1 minute + 1 second
        first_str = str(tick)
        second_str = str(tick)
        assert first_str == second_str

    def test_iso8601_duration_format_pt_prefix(self):
        """Test ISO 8601 duration format with PT prefix."""
        # PT indicates time component
        tick_h = Tick(duration="PT5H")
        tick_m = Tick(duration="PT30M")
        tick_s = Tick(duration="PT45S")

        assert tick_h.tick == 5 * 60 * 60
        assert tick_m.tick == 30 * 60
        assert tick_s.tick == 45

    def test_iso8601_duration_format_p_prefix(self):
        """Test ISO 8601 duration format with P prefix."""
        # P indicates date component
        tick_y = Tick(duration="P1Y")
        tick_m = Tick(duration="P2M")
        tick_w = Tick(duration="P3W")
        tick_d = Tick(duration="P4D")

        assert tick_y.tick == 365 * 24 * 60 * 60
        assert tick_m.tick == 2 * 30 * 24 * 60 * 60
        assert tick_w.tick == 3 * 7 * 24 * 60 * 60
        assert tick_d.tick == 4 * 24 * 60 * 60

    def test_different_instances_independent(self):
        """Test that different Tick instances are independent."""
        tick1 = Tick(value=100)
        tick2 = Tick(value=200)
        tick3 = Tick(duration="P1D")

        assert tick1.tick == 100
        assert tick2.tick == 200
        assert tick3.tick == 86400
        # Verify they don't interfere with each other
        assert tick1.tick == 100

    def test_str_no_trailing_comma(self):
        """Test that string representation has no trailing comma."""
        tick = Tick(value=3661)  # 1 hour, 1 minute, 1 second
        result = str(tick)
        assert not result.endswith(",")
        assert not result.startswith(",")
