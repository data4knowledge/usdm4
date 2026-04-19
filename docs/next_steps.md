# USDM4 validation engine — next steps

Written 2026-04-19, refreshed after the 88 % push. Read alongside
`docs/lessons_learned.md` which captures the *how*. This file captures
the *what next*.

## Current state

**Rule coverage:** 182 of 210 V4 DDF rules have real `validate()`
bodies (~87 %). 28 V4 stubs remain.

**Stub detection (V4-accurate):**

```bash
for f in src/usdm4/rules/intermediate/rule_ddf*.yaml; do
    rid=$(basename "$f" .yaml)
    py="src/usdm4/rules/library/${rid}.py"
    [ -f "$py" ] && grep -q NotImplementedError "$py" && echo "$rid"
done
```

Cross-references the intermediate YAMLs (which correspond to V4 rules
only). A plain `grep -l NotImplementedError rule_ddf*.py` returns more
hits (~75) because some non-V4 DDF IDs also have stub files.

The YAML `classification` field is stale for rules where the
biconditional / implication predicate was hand-filled — don't trust
it as a stub signal (§13 of lessons_learned.md).

**Committed so far** (62 hand-authored rules this session, across
multiple commits): see the §10 progression table in
`lessons_learned.md` for the full cluster breakdown.

**Uncommitted changes** (if any): check `git status` before the next
commit. Today's batch added 16 rules + 16 test files + the doc
refresh.

**`test_package.py` baseline** — same 2 pre-existing failures:

- `test_validate` (blocked by pre-existing DDF00166 fixture issue)
- `test_example_2` (blocked by pre-existing DDF00217 placeholder issue)

**Legitimate fixture findings** from new rules that fire but are masked
by the pre-existing blockers (see §14 of lessons_learned.md):

- **DDF00006** — one Timing has a partially defined window.
- **DDF00010** — two SubjectEnrollments share a name across amendments.
  Matches CORE's model-wide grouping; may revisit as per-parent.
- **DDF00035** — Code with decode "No Concept Code" used with code
  `AEHLGT` in the CDISC 2024-09-27 codelist — broken 1:1 mapping.
- **DDF00075** — an Activity with no leaf references.
- **DDF00101** — Interventional StudyDesign with no Procedure linked
  to a StudyIntervention.
- **DDF00153** — Main ScheduleTimeline without a `plannedDuration`.
- **DDF00187** / **DDF00247** — malformed XHTML in NCItem /
  EligibilityCriterionItem text.
- **DDF00188** — `plannedSex: [{code: C49636 "Both"}]` (single "Both"
  encoding rejected; must be separate Male + Female entries).
- **DDF00189** — StudyRole with empty `appliesToIds`.
- **DDF00236** — BC whose synonym equals its label (case-insensitive).

None change pass/fail because DDF00166 / DDF00217 are blocking.

## Remaining 28 V4 stubs — triage

### Tractable (~15 rules, same patterns as today's batch)

**"Must reference X in same StudyDesign" cluster (7 rules)** — all
direct reuse of the DDF00107/00127 parent_by_klass pattern:

- **DDF00019** — SAI / ScheduledDecisionInstance must not refer to
  self as `defaultConditionId`. Self-reference (DDF00021/22 pattern).
- **DDF00024** — StudyEpoch `previousId` / `nextId` must be in same
  study design.
- **DDF00028** — Activity `previousId` / `nextId` same study design.
- **DDF00029** — Encounter `previousId` / `nextId` same study design.
- **DDF00046** — Timing `relativeFromScheduledInstanceId` /
  `relativeToScheduledInstanceId` same study design.
- **DDF00047** — StudyCell `elementIds` same study design.
- **DDF00152** — Activity `timelineId` same study design.

**Unique-within-scope dateValues (2 rules)**

- **DDF00093** — StudyVersion.dateValues unique by (type,
  geographicScope).
- **DDF00181** — StudyDefinitionDocumentVersion.dateValues same shape.

**Scope / mutex (2 rules)**

- **DDF00073** — Only one version of any code system is expected to
  be used within a study version. Group Code by codeSystem, check
  distinct codeSystemVersion count.
- **DDF00198** — StudyDefinitionDocumentVersion must be referenced
  by either a StudyVersion or a StudyDesign.

**Biconditional-shaped / at-least-one (2 rules)**

- **DDF00185** — If a dose is specified then a corresponding
  administrable product must also be specified. Sister of DDF00177.
- **DDF00231** — Biospecimen retention: if type retained, indicate
  whether consented. Conditional check.

**Grid / multi-attr (2 rules)**

- **DDF00243** — Each StudyArm has one StudyCell per StudyEpoch.
  Two-dimensional coverage check.
- **DDF00245** — Section numbers unique within a document version.
  Uniqueness within parent.

### Moderately harder (~5 rules — possible but heavier lift)

- **DDF00023** — "previous id value must match the next id value" —
  ordering consistency across paired attrs. Might be simpler than it
  reads.
- **DDF00027** — Same instance not referenced >1 as previous or next.
  Group-by across scope classes.
- **DDF00137** — ParameterMap reference format check. Regex /
  state-machine.
- **DDF00210** — Product designation CT codelist
  (C207xxx — check xlsx). Requires a ct_config.yaml entry + test
  fixtures for all applicable codes.
- **DDF00237** — Planned age unit CT codelist (C66781 Age Unit).
  Same shape as DDF00210.
- **DDF00246** — Parameter names in text must appear in data dictionary
  parameter maps. Cross-class reference check with regex.

### Genuinely hard (8 rules — likely skip or punt to interactive
prompt/response)

- **DDF00081** — Class relationships must conform with USDM schema.
  Probably a no-op (enforced by Pydantic loaders) or a massive refactor.
- **DDF00087 / DDF00088 / DDF00161** — prev-next ordering must match
  SAI ordering / activity parent-child ordering. Cross-class graph
  alignment. Need a topological walk.
- **DDF00091** — Condition `appliesTo` multi-class cardinality with
  conditional logic based on target class.
- **DDF00125 / DDF00126** — Attributes/cardinalities must conform to
  USDM schema. Same as DDF00081.

## Path to near-100 %

**Stage 1 (~15 more rules, 1-2 hours):** pick off the tractable cluster
above. Would bring coverage to ~95 % (197/210).

**Stage 2 (~5 more rules, 2-3 hours):** tackle the moderately-harder
set. Adds CT config work for DDF00210 and DDF00237. Would bring
coverage to ~98 % (202/210).

**Stage 3 (8 rules, interactive prompt/response):** the hard set
genuinely benefits from per-rule discussion — "what does 'conform to
the USDM schema' actually mean in our context?" "Is the ordering
check on absolute or topological order?" Answers will depend on Dave's
domain judgment more than Python skill. Could land all 8 with
targeted clarification, or land some and explicitly mark the rest
as "out of scope" / "spec ambiguous".

**Stage 4 (real-file testing):** once coverage is ~100 %, run the
full library against the 21 protocols in udp_prism and compare
findings against expected baselines. First-pass is likely to surface
(a) fixture drift issues (plannedSex "Both" encoding, etc.), (b) real
data issues in some protocols, and (c) a handful of rule-interpretation
bugs that only show up on real data. Each category needs a separate
reconciliation pass.

## Immediate next steps — ordered

1. **Commit the latest 16 rules + doc refresh** (clean checkpoint).
2. **Unblock DDF00166 / DDF00217 fixture failures** so package tests
   become a live regression detector before adding more rules.
3. **Stage 1 hand-authoring** — the 15 tractable stubs above. Follow
   the existing pattern library; most should be 3-5 min each.
4. **Stage 2 hand-authoring + CT config** — 5 harder rules, including
   two new CT codelist registrations.
5. **Stage 3 interactive** — talk through the 8 hard rules, decide
   scope per rule.
6. **Stage 4 real-file regression** — run against udp_prism protocols.

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
- **CT cache drift** breaks tests that pin specific dates. Not a code
  regression.

## Baseline reference

Last known good test summary:

```
tests/usdm4/test_package.py
  14 passed
  2 failed (DDF00166 / DDF00217 — pre-existing)

62 hand-authored rule tests (this session)
  62 passed (metadata)
  124 skipped (positive/negative fixture TODOs)
```
