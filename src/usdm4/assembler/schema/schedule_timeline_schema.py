"""The timeline assembler's input — issue 63; structured in issue 73 (U4-35).

One ``ScheduleTimelineInput`` per timeline. ``usdm4`` is algorithm only and
never reads printed text: the caller (``usdm4_protocol``, which may use AI;
``protocol_corpus``'s ground truth; or any algorithmic source) turns the
printed schedule into structure, and hands every header value over as a
structured object. Specification: ``docs/timeline_assembler_design.md`` § 3
and § 9 U4-35.

Every value object carries:

- ``text`` — the source as printed, for debug and after-the-event analysis.
  Never read or interpreted. Its one use is as a label, copied verbatim into
  USDM; when it is empty the label is rendered from the structure. Empty when
  the caller structured the value from an algorithmic source.
- ``markers`` — the footnote markers printed on THIS value
  (``Visit 3^1,2`` → ``["1", "2"]``, issue 64).
- ``redacted`` — the sponsor printed ``CCI`` in place of the value. The
  structured fields must then be empty.

A value whose structured fields are all empty and that is not redacted is
*text only*: the caller states the value is printed but could not be
structured. It is carried as a label and never read (U4-3: a text-only timing
is a zero timing plus a warning).

Day numbers (timing, time ranges) are the numbers as printed; ``usdm4``
applies the Day 0 rule using the timeline's ``day_zero`` flag.

This module checks STRUCTURE only — required fields, types, value ranges and
references inside one timeline (column ids, cell columns, activity parents,
footnote markers).

Unknown keys are refused (``extra="forbid"``). An input that dropped them
silently once hid a classification field from the assembler for some time; a
contract other programs generate should say when it is misused.
"""

from typing import ClassVar, Literal

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

# The only units accepted (U4-35). The caller normalises; nothing else is read.
Unit = Literal["minutes", "hours", "days", "weeks", "months", "years"]

# The printed header rows of a column, in the order they are read. Also the
# only keys ``ScheduleTimelineInput.rows`` accepts.
HEADER_FIELDS: tuple[str, ...] = (
    "epoch",
    "visit",
    "cycle",
    "cycle_length",
    "timing",
    "window",
)

# Every value a column can carry: the header rows plus ``delay`` (R8), which
# is printed in whichever row the protocol uses.
VALUE_FIELDS: tuple[str, ...] = HEADER_FIELDS + ("delay",)


def family_of(timeline_type: str) -> str:
    """The family a timeline type belongs to. Derived, never supplied."""
    return FAMILY[timeline_type]


class _Model(BaseModel):
    model_config = ConfigDict(strict=False, extra="forbid")


class _Value(_Model):
    """What every header value carries besides its structure."""

    text: str = ""
    markers: list[str] = []
    redacted: bool = False

    # The structured fields of the subclass; all set, or all empty.
    _STRUCTURE: ClassVar[tuple[str, ...]] = ()
    # The fields that must be set for the value to be structured (a subclass
    # may have optional ones, e.g. a cycle's ``last``).
    _REQUIRED: ClassVar[tuple[str, ...]] = ()

    def _set(self) -> list[str]:
        return [name for name in self._STRUCTURE if getattr(self, name) is not None]

    @property
    def structured(self) -> bool:
        """True when the value carries its structure (not text only, not
        redacted)."""
        return not self.redacted and all(
            getattr(self, name) is not None for name in self._REQUIRED
        )

    def _check_value(self) -> None:
        """Shared rules: a redacted value carries no structure; a value with
        no structure is text only and needs its text; a structured value has
        every required field."""
        name = type(self).__name__
        set_fields = self._set()
        if self.redacted:
            if set_fields:
                raise ValueError(
                    f"a redacted {name} carries no structure; set: {set_fields}"
                )
            return
        if not set_fields:
            if not self.text.strip():
                raise ValueError(
                    f"a {name} needs its structure, printed text, or redacted; "
                    "use null for a value that is not there"
                )
            return
        missing = [f for f in self._REQUIRED if getattr(self, f) is None]
        if missing:
            raise ValueError(f"a {name} is missing {missing}")


class LabelValue(_Value):
    """An epoch or visit: free text. The text is the value."""

    @model_validator(mode="after")
    def _check(self) -> "LabelValue":
        if not self.redacted and not self.text.strip():
            raise ValueError(
                "an epoch or visit needs its text, or redacted; use null for a "
                "value that is not there"
            )
        return self


class TimingValue(_Value):
    """A scheduled time, in printed day (week, hour …) numbers.

    - a point: ``{value: 1, unit: "days"}`` (``Day 1``);
    - a range: ``{start: -28, end: -1, unit: "days"}`` (``Day -28 to Day -1``)
      — the visit falls anywhere in the span; how that is stored in USDM is
      ``usdm4``'s business (U4-35).
    """

    value: int | None = None
    start: int | None = None
    end: int | None = None
    unit: Unit | None = None

    _STRUCTURE: ClassVar[tuple[str, ...]] = ("value", "start", "end", "unit")

    @property
    def structured(self) -> bool:
        if self.redacted or self.unit is None:
            return False
        return self.value is not None or self.start is not None

    @property
    def is_range(self) -> bool:
        return self.start is not None

    @model_validator(mode="after")
    def _check(self) -> "TimingValue":
        if self.redacted or not self._set():
            self._check_value()
            return self
        if self.unit is None:
            raise ValueError("a timing needs its unit")
        point = self.value is not None
        range_ = self.start is not None or self.end is not None
        if point and range_:
            raise ValueError(
                "a timing is a point (value) or a range (start, end), not both"
            )
        if not point and not range_:
            raise ValueError("a timing needs a value, or a start and an end")
        if range_:
            if self.start is None or self.end is None:
                raise ValueError("a time range needs both its start and its end")
            if self.end < self.start:
                raise ValueError(
                    f"a time range's end ({self.end}) is before its start "
                    f"({self.start})"
                )
        return self


class WindowValue(_Value):
    """A window: ``{before: 3, after: 3, unit: "days"}`` (``±3 days``), both
    distances from the scheduled time, never negative."""

    before: int | None = None
    after: int | None = None
    unit: Unit | None = None

    _STRUCTURE: ClassVar[tuple[str, ...]] = ("before", "after", "unit")
    _REQUIRED: ClassVar[tuple[str, ...]] = ("before", "after", "unit")

    @model_validator(mode="after")
    def _check(self) -> "WindowValue":
        self._check_value()
        for name in ("before", "after"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"a window's {name} may not be negative ({value})")
        return self


class CycleValue(_Value):
    """A cycle: ``{first: 2, last: 2}`` a single cycle, ``{first: 1, last: 6}``
    a range, ``{first: 3, last: null}`` open-ended (``Cycle 3+``)."""

    first: int | None = None
    last: int | None = None

    _STRUCTURE: ClassVar[tuple[str, ...]] = ("first", "last")
    _REQUIRED: ClassVar[tuple[str, ...]] = ("first",)

    @property
    def is_range(self) -> bool:
        return self.last is None or self.last != self.first

    @model_validator(mode="after")
    def _check(self) -> "CycleValue":
        self._check_value()
        if self.first is not None and self.first < 0:
            raise ValueError(f"a cycle number may not be negative ({self.first})")
        if self.first is not None and self.last is not None and self.last < self.first:
            raise ValueError(
                f"a cycle range's last ({self.last}) is before its first ({self.first})"
            )
        return self


class QuantityValue(_Value):
    """A cycle length: ``{value: 21, unit: "days"}``. Never zero."""

    value: int | None = None
    unit: Unit | None = None

    _STRUCTURE: ClassVar[tuple[str, ...]] = ("value", "unit")
    _REQUIRED: ClassVar[tuple[str, ...]] = ("value", "unit")

    @model_validator(mode="after")
    def _check(self) -> "QuantityValue":
        self._check_value()
        if self.value is not None and self.value <= 0:
            raise ValueError(f"a cycle length must be more than 0 ({self.value})")
        return self


class DelayValue(_Value):
    """A variable delay (R8, U4-10): ``{min: 2, max: 10, unit: "days"}``
    (``Washout 2-10 days``). ``max`` null: no printed maximum. Accepted and
    carried; built by R8."""

    min: int | None = None
    max: int | None = None
    unit: Unit | None = None

    _STRUCTURE: ClassVar[tuple[str, ...]] = ("min", "max", "unit")
    _REQUIRED: ClassVar[tuple[str, ...]] = ("min", "unit")

    @model_validator(mode="after")
    def _check(self) -> "DelayValue":
        self._check_value()
        if self.min is not None and self.min < 0:
            raise ValueError(f"a delay's min may not be negative ({self.min})")
        if self.min is not None and self.max is not None and self.max < self.min:
            raise ValueError(
                f"a delay's max ({self.max}) is less than its min ({self.min})"
            )
        return self


class HeaderNote(_Model):
    """A further header row kept as text only — a second timing row, a timing
    clarification, an unassigned row. Never read."""

    role: str
    text: str


class ColumnInput(_Model):
    """One column of the schedule, in document order. Footnote markers sit
    on the value they are printed on, not on the column (issue 64)."""

    id: str
    epoch: LabelValue | None = None
    visit: LabelValue | None = None
    cycle: CycleValue | None = None
    cycle_length: QuantityValue | None = None
    timing: TimingValue | None = None
    window: WindowValue | None = None
    delay: DelayValue | None = None
    notes: list[HeaderNote] = []

    @model_validator(mode="after")
    def _check(self) -> "ColumnInput":
        if not self.id.strip():
            raise ValueError("a column id may not be blank")
        if self.delay is not None and (
            self.timing is not None or self.window is not None
        ):
            raise ValueError(
                f"column {self.id!r}: a delay has no anchored time, so no timing "
                "or window on the same column"
            )
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
    """One timeline — ``AssemblerInput.soa`` is a list of these. Replaced
    ``TimelineInput`` in issue 63; structured in issue 73."""

    type: TimelineType
    title: str | None = None
    description: str | None = None
    entry_condition: str | None = None
    attaches_to: str | None = None
    # Whether the protocol numbers a Day 0 (U4-35). Default: Day 1, no Day 0
    # — ``Day -1`` is the day before ``Day 1``.
    day_zero: bool = False
    classification: TimelineClassification = TimelineClassification()
    # Header field -> the row's printed label ("Days from randomization").
    # Carried for analysis; never read.
    rows: dict[str, str] = {}
    columns: list[ColumnInput] = []
    activities: list[ActivityInput] = []
    footnotes: list[FootnoteInput] = []

    @property
    def family(self) -> str:
        return family_of(self.type)

    @model_validator(mode="after")
    def _check_references(self) -> "ScheduleTimelineInput":
        unknown_rows = sorted(set(self.rows) - set(HEADER_FIELDS))
        if unknown_rows:
            raise ValueError(
                f"rows keys must be header fields {list(HEADER_FIELDS)}; "
                f"unknown: {unknown_rows}"
            )

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
