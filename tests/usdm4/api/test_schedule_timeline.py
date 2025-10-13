from unittest.mock import Mock
from src.usdm4.api.schedule_timeline import ScheduleTimeline
from src.usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
)
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
            instanceType="ScheduleTimeline",
        )

    def test_first_timepoint_with_instances(self):
        """Test first_timepoint method when instances exist."""
        instance1 = ScheduledActivityInstance(
            id="instance1", name="Instance 1", instanceType="ScheduledActivityInstance"
        )
        instance2 = ScheduledActivityInstance(
            id="instance2", name="Instance 2", instanceType="ScheduledActivityInstance"
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
            id="instance1", name="Instance 1", instanceType="ScheduledActivityInstance"
        )
        instance2 = ScheduledActivityInstance(
            id="instance2", name="Instance 2", instanceType="ScheduledActivityInstance"
        )

        self.timeline.instances = [instance1, instance2]
        result = self.timeline.find_timepoint("instance2")
        assert result == instance2
        assert result.id == "instance2"

    def test_find_timepoint_not_found(self):
        """Test find_timepoint method when timepoint doesn't exist."""
        instance1 = ScheduledActivityInstance(
            id="instance1", name="Instance 1", instanceType="ScheduledActivityInstance"
        )

        self.timeline.instances = [instance1]
        result = self.timeline.find_timepoint("nonexistent")
        assert result is None

    def test_timepoint_list(self):
        """Test timepoint_list method."""
        instance1 = ScheduledActivityInstance(
            id="instance1", name="Instance 1", instanceType="ScheduledActivityInstance"
        )
        instance2 = ScheduledDecisionInstance(
            id="instance2", name="Instance 2", instanceType="ScheduledDecisionInstance"
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
            type=Code(
                id="code1",
                code="TYPE1",
                codeSystem="SYSTEM1",
                codeSystemVersion="1.0",
                decode="Type 1",
                instanceType="Code",
            ),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(
                id="code2",
                code="FROM1",
                codeSystem="SYSTEM1",
                codeSystemVersion="1.0",
                decode="From 1",
                instanceType="Code",
            ),
            relativeFromScheduledInstanceId="instance1",
            instanceType="Timing",
        )
        timing2 = Timing(
            id="timing2",
            name="Timing 2",
            type=Code(
                id="code3",
                code="TYPE2",
                codeSystem="SYSTEM1",
                codeSystemVersion="1.0",
                decode="Type 2",
                instanceType="Code",
            ),
            value="2",
            valueLabel="Day 2",
            relativeToFrom=Code(
                id="code4",
                code="FROM2",
                codeSystem="SYSTEM1",
                codeSystemVersion="1.0",
                decode="From 2",
                instanceType="Code",
            ),
            relativeFromScheduledInstanceId="instance2",
            instanceType="Timing",
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
            type=Code(
                id="code1",
                code="TYPE1",
                codeSystem="SYSTEM1",
                codeSystemVersion="1.0",
                decode="Type 1",
                instanceType="Code",
            ),
            value="1",
            valueLabel="Day 1",
            relativeToFrom=Code(
                id="code2",
                code="FROM1",
                codeSystem="SYSTEM1",
                codeSystemVersion="1.0",
                decode="From 1",
                instanceType="Code",
            ),
            relativeFromScheduledInstanceId="instance1",
            instanceType="Timing",
        )

        self.timeline.timings = [timing1]
        result = self.timeline.find_timing_from("nonexistent")
        assert result is None

    def test_timeline_with_exits_and_duration(self):
        """Test timeline with exits and planned duration."""
        exit1 = ScheduleTimelineExit(id="exit1", instanceType="ScheduleTimelineExit")
        exit2 = ScheduleTimelineExit(id="exit2", instanceType="ScheduleTimelineExit")

        duration = Duration(
            id="duration1",
            text="4 weeks",
            durationWillVary=False,
            instanceType="Duration",
        )

        timeline = ScheduleTimeline(
            id="timeline1",
            name="Test Timeline",
            mainTimeline=False,
            entryCondition="condition",
            entryId="entry1",
            exits=[exit1, exit2],
            plannedDuration=duration,
            instanceType="ScheduleTimeline",
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
            instanceType="ScheduleTimeline",
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
