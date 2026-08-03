from typing import List, Literal, Union
from .api_base_model import ApiBaseModelWithIdNameLabelAndDesc
from .schedule_timeline_exit import ScheduleTimelineExit
from .scheduled_instance import ScheduledActivityInstance, ScheduledDecisionInstance
from .timing import Timing
from .duration import Duration


class ScheduleTimeline(ApiBaseModelWithIdNameLabelAndDesc):
    mainTimeline: bool
    entryCondition: str
    entryId: str
    exits: List[ScheduleTimelineExit] = []
    timings: List[Timing] = []
    instances: List[Union[ScheduledDecisionInstance, ScheduledActivityInstance]] = []
    plannedDuration: Union[Duration, None] = None
    instanceType: Literal["ScheduleTimeline"]

    def first_timepoint(self) -> ScheduledActivityInstance:
        return self.instances[0] if self.instances else None

    def find_timepoint(
        self, id: str
    ) -> ScheduledActivityInstance | ScheduledDecisionInstance:
        return next((x for x in self.instances if x.id == id), None)

    def find_exit(self, id: str) -> ScheduleTimelineExit:
        return next((x for x in self.exits if x.id == id), None)

    def timepoint_list(self) -> list:
        return self.instances

    def find_timing_from(self, id: str) -> Timing:
        return next(
            (x for x in self.timings if x.relativeFromScheduledInstanceId == id), None
        )

    def find_timing_to(self, id: str) -> Timing:
        return next(
            (x for x in self.timings if x.relativeToScheduledInstanceId == id), None
        )
