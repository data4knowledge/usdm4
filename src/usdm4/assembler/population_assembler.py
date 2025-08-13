import json
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.api.population_definition import StudyDesignPopulation


class PopulationAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.population_assembler.PopulationAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the IdentificationAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._population = None
        self._cohorts = []

    def execute(self, data: dict) -> None:
        try:
            params = {
                "name": data["label"].upper().replace(" ", "-"),
                "label": data["label"],
                "description": "The study population, currently blank",
                "includesHealthySubjects": True,
                "criteria": [],
            }
            self._population = self._builder.create(StudyDesignPopulation, params)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(f"Failed during creation of population", e, location)

    @property
    def population(self):
        return self._population
