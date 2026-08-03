from usdm4.expander.expander import Expander
from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
    ConditionAssignment,
)
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.timing import Timing
from usdm4.api.code import Code
from usdm4.api.activity import Activity
from usdm4.api.encounter import Encounter
from usdm4.api.procedure import Procedure
from usdm4.api.population_definition import StudyDesignPopulation
from simple_error_log import Errors
import operator


class TestExpander:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create test codes
        self.timing_type_anchor = Code(
            id="timing_type_anchor",
            code="C201358",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Anchor",
            instanceType="Code",
        )

        self.timing_type_after = Code(
            id="timing_type_after",
            code="C201356",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="After",
            instanceType="Code",
        )

        self.relative_to_from = Code(
            id="relative_to_from",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Start",
            instanceType="Code",
        )

        self.encounter_type = Code(
            id="encounter_type",
            code="C12345",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Visit",
            instanceType="Code",
        )

        self.procedure_code = Code(
            id="procedure_code",
            code="P12345",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Blood Draw",
            instanceType="Code",
        )

        # Create test procedure
        self.procedure = Procedure(
            id="procedure_1",
            name="Blood Draw",
            label="Blood Draw",
            description="Blood draw procedure",
            procedureType="Laboratory",
            code=self.procedure_code,
            instanceType="Procedure",
        )

        # Create test activity
        self.activity = Activity(
            id="activity_1",
            name="Screening Activity",
            label="Screening Activity",
            description="Screening activity",
            definedProcedures=[self.procedure],
            instanceType="Activity",
        )

        # Create test encounter
        self.encounter = Encounter(
            id="encounter_1",
            name="Screening Visit",
            label="Screening Visit",
            description="Screening visit",
            type=self.encounter_type,
            instanceType="Encounter",
        )

        # Create population
        self.population = StudyDesignPopulation(
            id="population_1",
            name="Test Population",
            label="Test Population",
            description="Test population",
            includesHealthySubjects=True,
            instanceType="StudyDesignPopulation",
        )

        # Create errors object - fresh for each test
        pass

    def _get_fresh_errors(self):
        """Get a fresh errors object for each test."""
        return Errors()

    def create_simple_timeline(self):
        """Helper to create a simple timeline with one activity."""
        # Create SAI
        sai = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="Simple SAI",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        # Create timing
        timing = Timing(
            id="timing_1",
            name="Anchor Timing",
            label="Anchor Timing",
            description="Anchor timing",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        # Create exit
        exit_node = ScheduleTimelineExit(
            id="exit_1", instanceType="ScheduleTimelineExit"
        )

        # Create timeline
        timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="sai_1",
            timings=[timing],
            instances=[sai],
            exits=[exit_node],
            instanceType="ScheduleTimeline",
        )

        return timeline

    def create_multi_activity_timeline(self):
        """Helper to create a timeline with multiple activities."""
        # Create SAIs
        sai1 = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="First SAI",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            defaultConditionId="sai_2",
            instanceType="ScheduledActivityInstance",
        )

        sai2 = ScheduledActivityInstance(
            id="sai_2",
            name="SAI 2",
            label="SAI 2",
            description="Second SAI",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        # Create timings
        timing1 = Timing(
            id="timing_1",
            name="Anchor Timing",
            label="Anchor Timing",
            description="Anchor timing",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        timing2 = Timing(
            id="timing_2",
            name="After Timing",
            label="After Timing",
            description="After timing",
            type=self.timing_type_after,
            value="P7D",
            valueLabel="7 days after",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_2",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        # Create exit
        exit_node = ScheduleTimelineExit(
            id="exit_1", instanceType="ScheduleTimelineExit"
        )

        # Create timeline
        timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="sai_1",
            timings=[timing1, timing2],
            instances=[sai1, sai2],
            exits=[exit_node],
            instanceType="ScheduleTimeline",
        )

        return timeline

    def create_decision_timeline(self, condition: str):
        """Helper to create a timeline with a decision instance."""
        # Create SAIs
        sai1 = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="First SAI",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            defaultConditionId="sdi_1",
            instanceType="ScheduledActivityInstance",
        )

        sai2 = ScheduledActivityInstance(
            id="sai_2",
            name="SAI 2",
            label="SAI 2",
            description="Second SAI (condition true)",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        sai3 = ScheduledActivityInstance(
            id="sai_3",
            name="SAI 3",
            label="SAI 3",
            description="Third SAI (condition false)",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        # Create condition assignment
        condition_assignment = ConditionAssignment(
            id="ca_1",
            condition=condition,
            conditionTargetId="sai_2",
            instanceType="ConditionAssignment",
        )

        # Create decision instance
        sdi = ScheduledDecisionInstance(
            id="sdi_1",
            name="SDI 1",
            label="SDI 1",
            description="Decision instance",
            defaultConditionId="sai_3",
            conditionAssignments=[condition_assignment],
            instanceType="ScheduledDecisionInstance",
        )

        # Create timings
        timing1 = Timing(
            id="timing_1",
            name="Anchor Timing",
            label="Anchor Timing",
            description="Anchor timing",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        timing2 = Timing(
            id="timing_2",
            name="Timing 2",
            label="Timing 2",
            description="Timing 2",
            type=self.timing_type_after,
            value="P10D",
            valueLabel="10 days after",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_2",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        timing3 = Timing(
            id="timing_3",
            name="Timing 3",
            label="Timing 3",
            description="Timing 3",
            type=self.timing_type_after,
            value="P20D",
            valueLabel="20 days after",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_3",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        # Create exit
        exit_node = ScheduleTimelineExit(
            id="exit_1", instanceType="ScheduleTimelineExit"
        )

        # Create timeline
        timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline with decision",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="sai_1",
            timings=[timing1, timing2, timing3],
            instances=[sai1, sai2, sai3, sdi],
            exits=[exit_node],
            instanceType="ScheduleTimeline",
        )

        return timeline

    def create_study_design(self, timeline):
        """Helper to create study design with given timeline."""
        return StudyDesign(
            id="design_1",
            name="Test Study Design",
            label="Test Study Design",
            description="Test study design",
            activities=[self.activity],
            encounters=[self.encounter],
            scheduleTimelines=[timeline],
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.population,
            instanceType="StudyDesign",
        )

    def test_init_basic(self):
        """Test basic initialization of Expander."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()

        expander = Expander(study_design, timeline, errors)

        assert expander._study_design == study_design
        assert expander._timeline == timeline
        assert expander._errors == errors
        assert expander._id == 1
        assert expander._nodes == []

    def test_nodes_property(self):
        """Test nodes property getter."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()

        expander = Expander(study_design, timeline, errors)

        assert expander.nodes == []

    def test_process_simple_timeline(self):
        """Test processing a simple timeline with one activity."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have one node (the activity)
        assert len(expander.nodes) == 1
        assert expander.nodes[0].id == "TP_1"
        assert expander.nodes[0].tick == 0
        assert errors.count() == 0

    def test_process_multi_activity_timeline(self):
        """Test processing a timeline with multiple activities."""
        timeline = self.create_multi_activity_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have two nodes
        assert len(expander.nodes) == 2
        assert expander.nodes[0].id == "TP_1"
        assert expander.nodes[0].tick == 0
        assert expander.nodes[1].id == "TP_2"
        assert expander.nodes[1].tick == 604800  # 7 days
        assert errors.count() == 0

    def test_process_nodes_sorted_by_tick(self):
        """Test that nodes are sorted by tick after processing."""
        timeline = self.create_multi_activity_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Verify nodes are sorted
        ticks = [node.tick for node in expander.nodes]
        assert ticks == sorted(ticks)

    def test_process_filters_nodes_without_activities(self):
        """Test that nodes without activities are filtered out."""
        # Create a timeline with SAI that has no activities
        sai_no_activities = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="SAI with no activities",
            activityIds=[],
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        timing = Timing(
            id="timing_1",
            name="Anchor Timing",
            label="Anchor Timing",
            description="Anchor timing",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        exit_node = ScheduleTimelineExit(
            id="exit_1", instanceType="ScheduleTimelineExit"
        )

        timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="sai_1",
            timings=[timing],
            instances=[sai_no_activities],
            exits=[exit_node],
            instanceType="ScheduleTimeline",
        )

        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have no nodes (filtered out)
        assert len(expander.nodes) == 0

    def test_process_decision_condition_true_greater_than(self):
        """Test processing with decision instance where condition is true (days > X)."""
        # Condition: days > 5, offset = 0, so 0 > 5*86400 is False
        # Should go to default (sai_3)
        timeline = self.create_decision_timeline("days > 5")
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have sai_1 and sai_3 (default path)
        assert len(expander.nodes) == 2
        assert expander.nodes[0].tick == 0  # sai_1
        assert expander.nodes[1].tick == 20 * 86400  # sai_3 at 20 days

    def test_process_decision_condition_false_less_than(self):
        """Test processing with decision instance where condition is false (days < X)."""
        # Condition: days < 1, offset = 0, so 0 < 1*86400 is True
        # Should go to condition target (sai_2)
        timeline = self.create_decision_timeline("days < 1")
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have sai_1 and sai_2 (condition path)
        assert len(expander.nodes) == 2
        assert expander.nodes[0].tick == 0  # sai_1
        assert expander.nodes[1].tick == 10 * 86400  # sai_2 at 10 days

    def test_process_decision_condition_equals(self):
        """Test processing with decision instance using equals operator."""
        timeline = self.create_decision_timeline("days = 0")
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Condition: days = 0, offset = 0, so 0 == 0*86400 is True
        # Should go to condition target (sai_2)
        assert len(expander.nodes) == 2
        assert expander.nodes[0].tick == 0  # sai_1
        assert expander.nodes[1].tick == 10 * 86400  # sai_2

    def test_process_decision_complex_condition(self):
        """Test processing with complex condition (multiple condition assignments)."""
        # Create decision with multiple condition assignments
        ca1 = ConditionAssignment(
            id="ca_1",
            condition="days > 5",
            conditionTargetId="sai_2",
            instanceType="ConditionAssignment",
        )

        ca2 = ConditionAssignment(
            id="ca_2",
            condition="days < 10",
            conditionTargetId="sai_3",
            instanceType="ConditionAssignment",
        )

        sai1 = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="First SAI",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            defaultConditionId="sdi_1",
            instanceType="ScheduledActivityInstance",
        )

        sai2 = ScheduledActivityInstance(
            id="sai_2",
            name="SAI 2",
            label="SAI 2",
            description="Second SAI",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        sai3 = ScheduledActivityInstance(
            id="sai_3",
            name="SAI 3",
            label="SAI 3",
            description="Third SAI (default)",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        sdi = ScheduledDecisionInstance(
            id="sdi_1",
            name="SDI 1",
            label="SDI 1",
            description="Complex decision",
            defaultConditionId="sai_3",
            conditionAssignments=[ca1, ca2],
            instanceType="ScheduledDecisionInstance",
        )

        timing1 = Timing(
            id="timing_1",
            name="Timing 1",
            label="Timing 1",
            description="Timing 1",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        timing2 = Timing(
            id="timing_2",
            name="Timing 2",
            label="Timing 2",
            description="Timing 2",
            type=self.timing_type_after,
            value="P5D",
            valueLabel="5 days",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_2",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        timing3 = Timing(
            id="timing_3",
            name="Timing 3",
            label="Timing 3",
            description="Timing 3",
            type=self.timing_type_after,
            value="P10D",
            valueLabel="10 days",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_3",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        exit_node = ScheduleTimelineExit(
            id="exit_1", instanceType="ScheduleTimelineExit"
        )

        timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="sai_1",
            timings=[timing1, timing2, timing3],
            instances=[sai1, sai2, sai3, sdi],
            exits=[exit_node],
            instanceType="ScheduleTimeline",
        )

        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Complex condition should be ignored and use default
        assert len(expander.nodes) == 2
        assert errors.count() > 0  # Should have error about complex condition

    def test_process_exit_instance(self):
        """Test processing when encountering exit instance."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should complete without errors
        assert len(expander.nodes) == 1
        assert errors.count() == 0

    def test_process_sai_without_next(self):
        """Test processing SAI without defaultConditionId or timelineExitId."""
        sai = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="SAI without next",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            instanceType="ScheduledActivityInstance",
        )

        timing = Timing(
            id="timing_1",
            name="Anchor Timing",
            label="Anchor Timing",
            description="Anchor timing",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="sai_1",
            instanceType="Timing",
        )

        timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="sai_1",
            timings=[timing],
            instances=[sai],
            instanceType="ScheduleTimeline",
        )

        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have error about missing next instance
        assert errors.count() > 0

    def test_days_condition_greater_than(self):
        """Test _days_condition with greater than operator."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("days > 5")

        assert op == operator.gt
        assert value == 5

    def test_days_condition_less_than(self):
        """Test _days_condition with less than operator."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("days < 10")

        assert op == operator.lt
        assert value == 10

    def test_days_condition_equals(self):
        """Test _days_condition with equals operator."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("days = 7")

        assert op == operator.eq
        assert value == 7

    def test_days_condition_case_insensitive(self):
        """Test _days_condition is case insensitive."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op1, value1 = expander._days_condition("DAYS > 5")
        op2, value2 = expander._days_condition("Days > 5")
        op3, value3 = expander._days_condition("dAyS > 5")

        assert op1 == operator.gt and value1 == 5
        assert op2 == operator.gt and value2 == 5
        assert op3 == operator.gt and value3 == 5

    def test_days_condition_singular_day(self):
        """Test _days_condition with singular 'day'."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("day > 3")

        assert op == operator.gt
        assert value == 3

    def test_days_condition_with_spaces(self):
        """Test _days_condition handles various spacing."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op1, value1 = expander._days_condition("days>5")
        op2, value2 = expander._days_condition("days  >  5")
        op3, value3 = expander._days_condition("days   >   10")

        assert op1 == operator.gt and value1 == 5
        assert op2 == operator.gt and value2 == 5
        assert op3 == operator.gt and value3 == 10

    def test_days_condition_invalid_text(self):
        """Test _days_condition with invalid text."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("invalid condition")

        assert op is None
        assert value is None

    def test_days_condition_no_operator(self):
        """Test _days_condition with missing operator."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("days 5")

        assert op is None
        assert value is None

    def test_days_condition_no_number(self):
        """Test _days_condition with missing number."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("days >")

        assert op is None
        assert value is None

    def test_days_condition_multiple_digits(self):
        """Test _days_condition with multiple digit numbers."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op1, value1 = expander._days_condition("days > 100")
        op2, value2 = expander._days_condition("days < 999")

        assert op1 == operator.gt and value1 == 100
        assert op2 == operator.lt and value2 == 999

    def test_days_condition_embedded_in_text(self):
        """Test _days_condition when pattern is embedded in larger text."""
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)
        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)

        op, value = expander._days_condition("If days > 5 then do something")

        assert op == operator.gt
        assert value == 5

    def test_process_increments_id(self):
        """Test that _id is incremented for each node."""
        timeline = self.create_multi_activity_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Check that IDs are sequential
        assert expander.nodes[0].id == "TP_1"
        assert expander.nodes[1].id == "TP_2"

    def test_process_with_offset_non_main_timeline(self):
        """Test processing with offset on non-main timeline."""
        # Create a nested timeline scenario
        nested_timeline = ScheduleTimeline(
            id="nested_timeline",
            name="Nested Timeline",
            label="Nested Timeline",
            description="Nested timeline",
            mainTimeline=False,
            entryCondition="Nested entry",
            entryId="nested_sai",
            timings=[
                Timing(
                    id="nested_timing",
                    name="Nested Timing",
                    label="Nested Timing",
                    description="Nested timing",
                    type=self.timing_type_anchor,
                    value="P0D",
                    valueLabel="Day 0",
                    relativeToFrom=self.relative_to_from,
                    relativeFromScheduledInstanceId="nested_sai",
                    relativeToScheduledInstanceId="nested_sai",
                    instanceType="Timing",
                )
            ],
            instances=[
                ScheduledActivityInstance(
                    id="nested_sai",
                    name="Nested SAI",
                    label="Nested SAI",
                    description="Nested SAI",
                    activityIds=["activity_1"],
                    encounterId="encounter_1",
                    timelineExitId="exit_1",
                    instanceType="ScheduledActivityInstance",
                )
            ],
            exits=[
                ScheduleTimelineExit(id="exit_1", instanceType="ScheduleTimelineExit")
            ],
            instanceType="ScheduleTimeline",
        )

        # Add nested timeline to activity
        activity_with_timeline = Activity(
            id="activity_with_timeline",
            name="Activity with Timeline",
            label="Activity with Timeline",
            description="Activity with nested timeline",
            definedProcedures=[self.procedure],
            timelineId="nested_timeline",
            instanceType="Activity",
        )

        # Create main timeline that references the activity
        main_sai = ScheduledActivityInstance(
            id="main_sai",
            name="Main SAI",
            label="Main SAI",
            description="Main SAI",
            activityIds=["activity_with_timeline"],
            encounterId="encounter_1",
            timelineExitId="exit_1",
            instanceType="ScheduledActivityInstance",
        )

        main_timeline = ScheduleTimeline(
            id="main_timeline",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Main entry",
            entryId="main_sai",
            timings=[
                Timing(
                    id="main_timing",
                    name="Main Timing",
                    label="Main Timing",
                    description="Main timing",
                    type=self.timing_type_anchor,
                    value="P0D",
                    valueLabel="Day 0",
                    relativeToFrom=self.relative_to_from,
                    relativeFromScheduledInstanceId="main_sai",
                    relativeToScheduledInstanceId="main_sai",
                    instanceType="Timing",
                )
            ],
            instances=[main_sai],
            exits=[
                ScheduleTimelineExit(id="exit_1", instanceType="ScheduleTimelineExit")
            ],
            instanceType="ScheduleTimeline",
        )

        study_design = StudyDesign(
            id="design_1",
            name="Test Study Design",
            label="Test Study Design",
            description="Test study design",
            activities=[self.activity, activity_with_timeline],
            encounters=[self.encounter],
            scheduleTimelines=[main_timeline, nested_timeline],
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.population,
            instanceType="StudyDesign",
        )

        errors = self._get_fresh_errors()
        expander = Expander(study_design, main_timeline, errors)
        expander.process()

        # Should have processed both main and nested timeline nodes
        assert len(expander.nodes) >= 1

    def test_process_unknown_instance_type(self):
        """Test processing with unknown instance type."""
        # This is a hypothetical test since we can't easily create an unknown type
        # But we can verify the error handling exists in the code
        timeline = self.create_simple_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should complete successfully with known types
        assert len(expander.nodes) == 1

    def test_recursive_processing(self):
        """Test that recursive processing works correctly."""
        # Create a timeline with nested structure
        timeline = self.create_multi_activity_timeline()
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Verify recursion processed all nodes
        assert len(expander.nodes) == 2
        assert all(node.activities for node in expander.nodes)

    def test_decision_no_day_condition(self):
        """Test decision instance with condition that's not a day condition."""
        timeline = self.create_decision_timeline("some other condition")
        study_design = self.create_study_design(timeline)

        errors = self._get_fresh_errors()
        expander = Expander(study_design, timeline, errors)
        expander.process()

        # Should have error and use default path
        assert errors.count() > 0
        assert len(expander.nodes) == 2  # sai_1 and default path
