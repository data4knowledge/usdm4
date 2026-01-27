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
from src.usdm4.api.extension import ExtensionAttribute
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
        assert date_obj == ""

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
        assert date_value == ""

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
    # Tests for fda_ind_identifier method (lines 220-225)
    # =====================================================

    def test_fda_ind_identifier_found(self):
        """Test fda_ind_identifier returns the identifier when FDA org exists."""
        fda_org = Organization(
            id="org_fda",
            name="FDA",
            label="Food and Drug Administration",
            type=self.non_sponsor_code,
            identifierScheme="scheme",
            identifier="fda_id",
            instanceType="Organization",
        )

        fda_identifier = StudyIdentifier(
            id="id_fda",
            text="IND-123456",
            scopeId="org_fda",
            instanceType="StudyIdentifier",
        )

        study_version = StudyVersion(
            id="sv_fda1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier, fda_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org, fda_org],
            instanceType="StudyVersion",
        )

        result = study_version.fda_ind_identifier()
        assert result == "IND-123456"

    def test_fda_ind_identifier_not_found(self):
        """Test fda_ind_identifier returns empty string when no FDA org exists."""
        result = self.study_version.fda_ind_identifier()
        assert result == ""

    # =====================================================
    # Tests for ema_identifier method (lines 227-232)
    # =====================================================

    def test_ema_identifier_found(self):
        """Test ema_identifier returns the identifier when EMA org exists."""
        ema_org = Organization(
            id="org_ema",
            name="EMA",
            label="European Medicines Agency",
            type=self.non_sponsor_code,
            identifierScheme="scheme",
            identifier="ema_id",
            instanceType="Organization",
        )

        ema_identifier = StudyIdentifier(
            id="id_ema",
            text="EudraCT-2024-001234-56",
            scopeId="org_ema",
            instanceType="StudyIdentifier",
        )

        study_version = StudyVersion(
            id="sv_ema1",
            versionIdentifier="v1.0",
            rationale="Test",
            studyIdentifiers=[self.sponsor_identifier, ema_identifier],
            titles=[self.official_title],
            organizations=[self.sponsor_org, ema_org],
            instanceType="StudyVersion",
        )

        result = study_version.ema_identifier()
        assert result == "EudraCT-2024-001234-56"

    def test_ema_identifier_not_found(self):
        """Test ema_identifier returns empty string when no EMA org exists."""
        result = self.study_version.ema_identifier()
        assert result == ""

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
