from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit

class Exit():

    def __init__(self, exit: ScheduleTimelineExit):
        self._exit: ScheduleTimelineExit = exit
    
    def _to_dict(self) -> dict:
        return {}