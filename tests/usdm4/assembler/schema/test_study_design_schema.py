import pytest
from pydantic import ValidationError

from src.usdm4.assembler.schema.study_design_schema import (
    ArmInput,
    CellInput,
    ElementInput,
    InterventionInput,
    StudyDesignInput,
)


class TestStudyDesignInput:
    def test_defaults(self):
        sd = StudyDesignInput()
        assert sd.label == ""
        assert sd.trial_phase == ""

    def test_full_input(self):
        data = {"label": "Parallel", "rationale": "Gold standard", "trial_phase": "III"}
        result = StudyDesignInput.model_validate(data)
        assert result.label == "Parallel"
        assert result.trial_phase == "III"

    def test_new_field_defaults(self):
        sd = StudyDesignInput()
        assert sd.intervention_model == ""
        assert sd.arms == []
        assert sd.interventions == []
        assert sd.cells == []
        assert sd.elements == []

    def test_full_input_with_arms(self):
        data = {
            "label": "Parallel 2-arm",
            "rationale": "Standard of care vs experimental",
            "trial_phase": "III",
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
                {"arm": "A1", "epoch": "Treatment"},
                {"arm": "A2", "epoch": "Treatment"},
            ],
        }
        result = StudyDesignInput.model_validate(data)
        assert result.intervention_model == "Parallel"
        assert len(result.arms) == 2
        assert result.arms[0].intervention_names == ["DrugX"]
        assert result.arms[0].planned_enrollment == 100
        assert len(result.interventions) == 2
        assert result.interventions[0].dose == "100 mg"
        assert result.interventions[0].route == "Oral"
        assert len(result.cells) == 2
        assert result.cells[0].arm == "A1"
        assert result.cells[0].epoch == "Treatment"
        assert result.cells[0].elements == []


class TestInterventionInput:
    def test_requires_name(self):
        with pytest.raises(ValidationError):
            InterventionInput.model_validate({})

    def test_name_only(self):
        i = InterventionInput.model_validate({"name": "X"})
        assert i.name == "X"
        assert i.label == ""
        assert i.dose is None
        assert i.route is None
        assert i.frequency is None


class TestArmInput:
    def test_requires_name(self):
        with pytest.raises(ValidationError):
            ArmInput.model_validate({})

    def test_defaults(self):
        a = ArmInput.model_validate({"name": "A1"})
        assert a.intervention_names == []
        assert a.planned_enrollment is None


class TestElementInput:
    def test_requires_name(self):
        with pytest.raises(ValidationError):
            ElementInput.model_validate({})

    def test_defaults(self):
        e = ElementInput.model_validate({"name": "E1"})
        assert e.intervention_names == []


class TestCellInput:
    def test_requires_arm_and_epoch(self):
        with pytest.raises(ValidationError):
            CellInput.model_validate({})
        with pytest.raises(ValidationError):
            CellInput.model_validate({"arm": "A1"})
        with pytest.raises(ValidationError):
            CellInput.model_validate({"epoch": "Treatment"})

    def test_elements_default_empty(self):
        c = CellInput.model_validate({"arm": "A1", "epoch": "Treatment"})
        assert c.elements == []


class TestCellElementCrossReference:
    """StudyDesignInput enforces that cell.elements names resolve to
    declared ElementInput.name values (Step 5 invariant: elements cannot be
    synthesised; if cells reference them, they must be declared)."""

    def test_cells_with_empty_elements_do_not_trigger_validator(self):
        sd = StudyDesignInput.model_validate(
            {
                "cells": [
                    {"arm": "A1", "epoch": "Treatment"},
                    {"arm": "A2", "epoch": "Treatment", "elements": []},
                ],
            }
        )
        assert sd.cells[0].elements == []

    def test_resolved_element_reference_passes(self):
        sd = StudyDesignInput.model_validate(
            {
                "elements": [{"name": "EL1"}, {"name": "EL2"}],
                "cells": [
                    {"arm": "A1", "epoch": "Treatment", "elements": ["EL1", "EL2"]},
                ],
            }
        )
        assert sd.cells[0].elements == ["EL1", "EL2"]

    def test_unresolved_element_reference_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            StudyDesignInput.model_validate(
                {
                    "elements": [{"name": "EL1"}],
                    "cells": [
                        {"arm": "A1", "epoch": "Treatment", "elements": ["EL_TYPO"]},
                    ],
                }
            )
        assert "undeclared element" in str(exc_info.value)
        assert "EL_TYPO" in str(exc_info.value)

    def test_cell_elements_without_any_declared_elements_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            StudyDesignInput.model_validate(
                {
                    "cells": [
                        {"arm": "A1", "epoch": "Treatment", "elements": ["EL1"]},
                    ],
                }
            )
        assert "undeclared element" in str(exc_info.value)
