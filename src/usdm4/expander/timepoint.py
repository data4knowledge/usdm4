from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import ScheduledActivityInstance
from usdm4.api.timing import Timing
from .tick import Tick
from simple_error_log import Errors


class Timepoint:
    def __init__(
        self,
        study_design: StudyDesign,
        timeline: ScheduleTimeline,
        sai: ScheduledActivityInstance,
        errors: Errors,
        id: int,
        offset: int,
    ):
        self._sai: ScheduledActivityInstance = sai
        self._errors = errors
        self._timeline = timeline
        self._study_design = study_design
        self._tick: int = self._calculate_hop(timeline, sai) + offset
        self._id: str = f"TP_{id}"
        self._edges: list[str] = []

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def id(self) -> str:
        return self._id

    @property
    def activities(self) -> bool:
        return len(self._sai.activityIds) > 0

    def add_edge(self, next: "Timepoint") -> None:
        self._edges.append(next.id)

    def activity_timelines(self) -> list[ScheduleTimeline]:
        activities = [
            self._study_design.find_activity(x) for x in self._sai.activityIds
        ]
        return [
            self._study_design.find_timeline(x.timelineId)
            for x in activities
            if x.timelineId
        ]

    def to_dict(self):
        parents = self._study_design.activity_parent()
        activities = [
            self._study_design.find_activity(x) for x in self._sai.activityIds
        ]
        return {
            "id": self._id,
            "tick": self._tick,
            "time": str(Tick(value=self._tick)),
            "label": self._sai.label,
            "encounter": self._study_design.find_encounter(self._sai.encounterId).label
            if self._sai.encounterId
            else None,
            "main_timeline": self._timeline.mainTimeline,
            "activities": {
                "items": [
                    {
                        "label": x.label,
                        "parent": self._study_design.find_activity(parents[x.id]).label
                        if x.id in parents
                        else None,
                        "procedures": [p.label for p in x.definedProcedures],
                    }
                    for x in activities
                ]
            },
            "edges": self._edges,
        }

    def _calculate_hop(
        self, timeline: ScheduleTimeline, sai: ScheduledActivityInstance
    ) -> int:
        return self._calculate_next_hop(timeline, sai, 0)

    def _calculate_next_hop(
        self, timeline: ScheduleTimeline, sai: ScheduledActivityInstance, tick: int
    ) -> int:
        # print(f"NEXT HOP: {timeline.id}, {sai.id}")
        timing: Timing = timeline.find_timing_from(sai.id)
        # print(f"TIMING: {timing}")
        to_sai = timeline.find_timepoint(timing.relativeToScheduledInstanceId)
        before = timing.type.code == "C201357"
        to_timing: Timing = timeline.find_timing_from(to_sai.id)
        value = self._calculate_tick(timing)
        new_tick = tick - value if before else tick + value
        if to_timing.type.code == "C201358":  # Anchor, so stop
            return new_tick
        else:
            return self._calculate_next_hop(timeline, to_sai, new_tick)

    def _calculate_tick(self, timing: Timing) -> int:
        try:
            return Tick(duration=timing.value).tick
        except Exception as e:
            self._errors.error(f"Failed to decode duration '{timing.value}', {e}")
            return 0
