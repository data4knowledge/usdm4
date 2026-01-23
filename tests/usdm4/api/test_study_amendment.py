from src.usdm4.api.study_amendment import StudyAmendment
from src.usdm4.api.study_amendment_reason import StudyAmendmentReason
from src.usdm4.api.geographic_scope import GeographicScope
from src.usdm4.api.code import Code


class TestStudyAmendment:
    def _create_code(self, code: str, decode: str, code_id: str = "code1") -> Code:
        """Helper method to create a Code object."""
        return Code(
            id=code_id,
            code=code,
            codeSystem="TEST_SYSTEM",
            codeSystemVersion="1.0",
            decode=decode,
            instanceType="Code",
        )

    def _create_reason(
        self, decode: str, reason_id: str = "reason1", other_reason: str = None
    ) -> StudyAmendmentReason:
        """Helper method to create a StudyAmendmentReason object."""
        code = self._create_code("REASON", decode, f"{reason_id}_code")
        return StudyAmendmentReason(
            id=reason_id,
            code=code,
            otherReason=other_reason,
            instanceType="StudyAmendmentReason",
        )

    def _create_geographic_scope(self, scope_id: str = "scope1") -> GeographicScope:
        """Helper method to create a GeographicScope object."""
        scope_type = self._create_code("GLOBAL", "Global", f"{scope_id}_type")
        return GeographicScope(
            id=scope_id,
            type=scope_type,
            instanceType="GeographicScope",
        )

    def _create_study_amendment(
        self,
        primary_reason: StudyAmendmentReason = None,
        secondary_reasons: list = None,
    ) -> StudyAmendment:
        """Helper method to create a StudyAmendment object."""
        if primary_reason is None:
            primary_reason = self._create_reason("Primary Reason", "primary_reason")
        if secondary_reasons is None:
            secondary_reasons = []

        return StudyAmendment(
            id="amendment1",
            name="Amendment 1",
            label="AMD-001",
            description="Test amendment",
            number="1",
            summary="Test amendment summary",
            primaryReason=primary_reason,
            secondaryReasons=secondary_reasons,
            geographicScopes=[self._create_geographic_scope()],
            instanceType="StudyAmendment",
        )

    def test_basic_initialization(self):
        """Test basic initialization of StudyAmendment."""
        amendment = self._create_study_amendment()

        assert amendment.id == "amendment1"
        assert amendment.name == "Amendment 1"
        assert amendment.label == "AMD-001"
        assert amendment.description == "Test amendment"
        assert amendment.number == "1"
        assert amendment.summary == "Test amendment summary"
        assert amendment.instanceType == "StudyAmendment"

    def test_default_values(self):
        """Test that default values are set correctly."""
        amendment = self._create_study_amendment()

        assert amendment.secondaryReasons == []
        assert amendment.changes == []
        assert amendment.impacts == []
        assert amendment.enrollments == []
        assert amendment.dateValues == []
        assert amendment.previousId is None
        assert amendment.notes == []

    def test_primary_reason_as_text(self):
        """Test primary_reason_as_text returns the decode of the primary reason code."""
        primary_reason = self._create_reason("Safety Update", "primary_reason")
        amendment = self._create_study_amendment(primary_reason=primary_reason)

        result = amendment.primary_reason_as_text()

        assert result == "Safety Update"

    def test_primary_other_reason_as_text_with_value(self):
        """Test primary_other_reason_as_text when otherReason is set."""
        primary_reason = self._create_reason(
            "Other", "primary_reason", other_reason="Custom safety concern"
        )
        amendment = self._create_study_amendment(primary_reason=primary_reason)

        result = amendment.primary_other_reason_as_text()

        assert result == "Custom safety concern"

    def test_primary_other_reason_as_text_without_value(self):
        """Test primary_other_reason_as_text when otherReason is None."""
        primary_reason = self._create_reason("Safety Update", "primary_reason")
        amendment = self._create_study_amendment(primary_reason=primary_reason)

        result = amendment.primary_other_reason_as_text()

        assert result == ""

    def test_secondary_reason_as_text_with_reasons(self):
        """Test secondary_reason_as_text returns the decode of the first secondary reason."""
        secondary_reason = self._create_reason("Protocol Clarification", "secondary1")
        amendment = self._create_study_amendment(secondary_reasons=[secondary_reason])

        result = amendment.secondary_reason_as_text()

        assert result == "Protocol Clarification"

    def test_secondary_reason_as_text_with_multiple_reasons(self):
        """Test secondary_reason_as_text returns only the first secondary reason."""
        secondary1 = self._create_reason("Protocol Clarification", "secondary1")
        secondary2 = self._create_reason("Eligibility Update", "secondary2")
        amendment = self._create_study_amendment(
            secondary_reasons=[secondary1, secondary2]
        )

        result = amendment.secondary_reason_as_text()

        assert result == "Protocol Clarification"

    def test_secondary_reason_as_text_empty_list(self):
        """Test secondary_reason_as_text returns empty string when no secondary reasons."""
        amendment = self._create_study_amendment(secondary_reasons=[])

        result = amendment.secondary_reason_as_text()

        assert result == ""

    def test_secondary_other_reason_as_text_with_value(self):
        """Test secondary_other_reason_as_text when otherReason is set."""
        secondary_reason = self._create_reason(
            "Other", "secondary1", other_reason="Custom eligibility concern"
        )
        amendment = self._create_study_amendment(secondary_reasons=[secondary_reason])

        result = amendment.secondary_other_reason_as_text()

        assert result == "Custom eligibility concern"

    def test_secondary_other_reason_as_text_without_value(self):
        """Test secondary_other_reason_as_text when otherReason is None."""
        secondary_reason = self._create_reason("Protocol Clarification", "secondary1")
        amendment = self._create_study_amendment(secondary_reasons=[secondary_reason])

        result = amendment.secondary_other_reason_as_text()

        assert result == ""

    def test_secondary_other_reason_as_text_empty_list(self):
        """Test secondary_other_reason_as_text returns empty string when no secondary reasons."""
        amendment = self._create_study_amendment(secondary_reasons=[])

        result = amendment.secondary_other_reason_as_text()

        assert result == ""

    def test_geographic_scopes_required(self):
        """Test that geographicScopes is a required field."""
        primary_reason = self._create_reason("Safety Update", "primary_reason")

        amendment = StudyAmendment(
            id="amendment1",
            name="Amendment 1",
            number="1",
            summary="Test summary",
            primaryReason=primary_reason,
            geographicScopes=[self._create_geographic_scope()],
            instanceType="StudyAmendment",
        )

        assert len(amendment.geographicScopes) == 1

    def test_with_multiple_geographic_scopes(self):
        """Test StudyAmendment with multiple geographic scopes."""
        primary_reason = self._create_reason("Safety Update", "primary_reason")
        scopes = [
            self._create_geographic_scope("scope1"),
            self._create_geographic_scope("scope2"),
            self._create_geographic_scope("scope3"),
        ]

        amendment = StudyAmendment(
            id="amendment1",
            name="Amendment 1",
            number="1",
            summary="Test summary",
            primaryReason=primary_reason,
            geographicScopes=scopes,
            instanceType="StudyAmendment",
        )

        assert len(amendment.geographicScopes) == 3


class TestStudyAmendmentIsGlobal:
    """Test the is_global method of StudyAmendment."""

    def _create_code(self, code: str, decode: str, code_id: str = "code1") -> Code:
        """Helper method to create a Code object."""
        return Code(
            id=code_id,
            code=code,
            codeSystem="TEST_SYSTEM",
            codeSystemVersion="1.0",
            decode=decode,
            instanceType="Code",
        )

    def _create_reason(self, decode: str, reason_id: str = "reason1") -> StudyAmendmentReason:
        """Helper method to create a StudyAmendmentReason object."""
        code = self._create_code("REASON", decode, f"{reason_id}_code")
        return StudyAmendmentReason(
            id=reason_id,
            code=code,
            instanceType="StudyAmendmentReason",
        )

    def _create_geographic_scope_with_type(
        self, type_code: str, type_decode: str, scope_id: str = "scope1"
    ) -> GeographicScope:
        """Helper method to create a GeographicScope with a specific type code."""
        scope_type = self._create_code(type_code, type_decode, f"{scope_id}_type")
        return GeographicScope(
            id=scope_id,
            type=scope_type,
            instanceType="GeographicScope",
        )

    def _create_amendment_with_scopes(self, scopes: list) -> StudyAmendment:
        """Helper method to create a StudyAmendment with specific scopes."""
        return StudyAmendment(
            id="amendment1",
            name="Amendment 1",
            number="1",
            summary="Test summary",
            primaryReason=self._create_reason("Primary Reason"),
            geographicScopes=scopes,
            instanceType="StudyAmendment",
        )

    def test_is_global_returns_true_for_global_scope(self):
        """Test is_global returns True when a global scope (C68846) is present."""
        global_scope = self._create_geographic_scope_with_type("C68846", "Global", "global_scope")
        amendment = self._create_amendment_with_scopes([global_scope])

        assert amendment.is_global() is True

    def test_is_global_returns_false_for_country_scope(self):
        """Test is_global returns False when only country scope (C25464) is present."""
        country_scope = self._create_geographic_scope_with_type("C25464", "Country", "country_scope")
        amendment = self._create_amendment_with_scopes([country_scope])

        assert amendment.is_global() is False

    def test_is_global_returns_false_for_region_scope(self):
        """Test is_global returns False when only region scope is present."""
        region_scope = self._create_geographic_scope_with_type("C25228", "Region", "region_scope")
        amendment = self._create_amendment_with_scopes([region_scope])

        assert amendment.is_global() is False

    def test_is_global_returns_true_with_mixed_scopes_including_global(self):
        """Test is_global returns True when global scope is among multiple scopes."""
        country_scope = self._create_geographic_scope_with_type("C25464", "Country", "country_scope")
        global_scope = self._create_geographic_scope_with_type("C68846", "Global", "global_scope")
        region_scope = self._create_geographic_scope_with_type("C25228", "Region", "region_scope")
        amendment = self._create_amendment_with_scopes([country_scope, global_scope, region_scope])

        assert amendment.is_global() is True

    def test_is_global_returns_false_with_multiple_non_global_scopes(self):
        """Test is_global returns False when multiple non-global scopes are present."""
        country_scope1 = self._create_geographic_scope_with_type("C25464", "Country", "country1")
        country_scope2 = self._create_geographic_scope_with_type("C25464", "Country", "country2")
        amendment = self._create_amendment_with_scopes([country_scope1, country_scope2])

        assert amendment.is_global() is False

    def test_is_global_finds_global_scope_at_end_of_list(self):
        """Test is_global finds global scope even when it's at the end of the list."""
        country_scope1 = self._create_geographic_scope_with_type("C25464", "Country", "country1")
        country_scope2 = self._create_geographic_scope_with_type("C25464", "Country", "country2")
        global_scope = self._create_geographic_scope_with_type("C68846", "Global", "global_scope")
        amendment = self._create_amendment_with_scopes([country_scope1, country_scope2, global_scope])

        assert amendment.is_global() is True
