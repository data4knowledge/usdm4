"""Expand a schedule timeline into the timepoints one participant passes through.

The expander is illustrative: it shows one way a USDM timeline can be executed. It is not
normative.

Loops (design § 7, decision U4-11). A decision branch that leads back to an instance already
reached on this walk is a loop. A loop is run twice, so the decision goes each way once: back the
first time, out the second (a cycle range `Cycle 3+` gives cycle 3, cycle 4, then on). When the
condition states a minimum (`≥ 7 days and washed out, or 28 days`), the loop is run until that
minimum has passed since the loop was first entered, then left. A decision that is not a loop
keeps the original rule: a `days <op> n` condition is tested, anything else takes the default.

Time. An instance's time is its timing chain back to its anchor, plus a shift for the walk. The
shift moves when the walk re-enters a loop (the loop's start falls at the decision's time) and
when it reaches an instance hung from a different anchor (period 2 after a gate starts at the
decision's time).
"""

import operator
import re
from collections import Counter
from typing import ClassVar

from simple_error_log import Errors
from simple_error_log.error_location import KlassMethodLocation

from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.scheduled_instance import (
    ConditionAssignment,
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
    ScheduledInstance,
)
from usdm4.api.study_design import StudyDesign

from .tick import Tick
from .timepoint import Timepoint


class Expander:
    MODULE = "usdm4.expander.expander.Expander"
    BEFORE = "C201357"
    FIXED_REFERENCE = "C201358"
    STEP_LIMIT = 10000
    _UNITS: ClassVar[dict[str, int]] = {
        "minute": 60,
        "hour": 3600,
        "day": 86400,
        "week": 604800,
        "month": 30 * 86400,
        "year": 365 * 86400,
    }
    _MINIMUM_RE = re.compile(
        r"(?i)(?:≥|>=)\s*(\d+)\s*(minute|hour|day|week|month|year)s?\b"
    )

    def __init__(
        self, study_design: StudyDesign, timeline: ScheduleTimeline, errors: Errors
    ):
        self._study_design = study_design
        self._timeline = timeline
        self._errors = errors
        self._id = 1
        self._nodes: list[Timepoint] = []

    @property
    def nodes(self):
        return self._nodes

    def process(self):
        entry: ScheduledInstance = self._timeline.find_timepoint(self._timeline.entryId)
        self._process_si(self._timeline, entry, 0)
        self._nodes = sorted(
            [node for node in self._nodes if node.activities], key=lambda x: x.tick
        )

    def _process_si(
        self,
        timeline: ScheduleTimeline,
        si: ScheduledActivityInstance
        | ScheduledDecisionInstance
        | ScheduleTimelineExit,
        offset: int,
    ):
        """Walk a timeline from `si`; `offset` is the time the walk starts at."""
        shift = offset
        previous_tick = offset
        anchor = None
        from_decision = False
        first_tick: dict[str, int] = {}
        reached: Counter = Counter()
        steps = 0
        while si is not None:
            steps += 1
            if steps > self.STEP_LIMIT:
                self._errors.error(
                    f"Expansion stopped after {self.STEP_LIMIT} steps on timeline '{timeline.id}', a loop did not end",
                    KlassMethodLocation(self.MODULE, "_process_si"),
                )
                return
            if isinstance(si, ScheduledActivityInstance):
                hop = self._hop(timeline, si.id)
                if hop is not None:
                    if (from_decision and si.id in first_tick) or (
                        anchor is not None and hop[1] != anchor
                    ):
                        shift = previous_tick - hop[0]
                    anchor = hop[1]
                from_decision = False
                reached[si.id] += 1
                tp = Timepoint(
                    self._study_design,
                    timeline,
                    si,
                    self._errors,
                    self._id,
                    shift,
                    reached[si.id],
                )
                self._id += 1
                self._nodes.append(tp)
                first_tick.setdefault(si.id, tp.tick)
                previous_tick = tp.tick
                self._sub_timelines(si, tp)
                si = self._next_after_activity(timeline, si)
            elif isinstance(si, ScheduledDecisionInstance):
                hop = self._hop(timeline, si.id)
                tick = hop[0] + shift if hop is not None else previous_tick
                reached[si.id] += 1
                first_tick.setdefault(si.id, tick)
                target_id = self._decide(si, tick, previous_tick, first_tick, reached)
                previous_tick = tick
                from_decision = True
                si = timeline.find_timepoint(target_id)
            elif isinstance(si, ScheduleTimelineExit):
                return
            else:
                self._errors.error(
                    f"Unknown instance type detected, {si}",
                    KlassMethodLocation(self.MODULE, "_process_si"),
                )
                return

    def _sub_timelines(self, si: ScheduledActivityInstance, tp: Timepoint) -> None:
        timelines = []
        if si.timelineId:
            timelines.append(self._study_design.find_timeline(si.timelineId))
        timelines += tp.activity_timelines()
        for sub_timeline in timelines:
            entry: ScheduledInstance = sub_timeline.find_timepoint(sub_timeline.entryId)
            self._process_si(sub_timeline, entry, tp.tick)

    def _next_after_activity(
        self, timeline: ScheduleTimeline, si: ScheduledActivityInstance
    ):
        if si.defaultConditionId:
            return timeline.find_timepoint(si.defaultConditionId)
        if not si.timelineExitId:
            self._errors.error(
                f"Next instance error, {si}",
                KlassMethodLocation(self.MODULE, "_process_si"),
            )
        return None

    def _decide(
        self,
        si: ScheduledDecisionInstance,
        tick: int,
        previous_tick: int,
        first_tick: dict[str, int],
        reached: Counter,
    ) -> str:
        if len(si.conditionAssignments) != 1:
            self._errors.error(
                "Complex condition encountered, being ignored.",
                KlassMethodLocation(self.MODULE, "_process_si"),
            )
            return si.defaultConditionId
        ca: ConditionAssignment = si.conditionAssignments[0]
        dc_op, dc_value = self._days_condition(ca.condition)
        if dc_op:
            if dc_op(previous_tick, dc_value * 24 * 60 * 60):
                return ca.conditionTargetId
            return si.defaultConditionId
        loop = self._loop(si, ca, first_tick)
        if loop is None:
            self._errors.error(
                "No day condition encountered, being ignored.",
                KlassMethodLocation(self.MODULE, "_process_si"),
            )
            return si.defaultConditionId
        back, out = loop
        minimum = self._minimum(ca.condition)
        if minimum is None:
            leave = reached[si.id] >= 2
        else:
            leave = tick - first_tick[back] >= minimum
        return out if leave else back

    def _loop(
        self,
        si: ScheduledDecisionInstance,
        ca: ConditionAssignment,
        first_tick: dict[str, int],
    ) -> tuple[str, str] | None:
        """(back, out) when exactly one branch returns to an instance already reached."""
        default_back = si.defaultConditionId in first_tick
        condition_back = ca.conditionTargetId in first_tick
        if default_back and not condition_back:
            return si.defaultConditionId, ca.conditionTargetId
        if condition_back and not default_back:
            return ca.conditionTargetId, si.defaultConditionId
        return None

    def _minimum(self, text: str) -> int | None:
        match = self._MINIMUM_RE.search(text or "")
        if match:
            return int(match.group(1)) * self._UNITS[match.group(2).lower()]
        return None

    def _hop(self, timeline: ScheduleTimeline, instance_id: str) -> tuple | None:
        """(time from the anchor, anchor id) by the timing chain; None when there is no chain."""
        tick = 0
        current = instance_id
        seen = set()
        while current not in seen:
            seen.add(current)
            timing = timeline.find_timing_from(current)
            if timing is None:
                return None
            if timing.type.code == self.FIXED_REFERENCE:
                return tick, current
            try:
                value = Tick(duration=timing.value).tick
            except Exception:  # noqa: BLE001 - Tick raises a bare Exception; Timepoint reports it
                value = 0
            tick += -value if timing.type.code == self.BEFORE else value
            current = timing.relativeToScheduledInstanceId
        return None

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
