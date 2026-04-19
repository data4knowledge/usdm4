# USDM4 validation engine — next steps

Written 2026-04-19, refreshed after Stage 1 (the tractable-stubs push)
and the DDF00082-delegation pass. Read alongside
`docs/lessons_learned.md` which captures the *how*. This file captures
the *what next*.

## Current state

**Rule coverage:** 200 of 210 V4 DDF rules are either implemented
or delegated (~95 %). 10 V4 rules remain as genuine stubs
(6 moderately-harder + 4 genuinely-hard).

Note: three rules (DDF00081, 00125, 00126) are deliberate no-ops that
delegate to DDF00082's JSON-schema validation. Counting them as
"covered" (rather than "stubbed") reflects that the check runs
end-to-end; the per-rule file simply doesn't duplicate it. See §10
of `lessons_learned.md` and the rule file module docstrings.

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
hits (~60) because some non-V4 DDF IDs also have stub files.

The YAML `classification` field is stale for rules where the
biconditional / implication predicate was hand-filled — don't trust
it as a stub signal (§13 of lessons_learned.md).

**Committed so far this session** (77 hand-authored + 3 no-op
delegates = 80 rule files touched across multiple commits): see the
§10 progression table in `lessons_learned.md` for the full
cluster breakdown.

**Uncommitted changes** (if any): check `git status`. Latest work
added the 15 Stage-1 rules, 3 delegated no-ops (DDF00081/125/126),
and the doc refresh.

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

None change pass/fail because DDF00166 / DDF00217 are blocking.

## Remaining 10 V4 stubs — triage

### Moderately-harder (6) — possible but heavier lift

- **DDF00023** — "previous id value must match the next id value" —
  ordering consistency across paired attrs. For each pair (A, B)
  where A.nextId = B.id, require B.previousId = A.id (and mirror).
  Group across scope classes (Activity, EligibilityCriterion,
  Encounter, etc. — see YAML entity list).
- **DDF00027** — Same instance not referenced more than once as
  previous or next. Group-by across the same scope classes;
  `Counter(prev_ids + next_ids)` and flag any count > 1.
- **DDF00137** — ParameterMap reference format check. Sister of
  DDF00162 but scoped to ParameterMap.reference. Reuse
  `_find_malformed` helpers from DDF00162 / DDF00124 / DDF00244.
- **DDF00210** — Product designation CT codelist. Need a
  `ct_config.yaml` entry binding `(AdministrableProduct,
  productDesignation)` to the right codelist (probably C207xxx —
  verify via USDM_CT.xlsx).
- **DDF00237** — Planned age unit CT codelist (C66781 Age Unit).
  Same shape as DDF00210 — ct_config binding for
  `(Quantity, unit)` nested under plannedAge, or a scoped override.
- **DDF00246** — Parameter names in text must appear in data
  dictionary parameter maps. Cross-class regex+lookup — combine
  the DDF00162 regex with a StudyVersion-scoped ParameterMap.tag
  lookup.

### Delegated to DDF00082 (already covered; no-ops on purpose)

- **DDF00081 / DDF00125 / DDF00126** — Class relationships / attribute
  presence / cardinalities per the USDM API spec. DDF00082 runs full
  JSON-schema validation against `src/usdm4/rules/library/schema/
  usdm_v4-0-0.json`, which covers all three. The rule files are
  `validate()`-no-ops (return True) with a module-level comment
  pointing at DDF00082. No further work needed.

### Genuinely hard (4 rules — likely skip or punt to interactive
prompt/response)

- **DDF00087 / DDF00088 / DDF00161** — prev-next ordering must match
  SAI ordering / activity parent-child ordering. Cross-class graph
  alignment. Need a topological walk.
- **DDF00091** — Condition `appliesTo` multi-class cardinality with
  conditional logic based on target class.

## Path to 100 %

**Stage 2 (6 rules, 1-2 hours):** the moderately-harder set above.
Adds CT config work for DDF00210 and DDF00237 (two new codelist
bindings). Brings coverage to **206/210 ≈ 98 %**.

**Stage 3 (4 rules, interactive prompt/response):** the genuinely-hard
set benefits from per-rule discussion. Answers will depend on Dave's
domain judgment — "what does 'consistent with SAI ordering' actually
mean in USDM v4?" "Is parent-before-child a topological requirement
or can it be violated for amendments?" — more than Python skill.
Could land all 4 with targeted clarification, or land some and
explicitly mark the rest as "spec ambiguous / out of scope".

**Stage 4 (real-file regression):** once coverage is ~100 %, run the
full library against the 21 protocols in udp_prism and compare
findings against expected baselines. First-pass is likely to surface
(a) fixture drift issues (plannedSex "Both" encoding, etc.), (b) real
data issues in some protocols, and (c) a handful of rule-interpretation
bugs that only show up on real data. Each category needs a separate
reconciliation pass.

## Immediate next steps — ordered

1. **Commit the Stage 1 batch + delegation pass + doc refresh** (clean
   checkpoint).
2. **Unblock DDF00166 / DDF00217 fixture failures** so `test_package.py`
   becomes a live regression detector before adding more rules. The
   "latent findings" list has grown to 13 now — this is becoming
   high-leverage.
3. **Stage 2 hand-authoring + CT config** — 6 moderately-harder rules,
   including two new CT codelist registrations.
4. **Stage 3 interactive** — talk through the 4 hard rules, decide
   scope per rule.
5. **Stage 4 real-file regression** — run against udp_prism protocols.

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
  rather than re-implementing. Keep the rule file registered, return
  True, point at the canonical check in a module-level comment.
  See §10 (DDF00082 delegation) and DDF00081/00125/00126 rule files
  for the pattern.
- **CT cache drift** breaks tests that pin specific dates. Not a code
  regression.

## Baseline reference

Last known good test summary:

```
tests/usdm4/test_package.py
  14 passed
  2 failed (DDF00166 / DDF00217 — pre-existing)

80 rule tests touched this session (77 hand-authored + 3 delegated no-ops)
  80 passed (metadata + delegated behaviour)
  154 skipped (positive/negative fixture TODOs on hand-authored rules)
```
