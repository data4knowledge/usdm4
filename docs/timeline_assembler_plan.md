# Timeline assembler — plan of work

**Status: 2026-09-25. Rate of change: per issue. Retired when the last issue below is
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
  outside it. Timing spans (D4) and cycle patterns are R4; until then a span or
  cycle value is carried as text only. *Written 2026-09-25:* `parse_timing` →
  `TimingPoint(unit, value)`, `parse_window` → `Window(lower, upper, unit)`,
  `parse_label` (trimmed, non-empty), `PatternError(kind, value, expected)`; units
  normalised to singular lower case. Refused on top of design § 4: `Day -0`,
  `Day 08`, `Day +8`, non-ASCII digits and minus. Tests
  `tests/usdm4/assembler/timeline/test_grammar.py`.
- **63.3 Schema** (`assembler/schema/`). The timeline, column, value, activity, cell and
  footnote models of design § 3, validated at the boundary as today
  (`AssemblerInput` → `model_dump()`). `AssemblerInput.soa` becomes a list of the new
  timeline model. `TimelineInput` is removed from the schema package. The schema is
  complete from the start — `cycle`, `cycle_length`, `notes`, `entry_condition`,
  `attaches_to` included — so later issues add rules, not fields. Fields a rule does
  not use yet are carried, and their text reaches labels where design § 3.2 says so.
- **63.4 Restructure** into parse → plan → build, with naming moved out unchanged
  (design § 5). The plan builds today's straight chain only; cycles, decisions and
  profile attachment are later issues. The public surface of `TimelineAssembler` does
  not change.
- **63.5 Rewrite the pinned fixtures once in the new schema** and compare the output
  with the pin. The only allowed differences are those the new input causes by
  design, each listed in the session log with its reason:
  - timing taken from `pattern` instead of a caller's number;
  - an instance printed `C2D8` whose cycle is now in the `cycle` field and whose
    timing is `Day 8`: named `D8` until R4 puts the cycle back into the name;
  - `windowLabel`: today built from the numbers (`-1..+2 days`); in issue 63 it is
    built the same way from the parsed pattern, and becomes the printed text in R4
    (design R4.4).
- **63.6 Rewrite the unit tests** in `test_timeline_assembler.py` (121 test functions,
  123 collected) and `test_timeline_assembler_name_collisions.py` (19) against the new
  schema. Tests of today's internal methods move to the module the method moved to.
- **63.7 Docs.** This file and the design updated to *as built*; `lessons_learned.md`
  entry; session log entry in `next_steps.md`.

**Gate.** Full test suite green (run in VSCode, not Cowork). Every difference from the
pin explained. The d4k and CORE integration tests
(`tests/usdm4/integration/test_assembler_to_*`) green on the new schema.

**Breaking change.** Every caller of `AssemblerInput.soa` breaks. The version number
is Dave's to set; it should read as breaking.

## R4 — timing and single cycles

Cycle and cycle-length patterns added to the grammar; cycle text used in instance
names and labels (`C2D8`). Anchor rule (D2), timing from the pattern for points and
spans (D4), windows from the pattern with the printed text as `windowLabel`,
text-only timing (D3), mixed units. Every instance gets a `Timing` — today a blank
timepoint text loses all of a timeline's timings (design § 2). Cycle columns measured
from their cycle's `Day 1` (single cycles only). Decisions D2, D3, D4 taken before the
branch.

## R5 — cycle ranges and the expander

The delay and the decision loop for `Cycle n-m` / `Cycle n+` (design § 6 R5), the
mixed single-then-range case, a missing cycle length (D8), the exit condition text
(D7). The expander follows the loop for one pass (D11) — today it would recurse
without end on the loop (design § 7), so the expander change ships in the same
branch, never after. This is the first `ScheduledDecisionInstance` the assembler
creates; unit tests cover the plan and the built USDM, and the expander on a loop.

## R6 — conditional timelines and copies

Sibling timelines with `entryCondition`; a column in two timelines (D5).

## R7 — profile attachment

`attaches_to` → `Activity.timelineId`; unattached profiles reported.

## R8 — gates

Only once D10 is taken.

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
