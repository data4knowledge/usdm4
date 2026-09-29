# Timeline assembler — specification

The contract and rules for `TimelineAssembler`: what a caller sends, and what USDM comes
back. Current as of 2026-09-27 (issues 63–76). How each issue was built is in the session
log, `docs/next_steps.md`; open problems are in `docs/issues.md`. Decisions are numbered
`U4-<n>` and listed in § 6.

## 1. What the assembler is for

`TimelineAssembler` turns a description of a Schedule of Activities into USDM:
`ScheduleTimeline`, `StudyEpoch`, `Encounter`, `ScheduledActivityInstance`,
`ScheduledDecisionInstance`, `Timing`, `Activity` and `Condition`.

It has more than one caller. `usdm4_protocol` uses it after reading a protocol PDF.
Other code can use it directly to create timelines. So the input is a public
contract: it must be easy for another program to generate, strict enough to test,
and complete enough that nothing a schedule prints is lost on the way in.

### The division of work

- **The caller decides what is printed and how it is organised.** Which columns form
  a timeline and of what type, which header row is the visit and which is the cycle,
  which cells are marked, which footnote applies where, and the structure of every
  value. That is judgement. In `usdm4_protocol` it may use AI.
- **The assembler turns that into USDM by fixed rules.** Same input, same USDM, every
  time. No AI, no guessing. A wrong rule is a bug, proven and fixed by a unit test in
  this repo.

The line between them is the input schema (§ 2). The assembler never reads printed
text (U4-35); printed text is carried only as labels. Two callers that state the same
structure get the same USDM through the same code.

## 2. The input schema

`AssemblerInput.soa` is a list of timelines (`ScheduleTimelineInput`,
`src/usdm4/assembler/schema/schedule_timeline_schema.py`):

```yaml
soa:
  - type: main                 # § 2.1
    id: main                   # optional; needed when a later timeline copies a column (U4-37)
    title: "Schedule of Activities"            # optional, becomes the label
    description: null                          # optional prose
    entry_condition: null      # printed text; any type (R1)
    attaches_to: null          # activity name; profile timelines (R7)
    day_zero: false            # does the protocol number a Day 0? default Day 1 (U4-35)
    classification:            # optional; emitted as d4k extensions
      orientation: null
      unit: null
      placement: null
    rows:                      # header field -> the row's printed label; carried, never read
      timing: "Days from randomization"
    columns:                   # document order
      - id: c1                 # caller's key, unique within the timeline
        epoch:   {text: "Screening"}
        visit:   {text: "V1", markers: [a]}           # markers on the value
        timing:  {text: "≤28", start: -28, end: -1, unit: days}   # a range
        notes:   []            # further header rows, text only (§ 2.2)
      - id: c4
        epoch:   {text: "On-Treatment"}
        visit:   {text: "D8"}
        cycle:   {text: "Cycle 1", first: 1, last: 1}
        cycle_length: {text: "Cycle = 21 days", value: 21, unit: days}
        timing:  {text: "D8", value: 8, unit: days}
        window:  {text: "(±3 days)", before: 3, after: 3, unit: days}
      - id: c5
        epoch:   {text: "CCI", redacted: true}        # redacted
        visit:   {text: "Visit 5"}
        timing:  {text: "[CCI]", redacted: true}
      - id: c6
        epoch:   {text: "Wash-out"}
        visit:   {text: "(7-28 days between doses)"}
        delay:   {min: 7, max: 28, unit: days}        # a gate (R8); no timing or window
    activities:                # body rows, document order
      - name: "Informed consent"   # as printed
        parent: null               # name of the grouping row, or null
        markers: [a]               # footnote markers on the name
        bcs: []                    # biomedical concept names
        cells:                     # one per non-empty cell
          - {column: c1, text: "X", markers: []}
    footnotes:
      - {marker: a, text: "ICF must be signed before any study procedure."}
  - type: early_termination
    id: et
    columns:
      - id: c1
        visit:  {text: "ED"}
        copy_of: {timeline: main, column: c14}        # same visit as main's c14 (U4-37)
```

### 2.1 Timeline type

The caller states the type. The family is derived from it, never supplied.

| family | types |
|---|---|
| planned | `main`, `extension_study`, `continued_access`, `follow_up` |
| variant | `arm`, `cohort` |
| conditional | `unscheduled`, `early_termination`, `adverse_event` |
| profile | `profile` |
| unclassified | `unclassified` |

Exactly one timeline in a study design carries `mainTimeline`: the first `main`, or
the first timeline if none is `main`. The family extension (TLF) is emitted for
`profile` timelines only, value `profile` — downstream readers take its presence to
mean "profile". Orientation, unit and placement are emitted when given. The type is
emitted on every timeline as extension 016 (TLT), value the input type (#77), for
debugging and assessing typing; nothing in the build reads it.

`follow_up` (#77) is a post-treatment follow-up schedule printed as its own table: timed
from the end of treatment or the last dose, entered by every participant who completes
or stops treatment. It is not `continued_access`, which gives the study drug.

### 2.2 Values: structured, with the printed text carried (U4-35)

Turning printed text into structure is the caller's job (`usdm4_protocol`, which may
use AI; `protocol_corpus`'s ground truth; any algorithmic source). Every value carries
`text`, `markers` and `redacted` beside its structure:

| value | structure | example |
|---|---|---|
| epoch, visit | the text is the value | `{text: "Screening"}` |
| timing, point | `value`, `unit` — the printed number | `{value: 1, unit: days}` |
| timing, range | `start`, `end`, `unit` — printed numbers | `{start: -28, end: -1, unit: days}` |
| window | `before`, `after`, `unit` — distances, never negative | `{before: 3, after: 3, unit: days}` |
| cycle | `first`, `last` (`null` open-ended; `first == last` a single cycle) | `{first: 3, last: null}` |
| cycle length | `value > 0`, `unit` | `{value: 21, unit: days}` |
| delay (R8) | `min`, `max` (optional, `≥ min`), `unit`; no timing or window on the column | `{min: 2, max: 10, unit: days}` |

- **Units** are `minutes | hours | days | weeks | months | years`, nothing else.
- **Day numbers are as printed.** `usdm4` applies the Day 0 rule from the timeline's
  `day_zero` flag (default Day 1). A `Day 0` timing with the flag at Day 1 is a
  warning; the flag is used.
- **A range is not a window**: the visit falls anywhere in the span. How it is stored
  in USDM (a timing at its start, a window forward to its end — `Timing` has no range)
  is `usdm4`'s business, Day 0 arithmetic included.
- **`text`** is the source as printed, for debug and after-the-event analysis. Never
  read or interpreted; its one use is as a label, copied verbatim into USDM. Empty when
  the caller structured the value from an algorithmic source — the label is then
  rendered from the structure (`Day 1`, `-3..+3 days`, `Cycle 3+`).
- **Text only.** A value with text and no structure states the caller could not
  structure it. Carried as the label, never read, warned; a text-only timing is a
  zero timing plus a warning (R4.5, U4-3).
- **`redacted: true`** states the sponsor printed `CCI` in place of the value. The
  structured fields must then be empty. Printed `CCI` not flagged is text.
- **Validation** refuses a partly structured value, a redacted value with structure,
  an empty value (use `null`), an unknown unit or key.
- **`markers`** are the footnote markers printed on this value (`Visit 3^1,2` →
  `["1", "2"]`). A column carries no markers of its own.

`rows` (per timeline) maps a header field to the row's printed label. Keys are the six
header fields; anything else is refused. Carried for analysis, never read.

`notes` holds every further header row the caller keeps — a second timing row, a
timing clarification, an unassigned row — as `{role, text}`. Text only; never read.

### 2.3 What the schema deliberately leaves out

- **Logical tables.** Joining page fragments into tables and splitting a table into
  timelines is the caller's judgement. The assembler only ever sees timelines.
- **Copies by id.** Column ids are scoped to one timeline; a shared id means nothing.
  A column printed in two timelines (a combined `EOT/ET` column) appears in both, and
  the later one names the original with `copy_of` (U4-37). `check_copies` requires the
  original to be in an earlier timeline, not itself a copy and not a gate.
- **Per-visit profile attachment.** `ScheduledActivityInstance.timelineId` is never
  set; a profile attaches to an activity (R7).

## 3. Structure

Four stages, each a module under `src/usdm4/assembler/timeline/`:

1. **Parse** (`columns.py`, `values.py`). Copy each validated, structured value into
   a typed value; build one column record per column. Pure functions, no USDM
   objects. A value sent as text only is a warning with the timeline, column and
   field and is not read; the timeline is still built.
2. **Plan** (`plan.py`). From the column records, the ordered sequence of nodes for
   one timeline — activity instance, start marker, gate, decision, end — each with its
   timing reference (which node it is measured from, `Before` / `After` / `Fixed
   Reference`, and the duration). Cycles and gates live entirely here. Pure,
   unit-tested without the builder.
3. **Build** (`build.py`). Turn the plan into USDM objects through the builder:
   epochs, encounters, instances, timings, the timeline, its exit, conditions. Objects
   are created in a fixed order (epochs, encounters, activities, instances, timings,
   cell links, conditions, timeline) because the builder numbers ids per class as they
   are made — the order is part of the output.
4. **Naming** (`naming.py`). House names for epochs, activities, instances
   (`C2D8`, `C3+D1`), decisions (`C3+DEC`), gates (`GATE1`) and ends (`T1-END`).

`TimelineAssembler` (`src/usdm4/assembler/timeline_assembler.py`) is the orchestrator.
Its public surface is fixed by three callers: `Assembler` calls `execute` and `clear`;
`StudyDesignAssembler` reads `epochs`, `encounters`, `activities` and `timelines` (its
study cells look epochs up by `label`, upper-cased); `StudyAssembler` reads
`conditions`, `biomedical_concepts` and `biomedical_concept_surrogates`. Profile
attachment (R7) is a pass after every timeline is built.

**Failure policy.** A timeline is always built if at all possible (U4-17). A value sent
as text only never stops it: the value is not read and a warning is reported once with
its location. A timeline is not built only when it has no columns, and is then
reported. Once building, a timeline is built whole or not at all: its epochs,
encounters and conditions are added only when the whole timeline has built; activities
are shared and stay registered.

## 4. The rules

### R1 — timeline

Each input timeline becomes a `ScheduleTimeline`: `name` `TIMELINE-<n>` (ordinal in
the input, gaps kept when a timeline is not built), `label` from `title` or a default,
`entryId` the first node, one `ScheduleTimelineExit`. `mainTimeline` and extensions per
§ 2.1. `entryCondition` (#77): the printed `entry_condition`, trimmed, for any type.
With none printed, the default for the type, with a warning except for `main`:

| type | default |
|---|---|
| `main` | `Subject identified` |
| `extension_study` | `Entered extension study` |
| `continued_access` | `Eligible for continued access` |
| `follow_up` | `Completed or discontinued treatment` |
| `arm` | `Assigned to arm` |
| `cohort` | `Assigned to cohort` |
| `unscheduled` | `Unscheduled visit` |
| `early_termination` | `Early termination` |
| `adverse_event` | `Adverse event` |
| `profile` | `Activity performed` |
| `unclassified` | `Entry condition not stated` |

The family decides how a timeline is built, not whether it has an entry condition.

### R2 — epochs

One `StudyEpoch` per distinct epoch text, identity trimmed and case-folded, named by
`naming.py` from the C99079 house terms. A column with no epoch builds no epoch and its
instance's `epochId` is `None` (U4-6). A cycle is never an epoch. A redacted epoch has
no text to tell one from another, so a consecutive run of redacted columns is one epoch
and a redacted run after a non-redacted epoch is a new one, named with an ordinal
(`CCI`, `CCI2`); a column with no epoch ends a run (U4-13).

### R3 — encounters, instances and cells

One `ScheduledActivityInstance` per column, in column order, labelled with the timing
text (or visit text where there is no timing), named by `sai_name` using the cycle and
day where there is one (`C2D8`). One `Encounter` per column, labelled with the visit
text — except a gate column (none, R8) and a copy (the original's, R6). An instance's
`activityIds` are the activities with a cell in its column. Activities are shared
across timelines by trimmed, case-folded name (U4-12). A cell's printed text stays on
the input (U4-9); its markers link to footnotes (R9). A redacted timing or visit is
never used in an instance name; with both redacted the name is positional
(`T1-SAI-3`). Instances in a second period or a copied timeline are named by
de-duplication (`D1-2`, `ED-2`) — `docs/issues.md` N3.

### R4 — timing

1. **Anchor** (U4-2). The first column, in column order, whose timing point is ≥ 0 in
   any unit — screening runs negative, the first event is `Day 0`, `Day 1`, `Week 0`,
   `Month 0`. In a cycle column the timing is the day within the cycle, so this lands on
   Cycle 1 Day 1 with no rule of its own. No such column → the first column, with a
   warning. The anchor is the `Fixed Reference`. A timeline whose values restart (a
   second `Day 1` after later days) with no gate before it is warned. After a gate each
   period has its own anchor (R8, U4-36).
2. **Duration** from the structured timing: point minus anchor in the column's unit,
   with the crossing-zero rule for days — Day 0 taken from the `day_zero` flag (U4-35),
   so with no Day 0, `Day -1` to `Day 1` is 1 day.
3. **Cycle columns** are measured from their cycle's `Day 1` by (day − 1), with the
   crossing-zero rule (`Day -1` predose is one day before `Day 1`, U4-24). Cycle 1's
   `Day 1` is Day 1 of the timeline, from the anchor; cycle *n*'s `Day 1` is `After`
   cycle *n* − 1's `Day 1` by cycle *n* − 1's length, converted only where exact (U4-27).
   A cycle with no printed `Day 1` column gets a start marker `C{n}D1` — an instance
   with no encounter and no activities (U4-22). A `Day 1` that cannot be chained (no
   readable length for cycle *n* − 1) is a zero timing, warned (U4-23). The day is read
   from `timing` only, never `visit` (U4-26).
4. **Windows** from the structured window: `windowLower`, `windowUpper` as ISO 8601
   durations, `windowLabel` the printed text (rendered when there is none).
5. **Timing sent as text only, or redacted** (U4-3): a zero timing (`PT0M`, `After`
   the previous column — `Before` the next when it precedes the anchor), `valueLabel`
   the printed text or `""`, and a warning naming the column. Never a guessed number.
   In a timeline with no readable timing the first column is the Fixed Reference.
6. **Mixed units.** A column whose timing unit differs from the anchor's is warned and
   timed by its absolute value. Conversion where exact (weeks to days, hours to
   minutes) is used for cycle lengths only — `docs/issues.md` N12.

### R5 — cycles

Nothing is ever expanded. A cycle has a length, a number or range, and days.

- **Single cycle** (`Cycle n`). Its columns are ordinary instances in the chain,
  timed per R4.3.
- **Range** (`Cycle n-m`, `Cycle n+`). The run of adjacent columns with the same range
  is one pass of the cycle. After its last day:
  1. **a delay** — a `Timing` placing the decision after the last day: cycle length
     minus the last day's offset within the cycle (21-day cycle, last day `Day 15`:
     21 − 14 = 7 days);
  2. **a decision** — a `ScheduledDecisionInstance` (`C3+DEC`), in the range's epoch,
     whose one `ConditionAssignment` is the exit condition `cycle exit condition`
     (U4-7) and leads to the next instance, and whose `defaultConditionId` loops back
     to the range's first node — its start marker, else its first column, so a predose
     `Day -1` printed before `Day 1` is inside the loop.
- **Mixed** — single cycles then a range (`Cycle 1`, `Cycle 2`, `Cycle 3+`) — is the
  common case; the range's `Day 1` chains from the previous cycle's (R4.3). A single
  cycle and a range with the same first cycle share one cycle slot.
- **Range as the last column.** A decision cannot target the timeline exit, so an end
  instance (`T1-END`) is added after the decision — no encounter, no activities —
  carrying the exit. The decision's exit branch leads to it.
- **No readable cycle length.** The loop is still built; the length is the largest day
  printed in the range (`D1`, `D8`, `D15` → 15 days), warned — a lower bound (U4-8).
  A length that does not convert exactly, or a last day beyond the length: zero delay,
  warned.

### R6 — conditional timelines and copies

A conditional timeline (`unscheduled`, `early_termination`, `adverse_event`) is a
sibling `ScheduleTimeline`; `entryCondition` as R1.

A column that names an original with `copy_of` gets its own instance, timing and
activities but shares the original's `Encounter` (U4-5, U4-37). If the printed visit
text differs, the original's label is kept, warned (U4-30). Original not built: the
copy gets its own `Encounter`, warned.

### R7 — profile timelines

A `profile` timeline with `attaches_to` is attached at `Activity.timelineId` of the
named activity (matched by U4-12 identity), in a pass after every timeline is built.
Not attached, profile built unattached: no `attaches_to` or an unknown name (warning);
a parent activity (error, DDF00160, U4-32); an activity already taken by an earlier
profile (error, U4-34); an attachment that would make a loop through the profiles
(error, U4-31). An activity scheduled on no other timeline is attached, with a warning
(U4-33). A profile's timings are relative to its own anchor (usually `Hour 0` /
`Minute 0`).

### R8 — gates

A gate is a variable delay between two anchored periods — `Washout 7-28 days`: wait at
least 7 days, move on when washed out, at most 28. It is not a window (a tolerance
around an anchored offset) and not a timing anchored to Day 0 (`Screening ≤28 days`,
`Run-in 2 weeks` are ordinary R4 timings). The caller marks it by sending a structured
`delay` on the column (no timing, no window); a delay sent as text only is warned and
the column is ordinary.

Built with R5's loop construct (U4-10):

1. **the gate instance** `GATE{n}` — the gate column itself, no `Encounter`, labelled
   with the delay as printed, in the column's epoch, carrying its cells' activities;
   `After` the previous node by zero;
2. **a decision** `GATE{n}DEC`, `After` the gate by 1 day, whose default loops back to
   the gate and whose one condition, `≥ 7 days and washed out, or 28 days` (no `max` →
   no `, or …`), leads to the next column;
3. **an end instance** `GATE{n}END` when the gate is the last column, as R5.

The period after a gate gets a new anchor at its `Day 1` — a second `Fixed Reference`,
with no timing back to the gate; the gap is the variable delay and the periods are
linked by the decision's exit (U4-36). One timeline covers both periods (U4-14
withdrawn). A gate with nothing before it is a Fixed Reference, warned.

### R9 — footnotes

Markers on header values (any field; a marker on two values of one column links once),
activity names and cells link footnotes to instances and activities. A footnote whose
marker is found becomes a `Condition` with its text verbatim and `contextIds` /
`appliesToIds` from where the marker was found. An unanchored footnote is dropped and
counted, never created without an anchor; a per-timeline summary line reports
`in / referenced / aligned / dropped_no_ref / dropped_no_match`. Never resolved into
logic.

## 5. The expander

`src/usdm4/expander/` walks a built timeline and lists what happens to a subject, day by
day. It is illustrative: one way a USDM timeline can be executed, not the only one, and
nothing normative follows from its output (U4-11). Nothing that builds USDM from a
protocol calls it.

- **Walk.** Iterative, with a step limit (`STEP_LIMIT`, 10,000) that ends any loop the
  rules below do not, as an error.
- **Loops.** A decision with one condition whose branch leads to an instance already
  reached is a loop. No readable minimum: back the first time, out the second — the
  loop is run twice, so the decision goes each way once. A minimum read from
  `≥ N <unit>` / `>= N <unit>` (a month 30 days, a year 365): out once the time since
  the loop start's first pass reaches it. A `days <op> n` condition keeps its own test.
- **Every repeat is shown**, never collapsed: a 7-day minimum on a 1-day loop gives seven
  timepoints for the gate, passes 1–7. Each timepoint carries `pass_number`
  (`"pass"` in `to_dict`).
- **Time.** An instance's time is its timing chain to its Fixed Reference plus a shift.
  The shift moves when a decision leads back into a loop (the loop start falls at the
  decision's time) and when an instance hangs from a different anchor than the last
  (period 2 after a gate starts at the decision's time).
- **Sub-timelines** are timed from the calling instance: its time plus the chain.
- **Accepted as is.** A loop whose start is a predose `Day -1` gets its second pass a
  day late.

## 6. Decisions

Each taken by Dave on the date given, unless marked as Claude's call. Superseded and
withdrawn decisions are kept, one line each, so the question isn't asked again.

| id | decision | outcome |
|---|---|---|
| U4-1 | Names of the new schema classes and fields | **Taken 2026-09-25:** `ScheduleTimelineInput`, `ColumnInput`, `HeaderValue`, `HeaderNote`, `ActivityInput`, `CellInput`, `FootnoteInput`, `TimelineClassification`. `HeaderValue` was replaced by the value objects of U4-35 (#73); fields as in § 2 |
| U4-2 | The anchor rule | **Taken 2026-09-25:** today's rule — first column with a timing point ≥ 0, else the first column with a warning; no code beyond the warning (R4.1). Checked against 72 drafted tables: `Week 0` and cycle tables anchor correctly under it; a narrower "`Day 1` or `Day 0`" rule was rejected (misses `Week 0`, needs cycle parsing, no better fallback) |
| U4-3 | Form of a timing with no readable value (no pattern, printed text unreadable, or redacted) | **Taken 2026-09-25:** a zero timing (`PT0M`) from the previous column, printed text as `valueLabel`, and a warning — nothing more. **Rejected:** an extension flag (Dave: no flags); measuring from the anchor (puts ED at Day 1 in the expander); no `Timing` (DDF00060 needs a duration, and the expander crashes on a missing one) |
| U4-4 | A time range (`Day -28 to Day -1`) | **Superseded by U4-35 (#73):** sent as `timing: {start, end, unit}`; stored as the timing at its start and a window forward to its end |
| U4-5 | A copied column: one `Encounter` shared by both timelines, or one each | **Taken 2026-09-26; built #75 (2026-09-27):** one shared `Encounter`; each timeline has its own `ScheduledActivityInstance`, so timing and activities can differ. A shared column id does not mean a shared visit (ids are scoped to one timeline, and the pins reuse `c1` for different visits), so the copy is named explicitly (U4-37). **Rejected:** ids spanning the assembly (silent merges from every existing caller); matching on id plus printed text (a guess) |
| U4-6 | A column with no epoch | **Taken 2026-09-27 (Dave, #75):** no epoch sent, no `StudyEpoch` built and the instance's `epochId` is `None` — a subsidiary timeline rarely links to epochs. **Was (proposal, never built):** inherit the previous column's; none on the first column an error. Before #75 an empty-label epoch was built |
| U4-7 | The exit condition text on a cycle loop | **Taken 2026-09-26 (Dave):** the fixed text `cycle exit condition`. **Noted, not crucial now:** the real exit rule (e.g. progression, unacceptable toxicity) is usually in the protocol body, not the SoA; finding it needs a search wider than the SoA. **Rejected:** printed range text (a heading, not a condition); caller-supplied text (no field in the frozen schema) |
| U4-8 | A range with no readable cycle length | **Taken 2026-09-26 (Dave):** the loop is built; the cycle length is the largest day number printed in the range (`D8` → 8 days, `D15` → 15 days), with a warning. It is a lower bound: the real length (21, 28 days) is usually longer. **Noted, not crucial now:** the true length may be stated outside the SoA; finding it needs a wider search. **Open edge:** a range printing only `Day 1` gives a 1-day cycle — settle when R5 hits it. **Rejected:** a text-only delay (DDF00060 needs a duration; the expander crashes, as U4-3). Ranges only; U4-23 (single cycles) is unchanged |
| U4-9 | Where a cell's printed text goes (`X`, `(X)`, `Predose`) | kept on the input only until a rule needs it |
| U4-10 | The gate loop (R8) | **Reframed 2026-09-26 (Dave):** a gate is a variable delay, built as R5's delay + decision loop; recognising it (duration, no anchored offset, between anchored columns) is not in question. **(a) Taken 2026-09-26 (Dave):** start node → 1-day delay → decision. The decision's condition is "≥ min days and washed out" (e.g. `≥ 2 days and washed out`) and exits to the next column; the default loops back to the start node. The minimum lives in the condition, not the delay; the start node is an instance with no visit (as the cycle start marker, U4-22). **(b) Taken 2026-09-26 (Dave):** the maximum is in the exit condition — `(≥ 2 days and washed out) or 10 days`; no second branch. **(c) Taken 2026-09-27 (Dave):** the exit condition text is filled from the delay — `≥ {min} {unit} and washed out, or {max} {unit}` (`≥ 7 days and washed out, or 28 days`); with no `max`, the `, or …` part is dropped. **Was:** "gate versus window in text alone" — wrong framing |
| U4-11 | How the expander presents a loop | **Taken 2026-09-27 (Dave):** a loop is run twice, so the decision goes each way once — back, then out (`Cycle 3+`: cycle 3, cycle 4, then on). A washout gate whose minimum can be read is run until the minimum has passed, then left. The expander is illustrative, not normative. Claude's, in the issue text: the minimum read from `≥ N <unit>` / `>= N <unit>`; each timepoint carries its pass number. As built: session log, #76 |
| U4-12 | Activity identity across timelines when names differ only by spacing or hyphenation | exact trimmed, case-folded match, as today |
| U4-13 | How redacted (`CCI`) epochs group | **Taken 2026-09-25 (issue 64):** a consecutive run of redacted columns is one epoch; a run after a non-redacted epoch is a new one, named with an ordinal (`CCI`, `CCI2`) |
| U4-14 | Crossover periods whose day numbering restarts | **Withdrawn 2026-09-27 (#74):** one timeline; the period after a gate has its own anchor (U4-36). Rejected: one timeline per period linked by an instance (a `Timing` cannot cross timelines, DDF00046) |
| U4-15 | A bare number with no unit | **Superseded by U4-35 (#73):** the caller sends the unit |
| U4-16 | A window printed in the timing cell and in the window field | **Superseded by U4-35 (#73):** the caller sends one window |
| U4-17 | A value the assembler cannot use | **Taken 2026-09-25 (#65), still standing:** always build the timeline if at all possible; the value is warned and not read (U4-3 for a timing). The pattern half is superseded by U4-35 |
| U4-18 | Printed `≤N` as a timing | **Superseded by U4-35 (#73):** the caller sends the range |
| U4-19 | Unit of a window printed with no unit | **Superseded by U4-35 (#73):** the caller sends the unit |
| U4-20 | Window length of a time range crossing zero (`Day -3 to Day 2`) | **Taken 2026-09-25 (#65):** the crossing-zero rule — 4 days with no Day 0, 5 with one (Day 0 from `day_zero`, U4-35) |
| U4-21 | Labels of a time range | **Taken 2026-09-25 (#65):** `valueLabel` the start (`Day -28`), `windowLabel` the window in pattern form (`-0..+27 days`), `Timing.label` the printed text (`≤28`) |
| U4-22 | A single cycle with no `Day 1` column | **Re-taken 2026-09-26 (#67; was: its columns measured from the anchor at (*n* − 1) × cycle length + (day − 1)):** every cycle has a `Day 1` node. With no printed `Day 1` column, a start marker is added before the cycle's first column — a `ScheduledActivityInstance` `C{n}D1` with no encounter and no activities, in that column's epoch; it is not a visit. The cycle's other columns are timed from it. When the anchor falls on a column of that cycle, the marker is the anchor |
| U4-23 | Cycle *n* > 1 with no readable cycle length | **Taken 2026-09-25 (R4 part 2); narrowed 2026-09-26 (#67):** the length that matters is cycle *n* − 1's (U4-27). When it cannot be read or converted exactly, or cycle *n* − 1 is not in the timeline, cycle *n*'s `Day 1` gets U4-3's zero timing and a warning; never a guessed number. Its other columns are still timed from that `Day 1`. The last cycle needs no length until R5's delay |
| U4-24 | A negative day inside a cycle (`Day -1` predose) | **Taken 2026-09-25 (R4 part 2):** today's crossing-zero rule — `Day -1` is one day before the cycle's `Day 1` |
| U4-25 | A cycle-range column before R5 | **Superseded by #69 (R5)** |
| U4-26 | Where a cycle column's day is read from | **Taken 2026-09-25 (R4 part 2):** the `timing` field only. A table printing the day in its visit row (`D1`) is stage 1's to assign to the timing role; `usdm4` never reads `visit` for timing |
| U4-27 | Cycle *n*'s `Day 1` | **Taken 2026-09-26 (Dave, #67):** a cycle starts at `Day 1`; cycle *n*'s `Day 1` is timed `After` cycle *n* − 1's `Day 1` by cycle *n* − 1's length — a chain. Cycle 1's `Day 1` is Day 1 of the timeline, timed from the anchor. #66 built (*n* − 1) × cycle *n*'s own length, right only when every cycle has the same length. (The example first recorded here, a length printed as `21 days (or 28 days …)`, is a length that differs by cohort, not between cycles; it is not read, U4-23) |
| U4-28 | Unit of a bare cycle length | **Superseded by U4-35 (#73):** the caller sends the unit |
| U4-29 | `entryCondition` of a conditional timeline with no printed `entry_condition` | **Replaced by #77 (R1).** Was, taken 2026-09-26 (Dave, #70): default text from the timeline type, with a warning — `unscheduled` → `Unscheduled visit`, `early_termination` → `Early termination`, `adverse_event` → `Adverse event`. **Rejected:** today's fixed `Paricipant identified` (says nothing about why the timeline is entered) |
| U4-30 | Label of a shared `Encounter` (U4-5) when the printed visit text differs between the copies | **Taken 2026-09-26 (Dave, #70); built #75.** The first timeline in input order sets the label (and the name, `T{t}-E{n}`); a warning names both texts. **Rejected:** the main timeline's text (an extra rule; main is almost always first) |
| U4-31 | A profile attachment that would make a loop (the attached activity is reached again through the profile it calls, directly or through another profile) | **Taken 2026-09-26 (Dave, R7):** not attached, reported as an error; the profile is built unattached. Sharing an activity between timelines is fine (U4-12 unchanged); a loop is not — they are different things. Checked over the whole attachment graph, not just the direct case |
| U4-32 | `attaches_to` names an activity with children | **Taken 2026-09-26 (Dave, R7):** not attached, reported as an error — DDF00160 forbids `timelineId` on a parent activity |
| U4-33 | `attaches_to` names an activity that exists but is scheduled on no other timeline | **Taken 2026-09-26 (Dave, R7):** attached, with a warning |
| U4-34 | Two profiles naming the same activity (`Activity.timelineId` holds one timeline) | **Taken 2026-09-26 (Dave, R7):** the first profile in input order is attached; each later one is not attached, reported as an error naming both profiles and the activity, and built unattached. **Rejected:** a warning only (hides a lost link); a made-up wrapper activity holding both (invents structure the protocol does not print) |
| U4-35 | Structured input — who turns printed text into structure | **Taken 2026-09-26 (Dave, from R8):** `usdm4` is algorithm only and never reads printed text; the caller (stage 1, may use AI; or an algorithmic source) supplies every header value as a structured object, e.g. `timing: {value: 1, unit: "days"}` (the printed day number — `usdm4` applies the crossing-zero rule), `window: {before: 3, after: 3, unit: "days"}`, `delay: {min: 2, max: 10, unit: "days"}`. Each value carries its source `text` for debug and after-the-event analysis — **never read or interpreted**; empty when the caller structured it from an algorithmic source. The one use: copied verbatim into USDM labels (`Timing.label`, instance and `Encounter` labels, `windowLabel`), as today (Dave, 2026-09-26). Empty `text` → the label is rendered from the structure (`Day 1`), as today's fallback to the pattern. Replaces the pattern grammar and the printed-text readers of #63–#71; supersedes the schema docstring's "a caller never hands over a number it has worked out from printed text". **Units (Dave, 2026-09-26):** `"minutes" | "hours" | "days" | "weeks" | "months" | "years"`, nothing else accepted; stage 1 normalises. **Cycle (Dave, 2026-09-26):** `{first: 3, last: null}` — `last: null` open-ended (`Cycle 3+`), `{first: 1, last: 6}` a range, `{first: 2, last: 2}` a single cycle (`first`/`last`, not `from`/`to` — `from` is a Python keyword). **Cycle length (Dave, 2026-09-26):** `{value: 21, unit: "days"}` — one `{value, unit}` type shared with the timing point; `value > 0` for a cycle length, a timing may be negative. **Time range (Dave, 2026-09-26):** a range is not a window — the visit falls anywhere in the span. The input says what the protocol says: `timing: {start: -28, end: -1, unit: "days"}` (printed day numbers). How it is stored in USDM (today: timing at the start, window forward to the end — `Timing` has no range) is `usdm4`'s business, as is the Day 0 arithmetic. The protocol_corpus issue 13 convention (range sent as start + window) is replaced. *(Briefly taken the same day as "no range form, stage 1 sends timing + window" — reversed: it pushed a USDM workaround into the input and the Day 0 arithmetic onto the callers.)* **Day 0 (Dave, 2026-09-26):** a timeline-level flag says whether the protocol numbers a Day 0; default Day 1 (no Day 0). Replaces inferring it from a printed `Day 0` column (`has_zero_timepoint`). A `Day 0` timing when the flag says Day 1 is a warning (Dave, 2026-09-26); the flag is used. **Redaction (Dave, 2026-09-26):** `redacted: bool = False` on every value object, replacing `pattern: "CCI"`; when true the structured fields are empty (refused otherwise) and `text` carries what was printed for the label; `usdm4` treats it as today (no timing, a warning). Nothing left open |
| U4-36 | Day numbering after a gate (R8) | **Taken 2026-09-27 (Dave):** the period after a gate gets a new anchor at its `Day 1`; its other columns (`Baseline PET`, `Day -1`, `Day 2`) are timed from it. DDF00009 asks for at least one anchor per timeline, so a second is allowed. An anchor is a Fixed Reference: no duration back to the gate — the gap is the variable delay; the periods are linked by the instance chain (the decision's exit) |
| U4-37 | How a copied column names its original (`protocol_corpus` N78, U4-5) | **Taken 2026-09-27 (Dave):** `ScheduleTimelineInput` gains an `id`; `ColumnInput.copy_of` is `{timeline, column}` — the original's timeline id and column id. A copy shares only the original's `Encounter` (the visit); it has its own instance, timing and activities, and normally no epoch — a subsidiary timeline rarely links to epochs. **Rejected:** referring to a timeline by its position in the input (breaks silently when a caller reorders timelines) |
