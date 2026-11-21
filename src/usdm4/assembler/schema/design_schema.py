from typing import Optional
from pydantic import BaseModel, ConfigDict

from usdm4.assembler.schema.population_schema import CohortInput, InclusionExclusion
from usdm4.assembler.schema.study_design_schema import StudyDesignInput
from usdm4.assembler.schema.schedule_timeline_schema import ScheduleTimelineInput
from usdm4.assembler.schema.objectives_schema import ObjectivesInput


class DesignInput(BaseModel):
    """One study design of a study with several (GitHub 108), e.g. a
    substudy of a master protocol.

    The design's label is ``study_design.label``; it is required and must be
    unique across the designs. Everything here belongs to this design only:
    its arms and interventions, its SoA timelines (and so its epochs,
    encounters and activities), its objectives, endpoints and estimands, and
    its cohorts.

    Eligibility is shared: the criteria on ``AssemblerInput.population``
    apply to every design. Their text is held once, as StudyVersion
    ``eligibilityCriterionItems``, and every design's criteria reference it.
    ``eligibility`` adds criteria for this design only, after the shared
    ones. The rest of ``AssemblerInput.population`` (label, demographics)
    is used for every design's population; ``planned_enrollment`` is this
    design's own.
    """

    model_config = ConfigDict(strict=False)

    study_design: StudyDesignInput
    soa: list[ScheduleTimelineInput] | None = None
    objectives: ObjectivesInput | None = None
    cohorts: list[CohortInput] = []
    eligibility: InclusionExclusion | None = None
    planned_enrollment: Optional[int] = None
