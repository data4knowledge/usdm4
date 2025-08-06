import pytest
from unittest.mock import Mock, MagicMock
from src.usdm4.api.schedule_timeline import ScheduleTimeline
from src.usdm4.api.scheduled_instance import ScheduledActivityInstance, ScheduledDecisionInstance
from src.usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from src.usdm4.api.timing import Timing
from src.usdm4.api.duration import Duration
from src.usdm4.api.code import Code


class TestScheduleTimeline:
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.timeline = ScheduleTimeline(
            id="timeline1",
            name="Test Timeline",
            label="Test Timeline Label",
            description="Test Timeline Description",
            mainTimeline=True,
            entryCondition="entry_condition",
            entryId="entry_id",
            instanceType="ScheduleTimeline"
        )

    def test_first_timepoint_with_instances(self):
        """Test first_timepoint method when instances exist."""
        instance1 = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            instanceType="ScheduledActivityInstance"
        )
        instance2 = ScheduledActivityInstance(
            id="instance2", 
            name="Instance 2",
            instanceType="ScheduledActivityInstance"
        )
        
        self.timeline.instances = [instance1, instance2]
        result = self.timeline.first_timepoint()
        assert result == instance1
        assert result.id == "instance1"

    def test_first_timepoint_empty_instances(self):
        """Test first_timepoint method when no instances exist."""
        self.timeline.instances = []
        result = self.timeline.first_timepoint()
        assert result is None

    def test_find_timepoint_found(self):
        """Test find_timepoint method when timepoint exists."""
        instance1 = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1", 
            instanceType="ScheduledActivityInstance"
        )
        instance2 = ScheduledActivityInstance(
            id="instance2",
            name="Instance 2",
            instanceType="ScheduledActivityInstance"
        )
        
        self.timeline.instances = [instance1, instance2]
        result = self.timeline.find_timepoint("instance2")
        assert result == instance2
        assert result.id == "instance2"

    def test_find_timepoint_not_found(self):
        """Test find_timepoint method when timepoint doesn't exist."""
        instance1 = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            instanceType="ScheduledActivityInstance"
        )
        
        self.timeline.instances = [instance1]
        result = self.timeline.find_timepoint("nonexistent")
        assert result is None

    def test_timepoint_list(self):
        """Test timepoint_list method."""
        instance1 = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            instanceType="ScheduledActivityInstance"
        )
        instance2 = ScheduledDecisionInstance(
            id="instance2",
            name="Instance 2", 
            instanceType="ScheduledDecisionInstance"
        )
        
        self.timeline.instances = [instance1, instance2]
        result = self.timeline.timepoint_list()
        assert result == [instance1, instance2]
        assert len(result) == 2

    def test_find_timing_from_found(self):
        """Test find_timing_from method when timing exists."""
        timing1 = Timing(
            id="timing1",
            name="Timing 1",
            type=Code(id="code1", code="TYPE1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 1", instanceType="Code"),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(id="code2", code="FROM1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 1", instanceType="Code"),
            relativeFromScheduledInstanceId="instance1",
            instanceType="Timing"
        )
        timing2 = Timing(
            id="timing2",
            name="Timing 2",
            type=Code(id="code3", code="TYPE2", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 2", instanceType="Code"),
            value="2", 
            valueLabel="Day 2",
            relativeToFrom=Code(id="code4", code="FROM2", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 2", instanceType="Code"),
            relativeFromScheduledInstanceId="instance2",
            instanceType="Timing"
        )
        
        self.timeline.timings = [timing1, timing2]
        result = self.timeline.find_timing_from("instance2")
        assert result == timing2
        assert result.relativeFromScheduledInstanceId == "instance2"

    def test_find_timing_from_not_found(self):
        """Test find_timing_from method when timing doesn't exist."""
        timing1 = Timing(
            id="timing1",
            name="Timing 1",
            type=Code(id="code1", code="TYPE1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 1", instanceType="Code"),
            value="1",
            valueLabel="Day 1", 
            relativeToFrom=Code(id="code2", code="FROM1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 1", instanceType="Code"),
            relativeFromScheduledInstanceId="instance1",
            instanceType="Timing"
        )
        
        self.timeline.timings = [timing1]
        result = self.timeline.find_timing_from("nonexistent")
        assert result is None

    def test_soa_method_comprehensive(self):
        """Test the complex soa method with comprehensive mock data."""
        # Create mock study design
        study_design = Mock()
        
        # Mock activity
        mock_activity = Mock()
        mock_activity.id = "activity1"
        mock_activity.name = "Activity 1"
        mock_activity.label = "Activity 1 Label"
        study_design.activity_list.return_value = [mock_activity]
        
        # Create scheduled instance
        instance = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            label="Visit 1",
            activityIds=["activity1"],
            encounterId="encounter1",
            epochId="epoch1",
            instanceType="ScheduledActivityInstance"
        )
        self.timeline.instances = [instance]
        
        # Create timing
        timing = Timing(
            id="timing1",
            name="Timing 1",
            type=Code(id="code1", code="TYPE1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 1", instanceType="Code"),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(id="code2", code="FROM1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 1", instanceType="Code"),
            relativeFromScheduledInstanceId="instance1",
            windowLabel="Day 1 ± 2",
            instanceType="Timing"
        )
        self.timeline.timings = [timing]
        
        # Mock encounter
        mock_encounter = Mock()
        mock_encounter.label = "Encounter 1"
        study_design.find_encounter.return_value = mock_encounter
        
        # Mock epoch
        mock_epoch = Mock()
        mock_epoch.label = "Epoch 1"
        study_design.find_epoch.return_value = mock_epoch
        
        # Call soa method
        result = self.timeline.soa(study_design)
        
        # Verify the result is HTML table
        assert isinstance(result, str)
        assert '<table class="soa-table table">' in result
        assert '<thead>' in result
        assert '<tbody>' in result
        assert '</table>' in result
        assert 'Epoch 1' in result
        assert 'Encounter 1' in result
        assert 'Visit 1' in result
        assert 'Day 1 ± 2' in result
        assert 'Activity 1 Label' in result

    def test_soa_method_with_none_values(self):
        """Test soa method with None encounter and epoch."""
        # Create mock study design
        study_design = Mock()
        
        # Mock activity
        mock_activity = Mock()
        mock_activity.id = "activity1"
        mock_activity.name = "Activity 1"
        mock_activity.label = None  # Test None label
        study_design.activity_list.return_value = [mock_activity]
        
        # Create scheduled instance
        instance = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            label="Visit 1",
            activityIds=["activity1"],
            encounterId="encounter1",
            epochId="epoch1",
            instanceType="ScheduledActivityInstance"
        )
        self.timeline.instances = [instance]
        
        # Create timing
        timing = Timing(
            id="timing1",
            name="Timing 1",
            type=Code(id="code1", code="TYPE1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 1", instanceType="Code"),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(id="code2", code="FROM1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 1", instanceType="Code"),
            relativeFromScheduledInstanceId="instance1",
            windowLabel=None,  # Test None windowLabel
            instanceType="Timing"
        )
        self.timeline.timings = [timing]
        
        # Mock returns None
        study_design.find_encounter.return_value = None
        study_design.find_epoch.return_value = None
        
        # Call soa method
        result = self.timeline.soa(study_design)
        
        # Verify the result handles None values
        assert isinstance(result, str)
        assert '<table class="soa-table table">' in result
        assert '&nbsp;' in result  # Should contain non-breaking spaces for None values
        assert 'Activity 1' in result  # Should use name when label is None

    def test_soa_method_multiple_activities_and_timepoints(self):
        """Test soa method with multiple activities and timepoints."""
        # Create mock study design
        study_design = Mock()
        
        # Mock multiple activities
        activity1 = Mock()
        activity1.id = "activity1"
        activity1.name = "Activity 1"
        activity1.label = "Activity 1 Label"
        
        activity2 = Mock()
        activity2.id = "activity2"
        activity2.name = "Activity 2"
        activity2.label = "Activity 2 Label"
        
        study_design.activity_list.return_value = [activity1, activity2]
        
        # Create multiple scheduled instances
        instance1 = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            label="Visit 1",
            activityIds=["activity1"],
            encounterId="encounter1",
            epochId="epoch1",
            instanceType="ScheduledActivityInstance"
        )
        
        instance2 = ScheduledActivityInstance(
            id="instance2",
            name="Instance 2", 
            label="Visit 2",
            activityIds=["activity1", "activity2"],
            encounterId="encounter2",
            epochId="epoch2",
            instanceType="ScheduledActivityInstance"
        )
        
        self.timeline.instances = [instance1, instance2]
        
        # Create multiple timings
        timing1 = Timing(
            id="timing1",
            name="Timing 1",
            type=Code(id="code1", code="TYPE1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 1", instanceType="Code"),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(id="code2", code="FROM1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 1", instanceType="Code"),
            relativeFromScheduledInstanceId="instance1",
            windowLabel="Day 1",
            instanceType="Timing"
        )
        
        timing2 = Timing(
            id="timing2",
            name="Timing 2",
            type=Code(id="code3", code="TYPE2", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 2", instanceType="Code"),
            value="7",
            valueLabel="Day 7",
            relativeToFrom=Code(id="code4", code="FROM2", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 2", instanceType="Code"),
            relativeFromScheduledInstanceId="instance2",
            windowLabel="Day 7",
            instanceType="Timing"
        )
        
        self.timeline.timings = [timing1, timing2]
        
        # Mock encounters and epochs
        encounter1 = Mock()
        encounter1.label = "Encounter 1"
        encounter2 = Mock()
        encounter2.label = "Encounter 2"
        
        epoch1 = Mock()
        epoch1.label = "Epoch 1"
        epoch2 = Mock()
        epoch2.label = "Epoch 2"
        
        def mock_find_encounter(encounter_id):
            if encounter_id == "encounter1":
                return encounter1
            elif encounter_id == "encounter2":
                return encounter2
            return None
            
        def mock_find_epoch(epoch_id):
            if epoch_id == "epoch1":
                return epoch1
            elif epoch_id == "epoch2":
                return epoch2
            return None
        
        study_design.find_encounter.side_effect = mock_find_encounter
        study_design.find_epoch.side_effect = mock_find_epoch
        
        # Call soa method
        result = self.timeline.soa(study_design)
        
        # Verify the result contains all elements
        assert isinstance(result, str)
        assert '<table class="soa-table table">' in result
        assert 'Activity 1 Label' in result
        assert 'Activity 2 Label' in result
        assert 'Visit 1' in result
        assert 'Visit 2' in result
        assert 'Encounter 1' in result
        assert 'Encounter 2' in result

    def test_soa_method_no_matching_activities(self):
        """Test soa method when no activities match timepoint activity IDs."""
        # Create mock study design
        study_design = Mock()
        
        # Mock activity that doesn't match
        mock_activity = Mock()
        mock_activity.id = "activity_no_match"
        mock_activity.name = "No Match Activity"
        mock_activity.label = "No Match Label"
        study_design.activity_list.return_value = [mock_activity]
        
        # Create scheduled instance with different activity ID
        instance = ScheduledActivityInstance(
            id="instance1",
            name="Instance 1",
            label="Visit 1",
            activityIds=["different_activity"],
            encounterId="encounter1",
            epochId="epoch1",
            instanceType="ScheduledActivityInstance"
        )
        self.timeline.instances = [instance]
        
        # Create timing
        timing = Timing(
            id="timing1",
            name="Timing 1",
            type=Code(id="code1", code="TYPE1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="Type 1", instanceType="Code"),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(id="code2", code="FROM1", codeSystem="SYSTEM1", codeSystemVersion="1.0", decode="From 1", instanceType="Code"),
            relativeFromScheduledInstanceId="instance1",
            windowLabel="Day 1",
            instanceType="Timing"
        )
        self.timeline.timings = [timing]
        
        # Mock encounter and epoch
        mock_encounter = Mock()
        mock_encounter.label = "Encounter 1"
        study_design.find_encounter.return_value = mock_encounter
        
        mock_epoch = Mock()
        mock_epoch.label = "Epoch 1"
        study_design.find_epoch.return_value = mock_epoch
        
        # Call soa method
        result = self.timeline.soa(study_design)
        
        # Verify the result still generates table but without activity rows
        assert isinstance(result, str)
        assert '<table class="soa-table table">' in result
        assert 'Visit 1' in result
        assert 'Encounter 1' in result
        # Activity should not appear since it doesn't match
        assert 'No Match Label' not in result

    def test_timeline_with_exits_and_duration(self):
        """Test timeline with exits and planned duration."""
        exit1 = ScheduleTimelineExit(id="exit1", instanceType="ScheduleTimelineExit")
        exit2 = ScheduleTimelineExit(id="exit2", instanceType="ScheduleTimelineExit")
        
        duration = Duration(
            id="duration1",
            text="4 weeks",
            durationWillVary=False,
            instanceType="Duration"
        )
        
        timeline = ScheduleTimeline(
            id="timeline1",
            name="Test Timeline",
            mainTimeline=False,
            entryCondition="condition",
            entryId="entry1",
            exits=[exit1, exit2],
            plannedDuration=duration,
            instanceType="ScheduleTimeline"
        )
        
        assert len(timeline.exits) == 2
        assert timeline.exits[0].id == "exit1"
        assert timeline.exits[1].id == "exit2"
        assert timeline.plannedDuration.text == "4 weeks"
        assert timeline.mainTimeline is False

    def test_timeline_empty_lists(self):
        """Test timeline with empty lists."""
        timeline = ScheduleTimeline(
            id="timeline1",
            name="Empty Timeline",
            mainTimeline=True,
            entryCondition="condition",
            entryId="entry1",
            instanceType="ScheduleTimeline"
        )
        
        # Test default empty lists
        assert timeline.exits == []
        assert timeline.timings == []
        assert timeline.instances == []
        assert timeline.plannedDuration is None
        
        # Test methods with empty lists
        assert timeline.first_timepoint() is None
        assert timeline.find_timepoint("any_id") is None
        assert timeline.timepoint_list() == []
        assert timeline.find_timing_from("any_id") is None

    def test_soa_method_empty_timeline(self):
        """Test soa method with empty timeline."""
        study_design = Mock()
        study_design.activity_list.return_value = []
        
        # Empty timeline
        self.timeline.instances = []
        self.timeline.timings = []
        
        result = self.timeline.soa(study_design)
        
        # Should still generate basic table structure
        assert isinstance(result, str)
        assert '<table class="soa-table table">' in result
        assert '<thead>' in result
        assert '<tbody>' in result
        assert '</table>' in result
