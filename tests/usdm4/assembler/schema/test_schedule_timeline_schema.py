"""The timeline assembler's new input — issue 63, part 63.3.

Structure only: the schema does not parse patterns (the parse stage does), so
a pattern outside the grammar is accepted here. Specification:
``docs/timeline_assembler_design.md`` § 3.
"""

import pytest
from pydantic import ValidationError

from src.usdm4.assembler.schema.schedule_timeline_schema import (
    FAMILY,
    ColumnInput,
    HeaderValue,
    ScheduleTimelineInput,
    family_of,
)


def _timeline(**overrides) -> dict:
    data = {
        "type": "main",
        "title": "Schedule of Activities",
        "columns": [
            {
                "id": "c1",
                "epoch": {"text": "Screening", "pattern": "Screening"},
                "visit": {"text": "V1", "pattern": "V1"},
                "timing": {"text": "≤28", "pattern": "Day -28 to Day -1"},
            },
            {
                "id": "c2",
                "epoch": {"text": "Treatment", "pattern": "Treatment"},
                "visit": {"text": "C1 D8", "pattern": "D8"},
                "cycle": {"text": "Cycle 1", "pattern": "Cycle 1"},
                "cycle_length": {"text": "Cycle = 21 days", "pattern": "21 days"},
                "timing": {"text": "D8", "pattern": "Day 8"},
                "window": {"text": "(±3 days)", "pattern": "-3..+3 days"},
                "notes": [{"role": "timing_clarification", "text": "pre-dose"}],
                "markers": ["a"],
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
        assert timeline.columns[1].cycle.pattern == "Cycle 1"
        assert timeline.columns[1].notes[0].role == "timing_clarification"
        assert timeline.activities[1].cells[1].markers == ["c"]

    def test_minimal_timeline(self):
        timeline = ScheduleTimelineInput.model_validate({"type": "main"})
        assert timeline.columns == []
        assert timeline.activities == []

    def test_pattern_outside_the_grammar_is_structurally_fine(self):
        # The parse stage refuses it, not the schema.
        column = ColumnInput.model_validate(
            {"id": "c1", "timing": {"text": "D8", "pattern": "D8"}}
        )
        assert column.timing.pattern == "D8"

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


class TestHeaderValue:
    def test_text_and_pattern(self):
        value = HeaderValue(text="D 15", pattern="Day 15")
        assert value.label == "D 15"

    def test_pattern_only_labels_with_the_pattern(self):
        assert HeaderValue(pattern="Day 15").label == "Day 15"

    def test_text_only_is_an_unparseable_value(self):
        value = HeaderValue(text="As clinically indicated")
        assert value.pattern is None
        assert value.label == "As clinically indicated"

    @pytest.mark.parametrize(
        "data", [{}, {"text": ""}, {"text": "  ", "pattern": " "}, {"pattern": ""}]
    )
    def test_empty_value_refused(self, data):
        with pytest.raises(ValidationError):
            HeaderValue.model_validate(data)


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
        data["columns"][0]["value"] = 1  # a caller-parsed number
        with pytest.raises(ValidationError):
            ScheduleTimelineInput.model_validate(data)

    def test_unknown_header_value_key(self):
        with pytest.raises(ValidationError):
            HeaderValue.model_validate({"text": "Day 1", "value": 1})

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
