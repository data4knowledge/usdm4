"""Schema tests for ObjectivesInput and its nested models.

Covers:
- Defaults / required fields on each nested input model
- The intra-model estimand -> endpoint reference validator
- The AssemblerInput-level estimand -> intervention reference validator
  (cross-model, so exercised through a full AssemblerInput dict)
"""

import pytest
from pydantic import ValidationError

from usdm4.assembler.schema.objectives_schema import (
    EndpointInput,
    ObjectiveInput,
    IntercurrentEventInput,
    EstimandInput,
    ObjectivesInput,
)
from usdm4.assembler.schema.assembler_input import AssemblerInput


def _minimal_assembler_data() -> dict:
    return {
        "identification": {
            "titles": {"brief": "Test", "official": "Official Test"},
            "identifiers": [
                {"identifier": "NCT12345678", "scope": {"standard": "nct"}}
            ],
        },
        "document": {
            "document": {
                "label": "Protocol",
                "version": "1.0",
                "status": "final",
                "template": "Template",
                "version_date": "2024-01-01",
            },
            "sections": [],
        },
        "population": {
            "label": "Population",
            "inclusion_exclusion": {"inclusion": [], "exclusion": []},
        },
        "study_design": {
            "label": "Design",
            "rationale": "Rationale",
            "trial_phase": "1",
            "interventions": [{"name": "Drug A"}],
        },
        "study": {
            "name": {"acronym": "TST"},
            "label": "Test",
            "version": "1.0",
            "rationale": "Rationale",
        },
    }


class TestEndpointInput:
    def test_minimal(self):
        ep = EndpointInput(text="Endpoint text")
        assert ep.text == "Endpoint text"
        assert ep.name == ""
        assert ep.label == ""
        assert ep.description == ""
        assert ep.purpose == ""
        assert ep.level == ""

    def test_text_required(self):
        with pytest.raises(ValidationError):
            EndpointInput()


class TestObjectiveInput:
    def test_minimal(self):
        obj = ObjectiveInput(text="Objective text")
        assert obj.text == "Objective text"
        assert obj.endpoints == []
        assert obj.level == ""

    def test_with_endpoints(self):
        obj = ObjectiveInput(
            text="Objective text",
            level="Primary",
            endpoints=[{"text": "Endpoint text", "level": "Primary"}],
        )
        assert len(obj.endpoints) == 1
        assert isinstance(obj.endpoints[0], EndpointInput)

    def test_text_required(self):
        with pytest.raises(ValidationError):
            ObjectiveInput(level="Primary")


class TestIntercurrentEventInput:
    def test_minimal(self):
        ice = IntercurrentEventInput(text="Discontinuation")
        assert ice.text == "Discontinuation"
        assert ice.strategy == ""

    def test_text_required(self):
        with pytest.raises(ValidationError):
            IntercurrentEventInput(strategy="Treatment policy")


class TestEstimandInput:
    def test_minimal(self):
        est = EstimandInput(summary_measure="Difference in means", endpoint_name="END1")
        assert est.summary_measure == "Difference in means"
        assert est.endpoint_name == "END1"
        assert est.treatment_names == []
        assert est.population_subset_names == []
        assert est.intercurrent_events == []

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            EstimandInput(endpoint_name="END1")
        with pytest.raises(ValidationError):
            EstimandInput(summary_measure="Difference in means")


class TestObjectivesInput:
    def test_defaults(self):
        oi = ObjectivesInput()
        assert oi.objectives == []
        assert oi.estimands == []

    def test_estimand_endpoint_reference_resolves(self):
        oi = ObjectivesInput(
            objectives=[
                {
                    "text": "Objective",
                    "endpoints": [{"name": "END1", "text": "Endpoint"}],
                }
            ],
            estimands=[{"summary_measure": "Mean", "endpoint_name": "END1"}],
        )
        assert len(oi.estimands) == 1

    def test_estimand_endpoint_reference_undeclared_raises(self):
        with pytest.raises(ValidationError, match="undeclared endpoint"):
            ObjectivesInput(
                objectives=[
                    {
                        "text": "Objective",
                        "endpoints": [{"name": "END1", "text": "Endpoint"}],
                    }
                ],
                estimands=[{"summary_measure": "Mean", "endpoint_name": "END99"}],
            )

    def test_unnamed_endpoint_not_referencable(self):
        # An endpoint without an explicit name cannot anchor an estimand
        # reference, even if its generated name would collide.
        with pytest.raises(ValidationError, match="undeclared endpoint"):
            ObjectivesInput(
                objectives=[{"text": "Objective", "endpoints": [{"text": "Endpoint"}]}],
                estimands=[
                    {
                        "summary_measure": "Mean",
                        "endpoint_name": "ENDPOINT-1-1",
                    }
                ],
            )


class TestAssemblerInputObjectives:
    def test_objectives_default_none(self):
        instance = AssemblerInput.model_validate(_minimal_assembler_data())
        assert instance.objectives is None

    def test_objectives_accepted(self):
        data = _minimal_assembler_data()
        data["objectives"] = {
            "objectives": [
                {
                    "text": "Objective",
                    "endpoints": [{"name": "END1", "text": "Endpoint"}],
                }
            ],
            "estimands": [
                {
                    "summary_measure": "Mean",
                    "endpoint_name": "END1",
                    "treatment_names": ["Drug A"],
                }
            ],
        }
        instance = AssemblerInput.model_validate(data)
        assert instance.objectives is not None
        assert len(instance.objectives.objectives) == 1

    def test_estimand_treatment_reference_undeclared_raises(self):
        data = _minimal_assembler_data()
        data["objectives"] = {
            "objectives": [
                {
                    "text": "Objective",
                    "endpoints": [{"name": "END1", "text": "Endpoint"}],
                }
            ],
            "estimands": [
                {
                    "summary_measure": "Mean",
                    "endpoint_name": "END1",
                    "treatment_names": ["Drug X"],
                }
            ],
        }
        with pytest.raises(ValidationError, match="undeclared intervention"):
            AssemblerInput.model_validate(data)

    def test_no_estimands_skips_treatment_check(self):
        data = _minimal_assembler_data()
        data["study_design"]["interventions"] = []
        data["objectives"] = {"objectives": [{"text": "Objective"}]}
        instance = AssemblerInput.model_validate(data)
        assert instance.objectives.estimands == []
