from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.builder.builder import Builder
from usdm4.api.objective import Objective
from usdm4.api.endpoint import Endpoint
from usdm4.api.estimand import Estimand
from usdm4.api.intercurrent_event import IntercurrentEvent
from usdm4.api.analysis_population import AnalysisPopulation


class ObjectivesAssembler(BaseAssembler):
    """
    Assembler responsible for creating Objective, Endpoint, Estimand,
    IntercurrentEvent and AnalysisPopulation objects from objectives data.

    Runs *after* StudyDesignAssembler: estimands reference interventions by
    name (``treatment_names``) and analysis populations reference cohorts,
    so both the study design and the population must already be assembled.
    The created objects are attached onto the existing
    ``InterventionalStudyDesign`` (``objectives`` / ``estimands`` /
    ``analysisPopulations``), following the same post-creation wiring
    precedent as cohort→arm linkage.
    """

    MODULE = "usdm4.assembler.objectives_assembler.ObjectivesAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the ObjectivesAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._objectives: list[Objective] = []
        self._estimands: list[Estimand] = []
        self._analysis_populations: list[AnalysisPopulation] = []
        self._endpoints_by_name: dict[str, Endpoint] = {}

    def execute(
        self,
        data: dict,
        study_design_assembler: StudyDesignAssembler,
        population_assembler: PopulationAssembler,
    ) -> None:
        """
        Creates objectives, endpoints, estimands and analysis populations and
        attaches them to the assembled study design.

        Args:
            data (dict): A dictionary matching ``ObjectivesInput``
                        (``usdm4.assembler.schema``):

                        - "objectives": list[dict] (text, level, endpoints)
                        - "estimands": list[dict]  (summary_measure,
                          population_text, endpoint_name, treatment_names,
                          intercurrent_events, ...)

            study_design_assembler (StudyDesignAssembler): Supplies the
                assembled study design (attachment target) and the
                interventions used to resolve ``treatment_names``.
            population_assembler (PopulationAssembler): Supplies the
                population and cohorts used to resolve
                ``population_subset_names``.

        Returns:
            None: Results are attached to the study design and exposed via
            the ``objectives`` / ``estimands`` / ``analysis_populations``
            properties.
        """
        try:
            if not data:
                self._errors.info(
                    "No objectives to build, no data",
                    KlassMethodLocation(self.MODULE, "execute"),
                )
                return

            self._objectives = self._build_objectives(data.get("objectives", []))
            self._build_estimands(
                data.get("estimands", []),
                study_design_assembler,
                population_assembler,
            )

            study_design = study_design_assembler.study_design
            if study_design is not None:
                study_design.objectives = self._objectives
                study_design.estimands = self._estimands
                study_design.analysisPopulations = self._analysis_populations
            else:
                self._errors.warning(
                    "No study design available; objectives assembled but not attached",
                    KlassMethodLocation(self.MODULE, "execute"),
                )
        except Exception as e:
            self._errors.exception(
                "Failed during creation of objectives",
                e,
                KlassMethodLocation(self.MODULE, "execute"),
            )

    @property
    def objectives(self) -> list[Objective]:
        return self._objectives

    @property
    def estimands(self) -> list[Estimand]:
        return self._estimands

    @property
    def analysis_populations(self) -> list[AnalysisPopulation]:
        return self._analysis_populations

    # ------------------------------------------------------------------
    # Objectives + endpoints
    # ------------------------------------------------------------------

    def _build_objectives(self, items: list[dict]) -> list[Objective]:
        """Build one ``Objective`` (with nested ``Endpoint``s) per item.

        Names are taken from the input where present, generated
        (``OBJECTIVE-<n>`` / ``ENDPOINT-<n>-<m>``) where absent. Named
        endpoints are indexed for estimand reference resolution.
        """
        result: list[Objective] = []
        for index, item in enumerate(items, start=1):
            try:
                endpoints = self._build_endpoints(item.get("endpoints", []), index)
                params = {
                    "name": self._object_name(item, f"OBJECTIVE-{index}"),
                    "label": item.get("label") or "",
                    "description": item.get("description") or "",
                    "text": item["text"],
                    "level": self._encoder.objective_level(item.get("level", "")),
                    "endpoints": endpoints,
                }
                obj = self._builder.create(Objective, params)
                if obj is not None:
                    result.append(obj)
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of objective {index}",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_objectives"),
                )
        return result

    def _build_endpoints(
        self, items: list[dict], objective_index: int
    ) -> list[Endpoint]:
        result: list[Endpoint] = []
        for index, item in enumerate(items, start=1):
            try:
                input_name = (item.get("name") or "").strip()
                params = {
                    "name": input_name or f"ENDPOINT-{objective_index}-{index}",
                    "label": item.get("label") or "",
                    "description": item.get("description") or "",
                    "text": item["text"],
                    "purpose": item.get("purpose") or "",
                    "level": self._encoder.endpoint_level(item.get("level", "")),
                }
                obj = self._builder.create(Endpoint, params)
                if obj is not None:
                    result.append(obj)
                    if input_name:
                        self._endpoints_by_name[input_name] = obj
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of endpoint {objective_index}-{index}",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_endpoints"),
                )
        return result

    # ------------------------------------------------------------------
    # Estimands + analysis populations
    # ------------------------------------------------------------------

    def _build_estimands(
        self,
        items: list[dict],
        study_design_assembler: StudyDesignAssembler,
        population_assembler: PopulationAssembler,
    ) -> None:
        interventions_ci = self._interventions_by_ref(study_design_assembler)
        for index, item in enumerate(items, start=1):
            try:
                endpoint = self._endpoints_by_name.get(item["endpoint_name"])
                if endpoint is None:
                    # Schema validation enforces this up front for dict
                    # input routed through AssemblerInput — guard anyway
                    # for direct assembler use.
                    self._errors.warning(
                        f"Estimand {index} references unknown endpoint "
                        f"'{item['endpoint_name']}'; skipping.",
                        KlassMethodLocation(self.MODULE, "_build_estimands"),
                    )
                    continue

                intervention_ids = self._resolve_treatments(
                    item.get("treatment_names", []), interventions_ci, index
                )
                analysis_population = self._build_analysis_population(
                    item, population_assembler, index
                )
                if analysis_population is None:
                    continue
                intercurrent_events = self._build_intercurrent_events(
                    item.get("intercurrent_events", []), index
                )
                params = {
                    "name": self._object_name(item, f"ESTIMAND-{index}"),
                    "label": item.get("label") or "",
                    "description": item.get("description") or "",
                    "populationSummary": item["summary_measure"],
                    "analysisPopulationId": analysis_population.id,
                    "interventionIds": intervention_ids,
                    "variableOfInterestId": endpoint.id,
                    "intercurrentEvents": intercurrent_events,
                }
                obj = self._builder.create(Estimand, params)
                if obj is not None:
                    self._estimands.append(obj)
                    self._analysis_populations.append(analysis_population)
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of estimand {index}",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_estimands"),
                )

    def _build_analysis_population(
        self,
        item: dict,
        population_assembler: PopulationAssembler,
        index: int,
    ) -> AnalysisPopulation | None:
        """One ``AnalysisPopulation`` per estimand.

        ``population_subset_names`` resolve against cohort names (input or
        assembled form) and the population label; when empty, the analysis
        population subsets the whole study population.
        """
        try:
            subset_ids = self._resolve_population_subsets(
                item.get("population_subset_names", []),
                population_assembler,
                index,
            )
            params = {
                "name": f"AP-{index}",
                "label": item.get("label") or "",
                "description": "",
                "text": item.get("population_text") or "",
                "subsetOfIds": subset_ids,
            }
            return self._builder.create(AnalysisPopulation, params)
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of analysis population {index}",
                e,
                KlassMethodLocation(self.MODULE, "_build_analysis_population"),
            )
            return None

    def _build_intercurrent_events(
        self, items: list[dict], estimand_index: int
    ) -> list[IntercurrentEvent]:
        result: list[IntercurrentEvent] = []
        for index, item in enumerate(items, start=1):
            try:
                params = {
                    "name": self._object_name(item, f"ICE-{estimand_index}-{index}"),
                    "label": item.get("label") or "",
                    "description": item.get("description") or "",
                    "text": item["text"],
                    "strategy": item.get("strategy") or "",
                }
                obj = self._builder.create(IntercurrentEvent, params)
                if obj is not None:
                    result.append(obj)
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of intercurrent event "
                    f"{estimand_index}-{index}",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_intercurrent_events"),
                )
        return result

    # ------------------------------------------------------------------
    # Reference resolution
    # ------------------------------------------------------------------

    def _interventions_by_ref(
        self, study_design_assembler: StudyDesignAssembler
    ) -> dict:
        """Case-insensitive lookup over assembled interventions.

        Keys cover both the assembled ``name`` (upper, dash-separated) and
        the original ``label``, so input references written either way
        resolve.
        """
        result = {}
        for intervention in study_design_assembler.study_interventions:
            result[intervention.name.upper()] = intervention
            if intervention.label:
                result[intervention.label.upper()] = intervention
        return result

    def _resolve_treatments(
        self, refs: list[str], interventions_ci: dict, index: int
    ) -> list[str]:
        ids: list[str] = []
        for ref in refs:
            intervention = interventions_ci.get(
                self._label_to_name(ref)
            ) or interventions_ci.get(ref.upper())
            if intervention is None:
                self._errors.warning(
                    f"Estimand {index} references unknown intervention "
                    f"'{ref}'; skipping reference.",
                    KlassMethodLocation(self.MODULE, "_resolve_treatments"),
                )
                continue
            ids.append(intervention.id)
        return ids

    def _resolve_population_subsets(
        self,
        refs: list[str],
        population_assembler: PopulationAssembler,
        index: int,
    ) -> list[str]:
        population = population_assembler.population
        if not refs:
            return [population.id] if population is not None else []
        cohorts_ci = {}
        for cohort in population_assembler.cohorts:
            cohorts_ci[cohort.name.upper()] = cohort
            if cohort.label:
                cohorts_ci[cohort.label.upper()] = cohort
        ids: list[str] = []
        for ref in refs:
            target = cohorts_ci.get(self._label_to_name(ref)) or cohorts_ci.get(
                ref.upper()
            )
            if (
                target is None
                and population is not None
                and (
                    ref.upper() == (population.label or "").upper()
                    or self._label_to_name(ref) == population.name.upper()
                )
            ):
                target = population
            if target is None:
                self._errors.warning(
                    f"Estimand {index} references unknown population subset "
                    f"'{ref}'; skipping reference.",
                    KlassMethodLocation(self.MODULE, "_resolve_population_subsets"),
                )
                continue
            ids.append(target.id)
        return ids

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _object_name(self, item: dict, generated: str) -> str:
        """Input name → assembled name, or the generated fallback."""
        input_name = (item.get("name") or "").strip()
        if input_name:
            return self._label_to_name(input_name)
        label = (item.get("label") or "").strip()
        if label:
            return self._label_to_name(label)
        return generated
