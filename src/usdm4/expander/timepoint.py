from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import ScheduledActivityInstance
from usdm4.api.timing import Timing
from .tick import Tick
from simple_error_log import Errors


class Timepoint():

    def __init__(self, study_design: StudyDesign, timeline: ScheduleTimeline, sai: ScheduledActivityInstance, errors: Errors):
        self._sai: ScheduledActivityInstance = sai
        self._tick: int = self._calculate_hop(timeline, sai)
        self._errors = errors
        self._timeline = timeline
        self._study_design = study_design

    def to_dict(self):
        activities = [self._study_design.find_activity(x) for x in self._sai.activityIds]
        return {
            "tick": self._tick,
            "time": str(Tick(value=self._tick)),
            "label": self._sai.label,
            "encounter": self._study_design.find_encounter(self._sai.encounterId).label if self._sai.encounterId else None,
            "activities": {
                "ordered": False,
                "items": [
                    {
                        "label": x.label,
                        "procedures": [p.label for p in x.definedProcedures],
                    } for x in activities
                ]
            }
        }
    
    def _calculate_hop(self, timeline: ScheduleTimeline, sai: ScheduledActivityInstance) -> int:
        return self._calculate_next_hop(timeline, sai, 0)

    def _calculate_next_hop(self, timeline: ScheduleTimeline, sai: ScheduledActivityInstance, tick: int) -> int:
        timing: Timing = timeline.find_timing_from(sai.id)
        to_sai = timeline.find_timepoint(timing.relativeToScheduledInstanceId)
        before = timing.type.code == "C201357"
        to_timing: Timing = timeline.find_timing_from(to_sai.id)
        value = self._calculate_tick(timing)
        new_tick = tick - value if before else tick + value
        if to_timing.type.code == "C201358": # Anchor, so stop
            return new_tick
        else:
            return self._calculate_next_hop(timeline, to_sai, new_tick)

    def _calculate_tick(self, timing: Timing) -> int:
        # return self._duration_to_ticks(timing.value)
        try:
            return Tick(duration=timing.value).tick
        except Exception as e:
            self._errors.error(f"Failed to decode duration '{timing.value}', {e}")
            return 0

