from pydantic import BaseModel, ConfigDict, model_validator

from usdm4.assembler.schema.identification_schema import IdentificationInput
from usdm4.assembler.schema.document_schema import DocumentInput
from usdm4.assembler.schema.population_schema import PopulationInput
from usdm4.assembler.schema.amendments_schema import AmendmentsInput
from usdm4.assembler.schema.study_design_schema import StudyDesignInput
from usdm4.assembler.schema.study_schema import StudyInput
from usdm4.assembler.schema.timeline_schema import TimelineInput


class AssemblerInput(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    identification: IdentificationInput
    document: DocumentInput
    population: PopulationInput
    study_design: StudyDesignInput
    study: StudyInput
    # ``amendments`` is treated as a presence-bearing optional, mirroring
    # ``soa`` below: ``None`` means "no amendment supplied", a populated
    # ``AmendmentsInput`` means "an amendment was supplied". A bare
    # ``AmendmentsInput()`` default would be indistinguishable from a real
    # but-empty input once dumped, which silently caused every original
    # protocol to gain a synthetic global-scope amendment after the
    # ``Assembler.execute`` change in 0.24.0.
    amendments: AmendmentsInput | None = None
    soa: TimelineInput | None = None

    @model_validator(mode="after")
    def _check_cohort_arm_references(self) -> "AssemblerInput":
        """Every ``cohort.arm_names`` entry must resolve to a declared arm.

        Cross-model invariant: cohorts live on ``PopulationInput`` while arms
        live on ``StudyDesignInput``, so the subset check only makes sense
        here at the top-level where both are visible.
        """
        arm_names = {a.name for a in self.study_design.arms}
        for cohort in self.population.cohorts:
            for ref in cohort.arm_names:
                if ref not in arm_names:
                    declared = sorted(arm_names) if arm_names else "(none)"
                    raise ValueError(
                        f"cohort {cohort.name!r} references undeclared arm "
                        f"{ref!r}; declared arms: {declared}"
                    )
        return self

    @classmethod
    def validate_strict(cls, data: dict) -> tuple["AssemblerInput", list[str]]:
        """Validate with warnings for empty required fields."""
        instance = cls.model_validate(data)
        warnings = []
        if not instance.identification.titles.official:
            warnings.append("identification.titles.official is empty")
        if not instance.document.document.version:
            warnings.append("document.document.version is empty")
        if not instance.study.version:
            warnings.append("study.version is empty")
        return instance, warnings
