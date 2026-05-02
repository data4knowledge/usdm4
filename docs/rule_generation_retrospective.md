# Rule generation retrospective

Written 2026-05-02, after the V4 rule library reached 100% coverage and the
two-stage generator infrastructure was retired. This document records the
process we followed to populate `src/usdm4/rules/library/`, the artefacts
that were used in the process, and the rationale for removing the
authoring scaffolding once it had served its purpose. It is the as-built
counterpart to `lessons_learned.md` (which records the non-obvious
decisions made along the way).

## What we set out to build

The V4 USDM specification carries 210 conformance rules in
`DDF-RA/Deliverables/RULES/USDM_CORE_Rules.xlsx` (the rows where
`Version 4.0 = Y`). The existing CDISC CORE engine
(`cdisc_rules_engine`) executes those rules in JSONata against
serialised USDM JSON. We wanted a parallel, Python-native engine living
inside `usdm4` — one that we own end-to-end, can reason about line by
line, can extend with our own protocol-level rules later, and that does
not depend on `usdm3` or any other rules package at runtime. CORE was
not being replaced; the two engines are siblings, and `validate/run.sh`
runs them together so we can diff their results.

The architectural shape was simple by the time the dust settled. One
`RuleTemplate` subclass per file under `src/usdm4/rules/library/`. The
engine at `src/usdm4/rules/engine.py` walks that directory at startup,
imports every `rule_*.py`, and registers every concrete subclass. No
manifest, no registry, no shared state. Adding a rule means dropping a
file. Removing one means deleting it.

## Why a generator at all

210 rules is a lot of code to hand-author. Worse, much of it is
shaped repetition: "every X must have a non-empty Y", "values of A are
drawn from CT codelist C-NNNNN", "all instances of class K are unique
within parent P". Hand-writing 210 such bodies invites copy-paste
divergence and burns weeks of attention on rules that are mostly
boilerplate.

Two complementary structured sources were available. The xlsx
catalogue gave us the canonical rule list, severity, applies-to class,
attribute names, and rule text. The CORE rules cache
(`<cache>/rules/usdm/4-0.json`, populated by `tools/prepare_core_cache.py`
which still exists) gave us a structured `conditions` tree for the 207
rules CORE implements — a small operator vocabulary
(`equal_to`, `non_empty`, `is_contained_by`, `is_not_unique_set`,
`invalid_duration`, etc.) that maps cleanly to a few lines of Python
each. Combining the two should produce most rules mechanically.

But mechanical generation has a failure mode: it produces wrong code
silently and confidently. Reviewing 210 generated Python bodies for
correctness was prohibitive. So we inserted an **intermediate YAML
between the sources and the generated Python**, with a human review
step in the middle. The YAML concentrated what mattered for review
(class, attribute, scope, predicate, message) and hid the boilerplate
of how each predicate becomes Python.

## The two-stage pipeline

```
DDF-RA/USDM_CORE_Rules.xlsx     ┐
<cache>/rules/usdm/4-0.json     ├──→ stage 1 ──→ intermediate YAML (per rule)
                                ┘                       │
                                                        ▼
                                                [human review]
                                                        │
                                                        ▼
                                                stage 2 ──→ rule_ddf#####.py
                                                         ──→ test_rule_ddf#####.py
```

Stage 1 (`tools/generate_rule_intermediate.py`) read the xlsx + CORE
JSON, classified each rule by what it could infer, and wrote one
`rule_ddf#####.yaml` per V4-applicable rule into
`src/usdm4/rules/intermediate/`. The classifications were confidence
bands rather than precise predicates: `HAS_IMPLEMENTATION` for rules
where existing code in `library/` was the ground truth (stage 1
introspected the Python and copied metadata out of it),
`HIGH_*` for rules whose CORE conditions matched a known structured
shape (CT-membership, required-attribute, unique-within-scope, etc.),
`MED_TEXT` when the CORE side was a JSONata string but the rule text
matched a known idiom, `LOW_CUSTOM` when nothing matched, and `STUB`
for rules absent from CORE altogether.

Stage 2 (`tools/generate_rule_python.py`) consumed the YAML and emitted
Python. Dispatch was on `classification` first and `predicate` second,
calling one of a handful of body renderers
(`render_body_ct_member`, `render_body_required_attribute`,
`render_body_unique`, `render_body_idref`,
`render_body_mutex_listed_attrs`, plus narrower helpers for
biconditional and implication patterns added later). For
`HAS_IMPLEMENTATION` rules stage 2 emitted only the test stub and left
the rule file alone. For `LOW_CUSTOM` and uncovered cases it emitted a
stub that raised `NotImplementedError` with the original CORE JSONata
preserved as a reference comment, plus a lock-in test that asserted
the stub raised — so anyone hand-authoring a rule had to add a real
test in the same commit or watch CI go red.

A narrow JSONata-to-Python translator (`tools/translate_jsonata.py`)
recognised five recurring shapes
(cross-instance unique, intra-attribute unique, subset within scope,
incompatible codes, at-least-one-of) and converted those CORE
conditions directly into Python. It covered 8 of the 92 JSONata-only
rules — the long tail had bespoke shapes that didn't generalise.

## Data sources, in order of authority

The xlsx catalogue was canonical for *what rules exist, what they say,
and what severity they have*. The CORE JSON was canonical for
*structured condition shapes when they're available*. For codelist
bindings the precedence order turned out to be
**`USDM_CT.xlsx` (the `Codelist URL` column)**, then the C-code
embedded in the rule text itself, with `dataStructure.yml` used purely
as a "does this (class, attribute) pair exist in the model?" cross-check —
never as a codelist source, because the NCI C-code in
`dataStructure.yml` is the *attribute's* concept code, not the codelist
its values are drawn from. Treating the latter as the former cost time
in early generator runs.

For runtime `validate()` bodies, the authoritative API was the
`DataStore` primitives: `instances_by_klass`, `instance_by_id`,
`parent_by_klass`, `path_by_id`. Generated and hand-authored code both
sit on those primitives, so the styles read alike. `lessons_learned.md`
section 11 catalogues the patterns that recurred.

## The `# MANUAL: do not regenerate` sentinel

Stage 2 had to coexist with hand-authored rules. The mechanism we
landed on was a sentinel comment on the first line of the Python file:
`# MANUAL: do not regenerate`. Stage 2 skipped any file containing
that string. Hand-authored rules carried the sentinel; regenerated
rules didn't. By the time the library reached 100% coverage, 119 of
the 210 rule files carried the sentinel — the long tail of
`LOW_CUSTOM` and bespoke conditional logic that no generator could
have produced.

## Outcome

210 of 210 V4 rules implemented (207 with real `validate()` bodies
plus 3 deliberate no-op delegates to DDF00082, which runs full
JSON-Schema validation against `usdm_v4-0-0.json` and subsumes the
class-relationships / required-properties / cardinalities checks that
DDF00081, DDF00125, and DDF00126 would otherwise duplicate). The
batch-by-batch progression sits in section 10 of `lessons_learned.md`.
Roughly 90 rules came out of the generator with little or no
hand-finishing; the rest were hand-authored in clusters where pattern
discovery made each new rule cheaper than the last.

The generator's honest ceiling was around 60% — the
`conditional` and `LOW_CUSTOM` long tail required per-rule domain
judgement that no template could absorb cheaply. Knowing that ceiling
exists matters: chasing higher auto-generation percentages produces
quietly-wrong rules.

## Why the scaffolding has now been removed

Three things were true by the time this document was written. First,
the runtime engine never read the YAMLs — it only loads `library/*.py`.
The intermediate directory was authoring scaffolding, not a runtime
artefact, and `setup.py`'s `package_data` already excluded it from the
pip wheel. Second, 119 of the 205 YAMLs no longer described their rule
correctly because the corresponding Python had been hand-rewritten;
DDF00249 was the most recent example we caught — its YAML still
described an attribute called `criterionItem` that doesn't exist on
the API model, despite the Python having been rewritten months earlier
to use the real `criterionItemId` field. Reading the stale YAML cost
real investigation time. Third, regeneration is reproducible: stage 1
takes the xlsx and CORE JSON cache as its only inputs, and both are
fetched on demand by `tools/prepare_core_cache.py`. If we ever needed
the YAMLs again — for example to bootstrap a USDM 4.1 rule library —
we'd regenerate them from scratch against the new sources, not lift
the snapshot we have today.

The retired artefacts are therefore: the entire
`src/usdm4/rules/intermediate/` directory (205 YAMLs) and the three
generator scripts under `tools/` —
`generate_rule_intermediate.py`, `generate_rule_python.py`, and
`translate_jsonata.py`. The CORE cache populator
(`tools/prepare_core_cache.py`) stays because `USDM4.validate_core` still
needs it. The `# MANUAL: do not regenerate` sentinels stay on the rule
files because they remain useful as a "this rule was hand-authored,
don't reach for templated edits without thinking" signal even though no
generator now reads them.

## Adding rules going forward

Without the generator, the workflow for adding or modifying a rule
collapses to authoring Python directly:

1. Decide whether the rule belongs in the V4 catalogue (xlsx with
   `Version 4.0 = Y`) or is a usdm4-specific extension. Use the next
   free DDF id from the catalogue, or assign a new identifier scheme
   for non-catalogue rules.
2. Create `src/usdm4/rules/library/rule_<id>.py` with a single
   `RuleTemplate` subclass. Set the rule id, severity, and rule text
   in `__init__`. Implement `validate(self, config)` against the
   `DataStore` primitives. The patterns to copy from already exist —
   neighbouring rule files for the same predicate shape are the
   shortest path.
3. Create `tests/usdm4/rules/test_rule_<id>.py`. Mock `DataStore` with
   `MagicMock` and the four core methods (`instances_by_klass`,
   `path_by_id`, `instance_by_id`, `parent_by_klass`) — the
   `feedback_usdm4_rule_test_pattern` memory describes the shape; many
   existing test files are templates.
4. Auto-discovery picks the rule up at the next engine instantiation.
   Run the test suite locally; the engine's `_load_rules` will register
   the new class and the validate path will exercise it on the next
   run of `validate/d4k.py` or `USDM4.validate(...)`.

## Where to read more

- `docs/lessons_learned.md` — the non-obvious calls made along the way,
  including the §10 batch progression table and §11 DataStore traversal
  patterns. Still current.
- `docs/cre_issues.md` — the CDISC Rules Engine bug catalogue and
  workarounds. Includes the "Defensibly d4k-stricter" appendix listing
  divergences that aren't bugs (DDF00082 schema scope, the
  CT-membership family).
- `docs/next_steps.md` — open work items, including open d4k design
  decisions where the DDF text is ambiguous (DDF00164/165 `"0"`
  treatment, DDF00187 XHTML wrapping).
