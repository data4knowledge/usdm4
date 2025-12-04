from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import ScheduledActivityInstance, ScheduledDecisionInstance, ScheduledInstance
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from simple_error_log import Errors
from .path import Path
from .timepoint import Timepoint
from .exit import Exit

class Expander():

    def __init__(self, study_design: StudyDesign, timeline: ScheduleTimeline, errors: Errors):
        self._path = None
        self._study_design = study_design
        self._timeline = timeline
        self._errors = errors

    def process(self):
        self._process_timeline()

    def to_json(self):
        return self._path.to_json()
    
    def _process_timeline(self):
        self._path = Path(self._errors)
        entry: ScheduledInstance = self._timeline.find_timepoint(self._timeline.entryId)
        self._process_si(entry)

    def _process_si(self, si: ScheduledActivityInstance | ScheduledDecisionInstance | ScheduleTimelineExit):
        if isinstance(si, ScheduledActivityInstance):
            tp = Timepoint(self._study_design, self._timeline, si, self._errors)
            self._path.add(tp)
            if si.defaultConditionId:
                self._process_si(self._timeline.find_timepoint(si.defaultConditionId))
            elif si.timelineExitId:
                self._process_si(self._timeline.find_exit(si.timelineExitId))
            else:
                self._errors.error(f"Next instance error, {si}") 
        elif isinstance(si, ScheduledDecisionInstance):
            pass
        elif isinstance(si, ScheduleTimelineExit):
            exit = Exit(si)
            self._path.add(exit)
        else:
            self._errors.error(f"Unknown instance type detected, {si.instanceType}") 
