import json
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.api.population_definition import StudyDesignPopulation


class PopulationAssembler(BaseAssembler):
    """
    Assembler responsible for processing population-related data and creating StudyDesignPopulation objects.

    This assembler handles the creation of study population definitions, including population criteria,
    cohort definitions, and subject enrollment information. It processes population data from the
    input structure and creates the appropriate USDM population objects.
    """

    MODULE = "usdm4.assembler.population_assembler.PopulationAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the PopulationAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._population = None
        self._cohorts = []

    def execute(self, data: dict) -> None:
        """
        Processes population data and creates a StudyDesignPopulation object.

        Args:
            data (dict): A dictionary containing population definition data.
                        The data parameter must have the following structure:

                        {
                            "label": str,              # Human-readable label for the population
                            # Additional optional fields may include:
                            # "description": str,       # Detailed description of the population
                            # "criteria": list,         # List of eligibility criteria
                            # "cohorts": list,          # List of population cohorts/subgroups
                            # "enrollment": dict,       # Subject enrollment information
                            # "analysis_populations": list  # Analysis population definitions
                        }

                        Required fields:
                        - "label": A string that provides a human-readable name for the population.
                          This will be used to generate both the display label and the internal name
                          (converted to uppercase with spaces replaced by hyphens).

                        The current implementation creates a basic population definition with:
                        - name: Generated from label (uppercase, spaces -> hyphens)
                        - label: Direct copy of the input label
                        - description: Default placeholder text
                        - includesHealthySubjects: Default to True
                        - criteria: Empty list (to be populated by future enhancements)

        Returns:
            None: The created population is stored in self._population property

        Raises:
            Exception: If population creation fails, logged via error handler
        """
        try:
            # Extract required label field and create population parameters
            # The label is used for both display purposes and name generation
            params = {
                "name": data["label"]
                .upper()
                .replace(" ", "-"),  # Convert label to internal name format
                "label": data["label"],  # Keep original label for display
                "description": "The study population, currently blank",  # Default description
                "includesHealthySubjects": True,  # Default assumption
                "criteria": [],  # Empty criteria list for now
            }

            # Create the StudyDesignPopulation object using the builder
            self._population = self._builder.create(StudyDesignPopulation, params)

        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(f"Failed during creation of population", e, location)

    @property
    def population(self):
        return self._population
