# USDM4 validation engine — next steps

Written 2026-04-19, refreshed after Stage 2 (the CT / prev-next /
ref-format batch). Read alongside `docs/lessons_learned.md` which
captures the *how*. This file captures the *what next*.

## Current state

**Rule coverage:** 206 of 210 V4 DDF rules are either implemented or
delegated (~98 %). 4 V4 rules remain as genuine stubs, all in the
Stage 3 interactive bucket.

Three rules (DDF00081, 00125, 00126) are deliberate no-ops that
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

Plain `grep -l NotImplementedError rule_ddf*.py` returns more hits
(~60) because some non-V4 DDF IDs also have stub files.

The YAML `classification` field is stale for rules where the
biconditional / implication predicate was hand-filled — don't trust
it as a stub signal (§13 of lessons_learned.md).

**Committed so far this session** (83 hand-authored + 3 no-op
delegates = 86 rule files touched across multiple commits):
see the §10 progression table in `lessons_learned.md` for the full
cluster breakdown.

**Uncommitted changes** (if any): check `git status`. Latest work
added the 6 Stage-2 rules + 1 ct_config.yaml addition (C66781) +
doc refresh.

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

Stage 2 added no new fixture findings (0 hits across DDF00023, 27,
137, 210, 237, 246). DDF00237 is in a "skip gracefully" state until
the CT cache is refreshed to pull C66781 — see §19 of
`lessons_learned.md`.

## Remaining 4 V4 stubs — all Stage 3 (interactive)

These genuinely benefit from per-rule discussion. Answers depend on
Dave's domain judgment more than Python skill — "what does
'consistent with SAI ordering' actually mean in USDM v4?", "is
parent-before-child a topological requirement or can it be violated
for amendments?" — and decisions may surface spec ambiguity rather
than implementation gaps.

### Ordering-graph rules (3)

- **DDF00087** — Encounter prev-next ordering must match the order
  of corresponding ScheduledActivityInstances that reference those
  encounters via `encounterId`. Need to define "corresponding
  SAI" precisely, then decide: strict positional match? Or a
  topological property that allows multiple SAIs per encounter?
- **DDF00088** — same shape for StudyEpoch prev-next vs. SAI
  ordering via `epochId`.
- **DDF00161** — Activity prev-next ordering must include parents
  preceding children — a topological ordering of the childIds tree
  relative to the prev-next chain.

### Multi-class cardinality (1)

- **DDF00091** — "When a condition applies to a procedure, activity,
  biomedical concept, biomedical concept category, or biomedical
  concept surrogate then ..." (rule text is cut off in the YAML).
  Needs the full rule text from USDM_CORE_Rules.xlsx, then a
  conditional-cardinality check per target class.

### Delegated to DDF00082 (already covered; no further work)

- **DDF00081 / DDF00125 / DDF00126** — Class relationships /
  attribute presence / cardinalities per USDM API spec. Schema
  validation runs in DDF00082.

## Path to 100 %

**Stage 3 (4 rules, interactive):** per-rule discussion. Could land
all 4 with targeted clarification, or land some and explicitly mark
the rest as "spec ambiguous / out of scope". Realistic end state:
**210/210** or **208/210 with 2 marked out-of-scope**.

**Stage 4 (real-file regression):** once coverage is ~100 %, run the
full library against the 21 protocols in udp_prism and compare
findings against expected baselines. First-pass is likely to surface
(a) fixture drift issues (plannedSex "Both" encoding, etc.), (b) real
data issues in some protocols, and (c) a handful of rule-interpretation
bugs that only show up on real data. Each category needs a separate
reconciliation pass.

Ahead of Stage 4 it would be high-leverage to finally **unblock
DDF00166 / DDF00217**: converts `test_package.py` into a live
regression detector. The latent-findings list is at 13 items now —
each is a legitimate rule firing that's hiding behind the pre-existing
failures.

## Immediate next steps — ordered

1. **Commit the Stage 2 batch + ct_config.yaml update + doc refresh**
   (clean checkpoint).
2. **Unblock DDF00166 / DDF00217** — unmasks the latent findings and
   makes further work self-verifying.
3. **CT cache refresh** — activates DDF00237 once the Age Unit codelist
   (C66781) is pulled from the CDISC API. Requires network access.
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
  True, point at the canonical check in a module-level comment. See
  §10 (DDF00082 delegation).
- **Trust ct_config bindings over the YAML's `class` field.** Stage-1
  class extraction sometimes gets the class wrong when CORE walks
  through a parent — ct_config has the authoritative binding. See
  §19.4 of lessons_learned.md and DDF00210 for an example.
- **When a CT codelist is registered but cache is stale, skip
  gracefully** rather than raising CTException. See §19.2 of
  lessons_learned.md and DDF00237 for the pattern.
- **CT cache drift** breaks tests that pin specific dates. Not a code
  regression.

## Baseline reference

Last known good test summary:

```
tests/usdm4/test_package.py
  14 passed
  2 failed (DDF00166 / DDF00217 — pre-existing)

86 rule tests touched this session (83 hand-authored + 3 delegated no-ops)
  86 passed (metadata + delegated behaviour)
  166 skipped (positive/negative fixture TODOs on hand-authored rules)
```
