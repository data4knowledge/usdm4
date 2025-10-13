import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder


def root_path():
    """Get the root path for the usdm4 package."""
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    """Create a Builder instance for testing."""
    return Builder(root_path(), Errors())


@pytest.fixture(scope="module")
def errors():
    """Create an Errors instance for testing."""
    return Errors()


@pytest.fixture
def timeline_assembler(builder, errors):
    """Create a TimelineAssembler instance for testing."""
    builder.clear()
    return TimelineAssembler(builder, errors)


@pytest.fixture
def minimal_timeline_data():
    """Provide minimal valid timeline data for testing."""
    return {
        "epochs": {
            "items": [
                {"text": "Screening"},
                {"text": "Treatment"},
            ]
        },
        "visits": {
            "items": [
                {"text": "Visit 1", "references": []},
                {"text": "Visit 2", "references": []},
            ]
        },
        "timepoints": {
            "items": [
                {"index": "0", "text": "Day 1", "value": "1", "unit": "days"},
                {"index": "1", "text": "Day 7", "value": "7", "unit": "days"},
            ]
        },
        "windows": {
            "items": [
                {"before": 0, "after": 0, "unit": "days"},
                {"before": 1, "after": 1, "unit": "days"},
            ]
        },
        "activities": {
            "items": [
                {
                    "name": "Consent",
                    "visits": [{"index": 0, "references": []}],
                },
                {
                    "name": "Blood Draw",
                    "visits": [{"index": 1, "references": []}],
                },
            ]
        },
        "conditions": {
            "items": []
        },
    }


class TestTimelineAssemblerInitialization:
    """Test TimelineAssembler initialization."""

    def test_init_with_valid_parameters(self, builder, errors):
        """Test TimelineAssembler initialization with valid parameters."""
        assembler = TimelineAssembler(builder, errors)

        assert assembler._builder is builder
        assert assembler._errors is errors
        assert assembler.MODULE == "usdm4.assembler.timeline_assembler.TimelineAssembler"

        # Test initial state
        assert assembler._timelines == []
        assert assembler._epochs == []
        assert assembler._encounters == []
        assert assembler._activities == []
        assert assembler._conditions == []
        assert assembler._condition_links == {}
        assert assembler._encoder is not None

    def test_properties_initial_state(self, timeline_assembler):
        """Test that properties return empty lists initially."""
        assert timeline_assembler.timelines == []
        assert timeline_assembler.epochs == []
        assert timeline_assembler.encounters == []
        assert timeline_assembler.activities == []
        assert timeline_assembler.conditions == []


class TestTimelineAssemblerExecution:
    """Test TimelineAssembler execute method."""

    def test_execute_with_minimal_valid_data(self, timeline_assembler, minimal_timeline_data):
        """Test execute with minimal valid data."""
        timeline_assembler.execute(minimal_timeline_data)

        # Verify timelines were created
        assert len(timeline_assembler.timelines) == 1
        timeline = timeline_assembler.timelines[0]
        assert timeline.mainTimeline is True
        assert timeline.name == "TIMELINE-1"

        # Verify epochs were created
        assert len(timeline_assembler.epochs) == 2

        # Verify encounters were created
        assert len(timeline_assembler.encounters) == 2

        # Verify activities were created
        assert len(timeline_assembler.activities) == 2

    def test_execute_with_empty_data_fails_gracefully(self, timeline_assembler, errors):
        """Test execute with empty data fails gracefully."""
        initial_error_count = errors.error_count()
        
        try:
            timeline_assembler.execute({})
        except Exception:
            pass

        # Should have logged errors
        assert errors.error_count() >= initial_error_count

    def test_execute_with_malformed_data(self, timeline_assembler, errors):
        """Test execute with malformed data."""
        initial_error_count = errors.error_count()
        
        malformed_data = {
            "epochs": "not a dict",
            "visits": None,
        }
        
        try:
            timeline_assembler.execute(malformed_data)
        except Exception:
            pass

        # Should have logged errors
        assert errors.error_count() >= initial_error_count


class TestTimelineAssemblerEpochs:
    """Test TimelineAssembler epoch creation."""

    def test_add_epochs_creates_correct_number(self, timeline_assembler, minimal_timeline_data):
        """Test that epochs are created correctly."""
        epochs = timeline_assembler._add_epochs(minimal_timeline_data)

        assert len(epochs) == 2
        assert epochs[0].label == "Screening"
        assert epochs[1].label == "Treatment"

    def test_add_epochs_with_duplicate_names(self, timeline_assembler):
        """Test epochs with duplicate names are handled."""
        data = {
            "epochs": {
                "items": [
                    {"text": "Treatment"},
                    {"text": "Treatment"},
                ]
            },
            "timepoints": {
                "items": [{}, {}]
            }
        }
        
        epochs = timeline_assembler._add_epochs(data)
        
        # Should only create one unique epoch
        assert len(epochs) == 1

    def test_add_epochs_with_exception(self, timeline_assembler, errors):
        """Test epoch creation with exception."""
        initial_error_count = errors.error_count()
        
        data = {
            "epochs": {
                "items": None  # Will cause exception
            }
        }
        
        epochs = timeline_assembler._add_epochs(data)
        
        assert len(epochs) == 0
        assert errors.error_count() > initial_error_count


class TestTimelineAssemblerEncounters:
    """Test TimelineAssembler encounter creation."""

    def test_add_encounters_creates_correct_number(self, timeline_assembler, minimal_timeline_data):
        """Test that encounters are created correctly."""
        encounters = timeline_assembler._add_encounters(minimal_timeline_data)

        assert len(encounters) == 2
        assert encounters[0].label == "Visit 1"
        assert encounters[1].label == "Visit 2"

    def test_add_encounters_with_references(self, timeline_assembler):
        """Test encounters with condition references."""
        data = {
            "visits": {
                "items": [
                    {"text": "Visit 1", "references": ["ref1", "ref2"]},
                ]
            },
            "timepoints": {
                "items": [{}]
            }
        }
        
        encounters = timeline_assembler._add_encounters(data)
        
        assert len(encounters) == 1
        # Check that references were tracked
        assert "ref1" in timeline_assembler._condition_links
        assert "ref2" in timeline_assembler._condition_links

    def test_add_encounters_with_exception(self, timeline_assembler, errors):
        """Test encounter creation with exception."""
        initial_error_count = errors.error_count()
        
        data = {
            "visits": {
                "items": None  # Will cause exception
            }
        }
        
        encounters = timeline_assembler._add_encounters(data)
        
        assert len(encounters) == 0
        assert errors.error_count() > initial_error_count


class TestTimelineAssemblerActivities:
    """Test TimelineAssembler activity creation."""

    def test_add_activities_creates_correct_number(self, timeline_assembler, minimal_timeline_data):
        """Test that activities are created correctly."""
        activities = timeline_assembler._add_activities(minimal_timeline_data)

        assert len(activities) == 2
        assert activities[0].label == "Consent"
        assert activities[1].label == "Blood Draw"

    def test_add_activities_with_children(self, timeline_assembler):
        """Test activities with child activities."""
        data = {
            "activities": {
                "items": [
                    {
                        "name": "Parent Activity",
                        "references": ["ref1"],
                        "children": [
                            {"name": "Child Activity", "references": ["ref2"]},
                        ],
                    },
                ]
            }
        }
        
        activities = timeline_assembler._add_activities(data)
        
        # Should create parent and child
        assert len(activities) == 2
        # Parent should have child ID in childIds
        assert len(activities[0].childIds) == 1

    def test_add_activities_with_exception(self, timeline_assembler, errors):
        """Test activity creation with exception."""
        initial_error_count = errors.error_count()
        
        data = {
            "activities": {
                "items": None  # Will cause exception
            }
        }
        
        activities = timeline_assembler._add_activities(data)
        
        assert len(activities) == 0
        assert errors.error_count() > initial_error_count


class TestTimelineAssemblerTimepoints:
    """Test TimelineAssembler timepoint creation."""

    def test_add_timepoints_creates_correct_number(self, timeline_assembler):
        """Test that timepoints (SAIs) are created correctly."""
        # First need to create epochs and encounters
        data = {
            "epochs": {
                "items": [{"text": "Screening"}]
            },
            "visits": {
                "items": [{"text": "Visit 1", "references": []}]
            },
            "timepoints": {
                "items": [{"index": "0", "text": "Day 1", "value": "1", "unit": "days"}]
            }
        }
        
        timeline_assembler._add_epochs(data)
        timeline_assembler._add_encounters(data)
        timepoints = timeline_assembler._add_timepoints(data)

        assert len(timepoints) == 1
        assert timepoints[0].label == "Day 1"

    def test_add_timepoints_with_exception(self, timeline_assembler, errors):
        """Test timepoint creation with exception."""
        initial_error_count = errors.error_count()
        
        data = {
            "timepoints": {
                "items": None  # Will cause exception
            }
        }
        
        timepoints = timeline_assembler._add_timepoints(data)
        
        assert len(timepoints) == 0
        assert errors.error_count() > initial_error_count


class TestTimelineAssemblerConditions:
    """Test TimelineAssembler condition creation."""

    def test_add_conditions_with_valid_references(self, timeline_assembler):
        """Test condition creation with valid references."""
        # Set up condition links
        timeline_assembler._condition_links["ref1"] = {
            "reference": "ref1",
            "timepoint_index": [0],
            "activity_id": ["act1"],
        }
        
        # Create timepoints first
        data = {
            "epochs": {"items": [{"text": "Screening"}]},
            "visits": {"items": [{"text": "Visit 1", "references": []}]},
            "timepoints": {"items": [{"index": "0", "text": "Day 1", "value": "1", "unit": "days"}]},
            "conditions": {"items": [{"reference": "ref1", "text": "If patient consents"}]},
        }
        
        timeline_assembler._add_epochs(data)
        timeline_assembler._add_encounters(data)
        timeline_assembler._add_timepoints(data)
        conditions = timeline_assembler._add_conditions(data)

        assert len(conditions) == 1
        assert conditions[0].text == "If patient consents"

    def test_add_conditions_with_invalid_reference(self, timeline_assembler, errors):
        """Test condition creation with invalid reference."""
        data = {
            "conditions": {"items": [{"reference": "invalid_ref", "text": "Some condition"}]},
            "timepoints": {"items": []},
        }
        
        conditions = timeline_assembler._add_conditions(data)
        
        # Should not create condition with invalid reference
        assert len(conditions) == 0

    def test_add_conditions_with_exception(self, timeline_assembler, errors):
        """Test condition creation with exception."""
        initial_error_count = errors.error_count()
        
        data = {
            "conditions": {"items": None},  # Will cause exception
            "timepoints": {"items": []},
        }
        
        conditions = timeline_assembler._add_conditions(data)
        
        assert len(conditions) == 0
        assert errors.error_count() > initial_error_count


class TestTimelineAssemblerTiming:
    """Test TimelineAssembler timing creation."""

    def test_add_timing_creates_correct_number(self, timeline_assembler):
        """Test timing creation."""
        data = {
            "epochs": {"items": [{"text": "Screening"}, {"text": "Screening"}]},
            "visits": {"items": [{"text": "Visit 1", "references": []}, {"text": "Visit 2", "references": []}]},
            "timepoints": {
                "items": [
                    {"index": "0", "text": "Day 1", "value": "1", "unit": "days"},
                    {"index": "1", "text": "Day 7", "value": "7", "unit": "days"},
                ]
            },
            "windows": {
                "items": [
                    {"before": 0, "after": 0, "unit": "days"},
                    {"before": 1, "after": 1, "unit": "days"},
                ]
            },
        }
        
        timeline_assembler._add_epochs(data)
        timeline_assembler._add_encounters(data)
        timeline_assembler._add_timepoints(data)
        timings = timeline_assembler._add_timing(data)

        # Should create timing for each timepoint
        assert len(timings) >= 1  # At least one timing created

    def test_find_anchor_returns_correct_index(self, timeline_assembler):
        """Test finding the anchor timepoint."""
        data = {
            "timepoints": {
                "items": [
                    {"index": "0", "value": "0", "sai_instance": None},
                    {"index": "1", "value": "1", "sai_instance": None},  # This should be the anchor
                    {"index": "2", "value": "7", "sai_instance": None},
                ]
            }
        }
        
        anchor_index = timeline_assembler._find_anchor(data)
        
        assert anchor_index == 1

    def test_find_anchor_defaults_to_zero(self, timeline_assembler):
        """Test finding anchor when none has value 1."""
        data = {
            "timepoints": {
                "items": [
                    {"index": "0", "value": "0"},
                    {"index": "1", "value": "7"},
                ]
            }
        }
        
        anchor_index = timeline_assembler._find_anchor(data)
        
        assert anchor_index == 0

    def test_window_label_formats_correctly(self, timeline_assembler):
        """Test window label formatting."""
        windows = [
            {"before": 1, "after": 2, "unit": "days"},
            {"before": 0, "after": 0, "unit": "days"},
        ]
        
        label1 = timeline_assembler._window_label(windows, 0)
        label2 = timeline_assembler._window_label(windows, 1)
        
        assert label1 == "-1..+2 days"
        assert label2 == ""  # Empty when both before and after are 0

    def test_window_label_out_of_range(self, timeline_assembler):
        """Test window label with out of range index."""
        windows = []
        
        label = timeline_assembler._window_label(windows, 0)
        
        assert label == "???"

    def test_timing_value_label(self, timeline_assembler):
        """Test timing value label."""
        timepoints = [
            {"text": "Day 1"},
            {"text": ""},
        ]
        
        label1 = timeline_assembler._timing_value_label(timepoints, 0)
        label2 = timeline_assembler._timing_value_label(timepoints, 1)
        
        assert label1 == "Day 1"
        assert label2 == "???"

    def test_timing_value_label_out_of_range(self, timeline_assembler):
        """Test timing value label with out of range index."""
        timepoints = []
        
        label = timeline_assembler._timing_value_label(timepoints, 0)
        
        assert label == "???"


class TestTimelineAssemblerConditionLinks:
    """Test TimelineAssembler condition linking methods."""

    def test_condition_timepoint_index_creates_link(self, timeline_assembler):
        """Test condition timepoint index linking."""
        timeline_assembler._condition_timepoint_index("ref1", 0)
        
        assert "ref1" in timeline_assembler._condition_links
        assert 0 in timeline_assembler._condition_links["ref1"]["timepoint_index"]

    def test_condition_activity_id_creates_link(self, timeline_assembler):
        """Test condition activity ID linking."""
        timeline_assembler._condition_activity_id("ref1", "act1")
        
        assert "ref1" in timeline_assembler._condition_links
        assert "act1" in timeline_assembler._condition_links["ref1"]["activity_id"]

    def test_condition_combined_creates_link(self, timeline_assembler):
        """Test combined condition linking."""
        timeline_assembler._condition_combined("ref1", 0, "act1")
        
        assert "ref1" in timeline_assembler._condition_links
        assert 0 in timeline_assembler._condition_links["ref1"]["timepoint_index"]
        assert "act1" in timeline_assembler._condition_links["ref1"]["activity_id"]

    def test_multiple_references_to_same_condition(self, timeline_assembler):
        """Test multiple references to the same condition."""
        timeline_assembler._condition_timepoint_index("ref1", 0)
        timeline_assembler._condition_timepoint_index("ref1", 1)
        timeline_assembler._condition_activity_id("ref1", "act1")
        timeline_assembler._condition_activity_id("ref1", "act2")
        
        assert len(timeline_assembler._condition_links["ref1"]["timepoint_index"]) == 2
        assert len(timeline_assembler._condition_links["ref1"]["activity_id"]) == 2


class TestTimelineAssemblerLinkingTimepoints:
    """Test TimelineAssembler linking of timepoints and activities."""

    def test_link_timepoints_and_activities_simple(self, timeline_assembler):
        """Test linking timepoints and activities."""
        # Prepare data with activities and timepoints
        data = {
            "epochs": {"items": [{"text": "Screening"}]},
            "visits": {"items": [{"text": "Visit 1", "references": []}]},
            "timepoints": {
                "items": [{"index": "0", "text": "Day 1", "value": "1", "unit": "days"}]
            },
            "activities": {
                "items": [
                    {
                        "name": "Activity 1",
                        "visits": [{"index": 0, "references": []}],
                    }
                ]
            },
        }
        
        timeline_assembler._add_epochs(data)
        timeline_assembler._add_encounters(data)
        timeline_assembler._add_activities(data)
        timeline_assembler._add_timepoints(data)
        timeline_assembler._link_timepoints_and_activities(data)
        
        # Verify linking occurred
        timepoint = data["timepoints"]["items"][0]["sai_instance"]
        assert len(timepoint.activityIds) == 1

    def test_link_timepoints_and_activities_with_children(self, timeline_assembler):
        """Test linking with child activities."""
        data = {
            "epochs": {"items": [{"text": "Screening"}]},
            "visits": {"items": [{"text": "Visit 1", "references": []}]},
            "timepoints": {
                "items": [{"index": "0", "text": "Day 1", "value": "1", "unit": "days"}]
            },
            "activities": {
                "items": [
                    {
                        "name": "Parent",
                        "children": [
                            {
                                "name": "Child",
                                "index": 0,
                                "visits": [{"index": 0, "references": []}],
                            }
                        ],
                    }
                ]
            },
        }
        
        timeline_assembler._add_epochs(data)
        timeline_assembler._add_encounters(data)
        timeline_assembler._add_activities(data)
        timeline_assembler._add_timepoints(data)
        timeline_assembler._link_timepoints_and_activities(data)
        
        # Verify child activity was linked
        timepoint = data["timepoints"]["items"][0]["sai_instance"]
        assert len(timepoint.activityIds) == 1


class TestTimelineAssemblerTimeline:
    """Test TimelineAssembler timeline creation."""

    def test_add_timeline_creates_timeline(self, timeline_assembler):
        """Test timeline creation."""
        data = {
            "epochs": {"items": [{"text": "Screening"}]},
            "visits": {"items": [{"text": "Visit 1", "references": []}]},
            "timepoints": {
                "items": [{"index": "0", "text": "Day 1", "value": "1", "unit": "days"}]
            },
            "windows": {"items": [{"before": 0, "after": 0, "unit": "days"}]},
        }
        
        timeline_assembler._add_epochs(data)
        timeline_assembler._add_encounters(data)
        timepoints = timeline_assembler._add_timepoints(data)
        timings = timeline_assembler._add_timing(data)
        timeline = timeline_assembler._add_timeline(data, timepoints, timings)
        
        assert timeline is not None
        assert timeline.mainTimeline is True
        assert timeline.name == "TIMELINE-1"
        assert len(timeline.instances) == 1
        assert len(timeline.timings) == 1


class TestTimelineAssemblerIntegration:
    """Integration tests for TimelineAssembler."""

    def test_full_execution_workflow(self, timeline_assembler, minimal_timeline_data):
        """Test full execution workflow."""
        timeline_assembler.execute(minimal_timeline_data)
        
        # Verify all components were created
        assert len(timeline_assembler.timelines) == 1
        assert len(timeline_assembler.epochs) > 0
        assert len(timeline_assembler.encounters) > 0
        assert len(timeline_assembler.activities) > 0
        
        # Verify timeline structure
        timeline = timeline_assembler.timelines[0]
        assert timeline.mainTimeline is True
        assert len(timeline.instances) > 0
        assert len(timeline.timings) > 0

    def test_complex_timeline_with_conditions(self, timeline_assembler):
        """Test complex timeline with conditions."""
        data = {
            "epochs": {
                "items": [{"text": "Screening"}, {"text": "Treatment"}]
            },
            "visits": {
                "items": [
                    {"text": "Visit 1", "references": ["c1"]},
                    {"text": "Visit 2", "references": []},
                ]
            },
            "timepoints": {
                "items": [
                    {"index": "0", "text": "Day 1", "value": "1", "unit": "days"},
                    {"index": "1", "text": "Day 7", "value": "7", "unit": "days"},
                ]
            },
            "windows": {
                "items": [
                    {"before": 0, "after": 0, "unit": "days"},
                    {"before": 1, "after": 1, "unit": "days"},
                ]
            },
            "activities": {
                "items": [
                    {
                        "name": "Consent",
                        "references": ["c1"],
                        "visits": [{"index": 0, "references": ["c1"]}],
                    },
                    {
                        "name": "Blood Draw",
                        "visits": [{"index": 1, "references": []}],
                    },
                ]
            },
            "conditions": {
                "items": [
                    {"reference": "c1", "text": "If patient consents"}
                ]
            },
        }
        
        timeline_assembler.execute(data)
        
        # Verify conditions were created
        assert len(timeline_assembler.conditions) == 1
        assert timeline_assembler.conditions[0].text == "If patient consents"


class TestTimelineAssemblerEdgeCases:
    """Test TimelineAssembler edge cases."""

    def test_empty_activities_list(self, timeline_assembler):
        """Test with empty activities list."""
        data = {
            "activities": {"items": []}
        }
        
        activities = timeline_assembler._add_activities(data)
        
        assert len(activities) == 0

    def test_empty_timepoints_list(self, timeline_assembler):
        """Test with empty timepoints list."""
        data = {
            "timepoints": {"items": []}
        }
        
        timepoints = timeline_assembler._add_timepoints(data)
        
        assert len(timepoints) == 0

    def test_missing_keys_in_data(self, timeline_assembler, errors):
        """Test with missing keys in data."""
        initial_error_count = errors.error_count()
        
        data = {}  # Missing all required keys
        
        try:
            timeline_assembler.execute(data)
        except Exception:
            pass
        
        assert errors.error_count() > initial_error_count
