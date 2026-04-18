# USDM4 validation engine — next steps

Written 2026-04-18 to hand off state between sessions. Read this alongside
`docs/lessons_learned.md` which captures the *how*. This file captures
the *what next*.

## Current state

**Rule coverage:** 151 of 210 V4 DDF rules have real `validate()` bodies
(~72 %). 59 remain as stubs.

**Stub detection:** use `grep -l NotImplementedError src/usdm4/rules/library/rule_ddf*.py`.
The YAML `classification` field is stale for rules where the biconditional /
implication predicate was hand-filled — don't trust it as a stub signal
(§13 of lessons_learned.md).

**Uncommitted changes** (as of this writeup): 29 hand-authored rules + 29
test files across 5 clusters. All metadata tests pass (13 A/B/C + 4 E +
4 F + 3 G + 5 one-offs = 29 pairs). `test_package.py` is at its
pre-existing baseline — same 2 failures as before the session started:

- `test_validate` (blocked by pre-existing DDF00166 fixture issue)
- `test_example_2` (blocked by pre-existing DDF00217 placeholder issue)

New rules firing against `example_2.json` that are *legitimate findings*,
not bugs (see §14 of lessons_learned.md):

- **DDF00188** — fixture has `plannedSex: [{code: C49636 "Both"}]` which
  the rule rejects (must be Male + Female separate entries).
- **DDF00189** — fixture has a StudyRole with empty `appliesToIds`.
- **DDF00236** — fixture has a BC whose synonym equals its label
  (case-insensitive). Warning-severity.

These surface in the package test output but don't change pass/fail
because the pre-existing failures are already blocking the assertion.

## Immediate next steps — ordered

### 1. Commit the 29 new rules

Single commit, scope obvious from the diff. Suggested message:

> Hand-author 29 LOW_CUSTOM / MED_TEXT / STUB rules
>
> Clusters: self-reference (4), quantity/unit (4), mixed-simple (5),
> distinct-within-scope (4), mutex-scope (4), orphan/reverse-FK (3),
> one-offs (5).
>
> All use the `# MANUAL: do not regenerate` sentinel. Coverage moves
> from 64 % → 72 % (135 → 151 of 210).
>
> test_package.py still at pre-existing baseline (DDF00166 / DDF00217
> fixture blockers). Tests 4 passing rules now fire legit findings
> against example_2.json: DDF00188, 189, 236. See lessons_learned.md §14.

### 2. Unblock `test_validate` / `test_example_2`

The two pre-existing test_package.py failures have been deferred through
multiple sessions. Fixing them converts the package tests into a live
regression detector — today any new rule firing hides behind these
existing failures.

**DDF00166** (`test_validate.json`): fixture has literal string
`"Protocol"` in a decode field where CORE expects a code from a
specific codelist. Either the fixture needs a valid CT code, or the
rule's acceptable-values list is wrong. Read the rule body and the
fixture side-by-side; most likely it's the fixture.

**DDF00217** (`test_example_2.json`): placeholder strings `"None"` and
`"Decode"` appear in Code fields. Clearly fixture problem — real
captures would use real C-codes.

Both are probably fixture regenerations, not code changes. Confirm by
reading the offending paths printed in the test output, then either
edit the fixture JSON or regenerate it via the assembler.

### 3. Keep hand-authoring — more tractable clusters remain

Per §9 of lessons_learned.md, the per-rule cost is ~5 min. Remaining
groups that look tractable without domain-deep interpretation, based on
rule text scanning:

**Amendment / reason (~3 rules)**

- **DDF00196** — one-to-one relationship between referenced section
  number and title within a StudyAmendment. Sibling of DDF00245.
- **DDF00255** — primary StudyAmendmentReason's code must not be "not
  applicable" (needs a CT code lookup — check the CORE JSONata for
  the code).
- **DDF00258** — StudyDesign must not have >1 of a specific set of
  characteristic codes ("Randomized", "Stratification",
  "Stratified Randomisation", ...). Set intersection check, similar
  shape to cluster E.

**Scoped uniqueness (~2 rules)**

- **DDF00173** — every identifier must be unique within the scope of
  the organization that owns it. Group-by-organization pattern.
- **DDF00174** — an organization has at most one StudyIdentifier for
  the study. Sibling of DDF00173, same group-by shape.

**Cross-reference integrity (~3 rules)**

- **DDF00114** — Condition.context points to a valid Activity or SAI
  instance. FK-resolution check via `instance_by_id`.
- **DDF00124** — ParameterMap referenced items must be available
  elsewhere. Similar FK shape.
- **DDF00244** — NarrativeContentItem referenced items must resolve.

**At-least-one / multi-relationship (~2 rules)**

- **DDF00075** — Activity must refer to ≥1 of procedure / BC / BCCat /
  BCSurrogate. `any()` across 4 id list attrs.
- **DDF00163** — NarrativeContent → child and/or content-item text.
  Similar shape.

**Masking / blinding (~2 rules, need CT code)**

- **DDF00191** — open-label blinding → no masking on any StudyRole.
- **DDF00192** — double-blind → masking on ≥2 StudyRoles.

Both need to identify "open label" and "double blind" codes from the
CDISC Blinding Schema codelist — grep the rule text and CORE JSONata
for `(C\d+)` to pull them out.

**Observational phase (~1 rule, CT code)**

- **DDF00232** — observational study must have study phase decode
  "NOT APPLICABLE". Check CT code.

**Estimated aggregate:** ~13 rules if all of the above land cleanly.
Would push coverage to roughly 78 %.

### 4. Harder — consider skipping or batching separately

- **Timing state machines:** DDF00006 (window fully-defined), DDF00007
  (Fixed Reference → one instance). Need genuine domain interpretation.
- **Cross-class ordering consistency:** DDF00087, DDF00088 — encounter /
  epoch ordering must match SAI ordering. Cross-class graph walk.
- **Activity children / ordering:** DDF00160, DDF00161 — similar
  cross-walk logic.
- **Duration state:** DDF00010 (unique names of child instances of the
  same parent class — model-wide).
- **Schema conformance:** DDF00081 — this one is "class relationships
  must conform to USDM schema via API spec". Almost certainly either
  a no-op (schema is enforced elsewhere) or a massive refactor. Skip.
- **HTML formatting:** DDF00187, DDF00247 — "expected to be HTML
  formatted". Could ship a weak heuristic (contains `<` or `&`) but
  that's not really a validation. Skip or ship as pure format check.
- **Reference format regex:** DDF00162 — parse-and-validate format of
  references in narrative text. Needs regex spec from somewhere.

### 5. Regenerate expected error baselines for the rules that fire

Running `test_package.py` to see which of the 29 new rules fire on the
current fixtures would prove each rule's behavior beyond just metadata.
After fixing the DDF00166/00217 blockers in step 2, re-run the package
tests, and for any rule that consistently fires the same way, lock in
the output as a baseline (via `SAVE=True` pattern where available).

### 6. Update `usdm4_protocol` — M11 docx-side plan

The next big chunk per `usdm4_protocol/docs/m11_validation_plan.md`:

- **RuleM11S###** (structural): docx template conformance
- **RuleM11T###** (technical): typography, cross-refs, numbering
- **RuleM11C###** (content): semantic checks against M11 sections

Still code-gen from `m11_specification` at authoring time, no runtime
dependency. Needs its own planning pass — scope, rule source, which
M11 version, how to integrate into `step_0_m11` in the udp_prism pipeline.

Don't start this inside the usdm4 engine work — keep it as a follow-on
repository.

## Session-to-session reminders

- **Never implement without explicit authorization.** Planning is not
  authorization. Wait for a clear "do it" / "go ahead" before writing
  to the repo. Questions about clusters, scope, etc. are still planning.
- **Severity from the YAML, not memory.** RuleTemplate.ERROR is the
  muscle-memory default but many rules are WARNING. The metadata test
  catches mismatches but costs a regen cycle.
- **xlsx attribute name ≠ JSON field name.** `members`/`children`/`dose`
  in the YAML usually become `memberIds`/`childIds`/`doseId` or
  embedded dicts in USDM JSON. Always verify via `dataStructure.yml`
  or by grepping a fixture before coding.
- **`# MANUAL: do not regenerate` sentinel on every hand-authored
  rule.** Without it, stage-2 will overwrite the work.
- **CT cache drift** breaks tests that pin specific dates. If you see
  `"2025-09-26" != "2026-03-27"`-type diffs, that's cache refresh, not
  code regression.

## Baseline reference

Last known good test summary from the session end:

```
tests/usdm4/test_package.py
  14 passed
  2 failed (DDF00166 "Protocol" decode, DDF00217 "Decode" placeholder — pre-existing)

29 new hand-authored rule tests
  29 passed (metadata)
  58 skipped (positive/negative fixture TODOs)

Full rule library on PYTHONPATH=src python -m pytest
  (not run end-to-end this session; presumed clean modulo the above)
```

Run the full suite before the next commit to confirm no drift.
