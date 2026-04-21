from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class InclusionExclusion(BaseModel):
    model_config = ConfigDict(strict=False)

    inclusion: list[str] = []
    exclusion: list[str] = []


class DemographicsInput(BaseModel):
    """Maps to PopulationDefinition fields: plannedAge (Range),
    plannedSex (list[Code]), includesHealthySubjects.

    ``sex`` drives ``plannedSex`` composition: ``"ALL"`` yields the two-entry
    list, ``"MALE"`` / ``"FEMALE"`` yield single-entry lists.
    """

    model_config = ConfigDict(strict=False)

    age_min: Optional[float] = None
    age_max: Optional[float] = None
    age_unit: str = "Years"
    sex: Literal["ALL", "MALE", "FEMALE"] = "ALL"
    healthy_volunteers: bool = False


class CohortInput(BaseModel):
    """Maps to usdm4.api.population_definition.StudyCohort.

    Each free-text ``characteristic`` becomes a ``Characteristic``
    (``SyntaxTemplate``) object at assembly time, mirroring how
    ``EligibilityCriterion`` wraps inclusion/exclusion text.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    planned_enrollment: Optional[int] = None
    characteristics: list[str] = []


class PopulationInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    inclusion_exclusion: InclusionExclusion = InclusionExclusion()
    demographics: DemographicsInput = DemographicsInput()
    cohorts: list[CohortInput] = []
    planned_enrollment: Optional[int] = None
