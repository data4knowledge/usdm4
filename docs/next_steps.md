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
