# USDM4 validation engine — next steps

Written 2026-04-18, refreshed after the amendment / masking / reference
batch committed. Read alongside `docs/lessons_learned.md` which captures
the *how*. This file captures the *what next*.

## Current state

**Rule coverage:** 163 of 210 V4 DDF rules have real `validate()` bodies
(~78 %). 47 stubs remain.

**Stub detection:** `grep -l NotImplementedError src/usdm4/rules/library/rule_ddf*.py`.
The YAML `classification` field is stale for rules where the biconditional /
implication predicate was hand-filled — don't trust it as a stub signal
(§13 of lessons_learned.md).

**Committed so far** (41 hand-authored rules this session): clusters A/B/C
self-reference/quantity-unit/mixed (13), E distinct-within-scope (4),
F mutex scope (4), G orphan/reverse-FK (3), one-offs (5), amendment/reason
(3), XHTML well-formedness (2), masking/blinding (2), scoped uniqueness (2),
context/reference (3).

**`test_package.py` baseline** — same 2 pre-existing failures:

- `test_validate` (blocked by pre-existing DDF00166 fixture issue)
- `test_example_2` (blocked by pre-existing DDF00217 placeholder issue)

**Legitimate fixture findings** from new rules that fire but are masked
by the pre-existing blockers (see §14 of lessons_learned.md):

- **DDF00187** / **DDF00247** — `example_2.json` has malformed XHTML in
  several NCItems and one EligibilityCriterionItem (bare `""=""`
  attribute on a `<table>`, unescaped ampersands, etc.).
- **DDF00188** — fixture has `plannedSex: [{code: C49636 "Both"}]` which
  the rule rejects (must be Male + Female separate entries).
- **DDF00189** — fixture has a StudyRole with empty `appliesToIds`.
- **DDF00236** — fixture has a BC whose synonym equals its label
  (case-insensitive).

None of these change pass/fail because DDF00166 / DDF00217 are already
blocking.

## Immediate next steps — ordered

### 1. Unblock `test_validate` / `test_example_2`

The two pre-existing test_package.py failures have been deferred through
multiple sessions. Fixing them converts the package tests into a live
regression detector — today any new rule firing hides behind these
existing failures (and the list above will grow).

**DDF00166** (`test_validate.json`): fixture has literal string
`"Protocol"` in a decode field where CORE expects a code from a
specific codelist.

**DDF00217** (`test_example_2.json`): placeholder strings `"None"` and
`"Decode"` appear in Code fields.

Both are probably fixture regenerations, not code changes. Read the
offending paths in the test output, edit the fixture JSON or regenerate
it via the assembler.

### 2. Keep hand-authoring — tractable candidates remain

After 41 rules this session, the hit rate per pattern is degrading and
effort per rule creeping up. Still tractable with the toolkit now in
place:

**Still-tractable from the "harder" list** (re-evaluated with the new
helpers):

- **DDF00006** — Timing windows: if any of {windowLabel, windowLower,
  windowUpper} is set, all must be. All-or-nothing on 3 attrs.
- **DDF00007** — Timing type "Fixed Reference" (code lookup needed) →
  exactly one `relativeToScheduledInstance`. Singleton cardinality.
- **DDF00010** — Names of sibling instances of the same parent class
  must be unique. Group children via `data._parent`, by
  (parent_id, child_class, name).
- **DDF00160** — Activity with children must not refer to a timeline /
  procedure / BC / BC-category / BC-surrogate. Mutex between childIds
  being non-empty and 5 FK attrs.
- **DDF00162** — NarrativeContentItem references must be in the correct
  `<usdm:ref>` format. Regex check, reuses the helpers from
  DDF00124/244.

**Other easy-ish stubs** (not on the "harder" list but still left):

- **DDF00017** — SubjectEnrollment.quantity is number or % (unit empty
  or %).
- **DDF00026** — ScheduledActivityInstance must not name its own
  timeline via `timelineId`. Self-reference pattern.
- **DDF00035** — One-to-one relationship between `code` and `decode`
  within the same (codeSystem, codeSystemVersion). Group-by with dict.
- **DDF00076** — Transitive BC reference exclusion across activity /
  BC category. Set-based check.
- **DDF00101** — Interventional study must reference ≥1 intervention
  from a procedure. Multi-class walk.
- **DDF00107** — SAI sub-timeline must be in same study design. Parent
  walk + comparison.
- **DDF00127** — Encounter scheduled at timing within same study
  design. Similar.
- **DDF00153** — Main timeline must have `plannedDuration`. Required
  attribute when `mainTimeline=true`. Twin of DDF00080.
- **DDF00163** — NarrativeContent → `childIds` and/or `contentItemId`.
  At-least-one.
- **DDF00203** — Sponsor StudyRole must apply to a StudyVersion.
  Subset check with a role-type CT code lookup.
- **DDF00205** — already done (this session)
- **DDF00206** — AdministrableProduct sourcing check when only embedded.
  Multi-class FK traversal.
- **DDF00212** — ProductOrganizationRole `appliesTo` constraint. Might
  need reading rule text carefully.
- **DDF00213** — Interventional single-group → one intervention. Needs
  intervention-model CT code lookup.
- **DDF00232** — Observational study phase = "NOT APPLICABLE". Simple
  CT code check.
- **DDF00255** — already done (this session)
- **DDF00258** — already done (this session)

**Estimated aggregate:** ~15 more rules within reach without crossing
into schema-conformance or cross-class-ordering territory. Would push
coverage past 85 %.

### 3. Harder — skip unless specifically needed

- **DDF00081** — USDM schema conformance. Either no-op (schema enforced
  elsewhere) or a massive refactor. Skip.
- **DDF00087 / DDF00088** — Encounter / epoch prev-next ordering must
  match SAI ordering. Cross-class graph alignment.
- **DDF00091** — Condition context cardinality across several classes.
  Needs careful multi-class FK traversal with conditional logic.
- **DDF00161** — Activity ordering: parents must precede children in
  prev/next chain. Topological-ordering-ish.
- **DDF00115 / DDF00191-related** — CT-scoped cardinality and title
  lookups. Need CT config extensions.

### 4. Write real fixtures for a few of the 41 rules

All 41 have `@pytest.mark.skip` on positive/negative fixture tests. A
minimal JSON blob for 4-5 of the structurally-interesting rules would
catch future regressions in rule *behavior* rather than just metadata.
~15 min per fixture pair. Good candidates: DDF00037 family, DDF00189,
DDF00196 (dict-of-sets logic), DDF00253 (one-step chain), DDF00124
(regex-based ref validation).

### 5. M11 docx-side plan (usdm4_protocol)

Per `usdm4_protocol/docs/m11_validation_plan.md`: `RuleM11S###`
(structural), `RuleM11T###` (technical), `RuleM11C###` (content).
Generated from `m11_specification` at authoring time, no runtime
dependency. Needs its own planning pass. Don't start inside the usdm4
engine work.

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
- **CT cache drift** breaks tests that pin specific dates. Not a code
  regression.

## Baseline reference

Last known good test summary:

```
tests/usdm4/test_package.py
  14 passed
  2 failed (DDF00166 / DDF00217 — pre-existing)

41 hand-authored rule tests (this session)
  41 passed (metadata)
  82 skipped (positive/negative fixture TODOs)
```
