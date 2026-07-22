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


# ----------------------------------------------------------------------
# Administrations + duration (issue 42)
# ----------------------------------------------------------------------

from src.usdm4.assembler.schema.study_design_schema import (  # noqa: E402
    AdministrationDurationInput,
    AdministrationInput,
)


class TestAdministrationDurationInput:
    def test_defaults(self):
        duration = AdministrationDurationInput()
        assert duration.description == ""
        assert duration.will_vary is False
        assert duration.will_vary_reason == ""
        assert duration.quantity is None

    def test_populated(self):
        duration = AdministrationDurationInput(
            description="IV bolus over 1 minute",
            will_vary=True,
            will_vary_reason="Adaptive",
            quantity="1 min",
        )
        assert duration.quantity == "1 min"
        assert duration.will_vary is True


class TestAdministrationInput:
    def test_defaults(self):
        admin = AdministrationInput()
        assert admin.name == ""
        assert admin.label == ""
        assert admin.description == ""
        assert admin.dose is None
        assert admin.route is None
        assert admin.frequency is None
        assert admin.duration is None

    def test_with_duration(self):
        admin = AdministrationInput(
            name="IV Dose",
            route="Intravenous",
            duration={"quantity": "1 min"},
        )
        assert isinstance(admin.duration, AdministrationDurationInput)
        assert admin.duration.quantity == "1 min"


class TestInterventionAdministrations:
    def test_administrations_list_accepted(self):
        intervention = InterventionInput(
            name="Drug A",
            administrations=[
                {"name": "Oral Dose", "route": "Oral"},
                {"route": "Intravenous", "duration": {"quantity": "1 min"}},
            ],
        )
        assert len(intervention.administrations) == 2
        assert isinstance(intervention.administrations[0], AdministrationInput)

    def test_flat_fields_still_accepted(self):
        intervention = InterventionInput(
            name="Drug A", dose="10 mg", route="Oral", frequency="Once"
        )
        assert intervention.administrations == []
        assert intervention.dose == "10 mg"

    def test_flat_and_administrations_together_rejected(self):
        for flat in ({"dose": "10 mg"}, {"route": "Oral"}, {"frequency": "Once"}):
            with pytest.raises(ValidationError, match="use one or the other"):
                InterventionInput(
                    name="Drug A",
                    administrations=[{"route": "Oral"}],
                    **flat,
                )


# ----------------------------------------------------------------------
# Arm -> intervention references (issue 44)
# ----------------------------------------------------------------------


class TestArmInterventionReferences:
    def test_valid_references_accepted(self):
        design = StudyDesignInput(
            label="D",
            interventions=[{"name": "Drug A"}, {"name": "Placebo"}],
            arms=[{"name": "Active", "intervention_names": ["Drug A", "Placebo"]}],
        )
        assert design.arms[0].intervention_names == ["Drug A", "Placebo"]

    def test_undeclared_reference_rejected(self):
        with pytest.raises(ValidationError, match="undeclared intervention"):
            StudyDesignInput(
                label="D",
                interventions=[{"name": "Drug A"}],
                arms=[{"name": "Active", "intervention_names": ["Drug X"]}],
            )

    def test_no_interventions_declared_message(self):
        with pytest.raises(ValidationError, match=r"\(none\)"):
            StudyDesignInput(
                label="D",
                arms=[{"name": "Active", "intervention_names": ["Drug A"]}],
            )

    def test_arms_without_references_pass(self):
        design = StudyDesignInput(
            label="D", arms=[{"name": "Active"}, {"name": "Control"}]
        )
        assert len(design.arms) == 2


# ----------------------------------------------------------------------
# Products (issue 48)
# ----------------------------------------------------------------------

from src.usdm4.assembler.schema.study_design_schema import (  # noqa: E402
    ProductInput,
    SubstanceInput,
)


class TestProductInput:
    def test_defaults(self):
        product = ProductInput(name="Drug A Tablet")
        assert product.dose_form == ""
        assert product.product_designation == ""
        assert product.substances == []

    def test_with_substances(self):
        product = ProductInput(
            name="Drug A Tablet",
            dose_form="Tablet",
            product_designation="IMP",
            substances=[{"name": "Drug A", "strength": "10 mg"}],
        )
        assert isinstance(product.substances[0], SubstanceInput)
        assert product.substances[0].strength == "10 mg"

    def test_name_required(self):
        with pytest.raises(ValidationError):
            ProductInput(dose_form="Tablet")


class TestAdministrationProductReferences:
    def test_valid_reference_accepted(self):
        design = StudyDesignInput(
            label="D",
            products=[{"name": "Drug A Tablet"}],
            interventions=[
                {
                    "name": "Drug A",
                    "administrations": [
                        {"route": "Oral", "product_name": "Drug A Tablet"}
                    ],
                }
            ],
        )
        admin = design.interventions[0].administrations[0]
        assert admin.product_name == "Drug A Tablet"

    def test_undeclared_reference_rejected(self):
        with pytest.raises(ValidationError, match="undeclared product"):
            StudyDesignInput(
                label="D",
                interventions=[
                    {
                        "name": "Drug A",
                        "administrations": [{"product_name": "Ghost"}],
                    }
                ],
            )

    def test_empty_reference_ignored(self):
        design = StudyDesignInput(
            label="D",
            interventions=[{"name": "Drug A", "administrations": [{"route": "Oral"}]}],
        )
        assert design.interventions[0].administrations[0].product_name == ""
