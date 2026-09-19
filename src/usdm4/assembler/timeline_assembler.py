import re
from pathlib import Path

from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.assembler.encoder import Encoder
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.api.scheduled_instance import ScheduledInstance, ScheduledActivityInstance
from usdm4.api.activity import Activity
from usdm4.api.study_epoch import StudyEpoch
from usdm4.api.encounter import Encounter
from usdm4.api.timing import Timing
from usdm4.api.condition import Condition
from usdm4.api.biomedical_concept import BiomedicalConcept
from usdm4.api.biomedical_concept_surrogate import BiomedicalConceptSurrogate
from usdm4.api.procedure import Procedure
from usdm4.api.code import Code
from usdm4.api.extension import ExtensionAttribute
from usdm4.api.extensions_d4k import (
    TLF_EXT_URL,
    TLO_EXT_URL,
    TLP_EXT_URL,
    TLU_EXT_URL,
)


class TimelineAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.timeline_assembler.TimelineAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._timelines: list[ScheduleTimeline] = []
        self._epochs: list[StudyEpoch] = []
        self._encounters: list[Encounter] = []
        self._activities: list[Activity] = []
        # Activities are SHARED across timelines: an activity named on both the
        # main and a subsidiary SoA table is one Activity object referenced by
        # both. Registry keyed by normalised label. Epochs, encounters, SAIs,
        # timings, conditions and the timeline itself are per-timeline
        # namespaced (T{t}-...) — see the individual add methods.
        self._activity_by_name: dict[str, Activity] = {}
        # SAI names are derived from timepoint/visit text (D1, W12, SCREENING)
        # so the timing sheet's from/to references are human-readable. The
        # registry keeps them unique across every timeline in the study.
        self._sai_name_registry: dict[str, int] = {}
        self._activity_name_registry: dict[str, str] = {}
        self._multi_timeline: bool = False
        self._condition_links: dict = {}
        self._conditions: list[Condition] = []
        self._biomedical_concepts: list[BiomedicalConcept] = []
        self._biomedical_concept_surrogates: list[BiomedicalConceptSurrogate] = []
        # self._procedures: list[Procedure] = []

    def execute(self, data) -> None:
        """Assemble one or more timelines.

        ``data`` may be a single SoA table dict (one timeline, the historical
        case) or a list of SoA table dicts (a main plus n subsidiary timelines).
        Exactly one timeline is flagged ``mainTimeline``: the first table whose
        ``table_type`` is ``main_soa`` (or the first table if none say so).

        A table with no timepoints is skipped before anything is built from it.
        The timepoints list is the spine — epochs and encounters are attached to
        it by positional index — so such a table can yield no
        ScheduledActivityInstance and therefore no ScheduleTimeline. Building it
        anyway registered its activities first and then failed, leaving them in
        the study design referenced by nothing, and if the table was the one
        ``_main_index`` had chosen, no timeline carried ``mainTimeline`` at all.
        The main timeline is therefore chosen from the tables that remain.

        Ordinals are the table's own position, so a skipped table leaves a gap
        (``TIMELINE-1``, ``TIMELINE-3``) rather than renaming the timelines that
        did assemble.
        """
        try:
            tables = self._normalise(data)
            keep = self._assemblable(tables)
            main_ordinal = self._main_ordinal(tables, keep)
            # House style: names are bare within a single-timeline study and
            # carry a `T{t}-` prefix only where more than one timeline is
            # built, so the common case stays short and a multi-timeline study
            # still has unique, traceable identifiers.
            self._multi_timeline = len(keep) > 1
            for index in keep:
                self._execute_one(
                    tables[index], index + 1, is_main=(index == main_ordinal)
                )
            # Single global ordering pass across every timeline's activities so
            # previousId/nextId are consistent (and shared activities are linked
            # once, not re-linked per table).
            self._builder.double_link(self._activities, "previousId", "nextId")
        except Exception as e:
            self._errors.exception(
                "Failed during creation of study design",
                e,
                KlassMethodLocation(self.MODULE, "execute"),
            )

    @staticmethod
    def _normalise(data) -> list[dict]:
        # A dict — even an empty one — is a single (possibly malformed) table;
        # only ``None`` or an empty list means "no timelines". This keeps the
        # historical behaviour where ``execute({})`` surfaces errors rather than
        # silently doing nothing.
        if data is None:
            return []
        return [data] if isinstance(data, dict) else list(data)

    @staticmethod
    def _has_spine(table) -> bool:
        """Does this table carry the timepoints every other list is indexed against?"""
        if not isinstance(table, dict):
            return False
        return bool((table.get("timepoints") or {}).get("items"))

    def _assemblable(self, tables: list[dict]) -> list[int]:
        """Indices of the tables a timeline can be built from, in order.

        Every rejection is reported once, with the table's ordinal and the
        number of activities discarded with it — the loss is otherwise invisible
        in the output, which is what made it hard to see.
        """
        keep: list[int] = []
        for index, table in enumerate(tables):
            if self._has_spine(table):
                keep.append(index)
                continue
            activities = []
            if isinstance(table, dict):
                activities = (table.get("activities") or {}).get("items") or []
            self._errors.error(
                f"Timeline {index + 1} has no timepoints, not created "
                f"({len(activities)} activities discarded with it)",
                KlassMethodLocation(self.MODULE, "_assemblable"),
            )
        return keep

    def _main_ordinal(self, tables: list[dict], keep: list[int]) -> int | None:
        """The index, within *tables*, of the table that carries ``mainTimeline``.

        Chosen over the assemblable tables only, so a skipped table cannot take
        the flag with it. ``None`` when nothing is assemblable.
        """
        if not keep:
            return None
        return keep[self._main_index([tables[index] for index in keep])]

    @staticmethod
    def _main_index(tables: list[dict]) -> int:
        for index, table in enumerate(tables):
            if (table.get("table_type") or "main_soa") == "main_soa":
                return index
        return 0

    def _execute_one(self, data: dict, t: int, is_main: bool) -> None:
        try:
            # Footnote references (e.g. "a", "b") are scoped to a single table,
            # so reset the link map per timeline to avoid cross-table collisions.
            self._condition_links = {}
            self._epochs += self._add_epochs(data, t)
            self._encounters += self._add_encounters(data, t)
            self._add_activities(data, t)
            timepoints = self._add_timepoints(data, t)
            timings = self._add_timing(data, t)
            self._link_timepoints_and_activities(data)
            self._conditions += self._add_conditions(data, t)
            tl = self._add_timeline(data, timepoints, timings, t, is_main)
            if tl:
                self._timelines.append(tl)
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of timeline {t}",
                e,
                KlassMethodLocation(self.MODULE, "_execute_one"),
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
        return self._activities

    @property
    def conditions(self) -> list[Condition]:
        return self._conditions

    @property
    def biomedical_concepts(self) -> list[BiomedicalConcept]:
        return self._biomedical_concepts

    @property
    def biomedical_concept_surrogates(self) -> list[BiomedicalConceptSurrogate]:
        return self._biomedical_concept_surrogates

    # @property
    # def procedures(self) -> list[Procedure]:
    #     return self._procedures

    def _add_epochs(self, data, t: int = 1) -> list[ScheduledInstance]:
        try:
            results = []
            map = {}
            # self._errors.debug(
            #     f"EPOCHS:\n{data['epochs']}\n",
            #     KlassMethodLocation(self.MODULE, "_add_epochs"),
            # )
            items = data["epochs"]["items"]
            timepoints = data["timepoints"]["items"]
            for index, item in enumerate(items):
                label = item["text"]
                name = f"EPOCH-{label.upper()}"
                if name not in map:
                    epoch: StudyEpoch = self._builder.create(
                        StudyEpoch,
                        {
                            "name": self._qualify(
                                self._epoch_name(label, index + 1), t),
                            "description": None,
                            "label": label,
                            "type": self._builder.klass_and_attribute_value(
                                StudyEpoch, "type", "Treatment Epoch"
                            ),
                        },
                    )
                    results.append(epoch)
                    map[name] = epoch
                epoch = map[name]
                timepoints[index]["epoch_instance"] = epoch
            self._errors.info(
                f"Epochs: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_epochs"),
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Epochs",
                e,
                KlassMethodLocation(self.MODULE, "_add_epochs"),
            )
            return results

    def _add_encounters(self, data, t: int = 1) -> list[Encounter]:
        try:
            results = []
            items = data["visits"]["items"]
            timepoints: dict = data["timepoints"]["items"]
            for index, item in enumerate(items):
                name = item["text"]
                encounter: Encounter = self._builder.create(
                    Encounter,
                    {
                        "name": self._qualify(f"E{index + 1}", t),
                        "description": None,
                        "label": name,
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
                        "scheduledAtId": None,  # @todo
                    },
                )
                results.append(encounter)
                timepoints[index]["encounter_instance"] = encounter
                for ref in item["references"]:
                    self._condition_timepoint_index(ref, index)
            self._errors.info(
                f"Encounters: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_encounters"),
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Encounters",
                e,
                KlassMethodLocation(self.MODULE, "_add_encounters"),
            )
            return results

    def _condition_timepoint_index(self, ref: str, index: int) -> None:
        if ref not in self._condition_links:
            self._condition_links[ref] = {
                "reference": ref,
                "timepoint_index": [],
                "activity_id": [],
            }
        self._condition_links[ref]["timepoint_index"].append(index)

    def _condition_activity_id(self, ref: str, id: str) -> None:
        if ref not in self._condition_links:
            self._condition_links[ref] = {
                "reference": ref,
                "timepoint_index": [],
                "activity_id": [],
            }
        self._condition_links[ref]["activity_id"].append(id)

    def _condition_combined(self, ref, sai_index: int, activity_id: str) -> None:
        if ref not in self._condition_links:
            self._condition_links[ref] = {
                "reference": ref,
                "timepoint_index": [],
                "activity_id": [],
            }
        self._condition_links[ref]["activity_id"].append(activity_id)
        self._condition_links[ref]["timepoint_index"].append(sai_index)

    def _add_activities(self, data, t: int = 1) -> list[Activity]:
        """Create (or reuse) the activities named on this table.

        Activities are shared across timelines: the registry
        (``self._activity_by_name``) is keyed by normalised label, so an
        activity that appears on more than one SoA table yields a single
        ``Activity`` referenced by each timeline. Only newly-created activities
        are appended to ``self._activities``; ordering (previousId/nextId) is
        applied once, globally, in ``execute``. Returns the activities created
        on this call (for logging only).
        """
        created: list[Activity] = []
        try:
            items = data["activities"]["items"]
            for item in items:
                activity = self._get_or_create_activity(item, created)
                if "references" in item:
                    for ref in item["references"]:
                        self._condition_activity_id(ref, activity.id)
                item["activity_instance"] = activity
                if "children" in item:
                    for child in item["children"]:
                        child_activity = self._get_or_create_activity(child, created)
                        if "references" in child:
                            for ref in child["references"]:
                                self._condition_activity_id(ref, child_activity.id)
                        child["activity_instance"] = child_activity
                        if child_activity.id not in activity.childIds:
                            activity.childIds.append(child_activity.id)
            self._errors.info(
                f"Activities (timeline {t}): +{len(created)} new, "
                f"{len(self._activity_by_name)} total",
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
            return created
        except Exception as e:
            self._errors.exception(
                "Error creating Activities",
                e,
                KlassMethodLocation(self.MODULE, "_add_activities"),
            )
            return created

    def _qualify(self, name: str, t: int) -> str:
        """House style: `E1` in a single-timeline study, `T2-E1` where several
        timelines are built. Prefixing unconditionally makes every identifier
        in the common case four characters longer for no gain."""
        return f"T{t}-{name}" if getattr(self, "_multi_timeline", False) else name

    _HOUSE_NAMES_PATH = Path(__file__).parent / "data" / "house_names.yaml"
    _house_names: dict | None = None

    @classmethod
    def _house(cls) -> dict:
        """The curated short-name vocabulary, loaded once.

        `data/house_names.yaml` is meant to be added to: an entry there beats
        the generated form, so curating a name is how an ugly one gets fixed.
        A missing or unreadable file degrades to generation for everything
        rather than failing the assembly."""
        if cls._house_names is None:
            try:
                import yaml
                cls._house_names = yaml.safe_load(
                    cls._HOUSE_NAMES_PATH.read_text()) or {}
            except Exception:
                cls._house_names = {}
        return cls._house_names

    @staticmethod
    def _name_key(text: str) -> str:
        """Lookup key: case, punctuation, whitespace and a trailing footnote
        marker all removed. `Pregnancy Test`, `pregnancy test` and
        `Pregnancy testb` resolve to the same entry."""
        t = (text or "").strip().lower()
        t = re.sub(r"[\s,;]*\(?[a-z]?\d{1,2}\)?$", "", t)
        t = re.sub(r"[^a-z0-9/ -]+", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    def _epoch_name(self, label: str, index: int) -> str:
        """House-style epoch name.

        Matched against the CDISC C99079 (SDTM Epoch) terms in
        `data/house_names.yaml` — SCREENING -> `SCR`, FOLLOW-UP -> `FU` — so
        the same phase carries the same name across protocols however the
        document words it. Unmatched epochs generate from the label."""
        key = self._name_key(label)
        if key:
            pairs = [(c, term["name"])
                     for term in (self._house().get("epochs") or {}).values()
                     for c in (term.get("match") or [])]
            # Longest candidate first: `long-term follow-up` must not be taken
            # by `follow-up`, which it ends with.
            for candidate, name in sorted(pairs, key=lambda x: -len(x[0])):
                if key == candidate or key.startswith(candidate + " ") \
                        or key.endswith(" " + candidate):
                    return name
            # No CT term fits — generate the same way an activity does, rather
            # than truncating a slug mid-word (`BONEMARROWSU`).
            return self._initials(label) or f"EP{index}"
        return f"EP{index}"

    _ACT_STOPWORDS = {
        "of", "the", "and", "or", "a", "an", "for", "to", "in", "at", "by",
        "with", "per", "on", "from", "if",
    }

    def _significant_words(self, text: str) -> list[str]:
        return [w for w in re.split(r"[^A-Za-z0-9]+", text or "")
                if w and w.lower() not in self._ACT_STOPWORDS]

    def _initials(self, text: str) -> str:
        """Initials of the significant words, uppercased and capped. A single
        word gives its first four characters."""
        words = self._significant_words(text)
        if not words:
            return ""
        return (words[0][:4] if len(words) == 1
                else "".join(w[0] for w in words)[:6]).upper()

    def _activity_name(self, text: str, seq: int) -> str:
        """House style short name for an activity: `VS`, `IC`, `ECG`.

        `name` is a shorthand identifier — short, unique, and meaningful enough
        to follow a cross-reference by eye. The protocol's own wording is the
        `label`; it does not belong in the name, where it produced 46-character
        identifiers full of spaces.

        Derivation is initials of the significant words (one word gives its
        first four characters). A collision extends the abbreviation from the
        word that diverges rather than appending a number, so the name keeps
        meaning: `physical examination` -> `PE`, `participant education` ->
        `PEDU`, `participant eligibility` -> `PELI`.
        """
        raw = (text or "").strip()
        if not raw:
            return f"ACT{seq}"
        table = self._house().get("activities") or {}
        key = self._name_key(raw)
        curated = table.get(key)
        if curated is None and len(key) > 4 and key[-1].isalpha():
            # `Pregnancy testb` — a footnote LETTER, the form register N13 does
            # not cover. Only consulted to find a curated entry; the text
            # itself is never rewritten, so `CD4` cannot be truncated to `CD`.
            curated = table.get(key[:-1].strip())
        if curated:
            self._activity_name_registry.setdefault(curated, raw)
            return curated
        words = self._significant_words(raw)
        if not words:
            return f"ACT{seq}"
        base = self._initials(raw)
        taken = self._activity_name_registry
        if base not in taken:
            taken[base] = raw
            return base
        if taken[base] == raw:
            return base
        for extra in range(1, 4):                      # PE -> PEDU -> PEDUC
            longer = "".join(w[: 1 + extra] for w in words)[:8].upper()
            if longer not in taken:
                taken[longer] = raw
                return longer
        n = 2
        while f"{base}{n}" in taken:
            n += 1
        taken[f"{base}{n}"] = raw
        return f"{base}{n}"

    def _get_or_create_activity(self, item: dict, created: list[Activity]) -> Activity:
        """Return the shared Activity for ``item['name']``, creating it on first
        sighting. The activity's name IS its (trimmed) label text — the SoA
        grid and BC/procedure references in the workbook show names, so they
        must be human-readable. Uniqueness holds because the registry is keyed
        by the normalised label (same label → same shared Activity); a
        label-less activity falls back to the ``ACTIVITY-{n}`` sequence."""
        key = (item["name"] or "").strip().lower()
        existing = self._activity_by_name.get(key)
        if existing is not None:
            return existing
        bc_ids, sbc_ids, procedures = self._get_biomedical_concepts(item)
        seq = len(self._activity_by_name) + 1
        params = {
            "name": self._activity_name(item["name"], seq),
            "description": None,
            "label": (item["name"] or "").strip() or None,
            "definedProcedures": procedures,
            "biomedicalConceptIds": bc_ids,
            "bcCategoryIds": [],
            "bcSurrogateIds": sbc_ids,
            "timelineId": None,
        }
        activity: Activity = self._builder.create(Activity, params)
        self._activity_by_name[key] = activity
        self._activities.append(activity)
        created.append(activity)
        return activity

    def _add_timepoints(self, data, t: int = 1) -> list[ScheduledInstance]:
        try:
            results = []
            timepoints: list = data["timepoints"]["items"]
            for index, item in enumerate(timepoints):
                sai = self._builder.create(
                    ScheduledActivityInstance,
                    {
                        "name": self._sai_name(data, index, t),
                        "description": None,
                        "label": item["text"],
                        "timelineExitId": None,
                        "encounterId": item["encounter_instance"].id
                        if item["encounter_instance"]
                        else None,
                        "scheduledInstanceTimelineId": None,
                        "defaultConditionId": None,
                        "epochId": item["epoch_instance"].id,
                        "activityIds": [],
                    },
                )
                item["sai_instance"] = sai
                results.append(sai)
            self._errors.info(
                f"SAI: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_timepoints"),
            )
            sai: ScheduledActivityInstance
            for index, sai in enumerate(results[:-1]):
                sai.defaultConditionId = results[index + 1].id
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating Scheduled Activity timepoints",
                e,
                KlassMethodLocation(self.MODULE, "_add_timepoints"),
            )
            return results

    def _add_conditions(self, data, t: int = 1) -> list[Condition]:
        """Create the Conditions for one timeline from its extracted footnotes.

        A condition is only created when its footnote reference (``"a"``,
        ``"1"``, …) can be aligned to something in the timeline — a timepoint,
        an activity, or both — via ``self._condition_links``, which the
        timepoint and activity passes populate.

        **Policy: an unanchored condition is skipped, not created.** Two cases
        are skipped, and both are counted and reported:

        - ``dropped_no_ref`` — the extractor supplied no reference at all, so
          there is nothing to align on.
        - ``dropped_no_match`` — a reference was supplied but nothing in this
          timeline carries it.

        Creating these anyway would mean a ``Condition`` with empty
        ``contextIds`` and ``appliesToIds``. Downstream that is a hard error:
        ``usdm4_legacy_excel`` rejects a condition with no ``appliesTo``, so
        emitting unanchored conditions would break the Excel round trip for
        every study. Anchoring is the extractor's job; this assembler's job is
        to say loudly when it did not happen.

        Every call emits one summary line (items in / referenced / aligned /
        dropped-no-ref / dropped-no-match) so the three outcomes can be told
        apart without re-running a whole corpus comparison.
        """
        results = []
        conditions: list = data["conditions"]["items"]
        timepoints: list = data["timepoints"]["items"]
        counts = {
            "in": 0,
            "referenced": 0,
            "aligned": 0,
            "dropped_no_ref": 0,
            "dropped_no_match": 0,
        }
        try:
            counts["in"] = len(conditions)
            for index, item in enumerate(conditions):
                ref = item.get("reference") if isinstance(item, dict) else None
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
                timepoint_ids = [
                    timepoints[x]["sai_instance"].id for x in links["timepoint_index"]
                ]
                activity_ids = [x for x in links["activity_id"]]
                condition = self._builder.create(
                    Condition,
                    {
                        "name": self._qualify(f"COND{index + 1}", t),
                        # The printed marker (`a`, `b`, `11`) is what a
                        # reviewer matches against the footnote legend by eye,
                        # and what makes a glued activity suffix provable.
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
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating conditions",
                e,
                KlassMethodLocation(self.MODULE, "_add_conditions"),
            )
            return results
        finally:
            self._condition_summary(counts, t)

    def _condition_summary(self, counts: dict, t: int) -> None:
        """Emit the per-timeline condition alignment summary.

        One line, always, even when there were no conditions to process — a
        zero line is itself the signal that the extractor produced nothing for
        this timeline, which is a different failure from producing footnotes
        that could not be anchored.
        """
        self._errors.info(
            f"Conditions T{t}: in={counts['in']}, "
            f"referenced={counts['referenced']}, "
            f"aligned={counts['aligned']}, "
            f"dropped_no_ref={counts['dropped_no_ref']}, "
            f"dropped_no_match={counts['dropped_no_match']}",
            KlassMethodLocation(self.MODULE, "_add_conditions"),
        )

    def _add_timing(self, data, t: int = 1) -> list[ScheduledInstance]:
        try:
            results = []
            timepoints: list = data["timepoints"]["items"]
            anchor_index = self._find_anchor(data)
            anchor: ScheduledInstance = timepoints[anchor_index]["sai_instance"]
            item: dict[str]
            for index, item in enumerate(timepoints):
                this_sai: ScheduledInstance = item["sai_instance"]
                if index < anchor_index:
                    if timing := self._timing(
                        data, index, anchor_index, "Before", this_sai.id, anchor.id, t
                    ):
                        results.append(timing)
                elif index == anchor_index:
                    if timing := self._timing(
                        data,
                        index,
                        anchor_index,
                        "Fixed Reference",
                        this_sai.id,
                        this_sai.id,
                        t,
                    ):
                        results.append(timing)
                else:
                    if timing := self._timing(
                        data, index, anchor_index, "After", this_sai.id, anchor.id, t
                    ):
                        results.append(timing)
            self._errors.info(
                f"Timing: {len(results)}",
                KlassMethodLocation(self.MODULE, "_add_timing"),
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Error creating timings",
                e,
                KlassMethodLocation(self.MODULE, "_add_timing"),
            )
            return results

    _EMPTY_WINDOW = {"before": 0, "after": 0, "unit": ""}

    def _timing(
        self,
        data: dict,
        index: int,
        anchor_index: int,
        type: str,
        from_id: str,
        to_id: str,
        t: int = 1,
    ) -> Timing:
        try:
            windows: list = data["windows"]["items"]
            timepoints: list = data["timepoints"]["items"]
            timepoint = timepoints[index]
            window = windows[index] if index < len(windows) else self._EMPTY_WINDOW
            item: Timing = self._builder.create(
                Timing,
                {
                    "type": self._builder.klass_and_attribute_value(
                        Timing, "type", type
                    ),
                    "value": self._encoder.iso8601_duration(
                        self._interval_from_anchor(timepoints, index, anchor_index),
                        timepoint["unit"],
                    ),
                    "valueLabel": self._timing_value_label(timepoints, index),
                    "name": self._qualify(f"TIM{index + 1}", t),
                    "description": None,
                    "label": self._timing_value_label(timepoints, index),
                    "relativeToFrom": self._builder.klass_and_attribute_value(
                        Timing, "relativeToFrom", "start to start"
                    ),
                    "windowLabel": self._window_label(windows, index),
                    "windowLower": self._encoder.iso8601_duration(
                        self._set_abs_duration(window["before"]), window["unit"]
                    )
                    if window["before"]
                    else "",
                    "windowUpper": self._encoder.iso8601_duration(
                        self._set_abs_duration(window["after"]), window["unit"]
                    )
                    if window["after"]
                    else "",
                    "relativeFromScheduledInstanceId": from_id,
                    "relativeToScheduledInstanceId": to_id,
                },
            )
            # print(f"WINDOW: {window} -> {item.windowLabel}, [{item.windowLower}, {item.windowUpper}]")
            return item
        except Exception as e:
            self._errors.exception(
                "Error creating individual timing",
                e,
                KlassMethodLocation(self.MODULE, "_timing"),
            )
            return None

    def _set_abs_duration(self, value: int | str) -> int:
        # print(f"DURATION: {value}")
        return 0 if not isinstance(value, int) else abs(value)

    @staticmethod
    def _coerce_int(value) -> int | None:
        """Coerce a timepoint value to int. Accepts int, whole float, and
        numeric strings (schema allows all three). Returns None if not numeric."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value) if value.is_integer() else None
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                return None
        return None

    _SAI_TEXT_PATTERNS = (
        (re.compile(r"^day\s*(-?\d+)$", re.IGNORECASE), "D{}"),
        (re.compile(r"^week\s*(-?\d+)$", re.IGNORECASE), "W{}"),
        (re.compile(r"^cycle\s*(\d+)[ ,]*day\s*(-?\d+)$", re.IGNORECASE), "C{}D{}"),
    )

    def _sai_name(self, data, index: int, t: int) -> str:
        """Human-readable SAI name for the timing sheet's from/to references:
        derived from the timepoint text (``Day 1`` → ``D1``, ``Week 12`` →
        ``W12``, ``Cycle 2 Day 1`` → ``C2D1``), else an upper-cased slug of the
        timepoint or visit text, else the positional fallback
        ``T{t}-SAI-{n}``. Uniqued across the study with a numeric suffix."""
        base = self._sai_base_name(data, index)
        if not base:
            base = f"T{t}-SAI-{index + 1}"
        count = self._sai_name_registry.get(base, 0) + 1
        self._sai_name_registry[base] = count
        return base if count == 1 else f"{base}-{count}"

    _UNIT_PREFIXES = {
        "day": "D",
        "d": "D",
        "week": "W",
        "wk": "W",
        "w": "W",
        "hour": "H",
        "hr": "H",
        "h": "H",
        "minute": "MIN",
        "min": "MIN",
        "month": "MTH",
        "mth": "MTH",
        "year": "Y",
        "yr": "Y",
        "y": "Y",
    }

    def _sai_base_name(self, data, index: int) -> str:
        timepoint = data["timepoints"]["items"][index]
        visits = (data.get("visits") or {}).get("items") or []
        visit_text = (visits[index].get("text") or "") if index < len(visits) else ""
        for source, text in (
            ("timepoint", timepoint.get("text") or ""),
            ("visit", visit_text),
        ):
            text = text.strip()
            if not text:
                continue
            if source == "timepoint" and re.fullmatch(r"[+-]?\d+", text):
                # A bare number is a day/week count — prefix with the unit
                # letter, preferring the signed value (the text often drops
                # the sign).
                unit = (timepoint.get("unit") or "").strip().lower().rstrip("s")
                prefix = self._UNIT_PREFIXES.get(unit)
                if prefix:
                    value = self._coerce_int(timepoint.get("value"))
                    return f"{prefix}{value if value is not None else text}"
            for pattern, template in self._SAI_TEXT_PATTERNS:
                match = pattern.match(text)
                if match:
                    return template.format(*match.groups())
            slug = re.sub(r"[^A-Z0-9+,_ .-]", "", text.upper().replace("/", " "))
            slug = re.sub(r"\s+", " ", slug).strip()
            if slug:
                return slug[:20].rstrip()
        return ""

    @staticmethod
    def _is_placeholder(item: dict) -> bool:
        """A blank SoA column: no text and no (or zero) value. These carry no
        timing information — e.g. an unlabelled ET/unscheduled column."""
        value = TimelineAssembler._coerce_int(item.get("value"))
        return not (item.get("text") or "").strip() and not value

    _DAY_UNITS = ("day", "days", "d")

    def _interval_from_anchor(
        self, timepoints: list[dict], index: int, anchor_index: int
    ) -> int:
        """Duration between this timepoint and the anchor.

        USDM ``Timing.value`` is the interval relative to the referenced
        instance, NOT the protocol's day number: Day 16 relative to a Day 1
        anchor is 15 days. When day numbering is 1-based (no Day 0 in the
        table, the common protocol convention), an interval crossing zero
        loses a day: Day -1 to Day 1 is 1 day, Day -42 to Day 1 is 42 days.
        Falls back to ``abs(value)`` (the historical behaviour) when either
        value is non-numeric or the units differ."""
        timepoint = timepoints[index]
        anchor = timepoints[anchor_index]
        value = self._coerce_int(timepoint.get("value"))
        anchor_value = self._coerce_int(anchor.get("value"))
        if value is None or anchor_value is None:
            return self._set_abs_duration(timepoint.get("value"))
        unit = (timepoint.get("unit") or "").strip().lower()
        anchor_unit = (anchor.get("unit") or "").strip().lower()
        if unit.rstrip("s") != anchor_unit.rstrip("s"):
            self._errors.warning(
                f"Timing unit '{timepoint.get('unit')}' differs from anchor "
                f"unit '{anchor.get('unit')}'; using absolute value "
                f"{abs(value)} for '{timepoint.get('text')}'",
                KlassMethodLocation(self.MODULE, "_interval_from_anchor"),
            )
            return abs(value)
        delta = abs(value - anchor_value)
        if (
            unit in self._DAY_UNITS
            and (value < 0 < anchor_value or anchor_value < 0 < value)
            and not self._has_zero_timepoint(timepoints)
        ):
            delta -= 1
        return delta

    def _has_zero_timepoint(self, timepoints: list[dict]) -> bool:
        """True if the table numbers days from zero (an explicit Day 0 column
        exists), in which case no crossing-zero correction applies."""
        for item in timepoints:
            if self._is_placeholder(item):
                continue
            if self._coerce_int(item.get("value")) == 0:
                return True
        return False

    def _window_label(self, windows: list[dict], index: int):
        """The window as `-1..+2 days`, or None where there is no window.

        House style: a label carries the protocol's words or it is absent.
        `???` read as data while saying nothing."""
        if index >= len(windows):
            return None
        window = windows[index]
        if window["before"] == 0 and window["after"] == 0:
            return ""
        return f"-{window['before']}..+{window['after']} {window['unit']}"

    def _timing_value_label(self, timepoints: list[dict], index: int):
        """The timepoint's own text, or None where the protocol states none.

        House style: a label carries the protocol's words or it is absent.
        `???` was a manufactured placeholder — it reads as data, sorts, and
        compares, while saying nothing."""
        if index >= len(timepoints):
            return None
        return timepoints[index]["text"] or None

    def _find_anchor(self, data) -> int:
        """Positional index of the anchor timepoint: the first real (non-blank)
        column with a value >= 0 — Day 0 or Day 1 in a typical SoA. Returns the
        position in the items list; the input's own ``index`` field is ignored
        (the schema defaults it to 0, so it is 0 for every item when the
        producer — e.g. ground truth — does not supply it)."""
        items = data["timepoints"]["items"]
        item: dict
        for index, item in enumerate(items):
            if self._is_placeholder(item):
                continue
            value = self._coerce_int(item.get("value"))
            if value is not None and value >= 0:
                return index
        return 0

    def _link_timepoints_and_activities(self, data: dict) -> None:
        """Attach each activity (and child activity) to the SAIs of the visits
        it is marked at. NOTE: an activity's own visits are always processed —
        the schema defaults ``children`` to ``[]`` for every activity, so a
        presence test on the key (the historical behaviour) made flat
        activities (the ground-truth shape) link nothing at all."""
        try:
            activities = data["activities"]["items"]
            timepoints = data["timepoints"]["items"]
            for activity in activities:
                self._link_one_activity(activity, timepoints)
                for child in activity.get("children") or []:
                    self._link_one_activity(child, timepoints)
        except Exception as e:
            self._errors.exception(
                "Error linking timepoints and activities",
                e,
                KlassMethodLocation(self.MODULE, "_link_timepoints_and_activities"),
            )
            return None

    def _link_one_activity(self, activity: dict, timepoints: list[dict]) -> None:
        activity_instance: Activity = activity["activity_instance"]
        for visit in activity.get("visits") or []:
            index = visit["index"]
            sai_instance: ScheduledActivityInstance = timepoints[index]["sai_instance"]
            sai_instance.activityIds.append(activity_instance.id)
            for ref in visit["references"]:
                self._condition_combined(ref, index, activity_instance.id)

    def _add_timeline(
        self,
        data,
        instances: list[ScheduledInstance],
        timings: list[Timing],
        t: int = 1,
        is_main: bool = True,
    ):
        try:
            self._errors.debug(
                f"Instances: {len(instances)}, Timings: {len(timings)}",
                KlassMethodLocation(self.MODULE, "_add_timeline"),
            )
            exit = self._builder.create(ScheduleTimelineExit, {})
            sai: ScheduledActivityInstance = instances[-1]
            sai.timelineExitId = exit.id
            sai.defaultConditionId = None
            duration = None
            title = data.get("table_title") or (
                "Main timeline" if is_main else f"Timeline {t}"
            )
            # The description is prose. It was generated from ``is_main`` alone
            # and has no other reader, so a caller with something better to say
            # about the timeline may supply it.
            description = data.get("table_description") or (
                "The main timeline" if is_main else f"Subsidiary timeline {t}"
            )
            return self._builder.create(
                ScheduleTimeline,
                {
                    "mainTimeline": is_main,
                    "name": f"TIMELINE-{t}",
                    "description": description,
                    "label": title,
                    "entryCondition": "Paricipant identified",
                    "entryId": instances[0].id,
                    "exits": [exit],
                    "plannedDuration": duration,
                    "instances": instances,
                    "timings": timings,
                    "extensionAttributes": self._timeline_extensions(data),
                },
            )
        except Exception as e:
            self._errors.exception(
                "Error creating timeline",
                e,
                KlassMethodLocation(self.MODULE, "_add_timeline"),
            )
            return None

    # The SoA input's classification keys, and the d4k extension each is
    # emitted as. One concept per URL, matching every other d4k extension.
    _CLASSIFICATION_EXTENSIONS = (
        ("table_family", TLF_EXT_URL),
        ("table_orientation", TLO_EXT_URL),
        ("table_unit", TLU_EXT_URL),
        ("table_placement", TLP_EXT_URL),
    )

    def _timeline_extensions(self, data: dict) -> list[ExtensionAttribute]:
        """Classification of the source table, as d4k extension attributes.

        A caller that has classified the table it read — a sampling or dosing
        profile, which way round its timing axis ran, in what unit, and whether
        it was printed with the main schedule or away from it — has nowhere in
        USDM to say so. The description is prose and would have to be parsed
        back; these are queryable by URL.

        Emitted together or not at all, so the presence of the family attribute
        is what marks a timeline as a profile. A caller that classifies nothing
        gets an empty list, which is what every timeline had before.
        """
        extensions: list[ExtensionAttribute] = []
        try:
            for key, url in self._CLASSIFICATION_EXTENSIONS:
                value = data.get(key)
                if value in (None, ""):
                    continue
                extensions.append(
                    self._builder.create(
                        ExtensionAttribute, {"url": url, "valueString": str(value)}
                    )
                )
        except Exception as e:
            self._errors.exception(
                "Error creating timeline classification extensions",
                e,
                KlassMethodLocation(self.MODULE, "_timeline_extensions"),
            )
        return extensions

    def _get_biomedical_concepts(
        self, activity: dict
    ) -> tuple[list[str], list[str], list[Procedure]]:
        bc_ids = []
        sbc_ids = []
        procedures = []
        # print(f"ACTIVITY: {activity}")
        if "actions" in activity:
            for bc_name in activity["actions"]["bcs"]:
                # print(f"BC: {bc_name}")
                if self._builder.cdisc_bc_library.exists(bc_name):
                    bc: BiomedicalConcept = self._builder.bc(bc_name)
                    if bc:
                        self._biomedical_concepts.append(bc)
                        bc_ids.append(bc.id)
                    else:
                        self._errors.warning(
                            f"Failed to create BC with name '{bc_name}'"
                        )
                else:
                    params = {
                        "name": bc_name,
                        "description": bc_name,
                        "label": bc_name,
                        "reference": "None set",
                    }
                    sbc: BiomedicalConceptSurrogate = self._builder.create(
                        BiomedicalConceptSurrogate, params
                    )
                    if sbc:
                        self._biomedical_concept_surrogates.append(sbc)
                        sbc_ids.append(sbc.id)
                    else:
                        self._errors.warning(
                            f"Failed to create surrogate BC with name '{bc_name}'"
                        )
                params = {
                    "name": bc_name,
                    "description": bc_name,
                    "label": bc_name,
                    "procedureType": activity["name"],
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
                }
                procedure = self._builder.create(Procedure, params)
                if procedure:
                    # self._procedures.append(procedure)
                    procedures.append(procedure)
                else:
                    self._errors.warning(
                        f"Failed to create procedure with name '{bc_name}'"
                    )
        # print(f"IDS: '{bc_ids}', '{sbc_ids}', '{procedures}'")
        return bc_ids, sbc_ids, procedures
