import pytest
from pydantic import ValidationError

from src.usdm4.assembler.schema.population_schema import (
    CohortInput,
    DemographicsInput,
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

    def test_new_field_defaults(self):
        p = PopulationInput()
        assert p.demographics.sex == "ALL"
        assert p.demographics.healthy_volunteers is False
        assert p.demographics.age_min is None
        assert p.demographics.age_max is None
        assert p.demographics.age_unit == "Years"
        assert p.cohorts == []
        assert p.planned_enrollment is None

    def test_full_input_with_demographics_and_cohorts(self):
        data = {
            "label": "Adults 18-65",
            "inclusion_exclusion": {"inclusion": ["Consent"], "exclusion": []},
            "demographics": {
                "age_min": 18,
                "age_max": 65,
                "age_unit": "Years",
                "sex": "ALL",
                "healthy_volunteers": False,
            },
            "cohorts": [
                {
                    "name": "Main",
                    "label": "Main cohort",
                    "planned_enrollment": 200,
                    "characteristics": ["treatment-naive"],
                },
            ],
            "planned_enrollment": 200,
        }
        result = PopulationInput.model_validate(data)
        assert result.demographics.age_min == 18
        assert result.demographics.age_max == 65
        assert result.demographics.sex == "ALL"
        assert result.demographics.healthy_volunteers is False
        assert len(result.cohorts) == 1
        assert result.cohorts[0].name == "Main"
        assert result.cohorts[0].planned_enrollment == 200
        assert result.cohorts[0].characteristics == ["treatment-naive"]
        assert result.planned_enrollment == 200


class TestDemographicsInput:
    def test_all_defaults(self):
        d = DemographicsInput()
        assert d.age_min is None
        assert d.age_max is None
        assert d.age_unit == "Years"
        assert d.sex == "ALL"
        assert d.healthy_volunteers is False

    def test_sex_literal_accepts_allowed(self):
        assert DemographicsInput.model_validate({"sex": "MALE"}).sex == "MALE"
        assert DemographicsInput.model_validate({"sex": "FEMALE"}).sex == "FEMALE"
        assert DemographicsInput.model_validate({"sex": "ALL"}).sex == "ALL"

    def test_sex_literal_rejects_unknown(self):
        with pytest.raises(ValidationError):
            DemographicsInput.model_validate({"sex": "OTHER"})

    def test_age_accepts_numeric(self):
        d = DemographicsInput.model_validate({"age_min": 18, "age_max": 65.5})
        assert d.age_min == 18
        assert d.age_max == 65.5


class TestCohortInput:
    def test_requires_name(self):
        with pytest.raises(ValidationError):
            CohortInput.model_validate({})

    def test_defaults(self):
        c = CohortInput.model_validate({"name": "C1"})
        assert c.label == ""
        assert c.description == ""
        assert c.planned_enrollment is None
        assert c.characteristics == []
