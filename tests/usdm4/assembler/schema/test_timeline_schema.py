from typing import ClassVar

from src.usdm4.assembler.schema.timeline_schema import (
    TimelineInput,
    ActivityItem,
    TimepointItem,
)


class TestTimelineInput:
    def test_defaults(self):
        t = TimelineInput()
        assert t.epochs.items == []
        assert t.visits.items == []

    def test_full_timeline(self):
        data = {
            "epochs": {
                "found": True,
                "items": [{"text": "Screening"}, {"text": "Treatment"}],
            },
            "visits": {
                "found": True,
                "items": [{"text": "Visit 1", "references": ["c1"]}],
            },
            "timepoints": {
                "items": [{"text": "Day 1", "value": 1, "unit": "day", "index": 0}]
            },
            "windows": {"items": [{"before": 1, "after": 1, "unit": "day"}]},
            "activities": {
                "items": [
                    {
                        "name": "Consent",
                        "visits": [{"index": 0, "references": []}],
                        "children": [],
                        "actions": {"bcs": ["Vital Signs"]},
                    }
                ]
            },
            "conditions": {"items": [{"reference": "c1", "text": "If applicable"}]},
        }
        result = TimelineInput.model_validate(data)
        assert len(result.epochs.items) == 2
        assert result.visits.items[0].text == "Visit 1"
        assert result.activities.items[0].name == "Consent"


class TestActivityItem:
    def test_nested_children(self):
        data = {
            "name": "Parent",
            "visits": [],
            "children": [
                {"name": "Child1", "visits": [{"index": 0, "references": []}]},
                {"name": "Child2", "visits": [{"index": 1, "references": []}]},
            ],
        }
        result = ActivityItem.model_validate(data)
        assert len(result.children) == 2
        assert result.children[0].name == "Child1"


class TestTimepointItem:
    def test_string_values_accepted(self):
        """Timeline assembler receives string index/value from extraction."""
        t = TimepointItem.model_validate(
            {"index": "0", "text": "Day 1", "value": "1", "unit": "days"}
        )
        assert t.text == "Day 1"

    def test_int_values_accepted(self):
        t = TimepointItem.model_validate(
            {"index": 0, "text": "Day 1", "value": 1, "unit": "days"}
        )
        assert t.value == 1


class TestTableClassificationFields:
    """The ``table_*`` fields must be DECLARED to survive validation.

    ``Assembler.execute`` validates with ``AssemblerInput.model_validate`` and
    passes ``model_dump()`` on, so pydantic's default ``extra="ignore"`` strips
    anything this model does not name. ``table_type`` and ``table_title`` were
    read by the timeline assembler while never reaching it through this path.
    """

    CLASSIFIED: ClassVar[dict[str, str]] = {
        "table_type": "profile",
        "table_title": "Profile — sampling for analysis",
        "table_description": (
            "Sampling or dosing profile: time running down a column, "
            "timed in minutes, printed away from the main schedule."
        ),
        "table_family": "unit_axis",
        "table_orientation": "vertical",
        "table_unit": "minute",
        "table_placement": "remote",
    }

    def test_all_seven_survive_a_dump(self):
        dumped = TimelineInput.model_validate(self.CLASSIFIED).model_dump(by_alias=True)
        assert {k: dumped[k] for k in self.CLASSIFIED} == self.CLASSIFIED

    def test_table_type_reaches_the_assembler(self):
        """The one that steers which timeline is the main one."""
        dumped = TimelineInput.model_validate({"table_type": "main_soa"}).model_dump()
        assert dumped["table_type"] == "main_soa"

    def test_an_unclassified_table_dumps_them_all_as_none(self):
        """The assembler reads them with ``.get()`` and falls back, so None is
        the same as absent to every consumer."""
        dumped = TimelineInput.model_validate({}).model_dump()
        assert all(dumped[k] is None for k in self.CLASSIFIED)

    def test_the_feature_blocks_are_untouched(self):
        t = TimelineInput.model_validate(
            {"epochs": {"found": True, "items": [{"text": "Screening"}]}, **self.CLASSIFIED}
        )
        assert t.epochs.found is True
        assert t.epochs.items[0].text == "Screening"
        assert t.table_family == "unit_axis"
