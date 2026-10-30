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

## 2026-10-02 — N25 BUILT (no GitHub issue yet, `main`): arms with interventions and no epochs get one synthesised Treatment Epoch; bs4 floor 4.13.1
- `usdm4 @ main`. Driven from the UDP PRISM project (udp_prism N8; pointer in
  `udp_prism/memory.md` 2026-10-02). `usdm4_fhir/docs/issues.md` I-22 added there.
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

## 2026-10-02 — Session log moved to `memory.md`; `next_steps.md` is the plan only

`usdm4 @ main`, docs only. Part of one layout across protocol_corpus, udp_prism and the usdm4
repos (udp_prism `memory.md`, same date).

**What changed**

- `memory.md` — new; the 24 Session Log entries from `docs/next_steps.md` moved verbatim,
  oldest first; the note on retired design and plan references moved into its header.
- `docs/next_steps.md` — Session Log removed; header states plan only.
- `CLAUDE.md` — § *Session log* and the `docs/` description name the layout.

**Figures.** None.

## 2026-10-06 — N26 registered: a required string accepts ""

usdm4, docs only. From udp_prism N43 (usdm4_fhir GitHub 45).

**What it was.** `StudyVersion.versionIdentifier` (and `StudyDefinitionDocumentVersion.version`)
is required in the USDM 4 schema with no `minLength`, so `""` is valid; usdm4_protocol stores
`""` when a protocol prints no version, and udp_prism keeps it end to end (Dave). Dave: a
required identifier should not be empty. No d4k rule checks it (DDF00126 delegates to the
schema); no CORE rule seen does.

**What changed.** `docs/issues.md` — N26.

Also found, not yet registered: `src/usdm4/ct/cdisc/missing/m11_codelists.yaml` (generated by
`usdm4_protocol/tools/generate_m11_ct.py` from the Technical Specification text) differs from
the published NCI EVS M11 terminology in 4 of 23 codelists — C217272 (16 vs 160 members),
C217274 (missing C218488), C217283 (missing C174269), C217287 (C25742 vs C218509). Plan:
move the generator here and read the terminology file (udp_prism N45 sequence).

## 2026-10-06 — GitHub 81: M11 CT generated from the published terminology

usdm4, branch `81-m11-ct-from-terminology-file`. From udp_prism N45; usdm4_protocol 75 and
usdm4_fhir 46 depend on it.

**What it was.** usdm4's M11 CT (`ct/cdisc/missing/m11_codelists.yaml`, `missing_ct.yaml`)
was generated by `usdm4_protocol/tools/generate_m11_ct.py` from the codelists printed in the
M11 Technical Specification. That printed text is not the published terminology: 4 of 23
codelists were wrong, C217272 held 16 per-section data-element codes instead of the 160
section codes. Other packages kept their own copies (usdm4_fhir a JSON of C217272) because
usdm4 offered no way to read one codelist.

**What changed.**
- `tools/m11_ct.py`, `tools/__init__.py` — new generator: reads the NCI EVS ICH M11
  Terminology `.xls` (newest `ICH M11 Terminology_*.xls` in `m11_specification`), response
  codelists only (names starting "ICH M11 Section " are data-element lists, excluded),
  extensions to C66737 from `M11_TO_SDTM` with the NCI preferred term.
- `src/usdm4/ct/cdisc/missing/m11_codelists.yaml`, `missing_ct.yaml` — regenerated from
  release 2025-12-19 (23 codelists, 278 terms; C217272 160 members; C217274, C217283,
  C217287 corrected).
- `src/usdm4/ct/cdisc/library.py` — `Library.codelist(codelist_id)`, a deep copy with terms.
- `src/usdm4/__init__.py` — `USDM4.ct_library()`, loaded once per instance.
- `src/usdm4/builder/builder.py` — `Builder.codelist()`.
- `src/usdm4/assembler/amendments_assembler.py` — a changed section's title is set to the
  C217272 preferred term for its number; a number not in the list keeps its title and logs
  a warning.
- `requirements.txt` — `xlrd>=2.0`, tool only, not in `setup.py`.
- Tests: `tests/tools/test_m11_ct.py` (new), amendments assembler, builder, library, package.
  `pytest` green (Dave).
- `CLAUDE.md` — the tool and the read interface; `docs/next_steps.md` item 0.

**Figures.** None measured here; udp_prism measures after merge.

**Rejected.** Hand-editing the CT files (generated). Members from the TS text (stale).
Emitting the per-section data-element codelists (field names, not permitted values). `xlrd`
as a package dependency (only the tool reads `.xls`).

## 2026-10-06 — GitHub 82: encounter and epoch links

**Repos and branches.** `usdm4` branch `82-encounter-and-epoch-links-missing`. Raised from
SDW GitHub 74 (an M11 import's exported USDM had every Encounter `previousId` / `nextId`
null).

**Cause.** `TimelineAssembler.execute` ran its one linking pass over activities only.
Epochs and encounters were never linked, ever — git history shows only activities (and
later criteria, document contents) were double-linked. Every StudyEpoch and Encounter left
the assembler with null links, so any design with 2+ epochs had 2+ chain heads (DDF00088).

**Decision (Dave).** One chain each across all timelines, input order — same as activities.

**Change.**
- `src/usdm4/assembler/timeline_assembler.py` — `double_link(self._epochs, ...)` and
  `double_link(self._encounters, ...)` after the activities pass. Lists are already in
  column order with no duplicates (a copied column reuses the original's encounter,
  issue 75). The design assembler's synthesised single epoch needs no links.
- `tests/usdm4/assembler/test_timeline_assembler.py` — `links` / `chained` helpers; epochs
  and encounters chained in column order, one chain across timelines (one epoch head), a
  single item unlinked, nothing built links nothing, a shared (copied) encounter chained
  once.
- `tests/usdm4/test_files/timeline_pin/expected_*.json` (all 9) — edited, not re-saved:
  epochs and encounters linked in list order. Diff is `previousId` / `nextId` lines only
  (272 changed).

**State.** py_compile only. Dave to run `pytest`. Downstream: `usdm4_protocol` USDM
goldens with a SoA (e.g. `Example1_usdm.json`, `NCT04320615_usdm.json`) will change
when regenerated; SDW's M11 goldens carry no SoA and are unaffected.


## 2026-10-07 — GitHub 83: assembler inputs for nine M11 1.1.2 fields

**Repos and branches.** `usdm4` branch `83-assembler-m11-112-fields`. Raised from udp_prism
N6 (step 1 drops most 1.1.2 data: the assembler had nowhere to put it).

**Checked first.** Two of the eleven missing 1.1.2 fields already had a route and are out of
scope: Nonproprietary Name (control) via products / substances, and the alternate intervention
duration via `AdministrationDurationInput.will_vary_reason`. The usdm4_protocol 1.1.2 view
already reads every USDM path below; only the input side was missing.

**Change.**
- `assembler/schema/study_design_schema.py` — `StudyDesignInput` gains `indications`,
  `site_distribution`, `site_geographic_scope`, `intervention_assignment_method`,
  `blinding_schema`, `blinded_roles`, `independent_committees`, `other_committees`,
  `participation_duration`.
- `assembler/encoder.py` — six lookups with no default (`_lookup_optional`): empty or "not
  applicable" -> `None` silently; unknown -> `None` with a warning. Labels normalised (case,
  hyphens, whitespace, trailing full stop). Codes: characteristics C207416 (C217004/5,
  C217006/7, C46079, C147145), blinding C66735, roles C215480. M11 "Participant" -> USDM Study
  Subject C41189. Assignment "No Intervention Assignment Method" / "Other" have no USDM home:
  no code, info message.
- `assembler/study_design_assembler.py` — indications (label = text, `isRareDisease` False),
  characteristics, `blindingSchema`, design roles (blinded with Masking; independent committees
  by code; other committees as C142489 + label, which is what the view reads), participation
  duration on the main timeline's `plannedDuration` (warned and dropped with no timeline).
- `assembler/study_assembler.py` — `_merge_roles`: a blinded role matching an unmasked
  identification role (sponsor) gets the masking on that role; a blinded sponsor with no
  sponsor role is dropped with a warning (otherwise DDF00202 fails).
- `assembler/identification_assembler.py` — `ROLE_CODES` tidy (N17 first bullet).
- Tests: `tests/usdm4/assembler/test_study_design_assembler_m11_112.py` (38);
  `test_identification_assembler.py` key list updated.

**Checked.** Assembler, integration, rules, api/builder/etc. tests pass in the Linux VM
(Python 3.10). Failures seen only where the VM lacks `jsonschema`, `lxml` or
`cdisc_rules_engine` (rules schema / xhtml tests, core, convert). d4k rules on an assembled
study with every new field set: no new failures; DDF00153 (main timeline has no
plannedDuration) clears.

**State.** Dave ran the full suite on his Mac: all pass. Ready to merge and release.

**Flagged, not done.** Other Committees use C142489 "Data Monitoring Committee" with the name
as label: C215480 has no generic committee term, and that is the code the view reads.

## 2026-10-07 — ISSUE 84 (GitHub 84, branch `84-repeat-visit-columns`): repeating visit columns — U4-38

**Repo**: `usdm4`, merged to `main` by Dave (`add0537 Repeat visit handling`). Callers: `usdm4_protocol` 85 sends it; `protocol_corpus` 31 states it in the ground truth.

**What it was.** A column could print a visit that repeats — explicit visits over a span (`Treatment (Week 3-11)` over visits `2-17`) or an open repeat (`Q12 Wks`, `Every 6 months`) — and `ColumnInput` had no way to say so: a timing is a point or a range, the only repeat a cycle. Dave ruled (2026-10-07): explicit visits create explicit encounters; an open repeat, like `Cycle 3+`, cannot.

**The fix**

- `assembler/schema/schedule_timeline_schema.py` — `VisitRange`, `RepeatValue` (`visits`, `period`, `end`), `ColumnInput.repeat`; refused beside a cycle or a delay.
- `assembler/timeline/columns.py` — parse reads the repeat; explicit visits are expanded before the plan: one column per visit number, named by it, cells copied, timed by the period or, with none, sharing the column's range with a warning.
- `assembler/timeline/plan.py` — an open repeat gets a decision `After` it by the period, looping back to it, and an end node when last; no period, no loop, warned.
- `assembler/timeline/build.py`, `naming.py` — `REPEAT{n}DEC` / `REPEAT{n}END`; exit condition the printed bound, else `repeat exit condition`.
- `docs/spec/timeline_assembler.md` — decision U4-38.
- `tests/usdm4/assembler/timeline/test_repeat.py` — 17 tests. Full suite: 3903 passed, 3 skipped; every changed file 100% covered except two `plan.py` lines uncovered before.

**Rejected.** Expanding an open repeat (invents visits); inferring a period not printed.

## 2026-10-08 — Partial planned age range: open-ended placeholders instead of a copied bound

**Repo**: `usdm4`. GitHub issue number and branch not captured in the session; Dave raised the issue and posted the closing statement. Found from udp_prism (TCBCPT_01 Maximum Age 18 for a document stating only a minimum at the time). Caller side: `usdm4_protocol` GitHub 87.

**What it was.** `assembler/population_assembler.py` `_build_planned_age` filled a missing bound with the supplied one, because a USDM `Range` requires both `minValue` and `maxValue`: "18 or over" was stored as 18–18. The docstring said a missing lower bound became 0; the code copied the upper bound.

**The fix**

- `src/usdm4/assembler/population_assembler.py` — `AGE_MIN_DEFAULT = 0`, `AGE_MAX_DEFAULT = 200` (years); a missing minimum becomes 0 years, a missing maximum 200 years, with the existing warning naming the value. The stated bound keeps its own unit; the filled one is always years. Docstring rewritten to match.
- `tests/usdm4/assembler/test_population_assembler_branches.py` — min-only gives 18–200 (max in years), max-only gives 0–65. Tests pass (Dave).
- `CLAUDE.md` — GitHub section added (title four or five words; issue and PR text with no line breaks inside a paragraph).

**Interim only.** The model gap is usdm4_fhir `docs/issues.md` M-39 (M11 allows an open age bound, USDM `Range` does not). Remove the defaults when `Range` allows a single bound.

**Rejected.** Omitting `plannedAge` when a bound is missing (loses the stated bound); keeping the zero-width range (states something the protocol does not).

## 2026-10-09 — GitHub 86 (branch `86-control-type-study-design-extension`): M11 Control Type as a study design extension

**Repo**: `usdm4`. Driven from udp_prism's 1.1.2 walk-through (its N63); usdm4_protocol (GitHub 92) and usdm4_fhir (GitHub 53) each have their own entry.

**What it was.** M11 1.1.2 Control Type (C217279: Placebo, Active Comparator, Dose Response, Different Dose or Regimen, External, Sham Procedure, No Control) had no home in USDM. `StudyDesign.characteristics` is bound to C207416, which holds none of these terms, and arm types cannot express Dose Response, Different Dose or Regimen or External.

**What changed.**
- `src/usdm4/api/extensions_d4k.py` — `CT_EXT_URL = "www.d4k.dk/usdm/extensions/018"`, at most one per design, `valueCode`.
- `src/usdm4/assembler/schema/study_design_schema.py` — `StudyDesignInput.control_type: Optional[str]` (M11 cardinality One to one).
- `src/usdm4/assembler/encoder.py` — `CONTROL_TYPE_MAP` (the seven C217279 terms, exact after `_normalise_label`) and `control_type()` on `_lookup_optional`: unknown warned and dropped, empty / N/A silent.
- `src/usdm4/assembler/study_design_assembler.py` — `_control_type_extensions()`: the decoded `Code` converted to `BaseCode` (as for `SIT_EXT_URL`), one `ExtensionAttribute`, appended after the intervention model provenance.
- `tests/usdm4/assembler/test_study_design_assembler_m11_112.py` — `TestControlType`, four tests. Pass (Dave).

**Rejected.** A list (`control_types`): M11 gives Control Type One to one (Blinded Roles and committees are One to many). Putting the codes in `characteristics`: breaks the C207416 binding; that would need a CDISC CT change.

## 2026-10-16 — GitHub 90: Adaptive design assembler input

**Repo**: `usdm4`, branch `90-adaptive-design-assembler-input`, with usdm4_protocol GitHub 114 and usdm4_fhir GitHub 54 (their entries of the same date) and udp_prism (the 1.1.2 walk-through that found it). Dave ran the tests and merged.

**What it was.** The study design input had no field for the M11 1.1.2 Adaptive Trial Design Indicator (C218706, Required, Yes / No from C217046), so StudyDesign.characteristics never held C98704 Adaptive Design (C207416, the DDF-RA home) and every protocol presented No.

**What changed.**
- `src/usdm4/assembler/schema/study_design_schema.py` — `adaptive_design: Optional[bool] = None`, beside the site and assignment fields.
- `src/usdm4/assembler/study_design_assembler.py` — `ADAPTIVE_DESIGN` (C98704); `_build_characteristics` appends it when True; False and None add nothing (no characteristic is No).
- `tests/usdm4/assembler/test_study_design_assembler_m11_112.py` — True, False / None, and order after the site and assignment characteristics.

**Figures.** No corpus figure; measured through udp_prism: TCBCPT_01 (cell set to Yes) carries C98704 at step 1 and step 3.

**Rejected.** Registering the gap instead of fixing it (Dave: a register row is a last resort).


## 2026-10-19 — GitHub 91 and 92: a timing measured from a named column or the timeline's start

**Repo**: `usdm4`, branches `91-timing-from-a-named-visit` and `92-first-column-delay-lost`, merged by Dave. Callers: `usdm4_protocol` 118 and the corpus `from` row (`protocol_corpus` N94; full entry in its `memory.md`, 2026-10-19).

**What it was.** `TimingValue` held only a point or range on the study clock, and the plan measured every timed column from the anchor. A column printed as a delay after another visit (`30 days after EOT`) arrived untimed and took U4-3's zero timing from its neighbour; a timeline whose first column is a delay from an event made that column the anchor and lost the delay.

**What changed.**
- `src/usdm4/assembler/schema/schedule_timeline_schema.py` — `TimingValue.from_` (alias `from`): a column id, or `start` (`TIMELINE_START`) on the first column only; a value of 0 or more, never a range. The timeline refuses an unknown column, the column itself, `start` on a later column, and `start` when a column is called `start`.
- `src/usdm4/assembler/timeline/columns.py` — a timing with `from` is `timing_delay` + `timing_from`, not `timing`: never the anchor, never read by another column's arithmetic; its printed text is the label.
- `src/usdm4/assembler/timeline/plan.py` — `_node`: a delay from a column is `After` that column's instance (`_from_index`, warning and U4-3 when the id is missing); `from: start` builds a `START` node (`_start_node`) with no visit, the anchor when no column is one, else zero before the anchor; no "first column is the anchor" warning for it.
- `src/usdm4/assembler/timeline/build.py`, `naming.py` — the start node becomes `T<n>-START`, no encounter, no activities, the timeline's entry.
- Tests: `tests/usdm4/assembler/timeline/test_plan.py` (16), `tests/usdm4/assembler/schema/test_schedule_timeline_schema.py` (13), `tests/usdm4/assembler/test_timeline_assembler.py` (3). Timeline, schema, assembler and pin tests pass (Dave ran the full suite).

**Figures.** None here; through the corpus, NCT02971956, NCT04250350 and NCT02551653 match on every rung with `usdm4_protocol` 118 (`protocol_corpus/docs/next_steps.md`).

**Rejected.** Measuring an untimed column from the anchor instead of U4-3 (it puts early termination at Day 1, as when U4-3 was taken). A larger timing grammar carrying the source in the value text (`30 days from column 6`): the source is its own field.

## 2026-10-19 — GitHub 93 (branch `93-type-soa-epochs-from-ct`): SoA epochs typed from C99079

**Repo**: `usdm4`. Driven from usdm4_protocol GitHub 117 (the SDTM trial design model, its decision D23) and udp_prism's trial design work (their entries of the same date). Nothing committed.

**What it was.** `timeline/build.py` `_add_epochs` matched each schedule epoch heading against the C99079 terms in `data/house_names.yaml` to choose its name (`Screening` -> `SCR`), then typed every epoch Treatment Epoch, so screening, washout and follow-up epochs were all typed as treatment.

**What changed.**
- `src/usdm4/assembler/timeline/naming.py` — `Naming.epoch_term(label)`: the C99079 submission value a heading matches (longest candidate first, as before), or None. `epoch_name` now uses it; names are unchanged.
- `src/usdm4/assembler/timeline/build.py` — `_epoch_type`: the type from that term through the CT library (all 15 house terms resolve, e.g. SCREENING -> C202487 Screening Epoch, WASHOUT -> C42872 Washout Period, FOLLOW-UP -> C202578 Follow-Up Epoch). Unmatched -> Treatment Epoch with a warning naming the heading; redacted -> Treatment Epoch, no warning.
- `tests/usdm4/assembler/timeline/test_epoch_type.py` — 18 tests: the match, names unchanged, types, unmatched warned, redacted.
- `tests/usdm4/test_files/timeline_pin/expected_*.json` — all 9 pins re-saved; checked first that the only differences were `epochs[].type` code and decode.

**Figures.** Full suite 3981 passed, 2 skipped, 2 xfailed (run in this session; Dave's gate passed). Typed over the existing step 1 USDM labels: udp_prism 47 of 78 epochs, protocol_corpus 1,353 of 2,591; the rest keep Treatment Epoch.

**Rejected.** Fixing the `match` lists in the same change: it changes epoch names too (Dave: separate, measured on its own).

**Found, not this work.** N27.

**Downstream.** Nothing in usdm4_protocol, usdm4_fhir, protocol_corpus scripts or udp_prism reads `StudyEpoch.type`; goldens that store whole USDM with SoA epochs (usdm4_protocol and usdm4_fhir integration tests) will differ on epoch type only.

## 2026-10-19 — Every footnote with a marker is kept as a condition

**Repo**: `usdm4`, GitHub 94, branch `94-keep-every-footnote-condition`. Caller: the `protocol_corpus` footnotes rung (its issue 33; full entry in its `memory.md`, 2026-10-19).

**What it was.** `TimelineBuild._add_conditions` dropped a footnote whose marker no column, activity or cell used (the docstring's Excel round-trip reason no longer holds: `usdm4_excel` imports a condition with no references with a warning), ignored a marker used with no legend entry without a word, never read markers on a `HeaderNote`, and listed an instance twice when a footnote sat on a column and on a cell in it. One condition per footnote, pointing at its instances and activities, stays (Dave).

**What changed.**
- `src/usdm4/assembler/timeline/build.py` — an unused footnote becomes a `Condition` with empty `contextIds` / `appliesToIds`, warned; a marker with no footnote is warned with the columns and activities it is on (`_where`); `_link` adds each instance and activity once; the summary reads `in / referenced / aligned / unused / dropped_no_ref`.
- `src/usdm4/assembler/schema/schedule_timeline_schema.py` — `HeaderNote.markers` (input schema change).
- `src/usdm4/assembler/timeline/columns.py` — `Column.all_markers` adds the notes' markers after the values'.
- `docs/spec/timeline_assembler.md` — R9 restated.
- Tests: `tests/usdm4/assembler/test_timeline_assembler.py` (4 new, 1 changed), `tests/usdm4/assembler/timeline/test_columns.py` (1 new, 1 changed). Pins re-saved: `features` and `nct04557384` gain three unused footnotes, `nct05565742`, `nct05565742_r6` and `nct06454630` lose a duplicated instance id; nothing else moved. 1,581 assembler tests pass (Dave ran the touched ones).

**Rejected.** One condition per footnote per place printed (exact cells in USDM): a condition points at several instances and activities by design (Dave); the 5 of 71 cell footnotes whose cells are not a full rows-by-columns block keep their exact cells in the corpus ground truth. Moving a row-only footnote's activity from `contextIds` to `appliesToIds`: tidying, dropped.

## 2026-10-23 — Every loop is Entry → loop start → Pad → untimed Decision

**Repo**: `usdm4`, GitHub 95, branch `95-soa-patterns`. Source of the patterns: `protocol_soa_patterns` `docs/working/node_patterns.md` and `docs/diagrams/node_patterns/` (Dave, 2026-10-22), read only, not changed.

**What it was.** Each loop the assembler built put the `Timing` on its `ScheduledDecisionInstance` (a cycle range's decision `After` its last printed day by the rest of the cycle, an open repeat's `After` the visit by the period, a gate's `After` the gate by 1 day), and the loop's first node carried the timing from outside the loop, so a pass that looped back was timed again from outside. Single cycles had no node marking their full length. Dave's rules: a Decision has no Timing; every loop is Entry (takes the outside timing) → loop start (0 after the entry) → … → Pad (no encounter, no activities, carries the pass) → untimed Decision looping back to the loop start; single cycles get a Pad.

**What changed.**
- `src/usdm4/assembler/timeline/plan.py` — node kinds `ENTRY` and `PAD`; a decision node has no timing (`timing_type`, `relative_to` None). Cycle range: `_add_loops` puts `C{n}ENTRY` before the range's first node with the range's `Day 1` timing (`_cycle_entry`, `_entry_for`; the anchor moves to the entry when `Day 1` was it), `C{n}PAD` after its last column `After` `Day 1` by the length less one (`_pad_node`; a length that cannot be read or converted, or a last day beyond it, is a zero pad after the last column, warned), then the untimed decision. Single cycle: a pad only, none when the length is missing or does not convert. Open repeat: `R{n}ENTRY` takes the visit's timing, `R{n}PAD` `After` the visit by the period less one day (`_less_one_day`; months and years do not convert, so the whole period, warned). Gate: `G{n}ENTRY` 0 after the previous node, the gate 0 after it, `G{n}PAD` 1 day after the gate. End nodes are `After` the pad by 0. `_previous` skips a decision when timing the next node.
- `src/usdm4/assembler/timeline/build.py` — `_add_loop_node` builds the entry and pad as instances with no encounter and no activities; `_add_timings` writes no Timing for a decision.
- `src/usdm4/assembler/timeline/naming.py` — `cycle_name` (`C3+ENTRY`, `C3+PAD`, `C3+DEC`); gate and repeat names take `ENTRY` / `PAD`.
- `docs/spec/timeline_assembler.md` — R5 and R8 restated, U4-10 and U4-38 amended, new decision U4-39 (the loop pattern). Open-repeat pad offset ruled 2026-10-23 (Dave): the quoted period is the cycle time, so the pad is the period less one day, as built.
- Tests: `tests/usdm4/assembler/timeline/test_plan.py` (`TestRanges` rewritten, `TestSingleCyclePad` new, single-cycle, day-one and gate expectations updated), `test_r5_nct05197426.py`, `test_r8_nct03069989.py`, `test_repeat.py`, `test_naming.py`, `tests/usdm4/assembler/test_timeline_assembler.py`. Pins `expected_nct05197426.json` and `expected_nct03069989_r8.json` re-saved by Dave; no other pin input has a cycle, gate or repeat. The input schema did not change; no d4k rule needs a Timing on every instance (DDF00031, DDF00038 hold).

**Figures.** Tests pass (Dave ran them). udp_prism run complete (Dave, 2026-10-23); none of its checks reads the schedule timeline.

**Rejected.** Writing code before the analysis, the issue and the branch existed (Dave: analysis first). Moving the pad to the full cycle length so the expander's passes come out the cycle length apart: the diagrams settle the pad at CL − 1; the expander was not changed.

## 2026-10-25 — GitHub 96 (branch `96-unmapped-codes-get-defaults`): CT lookups with no defaults, sourcing coded, the loop pad is the full period

Driven from udp_prism (section 6 interventions); udp_prism `memory.md` 2026-10-25 holds the figures.

**What it was.** Route, frequency and dose form text that did not match a CT term was given a default code, so a wrong code stood where the printed text should be. Product sourcing text ("Central", "Local") was not read. The loop pad was CL − 1, so the expander's passes did not come out one period apart.

**What changed.**
- `src/usdm4/encoder.py`: route and frequency go through `_lookup_ct` with no default; `ct_term` added; dose form falls back to the printed text. `SOURCING_MAP` (CENTRAL/CENTRALLY → C215659 "Centrally Sourced Indicator", LOCAL/LOCALLY → C215660) and `sourcing(text)` via `_lookup_ct(text, SOURCING_MAP, "C215483", ...)`.
- `src/usdm4/assembler/schema/study_design_schema.py`: `ProductInput.sourcing: str = ""`.
- `src/usdm4/assembler/study_design_assembler.py`: `_sourcing` returns `self._encoder.sourcing(text)`; `params["sourcing"]` set when not None.
- `src/usdm4/assembler/timeline/plan.py`: the loop pad is the full period. Tests and the R5 pin updated. This reverses the 2026-10-23 "Rejected" note on the full cycle length (Dave, this session).
- Tests: `test_study_design_assembler_products.py` (sourcing) and the encoder and timeline tests.

**Figures.** Section 6 interventions end to end 0 unexplained, 27 / 27 (udp_prism set, with the usdm4_fhir 56 and usdm4_protocol 129 branches). Tests run by Dave: pass.

**Rejected.** A default code for unmatched text (it hides the printed value behind a wrong code).

**Found, not this work.** None (N71, a regimen with no USDM home, is in udp_prism `docs/issues.md`).

## 2026-10-30 — GitHub 97 (branch `97-section-that-skips-a-heading-level-is-dropped`): a section that skips a heading level is kept

**Repos.** usdm4 (this entry). Driven from the UDP PRISM project (udp_prism N22; pointer in `udp_prism/memory.md` 2026-10-30). raw_docx issue 16 now numbers such sections as Word shows them.

**What it was.** `DocumentAssembler._section_to_narrative` builds the narrative tree by section level. A section more than one level below the one before it (9.2 then 9.2.1.1, no 9.2.1) reached a recursion level with no previous section: it logged the error "No previous section set while processing sections" and skipped the section and its text. IGBJ 9.2.1.1 and Takeda_Vedolizumab 9.5.1.1 / 9.5.1.2 were lost at step 1. The documents do skip the level; Dave ruled to accommodate it and report it.

**What changed.**
- `src/usdm4/assembler/document_assembler.py` — `_section_to_narrative`: with no previous section at the level, the section is processed one level down under the same parent, so it becomes a child of the nearest section above it. The error is replaced by a warning: "Section 9.2.1.1 skips a heading level (no 9.2.1); placed under 9.2" ("the top level" when there is no parent).
- `tests/usdm4/assembler/test_document_assembler.py` — `test_section_to_narrative_skipped_heading_level` (9, 9.2, 9.2.1.1, 9.5: tree and warning) and `test_section_to_narrative_skipped_level_at_top` (a document starting at 1.1), both through `execute()`.

**Figures.** pytest all pass, coverage 100% (Dave). udp_prism narrative end to end 30 → 27 unexplained, no section missing; round trip exact.

**Rejected.** Registering the three sections as a known data issue instead (Dave: accommodate the document error and report it). Calling `_section_to_narrative` directly in the test after creating the document version by hand: the create returns None in this fixture (the two older tests skip on that), so the first version failed.

**Found, not this work.** None.
