from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class CriterionInput(BaseModel):
    """Structured eligibility criterion.

    Maps to ``EligibilityCriterion`` / ``EligibilityCriterionItem``:
    ``text`` is the criterion wording (required); ``identifier`` is the
    source numbering (e.g. "01", "5" — honoured verbatim so gaps in M11
    numbering, where deleted criteria are not reused, survive assembly);
    ``name`` / ``label`` / ``description`` override the generated
    defaults when supplied.
    """

    model_config = ConfigDict(strict=False)

    text: str
    identifier: str = ""
    name: str = ""
    label: str = ""
    description: str = ""


class InclusionExclusion(BaseModel):
    """Criteria lists accepting either form per entry:

    - plain string — the criterion text, everything else generated
      (back-compat with the original ``list[str]`` shape);
    - ``CriterionInput`` dict — structured, with source identifiers.
    """

    model_config = ConfigDict(strict=False)

    inclusion: list[CriterionInput | str] = []
    exclusion: list[CriterionInput | str] = []


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

    ``arm_names`` expresses cohort -> arm linkage by label-based reference into
    ``StudyDesignInput.arms[*].name``. The subset invariant is enforced at the
    ``AssemblerInput`` level (cohorts and arms live on sibling models).
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    planned_enrollment: Optional[int] = None
    characteristics: list[str] = []
    arm_names: list[str] = []
    # Cohort-level eligibility criteria (M11 maps criteria to population OR
    # cohort level). ``None`` means no cohort criteria — the cohort relies
    # on the population-level criteria alone.
    inclusion_exclusion: Optional[InclusionExclusion] = None


class PopulationInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    inclusion_exclusion: InclusionExclusion = InclusionExclusion()
    demographics: DemographicsInput = DemographicsInput()
    cohorts: list[CohortInput] = []
    planned_enrollment: Optional[int] = None
