# USDM4 validation engine — next steps

What's still open. The rule library is feature-complete (210 of 210 V4
DDF rules covered, 207 implemented + 3 delegated to DDF00082's schema
validation). CRE-vs-d4k reconciliation is at the no-known-d4k-bugs
state on CRE 0.16.0; the corpus baseline of record is
`validate/corpus_cre_0_16/` and the bug catalogue is in
`docs/cre_issues.md`. Read this file alongside `lessons_learned.md`
(the *how*) and `rule_generation_retrospective.md` (the as-built
record of the rule generation process).

> Per-rule status of every CRE-vs-d4k divergence currently lives in
> `docs/d4k_cre_divergence_index.md`. When something below references "the
> CT-membership cluster" or "the cross-reference traversal rules" or "the
> first-chain-head rules", that index has the row-by-row breakdown with
> file counts and authority pointers. Look there first.

## Working arrangement — three machines (2026-09-26)

This repo is **machine A** of three parallel threads (plan: `protocol_corpus/docs/next_steps.md`).
Work here, one issue each: cycle reading (#68, merged) → R5 cycle loop (#69, merged) → R6
(#70, merged) → R7 (#71, closed, not yet merged); R8 waits on U4-10. Copied columns (U4-5 shared `Encounter`)
wait on `protocol_corpus` `N78`, a schema change. The
expander is its own issue (decide U4-11 first): it is off the build path but blocks the
next release once R5 is merged. Order and schema checks: `timeline_assembler_plan.md`
§ *Order from here*. **The timeline input schema
(`src/usdm4/assembler/schema/schedule_timeline_schema.py`) is frozen** — `usdm4_protocol` (machine B)
builds against it; a change needs its own issue, merged first, with B and C told. Gate here: tests
and pins only. Corpus figures are run and quoted on machine C only. Nothing is written to
`protocol_corpus` from here.

## Session Log

Newest first. This repo's own log: every session that works a `usdm4` issue is entered here in
full, whichever Claude project drove it (see `CLAUDE.md` § *Session log*).

### 2026-09-26 — ISSUE 71 CLOSED, NOT YET MERGED (GitHub 71, branch `71-r7-profile-attachment`): profiles hang off the activity they name
- `usdm4 @ 71-r7-profile-attachment`. Driven from the USDM4 project (machine A).
- `protocol_corpus` touched: read `docs/issues.md`, the `ground_truth.yaml` of the seven protocols with a
  profile timeline, and NCT02674152's `build/` drafts; `scripts/draft_patterns.py` run read-only. **One
  write**, at Dave's request: resolved a stash-pop conflict in `docs/issues.md` (upstream N76/N77 kept,
  the local N78 row kept; open count 14). Not staged — Dave marks it resolved in GitHub Desktop.
- #70 (R6) found merged at session start (`main` @ e70966b); docs said "not yet merged" — corrected.
- **State:** full suite green (Dave, VSCode); GitHub issue closed; branch not yet merged into `main`.

**What it was.** `attaches_to` was accepted by the schema (profile timelines only) and then dropped:
`ParsedTimeline` had no field, and `Activity.timelineId` was always `None`. No profile was ever attached.

**Decisions (Dave), design § 9.**
- U4-31: a loop — the attached activity reached again through the profile it calls, directly or through
  other profiles — is not attached, error. Sharing an activity is fine; looping is not.
- U4-32: a parent activity is not attached, error (DDF00160).
- U4-33: an activity scheduled on no other timeline is attached, with a warning.
- U4-34: two profiles on one activity — the first in input order is attached, a later one is an error.
- Test case NCT02674152, profile attached to `Pharmacokinetics` (Dave). Pin fixture option A (Dave): the
  profile as printed is a 48-column course-spanning PK schedule, each column a day plus a clock time; only
  course 1 Day 1 (8 columns) is used, timed in minutes from the start of infusion.

**What changed.**
- `src/usdm4/assembler/timeline/columns.py` — `ParsedTimeline.attaches_to`.
- `src/usdm4/assembler/timeline_assembler.py` — `_build_one` returns the built timeline;
  `_attach_profiles`, `_activity_ids`, `_reaches`; the pass runs after every timeline is built.
- `tests/usdm4/assembler/test_timeline_assembler.py` — `TestProfileAttachment`, 18 tests.
- `tests/usdm4/assembler/test_timeline_pin.py` — case `nct02674152_r7`.
- `tests/usdm4/test_files/timeline_pin/input_nct02674152_r7.json` (new) — built by a one-off script from
  the corpus drafts: main table A as drafted (each value's printed text, the `draft_patterns` pattern only
  where flagged `ok`), 22 body rows; profile course 1 Day 1, `Minute -5` … `Minute 480`, course/day/time
  point as notes. Footnote markers dropped (no footnote text drafted). `expected_nct02674152_r7.json`
  (new) — saved from the built output.
- Docs: design § 9 U4-31–U4-34, § 18 as built. Plan: R6 merged, R7 decisions, test case, fixture. This
  file: *Working arrangement*, § 10 heading, the #70 entry's title.

**The numbers.** Sandbox (Python 3.10, no `cdisc-rules-engine`, `PYTHONPATH=src:.`): timeline, assembler,
schema and pin tests 817 pass; `timeline_assembler.py` and `columns.py` 100%. Ruff: no new findings
(three existing — two blind `except` in `timeline_assembler.py`, one in the R6 test class); format clean.
The new pin builds TIMELINE-1 (14 instances) and TIMELINE-2 (8 instances, `PT5M` before … `PT480M` after
the `0:00` anchor); `Pharmacokinetics.timelineId` = TIMELINE-2; no attachment message. Existing pins
unchanged. Full suite green (Dave, VSCode). Corpus gate not run (machine C).

**Rejected.** The full 48-column profile in the pin (brittle: pins degraded output unrelated to R7).
Attaching to `Administration of BI 836880` (Dave chose `Pharmacokinetics`). A warning only for U4-34
(hides a lost link); a wrapper activity holding two profiles (invents structure).

**Found, not this issue.**
- Corpus profiles are mostly course-spanning PK schedules (NCT02674152, NCT03433898), not single-anchor
  profiles. Activity-level attachment nests the whole schedule in every visit that ticks the activity;
  per-visit attachment (`ScheduledActivityInstance.timelineId`) needs a column reference the frozen schema
  lacks. Not logged — a schema row if a real case needs it.
- NCT02674152's table A header draft has its roles wrong: `Week` drafted as the timing, the
  `Day; visit window` row as the window. Unreviewed; the reviewer fixes it on the columns screen.
- No corpus ground truth records `attaches_to`; the corpus mapping needs it before the reference USDM
  carries an attachment (`soa_two_stage.md` lists profile attachment as still to state).

**Next.**
1. Merge #71.
2. N78 — copy reference on `ColumnInput`: a schema issue, merged first, B and C told.
3. U4-11 and the expander issue — before the next release.
4. R8 waits on U4-10.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

### 2026-09-26 — ISSUE 70 MERGED (GitHub 70, branch `70-r6-copied-columns`): conditional timelines entered on their printed condition; copied columns deferred to N78
- `usdm4 @ 70-r6-copied-columns`. Driven from the USDM4 project (machine A).
- `protocol_corpus` touched in passing: read `docs/issues.md`, `docs/next_steps.md` and
  NCT05565742's `ground_truth.yaml` / `build/soa_headers.yaml`; **one write**, at Dave's request —
  register row `N78` in `docs/issues.md` (open count 13 → 14), the copied-column fix. This departs
  from *Working arrangement* ("nothing is written to `protocol_corpus` from here"); Dave asked.
- #69 (R5) was merged before this session; its entry, back-filled this session, is below.
- **State:** full suite green (Dave, VSCode); GitHub issue closed; branch not yet merged into `main`.

**What it was.** Every timeline got `entryCondition` `Paricipant identified`, including a
conditional one (`unscheduled`, `early_termination`, `adverse_event`); the printed
`entry_condition` was validated by the schema and then dropped — `ParsedTimeline` had no field for
it. R6 as designed also shared an `Encounter` between timelines by column `id`. That cannot work:
the schema scopes column ids to one timeline, `validate/corpus_adapter.py` numbers them `c1…` per
timeline, and the `features` and `nct04557384` pins reuse `c1`/`c2` in several timelines for
different visits. Sharing by id would merge unrelated visits silently.

**Decisions (Dave), design § 9.**
- U4-5: target one shared `Encounter`, an instance per timeline. **Interim: one `Encounter` per
  timeline**, until an explicit copy reference exists — a schema change, logged as `protocol_corpus`
  `N78`, not a GitHub issue.
- U4-29: a conditional timeline with no printed `entry_condition` takes a default from its type
  (`Unscheduled visit`, `Early termination`, `Adverse event`) and a warning. The strings are
  Claude's; Dave took the rule.
- U4-30: when copies print different visit text, the first timeline in input order sets the label,
  with a warning. Taken, not built — needs N78.
- Test case NCT05565742: `ED` is a real copy — completers reach it after Visit 12, discontinuers
  enter it from the ET timeline (Dave). Claude's objection that ED did not belong in main was wrong
  and withdrawn.
- R6 schema check: all three conditional types map to family `conditional`; no schema change.

**What changed.**
- `src/usdm4/assembler/timeline/columns.py` — `ParsedTimeline.entry_condition`, carried from the input.
- `src/usdm4/assembler/timeline/build.py` — `_entry_condition`: conditional → printed text
  trimmed, else the type default plus warning; other families → `PLANNED_ENTRY_CONDITION` (old
  text, typo kept, design § 8). `CONDITIONAL_ENTRY_CONDITIONS` table.
- `tests/usdm4/assembler/test_timeline_assembler.py` — `TestConditionalTimelines`: printed text per
  type, trimming, blank = none, defaults and warning text, other families unchanged and silent,
  sibling not main, a guard that every conditional type in `FAMILY` has a default, and the copied
  column's two `Encounter`s pinned (points at N78).
- `tests/usdm4/assembler/test_timeline_pin.py` — case `nct05565742_r6`.
- `tests/usdm4/test_files/timeline_pin/input_nct05565742_r6.json` (new) — the frozen `nct05565742`
  main timeline unchanged, plus an `early_termination` timeline: column `c14` (ED), the 16
  activities marked in it, footnote `cell-4`, no title, no entry condition. The frozen
  `input_nct05565742.json` is untouched. `expected_nct05565742_r6.json` (new) — saved from the
  built output.
- Docs: design § 9 U4-5 (target + interim), U4-29, U4-30; § 17 as built. Plan: #69 merged, R6
  status and test case. This file: *Working arrangement*, § 10 heading.

**The numbers.** Sandbox (Python 3.10, no `cdisc-rules-engine`, `PYTHONPATH=src:.`): timeline,
assembler, schema and pin tests 798 pass; `build.py` and `columns.py` 100%. Ruff check and format
clean. The new pin builds TIMELINE-1 (14 instances, `Paricipant identified`) and TIMELINE-2 (1
instance, `Early termination`, warned); 15 encounters, 42 activities (none duplicated — shared by
name), 5 conditions. Existing pins unchanged. Full suite green (Dave, VSCode). Corpus gate not run
(machine C).

**Rejected.** Sharing by bare column id (silent merges in existing pins). Making ids span the
assembly (every caller renumbers or merges wrongly). Matching on id plus printed text (a guess;
contradicts U4-30). Re-saving the frozen `nct05565742` pin with the ED timeline — a new case
instead. A title for the ED timeline (none printed).

**Found, not this issue.**
- The ED timeline's instance is named `ED-2`, not `T2-ED`: `sai_name` de-duplicates across
  timelines instead of qualifying. Existing behaviour.
- The main timeline still warns `timing restarts (day 0 after day 540)` on column `c14` — the ED
  column's pattern `Day 0` in the frozen input (noted under #65).

**Next.**
1. R7 — profile attachment (`attaches_to` → `Activity.timelineId`); schema already carries it.
2. N78 — copy reference on `ColumnInput`: a schema issue, merged first, `usdm4_protocol` and
   `protocol_corpus` told; then the shared `Encounter` and U4-30.
3. U4-11 and the expander issue — before the next release, since R5 is merged.
4. R8 waits on U4-10.
R7 first: nothing blocks it, and N78 needs B and C coordinated.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

### 2026-09-26 — ISSUE 69 MERGED (GitHub 69, branch `69-r5-cycle-decision-loop`): cycle ranges built as a delay and a decision loop; CT/BC cache load 5x faster
Back-filled 2026-09-26 (the #70 session) from design § 16, the plan's R5 section and the branch's
two commits. The #69 session wrote no entry here; figures below are only those recorded in those
sources.

- `usdm4 @ 69-r5-cycle-decision-loop`. Driven from the USDM4 project (machine A). No sibling repo
  written.

**What it was.** A cycle-range column (`Cycle 3 and beyond`, `2-3`, `4+`) was parsed but not
planned: U4-25 gave it a zero timing and a warning. There was no loop, so a repeating cycle was one
pass with nothing to return to, and the assembler had never built a `ScheduledDecisionInstance`.

**Decisions (Dave), design § 9.**
- U4-7: the exit condition text is the fixed `cycle exit condition`. The real rule (progression,
  toxicity) is usually in the protocol body. Rejected: the printed range text (a heading, not a
  condition); caller-supplied text (no field in the frozen schema).
- U4-8: a range with no readable length is looped with the largest day printed in the range as
  its length (`D15` → 15 days), warned — a lower bound. Open edge: a range printing only `Day 1`
  gives a 1-day cycle. Rejected: a text-only delay (DDF00060; the expander crashes).
- Test case NCT05197426 (headers reviewed 2026-09-26): Cycle 1, Cycle 2, then `Cycle 3 and beyond`
  on Day 1 and Day 15, 4-week cycle. NCT02107703 kept as an edge test only.
- U4-25 superseded.

**What changed.**
- `src/usdm4/assembler/timeline/plan.py` — a range column is a cycle slot numbered by its first
  cycle; its `Day 1` (or U4-22 marker) chains from the previous cycle's `Day 1`, found by
  `_CycleStart.covers` so a range covering cycle *n* − 1 counts (`2-3` then `4+`). Ranges take
  lengths like single cycles, else U4-8. `_add_loops`: a `DECISION` node after each range's last
  column, `After` it by length − (last day − 1), `loop_to` the range's first node; an `END` node
  after the decision when that column is the last. No length, an inexact conversion, or a last day
  beyond the length: zero delay, warned.
- `src/usdm4/assembler/timeline/build.py` — `ScheduledDecisionInstance` in the range's epoch; its
  default loops back; one `ConditionAssignment` (`cycle exit condition`) to the next instance.
  End instance: no encounter, no activities, takes the exit. Range names `C3+D1`, `C2-3D1`.
- `src/usdm4/assembler/timeline/naming.py` — `decision_name` (`C3+DEC`), `end_name` (`T1-END`).
- `src/usdm4/file_cache/file_cache.py` — YAML read with `CSafeLoader` when PyYAML has libyaml, else
  `SafeLoader`; same result. Commit comment: 15 MB CT cache 18 s → 3 s, read by every `Builder`.
  This is the cause the #68 entry could not find (13 s first builder/CT load).
  `tests/usdm4/file_cache/test_file_cache.py` patches `yaml.load` to match.
- Tests: `test_plan.py` `TestRanges`, `TestNct02107703Headers` (ranges timed and looped); new
  `test_r5_nct05197426.py` (16 tests: single cycles, the range, and other shapes on structured
  input — bounded then open range, no `Day 1`, predose `Day -1`, weeks); pin `nct05197426` added.
  Existing pins unchanged. No test expands a looped timeline.
- Docs: design § 9 U4-7, U4-8, U4-25; § 16 as built; plan R5; this file's *Working arrangement*.

**Calls made while building, not ruled.**
- The loop returns to the range's first column, not `Day 1`, when a day is printed before `Day 1`
  in the range.
- Printed text supported but not held to the structured form's standard (Dave): `1 Cycle = 4
  Weeks` is not read as a length; the structured `4 weeks` is.
- A column after a range with no readable timing keeps U4-3's zero timing after the previous
  column, not after the decision.
- A single cycle and a range with the same first cycle share one cycle slot.

**The numbers.** Full suite green (Dave, VSCode); merged. Sandbox counts and coverage were not
recorded.

**Consequence.** R5 is merged, so no `usdm4` release is cut until the expander issue is merged
(plan § *Order from here*).

### 2026-09-26 — ISSUE 68 MERGED (GitHub 68, branch `68-cycle-and-ranges`): cycle ranges with no cycle word, cycle length unit from the row labels; order after R4 re-planned
- `usdm4 @ 68-cycle-and-ranges`. Driven from the USDM4 project (machine A). `protocol_corpus` read
  only (its `docs/next_steps.md` and NCT02107703's `build/timepoints.yaml` row labels); nothing
  written there.

**Plan re-ordered first (before the branch).** `timeline_assembler_plan.md` gains § *Order from
here*: cycle reading (#68) → R5 → R6 → R7; R8 waits on U4-10. The expander is split out of R5
into its own issue: nothing that builds USDM from a protocol calls it (no import in `usdm4/src`
outside `expander/`, `usdm4/validate`, `usdm4_protocol`, or live `protocol_corpus` code — only
`scripts/archive/review_gt.py`), so it gates the **release**, not the build. Once R5 is merged, no
release is cut until the expander issue is merged. R5's tests must not expand a looped timeline.
Each rule checked against the frozen input schema: U4-7's "unless the caller supplies one" has no
field (only a `HeaderNote` side channel); R6's `entry_condition` is accepted only for family
`conditional`; R8's gate must be told from printed text alone; U4-14 needs a schema issue of its
own. Design § 7 and this file's *Working arrangement* updated to match.

**What it was.** NCT02107703 prints `2-3` and `4 and Beyond (if Applicable)` in its cycle row and
`28` under `Approximate Duration (days)`. `_CYCLE_RE` made the cycle word optional but
`_CYCLE_RANGE_RE` required it, so a bare range was unread; `_CYCLE_LENGTH_RE` required a unit in the
value and `read_cycle_length` never saw a row label, unlike `read_timing` and `read_window`. All
three unread, so R5 could build no loop on its first test case.

**Decision (Dave), design § 9.** U4-28: a bare cycle length takes the cycle length row label's
unit, else the timing row label's ("there should be a unit stated in the timing row"); none → not
read, warned, never days. Taken as the row *label*; the unit of the timing values themselves (as
U4-19 does for windows) was not added — ask before adding it.

**What changed.**
- `src/usdm4/assembler/timeline/printed.py` — `_CYCLE_RANGE_RE` cycle word optional (`2-3`,
  `3-n`, `4+`, `4 and beyond`, `3 onwards`); `_CYCLE_LENGTH_RE` unit optional;
  `read_cycle_length(text, row_label, timing_row_label)`; module docstring.
- `src/usdm4/assembler/timeline/columns.py` — `_read_cycle_length` passes `rows.cycle_length` and
  `rows.timing`; a bare number with no unit anywhere gets its own warning (`_WARNED` sentinel stops
  the generic "not read" warning doubling it).
- `tests/usdm4/assembler/timeline/test_printed.py` — new range forms; must-not-fire (`6-3`,
  `1 Day 1`, `and beyond`); bare length with each label, label precedence, value unit wins, no
  unit anywhere, two lengths still refused.
- `tests/usdm4/assembler/timeline/test_columns.py` — row labels reach the reader, timing-row
  fallback, the no-unit warning text, pattern still wins.
- `tests/usdm4/assembler/timeline/test_plan.py` — `TestNct02107703Headers`: every header read, no
  warnings; ranges keep U4-25's zero timing until R5.
- Docs: design § 7 note, § 9 U4-28, § 15 as built; plan § *Order from here*, cycle-reading,
  R5, expander, R6–R8 schema notes; this file's *Working arrangement*.

**The numbers.** Sandbox (Python 3.10, `cdisc-rules-engine` not installable, run with
`PYTHONPATH=src:.`): timeline, assembler and pin tests 566 pass; the new tests 0.44 s;
`columns.py`, `printed.py` 100%. `plan.py` lines 304 and 447 uncovered **by that subset** — not
touched here, likely covered elsewhere in the full run; unconfirmed. Pins unchanged. Ruff check and
format clean. Full suite green (Dave, VSCode); merged.

**Slowness, measured.** Not from #68: in the subset, the only slow tests are
`test_timeline_pin[minimal]` and `TestState::test_clear_resets_everything`, 13 s each — the first
builder/CT load, unchanged code. Both readers return in ~1 ms on 5,000–10,000-character inputs, so
no regex backtracking. The full-suite cause is not found; CORE integration tests were not run here.

**Rejected.** Folding the reading gaps into R5 (R5 is already the first decision instance; reading
and planning are separate stages). Keeping the expander in R5's branch (the reason was release
safety, not build need). Defaulting a unitless cycle length to days as U4-15 does for timing.

**Found, not this issue.** Local branches `65`, `66`, `67` are merged into `main`.

**Next.**
1. ~~U4-7 and U4-8~~ (taken 2026-09-26, design § 9), then R5 on NCT05197426 (Dave, 2026-09-26; NCT02107703 an edge test only).
2. U4-11, then the expander issue — any time before the release containing R5.
3. U4-5, then R6; R7.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py
```

### 2026-09-26 — ISSUE 67 BUILT (GitHub 67, branch `67-cycles`): cycle Day 1 chained, start marker when none printed
Back-filled 2026-09-26 from `protocol_corpus/memory.md` (entry of the same date). Until then this repo's
sessions were logged only in the corpus.

- `usdm4 @ 67-cycles`. Driven from `protocol_corpus` (register row `N70`).

**What it was.** `plan._cycle_offset` (#66) put cycle *n*'s `Day 1` at (*n* − 1) × cycle *n*'s OWN
length from Cycle 1 — right only when all lengths are equal. A cycle printing no `Day 1` had its
columns timed from the anchor, with no node to hang from and nothing for R5's loop to return to.

**Decisions (Dave), design § 9.** U4-27 taken: cycle *n*'s `Day 1` = cycle *n* − 1's `Day 1` +
cycle *n* − 1's length. U4-22 re-taken: a cycle with no printed `Day 1` gets a start marker
`C{n}D1` — an instance, not a visit (no encounter, no activities). U4-23 narrowed to the previous
cycle's length.

**What changed.**
- `src/usdm4/assembler/timeline/plan.py` — `_CycleStart` (printed column or marker `C{n}D1`);
  `_cycle_starts` (first column with day 1 in days or weeks, else a marker before the cycle's first
  column; none for a cycle with no readable day); `_start_timing` (anchor fixed; *n* > 1 `After`
  cycle *n* − 1's `Day 1` by its length, exact conversion only; cycle 1 from the anchor as Day 1;
  else zero after the previous node + warning); `_marker_node`; `_cycle_node` times other columns
  from their cycle's `Day 1` node; `_anchor` makes the marker the anchor when the anchor column is
  in its cycle; `_interval`; `_Context`. `InstanceNode` gains `marker`, `cycle`, `epoch_column`,
  `key`; `relative_to` and `TimelinePlan.anchor` are node keys (column index or `C{n}D1`).
  `_cycle_offset`, `_position`, `_day_one` removed.
- `src/usdm4/assembler/timeline/build.py` — `_add_start_marker`: SAI `C{n}D1`, no encounter, no
  activities, epoch of the cycle's first column; timing `TIMC{n}D1`; SAIs and timings keyed by node key.
- `tests/usdm4/assembler/timeline/test_plan.py` — `TestSingleCycles` rewritten to the chain; new
  `TestCycleDayOne`; `TestAnchorWarnings.test_a_restart_in_a_cycle_column_is_not_warned` fixture moved
  its length to Cycle 1.
- `tests/usdm4/assembler/test_timeline_assembler.py` — end to end with a marker.
- `docs/timeline_assembler_design.md` — status, § 9 U4-22/U4-23/U4-27, R5 *Mixed*, § 13 note,
  new § 14 as built. `docs/timeline_assembler_plan.md` — status line.

**Behaviour changes.** Equal lengths: every `Day 1` lands where it did, but cycle *n* > 2's `Day 1`
is now relative to the previous `Day 1`, not the anchor. An unchainable `Day 1` is zero-timed but
its cycle's other columns keep their timing from it (#66 zeroed them all). `Cycle 2` with no
`Cycle 1` gets a zero `C2D1` and a warning (was 28 days). `Week 1` counts as a printed cycle start.

**The numbers.** Full suite passes (Dave, VSCode). Corpus gate (measured set, `usdm4_protocol`
`0.11.0.a10`): timelines 83 / 104, activities 1 / 104, unchanged — no rung reads timings.

**Rejected.** Summing earlier lengths as a "proposal"; splitting U4-27 and the marker into two issues.

**Next.** (1) Choose R5's test case — a simple cycle-range table (candidate NCT02107703, headers to
review first). (2) R5 cycle loop, then R6–R8. Decisions still proposals in § 9: U4-5–U4-12, U4-14.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py
```

### 2026-09-25 — ISSUE 66 BUILT (GitHub 66, branch `66-r4-part-2-single-cycles`): single cycles timed and named
Back-filled 2026-09-26 from `protocol_corpus/memory.md`.

- `usdm4 @ 66-r4-part-2-single-cycles`. R4 part 2 (design § 6 R4.3).

**What it was.** `cycle` and `cycle_length` reached the assembler as label text only; nothing read
them, so every cycle column was timed as if its day were a study day, and `C2D1` names came only
from a regex on timing text.

**Decisions (Dave), design § 9.** U4-22 a single cycle with no `Day 1` column measured from the
anchor (re-taken in #67). U4-23 cycle *n* > 1 with no readable length: zero timing plus a warning.
U4-24 a negative day in a cycle: `Day -1` one day before `Day 1`. U4-25 a cycle-range column before
R5: range parsed, not planned; zero timing plus a warning. U4-26 the day is read from `timing` only,
never `visit`. Test input: hand-written unit fixtures only; the NCT04557384 pin input carries no
cycle fields and is left for R5. Decision ids renamed `D<n>` → `U4-<n>` (clashed with day tokens).

**What changed.**
- `src/usdm4/assembler/timeline/grammar.py` — `CycleNumber`, `CycleRange` (`end=None` for
  `Cycle n+`), `CycleLength`; `parse_cycle`, `parse_cycle_length`.
- `src/usdm4/assembler/timeline/printed.py` — `read_cycle` (`Cycle 2`, `C2`, `C 2`, bare `2`;
  `Cycle 3-n`, `Cycles 3-6`, `C3-C6`, `Cycle 3+`, `… and beyond`, `… onwards`; trailing `(…)` ignored;
  `Subsequent Cycles` unread), `read_cycle_length` (`21 days`, `21-day cycle`, `Cycle = 21 days`,
  `(21 days)`; two lengths in one value unread).
- `src/usdm4/assembler/timeline/columns.py` — `Column.cycle`, `Column.cycle_length` read
  pattern → text → nothing, warnings naming timeline/column/field; `Column.cycle_day`.
- `src/usdm4/assembler/timeline/plan.py` — `_resolve_cycles` before the anchor; a cycle's length from
  any of its own columns (a second different length warned); exact conversion only; U4-23/U4-25
  remove the timing so U4-3 applies.
- `naming.py`, `build.py` — `sai_name(..., cycle=n)` → `C{n}D{day}`; text regex kept as fallback.
- Tests: `test_grammar.py`, `test_printed.py`, `test_columns.py`, `test_plan.py` (`TestSingleCycles`),
  `test_naming.py`, `test_timeline_assembler.py` (`C1D1 C1D8 C2D1 C2D8`, `PT0M P7D P21D P7D`).
- Docs: design status banner, § 9 U4-22–U4-27, § 13 as built; plan R4 status.

**The numbers.** Sandbox: timeline, assembler and pin tests 531 pass; `assembler/timeline/*` and
`timeline_assembler.py` 100% coverage. Full suite passes (Dave, VSCode). Pins unchanged. Corpus gate
unchanged (timelines 83 / 104, activities 1 / 104).

**Found, not this issue.** `naming.py` carries three ruff findings (RUF012 ×2, BLE001) that predate
the branch.

Re-verify: as #67.

### 2026-09-25 — ISSUE 65 BUILT (GitHub 65, branch `65-r4-part-1-timeline`): every instance timed, printed text read, time ranges decoded
Back-filled 2026-09-26 from `protocol_corpus/memory.md`.

- `usdm4 @ 65-r4-part-1-timeline`. R4 without cycles.

**What it was.** The assembler read only `pattern`. A caller holding only printed text got no
timings; a blank timing text built no `Timing` (`valueLabel` required, got `None`); a time range
(`Day -28 to Day -1`) was carried as text and timed at 0 from the anchor; a refused pattern dropped
the whole timeline.

**Decisions (Dave), design § 9.** Input restated: a caller sends printed text only, pattern only, or
both; with both, the pattern is used; the assembler reads printed text itself. U4-2 anchor = first
column with a timing ≥ 0, warning when none. U4-3 a text-only or `CCI` timing is `PT0M` `After` the
previous column plus a warning, nothing more. U4-4 a printed time range is sent as printed and
decoded here. U4-15 a bare number with no unit → days. U4-16 a window printed in the timing cell
loses to the window field, with a warning. U4-17 always build the timeline if at all possible — a
refused pattern warns and falls back to printed text. U4-18 `≤N` is `Day -N to Day -1` only before
the anchor. U4-19 a window with no unit takes the window row label's unit, else the timing's, else
days with a warning. U4-20 a time range crossing zero: `Day -3 to Day 2` is 4 days with no Day 0.
U4-21 labels of a decoded range: `valueLabel` the decoded start, `windowLabel` the window in pattern
form, `Timing.label` the printed text. Term: a scheduled time printed as a range is a **time range**,
never a "span".

**What changed.**
- `grammar.py` — `TimeRange`, `parse_time_range`, `is_time_range`.
- `printed.py` (new) — `read_timing`, `read_window`, `unit_of_label`, `is_blank`, `normalise`.
- `columns.py` — per field: pattern, else text, else nothing; refused pattern warns and falls back.
- `plan.py` — anchor warning, restart warning, `≤N`, zero-timing chain, `range_window`.
- `build.py` — every instance timed; labels per U4-21.
- `timeline_assembler.py` — no timeline dropped for a bad pattern.
- Tests: `test_printed.py` (new), `test_grammar.py`, `test_columns.py`, `test_plan.py`,
  `test_timeline_assembler.py`. Pin re-saved for `features`, `nct06454630`, `nct04557384`, every
  difference in design § 12.
- Docs: design §§ 1, 3.2, 4, 5, R4, § 9, § 12 as built; plan R4.

**The numbers.** Full suite passes (Dave, VSCode); `assembler/timeline/*` 100% coverage. Corpus gate
unchanged (timelines 83 / 104, activities 1 / 104) — no rung reads timings.

**Not this issue.** NCT05565742's pinned input has a trailing `Day 0` after `Day 540` (a drafting
error); the restart warning fires on it. Mixed units (R4.6) not built.

**Found.** In the Cowork sandbox even a read-only `git status` leaves `.git/index.lock`; use
`git --no-optional-locks`.

Re-verify: as #67.

### 2026-09-25 — ISSUE 64 BUILT (GitHub 64, branch `64-timeline-inputs-new-features`): redaction, per-value markers, row labels
Back-filled 2026-09-26 from `protocol_corpus/memory.md`.

- `usdm4 @ 64-timeline-inputs-new-features`. Input gaps found by `protocol_corpus` issue 9.

**What changed.**
- `grammar.py` — `REDACTED = "CCI"`, `is_redacted()` (any case, trimmed); caught before the parsers.
- `schema/schedule_timeline_schema.py` — `HEADER_FIELDS`; `HeaderValue.markers`;
  `ColumnInput.markers` removed (now refused); `ScheduleTimelineInput.rows` (header field → printed
  label, keys checked).
- `columns.py` — `Column.redacted` (set of fields), `Column.markers` (field → list, replaces
  `visit_markers`), `Column.all_markers`; a redacted field is never parsed, printed text stays the
  label; `ParsedTimeline.rows`.
- `build.py` — redacted epochs group by consecutive run (U4-13: a run after a non-redacted epoch is a
  new epoch, `CCI` / `CCI2`); a redacted timing or visit never names an instance (both redacted →
  `T1-SAI-n`); every header value's markers link to the timepoint, once per column.
- `validate/corpus_adapter.py` — markers onto the visit value, else timing, else epoch.
- Pin inputs — markers moved onto the visit value in 3 columns; expected output untouched.
- Tests: `test_grammar.py`, `test_columns.py`, `test_schedule_timeline_schema.py`,
  `test_timeline_assembler.py` (TestRedaction, per-value markers), `helpers.py`.
- Docs: design § 3, § 4, R2, R3, R9, U4-13, new § 11; plan #64 entry.
- Six unrelated files show whitespace-only changes from a repo-wide `ruff format`.

**The numbers.** Full suite green, pin unchanged (Dave, VSCode).

**Rejected.** One issue for the input gaps and R4 together. Redacted epochs as all one epoch, or one
per column.

**Not this issue.** A marker printed on a header row kept as a `note` has no home
(`HeaderNote` is `{role, text}`).

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/schema/test_schedule_timeline_schema.py tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py -v
```

### 2026-09-25 — ISSUE 63 BUILT (GitHub 63, branch `63-timeline-assembler`): text input, grammar, parse → plan → build, behaviour kept
- `usdm4 @ 63-timeline-assembler`. No sibling repo changed. Plan parts 63.1–63.7 done
  (`docs/timeline_assembler_plan.md`); as built in `docs/timeline_assembler_design.md` § 10.

**What changed.**
- `src/usdm4/assembler/schema/schedule_timeline_schema.py` — the new input,
  `ScheduleTimelineInput`: columns of header values (printed text + pattern form),
  activities with cells, footnotes; structure only; unknown keys refused.
  `AssemblerInput.soa` is `list[ScheduleTimelineInput] | None`. `schema/timeline_schema.py`
  (`TimelineInput`) deleted.
- `src/usdm4/assembler/timeline/grammar.py` — the pattern grammar for timing points,
  windows and labels; `PatternError` on anything outside it.
- `timeline/columns.py` (parse), `plan.py` (straight chain, one anchor, today's rules),
  `build.py` (USDM objects in the old creation order), `naming.py` (moved unchanged);
  `timeline_assembler.py` is the orchestrator, public surface unchanged.
- `validate/corpus_adapter.py` — converts the corpus's retired-shape `soa` with the
  63.5 rules (`timeline_input_to_schedule`), every table kept; `eval_corpus.py` reports
  `soa_timelines_converted`.

**The numbers.** Pin (`tests/usdm4/assembler/test_timeline_pin.py`): 4 of 5 inputs
identical to the pre-issue output; 1 difference, re-saved with its reason
(NCT04557384's PK timeline, caller unit `cycle`: anchor moves, 14 timings Before, Day 30
P30D → PT0M — both wrong until R4). Full suite green (run by Dave), new modules at 100%
coverage. Tests: `test_timeline_assembler.py` rewritten end to end; new
`tests/usdm4/assembler/timeline/` (grammar, columns, plan, naming, helpers);
`test_timeline_assembler_name_collisions.py` folded into `test_naming.py`.

**Calls made.** TLF (family) still emitted for profiles only — its presence marks a
profile downstream; the type extension waits. A timeline with a refused pattern or no
columns is reported and not built. Defects kept on purpose and pinned in tests: blank
timing → no `Timing` (R4), epoch-less column → empty-label epoch (U4-6), `Paricipant`
typo and placeholder procedure code (design § 8).

**Breaking change.** Every caller of `AssemblerInput.soa` breaks; `usdm4_protocol` stays
on the previous release until its stage-1 work produces the new input. Version is
Dave's to set.

**Found, not this issue.** A plain `git status` from the Cowork sandbox left
`.git/index.lock` behind (removed); use `git --no-optional-locks`.

**Next.** R4 — timing from the pattern, the anchor rule (U4-2), text-only timing (U4-3),
spans (U4-4), single cycles. Decide U4-2–U4-4 first. Corpus side: `protocol_corpus` issue 9
(pattern forms in the ground truth).

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py -v
python3 -m pytest tests -q
```

### 2026-09-25 — ISSUE 63 OPENED (GitHub 63, branch `63-timeline-assembler`): the timeline assembler is rebuilt on a text input
- `usdm4 @ 63-timeline-assembler`. Design and plan only; no code changed. Driven from
  `protocol_corpus` (register row `N70`, `docs/spec/soa_two_stage.md`).

**What it is.** The timeline assembler takes parallel positional lists with timing and
window numbers already parsed by the caller, builds a straight instance chain, and times
every column from one anchor. It has nowhere for a cycle, a cycle length or a second
timing row, so they are lost before it sees them; a cycle-relative day (`D8` in cycle 3)
is timed as 7 days after the anchor with no error; and no step exists where a delay or a
`ScheduledDecisionInstance` can go, so a repeating cycle cannot be a loop.

**Decided (Dave, 2026-09-25).**
- The input is TEXT, in a small strict pattern grammar other code can generate easily.
  Each header value carries the printed text (labels) and its pattern form (parsed). All
  parsing is in `usdm4`; a caller never hands over a number worked out from printed text.
- `TimelineInput` is retired for the schedule, not kept beside the new input. One input,
  one parse path. Breaking change.
- The assembler is restructured into parse → plan → build, naming in its own module,
  behaviour kept for R1–R3; later rules are separate issues.
- Cycles: a cycle has a length, a number or range, and days (CnDm). `Cycle n` is part of
  the chain; `Cycle n-m` / `Cycle n+` is one pass, then a delay to fill the cycle length,
  then a decision checking the exit condition that loops back or exits. Nothing is ever
  expanded.

**Files.** `docs/timeline_assembler_design.md` (the design: today, input schema, grammar,
structure, rules R1–R9, the expander, open decisions U4-1–U4-12);
`docs/timeline_assembler_plan.md` (the work order, gates, callers).

**Found, not this issue.** `entryCondition` is hard-coded `"Paricipant identified"`; every
BC mints a `Procedure` with placeholder code `12345`; `plannedDuration` is always `None`;
`_add_timepoints` passes `scheduledInstanceTimelineId`, which is not an API field (the
field is `timelineId`).

**Found, and in scope later.** The expander recurses without end on a loop: a
non-`days` decision condition takes the default, which in a cycle loop points back, and
on the main timeline every pass has the same tick. The expander change therefore ships
in the same branch as the cycle loop (R5 in the plan).

**Next.** 63.1: pin today's output, before any code moves. (Plan parts are 63.1–63.7, later issues R4–R8.)

### 2026-09-18 — ISSUE 58 CLOSED (GitHub 58, branch `58-assembler-orphans-and-timelines`): a table with no timepoint spine is skipped, not half-built
- `usdm4 @ 58-assembler-orphans-and-timelines`. No `usdm4_protocol` change. Gated live from
  `protocol_corpus`, whose register row N20 scoped this; that repo's `memory.md` 2026-09-18 holds
  the corpus-side figures and the reviewer decisions.

**What it was.** `TimelineAssembler._execute_one` registered a table's activities before building
that table's timepoints, timings and timeline. When the caller supplied a table whose
`timepoints.items` was empty, `_add_timing` raised `IndexError` on `timepoints[anchor_index]` and
`_add_timeline` raised `IndexError` on `instances[-1]`. Both were caught and logged and the run
continued — but the activities were already in `self._activities` and no `ScheduledActivityInstance`
had been created to reference them, so they reached the study design linked to nothing. Separately,
`_main_index` chose the main timeline before any of that ran, so when its pick was the table that
failed, no timeline in the study carried `mainTimeline` at all.

The timepoints list is the spine: epochs and encounters are attached to it by positional index.
A table without it can produce no SAI and therefore no `ScheduleTimeline`, so there was nothing to
salvage from building it.

**The fix.** `src/usdm4/assembler/timeline_assembler.py`, one method plus three helpers:

- `_has_spine(table)` — does the table carry the timepoints every other list is indexed against.
  Non-dict input answers False, which is how a malformed element now leaves the loop alone.
- `_assemblable(tables)` — the indices a timeline can be built from, reporting each rejection once
  with its ordinal and the count of activities discarded with it. The loss was otherwise invisible
  in the output, which is what made it hard to see.
- `_main_ordinal(tables, keep)` — the main flag is chosen over the assemblable tables only, so a
  skipped table cannot take it. `_main_index` is unchanged and still decides by `table_type`; it
  is simply handed a shorter list.
- `execute` iterates `keep` and passes `index + 1` as the ordinal, so a skipped table leaves a gap
  (`TIMELINE-1`, `TIMELINE-3`) rather than renaming the timelines that did assemble.

**The detector, and why it is that and not something else.** The condition is the empty spine, not
a classification of the table. Measured across `protocol_corpus`'s 104-protocol measurement set at
usdm4_protocol 0.11.0.a6: every crash has `SAI: 0` and no crash has `SAI > 0`. The correlation is
1:1, so the skip set and the crash set are provably the same set and the change cannot take a
table that was producing a timeline. Sweeping by package version mattered — the raw corpus-wide
sweep showed 30 crashes in 22 protocols, but 14 were stale results at 0.10.0 / 0.11.0a2 and four
of those were a different mechanism (`KeyError: 'encounter_instance'`) fixed upstream long ago.

**Gate PASSED live 2026-09-18**, 8 protocols re-extracted and compared:

| protocol | timelines | mainTimeline | activities | orphans | crashes | skips |
|---|---|---|---|---|---|---|
| NCT02107703 | 2 → 2 | 1 | 20 → 7 | 13 → 0 | 2 → 0 | 2 |
| NCT03486912 | 2 → 2 | 1 | 69 → 44 | 25 → 0 | 2 → 0 | 2 |
| NCT04586920 | 0 → 0 | 0 | 3 → 0 | 3 → 0 | 1 → 0 | 1 |
| NCT04682119 | 3 → 3 | 1 | 33 → 29 | 4 → 0 | 1 → 0 | 1 |
| NCT04776148 | 3 → 3 | 1 | 60 → 57 | 10 → 7 | 1 → 0 | 1 |
| NCT05262387 | 1 → 1 | 1 | 43 → 41 | 2 → 0 | 1 → 0 | 1 |
| NCT06085482 | 1 → 1 | 0 → 1 | 50 → 26 | 24 → 0 | 1 → 0 | 1 |
| NCT06868654 | 2 → 2 | 1 | 82 → 77 | 9 → 4 | 1 → 0 | 1 |

Timeline counts unchanged on every one, which was the prediction: the fix creates no timelines.
10 crashes → 0, replaced by 10 accounted-for skip lines. 90 orphan activities → 11. NCT06085482
regained its `mainTimeline`. NCT04586920's 0 is correct — it has no timelines, so nothing to flag.

**Regression evidence.** Before the change was written, a monkey-patched version was run against
the three real assembler-input shapes and five controls; afterwards the same harness was run
against the edited source and matched it. Every control is byte-identical to the pre-change run:
a single table passed as a dict, three tables, a one-timepoint table, a value-0 placeholder
timepoint, `table_type` steering the main flag to table 2, `execute(None)` and `execute([])`.
Timeline names and labels on surviving tables are unchanged (`TIMELINE-1` / `TIMELINE-3`,
`Main timeline` / `Timeline 3`). One control did change deliberately: `execute({})` surfaced 7
cascading errors and now surfaces 1. It still surfaces an error, which is what `_normalise`'s
docstring promises.

**Files changed**

- `src/usdm4/assembler/timeline_assembler.py` — `execute` filters before it builds; new
  `_has_spine`, `_assemblable`, `_main_ordinal`.
- `tests/usdm4/assembler/test_timeline_assembler.py` — new `TestTimelineAssemblerNoTimepointSpine`
  (14 tests) plus a `_spineless` fixture helper whose docstring records why the shape is what it
  is. `test_execute_outer_exception_on_non_dict_table` was rewritten and renamed: a non-dict
  element no longer reaches `_main_index`, so `execute`'s outer handler is now exercised by making
  the final ordering pass raise. Its old assertion was replaced by
  `test_non_dict_table_is_skipped_not_raised`. That rewrite is not optional housekeeping —
  `pytest.ini` enforces `--cov-fail-under=100`, so leaving the outer `except` unreached would fail
  the suite on coverage.

The new tests are weighted to must-not-fire: single table, several tables, a one-timepoint table
(the shortest real spine), a value-0 placeholder timepoint, and `table_type` steering the main
flag all have to be unaffected. The must-fire half covers no timeline, no orphans, the error
report, the main flag moving, the ordinal gap, all-tables-spineless, a missing `timepoints` key
and a null `timepoints` block.

**Re-verify:**

```
python3 -m pytest tests/usdm4/assembler/test_timeline_assembler.py -v --no-cov
python3 -m pytest
```

**Found, and not this issue.** Eleven orphan activities survive the fix — 7 on NCT04776148, 4 on
NCT06868654 — and the arithmetic shows they never came from a skipped table. They are activities
in *surviving* timelines that no SAI references, caused by `_activity_by_name` keying on the exact
normalised label: one activity printed three ways across three arm tables registers as three
activities, and only the one whose cells resolved gets linked. Logged as `protocol_corpus` register
row N22; the repo is undecided between normalising labels upstream and changing the registry key
here, and the population needs sweeping before either is worth building.

**Next.** Nothing open in this repo from this issue. The corpus register's next item is transposed
decode of sampling profiles, which is `usdm4_protocol` work.

### 2026-09-17 — timeline classification: `table_*` input fields declared, four d4k extensions, description freed for prose
- `usdm4 @ 57-let-the-soa-input-set-a-timelines-description` (0.30.0). Paired with
  `usdm4_protocol @ 45-classify-profile-tables-and-keep-them-instead-of-dropping-them` (0.11.0.a6),
  whose SoA extractor now classifies sampling and dosing profiles instead of discarding them and
  needs somewhere to record what kind of table a timeline came from.

**What changed**

1. **`TimelineInput` declares seven `table_*` fields** (`timeline_schema.py`) — and this is a
   defect fix, not just a feature. `Assembler.execute` validates with
   `AssemblerInput.model_validate` and passes `model_dump()` on, so pydantic's default
   `extra="ignore"` was stripping every key the model did not name. **`table_type` had never
   reached `TimelineAssembler._main_index`, and `table_title` never reached `_add_timeline`,
   through the live pipeline.** Nothing looked wrong because the main-timeline choice agrees with
   `_main_index`'s first-table fallback on every input tried, and the unit tests call
   `timeline_assembler.execute()` with raw dicts, bypassing the validation that was doing the
   damage.
2. **`ScheduleTimeline.description` is caller-settable** from `table_description`, generated
   string as the fallback. It is prose — the structure goes in the extensions.
3. **Four flat d4k extensions**, `extensions_d4k.py` 011-014: `TLF` family, `TLO` orientation,
   `TLU` unit, `TLP` placement. `_add_timeline` builds them through a new `_timeline_extensions`
   using the same `_builder.create(ExtensionAttribute, ...)` call `study_assembler` makes. Absent
   values are omitted rather than filled, so a missing attribute means "not measured". A caller
   that classifies nothing gets `[]`, as every timeline had before.

**Why extensions rather than a string in the description** (Dave's call): the description is prose
and would have to be parsed back; extensions are queryable by URL via `get_extension`, and the
backbone materialises them generically (`loader/schedule_timeline.py` calls
`merge_extension_attributes`, `serializer/walker.py` round-trips them), so the structure survives
into RDF and back. Flat rather than nested because every existing d4k extension is a flat
`valueString`.

**Verified** by constructing the real models: `ScheduleTimeline` accepts the four,
`get_extension(TLF_EXT_URL)` returns its value, a missing URL returns `None`, `to_json()` emits
urls 011-014. Live through the corpus on seven protocols: five profiles tagged with correct
family/orientation/unit/placement, no profile taking `mainTimeline`, both controls clean.

**Tests** — `tests/usdm4/assembler/schema/test_timeline_schema.py::TestTableClassificationFields`
(the seven fields survive a dump; `table_type` reaches the assembler; unclassified dumps as None;
feature blocks untouched) and seven in `test_timeline_assembler.py` for the description and the
extensions.

**NEXT** — nothing outstanding in this repo for this work. If a fifth extension is wanted for an
explicit timeline *kind*, it is 015; today profile-ness is implied by `TLF` being present, since
its values name profile families.

### 2026-06-18 — Amendment enrollment geographic scope derivation — NOT WORKING YET, tests needed

**Status: incomplete and unverified. No unit tests written for this change yet. Nothing run in Cowork (tests are VSCode-only).**

**Branch:** `39-further-ich-m11-updates`. Uncommitted — Dave commits. Cross-repo change; companions: `usdm4_protocol @ m11-rules` (renderer), `udp_prism @ main` (expected baseline). See their `docs/next_steps.md`.

**Change.** `src/usdm4/assembler/amendments_assembler.py` — `_create_enrollment` no longer hardcodes a global `forGeographicScope`. New helper `_enrollment_geographic_scope(data)` derives it from `data["scope"]` (the amendment's Amendment Scope field): global → Global (C68846, no code); first resolvable country → Country (C25464) + ISO code; else first region → Region (C41129) + code. It tries `scope["countries"]`/`scope["regions"]` **and `scope["unknown"]`** — the M11 step-1 extractor drops a bare country name (e.g. "France") into `unknown`, whereas the FHIR step-3 import populates `countries`. Output stays CT-valid: `GeographicScope.type` ∈ C207412 (DDF00144, ERROR) and a non-global scope carries a code (DDF00261, WARNING).

**Why.** Principle (USDM stores, M11 presents): USDM stores only the geographic scope; the Globally/Locally/By Cohort wording (C217275) is M11 presentation, applied in `usdm4_protocol` at render time — never stored here. Previously the enrollment scope was always Global, so a country/regional amendment lost its scope through the round-trip.

**Known gap.** A purely site- or cohort-scoped amendment has no C207412 area code to anchor a non-global scope, so it falls back to Global and logs a warning. Country/regional (the case this serves) derive correctly.

**To resume / verify (VSCode).** Write unit tests for `_enrollment_geographic_scope` (global / country-in-`countries` / country-in-`unknown` / region / site-fallback) and a round-trip check; run pytest; then run the udp_prism pipeline and confirm TCBCPT_03 renders "Locally". **End-to-end is not clean yet.**

## 1. `test_example_2` reconciliation

`tests/usdm4/test_package.py::test_example_2` is marked
`@pytest.mark.xfail(strict=True)` because `example_2.json` triggers
findings from rules added during the V4 build-out. Three buckets of
work; when the file produces zero failures the strict xfail flips to
XPASS and pytest fails the run — that's the signal to remove the
marker.

**a. Rule-interpretation revisit.** DDF00010 — SubjectEnrollment names
duplicating across amendments. The current model-wide
`(instanceType, name)` interpretation matches CORE's JSONata but is
too strict for real data; the rule text says "same parent class".
Revisit as per-parent uniqueness. See the
"Rule-text-vs-CORE-JSONata disagreement — policy" section of
`cre_issues.md` (the meta-rule that says "mirror CORE"); the question
here is whether DDF00010 is one of the rare exceptions where the spec
should change. DDF00010 is also the load-bearing example in the
`docs/d4k_cre_divergence_index.md` "d4k under-reporting" section.

**b. Fixture drift.** DDF00051 (Timing type CT — fixture uses labels
rather than decodes), DDF00157 (Environmental settings CT — invalid
C-codes), DDF00199, DDF00218 (other invalid CT decodes/codes), and
DDF00075 (Activities with no leaf references). Either fix the fixture
to use valid CT entries / proper refs, or — for DDF00075 — reconsider
the rule's strictness.

**c. Low-volume legit findings.** This was a snapshot from a pre-rewrite
run of the test fixtures (DDF00035, 40, 84, 87, 88, 101, 112, 153, 164,
165, 172, 181, 182, 185, 187, 188, 189, 201, 236, 247, 259). The
authoritative live list of every divergence the corpus exercises is now
in `docs/d4k_cre_divergence_index.md` — refresh that, not this snapshot,
before working through `test_example_2`. Several rules in the snapshot
have since been categorised: DDF00084 / 087 / 088 / 181 sit in the
divergence index; DDF00164 / 165 / 187 are in §4 below. The remainder
either no longer fire (rule rewrites between baselines) or remain
fixture-specific to `example_2.json` and need the per-finding triage the
original section called for.

## 2. CT cache refresh

DDF00237 (`plannedAge.unit` must be Age Unit C66781) is in
"skip gracefully" mode because C66781 isn't in the USDM cache yet.
Already registered in `ct_config.yaml`; activates after a refresh
against the CDISC Library API (requires network).

## 3. Real-file regression — corpus baseline supersedes `udp_prism` plan

The "run against 21 udp_prism protocols" plan was written before the
234-protocol corpus baseline at `validate/corpus_cre_0_16/` existed. The
corpus run already provides real-file regression coverage and is the
recipe `validate/README.md` documents. The work now is:

- **Re-run the corpus on each non-trivial rule library change** and
  diff the new `engine_diff.md` against the frozen baseline. The
  divergence index at `docs/d4k_cre_divergence_index.md` is the
  routing layer — every new divergence row should land in one of its
  categories.
- **Decide whether `udp_prism` is a separate validation set.** If yes,
  give it its own subdirectory under `validate/` with its own frozen
  baseline; if no, retire the plan. The 21 protocols don't currently
  exercise anything the 234-protocol corpus doesn't already cover.
- **Open d4k design calls surfaced by the corpus.** DDF00087 and
  DDF00088 (first-chain-head selection) are the standing candidates;
  the divergence index marks them as "Open d4k design call" pending
  decision. DDF00031 (timing FK consistency) and DDF00045 (V3 rule
  retained alongside V4 DDF00194) sit in the index as
  "Open / investigate" — categorise before the next corpus refresh.

## 4. Open d4k design decisions

Two known divergences from CORE that aren't bugs in either engine —
they're cases where the DDF text is ambiguous and d4k's reading is
defensibly stricter than CORE's. Both are documented here so the
question doesn't get re-litigated each time the divergence surfaces.
Both are also rows in `docs/d4k_cre_divergence_index.md` under "Open d4k
design calls".

**DDF00164 / DDF00165 — `"0"` as a section number.** d4k treats the rule
symmetrically: `displayX=true` iff `X` is truthy. Python's `bool("0")` is
`True`, so d4k sees `sectionNumber="0"` as "a number is specified" and
flags the mismatch when `displaySectionNumber=false`. CORE treats `"0"`
as "no section" and passes. The DDF text ("If a section number is to be
displayed then a number must be specified and vice versa") is ambiguous.
Decision: leave d4k as-is unless a canonical spec clarifies that `"0"`
is "unset". The alternative — strip `"0"` to empty string before the
truthy test — is data-specific hand-tuning.

**DDF00187 — XHTML wrapping context for self-namespacing fragments.**
A `NarrativeContentItem` whose text starts with its own nested
`<div xmlns="http://www.w3.org/1999/xhtml">` wrapper passes d4k but is
flagged by CORE ("body has non-whitespace character content"). The
mechanism: d4k wraps the fragment as
`<html>...<body><div>FRAGMENT</div></body></html>` so plain text, inline
markup, and block markup all validate; CORE wraps directly in `<body>`,
which produces a character-content error when the fragment itself
declares a namespace-prefixed wrapper. Decision: aligning this case
would need per-source heuristics (e.g. detect a top-level
`<div xmlns=...>` and re-parent) and the cost probably exceeds the
benefit for one outlier per protocol.

## 5. Upstream CRE asks

From the CRE 0.16.0 reconciliation (see `cre_issues.md` for context):

- Execution-error sentinels currently share the `errors` list with
  real findings, distinguishable only by string-matching against
  `_EXECUTION_ERROR_TYPES`. Worth raising upstream that they should
  be returned with a distinct status code rather than as
  string-tagged entries. The sentinel set has now grown to six
  strings; the maintenance burden will only increase.
- `_run_validation`'s unconditional stdout/stderr suppression
  compounded the 0.16 wrapper-API debug session. Make it
  configurable (env var or flag) so diagnostic runs can surface
  engine output.

## 6. (Optional) Real fixtures for hand-authored rules

Roughly 87 hand-authored rule tests carry `@pytest.mark.skip` on
their positive/negative fixture cases (metadata-only coverage). A
minimal JSON blob per rule converts each into a live behavioural
test, around 15 minutes per pair, so ~22 hours to do them all.
Worth starting with the structurally interesting rules — DDF00189
mutex, DDF00196 1:1-dict-of-sets, DDF00124 regex-ref, DDF00010
model-wide uniqueness, DDF00161 preorder-walk — and letting the
rest wait.

## 7. (Optional) M11 docx-side plan in `usdm4_protocol`

Per `usdm4_protocol/docs/m11_validation_plan.md`: `RuleM11S###`
(structural), `RuleM11T###` (technical), `RuleM11C###` (content),
generated from `m11_specification` at authoring time. Needs its
own planning pass — separate scope from the usdm4 engine work.

## 8. Assembler CORE conformance — known gaps

`tests/usdm4/integration/test_assembler_to_core.py::test_core_minimum_assembled_study`
runs CORE against the minimum assembler fixture and pins the failing
rule-id set as `_KNOWN_FAILING_RULES` (27 rules as of 2026-05-02). The
test is a regression detector: passes when the set is unchanged, fails
on additions or removals so the maintainer is forced to triage.

A 2026-05-02 bisection tried three fixture-only additions to clear
known gaps. Summary of cost vs benefit:

| Variant | Cleared | Introduced | Δ rules | Δ errors |
| --- | --- | --- | --- | --- |
| Sponsor identifier (`role: sponsor` non-standard scope) | CORE-000973, CORE-001054 | CORE-000971, CORE-001063; bumped CORE-000879 +2, CORE-000972 +1 | 0 | +3 |
| `population.demographics` with age range | CORE-000815 | CORE-001060, CORE-001061; bumped CORE-000879 +2 | +1 | +5 |
| Activity `actions.bcs` with two CDISC BCs | CORE-001076 | CORE-000427, CORE-000808, CORE-001006, CORE-001013 (8 errors) | +3 | +12 |

All three are net-negative, so the fixture was reverted and none of the
additions are in the codebase. Variant A (sponsor identifier) was the
closest to break-even and the only one worth revisiting once the
introduced rules can be cleared at the same time. The BC path (variant
C) caused 8 CORE-001013 "names of all instances of the same class must
be unique" errors — strong signal that either the BC's internal
sub-instances collide by name or the loaded BC structure duplicates
Codes. Worth investigating before activities reference BCs in any
fixture.

Of the 27 baseline rules, four have descriptions decoded from the
corpus baseline and need code (not fixture) work to clear:

- **CORE-000973** — exactly one `StudyRole(code="sponsor")`.
  `IdentificationAssembler` comment claims sponsor is wired through the
  identifier scope, but no code path actually creates a `StudyRole`
  with the sponsor code. Candidate fix: have `_create_organization`
  emit a sponsor `StudyRole` when the org's role is `"sponsor"`.
- **CORE-001036** — at least one endpoint with level=primary.
  `StudyDesignInput` has no `endpoints` / `objectives` field. Needs
  schema additions plus an objectives-and-endpoints assembler.
- **CORE-001016** — planned duration on the main timeline.
  `TimelineInput` has no duration field; nothing emits
  `ScheduleTimeline.plannedDuration`. Schema + assembler change.
- **CORE-001058** — study phase from the C66737 SDTM codelist.
  Fixture sets `trial_phase: "phase-1"`; the resulting `Code` has
  wrong `codeSystem` / `codeSystemVersion` / `decode` for C66737.
  Encoder gap in `study_design_assembler` / encoder.

The remaining 23 baseline rules don't fire on any of the 234 corpus
protocols, which means they're specific to the bare-bones shape of the
minimum fixture. They'll need individual investigation — likely a mix
of "real gap" and "fires only on degenerate input".

Order of attack when work resumes: fix CORE-000973 (smallest, has a
clear code path), then revisit variant A's introduced rules
(CORE-000971 needs a populated `legalAddress` on the sponsor org;
CORE-001063 needs decoding) so the sponsor-identifier change can land
cleanly.

## 9. Assembler conditions — drop policy and diagnostics (branch `51-condition-assembler-diagnostic`)

**Done 2026-07-30, full suite green.** `TimelineAssembler._add_conditions` opened
`if ref := item["reference"]:` with no `else`, so a condition the extractor could not
reference was discarded with no warning, no count and no log line. The mismatch case
warned; the empty case was invisible — which made four upstream bugs in
`usdm4_protocol`'s footnote handling look like "the extractor emits no conditions" when
it was emitting 13–73 per protocol and every one was evaporating here.

**Policy, recorded in the method docstring: skip, warn, count — never create unanchored.**
A `Condition` with empty `contextIds`/`appliesToIds` is a hard error downstream —
`usdm4_legacy_excel` rejects a condition with no `appliesTo` — so emitting them would
break the Excel round trip for every study. Anchoring is the extractor's job.

New `_condition_summary` emits one line per timeline, from a `finally` so a crash still
reports it, and for an empty condition list too:

```
Conditions T1: in=… referenced=… aligned=… dropped_no_ref=… dropped_no_match=…
```

A zero `in` means the extractor produced nothing; `dropped_no_ref` means it produced
footnotes with no marker; `dropped_no_match` means the marker exists but nothing in the
timeline carries it. Three different bugs in three different places — the old single
warning covered only the last.

Tests: `TestTimelineAssemblerConditionDiagnostics` in
`tests/usdm4/assembler/test_timeline_assembler.py` (8 tests — the three unreferenced
shapes parametrised, the skip-not-create policy pin, and the summary cases including the
exception path).

Full context and the usdm4_protocol half: `usdm4_protocol/docs/next_steps.md` § Session
Log, session 12 (2026-07-30).

## 10. Timeline assembler upgrade (issues 63–70 merged; 71 (R7) closed 2026-09-26, not yet merged; R8, N78 and the expander to come)

The timeline assembler is rebuilt on a text input with a pattern grammar, restructured
into parse → plan → build, and extended with cycles, conditional timelines, profile
attachment and gates, one issue per step. Design: `docs/timeline_assembler_design.md`.
Work order and gates: `docs/timeline_assembler_plan.md`. Decisions U4-1–U4-34 (open and taken) are in the
design, § 9.
