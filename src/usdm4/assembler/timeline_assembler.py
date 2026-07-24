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

    def _get_or_create_activity(
        self, item: dict, created: list[Activity]
    ) -> Activity:
        """Return the shared Activity for ``item['name']``, creating it on first
        sighting. Names (``ACTIVITY-{n}``) use a study-global sequence so they
        stay unique across timelines; the builder rejects duplicate keys."""
        key = (item["name"] or "").strip().lower()
        existing = self._activity_by_name.get(key)
        if existing is not None:
            return existing
        bc_ids, sbc_ids, procedures = self._get_biomedical_concepts(item)
        seq = len(self._activity_by_name) + 1
        params = {
            "name": f"ACTIVITY-{seq}",
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
                        "name": f"T{t}-SAI-{index + 1}",
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
                        data, index, "Before", this_sai.id, anchor.id, t
                    ):
                        results.append(timing)
                elif index == anchor_index:
                    if timing := self._timing(
                        data, index, "Fixed Reference", this_sai.id, this_sai.id, t
                    ):
                        results.append(timing)
                else:
                    if timing := self._timing(
                        data, index, "After", this_sai.id, anchor.id, t
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
        self, data: dict, index: int, type: str, from_id: str, to_id: str, t: int = 1
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
                        self._set_abs_duration(timepoint["value"]), timepoint["unit"]
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
        items = data["timepoints"]["items"]
        item: dict
        for item in items:
            # print(f"ANCHOR CHECK: '{item['value']}', {type(item['value'])}")
            if isinstance(item["value"], int) and item["value"] >= 0:
                # print(f"ANCHOR CHECK: POSITIVE")
                item["sai_instance"]
                return int(item["index"])
        return 0

    def _link_timepoints_and_activities(self, data: dict) -> None:
        try:
            activities = data["activities"]["items"]
            timepoints = data["timepoints"]["items"]
            for a_index, activity in enumerate(activities):
                if "children" in activity:
                    for child in activity["children"]:
                        # sai_index = child["index"]
                        activity_instance: Activity = child["activity_instance"]
                        for visit in child["visits"]:
                            index = visit["index"]
                            sai_instance: ScheduledActivityInstance = timepoints[index][
                                "sai_instance"
                            ]
                            sai_instance.activityIds.append(activity_instance.id)
                            for ref in visit["references"]:
                                self._condition_combined(
                                    ref, index, activity_instance.id
                                )
                else:
                    activity_instance: Activity = activity["activity_instance"]
                    for visit in activity["visits"]:
                        index = visit["index"]
                        sai_instance: ScheduledActivityInstance = timepoints[index][
                            "sai_instance"
                        ]
                        sai_instance.activityIds.append(activity_instance.id)
                        for ref in visit["references"]:
                            self._condition_combined(ref, index, activity_instance.id)
        except Exception as e:
            self._errors.exception(
                "Error linking timepoints and activities",
                e,
                KlassMethodLocation(self.MODULE, "_link_timepoints_and_activities"),
            )
            return None

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
