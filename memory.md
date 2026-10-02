# USDM4 — Working Memory

The session log. **Rate of change: per session, appended. Never retired.**

An entry is a dated record of what happened, and the file's one job is total
recall — a cold start on another machine reads this plus `docs/lessons_learned.md`
plus `CLAUDE.md` and resumes without the chat. Nothing is removed.

Entries are appended at the END, headed `## YYYY-MM-DD — title` and nothing else.
Several entries may share a date. The plan is `docs/next_steps.md`, rewritten
wholesale; it holds no log.

Every session that works a `usdm4` issue is entered here in full, whichever
Claude project drove it. Entries up to 2026-10-02 were moved verbatim from the
Session Log formerly in `docs/next_steps.md`.

References in entries up to 2026-09-27 to "design § n" and "plan …" are to
`timeline_assembler_design.md` and `timeline_assembler_plan.md`, both retired that day (git
history). The design's as-built sections are now in the entries they belong to; the current
rules and decisions (U4-n) are in `docs/spec/timeline_assembler.md`.

## 2026-06-18 — Amendment enrollment geographic scope derivation — NOT WORKING YET, tests needed

**Status: incomplete and unverified. No unit tests written for this change yet. Nothing run in Cowork (tests are VSCode-only).**

**Branch:** `39-further-ich-m11-updates`. Uncommitted — Dave commits. Cross-repo change; companions: `usdm4_protocol @ m11-rules` (renderer), `udp_prism @ main` (expected baseline). See their `docs/next_steps.md`.

**Change.** `src/usdm4/assembler/amendments_assembler.py` — `_create_enrollment` no longer hardcodes a global `forGeographicScope`. New helper `_enrollment_geographic_scope(data)` derives it from `data["scope"]` (the amendment's Amendment Scope field): global → Global (C68846, no code); first resolvable country → Country (C25464) + ISO code; else first region → Region (C41129) + code. It tries `scope["countries"]`/`scope["regions"]` **and `scope["unknown"]`** — the M11 step-1 extractor drops a bare country name (e.g. "France") into `unknown`, whereas the FHIR step-3 import populates `countries`. Output stays CT-valid: `GeographicScope.type` ∈ C207412 (DDF00144, ERROR) and a non-global scope carries a code (DDF00261, WARNING).

**Why.** Principle (USDM stores, M11 presents): USDM stores only the geographic scope; the Globally/Locally/By Cohort wording (C217275) is M11 presentation, applied in `usdm4_protocol` at render time — never stored here. Previously the enrollment scope was always Global, so a country/regional amendment lost its scope through the round-trip.

**Known gap.** A purely site- or cohort-scoped amendment has no C207412 area code to anchor a non-global scope, so it falls back to Global and logs a warning. Country/regional (the case this serves) derive correctly.

**To resume / verify (VSCode).** Write unit tests for `_enrollment_geographic_scope` (global / country-in-`countries` / country-in-`unknown` / region / site-fallback) and a round-trip check; run pytest; then run the udp_prism pipeline and confirm TCBCPT_03 renders "Locally". **End-to-end is not clean yet.**

## 2026-07-30 — Assembler conditions: drop policy and diagnostics (branch `51-condition-assembler-diagnostic`)

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

## 2026-08-03 — TagResolver fixed and exposed
Moved 2026-09-27 from the retired repo-root `memory.md`.

- utility/tag_resolver.py already held the recursive usdm:ref/usdm:tag
  resolver (from usdm_utility/to_m11.py) but was broken: imported DataStore
  from usdm3 (eliminated in the v3→v4 merge) → fixed to
  usdm4.data_store.data_store. soup.py MODULE string fixed
  (was "usdm4_fhir.m11.soup.soup").
- beautifulsoup4>=4.9 declared in setup.py + requirements.txt — first
  direct bs4 use in usdm4 (previously only transitive via
  cdisc-rules-engine).
- Public access added: Builder.data_store property (None before seed());
  USDM4.tag_resolver(file_path, errors) → TagResolver over a decomposed
  DataStore. TagResolver + DataStore exported from usdm4 __init__.
- New integration test tests/usdm4/utility/test_tag_resolver_integration.py
  using sample_usdm_7.json (dictionary min_age/max_age tags → nested
  usdm:ref → Quantity values; exercises the recursion for real).
- Placement decision (Dave): usdm:ref + usdm:tag are USDM-standard →
  resolver lives in usdm4. usdm:macro is authoring sugar → expanded at
  workbook import by usdm4_excel; never appears in USDM JSON, resolver
  ignores it by design.
- usdm_utility/to_m11.py stays as-is: throwaway test code (Dave), not to be
  refactored onto the resolver.
- Escaping FIXED (Dave, 2026-08-03): resolver output is destined for
  rendered documents (usdm4_protocol / usdm4), so replace_with now inserts
  parsed soup, not text — refs to XHTML-valued attributes come through as
  markup, nested tags inside resolve too. Verified standalone against
  sample_usdm_7 (scalar, plain, rich cases).
- Stray usdm:macro in USDM content: TagResolver now WARNS ("Unexpanded
  usdm:macro...") and leaves the tag in place (was silent pass-through).
  Macro EXPANSION stays in usdm4_excel only — the engine needs workbook
  context (import-time name/xref registrations, workbook dir for images);
  no second consumer exists. Revisit lifting it into usdm4 only if
  usdm4_protocol or another non-Excel author needs macros.
- Suite state: ALL TESTS PASS (Dave's run, 2026-08-03), incl. the new
  test_tag_resolver_integration.py.

## 2026-08-03 — `api` `__all__` gaps: CommentAnnotation, BiospecimenRetention, ConditionAssignment
Moved 2026-09-27 from the retired repo-root `memory.md`.

- usdm4_excel's annotations_and_abbreviations parity fixture exposed:
  CommentAnnotation missing from api/__init__.py __all__, which seeds the
  Builder IdManager → builder.create KeyError, every note creation
  failed. Audit found two more latent ones also builder-created by
  usdm4_excel readers: BiospecimenRetention, ConditionAssignment. All
  three added to imports + __all__.
- Third recurrence of this bug class (12076cf fixed MedicalDevice/
  Substance/ProductOrganizationRole). New guard test
  tests/usdm4/api/test_api_all_complete.py: scans api/*.py class defs,
  subtracts a NON_CONCRETE list (ApiBase*/Base*/Extension/Identifier/
  PopulationDefinition/QuantityRange), asserts the rest are in __all__.
- Why usdm4_excel unit tests never caught it: their SheetFramework mocks
  IdManager.build_id — only real end-to-end imports hit the id index.

## 2026-08-07 — ISSUE 54 (GitHub 54, branch `54-core-engine`): CoreValidator follows executionStatus; bundled USDM schema
Moved 2026-09-27 from the retired repo-root `memory.md`.

- Root causes of the exec-error flood (6,749/file) and dropped findings,
  found by diffing our wrapper against the CORE CLI (same engine 0.16.0,
  same rules — byte-identical; same json):
  1. _classify_errors ignored the engine's per-result executionStatus and
     string-matched error text. "skipped" results (rule doesn't apply to
     entity — SkippedReason lists the very strings we matched) flooded
     execution_errors. Now: skipped→dropped, "issue reported"→findings,
     "execution error"→exec errors; string set kept only as no-status
     fallback. Matches the CLI report logic (usdm_report_data.py).
  2. LibraryMetadataContainer got no standard_schema_definition, so
     JsonSchemaCheckDatasetBuilder rules (CORE-000938/DDF00126 cardinality)
     silently found nothing. The CLI ships usdm-<v>-schema.pkl — a pydantic
     model_json_schema() dump of the API Wrapper (NOT our
     rules/library/schema/usdm_v4-0-0.json, which is the full OpenAPI doc).
     DECIDED (Dave): vendor CORE's shipped schemas, converted pkl→JSON, as
     core/data/usdm-{3-0,4-0}-schema.json (source: cdisc-rules-engine
     v0.16.0, c78b05c); manual refresh when CORE updates. NOTE: our Wrapper
     model has drifted (84 $defs vs shipped 82, Base* classes) — vendoring
     keeps parity with official CORE; disagreements surface as findings.
- Parity verified: NCT04573309 49 findings + 1 exec error; NCT03637764
  84 + 1 — both match the CLI number-for-number per rule.
- Changed: core_validator.py, setup.py (package_data), new core/data/*.json,
  tests (+8, status classification + schema loading). core/ subset: 177
  pass, core_validator.py 100% cov. Ruff default-rules + format clean.
- Dave's full-suite run then surfaced 2 baseline failures = the fix seeing
  what was invisible: (a) sample_usdm_7.json had 'extensionAtrtibutes' key
  typo x3 + mangled instanceType values x7 (extensionClass/extensionCLass/
  ExtensionCLass/extensionAttribute) in its extension subtree — ALL FIXED
  in the file (Dave's call: clean exemplar, not as-received artifact);
  cleared CORE-000937, CORE-000949 and d4k DDF00082 with no baseline edit.
  (b) assembled-minimum: CORE-000938 ADDED to _KNOWN_FAILING_RULES with
  comment — three real assembler gaps on the minimum fixture
  (StudyAmendment.changes, InterventionalStudyDesign.arms, .studyCells all
  emitted []); assembler fix is separate work, candidate for its own issue.
  Full suite GREEN (Dave's run, 2026-08-07) — issue #54 resolved.

## 2026-09-17 — timeline classification: `table_*` input fields declared, four d4k extensions, description freed for prose
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

## 2026-09-18 — ISSUE 58 CLOSED (GitHub 58, branch `58-assembler-orphans-and-timelines`): a table with no timepoint spine is skipped, not half-built
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

## 2026-09-25 — ISSUE 63 OPENED (GitHub 63, branch `63-timeline-assembler`): the timeline assembler is rebuilt on a text input
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

## 2026-09-25 — ISSUE 63 BUILT (GitHub 63, branch `63-timeline-assembler`): text input, grammar, parse → plan → build, behaviour kept
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

**Before this issue** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 2).

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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 10).

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

## 2026-09-25 — ISSUE 64 BUILT (GitHub 64, branch `64-timeline-inputs-new-features`): redaction, per-value markers, row labels
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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 11).

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

## 2026-09-25 — ISSUE 65 BUILT (GitHub 65, branch `65-r4-part-1-timeline`): every instance timed, printed text read, time ranges decoded
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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 12).

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

## 2026-09-25 — ISSUE 66 BUILT (GitHub 66, branch `66-r4-part-2-single-cycles`): single cycles timed and named
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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 13).

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

## 2026-09-26 — ISSUE 67 BUILT (GitHub 67, branch `67-cycles`): cycle Day 1 chained, start marker when none printed
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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 14).

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

## 2026-09-26 — ISSUE 68 MERGED (GitHub 68, branch `68-cycle-and-ranges`): cycle ranges with no cycle word, cycle length unit from the row labels; order after R4 re-planned
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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 15).

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

## 2026-09-26 — ISSUE 69 MERGED (GitHub 69, branch `69-r5-cycle-decision-loop`): cycle ranges built as a delay and a decision loop; CT/BC cache load 5x faster
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

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 16).

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

## 2026-09-26 — ISSUE 70 MERGED (GitHub 70, branch `70-r6-copied-columns`): conditional timelines entered on their printed condition; copied columns deferred to `protocol_corpus` N78
- `usdm4 @ 70-r6-copied-columns`. Driven from the USDM4 project (machine A).
- `protocol_corpus` touched in passing: read `docs/issues.md`, `docs/next_steps.md` and
  NCT05565742's `ground_truth.yaml` / `build/soa_headers.yaml`; **one write**, at Dave's request —
  register row `N78` in `protocol_corpus/docs/issues.md` (open count 13 → 14), the copied-column fix. This departs
  from *Working arrangement* ("nothing is written to `protocol_corpus` from here"); Dave asked.
- #69 (R5) was merged before this session; its entry, back-filled this session, is below.
- **State:** full suite green (Dave, VSCode); GitHub issue closed; **merged to `main`**.

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
  with a warning. Taken, not built — needs `protocol_corpus` N78.
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
  column's two `Encounter`s pinned (points at `protocol_corpus` N78).
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
2. `protocol_corpus` N78 — copy reference on `ColumnInput`: a schema issue, merged first, `usdm4_protocol` and
   `protocol_corpus` told; then the shared `Encounter` and U4-30.
3. U4-11 and the expander issue — before the next release, since R5 is merged.
4. R8 waits on U4-10.
R7 first: nothing blocks it, and `protocol_corpus` N78 needs B and C coordinated.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 17).

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

## 2026-09-26 — ISSUE 71 MERGED (GitHub 71, branch `71-r7-profile-attachment`): profiles hang off the activity they name
- `usdm4 @ 71-r7-profile-attachment`. Driven from the USDM4 project (machine A).
- `protocol_corpus` touched: read `docs/issues.md`, the `ground_truth.yaml` of the seven protocols with a
  profile timeline, and NCT02674152's `build/` drafts; `scripts/draft_patterns.py` run read-only. **One
  write**, at Dave's request: resolved a stash-pop conflict in `protocol_corpus/docs/issues.md` (upstream N76/N77
  kept, the local N78 row kept; open count 14). Not staged — Dave marks it resolved in GitHub Desktop.
- #70 (R6) found merged at session start (`main` @ e70966b); docs said "not yet merged" — corrected.
- **State:** full suite green (Dave, VSCode); GitHub issue closed; **merged to `main`**.

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
2. `protocol_corpus` N78 — copy reference on `ColumnInput`: a schema issue, merged first, B and C told.
3. U4-11 and the expander issue — before the next release.
4. R8 waits on U4-10.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 18).

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

## 2026-09-26 — ISSUE 73 MERGED (GitHub 73, branch `73-update-schema`): structured input, `usdm4` never reads printed text
- `usdm4 @ 73-update-schema`. Driven from the USDM4 project (machine A). Started as R8 (#72, branch
  `72-r8-variable-delay`, docs only so far); R8 needed the input to carry a delay, which became #73.
- `protocol_corpus` touched: read only (`docs/issues.md`, `docs/spec/`, ground truths of NCT03069989,
  NCT03360071, NCT03421379, NCT04050553 — searched for washout columns). Nothing written.
- **State:** full suite green (Dave, VSCode); **merged to `main`**. (Telling B and C dropped
  2026-09-27 with the three-machine arrangement.)

**Decisions (Dave), design § 9.**
- U4-10 reframed: a gate is a variable delay (`Washout 2-10 days`), built with R5's loop — start node →
  1-day delay → decision; exit `(≥ 2 days and washed out) or 10 days`, else back to the start node.
  `Screening ≤28 days` / `Run-in 2 weeks` are ordinary timings. Open: the exit text.
- U4-14: in theory not needed — a crossover period chains after the washout gate like a cycle; to prove
  on R8's test case (NCT03069989 checked by Dave; NCT03421379 old-shape).
- U4-35 (new): `usdm4` is algorithm only; the caller structures every value; `text` carried, never read,
  used only as a label (empty → rendered). Units `minutes … years`. Cycle `{first, last}`. Cycle length
  `{value, unit}`. Time range `{start, end, unit}` in printed numbers — a range is not a window; USDM
  storage and Day 0 arithmetic are `usdm4`'s (briefly taken as "stage 1 sends timing + window",
  reversed). `day_zero` flag, default Day 1; a printed Day 0 with the flag false is a warning, flag
  used. `redacted: true` replaces `CCI`. Delay `{min, max, unit}`. `protocol_corpus` N78 kept out.
- Not ruled by Dave (Claude's addition, flagged): a value with text and no structure is accepted as
  "could not structure" — carried as its label, not read, warned. The pins need it (e.g. course lists
  `1, 2, 3, 4`, window `d1`, which the old code could not read either).

**What changed.** Listed under *As built* below. Schema rewritten (value objects, `day_zero`, `delay`);
`timeline/values.py` new; `columns.py` rewritten; `plan.py` (Day 0 from the flag, `≤N` and
`has_zero_timepoint` gone); `build.py` (cell-window label path gone); `grammar.py`, `printed.py` and
their tests deleted; `validate/corpus_adapter.py` emits the structured form. Tests: compact fixture
notation converted by `tests/usdm4/assembler/timeline/structure.py`; `test_columns.py` and schema tests
rewritten; printed-text tests deleted or rewritten. Pin inputs converted by a one-off script run on the
OLD parse (`convert_pins.py`, a one-off kept outside the repo) — every expected output unchanged. Docs: design § 3, § 4
(retired), § 9, § 19; plan; this file.

**The numbers.** Sandbox (Python 3.10, no `cdisc-rules-engine`, `PYTHONPATH=src:.`):
`tests/usdm4/assembler` 1,356 pass, 2 skipped; the 8 pins unchanged; `schedule_timeline_schema.py`,
`columns.py`, `values.py`, `build.py`, `timeline_assembler.py` 100%; `plan.py` 99% over the timeline
tests alone, the same two lines as before the change (454/596 then, 458/600 now). Ruff: no new findings
beyond the baseline; format clean. Full suite green in VSCode (Dave), after a fix: the
integration fixture (`tests/usdm4/integration/conftest.py`) still sent `{text, pattern}` — converted.

**Rejected.** Pattern strings for the delay (`2 to 10 days`) — text in, however strict. A structured
`delay` only, patterns kept elsewhere (a mixed interface). Stage 1 sending a range as timing + window
(pushes a USDM workaround and the Day 0 arithmetic onto B and C). Inferring Day 0 from the columns.

**Found, not this issue.**
- NCT03069989's reviewed header has no timing row: every day value and the washout
  `(7-28 days between doses)` sit in the visit row, unstructured. It needs structured timings and a
  `delay` in its ground truth before it can be R8's pin.
- The only real gates found are crossover washouts (NCT03069989, NCT03421379); the scan searched the
  word "washout" only.

**Process slip.** A version-control command was run by mistake while deleting files; it left an empty
index lock file in the repo's version-control folder, removed at once. Nothing else changed. The rule
stands: Claude runs no version-control commands in Dave's repos.

**Next** (in order: B and C are blocked by #73 until told; R8 needs #73's `delay`).
1. ~~Merge #73~~ — done.
2. Tell B (`usdm4_protocol` emits the structured form) and C (`assemble_ground_truth`, the columns
   screen and ground-truth storage; issue 13's "range as start + window" is replaced by the range form;
   `day_zero` per protocol).
3. R8 (#72): U4-10 exit text, then build on NCT03069989 (patterns/structure needed in its ground truth).
4. `protocol_corpus` N78; U4-11 and the expander before the next release.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

**The pattern grammar, retired by this issue** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 4).

Issues 63–71 took each header value as printed text plus a *pattern form*
(`Day 1`, `Day -28 to Day -1`, `-3..+3 days`, `Cycle 3+`, `21 days`, `CCI`), parsed
by `timeline/grammar.py`, with `timeline/printed.py` reading printed text when there
was no pattern. Both are deleted: that was `usdm4` reading text (U4-35). The
grammar's notation survives in two places only — as the rendered label of a value sent
with no text, and as the compact fixture notation of the tests
(`tests/usdm4/assembler/timeline/structure.py`). Retired with it: `≤N` read by
`usdm4` (U4-18), a window read from the timing cell (U4-16), units from row labels
(U4-28), time ranges decoded from text (U4-4's text path).

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 19).

Structured input (U4-35). Branch `73-update-schema`.

- `schema/schedule_timeline_schema.py` — `HeaderValue {text, pattern}` replaced by value
  objects: `LabelValue` (epoch, visit), `TimingValue` (point or range), `WindowValue`,
  `CycleValue`, `QuantityValue` (cycle length), `DelayValue` (new, R8). Each carries
  `text`, `markers`, `redacted`; validation per § 3.2. `ColumnInput.delay`;
  `ScheduleTimelineInput.day_zero`; `VALUE_FIELDS` = header fields + `delay`. The
  docstring's "a caller never hands over a number it has worked out from printed text"
  replaced by U4-35.
- `timeline/values.py` (new) — the parsed value types (moved from `grammar.py`), `Delay`,
  and `render_*` for labels when a value has no text.
- `timeline/columns.py` — copies the structure across; no fallback to text. Text only:
  a warning for window, cycle, cycle length, delay (a timing is warned by the plan,
  U4-3). `Column.up_to` gone; `window_from` is `"window"` or `"range"`; `Column.delay`;
  `ParsedTimeline.day_zero`. A delay is carried with a warning ("not built until R8").
- `timeline/plan.py` — Day 0 from `day_zero`, not inferred (`has_zero_timepoint`
  deleted); a printed `Day 0` with the flag false is warned, flag used.
  `_resolve_up_to` deleted. `is_placeholder` is "no readable timing" (it read the
  label's emptiness before). `interval_from_anchor` takes `has_zero`.
- `timeline/build.py` — the "window printed in the timing cell" label path gone.
- Deleted: `timeline/grammar.py`, `timeline/printed.py` and their tests.
- `validate/corpus_adapter.py` — emits the structured form; `day_zero` true when a
  non-placeholder column is timed at day 0 (what the plan used to infer); a window in
  an unknown unit is text only.
- Tests: fixtures keep their compact notation, turned into structured objects by
  `tests/usdm4/assembler/timeline/structure.py` (test code only). `test_columns.py`
  and the schema tests rewritten against the contract itself. Printed-text reading
  tests deleted or rewritten as caller-structured equivalents.
- Pins (the timeline pin test's input files, `tests/usdm4/test_files/timeline_pin/`): all 8 inputs converted mechanically by the OLD parse (each structured value is
  what the old code read; text is the old label; `day_zero` is what the old plan
  inferred; `≤N` before the anchor as the range it resolved to; a window read from the
  timing cell moved to the window field with no text). **Every expected output
  unchanged.**

## 2026-09-27 — ISSUE 74 BUILT (GitHub 74, branch `74-r8-washout-variable-delay`): a washout is a gate; the period after it has its own anchor
- `usdm4 @ 74-r8-washout-variable-delay`. Driven from the USDM4 project. #72 closed unbuilt (it held
  docs only); R8 raised again as #74. The three-machine arrangement dropped (Dave): next steps live
  here; test inputs are written in `usdm4`'s structured form, not taken from `protocol_corpus`.
- **State:** full suite green (Dave, VSCode, 2026-09-27); **merged to `main`**.
- `protocol_corpus`: read only — NCT03069989's `ground_truth.yaml`, `build/timepoints.yaml` and the
  source PDF text, early in the session; then set aside (Dave: out of date; not used for `usdm4`
  work). Nothing written.

**What it was.** A column carrying a structured `delay` (schema since #73) was parsed and carried with
a "not built until R8" warning; `plan.py` and `build.py` never read it. Every non-cycle column was
timed from one anchor, so a crossover's period 2 (`Day -1`, `Day 1` after the washout) was timed back
from period 1's `Day 1` and warned as a restart.

**Decisions (Dave), design § 9.**
- U4-10 (c): exit text filled from the delay — `≥ 7 days and washed out, or 28 days`; no max → no
  `, or …`.
- U4-36 (new): the period after a gate gets a new anchor at its `Day 1`; an anchor is a Fixed
  Reference, so no timing joins the periods — the decision's exit does.
- Test input: `Day ≤-30` is a day with a window — `timing -30`, window `[0, 29]` (to Day -1).
- Not ruled (Claude's, in the issue text): Follow-up `7-14 days post-final dose` as a time range
  Day 8 to Day 15 in period 2's numbering (final dose Day 1). Activities and footnote texts in the
  input are illustrative.

**What changed.** Listed under *As built* below. `plan.py` (`is_gate`, `_periods`, per-period anchors,
`_gate_nodes`, `TimelinePlan.anchors`, restart warning "with no gate before it"); `build.py` (no
`Encounter` for a gate column, `_add_gate`, gate decision and end, `gate_condition`); `naming.py`
(`gate_name`); `columns.py` (R8 warning gone). Tests: `test_plan.py` `TestGates` (15),
`test_r8_nct03069989.py` (22), `test_naming.py`, `test_columns.py`; pin case `nct03069989_r8` (input
by hand, expected saved from the built output). Docs: design status, R4.1, R8, § 9 U4-10/U4-14/U4-36,
§ 20; plan R8; this file.

**The numbers.** Sandbox (Python 3.10, no `cdisc-rules-engine`, `PYTHONPATH=src:.`): timeline,
assembler, pin and schema tests 582 pass; `build.py`, `columns.py`, `naming.py`, `values.py`,
`timeline_assembler.py` 100%; `plan.py` 99% — lines 573 and 715, the same two uncovered before this
issue over this subset. Other pin cases unchanged. Ruff: one new finding (import order) fixed; the rest
predate the branch; format clean.

**Built USDM, NCT03069989.** 11 instances (10 columns + `GATE1DEC`), 11 timings, 9 encounters.
Screening `Before` period 1 `Day 1` `P30D`, window `P29D`; `GATE1` `After` `Day 2` `PT0M`;
`GATE1DEC` `After` `GATE1` `P1D`, default → `GATE1`, exit → `Baseline PET`; period 2 `Day 1` a
second Fixed Reference; Follow-up `After` it `P7D`, window `P7D`. U4-14 withdrawn.

**Rejected.** A separate start node added and the washout column dropped (loses its cells). Timing
period 2's `Day 1` `After` the decision by zero (a false duration; the gap is the variable delay).
Taking test data from `protocol_corpus` ground truth (out of date; `usdm4` inputs are written here).

**Found, not this issue.** Period 2's instances are named `D-1-2`, `D1-2`, `D2-2` (de-duplicated,
not period-named), as `ED-2` in #70. `gate_condition` pluralises naively (`≥ 1 weeks`), as
`render_delay` does.

**Next.**
1. ~~Merge #74~~ — done.
2. U4-11, then the expander issue — before the next release.
3. `protocol_corpus` N78, copied columns.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 20).

R8, gates (§ 6 R8, U4-10 (a)–(c), U4-36). Branch `74-r8-washout-variable-delay`. No input
schema change (`delay` came with #73).

- `columns.py` — the "not built until R8" warning on a structured delay removed. A delay sent
  as text only is still warned and not read, so its column is an ordinary one (no gate).
- `plan.py` — `Planner.is_gate` (a column with a structured delay). `_periods` splits the
  columns at each gate; each period's anchor is found by U4-2 within the period (U4-36), so a
  gated timeline has one Fixed Reference per period; `TimelinePlan.anchors` lists them
  (`anchor` stays the first). `find_anchor` falls back to the period's own first column.
  `_gate_nodes`: the gate column's node (`kind` `GATE`), `After` the previous node by zero;
  a `DECISION` node `G{n}DEC`, `After` it by 1 day, `loop_to` it; when the gate is the last
  column an `END` node `G{n}END`. A gate with nothing before it is a Fixed Reference, warned.
  `_warn_restarts` resets at a gate and now reads "… with no gate before it" (U4-14). The
  "no column has a timing of 0 or more" warning names the period when there is more than one.
- `build.py` — a gate column gets no `Encounter`; its instance `GATE{n}` is labelled with the
  delay as printed, in the column's epoch, and takes the activities of its cells. The
  decision `GATE{n}DEC` loops back to it; its one `ConditionAssignment` is
  `TimelineBuild.gate_condition(delay)` (`≥ 7 days and washed out, or 28 days`; no max → no
  `, or …`) and leads to the next instance. End instance `GATE{n}END` as R5's. Header-value
  markers now link before the encounter is made (a gate column has none); order of
  created objects unchanged.
- `naming.py` — `gate_name(n, suffix)`.
- Tests: `test_plan.py` `TestGates`; `test_r8_nct03069989.py` (the built USDM from the new
  input, a washout timed as a range builds no gate, a gate as the last column, the exit
  text); `test_naming.py` gate names; `test_columns.py` (no R8 warning). Pin case
  `nct03069989_r8` added: `input_nct03069989_r8.json` written by hand (Dave's structure;
  activities and footnote texts illustrative), `expected_nct03069989_r8.json` saved from the
  built output. Other pin cases unchanged.

**U4-14.** Proven on this input: period 2 is one timeline with period 1, its `Day 1` a
second anchor after the gate, no restart warning. U4-14's "one timeline per period" is
withdrawn.

**Seen, not this issue.** Period 2's instances are named `D-1-2`, `D1-2`, `D2-2`: `sai_name`
de-duplicates rather than naming the period (as `ED-2` in § 17).

## 2026-09-27 — ISSUE 75 MERGED (GitHub 75, branch `75-copied-column-and-shared-encounter`): a copied column shares one Encounter; no epoch sent, none linked
- `usdm4 @ 75-copied-column-and-shared-encounter`. Driven from the USDM4 project. No sibling repo
  read or written. N78 (the `protocol_corpus` register row) is this issue.
- **State:** full suite green (Dave, VSCode, 2026-09-27); **merged to `main`**, issue closed.
- Before the issue: #74 found already merged to `main`; the docs saying "merge next" corrected
  (`next_steps.md`, `memory.md`, plan status and R8, design status). The plan's R7 section still
  said #71 "not yet merged" — corrected. The expander moved to **last** (Dave): nothing that uses
  `usdm4` depends on it, so it does not gate a release; plan § *Order from here*, § *Expander* and
  design § 7 reworded.

**What it was.** A column printed in two timelines (NCT05565742's `ED`, in main and early
termination) built one `Encounter` per timeline (U4-5 interim, #70): column ids are scoped to one
timeline, so nothing in the input said two columns were one visit. Separately, a column with no
epoch built a `StudyEpoch` with an empty label and linked its instance to it (U4-6, proposed, never
built) — `T2-EP1` in the R7 pin, `T3-EP1` in `nct04557384`.

**Decisions (Dave), design § 9.**
- U4-37 (new): `ScheduleTimelineInput` gains an `id`; `ColumnInput.copy_of` is `{timeline,
  column}`. Rejected: a timeline by its position (breaks silently when a caller reorders).
- The copy pattern shares only the visit (`Encounter`). A subsidiary timeline rarely links to
  epochs, so none is sent for its columns.
- U4-6 taken, in this issue: no epoch sent, no `StudyEpoch` built, `epochId` `None`.
- Claude's, in the issue text, not objected to: `id` optional (no caller breaks); the original must
  be in an earlier timeline; original not built → the copy gets its own `Encounter`, warned.

**What changed.**
- `src/usdm4/assembler/schema/schedule_timeline_schema.py` — `CopyOf`; `ColumnInput.copy_of` (a
  gate cannot be a copy); `ScheduleTimelineInput.id`; `check_copies` (ids unique, not blank;
  `copy_of` names an earlier timeline and a column in it; the original is not a copy, not a gate).
- `src/usdm4/assembler/schema/assembler_input.py` — `_check_timeline_copies` calls `check_copies`.
- `src/usdm4/assembler/timeline/columns.py` — `Column.copy_of`, `ParsedTimeline.id`.
- `src/usdm4/assembler/timeline/build.py` — `SharedState.encounter_by_column`; `_copied_encounter`
  (reuse, U4-30 warning, not-built fallback); `_add_epochs` skips a column with no epoch (a blank
  ends a redacted run); `_epoch_id` gives `None` for it at every instance kind.
- Tests: `test_schedule_timeline_schema.py` `TestCopies` (14); `test_assembler_input.py` (1);
  `test_timeline_assembler.py` `TestCopiedColumns` (9) replaces the interim two-encounter test,
  epoch tests (3) replace the empty-label one; `test_timeline_pin.py` runs `check_copies`.
- Pins: `input_nct05565742_r6.json` — ids `main`, `et`; ET `c14` `copy_of` main `c14`, its epoch
  removed. Expected re-saved: `nct05565742_r6`, `nct02674152_r7`, `nct04557384`.
- Docs: design § 3.3, R6, § 9 U4-5/U4-6/U4-30/U4-37, new § 21, status; plan R6 and status; this file.

**The numbers.** Sandbox (Python 3.10, no `cdisc-rules-engine`, `PYTHONPATH=src:.`): timeline,
assembler, pin and schema tests 607 pass; the rest of `tests/usdm4/assembler` 813 pass, 2 skipped.
`build.py`, `columns.py`, `schedule_timeline_schema.py`, `assembler_input.py` 100%; `plan.py` 99%,
lines 573 and 715 as before. Pins: `nct05565742_r6` encounters 15 → 14, epochs 4 → 3, T2's instance
on `T1-E14`; `nct02674152_r7` epochs 6 → 5; `nct04557384` epochs 6 → 5; every other difference in
the three is `Code` id renumbering (one fewer epoch type code). Other six pins unchanged. Ruff: two
new ISC004 in the new tests fixed; format clean. Full suite green (Dave, VSCode).

**Rejected.** A timeline named by position. Leaving the epoch in the r6 pin (a duplicate
`T2-PITAP`). Removing it without U4-6 (an empty-label `T2-EP1` instead — no better). Logging epoch
duplication as its own issue (Dave: sub-timelines do not link to epochs; the fix is U4-6).

**Found, not this issue.** `usdm4_protocol` gets the shared `Encounter` only once it emits timeline
ids and `copy_of`, and sends no epoch for a subsidiary timeline's columns. A project memory note
("given up on the expander") was misread as abandoning the work; it meant "last" — reworded.

**Next.**
1. ~~Merge #75~~ — done.
2. The expander issue (U4-11 is part of it) — last.

Re-verify:
```
python3 -m pytest tests/usdm4/assembler/timeline tests/usdm4/assembler/test_timeline_assembler.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 21).

Copied columns (U4-5 target, U4-30, U4-37) and no epoch sent (U4-6). Branch
`75-copied-column-and-shared-encounter`. Schema change, additive: no caller breaks.

- **Schema.** `ScheduleTimelineInput.id` (optional). `ColumnInput.copy_of`
  `{timeline, column}` (`CopyOf`). A gate column cannot be a copy. `check_copies`, called
  by `AssemblerInput`: ids unique and not blank; `copy_of` names an EARLIER timeline and a
  column in it; the original is not itself a copy and not a gate.
- **Parse.** `ParsedTimeline.id`; `Column.copy_of` as `(timeline id, column id)`.
- **Build.** `SharedState.encounter_by_column` — every `Encounter` of a timeline with an
  id, keyed `(timeline id, column id)`. A copy reuses the original's `Encounter` and does
  not list it again; its instance, timing and activities are its own. Different visit
  text: the original's label kept, warned (U4-30). Original not found (the check was not
  run, or its timeline failed): own `Encounter`, warned.
- **Epochs (U4-6).** A column with no epoch sent builds no `StudyEpoch`; its instance's
  `epochId` is `None`. A blank column ends a redacted run (U4-13).
- **Pins.** `nct05565742_r6` input: timeline ids `main`, `et`; ET `c14` `copy_of` main
  `c14`, its epoch removed. Re-saved: 15 → 14 encounters, T2's instance on `T1-E14`,
  `T2-PITAP` gone. `nct02674152_r7` (`T2-EP1`) and `nct04557384` (`T3-EP1`) re-saved:
  the empty-label epoch gone, its instances' `epochId` `None`. Every other difference in
  the three is `Code` id renumbering (one fewer epoch type code). Other pins unchanged.

## 2026-09-27 — ISSUE 76 BUILT (GitHub 76, branch `76-expander-update`): a loop is run twice, a gate to its minimum
- `usdm4 @ 76-expander-update`. Driven from the USDM4 project. No sibling repo read or written.
- **State:** full suite green (Dave, VSCode, 2026-09-27); not merged.

**What it was.** The expander recursed without end on the R5 cycle loop and the R8 gate: a
non-`days` condition took the default, which points back, and each pass recomputed the same
tick (a time was only the timing chain to the anchor). Period 2 after a gate, hung from its
own Fixed Reference, would restart at 0.

**Decision (Dave), design § 9 U4-11.** A loop is run twice, so the decision goes each way
once (`Cycle 3` to N: cycle 3, cycle 4, then on). A washout with a minimum that can be read is
run until the minimum has passed, then left. The expander is illustrative, not normative.
Claude's, in the issue text, not objected to: minimum read from `≥ N <unit>` / `>= N <unit>`;
a loop is a branch back to an instance already reached; pass number on each timepoint.

**What changed.** Listed under *As built* below.
- `src/usdm4/expander/expander.py` — iterative walk with a step limit; `_decide`, `_loop`,
  `_minimum`, `_hop` (chain to the anchor, with anchor id); shift on loop re-entry and on a
  new anchor; `_sub_timelines`, `_next_after_activity` split out.
- `src/usdm4/expander/timepoint.py` — `pass_number` (optional, default 1); `to_dict` `"pass"`.
- Tests: `tests/usdm4/expander/test_expander_loops.py` (new, 25): cycle loop both ways round,
  minimum met on the first pass, gate to 7 days and period 2, minimum units, no-minimum gate,
  new anchor without a decision, sub-timeline timing, both branches back (step limit), `_hop`
  edges, the R5/R7/R8 pin outputs expanded.
- Docs: design § 7 rewritten, § 9 U4-11, § 22, status; plan status and expander section;
  this file; `memory.md`.

**The numbers.** Sandbox (Python 3.10, no `cdisc-rules-engine`, `PYTHONPATH=src:.`):
`tests/usdm4/expander` 143 pass (118 before + 25); `expander.py` 100%; `timepoint.py` 98% over
the expander tests alone — `_code_dict`, uncovered by that subset before this change too. The
assembler's expander test passes. Expanded pins: R5 — `C3+D1` day 56 then 84 (pass 2), `C3+D15`
70 then 98; R8 — gate days 1–7 (passes 1–7), period 2 `Day -1` day 8, `Day 1` day 9, follow-up
day 16; R7 — profile points now `-5 min`, `1:30`, `2:00` … after each calling visit (were
accumulated, `1:30` at 2 h 55 m). The other six pins expand exactly as before. Ruff: no new
findings in the changed files (the `_days_condition` BLE001 predates); format clean.

**Ruled (Dave).** Every repeat is shown — the expander shows what happens to a subject day by
day. A 7-day gate on a 1-day loop gives seven gate timepoints.

**Accepted as is (Dave).** A loop starting at a predose `Day -1` gets its second pass a day late.

**Rejected.** One gate entry then a jump to the minimum (Dave: the expander shows every day of
a subject, so repeats are the point). Re-timing every instance reached again on a loop — the
first cut did, and put `C3+D15` pass 2 on day 84 instead of 98; only the loop start, entered
from the decision, is re-timed. Keeping the recursion with a visited set (a repeat cannot be
shown if a visited instance is never re-entered).

**Found, not this issue.** Sub-timelines were mis-timed before this change (each point added
to the previous point's time); fixed here, since the new walk replaced that code.

**Next.**
1. Merge #76.
2. Then the placeholder procedure code `12345` (`build.py`) — it puts a made-up code into
   every assembled USDM; then CORE-000938; then the small output defects.

Re-verify:
```
python3 -m pytest tests/usdm4/expander tests/usdm4/assembler/test_timeline_assembler.py -q
```

**As built** (moved 2026-09-27 from the retired `timeline_assembler_design.md` § 22).

U4-11. Branch `76-expander-update`. `src/usdm4/expander/` only; the assembler is unchanged.

- **Walk.** `Expander._process_si` walks a timeline in a loop, not by recursion; a step
  limit (`STEP_LIMIT`, 10,000) ends any loop the rules below do not, as an error.
- **Loop.** A decision with one condition whose branch leads to an instance already reached
  on this walk is a loop. No readable minimum: back the first time the decision is
  reached, out the second. A minimum (`≥ 7 days …`, `>= 3 days`; minutes to years, a month
  30 days, a year 365, as `Tick`): out once the decision's time less the loop start's first
  time reaches it. A `days <op> n` condition keeps the original test; a non-loop,
  non-`days` condition keeps the default plus error; two or more conditions as before.
- **Time.** An instance's time is its timing chain to its Fixed Reference (`_hop`) plus a
  shift. The shift moves when a decision leads back into a loop (the loop start falls at
  the decision's time) and when an instance hangs from a different anchor than the last
  (period 2 after a gate starts at the decision's time; without a decision, at the
  previous instance's time). A decision is timed by its own timing, else the previous
  instance's time.
- **Sub-timelines.** Timed from the calling instance: base + chain. Before, each instance
  added its chain to the previous instance's time, so a profile's third point onwards was
  wrong (R7 pin: `1:30` came out at 2 h 55 m).
- **Timepoint.** `pass_number` (1 outside a loop; the count of times the walk reached the
  instance); `to_dict` gains `"pass"`.
- **Tests.** `tests/usdm4/expander/test_expander_loops.py`: hand-written cycle and gate
  loops, minimum units, anchors, sub-timeline timing, guards; the R5, R7 and R8 pin
  outputs expanded. Existing expander tests unchanged and passing. Other pins expand as
  before.

**Ruled (Dave, 2026-09-27).** The expander shows everything that happens to a subject, day
by day, so every repeat is shown: a gate with a 7-day minimum and a 1-day loop gives seven
timepoints for the gate instance, passes 1–7. Never collapse repeats.

**Accepted as is (Dave).** A loop whose start is a predose `Day -1` gets its second pass one day late (the decision
falls at the next `Day 1`; the loop start is placed there).

## 2026-09-27 — DOCS TIDIED (no GitHub issue, `main`): aims, issues register N1–N13, one CORE-vs-d4k reference, timeline spec
- `usdm4`, branch not captured (no git run). Driven from the USDM4 project. No sibling repo read
  or written. Docs, docstrings and comments only; no code behaviour changed; nothing run.

**What it was.** `docs/` held ten files. Five recorded finished work (a May debugging pass, the
retired rule generator, the corpus extractor fix list, the timeline plan whose own status said
"retired when the last issue is closed"), two split one subject (CRE bugs and the divergence
index), and open problems were scattered through them and through `next_steps.md` §1–§9 below
the log. Several asserted things the code no longer does.

**What changed.**
- `docs/aims.md` (new) — purpose, what the package provides (file handling, builder and
  assembler, the two validators), principles, scope. Wording ruled by Dave: `usdm4` provides the
  common basic facilities other packages build on and does not do everything; the validators
  check a JSON file and report — no conclusions, the user decides; convert is USDM3 → USDM4;
  callers are not named.
- `docs/issues.md` (new) — open problems only, `N<n>`, never reused (Dave: same series style as
  the other repos). N1–N13; see *Found* for N12, N13.
- `docs/cre_issues.md` — `d4k_cre_divergence_index.md` merged in as the lookup table, pointers
  fixed (DDF00227 row, DDF00087/88 → N6), the settled d4k departures (DDF00164/165, DDF00187)
  moved in from `next_steps.md` § 4, CT-family lists reconciled, open follow-ups → N7, N8.
  Issue 5's workaround corrected to #54's `executionStatus` classification; a note that the
  corpus baseline predates #54.
- `docs/spec/timeline_assembler.md` (new; `docs/spec/` is where designs go, Dave) — the spec
  part of the old design (§ 1, 3, 5, 6, 7) plus the U4 decisions sorted, superseded rows one
  line each. Drift fixed against the code: R1–R3 "Today" notes, R2 no-epoch rule (U4-6), R4.3
  chain (U4-27), R4.6 mixed units, R6–R8 as built, input example with `id` and `copy_of`. The
  pointer to `protocol_corpus/docs/spec/soa_two_stage.md` removed (Dave): R1–R9 are defined here.
- `docs/next_steps.md` — header lists the docs; *Next steps* corrected (#76 merged). The design's § 2, § 4 and § 10–§ 22 moved into the #63–#76 entries as *As built*; a
  note atop the log says "design § n" / "plan" references are to retired files. Old §1–§8 →
  N2, N5–N10; § 9 → the 2026-07-30 entry; § 10 and the "Moved" note removed.
- `docs/lessons_learned.md` — § 9 rewritten as "Adding or changing a rule" (the retrospective's
  recipe; the dead `feedback_usdm4_rule_test_pattern` memory pointer replaced by
  `test_rule_ddf00035.py`); § 5 gains "Retired 2026-05-02"; this session's lesson.
- Repo-root `memory.md` retired (same layout as the other repos: the log lives here). Its three
  August entries, found nowhere else, moved into this log in date order; its September entries
  were short copies of entries here.
- Deleted: `corpus_extractor_fixes.md` (by Dave), `assembler_validation_findings.md`,
  `d4k_cre_divergence_index.md`, `rule_generation_retrospective.md`,
  `timeline_assembler_design.md`, `timeline_assembler_plan.md`.
- References repointed: `CLAUDE.md` (docs line); `validate/README.md`;
  `validate/corpus_adapter.py` docstring (+ the missing `_adapt_non_standard_orgs` bullet);
  `src/usdm4/assembler/timeline_assembler.py`, `timeline/__init__.py`,
  `schema/schedule_timeline_schema.py`, `schema/assembler_input.py`; tests
  `test_package.py` (xfail reason → N5), `integration/test_assembler_to_d4k.py` (docstring,
  xfail reason → N2), `integration/README.md`, `integration/test_sample_usdm_7_core.py`,
  `assembler/schema/test_schedule_timeline_schema.py`, `assembler/test_timeline_pin.py`; the six
  `timeline_pin/input_*.json` `converted` notes. Every bare `N78` marked `protocol_corpus` N78.

**The numbers.** `docs/` 10 files → 5 plus `spec/timeline_assembler.md`. Timeline docs 1,219
lines → spec 410. Edited Python files parse; pin JSON files load. Tests not run (text-only
changes in docstrings and string values).

**Rejected.** `cre_issues.md` as a section of `issues.md` (most of it is settled reference; it
would bury the open items). `I<n>` numbering (Dave: `N<n>`). Deleting the design's as-built
sections outright (the session log pointed at them). Naming callers in `aims.md` (Dave).
"Anything failing both engines is a `usdm4` defect" (Dave: too strict).

**Found, not this work.**
- N12: a timing in a unit other than the anchor's is warned and timed by its printed number;
  the design claimed exact conversion, never built.
- N13: `Convert` is USDM3 → USDM4 but reads no input version; two fixtures say `2.11.0`.
- N11: empty population label still fails assembly (Finding 8 of May, confirmed in code).
- `lessons_learned.md` § 10 still says "123 of 210" implemented — a dated snapshot, not current.
- The `save-session` skill still names `timeline_assembler_design.md` and
  `timeline_assembler_plan.md` as `usdm4` targets; both are retired.

**Next.**
1. N1, then N2 from CORE-000938, then N3. N1 first: a made-up LOINC code goes into every
   assembled study.

Re-verify (the files touched that carry code or tests):
```
python3 -m pytest tests/usdm4/test_package.py tests/usdm4/integration/test_assembler_to_d4k.py tests/usdm4/assembler/test_timeline_pin.py tests/usdm4/assembler/schema -q
```

## 2026-09-27 — CODE REVIEWED (no GitHub issue, `main`): ten bugs logged N14–N23, structural tidy-up N24.1–N24.11, plan reordered
- `usdm4 @ main`. Driven from the USDM4 project. No sibling repo read or written. Docs only;
  no code changed; nothing run.

**What it was.** Dave asked for a senior-developer review of structure and design: the code
had been changed session by session and needed tidying. Three read-only reviews (assembler;
rules, CORE and data store; api, builder, convert, ct, bc, packaging, tests), then the
findings checked against the code before logging. Verdict: the design holds (builder vs
assembler, `timeline/` split, one file per rule, `RuleTemplate`); the problems are guards,
copies and workarounds layered on it.

**What changed.**
- `docs/issues.md` — N14–N21 (bugs: convert on two designs and duplicate ids; CT/BC API-key
  variable; CT refresh deletes before fetch; `project maanger` and `APPORVAL` typos; empty
  extensions always emitted; `errors.exception` without the exception; missing `f` prefixes;
  BC `valid` inverted and class stored for instance). N22 (rule loader drops rules silently,
  constructor failure blamed on the previous rule). N23 (CORE `is_valid` true with zero rules
  run). N24 with N24.1–N24.11 (structural). Header: sub-issue numbering `N<n>.<m>` (Dave).
- `docs/next_steps.md` — plan reordered (below); this entry.

**The numbers.** Measured by reading, not by running: 65 test files import `src.usdm4`;
47 `except Exception` in 11 assembler files; ~86 of 213 rule files in 13 identical-body
groups; ~112 hard-coded C-codes in `encoder.py`. Tests not run.

**Rejected.**
- A separate file for the structural issues (a second register drifts); one issue per
  structural item with a flat number (Dave chose `N24.<m>` to keep them together).
- "Guards in `identification_assembler.py` ~378-380 always true" — checked: harmless
  defaults, dropped.
- Leaving the rule-loader and zero-rules CORE problems inside N24 — they give wrong
  validation results, so they are bugs (N22, N23, Dave).

**Found, not this work.** Everything found is logged above as N14–N24. Carried from the
previous entry, still open: `lessons_learned.md` § 10 says "123 of 210"; the `save-session`
skill still names the two retired timeline docs.

**Next.**
1. N24.1 — one import path in tests; no later fix can be trusted without it.
2. N22, N23 — validators must not report clean when rules did not run.
3. N14–N21, then N1 — small, independent bugs.
4. N24.2–N24.11.
5. N2, N11, N3.

Re-verify (the bugs are still in the code):
```
grep -n "maanger" src/usdm4/assembler/identification_assembler.py
grep -n "CDISC_API_KEY" src/usdm4/ct/cdisc/library_api.py src/usdm4/bc/cdisc/library_api.py
grep -n 'version.pop("studyPhase")' src/usdm4/convert/convert.py
grep -rlE "from src\.usdm4|import src\.usdm4" tests
```

## 2026-10-02 — N25 BUILT (no GitHub issue yet, `main`): arms with interventions and no epochs get one synthesised Treatment Epoch; bs4 floor 4.13.1
- `usdm4 @ main`. Driven from the UDP PRISM project (udp_prism N8; pointer in
  `udp_prism/docs/next_steps.md` 2026-10-02). `usdm4_fhir/docs/issues.md` I-22 added there.
  Tests run by Dave: all pass.

**What it was.** USDM links an arm to its interventions only through `StudyCell` →
`StudyElement`, and `StudyCell.epochId` is required. `StudyDesignAssembler` got epochs only
from the timeline build, so input with arms naming interventions and no SoA (the PRISM3 FHIR
import; an extraction without an SoA) built no cells. `_attach_arm_element` made `EL-<ARM>`
with the right interventions on no cell, and the arm read as having none.

Separately: bs4 4.12.x `_markup_resembles_filename()` warns on any text containing `/`, so
`get_soup` logged a "looks more like a filename" entry for most criteria text. 4.13 warns only
on real file extensions. 4.13.0 was yanked.

**What changed**
- `src/usdm4/api/extensions_d4k.py` — `EPP_EXT_URL` (`…/extensions/017`, epoch provenance),
  with the rule that any epoch export must skip an epoch carrying it.
- `src/usdm4/assembler/study_design_assembler.py` — `epochs = timeline epochs or
  _synthesised_epochs(...)`, used for cells and for the design's `epochs`. The new method fires
  only with no timeline epochs, no explicit cells or elements, and a built arm naming an
  intervention that resolves; it builds `TREATMENT-EPOCH` / "Treatment Epoch", C101526, with
  017. The existing grid and `_attach_arm_element` do the rest.
- `tests/usdm4/assembler/test_study_design_assembler_arm_interventions.py` — the no-epochs
  test now expects the epoch and one cell per arm; `TestSynthesisedEpoch` (shape and
  extension, cells on the epoch, timeline epochs untouched, no epoch without arms /
  interventions / resolvable names / with explicit elements, exception and `None` paths).
- `setup.py`, `requirements.txt` — `beautifulsoup4>=4.13.1`. `CLAUDE.md` dependency line.
- `docs/issues.md` — N25 added (spec, decisions, model gap).

**Figures.** udp_prism `./run.sh` 2026-10-02 with this installed: section 6 round-trip diff
1,331 → 1,171 cells, 14 → 6 protocols; every protocol whose arms have one intervention now
round-trips them. Not run: `validate/run.sh` (d4k + CORE) on a step-3 file with the lone
epoch.

**Rejected.** An arm extension holding intervention ids (d4k-only; a second home for the same
fact; kept as a DDF proposal, `StudyArm.studyInterventionIds`). Marking the epoch by inference
(no activity instance references it) or by `description` (not testable): the timeline build
types every epoch Treatment Epoch, so 017 is the only marker. Triggering with explicit elements
(that mode only checks reachability).

**Found, not this work.** None new here. `_dose_form` defaults to C17998 Unknown with no
provenance marker — recorded as udp_prism N15, owner usdm4; no row here yet.
