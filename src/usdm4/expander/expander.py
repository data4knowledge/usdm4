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
        self._path = Path(self._errors)
        entry: ScheduledInstance = self._timeline.find_timepoint(self._timeline.entryId)
        self._process_si(self._timeline, entry)

    def to_json(self):
        return self._path.to_json()
    
    def _process_si(self, timeline: ScheduleTimeline, si: ScheduledActivityInstance | ScheduledDecisionInstance | ScheduleTimelineExit, offset: int=0):
        if isinstance(si, ScheduledActivityInstance):
            print(f"SAI with id {si.id}")
            tp = Timepoint(self._study_design, timeline, si, self._errors, offset)
            self._path.add(tp)

            # Timepoint timeline
            if si.timelineId:
                print(f"Timepoint timeline")
                tp_timeline = self._study_design.find_timeline(si.timelineId)
                entry: ScheduledInstance = tp_timeline.find_timepoint(tp_timeline.entryId)
                self._process_si(tp_timeline, entry, tp.tick)

            # Activity timelines
            a_timelines = tp.activity_timelines()
            for a_timeline in a_timelines:
                # print(f"ACTIVITY TIMELINE: {a_timeline.id}")
                entry: ScheduledInstance = a_timeline.find_timepoint(a_timeline.entryId)
                self._process_si(a_timeline, entry, tp.tick)

            # Next 
            if si.defaultConditionId:
                self._process_si(timeline, timeline.find_timepoint(si.defaultConditionId), offset)
            elif si.timelineExitId:
                self._process_si(timeline, timeline.find_exit(si.timelineExitId), offset)
            else:
                self._errors.error(f"Next instance error, {si}") 
        elif isinstance(si, ScheduledDecisionInstance):
            pass
        elif isinstance(si, ScheduleTimelineExit):
            exit = Exit(si)
            self._path.add(exit)
        else:
            self._errors.error(f"Unknown instance type detected, {si}") 
