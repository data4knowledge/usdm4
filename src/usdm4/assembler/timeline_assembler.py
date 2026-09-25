"""The timeline assembler — orchestrates parse → plan → build (issue 63).

Input: a list of ``ScheduleTimelineInput`` dicts (validated and dumped by
``Assembler``). Every header value is text — printed text plus a pattern form
— and all parsing happens here, in ``timeline/columns.py`` with the grammar in
``timeline/grammar.py``. Design: ``docs/timeline_assembler_design.md``.

The public surface is unchanged, because three callers read it: ``Assembler``
calls ``execute`` and ``clear``; ``StudyDesignAssembler`` reads ``epochs``,
``encounters``, ``activities`` and ``timelines``; ``StudyAssembler`` reads
``conditions``, ``biomedical_concepts`` and ``biomedical_concept_surrogates``.
"""

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.api.activity import Activity
from usdm4.api.biomedical_concept import BiomedicalConcept
from usdm4.api.biomedical_concept_surrogate import BiomedicalConceptSurrogate
from usdm4.api.condition import Condition
from usdm4.api.encounter import Encounter
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.study_epoch import StudyEpoch
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.assembler.timeline.build import SharedState, TimelineBuild
from usdm4.assembler.timeline.columns import ParsedTimeline, parse_timeline
from usdm4.assembler.timeline.grammar import PatternError
from usdm4.assembler.timeline.plan import Planner
from usdm4.builder.builder import Builder


class TimelineAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.timeline_assembler.TimelineAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._state = SharedState()
        self._timelines: list[ScheduleTimeline] = []
        self._epochs: list[StudyEpoch] = []
        self._encounters: list[Encounter] = []
        self._conditions: list[Condition] = []

    def execute(self, data) -> None:
        """Assemble every timeline in ``data`` (a list of timeline dicts; one
        dict is accepted as a list of one).

        Each timeline is parsed first. A timeline whose patterns the grammar
        refuses, or that has no columns, is reported once and not built — it
        can yield no instances, so nothing built from it would be reachable.
        Exactly one built timeline carries ``mainTimeline``: the first of type
        ``main``, else the first. Ordinals are the timeline's own position in
        the input, so a skipped one leaves a gap (``TIMELINE-1``,
        ``TIMELINE-3``) rather than renaming the others.
        """
        try:
            timelines = self._normalise(data)
            parsed = self._parse_all(timelines)
            keep = [i for i, p in enumerate(parsed) if p is not None]
            main = self._main_ordinal(parsed, keep)
            # House style: names are bare within a single-timeline study and
            # carry a `T{t}-` prefix only where more than one timeline is built.
            self._state.naming.multi_timeline = len(keep) > 1
            planner = Planner(self._errors)
            for index in keep:
                self._build_one(parsed[index], planner, index + 1, index == main)
            # One global ordering pass across every timeline's activities, so
            # previousId/nextId are consistent and shared activities are linked
            # once.
            self._builder.double_link(self._state.activities, "previousId", "nextId")
        except Exception as e:
            self._errors.exception(
                "Failed during creation of study design",
                e,
                KlassMethodLocation(self.MODULE, "execute"),
            )

    @staticmethod
    def _normalise(data) -> list[dict]:
        if data is None:
            return []
        return [data] if isinstance(data, dict) else list(data)

    def _parse_all(self, timelines: list[dict]) -> list[ParsedTimeline | None]:
        parsed: list[ParsedTimeline | None] = []
        for index, data in enumerate(timelines):
            location = KlassMethodLocation(self.MODULE, "_parse_all")
            try:
                timeline = parse_timeline(data)
            except PatternError as e:
                self._errors.error(f"Timeline {index + 1} not created: {e}", location)
                parsed.append(None)
                continue
            if not timeline.columns:
                self._errors.error(
                    f"Timeline {index + 1} has no columns, not created "
                    f"({len(timeline.activities)} activities discarded with it)",
                    location,
                )
                parsed.append(None)
                continue
            parsed.append(timeline)
        return parsed

    @staticmethod
    def _main_ordinal(
        parsed: list[ParsedTimeline | None], keep: list[int]
    ) -> int | None:
        if not keep:
            return None
        for index in keep:
            if parsed[index].type == "main":
                return index
        return keep[0]

    def _build_one(
        self, timeline: ParsedTimeline, planner: Planner, t: int, is_main: bool
    ) -> None:
        try:
            plan = planner.plan(timeline)
            built = TimelineBuild(
                self._builder,
                self._errors,
                self._encoder,
                self._state,
                timeline,
                plan,
                t,
                is_main,
            ).build()
            self._epochs += built.epochs
            self._encounters += built.encounters
            self._conditions += built.conditions
            if built.timeline:
                self._timelines.append(built.timeline)
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of timeline {t}",
                e,
                KlassMethodLocation(self.MODULE, "_build_one"),
            )

    @property
    def timelines(self) -> list[ScheduleTimeline]:
        return self._timelines

    @property
    def encounters(self) -> list[Encounter]:
        return self._encounters

    @property
    def epochs(self) -> list[StudyEpoch]:
        return self._epochs

    @property
    def activities(self) -> list[Activity]:
        return self._state.activities

    @property
    def conditions(self) -> list[Condition]:
        return self._conditions

    @property
    def biomedical_concepts(self) -> list[BiomedicalConcept]:
        return self._state.biomedical_concepts

    @property
    def biomedical_concept_surrogates(self) -> list[BiomedicalConceptSurrogate]:
        return self._state.biomedical_concept_surrogates
