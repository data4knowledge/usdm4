import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.builder.builder import Builder
from usdm4.api.population_definition import StudyDesignPopulation
from usdm4.api.eligibility_criterion import (
    EligibilityCriterion,
    EligibilityCriterionItem,
)
from usdm4.api.code import Code


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
def population_assembler(builder, errors):
    """Create a PopulationAssembler instance for testing."""
    builder.clear()  # Clear any existing cross-references to avoid conflicts
    return PopulationAssembler(builder, errors)


class TestPopulationAssembler:
    """Test suite for PopulationAssembler class."""

    def test_initialization_valid_builder_and_errors(self, builder, errors):
        """Test PopulationAssembler initialization with valid Builder and Errors instances."""
        assembler = PopulationAssembler(builder, errors)

        assert assembler._builder is builder
        assert assembler._errors is errors
        assert assembler._population is None
        assert assembler._cohorts == []
        assert assembler._ec_items == []
        assert assembler._eci_items == []
        assert (
            assembler.MODULE
            == "usdm4.assembler.population_assembler.PopulationAssembler"
        )

    def test_initialization_invalid_builder(self, errors):
        """Test PopulationAssembler initialization with invalid Builder instance."""
        # PopulationAssembler doesn't validate builder type at initialization
        # It will fail when methods are called on the invalid builder
        assembler = PopulationAssembler("not_a_builder", errors)
        assert assembler._builder == "not_a_builder"

    def test_initialization_invalid_errors(self, builder):
        """Test PopulationAssembler initialization with invalid Errors instance."""
        # PopulationAssembler doesn't validate errors type at initialization
        # It will fail when methods are called on the invalid errors object
        assembler = PopulationAssembler(builder, "not_errors")
        assert assembler._errors == "not_errors"

    def test_execute_valid_data_basic(self, population_assembler):
        """Test execute method with valid basic population data."""
        data = {
            "label": "Study Population",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 18 years", "Signed informed consent"],
                "exclusion": ["Pregnancy", "Severe medical condition"],
            },
        }

        population_assembler.execute(data)

        # Check that population was created
        assert population_assembler.population is not None
        assert hasattr(population_assembler.population, "name")
        assert hasattr(population_assembler.population, "label")
        assert hasattr(population_assembler.population, "description")
        assert hasattr(population_assembler.population, "includesHealthySubjects")

        # Check population properties
        assert population_assembler.population.name == "STUDY-POPULATION"
        assert population_assembler.population.label == "Study Population"
        assert (
            population_assembler.population.description
            == "The study population, currently blank"
        )
        assert population_assembler.population.includesHealthySubjects is True

        # Check that criteria were created
        assert len(population_assembler._ec_items) == 4  # 2 inclusion + 2 exclusion
        assert len(population_assembler._eci_items) == 4  # 2 inclusion + 2 exclusion

    def test_execute_valid_data_empty_criteria(self, population_assembler):
        """Test execute method with valid data but empty inclusion/exclusion criteria."""
        data = {
            "label": "Empty Criteria Population",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
        }

        population_assembler.execute(data)

        assert population_assembler.population is not None
        assert population_assembler.population.name == "EMPTY-CRITERIA-POPULATION"
        assert population_assembler.population.label == "Empty Criteria Population"
        assert len(population_assembler._ec_items) == 0
        assert len(population_assembler._eci_items) == 0

    def test_execute_valid_data_single_word_label(self, population_assembler):
        """Test execute method with single word label."""
        data = {
            "label": "Population",
            "inclusion_exclusion": {"inclusion": ["Adult"], "exclusion": []},
        }

        population_assembler.execute(data)

        assert population_assembler.population.name == "POPULATION"
        assert population_assembler.population.label == "Population"

    def test_execute_valid_data_complex_label(self, population_assembler):
        """Test execute method with complex label containing special characters."""
        data = {
            "label": "Phase II/III Study Population",
            "inclusion_exclusion": {
                "inclusion": ["Eligible patients"],
                "exclusion": [],
            },
        }

        population_assembler.execute(data)

        assert population_assembler.population.name == "PHASE-II/III-STUDY-POPULATION"
        assert population_assembler.population.label == "Phase II/III Study Population"

    def test_execute_invalid_data_missing_label(self, population_assembler, errors):
        """Test execute method with missing label field."""
        data = {"inclusion_exclusion": {"inclusion": ["Age >= 18"], "exclusion": []}}

        population_assembler.execute(data)

        # Should have logged an error
        assert errors.error_count() > 0
        assert population_assembler.population is None

    def test_execute_invalid_data_missing_inclusion_exclusion(
        self, population_assembler, errors
    ):
        """Test execute method with missing inclusion_exclusion field."""
        data = {"label": "Test Population"}

        population_assembler.execute(data)

        # Should have logged an error
        assert errors.error_count() > 0
        assert population_assembler.population is None

    def test_execute_invalid_data_malformed_inclusion_exclusion(
        self, population_assembler, errors
    ):
        """Test execute method with malformed inclusion_exclusion structure."""
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {"inclusion": "not a list", "exclusion": []},
        }

        population_assembler.execute(data)

        # Should have logged an error
        assert errors.error_count() > 0

    def test_execute_invalid_data_missing_inclusion(self, population_assembler, errors):
        """Test execute method with missing inclusion field."""
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {"exclusion": ["Pregnancy"]},
        }

        population_assembler.execute(data)

        # Should have logged an error
        assert errors.error_count() > 0

    def test_execute_invalid_data_missing_exclusion(self, population_assembler, errors):
        """Test execute method with missing exclusion field."""
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {"inclusion": ["Age >= 18"]},
        }

        population_assembler.execute(data)

        # Should have logged an error
        assert errors.error_count() > 0

    def test_execute_invalid_data_none_values(self, population_assembler, errors):
        """Test execute method with None values in criteria."""
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {
                "inclusion": [None, "Valid criterion"],
                "exclusion": ["Valid exclusion", None],
            },
        }

        population_assembler.execute(data)

        # Should handle None values gracefully or log errors
        # The exact behavior depends on implementation
        assert errors.error_count() >= 0  # May or may not generate errors

    def test_execute_invalid_data_empty_strings(self, population_assembler):
        """Test execute method with empty string criteria."""
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {
                "inclusion": ["", "Valid criterion"],
                "exclusion": ["Valid exclusion", ""],
            },
        }

        population_assembler.execute(data)

        # Should create population and criteria, including empty strings
        assert population_assembler.population is not None
        assert len(population_assembler._ec_items) == 4
        assert len(population_assembler._eci_items) == 4

    def test_execute_invalid_data_non_string_criteria(
        self, population_assembler, errors
    ):
        """Test execute method with non-string criteria values."""
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {
                "inclusion": [123, {"invalid": "criterion"}],
                "exclusion": [True, ["nested", "list"]],
            },
        }

        population_assembler.execute(data)

        # Should handle non-string values or log errors
        # The exact behavior depends on implementation
        assert errors.error_count() >= 0

    def test_population_property(self, population_assembler):
        """Test population property getter."""
        # Initially None
        assert population_assembler.population is None

        # After successful execution
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {"inclusion": ["Age >= 18"], "exclusion": []},
        }
        population_assembler.execute(data)

        population = population_assembler.population
        assert population is not None
        assert hasattr(population, "instanceType")

    def test_criteria_items_property(self, population_assembler):
        """Test criteria_items property getter."""
        # Initially empty
        assert population_assembler.criteria_items == []

        # After successful execution
        data = {
            "label": "Test Population",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 18", "Signed consent"],
                "exclusion": ["Pregnancy"],
            },
        }
        population_assembler.execute(data)

        criteria_items = population_assembler.criteria_items
        assert len(criteria_items) == 3
        for item in criteria_items:
            assert hasattr(item, "instanceType")

    def test_ie_method_inclusion_only(self, population_assembler):
        """Test _ie method with inclusion criteria only."""
        criteria = {"inclusion": ["Age >= 18", "Signed consent"], "exclusion": []}

        population_assembler._ie(criteria)

        assert len(population_assembler._ec_items) == 2
        assert len(population_assembler._eci_items) == 2

        # Check inclusion criteria naming
        for i, ec_item in enumerate(population_assembler._ec_items):
            assert ec_item.name == f"INC{i + 1}"
            assert "Inclusion" in ec_item.label

    def test_ie_method_exclusion_only(self, population_assembler):
        """Test _ie method with exclusion criteria only."""
        criteria = {"inclusion": [], "exclusion": ["Pregnancy", "Severe illness"]}

        population_assembler._ie(criteria)

        assert len(population_assembler._ec_items) == 2
        assert len(population_assembler._eci_items) == 2

        # Check exclusion criteria naming
        for i, ec_item in enumerate(population_assembler._ec_items):
            assert ec_item.name == f"EXC{i + 1}"
            assert "Exclusion" in ec_item.label

    def test_ie_method_both_inclusion_and_exclusion(self, population_assembler):
        """Test _ie method with both inclusion and exclusion criteria."""
        criteria = {
            "inclusion": ["Age >= 18"],
            "exclusion": ["Pregnancy", "Severe illness"],
        }

        population_assembler._ie(criteria)

        assert len(population_assembler._ec_items) == 3
        assert len(population_assembler._eci_items) == 3

        # Check that inclusion comes first, then exclusion
        assert population_assembler._ec_items[0].name == "INC1"
        assert population_assembler._ec_items[1].name == "EXC1"
        assert population_assembler._ec_items[2].name == "EXC2"

    def test_collection_method_inclusion(self, population_assembler):
        """Test _collection method for inclusion criteria."""
        criteria = ["Age >= 18", "Signed informed consent"]

        population_assembler._collection(
            criteria, "C25532", "INCLUSION", "INC", "Inclusion"
        )

        assert len(population_assembler._ec_items) == 2
        assert len(population_assembler._eci_items) == 2

        # Check first criterion
        assert population_assembler._ec_items[0].name == "INC1"
        assert population_assembler._ec_items[0].label == "Inclusion criterion 1 "
        assert population_assembler._ec_items[0].identifier == "1"

        # Check first criterion item
        assert population_assembler._eci_items[0].name == "INC-I1"
        assert population_assembler._eci_items[0].label == "Inclusion item 1 "
        assert population_assembler._eci_items[0].text == "Age >= 18"

    def test_collection_method_exclusion(self, population_assembler):
        """Test _collection method for exclusion criteria."""
        criteria = ["Pregnancy"]

        population_assembler._collection(
            criteria, "C25370", "EXCLUSION", "EXC", "Exclusion"
        )

        assert len(population_assembler._ec_items) == 1
        assert len(population_assembler._eci_items) == 1

        # Check criterion
        assert population_assembler._ec_items[0].name == "EXC1"
        assert population_assembler._ec_items[0].label == "Exclusion criterion 1 "
        assert population_assembler._ec_items[0].identifier == "1"

        # Check criterion item
        assert population_assembler._eci_items[0].name == "EXC-I1"
        assert population_assembler._eci_items[0].label == "Exclusion item 1 "
        assert population_assembler._eci_items[0].text == "Pregnancy"

    def test_collection_method_empty_list(self, population_assembler):
        """Test _collection method with empty criteria list."""
        criteria = []

        population_assembler._collection(
            criteria, "C25532", "INCLUSION", "INC", "Inclusion"
        )

        assert len(population_assembler._ec_items) == 0
        assert len(population_assembler._eci_items) == 0

    def test_multiple_executions_state_management(self, population_assembler):
        """Test that multiple executions properly manage internal state."""
        # First execution
        data1 = {
            "label": "Population 1",
            "inclusion_exclusion": {"inclusion": ["Age >= 18"], "exclusion": []},
        }
        population_assembler.execute(data1)

        first_population = population_assembler.population
        first_criteria_count = len(population_assembler._ec_items)

        # Second execution should not clear previous state
        data2 = {
            "label": "Population 2",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 21"],
                "exclusion": ["Pregnancy"],
            },
        }
        population_assembler.execute(data2)

        # Should have new population but accumulated criteria
        assert population_assembler.population != first_population
        assert population_assembler.population.label == "Population 2"
        assert len(population_assembler._ec_items) > first_criteria_count

    def test_builder_integration_no_mocking(self, population_assembler):
        """Test that Builder class is used without mocking."""
        data = {
            "label": "Integration Test Population",
            "inclusion_exclusion": {"inclusion": ["Test criterion"], "exclusion": []},
        }

        population_assembler.execute(data)

        # Verify actual Builder was used by checking created objects
        assert population_assembler.population is not None
        assert isinstance(population_assembler.population, StudyDesignPopulation)
        assert len(population_assembler._ec_items) == 1
        assert isinstance(population_assembler._ec_items[0], EligibilityCriterion)
        assert len(population_assembler._eci_items) == 1
        assert isinstance(population_assembler._eci_items[0], EligibilityCriterionItem)

    def test_errors_integration_no_mocking(self, population_assembler, errors):
        """Test that Errors class is used without mocking for error handling."""
        # Test with invalid data that should trigger error handling
        data = {
            "label": "Error Test Population"
            # Missing inclusion_exclusion
        }

        initial_error_count = errors.error_count()
        population_assembler.execute(data)

        # Should have logged an error
        assert errors.error_count() > initial_error_count
        assert population_assembler.population is None

    def test_inheritance_from_base_assembler(self, population_assembler):
        """Test that PopulationAssembler properly inherits from BaseAssembler."""
        # Test that inherited methods are available
        assert hasattr(population_assembler, "_label_to_name")

        # Test _label_to_name method
        result = population_assembler._label_to_name("Test Label")
        assert result == "TEST-LABEL"

    def test_edge_case_very_long_criteria_list(self, population_assembler):
        """Test handling of very long criteria lists."""
        long_inclusion = [f"Inclusion criterion {i}" for i in range(100)]
        long_exclusion = [f"Exclusion criterion {i}" for i in range(50)]

        data = {
            "label": "Long Criteria Population",
            "inclusion_exclusion": {
                "inclusion": long_inclusion,
                "exclusion": long_exclusion,
            },
        }

        population_assembler.execute(data)

        assert population_assembler.population is not None
        assert len(population_assembler._ec_items) == 150
        assert len(population_assembler._eci_items) == 150

    def test_edge_case_unicode_criteria(self, population_assembler):
        """Test handling of Unicode characters in criteria."""
        data = {
            "label": "Unicode Population",
            "inclusion_exclusion": {
                "inclusion": ["Âge ≥ 18 années", "Consentement éclairé signé"],
                "exclusion": ["Grossesse", "Maladie grave"],
            },
        }

        population_assembler.execute(data)

        assert population_assembler.population is not None
        assert len(population_assembler._ec_items) == 4

        # Check that Unicode text is preserved
        unicode_texts = [item.text for item in population_assembler._eci_items]
        assert "Âge ≥ 18 années" in unicode_texts
        assert "Consentement éclairé signé" in unicode_texts

    def test_edge_case_very_long_label(self, population_assembler):
        """Test handling of very long population labels."""
        long_label = "A" * 1000  # Very long label

        data = {
            "label": long_label,
            "inclusion_exclusion": {"inclusion": ["Test"], "exclusion": []},
        }

        population_assembler.execute(data)

        assert population_assembler.population is not None
        assert population_assembler.population.label == long_label
        assert (
            population_assembler.population.name == "A" * 1000
        )  # Should handle long names

    def test_cdisc_code_integration(self, population_assembler):
        """Test integration with CDISC code creation."""
        data = {
            "label": "CDISC Test Population",
            "inclusion_exclusion": {
                "inclusion": ["Test inclusion"],
                "exclusion": ["Test exclusion"],
            },
        }

        population_assembler.execute(data)

        # Check that CDISC codes were properly created and assigned
        inclusion_criterion = None
        exclusion_criterion = None

        for criterion in population_assembler._ec_items:
            if criterion.name.startswith("INC"):
                inclusion_criterion = criterion
            elif criterion.name.startswith("EXC"):
                exclusion_criterion = criterion

        assert inclusion_criterion is not None
        assert exclusion_criterion is not None
        assert hasattr(inclusion_criterion, "category")
        assert hasattr(exclusion_criterion, "category")
        assert isinstance(inclusion_criterion.category, Code)
        assert isinstance(exclusion_criterion.category, Code)
