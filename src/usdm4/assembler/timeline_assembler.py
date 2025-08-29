from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.scheduled_instance import ScheduledInstance, ScheduledActivityInstance
from usdm4.api.activity import Activity
from usdm4.api.study_epoch import StudyEpoch
from usdm4.api.encounter import Encounter
from usdm4.api.timing import Timing


class TimelineAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.timeline_assembler.TimelineAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._timelines = None

    def execute(self, data: dict) -> None:
        try:
            self._epochs = self._add_epochs(data)
            self._encounters = self._add_encounters(data)
            self._activities = self._add_activities(data)
            instances = self._add_instances(data)
            timings = self._add_timing(data)
            return self._add_timeline(data, instances, timings)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(
                "Failed during creation of study design", e, location
            )

    @property
    def timelines(self) -> list[ScheduleTimeline]:
        return self._timelines

    def _add_epochs(self, data) -> list[ScheduledInstance]:
        results = []
        map = {}
        items = data["raw"]["epochs"]
        table = data["final"]["table-001"]
        instances = table["schedule_columns_data"]
        for index, item in enumerate(items):
            label = item["text"]
            name = f"EPOCH-{label.upper()}"
            if name not in map:
                epoch = self._builer.create(
                    StudyEpoch,
                    {
                        "name": name,
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
            instances[index]["encounter_id"] = epoch.id

    def _add_encounters(self, data) -> list[Encounter]:
        results = []
        table = data["final"]["table-001"]
        instances = table["schedule_columns_data"]
        items = table["grid_columns"]
        item: dict[str]
        for index, item in enumerate(items):
            encounter = self._builder.create(
                Encounter,
                {
                    "name": f"ENCOUNTER-{item['header_text'].upper()}",
                    "description": f"Encounter {item['header_text']}",
                    "label": item["header_text"],
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
                            Encounter, "environmentalSettings", "In Person"
                        )
                    ],
                    "transitionStartRule": None,
                    "transitionEndRule": None,
                    "scheduledAtId": None,  # @todo
                },
            )
            results.append(encounter)
            instances[index]["encounter_id"] = encounter.id

    def _add_activities(self, data) -> list[Activity]:
        results = []
        table = data["final"]["table-001"]
        items = table["activity_rows"]
        item: dict[str]
        for item in items:
            params = {
                "name": f"ACTIVITY-{item['activity_name'].to_upper()}",
                "description": f"Activity {item['activity_name']}",
                "label": item["activity_name"],
                "definedProcedures": [],
                "biomedicalConceptIds": [],
                "bcCategoryIds": [],
                "bcSurrogateIds": [],
                "timelineId": None,
            }
            results.append(self._builder.create(Activity, params))
        return results

    def _add_instances(self, data) -> list[ScheduledInstance]:
        results = []
        table = data["final"]["table-001"]
        items = table["schedule_columns_data"]
        item: dict[str]
        for item in items:
            sai = self._builder.create(
                ScheduledActivityInstance,
                {
                    "name": f"SAI-{item['timepoint_reference'].to_upper()}",
                    "description": f"Scheduled activity instance {item['temporal_value']}",
                    "label": item["temporal_value"],
                    "timelineExitId": None,
                    "encounterId": item["encounter_id"],
                    "scheduledInstanceTimelineId": None,
                    "defaultConditionId": None,
                    "epochId": item["epoch_id"],
                    "activityIds": [],
                },
            )
            item["sai_id"] = sai.id
            results.append(sai)
        return results

    def _add_timing(self, data) -> list[ScheduledInstance]:
        results = []
        table = data["final"]["table-001"]
        items = table["schedule_columns_data"]
        anchor_index = self._find_anchor(data)
        anchor_id = items[anchor_index]["sai_id"]
        item: dict[str]
        for index, item in enumerate(items):
            this_id = item["sai_id"]
            if index < anchor_index:
                self._timing(self, index, item, "Before", this_id, anchor_id)
            elif index == anchor_index:
                self._timing(self, index, item, "Fixed Reference", this_id, this_id)
            else:
                self._timing(self, index, item, "After", anchor_id, this_id)
        return results

    def _timing(
        self, data: dict, index, int, type: str, from_id: str, to_id: str
    ) -> Timing:
        item: Timing = self._create(
            Timing,
            {
                "type": self._builder.klass_and_attribute_value(Timing, "type", type),
                "value": "ENCODE ???",
                "valueLabel": "???",
                "name": f"TIMING-{index}",
                "description": f"Timing {index + 1}",
                "label": "",
                "relativeToFrom": self._builder.klass_and_attribute_value(
                    Timing, "relativeToFrom", "start to start"
                ),
                "windowLabel": "",
                "windowLower": "",
                "windowUpper": "",
                "relativeFromScheduledInstanceId": from_id,
                "relativeToScheduledInstanceId": to_id,
            },
        )

    def _find_anchor(self, data) -> int:
        table = data["final"]["table-001"]
        items = table["schedule_columns_data"]
        item: dict[str]
        for index, item in enumerate(items):
            if item["temporal_dict"]["value"] == "1":
                return index
        return 0

    def _add_timeline(
        self, data, instances: list[ScheduledInstance], timings: list[Timing]
    ):
        exit = self._builder.create(ScheduleTimelineExit, {})
        # duration = (
        #     self._builder.create(
        #         Duration,
        #         {
        #             "text": self.duration_text,
        #             "quantity": self.duration,
        #             "durationWillVary": False,
        #             "reasonDurationWillVary": "",
        #         },
        #     )
        #     if self.duration
        #     else None
        # )
        duration = None
        return self._builder.create(
            ScheduleTimeline,
            {
                "mainTimeline": True,
                "name": "MAIN-TIMELINE",
                "description": "The main timeline",
                "label": "Main timeline",
                "entryCondition": "Paricipant identified",
                "entryId": instances[0].id,
                "exits": exit,
                "plannedDuration": duration,
                "instances": instances,
                "timings": timings,
            },
        )
