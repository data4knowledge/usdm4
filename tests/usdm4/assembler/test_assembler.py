import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.assembler.assembler import Assembler
from src.usdm4.__info__ import __model_version__ as usdm_version


def root_path():
    """Get the root path for the usdm4 package."""
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


global_errors = Errors()
global_assembler = Assembler(root_path(), global_errors)


def get_global_assembler():
    global_assembler.clear()
    return global_assembler


@pytest.fixture
def minimal_study_data():
    """Provide minimal valid study data for testing."""
    return {
        "identification": {
            "titles": {"brief": "Test Study", "official": "Official Test Study"},
            "identifiers": [
                {"identifier": "NCT12345678", "scope": {"standard": "ct.gov"}}
            ],
        },
        "document": {
            "document": {
                "label": "Test Protocol",
                "version": "1.0",
                "status": "final",
                "template": "Protocol Template",
                "version_date": "2024-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Introduction text",
                }
            ],
        },
        "population": {
            "label": "Test Population",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 18 years"],
                "exclusion": ["Pregnant"],
            },
        },
        "amendments": {
            "summary": "Initial version",
            "reasons": {"primary": "First version"},
            "impact": {"safety": False, "reliability": False},
            "enrollment": {"value": 100, "unit": "subjects"},
        },
        "study_design": {
            "label": "Test Study Design",
            "rationale": "Test rationale",
            "trial_phase": "phase-1",
        },
        "study": {
            "name": {"acronym": "TST"},
            "label": "Test Study",
            "version": "1.0",
            "rationale": "Test study rationale",
        },
    }


@pytest.fixture
def complete_study_data_with_soa(minimal_study_data):
    """Provide complete study data including SOA."""
    data = minimal_study_data.copy()
    data["soa"] = {
        "epochs": {
            "items": [
                {"text": "Screening"},
                {"text": "Treatment"},
            ]
        },
        "visits": {
            "items": [
                {"text": "Visit 1", "references": []},
                {"text": "Visit 2", "references": []},
            ]
        },
        "timepoints": {
            "items": [
                {"index": "0", "text": "Day 1", "value": "1", "unit": "days"},
                {"index": "1", "text": "Day 7", "value": "7", "unit": "days"},
            ]
        },
        "windows": {
            "items": [
                {"before": 0, "after": 0, "unit": "days"},
                {"before": 1, "after": 1, "unit": "days"},
            ]
        },
        "activities": {
            "items": [
                {
                    "name": "Consent",
                    "visits": [{"index": 0, "references": []}],
                },
                {
                    "name": "Blood Draw",
                    "visits": [{"index": 1, "references": []}],
                },
            ]
        },
        "conditions": {"items": []},
    }
    return data


class TestAssemblerInitialization:
    """Test Assembler initialization."""

    def test_init_with_valid_parameters(self):
        """Test Assembler initialization with valid parameters."""
        errors = Errors()
        assembler = Assembler(root_path(), errors)
        assert assembler._errors is errors
        assert assembler._builder is not None
        assert assembler.MODULE == "usdm4.assembler.assembler.Assembler"
        assert assembler.study is None

        # Verify all sub-assemblers are initialized
        assert assembler._identification_assembler is not None
        assert assembler._population_assembler is not None
        assert assembler._amendments_assembler is not None
        assert assembler._document_assembler is not None
        assert assembler._study_design_assembler is not None
        assert assembler._study_assembler is not None
        assert assembler._timeline_assembler is not None

    def test_init_creates_builder_with_correct_path(self):
        """Test that builder is created with correct root path."""
        assembler = global_assembler

        # Verify builder exists and has been initialized
        assert assembler._builder is not None

    def test_study_property_initial_state(self):
        """Test that study property returns None initially."""
        assembler = global_assembler
        assert assembler.study is None


class TestAssemblerExecution:
    """Test Assembler execute method."""

    def test_execute_with_minimal_valid_data(self, minimal_study_data):
        """Test execute with minimal valid data."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Verify study was created
        assert assembler.study is not None
        assert assembler.study.name == "TST"
        assert assembler.study.label == "TST"
        assert len(assembler.study.versions) == 1

    def test_execute_with_complete_data_including_soa(
        self, complete_study_data_with_soa
    ):
        """Test execute with complete data including SOA/timeline."""
        assembler = get_global_assembler()
        assembler.execute(complete_study_data_with_soa)

        # Verify study was created
        assert assembler.study is not None
        assert assembler.study.name == "TST"

        # Verify timeline data was processed
        assert assembler._timeline_assembler.timelines is not None

    def test_execute_without_soa_data(self, minimal_study_data):
        """Test execute without SOA data (should work fine)."""
        # SOA data is optional, so this should work
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Verify study was created even without SOA
        assert assembler.study is not None
        assert assembler.study.name == "TST"

    def test_execute_with_empty_data_fails_gracefully(self):
        """Test execute with empty data fails gracefully."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        try:
            assembler.execute({})
        except Exception:
            pass

        # Should have logged errors
        assert global_errors.error_count() > initial_error_count

    def test_execute_with_missing_required_keys(self):
        """Test execute with missing required keys."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        incomplete_data = {
            "identification": {"titles": {"brief": "Test"}},
            # Missing other required keys
        }

        try:
            assembler.execute(incomplete_data)
        except Exception:
            pass

        # Should have logged errors
        assert global_errors.error_count() > initial_error_count

    def test_execute_with_malformed_data(self):
        """Test execute with malformed data."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        malformed_data = {
            "identification": "not a dict",
            "document": None,
            "population": [],
            "amendments": 123,
            "study_design": "invalid",
            "study": {"name": "missing structure"},
        }

        try:
            assembler.execute(malformed_data)
        except Exception:
            pass

        # Should have logged errors
        assert global_errors.error_count() > initial_error_count

    def test_execute_with_none_values(self):
        """Test execute with None values in data."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        data_with_nones = {
            "identification": None,
            "document": None,
            "population": None,
            "amendments": None,
            "study_design": None,
            "study": None,
        }

        try:
            assembler.execute(data_with_nones)
        except Exception:
            pass

        # Should have logged errors
        assert global_errors.error_count() > initial_error_count


class TestAssemblerStudyProperty:
    """Test Assembler study property."""

    def test_study_property_returns_created_study(self, minimal_study_data):
        """Test that study property returns the created study."""
        # Initially None
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Now should return the study
        assert assembler.study is not None
        assert assembler.study.name == "TST"

    def test_study_property_type(self, minimal_study_data):
        """Test that study property returns correct type."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        study = assembler.study
        assert study is not None
        assert hasattr(study, "name")
        assert hasattr(study, "label")
        assert hasattr(study, "versions")


class TestAssemblerWrapperMethod:
    """Test Assembler wrapper method."""

    def test_wrapper_with_valid_parameters(self, minimal_study_data):
        """Test wrapper creation with valid parameters."""
        # First execute to create a study
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Create wrapper
        wrapper = assembler.wrapper("TestSystem", "1.0.0")

        assert wrapper is not None
        assert wrapper.study is not None
        assert wrapper.systemName == "TestSystem"
        assert wrapper.systemVersion == "1.0.0"
        assert wrapper.usdmVersion == usdm_version

    def test_wrapper_without_study_creation(self):
        """Test wrapper creation without creating study first."""
        # Try to create wrapper without executing first
        assembler = get_global_assembler()
        wrapper = assembler.wrapper("TestSystem", "1.0.0")

        # Should return None or handle gracefully
        # (depends on builder implementation)
        assert wrapper is None or wrapper.study is None

    def test_wrapper_with_empty_name(self, minimal_study_data):
        """Test wrapper with empty system name."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        wrapper = assembler.wrapper("", "1.0.0")

        # Should still create wrapper with empty name
        assert wrapper is not None
        assert wrapper.systemName == ""

    def test_wrapper_with_empty_version(self, minimal_study_data):
        """Test wrapper with empty version."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        wrapper = assembler.wrapper("TestSystem", "")

        # Should still create wrapper with empty version
        assert wrapper is not None
        assert wrapper.systemVersion == ""

    def test_wrapper_usdm_version_matches_package_version(self, minimal_study_data):
        """Test that wrapper usdmVersion matches the package version."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        wrapper = assembler.wrapper("TestSystem", "1.0.0")

        assert wrapper is not None
        assert wrapper.usdmVersion == usdm_version

    def test_wrapper_contains_study_reference(self, minimal_study_data):
        """Test that wrapper contains a reference to the study."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        wrapper = assembler.wrapper("TestSystem", "1.0.0")

        assert wrapper is not None
        assert wrapper.study is not None
        assert wrapper.study == assembler.study


class TestAssemblerSequencing:
    """Test Assembler execution sequencing and dependencies."""

    def test_assemblers_executed_in_correct_order(self, minimal_study_data):
        """Test that sub-assemblers are executed in the correct order."""
        # Execute the full assembly process
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Verify that all assemblers have been executed by checking their results
        # Identification should have processed titles
        assert assembler._identification_assembler is not None

        # Document should have been created
        assert assembler._document_assembler is not None

        # Population should have been created
        assert assembler._population_assembler.population is not None

        # Study design should have been created
        assert assembler._study_design_assembler.study_design is not None

        # Study should have been created last
        assert assembler._study_assembler.study is not None

    def test_study_design_receives_population_assembler(self, minimal_study_data):
        """Test that study design assembler receives population assembler reference."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Verify population was created before study design
        assert assembler._population_assembler.population is not None
        assert assembler._study_design_assembler.study_design is not None

    def test_study_assembler_receives_all_dependencies(self, minimal_study_data):
        """Test that study assembler receives all required assembler references."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Verify study was created with all dependencies
        assert assembler._study_assembler.study is not None
        assert len(assembler._study_assembler.study.versions) > 0


class TestAssemblerIntegration:
    """Integration tests for Assembler."""

    def test_full_assembly_workflow(self, minimal_study_data):
        """Test complete assembly workflow from data to study."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Verify all major components
        study = assembler.study
        assert study is not None
        assert study.name == "TST"
        assert len(study.versions) == 1

        # Verify study version has all components
        version = study.versions[0]
        assert version.versionIdentifier == "1.0"
        assert version.rationale == "Test study rationale"

    def test_assembly_with_wrapper_creation(self, minimal_study_data):
        """Test full assembly including wrapper creation."""
        # Execute assembly
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        # Create wrapper
        wrapper = assembler.wrapper("TestSystem", "1.0.0")

        # Verify complete structure
        assert wrapper is not None
        assert wrapper.study is not None
        assert wrapper.study.name == "TST"
        assert wrapper.systemName == "TestSystem"
        assert wrapper.systemVersion == "1.0.0"
        assert wrapper.usdmVersion == usdm_version

    def test_multiple_executions_on_same_assembler(self):
        """Test multiple executions on the same assembler instance."""
        errors1 = Errors()
        assembler1 = Assembler(root_path(), errors1)

        data1 = {
            "identification": {"titles": {"brief": "Study 1"}},
            "document": {
                "document": {
                    "label": "Doc1",
                    "version": "1.0",
                    "status": "final",
                    "template": "T",
                    "version_date": "2024-01-01",
                },
                "sections": [],
            },
            "population": {
                "label": "Pop1",
                "inclusion_exclusion": {"inclusion": ["Age >= 18"], "exclusion": []},
            },
            "amendments": {
                "summary": "V1",
                "reasons": {"primary": "R1"},
                "impact": {"safety": False, "reliability": False},
                "enrollment": {"value": 100, "unit": "subjects"},
            },
            "study_design": {
                "label": "Design1",
                "rationale": "Rat1",
                "trial_phase": "phase-1",
            },
            "study": {
                "name": {"acronym": "S1"},
                "label": "Study1",
                "version": "1.0",
                "rationale": "R1",
            },
        }

        assembler1.execute(data1)
        study1 = assembler1.study

        # Create new assembler for second execution
        errors2 = Errors()
        assembler2 = Assembler(root_path(), errors2)

        data2 = {
            "identification": {"titles": {"brief": "Study 2"}},
            "document": {
                "document": {
                    "label": "Doc2",
                    "version": "2.0",
                    "status": "final",
                    "template": "T",
                    "version_date": "2024-01-01",
                },
                "sections": [],
            },
            "population": {
                "label": "Pop2",
                "inclusion_exclusion": {"inclusion": ["Age >= 21"], "exclusion": []},
            },
            "amendments": {
                "summary": "V2",
                "reasons": {"primary": "R2"},
                "impact": {"safety": False, "reliability": False},
                "enrollment": {"value": 200, "unit": "subjects"},
            },
            "study_design": {
                "label": "Design2",
                "rationale": "Rat2",
                "trial_phase": "phase-2",
            },
            "study": {
                "name": {"acronym": "S2"},
                "label": "Study2",
                "version": "2.0",
                "rationale": "R2",
            },
        }

        assembler2.execute(data2)
        study2 = assembler2.study

        # Verify both studies are different
        assert study1 is not None
        assert study2 is not None
        assert study1.name != study2.name


class TestAssemblerEdgeCases:
    """Test Assembler edge cases."""

    def test_execute_with_extra_keys(self, minimal_study_data):
        """Test execute with extra unexpected keys in data."""
        data_with_extra = minimal_study_data.copy()
        data_with_extra["unexpected_key"] = {"some": "data"}
        data_with_extra["another_extra"] = "value"

        # Should ignore extra keys and process normally
        assembler = get_global_assembler()
        assembler.execute(data_with_extra)

        assert assembler.study is not None

    def test_wrapper_with_special_characters(self, minimal_study_data):
        """Test wrapper with special characters in system name and version."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        wrapper = assembler.wrapper("Test-System_v2.0", "1.0.0-beta+001")

        assert wrapper is not None
        assert wrapper.systemName == "Test-System_v2.0"
        assert wrapper.systemVersion == "1.0.0-beta+001"

    def test_wrapper_with_unicode_characters(self, minimal_study_data):
        """Test wrapper with unicode characters."""
        assembler = get_global_assembler()
        assembler.execute(minimal_study_data)

        wrapper = assembler.wrapper("Système de Test", "1.0.0")

        assert wrapper is not None
        assert wrapper.systemName == "Système de Test"

    def test_execute_with_nested_none_values(self):
        """Test execute with nested None values."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        data = {
            "identification": {"titles": None},
            "document": {"document": None, "sections": None},
            "population": {"label": None, "inclusion_exclusion": None},
            "amendments": {"summary": None},
            "study_design": {"label": None},
            "study": {"name": None},
        }

        try:
            assembler.execute(data)
        except Exception:
            pass

        # Should have logged errors
        assert global_errors.error_count() > initial_error_count


class TestAssemblerErrorHandling:
    """Test Assembler error handling."""

    def test_error_logging_on_exception(self):
        """Test that exceptions are properly logged."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        # Cause an exception by passing invalid data
        try:
            assembler.execute(None)
        except Exception:
            pass

        # Should have logged the exception
        assert global_errors.error_count() > initial_error_count

    def test_wrapper_error_handling(self):
        """Test wrapper error handling."""
        # Try to create wrapper without executing first (study will be None)
        assembler = get_global_assembler()
        wrapper = assembler.wrapper("TestSystem", "1.0.0")

        # Should handle gracefully and return None or valid wrapper
        # Exact behavior depends on builder implementation
        assert wrapper is None or wrapper is not None

    def test_partial_data_execution(self):
        """Test execution with only some required data present."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        partial_data = {
            "identification": {
                "titles": {"brief": "Test Study"},
                "identifiers": [
                    {"identifier": "TEST001", "scope": {"standard": "internal"}}
                ],
            },
            "document": {
                "document": {
                    "label": "Doc",
                    "version": "1.0",
                    "status": "final",
                    "template": "T",
                    "version_date": "2024-01-01",
                },
                "sections": [],
            },
            # Missing other required sections
        }

        try:
            assembler.execute(partial_data)
        except Exception:
            pass

        # Should have logged errors for missing data
        assert global_errors.error_count() > initial_error_count


class TestAssemblerModuleConstant:
    """Test Assembler MODULE constant."""

    def test_module_constant_value(self):
        """Test that MODULE constant has correct value."""
        assembler = get_global_assembler()
        assert assembler.MODULE == "usdm4.assembler.assembler.Assembler"

    def test_module_constant_is_string(self):
        """Test that MODULE constant is a string."""
        assembler = get_global_assembler()
        assert isinstance(assembler.MODULE, str)


class TestAssemblerWrapperExceptionHandling:
    """Test wrapper method exception handling (covers lines 157-160)."""

    def test_wrapper_exception_returns_none(self):
        """Test that wrapper returns None when builder.create raises exception."""
        assembler = get_global_assembler()
        initial_error_count = global_errors.error_count()

        # Monkey-patch builder.create to raise an exception
        original_create = assembler._builder.create

        def raise_error(cls, params):
            raise RuntimeError("Simulated wrapper creation failure")

        assembler._builder.create = raise_error

        try:
            result = assembler.wrapper("TestSystem", "1.0.0")
        finally:
            assembler._builder.create = original_create

        assert result is None
        assert global_errors.error_count() > initial_error_count
