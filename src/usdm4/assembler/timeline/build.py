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
        for column in self._timeline.columns:
            label = column.epoch_label or ""
            # Keyed on the identity, not the raw text: `Screening` and
            # `Screening ` are one epoch stated twice.
            key = self._naming.identity(label)
            if key not in by_identity:
                epoch = self._builder.create(
                    StudyEpoch,
                    {
                        "name": self._naming.claim_epoch_name(
                            self._qualify(
                                self._naming.epoch_name(label, column.index + 1)
                            ),
                            label,
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
            for marker in column.visit_markers:
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
            column = node.column
            encounter = self._encounter_for.get(column.index)
            sai = self._builder.create(
                ScheduledActivityInstance,
                {
                    "name": self._naming.sai_name(
                        column.timing_label,
                        column.timing.value if column.timing else None,
                        column.timing.unit if column.timing else None,
                        column.visit_label,
                        self._t,
                        column.index,
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

    # ------------------------------------------------------------------
    # Timings — every node from the plan's one anchor

    def _add_timings(self) -> list[Timing]:
        results: list[Timing] = []
        for node in self._plan.nodes:
            column = node.column
            this_sai = self._sai_for[column.index]
            to_sai = self._sai_for[node.relative_to]
            window = column.window
            label = column.timing_label or None
            timing = self._builder.create(
                Timing,
                {
                    "type": self._builder.klass_and_attribute_value(
                        Timing, "type", node.timing_type
                    ),
                    "value": self._encoder.iso8601_duration(node.duration, node.unit),
                    "valueLabel": label,
                    "name": self._qualify(f"TIM{column.index + 1}"),
                    "description": None,
                    "label": label,
                    "relativeToFrom": self._builder.klass_and_attribute_value(
                        Timing, "relativeToFrom", "start to start"
                    ),
                    "windowLabel": self._window_label(column),
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
    def _window_label(column) -> str | None:
        """The window as printed, `""` for a zero window, None where there is
        no window. House style: a label carries the protocol's words or it is
        absent."""
        if column.window is None:
            return None
        if column.window.lower == 0 and column.window.upper == 0:
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
