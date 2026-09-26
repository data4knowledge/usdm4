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
    TLU_EXT_URL,
)
from usdm4.api.procedure import Procedure
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.scheduled_instance import ScheduledActivityInstance
from usdm4.api.study_epoch import StudyEpoch
from usdm4.api.timing import Timing
from usdm4.assembler.encoder import Encoder
from usdm4.assembler.timeline.columns import ParsedTimeline
from usdm4.assembler.timeline.grammar import CycleNumber
from usdm4.assembler.timeline.naming import Naming
from usdm4.assembler.timeline.plan import TimelinePlan
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


@dataclass
class BuiltTimeline:
    timeline: ScheduleTimeline | None
    epochs: list[StudyEpoch]
    encounters: list[Encounter]
    conditions: list[Condition]


class TimelineBuild:
    """Builds ONE timeline. ``t`` is its ordinal in the input."""

    MODULE = "usdm4.assembler.timeline.build.TimelineBuild"

    # The SoA input's classification and the d4k extension each is emitted
    # as. One concept per URL, matching every other d4k extension. TLF names
    # the family and is emitted for profiles only — its presence is what marks
    # a timeline as a profile to downstream readers.
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
            # Keyed on the identity, not the raw text: `Screening` and
            # `Screening ` are one epoch stated twice.
            key = self._naming.identity(label)
            redacted = column.is_redacted("epoch")
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

    # ------------------------------------------------------------------
    # Encounters

    def _add_encounters(self) -> list[Encounter]:
        results: list[Encounter] = []
        for column in self._timeline.columns:
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
            # Markers on any header value of the column link to its
            # timepoint, each once (issue 64).
            for marker in column.all_markers:
                self._link(marker, timepoint=column.index)
        self._errors.info(
            f"Encounters: {len(results)}",
            KlassMethodLocation(self.MODULE, "_add_encounters"),
        )
        return results

    # ------------------------------------------------------------------
    # Activities

    def _add_activities(self) -> None:
        created: list[Activity] = []
        rows = self._timeline.activities
        for index, row in enumerate(rows):
            activity = self._get_or_create_activity(row, created)
            for marker in row.get("markers") or []:
                self._link(marker, activity=activity.id)
            self._activity_for[index] = activity
        # Parents are named, so link children once every row has its Activity.
        by_name = {row["name"]: self._activity_for[i] for i, row in enumerate(rows)}
        for index, row in enumerate(rows):
            parent_name = row.get("parent")
            if parent_name is None:
                continue
            parent = by_name[parent_name]
            child = self._activity_for[index]
            if child.id not in parent.childIds:
                parent.childIds.append(child.id)
        self._errors.info(
            f"Activities (timeline {self._t}): +{len(created)} new, "
            f"{len(self._state.activity_by_name)} total",
            KlassMethodLocation(self.MODULE, "_add_activities"),
        )

    def _get_or_create_activity(self, row: dict, created: list[Activity]) -> Activity:
        """The shared Activity for ``row['name']``, created on first sighting.
        The registry is keyed by identity (trimmed, case-folded), so the same
        label on two timelines gives one Activity referenced by both."""
        key = self._naming.identity(row["name"])
        existing = self._state.activity_by_name.get(key)
        if existing is not None:
            return existing
        bc_ids, sbc_ids, procedures = self._biomedical_concepts(row)
        seq = len(self._state.activity_by_name) + 1
        activity: Activity = self._builder.create(
            Activity,
            {
                "name": self._naming.activity_name(row["name"], seq),
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

    def _add_instances(self) -> list[ScheduledActivityInstance]:
        results: list[ScheduledActivityInstance] = []
        for node in self._plan.nodes:
            if node.column is None:
                sai = self._add_start_marker(node)
                self._sai_for[node.key] = sai
                results.append(sai)
                continue
            column = node.column
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
                    "epochId": self._epoch_for[column.index].id,
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
        return results

    def _add_start_marker(self, node) -> ScheduledActivityInstance:
        """A cycle's start marker (issue 67): the cycle's ``Day 1`` when the
        schedule prints none. Not a visit — no encounter, no activities — in
        the epoch of the cycle's first column."""
        return self._builder.create(
            ScheduledActivityInstance,
            {
                "name": self._naming.sai_name(
                    None, 1, "day", None, self._t, node.epoch_column, cycle=node.cycle
                ),
                "description": f"Start of cycle {node.cycle}; no Day 1 column "
                "is printed",
                "label": "",
                "timelineExitId": None,
                "encounterId": None,
                "defaultConditionId": None,
                "epochId": self._epoch_for[node.epoch_column].id,
                "activityIds": [],
            },
        )

    @staticmethod
    def _cycle_number(column) -> int | None:
        """The cycle number of a single-cycle column the plan timed (issue
        66), else ``None``: a range or an untimed column is named from its
        text."""
        if isinstance(column.cycle, CycleNumber) and column.timing is not None:
            return column.cycle.n
        return None

    # ------------------------------------------------------------------
    # Timings — one per instance (issue 65), as the plan places them

    def _add_timings(self) -> list[Timing]:
        results: list[Timing] = []
        for node in self._plan.nodes:
            column = node.column
            this_sai = self._sai_for[node.key]
            to_sai = self._sai_for[node.relative_to]
            window = node.window
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
                    "windowLabel": self._window_label(node),
                    "windowLower": self._encoder.iso8601_duration(
                        window.lower, window.unit
                    )
                    if window and window.lower
                    else "",
                    "windowUpper": self._encoder.iso8601_duration(
                        window.upper, window.unit
                    )
                    if window and window.upper
                    else "",
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

    @staticmethod
    def _window_label(node) -> str | None:
        """The window as printed. A window with no printed text of its own —
        decoded from a time range (U4-21) or printed inside the timing cell —
        is labelled in pattern form (``-0..+27 days``). A zero window from the
        window field is ``""``. With no window, the printed window text if
        any (unread or redacted), else None."""
        column, window = node.column, node.window
        if column is None:
            return None
        if window is None:
            return column.window_label or None
        if node.window_from in ("range", "timing"):
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
        if activity is not None:
            links["activity_id"].append(activity)
        if timepoint is not None:
            links["timepoint_index"].append(timepoint)

    def _add_conditions(self) -> list[Condition]:
        """A footnote becomes a ``Condition`` only when its marker is found on
        a column, an activity or a cell of this timeline. An unanchored
        footnote is skipped, not created, and counted: a condition with no
        ``appliesTo`` breaks the Excel round trip downstream."""
        results: list[Condition] = []
        counts = {
            "in": 0,
            "referenced": 0,
            "aligned": 0,
            "dropped_no_ref": 0,
            "dropped_no_match": 0,
        }
        footnotes = self._timeline.footnotes
        counts["in"] = len(footnotes)
        for index, item in enumerate(footnotes):
            ref = item.get("marker")
            if not ref:
                counts["dropped_no_ref"] += 1
                self._errors.warning(
                    f"Condition has no reference, not created: {item}",
                    KlassMethodLocation(self.MODULE, "_add_conditions"),
                )
                continue
            counts["referenced"] += 1
            if ref not in self._condition_links:
                counts["dropped_no_match"] += 1
                self._errors.warning(
                    f"Failed to align condition {item}, not created.",
                    KlassMethodLocation(self.MODULE, "_add_conditions"),
                )
                continue
            links = self._condition_links[ref]
            timepoint_ids = [self._sai_for[x].id for x in links["timepoint_index"]]
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
        self._errors.info(
            f"Conditions T{self._t}: in={counts['in']}, "
            f"referenced={counts['referenced']}, "
            f"aligned={counts['aligned']}, "
            f"dropped_no_ref={counts['dropped_no_ref']}, "
            f"dropped_no_match={counts['dropped_no_match']}",
            KlassMethodLocation(self.MODULE, "_add_conditions"),
        )
        return results

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
                # Hard-coded, typo included — design § 8, out of scope here.
                "entryCondition": "Paricipant identified",
                "entryId": instances[0].id,
                "exits": [exit],
                "plannedDuration": None,
                "instances": instances,
                "timings": timings,
                "extensionAttributes": self._extensions(),
            },
        )

    def _extensions(self) -> list[ExtensionAttribute]:
        extensions: list[ExtensionAttribute] = []
        values: list[tuple[str, str]] = []
        if self._timeline.family == "profile":
            values.append((TLF_EXT_URL, "profile"))
        for key, url in self._CLASSIFICATION_EXTENSIONS:
            value = self._timeline.classification.get(key)
            if value not in (None, ""):
                values.append((url, str(value)))
        for url, value in values:
            extensions.append(
                self._builder.create(
                    ExtensionAttribute, {"url": url, "valueString": value}
                )
            )
        return extensions
