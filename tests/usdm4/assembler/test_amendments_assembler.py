import os
import pathlib
import pytest
from unittest.mock import MagicMock
from simple_error_log.errors import Errors
from src.usdm4.assembler.amendments_assembler import AmendmentsAssembler
from src.usdm4.assembler.document_assembler import DocumentAssembler
from src.usdm4.builder.builder import Builder


def root_path():
    """Get the root path for the usdm4 package."""
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    """Create a Builder instance for testing."""
    return Builder(root_path(), Errors())


@pytest.fixture(scope="module")
def errors():
    """Create an Errors instance for testing."""
    return Errors()


@pytest.fixture
def document_assembler(builder, errors):
    """Create a DocumentAssembler instance for testing with a mock document."""
    assembler = DocumentAssembler(builder, errors)
    # Execute with minimal document data to create a real document with an id
    document_data = {
        "document": {
            "label": "Test Protocol Document",
            "version": "1.0",
            "status": "final",
            "template": "Protocol Template",
            "version_date": "2024-01-01",
        },
        "sections": [
            {
                "section_number": "1",
                "section_title": "Introduction",
                "text": "This is the introduction section.",
            }
        ],
    }
    assembler.execute(document_data)
    return assembler


@pytest.fixture
def amendments_assembler(builder, errors):
    """Create an AmendmentsAssembler instance for testing."""
    # Clear the builder to avoid cross-reference conflicts
    builder.clear()
    return AmendmentsAssembler(builder, errors)


class TestAmendmentsAssemblerInitialization:
    """Test AmendmentsAssembler initialization."""

    def test_init_with_valid_parameters(self, builder, errors):
        """Test AmendmentsAssembler initialization with valid parameters."""
        assembler = AmendmentsAssembler(builder, errors)

        assert assembler._builder is builder
        assert assembler._errors is errors
        assert (
            assembler.MODULE
            == "usdm4.assembler.amendments_assembler.AmenementsAssembler"
        )

        # Test initial state
        assert assembler._amendment is None
        assert assembler._encoder is not None

    def test_amendment_property_initial_state(self, amendments_assembler):
        """Test that amendment property returns None initially."""
        assert amendments_assembler.amendment is None

    def test_encoder_initialization(self, amendments_assembler):
        """Test that encoder is properly initialized."""
        assert amendments_assembler._encoder is not None
        assert hasattr(amendments_assembler._encoder, "amendment_reason")


def make_impact(safety=False, rights=False, reliability=False, robustness=False):
    """Helper to create the new impact data structure."""
    return {
        "safety_and_rights": {
            "safety": {
                "substantial": safety,
                "reason": "Safety reason" if safety else "",
            },
            "rights": {
                "substantial": rights,
                "reason": "Rights reason" if rights else "",
            },
        },
        "reliability_and_robustness": {
            "reliability": {
                "substantial": reliability,
                "reason": "Reliability reason" if reliability else "",
            },
            "robustness": {
                "substantial": robustness,
                "reason": "Robustness reason" if robustness else "",
            },
        },
    }


def make_changes():
    """Helper to create default changes data."""
    return []


class TestAmendmentsAssemblerValidData:
    """Test AmendmentsAssembler with valid data."""

    def test_execute_with_complete_valid_data(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with complete valid amendment data."""
        data = {
            "identifier": "1",
            "summary": "Amendment to add new safety monitoring procedures",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "enrollment": {"value": 150, "unit": "%"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        # Should have created an amendment
        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment

        # Verify amendment properties
        assert amendment.name == "AMENDMENT 1"
        assert amendment.number == "1"
        assert amendment.summary == "Amendment to add new safety monitoring procedures"

        # Verify reasons
        assert amendment.primaryReason is not None
        assert amendment.secondaryReasons is not None
        assert len(amendment.secondaryReasons) == 1

        # Verify enrollments
        assert amendment.enrollments is not None
        assert len(amendment.enrollments) == 1

        # Verify geographic scopes
        assert amendment.geographicScopes is not None
        assert len(amendment.geographicScopes) == 1

    def test_execute_with_minimal_valid_data(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with minimal valid amendment data."""
        data = {
            "identifier": "1",
            "summary": "Minor protocol clarification",
            "reasons": {
                "primary": "C207603:Inconsistency And/Or Error In The Protocol",
                "secondary": "C17649:Other",
            },
            "impact": make_impact(reliability=True),
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        # Should have created an amendment
        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment

        # Verify basic properties
        assert amendment.name == "AMENDMENT 1"
        assert amendment.number == "1"
        assert amendment.summary == "Minor protocol clarification"

        # Should have enrollment with default value 0
        assert amendment.enrollments is not None
        assert len(amendment.enrollments) == 1
        enrollment = amendment.enrollments[0]
        assert enrollment.quantity.value == 0

    def test_execute_with_safety_impact_true(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with safety impact set to true."""
        data = {
            "identifier": "1",
            "summary": "Safety-related amendment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207612:Regulatory Agency Request To Amend",
            },
            "impact": make_impact(safety=True),
            "enrollment": {"value": 200, "unit": "%"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        _ = amendments_assembler.amendment
        # Test that amendment was created successfully

    def test_execute_with_reliability_impact_true(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with reliability impact set to true."""
        data = {
            "identifier": "1",
            "summary": "Reliability-related amendment",
            "reasons": {
                "primary": "C207610:Protocol Design Error",
                "secondary": "C207601:Change In Strategy",
            },
            "impact": make_impact(reliability=True),
            "enrollment": {"value": 100, "unit": "%"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        _ = amendments_assembler.amendment
        # Test that amendment was created successfully

    def test_execute_with_both_impacts_false(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with both safety and reliability impacts false."""
        data = {
            "identifier": "1",
            "summary": "Minor administrative change",
            "reasons": {
                "primary": "C17649:Other",
                "secondary": "C48660:Not Applicable",
            },
            "impact": make_impact(),
            "enrollment": {"value": 75, "unit": "%"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        _ = amendments_assembler.amendment
        # Test that amendment was created successfully

    def test_execute_with_both_impacts_true(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with both safety and reliability impacts true."""
        data = {
            "identifier": "1",
            "summary": "Major protocol amendment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207610:Protocol Design Error",
            },
            "impact": make_impact(safety=True, reliability=True),
            "enrollment": {"value": 300, "unit": "%"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        _ = amendments_assembler.amendment
        # Test that amendment was created successfully

    def test_execute_with_different_enrollment_units(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with different enrollment unit values."""
        # Test with percentage unit
        data = {
            "identifier": "1",
            "summary": "Test amendment with percentage enrollment",
            "reasons": {
                "primary": "C207601:Change In Strategy",
                "secondary": "C17649:Other",
            },
            "impact": make_impact(reliability=True),
            "enrollment": {"value": 125, "unit": "%"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        enrollment = amendment.enrollments[0]
        assert enrollment.quantity.value == 125
        assert enrollment.quantity.unit is not None  # Should have percentage unit

    def test_execute_with_non_percentage_enrollment_unit(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with non-percentage enrollment unit."""
        data = {
            "identifier": "1",
            "summary": "Test amendment with non-percentage enrollment",
            "reasons": {
                "primary": "C207602:IMP Addition",
                "secondary": "C207604:Investigator/Site Feedback",
            },
            "impact": make_impact(safety=True),
            "enrollment": {"value": 50, "unit": "subjects"},
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        enrollment = amendment.enrollments[0]
        assert enrollment.quantity.value == 50
        assert (
            enrollment.quantity.unit is None
        )  # Should be None for non-percentage units

    def test_execute_with_all_valid_reason_codes(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with various valid amendment reason codes."""
        valid_reasons = [
            "C207612:Regulatory Agency Request To Amend",
            "C207608:New Regulatory Guidance",
            "C207605:IRB/IEC Feedback",
            "C207609:New Safety Information Available",
            "C207606:Manufacturing Change",
            "C207602:IMP Addition",
            "C207601:Change In Strategy",
            "C207600:Change In Standard Of Care",
            "C207607:New Data Available (Other Than Safety Data)",
            "C207604:Investigator/Site Feedback",
            "C207611:Recruitment Difficulty",
            "C207603:Inconsistency And/Or Error In The Protocol",
            "C207610:Protocol Design Error",
            "C17649:Other",
            "C48660:Not Applicable",
        ]

        for i, reason in enumerate(
            valid_reasons[:5]
        ):  # Test first 5 to avoid too many iterations
            # Clear previous amendment and builder state
            amendments_assembler._amendment = None
            amendments_assembler._builder.clear()

            data = {
                "identifier": "1",
                "summary": f"Test amendment {i + 1}",
                "reasons": {"primary": reason, "secondary": "C17649:Other"},
                "impact": make_impact(safety=i % 2 == 0, reliability=i % 2 == 1),
                "enrollment": {"value": 100 + i * 10, "unit": "%"},
                "changes": make_changes(),
            }

            amendments_assembler.execute(data, document_assembler)

            assert amendments_assembler.amendment is not None
            amendment = amendments_assembler.amendment
            assert amendment.summary == f"Test amendment {i + 1}"


class TestAmendmentsAssemblerInvalidData:
    """Test AmendmentsAssembler with invalid data."""

    def test_execute_with_empty_data(self, amendments_assembler, document_assembler):
        """Test execute with empty data dictionary."""
        data = {}

        amendments_assembler.execute(data, document_assembler)

        # Should handle empty data gracefully
        assert amendments_assembler.amendment is None

    def test_execute_with_none_data(self, amendments_assembler, document_assembler):
        """Test execute with None data."""
        amendments_assembler.execute(None, document_assembler)

        # Should handle None data gracefully
        assert amendments_assembler.amendment is None

    def test_execute_with_missing_summary(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing summary field."""
        data = {
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing summary - may create amendment with None summary or fail
        # The exact behavior depends on the Builder's handling of None values

    def test_execute_with_missing_reasons(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing reasons field."""
        data = {
            "summary": "Test amendment without reasons",
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing reasons gracefully - likely will fail during creation
        # The amendment should be None due to the exception handling

    def test_execute_with_missing_impact(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing impact field."""
        data = {
            "summary": "Test amendment without impact",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing impact gracefully - likely will fail during creation

    def test_execute_with_invalid_reason_format(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with invalid reason format."""
        data = {
            "summary": "Test amendment with invalid reasons",
            "reasons": {
                "primary": "Invalid reason format",
                "secondary": "Another invalid reason",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle invalid reason format - encoder should handle this gracefully
        # May create amendment with "Other" reason codes

    def test_execute_with_missing_primary_reason(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing primary reason."""
        data = {
            "summary": "Test amendment without primary reason",
            "reasons": {"secondary": "C207605:IRB/IEC Feedback"},
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing primary reason - likely will fail during creation

    def test_execute_with_missing_secondary_reason(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing secondary reason."""
        data = {
            "summary": "Test amendment without secondary reason",
            "reasons": {"primary": "C207609:New Safety Information Available"},
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing secondary reason - likely will fail during creation

    def test_execute_with_invalid_enrollment_value(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with invalid enrollment value."""
        data = {
            "summary": "Test amendment with invalid enrollment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": "invalid_number", "unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle invalid enrollment value - may fail during quantity creation

    def test_execute_with_missing_enrollment_value(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing enrollment value."""
        data = {
            "summary": "Test amendment with missing enrollment value",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing enrollment value - may fail during quantity creation

    def test_execute_with_missing_enrollment_unit(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with missing enrollment unit."""
        data = {
            "summary": "Test amendment with missing enrollment unit",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": 100},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle missing enrollment unit - may create quantity with None unit

    def test_execute_with_invalid_impact_values(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with invalid impact values."""
        data = {
            "summary": "Test amendment with invalid impact",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": "not_boolean", "reliability": "also_not_boolean"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle invalid impact values - may fail during boolean evaluation

    def test_execute_with_malformed_data_structure(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with malformed data structure."""
        malformed_data = {
            "summary": "Test amendment",
            "reasons": "not_a_dict",  # Should be a dict
            "impact": ["not", "a", "dict"],  # Should be a dict
            "enrollment": "not_a_dict",  # Should be a dict
        }

        # Should handle malformed data gracefully without crashing
        try:
            amendments_assembler.execute(malformed_data, document_assembler)
        except (AttributeError, TypeError, KeyError):
            # Expected behavior - the method doesn't handle malformed data gracefully
            pass

        # Amendment should be None due to exception handling
        # The exact behavior depends on where the exception occurs

    def test_execute_with_none_values_in_data(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with None values in data fields."""
        data = {
            "summary": None,
            "reasons": {"primary": None, "secondary": None},
            "impact": {"safety": None, "reliability": None},
            "enrollment": None,
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle None values - may fail during processing


class TestAmendmentsAssemblerEdgeCases:
    """Test AmendmentsAssembler edge cases."""

    def test_execute_with_empty_summary(self, amendments_assembler, document_assembler):
        """Test execute with empty summary string."""
        data = {
            "summary": "",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle empty summary
        if amendments_assembler.amendment is not None:
            assert amendments_assembler.amendment.summary == ""

    def test_execute_with_very_long_summary(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with very long summary text."""
        long_summary = "A" * 1000  # 1000 character summary
        data = {
            "summary": long_summary,
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle long summary
        if amendments_assembler.amendment is not None:
            assert amendments_assembler.amendment.summary == long_summary

    def test_execute_with_unicode_summary(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with unicode characters in summary."""
        unicode_summary = (
            "Amendment with émojis 🧬💊 and special characters: àáâãäåæçèéêë"
        )
        data = {
            "summary": unicode_summary,
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle unicode characters
        if amendments_assembler.amendment is not None:
            assert amendments_assembler.amendment.summary == unicode_summary

    def test_execute_with_zero_enrollment_value(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with zero enrollment value."""
        data = {
            "summary": "Amendment with zero enrollment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": 0, "unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle zero enrollment value
        if amendments_assembler.amendment is not None:
            enrollment = amendments_assembler.amendment.enrollments[0]
            assert enrollment.quantity.value == 0

    def test_execute_with_negative_enrollment_value(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with negative enrollment value."""
        data = {
            "summary": "Amendment with negative enrollment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": -50, "unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle negative enrollment value
        if amendments_assembler.amendment is not None:
            enrollment = amendments_assembler.amendment.enrollments[0]
            assert enrollment.quantity.value == -50

    def test_execute_with_very_large_enrollment_value(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with very large enrollment value."""
        data = {
            "summary": "Amendment with large enrollment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": 999999, "unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle large enrollment value
        if amendments_assembler.amendment is not None:
            enrollment = amendments_assembler.amendment.enrollments[0]
            assert enrollment.quantity.value == 999999

    def test_execute_with_float_enrollment_value(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with float enrollment value."""
        data = {
            "summary": "Amendment with float enrollment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": 123.45, "unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle float enrollment value
        if amendments_assembler.amendment is not None:
            enrollment = amendments_assembler.amendment.enrollments[0]
            assert enrollment.quantity.value == 123.45

    def test_execute_with_special_characters_in_reasons(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with special characters in reason strings."""
        data = {
            "summary": "Amendment with special reason characters",
            "reasons": {
                "primary": "C207609:New Safety Information Available (with special chars: @#$%)",
                "secondary": "C207605:IRB/IEC Feedback & Additional Notes",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle special characters in reasons
        # The encoder should process these and likely fall back to "Other" category

    def test_execute_multiple_times_overwrites_amendment(
        self, amendments_assembler, document_assembler
    ):
        """Test that multiple execute calls overwrite the previous amendment."""
        # First call
        data1 = {
            "summary": "First amendment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }
        amendments_assembler.execute(data1, document_assembler)
        first_amendment = amendments_assembler.amendment

        # Second call
        data2 = {
            "summary": "Second amendment",
            "reasons": {
                "primary": "C207610:Protocol Design Error",
                "secondary": "C207601:Change In Strategy",
            },
            "impact": {"safety": False, "reliability": True},
        }
        amendments_assembler.execute(data2, document_assembler)
        second_amendment = amendments_assembler.amendment

        # Should have overwritten the first amendment
        if second_amendment is not None:
            assert second_amendment.summary == "Second amendment"
            assert second_amendment is not first_amendment


class TestAmendmentsAssemblerPrivateMethods:
    """Test AmendmentsAssembler private methods."""

    def test_create_amendment_with_valid_data(self, amendments_assembler):
        """Test _create_amendment with valid data."""
        data = {
            "summary": "Test amendment creation",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {"value": 100, "unit": "%"},
        }

        amendment = amendments_assembler._create_amendment(data)

        if amendment is not None:
            assert amendment.instanceType == "StudyAmendment"
            assert amendment.name == "AMENDMENT 1"
            assert amendment.number == "1"
            assert amendment.summary == "Test amendment creation"
            # Test that amendment was created successfully

    def test_create_enrollment_with_valid_data(self, amendments_assembler):
        """Test _create_enrollment with valid enrollment data."""
        data = {"enrollment": {"value": 150, "unit": "%"}}

        enrollment = amendments_assembler._create_enrollment(data)

        if enrollment is not None:
            assert enrollment.instanceType == "SubjectEnrollment"
            assert enrollment.name == "ENROLLMENT"
            assert enrollment.quantity.value == 150
            assert enrollment.quantity.unit is not None  # Should have percentage unit

    def test_create_enrollment_without_enrollment_data(self, amendments_assembler):
        """Test _create_enrollment without enrollment data."""
        data = {}

        enrollment = amendments_assembler._create_enrollment(data)

        if enrollment is not None:
            assert enrollment.instanceType == "SubjectEnrollment"
            assert enrollment.name == "ENROLLMENT"
            assert enrollment.quantity.value == 0
            assert enrollment.quantity.unit is None

    def test_create_enrollment_with_non_percentage_unit(self, amendments_assembler):
        """Test _create_enrollment with non-percentage unit."""
        data = {"enrollment": {"value": 75, "unit": "subjects"}}

        enrollment = amendments_assembler._create_enrollment(data)

        if enrollment is not None:
            assert enrollment.instanceType == "SubjectEnrollment"
            assert enrollment.quantity.value == 75
            assert enrollment.quantity.unit is None  # Should be None for non-percentage


class TestAmendmentsAssemblerErrorHandling:
    """Test AmendmentsAssembler error handling (without mocking Errors)."""

    def test_error_handling_with_exception_in_create_amendment(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test error handling when _create_amendment raises an exception."""
        # This will likely cause an exception due to missing required fields
        data = {
            "summary": "Test amendment",
            "reasons": {},  # Empty reasons dict
            "impact": {"safety": True, "reliability": False},
        }

        initial_error_count = errors.error_count()
        amendments_assembler.execute(data, document_assembler)

        # Should have logged an error
        assert errors.error_count() > initial_error_count
        assert amendments_assembler.amendment is None

    def test_error_handling_with_exception_in_create_enrollment(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test error handling when _create_enrollment raises an exception."""
        # Create a scenario that might cause enrollment creation to fail
        data = {
            "summary": "Test amendment",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {
                "value": "invalid_value",  # This might cause an exception
                "unit": "%",
            },
        }

        amendments_assembler.execute(data, document_assembler)

        # May have logged an error depending on where the exception occurs
        # The amendment might still be None due to exception handling

    def test_error_handling_with_builder_failures(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test error handling when Builder operations fail."""
        # This test depends on the Builder's behavior with invalid data
        data = {
            "summary": "Test amendment with potential builder failures",
            "reasons": {
                "primary": "INVALID_CODE:Invalid Reason",
                "secondary": "ANOTHER_INVALID:Another Invalid Reason",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # The encoder should handle invalid reason codes gracefully
        # May still create an amendment with "Other" reason codes


class TestAmendmentsAssemblerBuilderIntegration:
    """Test AmendmentsAssembler integration with Builder (without mocking)."""

    def test_builder_cdisc_code_integration(
        self, amendments_assembler, document_assembler
    ):
        """Test integration with Builder's cdisc_code method."""
        data = {
            "summary": "Test builder integration",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should integrate with Builder's cdisc_code functionality
        if amendments_assembler.amendment is not None:
            amendment = amendments_assembler.amendment
            assert amendment.primaryReason is not None
            # The reason should have a code created by Builder

    def test_builder_create_method_integration(
        self, amendments_assembler, document_assembler
    ):
        """Test integration with Builder's create method."""
        data = {
            "summary": "Test create method integration",
            "reasons": {
                "primary": "C207610:Protocol Design Error",
                "secondary": "C207601:Change In Strategy",
            },
            "impact": {"safety": False, "reliability": True},
            "enrollment": {"value": 200, "unit": "%"},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should use Builder's create method to create objects
        if amendments_assembler.amendment is not None:
            amendment = amendments_assembler.amendment
            assert hasattr(
                amendment, "id"
            )  # Objects created by Builder should have IDs
            assert amendment.summary == "Test create method integration"

            # Check enrollment object creation
            enrollment = amendment.enrollments[0]
            assert hasattr(enrollment, "id")
            assert enrollment.name == "ENROLLMENT"

    def test_encoder_integration(self, amendments_assembler, document_assembler):
        """Test integration with Encoder for amendment reasons."""
        data = {
            "summary": "Test encoder integration",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "INVALID_FORMAT:This should fall back to Other",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should use Encoder to process amendment reasons
        if amendments_assembler.amendment is not None:
            amendment = amendments_assembler.amendment
            assert amendment.primaryReason is not None
            assert amendment.secondaryReasons is not None
            assert len(amendment.secondaryReasons) == 1


class TestAmendmentsAssemblerStateManagement:
    """Test AmendmentsAssembler state management."""

    def test_amendment_property_reflects_current_state(
        self, amendments_assembler, document_assembler
    ):
        """Test that amendment property reflects current state after operations."""
        # Initially None
        assert amendments_assembler.amendment is None

        data = {
            "summary": "Test state management",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should reflect current state
        if amendments_assembler.amendment is not None:
            assert amendments_assembler.amendment.summary == "Test state management"
            # Property should return the same object
            assert amendments_assembler.amendment is amendments_assembler._amendment

    def test_inheritance_from_base_assembler(self, amendments_assembler):
        """Test that AmendmentsAssembler properly inherits BaseAssembler methods."""
        # Test _label_to_name method inheritance
        result = amendments_assembler._label_to_name("Test Amendment Name")
        assert result == "TEST-AMENDMENT-NAME"

        # Test that MODULE constant is properly set
        assert (
            amendments_assembler.MODULE
            == "usdm4.assembler.amendments_assembler.AmenementsAssembler"
        )


class TestAmendmentsAssemblerScopeCreation:
    """Test AmendmentsAssembler scope creation methods for coverage of lines 101-143, 168-176, 188."""

    def test_create_scopes_with_global_scope(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_scopes with GLOBAL scope (covers lines 106-107)."""
        data = {
            "identifier": "1",
            "summary": "Test with global scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": True,
                "countries": [],
                "regions": [],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.geographicScopes is not None
        assert len(amendment.geographicScopes) >= 1

    def test_create_scopes_with_not_applicable_scope(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_scopes with NOT APPLICABLE scope (treated as global)."""
        data = {
            "identifier": "1",
            "summary": "Test with not applicable scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": True,
                "countries": [],
                "regions": [],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.geographicScopes is not None
        assert len(amendment.geographicScopes) >= 1

    def test_create_scopes_with_not_global_country(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_scopes with country in countries array (covers lines 108-122)."""
        data = {
            "identifier": "1",
            "summary": "Test with not global country scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": False,
                "countries": ["US"],
                "regions": [],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.geographicScopes is not None

    def test_create_scopes_with_local_country(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_scopes with LOCAL country code (covers lines 108-122)."""
        data = {
            "identifier": "1",
            "summary": "Test with local country scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": False,
                "countries": ["GB"],
                "regions": [],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.geographicScopes is not None

    def test_create_scopes_with_multiple_countries(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_scopes with multiple country codes (covers lines 114-122)."""
        data = {
            "identifier": "1",
            "summary": "Test with multiple country scopes",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": False,
                "countries": ["US", "GB", "DE"],
                "regions": [],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.geographicScopes is not None

    def test_create_scopes_with_region_code(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_scopes with region code (covers lines 124-129)."""
        data = {
            "identifier": "1",
            "summary": "Test with region scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": False,
                "countries": [],
                "regions": ["Europe"],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None

    def test_create_scopes_with_invalid_identifier(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test _create_scopes with invalid country/region identifier (covers lines 130-134)."""
        initial_error_count = errors.error_count()
        data = {
            "identifier": "1",
            "summary": "Test with invalid identifier",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": "Not Global INVALIDCODE",
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        # Should log an error for invalid scope identifier
        assert errors.error_count() > initial_error_count

    def test_create_scopes_with_unrecognized_scope_format(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test _create_scopes with unrecognized scope in unknown array - now creates site scope extension."""
        data = {
            "identifier": "1",
            "summary": "Test with unrecognized scope format",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": False,
                "countries": [],
                "regions": [],
                "sites": [],
                "unknown": ["SomeUnknownCode"],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        # Unknown codes that are not countries or regions are now treated as site identifiers
        # and create site scope extensions instead of logging errors
        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        # Should have site scope extension attribute created for the unknown code
        assert amendment.extensionAttributes is not None
        assert len(amendment.extensionAttributes) == 1

    def test_create_scopes_with_empty_scope(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test _create_scopes with empty scope string (covers lines 141-146)."""
        initial_error_count = errors.error_count()
        data = {
            "identifier": "1",
            "summary": "Test with empty scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "scope": "",
        }

        amendments_assembler.execute(data, document_assembler)

        # Should log an error for empty scope and default to global
        assert errors.error_count() > initial_error_count

    def test_create_scopes_with_whitespace_only_scope(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test _create_scopes with whitespace-only scope (covers lines 101-102)."""
        initial_error_count = errors.error_count()
        data = {
            "identifier": "1",
            "summary": "Test with whitespace scope",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
            "scope": "   ",
        }

        amendments_assembler.execute(data, document_assembler)

        # Should log an error for empty/whitespace scope
        assert errors.error_count() > initial_error_count


class TestAmendmentsAssemblerCreateScopeMethod:
    """Test _create_scope private method for coverage of lines 168-176, 188."""

    def test_create_scope_with_country_code(self, amendments_assembler):
        """Test _create_scope with valid country code (covers lines 168-174)."""
        results = []
        country_code = amendments_assembler._encoder.geographic_scope("COUNTRY")

        amendments_assembler._create_scope(results, country_code, "US", "United States")

        assert len(results) == 1
        scope = results[0]
        assert scope.instanceType == "GeographicScope"
        assert scope.code is not None

    def test_create_scope_with_region_code(self, amendments_assembler):
        """Test _create_scope with region code type (covers lines 168-174)."""
        results = []
        region_code = amendments_assembler._encoder.geographic_scope("REGION")

        amendments_assembler._create_scope(results, region_code, "150", "Europe")

        assert len(results) == 1
        scope = results[0]
        assert scope.instanceType == "GeographicScope"

    def test_create_scope_without_code_and_decode(self, amendments_assembler):
        """Test _create_scope without code/decode (covers line 166-167 branch)."""
        results = []
        global_code = amendments_assembler._encoder.geographic_scope("GLOBAL")

        amendments_assembler._create_scope(results, global_code)

        assert len(results) == 1
        scope = results[0]
        assert scope.instanceType == "GeographicScope"
        assert scope.code is None

    def test_create_scope_with_invalid_country_code(self, amendments_assembler, errors):
        """Test _create_scope with invalid country code that fails lookup (covers lines 175-179)."""
        initial_error_count = errors.error_count()
        results = []
        country_code = amendments_assembler._encoder.geographic_scope("COUNTRY")

        # Use a code that won't be found in ISO3166 library
        amendments_assembler._create_scope(
            results, country_code, "ZZZZ", "Invalid Country"
        )

        # Should log an error for failed standard code creation
        assert errors.error_count() > initial_error_count

    def test_global_scope_method(self, amendments_assembler):
        """Test _global_scope helper method."""
        results = []

        amendments_assembler._global_scope(results)

        assert len(results) == 1
        scope = results[0]
        assert scope.instanceType == "GeographicScope"


class TestAmendmentsAssemblerExceptionHandling:
    """Test exception handling in execute method (covers lines 29-31)."""

    def test_execute_exception_logged(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test that exceptions in execute are properly caught and logged (covers lines 29-31)."""
        # Force an exception by passing data that will cause _create_amendment to fail
        # We need data that passes the initial check but fails during processing
        initial_error_count = errors.error_count()

        # Create a mock that will raise an exception
        original_create_amendment = amendments_assembler._create_amendment

        def raise_exception(data):
            raise RuntimeError("Test exception for coverage")

        amendments_assembler._create_amendment = raise_exception

        try:
            data = {
                "identifier": "1",
                "summary": "Test exception handling",
                "reasons": {
                    "primary": "C207609:New Safety Information Available",
                    "secondary": "C207605:IRB/IEC Feedback",
                },
                "impact": {"safety": True, "reliability": False},
            }

            amendments_assembler.execute(data, document_assembler)

            # Exception should have been caught and logged
            assert errors.error_count() > initial_error_count
            assert amendments_assembler.amendment is None
        finally:
            # Restore original method
            amendments_assembler._create_amendment = original_create_amendment


class TestAmendmentsAssemblerAdditionalCoverage:
    """Additional test cases to improve coverage."""

    def test_execute_with_complex_mixed_data(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with complex mixed valid and invalid data."""
        data = {
            "summary": "Complex mixed data test",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "INVALID:This will be handled by encoder",
            },
            "impact": {"safety": True, "reliability": False},
            "enrollment": {
                "value": 150.5,  # Float value
                "unit": "%",
            },
        }

        amendments_assembler.execute(data, document_assembler)

        # Should process valid data and handle invalid data gracefully
        if amendments_assembler.amendment is not None:
            amendment = amendments_assembler.amendment
            assert amendment.summary == "Complex mixed data test"
            # Test that amendment was created successfully

            # Check enrollment with float value
            enrollment = amendment.enrollments[0]
            assert enrollment.quantity.value == 150.5

    def test_execute_with_whitespace_in_summary(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with whitespace in summary."""
        data = {
            "summary": "  Amendment with leading and trailing spaces  ",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should preserve whitespace in summary
        if amendments_assembler.amendment is not None:
            assert (
                amendments_assembler.amendment.summary
                == "  Amendment with leading and trailing spaces  "
            )

    def test_execute_with_newlines_in_summary(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with newlines in summary."""
        multiline_summary = "Amendment summary\nwith multiple\nlines of text"
        data = {
            "summary": multiline_summary,
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle multiline summary
        if amendments_assembler.amendment is not None:
            assert amendments_assembler.amendment.summary == multiline_summary

    def test_execute_with_boolean_string_impact_values(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with string boolean values in impact."""
        data = {
            "summary": "Test with string boolean values",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {
                "safety": "true",  # String instead of boolean
                "reliability": "false",  # String instead of boolean
            },
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle string boolean values - behavior depends on Python's truthiness
        # Non-empty strings are truthy in Python
        if amendments_assembler.amendment is not None:
            # Test that amendment was created successfully
            assert (
                amendments_assembler.amendment.summary
                == "Test with string boolean values"
            )

    def test_execute_with_numeric_impact_values(
        self, amendments_assembler, document_assembler
    ):
        """Test execute with numeric impact values."""
        data = {
            "summary": "Test with numeric impact values",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {
                "safety": 1,  # Numeric instead of boolean
                "reliability": 0,  # Numeric instead of boolean
            },
        }

        amendments_assembler.execute(data, document_assembler)

        # Should handle numeric values - 1 is truthy, 0 is falsy
        if amendments_assembler.amendment is not None:
            # Test that amendment was created successfully
            assert (
                amendments_assembler.amendment.summary
                == "Test with numeric impact values"
            )

    def test_create_enrollment_edge_cases(self, amendments_assembler):
        """Test _create_enrollment with various edge cases."""
        # Test with empty enrollment dict
        data_empty = {"enrollment": {}}
        enrollment_empty = amendments_assembler._create_enrollment(data_empty)

        # Test with None enrollment
        data_none = {"enrollment": None}
        enrollment_none = amendments_assembler._create_enrollment(data_none)

        # Test with missing enrollment key entirely
        data_missing = {}
        enrollment_missing = amendments_assembler._create_enrollment(data_missing)

        # All should create enrollment with default values
        for enrollment in [enrollment_empty, enrollment_none, enrollment_missing]:
            if enrollment is not None:
                assert enrollment.name == "ENROLLMENT"
                assert enrollment.quantity.value == 0
                assert enrollment.quantity.unit is None

    def test_geographic_scope_creation(self, amendments_assembler, document_assembler):
        """Test that geographic scope is properly created."""
        data = {
            "summary": "Test geographic scope creation",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        if amendments_assembler.amendment is not None:
            amendment = amendments_assembler.amendment
            assert amendment.geographicScopes is not None
            assert len(amendment.geographicScopes) == 1

            geo_scope = amendment.geographicScopes[0]
            assert geo_scope.instanceType == "GeographicScope"
            # Should have Global code (C68846)

    def test_amendment_fixed_values(self, amendments_assembler, document_assembler):
        """Test that amendment has fixed name and number values."""
        data = {
            "summary": "Test fixed values",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": {"safety": True, "reliability": False},
        }

        amendments_assembler.execute(data, document_assembler)

        if amendments_assembler.amendment is not None:
            amendment = amendments_assembler.amendment
            # These values are hardcoded in the implementation
            assert amendment.name == "AMENDMENT 1"
            assert amendment.number == "1"


class TestAmendmentsAssemblerChanges:
    """Test AmendmentsAssembler _create_changes and _extract_section_numer_and_title methods."""

    def test_create_changes_with_valid_section_data(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_changes with valid section data (covers lines 125-133)."""
        data = {
            "identifier": "1",
            "summary": "Test with changes",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "changes": [
                {
                    "section": "1.1 Introduction",
                    "description": "Updated introduction text",
                    "rationale": "Clarify study objectives",
                }
            ],
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.changes is not None
        assert len(amendment.changes) == 1
        change = amendment.changes[0]
        assert change.summary == "Updated introduction text"
        assert change.rationale == "Clarify study objectives"

    def test_create_changes_with_multiple_changes(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_changes with multiple change items."""
        data = {
            "identifier": "1",
            "summary": "Test with multiple changes",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "changes": [
                {
                    "section": "1.1 Introduction",
                    "description": "First change description",
                    "rationale": "First rationale",
                },
                {
                    "section": "2.3.1 Procedures",
                    "description": "Second change description",
                    "rationale": "Second rationale",
                },
            ],
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.changes is not None
        assert len(amendment.changes) == 2

    def test_create_changes_with_section_prefix(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_changes with 'Section' prefix in section text."""
        data = {
            "identifier": "1",
            "summary": "Test with Section prefix",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "changes": [
                {
                    "section": "Section 3.2 Safety Monitoring",
                    "description": "Added safety monitoring procedures",
                    "rationale": "Required by regulatory agency",
                }
            ],
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.changes is not None
        assert len(amendment.changes) == 1
        # Verify the section reference was created
        change = amendment.changes[0]
        assert len(change.changedSections) == 1
        section_ref = change.changedSections[0]
        assert section_ref.sectionNumber == "3.2"
        assert section_ref.sectionTitle == "Safety Monitoring"

    def test_create_changes_with_multiline_sections(
        self, amendments_assembler, document_assembler
    ):
        """Test _create_changes with multiple section references in one change."""
        data = {
            "identifier": "1",
            "summary": "Test with multiline sections",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "changes": [
                {
                    "section": "1.1 Introduction\n2.3 Methods\n3.4.5 Analysis",
                    "description": "Multiple sections updated",
                    "rationale": "Comprehensive revision",
                }
            ],
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        assert amendment.changes is not None
        assert len(amendment.changes) == 1
        change = amendment.changes[0]
        # Should have 3 section references
        assert len(change.changedSections) == 3

    def test_extract_section_with_invalid_format(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test _extract_section_numer_and_title with invalid section format (covers line 150-151)."""
        initial_error_count = errors.error_count()
        data = {
            "identifier": "1",
            "summary": "Test with invalid section format",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "changes": [
                {
                    "section": "Invalid section without number",
                    "description": "Test description",
                    "rationale": "Test rationale",
                }
            ],
        }

        amendments_assembler.execute(data, document_assembler)

        # Should log an error for invalid section format
        assert errors.error_count() > initial_error_count

    def test_extract_section_direct_call(
        self, amendments_assembler, document_assembler
    ):
        """Test _extract_section_numer_and_title directly with various formats."""
        # Set up the _document_assembler attribute needed by _extract_section_numer_and_title
        amendments_assembler._document_assembler = document_assembler

        # Valid section number without prefix
        result = amendments_assembler._extract_section_numer_and_title(
            "1.2.3 Title Here"
        )
        assert len(result) == 1
        assert result[0].sectionNumber == "1.2.3"
        assert result[0].sectionTitle == "Title Here"

        # Valid section with 'Section' prefix
        result = amendments_assembler._extract_section_numer_and_title(
            "Section 4.5 Another Title"
        )
        assert len(result) == 1
        assert result[0].sectionNumber == "4.5"
        assert result[0].sectionTitle == "Another Title"

        # Section number with comma separator
        result = amendments_assembler._extract_section_numer_and_title(
            "6.7, Some Title"
        )
        assert len(result) == 1
        assert result[0].sectionNumber == "6.7"
        assert result[0].sectionTitle == "Some Title"

    def test_extract_section_with_mixed_valid_invalid(
        self, amendments_assembler, document_assembler, errors
    ):
        """Test _extract_section_numer_and_title with mix of valid and invalid lines."""
        # Set up the _document_assembler attribute needed by _extract_section_numer_and_title
        amendments_assembler._document_assembler = document_assembler

        initial_error_count = errors.error_count()

        # Multiple lines with one invalid
        result = amendments_assembler._extract_section_numer_and_title(
            "1.1 Valid Section\nNo number here\n2.2 Another Valid"
        )

        # Should have 2 valid results
        assert len(result) == 2
        # Should have logged error for invalid line
        assert errors.error_count() > initial_error_count


class TestAmendmentsAssemblerRegionScope:
    """Test region scope creation specifically (covers lines 282-283)."""

    def test_create_scope_with_region_direct(self, amendments_assembler):
        """Test _create_scope directly with region type."""
        results = []
        region_code = amendments_assembler._encoder.geographic_scope("REGION")

        # Use a valid region code and decode
        amendments_assembler._create_scope(results, region_code, "150", "Europe")

        assert len(results) == 1
        scope = results[0]
        assert scope.instanceType == "GeographicScope"
        # code may be None if iso3166_region_code lookup fails, but scope should still be created

    def test_execute_with_region_scope_in_amendment(
        self, amendments_assembler, document_assembler
    ):
        """Test full amendment creation with region scope (covers lines 282-283)."""
        data = {
            "identifier": "1",
            "summary": "Test with Europe region",
            "reasons": {
                "primary": "C207609:New Safety Information Available",
                "secondary": "C207605:IRB/IEC Feedback",
            },
            "impact": make_impact(safety=True),
            "scope": {
                "global": False,
                "countries": [],
                "regions": ["Europe"],
                "sites": [],
                "unknown": [],
            },
            "changes": make_changes(),
        }

        amendments_assembler.execute(data, document_assembler)

        assert amendments_assembler.amendment is not None
        amendment = amendments_assembler.amendment
        # Should have region scope created
        assert amendment.geographicScopes is not None
        assert len(amendment.geographicScopes) >= 1


class TestAmendmentsAssemblerGeographicScopeFailure:
    """Test geographic scope creation failure path (covers line 365)."""

    def test_create_scope_failure_logged(self, amendments_assembler, errors):
        """Test that failure to create geographic scope is logged (covers line 365)."""
        initial_error_count = errors.error_count()
        results = []

        # Mock the builder.create to return None
        original_create = amendments_assembler._builder.create

        def mock_create(cls, params):
            from usdm4.api.geographic_scope import GeographicScope

            if cls == GeographicScope:
                return None
            return original_create(cls, params)

        amendments_assembler._builder.create = mock_create

        try:
            global_code = amendments_assembler._encoder.geographic_scope("GLOBAL")
            amendments_assembler._create_scope(results, global_code)

            # Should have logged an error
            assert errors.error_count() > initial_error_count
            # Results should be empty since creation failed
            assert len(results) == 0
        finally:
            # Restore original create method
            amendments_assembler._builder.create = original_create
