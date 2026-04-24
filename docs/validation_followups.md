# d4k validation engine — follow-up items

Started 2026-04-24, refreshed end-of-day the same day. Captures the
state of CORE-vs-d4k reconciliation after a full day's work. Lives
alongside `core_validation.md` (the CORE module user guide) and
`next_steps.md` (the rule coverage roadmap).

## Context

`validate/run.sh <usdm.json>` runs CORE and d4k against the same USDM
JSON and produces a rule-by-rule alignment report via
`validate/compare.py`. The comparer reconciles CORE's `CORE-NNNNNN` ids
to d4k's `DDF000NN` ids via the
`authorities[].Standards[].References[].Rule_Identifier.Id` field in
the CORE rules JSON cache, so same-rule hits from both engines collapse
to a single row.

Four sample inputs are committed under `validate/`: `sample_usdm_1.json`
through `sample_usdm_4.json`. Each progressively richer; bigger samples
exercise more rules, and also trigger more CORE execution errors.

## Current state

| Sample | CORE findings | CORE exec_errors | d4k findings | aligned_pass | aligned_fail | core_only | d4k_only | count_mismatch |
|--------|---------------|------------------|--------------|--------------|--------------|-----------|----------|----------------|
| 1      | 60            | 2578             | 26           | 192          | 13           | 7         | 1        | 0              |
| 2      | 25            | 5447             | 286          | 191          | 11           | 2         | 8        | 1              |
| 3      | 94            | 5878             | 509          | 180          | 22           | 4         | 5        | 2              |
| 4      | 40            | 6747             | 566          | 187          | 13           | 3         | 10       | 0              |

**There are no known d4k bugs left.** Every remaining divergence falls
into one of the categories below.

## Remaining divergences — triage

### 1. CORE-side pandas/numpy dtype bug — the dominant source of noise

Every sample produces thousands of CORE `exec_errors` (2578 → 6747 as
samples grow). The signature is consistent across rules and samples:

```text
Failed to execute rule operation. Operation: codelist_extensible,
Target: None, Domain: StudyDesignPopulation, Error: You are trying to
merge on object and float64 columns for key 'codeSystemVersion'. If
you wish to proceed you should use pd.concat.
```

And, for the record-count family:

```text
Cannot perform 'rand_' with a dtyped [float64] array and scalar of
type [bool].
```

CORE's internal DataFrame for CT packages carries `codeSystemVersion`
as `float64` (likely a pandas type inference from an all-missing
column), while the incoming USDM data has it as strings like
`"2023-12-15"`. The merge fails, CORE falls back to a generic
"not in codelist" message, and the `details` block shows every CT
lookup returned `null`.

**Rules affected across all four samples:**
DDF00093, DDF00094, DDF00114, DDF00141, DDF00142, DDF00143, DDF00144,
DDF00146, DDF00181, DDF00187. Every sample's `core_only` set is
dominated by this family.

**Action.** Drafted as a bug to file at
<https://github.com/cdisc-org/cdisc-rules-engine>. Until fixed,
`core_only` findings on these rules are noise, not d4k gaps.

**Expected impact when fixed.** All `core_only` rows across the four
samples should flip to either `aligned_pass` or `aligned_fail`,
clearing most of the remaining noise.

### 2. CORE JSONata bug on multi-parent activities (DDF00161)

Sample 3's DDF00161 `count_mismatch` is d4k 2 / CORE 4. The two extra
CORE findings are on Activities that appear as a child in TWO
different parents' `childIds` lists (Activity_23 and Activity_24 —
children of both Activity_19 and Activity_34).

CORE's JSONata predicate for issue 2 is:

```text
$pacts[self in children.id].[id, children[id!=self].id,
                             children[id!=self].**.children.id]
```

For multi-parent activities this produces a nested array
`[[id1, [siblings1], [deep1]], [id2, [siblings2], [deep2]]]`.
JSONata's `in` operator doesn't flatten across the inner sibling
arrays, so valid siblings that appear in CORE's own reported
"Parent Activity's other descendants' ids" still fail the `in` check.

d4k handles this correctly by explicitly unioning the allowed set
across all parents (added this session).

**Action.** File upstream alongside the dtype bug; the multi-parent
JSONata is its own distinct defect. No d4k action needed.

### 3. DDF00164 / DDF00165 — treatment of `"0"` as a section number

Sample 2, each `d4k_only` with 1 finding on `NarrativeContent_1` (the
Title Page): `sectionNumber: "0"`, `displaySectionNumber: false`.

The d4k implementation treats the rule symmetrically: `displayX=true`
iff `X` is truthy. Python's `bool("0")` is `True`, so d4k sees
`sectionNumber="0"` as "a number is specified" and flags the
mismatch. CORE treats `"0"` as "no section" and passes.

The DDF text is ambiguous ("If a section number is to be displayed
then a number must be specified and vice versa").

**Decision still open.** Options:

- *Leave as-is.* d4k defensibly strict per the rule text.
- *Relax to match CORE.* Treat `"0"` specially — either strip it to
  an empty string before the truthy test, or strip `"0"`-only
  sectionNumbers entirely. Risk: this is data-specific hand-tuning.

**Current preference.** Leave as-is unless a canonical spec clarifies
that `"0"` is "unset". Documenting to avoid re-litigation.

### 4. DDF00187 off-by-one on sample 2

One `NarrativeContentItem` (`NarrativeContentItem_2`) whose text starts
with its own nested `<div xmlns="http://www.w3.org/1999/xhtml">` wrapper
is flagged by CORE ("body has non-whitespace character content") but
passes d4k's validator. 5 of CORE's 6 findings align exactly (same
line numbers, same error messages); this is the one outlier.

The root cause is a difference in wrapping context. d4k wraps the
fragment as
`<html>...<body><div>FRAGMENT</div></body></html>` so plain text,
inline markup, and block markup all validate; CORE appears to wrap
directly in `<body>` which produces a character-content error when
the fragment itself declares a namespace-prefixed wrapper.

**Decision still open.** Aligning this one case would need per-source
heuristics (e.g. detect a top-level `<div xmlns=...>` and re-parent);
cost probably exceeds benefit.

## Resolved this session (for the record)

Items that were open when this doc was first written but are now
closed. Kept so later readers don't re-discover them:

- **DDF00247 / DDF00187 — XHTML schema validation.** Rewritten to use
  `lxml` + the bundled USDM-XHTML 1.0 XSD (65 schema files copied from
  the CORE resource cache at
  `src/usdm4/rules/library/schema/xml/`). Shared validator at
  `src/usdm4/rules/xhtml_validation.py`. `lxml>=4.9` added to
  `setup.py` install_requires; the schema files added to
  `package_data`. Seven of eight sample-rule cells across the four
  samples now exact-count match with CORE.

- **The DDF00051, 00075, 00155, 00166, 00249 family (d4k_only).**
  These were suspect earlier; on investigation each is d4k correctly
  catching real CT-membership issues (invalid decode, invalid
  codeSystemVersion, missing criterionItem) that CORE misses because
  of its dtype bug. d4k is doing real work. Keep flagging.

- **DDF00073 granularity.** Rewrote to emit one failure per
  `(codeSystem, codeSystemVersion)` group with a representative
  instance and count, rather than one per Code. 623 findings →
  2 findings on sample 2, matching CORE's `$record_count` semantics.

- **Fifteen rules using `STUDY_DESIGN_KLASSES` / `STUDY_DESIGN_CLASSES`.**
  The constant was `["InterventionalStudyDesign",
  "ObservationalStudyDesign"]`; samples carry `"StudyDesign"` as a
  concrete type. Added `"StudyDesign"` to the list in all 15 files so
  the loops run against any StudyDesign-family instance.

- **DDF00008.** XOR check now catches both edges (both empty AND both
  set), not just the both-set case. Unlocked 4 findings on sample 3.

- **DDF00009.** Fixed class-name typo (`ScheduledTimeline` →
  `ScheduleTimeline`), added the timeline-scoped anchor check
  (Fixed Reference timing target must be in this timeline's own
  `instances` list), recognised the CT code C201358 alongside the
  decode fallback.

- **DDF00040.** Was iterating `StudyElement` and looking for a
  non-existent `elements` attribute on it. Rewritten to collect
  referenced ids from each `StudyCell.elementIds` and flag every
  `StudyElement` not in the referenced set.

- **DDF00041.** Was checking only that each Endpoint had *some*
  level set. Rewritten to count Endpoints where `level.code ==
  "C94496"` (Primary) across all StudyDesign objectives and fail if
  count < 1.

- **DDF00083.** Was literally `return True`. Rewritten as a
  DataStore-wide id-uniqueness walk over `data.data` that groups
  `(id, instanceType)` occurrences and reports duplicates, matching
  CORE-001015's `**.*[id and instanceType]` semantics.

- **DDF00097, 00098, 00132, 00133.** The four "population-or-cohorts"
  consistency rules, previously over-strict (unconditionally required
  the attribute on the population). Rewritten to the full CORE
  semantics: fail if specified in both places, fail if specified on
  only a subset of cohorts, fail if required-but-unspecified (for
  00097 and 00098 only — 00132 and 00133 have "if defined"
  conditionals in their DDF text).

- **DDF00141.** Was `return pop_result or cohort_result` — a boolean
  short-circuit that hid StudyCohort failures when the
  StudyDesignPopulation side passed. Now `return self._result()` so
  accumulated errors across both scopes are honoured.

- **DDF00161.** Multi-parent handling rewritten: the parent-of map
  now tracks all parents (was single-parent, last-writer-wins), and
  issue 2's allowed set is unioned across them. Net effect on
  sample 3: d4k dropped one accidentally-right finding; the remaining
  2 findings are both genuine.

- **DDF00194.** Was iterating `LegalAddress` (not a class in the V4
  API) and using the wrong attribute name `line` instead of `lines`.
  Rewritten to iterate `Address` and walk the real attribute list.

- **`validate/compare.py`.** Added CORE→DDF id reconciliation via
  the CORE rules JSON `authorities` map, eliminating double-counted
  divergence rows where the same rule appeared once under each id
  namespace.

- **47 V3-only rule stubs deleted.** DDF-RA/USDM_CORE_Rules.xlsx marks
  them `V4=N`; the stubs were residue from an earlier generator pass
  before the V4 filter existed. All were `raise NotImplementedError`.
  d4k's engine loader discovers rules by glob, so removal was clean.

## Not follow-ups — defensibly d4k-stricter

For the record, d4k is legitimately stricter than CORE on these — by
design, not bug:

- **DDF00082** (d4k_only across every sample) — d4k validates the JSON
  against `schema/usdm_v4-0-0.json`. CORE handles schema-shape checks
  outside its rule engine. Scope difference.

- **The CT-membership family on samples 2/3/4** — DDF00051, 00075,
  00084, 00155, 00166, 00249. d4k's `_ct_check` and helpers complete
  correctly when CORE's dtype merge fails, so d4k surfaces real CT
  issues CORE can't. Keep flagging.
