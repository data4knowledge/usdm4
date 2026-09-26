# Timeline assembler — design

**Status: 2026-09-26. Issues 63–68 merged** (cycle reading: bare ranges,
cycle length unit from the row labels, branch `68-cycle-and-ranges`). Built so far: the input schema
(§ 3), the pattern grammar incl. time ranges and cycles (§ 4), parse → plan → build →
naming (§ 5), R1–R3, R4 (timing, single cycles) and R9. R5–R8 are later issues. § 2
records the assembler as it was BEFORE issue 63; §§ 10–15 record what issues 63–68
built and the calls made on the way. Decisions are in § 9, taken one at a time; none is
open. The work order is in `timeline_assembler_plan.md`.

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
  which cells are marked, which footnote applies where. That is judgement. In
  `usdm4_protocol` it may use AI.
- **The assembler turns that into USDM by fixed rules.** Same input, same USDM, every
  time. No AI, no guessing. A wrong rule is a bug, proven and fixed by a unit test in
  this repo.

The line between them is the input schema (§ 3). **All parsing of text happens in the
assembler.** A caller never hands over a number it has worked out from printed text.
For each header value it hands over the printed text, the pattern form (§ 4), or
both; with both, the pattern is used. Two callers reading the same schedule must
reach the same timings through the same code.

## 2. Today (before issue 63)

One `TimelineInput` per timeline (`assembler/schema/timeline_schema.py`): six blocks —
`epochs`, `visits`, `timepoints`, `windows`, `activities`, `conditions` — plus
`table_*` classification fields. Epochs, visits, timepoints and windows are parallel
lists matched by column position. `timepoints` carry `value` and `unit` already parsed
by the caller; `windows` carry integer `before` / `after`.

`TimelineAssembler._execute_one` (`assembler/timeline_assembler.py`) runs, per
timeline: epochs → encounters → activities → timepoints → timing → link activities →
conditions → timeline. What that does and does not do:

- **Chain.** One `ScheduledActivityInstance` per column. `_add_timepoints` points each
  instance's `defaultConditionId` at the next column; `_add_timeline` points the last
  at a `ScheduleTimelineExit`. No `ScheduledDecisionInstance` is created anywhere in
  the assembler, builder or converter.
- **Timing.** `_find_anchor` picks the first non-blank column with a value ≥ 0. Every
  column gets one `Timing` relative to that anchor (`Before`, `Fixed Reference`,
  `After`); `_interval_from_anchor` is the difference in the column's unit, less one
  day when a day count crosses zero and the table has no Day 0. A column whose own
  value is non-numeric gets a zero duration with no error; if only the anchor's value
  is non-numeric, the column's absolute value is used. Mixed units give a warning and
  the absolute value.
- **Seen in the 63.1 pin (2026-09-25).** A column with empty timepoint text gets
  **no `Timing` at all**: `valueLabel` is required by the API and `_timing_value_label`
  returns `None`, so every timing of such a timeline fails and the timeline has
  instances but zero timings — two of the three real pinned schedules' main timelines.
  A caller unit the encoder does not know (`cycle`) gives a zero duration for every
  column; a `Day 30` after cycle columns falls to the mixed-units path and reads 30
  days after the anchor. An empty period text becomes an epoch with an empty label.
- **Epochs.** One per distinct period text (identity = trimmed, case-folded text);
  named from the C99079 house terms, uniqued by `_claim_epoch_name`.
- **Encounters.** One per column, never merged, labelled with the visit text.
- **Instances.** Labelled with the timepoint text only. `_sai_name` derives `D1`,
  `W12`, `C2D1` from the timepoint (or visit) text by regex, uniqued with a suffix —
  so `C2D1` appears only when the printed timepoint text says `Cycle 2 Day 1`.
- **Main timeline.** `_main_index` takes the first table whose `table_type` is
  `main_soa`, a missing `table_type` counting as `main_soa`; failing that, the first.
- **Classification.** `table_family`, `table_orientation`, `table_unit` and
  `table_placement` are caller-supplied and emitted as d4k extension attributes;
  `table_type` only steers the main flag.
- **Activities.** Shared across timelines by trimmed, case-folded name
  (`_activity_by_name`); house-style short names (`_activity_name`); BCs from
  `actions.bcs`, each also minting a `Procedure`.
- **Conditions.** Footnote markers on visits, activities and cells are collected in
  `_condition_links`; a footnote becomes a `Condition` only when its marker is found.
  Unanchored footnotes are dropped and counted.
- **Not done.** `ScheduledActivityInstance.timelineId` and `Activity.timelineId` are
  always `None`, so a profile is never attached. `plannedDuration` is always `None`.
  There is no field for a cycle, a cycle length, a second timing row or a timing
  clarification — they are lost before the assembler sees them.
- **Failure handling.** Every step is wrapped in `try/except` that logs and returns
  what it has, so a failure mid-timeline yields partial output.

The expander (`expander/`) walks a built timeline. It follows sub-timelines, and a
`ScheduledDecisionInstance` only when it has one assignment of the form
`days <op> <n>`; anything else is logged and the default path taken. On the main
timeline it resets the offset to 0, so a loop back to an earlier instance would
recompute the same tick each time.

## 3. The input schema

`TimelineInput` is retired for the schedule. `AssemblerInput.soa` becomes a list of
timelines in the shape below. Field names are a proposal (decision U4-1).

```yaml
soa:
  - type: main                 # § 3.1
    title: "Schedule of Activities"            # optional, becomes the label
    description: null                          # optional prose
    entry_condition: null      # printed text; conditional timelines (R6)
    attaches_to: null          # activity name; profile timelines (R7)
    classification:            # optional; today's table_orientation/unit/placement
                               # (table_family is no longer supplied — § 3.1)
      orientation: null
      unit: null
      placement: null
    rows:                      # header field -> the row's printed label (issue 64)
      timing: "Days from randomization"
    columns:                   # document order
      - id: c1                 # caller's key, unique within the timeline
        epoch:   {text: "Screening", pattern: "Screening"}
        visit:   {text: "V1", pattern: "V1", markers: [a]}  # markers on the value
        cycle:   null
        cycle_length: null
        timing:  {text: "≤28", pattern: "Day -28 to Day -1"}
        window:  {text: "", pattern: null}
        notes:   []            # further header rows, text only (§ 3.2)
      - id: c4
        epoch:   {text: "On-Treatment", pattern: "On-Treatment"}
        visit:   {text: "D8", pattern: "D8"}
        cycle:   {text: "Cycle 1", pattern: "Cycle 1"}
        cycle_length: {text: "Cycle = 21 days", pattern: "21 days"}
        timing:  {text: "D8", pattern: "Day 8"}
        window:  {text: "(±3 days)", pattern: "-3..+3 days"}
        notes:   []
      - id: c5
        epoch:   {text: "CCI", pattern: "CCI"}         # redacted (issue 64)
        visit:   {text: "Visit 5", pattern: "Visit 5"}
        timing:  {text: "[CCI]", pattern: "CCI"}
    activities:                # body rows, document order
      - name: "Informed consent"   # as printed
        parent: null               # name of the grouping row, or null
        markers: [a]               # footnote markers on the name
        bcs: []                    # biomedical concept names (today's actions.bcs)
        cells:                     # one per non-empty cell
          - {column: c1, text: "X", markers: []}
    footnotes:
      - {marker: a, text: "ICF must be signed before any study procedure."}
```

### 3.1 Timeline type

The caller states the type. The family is derived from it by the assembler, never
supplied.

| family | types |
|---|---|
| planned | `main`, `extension_study`, `continued_access` |
| variant | `arm`, `cohort` |
| conditional | `unscheduled`, `early_termination`, `adverse_event` |
| profile | `profile` |
| unclassified | `unclassified` |

Exactly one timeline in a study design carries `mainTimeline`: the first `main`, or
the first timeline if none is `main`. (Today's rule differs slightly: a table with no
`table_type` counts as main. In the new schema `type` is required, so that case goes.)
Type and family are emitted as d4k extension attributes on the `ScheduleTimeline`,
beside the orientation, unit and placement extensions. Today the caller supplies
`table_family`; from now it is derived from the type and never supplied.

### 3.2 Values: printed text and pattern form

Every header value is `{text, pattern, markers}`.

- `text` is what the document prints. It is used for labels, so the protocol's words
  survive into USDM.
- `pattern` is the same value in the pattern grammar (§ 4).
- **A caller may supply text only, pattern only, or both.** Each field (timing,
  window, and later cycle and cycle length) is read the same way: the pattern when
  there is one; else the printed text, read by the assembler; else nothing. With
  pattern only, the label defaults to the pattern.
- Printed text the assembler cannot read, with no pattern, gets no value: the text is
  carried and R4.5 applies (zero timing plus a warning).
- A `pattern` that is present and does not match the grammar raises a warning and is
  set aside; the field is then read from its printed text, else gets no value (U4-17).
- `pattern: "CCI"` states the sponsor redacted the value (issue 64). It is valid in
  every field and is not the same as `null`: the value exists and was withheld. Only
  the pattern states a redaction — printed `CCI` text with a `null` pattern is
  ordinary text.
- `markers` are the footnote markers printed on this value (`Visit 3^1,2` →
  `["1", "2"]`). A column carries no markers of its own; the value they are printed
  on does (issue 64).

`rows` (per timeline) maps a header field to the row's printed label — "Days from
randomization", "Visit interval tolerance (days)", "Planned Time [h:min]". The label
states the unit, the anchor and the clock format. Keys are the six header fields
(`epoch`, `visit`, `cycle`, `cycle_length`, `timing`, `window`); anything else is
refused. Carried, not yet read: R4 uses the anchor it states.

`notes` holds every further header row the caller keeps — a second timing row, a
timing clarification, an unassigned row — as `{role, text}`. Text only; the
assembler puts them on labels or descriptions and never parses them.

### 3.3 What the schema deliberately leaves out

- **Logical tables.** Joining page fragments into tables and splitting a table into
  timelines is the caller's judgement. The assembler only ever sees timelines.
- **Copies.** A column that belongs to two timelines (a combined `EOT/ET` column)
  appears in both, with the same `id`. What that means in USDM is decision U4-5.
- **Parsed numbers.** There are no `value`, `unit`, `before` or `after` fields.

## 4. The pattern grammar

Strict and small on purpose. One way to write each thing. Case-insensitive keywords,
single spaces, ASCII only — a window is written `-a..+b`, never with `±`.

| value | pattern | examples |
|---|---|---|
| timing, point | `<Unit> <int>` | `Day 1`, `Day -7`, `Week 12`, `Month 6`, `Year 2`, `Hour 4`, `Minute 30` |
| time range | `<Unit> <int> to <Unit> <int>` | `Day -28 to Day -1` |
| window | `-<int>..+<int> <units>` | `-3..+3 days`, `-0..+2 hours`, `-7..+0 days` |
| cycle, single | `Cycle <int>` | `Cycle 1`, `Cycle 2` |
| cycle, range | `Cycle <int>-<int>` or `Cycle <int>+` | `Cycle 1-6`, `Cycle 3+` |
| cycle length | `<int> <units>` | `21 days`, `4 weeks` |
| epoch, visit | free text, trimmed | `Screening`, `V1`, `D8` |
| any field, redacted | `CCI` | `CCI` |

`<Unit>` is one of Day, Week, Month, Year, Hour, Minute. `<units>` is its plural,
lower case.

Rules the grammar carries:

- **In a cycle column, `timing` is the day within the cycle.** `Day 8` in a column
  whose cycle is `Cycle 3` means C3D8. The printed `C3D8` stays in `text`. There is
  one way to write it.
- **An open-ended range is `Cycle n+`.** `Cycle 2-n`, `Cycle 2+`, `Cycles 2 and
  beyond` all become `Cycle 2+`; the printed words stay in `text`.
- **A time range** is a column whose scheduled time is a range (`-28 to -1`,
  `≤28`). The interface takes it in either form (U4-4): as a time range — printed text or
  range pattern — which `usdm4` decodes to the timing at its start and a window
  forward to its end; or already decoded, as a point plus a window, from a tool that
  holds decoded timings.

- **A redacted value is `CCI`** in any field, ignoring case. It is never parsed: no
  timing, no window, no guessed number. A later rule may supply a default.

Anything the grammar cannot express is `pattern: null`, stated by the caller.

## 5. Structure

The assembler is split into four stages. Each is its own module under
`assembler/timeline/` (proposal; the package layout is part of issue 63).

1. **Parse** (`grammar.py`, `columns.py`). Validate the input; parse every `pattern`
   into a typed value; build one column record per column. Pure functions, no USDM
   objects. A bad pattern or unreadable text is a warning with the timeline, column and
   field, and the field falls back (U4-17); the timeline is still built.
2. **Plan** (`plan.py`). From the column records, the ordered sequence of nodes for
   one timeline: activity instance, delay, decision, exit — each node with its timing
   reference (which instance it is measured from, `Before` / `After` / `Fixed
   Reference`, and the duration). Cycles live entirely here. Pure, unit-tested
   without the builder.
3. **Build** (`build.py`). Turn the plan into USDM objects through the builder:
   epochs, encounters, instances, timings, the timeline, its exit, conditions.
4. **Naming** (`naming.py`). House names for epochs, activities and instances, moved
   out unchanged with their state: `_house` (with `_HOUSE_NAMES_PATH` and the
   class-level cache), `_name_key`, `_epoch_name`, `_claim_epoch_name`, `_identity`,
   `_qualify`, `_activity_name`, `_initials`, `_significant_words` (with
   `_ACT_STOPWORDS`), `_sai_name` and `_sai_base_name` (with `_SAI_TEXT_PATTERNS`,
   `_UNIT_PREFIXES`, `_coerce_int`), and the three name registries.

`TimelineAssembler` stays as the orchestrator with the same public surface, because
three callers depend on it: `Assembler` calls `execute` and `clear`;
`StudyDesignAssembler` reads `epochs`, `encounters`, `activities` and `timelines` (its
study cells look epochs up by `label`, upper-cased); `StudyAssembler` reads
`conditions`, `biomedical_concepts` and `biomedical_concept_surrogates`.

**Failure policy.** A timeline is always built if at all possible (U4-17). A bad pattern
or unreadable printed text never stops it: the field falls back and a warning is
reported once with its location. A timeline is not built only when nothing can be
built — no columns — and is then reported. Once building, a timeline is built whole
or not at all; no step returns a partial result after an exception.

## 6. The rules

Numbered to match `protocol_corpus/docs/spec/soa_two_stage.md`.

### R1 — timeline

Each input timeline becomes a `ScheduleTimeline`: `name` `TIMELINE-<n>` (ordinal in
the input, gaps kept when a timeline is not built), `label` from `title` or a default,
`entryId` the first node, one `ScheduleTimelineExit`. `mainTimeline` per § 3.1. Type,
family and classification as extension attributes. *Today:* all of this except the
type extension; family is caller-supplied, not derived.

### R2 — epochs

One `StudyEpoch` per distinct epoch text, identity as today (trimmed, case-folded),
named by `naming.py`. Every instance carries its column's epoch. A column with no
epoch takes the previous column's epoch; the first column with none is an input
error (decision U4-6 confirms). A cycle is never an epoch. A redacted epoch (`CCI`)
has no text to tell one from another, so a consecutive run of redacted columns is
one epoch and a redacted run after a non-redacted epoch is a new one (U4-13).
*Today:* one epoch per distinct text, matched to columns by position; no
inheritance and no error for a missing epoch.

### R3 — encounters, instances and cells

One `ScheduledActivityInstance` per column, in column order, labelled with the timing
text (or visit text where there is no timing), named by `_sai_name` using the cycle
and day where there is one (`C2D8`). One `Encounter` per column, labelled with the
visit text. An instance's `activityIds` are the activities with a cell in its
column. The cell's printed text is kept (decision U4-9 for where); its markers link to
footnotes (R9). A redacted timing or visit is never used in an instance name; with
both redacted the name is positional (`T1-SAI-3`). *Today:* the same from positional lists and `visits[].index`, except
that the instance label is the timepoint text with no visit fallback, and `C2D1`
comes only from a regex on that text.

### R4 — timing

1. **Anchor.** Decision U4-2, taken 2026-09-25: today's rule. The anchor is the first
   column, in column order, whose timing point is ≥ 0 in any unit — screening runs
   negative, the first event is `Day 0`, `Day 1`, `Week 0`, `Month 0`. In a cycle
   column the timing is the day within the cycle, so this lands on Cycle 1 Day 1 with
   no rule of its own. No such column → the first column, **with a warning** (today
   it is silent). Durations are differences, so a late anchor (`Day 14` when nothing
   earlier is timed) moves only the Fixed Reference, not the intervals. A timeline
   whose values restart outside a cycle (a second `Day 1` after later days) is
   warned: it is two periods and should be two timelines (U4-14).
2. **Duration** from the pattern, else the printed text: point minus anchor in the column's unit, with
   today's crossing-zero rule for days kept exactly.
3. **Cycle columns** are measured from their cycle's `Day 1`, and that `Day 1` from
   the anchor (for a single cycle *n*: (*n* − 1) × cycle length after the first
   cycle's `Day 1`). This makes a chain of timings, which the expander already
   follows hop by hop.
4. **Windows** from the pattern, else the printed text: `windowLower`, `windowUpper`
   as ISO 8601 durations, `windowLabel` the printed text.
5. **No pattern and unreadable text, or redacted** → decision U4-3, taken 2026-09-25: a zero timing
   (`PT0M`, `After` the previous column — `Before` the next when it precedes the
   anchor), `valueLabel` the printed text or `""`, and a warning naming the column.
   Nothing more: no extension, no flag. Never a guessed number. In a timeline with
   no readable timing the first column is the Fixed Reference.
6. **Mixed units** are converted where exact (hours to minutes, weeks to days) and
   reported otherwise.

### R5 — cycles

Nothing is ever expanded. A cycle has a length, a number or range, and days.

- **Single cycle (`Cycle n`).** Its columns are ordinary instances in the chain.
  Timing per R4.3.
- **Range (`Cycle n-m`, `Cycle n+`).** The run of adjacent columns with the same range
  is one pass of the cycle. After its last day:
  1. **a delay** — a `Timing` placing the decision after the last day: cycle length
     minus the last day's offset within the cycle (21-day cycle, last day `Day 15`:
     21 − 14 = 7 days);
  2. **a decision** — a `ScheduledDecisionInstance` whose one `ConditionAssignment`
     is the exit condition and leads to the node after the range (or the exit), and
     whose `defaultConditionId` loops back to the range's first column.

  The exit condition's text is the fixed string `cycle exit condition` (U4-7).
- **Mixed** — single cycles then a range (`Cycle 1`, `Cycle 2`, `Cycle 3+`) — is the
  common case. The range's `Day 1` is the previous cycle's length after the previous
  cycle's `Day 1` (U4-27). A range that prints no `Day 1` has a start marker
  (U4-22), and the decision loops back to it.
- **Range as the last column.** A decision cannot target the timeline exit, so an end
  instance is added after the decision — a `ScheduledActivityInstance` with no
  encounter and no activities, like a start marker (U4-22) — carrying the
  `timelineExitId`. The decision's exit branch leads to it (Dave, 2026-09-26).
- **Cycle length missing or `pattern: null`.** The loop is still built; the cycle
  length is the largest day number printed in the range (`D1`, `D8`, `D15` → 15 days),
  with a warning (U4-8). The delay is then 15 − 14 = 1 day: the next pass starts the
  day after the last printed day.

### R6 — conditional timelines and copies

A conditional timeline (`unscheduled`, `early_termination`, `adverse_event`) is a
sibling `ScheduleTimeline`; `entryCondition` is the printed `entry_condition` text. A
column that appears in two timelines (same `id`) becomes an instance in each. Whether
they share one `Encounter` is decision U4-5.

### R7 — profile timelines

A `profile` timeline with `attaches_to` is attached as a sub-timeline at
`Activity.timelineId` of the named activity. Without `attaches_to` it is built
unattached and reported. Its timings are relative to its own anchor (usually
`Hour 0` / `Minute 0`).

### R8 — gates

A column whose timing is a duration with no anchored offset becomes a
`ScheduledDecisionInstance`, not a window. How to tell a gate from a window in text
alone is decision U4-10; not built until it is taken.

### R9 — footnotes

As today: markers on header values (any field — issue 64; a marker on two values of
one column links once), activity names and cells link footnotes to
instances and activities; a footnote whose marker is found becomes a `Condition`
with its text verbatim, `contextIds` and `appliesToIds` as today; an unanchored
footnote is dropped and counted. Never resolved into logic.

## 7. The expander

The expander must follow the R5 loop without unrolling it: take one pass through the
range, then the decision's exit branch. Today a loop recurses without end: a
condition not of the form `days <op> <n>` logs an error and takes the default — which
in the R5 loop points back to the range's start — and on the main timeline every pass
recomputes the same tick, so a `days` condition either exits at once or never does
(`expander.py`, no visited set). A printed range text as the exit condition (U4-7) is
exactly the non-`days` case. How the expanded view shows a repeating
range (a flag on the pass, the condition text) is decision U4-11.

Nothing that builds USDM from a protocol calls the expander, so this change is its own
issue, not part of R5's branch; it must be merged before any release containing R5
(plan § *Order from here*).

## 8. Out of scope for this work, noted

Seen while reading the code; each is its own issue if wanted.

- `entryCondition` is hard-coded as `"Paricipant identified"` (typo) on every
  timeline.
- Every BC mints a `Procedure` with a placeholder code (`12345`, LOINC, version `1`).
- `plannedDuration` is always `None`.
- `_add_timepoints` passes `"scheduledInstanceTimelineId": None`; the API field is
  `timelineId` (`api/scheduled_instance.py`).

## 9. Open decisions

Taken one at a time, each recorded here with its date when taken.

| id | decision | proposal |
|---|---|---|
| U4-1 | Names of the new schema classes and fields | **Taken 2026-09-25:** `ScheduleTimelineInput`, `ColumnInput`, `HeaderValue`, `HeaderNote`, `ActivityInput`, `CellInput`, `FootnoteInput`, `TimelineClassification`; fields as in § 3 |
| U4-2 | The anchor rule | **Taken 2026-09-25:** today's rule — first column with a timing point ≥ 0, else the first column with a warning; no code beyond the warning (§ 6 R4.1). Checked against 72 drafted tables: `Week 0` and cycle tables anchor correctly under it; a narrower "`Day 1` or `Day 0`" rule was rejected (misses `Week 0`, needs cycle parsing, no better fallback) |
| U4-3 | Form of a timing with no readable value (no pattern, printed text unreadable, or redacted) | **Taken 2026-09-25:** a zero timing (`PT0M`) from the previous column, printed text as `valueLabel`, and a warning — nothing more. **Rejected:** an extension flag (Dave: no flags); measuring from the anchor (puts ED at Day 1 in the expander); no `Timing` (DDF00060 needs a duration, and the expander crashes on a missing one) |
| U4-4 | A time range (`Day -28 to Day -1`): the column's timing, its window, or both | **Taken 2026-09-25:** the interface takes both forms. A tool that already holds decoded timings sends a point and a window. A caller reading a document — `usdm4_protocol`, and the corpus ground truth — sends the time range as printed (text, range pattern, or both), and `usdm4` decodes it to the timing at its start and a window forward to its end. Decoding lives here so that nobody has to check it by hand per protocol |
| U4-5 | A copied column: one `Encounter` shared by both timelines, or one each | **Target, taken 2026-09-26 (Dave):** one shared `Encounter`; each timeline gets its own `ScheduledActivityInstance`, so timing and activities can differ per timeline. **Interim, 2026-09-26 (Dave, #70): one `Encounter` each, until a copy can be identified.** Column ids are scoped to one timeline (schema, and every caller numbers them `c1…` per timeline — `features` and `nct04557384` pins reuse `c1` for different visits), so a shared id does not mean a shared visit; sharing by id would silently merge unrelated visits. The fix — an explicit copy reference on the input — is a schema change, logged as `protocol_corpus` register row `N78`. **Rejected:** ids spanning the assembly (silent merges from every existing caller); matching on id plus printed text (a guess) |
| U4-6 | A column with no epoch | inherit the previous column's; none on the first column is an error |
| U4-7 | The exit condition text on a cycle loop | **Taken 2026-09-26 (Dave):** the fixed text `cycle exit condition`. **Noted, not crucial now:** the real exit rule (e.g. progression, unacceptable toxicity) is usually in the protocol body, not the SoA; finding it needs a search wider than the SoA. **Rejected:** printed range text (a heading, not a condition); caller-supplied text (no field in the frozen schema) |
| U4-8 | A range with no readable cycle length | **Taken 2026-09-26 (Dave):** the loop is built; the cycle length is the largest day number printed in the range (`D8` → 8 days, `D15` → 15 days), with a warning. It is a lower bound: the real length (21, 28 days) is usually longer. **Noted, not crucial now:** the true length may be stated outside the SoA; finding it needs a wider search. **Open edge:** a range printing only `Day 1` gives a 1-day cycle — settle when R5 hits it. **Rejected:** a text-only delay (DDF00060 needs a duration; the expander crashes, as U4-3). Ranges only; U4-23 (single cycles) is unchanged |
| U4-9 | Where a cell's printed text goes (`X`, `(X)`, `Predose`) | kept on the input only until a rule needs it |
| U4-10 | Gate versus window in text alone (R8) | open |
| U4-11 | How the expander presents a loop | one pass, flagged as repeating |
| U4-12 | Activity identity across timelines when names differ only by spacing or hyphenation | exact trimmed, case-folded match, as today |
| U4-14 | Crossover periods whose day numbering restarts (a second `Day 1`) | **Working hypothesis 2026-09-25, to be proven on real cases:** one timeline per period. A `Timing` cannot cross timelines (DDF00046), so the link is an instance: the printed washout column (`Wash out 3 to 14 days`, `Minimum 2 wks after end of session 1`) becomes a linking instance in the earlier period, reached by a `Timing` that is the washout, and calling the next period through `timelineId`; the next period's `entryCondition` carries the printed text. Rejected for now: the last instance calling the next period with the washout as text only. Needs a stage-1 marking (periods as timelines, the washout column as the link) and a stage-2 rule; neither built |
| U4-15 | Printed timing text that is a bare number (`15`, `-7`) with no unit in the timeline's timing row label, or no row label | **Taken 2026-09-25 (#65):** days |
| U4-16 | A timing cell that prints its own window (`15 ± 3`) when the column's window field also has a value | **Taken 2026-09-25 (#65):** the window field wins, with a warning. **Standing rule with it:** every problem found reading printed text — unreadable text, a conflict, a default applied — raises a warning naming the timeline, column and field |
| U4-17 | A pattern the grammar refuses | **Taken 2026-09-25 (#65):** always build the timeline if at all possible. The bad pattern is a warning and is set aside; the field is read from its printed text, else gets no value (U4-3 for a timing). Replaces issue 63's "refused pattern → timeline not built" |
| U4-18 | Printed `≤N` as a timing | **Taken 2026-09-25 (#65):** read as the time range `Day -N to Day -1` only in a column before the anchor. Anywhere else it is not read: a zero timing after the previous column, the printed text as `valueLabel`, and a warning |
| U4-19 | Unit of a printed window with no unit (`±3`) | **Taken 2026-09-25 (#65):** the window row label's unit when it states one; else the column's timing unit; else days, with a warning |
| U4-20 | Window length of a time range crossing zero (`Day -3 to Day 2`) | **Taken 2026-09-25 (#65):** today's crossing-zero rule — 4 days when the table has no Day 0, 5 when it has one (`Planner.has_zero_timepoint`) |
| U4-21 | Labels of a decoded time range (`≤28` → `Day -28 to Day -1`) | **Taken 2026-09-25 (#65):** `valueLabel` the decoded start (`Day -28`), `windowLabel` the decoded window in pattern form (`-0..+27 days`), `Timing.label` the printed text (`≤28`). Time ranges only; a printed point and window keep their printed text on both labels |
| U4-13 | How redacted (`CCI`) epochs group | **Taken 2026-09-25 (issue 64):** a consecutive run of redacted columns is one epoch; a run after a non-redacted epoch is a new one, named with an ordinal (`CCI`, `CCI2`) |
| U4-22 | A single cycle with no `Day 1` column | **Re-taken 2026-09-26 (#67; was: its columns measured from the anchor at (*n* − 1) × cycle length + (day − 1)):** every cycle has a `Day 1` node. With no printed `Day 1` column, a start marker is added before the cycle's first column — a `ScheduledActivityInstance` `C{n}D1` with no encounter and no activities, in that column's epoch; it is not a visit. The cycle's other columns are timed from it. When the anchor falls on a column of that cycle, the marker is the anchor |
| U4-23 | Cycle *n* > 1 with no readable cycle length | **Taken 2026-09-25 (R4 part 2); narrowed 2026-09-26 (#67):** the length that matters is cycle *n* − 1's (U4-27). When it cannot be read or converted exactly, or cycle *n* − 1 is not in the timeline, cycle *n*'s `Day 1` gets U4-3's zero timing and a warning; never a guessed number. Its other columns are still timed from that `Day 1`. The last cycle needs no length until R5's delay |
| U4-24 | A negative day inside a cycle (`Day -1` predose) | **Taken 2026-09-25 (R4 part 2):** today's crossing-zero rule — `Day -1` is one day before the cycle's `Day 1` |
| U4-25 | A cycle-range column (`Cycle n-m`, `Cycle n+`) before R5 | **Superseded 2026-09-26 by #69 (R5, § 16).** Was, taken 2026-09-25 (R4 part 2): the range is parsed, not planned; the column gets a U4-3 zero timing and a warning saying cycle ranges come with R5 |
| U4-26 | Where a cycle column's day is read from | **Taken 2026-09-25 (R4 part 2):** the `timing` field only. A table printing the day in its visit row (`D1`) is stage 1's to assign to the timing role; `usdm4` never reads `visit` for timing |
| U4-27 | Cycle *n*'s `Day 1` | **Taken 2026-09-26 (Dave, #67):** a cycle starts at `Day 1`; cycle *n*'s `Day 1` is timed `After` cycle *n* − 1's `Day 1` by cycle *n* − 1's length — a chain. Cycle 1's `Day 1` is Day 1 of the timeline, timed from the anchor. #66 built (*n* − 1) × cycle *n*'s own length, right only when every cycle has the same length. (The example first recorded here, a length printed as `21 days (or 28 days …)`, is a length that differs by cohort, not between cycles; it is not read, U4-23) |
| U4-28 | Unit of a printed cycle length that is a bare number (`28`) | **Taken 2026-09-26 (Dave, #68):** the cycle length row label's unit (`Approximate Duration (days)`), else the timing row label's (`Relative day within a cycle`). With no unit in either, not read, with a warning saying so — never defaulted to days (unlike U4-15); U4-23 then applies |
| U4-29 | `entryCondition` of a conditional timeline with no printed `entry_condition` | **Taken 2026-09-26 (Dave, #70):** default text from the timeline type, with a warning — `unscheduled` → `Unscheduled visit`, `early_termination` → `Early termination`, `adverse_event` → `Adverse event`. **Rejected:** today's fixed `Paricipant identified` (says nothing about why the timeline is entered) |
| U4-30 | Label of a shared `Encounter` (U4-5) when the printed visit text differs between the copies | **Taken 2026-09-26 (Dave, #70); not built — applies once U4-5's shared `Encounter` is.** The first timeline in input order sets the label (and the name, `T{t}-E{n}`); a warning names both texts. **Rejected:** the main timeline's text (an extra rule; main is almost always first) |
| U4-31 | A profile attachment that would make a loop (the attached activity is reached again through the profile it calls, directly or through another profile) | **Taken 2026-09-26 (Dave, R7):** not attached, reported as an error; the profile is built unattached. Sharing an activity between timelines is fine (U4-12 unchanged); a loop is not — they are different things. Checked over the whole attachment graph, not just the direct case |
| U4-32 | `attaches_to` names an activity with children | **Taken 2026-09-26 (Dave, R7):** not attached, reported as an error — DDF00160 forbids `timelineId` on a parent activity |
| U4-33 | `attaches_to` names an activity that exists but is scheduled on no other timeline | **Taken 2026-09-26 (Dave, R7):** attached, with a warning |
| U4-34 | Two profiles naming the same activity (`Activity.timelineId` holds one timeline) | **Taken 2026-09-26 (Dave, R7):** the first profile in input order is attached; each later one is not attached, reported as an error naming both profiles and the activity, and built unattached. **Rejected:** a warning only (hides a lost link); a made-up wrapper activity holding both (invents structure the protocol does not print) |

## 10. As built — issue 63 (2026-09-25)

- **Modules.** `assembler/schema/schedule_timeline_schema.py` (the input);
  `assembler/timeline/grammar.py`, `columns.py` (parse), `plan.py`, `build.py`,
  `naming.py`; `assembler/timeline_assembler.py` is the orchestrator with its public
  surface unchanged. `TimelineInput` and `schema/timeline_schema.py` are gone;
  `AssemblerInput.soa` is `list[ScheduleTimelineInput] | None` (a single dict is
  refused).
- **The schema checks structure only** and refuses unknown keys. Patterns are read in
  the parse stage, so a time range (`… to …`) and the cycle fields are carried as text
  until R4.
- **Behaviour kept exactly**, pinned by `tests/usdm4/assembler/test_timeline_pin.py`:
  four of five pinned inputs reproduce the pre-issue output byte for byte. The fifth
  differs in one timeline whose caller unit was `cycle` (not a grammar unit), which
  moves its anchor — recorded in the plan, 63.5. Both outputs are wrong; R4 fixes it.
- **Object creation order is part of the output.** The builder numbers ids per class
  as objects are made, so `build.py` creates them in the old order: epochs,
  encounters, activities, instances, timings, cell links, conditions, timeline.
- **The profile marker.** The family extension (TLF) is emitted for `profile`
  timelines only, value `profile`: downstream readers take its presence to mean
  "profile". Orientation, unit and placement are emitted when given. The type
  extension R1 calls for is not yet emitted.
- **Failure policy.** A timeline whose patterns the grammar refuses, or with no
  columns, is reported and not built. A built timeline's epochs, encounters and
  conditions are added only once the whole timeline has built; activities are shared
  and stay registered.
- **Kept on purpose until a later rule:** a column with no timing text gets no
  `Timing` (R4); an epoch-less column gets an epoch with an empty label (U4-6); the
  `Paricipant identified` entry condition and the placeholder procedure code (§ 8).
- **Dropped:** the `scheduledInstanceTimelineId` key, which was not an API field.
- **Family names.** `unclassified` is its own family.

## 11. As built — issue 64 (2026-09-25)

Three things the protocol prints that the input dropped. Schema and grammar only; no
timing logic — R4 reads what this adds.

- **Redaction.** `grammar.REDACTED = "CCI"`, `grammar.is_redacted()`; accepted in every
  field. `parse_column` records a redacted field in `Column.redacted` and never parses
  it; the printed text stays the label. Build: a redacted timing or window makes no
  value (as `pattern: null` does); a redacted epoch groups by consecutive run (U4-13);
  a redacted timing or visit never names an instance.
- **Markers per value.** `HeaderValue.markers`; `ColumnInput.markers` is gone (refused
  as an unknown key). `Column.markers` is field → list; `Column.all_markers` is the
  union in field order, each once, and is what links to the timepoint.
- **Row labels.** `ScheduleTimelineInput.rows` (header field → printed label, keys
  checked against `HEADER_FIELDS`); carried to `ParsedTimeline.rows`. Nothing reads it.
- **Pin inputs** moved their column markers onto the visit value (3 columns:
  `features` 1, `nct06454630` 2). Expected output is unchanged — the pin is the proof
  the move is behaviour-neutral. `validate/corpus_adapter.py` does the same move
  (to timing, then epoch, when the visit is blank).
- **Breaking** for any caller that put `markers` on the column. Unreleased since #63.

## 12. As built — issue 65 (2026-09-25)

R4 without cycles. Decisions U4-2–U4-4 and U4-15–U4-21 (§ 9).

- **Grammar.** `TimeRange(unit, start, end)`, `parse_time_range`, `is_time_range`.
  Both ends one unit; end not before start.
- **Printed-text reader** (`assembler/timeline/printed.py`, new). `read_timing(text,
  row_label)` → `ReadTiming(timing, window, unit_defaulted)` where `timing` is a
  `TimingPoint`, `TimeRange` or `UpTo` (`≤N`); `read_window(text, row_label,
  timing_unit)` → `ReadWindow(window, unit_defaulted)`; `unit_of_label`; `is_blank`
  (empty or dashes only — nothing printed, not warned); `normalise` (Unicode minus,
  `+/-`, `<=`). Pure; returns `None` for text it cannot read.
- **Parse** (`columns.py`). Each of timing and window: pattern, else printed text,
  else nothing. A refused pattern is a warning and the field falls back to its text
  (U4-17) — `parse_timeline` no longer raises. `parse_column(index, data, rows, errors,
  t)`. `Column` gains `time_range`, `up_to`, `window_from` (`window` / `timing`). A
  window field beats a window printed in the timing cell, and beats a time range's
  decoded window, each with a warning (U4-16). Epoch and visit patterns are no longer
  checked: blank is already no pattern, so nothing can be refused.
- **Plan** (`plan.py`). `plan(timeline, t)`. U4-2 warning when no column is ≥ 0; U4-14
  restart warning (a lower timing point, same unit, no cycle text). `≤N` resolved to
  `Day -N to Day -1` before the anchor, else warned and unread (U4-18). A column with
  no readable timing: `PT0M`, `After` the previous column, `Before` the next before
  the anchor, warned (U4-3); the anchor itself with no timing is still the Fixed
  Reference, warned. `InstanceNode` gains `window`, `window_from` (`window`, `timing`,
  `range`) and `timed`. `range_window` applies the crossing-zero rule (U4-20).
- **Build.** Every instance has a `Timing`. `valueLabel` the printed text or `""`, the
  decoded start for a time range (U4-21); `label` the printed text or `""`.
  `windowLabel`: printed window text; pattern form for a window decoded from a time
  range (U4-21) **or printed in the timing cell** (`-3..+3 days` — not a decision
  taken; chosen because the cell's printed text is already `valueLabel`); `""` for a
  zero window; the printed text when the window was redacted or unread.
- **Orchestrator.** A timeline is skipped only when it has no columns.
- **Warnings.** A column whose text is unread gets two: one from parse (why), one
  from the plan (the zero timing).
- **Pin.** Re-saved for three cases, every difference explained:
  - `features`: the unread `Cycle 2 Day 1` column is timed from the previous column
    (`D29`) instead of the anchor (`D1`); still `PT0M`.
  - `nct06454630`: 6 instances, 0 timings → 6. No readable timing anywhere, so the
    first column is the Fixed Reference and the rest chain `After` the previous at
    `PT0M`.
  - `nct04557384`: main 0 → 15 timings and continued-access 0 → 2, chained the same
    way (blank timing text). The PK timeline's 14 unread cycle columns (before its
    `Day 30` anchor) chain `Before` the next column instead of all pointing at the
    anchor; values unchanged (`PT0M`). Cycle reading is the next R4 issue.
  - `minimal`, `nct05565742`: unchanged. `nct05565742` raises the restart warning on
    its trailing `Day 0` after `Day 540` (a drafting error in that pinned input).

## 13. As built — issue 66 (2026-09-25)

R4 part 2, single cycles. Decisions U4-22–U4-26 (§ 9).

- **Grammar.** `CycleNumber(n)` (`Cycle 2`), `CycleRange(start, end)` (`Cycle 3-6`;
  `Cycle 3+` has `end=None`), `CycleLength(n, unit)` (`21 days`); `parse_cycle`,
  `parse_cycle_length`. `Cycle 0` is accepted; a range ending before its start and a
  zero length are refused.
- **Printed-text reader.** `read_cycle`: `Cycle 2`, `Cycle2`, `C2`, `C 2`, a bare `2`;
  ranges `Cycle 3-6`, `Cycles 3-6`, `C3-C6`, `Cycle 3-n`, `Cycle 3+`, `… and beyond`,
  `… onwards`, `… and subsequent`. A trailing parenthetical (`Cycle 2-n (if held)`) is
  ignored. `Subsequent Cycles` (no number) is not read. `read_cycle_length`: `21 days`,
  `21-day cycle`, `Cycle = 21 days`, `Cycle length: 21 days`, `(21 days)`, `4 weeks`;
  a length with no unit or two lengths (`21 days (or 28 days …)`) is not read.
- **Parse** (`columns.py`). `Column.cycle`, `Column.cycle_length`: pattern, else
  printed text, else nothing, each problem a warning naming timeline, column and
  field; a redacted value is not read. `Column.cycle_day` holds the day within the
  cycle when the plan takes a column's timing away.
- **Plan** (`plan.py`). `_resolve_cycles` runs before the anchor is chosen. A
  cycle's length is the first readable one among its own columns (a second,
  different one is warned). Cycle *n*'s offset is (*n* − 1) × its length, converted
  to the day's unit only where exact (`_convert`; weeks ↔ days ↔ hours ↔ minutes;
  months and years never). A column in cycle *n* is `After` / `Before` its cycle's
  first `Day 1` column by the day distance with the crossing-zero rule; a cycle's
  `Day 1`, and every column of a cycle with no `Day 1` column, is measured from the
  anchor on the timeline's own line (`_position`). No length (U4-23), no exact
  conversion, or a range (U4-25) → timing removed, so U4-3's zero timing applies,
  with a warning of its own.
- **Naming.** `sai_name(..., cycle=n)`: a single cycle with a day timing is
  `C{n}D{day}` (`C2D8`, `C3D-1`). The text regex (`Cycle 2 Day 1` → `C2D1`) stays as
  the fallback for text-only columns.
- **Tests.** Hand-written fixtures only (`test_grammar`, `test_printed`,
  `test_columns`, `test_plan` `TestSingleCycles`, `test_naming`,
  `test_timeline_assembler` end to end). Pins unchanged — no pinned input carries a
  cycle field. `assembler/timeline/*` and `timeline_assembler.py` 100% coverage.

**Calls made while building, not ruled:**
- The length is cycle *n*'s own, as § 6 R4.3 and U4-23 said. Wrong where cycles
  differ in length; replaced by the chain in #67 (§ 14, U4-27).
- A cycle's length comes from any of its columns, not only an earlier one (the issue
  said "the previous column"): a length printed on a later column of the cycle would
  otherwise leave its `Day 1` untimed.
- A cycle and day printed together in the timing field with no cycle field
  (`Cycle 2 Day 1`) is still unread (U4-26: stage 1 splits it).
- A column timed to zero for a cycle reason gets two warnings: the cycle reason and
  U4-3's "no readable timing".

## 14. As built — issue 67 (2026-09-26)

Cycle `Day 1`: the chain and the start marker. Decisions U4-22 (re-taken), U4-23
(narrowed), U4-27 (§ 9).

- **Plan** (`plan.py`). `_resolve_cycles` finds the timeable single-cycle columns and
  the lengths; no offsets. `_cycle_starts` gives each cycle with a readable day a
  `Day 1` node: its first column whose day is `1` in days or weeks, else a marker keyed
  `C{n}D1`, placed before the cycle's first column (any column carrying that cycle
  number). A cycle none of whose columns has a readable day gets no marker. A marker
  is logged at info level.
- **Node keys.** `InstanceNode.relative_to` and `TimelinePlan.anchor` are node keys: a
  column index, or a marker's `C{n}D1`. A marker node has `column=None`, `marker`,
  `cycle` and `epoch_column`; `InstanceNode.key` returns the key either way.
- **Timing.** A cycle's `Day 1` (`_start_timing`): the anchor is fixed; cycle *n* > 1
  is `After` cycle *n* − 1's `Day 1` by cycle *n* − 1's length, converted to cycle
  *n*'s unit only where exact; cycle 1 is Day 1 of the timeline, from the anchor. Any
  other cycle column is `After` / `Before` its cycle's `Day 1` node by (day − 1), with
  the crossing-zero rule. A `Day 1` that cannot be chained is a zero timing `After` the
  previous node, with a warning naming the reason.
- **Anchor.** Chosen as before (first column with a timing ≥ 0). When that column
  belongs to a cycle whose `Day 1` is a marker, the marker is the anchor, at Day 1;
  columns outside the cycle are measured from it with the crossing-zero rule
  (`_interval`).
- **Build** (`build.py`). A marker node becomes a `ScheduledActivityInstance` named
  `C{n}D1`, `encounterId` `None`, no activities, the epoch of its cycle's first column,
  description `Start of cycle n; no Day 1 column is printed`. Its `Timing` is
  `TIMC{n}D1` with empty labels. No encounter is created for it; encounters stay one
  per column.
- **Equal lengths.** Every `Day 1` lands where #66 placed it; what changes is the
  reference — cycle *n* > 2's `Day 1` is now relative to cycle *n* − 1's `Day 1`, not
  the anchor.
- **Tests.** `test_plan` `TestSingleCycles` (rewritten to the chain) and
  `TestCycleDayOne`; `test_timeline_assembler` end to end with a marker. Pins
  unchanged — no pinned input carries a cycle field.

**Calls made while building, not ruled:**
- `Week 1` counts as a printed cycle start, like `Day 1`, because #66 already measured
  week-counted cycles from value 1. The marker is still named `C{n}D1`.
- A `Day 1` that cannot be chained is zero-timed, but the cycle's other columns keep
  their timing from it. #66 zero-timed every column of such a cycle.
- A table beginning at cycle *n* > 1 whose anchor is that cycle's `Day 1` is fixed
  there; no warning about the missing earlier cycle.

## 15. As built — issue 68 (2026-09-26)

Cycle reading; the three headers NCT02107703 prints. Decision U4-28 (§ 9). Reading
only — the input schema is unchanged.

- `printed.py` — `_CYCLE_RANGE_RE`: the cycle word is optional, so `2-3`, `3-n`, `4+`,
  `4 and Beyond (if Applicable)`, `3 onwards` are ranges. `_CYCLE_LENGTH_RE`: the unit
  is optional; `read_cycle_length(text, row_label, timing_row_label)` gives a bare
  number the cycle length row label's unit, else the timing row label's, else `None`.
- `columns.py` — `_read_cycle_length` passes `rows.cycle_length` and `rows.timing`, and
  warns a bare number with no unit anywhere as such (not the generic "not read").
- Tests: `test_printed.py` (`TestCycle`, `TestCycleLength`), `test_columns.py`,
  `test_plan.py` (`TestNct02107703Headers`: every header read, ranges still U4-25 zero
  timings until R5).

## 16. As built — issue 69 (2026-09-26)

R5, cycle ranges (§ 6 R5, U4-7, U4-8, end instance). Supersedes U4-25. No input schema
change.

- `plan.py` — a range column is a cycle slot numbered by its first cycle; its `Day 1`
  (or U4-22 marker) is chained from the previous cycle's `Day 1`, found by
  `_CycleStart.covers` so a range covering cycle *n* − 1 counts (`2-3` then `4+`).
  Ranges take lengths like single cycles; none readable → U4-8, the largest day printed
  in the range (same unit as the first), warned. `_add_loops` puts a `DECISION` node
  after each range's last column — `After` it by length − (last day − 1), `loop_to` the
  range's first node (its start marker, else its first column, so a predose `Day -1`
  printed before `Day 1` is inside the loop) — and an `END` node after the decision when that column is the
  last. No length, a length that does not convert exactly, or a last day beyond the
  length: zero delay, warned.
- `build.py` — `ScheduledDecisionInstance` in the range's epoch; its default loops back;
  one `ConditionAssignment`, `cycle exit condition`, to the next instance. The end
  instance: no encounter, no activities; it is the last instance, so it takes the exit.
  Range instances, and a range's start marker, are named `C3+D1`, `C2-3D1`.
- `naming.py` — `decision_name` (`C3+DEC`), `end_name` (`T1-END`).
- Tests: `test_plan.py` `TestRanges`, `TestNct02107703Headers` (ranges timed and
  looped); `test_r5_nct05197426.py` (the built USDM, and other shapes on structured
  input: bounded then open range, no `Day 1`, predose `Day -1`, weeks); pin `nct05197426` added. Existing
  pins unchanged.

**Calls made while building, not ruled:**
- The loop returns to the range's first column, not `Day 1`, when a day is printed
  before `Day 1` in the range (§ 6 R5 said first column; the #69 issue text said Day 1).
- Printed text is supported but not held to the structured form's standard (Dave):
  `1 Cycle = 4 Weeks` is not read as a length; the structured `4 weeks` is.
- A column after a range with no readable timing keeps U4-3's zero timing after the
  previous *column* (the range's last day), not after the decision the exit leads to.
- A single cycle and a range with the same first cycle (`Cycle 2`, `Cycle 2-n (if …)`)
  share one cycle slot.

## 17. As built — issue 70 (2026-09-26)

R6, conditional timelines (§ 6 R6, U4-29). Copied columns deferred (U4-5 interim). No
input schema change.

- `columns.py` — `ParsedTimeline.entry_condition` carried from the input.
- `build.py` — `_entry_condition`: a conditional timeline takes its printed
  `entry_condition`, trimmed; blank or absent → the type's default
  (`CONDITIONAL_ENTRY_CONDITIONS`) and a warning. Every other family keeps
  `PLANNED_ENTRY_CONDITION`, the old fixed text, typo included (§ 8).
- A copied column (NCT05565742's `ED`, in main and in the early-termination timeline)
  builds one `Encounter` per timeline — U4-5 interim, fix logged as `protocol_corpus` `N78`. U4-30 not built.
- Tests: `test_timeline_assembler.py` `TestConditionalTimelines` (defaults per type,
  printed text, blank, other families unchanged, a guard that every conditional type
  has a default, the copied column's two encounters pinned); pin `nct05565742_r6`
  added (the frozen `nct05565742` main timeline plus the ED timeline from the corpus
  ground truth, timeline 2). Existing pins unchanged.

**Seen, not this issue.** The ED timeline's instance is named `ED-2`, not `T2-ED`:
`sai_name` de-duplicates across timelines rather than qualifying. Existing behaviour.

## 18. As built — issue 71 (2026-09-26)

R7, profile attachment (§ 6 R7, U4-31–U4-34). No input schema change.

- `columns.py` — `ParsedTimeline.attaches_to` carried from the input (the schema
  accepted it and it was dropped, as R6 found for `entry_condition`).
- `timeline_assembler.py` — `_attach_profiles`, a pass after every timeline is built
  and before `double_link`: the named activity usually sits on another timeline,
  possibly later in the input. The name is matched on identity (U4-12) in
  `SharedState.activity_by_name`; `Activity.timelineId` is set to the profile.
  Not attached, profile built unattached: no `attaches_to` or an unknown name
  (warning); a parent activity (error, DDF00160, U4-32); an activity already taken
  by an earlier profile (error, U4-34 — only a successful attachment claims it); a
  loop (error, U4-31). Scheduled on no other timeline: attached, warning (U4-33).
- The loop check (`_reaches`) walks from the profile through every activity its
  instances schedule and every timeline those activities already call; the target
  activity found anywhere on that walk is a loop. A timeline reached twice (a
  diamond) is walked once and is not a loop.
- `build.py` unchanged: activities are still created with `timelineId = None`.
  `ScheduledActivityInstance.timelineId` stays `None` — per-visit attachment needs a
  column reference the frozen schema lacks (out of scope).
- Tests: `test_timeline_assembler.py` `TestProfileAttachment` (18: attached,
  identity match, profile before main, no/blank/unknown `attaches_to`, direct loop,
  loop through a second profile, a chain, a diamond, parent, unscheduled, two
  profiles, a refused profile not blocking a later one, other families). Pin
  `nct02674152_r7` added: main table A as drafted plus the profile's course 1 Day 1
  columns (8 of 48), `attaches_to: Pharmacokinetics` — `Pharmacokinetics` calls
  TIMELINE-2, no attachment message. Existing pins unchanged (`features` has a
  profile with no `attaches_to`: a new warning, no output change).

**Seen, not this issue.** The pin's main timeline is built from unreviewed header
drafts whose roles are wrong: the `Week` row is drafted as the timing and the
`Day; visit window` row as the window, so V1's three days all time as `Week 1` and
every window is unread; course lists (`1, 2, 3, 4`) are not read. Frozen as drafted —
a fixture, not a reference.
