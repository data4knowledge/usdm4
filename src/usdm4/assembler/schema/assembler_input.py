from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from usdm4.assembler.schema.identification_schema import IdentificationInput
from usdm4.assembler.schema.document_schema import DocumentInput
from usdm4.assembler.schema.population_schema import PopulationInput
from usdm4.assembler.schema.amendments_schema import AmendmentsInput
from usdm4.assembler.schema.study_design_schema import StudyDesignInput
from usdm4.assembler.schema.study_schema import StudyInput
from usdm4.assembler.schema.schedule_timeline_schema import (
    ScheduleTimelineInput,
    check_copies,
)
from usdm4.assembler.schema.objectives_schema import ObjectivesInput
from usdm4.assembler.schema.design_schema import DesignInput


class AssemblerInput(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    identification: IdentificationInput
    document: DocumentInput
    population: PopulationInput
    # ``study_designs`` is presence-bearing (GitHub 108): ``None`` means one
    # design, given by ``study_design``, ``soa`` and ``objectives`` and the
    # cohorts on ``population``, exactly as before. A list means one design
    # per entry, each carrying its own design, SoA, objectives and cohorts;
    # the top-level ``study_design``, ``soa``, ``objectives`` and
    # ``population.cohorts`` must then not be supplied. ``population``'s
    # criteria are shared by every design. Declared before ``study_design``
    # so that field's check can see it.
    study_designs: list[DesignInput] | None = None
    # The single design: required unless ``study_designs`` is supplied.
    study_design: StudyDesignInput | None = Field(default=None, validate_default=True)
    study: StudyInput
    # ``amendments`` is treated as a presence-bearing optional, mirroring
    # ``soa`` below: ``None`` means "no amendment supplied", a populated
    # ``AmendmentsInput`` means "an amendment was supplied". A bare
    # ``AmendmentsInput()`` default would be indistinguishable from a real
    # but-empty input once dumped, which silently caused every original
    # protocol to gain a synthetic global-scope amendment after the
    # ``Assembler.execute`` change in 0.24.0.
    amendments: AmendmentsInput | None = None
    # ``soa`` is presence-bearing (``None`` means no SoA supplied): a list of
    # timelines, each a ``ScheduleTimelineInput`` — header values structured
    # by the caller, printed text carried as labels only (issues 63, 73;
    # ``docs/spec/timeline_assembler.md`` U4-35). Exactly one built timeline is
    # flagged as the main timeline (see ``TimelineAssembler.execute``).
    soa: list[ScheduleTimelineInput] | None = None
    # ``objectives`` follows the same presence-bearing optional pattern:
    # ``None`` means "no objectives supplied" and the objectives assembler
    # is skipped entirely, leaving the study design's objectives/estimands/
    # analysisPopulations as empty lists.
    objectives: ObjectivesInput | None = None

    @field_validator("study_design", mode="after")
    @classmethod
    def _study_design_required(
        cls, value: StudyDesignInput | None, info: ValidationInfo
    ) -> StudyDesignInput | None:
        if value is None and info.data.get("study_designs") is None:
            raise ValueError(
                "Field required (or study_designs, for a study with several designs)"
            )
        return value

    @model_validator(mode="after")
    def _check_study_designs(self) -> "AssemblerInput":
        """Several designs replace the single design's inputs, never
        add to them, and each needs its own label."""
        if self.study_designs is None:
            return self
        if not self.study_designs:
            raise ValueError("study_designs, when supplied, may not be empty")
        supplied = [
            name
            for name, given in (
                ("study_design", self.study_design is not None),
                ("soa", self.soa is not None),
                ("objectives", self.objectives is not None),
                ("population.cohorts", bool(self.population.cohorts)),
            )
            if given
        ]
        if supplied:
            raise ValueError(
                f"study_designs is supplied, so {', '.join(supplied)} must not "
                f"be; give them on each design instead"
            )
        labels = [d.study_design.label.strip() for d in self.study_designs]
        if not all(labels):
            raise ValueError("every entry in study_designs needs a study_design.label")
        repeated = sorted({x for x in labels if labels.count(x) > 1})
        if repeated:
            raise ValueError(
                f"study design labels must be unique; repeated: {repeated}"
            )
        return self

    @model_validator(mode="after")
    def _check_cohort_arm_references(self) -> "AssemblerInput":
        """Every ``cohort.arm_names`` entry must resolve to a declared arm
        of the same design.

        Cross-model invariant: cohorts live on ``PopulationInput`` (or on the
        ``DesignInput``) while arms live on ``StudyDesignInput``, so the
        subset check only makes sense here where both are visible.
        """
        for study_design, cohorts in self._designs(
            lambda d: d.cohorts, self.population.cohorts
        ):
            arm_names = {a.name for a in study_design.arms}
            for cohort in cohorts:
                for ref in cohort.arm_names:
                    if ref not in arm_names:
                        declared = sorted(arm_names) if arm_names else "(none)"
                        raise ValueError(
                            f"cohort {cohort.name!r} references undeclared arm "
                            f"{ref!r}; declared arms: {declared}"
                        )
        return self

    def _designs(self, part, single) -> list[tuple[StudyDesignInput, object]]:
        """Each design with one of its parts: ``part`` reads it from a
        ``DesignInput``, ``single`` is the single design's."""
        if self.study_designs is None:
            return [(self.study_design, single)]
        return [(d.study_design, part(d)) for d in self.study_designs]

    @model_validator(mode="after")
    def _check_estimand_treatment_references(self) -> "AssemblerInput":
        """Every ``estimand.treatment_names`` entry must resolve to a
        declared intervention.

        Cross-model invariant mirroring ``_check_cohort_arm_references``:
        estimands live on ``ObjectivesInput`` while interventions live on
        ``StudyDesignInput``, so the subset check belongs here at the
        top level where both are visible; per design, against that
        design's interventions. (Estimand→endpoint references are
        intra-model and validated on ``ObjectivesInput`` itself.)
        """
        for study_design, objectives in self._designs(
            lambda d: d.objectives, self.objectives
        ):
            if objectives is None:
                continue
            intervention_names = {i.name for i in study_design.interventions}
            for estimand in objectives.estimands:
                for ref in estimand.treatment_names:
                    if ref not in intervention_names:
                        declared = (
                            sorted(intervention_names)
                            if intervention_names
                            else "(none)"
                        )
                        raise ValueError(
                            f"estimand {estimand.name or estimand.endpoint_name!r} "
                            f"references undeclared intervention {ref!r}; "
                            f"declared interventions: {declared}"
                        )
        return self

    @model_validator(mode="after")
    def _check_timeline_copies(self) -> "AssemblerInput":
        """A copied column names an earlier timeline's column (issue 75).
        Across timelines, so checked here where every timeline is visible;
        per design, since a copy never crosses designs."""
        for _, soa in self._designs(lambda d: d.soa, self.soa):
            if soa:
                check_copies(soa)
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
