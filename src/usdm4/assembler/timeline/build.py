"""Build — issue 63, part 63.4.

Turns one parsed and planned timeline into USDM objects through the builder:
epochs, encounters, activities (shared across timelines), scheduled activity
instances, timings, conditions and the ``ScheduleTimeline``.

The order objects are created in is part of the output — the builder numbers
ids per class as they are made — so it is kept exactly as it was before the
restructure: epochs, encounters, activities, instances, timings, cell links,
conditions, timeline.
"""

from dataclasses import dataclass, field

from simple_error_log.error_location import KlassMethodLocation
from simple_error_log.errors import Errors

from usdm4.api.activity import Activity
from usdm4.api.biomedical_concept import BiomedicalConcept
from usdm4.api.biomedical_concept_surrogate import BiomedicalConceptSurrogate
from usdm4.api.code import Code
from usdm4.api.condition import Condition
from usdm4.api.encounter import Encounter
from usdm4.api.extension import ExtensionAttribute
from usdm4.api.extensions_d4k import (
    TLF_EXT_URL,
    TLO_EXT_URL,
    TLP_EXT_URL,
    TLT_EXT_URL,
    TLU_EXT_URL,
)
from usdm4.api.procedure import Procedure
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.scheduled_instance import (
    ConditionAssignment,
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
)
from usdm4.api.study_epoch import StudyEpoch
from usdm4.api.timing import Timing
from usdm4.assembler.encoder import Encoder
from usdm4.assembler.timeline.columns import ParsedTimeline
from usdm4.assembler.timeline.naming import Naming
from usdm4.assembler.timeline.plan import (
    DECISION,
    END,
    FIXED,
    GATE,
    START,
    Planner,
    TimelinePlan,
)
from usdm4.assembler.timeline.values import CycleNumber, CycleRange, Delay
from usdm4.builder.builder import Builder


@dataclass
class SharedState:
    """What every timeline of one assembly shares. Activities are SHARED
    across timelines: an activity named on both the main and a subsidiary
    table is one ``Activity`` referenced by both, keyed by identity."""

    naming: Naming = field(default_factory=Naming)
    activities: list[Activity] = field(default_factory=list)
    activity_by_name: dict[str, Activity] = field(default_factory=dict)
    biomedical_concepts: list[BiomedicalConcept] = field(default_factory=list)
    biomedical_concept_surrogates: list[BiomedicalConceptSurrogate] = field(
        default_factory=list
    )
    # (timeline id, column id) -> the column's Encounter, for copied columns
    # (issue 75). Only timelines with an id register.
    encounter_by_column: dict[tuple[str, str], Encounter] = field(default_factory=dict)


@dataclass
class BuiltTimeline:
    timeline: ScheduleTimeline | None
    epochs: list[StudyEpoch]
    encounters: list[Encounter]
    conditions: list[Condition]


class TimelineBuild:
    """Builds ONE timeline. ``t`` is its ordinal in the input."""

    MODULE = "usdm4.assembler.timeline.build.TimelineBuild"

    # U4-7: the exit condition of a cycle loop. The real rule is usually in
    # the protocol body, not the SoA; fixed text until something reads it.
    EXIT_CONDITION = "cycle exit condition"
    # Issue 84: an open repeat's exit when no bound is printed.
    REPEAT_EXIT_CONDITION = "repeat exit condition"

    # #77. Every timeline is entered on its printed entry condition; with
    # none printed, the default for its type. One entry per ``TimelineType``.
    ENTRY_CONDITIONS = {
        "main": "Subject identified",
        "extension_study": "Entered extension study",
        "continued_access": "Eligible for continued access",
        "follow_up": "Completed or discontinued treatment",
        "arm": "Assigned to arm",
        "cohort": "Assigned to cohort",
        "unscheduled": "Unscheduled visit",
        "early_termination": "Early termination",
        "adverse_event": "Adverse event",
        "profile": "Activity performed",
        "unclassified": "Entry condition not stated",
    }

    # The SoA input's classification and the d4k extension each is emitted
    # as. One concept per URL, matching every other d4k extension. TLF names
    # the family and is emitted for profiles only — its presence is what marks
    # a timeline as a profile to downstream readers. TLT, the type, is
    # emitted on every timeline, last.
    _CLASSIFICATION_EXTENSIONS = (
        ("orientation", TLO_EXT_URL),
        ("unit", TLU_EXT_URL),
        ("placement", TLP_EXT_URL),
    )

    def __init__(
        self,
        builder: Builder,
        errors: Errors,
        encoder: Encoder,
        state: SharedState,
        timeline: ParsedTimeline,
        plan: TimelinePlan,
        t: int,
        is_main: bool,
    ):
        self._builder = builder
        self._errors = errors
        self._encoder = encoder
        self._state = state
        self._naming = state.naming
        self._timeline = timeline
        self._plan = plan
        self._t = t
        self._is_main = is_main
        # Per column index.
        self._epoch_for: dict[int, StudyEpoch] = {}
        self._encounter_for: dict[int, Encounter] = {}
        self._sai_for: dict[int, ScheduledActivityInstance] = {}
        # Per activity row index.
        self._activity_for: dict[int, Activity] = {}
        # Footnote markers are scoped to one timeline.
        self._condition_links: dict[str, dict] = {}

    def build(self) -> BuiltTimeline:
        epochs = self._add_epochs()
        encounters = self._add_encounters()
        self._add_activities()
        instances = self._add_instances()
        timings = self._add_timings()
        self._link_cells()
        conditions = self._add_conditions()
        timeline = self._add_timeline(instances, timings)
        return BuiltTimeline(timeline, epochs, encounters, conditions)

    def _qualify(self, name: str) -> str:
        return self._naming.qualify(name, self._t)

    # ------------------------------------------------------------------
    # Epochs

    def _add_epochs(self) -> list[StudyEpoch]:
        results: list[StudyEpoch] = []
        by_identity: dict[str, StudyEpoch] = {}
        # Issue 64: redacted epochs cannot be told apart by their text, so a
        # consecutive run of redacted columns is one epoch and a redacted run
        # after a non-redacted epoch is a new one.
        redacted_run = 0
        previous_redacted = False
        for column in self._timeline.columns:
            label = column.epoch_label or ""
            redacted = column.is_redacted("epoch")
            # Issue 75: no epoch sent, none linked (U4-6) — a subsidiary
            # timeline rarely links to epochs.
            if not redacted and not label.strip():
                previous_redacted = False
                continue
            # Keyed on the identity, not the raw text: `Screening` and
            # `Screening ` are one epoch stated twice.
            key = self._naming.identity(label)
            if redacted:
                if not previous_redacted:
                    redacted_run += 1
                # A NUL prefix cannot collide with any printed label.
                key = f"\x00redacted:{redacted_run}"
            previous_redacted = redacted
            if key not in by_identity:
                epoch = self._builder.create(
                    StudyEpoch,
                    {
                        "name": self._naming.claim_epoch_name(
                            self._qualify(
                                self._naming.epoch_name(label, column.index + 1)
                            ),
                            # Identity for the name registry: the label, or
                            # for a redacted run the run's own key, so a
                            # second run takes an ordinal (`CCI2`).
                            key if redacted else label,
                        ),
                        "description": None,
                        "label": label,
                        "type": self._builder.klass_and_attribute_value(
                            StudyEpoch, "type", "Treatment Epoch"
                        ),
                    },
                )
                results.append(epoch)
                by_identity[key] = epoch
            self._epoch_for[column.index] = by_identity[key]
        self._errors.info(
            f"Epochs: {len(results)}",
            KlassMethodLocation(self.MODULE, "_add_epochs"),
        )
        return results

    def _epoch_id(self, index: int) -> str | None:
        """The id of the epoch of the column at ``index``; ``None`` when no
        epoch was sent (issue 75)."""
        epoch = self._epoch_for.get(index)
        return epoch.id if epoch else None

    # ------------------------------------------------------------------
    # Encounters

    def _add_encounters(self) -> list[Encounter]:
        results: list[Encounter] = []
        for column in self._timeline.columns:
            # Markers on any header value of the column link to its
            # timepoint, each once (issue 64).
            for marker in column.all_markers:
                self._link(marker, timepoint=column.index)
            # A gate's column is not a visit (R8, U4-10 (a)): no Encounter.
            if Planner.is_gate(column):
                continue
            shared = self._copied_encounter(column)
            if shared is not None:
                # Issue 75: the same visit; not listed again.
                self._encounter_for[column.index] = shared
                continue
            encounter = self._builder.create(
                Encounter,
                {
                    "name": self._qualify(f"E{column.index + 1}"),
                    "description": None,
                    "label": column.visit_label or "",
                    "type": self._builder.klass_and_attribute_value(
                        Encounter, "type", "visit"
                    ),
                    "environmentalSettings": [
                        self._builder.klass_and_attribute_value(
                            Encounter, "environmentalSettings", "clinic"
                        )
                    ],
                    "contactModes": [
                        self._builder.klass_and_attribute_value(
                            Encounter, "contactModes", "In Person"
                        )
                    ],
                    "transitionStartRule": None,
                    "transitionEndRule": None,
                    "scheduledAtId": None,
                },
            )
            results.append(encounter)
            self._encounter_for[column.index] = encounter
            if self._timeline.id is not None:
                self._state.encounter_by_column[(self._timeline.id, column.id)] = (
                    encounter
                )
        self._errors.info(
            f"Encounters: {len(results)}",
            KlassMethodLocation(self.MODULE, "_add_encounters"),
        )
        return results

    def _copied_encounter(self, column) -> Encounter | None:
        """The original's ``Encounter`` for a copied column (issue 75, U4-5),
        else ``None`` and the column builds its own.

        The original's timeline sets the label (U4-30): a copy printing
        different visit text is warned, naming both. A copy whose original was
        not built gets its own ``Encounter``, warned."""
        if column.copy_of is None:
            return None
        location = KlassMethodLocation(self.MODULE, "_add_encounters")
        where = f"Timeline {self._t}, column '{column.id}'"
        timeline_id, column_id = column.copy_of
        encounter = self._state.encounter_by_column.get(column.copy_of)
        if encounter is None:
            self._errors.warning(
                f"{where}: copy of timeline '{timeline_id}' column '{column_id}', "
                f"which was not built; given its own encounter",
                location,
            )
            return None
        text = (column.visit_label or "").strip()
        if text and text != (encounter.label or "").strip():
            self._errors.warning(
                f"{where}: copy prints visit '{text}', the original "
                f"'{encounter.label}'; the original's label kept",
                location,
            )
        return encounter

    # ------------------------------------------------------------------
    # Activities

    def _add_activities(self) -> None:
        created: list[Activity] = []
        rows = self._timeline.activities
        for index, row in enumerate(rows):
            activity = self._get_or_create_activity(row, created, self._own_group(row))
            for marker in row.get("markers") or []:
                self._link(marker, activity=activity.id)
            self._activity_for[index] = activity
        # Parents are named, so link children once every row has its Activity.
        # A child named as its own group is not the group (issue 88), so it
        # never answers for the group's name.
        by_name = {
            row["name"]: self._activity_for[i]
            for i, row in enumerate(rows)
            if not self._own_group(row)
        }
        for index, row in enumerate(rows):
            parent_name = row.get("parent")
            if parent_name is None:
                continue
            parent = by_name[parent_name]
            child = self._activity_for[index]
            if child.id != parent.id and child.id not in parent.childIds:
                parent.childIds.append(child.id)
        self._errors.info(
            f"Activities (timeline {self._t}): +{len(created)} new, "
            f"{len(self._state.activity_by_name)} total",
            KlassMethodLocation(self.MODULE, "_add_activities"),
        )

    def _own_group(self, row: dict) -> bool:
        """The row is a child named as its own group — "Medical History"
        under "Medical History", or a redacted row under a redacted group."""
        parent = row.get("parent")
        return parent is not None and self._naming.identity(
            parent
        ) == self._naming.identity(row["name"])

    def _get_or_create_activity(
        self, row: dict, created: list[Activity], own_group: bool = False
    ) -> Activity:
        """The shared Activity for ``row['name']``, created on first sighting.
        The registry is keyed by identity (trimmed, case-folded), so the same
        label on two timelines gives one Activity referenced by both. A child
        named as its own group is a separate Activity (issue 88): keyed apart
        from the group, named apart, the same label, and warned."""
        key = self._naming.identity(row["name"])
        if own_group:
            key = f"{key}\x00in\x00{key}"
        existing = self._state.activity_by_name.get(key)
        if existing is not None:
            return existing
        if own_group:
            self._errors.warning(
                f"Timeline {self._t}: activity '{row['name']}' is a child of a "
                "group with the same name; kept as a separate activity",
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
        bc_ids, sbc_ids, procedures = self._biomedical_concepts(row)
        seq = len(self._state.activity_by_name) + 1
        activity: Activity = self._builder.create(
            Activity,
            {
                "name": self._naming.activity_name(
                    row["name"], seq, identity=key if own_group else None
                ),
                "description": None,
                "label": (row["name"] or "").strip() or None,
                "definedProcedures": procedures,
                "biomedicalConceptIds": bc_ids,
                "bcCategoryIds": [],
                "bcSurrogateIds": sbc_ids,
                "timelineId": None,
            },
        )
        self._state.activity_by_name[key] = activity
        self._state.activities.append(activity)
        created.append(activity)
        return activity

    def _biomedical_concepts(
        self, row: dict
    ) -> tuple[list[str], list[str], list[Procedure]]:
        bc_ids: list[str] = []
        sbc_ids: list[str] = []
        procedures: list[Procedure] = []
        for bc_name in row.get("bcs") or []:
            if self._builder.cdisc_bc_library.exists(bc_name):
                bc: BiomedicalConcept = self._builder.bc(bc_name)
                if bc:
                    self._state.biomedical_concepts.append(bc)
                    bc_ids.append(bc.id)
                else:
                    self._errors.warning(f"Failed to create BC with name '{bc_name}'")
            else:
                sbc: BiomedicalConceptSurrogate = self._builder.create(
                    BiomedicalConceptSurrogate,
                    {
                        "name": bc_name,
                        "description": bc_name,
                        "label": bc_name,
                        "reference": "None set",
                    },
                )
                if sbc:
                    self._state.biomedical_concept_surrogates.append(sbc)
                    sbc_ids.append(sbc.id)
                else:
                    self._errors.warning(
                        f"Failed to create surrogate BC with name '{bc_name}'"
                    )
            # Placeholder code — noted in the design, § 8; out of scope here.
            procedure = self._builder.create(
                Procedure,
                {
                    "name": bc_name,
                    "description": bc_name,
                    "label": bc_name,
                    "procedureType": row["name"],
                    "code": self._builder.create(
                        Code,
                        {
                            "code": "12345",
                            "codeSystem": "LOINC",
                            "codeSystemVersion": "1",
                            "decode": bc_name,
                        },
                    ),
                    "reference": "Not applicable",
                },
            )
            if procedure:
                procedures.append(procedure)
            else:
                self._errors.warning(
                    f"Failed to create procedure with name '{bc_name}'"
                )
        return bc_ids, sbc_ids, procedures

    # ------------------------------------------------------------------
    # Scheduled activity instances — a straight chain

    def _add_instances(
        self,
    ) -> list[ScheduledActivityInstance | ScheduledDecisionInstance]:
        results: list[ScheduledActivityInstance | ScheduledDecisionInstance] = []
        for node in self._plan.nodes:
            if node.column is None:
                if node.kind == DECISION:
                    sai = self._add_decision(node)
                elif node.kind == END:
                    sai = self._add_end(node)
                elif node.kind == START:
                    sai = self._add_start(node)
                else:
                    sai = self._add_start_marker(node)
                self._sai_for[node.key] = sai
                results.append(sai)
                continue
            column = node.column
            if node.kind == GATE:
                sai = self._add_gate(node)
                self._sai_for[column.index] = sai
                results.append(sai)
                continue
            encounter = self._encounter_for.get(column.index)
            sai = self._builder.create(
                ScheduledActivityInstance,
                {
                    # A redacted value names nothing: every instance would
                    # be `CCI`, `CCI-2` … (issue 64). Skip to the next
                    # source, else the positional fallback.
                    "name": self._naming.sai_name(
                        None if column.is_redacted("timing") else column.timing_label,
                        column.timing.value if column.timing else None,
                        column.timing.unit if column.timing else None,
                        None if column.is_redacted("visit") else column.visit_label,
                        self._t,
                        column.index,
                        cycle=self._cycle_number(column),
                    ),
                    "description": None,
                    "label": column.timing_label or "",
                    "timelineExitId": None,
                    "encounterId": encounter.id if encounter else None,
                    "defaultConditionId": None,
                    "epochId": self._epoch_id(column.index),
                    "activityIds": [],
                },
            )
            self._sai_for[column.index] = sai
            results.append(sai)
        self._errors.info(
            f"SAI: {len(results)}",
            KlassMethodLocation(self.MODULE, "_add_instances"),
        )
        for index, sai in enumerate(results[:-1]):
            sai.defaultConditionId = results[index + 1].id
        self._wire_decisions(results)
        return results

    def _wire_decisions(
        self, results: list[ScheduledActivityInstance | ScheduledDecisionInstance]
    ) -> None:
        """R5: a decision's default loops back to its range's ``Day 1``; its
        one condition leads on to the next instance (U4-7)."""
        for index, node in enumerate(self._plan.nodes):
            if node.kind != DECISION:
                continue
            decision = results[index]
            onward = results[index + 1]
            decision.defaultConditionId = self._sai_for[node.loop_to].id
            if node.gate is not None:
                condition = self.gate_condition(self._gate_delay(node))
            elif node.repeat is not None:
                condition = self._repeat_condition(node)
            else:
                condition = self.EXIT_CONDITION
            assignment = self._builder.create(
                ConditionAssignment,
                {"condition": condition, "conditionTargetId": onward.id},
            )
            decision.conditionAssignments = [assignment] if assignment else []

    @staticmethod
    def gate_condition(delay: Delay) -> str:
        """U4-10 (b), (c): a gate's exit condition, filled from its delay —
        ``≥ 7 days and washed out, or 28 days``; with no maximum, no
        ``, or …``."""
        unit = f"{delay.unit}s"
        text = f"≥ {delay.min} {unit} and washed out"
        if delay.max is not None:
            text += f", or {delay.max} {unit}"
        return text

    def _repeat_condition(self, node) -> str:
        """Issue 84: an open repeat exits on its printed bound, else the fixed
        text."""
        repeat = self._timeline.columns[node.epoch_column].repeat
        return repeat.end or self.REPEAT_EXIT_CONDITION

    def _gate_delay(self, node) -> Delay:
        return self._timeline.columns[node.epoch_column].delay

    def _add_gate(self, node) -> ScheduledActivityInstance:
        """A gate's column (R8, U4-10 (a)): the instance the gate's decision
        loops back to. Not a visit — no encounter; labelled with the delay as
        printed. Activities with a cell in the column attach as for any
        column."""
        column = node.column
        return self._builder.create(
            ScheduledActivityInstance,
            {
                "name": self._naming.gate_name(node.gate),
                "description": f"Gate {node.gate}: {column.delay_label}",
                "label": column.delay_label or "",
                "timelineExitId": None,
                "encounterId": None,
                "defaultConditionId": None,
                "epochId": self._epoch_id(column.index),
                "activityIds": [],
            },
        )

    def _add_decision(self, node) -> ScheduledDecisionInstance:
        """A cycle range's decision (R5) or a gate's (R8): after the range's
        last column or the gate's column, in its epoch. Wired once every
        instance exists."""
        if node.gate is not None:
            name = self._naming.gate_name(node.gate, "DEC")
            description = f"End of gate {node.gate}"
        elif node.repeat is not None:
            name = self._naming.repeat_name(node.repeat, "DEC")
            description = f"End of a pass of repeat {node.repeat}"
        else:
            name = self._naming.decision_name(self._cycle_label(node), self._t)
            description = f"End of a pass of cycle {self._cycle_label(node)}"
        return self._builder.create(
            ScheduledDecisionInstance,
            {
                "name": name,
                "description": description,
                "label": "",
                "defaultConditionId": None,
                "epochId": self._epoch_id(node.epoch_column),
                "conditionAssignments": [],
            },
        )

    def _add_start(self, node) -> ScheduledActivityInstance:
        """The timeline's start (issue 92), when its first column is a delay
        from it. Not a visit — no encounter, no activities."""
        return self._builder.create(
            ScheduledActivityInstance,
            {
                "name": self._naming.start_name(self._t),
                "description": "Start of the timeline; its first visit is a "
                "delay from it",
                "label": "",
                "timelineExitId": None,
                "encounterId": None,
                "defaultConditionId": None,
                "epochId": self._epoch_id(node.epoch_column),
                "activityIds": [],
            },
        )

    def _add_end(self, node) -> ScheduledActivityInstance:
        """The instance after a range or a gate that is the last column (R5,
        R8): a decision cannot target the timeline exit, so this carries it.
        Not a visit — no encounter, no activities."""
        if node.gate is not None:
            name = self._naming.gate_name(node.gate, "END")
            description = f"End of gate {node.gate}"
        elif node.repeat is not None:
            name = self._naming.repeat_name(node.repeat, "END")
            description = f"End of repeat {node.repeat}"
        else:
            name = self._naming.end_name(self._t)
            description = f"End of cycle {self._cycle_label(node)}"
        return self._builder.create(
            ScheduledActivityInstance,
            {
                "name": name,
                "description": description,
                "label": "",
                "timelineExitId": None,
                "encounterId": None,
                "defaultConditionId": None,
                "epochId": self._epoch_id(node.epoch_column),
                "activityIds": [],
            },
        )

    def _cycle_label(self, node) -> str:
        """The range a decision or end node closes, as ``3+`` or ``2-3``."""
        return self._cycle_number(self._timeline.columns[node.epoch_column])

    def _add_start_marker(self, node) -> ScheduledActivityInstance:
        """A cycle's start marker (issue 67): the cycle's ``Day 1`` when the
        schedule prints none. Not a visit — no encounter, no activities — in
        the epoch of the cycle's first column."""
        return self._builder.create(
            ScheduledActivityInstance,
            {
                "name": self._naming.sai_name(
                    None,
                    1,
                    "day",
                    None,
                    self._t,
                    node.epoch_column,
                    cycle=self._cycle_label(node) or node.cycle,
                ),
                "description": f"Start of cycle {node.cycle}; no Day 1 column "
                "is printed",
                "label": "",
                "timelineExitId": None,
                "encounterId": None,
                "defaultConditionId": None,
                "epochId": self._epoch_id(node.epoch_column),
                "activityIds": [],
            },
        )

    @staticmethod
    def _cycle_number(column) -> int | str | None:
        """The cycle of a cycle column the plan timed — ``2`` (issue 66), or
        for a range ``3+`` / ``2-3`` (issue 69) — else ``None``: an untimed
        column is named from its text."""
        if column.timing is None:
            return None
        if isinstance(column.cycle, CycleNumber):
            return column.cycle.n
        if isinstance(column.cycle, CycleRange):
            cycle = column.cycle
            return (
                f"{cycle.start}+" if cycle.end is None else f"{cycle.start}-{cycle.end}"
            )
        return None

    # ------------------------------------------------------------------
    # Timings — one per instance (issue 65), as the plan places them

    def _add_timings(self) -> list[Timing]:
        results: list[Timing] = []
        for node in self._plan.nodes:
            column = node.column
            this_sai = self._sai_for[node.key]
            to_sai = self._sai_for[node.relative_to]
            window_label, window_lower, window_upper = self._window(node)
            label = (column.timing_label or "") if column else ""
            name = f"TIM{column.index + 1}" if column else f"TIM{node.marker}"
            timing = self._builder.create(
                Timing,
                {
                    "type": self._builder.klass_and_attribute_value(
                        Timing, "type", node.timing_type
                    ),
                    "value": self._encoder.iso8601_duration(node.duration, node.unit),
                    "valueLabel": self._value_label(column),
                    "name": self._qualify(name),
                    "description": None,
                    "label": label,
                    "relativeToFrom": self._builder.klass_and_attribute_value(
                        Timing, "relativeToFrom", "start to start"
                    ),
                    "windowLabel": window_label,
                    "windowLower": window_lower,
                    "windowUpper": window_upper,
                    "relativeFromScheduledInstanceId": this_sai.id,
                    "relativeToScheduledInstanceId": to_sai.id,
                },
            )
            if timing:
                results.append(timing)
        self._errors.info(
            f"Timing: {len(results)}",
            KlassMethodLocation(self.MODULE, "_add_timings"),
        )
        return results

    @staticmethod
    def _value_label(column) -> str:
        """The printed timing text, or ``""``. A time range is labelled with
        its decoded start (``Day -28``) — U4-21; its printed text stays on
        ``label``. A start marker (no column) has none."""
        if column is None:
            return ""
        if column.time_range is not None:
            return f"{column.time_range.unit.capitalize()} {column.time_range.start}"
        return column.timing_label or ""

    def _window(self, node) -> tuple[str | None, str, str]:
        """The timing's window as (label, lower, upper) — all set or none
        (DDF00006). A zero bound is the zero duration, never "". An anchor
        (Fixed Reference) timing has no window (DDF00025): its column's
        printed window is logged at info level and not used. A printed
        window with no bounds (unread or redacted) gives no window and is
        logged as a warning."""
        column, window = node.column, node.window
        location = KlassMethodLocation(self.MODULE, "_window")
        printed = column.window_label if column else None
        zero = window is not None and window.lower == 0 and window.upper == 0
        if node.timing_type == FIXED:
            if zero:
                return "", "", ""
            if window is not None or printed:
                self._errors.info(
                    f"Anchor timing for column '{self._column_text(column)}': "
                    f"its printed window '{printed or ''}' is not used",
                    location,
                )
            return None, "", ""
        if window is None:
            if printed:
                self._errors.warning(
                    f"Column '{self._column_text(column)}': window '{printed}' "
                    "has no bounds; no window written",
                    location,
                )
            return None, "", ""
        if zero:
            return "", "", ""
        return (
            self._window_label(node),
            self._encoder.iso8601_duration(window.lower, window.unit),
            self._encoder.iso8601_duration(window.upper, window.unit),
        )

    @staticmethod
    def _column_text(column) -> str:
        return (column.timing_label or column.visit_label or "") if column else ""

    @staticmethod
    def _window_label(node) -> str | None:
        """The window as printed. A window with no printed text of its own —
        a time range's span (U4-21) — is labelled in rendered form
        (``-0..+27 days``). A zero window from the
        window field is ``""``. With no window, the printed window text if
        any (unread or redacted), else None."""
        column, window = node.column, node.window
        if column is None:
            return None
        if window is None:
            return column.window_label or None
        if node.window_from == "range":
            return f"-{window.lower}..+{window.upper} {window.unit}s"
        if window.lower == 0 and window.upper == 0:
            return ""
        return column.window_label

    # ------------------------------------------------------------------
    # Cells

    def _link_cells(self) -> None:
        """Attach each activity to the instances of the columns it has a cell
        in, and link the cell's footnote markers."""
        index_of = self._timeline.column_index
        for row_index, row in enumerate(self._timeline.activities):
            activity = self._activity_for[row_index]
            for cell in row.get("cells") or []:
                column_index = index_of[cell["column"]]
                self._sai_for[column_index].activityIds.append(activity.id)
                for marker in cell.get("markers") or []:
                    self._link(marker, timepoint=column_index, activity=activity.id)

    # ------------------------------------------------------------------
    # Conditions

    def _link(
        self, marker: str, timepoint: int | None = None, activity: str | None = None
    ) -> None:
        links = self._condition_links.setdefault(
            marker, {"reference": marker, "timepoint_index": [], "activity_id": []}
        )
        # Each instance and each activity once, however many places print the
        # marker (issue 94).
        if activity is not None and activity not in links["activity_id"]:
            links["activity_id"].append(activity)
        if timepoint is not None and timepoint not in links["timepoint_index"]:
            links["timepoint_index"].append(timepoint)

    def _add_conditions(self) -> list[Condition]:
        """Every footnote with a marker becomes a ``Condition``, with
        ``contextIds`` / ``appliesToIds`` from where its marker is found on
        a column, an activity or a cell of this timeline. A footnote whose
        marker nothing uses is kept with both lists empty (issue 94), so the
        legend survives whole. A footnote with no marker is skipped and
        counted; a marker used with no footnote is warned."""
        results: list[Condition] = []
        counts = {
            "in": 0,
            "referenced": 0,
            "aligned": 0,
            "unused": 0,
            "dropped_no_ref": 0,
        }
        location = KlassMethodLocation(self.MODULE, "_add_conditions")
        footnotes = self._timeline.footnotes
        counts["in"] = len(footnotes)
        legend: set[str] = set()
        for index, item in enumerate(footnotes):
            ref = item.get("marker")
            if not ref:
                counts["dropped_no_ref"] += 1
                self._errors.warning(
                    f"Condition has no reference, not created: {item}",
                    location,
                )
                continue
            counts["referenced"] += 1
            legend.add(ref)
            links = self._condition_links.get(ref)
            if links is None:
                counts["unused"] += 1
                self._errors.warning(
                    f"Footnote '{ref}' is used on no column, activity or cell; "
                    f"created with no context: {item}",
                    location,
                )
                timepoint_ids, activity_ids = [], []
            else:
                timepoint_ids = [
                    self._sai_for[x].id for x in links["timepoint_index"]
                ]
                activity_ids = list(links["activity_id"])
            condition = self._builder.create(
                Condition,
                {
                    "name": self._qualify(f"COND{index + 1}"),
                    # The printed marker is what a reviewer matches against
                    # the footnote legend by eye.
                    "label": str(ref).strip() or None,
                    "description": None,
                    "text": item["text"],
                    "dictionaryId": None,
                    "contextIds": timepoint_ids if timepoint_ids else activity_ids,
                    "appliesToIds": activity_ids if timepoint_ids else [],
                },
            )
            if condition:
                counts["aligned"] += 1
                results.append(condition)
        for ref, links in self._condition_links.items():
            if ref not in legend:
                self._errors.warning(
                    f"Marker '{ref}' is used on {self._where(links)} but has no "
                    f"footnote in the legend",
                    location,
                )
        self._errors.info(
            f"Conditions T{self._t}: in={counts['in']}, "
            f"referenced={counts['referenced']}, "
            f"aligned={counts['aligned']}, "
            f"unused={counts['unused']}, "
            f"dropped_no_ref={counts['dropped_no_ref']}",
            location,
        )
        return results

    def _where(self, links: dict) -> str:
        """Where a marker is printed, for a warning: the columns by id and
        the activities as printed."""
        ids = {c.index: c.id for c in self._timeline.columns}
        names = {a.id: a.label or a.name for a in self._activity_for.values()}
        parts = [f"column '{ids.get(x, x)}'" for x in links["timepoint_index"]]
        parts += [f"activity '{names.get(a, a)}'" for a in links["activity_id"]]
        return ", ".join(parts) or "nothing"

    # ------------------------------------------------------------------
    # The timeline

    def _add_timeline(
        self, instances: list[ScheduledActivityInstance], timings: list[Timing]
    ) -> ScheduleTimeline | None:
        exit = self._builder.create(ScheduleTimelineExit, {})
        last = instances[-1]
        last.timelineExitId = exit.id
        last.defaultConditionId = None
        title = self._timeline.title or (
            "Main timeline" if self._is_main else f"Timeline {self._t}"
        )
        description = self._timeline.description or (
            "The main timeline" if self._is_main else f"Subsidiary timeline {self._t}"
        )
        return self._builder.create(
            ScheduleTimeline,
            {
                "mainTimeline": self._is_main,
                "name": f"TIMELINE-{self._t}",
                "description": description,
                "label": title,
                "entryCondition": self._entry_condition(),
                "entryId": instances[0].id,
                "exits": [exit],
                "plannedDuration": None,
                "instances": instances,
                "timings": timings,
                "extensionAttributes": self._extensions(),
            },
        )

    def _entry_condition(self) -> str:
        """#77. A timeline of any type is entered on its printed
        ``entry_condition``; with none printed, the default for its type. The
        default is warned, except for ``main``, which almost never prints
        one."""
        text = (self._timeline.entry_condition or "").strip()
        if text:
            return text
        default = self.ENTRY_CONDITIONS[self._timeline.type]
        if self._timeline.type == "main":
            return default
        self._errors.warning(
            f"Timeline {self._t} ({self._timeline.type}) has no entry condition; "
            f"'{default}' used",
            KlassMethodLocation(self.MODULE, "_entry_condition"),
        )
        return default

    def _extensions(self) -> list[ExtensionAttribute]:
        extensions: list[ExtensionAttribute] = []
        values: list[tuple[str, str]] = []
        if self._timeline.family == "profile":
            values.append((TLF_EXT_URL, "profile"))
        for key, url in self._CLASSIFICATION_EXTENSIONS:
            value = self._timeline.classification.get(key)
            if value not in (None, ""):
                values.append((url, str(value)))
        values.append((TLT_EXT_URL, self._timeline.type))
        for url, value in values:
            extensions.append(
                self._builder.create(
                    ExtensionAttribute, {"url": url, "valueString": value}
                )
            )
        return extensions
