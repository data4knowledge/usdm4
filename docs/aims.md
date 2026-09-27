# USDM4 — aims

Why this package exists and what it is for. `issues.md` holds what is still wrong,
`next_steps.md` the order it is being worked in, and `spec/` the detailed designs. Work that
serves none of the aims below does not belong here.

## Purpose

`usdm4` is the Python package for the CDISC TransCelerate Unified Study Definitions Model
(USDM), version 4. It lets a program read, build and validate USDM4 JSON. What it builds should be
high-quality USDM: conformant to the model, the controlled terminology and the DDF rules.

It provides the common, basic USDM4 facilities that other packages build on. It does not
try to do everything: work specific to one use — reading protocol documents, rendering
documents, other formats — belongs in the package that needs it. It is self-contained, with
no dependency on `usdm3` or any other USDM package.

## What it provides

**Handling USDM4 files.** The API model: one Pydantic class per USDM4 class (`api/`). Load
USDM4 JSON from a file or a dict into those classes and write it back out (`USDM4.load`,
`loadd`, `from_json`), and convert USDM3 JSON to USDM4 (`convert/`). A data
store for walking a loaded study by id, class and parent, and resolution of the standard
`usdm:ref` / `usdm:tag` references in narrative text (`TagResolver`).

**Building, two ways.**

- **The builder** (`builder/`) is the low-level mechanism. It creates any USDM4 class with
  ids assigned and cross-references kept, and supplies correct codes from the CDISC
  controlled terminology, the CDISC biomedical concepts and the ISO 3166 / 639 libraries.
  The caller decides every object; the builder makes each one correct.
- **The assembler** (`assembler/`) is the high-level mechanism. It takes one structured
  input (`AssemblerInput`, validated at the boundary) describing a study as a protocol
  presents it — identification, document, population, study design, amendments, schedule
  of activities — and turns it into a complete USDM4 study through the builder. It encodes
  the common patterns so each caller does not reinvent them: sponsor and identifier
  organisations, amendment scopes, and in the schedule of activities cycles, cycle loops,
  washout gates, conditional timelines, copied visits, profile timelines and footnote
  conditions (`spec/timeline_assembler.md`).

**Validating, with two engines.**

- **d4k** (`rules/`) — the package's own Python implementation of the DDF rule catalogue:
  all 210 V4 rules, one file per rule. Fast, no external service, readable line by line,
  and extensible with rules of our own.
- **CDISC CORE** (`core/`) — a wrapper around `cdisc-rules-engine`, the reference
  implementation, with its cache management and the workarounds its known bugs need
  (`cre_issues.md`).

Both check a USDM4 JSON file and report what they find. They draw no conclusions: whether
a finding matters is for the user to decide, given their use case. The two can run side by
side so their results can be compared (`validate/`). Where they disagree, d4k mirrors CORE
unless there is a recorded reason not to; every divergence is explained in `cre_issues.md`.

**Also.** A minimum valid study for a start (`USDM4.minimum`), and an expander that walks a
built schedule and lists what happens to a subject day by day — an illustration of executing
a USDM timeline, not a normative one.

## Principles

- **What `usdm4` builds should be correct USDM.** A made-up code, an empty required field
  or an unanchored condition created by the builder or the assembler is a defect in
  `usdm4`. The validators report on any file; they judge nothing.
- **Same input, same USDM.** Building is by fixed rules: no AI, no guessing, no reading of
  printed text. Judgement — what a protocol says and how it is organised — belongs to the
  caller, which hands over structured values. A wrong rule is a bug, proven and fixed with a
  unit test here.
- **USDM stores, presentation is elsewhere.** `usdm4` stores what the model holds. How an
  ICH M11 protocol words or lays it out is applied when it is rendered, never stored here.
- **Always build if possible, and say what was wrong.** A value that cannot be used is
  warned with its location and set aside; a partial or silently dropped result is not
  acceptable.
- **Everything is explained where it is decided.** Rule-interpretation calls and design
  decisions are recorded with their reasons and the options rejected (`cre_issues.md`,
  `spec/`), so the same question is not argued twice.

## Scope

A facility belongs in `usdm4` when it is common to USDM4 work in general and more than one
package would otherwise build it. Otherwise it belongs elsewhere. For example:

- Reading protocol documents (PDF, Word) and deciding what they say — not here; the caller
  hands the assembler structured values.
- Rendering USDM as a document (ICH M11 or otherwise) — not here.
- Other formats, such as FHIR or Excel — not here.
- CDISC CORE itself — not here; `usdm4` wraps it, and d4k is a second, independent engine,
  not a replacement.
