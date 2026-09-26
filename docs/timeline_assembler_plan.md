# Timeline assembler — plan of work

**Status: 2026-09-26. Rate of change: per issue. Retired when the last issue below is
closed.** The design is `timeline_assembler_design.md`; this file is the order the
work is done in, what each issue delivers and how each is gated. One issue, one
branch. Each later issue is raised on GitHub when the one before it is merged.

**Naming.** The parts of issue 63 are **63.1–63.7**. The later `usdm4` issues are named
by the rule they build: **R4, R5, R6, R7, R8**. "Step" is not used here — it is kept
for the cross-repo sequence in `protocol_corpus/docs/next_steps.md`, where all of this
file is one step.

## Why this order

Rules R1–R3 already exist and work. The structure they sit in has no place for a
loop, and the input carries neither cycles nor text. So issue 63 changes the input
and the structure together and keeps behaviour — every later rule is then a small
addition to a clean plan stage, not a patch on the old chain.

## Issue 63 — new input, grammar, restructure (behaviour kept)

Branch `63-timeline-assembler`.

- **63.1 Pin today's output.** *Done 2026-09-25.* Before any code moves, record the
  assembled USDM for a set of inputs in today's `TimelineInput` shape:
  `tests/usdm4/assembler/test_timeline_pin.py`, inputs in
  `tests/usdm4/test_files/timeline_pin/input_*.json` — `minimal` (the existing
  fixture), `features` (hand-built: footnote markers on visits, activities and cells,
  an unanchored and an unmarked footnote, parent and child activities, a library and a
  surrogate BC, mixed units, a non-numeric timing, a classified profile timeline, a
  table with no timepoints), and three real machine-drafted schedules copied in and
  frozen (`nct05565742`, `nct06454630`, `nct04557384` — the last with three timelines
  and cycles). Output is everything the other assemblers read, as JSON. Ids come from
  the builder's counter after `clear()`, so no normalising is needed; a determinism
  test checks that. The expected files were created by one run with `SAVE = True` on
  the unchanged code, and pass.
- **63.2 Grammar** (`assembler/timeline/grammar.py`). Parse epoch, visit, timing points
  and window patterns into typed values — what today's build already uses. Unit
  tests for every one of those forms in design § 4 and for rejection of everything
  outside it. Time ranges (U4-4) and cycle patterns are R4; until then a time range or
  cycle value is carried as text only. *Written 2026-09-25:* `parse_timing` →
  `TimingPoint(unit, value)`, `parse_window` → `Window(lower, upper, unit)`,
  `parse_label` (trimmed, non-empty), `PatternError(kind, value, expected)`; units
  normalised to singular lower case. Refused on top of design § 4: `Day -0`,
  `Day 08`, `Day +8`, non-ASCII digits and minus. Tests
  `tests/usdm4/assembler/timeline/test_grammar.py`.
- **63.3 Schema** (`assembler/schema/`). The timeline, column, value, activity, cell and
  footnote models of design § 3. The schema is complete from the start — `cycle`,
  `cycle_length`, `notes`, `entry_condition`, `attaches_to` included — so later issues
  add rules, not fields. Fields a rule does not use yet are carried, and their text
  reaches labels where design § 3.2 says so. *Written 2026-09-25:*
  `assembler/schema/schedule_timeline_schema.py` — `ScheduleTimelineInput`,
  `ColumnInput`, `HeaderValue` (`text`, `pattern`, `label`), `HeaderNote`, `CellInput`,
  `ActivityInput`, `FootnoteInput`, `TimelineClassification`, `TimelineType`,
  `FAMILY` / `family_of` (U4-1 taken as these names). Structure only — patterns are
  parsed in the parse stage, so a time range or cycle can be carried as text until R4.
  Unknown keys refused (`extra="forbid"`). Checks inside one timeline: unique column
  ids, cells in known columns and at most one per column, known parents, unique
  footnote markers, `attaches_to` only on `profile`, `entry_condition` only on a
  conditional type. Additive: exported beside `TimelineInput`, nothing reads it yet.
  **Sequencing change:** switching `AssemblerInput.soa` to the new model and removing
  `TimelineInput` moves to 63.4, so the branch stays green between parts — switching
  here would break the assembler until it can read the new input. Tests
  `tests/usdm4/assembler/schema/test_schedule_timeline_schema.py`.
- **63.4 Restructure** into parse → plan → build, with naming moved out unchanged
  (design § 5). `AssemblerInput.soa` becomes a list of `ScheduleTimelineInput` and
  `TimelineInput` is removed (moved here from 63.3). *Written 2026-09-25:*
  `assembler/timeline/columns.py` (parse: one `Column` per column, patterns read with
  the grammar; a time range is carried as text, cycle fields as text), `plan.py` (the
  straight chain, one anchor, today's crossing-zero and mixed-unit rules),
  `build.py` (`TimelineBuild` per timeline, objects created in exactly the old order
  because the builder numbers ids as they are made; `SharedState` for activities
  and BCs), `naming.py` (`Naming`, moved unchanged); `timeline_assembler.py` is the
  orchestrator. A timeline whose patterns the grammar refuses, or with no columns, is
  reported and not built; a built timeline's epochs, encounters and conditions are
  added only once the whole timeline is built. `schema/timeline_schema.py` and its
  test are deleted. TLF (family) is still emitted for profiles only — its presence
  marks a profile to downstream readers; the type extension is left for R1's
  completion. The `scheduledInstanceTimelineId` key is no longer passed. The plan builds today's straight chain only; cycles, decisions and
  profile attachment are later issues. The public surface of `TimelineAssembler` does
  not change.
- **63.5 Rewrite the pinned fixtures once in the new schema** and compare the output
  with the pin. *Done 2026-09-25, together with 63.4 (the restructure cannot be
  checked without it).* Conversion rules, mechanical: one column per old timepoint
  (`c1`, `c2` …); epoch and visit text → `{text, pattern: text}`, blank → null; timing
  `{text, pattern: "<Unit> <value>"}` when the old value is an integer and its unit is
  in the grammar, else text only, and a blank text with a zero value (a placeholder
  column) → null; window → pattern `-b..+a <units>`, text the old label
  (`-b..+a <unit>`, blank for a zero window); activities flattened, children after
  their parent with `parent` set, visit indexes → cells (`X`) with their markers;
  conditions → footnotes; `main_soa` or missing type → `main`, other tables →
  `profile` when they carried a `table_family`, else `unclassified`. **Result: four of
  five cases identical to the 63.1 pin; one difference, re-saved:** NCT04557384's PK
  timeline was drafted with unit `cycle`, which the grammar has no word for, so its
  cycle columns are text only; the anchor moves from C1D1 to its one `Day 30`
  column, turning 14 `After` timings into `Before` and the `Day 30` timing from
  `P30D` to `PT0M`. Both versions are wrong — this timeline needs R4's cycle timing.
  Other differences the plan allowed for did not occur with these inputs:
  - timing taken from `pattern` instead of a caller's number;
  - an instance printed `C2D8` whose cycle is now in the `cycle` field and whose
    timing is `Day 8`: named `D8` until R4 puts the cycle back into the name;
  - `windowLabel`: today built from the numbers (`-1..+2 days`); in issue 63 it is
    built the same way from the parsed pattern, and becomes the printed text in R4
    (design R4.4).
- **63.6 Rewrite the unit tests** against the new structure. The repo requires 100%
  coverage. *Done 2026-09-25:* `tests/usdm4/assembler/test_timeline_assembler.py`
  rewritten end to end through `execute` (state and dispatch, timelines and the main
  flag, skipped timelines, extensions, epochs, encounters, instances, timings,
  windows, activities and cells, BCs, footnotes); new `tests/usdm4/assembler/timeline/`
  `test_naming.py` (the name-collision tests moved here — the old
  `test_timeline_assembler_name_collisions.py` is deleted), `test_columns.py`,
  `test_plan.py` and `helpers.py`. The four old-shape `soa` fixtures moved to the new
  input (`test_assembler.py` ×2, `schema/test_assembler_input.py`, which also gains
  "old shape refused" and "must be a list", and `tests/usdm4/integration/conftest.py`).
  Today's defects the later rules fix are pinned as they are and say so (blank timing
  gets no `Timing`; the `Paricipant` typo; placeholder procedure code; an epoch-less
  column's empty epoch). The code under test imports `usdm4.*` while tests import
  `src.usdm4.*`, so grammar classes are compared by field and `PatternError` caught as
  `ValueError`. Checked in a sandbox subset: 406 tests pass and the new modules are at
  100%; the d4k integration tests pass (CORE not run). `validate/corpus_adapter.py`
  and `validate/eval_corpus.py` still build the old `soa` shape — tooling, not tests;
  they break until moved (63.7 or a follow-up).
- **63.7 Docs and the corpus tooling.** *Done 2026-09-25:* this file and the design
  (§ 10, *as built*) updated; `lessons_learned.md` (restructure behind a pin); session log entry in
  `next_steps.md`. `validate/corpus_adapter.py` now converts the retired shape
  (which the corpus still drafts) into `ScheduleTimelineInput` with the 63.5 rules —
  `timeline_input_to_schedule` — keeping every table instead of collapsing to the
  main one; a table already in the new shape passes through. `AdapterReport` field
  `soa_timelines_converted` replaces `soa_list_collapsed` / `soa_subtimelines_dropped`
  (and `eval_corpus.py` reports it). Checked: converting the five old pin inputs
  gives exactly the committed new ones, and NCT05565742's corpus ground truth
  assembles through the adapter.

**Gate.** Full test suite green (run in VSCode, not Cowork). Every difference from the
pin explained. The d4k and CORE integration tests
(`tests/usdm4/integration/test_assembler_to_*`) green on the new schema.

**Breaking change.** Every caller of `AssemblerInput.soa` breaks. The version number
is Dave's to set; it should read as breaking.

## Issue 64 — redaction, per-value markers, row labels

Branch `64-timeline-inputs-new-features`. Raised from `protocol_corpus` issue 9: three
things the protocol prints that the input dropped. Schema and grammar only; R4 uses
them. As built: design § 11.

- **Redaction.** `CCI` is a valid pattern in every field and is never parsed; the
  column records which fields are redacted. Redacted epochs group by consecutive run
  (U4-13, taken 2026-09-25); a redacted timing or visit never names an instance.
- **Markers per value.** `HeaderValue.markers` replaces `ColumnInput.markers`; every
  header value's markers link to the column's timepoint, each once.
- **Row labels.** `ScheduleTimelineInput.rows`, header field → printed label. Carried;
  R4 reads the anchor.
- **Pin.** The three pin-input columns with markers had them moved onto the visit
  value; expected output untouched. A pin difference is a bug.

**Gate.** Full suite green (VSCode), pin unchanged, coverage held.

**Test cases** (`protocol_corpus` ground truth): NCT06454630 (timing row redacted),
NCT05565742 (row labels, visit markers).

## R4 — timing and single cycles

Cycle and cycle-length patterns added to the grammar; cycle text used in instance
names and labels (`C2D8`). Anchor rule (U4-2), timing from the pattern for points and
time ranges (U4-4), windows from the pattern with the printed text as `windowLabel`,
text-only timing (U4-3), mixed units. Every instance gets a `Timing` — today a blank
timepoint text loses all of a timeline's timings (design § 2). Cycle columns measured
from their cycle's `Day 1` (single cycles only). Decisions U4-2, U4-3, U4-4 taken before the
branch. **U4-2, U4-3, U4-4 taken 2026-09-25** (design § 9): U4-2 today's anchor rule plus a
warning when no column is ≥ 0 and on a restart outside a cycle (U4-14); U4-3 a text-only or
redacted timing is a zero timing plus a warning; U4-4 a time range is decoded here to the timing at
its start and a window forward to its end. Split: the first R4 issue (#65) is timing without
cycles (every instance timed, U4-2 warnings, U4-3, time ranges, printed `windowLabel`, and each
of timing and window read from its pattern, else from the printed text — design
§ 3.2); single cycles are the second. **#65 written 2026-09-25**, with U4-15–U4-21 taken
during it (design § 9) — as built: design § 12. **#65 merged 2026-09-25.** **R4 part 2 — single cycles**:
decisions U4-22–U4-26 taken 2026-09-25 (design § 9); tested on hand-written unit fixtures
only — the NCT04557384 pin input carries no cycle fields and is left alone until R5. **#66 built 2026-09-25** (branch `66-r4-part-2-single-cycles`) — as built: design § 13. **#67 built 2026-09-26** (branch `67-cycles`): every cycle has a `Day 1` node — printed, or a start marker `C{n}D1` that is not a visit (U4-22 re-taken) — and cycle *n*'s `Day 1` is chained from cycle *n* − 1's by cycle *n* − 1's length (U4-27 taken). As built: design § 14.

## Order from here (2026-09-26)

Cycle reading → R5 → R6 → R7, one issue each, each merged when its gate passes. The
expander is its own issue, off the build path: nothing that builds USDM from a
protocol calls it (not the assembler, `validate/`, `usdm4_protocol` or the corpus
tooling — only `usdm4`'s own tests). It gates the **release**, not the build: no
`usdm4` release is cut once R5 is merged until the expander issue is merged too. R8
waits on U4-10. **The input schema is frozen** (`next_steps.md` § Working arrangement);
every issue below is checked against it.

## Cycle reading — the three gaps NCT02107703 prints

**#68 merged 2026-09-26** (branch `68-cycle-and-ranges`), U4-28 taken — as built: design § 15.

Reading only, `printed.py` / `columns.py`; no schema change (`rows` already takes
`cycle_length`). Without it R5 builds no loop on its first test case.

- `read_cycle`: a bare range (`2-3`; a bare `1` is already read).
- `read_cycle`: `… and beyond` / `onwards` with no leading `Cycle`
  (`4 and Beyond (if Applicable)`; the trailing `(…)` is already ignored).
- `read_cycle_length`: a bare number takes its unit from the cycle-length row label
  (`28` under `Approximate Duration (days)`), as timing and window already do.

**Gate.** Full suite green (VSCode), pins unchanged, coverage held.

## R5 — cycle ranges

The delay and the decision loop for `Cycle n-m` / `Cycle n+` (design § 6 R5), the
mixed single-then-range case, a missing cycle length (U4-8), the exit condition text
(U4-7). This is the first `ScheduledDecisionInstance` the assembler creates; unit
tests cover the plan and the built USDM. **No test in this issue expands a looped
timeline** — the expander would recurse without end until its own issue is merged.
Decide U4-7 and U4-8 before the branch. U4-7's proposal ("unless the caller supplies
one") has no field in the frozen schema; only a `HeaderNote` side channel could carry
it — to settle when U4-7 is taken.

Test case: NCT02107703 (cycles `1`, `2-3`, `4 and Beyond`, length 28) — candidate,
to be ruled when the issue is opened.

## Expander — follow a loop for one pass

Design § 7: take one pass through the range, then the decision's exit branch; never
unroll. Built and tested on hand-written USDM with a decision loop — it needs nothing
from R5 and can be done before, alongside or after it. Decide U4-11 first. Must be
merged before the next `usdm4` release that contains R5. Before release, check whether
SDW or `usdm4_pj` call this expander; if they do, they are consumers of the change.

## R6 — conditional timelines and copies

Sibling timelines with `entryCondition`; a column in two timelines (U4-5). Decide U4-5
first. Schema check: `entry_condition` is accepted only when the type's family is
`conditional` — confirm `unscheduled`, `early_termination` and `adverse_event` all map
there, or R6 needs a schema change.

## R7 — profile attachment

`attaches_to` → `Activity.timelineId`; unattached profiles reported. Schema already
carries it.

## R8 — gates

Only once U4-10 is taken. Under the frozen schema the gate must be told from printed
text alone; an answer that needs the caller to mark a gate column is a schema change.

## Outside R5–R8

U4-14 (crossover periods) needs a stage-1 marking for the washout link, which the
schema has no place for. When it is taken up it is a schema issue, merged first, with
`usdm4_protocol` and `protocol_corpus` told. Not part of R6.

## Outside this repo, alongside it

- **`usdm4_protocol`** stays on the last `usdm4` release with `TimelineInput` until its
  stage-1 work produces the new input: timelines by type, every header row by role,
  each value as printed text plus pattern form, cells with their text. That is its
  own plan in `usdm4_protocol`, driven from `protocol_corpus` `N70`.
- **`protocol_corpus`** maps its reviewer-stated ground truth into the new input with
  no judgement, and builds the reference USDM through this assembler. The pattern form
  of each header value is drafted by a corpus script (which must not reuse
  `usdm4_protocol`'s code) and checked by the reviewer, never typed —
  `protocol_corpus` issue 9.
- **Other callers** of `AssemblerInput.soa` are not known from this repo. Check before
  the release.

## Test protocols

Kept inside `tests/` as copied fixtures. Start simple: two single-timeline schedules
with no cycles for issue 63; a schedule printing one cycle in full then a
`Cycle 3-n` range for R4 and R5.
