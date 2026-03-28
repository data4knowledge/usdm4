from src.usdm4.assembler.schema.timeline_schema import (
    TimelineInput,
    ActivityItem,
    TimepointItem,
    EpochsBlock,
    VisitsBlock,
)


class TestTimelineInput:

    def test_defaults(self):
        t = TimelineInput()
        assert t.epochs.items == []
        assert t.visits.items == []

    def test_full_timeline(self):
        data = {
            "epochs": {"found": True, "items": [{"text": "Screening"}, {"text": "Treatment"}]},
            "visits": {"found": True, "items": [{"text": "Visit 1", "references": ["c1"]}]},
            "timepoints": {"items": [{"text": "Day 1", "value": 1, "unit": "day", "index": 0}]},
            "windows": {"items": [{"before": 1, "after": 1, "unit": "day"}]},
            "activities": {"items": [
                {
                    "name": "Consent",
                    "visits": [{"index": 0, "references": []}],
                    "children": [],
                    "actions": {"bcs": ["Vital Signs"]},
                }
            ]},
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
        t = TimepointItem.model_validate({"index": "0", "text": "Day 1", "value": "1", "unit": "days"})
        assert t.text == "Day 1"

    def test_int_values_accepted(self):
        t = TimepointItem.model_validate({"index": 0, "text": "Day 1", "value": 1, "unit": "days"})
        assert t.value == 1
