"""The timeline assembler's new input — issue 63, part 63.3.

One ``ScheduleTimelineInput`` per timeline. Every header value is text: the
text as printed (``text``, used for labels) and its pattern form (``pattern``,
parsed by ``usdm4.assembler.timeline.grammar``). A caller never hands over a
number it has worked out from printed text. Specification:
``docs/timeline_assembler_design.md`` § 3.

This module checks STRUCTURE only — required fields, types, and references
inside one timeline (column ids, cell columns, activity parents, footnote
markers). It does not parse patterns: that happens in the assembler's parse
stage, so a pattern the grammar cannot yet read (a timing span, a cycle) can be
carried as text until the rule that reads it exists.

Unknown keys are refused (``extra="forbid"``). The input this replaces dropped
them silently, which once hid a classification field from the assembler for
some time; a contract other programs generate should say when it is misused.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

TimelineType = Literal[
    "main",
    "extension_study",
    "continued_access",
    "arm",
    "cohort",
    "unscheduled",
    "early_termination",
    "adverse_event",
    "profile",
    "unclassified",
]

TimelineFamily = Literal["planned", "variant", "conditional", "profile", "unclassified"]

FAMILY: dict[str, str] = {
    "main": "planned",
    "extension_study": "planned",
    "continued_access": "planned",
    "arm": "variant",
    "cohort": "variant",
    "unscheduled": "conditional",
    "early_termination": "conditional",
    "adverse_event": "conditional",
    "profile": "profile",
    "unclassified": "unclassified",
}


def family_of(timeline_type: str) -> str:
    """The family a timeline type belongs to. Derived, never supplied."""
    return FAMILY[timeline_type]


class _Model(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")


class HeaderValue(_Model):
    """One header value: as printed, and in the pattern grammar.

    - ``pattern`` only: a caller using the assembler directly; the label
      defaults to the pattern.
    - ``text`` only (``pattern`` null): the caller states the value cannot be
      expressed in the grammar; it is carried as text and never parsed.
    - both empty: not a value — leave the field null instead.
    """

    text: str = ""
    pattern: str | None = None

    @model_validator(mode="after")
    def _not_empty(self) -> "HeaderValue":
        if not self.text.strip() and not (self.pattern or "").strip():
            raise ValueError(
                "a header value needs printed text or a pattern; "
                "use null for a value that is not there"
            )
        return self

    @property
    def label(self) -> str:
        """The text to use as a label: as printed, else the pattern."""
        return self.text.strip() or (self.pattern or "").strip()


class HeaderNote(_Model):
    """A further header row kept as text only — a second timing row, a timing
    clarification, an unassigned row. Never parsed."""

    role: str
    text: str


class ColumnInput(_Model):
    """One column of the schedule, in document order."""

    id: str
    epoch: HeaderValue | None = None
    visit: HeaderValue | None = None
    cycle: HeaderValue | None = None
    cycle_length: HeaderValue | None = None
    timing: HeaderValue | None = None
    window: HeaderValue | None = None
    notes: list[HeaderNote] = []
    markers: list[str] = []

    @model_validator(mode="after")
    def _id_not_blank(self) -> "ColumnInput":
        if not self.id.strip():
            raise ValueError("a column id may not be blank")
        return self


class CellInput(_Model):
    """One non-empty body cell: the column it sits in, its printed text
    (``X``, ``(X)``, ``Predose`` …) and any footnote markers on it."""

    column: str
    text: str = ""
    markers: list[str] = []


class ActivityInput(_Model):
    """One body row. ``name`` is as printed; ``parent`` is the name of the
    grouping row it sits under, if any."""

    name: str
    parent: str | None = None
    markers: list[str] = []
    bcs: list[str] = []
    cells: list[CellInput] = []

    @model_validator(mode="after")
    def _name_not_blank(self) -> "ActivityInput":
        if not self.name.strip():
            raise ValueError("an activity name may not be blank")
        return self


class FootnoteInput(_Model):
    """A footnote in the timeline's legend, marker to text, verbatim."""

    marker: str
    text: str


class TimelineClassification(_Model):
    """How the source table was printed. Emitted as d4k extension
    attributes; the family is not here because it is derived from the type."""

    orientation: str | None = None
    unit: str | None = None
    placement: str | None = None


class ScheduleTimelineInput(_Model):
    """One timeline. Replaces ``TimelineInput`` once the assembler reads it
    (issue 63, part 63.4)."""

    type: TimelineType
    title: str | None = None
    description: str | None = None
    entry_condition: str | None = None
    attaches_to: str | None = None
    classification: TimelineClassification = TimelineClassification()
    columns: list[ColumnInput] = []
    activities: list[ActivityInput] = []
    footnotes: list[FootnoteInput] = []

    @property
    def family(self) -> str:
        return family_of(self.type)

    @model_validator(mode="after")
    def _check_references(self) -> "ScheduleTimelineInput":
        column_ids = [c.id for c in self.columns]
        duplicates = sorted({x for x in column_ids if column_ids.count(x) > 1})
        if duplicates:
            raise ValueError(f"column ids must be unique; repeated: {duplicates}")
        known_columns = set(column_ids)

        names = [a.name for a in self.activities]
        for activity in self.activities:
            if activity.parent is not None and activity.parent not in names:
                raise ValueError(
                    f"activity {activity.name!r} names parent "
                    f"{activity.parent!r}, which is not an activity here"
                )
            seen: set[str] = set()
            for cell in activity.cells:
                if cell.column not in known_columns:
                    raise ValueError(
                        f"activity {activity.name!r} has a cell in column "
                        f"{cell.column!r}, which is not a column here"
                    )
                if cell.column in seen:
                    raise ValueError(
                        f"activity {activity.name!r} has two cells in "
                        f"column {cell.column!r}"
                    )
                seen.add(cell.column)

        markers = [f.marker for f in self.footnotes]
        repeated = sorted({x for x in markers if markers.count(x) > 1})
        if repeated:
            raise ValueError(f"footnote markers must be unique; repeated: {repeated}")

        # The activity a profile attaches to usually sits on ANOTHER timeline
        # (the main one), so only the type can be checked here.
        if self.attaches_to is not None and self.type != "profile":
            raise ValueError(
                f"attaches_to is for profile timelines; this one is {self.type!r}"
            )

        if self.entry_condition is not None and self.family != "conditional":
            raise ValueError(
                f"entry_condition is for conditional timelines; this one is "
                f"{self.type!r}"
            )
        return self
