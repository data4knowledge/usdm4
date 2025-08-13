import json
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.builder.builder import Builder
from usdm4.api.study_design import InterventionalStudyDesign


class StudyDesignAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.study_design_assembler.StudyDesignAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the IdentificationAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._study_design = None

    def execute(self, data: dict, population_assembler: PopulationAssembler) -> None:
        try:
            intervention_model_code = self._builder.cdisc_code(
                "C82639", "Parallel Study"
            )
            self._study_design = self._builder.create(
                InterventionalStudyDesign,
                {
                    "name": self._label_to_name(data["label"]),
                    "label": data["label"],
                    "description": "A study design",
                    "rationale": data["rationale"],
                    "model": intervention_model_code,
                    "arms": [],
                    "studyCells": [],
                    "epochs": [],
                    "population": population_assembler.population,
                    "objectives": [],  # objectives,
                    "estimands": [],  # estimands,
                    "studyInterventions": [],  # interventions,
                    "analysisPopulations": [],  # analysis_populations,
                    "studyPhase": data["trial_phase"],
                },
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(f"Failed during creation of population", e, location)

    @property
    def study_design(self) -> InterventionalStudyDesign:
        return self._study_design
