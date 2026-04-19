# USDM4 validation engine — next steps

Written 2026-04-19, refreshed after Stage 3 closed the rule library.
Read alongside `docs/lessons_learned.md` which captures the *how*.
This file captures the *what next*.

## Current state

**Rule coverage:** **210 of 210 V4 DDF rules covered (100 %).** 207
implemented + 3 delegated to DDF00082's schema validation.

**Stub detection (V4-accurate):**

```bash
for f in src/usdm4/rules/intermediate/rule_ddf*.yaml; do
    rid=$(basename "$f" .yaml)
    py="src/usdm4/rules/library/${rid}.py"
    [ -f "$py" ] && grep -q NotImplementedError "$py" && echo "$rid"
done
```

Returns empty.

Plain `grep -l NotImplementedError rule_ddf*.py` still returns some
hits, but all of them are non-V4 DDF IDs (rule files that exist
without a corresponding intermediate YAML — legacy stubs from
pre-V4 catalogues). These are not on the V4 scope.

The YAML `classification` field is stale for many rules (biconditional
predicates, delegated no-ops, etc.) — don't trust it as a stub signal
(§13 of lessons_learned.md).

**Committed so far this session** (90 rule files touched across
multiple commits; see the §10 progression table in
`lessons_learned.md` for the full batch breakdown):

- 87 hand-authored (real `validate()` bodies)
- 3 no-op delegates to DDF00082 (schema conformance)

**Uncommitted changes** (if any): check `git status`. Latest work
added the 4 Stage 3 rules + doc refresh.

**`test_package.py` baseline** — same 2 pre-existing failures that
have blocked the package assertion all session:

- `test_validate` (blocked by pre-existing DDF00166 fixture issue)
- `test_example_2` (blocked by pre-existing DDF00217 placeholder issue)

**Legitimate fixture findings** from rules that fire but are masked
by the pre-existing blockers (see §14 of lessons_learned.md):

- **DDF00006** — one Timing has a partially defined window.
- **DDF00010** — two SubjectEnrollments share a name across amendments.
  Matches CORE's model-wide grouping; may revisit as per-parent.
- **DDF00035** — Code with decode "No Concept Code" used with code
  `AEHLGT` in the CDISC 2024-09-27 codelist — broken 1:1 mapping.
- **DDF00075** — an Activity with no leaf references.
- **DDF00087** — Encounter prev/next chain of 50 vs. 5 encounters
  reached via SAI flow (fixture data issue).
- **DDF00088** — StudyEpoch prev/next chain of 4 vs. 2 epochs reached
  via SAI flow (same fixture data issue).
- **DDF00101** — Interventional StudyDesign with no Procedure linked
  to a StudyIntervention.
- **DDF00153** — Main ScheduleTimeline without a `plannedDuration`.
- **DDF00181** — SDDV with 4 GovernanceDates sharing (type C71476,
  scope [C68846 Global]) — real duplication.
- **DDF00185** — Administration with dose but no administrable
  product (direct or embedded).
- **DDF00187** / **DDF00247** — malformed XHTML in NCItem /
  EligibilityCriterionItem text.
- **DDF00188** — `plannedSex: [{code: C49636 "Both"}]` (single "Both"
  encoding rejected; must be separate Male + Female entries).
- **DDF00189** — StudyRole with empty `appliesToIds`.
- **DDF00198** — an SDDV not referenced from any StudyVersion or
  StudyDesign.
- **DDF00236** — BC whose synonym equals its label (case-insensitive).

15 latent findings in total. None change pass/fail because DDF00166 /
DDF00217 are the hard blockers. Unblocking those two is now the
highest-value remaining task.

## Immediate next steps — ordered

### 1. Commit Stage 3 + doc refresh

Clean checkpoint — the rule library is feature-complete at 100 % V4
coverage.

### 2. Unblock `test_validate` / `test_example_2`

Converts `test_package.py` into a live regression detector. The
latent-findings list above becomes visible / actionable as soon as
DDF00166 and DDF00217 are fixed. Without this step, every future
rule tweak risks silently introducing real-data failures that
blend into the pre-existing baseline.

**DDF00166** (`test_validate.json`): fixture has literal string
`"Protocol"` in a decode field where CORE expects a code from a
specific codelist.

**DDF00217** (`test_example_2.json`): placeholder strings `"None"`
and `"Decode"` appear in Code fields.

Both are fixture regenerations, not code changes. Edit the JSON or
regenerate via the assembler. Once green, the 15 latent findings
surface as real assertion failures and can be reconciled either
by fixing the fixtures or by accepting the new baseline.

### 3. CT cache refresh

DDF00237 (plannedAge.unit must be Age Unit C66781) is currently in
"skip gracefully" mode because C66781 isn't in the USDM cache yet.
Registered in `ct_config.yaml`; activates after a cache refresh
against the CDISC Library API. Requires network access.

### 4. Stage 4 — real-file regression against udp_prism

Run the full 210-rule library against the 21 protocols in
`udp_prism` and compare findings against expected baselines. First
pass will surface three categories:

a. **Fixture drift** — test fixtures that predate recently-added
   rules. Example: DDF00188's `plannedSex: "Both"` encoding.
   Decision per finding: update fixture or accept baseline.

b. **Real data issues in protocols** — actual content problems that
   the rule library correctly flags. These are the reason the rule
   library exists. Triage with the protocol owners.

c. **Rule-interpretation bugs** — rules that fire on data that is
   actually valid, revealing a Python bug or a spec
   misinterpretation. Triage per rule; likely candidates:
   DDF00010 (global-unique-name interpretation), DDF00087 / DDF00088
   (first-chain-head selection), DDF00091 (appliesToIds contracts).

Each category needs a separate reconciliation pass. Expect the
first run against real data to produce a lot of noise — that's
expected and normal for a newly-completed rule library.

### 5. (Optional) Real fixtures for the 87 hand-authored rules

All 87 have `@pytest.mark.skip` on positive/negative fixture tests
(metadata-only coverage). A minimal JSON blob per rule would
convert them into live behavioural tests. ~15 min per fixture pair,
so ~22 hours to do them all. Worth doing for the structurally
interesting rules (DDF00189 mutex, DDF00196 1:1-dict-of-sets,
DDF00124 regex-ref, DDF00010 model-wide uniqueness, DDF00161
preorder-walk) first; the others can wait.

### 6. (Optional) M11 docx-side plan (usdm4_protocol)

Per `usdm4_protocol/docs/m11_validation_plan.md`: `RuleM11S###`
(structural), `RuleM11T###` (technical), `RuleM11C###` (content).
Generated from `m11_specification` at authoring time. Needs its
own planning pass — separate scope from the usdm4 engine work.

## Session-to-session reminders

- **Never implement without explicit authorization.** Planning is not
  authorization.
- **Severity from the YAML, not memory.** The metadata test catches
  mismatches but costs a regen cycle.
- **xlsx attribute name ≠ JSON field name.** Always verify via
  `dataStructure.yml` or by grepping a fixture before coding.
- **`# MANUAL: do not regenerate` sentinel** on every hand-authored
  rule. Without it, stage-2 will overwrite the work.
- **"Specified" can mean "has an id"** in CORE semantics — mirror the
  `$exists(...)` guard in the JSONata rather than defaulting to
  Python truthiness. See §12 of lessons_learned.md.
- **When rule text and CORE JSONata disagree, mirror CORE.** Note the
  divergence in a comment. See §16.4 of lessons_learned.md.
- **When a real schema validator already covers a rule, delegate**
  rather than re-implementing. See §10.
- **Trust ct_config bindings over the YAML's `class` field.** See
  §19.4.
- **When a CT codelist is registered but cache is stale, skip
  gracefully** rather than raising CTException. See §19.2.
- **For "topology / ordering" rules, ask the domain owner what the
  attribute is actually used for in practice.** The answer often
  collapses three nested JSONata predicates into three FK lookups.
  See §20.2.
- **CT cache drift** breaks tests that pin specific dates. Not a code
  regression.

## Baseline reference

Last known good test summary:

```
tests/usdm4/test_package.py
  14 passed
  2 failed (DDF00166 / DDF00217 — pre-existing)

90 rule tests touched this session (87 hand-authored + 3 delegated no-ops)
  90 passed (metadata + delegated behaviour)
  174 skipped (positive/negative fixture TODOs on hand-authored rules)

V4 DDF coverage: 210/210 (100 %)
```
