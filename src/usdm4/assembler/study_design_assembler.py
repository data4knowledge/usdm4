import re
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.timeline_assembler import TimelineAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.builder.builder import Builder
from usdm4.api.study_design import InterventionalStudyDesign
from usdm4.api.study_arm import StudyArm
from usdm4.api.study_cell import StudyCell
from usdm4.api.study_element import StudyElement
from usdm4.api.study_epoch import StudyEpoch
from usdm4.api.study_intervention import StudyIntervention
from usdm4.api.administration import Administration
from usdm4.api.duration import Duration
from usdm4.api.quantity_range import Quantity


class StudyDesignAssembler(BaseAssembler):
    """
    Assembler responsible for creating InterventionalStudyDesign objects from study design data.

    This assembler processes study design information including intervention models, study phases,
    arms, epochs, cells, and other structural elements that define how the study is conducted.
    It creates the core study design structure that serves as the framework for the clinical trial.
    """

    MODULE = "usdm4.assembler.study_design_assembler.StudyDesignAssembler"

    # Default dataOriginType for StudyArm — codelist C188727.
    # "Data Generated Within Study" (C188866) is the sensible default for
    # a freshly-assembled interventional protocol: we always assume arm
    # data originates in the current study unless told otherwise.
    DATA_ORIGIN_TYPE_CODE = "C188866"
    DATA_ORIGIN_TYPE_DECODE = "Data Generated Within Study"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the StudyDesignAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._study_design = None
        self._study_interventions: list[StudyIntervention] = []

    def execute(
        self,
        data: dict,
        population_assembler: PopulationAssembler,
        timeline_assembler: TimelineAssembler,
    ) -> None:
        """
        Creates an InterventionalStudyDesign object from study design data.

        Args:
            data (dict): A dictionary containing study design information.
                        See ``StudyDesignInput`` (``usdm4.assembler.schema``) for
                        the full list of supported fields. Commonly used:

                        - "label": Display name for the study design
                        - "rationale": Explanation for this design choice
                        - "trial_phase": Clinical development phase
                        - "intervention_model": Parallel / Crossover / ...
                        - "arms": list[dict]     (name, type, intervention_names, ...)
                        - "interventions": list[dict] (name, type, role, dose, route, frequency)
                        - "elements": list[dict] (name, intervention_names)
                        - "cells": list[dict]    (arm, epoch, elements)

            population_assembler (PopulationAssembler): Assembler containing the study
                population definition. Cohorts live on that assembler and are wired
                back onto ``StudyArm.populationIds`` here.
            timeline_assembler (TimelineAssembler): Assembler containing the timelines
                — epochs in particular are resolved by label for cell construction.

        Returns:
            None: The created study design is stored in ``self._study_design``; the
            intervention list is additionally exposed via ``self.study_interventions``
            so ``StudyAssembler`` can thread it onto ``StudyVersion.studyInterventions``.
        """
        try:
            # Pass 1 — interventions. Build once, index by name for pass 2a.
            interventions_by_name = self._build_interventions(
                data.get("interventions", [])
            )

            # Pass 2a — elements. Resolve intervention_names → studyInterventionIds.
            elements_by_name = self._build_elements(
                data.get("elements", []), interventions_by_name
            )

            # Pass 2b — arms. Resolve type via encoder; populationIds is finalised
            # later once cohorts know which arms they belong to.
            arms_by_name = self._build_arms(data.get("arms", []))

            # Pass 2c — cells. Synthesise arm×epoch grid if the input has arms
            # but no cells; label lookups are case-insensitive (_add_epochs
            # convention).
            cells_list = self._build_cells(
                data.get("cells", []),
                arms_by_name,
                elements_by_name,
                timeline_assembler.epochs,
            )

            # Arm → intervention wiring. ``ArmInput.intervention_names`` has
            # no direct home on the API StudyArm (USDM expresses the
            # linkage as cell → element → intervention), so it is encoded
            # via elements — synthesised ones when the input declared none.
            self._wire_arm_interventions(
                data.get("arms", []),
                arms_by_name,
                interventions_by_name,
                elements_by_name,
                cells_list,
                had_explicit_elements=bool(data.get("elements")),
            )

            # Cohort → arm wiring. Cohorts were assembled in PopulationAssembler
            # with arm_names already captured; finalise StudyArm.populationIds
            # here, the one place with visibility into both the population and
            # the arm objects.
            self._wire_cohorts_to_arms(population_assembler, arms_by_name)

            # Persist for StudyAssembler (interventions live on StudyVersion,
            # not on StudyDesign — StudyDesign only stores the id references).
            self._study_interventions = list(interventions_by_name.values())

            # Intervention model — human label → CDISC Code via encoder.
            intervention_model_code = self._encoder.intervention_model(
                data.get("intervention_model", "")
            )

            # Create the InterventionalStudyDesign object.
            #
            # ``studyType`` is required by DDF00227 ("an interventional study
            # must be specified using the InterventionalStudyDesign class").
            # We always set the SDTM ``Interventional Study`` code (C98388);
            # there's no ``observational`` branch in this assembler today, so
            # the choice is unambiguous. The decode is overridden by Bug 2's
            # canonical-CT-decode lookup at Code-creation time.
            self._study_design = self._builder.create(
                InterventionalStudyDesign,
                {
                    "name": self._label_to_name(data["label"]),
                    "label": data["label"],
                    "description": "A study design",
                    "rationale": data["rationale"],
                    "model": intervention_model_code,
                    "studyType": self._builder.cdisc_code(
                        "C98388", "Interventional Study"
                    ),
                    "arms": list(arms_by_name.values()),
                    "studyCells": cells_list,
                    "elements": list(elements_by_name.values()),
                    "epochs": timeline_assembler.epochs,
                    "encounters": timeline_assembler.encounters,
                    "activities": timeline_assembler.activities,
                    "population": population_assembler.population,
                    "objectives": [],
                    "estimands": [],
                    "studyInterventionIds": [i.id for i in self._study_interventions],
                    "analysisPopulations": [],
                    "studyPhase": self._encoder.phase(data["trial_phase"]),
                    "scheduleTimelines": timeline_assembler.timelines,
                    "eligibilityCriteria": population_assembler.criteria,
                },
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(
                "Failed during creation of study design", e, location
            )

    @property
    def study_design(self) -> InterventionalStudyDesign:
        return self._study_design

    @property
    def study_interventions(self) -> list[StudyIntervention]:
        """Interventions assembled here — consumed by ``StudyAssembler`` for
        placement on ``StudyVersion.studyInterventions`` (the canonical home
        for ``StudyIntervention`` objects in the USDM v4 model).
        """
        return self._study_interventions

    # ------------------------------------------------------------------
    # Pass 1 — StudyIntervention
    # ------------------------------------------------------------------

    def _build_interventions(self, items: list[dict]) -> dict[str, StudyIntervention]:
        """Build one ``StudyIntervention`` per input item; return ``{name: obj}``.

        Administrations come from the ``administrations`` list, or from the
        flat ``dose``/``route``/``frequency`` back-compat fields collapsed
        into a single ``Administration`` — see ``_build_administrations``.
        """
        result: dict[str, StudyIntervention] = {}
        for item in items:
            try:
                administrations = self._build_administrations(item)
                params = {
                    "name": self._label_to_name(item["name"]),
                    "label": item.get("label") or item["name"],
                    "description": item.get("description") or "",
                    "role": self._encoder.intervention_role(item.get("role", "")),
                    "type": self._encoder.intervention_type(item.get("type", "")),
                    "administrations": administrations,
                }
                obj = self._builder.create(StudyIntervention, params)
                if obj is not None:
                    result[item["name"]] = obj
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of intervention '{item.get('name', '?')}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_interventions"),
                )
        return result

    def _build_administrations(self, item: dict) -> list[Administration]:
        """Assemble the ``Administration`` list for one intervention.

        Two input styles are supported (mutually exclusive, enforced by
        ``InterventionInput``):

        - ``administrations``: a list of administration dicts, each with an
          optional ``duration``;
        - flat ``dose`` / ``route`` / ``frequency``: back-compat sugar,
          collapsed into a single administration.

        Returns an empty list when neither style supplies anything —
        existing interventions without administration details should not
        synthesise a stub.
        """
        admin_items = item.get("administrations") or []
        if not admin_items:
            dose = item.get("dose")
            route = item.get("route")
            frequency = item.get("frequency")
            if not (dose or route or frequency):
                return []
            admin_items = [{"dose": dose, "route": route, "frequency": frequency}]

        result: list[Administration] = []
        multiple = len(admin_items) > 1
        for index, admin in enumerate(admin_items, start=1):
            administration = self._build_one_administration(
                item, admin, index, multiple
            )
            if administration is not None:
                result.append(administration)
        return result

    def _build_one_administration(
        self, item: dict, admin: dict, index: int, multiple: bool
    ) -> Administration | None:
        """Build a single ``Administration`` from one admin input dict."""
        try:
            route = admin.get("route")
            frequency = admin.get("frequency")
            input_name = (admin.get("name") or "").strip()
            if input_name:
                name = self._label_to_name(input_name)
            else:
                name = f"ADM-{self._label_to_name(item['name'])}"
                if multiple:
                    name = f"{name}-{index}"
            description = admin.get("description") or ""
            dose = self._dose_quantity(admin.get("dose"))
            if admin.get("dose") and dose is None:
                # Text fallback — Administration has no dose-text field, so
                # preserve the unparseable dose on the description rather
                # than dropping it.
                raw = admin["dose"]
                description = (
                    f"{description} [Dose: {raw}]" if description else f"Dose: {raw}"
                )
            params = {
                "name": name,
                "label": admin.get("label")
                or input_name
                or item.get("label")
                or item["name"],
                "description": description,
                "duration": self._build_duration(admin.get("duration")),
                "dose": dose,
                "route": self._encoder.route(route) if route else None,
                "frequency": self._encoder.frequency(frequency) if frequency else None,
            }
            return self._builder.create(Administration, params)
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of administration for '{item.get('name', '?')}'",
                e,
                KlassMethodLocation(self.MODULE, "_build_one_administration"),
            )
            return None

    def _build_duration(self, duration: dict | None) -> Duration:
        """Build the ``Duration`` for one administration.

        With no input a zero-content placeholder is created (``Duration`` is
        required on ``Administration``). With input, ``quantity`` is parsed
        as a value+unit string; when the unit does not resolve against CDISC
        CT the raw string is preserved on ``Duration.text`` alongside any
        description rather than being dropped.
        """
        duration = duration or {}
        text = duration.get("description") or None
        quantity = self._duration_quantity(duration.get("quantity"))
        if duration.get("quantity") and quantity is None:
            raw = duration["quantity"]
            text = f"{text} ({raw})" if text else raw
        return self._builder.create(
            Duration,
            {
                "text": text,
                "quantity": quantity,
                "durationWillVary": bool(duration.get("will_vary", False)),
                "reasonDurationWillVary": duration.get("will_vary_reason") or None,
            },
        )

    # Value + unit, e.g. "10 mg", "1mg", "2.5 mg/kg", "1 min", "5 %".
    QUANTITY_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)?)\s*([A-Za-z%\u00b5\u03bc][A-Za-z0-9/%\u00b5\u03bc]*)\s*$"
    )

    # Spellings the CT unit lookup does not know; normalised before lookup.
    UNIT_ALIASES = {"mcg": "ug", "\u00b5g": "ug", "\u03bcg": "ug"}

    def _duration_quantity(self, text: str | None) -> Quantity | None:
        """Parse a "1 min" / "6 weeks" style string into a ``Quantity``.

        Returns ``None`` — caller falls back to ``Duration.text`` — when the
        string does not match or the unit is unknown. A regex miss is not
        warned: free-text durations ("until progression") are expected.
        """
        return self._parse_quantity(text, "duration", warn_no_match=False)

    def _dose_quantity(self, text: str | None) -> Quantity | None:
        """Parse a dose string ("10 mg", "2.5 mg/kg") into a ``Quantity``.

        Returns ``None`` on any parse failure — caller preserves the raw
        text on the administration description. Both failure modes warn:
        a dose that fails to parse is worth surfacing.
        """
        return self._parse_quantity(text, "dose", warn_no_match=True)

    def _parse_quantity(
        self, text: str | None, label: str, warn_no_match: bool
    ) -> Quantity | None:
        """Shared value+unit parser behind duration and dose quantities.

        The unit resolves via CDISC CT, trying the raw form, a known alias
        (mcg/\u00b5g \u2192 ug), then the singular ("weeks" \u2192 "week").
        """
        if not text:
            return None
        match = self.QUANTITY_RE.match(text)
        if not match:
            if warn_no_match:
                self._errors.warning(
                    f"Could not parse {label} '{text}' as value+unit; "
                    f"keeping raw text.",
                    KlassMethodLocation(self.MODULE, "_parse_quantity"),
                )
            return None
        value, unit_text = float(match.group(1)), match.group(2)
        lookup = self.UNIT_ALIASES.get(unit_text.lower(), unit_text)
        unit_code = self._builder.cdisc_unit_code(lookup)
        if unit_code is None and lookup.lower().endswith("s"):
            unit_code = self._builder.cdisc_unit_code(lookup[:-1])
        if unit_code is None:
            self._errors.warning(
                f"{label.capitalize()} unit '{unit_text}' not recognised; "
                f"keeping raw text.",
                KlassMethodLocation(self.MODULE, "_parse_quantity"),
            )
            return None
        return self._builder.create(
            Quantity,
            {"value": value, "unit": self._builder.alias_code(unit_code)},
        )

    # ------------------------------------------------------------------
    # Pass 2a — StudyElement
    # ------------------------------------------------------------------

    def _build_elements(
        self,
        items: list[dict],
        interventions_by_name: dict[str, StudyIntervention],
    ) -> dict[str, StudyElement]:
        """Build one ``StudyElement`` per input item; return ``{name: obj}``.

        ``intervention_names`` are resolved to intervention ids. Unknown
        names are logged as warnings and dropped — the ``StudyDesignInput``
        validator already constrains cell→element references, but
        element→intervention references are not yet enforced at the schema
        level.
        """
        result: dict[str, StudyElement] = {}
        for item in items:
            try:
                intervention_ids: list[str] = []
                for ref in item.get("intervention_names", []):
                    intervention = interventions_by_name.get(ref)
                    if intervention is None:
                        self._errors.warning(
                            f"Element '{item['name']}' references undeclared "
                            f"intervention '{ref}'; skipping reference.",
                            KlassMethodLocation(self.MODULE, "_build_elements"),
                        )
                        continue
                    intervention_ids.append(intervention.id)
                params = {
                    "name": self._label_to_name(item["name"]),
                    "label": item.get("label") or item["name"],
                    "description": item.get("description") or "",
                    "studyInterventionIds": intervention_ids,
                }
                obj = self._builder.create(StudyElement, params)
                if obj is not None:
                    result[item["name"]] = obj
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of element '{item.get('name', '?')}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_elements"),
                )
        return result

    # ------------------------------------------------------------------
    # Pass 2b — StudyArm
    # ------------------------------------------------------------------

    def _build_arms(self, items: list[dict]) -> dict[str, StudyArm]:
        """Build one ``StudyArm`` per input item; return ``{name: obj}``.

        ``populationIds`` is seeded empty here and finalised in
        ``_wire_cohorts_to_arms`` once cohort ids are known.
        """
        result: dict[str, StudyArm] = {}
        for item in items:
            try:
                # Build a fresh dataOriginType Code per arm. Sharing one
                # Code instance across arms produces the same ``id`` at
                # every arm's ``dataOriginType`` path, which DDF00083 /
                # CORE-001015 flag as a uniqueness violation.
                data_origin_type = self._builder.cdisc_code(
                    self.DATA_ORIGIN_TYPE_CODE, self.DATA_ORIGIN_TYPE_DECODE
                )
                params = {
                    "name": self._label_to_name(item["name"]),
                    "label": item.get("label") or item["name"],
                    "description": item.get("description")
                    or item.get("label")
                    or item["name"],
                    "type": self._encoder.arm_type(item.get("type", "")),
                    "dataOriginDescription": item.get("description") or "",
                    "dataOriginType": data_origin_type,
                    "populationIds": [],
                }
                obj = self._builder.create(StudyArm, params)
                if obj is not None:
                    result[item["name"]] = obj
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of arm '{item.get('name', '?')}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_arms"),
                )
        return result

    # ------------------------------------------------------------------
    # Pass 2c — StudyCell
    # ------------------------------------------------------------------

    def _build_cells(
        self,
        items: list[dict],
        arms_by_name: dict[str, StudyArm],
        elements_by_name: dict[str, StudyElement],
        epochs: list[StudyEpoch],
    ) -> list[StudyCell]:
        """Build ``StudyCell``s from explicit input, or synthesise a full
        arm×epoch grid when ``items`` is empty but arms and epochs exist.

        Name lookups for arm / epoch / element are case-insensitive to match
        the ``_add_epochs`` convention in ``TimelineAssembler``.
        """
        if not items and arms_by_name and epochs:
            return self._synthesise_cell_grid(arms_by_name, epochs)

        # Case-insensitive lookup helpers.
        arms_ci = {name.upper(): arm for name, arm in arms_by_name.items()}
        elements_ci = {name.upper(): el for name, el in elements_by_name.items()}
        epochs_ci = {(epoch.label or "").upper(): epoch for epoch in epochs}

        result: list[StudyCell] = []
        for item in items:
            try:
                arm = arms_ci.get(item["arm"].upper())
                epoch = epochs_ci.get(item["epoch"].upper())
                if arm is None:
                    self._errors.warning(
                        f"Cell references unknown arm '{item['arm']}'; skipping.",
                        KlassMethodLocation(self.MODULE, "_build_cells"),
                    )
                    continue
                if epoch is None:
                    self._errors.warning(
                        f"Cell ({item['arm']}, {item['epoch']}) references unknown "
                        f"epoch '{item['epoch']}'; skipping.",
                        KlassMethodLocation(self.MODULE, "_build_cells"),
                    )
                    continue
                element_ids: list[str] = []
                for ref in item.get("elements", []):
                    element = elements_ci.get(ref.upper())
                    if element is None:
                        # Shouldn't happen — StudyDesignInput validates this
                        # up front — but guard anyway.
                        self._errors.warning(
                            f"Cell ({item['arm']}, {item['epoch']}) references "
                            f"unknown element '{ref}'; skipping reference.",
                            KlassMethodLocation(self.MODULE, "_build_cells"),
                        )
                        continue
                    element_ids.append(element.id)
                cell = self._builder.create(
                    StudyCell,
                    {
                        "armId": arm.id,
                        "epochId": epoch.id,
                        "elementIds": element_ids,
                    },
                )
                if cell is not None:
                    result.append(cell)
            except Exception as e:
                self._errors.exception(
                    "Failed during creation of cell",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_cells"),
                )
        return result

    def _synthesise_cell_grid(
        self,
        arms_by_name: dict[str, StudyArm],
        epochs: list[StudyEpoch],
    ) -> list[StudyCell]:
        """Create the default arm×epoch grid with empty element lists.

        Kept behind a named helper because the caller logic ("arms exist
        but cells don't") is easier to read when the branch is a single
        line.
        """
        cells: list[StudyCell] = []
        for arm in arms_by_name.values():
            for epoch in epochs:
                try:
                    cell = self._builder.create(
                        StudyCell,
                        {
                            "armId": arm.id,
                            "epochId": epoch.id,
                            "elementIds": [],
                        },
                    )
                    if cell is not None:
                        cells.append(cell)
                except Exception as e:
                    self._errors.exception(
                        "Failed during synthesis of arm×epoch cell",
                        e,
                        KlassMethodLocation(self.MODULE, "_synthesise_cell_grid"),
                    )
        return cells

    # ------------------------------------------------------------------
    # Arm → intervention wiring
    # ------------------------------------------------------------------

    def _wire_arm_interventions(
        self,
        items: list[dict],
        arms_by_name: dict[str, StudyArm],
        interventions_by_name: dict[str, StudyIntervention],
        elements_by_name: dict[str, StudyElement],
        cells: list[StudyCell],
        had_explicit_elements: bool,
    ) -> None:
        """Encode ``ArmInput.intervention_names`` into the design.

        The API ``StudyArm`` has no intervention reference; USDM expresses
        arm → intervention through cell → element → ``studyInterventionIds``.
        Two modes:

        - The input declared explicit elements: those are authoritative.
          Each arm's named interventions are checked for reachability via
          the arm's cells and a warning is raised for any that are not —
          no mutation.
        - No explicit elements (the common extraction path): one element
          per arm (``EL-<ARM>``) is synthesised to carry the resolved
          intervention ids and attached to every one of the arm's cells.
          With no cells (no epochs available) the element is still created
          on the design so the linkage survives, just without cell
          placement.
        """
        for item in items:
            names = item.get("intervention_names", [])
            if not names:
                continue
            arm = arms_by_name.get(item["name"])
            if arm is None:
                continue  # Arm creation already failed and was logged.
            intervention_ids = self._resolve_arm_interventions(
                item["name"], names, interventions_by_name
            )
            if not intervention_ids:
                continue
            arm_cells = [c for c in cells if c.armId == arm.id]
            if had_explicit_elements:
                self._check_arm_intervention_reachability(
                    item["name"], intervention_ids, arm_cells, elements_by_name
                )
            else:
                self._attach_arm_element(
                    item["name"], arm_cells, intervention_ids, elements_by_name
                )

    def _resolve_arm_interventions(
        self,
        arm_name: str,
        names: list[str],
        interventions_by_name: dict[str, StudyIntervention],
    ) -> list[str]:
        """Resolve intervention name references for one arm; warn on misses."""
        ids: list[str] = []
        for ref in names:
            intervention = interventions_by_name.get(ref)
            if intervention is None:
                self._errors.warning(
                    f"Arm '{arm_name}' references undeclared intervention "
                    f"'{ref}'; skipping reference.",
                    KlassMethodLocation(self.MODULE, "_resolve_arm_interventions"),
                )
                continue
            ids.append(intervention.id)
        return ids

    def _check_arm_intervention_reachability(
        self,
        arm_name: str,
        intervention_ids: list[str],
        arm_cells: list[StudyCell],
        elements_by_name: dict[str, StudyElement],
    ) -> None:
        """Explicit-elements mode: verify, never mutate.

        An arm's named interventions should already be reachable through
        its cells' elements; anything unreachable indicates inconsistent
        input worth surfacing.
        """
        elements_by_id = {e.id: e for e in elements_by_name.values()}
        reachable: set[str] = set()
        for cell in arm_cells:
            for element_id in cell.elementIds:
                element = elements_by_id.get(element_id)
                if element is not None:
                    reachable.update(element.studyInterventionIds)
        missing = [i for i in intervention_ids if i not in reachable]
        if missing:
            self._errors.warning(
                f"Arm '{arm_name}' names {len(missing)} intervention(s) not "
                f"reachable through its cells' elements; explicit elements "
                f"are authoritative — check the element definitions.",
                KlassMethodLocation(
                    self.MODULE, "_check_arm_intervention_reachability"
                ),
            )

    def _attach_arm_element(
        self,
        arm_name: str,
        arm_cells: list[StudyCell],
        intervention_ids: list[str],
        elements_by_name: dict[str, StudyElement],
    ) -> None:
        """Synthesise the per-arm element and place it on the arm's cells."""
        try:
            element_name = f"EL-{self._label_to_name(arm_name)}"
            element = self._builder.create(
                StudyElement,
                {
                    "name": element_name,
                    "label": f"{arm_name} interventions",
                    "description": f"Interventions administered in arm '{arm_name}'",
                    "studyInterventionIds": intervention_ids,
                },
            )
            if element is None:
                return
            elements_by_name[element_name] = element
            for cell in arm_cells:
                if element.id not in cell.elementIds:
                    cell.elementIds.append(element.id)
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of arm element for '{arm_name}'",
                e,
                KlassMethodLocation(self.MODULE, "_attach_arm_element"),
            )

    # ------------------------------------------------------------------
    # Cohort → arm wiring
    # ------------------------------------------------------------------

    def _wire_cohorts_to_arms(
        self,
        population_assembler: PopulationAssembler,
        arms_by_name: dict[str, StudyArm],
    ) -> None:
        """Append each cohort id onto the arms named in its ``arm_names``.

        The PopulationAssembler preserves the raw input cohort list so the
        arm mapping can be reconstructed here — the API-level ``StudyCohort``
        does not carry a back-reference to arms, so wiring has to live at a
        point with visibility into both sides of the cross-reference.
        """
        raw_cohorts = getattr(population_assembler, "raw_cohorts", None) or []
        cohort_objs = {c.name: c for c in getattr(population_assembler, "cohorts", [])}
        arms_ci = {name.upper(): arm for name, arm in arms_by_name.items()}
        for raw in raw_cohorts:
            cohort_name = raw.get("name") if isinstance(raw, dict) else None
            if not cohort_name:
                continue
            cohort_obj_name = self._label_to_name(cohort_name)
            cohort = cohort_objs.get(cohort_obj_name)
            if cohort is None:
                continue
            arm_names = raw.get("arm_names", []) if isinstance(raw, dict) else []
            for arm_name in arm_names:
                arm = arms_ci.get(arm_name.upper())
                if arm is None:
                    self._errors.warning(
                        f"Cohort '{cohort_name}' references unknown arm "
                        f"'{arm_name}'; skipping reference.",
                        KlassMethodLocation(self.MODULE, "_wire_cohorts_to_arms"),
                    )
                    continue
                if cohort.id not in arm.populationIds:
                    arm.populationIds.append(cohort.id)
