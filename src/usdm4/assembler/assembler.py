from pydantic import ValidationError
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.builder.builder import Builder
from usdm4.assembler.schema import AssemblerInput
from usdm4.assembler.identification_assembler import IdentificationAssembler
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.document_assembler import DocumentAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.assembler.amendments_assembler import AmendmentsAssembler
from usdm4.assembler.study_assembler import StudyAssembler
from usdm4.assembler.timeline_assembler import TimelineAssembler
from usdm4.api.study import Study
from usdm4.api.wrapper import Wrapper
from usdm4.__info__ import __model_version__ as usdm_version


class Assembler:
    """
    Main assembler class responsible for orchestrating the assembly of a complete Study object
    from structured input data.

    The Assembler coordinates multiple specialized assemblers to process different domains
    of study data in the correct sequence, ensuring proper cross-references and dependencies
    are maintained throughout the assembly process.

    The assembly process follows a specific order to handle data dependencies:
    1. Identification (study IDs and versions)
    2. Documents (protocols and amendments)
    3. Populations (subject populations and analysis sets)
    4. Study Design (arms, epochs, activities, timelines)
    5. Study (core study information and final assembly)
    """

    MODULE = "usdm4.assembler.assembler.Assembler"

    def __init__(self, root_path: str, errors: Errors):
        self._errors = errors
        self._builder = Builder(root_path, self._errors)
        self._identification_assembler = IdentificationAssembler(
            self._builder, self._errors
        )
        self._population_assembler = PopulationAssembler(self._builder, self._errors)
        self._amendments_assembler = AmendmentsAssembler(self._builder, self._errors)
        self._document_assembler = DocumentAssembler(self._builder, self._errors)
        self._study_design_assembler = StudyDesignAssembler(self._builder, self._errors)
        self._study_assembler = StudyAssembler(self._builder, self._errors)
        self._timeline_assembler = TimelineAssembler(self._builder, self._errors)

    def clear(self):
        self._errors.clear()
        self._builder.clear()
        self._identification_assembler.clear()
        self._population_assembler.clear()
        self._amendments_assembler.clear()
        self._document_assembler.clear()
        self._study_design_assembler.clear()
        self._study_assembler.clear()
        self._timeline_assembler.clear()

    def execute(self, data: AssemblerInput | dict) -> None:
        """
        Executes the assembly process to build a complete Study object from structured data.

        Accepts either an ``AssemblerInput`` Pydantic model or a raw ``dict``.  When a
        dict is supplied it is validated against the ``AssemblerInput`` schema; structural
        errors are reported via the shared ``Errors`` instance and the method returns
        early.  After validation the **original** dict is forwarded to the sub-assemblers
        so that their existing key-access patterns are preserved unchanged.

        Args:
            data: A dict (or ``AssemblerInput``) with the top-level keys
                  ``identification``, ``document``, ``population``, ``study_design``,
                  ``study``, and optionally ``amendments`` and ``soa``.

        Returns:
            None
        """
        # --- input validation ------------------------------------------------
        if isinstance(data, dict):
            try:
                AssemblerInput.model_validate(data)
            except ValidationError as e:
                location = KlassMethodLocation(self.MODULE, "execute")
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    msg = f"Schema validation: {field_path} — {error['msg']}"
                    self._errors.error(msg, location)
                return
        elif isinstance(data, AssemblerInput):
            data = data.model_dump(by_alias=True, exclude_none=True)
        else:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.error(
                f"Invalid input type: expected dict or AssemblerInput, "
                f"got {type(data).__name__}",
                location,
            )
            return

        # --- assembly ---------------------------------------------------------
        try:
            # Process identification data - establishes study identity and versioning
            self._identification_assembler.execute(data["identification"])

            # Process document data - sets up protocol documents
            self._document_assembler.execute(data["document"])

            # Process population data - defines subject populations and analysis sets
            self._population_assembler.execute(data["population"])

            # Process amendments data
            self._amendments_assembler.execute(
                data["amendments"], self._document_assembler
            )

            # Timelines data
            if "soa" in data:
                self._timeline_assembler.execute(data["soa"])

            # Process study design data - requires population assembler for cross-references
            self._study_design_assembler.execute(
                data["study_design"],
                self._population_assembler,
                self._timeline_assembler,
            )

            # Process core study data - requires all other assemblers for final assembly
            self._study_assembler.execute(
                data["study"],
                self._identification_assembler,
                self._study_design_assembler,
                self._document_assembler,
                self._population_assembler,
                self._amendments_assembler,
                self._timeline_assembler,
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during assembler", e, location)

    @property
    def study(self) -> Study:
        return self._study_assembler.study

    def wrapper(self, name: str, version: str) -> Wrapper | None:
        try:
            params = {
                "study": self._study_assembler.study,
                "usdmVersion": usdm_version,
                "systemVersion": version,
                "systemName": name,
            }
            return self._builder.create(Wrapper, params)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during assembler", e, location)
            return None
