import re

from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.assembler.encoder import Encoder
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.scheduled_instance import ScheduledInstance, ScheduledActivityInstance
from usdm4.api.activity import Activity
from usdm4.api.study_epoch import StudyEpoch
from usdm4.api.encounter import Encounter
from usdm4.api.timing import Timing
from usdm4.api.condition import Condition
from usdm4.api.biomedical_concept import BiomedicalConcept
from usdm4.api.biomedical_concept_surrogate import BiomedicalConceptSurrogate
from usdm4.api.procedure import Procedure
from usdm4.api.code import Code


class TimelineAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.timeline_assembler.TimelineAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._timelines: list[ScheduleTimeline] = []
        self._epochs: list[StudyEpoch] = []
        self._encounters: list[Encounter] = []
        self._activities: list[Activity] = []
        # Activities are SHARED across timelines: an activity named on both the
        # main and a subsidiary SoA table is one Activity object referenced by
        # both. Registry keyed by normalised label. Epochs, encounters, SAIs,
        # timings, conditions and the timeline itself are per-timeline
        # namespaced (T{t}-...) — see the individual add methods.
        self._activity_by_name: dict[str, Activity] = {}
        # SAI names are derived from timepoint/visit text (D1, W12, SCREENING)
        # so the timing sheet's from/to references are human-readable. The
        # registry keeps them unique across every timeline in the study.
        self._sai_name_registry: dict[str, int] = {}
        self._condition_links: dict = {}
        self._conditions: list[Condition] = []
        self._biomedical_concepts: list[BiomedicalConcept] = []
        self._biomedical_concept_surrogates: list[BiomedicalConceptSurrogate] = []
        # self._procedures: list[Procedure] = []

    def execute(self, data) -> None:
        """Assemble one or more timelines.

        ``data`` may be a single SoA table dict (one timeline, the historical
        case) or a list of SoA table dicts (a main plus n subsidiary timelines).
        Exactly one timeline is flagged ``mainTimeline``: the first table whose
        ``table_type`` is ``main_soa`` (or the first table if none say so).
        """
        try:
            tables = self._normalise(data)
            main_index = self._main_index(tables)
            for offset, table in enumerate(tables):
                self._execute_one(table, offset + 1, is_main=(offset == main_index))
            # Single global ordering pass across every timeline's activities so
            # previousId/nextId are consistent (and shared activities are linked
            # once, not re-linked per table).
            self._builder.double_link(self._activities, "previousId", "nextId")
        except Exception as e:
            self._errors.exception(
                "Failed during creation of study design",
                e,
                KlassMethodLocation(self.MODULE, "execute"),
            )

    @staticmethod
    def _normalise(data) -> list[dict]:
        # A dict — even an empty one — is a single (possibly malformed) table;
        # only ``None`` or an empty list means "no timelines". This keeps the
        # historical behaviour where ``execute({})`` surfaces errors rather than
        # silently doing nothing.
        if data is None:
            return []
        return [data] if isinstance(data, dict) else list(data)

    @staticmethod
    def _main_index(tables: list[dict]) -> int:
        for index, table in enumerate(tables):
            if (table.get("table_type") or "main_soa") == "main_soa":
                return index
        return 0

    def _execute_one(self, data: dict, t: int, is_main: bool) -> None:
        try:
            # Footnote references (e.g. "a", "b") are scoped to a single table,
            # so reset the link map per timeline to avoid cross-table collisions.
            self._condition_links = {}
            self._epochs += self._add_epochs(data, t)
            self._encounters += self._add_encounters(data, t)
            self._add_activities(data, t)
            timepoints = self._add_timepoints(data, t)
            timings = self._add_timing(data, t)
            self._link_timepoints_and_activities(data)
            self._conditions += self._add_conditions(data, t)
            tl = self._add_timeline(data, timepoints, timings, t, is_main)
            if tl:
                self._timelines.append(tl)
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of timeline {t}",
                e,
                KlassMethodLocation(self.MODULE, "_execute_one"),
            )

    @property
    def timelines(self) -> list[ScheduleTimeline]:
        return self._timelines

    @property
    def encounters(self) -> list[Encounter]:
        return self._encounters

    @property
    def epochs(self) -> list[StudyEpoch]:
        return self._epochs

    @property
    def activities(self) -> list[Activity]:
        return self._activities

    @property
    def conditions(self) -> list[Condition]:
        return self._conditions

    @property
    def biomedical_concepts(self) -> list[BiomedicalConcept]:
        return self._biomedical_concepts

    @property
    def biomedical_concept_surrogates(self) -> list[BiomedicalConceptSurrogate]:
        return self._biomedical_concept_surrogates

    # @property
    # def procedures(self) -> list[Procedure]:
    #     return self._procedures

    def _add_epochs(self, data, t: int = 1) -> list[ScheduledInstance]:
        try:
            results = []
            map = {}
            # self._errors.debug(
            #     f"EPOCHS:\n{data['epochs']}\n",
            #     KlassMethodLocation(self.MODULE, "_add_epochs"),
            # )
            items = data["epochs"]["items"]
            timepoints = data["timepoints"]["items"]
            for index, item in enumerate(items):
                label = item["text"]
                name = f"EPOCH-{label.upper()}"
                if name not in map:
                    epoch: StudyEpoch = self._builder.create(
                        StudyEpoch,
                        {
                            "name": f"T{t}-EPOCH-{index + 1}",
                            "description": f"EPOCH-{name}",
                            "label": label,
                            "type": self._builder.klass_and_attribute_value(
                                StudyEpoch, "type", "Treatment Epoch"
                            ),
                        },
                    )
                    results.append(epoch)
                    map[name] = epoch
                epoch = map[name]
                timepoints[index]["epoch_instance"] = epoch
            self._errors.info(
                f"Epochs: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_epochs"),
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Epochs",
                e,
                KlassMethodLocation(self.MODULE, "_add_epochs"),
            )
            return results

    def _add_encounters(self, data, t: int = 1) -> list[Encounter]:
        try:
            results = []
            items = data["visits"]["items"]
            timepoints: dict = data["timepoints"]["items"]
            for index, item in enumerate(items):
                name = item["text"]
                encounter: Encounter = self._builder.create(
                    Encounter,
                    {
                        "name": f"T{t}-ENCOUNTER-{index + 1}",
                        "description": f"Encounter {name}",
                        "label": name,
                        "type": self._builder.klass_and_attribute_value(
                            Encounter, "type", "visit"
                        ),
                        "environmentalSettings": [
                            self._builder.klass_and_attribute_value(
                                Encounter, "environmentalSettings", "clinic"
                            )
                        ],
                        "contactModes": [
                            self._builder.klass_and_attribute_value(
                                Encounter, "contactModes", "In Person"
                            )
                        ],
                        "transitionStartRule": None,
                        "transitionEndRule": None,
                        "scheduledAtId": None,  # @todo
                    },
                )
                results.append(encounter)
                timepoints[index]["encounter_instance"] = encounter
                for ref in item["references"]:
                    self._condition_timepoint_index(ref, index)
            self._errors.info(
                f"Encounters: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_encounters"),
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Encounters",
                e,
                KlassMethodLocation(self.MODULE, "_add_encounters"),
            )
            return results

    def _condition_timepoint_index(self, ref: str, index: int) -> None:
        if ref not in self._condition_links:
            self._condition_links[ref] = {
                "reference": ref,
                "timepoint_index": [],
                "activity_id": [],
            }
        self._condition_links[ref]["timepoint_index"].append(index)

    def _condition_activity_id(self, ref: str, id: str) -> None:
        if ref not in self._condition_links:
            self._condition_links[ref] = {
                "reference": ref,
                "timepoint_index": [],
                "activity_id": [],
            }
        self._condition_links[ref]["activity_id"].append(id)

    def _condition_combined(self, ref, sai_index: int, activity_id: str) -> None:
        if ref not in self._condition_links:
            self._condition_links[ref] = {
                "reference": ref,
                "timepoint_index": [],
                "activity_id": [],
            }
        self._condition_links[ref]["activity_id"].append(activity_id)
        self._condition_links[ref]["timepoint_index"].append(sai_index)

    def _add_activities(self, data, t: int = 1) -> list[Activity]:
        """Create (or reuse) the activities named on this table.

        Activities are shared across timelines: the registry
        (``self._activity_by_name``) is keyed by normalised label, so an
        activity that appears on more than one SoA table yields a single
        ``Activity`` referenced by each timeline. Only newly-created activities
        are appended to ``self._activities``; ordering (previousId/nextId) is
        applied once, globally, in ``execute``. Returns the activities created
        on this call (for logging only).
        """
        created: list[Activity] = []
        try:
            items = data["activities"]["items"]
            for item in items:
                activity = self._get_or_create_activity(item, created)
                if "references" in item:
                    for ref in item["references"]:
                        self._condition_activity_id(ref, activity.id)
                item["activity_instance"] = activity
                if "children" in item:
                    for child in item["children"]:
                        child_activity = self._get_or_create_activity(child, created)
                        if "references" in child:
                            for ref in child["references"]:
                                self._condition_activity_id(ref, child_activity.id)
                        child["activity_instance"] = child_activity
                        if child_activity.id not in activity.childIds:
                            activity.childIds.append(child_activity.id)
            self._errors.info(
                f"Activities (timeline {t}): +{len(created)} new, "
                f"{len(self._activity_by_name)} total",
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
            return created
        except Exception as e:
            self._errors.exception(
                "Error creating Activities",
                e,
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
            return created

    def _get_or_create_activity(self, item: dict, created: list[Activity]) -> Activity:
        """Return the shared Activity for ``item['name']``, creating it on first
        sighting. The activity's name IS its (trimmed) label text — the SoA
        grid and BC/procedure references in the workbook show names, so they
        must be human-readable. Uniqueness holds because the registry is keyed
        by the normalised label (same label → same shared Activity); a
        label-less activity falls back to the ``ACTIVITY-{n}`` sequence."""
        key = (item["name"] or "").strip().lower()
        existing = self._activity_by_name.get(key)
        if existing is not None:
            return existing
        bc_ids, sbc_ids, procedures = self._get_biomedical_concepts(item)
        seq = len(self._activity_by_name) + 1
        params = {
            "name": (item["name"] or "").strip() or f"ACTIVITY-{seq}",
            "description": f"Activity {item['name']}",
            "label": item["name"],
            "definedProcedures": procedures,
            "biomedicalConceptIds": bc_ids,
            "bcCategoryIds": [],
            "bcSurrogateIds": sbc_ids,
            "timelineId": None,
        }
        activity: Activity = self._builder.create(Activity, params)
        self._activity_by_name[key] = activity
        self._activities.append(activity)
        created.append(activity)
        return activity

    def _add_timepoints(self, data, t: int = 1) -> list[ScheduledInstance]:
        try:
            results = []
            timepoints: list = data["timepoints"]["items"]
            for index, item in enumerate(timepoints):
                sai = self._builder.create(
                    ScheduledActivityInstance,
                    {
                        "name": self._sai_name(data, index, t),
                        "description": f"Scheduled activity instance {index + 1}",
                        "label": item["text"],
                        "timelineExitId": None,
                        "encounterId": item["encounter_instance"].id
                        if item["encounter_instance"]
                        else None,
                        "scheduledInstanceTimelineId": None,
                        "defaultConditionId": None,
                        "epochId": item["epoch_instance"].id,
                        "activityIds": [],
                    },
                )
                item["sai_instance"] = sai
                results.append(sai)
            self._errors.info(
                f"SAI: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_timepoints"),
            )
            sai: ScheduledActivityInstance
            for index, sai in enumerate(results[:-1]):
                sai.defaultConditionId = results[index + 1].id
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Scheduled Activity timepoints",
                e,
                KlassMethodLocation(self.MODULE, "_add_timepoints"),
            )
            return results

    def _add_conditions(self, data, t: int = 1) -> list[Condition]:
        results = []
        conditions: list = data["conditions"]["items"]
        timepoints: list = data["timepoints"]["items"]
        # print(f"COND LINKS: {self._condition_links:}")
        try:
            for index, item in enumerate(conditions):
                # print(f"COND: {item}")
                if ref := item["reference"]:
                    if ref in self._condition_links:
                        # print(f"COND REF 1: {ref}")
                        links = self._condition_links[ref]
                        timepoint_ids = [
                            timepoints[x]["sai_instance"].id
                            for x in links["timepoint_index"]
                        ]
                        activity_ids = [x for x in links["activity_id"]]
                        condition = self._builder.create(
                            Condition,
                            {
                                "name": f"T{t}-Condition-{index + 1}",
                                "label": f"Condition {index + 1}",
                                "description": f"Extracted footnote / condition {index + 1}",
                                "text": item["text"],
                                "dictionaryId": None,
                                "contextIds": timepoint_ids
                                if timepoint_ids
                                else activity_ids,
                                "appliesToIds": activity_ids if timepoint_ids else [],
                            },
                        )
                        if condition:
                            # print(f"COND REF 2: {condition}")
                            results.append(condition)
                    else:
                        # print(f"COND LINKS: {self._condition_links:}")
                        self._errors.warning(
                            f"Failed to align condition {item}, not created.",
                            KlassMethodLocation(self.MODULE, "_add_conditions"),
                        )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating conditions",
                e,
                KlassMethodLocation(self.MODULE, "_add_conditions"),
            )
            return results

    def _add_timing(self, data, t: int = 1) -> list[ScheduledInstance]:
        try:
            results = []
            timepoints: list = data["timepoints"]["items"]
            anchor_index = self._find_anchor(data)
            anchor: ScheduledInstance = timepoints[anchor_index]["sai_instance"]
            item: dict[str]
            for index, item in enumerate(timepoints):
                this_sai: ScheduledInstance = item["sai_instance"]
                if index < anchor_index:
                    if timing := self._timing(
                        data, index, anchor_index, "Before", this_sai.id, anchor.id, t
                    ):
                        results.append(timing)
                elif index == anchor_index:
                    if timing := self._timing(
                        data,
                        index,
                        anchor_index,
                        "Fixed Reference",
                        this_sai.id,
                        this_sai.id,
                        t,
                    ):
                        results.append(timing)
                else:
                    if timing := self._timing(
                        data, index, anchor_index, "After", this_sai.id, anchor.id, t
                    ):
                        results.append(timing)
            self._errors.info(
                f"Timing: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_timing"),
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating timings",
                e,
                KlassMethodLocation(self.MODULE, "_add_timing"),
            )
            return results

    _EMPTY_WINDOW = {"before": 0, "after": 0, "unit": ""}

    def _timing(
        self,
        data: dict,
        index: int,
        anchor_index: int,
        type: str,
        from_id: str,
        to_id: str,
        t: int = 1,
    ) -> Timing:
        try:
            windows: list = data["windows"]["items"]
            timepoints: list = data["timepoints"]["items"]
            timepoint = timepoints[index]
            window = windows[index] if index < len(windows) else self._EMPTY_WINDOW
            item: Timing = self._builder.create(
                Timing,
                {
                    "type": self._builder.klass_and_attribute_value(
                        Timing, "type", type
                    ),
                    "value": self._encoder.iso8601_duration(
                        self._interval_from_anchor(timepoints, index, anchor_index),
                        timepoint["unit"],
                    ),
                    "valueLabel": self._timing_value_label(timepoints, index),
                    "name": f"T{t}-TIMING-{index}",
                    "description": f"Timing {index + 1}",
                    "label": self._timing_value_label(timepoints, index),
                    "relativeToFrom": self._builder.klass_and_attribute_value(
                        Timing, "relativeToFrom", "start to start"
                    ),
                    "windowLabel": self._window_label(windows, index),
                    "windowLower": self._encoder.iso8601_duration(
                        self._set_abs_duration(window["before"]), window["unit"]
                    )
                    if window["before"]
                    else "",
                    "windowUpper": self._encoder.iso8601_duration(
                        self._set_abs_duration(window["after"]), window["unit"]
                    )
                    if window["after"]
                    else "",
                    "relativeFromScheduledInstanceId": from_id,
                    "relativeToScheduledInstanceId": to_id,
                },
            )
            # print(f"WINDOW: {window} -> {item.windowLabel}, [{item.windowLower}, {item.windowUpper}]")
            return item
        except Exception as e:
            self._errors.exception(
                "Error creating individual timing",
                e,
                KlassMethodLocation(self.MODULE, "_timing"),
            )
            return None

    def _set_abs_duration(self, value: int | str) -> int:
        # print(f"DURATION: {value}")
        return 0 if not isinstance(value, int) else abs(value)

    @staticmethod
    def _coerce_int(value) -> int | None:
        """Coerce a timepoint value to int. Accepts int, whole float, and
        numeric strings (schema allows all three). Returns None if not numeric."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value) if value.is_integer() else None
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                return None
        return None

    _SAI_TEXT_PATTERNS = (
        (re.compile(r"^day\s*(-?\d+)$", re.IGNORECASE), "D{}"),
        (re.compile(r"^week\s*(-?\d+)$", re.IGNORECASE), "W{}"),
        (re.compile(r"^cycle\s*(\d+)[ ,]*day\s*(-?\d+)$", re.IGNORECASE), "C{}D{}"),
    )

    def _sai_name(self, data, index: int, t: int) -> str:
        """Human-readable SAI name for the timing sheet's from/to references:
        derived from the timepoint text (``Day 1`` → ``D1``, ``Week 12`` →
        ``W12``, ``Cycle 2 Day 1`` → ``C2D1``), else an upper-cased slug of the
        timepoint or visit text, else the positional fallback
        ``T{t}-SAI-{n}``. Uniqued across the study with a numeric suffix."""
        base = self._sai_base_name(data, index)
        if not base:
            base = f"T{t}-SAI-{index + 1}"
        count = self._sai_name_registry.get(base, 0) + 1
        self._sai_name_registry[base] = count
        return base if count == 1 else f"{base}-{count}"

    _UNIT_PREFIXES = {
        "day": "D",
        "d": "D",
        "week": "W",
        "wk": "W",
        "w": "W",
        "hour": "H",
        "hr": "H",
        "h": "H",
        "minute": "MIN",
        "min": "MIN",
        "month": "MTH",
        "mth": "MTH",
        "year": "Y",
        "yr": "Y",
        "y": "Y",
    }

    def _sai_base_name(self, data, index: int) -> str:
        timepoint = data["timepoints"]["items"][index]
        visits = (data.get("visits") or {}).get("items") or []
        visit_text = (visits[index].get("text") or "") if index < len(visits) else ""
        for source, text in (
            ("timepoint", timepoint.get("text") or ""),
            ("visit", visit_text),
        ):
            text = text.strip()
            if not text:
                continue
            if source == "timepoint" and re.fullmatch(r"[+-]?\d+", text):
                # A bare number is a day/week count — prefix with the unit
                # letter, preferring the signed value (the text often drops
                # the sign).
                unit = (timepoint.get("unit") or "").strip().lower().rstrip("s")
                prefix = self._UNIT_PREFIXES.get(unit)
                if prefix:
                    value = self._coerce_int(timepoint.get("value"))
                    return f"{prefix}{value if value is not None else text}"
            for pattern, template in self._SAI_TEXT_PATTERNS:
                match = pattern.match(text)
                if match:
                    return template.format(*match.groups())
            slug = re.sub(r"[^A-Z0-9+,_ .-]", "", text.upper().replace("/", " "))
            slug = re.sub(r"\s+", " ", slug).strip()
            if slug:
                return slug[:20].rstrip()
        return ""

    @staticmethod
    def _is_placeholder(item: dict) -> bool:
        """A blank SoA column: no text and no (or zero) value. These carry no
        timing information — e.g. an unlabelled ET/unscheduled column."""
        value = TimelineAssembler._coerce_int(item.get("value"))
        return not (item.get("text") or "").strip() and not value

    _DAY_UNITS = ("day", "days", "d")

    def _interval_from_anchor(
        self, timepoints: list[dict], index: int, anchor_index: int
    ) -> int:
        """Duration between this timepoint and the anchor.

        USDM ``Timing.value`` is the interval relative to the referenced
        instance, NOT the protocol's day number: Day 16 relative to a Day 1
        anchor is 15 days. When day numbering is 1-based (no Day 0 in the
        table, the common protocol convention), an interval crossing zero
        loses a day: Day -1 to Day 1 is 1 day, Day -42 to Day 1 is 42 days.
        Falls back to ``abs(value)`` (the historical behaviour) when either
        value is non-numeric or the units differ."""
        timepoint = timepoints[index]
        anchor = timepoints[anchor_index]
        value = self._coerce_int(timepoint.get("value"))
        anchor_value = self._coerce_int(anchor.get("value"))
        if value is None or anchor_value is None:
            return self._set_abs_duration(timepoint.get("value"))
        unit = (timepoint.get("unit") or "").strip().lower()
        anchor_unit = (anchor.get("unit") or "").strip().lower()
        if unit.rstrip("s") != anchor_unit.rstrip("s"):
            self._errors.warning(
                f"Timing unit '{timepoint.get('unit')}' differs from anchor "
                f"unit '{anchor.get('unit')}'; using absolute value "
                f"{abs(value)} for '{timepoint.get('text')}'",
                KlassMethodLocation(self.MODULE, "_interval_from_anchor"),
            )
            return abs(value)
        delta = abs(value - anchor_value)
        if (
            unit in self._DAY_UNITS
            and (value < 0 < anchor_value or anchor_value < 0 < value)
            and not self._has_zero_timepoint(timepoints)
        ):
            delta -= 1
        return delta

    def _has_zero_timepoint(self, timepoints: list[dict]) -> bool:
        """True if the table numbers days from zero (an explicit Day 0 column
        exists), in which case no crossing-zero correction applies."""
        for item in timepoints:
            if self._is_placeholder(item):
                continue
            if self._coerce_int(item.get("value")) == 0:
                return True
        return False

    def _window_label(self, windows: list[dict], index: int) -> str:
        if index >= len(windows):
            return "???"
        window = windows[index]
        if window["before"] == 0 and window["after"] == 0:
            return ""
        return f"-{window['before']}..+{window['after']} {window['unit']}"

    def _timing_value_label(self, timepoints: list[dict], index: int) -> str:
        if index >= len(timepoints):
            return "???"
        return f"{timepoints[index]['text']}" if timepoints[index]["text"] else "???"

    def _find_anchor(self, data) -> int:
        """Positional index of the anchor timepoint: the first real (non-blank)
        column with a value >= 0 — Day 0 or Day 1 in a typical SoA. Returns the
        position in the items list; the input's own ``index`` field is ignored
        (the schema defaults it to 0, so it is 0 for every item when the
        producer — e.g. ground truth — does not supply it)."""
        items = data["timepoints"]["items"]
        item: dict
        for index, item in enumerate(items):
            if self._is_placeholder(item):
                continue
            value = self._coerce_int(item.get("value"))
            if value is not None and value >= 0:
                return index
        return 0

    def _link_timepoints_and_activities(self, data: dict) -> None:
        """Attach each activity (and child activity) to the SAIs of the visits
        it is marked at. NOTE: an activity's own visits are always processed —
        the schema defaults ``children`` to ``[]`` for every activity, so a
        presence test on the key (the historical behaviour) made flat
        activities (the ground-truth shape) link nothing at all."""
        try:
            activities = data["activities"]["items"]
            timepoints = data["timepoints"]["items"]
            for activity in activities:
                self._link_one_activity(activity, timepoints)
                for child in activity.get("children") or []:
                    self._link_one_activity(child, timepoints)
        except Exception as e:
            self._errors.exception(
                "Error linking timepoints and activities",
                e,
                KlassMethodLocation(self.MODULE, "_link_timepoints_and_activities"),
            )
            return None

    def _link_one_activity(self, activity: dict, timepoints: list[dict]) -> None:
        activity_instance: Activity = activity["activity_instance"]
        for visit in activity.get("visits") or []:
            index = visit["index"]
            sai_instance: ScheduledActivityInstance = timepoints[index]["sai_instance"]
            sai_instance.activityIds.append(activity_instance.id)
            for ref in visit["references"]:
                self._condition_combined(ref, index, activity_instance.id)

    def _add_timeline(
        self,
        data,
        instances: list[ScheduledInstance],
        timings: list[Timing],
        t: int = 1,
        is_main: bool = True,
    ):
        try:
            self._errors.debug(
                f"Instances: {len(instances)}, Timings: {len(timings)}",
                KlassMethodLocation(self.MODULE, "_add_timeline"),
            )
            exit = self._builder.create(ScheduleTimelineExit, {})
            sai: ScheduledActivityInstance = instances[-1]
            sai.timelineExitId = exit.id
            sai.defaultConditionId = None
            duration = None
            title = data.get("table_title") or (
                "Main timeline" if is_main else f"Timeline {t}"
            )
            return self._builder.create(
                ScheduleTimeline,
                {
                    "mainTimeline": is_main,
                    "name": f"TIMELINE-{t}",
                    "description": "The main timeline"
                    if is_main
                    else f"Subsidiary timeline {t}",
                    "label": title,
                    "entryCondition": "Paricipant identified",
                    "entryId": instances[0].id,
                    "exits": [exit],
                    "plannedDuration": duration,
                    "instances": instances,
                    "timings": timings,
                },
            )
        except Exception as e:
            self._errors.exception(
                "Error creating timeline",
                e,
                KlassMethodLocation(self.MODULE, "_add_timeline"),
            )
            return None

    def _get_biomedical_concepts(
        self, activity: dict
    ) -> tuple[list[str], list[str], list[Procedure]]:
        bc_ids = []
        sbc_ids = []
        procedures = []
        # print(f"ACTIVITY: {activity}")
        if "actions" in activity:
            for bc_name in activity["actions"]["bcs"]:
                # print(f"BC: {bc_name}")
                if self._builder.cdisc_bc_library.exists(bc_name):
                    bc: BiomedicalConcept = self._builder.bc(bc_name)
                    if bc:
                        self._biomedical_concepts.append(bc)
                        bc_ids.append(bc.id)
                    else:
                        self._errors.warning(
                            f"Failed to create BC with name '{bc_name}'"
                        )
                else:
                    params = {
                        "name": bc_name,
                        "description": bc_name,
                        "label": bc_name,
                        "reference": "None set",
                    }
                    sbc: BiomedicalConceptSurrogate = self._builder.create(
                        BiomedicalConceptSurrogate, params
                    )
                    if sbc:
                        self._biomedical_concept_surrogates.append(sbc)
                        sbc_ids.append(sbc.id)
                    else:
                        self._errors.warning(
                            f"Failed to create surrogate BC with name '{bc_name}'"
                        )
                params = {
                    "name": bc_name,
                    "description": bc_name,
                    "label": bc_name,
                    "procedureType": activity["name"],
                    "code": self._builder.create(
                        Code,
                        {
                            "code": "12345",
                            "codeSystem": "LOINC",
                            "codeSystemVersion": "1",
                            "decode": bc_name,
                        },
                    ),
                    "reference": "Not applicable",
                }
                procedure = self._builder.create(Procedure, params)
                if procedure:
                    # self._procedures.append(procedure)
                    procedures.append(procedure)
                else:
                    self._errors.warning(
                        f"Failed to create procedure with name '{bc_name}'"
                    )
        # print(f"IDS: '{bc_ids}', '{sbc_ids}', '{procedures}'")
        return bc_ids, sbc_ids, procedures
