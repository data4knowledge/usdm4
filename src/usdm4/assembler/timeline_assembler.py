"""The timeline assembler — orchestrates parse → plan → build (issue 63).

Input: a list of ``ScheduleTimelineInput`` dicts (validated and dumped by
``Assembler``). Every header value is structured by the caller (issue 73,
U4-35); ``usdm4`` never reads printed text — ``timeline/columns.py`` copies the
values across, printed text kept only as labels. Specification:
``docs/spec/timeline_assembler.md``.

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
from usdm4.api.scheduled_instance import ScheduledActivityInstance
from usdm4.api.study_epoch import StudyEpoch
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.assembler.timeline.build import SharedState, TimelineBuild
from usdm4.assembler.timeline.columns import ParsedTimeline, parse_timeline
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
        # Each built timeline's instances by column id, by the timeline's
        # caller id (GitHub 111).
        self._instances: dict[str, dict[str, ScheduledActivityInstance]] = {}

    def execute(self, data) -> None:
        """Assemble every timeline in ``data`` (a list of timeline dicts; one
        dict is accepted as a list of one).

        Each timeline is parsed first. A timeline is always built if at all
        possible (U4-17): a value sent as text only is a warning and is not
        read. Only a timeline with no columns is reported and not
        built — it can yield no instances, so nothing built from it would be
        reachable.
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
            built: list[tuple[ParsedTimeline, ScheduleTimeline, int]] = []
            for index in keep:
                timeline = self._build_one(
                    parsed[index], planner, index + 1, index == main
                )
                if timeline is not None:
                    built.append((parsed[index], timeline, index + 1))
            # R7. The activity a profile hangs off usually sits on another
            # timeline, possibly later in the input, so profiles are attached
            # only once every timeline is built.
            self._attach_profiles(built)
            # One global ordering pass across every timeline's activities, so
            # previousId/nextId are consistent and shared activities are linked
            # once.
            self._builder.double_link(self._state.activities, "previousId", "nextId")
            # Issue 82: epochs and encounters are chained the same way — one
            # chain each, across every timeline in input order. Both lists are
            # already in column order with no duplicates (a copied column
            # reuses the original's encounter, issue 75), and one epoch chain
            # per design is what DDF00088 expects.
            self._builder.double_link(self._epochs, "previousId", "nextId")
            self._builder.double_link(self._encounters, "previousId", "nextId")
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
            timeline = parse_timeline(data, self._errors, index + 1)
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
    ) -> ScheduleTimeline | None:
        try:
            plan = planner.plan(timeline, t)
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
                if timeline.id is not None:
                    self._instances[timeline.id] = built.instances
            return built.timeline
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of timeline {t}",
                e,
                KlassMethodLocation(self.MODULE, "_build_one"),
            )
            return None

    # ------------------------------------------------------------------
    # R7 — profile attachment

    def _attach_profiles(
        self, built: list[tuple[ParsedTimeline, ScheduleTimeline, int]]
    ) -> None:
        """Hang each profile timeline where its input says (R7, GitHub 111):
        off the activity its ``attaches_to`` names (``Activity.timelineId``),
        or from the instances its ``attaches_at`` names
        (``ScheduledActivityInstance.timelineId``). The activity is matched on
        identity (U4-12) across every built timeline; an instance by its
        timeline's id and column id.

        At an activity — not attached, profile built unattached:
        - no ``attaches_to`` and no ``attaches_at``, or no activity by that
          name — warning;
        - the activity has children — error (U4-32, DDF00160);
        - the activity is already attached to an earlier profile — error
          (U4-34: first in input order wins);
        - attaching would make a loop, directly or through other profiles —
          error (U4-31).
        Attached with a warning: the activity is scheduled on no other
        timeline (U4-33).

        At instances — each instance on its own; a refused one is left
        unattached, the others attached:
        - the instance's timeline was not built — error (U4-40);
        - the instance is already attached to an earlier profile — error
          (U4-41: first in input order wins);
        - attaching would make a loop: the instance's timeline is reached
          from the profile — error (U4-42)."""
        location = KlassMethodLocation(self.MODULE, "_attach_profiles")
        activity_by_id = {a.id: a for a in self._state.activities}
        timeline_by_id = {tl.id: tl for _, tl, _ in built}
        attached_by: dict[str, int] = {}
        instance_by: dict[str, int] = {}
        for parsed, profile, t in built:
            if parsed.family != "profile":
                continue
            if parsed.attaches_at:
                self._attach_at_instances(
                    parsed, profile, t, activity_by_id, timeline_by_id, instance_by
                )
                continue
            name = (parsed.attaches_to or "").strip()
            if not name:
                self._errors.warning(
                    f"Profile timeline {t} has no attaches_to or attaches_at; "
                    f"built unattached",
                    location,
                )
                continue
            key = self._state.naming.identity(name)
            # A group with a child of the same name (issue 88): the profile
            # belongs to the scheduled child, not the group.
            activity = self._state.activity_by_name.get(
                f"{key}\x00in\x00{key}"
            ) or self._state.activity_by_name.get(key)
            if activity is None:
                self._errors.warning(
                    f"Profile timeline {t} attaches to '{name}', which is not an "
                    f"activity; built unattached",
                    location,
                )
                continue
            if activity.childIds:
                self._errors.error(
                    f"Profile timeline {t} attaches to '{name}', which has child "
                    f"activities; not attached (DDF00160)",
                    location,
                )
                continue
            if activity.id in attached_by:
                self._errors.error(
                    f"Profile timeline {t} attaches to '{name}', already attached "
                    f"to profile timeline {attached_by[activity.id]}; not attached",
                    location,
                )
                continue
            if self._reaches(profile, activity.id, activity_by_id, timeline_by_id):
                self._errors.error(
                    f"Profile timeline {t} attaches to '{name}', which the profile "
                    f"itself reaches; not attached (loop)",
                    location,
                )
                continue
            if not any(
                activity.id in self._activity_ids(other)
                for _, other, _ in built
                if other is not profile
            ):
                self._errors.warning(
                    f"Profile timeline {t} attaches to '{name}', which is scheduled "
                    f"on no other timeline; attached",
                    location,
                )
            activity.timelineId = profile.id
            attached_by[activity.id] = t

    def _attach_at_instances(
        self,
        parsed: ParsedTimeline,
        profile: ScheduleTimeline,
        t: int,
        activity_by_id: dict[str, Activity],
        timeline_by_id: dict[str, ScheduleTimeline],
        instance_by: dict[str, int],
    ) -> None:
        """GitHub 111: the profile is run from each instance ``attaches_at``
        names — ``ScheduledActivityInstance.timelineId``. Each instance is
        attached or refused on its own (``_attach_profiles``)."""
        location = KlassMethodLocation(self.MODULE, "_attach_at_instances")
        for timeline_id, column_id in parsed.attaches_at:
            where = (
                f"Profile timeline {t} attaches at timeline '{timeline_id}' "
                f"column '{column_id}'"
            )
            instance = self._instances.get(timeline_id, {}).get(column_id)
            if instance is None:
                self._errors.error(
                    f"{where}, which was not built; not attached", location
                )
                continue
            if instance.id in instance_by:
                self._errors.error(
                    f"{where}, already attached to profile timeline "
                    f"{instance_by[instance.id]}; not attached",
                    location,
                )
                continue
            owner = next(
                (tl for tl in timeline_by_id.values() if instance in tl.instances),
                None,
            )
            if owner is not None and self._reaches_timeline(
                profile, owner.id, activity_by_id, timeline_by_id
            ):
                self._errors.error(
                    f"{where}, whose timeline the profile itself reaches; not "
                    f"attached (loop)",
                    location,
                )
                continue
            instance.timelineId = profile.id
            instance_by[instance.id] = t

    @staticmethod
    def _activity_ids(timeline: ScheduleTimeline) -> set[str]:
        """Every activity an instance of ``timeline`` schedules. Decision
        instances schedule none."""
        ids: set[str] = set()
        for instance in timeline.instances:
            ids.update(getattr(instance, "activityIds", None) or [])
        return ids

    @classmethod
    def _reaches(
        cls,
        timeline: ScheduleTimeline,
        activity_id: str,
        activity_by_id: dict[str, Activity],
        timeline_by_id: dict[str, ScheduleTimeline],
    ) -> bool:
        """True when ``activity_id`` is scheduled on ``timeline`` or on any
        timeline reached from it (``_reached``) — so attaching ``timeline`` to
        that activity would close a loop."""
        return any(
            activity_id in cls._activity_ids(reached)
            for reached in cls._reached(timeline, activity_by_id, timeline_by_id)
        )

    @classmethod
    def _reaches_timeline(
        cls,
        timeline: ScheduleTimeline,
        target_id: str,
        activity_by_id: dict[str, Activity],
        timeline_by_id: dict[str, ScheduleTimeline],
    ) -> bool:
        """True when the timeline ``target_id`` is ``timeline`` or is reached
        from it — so running ``timeline`` from an instance of the target would
        close a loop (GitHub 111)."""
        return any(
            reached.id == target_id
            for reached in cls._reached(timeline, activity_by_id, timeline_by_id)
        )

    @classmethod
    def _reached(
        cls,
        timeline: ScheduleTimeline,
        activity_by_id: dict[str, Activity],
        timeline_by_id: dict[str, ScheduleTimeline],
    ) -> list[ScheduleTimeline]:
        """``timeline`` and every timeline reached from it: through an
        activity it schedules whose ``timelineId`` is set, or an instance of
        it whose ``timelineId`` is set (GitHub 111). Each once."""
        seen: set[str] = set()
        out: list[ScheduleTimeline] = []
        todo = [timeline]
        while todo:
            current = todo.pop()
            if current.id in seen:
                continue
            seen.add(current.id)
            out.append(current)
            for scheduled in cls._activity_ids(current):
                sub = activity_by_id.get(scheduled)
                if sub is not None and sub.timelineId in timeline_by_id:
                    todo.append(timeline_by_id[sub.timelineId])
            for instance in current.instances:
                target = getattr(instance, "timelineId", None)
                if target in timeline_by_id:
                    todo.append(timeline_by_id[target])
        return out

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
