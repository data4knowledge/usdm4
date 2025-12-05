import re
import json
import operator
from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
    ScheduledInstance,
    ConditionAssignment,
)
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from simple_error_log import Errors
from simple_error_log.error_location import KlassMethodLocation
from .timepoint import Timepoint


class Expander:
    MODULE = "usdm4.expander.expander.Expander"

    def __init__(
        self, study_design: StudyDesign, timeline: ScheduleTimeline, errors: Errors
    ):
        # self._path = None
        self._study_design = study_design
        self._timeline = timeline
        self._errors = errors
        self._id = 1
        self._nodes: list[Timepoint] = []

    def process(self):
        entry: ScheduledInstance = self._timeline.find_timepoint(self._timeline.entryId)
        self._process_si(self._timeline, entry, None, 0)
        sorted(self._nodes, key=lambda x: x.tick)

    def to_json(self) -> str:
        print(f"NODES: {len(self._nodes)}")
        return json.dumps({"nodes": [x.to_dict() for x in self._nodes]}, indent=4)

    def _process_si(
        self,
        timeline: ScheduleTimeline,
        si: ScheduledActivityInstance
        | ScheduledDecisionInstance
        | ScheduleTimelineExit,
        previous: Timepoint,
        offset: int,
    ):
        print(f"SI {si.id}, {si.instanceType}, {type(si)}")
        if si.id == "ScheduledDecisionInstance_1":
            print(f"SDI: {si}")
        if isinstance(si, ScheduledActivityInstance):
            # print(f"SAI with id {si.id}")
            tp = Timepoint(
                self._study_design,
                timeline,
                si,
                self._errors,
                self._id,
                previous.tick if previous else 0,
            )
            self._id += 1
            self._nodes.append(tp)
            if previous:
                previous.add_edge(tp)

            # Timepoint timeline
            if si.timelineId:
                print(f"Timepoint timeline {si.timelineId}")
                tp_timeline = self._study_design.find_timeline(si.timelineId)
                entry: ScheduledInstance = tp_timeline.find_timepoint(
                    tp_timeline.entryId
                )
                tp = self._process_si(tp_timeline, entry, tp, tp.tick)

            # Activity timelines
            a_timelines = tp.activity_timelines()
            for a_timeline in a_timelines:
                # print(f"ACTIVITY TIMELINE: {a_timeline.id}")
                entry: ScheduledInstance = a_timeline.find_timepoint(a_timeline.entryId)
                tp = self._process_si(a_timeline, entry, tp, tp.tick)

            # Next
            if si.defaultConditionId:
                tp = self._process_si(
                    timeline, timeline.find_timepoint(si.defaultConditionId), tp, offset
                )
            elif si.timelineExitId:
                tp = self._process_si(
                    timeline, timeline.find_exit(si.timelineExitId), tp, offset
                )
            else:
                self._errors.error(
                    f"Next instance error, {si}",
                    KlassMethodLocation(self.MODULE, "_process_si"),
                )
            return tp
        elif isinstance(si, ScheduledDecisionInstance):
            print(f"SDI with id {si.id}")
            if len(si.conditionAssignments) == 1:
                ca: ConditionAssignment = si.conditionAssignments[0]
                dc_op, dc_value = self._days_condition(ca.condition)
                if dc_op:
                    if dc_op(previous.tick, dc_value * 24 * 60 * 60):
                        tp = self._process_si(
                            timeline,
                            timeline.find_timepoint(ca.conditionTargetId),
                            previous,
                            offset,
                        )
                    else:
                        tp = self._process_si(
                            timeline,
                            timeline.find_timepoint(si.defaultConditionId),
                            previous,
                            offset,
                        )
                else:
                    self._errors.error(
                        f"No day condition encountered, being ignored.",
                        KlassMethodLocation(self.MODULE, "_process_si"),
                    )
                    tp = self._process_si(
                        timeline,
                        timeline.find_timepoint(si.defaultConditionId),
                        previous,
                        offset,
                    )
            else:
                self._errors.error(
                    f"Complex condition encountered, being ignored.",
                    KlassMethodLocation(self.MODULE, "_process_si"),
                )
                tp = self._process_si(
                    timeline,
                    timeline.find_timepoint(si.defaultConditionId),
                    previous,
                    offset,
                )
            return tp
        elif isinstance(si, ScheduleTimelineExit):
            return previous
        else:
            self._errors.error(
                f"Unknown instance type detected, {si}",
                KlassMethodLocation(self.MODULE, "_process_si"),
            )
            return previous

    def _days_condition(self, text) -> tuple[object, int]:
        try:
            operators = {">": operator.gt, "<": operator.lt, "=": operator.eq}
            pattern = r"(?i)days?\s*([<>=])\s*(\d+)"
            match = re.search(pattern, text)
            if match:
                op = operators[match.group(1)]  # Select the operator
                value = int(match.group(2))
                return op, value
            return None, None
        except Exception as e:
            self._errors.exception(
                f"Error detected processing, '{text}'",
                e,
                KlassMethodLocation(self.MODULE, "_days_condition"),
            )
            return None, None
