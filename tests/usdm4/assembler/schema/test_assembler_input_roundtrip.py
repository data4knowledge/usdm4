"""Round-trip tests for extended AssemblerInput schemas.

Exercises StudyDesignInput and PopulationInput end-to-end via
``AssemblerInput.model_validate`` to prove:

1. Legacy payloads (before the arms/interventions/cells + demographics/cohorts
   extensions) still validate unchanged.
2. Payloads that opt in to the new fields round-trip through ``model_dump``
   without loss.
3. Required sub-fields (``ArmInput.name``, ``CellInput.arm``/``epoch``,
   ``DemographicsInput.sex`` literal) validate as expected.
"""

import pytest
from pydantic import ValidationError

from src.usdm4.assembler.schema import AssemblerInput


@pytest.fixture
def legacy_minimal_dict():
    """Shape that existed before the schema extensions — must keep validating."""
    return {
        "identification": {"titles": {"brief": "Test", "official": "Full Title"}},
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
        "population": {
            "label": "Pop",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
        },
        "study_design": {"label": "Design", "rationale": "R", "trial_phase": "1"},
        "study": {"name": {"acronym": "TST"}, "version": "1.0", "rationale": "R"},
    }


@pytest.fixture
def extended_dict(legacy_minimal_dict):
    """Legacy payload plus every new field populated."""
    d = {**legacy_minimal_dict}
    d["study_design"] = {
        **d["study_design"],
        "intervention_model": "Parallel",
        "arms": [
            {
                "name": "A1",
                "label": "Experimental",
                "type": "Experimental",
                "intervention_names": ["DrugX"],
                "planned_enrollment": 100,
            },
            {
                "name": "A2",
                "label": "Control",
                "type": "Placebo Comparator",
                "intervention_names": ["Placebo"],
                "planned_enrollment": 100,
            },
        ],
        "interventions": [
            {
                "name": "DrugX",
                "label": "Drug X",
                "type": "Drug",
                "role": "Investigational Treatment",
                "dose": "100 mg",
                "route": "Oral",
                "frequency": "Once daily",
            },
            {"name": "Placebo", "type": "Drug", "role": "Placebo Comparator"},
        ],
        "cells": [
            {"arm": "A1", "epoch": "Treatment", "elements": []},
            {"arm": "A2", "epoch": "Treatment", "elements": []},
        ],
        "elements": [],
    }
    d["population"] = {
        **d["population"],
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
                "arm_names": ["A1", "A2"],
            },
        ],
        "planned_enrollment": 200,
    }
    return d


class TestBackwardCompat:
    def test_legacy_shape_still_validates(self, legacy_minimal_dict):
        result = AssemblerInput.model_validate(legacy_minimal_dict)
        # New StudyDesignInput fields fall back to their defaults.
        assert result.study_design.intervention_model == ""
        assert result.study_design.arms == []
        assert result.study_design.interventions == []
        assert result.study_design.cells == []
        assert result.study_design.elements == []
        # New PopulationInput fields fall back to their defaults.
        assert result.population.demographics.sex == "ALL"
        assert result.population.demographics.age_min is None
        assert result.population.demographics.age_max is None
        assert result.population.demographics.age_unit == "Years"
        assert result.population.demographics.healthy_volunteers is False
        assert result.population.cohorts == []
        assert result.population.planned_enrollment is None

    def test_legacy_inclusion_exclusion_untouched(self, legacy_minimal_dict):
        legacy_minimal_dict["population"]["inclusion_exclusion"] = {
            "inclusion": ["Age >= 18"],
            "exclusion": ["Pregnant"],
        }
        result = AssemblerInput.model_validate(legacy_minimal_dict)
        assert result.population.inclusion_exclusion.inclusion == ["Age >= 18"]
        assert result.population.inclusion_exclusion.exclusion == ["Pregnant"]

    def test_validate_strict_still_clean_for_complete_legacy(self, legacy_minimal_dict):
        _result, warnings = AssemblerInput.validate_strict(legacy_minimal_dict)
        assert warnings == []


class TestExtendedRoundtrip:
    def test_full_extended_payload_validates(self, extended_dict):
        result = AssemblerInput.model_validate(extended_dict)
        assert result.study_design.intervention_model == "Parallel"
        assert len(result.study_design.arms) == 2
        assert result.study_design.arms[0].intervention_names == ["DrugX"]
        assert result.study_design.arms[0].planned_enrollment == 100
        assert len(result.study_design.interventions) == 2
        assert result.study_design.interventions[0].dose == "100 mg"
        assert result.study_design.cells[0].epoch == "Treatment"
        assert result.population.demographics.age_min == 18
        assert result.population.demographics.age_max == 65
        assert result.population.demographics.sex == "ALL"
        assert len(result.population.cohorts) == 1
        assert result.population.cohorts[0].name == "Main"
        assert result.population.cohorts[0].arm_names == ["A1", "A2"]
        assert result.population.planned_enrollment == 200

    def test_roundtrip_via_model_dump(self, extended_dict):
        first = AssemblerInput.model_validate(extended_dict)
        second = AssemblerInput.model_validate(first.model_dump())
        assert first == second

    def test_arm_intervention_names_preserved_through_dump(self, extended_dict):
        first = AssemblerInput.model_validate(extended_dict)
        dumped = first.model_dump()
        assert dumped["study_design"]["arms"][0]["intervention_names"] == ["DrugX"]
        assert dumped["population"]["cohorts"][0]["characteristics"] == [
            "treatment-naive"
        ]


class TestValidationBoundaries:
    def test_arm_requires_name(self, extended_dict):
        extended_dict["study_design"]["arms"][0].pop("name")
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate(extended_dict)

    def test_intervention_requires_name(self, extended_dict):
        extended_dict["study_design"]["interventions"][0].pop("name")
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate(extended_dict)

    def test_cell_requires_arm_and_epoch(self, extended_dict):
        extended_dict["study_design"]["cells"] = [{"elements": []}]
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate(extended_dict)

    def test_cohort_requires_name(self, extended_dict):
        extended_dict["population"]["cohorts"][0].pop("name")
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate(extended_dict)

    def test_sex_literal_rejects_unknown(self, extended_dict):
        extended_dict["population"]["demographics"]["sex"] = "OTHER"
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate(extended_dict)

    def test_top_level_extra_keys_still_ignored(self, extended_dict):
        extended_dict["unexpected"] = "data"
        result = AssemblerInput.model_validate(extended_dict)
        assert result.study.version == "1.0"


class TestCrossModelReferences:
    """Folded-in Step 5 findings: cross-reference invariants are enforced at
    schema-validation time, not pushed out to runtime.
    """

    def test_cohort_arm_names_resolve_to_declared_arms(self, extended_dict):
        # Extended fixture uses arm_names ["A1", "A2"] which match declared
        # arms; validation should succeed.
        result = AssemblerInput.model_validate(extended_dict)
        assert result.population.cohorts[0].arm_names == ["A1", "A2"]

    def test_cohort_arm_names_unresolved_raises(self, extended_dict):
        extended_dict["population"]["cohorts"][0]["arm_names"] = ["A1", "A_TYPO"]
        with pytest.raises(ValidationError) as exc_info:
            AssemblerInput.model_validate(extended_dict)
        assert "undeclared arm" in str(exc_info.value)
        assert "A_TYPO" in str(exc_info.value)

    def test_cohort_with_empty_arm_names_allowed(self, extended_dict):
        extended_dict["population"]["cohorts"][0]["arm_names"] = []
        result = AssemblerInput.model_validate(extended_dict)
        assert result.population.cohorts[0].arm_names == []

    def test_cohort_arm_names_without_any_arms_raises(self, legacy_minimal_dict):
        legacy_minimal_dict["population"]["cohorts"] = [
            {"name": "C1", "arm_names": ["A1"]}
        ]
        with pytest.raises(ValidationError) as exc_info:
            AssemblerInput.model_validate(legacy_minimal_dict)
        assert "undeclared arm" in str(exc_info.value)

    def test_cell_element_reference_enforced_at_study_design_level(self, extended_dict):
        # Add a cell that references an element name not declared at top level.
        extended_dict["study_design"]["cells"][0]["elements"] = ["EL_TYPO"]
        extended_dict["study_design"]["elements"] = [{"name": "EL1"}]
        with pytest.raises(ValidationError) as exc_info:
            AssemblerInput.model_validate(extended_dict)
        assert "undeclared element" in str(exc_info.value)


class TestEmptyListsAndOptionalFields:
    def test_empty_arms_list_validates(self, legacy_minimal_dict):
        legacy_minimal_dict["study_design"]["arms"] = []
        result = AssemblerInput.model_validate(legacy_minimal_dict)
        assert result.study_design.arms == []

    def test_partial_demographics(self, legacy_minimal_dict):
        legacy_minimal_dict["population"]["demographics"] = {"sex": "FEMALE"}
        result = AssemblerInput.model_validate(legacy_minimal_dict)
        assert result.population.demographics.sex == "FEMALE"
        assert result.population.demographics.age_min is None
        assert result.population.demographics.healthy_volunteers is False

    def test_intervention_optional_dose_route_frequency(self, legacy_minimal_dict):
        legacy_minimal_dict["study_design"]["interventions"] = [
            {"name": "DrugY", "type": "Drug"}
        ]
        result = AssemblerInput.model_validate(legacy_minimal_dict)
        intervention = result.study_design.interventions[0]
        assert intervention.dose is None
        assert intervention.route is None
        assert intervention.frequency is None
