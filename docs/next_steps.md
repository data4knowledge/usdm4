# USDM4 validation engine — next steps

What's still open. The rule library is feature-complete (210 of 210 V4
DDF rules covered, 207 implemented + 3 delegated to DDF00082's schema
validation). CRE-vs-d4k reconciliation is at the no-known-d4k-bugs
state on CRE 0.16.0; the corpus baseline of record is
`validate/corpus_out_cre_0_16_v2/` and the bug catalogue is in
`docs/cre_issues.md`. Read this file alongside `lessons_learned.md`
(the *how*) and `rule_generation_retrospective.md` (the as-built
record of the rule generation process).

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
Revisit as per-parent uniqueness. See §16.4 of `lessons_learned.md`
on rule-text-vs-CORE disagreement.

**b. Fixture drift.** DDF00051 (Timing type CT — fixture uses labels
rather than decodes), DDF00157 (Environmental settings CT — invalid
C-codes), DDF00199, DDF00218 (other invalid CT decodes/codes), and
DDF00075 (Activities with no leaf references). Either fix the fixture
to use valid CT entries / proper refs, or — for DDF00075 — reconsider
the rule's strictness.

**c. Low-volume legit findings.** DDF00035, 40, 84, 87, 88, 101, 112,
153, 164, 165, 172, 181, 182, 185, 187, 188, 189, 201, 236, 247, 259
— each in the range of one to a handful of hits. Triage individually:
fixture fix vs rule fix vs accept. (The list is a snapshot from a
pre-rewrite run; refresh it against a current test run before using
it as a worklist.)

## 2. CT cache refresh

DDF00237 (`plannedAge.unit` must be Age Unit C66781) is in
"skip gracefully" mode because C66781 isn't in the USDM cache yet.
Already registered in `ct_config.yaml`; activates after a refresh
against the CDISC Library API (requires network).

## 3. Real-file regression against `udp_prism`

Run the full 210-rule library against the 21 protocols in `udp_prism`
and compare findings against expected baselines. Three categories
will surface:

- **Fixture drift** — test fixtures that predate recently-added
  rules. Decision per finding: update fixture or accept baseline.
- **Real data issues** — actual content problems the rule library
  correctly flags. Triage with protocol owners.
- **Rule-interpretation bugs** — rules that fire on data that is
  actually valid. Likely candidates: DDF00010 (global-unique-name
  interpretation), DDF00087 / DDF00088 (first-chain-head selection),
  DDF00091 (`appliesToIds` contracts).

Each category needs a separate reconciliation pass. Expect the first
run against real data to produce noise.

## 4. Refresh `validation_followups.md`

The rule-by-rule reconciliation state table in `validation_followups.md`
predates the CRE 0.16.0 upgrade. Compare against
`validate/corpus_out_cre_0_16_v2/` and update.

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
