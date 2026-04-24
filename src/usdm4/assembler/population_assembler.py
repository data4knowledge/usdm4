from typing import Union
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.builder.builder import Builder
from usdm4.api.population_definition import StudyDesignPopulation, StudyCohort
from usdm4.api.eligibility_criterion import (
    EligibilityCriterion,
    EligibilityCriterionItem,
)
from usdm4.api.quantity_range import Quantity, Range
from usdm4.api.characteristic import Characteristic


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
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._population = None
        self._cohorts: list[StudyCohort] = []
        self._ec_items: list[EligibilityCriterion] = []
        self._eci_items: list[EligibilityCriterionItem] = []
        self._raw_cohorts: list[dict] = []

    def execute(self, data: dict) -> None:
        """
        Processes population data and creates a StudyDesignPopulation object.

        Args:
            data (dict): A dictionary containing population definition data.
                        See ``PopulationInput`` (``usdm4.assembler.schema``) for
                        the full structure. The assembler now consumes:

                        - "label": required display name (used for internal name)
                        - "inclusion_exclusion": dict with "inclusion" / "exclusion"
                        - "demographics": dict with age_min/age_max/age_unit/sex/
                          healthy_volunteers
                        - "cohorts": list[dict] with per-cohort characteristics /
                          planned_enrollment / arm_names
                        - "planned_enrollment": overall study enrollment count

        Returns:
            None: The created population is stored in ``self._population``;
            cohort objects and the raw input cohort list are additionally
            exposed so ``StudyDesignAssembler`` can complete the cohort→arm
            wiring.
        """
        try:
            if not data:
                self._errors.info(
                    "No population to build, no data",
                    KlassMethodLocation(self.MODULE, "execute"),
                )
                return

            self._ie(data["inclusion_exclusion"])

            demographics = data.get("demographics") or {}
            includes_healthy = bool(demographics.get("healthy_volunteers", True))
            planned_sex = self._build_planned_sex(demographics)
            planned_age = self._build_planned_age(demographics)
            planned_enrollment_qty = self._build_planned_enrollment(data)

            # Cohorts — persist raw input so cohort→arm wiring (which needs
            # ``arm_names``, a field that does not survive onto the API
            # StudyCohort) can happen later in StudyDesignAssembler.
            self._raw_cohorts = list(data.get("cohorts") or [])
            self._cohorts = self._build_cohorts(self._raw_cohorts, includes_healthy)

            params = {
                "name": data["label"].upper().replace(" ", "-"),
                "label": data["label"],
                "description": "The study population, currently blank",
                "includesHealthySubjects": includes_healthy,
                "criterionIds": [x.id for x in self._ec_items],
                "plannedSex": planned_sex,
                "plannedAge": planned_age,
                "plannedEnrollmentNumber": planned_enrollment_qty,
                "cohorts": self._cohorts,
            }

            self._population = self._builder.create(StudyDesignPopulation, params)
        except Exception as e:
            self._errors.exception(
                "Failed during creation of population",
                e,
                KlassMethodLocation(self.MODULE, "execute"),
            )

    @property
    def population(self) -> StudyDesignPopulation:
        return self._population

    @property
    def criteria(self) -> list[EligibilityCriterion]:
        return self._ec_items

    @property
    def criteria_items(self) -> list[EligibilityCriterionItem]:
        return self._eci_items

    @property
    def cohorts(self) -> list[StudyCohort]:
        return self._cohorts

    @property
    def raw_cohorts(self) -> list[dict]:
        """Raw input cohort dicts (preserving ``arm_names``).

        ``StudyCohort`` has no back-reference to arms, so cohort→arm wiring
        has to read the original input. ``StudyDesignAssembler`` consumes
        this to populate ``StudyArm.populationIds``.
        """
        return self._raw_cohorts

    # ------------------------------------------------------------------
    # Demographics → population fields
    # ------------------------------------------------------------------

    def _build_planned_sex(self, demographics: dict):
        """Build the ``plannedSex`` list from a ``sex`` label.

        ``"ALL"`` yields both codes, ``"MALE"`` / ``"FEMALE"`` yield a single
        entry each. Missing / unknown values default to the ALL pair, which
        is the least surprising behaviour for an unspecified trial.
        """
        sex = str(demographics.get("sex", "ALL")).upper()
        if sex == "ALL":
            return [self._encoder.sex("FEMALE"), self._encoder.sex("MALE")]
        if sex == "MALE":
            return [self._encoder.sex("MALE")]
        if sex == "FEMALE":
            return [self._encoder.sex("FEMALE")]
        # Fall through — the encoder will log a warning for unknown values.
        return [self._encoder.sex(sex)]

    def _build_planned_age(self, demographics: dict) -> Union[Range, None]:
        """Build ``plannedAge`` (``Range``) from ``age_min`` / ``age_max``.

        Returns ``None`` when neither bound is supplied. When only one bound
        is given the missing side is logged as a warning and treated as 0
        (lower) or the supplied value (upper) so that a ``Range`` remains
        well-formed — the underlying model requires both ``minValue`` and
        ``maxValue``.
        """
        age_min = demographics.get("age_min")
        age_max = demographics.get("age_max")
        if age_min is None and age_max is None:
            return None

        unit_code = self._encoder.age_unit(demographics.get("age_unit", "Years"))
        unit_alias = self._builder.alias_code(unit_code)

        # Range requires both minValue and maxValue; fill any missing bound
        # with the other (a zero-width range) and log the compromise.
        effective_min = age_min if age_min is not None else age_max
        effective_max = age_max if age_max is not None else age_min
        if age_min is None or age_max is None:
            self._errors.warning(
                f"Planned age range partially supplied (min={age_min}, max={age_max}); "
                f"filling missing bound with supplied value.",
                KlassMethodLocation(self.MODULE, "_build_planned_age"),
            )

        min_qty = self._builder.create(
            Quantity, {"value": float(effective_min), "unit": unit_alias}
        )
        max_qty = self._builder.create(
            Quantity, {"value": float(effective_max), "unit": unit_alias}
        )
        if min_qty is None or max_qty is None:
            return None
        return self._builder.create(
            Range,
            {
                "minValue": min_qty,
                "maxValue": max_qty,
                "isApproximate": False,
            },
        )

    def _build_planned_enrollment(self, data: dict) -> Union[Quantity, None]:
        """Build the overall ``plannedEnrollmentNumber`` ``Quantity``.

        Explicit ``planned_enrollment`` wins; otherwise sum the per-cohort
        planned enrollment values. ``None`` is returned if neither source
        has a usable number so the field degrades rather than emitting a
        bogus zero.
        """
        explicit = data.get("planned_enrollment")
        if explicit is None and data.get("cohorts"):
            total = 0
            seen = False
            for cohort in data["cohorts"]:
                pe = (
                    cohort.get("planned_enrollment")
                    if isinstance(cohort, dict)
                    else None
                )
                if pe is not None:
                    seen = True
                    try:
                        total += int(pe)
                    except (TypeError, ValueError):
                        self._errors.warning(
                            f"Cohort '{cohort.get('name', '?')}' has non-numeric "
                            f"planned_enrollment '{pe}'; skipping in total.",
                            KlassMethodLocation(
                                self.MODULE, "_build_planned_enrollment"
                            ),
                        )
            explicit = total if seen else None
        if explicit is None:
            return None
        try:
            value = float(explicit)
        except (TypeError, ValueError):
            self._errors.warning(
                f"Planned enrollment '{explicit}' not numeric; dropping.",
                KlassMethodLocation(self.MODULE, "_build_planned_enrollment"),
            )
            return None
        return self._builder.create(Quantity, {"value": value, "unit": None})

    # ------------------------------------------------------------------
    # Cohorts
    # ------------------------------------------------------------------

    def _build_cohorts(
        self, raw_cohorts: list, parent_includes_healthy: bool
    ) -> list[StudyCohort]:
        result: list[StudyCohort] = []
        for c in raw_cohorts:
            if not isinstance(c, dict):
                continue
            try:
                name = c.get("name")
                if not name:
                    self._errors.warning(
                        "Cohort is missing 'name'; skipping.",
                        KlassMethodLocation(self.MODULE, "_build_cohorts"),
                    )
                    continue
                characteristics = self._build_characteristics(
                    name, c.get("characteristics", [])
                )
                cohort = self._builder.create(
                    StudyCohort,
                    {
                        "name": self._label_to_name(name),
                        "label": c.get("label") or name,
                        "description": c.get("description") or "",
                        "includesHealthySubjects": parent_includes_healthy,
                        "plannedEnrollmentNumber": self._cohort_enrollment(c),
                        "characteristics": characteristics,
                    },
                )
                if cohort is not None:
                    result.append(cohort)
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of cohort '{c.get('name', '?')}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_cohorts"),
                )
        return result

    def _build_characteristics(
        self, cohort_name: str, texts: list
    ) -> list[Characteristic]:
        result: list[Characteristic] = []
        for idx, text in enumerate(texts):
            try:
                ch = self._builder.create(
                    Characteristic,
                    {
                        "name": f"{self._label_to_name(cohort_name)}-CHAR-{idx + 1}",
                        "label": f"{cohort_name} characteristic {idx + 1}",
                        "description": "",
                        "text": str(text) if text is not None else "",
                    },
                )
                if ch is not None:
                    result.append(ch)
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of characteristic for cohort '{cohort_name}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_build_characteristics"),
                )
        return result

    def _cohort_enrollment(self, c: dict) -> Union[Quantity, None]:
        pe = c.get("planned_enrollment")
        if pe is None:
            return None
        try:
            value = float(pe)
        except (TypeError, ValueError):
            self._errors.warning(
                f"Cohort '{c.get('name', '?')}' has non-numeric "
                f"planned_enrollment '{pe}'; dropping.",
                KlassMethodLocation(self.MODULE, "_cohort_enrollment"),
            )
            return None
        return self._builder.create(Quantity, {"value": value, "unit": None})

    # ------------------------------------------------------------------
    # Inclusion / Exclusion (unchanged logic)
    # ------------------------------------------------------------------

    def _ie(self, criteria: dict) -> None:
        self._collection(
            criteria["inclusion"], "C25532", "INCLUSION", "INC", "Inclusion"
        )
        self._collection(
            criteria["exclusion"], "C25370", "EXCLUSION", "EXC", "Exclusion"
        )

    def _collection(
        self, criteria: list[str], code: str, decode: str, prefix: str, label: str
    ) -> None:
        for index, text in enumerate(criteria):
            try:
                category = self._builder.cdisc_code(code, decode)
                params = {
                    "name": f"{prefix}-I{index + 1}",
                    "label": f"{label} item {index + 1} ",
                    "description": "",
                    "text": text,
                }
                eci_item = self._builder.create(EligibilityCriterionItem, params)
                self._eci_items.append(eci_item)
                params = {
                    "name": f"{prefix}{index + 1}",
                    "label": f"{label} criterion {index + 1} ",
                    "description": "",
                    "criterionItemId": eci_item.id,
                    "category": category,
                    "identifier": f"{index + 1}",
                }
                self._ec_items.append(
                    self._builder.create(EligibilityCriterion, params)
                )
            except Exception as e:
                location = KlassMethodLocation(self.MODULE, "_collection")
                self._errors.exception(
                    f"Failed during creation of criterion '{text}", e, location
                )
