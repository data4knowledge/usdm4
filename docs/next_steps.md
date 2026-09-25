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

## Session Log

Newest first. Cross-repo "save session" entries; pairs with `usdm4_protocol` and `udp_prism` logs.

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
timing → no `Timing` (R4), epoch-less column → empty-label epoch (D6), `Paricipant`
typo and placeholder procedure code (design § 8).

**Breaking change.** Every caller of `AssemblerInput.soa` breaks; `usdm4_protocol` stays
on the previous release until its stage-1 work produces the new input. Version is
Dave's to set.

**Found, not this issue.** A plain `git status` from the Cowork sandbox left
`.git/index.lock` behind (removed); use `git --no-optional-locks`.

**Next.** R4 — timing from the pattern, the anchor rule (D2), text-only timing (D3),
spans (D4), single cycles. Decide D2–D4 first. Corpus side: `protocol_corpus` issue 9
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
structure, rules R1–R9, the expander, open decisions D1–D12);
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

## 10. Timeline assembler upgrade (issue 63 built 2026-09-25; R4–R8 to come)

The timeline assembler is rebuilt on a text input with a pattern grammar, restructured
into parse → plan → build, and extended with cycles, conditional timelines, profile
attachment and gates, one issue per step. Design: `docs/timeline_assembler_design.md`.
Work order and gates: `docs/timeline_assembler_plan.md`. Open decisions D1–D12 are in the
design, § 9.
