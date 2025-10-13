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
        self._condition_links: dict = {}
        self._conditions = []

    def execute(self, data: dict) -> None:
        try:
            self._epochs = self._add_epochs(data)
            self._encounters = self._add_encounters(data)
            self._activities = self._add_activities(data)
            timepoints = self._add_timepoints(data)
            timings = self._add_timing(data)
            self._link_timepoints_and_activities(data)
            self._conditions = self._add_conditions(data)
            tl = self._add_timeline(data, timepoints, timings)
            self._timelines.append(tl)
        except Exception as e:
            self._errors.exception(
                "Failed during creation of study design",
                e,
                KlassMethodLocation(self.MODULE, "execute"),
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

    def _add_epochs(self, data) -> list[ScheduledInstance]:
        try:
            results = []
            map = {}
            self._errors.debug(
                f"EPOCHS:\n{data['epochs']}\n",
                KlassMethodLocation(self.MODULE, "_add_epochs"),
            )
            items = data["epochs"]["items"]
            timepoints = data["timepoints"]["items"]
            for index, item in enumerate(items):
                label = item["text"]
                name = f"EPOCH-{label.upper()}"
                if name not in map:
                    epoch: StudyEpoch = self._builder.create(
                        StudyEpoch,
                        {
                            "name": f"EPOCH-{index + 1}",
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

    def _add_encounters(self, data) -> list[Encounter]:
        try:
            results = []
            items = data["visits"]["items"]
            timepoints: dict = data["timepoints"]["items"]
            for index, item in enumerate(items):
                name = item["text"]
                encounter: Encounter = self._builder.create(
                    Encounter,
                    {
                        "name": f"ENCOUNTER-{index + 1}",
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

    def _add_activities(self, data) -> list[Activity]:
        try:
            results = []
            items = data["activities"]["items"]
            for index, item in enumerate(items):
                # print(f"ADDING ACTIVITY: {index}, {item}")
                params = {
                    "name": f"ACTIVITY-{index + 1}",
                    "description": f"Activity {item['name']}",
                    "label": item["name"],
                    "definedProcedures": [],
                    "biomedicalConceptIds": [],
                    "bcCategoryIds": [],
                    "bcSurrogateIds": [],
                    "timelineId": None,
                }
                activity: Activity = self._builder.create(Activity, params)
                results.append(activity)
                if "references" in item:
                    for ref in item["references"]:
                        # print(f"ADDING ACTIVITY REF: {item["name"]} -> {ref}")
                        self._condition_activity_id(ref, activity.id)
                item["activity_instance"] = activity
                if "children" in item:
                    for child in item["children"]:
                        # print(f"ADDING ACTIVITY: _, {child}")
                        params = {
                            "name": f"ACTIVITY-{child['name'].upper()}",
                            "description": f"Activity {child['name']}",
                            "label": child["name"],
                            "definedProcedures": [],
                            "biomedicalConceptIds": [],
                            "bcCategoryIds": [],
                            "bcSurrogateIds": [],
                            "timelineId": None,
                        }
                        child_activity: Activity = self._builder.create(
                            Activity, params
                        )
                        results.append(child_activity)
                        if "references" in child:
                            for ref in child["references"]:
                                # print(f"ADDING ACTIVITY REF: {item["name"]} -> {ref}")
                                self._condition_activity_id(ref, child_activity.id)
                        child["activity_instance"] = child_activity
                        activity.childIds.append(child_activity.id)
            self._errors.info(
                f"Activities: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
            self._builder.double_link(results, "previousId", "nextId")
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Activities",
                e,
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
            return results

    def _add_timepoints(self, data) -> list[ScheduledInstance]:
        try:
            results = []
            timepoints: list = data["timepoints"]["items"]
            # epochs: list = data["epochs"]["items"]
            # encounters: list = data["visits"]["items"]
            for index, item in enumerate(timepoints):
                sai = self._builder.create(
                    ScheduledActivityInstance,
                    {
                        "name": f"SAI-{index + 1}",
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
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Scheduled Activity timepoints",
                e,
                KlassMethodLocation(self.MODULE, "_add_timepoints"),
            )
            return results

    def _add_conditions(self, data) -> list[Condition]:
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
                                "name": f"Condition_{index + 1}",
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

    def _add_timing(self, data) -> list[ScheduledInstance]:
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
                        data, index, "Before", this_sai.id, anchor.id
                    ):
                        results.append(timing)
                elif index == anchor_index:
                    if timing := self._timing(
                        data, index, "Fixed Reference", this_sai.id, this_sai.id
                    ):
                        results.append(timing)
                else:
                    if timing := self._timing(
                        data, index, "After", this_sai.id, anchor.id
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

    def _timing(
        self, data: dict, index: int, type: str, from_id: str, to_id: str
    ) -> Timing:
        try:
            windows: list = data["windows"]["items"]
            timepoints: list = data["timepoints"]["items"]
            timepoint = timepoints[index]
            window = windows[index]
            item: Timing = self._builder.create(
                Timing,
                {
                    "type": self._builder.klass_and_attribute_value(
                        Timing, "type", type
                    ),
                    "value": self._encoder.iso8601_duration(
                        timepoint["value"], timepoint["unit"]
                    ),
                    "valueLabel": self._timing_value_label(timepoints, index),
                    "name": f"TIMING-{index}",
                    "description": f"Timing {index + 1}",
                    "label": self._timing_value_label(timepoints, index),
                    "relativeToFrom": self._builder.klass_and_attribute_value(
                        Timing, "relativeToFrom", "start to start"
                    ),
                    "windowLabel": self._window_label(windows, index),
                    "windowLower": self._encoder.iso8601_duration(
                        window["before"], window["unit"]
                    )
                    if window["before"]
                    else "",
                    "windowUpper": self._encoder.iso8601_duration(
                        window["after"], window["unit"]
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
            if item["value"] == "1":
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
        self, data, instances: list[ScheduledInstance], timings: list[Timing]
    ):
        try:
            self._errors.debug(
                f"Instances: {len(instances)}, Timings: {len(timings)}",
                KlassMethodLocation(self.MODULE, "_add_timeline"),
            )
            exit = self._builder.create(ScheduleTimelineExit, {})
            duration = None
            return self._builder.create(
                ScheduleTimeline,
                {
                    "mainTimeline": True,
                    "name": "TIMELINE-1",
                    "description": "The main timeline",
                    "label": "Main timeline",
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
