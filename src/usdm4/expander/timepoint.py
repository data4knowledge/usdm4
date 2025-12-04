from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import ScheduledActivityInstance
from usdm4.api.timing import Timing
from simple_error_log import Errors


class Timepoint():

    def __init__(self, timeline: ScheduleTimeline, sai: ScheduledActivityInstance, errors: Errors):
        self._sai: ScheduledActivityInstance = sai
        self._tick: int = self._calculate_hop(timeline, sai)
        self._errors = errors

    def to_dict(self):
        return {"tick": self._tick}
    
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
        return self._duration_to_ticks(timing.value)

    def _duration_to_ticks(self, duration: str) -> int:
        if duration.endswith("Y"):
            return int(duration[1:-1]) * 365 * 24 * 60 * 60
        elif duration.endswith("M"):
            return int(duration[1:-1]) * 30 * 24 * 60 * 60
        elif duration.endswith("W"):
            return int(duration[1:-1]) * 7 * 24 * 60 * 60
        elif duration.endswith("D"):
            return int(duration[1:-1]) * 24 * 60 * 60
        elif duration.endswith("H"):
            return int(duration[1:-1]) * 60 * 60
        elif duration.endswith("M"):
            return int(duration[1:-1]) * 60
        elif duration.endswith("S"):
            return int(duration[1:-1])
        else:
            self._errors.error(f"Failed to decode duration '{duration}")
            return 0

