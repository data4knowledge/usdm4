from typing import Optional
from pydantic import BaseModel, ConfigDict


class InterventionInput(BaseModel):
    """Maps to usdm4.api.study_intervention.StudyIntervention + Administration.

    Human-readable strings in, CDISC codes out: the assembler is responsible
    for looking up codes via cdisc_code(...) / encoder.* methods.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    type: str = ""
    role: str = ""
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None


class ArmInput(BaseModel):
    """Maps to usdm4.api.study_arm.StudyArm.

    ``intervention_names`` holds label-based references into the sibling
    ``StudyDesignInput.interventions`` list; IDs are a post-assembly concern.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    type: str = ""
    intervention_names: list[str] = []
    planned_enrollment: Optional[int] = None


class ElementInput(BaseModel):
    """Maps to usdm4.api.study_element.StudyElement.

    Optional — if omitted, the assembler synthesises one default element per
    cell.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    intervention_names: list[str] = []


class CellInput(BaseModel):
    """Maps to usdm4.api.study_cell.StudyCell.

    ``arm`` and ``epoch`` are label-based references (case-insensitive match,
    same convention as ``_add_epochs``). If ``StudyDesignInput.cells`` is
    empty the assembler derives a default arm x epoch grid.
    """

    model_config = ConfigDict(strict=False)

    arm: str
    epoch: str
    elements: list[str] = []


class StudyDesignInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    rationale: str = ""
    trial_phase: str = ""
    intervention_model: str = ""
    arms: list[ArmInput] = []
    interventions: list[InterventionInput] = []
    cells: list[CellInput] = []
    elements: list[ElementInput] = []
