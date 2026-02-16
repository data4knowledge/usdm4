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
from src.usdm4.api.extension import ExtensionAttribute, BaseCode
from src.usdm4.api.study_definition_document import StudyDefinitionDocument
from src.usdm4.api.study_definition_document_version import (
    StudyDefinitionDocumentVersion,
)
from src.usdm4.api.study_amendment import StudyAmendment
from src.usdm4.api.study_amendment_reason import StudyAmendmentReason
from src.usdm4.api.geographic_scope import GeographicScope
from src.usdm4.api.study_role import StudyRole


class TestStudyVersion:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create test codes
        self.official_title_code = Code(
            id="title_code_1",
            code="C207616",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Official Study Title",
            instanceType="Code",
        )

        self.short_title_code = Code(
            id="title_code_2",
            code="C207615",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Brief Study Title",
            instanceType="Code",
        )

        self.acronym_code = Code(
            id="title_code_3",
            code="C207646",
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
            code="C71476",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Approval Date",
            instanceType="Code",
        )

        self.approval_date_code = Code(
            id="approval_date_code",
            code="C71476",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Approval Date",
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
            name="CT.GOV",
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

    def test_sponsor_organization_via_fallback(self):
        """Test getting sponsor organization via fallback (organization type code C54149)."""
        # The main study_version fixture uses the fallback path (org type C54149)
        org = self.study_version.sponsor_organization()
        assert org is not None
        assert org.name == "Test Sponsor"
        assert org.id == "org_1"

    def test_sponsor_organization_via_role(self):
        """Test getting sponsor organization via role with code C70793."""
        # Create sponsor role code
        sponsor_role_code = Code(
            id="sponsor_role_code",
            code="C70793",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Sponsor",
            instanceType="Code",
        )

        # Create a sponsor role linking to the sponsor organization
        sponsor_role = StudyRole(
            id="role_sponsor",
            name="Sponsor Role",
            label="Sponsor Role",
            description="Sponsor role description",
            code=sponsor_role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        # Create study version with sponsor role
        study_version = StudyVersion(
            id="study_version_role",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier, self.nct_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org, self.non_sponsor_org],
            roles=[sponsor_role],
            instanceType="StudyVersion",
        )

        org = study_version.sponsor_organization()
        assert org is not None
        assert org.name == "Test Sponsor"
        assert org.id == "org_1"

    def test_sponsor_organization_none(self):
        """Test sponsor organization returns None when no sponsor exists."""
        study_version = StudyVersion(
            id="study_version_no_sponsor",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.nct_identifier],
            titles=[self.official_title],
            organizations=[self.non_sponsor_org],
            instanceType="StudyVersion",
        )
        org = study_version.sponsor_organization()
        assert org is None

    def test_sponsor_identifier_via_role(self):
        """Test getting sponsor identifier when sponsor is found via role."""
        # Create sponsor role code
        sponsor_role_code = Code(
            id="sponsor_role_code_2",
            code="C70793",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Sponsor",
            instanceType="Code",
        )

        # Create a sponsor role linking to the sponsor organization
        sponsor_role = StudyRole(
            id="role_sponsor_2",
            name="Sponsor Role",
            label="Sponsor Role",
            description="Sponsor role description",
            code=sponsor_role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        # Create study version with sponsor role
        study_version = StudyVersion(
            id="study_version_role_2",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier, self.nct_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org, self.non_sponsor_org],
            roles=[sponsor_role],
            instanceType="StudyVersion",
        )

        identifier = study_version.sponsor_identifier()
        assert identifier is not None
        assert identifier.text == "SPONSOR-123"

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

    def test_protocol_date(self):
        """Test getting protocol date."""
        date_obj = self.study_version.protocol_date()
        assert date_obj is not None
        assert date_obj.dateValue == date(2024, 1, 15)

    def test_protocol_date_empty(self):
        """Test getting protocol date when none exists."""
        # Create a date with a different code that won't match C71476
        other_date_code = Code(
            id="other_date_code",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Other Date Type",
            instanceType="Code",
        )
        other_date = GovernanceDate(
            id="other_date",
            name="Other Date",
            label="Other Date",
            description="Some other date",
            type=other_date_code,
            dateValue=date(2024, 1, 10),
            geographicScopes=[],
            instanceType="GovernanceDate",
        )
        study_version = StudyVersion(
            id="study_version_15",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[other_date],  # Only a non-matching date
            instanceType="StudyVersion",
        )
        date_obj = study_version.protocol_date()
        assert date_obj == ""

    def test_approval_date(self):
        """Test getting approval date."""
        # Note: Both protocol_date() and approval_date() methods use the same code C71476
        # so they return the first matching date in the dateValues list
        date_obj = self.study_version.approval_date()
        assert date_obj is not None
        assert date_obj.dateValue == date(2024, 1, 15)

    def test_approval_date_empty(self):
        """Test getting approval date when none exists."""
        # Create a date with a different code that won't match C71476
        other_date_code = Code(
            id="other_date_code",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Other Date Type",
            instanceType="Code",
        )
        other_date = GovernanceDate(
            id="other_date",
            name="Other Date",
            label="Other Date",
            description="Some other date",
            type=other_date_code,
            dateValue=date(2024, 1, 10),
            geographicScopes=[],
            instanceType="GovernanceDate",
        )
        study_version = StudyVersion(
            id="study_version_16",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[other_date],  # Only a non-matching date
            instanceType="StudyVersion",
        )
        date_obj = study_version.approval_date()
        assert date_obj is None

    def test_protocol_date_value(self):
        """Test getting protocol date value."""
        date_value = self.study_version.protocol_date_value()
        assert date_value == date(2024, 1, 15)

    def test_protocol_date_value_empty(self):
        """Test getting protocol date value when none exists."""
        # Create a date with a different code that won't match C71476
        other_date_code = Code(
            id="other_date_code",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Other Date Type",
            instanceType="Code",
        )
        other_date = GovernanceDate(
            id="other_date",
            name="Other Date",
            label="Other Date",
            description="Some other date",
            type=other_date_code,
            dateValue=date(2024, 1, 10),
            geographicScopes=[],
            instanceType="GovernanceDate",
        )
        study_version = StudyVersion(
            id="study_version_17",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[other_date],  # Only a non-matching date
            instanceType="StudyVersion",
        )
        date_value = study_version.protocol_date_value()
        assert date_value == ""

    def test_approval_date_value(self):
        """Test getting approval date value."""
        # Note: Both protocol_date_value() and approval_date_value() methods use the same code C71476
        # so they return the first matching date in the dateValues list
        date_value = self.study_version.approval_date_value()
        assert date_value == date(2024, 1, 15)

    def test_approval_date_value_empty(self):
        """Test getting approval date value when none exists."""
        # Create a date with a different code that won't match C71476
        other_date_code = Code(
            id="other_date_code",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Other Date Type",
            instanceType="Code",
        )
        other_date = GovernanceDate(
            id="other_date",
            name="Other Date",
            label="Other Date",
            description="Some other date",
            type=other_date_code,
            dateValue=date(2024, 1, 10),
            geographicScopes=[],
            instanceType="GovernanceDate",
        )
        study_version = StudyVersion(
            id="study_version_18",
            versionIdentifier="v1.0",
            rationale="Test study version",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[other_date],  # Only a non-matching date
            instanceType="StudyVersion",
        )
        date_value = study_version.approval_date_value()
        assert date_value is None

    def test_organization_map(self):
        """Test getting organization map."""
        org_map = self.study_version.organization_map()
        assert isinstance(org_map, dict)
        assert "org_1" in org_map
        assert "org_2" in org_map
        assert org_map["org_1"].name == "Test Sponsor"
        assert org_map["org_2"].name == "CT.GOV"

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

    def test_confidentiality_statement_with_extension(self):
        """Test confidentiality_statement returns the value when extension exists."""
        # Create extension with confidentiality statement
        cs_extension = ExtensionAttribute(
            id="ext_cs",
            url="www.d4k.dk/usdm/extensions/001",
            valueString="This is a confidential study protocol.",
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_cs1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[cs_extension],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement == "This is a confidential study protocol."

    def test_confidentiality_statement_no_extension(self):
        """Test confidentiality_statement returns empty string when no extension exists."""
        study_version = StudyVersion(
            id="sv_cs2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement == ""

    # =====================================================
    # Tests for documents method
    # =====================================================

    def _create_document_version(
        self, version_id: str, version_number: str = "1.0"
    ) -> StudyDefinitionDocumentVersion:
        """Helper method to create a StudyDefinitionDocumentVersion."""
        status_code = Code(
            id="status1",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code",
        )

        return StudyDefinitionDocumentVersion(
            id=version_id,
            version=version_number,
            status=status_code,
            instanceType="StudyDefinitionDocumentVersion",
        )

    def _create_document_with_versions(
        self, doc_id: str, template_name: str, versions: list
    ) -> StudyDefinitionDocument:
        """Helper method to create a StudyDefinitionDocument with versions."""
        doc_language = Code(
            id="lang1",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )

        doc_type = Code(
            id=f"doc_type_{doc_id}",
            code=template_name,
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode=f"{template_name} Document",
            instanceType="Code",
        )

        return StudyDefinitionDocument(
            id=doc_id,
            name=f"{template_name} Document",
            label=f"{template_name} v1.0",
            templateName=template_name,
            language=doc_language,
            type=doc_type,
            versions=versions,
            instanceType="StudyDefinitionDocument",
        )

    def _create_document_map(self, docs_with_versions: list) -> dict:
        """Helper to create a document_map similar to Study.document_map()."""
        result = {}
        for doc, versions in docs_with_versions:
            for version in versions:
                result[version.id] = {"document": doc, "version": version}
        return result

    def test_documents_empty_document_version_ids(self):
        """Test documents() with empty documentVersionIds."""
        study_version = StudyVersion(
            id="sv_docs1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=[],
            instanceType="StudyVersion",
        )

        document_map = {}
        result = study_version.documents(document_map)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_documents_single_document_version(self):
        """Test documents() with a single documentVersionId."""
        version1 = self._create_document_version("version1", "1.0")
        doc1 = self._create_document_with_versions("doc1", "PROTOCOL", [version1])
        document_map = self._create_document_map([(doc1, [version1])])

        study_version = StudyVersion(
            id="sv_docs2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["version1"],
            instanceType="StudyVersion",
        )

        result = study_version.documents(document_map)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "document" in result[0]
        assert "version" in result[0]
        assert result[0]["document"] == doc1
        assert result[0]["version"] == version1

    def test_documents_multiple_document_versions(self):
        """Test documents() with multiple documentVersionIds."""
        version1 = self._create_document_version("version1", "1.0")
        version2 = self._create_document_version("version2", "2.0")
        version3 = self._create_document_version("version3", "1.0")

        doc1 = self._create_document_with_versions(
            "doc1", "PROTOCOL", [version1, version2]
        )
        doc2 = self._create_document_with_versions("doc2", "CSR", [version3])

        document_map = self._create_document_map(
            [(doc1, [version1, version2]), (doc2, [version3])]
        )

        study_version = StudyVersion(
            id="sv_docs3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["version1", "version2", "version3"],
            instanceType="StudyVersion",
        )

        result = study_version.documents(document_map)

        assert isinstance(result, list)
        assert len(result) == 3

        # First entry
        assert result[0]["document"] == doc1
        assert result[0]["version"] == version1

        # Second entry
        assert result[1]["document"] == doc1
        assert result[1]["version"] == version2

        # Third entry
        assert result[2]["document"] == doc2
        assert result[2]["version"] == version3

    def test_documents_preserves_order(self):
        """Test documents() preserves the order of documentVersionIds."""
        version1 = self._create_document_version("version1", "1.0")
        version2 = self._create_document_version("version2", "2.0")
        version3 = self._create_document_version("version3", "3.0")

        doc1 = self._create_document_with_versions(
            "doc1", "PROTOCOL", [version1, version2, version3]
        )
        document_map = self._create_document_map(
            [(doc1, [version1, version2, version3])]
        )

        # Specify different order
        study_version = StudyVersion(
            id="sv_docs4",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["version3", "version1", "version2"],
            instanceType="StudyVersion",
        )

        result = study_version.documents(document_map)

        assert len(result) == 3
        assert result[0]["version"].id == "version3"
        assert result[1]["version"].id == "version1"
        assert result[2]["version"].id == "version2"

    def test_documents_returns_dict_with_correct_keys(self):
        """Test documents() returns list of dicts with 'document' and 'version' keys."""
        version1 = self._create_document_version("version1", "1.0")
        doc1 = self._create_document_with_versions("doc1", "PROTOCOL", [version1])
        document_map = self._create_document_map([(doc1, [version1])])

        study_version = StudyVersion(
            id="sv_docs5",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["version1"],
            instanceType="StudyVersion",
        )

        result = study_version.documents(document_map)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert set(result[0].keys()) == {"document", "version"}
        assert isinstance(result[0]["document"], StudyDefinitionDocument)
        assert isinstance(result[0]["version"], StudyDefinitionDocumentVersion)

    def test_documents_subset_of_map(self):
        """Test documents() returns only documents matching documentVersionIds."""
        version1 = self._create_document_version("version1", "1.0")
        version2 = self._create_document_version("version2", "2.0")
        version3 = self._create_document_version("version3", "3.0")

        doc1 = self._create_document_with_versions("doc1", "PROTOCOL", [version1])
        doc2 = self._create_document_with_versions("doc2", "CSR", [version2])
        doc3 = self._create_document_with_versions("doc3", "SAP", [version3])

        # Full document_map with all versions
        document_map = self._create_document_map(
            [(doc1, [version1]), (doc2, [version2]), (doc3, [version3])]
        )

        # But study_version only references some of them
        study_version = StudyVersion(
            id="sv_docs6",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["version1", "version3"],  # Only version1 and version3
            instanceType="StudyVersion",
        )

        result = study_version.documents(document_map)

        assert len(result) == 2
        assert result[0]["version"].id == "version1"
        assert result[1]["version"].id == "version3"

    def test_confidentiality_statement_wrong_url(self):
        """Test confidentiality_statement returns empty string when extension has wrong URL."""
        # Create extension with different URL
        other_extension = ExtensionAttribute(
            id="ext_other",
            url="www.example.com/different/url",
            valueString="Some other value",
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_cs3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[other_extension],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement == ""

    def test_confidentiality_statement_null_value(self):
        """Test confidentiality_statement returns None when valueString is None."""
        # Create extension with None valueString
        cs_extension = ExtensionAttribute(
            id="ext_cs_null",
            url="www.d4k.dk/usdm/extensions/001",
            valueString=None,
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_cs4",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[cs_extension],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement is None

    def test_confidentiality_statement_case_insensitive_url(self):
        """Test confidentiality_statement matches URL case-insensitively."""
        # Create extension with uppercase URL
        cs_extension = ExtensionAttribute(
            id="ext_cs_upper",
            url="WWW.D4K.DK/USDM/EXTENSIONS/001",
            valueString="Confidential statement with uppercase URL",
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_cs5",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[cs_extension],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement == "Confidential statement with uppercase URL"

    def test_confidentiality_statement_multiple_extensions(self):
        """Test confidentiality_statement finds correct extension among multiple."""
        # Create multiple extensions
        other_extension1 = ExtensionAttribute(
            id="ext_other1",
            url="www.example.com/extension/001",
            valueString="Other extension 1",
            instanceType="ExtensionAttribute",
        )

        cs_extension = ExtensionAttribute(
            id="ext_cs_multiple",
            url="www.d4k.dk/usdm/extensions/001",
            valueString="The confidentiality statement",
            instanceType="ExtensionAttribute",
        )

        other_extension2 = ExtensionAttribute(
            id="ext_other2",
            url="www.example.com/extension/002",
            valueString="Other extension 2",
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_cs6",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[other_extension1, cs_extension, other_extension2],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement == "The confidentiality statement"

    def test_confidentiality_statement_empty_string(self):
        """Test confidentiality_statement returns empty string when valueString is empty."""
        # Create extension with empty string valueString
        cs_extension = ExtensionAttribute(
            id="ext_cs_empty",
            url="www.d4k.dk/usdm/extensions/001",
            valueString="",
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_cs7",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[cs_extension],
            instanceType="StudyVersion",
        )

        statement = study_version.confidentiality_statement()
        assert statement == ""

    # =====================================================
    # Tests for original_version method (lines 73-75)
    # =====================================================

    def test_original_version_true(self):
        """Test original_version returns True when extension exists with True value."""
        ov_extension = ExtensionAttribute(
            id="ext_ov_true",
            url="www.d4k.dk/usdm/extensions/002",
            valueBoolean=True,
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_ov1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[ov_extension],
            instanceType="StudyVersion",
        )

        result = study_version.original_version()
        assert result is True

    def test_original_version_false_with_extension(self):
        """Test original_version returns False when extension exists with False value."""
        ov_extension = ExtensionAttribute(
            id="ext_ov_false",
            url="www.d4k.dk/usdm/extensions/002",
            valueBoolean=False,
            instanceType="ExtensionAttribute",
        )

        study_version = StudyVersion(
            id="sv_ov2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[ov_extension],
            instanceType="StudyVersion",
        )

        result = study_version.original_version()
        assert result is False

    def test_original_version_false_no_extension(self):
        """Test original_version returns False when no extension exists."""
        study_version = StudyVersion(
            id="sv_ov3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )

        result = study_version.original_version()
        assert result is False

    # =====================================================
    # Tests for first_amendment method (lines 77-85)
    # =====================================================

    def _create_amendment(
        self, amendment_id: str, previous_id: str = None
    ) -> StudyAmendment:
        """Helper method to create a StudyAmendment."""
        reason_code = Code(
            id=f"reason_code_{amendment_id}",
            code="C12345",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Test Reason",
            instanceType="Code",
        )

        primary_reason = StudyAmendmentReason(
            id=f"reason_{amendment_id}",
            code=reason_code,
            instanceType="StudyAmendmentReason",
        )

        country_code = Code(
            id=f"country_{amendment_id}",
            code="US",
            codeSystem="ISO",
            codeSystemVersion="1.0",
            decode="United States",
            instanceType="Code",
        )

        geo_scope = GeographicScope(
            id=f"geo_{amendment_id}",
            type=country_code,
            instanceType="GeographicScope",
        )

        return StudyAmendment(
            id=amendment_id,
            name=f"Amendment {amendment_id}",
            label=f"Amendment {amendment_id}",
            description=f"Description for {amendment_id}",
            number="1",
            summary="Test amendment summary",
            primaryReason=primary_reason,
            geographicScopes=[geo_scope],
            previousId=previous_id,
            instanceType="StudyAmendment",
        )

    def test_first_amendment_no_amendments(self):
        """Test first_amendment returns None when no amendments exist."""
        study_version = StudyVersion(
            id="sv_fa1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            amendments=[],
            instanceType="StudyVersion",
        )

        result = study_version.first_amendment()
        assert result is None

    def test_first_amendment_single_amendment(self):
        """Test first_amendment returns the only amendment when there's just one."""
        amendment1 = self._create_amendment("amend1", previous_id=None)

        study_version = StudyVersion(
            id="sv_fa2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            amendments=[amendment1],
            instanceType="StudyVersion",
        )

        result = study_version.first_amendment()
        assert result is not None
        assert result.id == "amend1"

    def test_first_amendment_chain_of_amendments(self):
        """Test first_amendment returns the latest amendment in a chain.

        The algorithm finds amendments whose ID is NOT in any other amendment's
        previousId - i.e., the amendment that no other amendment points back to.
        In a chronological chain where each amendment points to its predecessor,
        this identifies the latest/most recent amendment (the head of the list).
        """
        # Create a chain: amend1 <- amend2 <- amend3 (amend3 is latest)
        amendment1 = self._create_amendment("amend1", previous_id=None)
        amendment2 = self._create_amendment("amend2", previous_id="amend1")
        amendment3 = self._create_amendment("amend3", previous_id="amend2")

        study_version = StudyVersion(
            id="sv_fa3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            amendments=[amendment3, amendment1, amendment2],
            instanceType="StudyVersion",
        )

        result = study_version.first_amendment()
        assert result is not None
        # amend3 is the latest - no other amendment references it as previousId
        assert result.id == "amend3"

    def test_first_amendment_multiple_amendments_no_chain(self):
        """Test first_amendment with multiple amendments where none reference others."""
        # Two amendments with no previousId - both would be 'first'
        amendment1 = self._create_amendment("amend1", previous_id=None)
        amendment2 = self._create_amendment("amend2", previous_id=None)

        study_version = StudyVersion(
            id="sv_fa4",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            amendments=[amendment1, amendment2],
            instanceType="StudyVersion",
        )

        result = study_version.first_amendment()
        assert result is not None
        # Should return one of the amendments (the first in the result set)
        assert result.id in ["amend1", "amend2"]

    # =====================================================
    # Tests for ema_identifier method (line 219-220)
    # =====================================================

    def test_ema_identifier_found(self):
        """Test ema_identifier returns identifier when type C218684 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_ema", "SPONSOR-123", "org_1", "C999999"
        )
        ema_id = self._create_identifier_with_type(
            "id_ema", "EudraCT-2024-001234-56", "org_2", "C218684"
        )
        sv = StudyVersion(
            id="sv_ema1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, ema_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.ema_identifier()
        assert result is not None
        assert result.text == "EudraCT-2024-001234-56"

    def test_ema_identifier_not_found(self):
        """Test ema_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_ema2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_ema2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.ema_identifier()
        assert result is None

    # =====================================================
    # Tests for eligibility_critieria_item_map method (line 271-272)
    # =====================================================

    def test_eligibility_critieria_item_map(self):
        """Test eligibility_critieria_item_map returns correct mapping."""
        item_map = self.study_version.eligibility_critieria_item_map()
        assert isinstance(item_map, dict)
        assert "criterion_1" in item_map
        assert item_map["criterion_1"].id == "criterion_1"
        assert item_map["criterion_1"].name == "Test Criterion"

    def test_eligibility_critieria_item_map_empty(self):
        """Test eligibility_critieria_item_map returns empty dict when no items."""
        study_version = StudyVersion(
            id="sv_ecim1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            eligibilityCriterionItems=[],
            instanceType="StudyVersion",
        )

        item_map = study_version.eligibility_critieria_item_map()
        assert isinstance(item_map, dict)
        assert len(item_map) == 0

    def test_eligibility_critieria_item_map_multiple_items(self):
        """Test eligibility_critieria_item_map with multiple items."""
        criterion1 = EligibilityCriterionItem(
            id="crit_1",
            name="Criterion 1",
            label="Criterion 1 Label",
            description="Criterion 1 description",
            text="Criterion 1 text",
            instanceType="EligibilityCriterionItem",
        )

        criterion2 = EligibilityCriterionItem(
            id="crit_2",
            name="Criterion 2",
            label="Criterion 2 Label",
            description="Criterion 2 description",
            text="Criterion 2 text",
            instanceType="EligibilityCriterionItem",
        )

        criterion3 = EligibilityCriterionItem(
            id="crit_3",
            name="Criterion 3",
            label="Criterion 3 Label",
            description="Criterion 3 description",
            text="Criterion 3 text",
            instanceType="EligibilityCriterionItem",
        )

        study_version = StudyVersion(
            id="sv_ecim2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            eligibilityCriterionItems=[criterion1, criterion2, criterion3],
            instanceType="StudyVersion",
        )

        item_map = study_version.eligibility_critieria_item_map()
        assert isinstance(item_map, dict)
        assert len(item_map) == 3
        assert "crit_1" in item_map
        assert "crit_2" in item_map
        assert "crit_3" in item_map
        assert item_map["crit_1"].name == "Criterion 1"
        assert item_map["crit_2"].name == "Criterion 2"
        assert item_map["crit_3"].name == "Criterion 3"

    # =====================================================
    # Tests for co_sponsor_organization method (line 139)
    # =====================================================

    def test_co_sponsor_organization_found(self):
        """Test co_sponsor_organization returns organization when role exists."""
        # Create co-sponsor role code (C215669)
        co_sponsor_role_code = Code(
            id="co_sponsor_role_code",
            code="C215669",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Co-Sponsor",
            instanceType="Code",
        )

        # Create a co-sponsor role linking to an organization
        co_sponsor_role = StudyRole(
            id="role_co_sponsor",
            name="Co-Sponsor Role",
            label="Co-Sponsor Role",
            description="Co-sponsor role description",
            code=co_sponsor_role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_cosponsor1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[co_sponsor_role],
            instanceType="StudyVersion",
        )

        org = study_version.co_sponsor_organization()
        assert org is not None
        assert org.id == "org_1"
        assert org.name == "Test Sponsor"

    def test_co_sponsor_organization_not_found(self):
        """Test co_sponsor_organization returns None when role doesn't exist."""
        study_version = StudyVersion(
            id="sv_cosponsor2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[],
            instanceType="StudyVersion",
        )

        org = study_version.co_sponsor_organization()
        assert org is None

    # =====================================================
    # Tests for local_sponsor_organization method (line 142)
    # =====================================================

    def test_local_sponsor_organization_found(self):
        """Test local_sponsor_organization returns organization when role exists."""
        # Create local sponsor role code (C215670)
        local_sponsor_role_code = Code(
            id="local_sponsor_role_code",
            code="C215670",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Local Sponsor",
            instanceType="Code",
        )

        # Create a local sponsor role linking to an organization
        local_sponsor_role = StudyRole(
            id="role_local_sponsor",
            name="Local Sponsor Role",
            label="Local Sponsor Role",
            description="Local sponsor role description",
            code=local_sponsor_role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_localsponsor1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[local_sponsor_role],
            instanceType="StudyVersion",
        )

        org = study_version.local_sponsor_organization()
        assert org is not None
        assert org.id == "org_1"
        assert org.name == "Test Sponsor"

    def test_local_sponsor_organization_not_found(self):
        """Test local_sponsor_organization returns None when role doesn't exist."""
        study_version = StudyVersion(
            id="sv_localsponsor2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[],
            instanceType="StudyVersion",
        )

        org = study_version.local_sponsor_organization()
        assert org is None

    # =====================================================
    # Tests for manufacturer_organization method (line 145)
    # =====================================================

    def test_manufacturer_organization_found(self):
        """Test manufacturer_organization returns organization when role exists."""
        # Create manufacturer role code (C25392)
        manufacturer_role_code = Code(
            id="manufacturer_role_code",
            code="C25392",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Manufacturer",
            instanceType="Code",
        )

        # Create a manufacturer role linking to an organization
        manufacturer_role = StudyRole(
            id="role_manufacturer",
            name="Manufacturer Role",
            label="Manufacturer Role",
            description="Manufacturer role description",
            code=manufacturer_role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_manufacturer1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[manufacturer_role],
            instanceType="StudyVersion",
        )

        org = study_version.manufacturer_organization()
        assert org is not None
        assert org.id == "org_1"
        assert org.name == "Test Sponsor"

    def test_manufacturer_organization_not_found(self):
        """Test manufacturer_organization returns None when role doesn't exist."""
        study_version = StudyVersion(
            id="sv_manufacturer2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[],
            instanceType="StudyVersion",
        )

        org = study_version.manufacturer_organization()
        assert org is None

    # =====================================================
    # Tests for device_manufacturer_organization method (lines 148-149)
    # =====================================================

    def test_device_manufacturer_organization_found(self):
        """Test device_manufacturer_organization returns organization when role and type match."""
        # Create device manufacturer organization type code (C215661)
        device_manufacturer_type_code = Code(
            id="device_manufacturer_type_code",
            code="C215661",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Device Manufacturer",
            instanceType="Code",
        )

        # Create device manufacturer organization
        device_manufacturer_org = Organization(
            id="org_device_manufacturer",
            name="Device Manufacturer Inc",
            label="Device Mfg",
            type=device_manufacturer_type_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )

        # Create manufacturer role code (C25392)
        manufacturer_role_code = Code(
            id="manufacturer_role_code_dm",
            code="C25392",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Manufacturer",
            instanceType="Code",
        )

        # Create manufacturer role linking to the device manufacturer org
        manufacturer_role = StudyRole(
            id="role_device_manufacturer",
            name="Manufacturer Role",
            label="Manufacturer Role",
            description="Manufacturer role description",
            code=manufacturer_role_code,
            organizationIds=["org_device_manufacturer"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_device_mfg1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org, device_manufacturer_org],
            roles=[manufacturer_role],
            instanceType="StudyVersion",
        )

        org = study_version.device_manufacturer_organization()
        assert org is not None
        assert org.id == "org_device_manufacturer"
        assert org.name == "Device Manufacturer Inc"
        assert org.type.code == "C215661"

    def test_device_manufacturer_organization_no_role(self):
        """Test device_manufacturer_organization returns None when no manufacturer role."""
        study_version = StudyVersion(
            id="sv_device_mfg2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            roles=[],
            instanceType="StudyVersion",
        )

        org = study_version.device_manufacturer_organization()
        assert org is None

    def test_device_manufacturer_organization_wrong_type(self):
        """Test device_manufacturer_organization returns None when org type doesn't match."""
        # Create manufacturer role code (C25392)
        manufacturer_role_code = Code(
            id="manufacturer_role_code_wt",
            code="C25392",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Manufacturer",
            instanceType="Code",
        )

        # Create manufacturer role linking to sponsor org (which has type C54149, not C215661)
        manufacturer_role = StudyRole(
            id="role_manufacturer_wt",
            name="Manufacturer Role",
            label="Manufacturer Role",
            description="Manufacturer role description",
            code=manufacturer_role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_device_mfg3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org],  # type.code is C54149, not C215661
            roles=[manufacturer_role],
            instanceType="StudyVersion",
        )

        org = study_version.device_manufacturer_organization()
        assert org is None

    # =====================================================
    # Tests for approval_date_text method (lines 274-277)
    # =====================================================

    def test_approval_date_text_found(self):
        """Test approval_date_text returns formatted date string when found."""
        result = self.study_version.approval_date_text()
        assert result == "2024-01-15"

    def test_approval_date_text_not_found(self):
        """Test approval_date_text returns None when no approval date exists."""
        # Create a date with a different code that won't match C71476
        other_date_code = Code(
            id="other_date_code_text",
            code="C99999",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Other Date Type",
            instanceType="Code",
        )
        other_date = GovernanceDate(
            id="other_date_text",
            name="Other Date",
            label="Other Date",
            description="Some other date",
            type=other_date_code,
            dateValue=date(2024, 1, 10),
            geographicScopes=[],
            instanceType="GovernanceDate",
        )

        study_version = StudyVersion(
            id="sv_adt1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[other_date],
            instanceType="StudyVersion",
        )

        result = study_version.approval_date_text()
        assert result is None

    def test_approval_date_text_empty_date_values(self):
        """Test approval_date_text returns None when dateValues is empty."""
        study_version = StudyVersion(
            id="sv_adt2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            dateValues=[],
            instanceType="StudyVersion",
        )

        result = study_version.approval_date_text()
        assert result is None

    # =====================================================
    # Tests for role_map method (line 288)
    # =====================================================

    def test_role_map_with_roles(self):
        """Test role_map returns correct mapping when roles exist."""
        # Create role codes
        role_code1 = Code(
            id="role_code_map1",
            code="C70793",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Sponsor",
            instanceType="Code",
        )

        role_code2 = Code(
            id="role_code_map2",
            code="C215669",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Co-Sponsor",
            instanceType="Code",
        )

        # Create roles
        role1 = StudyRole(
            id="role_map_1",
            name="Sponsor Role",
            label="Sponsor Role",
            description="Sponsor role description",
            code=role_code1,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        role2 = StudyRole(
            id="role_map_2",
            name="Co-Sponsor Role",
            label="Co-Sponsor Role",
            description="Co-sponsor role description",
            code=role_code2,
            organizationIds=["org_2"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_rolemap1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            roles=[role1, role2],
            instanceType="StudyVersion",
        )

        role_map = study_version.role_map()
        assert isinstance(role_map, dict)
        assert len(role_map) == 2
        assert "role_map_1" in role_map
        assert "role_map_2" in role_map
        assert role_map["role_map_1"].name == "Sponsor Role"
        assert role_map["role_map_2"].name == "Co-Sponsor Role"

    def test_role_map_empty(self):
        """Test role_map returns empty dict when no roles exist."""
        study_version = StudyVersion(
            id="sv_rolemap2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            roles=[],
            instanceType="StudyVersion",
        )

        role_map = study_version.role_map()
        assert isinstance(role_map, dict)
        assert len(role_map) == 0

    def test_role_map_single_role(self):
        """Test role_map with a single role."""
        role_code = Code(
            id="role_code_single",
            code="C70793",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Sponsor",
            instanceType="Code",
        )

        role = StudyRole(
            id="role_single",
            name="Single Role",
            label="Single Role",
            description="Single role description",
            code=role_code,
            organizationIds=["org_1"],
            instanceType="StudyRole",
        )

        study_version = StudyVersion(
            id="sv_rolemap3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            roles=[role],
            instanceType="StudyVersion",
        )

        role_map = study_version.role_map()
        assert isinstance(role_map, dict)
        assert len(role_map) == 1
        assert "role_single" in role_map
        assert role_map["role_single"].name == "Single Role"

    # =====================================================
    # Helper to create a study version with a role-based org
    # =====================================================

    def _create_study_version_with_role_org(
        self, sv_id, role_code_id, role_code_value, role_id, org=None, role_org_ids=None
    ):
        """Helper to create a StudyVersion with a role linking to an organization."""
        role_code = Code(
            id=role_code_id,
            code=role_code_value,
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Role",
            instanceType="Code",
        )
        role = StudyRole(
            id=role_id,
            name="Role",
            label="Role",
            description="Role description",
            code=role_code,
            organizationIds=role_org_ids or ["org_1"],
            instanceType="StudyRole",
        )
        orgs = [org] if org else [self.sponsor_org]
        return StudyVersion(
            id=sv_id,
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=orgs,
            roles=[role],
            instanceType="StudyVersion",
        )

    # =====================================================
    # Tests for co_sponsor_name, co_sponsor_label,
    # co_sponsor_label_name, co_sponsor_address (lines 147-162)
    # =====================================================

    def test_co_sponsor_name_found(self):
        """Test co_sponsor_name returns name when co-sponsor role exists."""
        sv = self._create_study_version_with_role_org(
            "sv_csn1", "rc_csn1", "C215669", "r_csn1"
        )
        assert sv.co_sponsor_name() == "Test Sponsor"

    def test_co_sponsor_name_not_found(self):
        """Test co_sponsor_name returns empty string when no co-sponsor role."""
        assert self.study_version.co_sponsor_name() == ""

    def test_co_sponsor_label_found(self):
        """Test co_sponsor_label returns label when co-sponsor role exists."""
        sv = self._create_study_version_with_role_org(
            "sv_csl1", "rc_csl1", "C215669", "r_csl1"
        )
        assert sv.co_sponsor_label() == "Test Sponsor Label"

    def test_co_sponsor_label_not_found(self):
        """Test co_sponsor_label returns empty string when no co-sponsor role."""
        assert self.study_version.co_sponsor_label() == ""

    def test_co_sponsor_label_name_returns_label(self):
        """Test co_sponsor_label_name returns label when it exists."""
        sv = self._create_study_version_with_role_org(
            "sv_csln1", "rc_csln1", "C215669", "r_csln1"
        )
        assert sv.co_sponsor_label_name() == "Test Sponsor Label"

    def test_co_sponsor_label_name_fallback_to_name(self):
        """Test co_sponsor_label_name falls back to name when label is empty."""
        org_no_label = Organization(
            id="org_csln_nolabel",
            name="Co-Sponsor Inc",
            label="",
            type=self.sponsor_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        sv = self._create_study_version_with_role_org(
            "sv_csln2",
            "rc_csln2",
            "C215669",
            "r_csln2",
            org=org_no_label,
            role_org_ids=["org_csln_nolabel"],
        )
        assert sv.co_sponsor_label_name() == "Co-Sponsor Inc"

    def test_co_sponsor_address_found(self):
        """Test co_sponsor_address returns address text when co-sponsor has address."""
        sv = self._create_study_version_with_role_org(
            "sv_csa1", "rc_csa1", "C215669", "r_csa1"
        )
        assert "123 Main St" in sv.co_sponsor_address()

    def test_co_sponsor_address_no_org(self):
        """Test co_sponsor_address returns empty string when no co-sponsor."""
        assert self.study_version.co_sponsor_address() == ""

    def test_co_sponsor_address_no_legal_address(self):
        """Test co_sponsor_address returns empty string when org has no legalAddress."""
        org_no_addr = Organization(
            id="org_csa_noaddr",
            name="No Address Org",
            label="No Address",
            type=self.sponsor_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        sv = self._create_study_version_with_role_org(
            "sv_csa2",
            "rc_csa2",
            "C215669",
            "r_csa2",
            org=org_no_addr,
            role_org_ids=["org_csa_noaddr"],
        )
        assert sv.co_sponsor_address() == ""

    # =====================================================
    # Tests for local_sponsor_name, local_sponsor_label,
    # local_sponsor_label_name, local_sponsor_address (lines 168-183)
    # =====================================================

    def test_local_sponsor_name_found(self):
        """Test local_sponsor_name returns name when local sponsor role exists."""
        sv = self._create_study_version_with_role_org(
            "sv_lsn1", "rc_lsn1", "C215670", "r_lsn1"
        )
        assert sv.local_sponsor_name() == "Test Sponsor"

    def test_local_sponsor_name_not_found(self):
        """Test local_sponsor_name returns empty string when no local sponsor role."""
        assert self.study_version.local_sponsor_name() == ""

    def test_local_sponsor_label_found(self):
        """Test local_sponsor_label returns label when local sponsor role exists."""
        sv = self._create_study_version_with_role_org(
            "sv_lsl1", "rc_lsl1", "C215670", "r_lsl1"
        )
        assert sv.local_sponsor_label() == "Test Sponsor Label"

    def test_local_sponsor_label_not_found(self):
        """Test local_sponsor_label returns empty string when no local sponsor role."""
        assert self.study_version.local_sponsor_label() == ""

    def test_local_sponsor_label_name_returns_label(self):
        """Test local_sponsor_label_name returns label when it exists."""
        sv = self._create_study_version_with_role_org(
            "sv_lsln1", "rc_lsln1", "C215670", "r_lsln1"
        )
        assert sv.local_sponsor_label_name() == "Test Sponsor Label"

    def test_local_sponsor_label_name_fallback_to_name(self):
        """Test local_sponsor_label_name falls back to name when label is empty."""
        org_no_label = Organization(
            id="org_lsln_nolabel",
            name="Local Sponsor Inc",
            label="",
            type=self.sponsor_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        sv = self._create_study_version_with_role_org(
            "sv_lsln2",
            "rc_lsln2",
            "C215670",
            "r_lsln2",
            org=org_no_label,
            role_org_ids=["org_lsln_nolabel"],
        )
        assert sv.local_sponsor_label_name() == "Local Sponsor Inc"

    def test_local_sponsor_address_found(self):
        """Test local_sponsor_address returns address text when local sponsor has address."""
        sv = self._create_study_version_with_role_org(
            "sv_lsa1", "rc_lsa1", "C215670", "r_lsa1"
        )
        assert "123 Main St" in sv.local_sponsor_address()

    def test_local_sponsor_address_no_org(self):
        """Test local_sponsor_address returns empty string when no local sponsor."""
        assert self.study_version.local_sponsor_address() == ""

    def test_local_sponsor_address_no_legal_address(self):
        """Test local_sponsor_address returns empty string when org has no legalAddress."""
        org_no_addr = Organization(
            id="org_lsa_noaddr",
            name="No Address Org",
            label="No Address",
            type=self.sponsor_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        sv = self._create_study_version_with_role_org(
            "sv_lsa2",
            "rc_lsa2",
            "C215670",
            "r_lsa2",
            org=org_no_addr,
            role_org_ids=["org_lsa_noaddr"],
        )
        assert sv.local_sponsor_address() == ""

    # =====================================================
    # Tests for device_manufacturer_name, device_manufacturer_label,
    # device_manufacturer_label_name, device_manufacturer_address (lines 193-208)
    # =====================================================

    def _create_device_manufacturer_study_version(self, sv_id, org=None):
        """Helper to create a StudyVersion with a device manufacturer org."""
        device_mfg_type_code = Code(
            id=f"dm_type_{sv_id}",
            code="C215661",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Device Manufacturer",
            instanceType="Code",
        )
        dm_org = org or Organization(
            id=f"org_dm_{sv_id}",
            name="Device Mfg Corp",
            label="Device Mfg Label",
            type=device_mfg_type_code,
            identifierScheme="scheme",
            identifier="id",
            legalAddress=self.test_address,
            instanceType="Organization",
        )
        mfg_role_code = Code(
            id=f"mfg_rc_{sv_id}",
            code="C25392",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Manufacturer",
            instanceType="Code",
        )
        mfg_role = StudyRole(
            id=f"role_dm_{sv_id}",
            name="Manufacturer Role",
            label="Manufacturer Role",
            description="Manufacturer role description",
            code=mfg_role_code,
            organizationIds=[dm_org.id],
            instanceType="StudyRole",
        )
        return StudyVersion(
            id=sv_id,
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org, dm_org],
            roles=[mfg_role],
            instanceType="StudyVersion",
        )

    def test_device_manufacturer_name_found(self):
        """Test device_manufacturer_name returns name when device manufacturer exists."""
        sv = self._create_device_manufacturer_study_version("sv_dmn1")
        assert sv.device_manufacturer_name() == "Device Mfg Corp"

    def test_device_manufacturer_name_not_found(self):
        """Test device_manufacturer_name returns empty string when no device manufacturer."""
        assert self.study_version.device_manufacturer_name() == ""

    def test_device_manufacturer_label_found(self):
        """Test device_manufacturer_label returns label when device manufacturer exists."""
        sv = self._create_device_manufacturer_study_version("sv_dml1")
        assert sv.device_manufacturer_label() == "Device Mfg Label"

    def test_device_manufacturer_label_not_found(self):
        """Test device_manufacturer_label returns empty string when no device manufacturer."""
        assert self.study_version.device_manufacturer_label() == ""

    def test_device_manufacturer_label_name_returns_label(self):
        """Test device_manufacturer_label_name returns label when it exists."""
        sv = self._create_device_manufacturer_study_version("sv_dmln1")
        assert sv.device_manufacturer_label_name() == "Device Mfg Label"

    def test_device_manufacturer_label_name_fallback_to_name(self):
        """Test device_manufacturer_label_name falls back to name when label is empty."""
        dm_type_code = Code(
            id="dm_type_nolabel",
            code="C215661",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Device Manufacturer",
            instanceType="Code",
        )
        org_no_label = Organization(
            id="org_dm_nolabel",
            name="Device Mfg No Label",
            label="",
            type=dm_type_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        sv = self._create_device_manufacturer_study_version(
            "sv_dmln2", org=org_no_label
        )
        assert sv.device_manufacturer_label_name() == "Device Mfg No Label"

    def test_device_manufacturer_address_found(self):
        """Test device_manufacturer_address returns address when device manufacturer has address."""
        sv = self._create_device_manufacturer_study_version("sv_dma1")
        assert "123 Main St" in sv.device_manufacturer_address()

    def test_device_manufacturer_address_no_org(self):
        """Test device_manufacturer_address returns empty string when no device manufacturer."""
        assert self.study_version.device_manufacturer_address() == ""

    def test_device_manufacturer_address_no_legal_address(self):
        """Test device_manufacturer_address returns empty string when org has no legalAddress."""
        dm_type_code = Code(
            id="dm_type_noaddr",
            code="C215661",
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode="Device Manufacturer",
            instanceType="Code",
        )
        org_no_addr = Organization(
            id="org_dm_noaddr",
            name="No Address Mfg",
            label="No Address",
            type=dm_type_code,
            identifierScheme="scheme",
            identifier="id",
            instanceType="Organization",
        )
        sv = self._create_device_manufacturer_study_version("sv_dma2", org=org_no_addr)
        assert sv.device_manufacturer_address() == ""

    # =====================================================
    # Tests for sponsor_approval_location (lines 339-340)
    # =====================================================

    def test_sponsor_approval_location_with_extension(self):
        """Test sponsor_approval_location returns value when extension exists."""
        sal_extension = ExtensionAttribute(
            id="ext_sal",
            url="www.d4k.dk/usdm/extensions/008",
            valueString="Section 5.2",
            instanceType="ExtensionAttribute",
        )
        sv = StudyVersion(
            id="sv_sal1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[sal_extension],
            instanceType="StudyVersion",
        )
        assert sv.sponsor_approval_location() == "Section 5.2"

    def test_sponsor_approval_location_no_extension(self):
        """Test sponsor_approval_location returns empty string when no extension."""
        assert self.study_version.sponsor_approval_location() == ""

    # =====================================================
    # Tests for compound_codes (lines 360-361)
    # =====================================================

    def test_compound_codes_with_extension(self):
        """Test compound_codes returns value when extension exists."""
        cc_extension = ExtensionAttribute(
            id="ext_cc",
            url="www.d4k.dk/usdm/extensions/004",
            valueString="ABC-123, DEF-456",
            instanceType="ExtensionAttribute",
        )
        sv = StudyVersion(
            id="sv_cc1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[cc_extension],
            instanceType="StudyVersion",
        )
        assert sv.compound_codes() == "ABC-123, DEF-456"

    def test_compound_codes_no_extension(self):
        """Test compound_codes returns empty string when no extension."""
        assert self.study_version.compound_codes() == ""

    # =====================================================
    # Tests for compound_names (lines 364-365)
    # =====================================================

    def test_compound_names_with_extension(self):
        """Test compound_names returns value when extension exists."""
        cn_extension = ExtensionAttribute(
            id="ext_cn",
            url="www.d4k.dk/usdm/extensions/005",
            valueString="Aspirin, Ibuprofen",
            instanceType="ExtensionAttribute",
        )
        sv = StudyVersion(
            id="sv_cn1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[cn_extension],
            instanceType="StudyVersion",
        )
        assert sv.compound_names() == "Aspirin, Ibuprofen"

    def test_compound_names_no_extension(self):
        """Test compound_names returns empty string when no extension."""
        assert self.study_version.compound_names() == ""

    # =====================================================
    # Tests for medical_expert (lines 368-369)
    # =====================================================

    def test_medical_expert_with_extension(self):
        """Test medical_expert_contact_details_location returns value when extension exists."""
        me_extension = ExtensionAttribute(
            id="ext_me",
            url="www.d4k.dk/usdm/extensions/006",
            valueString="Dr. Jane Smith",
            instanceType="ExtensionAttribute",
        )
        sv = StudyVersion(
            id="sv_me1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[me_extension],
            instanceType="StudyVersion",
        )
        assert sv.medical_expert_contact_details_location() == "Dr. Jane Smith"

    def test_medical_expert_no_extension(self):
        """Test medical_expert_contact_details_location returns None when no extension."""
        assert self.study_version.medical_expert_contact_details_location() is None

    # =====================================================
    # Tests for sponsor_signatory (lines 372-373)
    # =====================================================

    def test_sponsor_signatory_with_extension(self):
        """Test sponsor_signatory returns value when extension exists."""
        ss_extension = ExtensionAttribute(
            id="ext_ss",
            url="www.d4k.dk/usdm/extensions/007",
            valueString="John Doe, VP Clinical",
            instanceType="ExtensionAttribute",
        )
        sv = StudyVersion(
            id="sv_ss1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            extensionAttributes=[ss_extension],
            instanceType="StudyVersion",
        )
        assert sv.sponsor_signatory() == "John Doe, VP Clinical"

    def test_sponsor_signatory_no_extension(self):
        """Test sponsor_signatory returns empty string when no extension."""
        assert self.study_version.sponsor_signatory() == ""

    # =====================================================
    # Tests for to_html (lines 351-357)
    # =====================================================

    def test_to_html_matching_template(self):
        """Test to_html returns HTML when matching template is found."""
        from src.usdm4.api.narrative_content import NarrativeContent

        # Create narrative content items
        item1 = NarrativeContentItem(
            id="nci_1",
            name="Section 1 Content",
            text="<p>Introduction text</p>",
            instanceType="NarrativeContentItem",
        )
        item2 = NarrativeContentItem(
            id="nci_2",
            name="Section 2 Content",
            text="<p>Methods text</p>",
            instanceType="NarrativeContentItem",
        )

        # Create narrative contents linked in order
        nc1 = NarrativeContent(
            id="nc_1",
            name="Section 1",
            sectionNumber="1",
            sectionTitle="Introduction",
            displaySectionNumber=True,
            displaySectionTitle=True,
            nextId="nc_2",
            contentItemId="nci_1",
            instanceType="NarrativeContent",
        )
        nc2 = NarrativeContent(
            id="nc_2",
            name="Section 2",
            sectionNumber="2",
            sectionTitle="Methods",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="nc_1",
            contentItemId="nci_2",
            instanceType="NarrativeContent",
        )

        # Create document version with contents
        status_code = Code(
            id="status_html",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code",
        )
        doc_version = StudyDefinitionDocumentVersion(
            id="dv_html",
            version="1.0",
            status=status_code,
            contents=[nc1, nc2],
            instanceType="StudyDefinitionDocumentVersion",
        )

        # Create document
        doc_language = Code(
            id="lang_html",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )
        doc_type = Code(
            id="doc_type_html",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )
        doc = StudyDefinitionDocument(
            id="doc_html",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="Protocol",
            language=doc_language,
            type=doc_type,
            versions=[doc_version],
            instanceType="StudyDefinitionDocument",
        )

        # Create document map
        document_map = {"dv_html": {"document": doc, "version": doc_version}}

        # Create study version referencing the document version
        sv = StudyVersion(
            id="sv_html1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_html"],
            narrativeContentItems=[item1, item2],
            instanceType="StudyVersion",
        )

        result = sv.to_html("Protocol", document_map)
        assert result is not None
        assert "<h1>1 Introduction</h1>" in result
        assert "<p>Introduction text</p>" in result
        assert "<h1>2 Methods</h1>" in result
        assert "<p>Methods text</p>" in result

    def test_to_html_no_matching_template(self):
        """Test to_html returns None when no matching template is found."""
        # Create a document with a different template name
        status_code = Code(
            id="status_html2",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code",
        )
        doc_version = StudyDefinitionDocumentVersion(
            id="dv_html2",
            version="1.0",
            status=status_code,
            instanceType="StudyDefinitionDocumentVersion",
        )
        doc_language = Code(
            id="lang_html2",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )
        doc_type = Code(
            id="doc_type_html2",
            code="CSR",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="CSR Document",
            instanceType="Code",
        )
        doc = StudyDefinitionDocument(
            id="doc_html2",
            name="CSR Document",
            label="CSR v1.0",
            templateName="CSR",
            language=doc_language,
            type=doc_type,
            versions=[doc_version],
            instanceType="StudyDefinitionDocument",
        )

        document_map = {"dv_html2": {"document": doc, "version": doc_version}}

        sv = StudyVersion(
            id="sv_html2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_html2"],
            instanceType="StudyVersion",
        )

        result = sv.to_html("Protocol", document_map)
        assert result is None

    def test_to_html_case_insensitive_template(self):
        """Test to_html matches template name case-insensitively."""
        from src.usdm4.api.narrative_content import NarrativeContent

        item = NarrativeContentItem(
            id="nci_ci",
            name="Content",
            text="<p>Content</p>",
            instanceType="NarrativeContentItem",
        )
        nc1 = NarrativeContent(
            id="nc_ci1",
            name="Section 1",
            sectionNumber="1",
            sectionTitle="Title",
            displaySectionNumber=True,
            displaySectionTitle=True,
            nextId="nc_ci2",
            contentItemId="nci_ci",
            instanceType="NarrativeContent",
        )
        nc2 = NarrativeContent(
            id="nc_ci2",
            name="Section 2",
            sectionNumber="2",
            sectionTitle="Second",
            displaySectionNumber=True,
            displaySectionTitle=True,
            previousId="nc_ci1",
            instanceType="NarrativeContent",
        )
        status_code = Code(
            id="status_ci",
            code="FINAL",
            codeSystem="DOC_STATUS",
            codeSystemVersion="1.0",
            decode="Final",
            instanceType="Code",
        )
        doc_version = StudyDefinitionDocumentVersion(
            id="dv_ci",
            version="1.0",
            status=status_code,
            contents=[nc1, nc2],
            instanceType="StudyDefinitionDocumentVersion",
        )
        doc_language = Code(
            id="lang_ci",
            code="EN",
            codeSystem="LANGUAGE",
            codeSystemVersion="1.0",
            decode="English",
            instanceType="Code",
        )
        doc_type = Code(
            id="doc_type_ci",
            code="PROTOCOL",
            codeSystem="DOC_TYPE",
            codeSystemVersion="1.0",
            decode="Protocol Document",
            instanceType="Code",
        )
        doc = StudyDefinitionDocument(
            id="doc_ci",
            name="Protocol Document",
            label="Protocol v1.0",
            templateName="protocol",
            language=doc_language,
            type=doc_type,
            versions=[doc_version],
            instanceType="StudyDefinitionDocument",
        )

        document_map = {"dv_ci": {"document": doc, "version": doc_version}}

        sv = StudyVersion(
            id="sv_ci",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_ci"],
            narrativeContentItems=[item],
            instanceType="StudyVersion",
        )

        # Search with different case
        result = sv.to_html("PROTOCOL", document_map)
        assert result is not None
        assert "<p>Content</p>" in result

    # =====================================================
    # Tests for study_document_version method
    # =====================================================

    def test_study_document_version_no_documents(self):
        """Test study_document_version() returns None when no documents linked."""
        sv = StudyVersion(
            id="sv_sdv1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=[],
            instanceType="StudyVersion",
        )
        result = sv.study_document_version("Protocol", {})
        assert result is None

    def test_study_document_version_matching_template(self):
        """Test study_document_version() returns version when template matches."""
        version1 = self._create_document_version("dv_sdv2", "1.0")
        doc1 = self._create_document_with_versions("doc_sdv2", "Protocol", [version1])
        document_map = self._create_document_map([(doc1, [version1])])

        sv = StudyVersion(
            id="sv_sdv2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_sdv2"],
            instanceType="StudyVersion",
        )

        result = sv.study_document_version("Protocol", document_map)
        assert result is not None
        assert isinstance(result, StudyDefinitionDocumentVersion)
        assert result.id == "dv_sdv2"

    def test_study_document_version_no_matching_template(self):
        """Test study_document_version() returns None when template doesn't match."""
        version1 = self._create_document_version("dv_sdv3", "1.0")
        doc1 = self._create_document_with_versions("doc_sdv3", "CSR", [version1])
        document_map = self._create_document_map([(doc1, [version1])])

        sv = StudyVersion(
            id="sv_sdv3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_sdv3"],
            instanceType="StudyVersion",
        )

        result = sv.study_document_version("Protocol", document_map)
        assert result is None

    def test_study_document_version_case_insensitive(self):
        """Test study_document_version() matches template name case-insensitively."""
        version1 = self._create_document_version("dv_sdv4", "1.0")
        doc1 = self._create_document_with_versions("doc_sdv4", "Protocol", [version1])
        document_map = self._create_document_map([(doc1, [version1])])

        sv = StudyVersion(
            id="sv_sdv4",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_sdv4"],
            instanceType="StudyVersion",
        )

        assert sv.study_document_version("protocol", document_map) is not None
        assert sv.study_document_version("PROTOCOL", document_map) is not None
        assert sv.study_document_version("Protocol", document_map) is not None

    def test_study_document_version_multiple_documents(self):
        """Test study_document_version() finds the correct document among multiple."""
        version1 = self._create_document_version("dv_sdv5a", "1.0")
        version2 = self._create_document_version("dv_sdv5b", "1.0")
        doc1 = self._create_document_with_versions("doc_sdv5a", "Protocol", [version1])
        doc2 = self._create_document_with_versions("doc_sdv5b", "ICF", [version2])
        document_map = self._create_document_map(
            [(doc1, [version1]), (doc2, [version2])]
        )

        sv = StudyVersion(
            id="sv_sdv5",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier],
            titles=[self.official_title],
            documentVersionIds=["dv_sdv5a", "dv_sdv5b"],
            instanceType="StudyVersion",
        )

        result = sv.study_document_version("ICF", document_map)
        assert result is not None
        assert result.id == "dv_sdv5b"

        result = sv.study_document_version("Protocol", document_map)
        assert result is not None
        assert result.id == "dv_sdv5a"

    # =====================================================
    # Helper for identifier type extension tests
    # =====================================================

    def _create_identifier_with_type(
        self, identifier_id: str, text: str, scope_id: str, type_code: str
    ) -> StudyIdentifier:
        """Helper to create a StudyIdentifier with a SIT extension (identifier type)."""
        sit_code = BaseCode(
            id=f"sit_code_{identifier_id}",
            code=type_code,
            codeSystem="CDISC",
            codeSystemVersion="1.0",
            decode=f"Identifier Type {type_code}",
            instanceType="Code",
        )
        sit_extension = ExtensionAttribute(
            id=f"sit_ext_{identifier_id}",
            url="www.d4k.dk/usdm/extensions/009",
            valueCode=sit_code,
            instanceType="ExtensionAttribute",
        )
        return StudyIdentifier(
            id=identifier_id,
            text=text,
            scopeId=scope_id,
            extensionAttributes=[sit_extension],
            instanceType="StudyIdentifier",
        )

    # =====================================================
    # Tests for nct_identifier method (line 210-211)
    # =====================================================

    def test_nct_identifier_found(self):
        """Test nct_identifier returns identifier when type C172240 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_ctgov", "SPONSOR-123", "org_1", "C999999"
        )
        ct_gov_id = self._create_identifier_with_type(
            "id_ctgov", "NCT00000001", "org_2", "C172240"
        )
        sv = StudyVersion(
            id="sv_ctgov1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, ct_gov_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.nct_identifier()
        assert result is not None
        assert result.text == "NCT00000001"

    def test_nct_identifier_not_found(self):
        """Test nct_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_ctgov2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_ctgov2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.nct_identifier()
        assert result is None

    # =====================================================
    # Tests for nmpa_identifier method (line 213-214)
    # =====================================================

    def test_nmpa_identifier_found(self):
        """Test nmpa_identifier returns identifier when type C218688 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_npma", "SPONSOR-123", "org_1", "C999999"
        )
        npma_id = self._create_identifier_with_type(
            "id_npma", "NMPA-12345", "org_2", "C218688"
        )
        sv = StudyVersion(
            id="sv_npma1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, npma_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.nmpa_identifier()
        assert result is not None
        assert result.text == "NMPA-12345"

    def test_nmpa_identifier_not_found(self):
        """Test nmpa_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_npma2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_npma2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.nmpa_identifier()
        assert result is None

    # =====================================================
    # Tests for who_identifier method (line 216-217)
    # =====================================================

    def test_who_identifier_found(self):
        """Test who_identifier returns identifier when type C218689 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_who", "SPONSOR-123", "org_1", "C999999"
        )
        who_id = self._create_identifier_with_type(
            "id_who", "WHO-2024-001", "org_2", "C218689"
        )
        sv = StudyVersion(
            id="sv_who1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, who_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.who_identifier()
        assert result is not None
        assert result.text == "WHO-2024-001"

    def test_who_identifier_not_found(self):
        """Test who_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_who2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_who2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.who_identifier()
        assert result is None

    # =====================================================
    # Tests for fda_ind_identifier method (line 222-223)
    # =====================================================

    def test_fda_ind_identifier_by_type_found(self):
        """Test fda_ind_identifier returns identifier when type C218685 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_fda", "SPONSOR-123", "org_1", "C999999"
        )
        fda_id = self._create_identifier_with_type(
            "id_fda_new", "FDA-2024-001", "org_2", "C218685"
        )
        sv = StudyVersion(
            id="sv_fda_new1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, fda_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.fda_ind_identifier()
        assert result is not None
        assert result.text == "FDA-2024-001"

    def test_fda_ind_identifier_by_type_not_found(self):
        """Test fda_ind_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_fda2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_fda_new2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.fda_ind_identifier()
        assert result is None

    # =====================================================
    # Tests for fda_ide_identifier method (line 225-226)
    # =====================================================

    def test_fda_ide_identifier_found(self):
        """Test fda_ide_identifier returns identifier when type C218686 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_ide", "SPONSOR-123", "org_1", "C999999"
        )
        fda_ide_id = self._create_identifier_with_type(
            "id_fda_ide", "IDE-2024-001", "org_2", "C218686"
        )
        sv = StudyVersion(
            id="sv_fda_ide1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, fda_ide_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.fda_ide_identifier()
        assert result is not None
        assert result.text == "IDE-2024-001"

    def test_fda_ide_identifier_not_found(self):
        """Test fda_ide_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_ide2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_fda_ide2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.fda_ide_identifier()
        assert result is None

    # =====================================================
    # Tests for jrct_identifier method (line 228-229)
    # =====================================================

    def test_jrct_identifier_found(self):
        """Test jrct_identifier returns identifier when type C218687 exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_jrct", "SPONSOR-123", "org_1", "C999999"
        )
        jrct_id = self._create_identifier_with_type(
            "id_jrct", "jRCT-2024-001", "org_2", "C218687"
        )
        sv = StudyVersion(
            id="sv_jrct1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, jrct_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.jrct_identifier()
        assert result is not None
        assert result.text == "jRCT-2024-001"

    def test_jrct_identifier_not_found(self):
        """Test jrct_identifier returns None when no matching identifier exists."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_jrct2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_jrct2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.jrct_identifier()
        assert result is None

    # =====================================================
    # Tests for other_identifiers method (line 231-239)
    # =====================================================

    def test_other_identifiers_found(self):
        """Test other_identifiers returns identifiers with type code C218690."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_oi", "SPONSOR-123", "org_1", "C999999"
        )
        other_id_1 = self._create_identifier_with_type(
            "id_other_1", "OTHER-001", "org_2", "C218690"
        )
        other_id_2 = self._create_identifier_with_type(
            "id_other_2", "OTHER-002", "org_2", "C218690"
        )
        sv = StudyVersion(
            id="sv_other1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, other_id_1, other_id_2],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            instanceType="StudyVersion",
        )
        result = sv.other_identifiers()
        assert len(result) == 2
        texts = [x.text for x in result]
        assert "OTHER-001" in texts
        assert "OTHER-002" in texts

    def test_other_identifiers_excludes_sponsor(self):
        """Test other_identifiers excludes the sponsor identifier even if it has type C218690."""
        sponsor_id_with_type = self._create_identifier_with_type(
            "id_sponsor_typed", "SPONSOR-TYPED", "org_1", "C218690"
        )
        other_id = self._create_identifier_with_type(
            "id_other_3", "OTHER-003", "org_2", "C218690"
        )
        sv = StudyVersion(
            id="sv_other2",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id_with_type, other_id],
            titles=[self.official_title],
            organizations=[self.sponsor_org, self.non_sponsor_org],
            instanceType="StudyVersion",
        )
        result = sv.other_identifiers()
        # sponsor_id_with_type is the sponsor_identifier() since org_1 is sponsor
        # so it should be excluded
        assert len(result) == 1
        assert result[0].text == "OTHER-003"

    def test_other_identifiers_empty(self):
        """Test other_identifiers returns empty list when no identifiers have type C218690."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_oi2", "SPONSOR-123", "org_1", "C999999"
        )
        sv = StudyVersion(
            id="sv_other_empty",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            instanceType="StudyVersion",
        )
        result = sv.other_identifiers()
        assert result == []

    def test_other_identifiers_skips_non_matching_types(self):
        """Test other_identifiers skips identifiers with non-C218690 type codes."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_oi3", "SPONSOR-123", "org_1", "C999999"
        )
        ct_gov_id = self._create_identifier_with_type(
            "id_ctgov_skip", "NCT99999", "org_2", "C172240"
        )
        other_id = self._create_identifier_with_type(
            "id_other_4", "OTHER-004", "org_2", "C218690"
        )
        sv = StudyVersion(
            id="sv_other3",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, ct_gov_id, other_id],
            titles=[self.official_title],
            organizations=[self.sponsor_org],
            instanceType="StudyVersion",
        )
        result = sv.other_identifiers()
        assert len(result) == 1
        assert result[0].text == "OTHER-004"

    # =====================================================
    # Tests for _identifier_of_type private method (line 241-242)
    # =====================================================

    def test_identifier_of_type_multiple_matches_returns_first(self):
        """Test _identifier_of_type returns the first matching identifier."""
        sponsor_id = self._create_identifier_with_type(
            "id_sponsor_iot", "SPONSOR-123", "org_1", "C999999"
        )
        id_1 = self._create_identifier_with_type(
            "id_dup_1", "FIRST-MATCH", "org_2", "C172240"
        )
        id_2 = self._create_identifier_with_type(
            "id_dup_2", "SECOND-MATCH", "org_2", "C172240"
        )
        sv = StudyVersion(
            id="sv_iot1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[sponsor_id, id_1, id_2],
            titles=[self.official_title],
            instanceType="StudyVersion",
        )
        result = sv.nct_identifier()
        assert result is not None
        assert result.text == "FIRST-MATCH"
