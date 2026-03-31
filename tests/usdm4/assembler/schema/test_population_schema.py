from src.usdm4.assembler.schema.population_schema import (
    PopulationInput,
)


class TestPopulationInput:
    def test_defaults(self):
        p = PopulationInput()
        assert p.label == ""

    def test_with_criteria(self):
        data = {
            "label": "Adult Population",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 18", "Informed consent"],
                "exclusion": ["Pregnant"],
            },
        }
        result = PopulationInput.model_validate(data)
        assert result.label == "Adult Population"
        assert len(result.inclusion_exclusion.inclusion) == 2
        assert result.inclusion_exclusion.exclusion == ["Pregnant"]
