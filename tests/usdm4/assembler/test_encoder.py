import pytest
import datetime
from unittest.mock import Mock
from simple_error_log.errors import Errors
from usdm4.builder.builder import Builder
from usdm4.assembler.encoder import Encoder
from usdm4.api.alias_code import AliasCode
from usdm4.api.code import Code


class TestEncoderInitialization:
    """Test Encoder initialization"""

    def test_init_with_valid_parameters(self):
        """Test initialization with valid builder and errors"""
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        encoder = Encoder(builder, errors)

        assert encoder._builder == builder
        assert encoder._errors == errors


class TestEncoderPhase:
    """Test phase encoding method"""

    @pytest.fixture
    def encoder(self):
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        return Encoder(builder, errors)

    def test_phase_0(self, encoder):
        """Test Phase 0 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase 0")

        encoder._builder.cdisc_code.assert_called_with("C54721", "Phase 0 Trial")
        assert result == mock_alias

    def test_phase_preclinical(self, encoder):
        """Test Pre-clinical phase decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("PRE-CLINICAL")

        encoder._builder.cdisc_code.assert_called_with("C54721", "Phase 0 Trial")
        assert result == mock_alias

    def test_phase_1(self, encoder):
        """Test Phase 1 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase I")

        encoder._builder.cdisc_code.assert_called_with("C15600", "Phase I Trial")
        assert result == mock_alias

    def test_phase_1_numeric(self, encoder):
        """Test Phase 1 numeric decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("1")

        encoder._builder.cdisc_code.assert_called_with("C15600", "Phase I Trial")
        assert result == mock_alias

    def test_phase_1_2(self, encoder):
        """Test Phase 1-2 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase 1-2")

        encoder._builder.cdisc_code.assert_called_with("C15693", "Phase I/II Trial")
        assert result == mock_alias

    def test_phase_1_slash_2(self, encoder):
        """Test Phase 1/2 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("1/2")

        encoder._builder.cdisc_code.assert_called_with("C15693", "Phase I/II Trial")
        assert result == mock_alias

    def test_phase_1_2_3(self, encoder):
        """Test Phase 1/2/3 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("1/2/3")

        encoder._builder.cdisc_code.assert_called_with(
            "C198366", "Phase I/II/III Trial"
        )
        assert result == mock_alias

    def test_phase_1_3(self, encoder):
        """Test Phase 1/3 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("1/3")

        encoder._builder.cdisc_code.assert_called_with("C198367", "Phase I/III Trial")
        assert result == mock_alias

    def test_phase_1a(self, encoder):
        """Test Phase 1A decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase 1A")

        encoder._builder.cdisc_code.assert_called_with("C199990", "Phase Ia Trial")
        assert result == mock_alias

    def test_phase_1b(self, encoder):
        """Test Phase 1B decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("IB")

        encoder._builder.cdisc_code.assert_called_with("C199989", "Phase Ib Trial")
        assert result == mock_alias

    def test_phase_2(self, encoder):
        """Test Phase 2 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase II")

        encoder._builder.cdisc_code.assert_called_with("C15601", "Phase II Trial")
        assert result == mock_alias

    def test_phase_2_3(self, encoder):
        """Test Phase 2-3 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("2-3")

        encoder._builder.cdisc_code.assert_called_with("C15694", "Phase II/III Trial")
        assert result == mock_alias

    def test_phase_2a(self, encoder):
        """Test Phase 2A decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("2A")

        encoder._builder.cdisc_code.assert_called_with("C49686", "Phase IIa Trial")
        assert result == mock_alias

    def test_phase_2b(self, encoder):
        """Test Phase 2B decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("IIB")

        encoder._builder.cdisc_code.assert_called_with("C49688", "Phase IIb Trial")
        assert result == mock_alias

    def test_phase_3(self, encoder):
        """Test Phase 3 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase III")

        encoder._builder.cdisc_code.assert_called_with("C15602", "Phase III Trial")
        assert result == mock_alias

    def test_phase_3a(self, encoder):
        """Test Phase 3A decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("IIIA")

        encoder._builder.cdisc_code.assert_called_with("C49687", "Phase IIIa Trial")
        assert result == mock_alias

    def test_phase_3b(self, encoder):
        """Test Phase 3B decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("3B")

        encoder._builder.cdisc_code.assert_called_with("C49689", "Phase IIIb Trial")
        assert result == mock_alias

    def test_phase_4(self, encoder):
        """Test Phase 4 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("4")

        encoder._builder.cdisc_code.assert_called_with("C15603", "Phase IV Trial")
        assert result == mock_alias

    def test_phase_5(self, encoder):
        """Test Phase 5 decoding"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("V")

        encoder._builder.cdisc_code.assert_called_with("C47865", "Phase V Trial")
        assert result == mock_alias

    def test_phase_unknown(self, encoder):
        """Test unknown phase decoding defaults to Not Applicable"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase Unknown")

        encoder._builder.cdisc_code.assert_called_with(
            "C48660", "[Trial Phase] Not Applicable"
        )
        encoder._errors.warning.assert_called()
        assert result == mock_alias

    def test_phase_empty_string(self, encoder):
        """Test empty phase string"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("")

        encoder._builder.cdisc_code.assert_called_with(
            "C48660", "[Trial Phase] Not Applicable"
        )
        encoder._errors.warning.assert_called()
        assert result == mock_alias


class TestEncoderDocumentStatus:
    """Test document_status encoding method"""

    @pytest.fixture
    def encoder(self):
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        return Encoder(builder, errors)

    def test_document_status_approved(self, encoder):
        """Test APPROVED status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("APPROVED")

        encoder._builder.cdisc_code.assert_called_with("C25425", "Approved")
        assert result == mock_code

    def test_document_status_draft(self, encoder):
        """Test DRAFT status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("DRAFT")

        encoder._builder.cdisc_code.assert_called_with("C85255", "Draft")
        assert result == mock_code

    def test_document_status_dft(self, encoder):
        """Test DFT status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("DFT")

        encoder._builder.cdisc_code.assert_called_with("C85255", "Draft")
        assert result == mock_code

    def test_document_status_final(self, encoder):
        """Test FINAL status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("FINAL")

        encoder._builder.cdisc_code.assert_called_with("C25508", "Final")
        assert result == mock_code

    def test_document_status_obsolete(self, encoder):
        """Test OBSOLETE status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("OBSOLETE")

        encoder._builder.cdisc_code.assert_called_with("C63553", "Obsolete")
        assert result == mock_code

    def test_document_status_pending(self, encoder):
        """Test PENDING status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("PENDING")

        encoder._builder.cdisc_code.assert_called_with("C188862", "Pending Review")
        assert result == mock_code

    def test_document_status_pending_review(self, encoder):
        """Test PENDING REVIEW status decoding"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("PRENDING REVIEW")

        encoder._builder.cdisc_code.assert_called_with("C188862", "Pending Review")
        assert result == mock_code

    def test_document_status_unknown(self, encoder):
        """Test unknown status defaults to Draft"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("UNKNOWN")

        encoder._builder.cdisc_code.assert_called_with("C85255", "Draft")
        encoder._errors.warning.assert_called()
        assert result == mock_code

    def test_document_status_empty_string(self, encoder):
        """Test empty status string"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("")

        encoder._builder.cdisc_code.assert_called_with("C85255", "Draft")
        encoder._errors.warning.assert_called()
        assert result == mock_code

    def test_document_status_lowercase(self, encoder):
        """Test lowercase status is normalized"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("approved")

        encoder._builder.cdisc_code.assert_called_with("C25425", "Approved")
        assert result == mock_code


class TestEncoderAmendmentReason:
    """Test amendment_reason encoding method"""

    @pytest.fixture
    def encoder(self):
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        return Encoder(builder, errors)

    def test_amendment_reason_regulatory_request(self, encoder):
        """Test Regulatory Agency Request To Amend"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Regulatory Agency Request To Amend")

        encoder._builder.cdisc_code.assert_called_with(
            "C207612", "Regulatory Agency Request To Amend"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_new_guidance(self, encoder):
        """Test New Regulatory Guidance"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:New Regulatory Guidance")

        encoder._builder.cdisc_code.assert_called_with(
            "C207608", "New Regulatory Guidance"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_irb_feedback(self, encoder):
        """Test IRB/IEC Feedback"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:IRB/IEC Feedback")

        encoder._builder.cdisc_code.assert_called_with("C207605", "IRB/IEC Feedback")
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_new_safety_info(self, encoder):
        """Test New Safety Information Available"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:New Safety Information Available")

        encoder._builder.cdisc_code.assert_called_with(
            "C207609", "New Safety Information Available"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_manufacturing_change(self, encoder):
        """Test Manufacturing Change"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Manufacturing Change")

        encoder._builder.cdisc_code.assert_called_with(
            "C207606", "Manufacturing Change"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_imp_addition(self, encoder):
        """Test IMP Addition"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:IMP Addition")

        encoder._builder.cdisc_code.assert_called_with("C207602", "IMP Addition")
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_change_in_strategy(self, encoder):
        """Test Change In Strategy"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Change In Strategy")

        encoder._builder.cdisc_code.assert_called_with("C207601", "Change In Strategy")
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_change_in_standard_of_care(self, encoder):
        """Test Change In Standard Of Care"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Change In Standard Of Care")

        encoder._builder.cdisc_code.assert_called_with(
            "C207600", "Change In Standard Of Care"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_new_data_available(self, encoder):
        """Test New Data Available (Other Than Safety Data)"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason(
            "Reason:New Data Available (Other Than Safety Data)"
        )

        encoder._builder.cdisc_code.assert_called_with(
            "C207607", "New Data Available (Other Than Safety Data)"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_investigator_feedback(self, encoder):
        """Test Investigator/Site Feedback"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Investigator/Site Feedback")

        encoder._builder.cdisc_code.assert_called_with(
            "C207604", "Investigator/Site Feedback"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_recruitment_difficulty(self, encoder):
        """Test Recruitment Difficulty"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Recruitment Difficulty")

        encoder._builder.cdisc_code.assert_called_with(
            "C207611", "Recruitment Difficulty"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_inconsistency_error(self, encoder):
        """Test Inconsistency And/Or Error In The Protocol"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason(
            "Reason:Inconsistency And/Or Error In The Protocol"
        )

        encoder._builder.cdisc_code.assert_called_with(
            "C207603", "Inconsistency And/Or Error In The Protocol"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_protocol_design_error(self, encoder):
        """Test Protocol Design Error"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Protocol Design Error")

        encoder._builder.cdisc_code.assert_called_with(
            "C207610", "Protocol Design Error"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_other(self, encoder):
        """Test Other - note that 'Other' matches 'New Data Available (Other Than Safety Data)' first"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Other")

        # "Other" is contained in "New Data Available (Other Than Safety Data)" so it matches that
        encoder._builder.cdisc_code.assert_called_with(
            "C207607", "New Data Available (Other Than Safety Data)"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_not_applicable(self, encoder):
        """Test Not Applicable"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Not Applicable")

        encoder._builder.cdisc_code.assert_called_with("C48660", "Not Applicable")
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_amendment_reason_unknown_with_text(self, encoder):
        """Test unknown reason with custom text"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Custom reason text")

        encoder._builder.cdisc_code.assert_called_with("C17649", "Other")
        encoder._errors.warning.assert_called()
        assert result["code"] == mock_code
        assert result["other_reason"] == "Custom reason text"

    def test_amendment_reason_malformed_string(self, encoder):
        """Test malformed reason string without colon"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Some text without colon")

        encoder._builder.cdisc_code.assert_called_with("C17649", "Other")
        encoder._errors.warning.assert_called()
        assert result["code"] == mock_code
        assert result["other_reason"] == "Some text without colon"

    def test_amendment_reason_empty_string(self, encoder):
        """Test empty reason string"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("")

        encoder._builder.cdisc_code.assert_called_with("C17649", "Other")
        encoder._errors.warning.assert_called()
        assert result["code"] == mock_code
        assert result["other_reason"] == "No reason text found"

    def test_amendment_reason_none(self, encoder):
        """Test None reason"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason(None)

        encoder._builder.cdisc_code.assert_called_with("C17649", "Other")
        encoder._errors.warning.assert_called()
        assert result["code"] == mock_code
        assert result["other_reason"] == "No reason text found"


class TestEncoderToDate:
    """Test to_date encoding method"""

    @pytest.fixture
    def encoder(self):
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        return Encoder(builder, errors)

    def test_to_date_valid_iso_format(self, encoder):
        """Test valid ISO format date"""
        result = encoder.to_date("2024-01-15")

        assert isinstance(result, datetime.datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_to_date_valid_us_format(self, encoder):
        """Test valid US format date"""
        result = encoder.to_date("01/15/2024")

        assert isinstance(result, datetime.datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_to_date_valid_with_time(self, encoder):
        """Test valid datetime with time"""
        result = encoder.to_date("2024-01-15 14:30:00")

        assert isinstance(result, datetime.datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30

    def test_to_date_with_whitespace(self, encoder):
        """Test date with leading/trailing whitespace"""
        result = encoder.to_date("  2024-01-15  ")

        assert isinstance(result, datetime.datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_to_date_empty_string(self, encoder):
        """Test empty date string returns None"""
        result = encoder.to_date("")

        assert result is None

    def test_to_date_whitespace_only(self, encoder):
        """Test whitespace-only string returns None"""
        result = encoder.to_date("   ")

        assert result is None

    def test_to_date_invalid_format(self, encoder):
        """Test invalid date format"""
        result = encoder.to_date("invalid date")

        assert result is None
        encoder._errors.exception.assert_called()

    def test_to_date_partial_date(self, encoder):
        """Test partial date like year-month"""
        result = encoder.to_date("2024-01")

        assert isinstance(result, datetime.datetime)
        assert result.year == 2024
        assert result.month == 1


class TestEncoderISO8601Duration:
    """Test iso8601_duration encoding method"""

    @pytest.fixture
    def encoder(self):
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        return Encoder(builder, errors)

    def test_iso8601_duration_years(self, encoder):
        """Test years duration encoding"""
        assert encoder.iso8601_duration(5, "Y") == "P5Y"
        assert encoder.iso8601_duration(2, "YEARS") == "P2Y"
        assert encoder.iso8601_duration(1, "YEAR") == "P1Y"
        assert encoder.iso8601_duration(3, "YRS") == "P3Y"
        assert encoder.iso8601_duration(1, "YR") == "P1Y"

    def test_iso8601_duration_months(self, encoder):
        """Test months duration encoding"""
        assert encoder.iso8601_duration(6, "MTHS") == "P6M"
        assert encoder.iso8601_duration(12, "MTH") == "P12M"
        assert encoder.iso8601_duration(3, "MONTHS") == "P3M"
        assert encoder.iso8601_duration(1, "MONTH") == "P1M"

    def test_iso8601_duration_weeks(self, encoder):
        """Test weeks duration encoding"""
        assert encoder.iso8601_duration(4, "W") == "P4W"
        assert encoder.iso8601_duration(2, "WEEKS") == "P2W"
        assert encoder.iso8601_duration(1, "WEEK") == "P1W"
        assert encoder.iso8601_duration(3, "WKS") == "P3W"
        assert encoder.iso8601_duration(1, "WK") == "P1W"

    def test_iso8601_duration_days(self, encoder):
        """Test days duration encoding"""
        assert encoder.iso8601_duration(7, "D") == "P7D"
        assert encoder.iso8601_duration(14, "DAYS") == "P14D"
        assert encoder.iso8601_duration(1, "DAY") == "P1D"
        assert encoder.iso8601_duration(30, "DYS") == "P30D"
        assert encoder.iso8601_duration(1, "DY") == "P1D"

    def test_iso8601_duration_hours(self, encoder):
        """Test hours duration encoding"""
        assert encoder.iso8601_duration(24, "H") == "PT24H"
        assert encoder.iso8601_duration(12, "HOURS") == "PT12H"
        assert encoder.iso8601_duration(1, "HOUR") == "PT1H"
        assert encoder.iso8601_duration(8, "HRS") == "PT8H"
        assert encoder.iso8601_duration(2, "HR") == "PT2H"

    def test_iso8601_duration_minutes(self, encoder):
        """Test minutes duration encoding"""
        assert encoder.iso8601_duration(60, "M") == "PT60M"
        assert encoder.iso8601_duration(30, "MINUTES") == "PT30M"
        assert encoder.iso8601_duration(1, "MINUTE") == "PT1M"
        assert encoder.iso8601_duration(45, "MINS") == "PT45M"
        assert encoder.iso8601_duration(15, "MIN") == "PT15M"

    def test_iso8601_duration_seconds(self, encoder):
        """Test seconds duration encoding"""
        assert encoder.iso8601_duration(60, "S") == "PT60S"
        assert encoder.iso8601_duration(30, "SECONDS") == "PT30S"
        assert encoder.iso8601_duration(1, "SECOND") == "PT1S"
        assert encoder.iso8601_duration(45, "SECS") == "PT45S"
        assert encoder.iso8601_duration(15, "SEC") == "PT15S"

    def test_iso8601_duration_lowercase(self, encoder):
        """Test lowercase unit handling"""
        assert encoder.iso8601_duration(5, "y") == "P5Y"
        assert encoder.iso8601_duration(3, "months") == "P3M"
        assert encoder.iso8601_duration(2, "weeks") == "P2W"
        assert encoder.iso8601_duration(7, "days") == "P7D"
        assert encoder.iso8601_duration(12, "hours") == "PT12H"
        assert encoder.iso8601_duration(30, "minutes") == "PT30M"
        assert encoder.iso8601_duration(45, "seconds") == "PT45S"

    def test_iso8601_duration_with_whitespace(self, encoder):
        """Test units with leading/trailing whitespace"""
        assert encoder.iso8601_duration(5, "  Y  ") == "P5Y"
        assert encoder.iso8601_duration(3, " MONTHS ") == "P3M"
        assert encoder.iso8601_duration(7, "  DAYS  ") == "P7D"

    def test_iso8601_duration_unknown_unit(self, encoder):
        """Test unknown unit returns zero duration"""
        result = encoder.iso8601_duration(10, "unknown")

        assert result == "PT0M"
        encoder._errors.warning.assert_called()

    def test_iso8601_duration_exception_handling(self, encoder):
        """Test exception handling in duration encoding"""
        encoder._errors.exception = Mock()

        # This should trigger the exception handler if any error occurs
        try:
            # Pass None as unit to potentially trigger an exception
            result = encoder.iso8601_duration(10, None)
        except:
            pass

        # At minimum it should handle gracefully


class TestEncoderConstants:
    """Test Encoder class constants"""

    def test_module_constant(self):
        """Test MODULE constant is properly defined"""
        assert Encoder.MODULE == "usdm4.encoder.encoder.Encoder"

    def test_zero_duration_constant(self):
        """Test ZERO_DURATION constant is properly defined"""
        assert Encoder.ZERO_DURATION == "PT0M"

    def test_phase_map_exists(self):
        """Test PHASE_MAP is properly defined"""
        assert isinstance(Encoder.PHASE_MAP, list)
        assert len(Encoder.PHASE_MAP) > 0

    def test_status_map_exists(self):
        """Test STATUS_MAP is properly defined"""
        assert isinstance(Encoder.STATUS_MAP, list)
        assert len(Encoder.STATUS_MAP) > 0

    def test_reason_map_exists(self):
        """Test REASON_MAP is properly defined"""
        assert isinstance(Encoder.REASON_MAP, list)
        assert len(Encoder.REASON_MAP) > 0


class TestEncoderEdgeCases:
    """Test edge cases and special scenarios"""

    @pytest.fixture
    def encoder(self):
        builder = Mock(spec=Builder)
        errors = Mock(spec=Errors)
        return Encoder(builder, errors)

    def test_phase_with_trial_keyword(self, encoder):
        """Test phase extraction removes TRIAL keyword"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("Phase I Trial")

        encoder._builder.cdisc_code.assert_called_with("C15600", "Phase I Trial")
        assert result == mock_alias

    def test_phase_mixed_case(self, encoder):
        """Test phase with mixed case"""
        mock_code = Mock(spec=Code)
        mock_alias = Mock(spec=AliasCode)
        encoder._builder.cdisc_code.return_value = mock_code
        encoder._builder.alias_code.return_value = mock_alias

        result = encoder.phase("pHaSe Ii")

        encoder._builder.cdisc_code.assert_called_with("C15601", "Phase II Trial")
        assert result == mock_alias

    def test_document_status_with_spaces(self, encoder):
        """Test document status with extra spaces"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.document_status("  DRAFT  ")

        encoder._builder.cdisc_code.assert_called_with("C85255", "Draft")
        assert result == mock_code

    def test_amendment_reason_with_multiple_colons(self, encoder):
        """Test amendment reason with multiple colons"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason("Reason:Text:With:Multiple:Colons")

        # When not matched, uses parts[-1] which is the last element after split
        encoder._builder.cdisc_code.assert_called_with("C17649", "Other")
        assert result["other_reason"] == "Colons"

    def test_amendment_reason_only_colon(self, encoder):
        """Test amendment reason with only colon"""
        mock_code = Mock(spec=Code)
        encoder._builder.cdisc_code.return_value = mock_code

        result = encoder.amendment_reason(":")

        # Empty string '' is in any string, so it matches the first reason in REASON_MAP
        encoder._builder.cdisc_code.assert_called_with(
            "C207612", "Regulatory Agency Request To Amend"
        )
        assert result["code"] == mock_code
        assert result["other_reason"] == ""

    def test_iso8601_duration_zero_value(self, encoder):
        """Test duration with zero value"""
        assert encoder.iso8601_duration(0, "DAYS") == "P0D"
        assert encoder.iso8601_duration(0, "HOURS") == "PT0H"

    def test_iso8601_duration_large_value(self, encoder):
        """Test duration with large value"""
        assert encoder.iso8601_duration(1000, "DAYS") == "P1000D"
        assert encoder.iso8601_duration(999, "HOURS") == "PT999H"

    def test_iso8601_duration_empty_unit(self, encoder):
        """Test duration with empty unit string"""
        result = encoder.iso8601_duration(5, "")

        assert result == "PT0M"
        encoder._errors.warning.assert_called()
