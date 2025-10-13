from datetime import date
from src.usdm4.api.study_version import StudyVersion
from src.usdm4.api.code import Code
from src.usdm4.api.study_title import StudyTitle
from src.usdm4.api.organization import Organization
from src.usdm4.api.identifier import StudyIdentifier
from src.usdm4.api.governance_date import GovernanceDate
from src.usdm4.api.study_design import (
    InterventionalStudyDesign,
    ObservationalStudyDesign,
)
from src.usdm4.api.eligibility_criterion import EligibilityCriterionItem
from src.usdm4.api.study_intervention import StudyIntervention
from src.usdm4.api.narrative_content import NarrativeContentItem
from src.usdm4.api.address import Address
from src.usdm4.api.population_definition import StudyDesignPopulation


class TestStudyVersion:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create test codes
        self.official_title_code = Code(
            id="title_code_1",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Official Study Title",
            instanceType="Code",
        )

        self.short_title_code = Code(
            id="title_code_2",
            code="C99998",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Brief Study Title",
            instanceType="Code",
        )

        self.acronym_code = Code(
            id="title_code_3",
            code="C99997",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Study Acronym",
            instanceType="Code",
        )

        self.sponsor_code = Code(
            id="sponsor_code",
            code="C54149",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Pharmaceutical Company",
            instanceType="Code",
        )

        self.non_sponsor_code = Code(
            id="non_sponsor_code",
            code="C12345",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Other Organization",
            instanceType="Code",
        )

        self.protocol_date_code = Code(
            id="protocol_date_code",
            code="C99996",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Protocol Effective Date",
            instanceType="Code",
        )

        self.approval_date_code = Code(
            id="approval_date_code",
            code="C99995",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Protocol Approval by Sponsor Date",
            instanceType="Code",
        )

        self.country_code = Code(
            id="country_code",
            code="US",
            codeSystem="ISO",
            codeSystemVersion="1.0",
            decode="United States",
            instanceType="Code",
        )

        # Create test address
        self.test_address = Address(
            id="address_1",
            lines=["123 Main St"],
            city="New York",
            district="Manhattan",
            state="NY",
            postalCode="10001",
            country=self.country_code,
            instanceType="Address",
        )
        self.test_address.set_text()

        # Create test organizations
        self.sponsor_org = Organization(
            id="org_1",
            name="Test Sponsor",
            label="Test Sponsor Label",
            type=self.sponsor_code,
            identifierScheme="scheme1",
            identifier="id1",
            legalAddress=self.test_address,
            instanceType="Organization",
        )

        self.non_sponsor_org = Organization(
            id="org_2",
            name="ClinicalTrials.gov",
            label="ClinicalTrials.gov",
            type=self.non_sponsor_code,
            identifierScheme="scheme2",
            identifier="id2",
            instanceType="Organization",
        )

        # Create test titles
        self.official_title = StudyTitle(
            id="title_1",
            text="Official Study Title Text",
            type=self.official_title_code,
            instanceType="StudyTitle",
        )

        self.short_title = StudyTitle(
            id="title_2",
            text="Short Title Text",
            type=self.short_title_code,
            instanceType="StudyTitle",
        )

        self.acronym_title = StudyTitle(
            id="title_3",
            text="ACRONYM",
            type=self.acronym_code,
            instanceType="StudyTitle",
        )

        # Create test identifiers
        self.sponsor_identifier = StudyIdentifier(
            id="id_1",
            text="SPONSOR-123",
            scopeId="org_1",
            instanceType="StudyIdentifier",
        )

        self.nct_identifier = StudyIdentifier(
            id="id_2",
            text="NCT12345678",
            scopeId="org_2",
            instanceType="StudyIdentifier",
        )

        # Create test dates
        self.protocol_date = GovernanceDate(
            id="date_1",
            name="Protocol Date",
            label="Protocol Date",
            description="Protocol effective date",
            type=self.protocol_date_code,
            dateValue=date(2024, 1, 15),
            geographicScopes=[],
            instanceType="GovernanceDate",
        )

        self.approval_date = GovernanceDate(
            id="date_2",
            name="Approval Date",
            label="Approval Date",
            description="Protocol approval date",
            type=self.approval_date_code,
            dateValue=date(2024, 1, 10),
            geographicScopes=[],
            instanceType="GovernanceDate",
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

        # Create test study designs
        self.phase_code = Code(
            id="phase_code",
            code="C15600",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Phase I",
            instanceType="Code",
        )

        self.interventional_design = InterventionalStudyDesign(
            id="design_1",
            name="Interventional Design",
            label="Interventional Design",
            description="Test interventional design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            model=self.phase_code,
            instanceType="InterventionalStudyDesign",
        )

        self.observational_design = ObservationalStudyDesign(
            id="design_2",
            name="Observational Design",
            label="Observational Design",
            description="Test observational design",
            arms=[],
            studyCells=[],
            rationale="Test rationale",
            epochs=[],
            population=self.test_population,
            model=self.phase_code,
            timePerspective=self.phase_code,
            instanceType="ObservationalStudyDesign",
        )

        # Create test eligibility criterion item
        self.criterion_item = EligibilityCriterionItem(
            id="criterion_1",
            name="Test Criterion",
            label="Test Criterion Label",
            description="Test criterion description",
            text="Test criterion text",
            instanceType="EligibilityCriterionItem",
        )

        # Create test study intervention
        self.study_intervention = StudyIntervention(
            id="intervention_1",
            name="Test Intervention",
            label="Test Intervention Label",
            description="Test intervention description",
            role=self.sponsor_code,
            type=self.non_sponsor_code,
            instanceType="StudyIntervention",
        )

        # Create test narrative content item
        self.narrative_item = NarrativeContentItem(
            id="narrative_1",
            name="Test Narrative",
            text="Test narrative content",
            instanceType="NarrativeContentItem",
        )

        # Create main study version for testing
        self.study_version = StudyVersion(
            id="study_version_1",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier, self.nct_identifier],
            titles=[self.official_title, self.short_title, self.acronym_title],
            organizations=[self.sponsor_org, self.non_sponsor_org],
            dateValues=[self.protocol_date, self.approval_date],
            studyDesigns=[self.interventional_design, self.observational_design],
            eligibilityCriterionItems=[self.criterion_item],
            studyInterventions=[self.study_intervention],
            narrativeContentItems=[self.narrative_item],
            instanceType="StudyVersion",
        )

    def test_get_title_official(self):
        """Test getting official title."""
        title = self.study_version.get_title("Official Study Title")
        assert title is not None
        assert title.text == "Official Study Title Text"

    def test_get_title_short(self):
        """Test getting short title."""
        title = self.study_version.get_title("Brief Study Title")
        assert title is not None
        assert title.text == "Short Title Text"

    def test_get_title_not_found(self):
        """Test getting title that doesn't exist."""
        title = self.study_version.get_title("Non-existent Title")
        assert title is None

    def test_sponsor_identifier(self):
        """Test getting sponsor identifier."""
        identifier = self.study_version.sponsor_identifier()
        assert identifier is not None
        assert identifier.text == "SPONSOR-123"

    def test_sponsor_identifier_none(self):
        """Test sponsor identifier when no sponsor exists."""
        # Create study version without sponsor
        study_version = StudyVersion(
            id="study_version_2",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.nct_identifier],
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],
            instanceType="StudyVersion",
        )
        identifier = study_version.sponsor_identifier()
        assert identifier is None

    def test_organization(self):
        """Test getting organization by ID."""
        org = self.study_version.organization("org_1")
        assert org is not None
        assert org.name == "Test Sponsor"

    def test_organization_not_found(self):
        """Test getting organization that doesn't exist."""
        org = self.study_version.organization("non_existent")
        assert org is None

    def test_criterion_item(self):
        """Test getting criterion item by ID."""
        item = self.study_version.criterion_item("criterion_1")
        assert item is not None
        assert item.id == "criterion_1"

    def test_criterion_item_not_found(self):
        """Test getting criterion item that doesn't exist."""
        item = self.study_version.criterion_item("non_existent")
        assert item is None

    def test_intervention(self):
        """Test getting intervention by ID."""
        intervention = self.study_version.intervention("intervention_1")
        assert intervention is not None
        assert intervention.id == "intervention_1"

    def test_intervention_not_found(self):
        """Test getting intervention that doesn't exist."""
        intervention = self.study_version.intervention("non_existent")
        assert intervention is None

    def test_phases(self):
        """Test getting phases as text."""
        phases = self.study_version.phases()
        # Since we don't have studyPhase set, it should return empty strings
        assert phases == ", "

    def test_phases_empty(self):
        """Test getting phases when no study designs exist."""
        study_version = StudyVersion(
            id="study_version_3",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        phases = study_version.phases()
        assert phases == ""

    def test_official_title_text(self):
        """Test getting official title text."""
        text = self.study_version.official_title_text()
        assert text == "Official Study Title Text"

    def test_official_title_text_empty(self):
        """Test getting official title text when none exists."""
        study_version = StudyVersion(
            id="study_version_4",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.short_title],  # Only short title, no official
            instanceType="StudyVersion",
        )
        text = study_version.official_title_text()
        assert text == ""

    def test_short_title_text(self):
        """Test getting short title text."""
        text = self.study_version.short_title_text()
        assert text == "Short Title Text"

    def test_short_title_text_empty(self):
        """Test getting short title text when none exists."""
        study_version = StudyVersion(
            id="study_version_5",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],  # Only official title, no short
            instanceType="StudyVersion",
        )
        text = study_version.short_title_text()
        assert text == ""

    def test_acronym_text(self):
        """Test getting acronym text."""
        text = self.study_version.acronym_text()
        assert text == "ACRONYM"

    def test_acronym_text_empty(self):
        """Test getting acronym text when none exists."""
        study_version = StudyVersion(
            id="study_version_6",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],  # Only official title, no acronym
            instanceType="StudyVersion",
        )
        text = study_version.acronym_text()
        assert text == ""

    def test_official_title(self):
        """Test getting official title object."""
        title = self.study_version.official_title()
        assert title is not None
        assert title.text == "Official Study Title Text"

    def test_official_title_none(self):
        """Test getting official title object when none exists."""
        study_version = StudyVersion(
            id="study_version_7",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.short_title],  # Only short title, no official
            instanceType="StudyVersion",
        )
        title = study_version.official_title()
        assert title is None

    def test_short_title(self):
        """Test getting short title object."""
        title = self.study_version.short_title()
        assert title is not None
        assert title.text == "Short Title Text"

    def test_short_title_none(self):
        """Test getting short title object when none exists."""
        study_version = StudyVersion(
            id="study_version_8",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],  # Only official title, no short
            instanceType="StudyVersion",
        )
        title = study_version.short_title()
        assert title is None

    def test_acronym(self):
        """Test getting acronym object."""
        title = self.study_version.acronym()
        assert title is not None
        assert title.text == "ACRONYM"

    def test_acronym_none(self):
        """Test getting acronym object when none exists."""
        study_version = StudyVersion(
            id="study_version_9",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],  # Only official title, no acronym
            instanceType="StudyVersion",
        )
        title = study_version.acronym()
        assert title is None

    def test_sponsor(self):
        """Test getting sponsor organization."""
        sponsor = self.study_version.sponsor()
        assert sponsor is not None
        assert sponsor.name == "Test Sponsor"

    def test_sponsor_none(self):
        """Test getting sponsor when none exists."""
        study_version = StudyVersion(
            id="study_version_10",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.nct_identifier],  # Only NCT identifier
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],  # Only non-sponsor org
            instanceType="StudyVersion",
        )
        sponsor = study_version.sponsor()
        assert sponsor is None

    def test_sponsor_identifier_text(self):
        """Test getting sponsor identifier text."""
        text = self.study_version.sponsor_identifier_text()
        assert text == "SPONSOR-123"

    def test_sponsor_identifier_text_empty(self):
        """Test getting sponsor identifier text when none exists."""
        study_version = StudyVersion(
            id="study_version_11",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.nct_identifier],  # Only NCT identifier
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],  # Only non-sponsor org
            instanceType="StudyVersion",
        )
        text = study_version.sponsor_identifier_text()
        assert text == ""

    def test_sponsor_name(self):
        """Test getting sponsor name."""
        name = self.study_version.sponsor_name()
        assert name == "Test Sponsor"

    def test_sponsor_name_empty(self):
        """Test getting sponsor name when none exists."""
        study_version = StudyVersion(
            id="study_version_12",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.nct_identifier],  # Only NCT identifier
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],  # Only non-sponsor org
            instanceType="StudyVersion",
        )
        name = study_version.sponsor_name()
        assert name == ""

    def test_sponsor_address(self):
        """Test getting sponsor address."""
        address = self.study_version.sponsor_address()
        assert "123 Main St" in address

    def test_sponsor_address_empty(self):
        """Test getting sponsor address when none exists."""
        study_version = StudyVersion(
            id="study_version_13",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.nct_identifier],  # Only NCT identifier
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],  # Only non-sponsor org
            instanceType="StudyVersion",
        )
        address = study_version.sponsor_address()
        assert address == ""

    def test_nct_identifier(self):
        """Test getting NCT identifier."""
        nct = self.study_version.nct_identifier()
        assert nct == "NCT12345678"

    def test_nct_identifier_empty(self):
        """Test getting NCT identifier when none exists."""
        study_version = StudyVersion(
            id="study_version_14",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],  # Only sponsor identifier
            titles=[self.official_title],
            organizations=[self.sponsor_org],  # Only sponsor org
            instanceType="StudyVersion",
        )
        nct = study_version.nct_identifier()
        assert nct == ""

    def test_protocol_date(self):
        """Test getting protocol date."""
        date_obj = self.study_version.protocol_date()
        assert date_obj is not None
        assert date_obj.dateValue == date(2024, 1, 15)

    def test_protocol_date_empty(self):
        """Test getting protocol date when none exists."""
        study_version = StudyVersion(
            id="study_version_15",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[self.approval_date],  # Only approval date
            instanceType="StudyVersion",
        )
        date_obj = study_version.protocol_date()
        assert date_obj == ""

    def test_approval_date(self):
        """Test getting approval date."""
        date_obj = self.study_version.approval_date()
        assert date_obj is not None
        assert date_obj.dateValue == date(2024, 1, 10)

    def test_approval_date_empty(self):
        """Test getting approval date when none exists."""
        study_version = StudyVersion(
            id="study_version_16",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[self.protocol_date],  # Only protocol date
            instanceType="StudyVersion",
        )
        date_obj = study_version.approval_date()
        assert date_obj == ""

    def test_protocol_date_value(self):
        """Test getting protocol date value."""
        date_value = self.study_version.protocol_date_value()
        assert date_value == date(2024, 1, 15)

    def test_protocol_date_value_empty(self):
        """Test getting protocol date value when none exists."""
        study_version = StudyVersion(
            id="study_version_17",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[self.approval_date],  # Only approval date
            instanceType="StudyVersion",
        )
        date_value = study_version.protocol_date_value()
        assert date_value == ""

    def test_approval_date_value(self):
        """Test getting approval date value."""
        date_value = self.study_version.approval_date_value()
        assert date_value == date(2024, 1, 10)

    def test_approval_date_value_empty(self):
        """Test getting approval date value when none exists."""
        study_version = StudyVersion(
            id="study_version_18",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[self.protocol_date],  # Only protocol date
            instanceType="StudyVersion",
        )
        date_value = study_version.approval_date_value()
        assert date_value == ""

    def test_organization_map(self):
        """Test getting organization map."""
        org_map = self.study_version.organization_map()
        assert isinstance(org_map, dict)
        assert "org_1" in org_map
        assert "org_2" in org_map
        assert org_map["org_1"].name == "Test Sponsor"
        assert org_map["org_2"].name == "ClinicalTrials.gov"

    def test_find_study_design(self):
        """Test finding study design by ID."""
        design = self.study_version.find_study_design("design_1")
        assert design is not None
        assert design.id == "design_1"

    def test_find_study_design_not_found(self):
        """Test finding study design that doesn't exist."""
        design = self.study_version.find_study_design("non_existent")
        assert design is None

    def test_narrative_content_item_map(self):
        """Test getting narrative content item map."""
        item_map = self.study_version.narrative_content_item_map()
        assert isinstance(item_map, dict)
        assert "narrative_1" in item_map
        assert item_map["narrative_1"].id == "narrative_1"

    def test_empty_lists_initialization(self):
        """Test that empty lists are properly initialized."""
        study_version = StudyVersion(
            id="study_version_19",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )

        # Test that default empty lists are properly initialized
        assert study_version.documentVersionIds == []
        assert study_version.dateValues == []
        assert study_version.amendments == []
        assert study_version.businessTherapeuticAreas == []
        assert study_version.referenceIdentifiers == []
        assert study_version.studyDesigns == []
        assert study_version.eligibilityCriterionItems == []
        assert study_version.narrativeContentItems == []
        assert study_version.abbreviations == []
        assert study_version.roles == []
        assert study_version.organizations == []
        assert study_version.studyInterventions == []
        assert study_version.administrableProducts == []
        assert study_version.medicalDevices == []
        assert study_version.productOrganizationRoles == []
        assert study_version.biomedicalConcepts == []
        assert study_version.bcCategories == []
        assert study_version.bcSurrogates == []
        assert study_version.dictionaries == []
        assert study_version.conditions == []
        assert study_version.notes == []

    def test_instance_type(self):
        """Test that instance type is correctly set."""
        assert self.study_version.instanceType == "StudyVersion"

    def test_regulatory_identifiers_with_regulatory_org(self):
        """Test regulatory_identifiers returns correct identifiers."""
        # Create regulatory organization code
        regulatory_code = Code(
            id="regulatory_code",
            code="C188863",  # Regulatory Authority code
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Regulatory Authority",
            instanceType="Code",
        )
        
        regulatory_org = Organization(
            id="org_regulatory",
            name="FDA",
            label="FDA",
            type=regulatory_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        
        regulatory_id = StudyIdentifier(
            id="id_regulatory",
            text="IND-123456",
            scopeId="org_regulatory",
            instanceType="StudyIdentifier",
        )
        
        study_version = StudyVersion(
            id="sv1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier, regulatory_id],
            titles=[self.official_title],
            organizations=[self.sponsor_org, regulatory_org],
            instanceType="StudyVersion",
        )
        
        regulatory_ids = study_version.regulatory_identifiers()
        assert len(regulatory_ids) == 1
        assert regulatory_ids[0].text == "IND-123456"

    def test_regulatory_identifiers_empty(self):
        """Test regulatory_identifiers returns empty list when none exist."""
        regulatory_ids = self.study_version.regulatory_identifiers()
        assert len(regulatory_ids) == 0

    def test_registry_identifiers_with_registry_org(self):
        """Test registry_identifiers returns correct identifiers."""
        # Create registry organization code
        registry_code = Code(
            id="registry_code",
            code="C93453",  # Clinical Trial Registry code
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Clinical Trial Registry",
            instanceType="Code",
        )
        
        registry_org = Organization(
            id="org_registry",
            name="ClinicalTrials.gov",
            label="CT.gov",
            type=registry_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        
        registry_id = StudyIdentifier(
            id="id_registry",
            text="NCT12345678",
            scopeId="org_registry",
            instanceType="StudyIdentifier",
        )
        
        study_version = StudyVersion(
            id="sv2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier, registry_id],
            titles=[self.official_title],
            organizations=[self.sponsor_org, registry_org],
            instanceType="StudyVersion",
        )
        
        registry_ids = study_version.registry_identifiers()
        assert len(registry_ids) == 1
        assert registry_ids[0].text == "NCT12345678"

    def test_registry_identifiers_empty(self):
        """Test registry_identifiers returns empty list when none exist."""
        registry_ids = self.study_version.registry_identifiers()
        assert len(registry_ids) == 0

    def test_condition_method_found(self):
        """Test condition method returns correct condition."""
        from src.usdm4.api.condition import Condition
        
        condition = Condition(
            id="cond1",
            name="Test Condition",
            label="Test Label",
            description="Test Description",
            text="Condition text",
            instanceType="Condition",
        )
        
        study_version = StudyVersion(
            id="sv3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            conditions=[condition],
            instanceType="StudyVersion",
        )
        
        found = study_version.condition("cond1")
        assert found is not None
        assert found.id == "cond1"
        assert found.text == "Condition text"

    def test_condition_method_not_found(self):
        """Test condition method returns None when not found."""
        found = self.study_version.condition("nonexistent")
        assert found is None

    def test_sponsor_label_with_label(self):
        """Test sponsor_label returns label when it exists."""
        label = self.study_version.sponsor_label()
        assert label == "Test Sponsor Label"

    def test_sponsor_label_empty_when_no_sponsor(self):
        """Test sponsor_label returns empty string when no sponsor."""
        # Create study version without sponsor
        study_version = StudyVersion(
            id="sv4",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.nct_identifier],
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],
            instanceType="StudyVersion",
        )
        
        label = study_version.sponsor_label()
        assert label == ""

    def test_sponsor_label_name_returns_label(self):
        """Test sponsor_label_name returns label when it exists."""
        label_name = self.study_version.sponsor_label_name()
        assert label_name == "Test Sponsor Label"

    def test_sponsor_label_name_fallback_to_name(self):
        """Test sponsor_label_name falls back to name when label is empty."""
        # Create organization with empty label
        org_no_label = Organization(
            id="org_no_label",
            name="Sponsor Company",
            label="",
            type=self.sponsor_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        
        sponsor_id = StudyIdentifier(
            id="id_no_label",
            text="SPONSOR-001",
            scopeId="org_no_label",
            instanceType="StudyIdentifier",
        )
        
        study_version = StudyVersion(
            id="sv5",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            organizations=[org_no_label],
            instanceType="StudyVersion",
        )
        
        label_name = study_version.sponsor_label_name()
        assert label_name == "Sponsor Company"
