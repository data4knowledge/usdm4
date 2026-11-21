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
from usdm4.assembler.objectives_assembler import ObjectivesAssembler
from usdm4.assembler.design_assemblers import DesignAssemblers
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
        self._objectives_assembler = ObjectivesAssembler(self._builder, self._errors)
        # One set of assemblers per design when ``study_designs`` is given
        # (GitHub 108); empty for a single design, built by the assemblers
        # above.
        self._designs: list[DesignAssemblers] = []

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
        self._objectives_assembler.clear()
        self._designs = []

    def execute(self, data: AssemblerInput | dict) -> None:
        """
        Executes the assembly process to build a complete Study object from structured data.

        Accepts either an ``AssemblerInput`` Pydantic model or a raw ``dict``.
        In both cases the input is validated against ``AssemblerInput`` and
        the **fully-defaulted** dict (schema-injected defaults included) is
        forwarded to the sub-assemblers. This means a sub-assembler can rely
        on every optional key being present (with its declared default value)
        rather than having to ``"key" in data`` everywhere.

        ``by_alias=True`` is kept on the dump so any aliased fields (e.g.
        ``amendments.impact.global`` aliased from ``global_``) are emitted
        under their alias names — sub-assemblers index by alias.

        Args:
            data: A dict (or ``AssemblerInput``) with the top-level keys
                  ``identification``, ``document``, ``population``, ``study_design``,
                  ``study``, and optionally ``amendments`` and ``soa``.
                  With ``study_designs`` (GitHub 108) one study design is
                  built per entry; see ``_execute_designs``.

        Returns:
            None
        """
        # --- input validation + normalisation --------------------------------
        if isinstance(data, dict):
            try:
                validated = AssemblerInput.model_validate(data)
            except ValidationError as e:
                location = KlassMethodLocation(self.MODULE, "execute")
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    msg = f"Schema validation: {field_path} — {error['msg']}"
                    self._errors.error(msg, location)
                return
            data = validated.model_dump(by_alias=True)
        elif isinstance(data, AssemblerInput):
            data = data.model_dump(by_alias=True)
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

            if data.get("study_designs"):
                # Amendments first, as for one design they follow the
                # population; nothing in them depends on a design.
                if data.get("amendments"):
                    self._amendments_assembler.execute(
                        data["amendments"], self._document_assembler
                    )
                self._execute_designs(data)
            else:
                # Process population data - defines subject populations and analysis sets
                self._population_assembler.execute(data["population"])

                # Process amendments data — truthy check, not key presence:
                # ``amendments`` is always present on the validated dict (Pydantic
                # default) but its value is ``None`` when no amendment was
                # supplied. Mirrors the ``soa`` branch below — and prevents the
                # sub-assembler from synthesising a default Global-scope amendment
                # for every protocol that has none (regression hunted in 0.24.0).
                if data.get("amendments"):
                    self._amendments_assembler.execute(
                        data["amendments"], self._document_assembler
                    )

                # Timelines data — truthy check, not key presence: ``soa`` is
                # always a key on the validated dict (Pydantic-injected default)
                # but its value is ``None`` when no SoA was supplied. ``soa`` is a
                # list of ``ScheduleTimelineInput`` timelines (issue 63).
                if data.get("soa"):
                    self._timeline_assembler.execute(data["soa"])

                # Process study design data - requires population assembler for cross-references
                self._study_design_assembler.execute(
                    data["study_design"],
                    self._population_assembler,
                    self._timeline_assembler,
                )

                # Objectives / endpoints / estimands — truthy check, mirroring
                # ``amendments`` and ``soa``: the key is always present on the
                # validated dict but ``None`` when not supplied. Runs after the
                # study design assembler because estimands resolve intervention
                # references and the results attach onto the created design.
                if data.get("objectives"):
                    self._objectives_assembler.execute(
                        data["objectives"],
                        self._study_design_assembler,
                        self._population_assembler,
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
                self._designs or None,
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during assembler", e, location)

    def _execute_designs(self, data: dict) -> None:
        """Build one study design per ``study_designs`` entry (GitHub 108),
        each with its own population, timeline, study design and objectives
        assemblers, run in the single-design order.

        Each design's population is the top-level ``population`` with the
        design's cohorts and planned enrollment. The population-level
        criteria are shared: the first design builds their items and every
        later design references them, so each item is held once at
        StudyVersion level. A design's ``eligibility`` adds criteria for that
        design only.

        Names are unique per class within a design, not across designs: each
        design is built in its own cross-reference scope.
        """
        cross_reference = self._builder.cross_reference
        shared = None
        for index, design in enumerate(data["study_designs"]):
            assemblers = DesignAssemblers.create(self._builder, self._errors)
            self._designs.append(assemblers)
            label = design["study_design"]["label"]
            cross_reference.scope = f"DESIGN-{index + 1}"
            try:
                population = dict(data["population"])
                population["cohorts"] = design["cohorts"]
                population["planned_enrollment"] = design["planned_enrollment"]
                assemblers.population.execute(
                    population,
                    shared=shared,
                    design_criteria=design["eligibility"],
                    design_prefix=f"{assemblers.population._label_to_name(label)}-",
                )
                if shared is None:
                    shared = assemblers.population
                if design.get("soa"):
                    assemblers.timeline.execute(design["soa"])
                assemblers.study_design.execute(
                    design["study_design"],
                    assemblers.population,
                    assemblers.timeline,
                )
                if design.get("objectives"):
                    assemblers.objectives.execute(
                        design["objectives"],
                        assemblers.study_design,
                        assemblers.population,
                    )
            finally:
                cross_reference.scope = ""

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
