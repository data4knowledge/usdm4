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
