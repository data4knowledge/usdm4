"""The timeline assembler's input — issue 63, part 63.3; issue 64; structured
in issue 73 (U4-35).

Every header value is a structured object carrying its printed ``text``,
``markers`` and ``redacted``; the caller structures, ``usdm4`` never reads
text. Specification: ``docs/timeline_assembler_design.md`` § 3, § 9 U4-35.
"""

import pytest
from pydantic import ValidationError

from src.usdm4.assembler.schema.schedule_timeline_schema import (
    FAMILY,
    HEADER_FIELDS,
    VALUE_FIELDS,
    ColumnInput,
    CycleValue,
    DelayValue,
    LabelValue,
    QuantityValue,
    ScheduleTimelineInput,
    TimingValue,
    WindowValue,
    family_of,
)


def _timeline(**overrides) -> dict:
    data = {
        "type": "main",
        "title": "Schedule of Activities",
        "columns": [
            {
                "id": "c1",
                "epoch": {"text": "Screening"},
                "visit": {"text": "V1"},
                "timing": {"text": "≤28", "start": -28, "end": -1, "unit": "days"},
            },
            {
                "id": "c2",
                "epoch": {"text": "Treatment"},
                "visit": {"text": "C1 D8", "markers": ["a"]},
                "cycle": {"text": "Cycle 1", "first": 1, "last": 1},
                "cycle_length": {
                    "text": "Cycle = 21 days",
                    "value": 21,
                    "unit": "days",
                },
                "timing": {"text": "D8", "value": 8, "unit": "days"},
                "window": {
                    "text": "(±3 days)",
                    "before": 3,
                    "after": 3,
                    "unit": "days",
                },
                "notes": [{"role": "timing_clarification", "text": "pre-dose"}],
            },
        ],
        "activities": [
            {"name": "Laboratory"},
            {
                "name": "Haematology",
                "parent": "Laboratory",
                "markers": ["b"],
                "bcs": ["Haemoglobin"],
                "cells": [
                    {"column": "c1", "text": "X"},
                    {"column": "c2", "text": "X", "markers": ["c"]},
                ],
            },
        ],
        "footnotes": [
            {"marker": "a", "text": "Within 3 days."},
            {"marker": "b", "text": "Local lab."},
            {"marker": "c", "text": "Pre-dose."},
        ],
    }
    data.update(overrides)
    return data


class TestAccepted:
    def test_full_timeline(self):
        timeline = ScheduleTimelineInput.model_validate(_timeline())
        assert timeline.type == "main"
        assert timeline.family == "planned"
        assert [c.id for c in timeline.columns] == ["c1", "c2"]
        assert timeline.columns[1].cycle.first == 1
        assert timeline.columns[0].timing.is_range
        assert timeline.columns[1].timing.structured
        assert timeline.columns[1].notes[0].role == "timing_clarification"
        assert timeline.activities[1].cells[1].markers == ["c"]
        assert timeline.columns[1].visit.markers == ["a"]
        assert timeline.rows == {}
        assert timeline.day_zero is False

    def test_minimal_timeline(self):
        timeline = ScheduleTimelineInput.model_validate({"type": "main"})
        assert timeline.columns == []
        assert timeline.activities == []

    def test_day_zero_flag(self):
        timeline = ScheduleTimelineInput.model_validate(_timeline(day_zero=True))
        assert timeline.day_zero is True

    def test_a_delay_column(self):
        column = ColumnInput.model_validate(
            {
                "id": "c1",
                "visit": {"text": "(7-28 days between doses)"},
                "delay": {"min": 7, "max": 28, "unit": "days"},
            }
        )
        assert (column.delay.min, column.delay.max) == (7, 28)

    def test_round_trip_through_model_dump(self):
        timeline = ScheduleTimelineInput.model_validate(_timeline())
        again = ScheduleTimelineInput.model_validate(timeline.model_dump())
        assert again == timeline

    def test_profile_may_attach_to_an_activity_on_another_timeline(self):
        timeline = ScheduleTimelineInput.model_validate(
            _timeline(type="profile", attaches_to="PK dosing")
        )
        assert timeline.attaches_to == "PK dosing"

    @pytest.mark.parametrize(
        "timeline_type", ["unscheduled", "early_termination", "adverse_event"]
    )
    def test_conditional_timeline_takes_an_entry_condition(self, timeline_type):
        timeline = ScheduleTimelineInput.model_validate(
            _timeline(type=timeline_type, entry_condition="If withdrawn early")
        )
        assert timeline.entry_condition == "If withdrawn early"

    def test_classification(self):
        timeline = ScheduleTimelineInput.model_validate(
            _timeline(
                type="profile",
                classification={
                    "orientation": "transposed",
                    "unit": "hour",
                    "placement": "away",
                },
            )
        )
        assert timeline.classification.orientation == "transposed"


class TestRows:
    """Issue 64 — each header row's printed label, keyed by header field."""

    def test_header_fields(self):
        assert HEADER_FIELDS == (
            "epoch",
            "visit",
            "cycle",
            "cycle_length",
            "timing",
            "window",
        )

    def test_rows_accepted(self):
        rows = {
            "timing": "Days from randomization",
            "window": "Visit interval tolerance (days)",
        }
        timeline = ScheduleTimelineInput.model_validate(_timeline(rows=rows))
        assert timeline.rows == rows

    def test_every_header_field_is_a_row_key(self):
        rows = {name: f"{name} label" for name in HEADER_FIELDS}
        assert ScheduleTimelineInput.model_validate(_timeline(rows=rows)).rows == rows

    @pytest.mark.parametrize("key", ["timepoint", "Timing", "notes", ""])
    def test_unknown_row_key_refused(self, key):
        with pytest.raises(ValidationError, match="rows"):
            ScheduleTimelineInput.model_validate(_timeline(rows={key: "x"}))


class TestValues:
    """U4-35: structured, text only, or redacted — never a mix."""

    def test_value_fields(self):
        assert VALUE_FIELDS == HEADER_FIELDS + ("delay",)

    def test_markers_and_text_default_empty(self):
        value = TimingValue(value=1, unit="days")
        assert (value.text, value.markers, value.redacted) == ("", [], False)

    @pytest.mark.parametrize(
        "model, data",
        [
            (TimingValue, {"value": 1, "unit": "days"}),
            (TimingValue, {"start": -3, "end": 3, "unit": "days"}),
            (WindowValue, {"before": 0, "after": 0, "unit": "hours"}),
            (CycleValue, {"first": 3}),
            (CycleValue, {"first": 1, "last": 6}),
            (QuantityValue, {"value": 4, "unit": "weeks"}),
            (DelayValue, {"min": 2, "max": 10, "unit": "days"}),
            (DelayValue, {"min": 2, "unit": "days"}),
        ],
    )
    def test_structured(self, model, data):
        assert model.model_validate(data).structured

    @pytest.mark.parametrize(
        "model", [TimingValue, WindowValue, CycleValue, QuantityValue, DelayValue]
    )
    def test_text_only_is_not_structured(self, model):
        value = model.model_validate({"text": "As clinically indicated"})
        assert not value.structured

    @pytest.mark.parametrize(
        "model",
        [LabelValue, TimingValue, WindowValue, CycleValue, QuantityValue, DelayValue],
    )
    def test_redacted_needs_no_text_and_is_not_structured(self, model):
        value = model.model_validate({"redacted": True})
        assert value.redacted
        if model is not LabelValue:
            assert not value.structured

    @pytest.mark.parametrize(
        "model",
        [LabelValue, TimingValue, WindowValue, CycleValue, QuantityValue, DelayValue],
    )
    @pytest.mark.parametrize("data", [{}, {"text": ""}, {"text": "  "}])
    def test_an_empty_value_is_refused(self, model, data):
        with pytest.raises(ValidationError, match="null"):
            model.model_validate(data)

    @pytest.mark.parametrize(
        "model, data",
        [
            (TimingValue, {"value": 1, "unit": "days"}),
            (WindowValue, {"before": 1, "after": 1, "unit": "days"}),
            (CycleValue, {"first": 1}),
            (QuantityValue, {"value": 21, "unit": "days"}),
            (DelayValue, {"min": 2, "unit": "days"}),
        ],
    )
    def test_redacted_with_structure_is_refused(self, model, data):
        with pytest.raises(ValidationError, match="redacted"):
            model.model_validate({**data, "redacted": True})

    @pytest.mark.parametrize(
        "model, data, match",
        [
            (TimingValue, {"value": 1}, "unit"),
            (TimingValue, {"unit": "days"}, "a value, or a start and an end"),
            (
                TimingValue,
                {"value": 1, "start": 1, "end": 2, "unit": "days"},
                "not both",
            ),
            (TimingValue, {"start": 1, "unit": "days"}, "both its start and its end"),
            (TimingValue, {"start": 3, "end": 1, "unit": "days"}, "before its start"),
            (WindowValue, {"before": 1, "unit": "days"}, "missing"),
            (WindowValue, {"before": -1, "after": 1, "unit": "days"}, "negative"),
            (CycleValue, {"last": 3}, "missing"),
            (CycleValue, {"first": -1}, "negative"),
            (CycleValue, {"first": 3, "last": 2}, "before its first"),
            (QuantityValue, {"value": 21}, "missing"),
            (QuantityValue, {"value": 0, "unit": "days"}, "more than 0"),
            (DelayValue, {"max": 10, "unit": "days"}, "missing"),
            (DelayValue, {"min": -1, "unit": "days"}, "negative"),
            (DelayValue, {"min": 5, "max": 2, "unit": "days"}, "less than its min"),
        ],
    )
    def test_bad_structure_is_refused(self, model, data, match):
        with pytest.raises(ValidationError, match=match):
            model.model_validate(data)

    @pytest.mark.parametrize("unit", ["day", "Days", "d", "cycles", "months "])
    def test_only_the_plural_units_are_accepted(self, unit):
        with pytest.raises(ValidationError):
            TimingValue.model_validate({"value": 1, "unit": unit})

    @pytest.mark.parametrize(
        "unit", ["minutes", "hours", "days", "weeks", "months", "years"]
    )
    def test_the_units(self, unit):
        assert TimingValue.model_validate({"value": 1, "unit": unit}).unit == unit

    def test_timing_point_and_range(self):
        assert not TimingValue(value=1, unit="days").is_range
        assert TimingValue(start=1, end=3, unit="days").is_range

    def test_cycle_single_range_and_open(self):
        assert not CycleValue(first=2, last=2).is_range
        assert CycleValue(first=1, last=6).is_range
        assert CycleValue(first=3).is_range

    def test_the_pattern_key_is_gone(self):
        with pytest.raises(ValidationError):
            TimingValue.model_validate({"text": "Day 1", "pattern": "Day 1"})


class TestRefused:
    def test_unknown_timeline_type(self):
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(_timeline(type="main_soa"))

    def test_type_is_required(self):
        data = _timeline()
        del data["type"]
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(data)

    @pytest.mark.parametrize(
        "extra",
        [
            {"table_type": "main_soa"},  # the old input's key
            {"family": "planned"},  # derived, never supplied
            {"epochs": {"items": []}},  # the old input's block
        ],
    )
    def test_unknown_timeline_key(self, extra):
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(_timeline(**extra))

    def test_unknown_column_key(self):
        data = _timeline()
        data["columns"][0]["value"] = 1  # not a column field
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(data)

    def test_markers_on_the_column_refused(self):
        # Issue 64: markers moved onto the header value they are printed on.
        data = _timeline()
        data["columns"][0]["markers"] = ["a"]
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(data)

    def test_unknown_value_key(self):
        with pytest.raises(ValidationError):
            TimingValue.model_validate({"text": "Day 1", "value": 1, "day": 1})

    @pytest.mark.parametrize("field", ["timing", "window"])
    def test_a_delay_with_a_timing_or_window_is_refused(self, field):
        data = {
            "id": "c1",
            "delay": {"min": 2, "unit": "days"},
            field: {"text": "x"},
        }
        with pytest.raises(ValidationError, match="no anchored time"):
            ColumnInput.model_validate(data)

    def test_duplicate_column_id(self):
        data = _timeline()
        data["columns"][1]["id"] = "c1"
        with pytest.raises(ValidationError, match="unique"):
            ScheduleTimelineInput.model_validate(data)

    def test_blank_column_id(self):
        with pytest.raises(ValidationError):
            ColumnInput.model_validate({"id": "  "})

    def test_cell_in_unknown_column(self):
        data = _timeline()
        data["activities"][1]["cells"][0]["column"] = "c9"
        with pytest.raises(ValidationError, match="c9"):
            ScheduleTimelineInput.model_validate(data)

    def test_two_cells_in_one_column(self):
        data = _timeline()
        data["activities"][1]["cells"][1]["column"] = "c1"
        with pytest.raises(ValidationError, match="two cells"):
            ScheduleTimelineInput.model_validate(data)

    def test_unknown_parent(self):
        data = _timeline()
        data["activities"][1]["parent"] = "Chemistry"
        with pytest.raises(ValidationError, match="Chemistry"):
            ScheduleTimelineInput.model_validate(data)

    def test_blank_activity_name(self):
        data = _timeline()
        data["activities"][0]["name"] = " "
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(data)

    def test_duplicate_footnote_marker(self):
        data = _timeline()
        data["footnotes"].append({"marker": "a", "text": "Again."})
        with pytest.raises(ValidationError, match="unique"):
            ScheduleTimelineInput.model_validate(data)

    def test_attaches_to_on_a_non_profile(self):
        with pytest.raises(ValidationError, match="profile"):
            ScheduleTimelineInput.model_validate(_timeline(attaches_to="PK dosing"))

    @pytest.mark.parametrize("timeline_type", ["main", "arm", "profile"])
    def test_entry_condition_on_a_non_conditional(self, timeline_type):
        with pytest.raises(ValidationError, match="conditional"):
            ScheduleTimelineInput.model_validate(
                _timeline(type=timeline_type, entry_condition="If withdrawn")
            )


class TestFamily:
    @pytest.mark.parametrize(
        "timeline_type, family",
        [
            ("main", "planned"),
            ("extension_study", "planned"),
            ("continued_access", "planned"),
            ("arm", "variant"),
            ("cohort", "variant"),
            ("unscheduled", "conditional"),
            ("early_termination", "conditional"),
            ("adverse_event", "conditional"),
            ("profile", "profile"),
            ("unclassified", "unclassified"),
        ],
    )
    def test_family_of(self, timeline_type, family):
        assert family_of(timeline_type) == family

    def test_every_type_has_a_family(self):
        types = ScheduleTimelineInput.model_fields["type"].annotation.__args__
        assert set(types) == set(FAMILY)
