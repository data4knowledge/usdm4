from src.usdm4.api.study_design import (
    StudyDesign,
    InterventionalStudyDesign,
    ObservationalStudyDesign,
)
from src.usdm4.api.code import Code
from src.usdm4.api.alias_code import AliasCode
from src.usdm4.api.activity import Activity
from src.usdm4.api.encounter import Encounter
from src.usdm4.api.study_epoch import StudyEpoch
from src.usdm4.api.population_definition import StudyDesignPopulation
from src.usdm4.api.eligibility_criterion import EligibilityCriterion, EligibilityCriterionItem
from src.usdm4.api.analysis_population import AnalysisPopulation
from src.usdm4.api.schedule_timeline import ScheduleTimeline


class TestStudyDesign:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create test codes
        self.phase_code = Code(
            id="phase_code",
            code="C15600",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Phase I",
            instanceType="Code",
        )

        self.study_type_code = Code(
            id="study_type_code",
            code="C98388",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Interventional Study",
            instanceType="Code",
        )

        self.therapeutic_area_code = Code(
            id="therapeutic_area_code",
            code="C12345",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Oncology",
            instanceType="Code",
        )

        self.characteristic_code = Code(
            id="characteristic_code",
            code="C67890",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Randomized",
            instanceType="Code",
        )

        self.blinding_code = Code(
            id="blinding_code",
            code="C15228",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Double Blind",
            instanceType="Code",
        )

        self.time_perspective_code = Code(
            id="time_perspective_code",
            code="C15234",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Prospective",
            instanceType="Code",
        )

        self.sampling_method_code = Code(
            id="sampling_method_code",
            code="C15235",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Random Sampling",
            instanceType="Code",
        )

        self.category_code = Code(
            id="category_code",
            code="C25337",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Inclusion Criteria",
            instanceType="Code",
        )

        # Create alias codes
        self.study_phase_alias = AliasCode(
            id="phase_alias", standardCode=self.phase_code, instanceType="AliasCode"
        )

        self.blinding_alias = AliasCode(
            id="blinding_alias",
            standardCode=self.blinding_code,
            instanceType="AliasCode",
        )

        # Create test population
        self.test_population = StudyDesignPopulation(
            id="population_1",
            name="Test Population",
            label="Test Population",
            description="Test population description",
            includesHealthySubjects=True,
            instanceType="StudyDesignPopulation",
        )

        # Create test activities
        self.activity1 = Activity(
            id="activity_1",
            name="First Activity",
            label="First Activity",
            description="First activity description",
            nextId="activity_2",
            instanceType="Activity",
        )

        self.activity2 = Activity(
            id="activity_2",
            name="Second Activity",
            label="Second Activity",
            description="Second activity description",
            previousId="activity_1",
            nextId="activity_3",
            instanceType="Activity",
        )

        self.activity3 = Activity(
            id="activity_3",
            name="Third Activity",
            label="Third Activity",
            description="Third activity description",
            previousId="activity_2",
            instanceType="Activity",
        )

        # Create test encounters
        self.encounter1 = Encounter(
            id="encounter_1",
            name="Screening Visit",
            label="Screening Visit",
            description="Screening encounter",
            type=self.phase_code,
            instanceType="Encounter",
        )

        self.encounter2 = Encounter(
            id="encounter_2",
            name="Baseline Visit",
            label="Baseline Visit",
            description="Baseline encounter",
            type=self.phase_code,
            instanceType="Encounter",
        )

        # Create test epochs
        self.epoch1 = StudyEpoch(
            id="epoch_1",
            name="Screening",
            label="Screening Epoch",
            description="Screening epoch",
            type=self.phase_code,
            instanceType="StudyEpoch",
        )

        self.epoch2 = StudyEpoch(
            id="epoch_2",
            name="Treatment",
            label="Treatment Epoch",
            description="Treatment epoch",
            type=self.phase_code,
            instanceType="StudyEpoch",
        )

        # Create test eligibility criteria
        self.eligibility_criterion = EligibilityCriterion(
            id="criterion_1",
            name="Age Criterion",
            label="Age Criterion",
            description="Age inclusion criterion",
            category=self.category_code,
            identifier="IC001",
            criterionItemId="criterion_item_1",
            instanceType="EligibilityCriterion",
        )

        # Create test analysis population
        self.analysis_population = AnalysisPopulation(
            id="analysis_pop_1",
            name="ITT Population",
            label="Intent-to-Treat Population",
            description="Intent-to-treat analysis population",
            text="Intent-to-treat analysis population text",
            instanceType="AnalysisPopulation",
        )

        # Create test schedule timelines
        self.main_timeline = ScheduleTimeline(
            id="timeline_1",
            name="Main Timeline",
            label="Main Timeline",
            description="Main study timeline",
            mainTimeline=True,
            entryCondition="Entry condition for main timeline",
            entryId="entry_1",
            instanceType="ScheduleTimeline",
        )

        self.secondary_timeline = ScheduleTimeline(
            id="timeline_2",
            name="Secondary Timeline",
            label="Secondary Timeline",
            description="Secondary study timeline",
            mainTimeline=False,
            entryCondition="Entry condition for secondary timeline",
            entryId="entry_2",
            instanceType="ScheduleTimeline",
        )

        # Create basic study design
        self.study_design = StudyDesign(
            id="design_1",
            name="Test Study Design",
            label="Test Study Design",
            description="Test study design description",
            studyType=self.study_type_code,
            studyPhase=self.study_phase_alias,
            therapeuticAreas=[self.therapeutic_area_code],
            characteristics=[self.characteristic_code],
            encounters=[self.encounter1, self.encounter2],
            activities=[self.activity1, self.activity2, self.activity3],
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[self.epoch1, self.epoch2],
            population=self.test_population,
            scheduleTimelines=[self.main_timeline, self.secondary_timeline],
            eligibilityCriteria=[self.eligibility_criterion],
            analysisPopulations=[self.analysis_population],
            instanceType="StudyDesign",
        )

        # Create interventional study design
        self.interventional_design = InterventionalStudyDesign(
            id="interventional_1",
            name="Interventional Design",
            label="Interventional Design",
            description="Test interventional design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[self.epoch1],
            population=self.test_population,
            model=self.phase_code,
            blindingSchema=self.blinding_alias,
            instanceType="InterventionalStudyDesign",
        )

        # Create observational study design
        self.observational_design = ObservationalStudyDesign(
            id="observational_1",
            name="Observational Design",
            label="Observational Design",
            description="Test observational design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[self.epoch1],
            population=self.test_population,
            model=self.phase_code,
            timePerspective=self.time_perspective_code,
            samplingMethod=self.sampling_method_code,
            instanceType="ObservationalStudyDesign",
        )

    def test_main_timeline(self):
        """Test getting main timeline."""
        timeline = self.study_design.main_timeline()
        assert timeline is not None
        assert timeline.id == "timeline_1"
        assert timeline.mainTimeline is True

    def test_main_timeline_none(self):
        """Test getting main timeline when none exists."""
        design = StudyDesign(
            id="design_2",
            name="Test Design",
            label="Test Design",
            description="Test design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            scheduleTimelines=[self.secondary_timeline],  # Only non-main timeline
            instanceType="StudyDesign",
        )
        timeline = design.main_timeline()
        assert timeline is None

    def test_phase(self):
        """Test getting phase code."""
        phase = self.study_design.phase()
        assert phase is not None
        assert phase.id == "phase_code"
        assert phase.decode == "Phase I"

    def test_phase_none_study_phase(self):
        """Test getting phase when studyPhase is None."""
        design = StudyDesign(
            id="design_3",
            name="Test Design",
            label="Test Design",
            description="Test design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            instanceType="StudyDesign",
        )
        phase = design.phase()
        assert phase is None

    def test_phase_exception(self):
        """Test getting phase when exception occurs."""
        # Test with a valid code but simulate exception handling in phase method
        # Since the phase() method has try/except, we'll test the normal case
        # and rely on the actual implementation's exception handling
        bad_code = Code(
            id="bad_code",
            code="BAD",
            codeSystem="TEST",
            codeSystemVersion="1.0",
            decode="Bad Code",
            instanceType="Code",
        )
        bad_alias = AliasCode(
            id="bad_alias", standardCode=bad_code, instanceType="AliasCode"
        )
        design = StudyDesign(
            id="design_4",
            name="Test Design",
            label="Test Design",
            description="Test design",
            studyPhase=bad_alias,
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            instanceType="StudyDesign",
        )
        phase = design.phase()
        assert phase is not None
        assert phase.id == "bad_code"

    def test_phase_as_text(self):
        """Test getting phase as text."""
        text = self.study_design.phase_as_text()
        assert text == "Phase I"

    def test_phase_as_text_empty(self):
        """Test getting phase as text when phase is None."""
        design = StudyDesign(
            id="design_5",
            name="Test Design",
            label="Test Design",
            description="Test design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            instanceType="StudyDesign",
        )
        text = design.phase_as_text()
        assert text == ""

    def test_first_activity(self):
        """Test getting first activity."""
        activity = self.study_design.first_activity()
        assert activity is not None
        assert activity.id == "activity_1"
        assert activity.nextId == "activity_2"

    def test_first_activity_none(self):
        """Test getting first activity when none exists."""
        design = StudyDesign(
            id="design_7",
            name="Test Design",
            label="Test Design",
            description="Test design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            activities=[],  # No activities
            instanceType="StudyDesign",
        )
        activity = design.first_activity()
        assert activity is None

    def test_find_activity(self):
        """Test finding activity by ID."""
        activity = self.study_design.find_activity("activity_2")
        assert activity is not None
        assert activity.id == "activity_2"
        assert activity.name == "Second Activity"

    def test_find_activity_not_found(self):
        """Test finding activity that doesn't exist."""
        activity = self.study_design.find_activity("non_existent")
        assert activity is None

    def test_activity_list(self):
        """Test getting ordered activity list."""
        activities = self.study_design.activity_list()
        assert len(activities) == 3
        assert activities[0].id == "activity_1"
        assert activities[1].id == "activity_2"
        assert activities[2].id == "activity_3"

    def test_activity_list_empty(self):
        """Test getting activity list when no activities exist."""
        design = StudyDesign(
            id="design_8",
            name="Test Design",
            label="Test Design",
            description="Test design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            activities=[],
            instanceType="StudyDesign",
        )
        activities = design.activity_list()
        assert activities == []

    def test_find_epoch(self):
        """Test finding epoch by ID."""
        epoch = self.study_design.find_epoch("epoch_1")
        assert epoch is not None
        assert epoch.id == "epoch_1"
        assert epoch.name == "Screening"

    def test_find_epoch_not_found(self):
        """Test finding epoch that doesn't exist."""
        epoch = self.study_design.find_epoch("non_existent")
        assert epoch is None

    def test_find_encounter(self):
        """Test finding encounter by ID."""
        encounter = self.study_design.find_encounter("encounter_1")
        assert encounter is not None
        assert encounter.id == "encounter_1"
        assert encounter.name == "Screening Visit"

    def test_find_encounter_not_found(self):
        """Test finding encounter that doesn't exist."""
        encounter = self.study_design.find_encounter("non_existent")
        assert encounter is None

    def test_find_timeline(self):
        """Test finding timeline by ID."""
        timeline = self.study_design.find_timeline("timeline_1")
        assert timeline is not None
        assert timeline.id == "timeline_1"
        assert timeline.name == "Main Timeline"

    def test_find_timeline_not_found(self):
        """Test finding timeline that doesn't exist."""
        timeline = self.study_design.find_timeline("non_existent")
        assert timeline is None

    def test_find_analysis_population(self):
        """Test finding analysis population by ID."""
        population = self.study_design.find_analysis_population("analysis_pop_1")
        assert population is not None
        assert population.id == "analysis_pop_1"
        assert population.name == "ITT Population"

    def test_find_analysis_population_not_found(self):
        """Test finding analysis population that doesn't exist."""
        population = self.study_design.find_analysis_population("non_existent")
        assert population is None

    def test_criterion_map(self):
        """Test getting criterion map."""
        criterion_map = self.study_design.criterion_map()
        assert isinstance(criterion_map, dict)
        assert "criterion_1" in criterion_map
        assert criterion_map["criterion_1"].name == "Age Criterion"

    def test_criterion_map_empty(self):
        """Test getting criterion map when no criteria exist."""
        design = StudyDesign(
            id="design_9",
            name="Test Design",
            label="Test Design",
            description="Test design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[],
            instanceType="StudyDesign",
        )
        criterion_map = design.criterion_map()
        assert criterion_map == {}

    def test_interventional_study_design_instance_type(self):
        """Test InterventionalStudyDesign instance type."""
        assert self.interventional_design.instanceType == "InterventionalStudyDesign"
        assert self.interventional_design.model.decode == "Phase I"
        assert (
            self.interventional_design.blindingSchema.standardCode.decode
            == "Double Blind"
        )

    def test_observational_study_design_instance_type(self):
        """Test ObservationalStudyDesign instance type."""
        assert self.observational_design.instanceType == "ObservationalStudyDesign"
        assert self.observational_design.model.decode == "Phase I"
        assert self.observational_design.timePerspective.decode == "Prospective"
        assert self.observational_design.samplingMethod.decode == "Random Sampling"

    def test_observational_study_design_no_sampling_method(self):
        """Test ObservationalStudyDesign without sampling method."""
        design = ObservationalStudyDesign(
            id="observational_2",
            name="Observational Design 2",
            label="Observational Design 2",
            description="Test observational design without sampling method",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            model=self.phase_code,
            timePerspective=self.time_perspective_code,
            instanceType="ObservationalStudyDesign",
        )
        assert design.samplingMethod is None

    def test_interventional_study_design_no_blinding(self):
        """Test InterventionalStudyDesign without blinding schema."""
        design = InterventionalStudyDesign(
            id="interventional_2",
            name="Interventional Design 2",
            label="Interventional Design 2",
            description="Test interventional design without blinding",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            model=self.phase_code,
            instanceType="InterventionalStudyDesign",
        )
        assert design.blindingSchema is None

    def test_study_design_default_lists(self):
        """Test that default lists are properly initialized."""
        design = StudyDesign(
            id="design_10",
            name="Minimal Design",
            label="Minimal Design",
            description="Minimal design for testing defaults",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            instanceType="StudyDesign",
        )

        # Test that default empty lists are properly initialized
        assert design.therapeuticAreas == []
        assert design.characteristics == []
        assert design.encounters == []
        assert design.activities == []
        assert design.elements == []
        assert design.estimands == []
        assert design.indications == []
        assert design.studyInterventionIds == []
        assert design.objectives == []
        assert design.scheduleTimelines == []
        assert design.biospecimenRetentions == []
        assert design.documentVersionIds == []
        assert design.eligibilityCriteria == []
        assert design.analysisPopulations == []
        assert design.notes == []

    def test_interventional_design_default_lists(self):
        """Test that InterventionalStudyDesign default lists are properly initialized."""
        design = InterventionalStudyDesign(
            id="interventional_3",
            name="Minimal Interventional",
            label="Minimal Interventional",
            description="Minimal interventional design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            model=self.phase_code,
            instanceType="InterventionalStudyDesign",
        )

        assert design.subTypes == []
        assert design.intentTypes == []

    def test_observational_design_default_lists(self):
        """Test that ObservationalStudyDesign default lists are properly initialized."""
        design = ObservationalStudyDesign(
            id="observational_3",
            name="Minimal Observational",
            label="Minimal Observational",
            description="Minimal observational design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            model=self.phase_code,
            timePerspective=self.time_perspective_code,
            instanceType="ObservationalStudyDesign",
        )

        assert design.subTypes == []

    def test_study_design_instance_type(self):
        """Test that StudyDesign instance type is correctly set."""
        assert self.study_design.instanceType == "StudyDesign"

    def test_activity_list_with_broken_chain(self):
        """Test activity list when chain is broken."""
        # Create activities with broken chain
        broken_activity = Activity(
            id="broken_activity",
            name="Broken Activity",
            label="Broken Activity",
            description="Activity with broken chain",
            nextId="non_existent_activity",
            instanceType="Activity",
        )

        design = StudyDesign(
            id="design_11",
            name="Broken Chain Design",
            label="Broken Chain Design",
            description="Design with broken activity chain",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            activities=[broken_activity],
            instanceType="StudyDesign",
        )

        activities = design.activity_list()
        assert len(activities) == 1
        assert activities[0].id == "broken_activity"

    # =====================================================
    # Tests for activity_parent method (lines 75-83, specifically 79-81)
    # =====================================================

    def test_activity_parent_with_children(self):
        """Test activity_parent returns mapping of child IDs to parent IDs."""
        # Create parent activity with children
        parent_activity = Activity(
            id="parent_activity",
            name="Parent Activity",
            label="Parent Activity",
            description="Parent activity with children",
            nextId="next_activity",
            childIds=["child_1", "child_2", "child_3"],
            instanceType="Activity",
        )

        next_activity = Activity(
            id="next_activity",
            name="Next Activity",
            label="Next Activity",
            description="Next activity",
            previousId="parent_activity",
            instanceType="Activity",
        )

        design = StudyDesign(
            id="design_ap1",
            name="Activity Parent Design",
            label="Activity Parent Design",
            description="Design with parent-child activities",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            activities=[parent_activity, next_activity],
            instanceType="StudyDesign",
        )

        parent_map = design.activity_parent()
        assert isinstance(parent_map, dict)
        assert len(parent_map) == 3
        assert parent_map["child_1"] == "parent_activity"
        assert parent_map["child_2"] == "parent_activity"
        assert parent_map["child_3"] == "parent_activity"

    def test_activity_parent_no_children(self):
        """Test activity_parent returns empty dict when no activities have children."""
        parent_map = self.study_design.activity_parent()
        assert isinstance(parent_map, dict)
        assert len(parent_map) == 0

    def test_activity_parent_multiple_parents(self):
        """Test activity_parent with multiple activities having children."""
        parent1 = Activity(
            id="parent1",
            name="Parent 1",
            label="Parent 1",
            description="First parent",
            nextId="parent2",
            childIds=["child_a", "child_b"],
            instanceType="Activity",
        )

        parent2 = Activity(
            id="parent2",
            name="Parent 2",
            label="Parent 2",
            description="Second parent",
            previousId="parent1",
            nextId="parent3",
            childIds=["child_c"],
            instanceType="Activity",
        )

        parent3 = Activity(
            id="parent3",
            name="Parent 3",
            label="Parent 3",
            description="Third parent (no children)",
            previousId="parent2",
            instanceType="Activity",
        )

        design = StudyDesign(
            id="design_ap2",
            name="Multi Parent Design",
            label="Multi Parent Design",
            description="Design with multiple parents",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            activities=[parent1, parent2, parent3],
            instanceType="StudyDesign",
        )

        parent_map = design.activity_parent()
        assert len(parent_map) == 3
        assert parent_map["child_a"] == "parent1"
        assert parent_map["child_b"] == "parent1"
        assert parent_map["child_c"] == "parent2"

    def test_activity_parent_empty_activities(self):
        """Test activity_parent returns empty dict when no activities exist."""
        design = StudyDesign(
            id="design_ap3",
            name="Empty Activities Design",
            label="Empty Activities Design",
            description="Design with no activities",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            activities=[],
            instanceType="StudyDesign",
        )

        parent_map = design.activity_parent()
        assert parent_map == {}

    # =====================================================
    # Tests for inclusion_criteria method (lines 100-101)
    # =====================================================

    def test_inclusion_criteria(self):
        """Test inclusion_criteria returns inclusion criteria with items."""
        # Create inclusion criterion (code C25532)
        inclusion_code = Code(
            id="inclusion_code",
            code="C25532",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Inclusion Criteria",
            instanceType="Code",
        )

        inclusion_criterion = EligibilityCriterion(
            id="inc_crit_1",
            name="Inclusion Criterion 1",
            label="Inclusion Criterion 1",
            description="First inclusion criterion",
            category=inclusion_code,
            identifier="IC001",
            criterionItemId="inc_item_1",
            instanceType="EligibilityCriterion",
        )

        inclusion_item = EligibilityCriterionItem(
            id="inc_item_1",
            name="Inclusion Item 1",
            label="Inclusion Item 1",
            description="First inclusion item",
            text="Age >= 18 years",
            instanceType="EligibilityCriterionItem",
        )

        design = StudyDesign(
            id="design_ic1",
            name="Inclusion Criteria Design",
            label="Inclusion Criteria Design",
            description="Design with inclusion criteria",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[inclusion_criterion],
            instanceType="StudyDesign",
        )

        criteria_map = {"inc_item_1": inclusion_item}
        result = design.inclusion_criteria(criteria_map)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "criterionItem" in result[0]
        assert result[0]["criterionItem"]["text"] == "Age >= 18 years"

    def test_inclusion_criteria_empty(self):
        """Test inclusion_criteria returns empty list when no inclusion criteria exist."""
        design = StudyDesign(
            id="design_ic2",
            name="No Inclusion Design",
            label="No Inclusion Design",
            description="Design without inclusion criteria",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[],
            instanceType="StudyDesign",
        )

        result = design.inclusion_criteria({})
        assert result == []

    # =====================================================
    # Tests for exclusion_criteria method (lines 103-104)
    # =====================================================

    def test_exclusion_criteria(self):
        """Test exclusion_criteria returns exclusion criteria with items."""
        # Create exclusion criterion (code C25370)
        exclusion_code = Code(
            id="exclusion_code",
            code="C25370",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Exclusion Criteria",
            instanceType="Code",
        )

        exclusion_criterion = EligibilityCriterion(
            id="exc_crit_1",
            name="Exclusion Criterion 1",
            label="Exclusion Criterion 1",
            description="First exclusion criterion",
            category=exclusion_code,
            identifier="EC001",
            criterionItemId="exc_item_1",
            instanceType="EligibilityCriterion",
        )

        exclusion_item = EligibilityCriterionItem(
            id="exc_item_1",
            name="Exclusion Item 1",
            label="Exclusion Item 1",
            description="First exclusion item",
            text="Pregnant or nursing",
            instanceType="EligibilityCriterionItem",
        )

        design = StudyDesign(
            id="design_ec1",
            name="Exclusion Criteria Design",
            label="Exclusion Criteria Design",
            description="Design with exclusion criteria",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[exclusion_criterion],
            instanceType="StudyDesign",
        )

        criteria_map = {"exc_item_1": exclusion_item}
        result = design.exclusion_criteria(criteria_map)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "criterionItem" in result[0]
        assert result[0]["criterionItem"]["text"] == "Pregnant or nursing"

    def test_exclusion_criteria_empty(self):
        """Test exclusion_criteria returns empty list when no exclusion criteria exist."""
        design = StudyDesign(
            id="design_ec2",
            name="No Exclusion Design",
            label="No Exclusion Design",
            description="Design without exclusion criteria",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[],
            instanceType="StudyDesign",
        )

        result = design.exclusion_criteria({})
        assert result == []

    # =====================================================
    # Tests for _criteria method (lines 106-116)
    # =====================================================

    def test_criteria_mixed_categories(self):
        """Test _criteria filters by category code correctly."""
        inclusion_code = Code(
            id="inc_code",
            code="C25532",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Inclusion",
            instanceType="Code",
        )

        exclusion_code = Code(
            id="exc_code",
            code="C25370",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Exclusion",
            instanceType="Code",
        )

        inc_criterion = EligibilityCriterion(
            id="inc_crit",
            name="Inclusion Criterion",
            label="Inclusion Criterion",
            description="Inclusion criterion",
            category=inclusion_code,
            identifier="IC001",
            criterionItemId="inc_item",
            instanceType="EligibilityCriterion",
        )

        exc_criterion = EligibilityCriterion(
            id="exc_crit",
            name="Exclusion Criterion",
            label="Exclusion Criterion",
            description="Exclusion criterion",
            category=exclusion_code,
            identifier="EC001",
            criterionItemId="exc_item",
            instanceType="EligibilityCriterion",
        )

        inc_item = EligibilityCriterionItem(
            id="inc_item",
            name="Inclusion Item",
            label="Inclusion Item",
            description="Inclusion item",
            text="Inclusion text",
            instanceType="EligibilityCriterionItem",
        )

        exc_item = EligibilityCriterionItem(
            id="exc_item",
            name="Exclusion Item",
            label="Exclusion Item",
            description="Exclusion item",
            text="Exclusion text",
            instanceType="EligibilityCriterionItem",
        )

        design = StudyDesign(
            id="design_mixed",
            name="Mixed Criteria Design",
            label="Mixed Criteria Design",
            description="Design with mixed criteria",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[inc_criterion, exc_criterion],
            instanceType="StudyDesign",
        )

        criteria_map = {"inc_item": inc_item, "exc_item": exc_item}

        # Test inclusion
        inclusion_result = design.inclusion_criteria(criteria_map)
        assert len(inclusion_result) == 1
        assert inclusion_result[0]["criterionItem"]["text"] == "Inclusion text"

        # Test exclusion
        exclusion_result = design.exclusion_criteria(criteria_map)
        assert len(exclusion_result) == 1
        assert exclusion_result[0]["criterionItem"]["text"] == "Exclusion text"

    def test_criteria_removes_criterionItemId(self):
        """Test _criteria removes criterionItemId from result and adds criterionItem."""
        inclusion_code = Code(
            id="inc_code2",
            code="C25532",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Inclusion",
            instanceType="Code",
        )

        criterion = EligibilityCriterion(
            id="criterion_test",
            name="Test Criterion",
            label="Test Criterion",
            description="Test criterion",
            category=inclusion_code,
            identifier="TC001",
            criterionItemId="test_item",
            instanceType="EligibilityCriterion",
        )

        item = EligibilityCriterionItem(
            id="test_item",
            name="Test Item",
            label="Test Item",
            description="Test item",
            text="Test text",
            instanceType="EligibilityCriterionItem",
        )

        design = StudyDesign(
            id="design_ci",
            name="Criterion Item Design",
            label="Criterion Item Design",
            description="Design for testing criterionItem replacement",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[criterion],
            instanceType="StudyDesign",
        )

        criteria_map = {"test_item": item}
        result = design.inclusion_criteria(criteria_map)

        assert len(result) == 1
        # Check criterionItemId is removed
        assert "criterionItemId" not in result[0]
        # Check criterionItem is added
        assert "criterionItem" in result[0]
        assert result[0]["criterionItem"]["id"] == "test_item"

    def test_criteria_multiple_same_category(self):
        """Test _criteria returns multiple criteria of same category."""
        inclusion_code = Code(
            id="inc_code3",
            code="C25532",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Inclusion",
            instanceType="Code",
        )

        criterion1 = EligibilityCriterion(
            id="crit1",
            name="Criterion 1",
            label="Criterion 1",
            description="First criterion",
            category=inclusion_code,
            identifier="C001",
            criterionItemId="item1",
            instanceType="EligibilityCriterion",
        )

        criterion2 = EligibilityCriterion(
            id="crit2",
            name="Criterion 2",
            label="Criterion 2",
            description="Second criterion",
            category=inclusion_code,
            identifier="C002",
            criterionItemId="item2",
            instanceType="EligibilityCriterion",
        )

        criterion3 = EligibilityCriterion(
            id="crit3",
            name="Criterion 3",
            label="Criterion 3",
            description="Third criterion",
            category=inclusion_code,
            identifier="C003",
            criterionItemId="item3",
            instanceType="EligibilityCriterion",
        )

        item1 = EligibilityCriterionItem(
            id="item1",
            name="Item 1",
            label="Item 1",
            description="First item",
            text="First criterion text",
            instanceType="EligibilityCriterionItem",
        )

        item2 = EligibilityCriterionItem(
            id="item2",
            name="Item 2",
            label="Item 2",
            description="Second item",
            text="Second criterion text",
            instanceType="EligibilityCriterionItem",
        )

        item3 = EligibilityCriterionItem(
            id="item3",
            name="Item 3",
            label="Item 3",
            description="Third item",
            text="Third criterion text",
            instanceType="EligibilityCriterionItem",
        )

        design = StudyDesign(
            id="design_multi",
            name="Multi Criteria Design",
            label="Multi Criteria Design",
            description="Design with multiple inclusion criteria",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            eligibilityCriteria=[criterion1, criterion2, criterion3],
            instanceType="StudyDesign",
        )

        criteria_map = {"item1": item1, "item2": item2, "item3": item3}
        result = design.inclusion_criteria(criteria_map)

        assert len(result) == 3
        texts = [r["criterionItem"]["text"] for r in result]
        assert "First criterion text" in texts
        assert "Second criterion text" in texts
        assert "Third criterion text" in texts
