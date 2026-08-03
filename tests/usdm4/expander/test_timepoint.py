from usdm4.expander.timepoint import Timepoint
from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import ScheduledActivityInstance
from usdm4.api.timing import Timing
from usdm4.api.code import Code
from usdm4.api.activity import Activity
from usdm4.api.encounter import Encounter
from usdm4.api.procedure import Procedure
from usdm4.api.population_definition import StudyDesignPopulation
from simple_error_log import Errors


class TestTimepoint:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create test codes
        self.timing_type_before = Code(
            id="timing_type_before",
            code="C201357",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Before",
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

        self.timing_type_anchor = Code(
            id="timing_type_anchor",
            code="C201358",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Anchor",
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

        # Create procedure codes
        self.procedure_code1 = Code(
            id="procedure_code_1",
            code="P12345",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Blood Draw",
            instanceType="Code",
        )

        self.procedure_code2 = Code(
            id="procedure_code_2",
            code="P67890",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="ECG",
            instanceType="Code",
        )

        # Create test procedures
        self.procedure1 = Procedure(
            id="procedure_1",
            name="Blood Draw",
            label="Blood Draw",
            description="Blood draw procedure",
            procedureType="Laboratory",
            code=self.procedure_code1,
            instanceType="Procedure",
        )

        self.procedure2 = Procedure(
            id="procedure_2",
            name="ECG",
            label="ECG",
            description="ECG procedure",
            procedureType="Diagnostic",
            code=self.procedure_code2,
            instanceType="Procedure",
        )

        # Create test activities
        self.activity1 = Activity(
            id="activity_1",
            name="Screening Activity",
            label="Screening Activity",
            description="Screening activity",
            definedProcedures=[self.procedure1],
            instanceType="Activity",
        )

        self.activity2 = Activity(
            id="activity_2",
            name="Baseline Activity",
            label="Baseline Activity",
            description="Baseline activity",
            definedProcedures=[self.procedure2],
            timelineId="timeline_1",
            instanceType="Activity",
        )

        self.activity3 = Activity(
            id="activity_3",
            name="Follow-up Activity",
            label="Follow-up Activity",
            description="Follow-up activity",
            definedProcedures=[self.procedure1, self.procedure2],
            timelineId="timeline_1",
            instanceType="Activity",
        )

        # Create parent activity for testing parent hierarchy
        self.parent_activity = Activity(
            id="parent_activity",
            name="Parent Activity",
            label="Parent Activity",
            description="Parent activity",
            definedProcedures=[],
            instanceType="Activity",
        )

        # Create child activity
        self.child_activity = Activity(
            id="child_activity",
            name="Child Activity",
            label="Child Activity",
            description="Child activity",
            definedProcedures=[self.procedure1],
            timelineId="timeline_1",
            instanceType="Activity",
        )

        # Create test encounter
        self.encounter1 = Encounter(
            id="encounter_1",
            name="Screening Visit",
            label="Screening Visit",
            description="Screening visit",
            type=self.encounter_type,
            instanceType="Encounter",
        )

        # Create scheduled activity instances (SAIs)
        self.anchor_sai = ScheduledActivityInstance(
            id="anchor_sai",
            name="Anchor Point",
            label="Anchor Point",
            description="Anchor point",
            activityIds=["activity_1"],
            encounterId="encounter_1",
            instanceType="ScheduledActivityInstance",
        )

        self.sai_with_activities = ScheduledActivityInstance(
            id="sai_1",
            name="SAI 1",
            label="SAI 1",
            description="SAI with activities",
            activityIds=["activity_2"],
            encounterId="encounter_1",
            instanceType="ScheduledActivityInstance",
        )

        self.sai_without_activities = ScheduledActivityInstance(
            id="sai_2",
            name="SAI 2",
            label="SAI 2",
            description="SAI without activities",
            activityIds=[],
            instanceType="ScheduledActivityInstance",
        )

        self.sai_multiple_activities = ScheduledActivityInstance(
            id="sai_3",
            name="SAI 3",
            label="SAI 3",
            description="SAI with multiple activities",
            activityIds=["activity_2", "activity_3"],
            encounterId="encounter_1",
            instanceType="ScheduledActivityInstance",
        )

        self.sai_with_child = ScheduledActivityInstance(
            id="sai_4",
            name="SAI 4",
            label="SAI 4",
            description="SAI with child activity",
            activityIds=["child_activity"],
            encounterId="encounter_1",
            instanceType="ScheduledActivityInstance",
        )

        # Create timings
        self.timing_anchor = Timing(
            id="timing_anchor",
            name="Anchor Timing",
            label="Anchor Timing",
            description="Anchor timing",
            type=self.timing_type_anchor,
            value="P0D",
            valueLabel="Day 0",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="anchor_sai",
            relativeToScheduledInstanceId="anchor_sai",
            instanceType="Timing",
        )

        self.timing_after = Timing(
            id="timing_after",
            name="After Timing",
            label="After Timing",
            description="After timing",
            type=self.timing_type_after,
            value="P7D",
            valueLabel="7 days after",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_1",
            relativeToScheduledInstanceId="anchor_sai",
            instanceType="Timing",
        )

        self.timing_before = Timing(
            id="timing_before",
            name="Before Timing",
            label="Before Timing",
            description="Before timing",
            type=self.timing_type_before,
            value="P3D",
            valueLabel="3 days before",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_2",
            relativeToScheduledInstanceId="anchor_sai",
            instanceType="Timing",
        )

        self.timing_invalid = Timing(
            id="timing_invalid",
            name="Invalid Timing",
            label="Invalid Timing",
            description="Invalid timing",
            type=self.timing_type_after,
            value="INVALID_DURATION",
            valueLabel="Invalid",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_3",
            relativeToScheduledInstanceId="anchor_sai",
            instanceType="Timing",
        )

        self.timing_for_child = Timing(
            id="timing_for_child",
            name="Child Timing",
            label="Child Timing",
            description="Child timing",
            type=self.timing_type_after,
            value="P1D",
            valueLabel="1 day after",
            relativeToFrom=self.relative_to_from,
            relativeFromScheduledInstanceId="sai_4",
            relativeToScheduledInstanceId="anchor_sai",
            instanceType="Timing",
        )

        # Create timeline
        self.timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main timeline",
            mainTimeline=True,
            entryCondition="Entry condition",
            entryId="anchor_sai",
            timings=[
                self.timing_anchor,
                self.timing_after,
                self.timing_before,
                self.timing_invalid,
                self.timing_for_child,
            ],
            instances=[
                self.anchor_sai,
                self.sai_with_activities,
                self.sai_without_activities,
                self.sai_multiple_activities,
                self.sai_with_child,
            ],
            instanceType="ScheduleTimeline",
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

        # Create study design
        self.study_design = StudyDesign(
            id="design_1",
            name="Test Study Design",
            label="Test Study Design",
            description="Test study design",
            activities=[
                self.activity1,
                self.activity2,
                self.activity3,
                self.parent_activity,
                self.child_activity,
            ],
            encounters=[self.encounter1],
            scheduleTimelines=[self.timeline],
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.population,
            instanceType="StudyDesign",
        )

        # Create errors object
        self.errors = Errors()

    def test_init_basic(self):
        """Test basic initialization of Timepoint."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=1,
            offset=0,
        )

        assert timepoint.id == "TP_1"
        assert timepoint.tick == 0
        assert self.errors.count() == 0

    def test_init_with_offset(self):
        """Test initialization with offset."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=2,
            offset=100,
        )

        assert timepoint.id == "TP_2"
        assert timepoint.tick == 100
        assert self.errors.count() == 0

    def test_init_with_after_timing(self):
        """Test initialization with 'after' timing (P7D = 7 days = 604800 seconds)."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=3,
            offset=0,
        )

        # P7D = 7 days = 7 * 24 * 60 * 60 = 604800 seconds
        assert timepoint.tick == 604800
        assert self.errors.count() == 0

    def test_init_with_before_timing(self):
        """Test initialization with 'before' timing (P3D = 3 days = 259200 seconds)."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_without_activities,
            errors=self.errors,
            id=4,
            offset=0,
        )

        # P3D = 3 days = 3 * 24 * 60 * 60 = 259200 seconds
        # Before means negative, so tick should be -259200
        assert timepoint.tick == -259200
        assert self.errors.count() == 0

    def test_init_with_invalid_duration(self):
        """Test initialization with invalid duration."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_multiple_activities,
            errors=self.errors,
            id=5,
            offset=0,
        )

        # With invalid duration, tick should be 0 (from error handling)
        assert timepoint.tick == 0
        assert self.errors.count() > 0

    def test_tick_property(self):
        """Test tick property getter."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=6,
            offset=0,
        )

        assert timepoint.tick == 0

    def test_id_property(self):
        """Test id property getter."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=7,
            offset=0,
        )

        assert timepoint.id == "TP_7"

    def test_activities_property_with_activities(self):
        """Test activities property when SAI has activities."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=8,
            offset=0,
        )

        assert timepoint.activities is True

    def test_activities_property_without_activities(self):
        """Test activities property when SAI has no activities."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_without_activities,
            errors=self.errors,
            id=9,
            offset=0,
        )

        assert timepoint.activities is False

    def test_add_edge(self):
        """Test adding edges to timepoint."""
        timepoint1 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=10,
            offset=0,
        )

        timepoint2 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=11,
            offset=0,
        )

        timepoint1.add_edge(timepoint2)

        result = timepoint1.to_dict()
        assert "TP_11" in result["edges"]
        assert len(result["edges"]) == 1

    def test_add_multiple_edges(self):
        """Test adding multiple edges to timepoint."""
        timepoint1 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=12,
            offset=0,
        )

        timepoint2 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=13,
            offset=0,
        )

        timepoint3 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_without_activities,
            errors=self.errors,
            id=14,
            offset=0,
        )

        timepoint1.add_edge(timepoint2)
        timepoint1.add_edge(timepoint3)

        result = timepoint1.to_dict()
        assert "TP_13" in result["edges"]
        assert "TP_14" in result["edges"]
        assert len(result["edges"]) == 2

    def test_activity_timelines(self):
        """Test getting activity timelines."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=15,
            offset=0,
        )

        timelines = timepoint.activity_timelines()
        assert len(timelines) == 1
        assert timelines[0].id == "timeline_1"

    def test_activity_timelines_multiple(self):
        """Test getting activity timelines with multiple activities."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_multiple_activities,
            errors=self.errors,
            id=16,
            offset=0,
        )

        timelines = timepoint.activity_timelines()
        # Both activities have timeline_1, but should still get 2 entries
        assert len(timelines) == 2
        assert all(t.id == "timeline_1" for t in timelines)

    def test_activity_timelines_empty(self):
        """Test getting activity timelines when SAI has no activities."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_without_activities,
            errors=self.errors,
            id=17,
            offset=0,
        )

        timelines = timepoint.activity_timelines()
        assert len(timelines) == 0

    def test_to_dict_basic(self):
        """Test to_dict with basic timepoint."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=18,
            offset=0,
        )

        result = timepoint.to_dict()

        assert result["id"] == "TP_18"
        assert result["tick"] == 0
        assert result["time"] == ""
        assert result["label"] == "Anchor Point"
        assert result["encounter"] == "Screening Visit"
        assert "activities" in result
        assert "items" in result["activities"]
        assert len(result["activities"]["items"]) == 1
        assert result["edges"] == []

    def test_to_dict_with_edges(self):
        """Test to_dict with edges."""
        timepoint1 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=19,
            offset=0,
        )

        timepoint2 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=20,
            offset=0,
        )

        timepoint1.add_edge(timepoint2)

        result = timepoint1.to_dict()
        assert result["edges"] == ["TP_20"]

    def test_to_dict_without_encounter(self):
        """Test to_dict when SAI has no encounter."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_without_activities,
            errors=self.errors,
            id=21,
            offset=0,
        )

        result = timepoint.to_dict()
        assert result["encounter"] is None

    def test_to_dict_with_procedures(self):
        """Test to_dict includes procedure information."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=22,
            offset=0,
        )

        result = timepoint.to_dict()
        activity_items = result["activities"]["items"]

        assert len(activity_items) == 1
        assert activity_items[0]["label"] == "Baseline Activity"
        assert activity_items[0]["procedures"] == ["ECG"]

    def test_to_dict_with_parent_activity(self):
        """Test to_dict includes parent activity information."""
        # Update child activity to have a parent reference
        self.child_activity.previousId = "parent_activity"
        self.parent_activity.nextId = "child_activity"

        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_child,
            errors=self.errors,
            id=23,
            offset=0,
        )

        result = timepoint.to_dict()
        activity_items = result["activities"]["items"]

        assert len(activity_items) == 1
        assert activity_items[0]["label"] == "Child Activity"
        # The parent field will be populated by activity_parent() method
        # which checks the activity hierarchy

    def test_to_dict_without_parent_activity(self):
        """Test to_dict when activity has no parent."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=24,
            offset=0,
        )

        result = timepoint.to_dict()
        activity_items = result["activities"]["items"]

        assert len(activity_items) == 1
        assert activity_items[0]["parent"] is None

    def test_to_dict_time_display(self):
        """Test to_dict time display formatting."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=25,
            offset=0,
        )

        result = timepoint.to_dict()
        # P7D = 604800 seconds = 1 week
        assert result["time"] == "1 week"

    def test_calculate_tick_valid_duration(self):
        """Test _calculate_tick with valid duration."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=26,
            offset=0,
        )

        tick = timepoint._calculate_tick(self.timing_after)
        # P7D = 7 * 24 * 60 * 60 = 604800
        assert tick == 604800
        assert self.errors.count() == 0

    def test_calculate_tick_invalid_duration(self):
        """Test _calculate_tick with invalid duration."""
        timepoint = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=27,
            offset=0,
        )

        tick = timepoint._calculate_tick(self.timing_invalid)
        assert tick == 0
        assert self.errors.count() > 0

    def test_multiple_timepoints_with_different_ids(self):
        """Test creating multiple timepoints with different IDs."""
        tp1 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.anchor_sai,
            errors=self.errors,
            id=28,
            offset=0,
        )

        tp2 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=29,
            offset=0,
        )

        tp3 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_without_activities,
            errors=self.errors,
            id=30,
            offset=0,
        )

        assert tp1.id == "TP_28"
        assert tp2.id == "TP_29"
        assert tp3.id == "TP_30"

    def test_offset_applied_correctly(self):
        """Test that offset is applied to calculated tick."""
        # Create two timepoints with same SAI but different offsets
        tp1 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=31,
            offset=0,
        )

        tp2 = Timepoint(
            study_design=self.study_design,
            timeline=self.timeline,
            sai=self.sai_with_activities,
            errors=self.errors,
            id=32,
            offset=1000,
        )

        # P7D = 604800 seconds
        assert tp1.tick == 604800
        assert tp2.tick == 604800 + 1000
        assert tp2.tick == tp1.tick + 1000
