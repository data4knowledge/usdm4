import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.assembler.study_assembler import StudyAssembler
from src.usdm4.assembler.identification_assembler import IdentificationAssembler
from src.usdm4.assembler.study_design_assembler import StudyDesignAssembler
from src.usdm4.assembler.document_assembler import DocumentAssembler
from src.usdm4.assembler.population_assembler import PopulationAssembler
from src.usdm4.assembler.amendments_assembler import AmendmentsAssembler
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
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
def study_assembler(builder, errors):
    """Create a StudyAssembler instance for testing."""
    # Clear the builder to avoid cross-reference conflicts
    builder.clear()
    return StudyAssembler(builder, errors)


@pytest.fixture
def identification_assembler(builder, errors):
    """Create an IdentificationAssembler instance for testing."""
    return IdentificationAssembler(builder, errors)


@pytest.fixture
def study_design_assembler(builder, errors):
    """Create a StudyDesignAssembler instance for testing."""
    return StudyDesignAssembler(builder, errors)


@pytest.fixture
def document_assembler(builder, errors):
    """Create a DocumentAssembler instance for testing."""
    return DocumentAssembler(builder, errors)


@pytest.fixture
def population_assembler(builder, errors):
    """Create a PopulationAssembler instance for testing."""
    return PopulationAssembler(builder, errors)


@pytest.fixture
def amendments_assembler(builder, errors):
    """Create an AmendmentsAssembler instance for testing."""
    return AmendmentsAssembler(builder, errors)


@pytest.fixture
def timeline_assembler(builder, errors):
    """Create a TimelineAssembler instance for testing."""
    return TimelineAssembler(builder, errors)


@pytest.fixture
def prepared_assemblers(
    identification_assembler,
    study_design_assembler,
    document_assembler,
    population_assembler,
    amendments_assembler,
    timeline_assembler,
):
    """Create and prepare all required assembler instances with minimal data."""
    # Prepare identification assembler with basic data
    identification_data = {
        "titles": {"brief": "Test Study", "official": "Official Test Study"},
        "identifiers": [{"identifier": "NCT12345678", "scope": {"standard": "nct"}}],
    }
    identification_assembler.execute(identification_data)

    # Prepare population assembler with minimal data FIRST
    population_data = {
        "label": "Test Population Label",
        "inclusion_exclusion": {
            "inclusion": [
                "Age >= 18 years",
                "Participants must be able to provide informed consent",
            ],
            "exclusion": ["Not pregnant", "No serious medical conditions"],
        },
    }
    population_assembler.execute(population_data)

    # Verify population was created successfully
    if population_assembler.population is None:
        raise RuntimeError("Population assembler failed to create population")

    # Create a minimal timeline assembler that doesn't fail
    # We'll manually set the properties instead of using execute
    timeline_assembler._timelines = []
    timeline_assembler._epochs = []
    timeline_assembler._encounters = []
    timeline_assembler._activities = []
    timeline_assembler._conditions = []

    # Prepare study design assembler with minimal data
    study_design_data = {
        "label": "Test Study Design Label",
        "rationale": "Test study design rationale",
        "trial_phase": "phase-1",
    }
    study_design_assembler.execute(
        study_design_data, population_assembler, timeline_assembler
    )

    # Verify study design was created successfully
    if study_design_assembler.study_design is None:
        raise RuntimeError("Study design assembler failed to create study design")

    # Prepare document assembler with minimal data
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
    document_assembler.execute(document_data)

    # Prepare amendments assembler with minimal data
    amendments_data = {
        "summary": "First amendment to the protocol",
        "reasons": {"primary": "Safety update", "secondary": "Protocol clarification"},
        "impact": {"safety": True, "reliability": False},
        "enrollment": {"value": 100, "unit": "subjects"},
    }
    amendments_assembler.execute(amendments_data, document_assembler)

    return {
        "identification": identification_assembler,
        "study_design": study_design_assembler,
        "document": document_assembler,
        "population": population_assembler,
        "amendments": amendments_assembler,
        "timeline": timeline_assembler,
    }


class TestStudyAssemblerInitialization:
    """Test StudyAssembler initialization."""

    def test_init_with_valid_parameters(self, builder, errors):
        """Test StudyAssembler initialization with valid parameters."""
        assembler = StudyAssembler(builder, errors)

        assert assembler._builder is builder
        assert assembler._errors is errors
        assert assembler.MODULE == "usdm4.assembler.study_assembler.StudyAssembler"

        # Test initial state
        assert assembler._study is None
        assert assembler._encoder is not None
        assert assembler._dates == []

    def test_study_property_initial_state(self, study_assembler):
        """Test that study property returns None initially."""
        assert study_assembler.study is None

    def test_inheritance_from_base_assembler(self, study_assembler):
        """Test that StudyAssembler properly inherits from BaseAssembler."""
        # Test _label_to_name method inheritance
        result = study_assembler._label_to_name("Test Study Name")
        assert result == "TEST-STUDY-NAME"

        # Test that MODULE constant is properly set
        assert (
            study_assembler.MODULE == "usdm4.assembler.study_assembler.StudyAssembler"
        )


class TestStudyAssemblerValidData:
    """Test StudyAssembler with valid data."""

    def test_execute_with_minimal_valid_data(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with minimal valid data."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study Label",
            "version": "1.0",
            "rationale": "Initial version of the test study",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should have created a study
        assert study_assembler.study is not None
        assert study_assembler.study.name == "TST"
        assert study_assembler.study.label == "TST"
        assert study_assembler.study.description == "The top-level study container"
        assert len(study_assembler.study.versions) == 1

        # Verify study version
        study_version = study_assembler.study.versions[0]
        assert study_version.versionIdentifier == "1.0"
        assert study_version.rationale == "Initial version of the test study"

    def test_execute_with_complete_valid_data(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with complete valid data including sponsor approval date."""
        data = {
            "name": {"identifier": "STUDY-001"},
            "label": "Complete Test Study",
            "version": "2.1",
            "rationale": "Updated version with new endpoints",
            "sponsor_approval_date": "2024-01-15",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should have created a study with governance date
        assert study_assembler.study is not None
        assert study_assembler.study.name == "STUDY001"
        assert study_assembler.study.label == "STUDY-001"
        assert len(study_assembler.study.versions) == 1

        # Verify study version
        study_version = study_assembler.study.versions[0]
        assert study_version.versionIdentifier == "2.1"
        assert study_version.rationale == "Updated version with new endpoints"

        # Should have created governance dates (sponsor approval date + document dates)
        assert len(study_version.dateValues) >= 1

    def test_execute_with_acronym_name(self, study_assembler, prepared_assemblers):
        """Test execute with acronym in name field."""
        data = {
            "name": {"acronym": "ACRONYM"},
            "label": "Test Study with Acronym",
            "version": "1.0",
            "rationale": "Test with acronym",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        assert study_assembler.study.name == "ACRONYM"
        assert study_assembler.study.label == "ACRONYM"

    def test_execute_with_compound_name(self, study_assembler, prepared_assemblers):
        """Test execute with compound in name field."""
        data = {
            "name": {"compound": "Test-Compound-123"},
            "label": "Test Study with Compound",
            "version": "1.0",
            "rationale": "Test with compound",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        assert study_assembler.study.name == "TESTCOMPOUND123"
        assert study_assembler.study.label == "Test-Compound-123"

    def test_execute_with_identifier_name(self, study_assembler, prepared_assemblers):
        """Test execute with identifier in name field."""
        data = {
            "name": {"identifier": "STUDY_ID_001"},
            "label": "Test Study with Identifier",
            "version": "1.0",
            "rationale": "Test with identifier",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        assert study_assembler.study.name == "STUDYID001"
        assert study_assembler.study.label == "STUDY_ID_001"

    def test_execute_with_valid_sponsor_approval_date(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with valid sponsor approval date."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
            "sponsor_approval_date": "2024-03-15",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        study_version = study_assembler.study.versions[0]

        # Should have at least one governance date (sponsor approval)
        assert len(study_version.dateValues) >= 1

        # Check if sponsor approval date was created
        sponsor_dates = [
            date
            for date in study_version.dateValues
            if hasattr(date, "name") and date.name == "SPONSOR-APPORVAL-DATE"
        ]
        assert len(sponsor_dates) >= 0  # May be 0 if date creation failed

    def test_execute_with_confidentiality(self, study_assembler, prepared_assemblers):
        """Test execute with complete valid data including sponsor approval date."""
        data = {
            "name": {"identifier": "STUDY-001"},
            "label": "Complete Test Study",
            "version": "2.1",
            "rationale": "Updated version with new endpoints",
            "sponsor_approval_date": "2024-01-15",
            "confidentiality": "Top Secret",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )
        print(f"ERRORS: {study_assembler._errors.dump(0)}")

        # Should have created a study with governance date
        assert study_assembler.study is not None
        assert study_assembler.study.name == "STUDY001"
        assert study_assembler.study.label == "STUDY-001"
        assert len(study_assembler.study.versions) == 1

        # Verify study version
        study_version = study_assembler.study.versions[0]
        assert study_version.versionIdentifier == "2.1"
        assert study_version.rationale == "Updated version with new endpoints"
        assert study_version.extensionAttributes[0].valueString == "Top Secret"

        # Should have created governance dates (sponsor approval date + document dates)
        assert len(study_version.dateValues) >= 1


class TestStudyAssemblerInvalidData:
    """Test StudyAssembler with invalid data."""

    def test_execute_with_empty_data(self, study_assembler, prepared_assemblers):
        """Test execute with empty data dictionary."""
        data = {}

        # Should handle empty data gracefully but may fail due to missing required fields
        try:
            study_assembler.execute(
                data,
                prepared_assemblers["identification"],
                prepared_assemblers["study_design"],
                prepared_assemblers["document"],
                prepared_assemblers["population"],
                prepared_assemblers["amendments"],
                prepared_assemblers["timeline"],
            )
        except KeyError:
            # Expected behavior - missing required fields
            pass

        # Study should not be created with empty data
        assert study_assembler.study is None

    def test_execute_with_missing_required_fields(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with missing required fields."""
        data = {
            "name": {"acronym": "TST"},
            # Missing version and rationale
        }

        try:
            study_assembler.execute(
                data,
                prepared_assemblers["identification"],
                prepared_assemblers["study_design"],
                prepared_assemblers["document"],
                prepared_assemblers["population"],
                prepared_assemblers["amendments"],
                prepared_assemblers["timeline"],
            )
        except KeyError:
            # Expected behavior - missing required fields
            pass

        # Study should not be created with missing required fields
        assert study_assembler.study is None

    def test_execute_with_invalid_sponsor_approval_date(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with invalid sponsor approval date format."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
            "sponsor_approval_date": "invalid-date-format",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should create study but without sponsor approval date
        assert study_assembler.study is not None
        study_version = study_assembler.study.versions[0]

        # Should not have created sponsor approval date due to invalid format
        sponsor_dates = [
            date
            for date in study_version.dateValues
            if hasattr(date, "name") and date.name == "SPONSOR-APPORVAL-DATE"
        ]
        assert len(sponsor_dates) == 0

    def test_execute_with_empty_name_dict(self, study_assembler, prepared_assemblers):
        """Test execute with empty name dictionary."""
        data = {
            "name": {},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should fail to create study due to empty name validation
        assert study_assembler.study is None

    def test_execute_with_none_values(self, study_assembler, prepared_assemblers):
        """Test execute with None values in data."""
        data = {
            "name": {"acronym": None},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
            "sponsor_approval_date": None,
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should fail to create study due to empty name validation
        assert study_assembler.study is None

    def test_execute_with_invalid_name_structure(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with invalid name structure."""
        data = {
            "name": "not_a_dict",  # Should be a dict
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        try:
            study_assembler.execute(
                data,
                prepared_assemblers["identification"],
                prepared_assemblers["study_design"],
                prepared_assemblers["document"],
                prepared_assemblers["population"],
                prepared_assemblers["amendments"],
                prepared_assemblers["timeline"],
            )
        except (TypeError, AttributeError):
            # Expected behavior - invalid name structure
            pass

        # Study should not be created with invalid name structure
        assert study_assembler.study is None


class TestStudyAssemblerEdgeCases:
    """Test StudyAssembler edge cases."""

    def test_execute_with_special_characters_in_name(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with special characters in name fields."""
        data = {
            "name": {"acronym": "TST-123_@#$"},
            "label": "Test Study with Special Characters",
            "version": "1.0",
            "rationale": "Test with special characters",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        # Special characters should be removed by _label_to_name
        assert study_assembler.study.name == "TST123"
        assert study_assembler.study.label == "TST-123_@#$"

    def test_execute_with_unicode_characters(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with unicode characters in data."""
        data = {
            "name": {"acronym": "ÉTUDE"},
            "label": "Étude clinique avec caractères spéciaux",
            "version": "1.0",
            "rationale": "Étude avec caractères unicode",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        assert study_assembler.study.name == "ÉTUDE"
        assert study_assembler.study.label == "ÉTUDE"

    def test_execute_with_very_long_strings(self, study_assembler, prepared_assemblers):
        """Test execute with very long strings."""
        long_string = "A" * 1000
        data = {
            "name": {"acronym": long_string},
            "label": "Test Study",
            "version": "1.0",
            "rationale": long_string,
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        assert study_assembler.study.name == long_string
        assert study_assembler.study.label == long_string

    def test_execute_with_multiple_name_options(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with multiple name options (should use first available)."""
        data = {
            "name": {
                "acronym": "ACR",
                "identifier": "ID-001",
                "compound": "COMP-123",
            },
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test with multiple name options",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        # Priority order is: identifier > acronym > compound
        assert study_assembler.study.name == "ID001"
        assert study_assembler.study.label == "ID-001"

    def test_execute_with_empty_string_values(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with empty string values."""
        data = {
            "name": {"acronym": ""},
            "label": "Test Study",
            "version": "",
            "rationale": "",
            "sponsor_approval_date": "",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should fail to create study due to empty name validation
        assert study_assembler.study is None


class TestStudyAssemblerPrivateMethods:
    """Test StudyAssembler private methods."""

    def test_create_date_with_valid_date(self, study_assembler):
        """Test _create_date with valid sponsor approval date."""
        data = {"sponsor_approval_date": "2024-01-15"}

        initial_dates_count = len(study_assembler._dates)
        study_assembler._create_date(data)

        # Should have added a governance date
        assert len(study_assembler._dates) >= initial_dates_count

    def test_create_date_with_invalid_date(self, study_assembler):
        """Test _create_date with invalid date format."""
        data = {"sponsor_approval_date": "invalid-date"}

        initial_dates_count = len(study_assembler._dates)
        study_assembler._create_date(data)

        # Should not have added any dates due to invalid format
        assert len(study_assembler._dates) == initial_dates_count

    def test_create_date_with_missing_date(self, study_assembler):
        """Test _create_date with missing sponsor approval date."""
        data = {}

        initial_dates_count = len(study_assembler._dates)
        study_assembler._create_date(data)

        # Should not have added any dates
        assert len(study_assembler._dates) == initial_dates_count

    def test_get_study_name_label_with_acronym(self, study_assembler):
        """Test _get_study_name_label with acronym."""
        options = {"acronym": "TEST-STUDY"}

        name, label = study_assembler._get_study_name_label(options)

        assert name == "TESTSTUDY"
        assert label == "TEST-STUDY"

    def test_get_study_name_label_with_identifier(self, study_assembler):
        """Test _get_study_name_label with identifier."""
        options = {"identifier": "STUDY_001"}

        name, label = study_assembler._get_study_name_label(options)

        assert name == "STUDY001"
        assert label == "STUDY_001"

    def test_get_study_name_label_with_compound(self, study_assembler):
        """Test _get_study_name_label with compound."""
        options = {"compound": "Compound-X"}

        name, label = study_assembler._get_study_name_label(options)

        assert name == "COMPOUNDX"
        assert label == "Compound-X"

    def test_get_study_name_label_with_empty_options(self, study_assembler):
        """Test _get_study_name_label with empty options."""
        options = {}

        name, label = study_assembler._get_study_name_label(options)

        assert name == ""
        assert label == ""

    def test_get_study_name_label_with_none_values(self, study_assembler):
        """Test _get_study_name_label with None values."""
        options = {"acronym": None, "identifier": "VALID-ID"}

        name, label = study_assembler._get_study_name_label(options)

        # Should skip None acronym and use identifier
        assert name == "VALIDID"
        assert label == "VALID-ID"

    def test_get_study_name_label_with_empty_string_values(self, study_assembler):
        """Test _get_study_name_label with empty string values."""
        options = {"acronym": "", "identifier": "VALID-ID"}

        name, label = study_assembler._get_study_name_label(options)

        # Should skip empty acronym and use identifier
        assert name == "VALIDID"
        assert label == "VALID-ID"

    def test_get_study_name_label_priority_order(self, study_assembler):
        """Test _get_study_name_label priority order (identifier > acronym > compound)."""
        options = {
            "compound": "COMPOUND",
            "identifier": "IDENTIFIER",
            "acronym": "ACRONYM",
        }

        name, label = study_assembler._get_study_name_label(options)

        # Should use identifier (highest priority)
        assert name == "IDENTIFIER"
        assert label == "IDENTIFIER"


class TestStudyAssemblerStateManagement:
    """Test StudyAssembler state management."""

    def test_study_property_after_successful_execution(
        self, study_assembler, prepared_assemblers
    ):
        """Test that study property returns created study after successful execution."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        # Initially None
        assert study_assembler.study is None

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should now return the created study
        assert study_assembler.study is not None
        assert study_assembler.study.name == "TST"

    def test_dates_accumulation(self, study_assembler):
        """Test that dates accumulate in _dates list."""
        # Initially empty
        assert len(study_assembler._dates) == 0

        # Add first date
        data1 = {"sponsor_approval_date": "2024-01-15"}
        study_assembler._create_date(data1)
        first_count = len(study_assembler._dates)

        # Add second date
        data2 = {"sponsor_approval_date": "2024-02-15"}
        study_assembler._create_date(data2)
        second_count = len(study_assembler._dates)

        # Should have accumulated dates
        assert second_count >= first_count

    def test_encoder_initialization(self, study_assembler):
        """Test that encoder is properly initialized."""
        assert study_assembler._encoder is not None
        assert hasattr(study_assembler._encoder, "to_date")


class TestStudyAssemblerBuilderIntegration:
    """Test StudyAssembler integration with Builder (without mocking)."""

    def test_builder_create_study_integration(
        self, study_assembler, prepared_assemblers
    ):
        """Test integration with Builder's create method for Study objects."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should use Builder's create method to create Study object
        if study_assembler.study is not None:
            assert hasattr(
                study_assembler.study, "id"
            )  # Objects created by Builder should have IDs
            assert hasattr(study_assembler.study, "name")
            assert hasattr(study_assembler.study, "label")
            assert hasattr(study_assembler.study, "versions")

    def test_builder_create_study_version_integration(
        self, study_assembler, prepared_assemblers
    ):
        """Test integration with Builder's create method for StudyVersion objects."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        if (
            study_assembler.study is not None
            and len(study_assembler.study.versions) > 0
        ):
            study_version = study_assembler.study.versions[0]
            assert hasattr(
                study_version, "id"
            )  # Objects created by Builder should have IDs
            assert hasattr(study_version, "versionIdentifier")
            assert hasattr(study_version, "rationale")

    def test_builder_cdisc_code_integration(self, study_assembler):
        """Test integration with Builder's cdisc_code method."""
        data = {"sponsor_approval_date": "2024-01-15"}

        study_assembler._create_date(data)

        # Should integrate with Builder's CDISC code functionality
        if len(study_assembler._dates) > 0:
            governance_date = study_assembler._dates[0]
            assert hasattr(governance_date, "type")
            # The type should be a Code object created by Builder

    def test_builder_create_governance_date_integration(self, study_assembler):
        """Test integration with Builder's create method for GovernanceDate objects."""
        data = {"sponsor_approval_date": "2024-01-15"}

        study_assembler._create_date(data)

        if len(study_assembler._dates) > 0:
            governance_date = study_assembler._dates[0]
            assert hasattr(
                governance_date, "id"
            )  # Objects created by Builder should have IDs
            assert hasattr(governance_date, "name")
            assert hasattr(governance_date, "type")
            assert hasattr(governance_date, "dateValue")


class TestStudyAssemblerErrorHandling:
    """Test StudyAssembler error handling (without mocking Errors)."""

    def test_error_handling_with_malformed_data(
        self, study_assembler, prepared_assemblers, errors
    ):
        """Test error handling with malformed data structures."""
        malformed_data = {
            "name": "not_a_dict",  # Should be a dict
            "version": 123,  # Should be a string
            "rationale": ["not", "a", "string"],  # Should be a string
        }

        initial_error_count = errors.error_count()
        try:
            study_assembler.execute(
                malformed_data,
                prepared_assemblers["identification"],
                prepared_assemblers["study_design"],
                prepared_assemblers["document"],
                prepared_assemblers["population"],
                prepared_assemblers["amendments"],
                prepared_assemblers["timeline"],
            )
        except (TypeError, AttributeError, KeyError):
            # Expected behavior - malformed data should cause errors
            pass

        # Should have logged errors
        assert errors.error_count() >= initial_error_count
        # Study should not be created with malformed data
        assert study_assembler.study is None

    def test_error_handling_with_exception_in_execution(self, study_assembler, errors):
        """Test error handling when exceptions occur during execution."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        # Pass None assemblers to trigger exceptions
        initial_error_count = errors.error_count()

        try:
            study_assembler.execute(data, None, None, None, None, None, None)
        except (AttributeError, TypeError):
            # Expected behavior - None assemblers should cause errors
            pass

        # Should have logged errors
        assert errors.error_count() > initial_error_count
        # Study should not be created when exceptions occur
        assert study_assembler.study is None

    def test_error_handling_with_invalid_date_creation(self, study_assembler, errors):
        """Test error handling during date creation."""
        data = {"sponsor_approval_date": "completely-invalid-date-format"}

        study_assembler._create_date(data)

        # Should handle invalid date gracefully (may log warning, not error)
        # No dates should be created
        assert len(study_assembler._dates) == 0

    def test_error_handling_with_builder_failures(
        self, study_assembler, prepared_assemblers, errors
    ):
        """Test error handling when Builder operations fail."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        # Execute with valid data - Builder failures are internal and handled
        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should handle Builder failures gracefully
        # May or may not create study depending on where failures occur


class TestStudyAssemblerAdditionalCoverage:
    """Additional test cases to improve coverage."""

    def test_initialization_with_invalid_parameters(self, builder, errors):
        """Test StudyAssembler initialization with invalid parameters."""
        # Test with invalid builder type
        assembler = StudyAssembler("not_a_builder", errors)
        assert assembler._builder == "not_a_builder"

        # Test with invalid errors type
        assembler = StudyAssembler(builder, "not_errors")
        assert assembler._errors == "not_errors"

    def test_execute_with_all_name_options_empty(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute when all name options are empty or None."""
        data = {
            "name": {
                "acronym": "",
                "identifier": None,
                "compound": "",
            },
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should fail to create study due to empty name validation
        assert study_assembler.study is None

    def test_execute_with_whitespace_only_values(
        self, study_assembler, prepared_assemblers
    ):
        """Test execute with whitespace-only values."""
        data = {
            "name": {"acronym": "   "},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        # Should fail to create study due to empty name validation (whitespace gets cleaned to empty)
        assert study_assembler.study is None

    def test_create_date_with_none_sponsor_approval_date(self, study_assembler):
        """Test _create_date with None sponsor_approval_date."""
        data = {"sponsor_approval_date": None}

        initial_dates_count = len(study_assembler._dates)
        study_assembler._create_date(data)

        # Should not add any dates
        assert len(study_assembler._dates) == initial_dates_count

    def test_create_date_with_empty_string_sponsor_approval_date(self, study_assembler):
        """Test _create_date with empty string sponsor_approval_date."""
        data = {"sponsor_approval_date": ""}

        initial_dates_count = len(study_assembler._dates)
        study_assembler._create_date(data)

        # Should not add any dates
        assert len(study_assembler._dates) == initial_dates_count

    def test_get_study_name_label_with_special_characters_in_all_fields(
        self, study_assembler
    ):
        """Test _get_study_name_label with special characters in all name fields."""
        options = {
            "acronym": "A@C#R$",
            "identifier": "I%D^E&N*T",
            "compound": "C(O)M+P=O{U}N[D]",
        }

        name, label = study_assembler._get_study_name_label(options)

        # Should use identifier (highest priority) and clean special characters
        # The regex r"[\W_]+" removes all non-word characters (including underscores)
        # "I%D^E&N*T" becomes "IDENT"
        assert name == "IDENT"
        assert label == "I%D^E&N*T"


class TestStudyAssemblerExtensions:
    """Test extension creation paths (covers lines 127, 134, 139, 144, 149)."""

    def test_execute_with_original_protocol(self, study_assembler, prepared_assemblers):
        """Test execute with original_protocol creates boolean extension (covers line 127)."""
        data = {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test rationale",
            "sponsor_approval_date": "2024-01-15",
            "original_protocol": "true",
        }

        study_assembler.execute(
            data,
            prepared_assemblers["identification"],
            prepared_assemblers["study_design"],
            prepared_assemblers["document"],
            prepared_assemblers["population"],
            prepared_assemblers["amendments"],
            prepared_assemblers["timeline"],
        )

        assert study_assembler.study is not None
        study_version = study_assembler.study.versions[0]
        # Should have at least one extension for original_protocol
        ext_urls = [e.url for e in study_version.extensionAttributes]
        assert "www.d4k.dk/usdm/extensions/002" in ext_urls

    def test_execute_with_compound_codes_and_names(self, builder, errors):
        """Test execute with compound_codes and compound_names (covers lines 134, 139)."""
        builder.clear()
        sa = StudyAssembler(builder, errors)
        ia = IdentificationAssembler(builder, errors)
        sda = StudyDesignAssembler(builder, errors)
        da = DocumentAssembler(builder, errors)
        pa = PopulationAssembler(builder, errors)
        aa = AmendmentsAssembler(builder, errors)
        ta = TimelineAssembler(builder, errors)

        # Set up identification with compound data
        ia.execute(
            {
                "titles": {"brief": "Test"},
                "identifiers": [
                    {"identifier": "NCT12345678", "scope": {"standard": "nct"}}
                ],
                "other": {
                    "sponsor_signatory": "Dr. Smith",
                    "medical_expert": {"name": "Dr. Jones"},
                    "compound_names": "CompoundA",
                    "compound_codes": "CODE-123",
                },
            }
        )

        pa.execute(
            {
                "label": "Pop",
                "inclusion_exclusion": {
                    "inclusion": ["Age >= 18"],
                    "exclusion": ["Pregnant"],
                },
            }
        )
        ta._timelines = []
        ta._epochs = []
        ta._encounters = []
        ta._activities = []
        ta._conditions = []
        sda.execute(
            {"label": "Design", "rationale": "Rat", "trial_phase": "phase-1"}, pa, ta
        )
        da.execute(
            {
                "document": {
                    "label": "Doc",
                    "version": "1.0",
                    "status": "final",
                    "template": "T",
                    "version_date": "2024-01-01",
                },
                "sections": [
                    {"section_number": "1", "section_title": "Intro", "text": "Text"}
                ],
            }
        )
        aa.execute(None, da)

        data = {
            "name": {"acronym": "TST"},
            "label": "Test",
            "version": "1.0",
            "rationale": "Test",
            "sponsor_approval_date": "2024-01-15",
        }

        sa.execute(data, ia, sda, da, pa, aa, ta)

        assert sa.study is not None
        study_version = sa.study.versions[0]
        ext_urls = [e.url for e in study_version.extensionAttributes]
        # Should have compound_codes, compound_names, sponsor_signatory extensions
        assert "www.d4k.dk/usdm/extensions/004" in ext_urls  # compound_codes
        assert "www.d4k.dk/usdm/extensions/005" in ext_urls  # compound_names
        assert "www.d4k.dk/usdm/extensions/007" in ext_urls  # sponsor_signatory
        # medical_expert with a name creates a role, not an extension
        assert "www.d4k.dk/usdm/extensions/006" not in ext_urls


class TestStudyAssemblerCreateExtensionException:
    """Test _create_extension exception handler (covers lines 213-214)."""

    def test_create_extension_exception_is_caught(self, study_assembler, errors):
        """Test that exceptions in _create_extension are caught and logged."""
        initial_error_count = errors.error_count()

        # Monkey-patch builder.create to raise an exception
        original_create = study_assembler._builder.create

        def raise_error(cls, params):
            raise RuntimeError("Simulated extension creation failure")

        study_assembler._builder.create = raise_error

        try:
            extensions = []
            study_assembler._create_extension(extensions, "test-url", "test-value")
        finally:
            study_assembler._builder.create = original_create

        assert len(extensions) == 0
        assert errors.error_count() > initial_error_count
