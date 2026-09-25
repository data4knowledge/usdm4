# Timeline assembler — design

**Status: DRAFT, 2026-09-25, issue 63 (branch `63-timeline-assembler`).** This is the
design the timeline assembler is rebuilt against. Nothing here is built yet except
where a section says *today*. Decisions still open are listed in § 9 and are taken
one at a time; the work order is in `timeline_assembler_plan.md`.

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
assembler.** A caller never hands over a number it has worked out from printed text;
it hands over text, in the pattern grammar (§ 4). Two callers reading the same
schedule must reach the same timings through the same code.

## 2. Today

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
timelines in the shape below. Field names are a proposal (decision D1).

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
    columns:                   # document order
      - id: c1                 # caller's key, unique within the timeline
        epoch:   {text: "Screening", pattern: "Screening"}
        visit:   {text: "V1", pattern: "V1"}
        cycle:   null
        cycle_length: null
        timing:  {text: "≤28", pattern: "Day -28 to Day -1"}
        window:  {text: "", pattern: null}
        notes:   []            # further header rows, text only (§ 3.2)
        markers: []            # footnote markers printed on this column's header
      - id: c4
        epoch:   {text: "On-Treatment", pattern: "On-Treatment"}
        visit:   {text: "D8", pattern: "D8"}
        cycle:   {text: "Cycle 1", pattern: "Cycle 1"}
        cycle_length: {text: "Cycle = 21 days", pattern: "21 days"}
        timing:  {text: "D8", pattern: "Day 8"}
        window:  {text: "(±3 days)", pattern: "-3..+3 days"}
        notes:   []
        markers: []
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

Every header value is `{text, pattern}`.

- `text` is what the document prints. It is used for labels, so the protocol's words
  survive into USDM. It is never parsed.
- `pattern` is the same value in the pattern grammar (§ 4). It is what the assembler
  parses. A caller using the assembler directly may supply `pattern` alone; the
  label then defaults to the pattern.
- `pattern: null` means the caller states the value cannot be expressed in the
  grammar. The assembler carries the text and makes no timing from it (R4).
- A `pattern` that is present and does not match the grammar is an input error.

`notes` holds every further header row the caller keeps — a second timing row, a
timing clarification, an unassigned row — as `{role, text}`. Text only; the
assembler puts them on labels or descriptions and never parses them.

### 3.3 What the schema deliberately leaves out

- **Logical tables.** Joining page fragments into tables and splitting a table into
  timelines is the caller's judgement. The assembler only ever sees timelines.
- **Copies.** A column that belongs to two timelines (a combined `EOT/ET` column)
  appears in both, with the same `id`. What that means in USDM is decision D5.
- **Parsed numbers.** There are no `value`, `unit`, `before` or `after` fields.

## 4. The pattern grammar

Strict and small on purpose. One way to write each thing. Case-insensitive keywords,
single spaces, ASCII only — a window is written `-a..+b`, never with `±`.

| value | pattern | examples |
|---|---|---|
| timing, point | `<Unit> <int>` | `Day 1`, `Day -7`, `Week 12`, `Month 6`, `Year 2`, `Hour 4`, `Minute 30` |
| timing, span | `<Unit> <int> to <Unit> <int>` | `Day -28 to Day -1` |
| window | `-<int>..+<int> <units>` | `-3..+3 days`, `-0..+2 hours`, `-7..+0 days` |
| cycle, single | `Cycle <int>` | `Cycle 1`, `Cycle 2` |
| cycle, range | `Cycle <int>-<int>` or `Cycle <int>+` | `Cycle 1-6`, `Cycle 3+` |
| cycle length | `<int> <units>` | `21 days`, `4 weeks` |
| epoch, visit | free text, trimmed | `Screening`, `V1`, `D8` |

`<Unit>` is one of Day, Week, Month, Year, Hour, Minute. `<units>` is its plural,
lower case.

Rules the grammar carries:

- **In a cycle column, `timing` is the day within the cycle.** `Day 8` in a column
  whose cycle is `Cycle 3` means C3D8. The printed `C3D8` stays in `text`. There is
  one way to write it.
- **An open-ended range is `Cycle n+`.** `Cycle 2-n`, `Cycle 2+`, `Cycles 2 and
  beyond` all become `Cycle 2+`; the printed words stay in `text`.
- **A timing span** is a column whose scheduled time is a range (`-28 to -1`,
  `≤28`). Whether a span is the column's timing or its window is decision D4.

Anything the grammar cannot express is `pattern: null`, stated by the caller.

## 5. Structure

The assembler is split into four stages. Each is its own module under
`assembler/timeline/` (proposal; the package layout is part of issue 63).

1. **Parse** (`grammar.py`, `columns.py`). Validate the input; parse every `pattern`
   into a typed value; build one column record per column. Pure functions, no USDM
   objects. An invalid input is reported with the timeline, column and field, and the
   timeline is not built.
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

**Failure policy.** Validation and parse errors stop the timeline before anything is
built, and are reported once with their location. A timeline is built whole or not
at all; no step returns a partial result after an exception. This extends the
issue 58 rule (a table with no timepoint spine is skipped, not half-built) to every
failure.

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
error (decision D6 confirms). A cycle is never an epoch. *Today:* one epoch per
distinct text, matched to columns by position; no inheritance and no error for a
missing epoch.

### R3 — encounters, instances and cells

One `ScheduledActivityInstance` per column, in column order, labelled with the timing
text (or visit text where there is no timing), named by `_sai_name` using the cycle
and day where there is one (`C2D8`). One `Encounter` per column, labelled with the
visit text. An instance's `activityIds` are the activities with a cell in its
column. The cell's printed text is kept (decision D9 for where); its markers link to
footnotes (R9). *Today:* the same from positional lists and `visits[].index`, except
that the instance label is the timepoint text with no visit fallback, and `C2D1`
comes only from a regex on that text.

### R4 — timing

1. **Anchor.** Decision D2. Proposal: the first column whose timing is `Day 1` or
   `Day 0`, or, in a cycle, the first `Day 1` of the first cycle. No such column → the
   first column, as today, with a warning.
2. **Duration** from the pattern: point minus anchor in the column's unit, with
   today's crossing-zero rule for days kept exactly.
3. **Cycle columns** are measured from their cycle's `Day 1`, and that `Day 1` from
   the anchor (for a single cycle *n*: (*n* − 1) × cycle length after the first
   cycle's `Day 1`). This makes a chain of timings, which the expander already
   follows hop by hop.
4. **Windows** from the pattern: `windowLower`, `windowUpper` as ISO 8601 durations,
   `windowLabel` the printed text.
5. **`pattern: null`** → a `Timing` carrying the printed text as its label and no
   duration value (decision D3 fixes the exact form). Never a guessed number.
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

  The exit condition's text is decision D7; the proposal is the printed range text
  (`Cycle 3-n`, `Cycles 1-6`) unless the caller supplies one.
- **Mixed** — single cycles then a range (`Cycle 1`, `Cycle 2`, `Cycle 3+`) — is the
  common case. The range's first `Day 1` is one cycle length after the previous
  cycle's `Day 1`.
- **Cycle length missing or `pattern: null`.** The loop is still built; the delay is a
  text-only timing (decision D8).

### R6 — conditional timelines and copies

A conditional timeline (`unscheduled`, `early_termination`, `adverse_event`) is a
sibling `ScheduleTimeline`; `entryCondition` is the printed `entry_condition` text. A
column that appears in two timelines (same `id`) becomes an instance in each. Whether
they share one `Encounter` is decision D5.

### R7 — profile timelines

A `profile` timeline with `attaches_to` is attached as a sub-timeline at
`Activity.timelineId` of the named activity. Without `attaches_to` it is built
unattached and reported. Its timings are relative to its own anchor (usually
`Hour 0` / `Minute 0`).

### R8 — gates

A column whose timing is a duration with no anchored offset becomes a
`ScheduledDecisionInstance`, not a window. How to tell a gate from a window in text
alone is decision D10; not built until it is taken.

### R9 — footnotes

As today: markers on column headers, activity names and cells link footnotes to
instances and activities; a footnote whose marker is found becomes a `Condition`
with its text verbatim, `contextIds` and `appliesToIds` as today; an unanchored
footnote is dropped and counted. Never resolved into logic.

## 7. The expander

The expander must follow the R5 loop without unrolling it: take one pass through the
range, then the decision's exit branch. Today a loop recurses without end: a
condition not of the form `days <op> <n>` logs an error and takes the default — which
in the R5 loop points back to the range's start — and on the main timeline every pass
recomputes the same tick, so a `days` condition either exits at once or never does
(`expander.py`, no visited set). A printed range text as the exit condition (D7) is
exactly the non-`days` case. How the expanded view shows a repeating
range (a flag on the pass, the condition text) is decision D11.

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
| D1 | Names of the new schema classes and fields | as in § 3 |
| D2 | The anchor rule | § 6 R4.1 |
| D3 | Form of a text-only timing (no parseable pattern) | `Timing` with label, `value` a zero duration flagged by an extension |
| D4 | A timing span (`Day -28 to Day -1`): the column's timing, its window, or both | timing = span end, window = span |
| D5 | A copied column: one `Encounter` shared by both timelines, or one each | one shared |
| D6 | A column with no epoch | inherit the previous column's; none on the first column is an error |
| D7 | The exit condition text on a cycle loop | printed range text unless the caller supplies one |
| D8 | A range with no readable cycle length | loop built, delay text-only |
| D9 | Where a cell's printed text goes (`X`, `(X)`, `Predose`) | kept on the input only until a rule needs it |
| D10 | Gate versus window in text alone (R8) | open |
| D11 | How the expander presents a loop | one pass, flagged as repeating |
| D12 | Activity identity across timelines when names differ only by spacing or hyphenation | exact trimmed, case-folded match, as today |
