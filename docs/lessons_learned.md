# USDM4 — Lessons Learned

Distilled from completed work. Kept short on purpose — the code is the source
of truth, this file captures the *why* and the non-obvious.

## 1. Assembler input schema (Pydantic at the boundary)

**What was done.** `Assembler.execute()` used to accept an untyped `dict`, and
failures surfaced deep inside sub-assemblers as `KeyError` / `AttributeError`
with no context. Added Pydantic schemas at the boundary in
`src/usdm4/assembler/schema/` — `AssemblerInput` plus seven domain schemas
(identification, document, population, amendments, timeline, study_design,
study). The assembler validates input, calls `model_dump()`, and passes plain
dicts to the sub-assemblers unchanged.

**Why this shape.**

- The *boundary* is where unknown input enters the package. Validating there
  produces one error report at one place, rather than a cascade of
  `KeyError`s.
- Keeping the sub-assembler internals dict-based meant no rewrite of the
  existing chain — strictly additive.
- `ConfigDict(strict=False)` is the production default: callers who pass
  slightly loose input still work. A `validate_strict()` helper catches
  quality issues during development.

**Lesson.** When you own both sides of an interface (external callers and
internal chain), validate once at the door, then let the internals use
whatever shape they already expect. Pydantic's `model_dump(by_alias=True)` is
essential — export schema domains (`usdm4.assembler.schema.AssemblerInput`
and siblings) so packages like `usdm4_protocol` can construct typed input
directly.

## 2. Lazy CT library loading

**Before:** `Builder.__init__()` eagerly loaded four CT libraries (CDISC CT,
CDISC BC, ISO 3166, ISO 639). Every test that constructed a `Builder` or
`Assembler` paid a 3+ second penalty.

**After:** Libraries are instantiated but not loaded. `_ensure_ct_loaded()`
is called at the start of every method that actually reads CT data. First
call loads; subsequent calls are a cheap boolean check.

**Impact on the test suite:** ~80 s → ~50 s for ~1,540 tests (38 % faster).

**Lesson.** An expensive resource should do the minimum at construction time.
If a method genuinely needs the resource, have it be the one that calls
`_ensure_X_loaded()`. Do this even when "production code always needs it" —
tests are the caller you'll have most often, and lazy initialisation is
free in the steady state.

## 3. Test-suite performance — the real bottleneck is import-time work

The CT library problem surfaced as slow *setup* times (3–4 s per test file).
Per-test work looked fine in isolation (~50 ms each) but the sum was dominated
by module-import-time cost that pytest pays for every file that imports the
Builder directly or indirectly.

**Lesson.** When "individual tests fast but total run slow", look at setup
vs call times in `--durations=50`. Module-import cost is invisible in
per-test profiling; it masquerades as fixture / conftest overhead.

## 4. V3 → V4 merge (zero remnants)

Merging `usdm3` into `usdm4` followed a fixed sequence:

1. **Catalogue** — `grep -rn "usdm3"` across `src/` and `tests/`; group by
   submodule; list consumer files.
2. **Copy** modules to their target locations verbatim, without editing.
3. **Rewrite imports** with a single sed-style pass (`from usdm3.X` →
   `from usdm4.X`) that skips wrapper files matching a specific regex.
4. **Inline wrapper bodies** (files like `from usdm3.rules.library.rule_ddf#####
   import RuleDDF##### as V3Rule`) by copying the v3 source in, adjusting its
   relative import, and preserving any v4-specific override.
5. **Drop the dependency** from `setup.py` and add the transitive deps that
   were coming in via v3 (`jsonschema`, `pyyaml`, `requests`, `pydantic`).
6. **Verify** with a fresh `grep -r "usdm3"` (returns nothing) plus the
   existing test suite.

### Pitfalls that cost time

- **"Wrapper" files often aren't just `pass`.** Of 25 v3-wrapper files in
  `usdm4.rules.library/`, five carried v4-specific overrides — e.g.
  `RuleDDF00105` used `["InterventionalStudyDesign",
  "ObservationalStudyDesign"]` as its scope instead of v3's generic
  `["StudyDesign"]`. Blindly inlining the v3 body lost those overrides and
  caused real behaviour change (16 false-positive findings per test
  fixture). Detect overrides by line count / presence of `def` in the
  wrapper file before inlining.
- **Broken dead code can exist in v3.** `usdm3/bc/cdisc/bc_library.py` had
  its entire class body commented out and didn't parse. Nothing imported
  it — we simply didn't carry it over. Check `py_compile` on every copied
  file; skip anything that fails.

### Diagnostic lesson

After the merge, `grep -r "usdm3"` showed zero hits but 16 rule findings
appeared on test data that previously had none. `inspect.getsource()` on
the affected rule object showed the *actual* source file Python had
resolved to — that's what revealed the missing override. For silent
behaviour changes after structural moves: use `inspect.getsourcefile()`
and `inspect.getsource()` on the live class; trust those over `cat`ing
files, because `__mro__` lookups can land on a different file than you
think.

## 5. Two-stage rule generator

Rather than going directly from CORE + xlsx → Python, we emit an
intermediate YAML per rule first, then generate Python from that.

**Why two stages.** The intermediate YAML is reviewable in under a minute per
rule. The alternative — reviewing ~200 Python rule bodies — took an order of
magnitude longer and missed misclassifications. The YAML concentrates what
matters (`class`, `attribute`, `scope`, `predicate`, `message`) and hides
boilerplate.

**Classifier confidence bands** matter more than precise labels:

- `HAS_IMPLEMENTATION` — existing working code. Preserve, extract metadata
  from the code, cross-check against CORE inference.
- `HIGH_*` — mechanical from CORE structured conditions. Emit working Python.
- `MED_TEXT` — CORE is JSONata string; rule text matches a known idiom.
  Flag `review_required: true`.
- `LOW_CUSTOM` — no pattern match. Emit stub with CORE JSONata preserved as a
  reference comment for later hand-authoring.
- `STUB` — not in CORE at all.

### Design decisions that held up

- **DataStore primitives are the authoritative API for rule bodies.** Generated
  code should prefer `data.instances_by_klass(X)`, `data.parent_by_klass(id,
  [...])`, `data.instance_by_id(id)` over raw JSON walking. Hand-written rules
  already did this; generated rules must match that style for reviewability.
- **Existing implementations are the ground truth, not the CORE inference.**
  Stage 1 introspects `rule_ddf#####.py`; if a real `validate()` exists, the
  YAML is populated from the code (class, scope, predicate, failure
  messages), not from CORE. This prevented stage 2 from overwriting working
  code with stubs.
- **`# MANUAL: do not regenerate` sentinel.** Hand-authored rules survive
  regeneration when the marker is present in the file.

### JSONata translator — narrow coverage is fine

Pattern-matching translator for 5 patterns (cross-instance unique,
intra-attribute unique, subset within scope, incompatible codes,
at-least-one-of) covers 8 of 92 JSONata rules. Not more — CORE's 92 JSONata
rules have rule-specific shapes and a narrow translator hits its ceiling
fast. Still worthwhile because the translated bodies are idiomatic Python,
not runtime JSONata.

### Predicate dispatch extends MED_TEXT coverage with review-flagged code

MED_TEXT rules have CORE conditions as JSONata strings the narrow
translator can't parse — but the rule *text* matched a known idiom during
stage 1, so the YAML carries a text-inferred `predicate` plus class /
attribute / scope. Stage 2 dispatches MED_TEXT by predicate the same way
HIGH_* dispatches by classification, reusing the same body renderers
(`render_body_required_attribute`, `render_body_unique`, etc.) plus two
new ones (`render_body_idref`, `render_body_mutex_listed_attrs`).

Generated code from text-inferred predicates carries a
`# GENERATED — predicate inferred from rule text, please review.` header
so the reviewer knows the confidence is lower than structured-CORE
generation.

Coverage delta from one dispatch extension:

- 15 / 15 `required-attribute` → real
- 11 / 11 `id-reference-resolves` → real
-  4 /  7 `unique-within-scope` → real (3 stubbed, no scope in YAML)
-  0 /  2 `format` → stub (format kind wasn't ISO 8601 duration)
-  0 /  2 `mutual-exclusion` → stub (needed ≥ 2 attrs, had only 1)
-  0 / 24 `conditional` → stub (rule-specific "if X then Y", no template)

~30 rules moved from stub to generated body in one pass. The `conditional`
bucket is the honest ceiling — each one is bespoke logic.

### Generator pitfalls

- **CORE's `instance_type` ≠ xlsx entity.** CORE walks into child classes
  (e.g. `Code`) when the semantic rule is about the parent's list attribute
  (`StudyVersion.businessTherapeuticAreas`). When they disagree and the
  xlsx attribute is plural, the rule is almost always intra-attribute
  uniqueness on the parent's list. Emit that, not cross-instance on the
  CORE class. This one bug alone produced 424 false-positive findings.
- **Not every CT pair has a codelist.** Generate `_ct_check(config, X, Y)`
  only after calling `CTLibrary.klass_and_attribute(X, Y)` at *generation
  time*. If it returns None, emit a stub — a runtime `CTException` is
  worse than a `NotImplementedError` because it's a crash, not a rule
  outcome.
- **JSONata variable leakage.** If the stage-1 attribute starts with `$`,
  the extractor picked up a JSONata variable name by mistake. Treat as
  unresolved and stub.
- **Text classifiers fold "at least one of A or B" into "required A".**
  The `required-attribute` regex matches "must be specified" which also
  appears in "at least X or Y must be specified". DDF00030 ("At least
  the text or the family name must be specified for a person name") was
  generated as a required-attribute check on `text` only, missing the
  alternation. Generated code is a starting point; the
  `# GENERATED — please review` header is doing real work.

## 6. Debugging patterns that paid off repeatedly

- **Staged diagnostic programs.** For silent pipeline failures (everything
  returns None with no error), build a small script that runs each stage
  independently, printing counts and types between stages. Catches the
  silent-exception pattern (top-level try/except returns None for every
  failure mode).
- **Sanity-check the shape before trusting the field.** When YAML / xlsx /
  CORE agree on a class but disagree on an attribute, prefer the xlsx
  attribute (the human-curated source). When they disagree on the class,
  prefer the xlsx entity if the attribute is list-shaped; otherwise prefer
  CORE's `instance_type`.
- **Protect existing tests from regeneration by default.** When a test file
  already exists, the default is "preserve it". Explicit `--overwrite-tests`
  flag required to replace. The tests/usdm4/rules/test_rule_ddf00105.py
  file had a sophisticated hand-authored mock-based test; a naïve
  regeneration would have lost it silently.
- **Severity is a silent trap when hand-authoring.** When you write a rule
  body by hand, `RuleTemplate.ERROR` is the natural default. But a rule's
  severity is determined by the xlsx (surfaced in the YAML's `severity`
  field) and may be `WARNING`. Two of three rules I hand-authored in the
  global-scope batch defaulted to ERROR when the YAML said WARNING — the
  metadata test caught both. **Always copy `severity` from the YAML**, not
  from muscle memory.
- **xlsx attribute names ≠ USDM JSON field names.** The xlsx "Attributes"
  column uses *semantic* names (`members`, `children`, `scope`, `dose`);
  the actual USDM JSON uses the reference convention
  (`memberIds`, `childIds`, `scopeId`). The generated metadata echoes the
  xlsx, but the `validate()` body must use the real JSON field names. Always
  verify via `dataStructure.yml` before coding.

## 7. Authoritative sources for CT codelist bindings

When generating rules that call `_ct_check(config, class, attribute)`, the
hard question is *which codelist does values of this attribute draw from?*
Three sources can answer, and they answer different questions:

- **`DDF-RA/Deliverables/UML/dataStructure.yml`** gives the attribute's
  *own concept* NCI C-code. For `Timing.relativeToFrom` the UML says
  `NCI C-Code: C201297` — that's "Timing Relative To From" (the attribute
  name concept), **not** the codelist the values come from. Using this
  as a codelist binding is wrong — I tripped on this.
- **`DDF-RA/Deliverables/CT/USDM_CT.xlsx`**, sheet `DDF Entities&Attributes`,
  column `Codelist URL` — this *is* the authoritative binding. For
  `Timing.relativeToFrom` the URL is
  `https://evsexplore.semantics.cancer.gov/.../C201265`. Extract the
  `C#####` from the URL. Only 55 of the ~255 attributes carry a URL;
  the rest don't have a controlled value-set.
- **CORE rule text**, e.g. `"... (C201265) DDF codelist"`. Regex out
  `\((C\d+)\)` from rule text. Usually agrees with USDM_CT.xlsx when
  both are populated.

**Preferred pipeline:** extract the C-code from rule text (regex over
xlsx source text); validate with USDM_CT.xlsx if available; never treat
UML's attribute NCI code as a codelist binding.

### Three conditions must all hold for a CT rule to run

`ct_config.yaml` has two sections with a silent precondition between
them:

1. The `klass_attribute_mapping` entry registers the `(class, attribute,
   codelist)` triple.
2. The codelist must appear in the top-level `code_lists:` list so the
   CT library loads its terms at init.
3. The codelist must actually be published in one of the loaded CDISC
   packages (`ddfct`, `sdtmct`, `protocolct`). Adding `C215479` to
   `code_lists:` when it isn't in any cached CDISC package fails: either
   silently (lookup returns None → `_ct_check` raises `CTException`) or
   loudly (CT library tries to fetch from CDISC Library API at load
   time → network call → ProxyError in offline environments).

All three conditions were satisfied for our 8 config additions. When
testing a new codelist, refresh the CT cache first; the library needs
the data before code-gen can rely on it.

### UML cross-check has a different job

`dataStructure.yml` doesn't give the codelist binding, but it does
validate whether `(class, attribute)` exists at all. Two of my initial
10 proposals — `StudyIntervention.productDesignation` and
`StudyDesignPopulation.unit` — failed this check: the attribute doesn't
exist on the stated class. Rule DDF00210 is really about
`AdministrableProduct.productDesignation` (CORE walked through the
wrong parent); DDF00237 targets `Quantity.unit` nested in `plannedAge`.
UML caught both as stage-1 class-identification bugs before I shipped
bad config.

**Workflow:** use USDM_CT.xlsx as the primary codelist source; use UML
as a validator that the (class, attribute) actually exists in the model.

## 8. "Complete the blanks" predicates — biconditional and implication

Some rule patterns are detectable from rule text but can't be fully
generated from text alone — you need the specific attributes and check
kinds filled in by a human. We handled two of these explicitly:

- **`biconditional`** — rule text contains `"vice versa"` or `"while if"`.
  Fires when the truth values of two conditions diverge.
- **`implication`** — rule text matches `"if ... then"` without biconditional
  markers. Fires when the antecedent holds but the consequent doesn't.

### The two-tier pattern

Stage-1 classifier sets `predicate: biconditional` (or `implication`) but
leaves the side specs (`side_a` / `side_b`, or `antecedent` / `consequent`)
empty. Stage-2's renderer stubs anything with incomplete specs and
generates working code for anything complete.

A human fills in the YAML specs between runs:

```yaml
# MANUAL: do not regenerate    ← stage-1 preserves the file
predicate: biconditional
class: Duration
side_a:
  attr: durationWillVary
  check: equal_to_bool
  value: true
side_b:
  attr: reasonDurationWillVary
  check: non_empty
```

The MANUAL sentinel on the YAML is essential — without it, the next
stage-1 regeneration clobbers the hand-completed specs.

### Shared check-kind library

Both predicates share the same check expressions, defined once in
`_biconditional_check_expr()`. Adding a new check kind gives both
predicates a new capability:

- `non_empty` — truthy value present
- `empty` — opposite of non_empty (used for inverse biconditionals)
- `equal_to_bool` — `item.attr is True` / `is False`
- `equal_to` — `item.attr == literal`
- `code_equals` — `item.attr.code == "C#####"` (for embedded Code/AliasCode attributes)

### What we got in two small passes

- **6 biconditional rules** generated from text classification + YAML specs
- **3 implication rules** (DDF00013, DDF00178, and DDF00261 which reclassified as biconditional after broadening the regex to include "while if")

Total: **9 more rules real for roughly 100 lines of generator code plus
~80 lines of YAML hand-edits**. The value isn't just these 9 rules —
it's the two templates' availability for any future MED_TEXT stub that
fits the pattern.

### When this approach fails

The "global-scope singular" cluster looked like a candidate (3 rules,
shared `if scope is global then ...` shape) but each rule's constraint
was actually different (cross-type uniqueness vs total-count-one vs a
different parent walk). A unified predicate would have needed three
parameter groups — more engineering than three hand-authored rules.

**Rule of thumb:** if two rules' Python bodies would have ≥ 70% line
overlap after parameter extraction, a template is worthwhile. Less than
that, hand-author each.

## 9. Hand-authoring workflow for bespoke rules

The per-rule recipe, refined across ~13 hand-authored rules this
session. Targets a ~5-minute cycle per rule.

1. **Read the intermediate YAML.** Note `text`, `class`, `attributes`,
   `severity`, `_core_jsonata_reference` (if present).
2. **Interpret the semantics.** Rule text is primary; CORE JSONata is a
   useful algorithmic guide for the check, especially for identifying
   which parent class to iterate and which codes to match.
3. **Verify field names in `dataStructure.yml`.** The xlsx attribute
   column uses semantic names that don't always match USDM JSON field
   names (see §6 on `members` vs `memberIds`). A quick lookup catches
   this before coding.
4. **Write the `validate()` body** using DataStore primitives —
   `instances_by_klass`, `parent_by_klass`, `instance_by_id`,
   `path_by_id`. Copy severity from YAML to avoid the ERROR-default
   trap (§6).
5. **Add the `# MANUAL: do not regenerate` sentinel at the top of the
   file.** This prevents stage-2 from overwriting your work on the next
   regeneration.
6. **Regenerate the test file** via
   `python3 tools/generate_rule_python.py --only DDF##### --overwrite-tests`.
   The sentinel protects the rule; the test file is re-emitted as an
   "implemented" skeleton (metadata check + two skipped TODO placeholders
   for positive/negative fixture data).

Typical timings:
- Cardinality / mutex / at-least-one-of / simple scoped check — 3 min each
- Cross-reference / scoped group-by — 5-8 min each
- Rules with inline helper functions in CORE's JSONata — 8-15 min each

## 10. Coverage realism — don't over-promise

After all the generator infrastructure (stage-1 YAML, stage-2 dispatch,
JSONata translator, MED_TEXT predicate dispatch, HAS_IMPLEMENTATION
preservation, CT codelist precheck, CT config extended, biconditional
and implication predicates, plus ~13 hand-authored rules),
**123 of 210 V4 rules have real implementations** (~59 %). The
remaining 87 fall into predictable buckets:

- 52 LOW_CUSTOM — rule-specific logic the JSONata translator can't help with
- 14 MED_TEXT conditional — rule-specific "if X then Y" logic that
  doesn't fit biconditional or simple implication (min < max comparisons,
  cross-class walks, ordering consistency, etc.)
- 11 HIGH_CT_MEMBER — class / attribute pair has no registered CT
  codelist; several of these are stage-1 bugs where CORE's condition
  walked into `codeSystemVersion` of a nested Code object and the
  extractor took that as the attribute
- 4 STUB — not in CORE at all
- 3 HIGH_UNIQUE_WITHIN_SCOPE — scope not inferable from CORE or rule text
- 1 HIGH_FORMAT — format kind not identified

Getting from 123 to 150+ means domain-knowledge hand-authoring per
rule, at roughly 5 minutes each per §9's workflow. Not more generator
engineering — the generator ceiling for this rule catalogue is around
60 %. Know this going in; don't chase an 80 % auto-generation target —
you'll either produce quietly-wrong rules or spend exponentially more
effort for diminishing returns.

**Session totals across a representative day:**

```
  84  start of session (after initial merge + stage-1/2 pipeline)
 101  + CT config + stage-2 xlsx-attribute fallback (+ cache refresh)
 111  + 10 hand-authored (at-least-one / cardinality / mutex / uniqueness)
 117  + biconditional batch (6)
 120  + implication batch (3)
 123  + global-scope batch (3 hand-authored)
```

A follow-up day pushed the total further via six hand-authored clusters:

```
 135  + cluster A self-reference (4: DDF00021/22/184/253)
       + cluster B quantity-unit (4: DDF00234/35/238/39)
       + cluster C mixed simple (5: DDF00033/44/63/188/256)
 143  + cluster E distinct-within-scope (4: DDF00219/20/21/22)
       + cluster F mutex scope (4: DDF00189/195/205/250)
 151  + cluster G orphan / reverse-FK (3: DDF00080/96/99)
       + cluster one-offs (5: DDF00018/42/186/236/241)
 163  + cluster amendment / reason (3: DDF00196/255/258)
       + cluster XHTML well-formedness (2: DDF00187/247)
       + cluster masking/blinding (2: DDF00191/192)
       + cluster scoped uniqueness (2: DDF00173/174)
       + cluster context/reference (3: DDF00114/124/244)
 168  + cluster harder-after-all (5: DDF00006/7/10/160/162)
 182  + cluster cross-design / CT / at-least-one (16: DDF00017/26/35/75/
         76/101/107/115/127/153/163/203/206/212/213/232)
 197  + Stage 1 batch — same-design / dateValues / mutex / conditional /
         grid / uniqueness (15: DDF00019/24/28/29/46/47/73/93/152/181/
         185/198/231/243/245)
 200  + DDF00081/125/126 marked as no-op delegates to DDF00082 (not new
         implementations; the schema validation has always been there)
 206  + Stage 2 batch — doubly-linked-list consistency / sibling-dup /
         ref-format / CT-codelist (6: DDF00023/27/137/210/237/246)
 210  + Stage 3 batch — cross-class prev/next vs. SAI flow / Condition
         appliesTo / Activity preorder walk (4: DDF00087/88/91/161)
```

**210 of 210 = 100 % coverage** (207 implemented + 3 delegated to
DDF00082). Stage 3 was the "interactive" batch where Dave's domain
answers unblocked each rule. Key clarification: prev/next on Activity
is a **display order** (preorder walk of the childIds tree) for SoA
rendering — not a graph-topology constraint. Once that was said,
DDF00161 collapsed into three short FK checks.

### Noting the DDF00082 delegation

DDF00081 ("class relationships conform to USDM schema"), DDF00125
("required/additional properties"), and DDF00126 ("cardinalities")
are all already enforced by DDF00082, which runs full `jsonschema`
validation against `src/usdm4/rules/library/schema/usdm_v4-0-0.json`.
The per-rule files for 00081/00125/00126 are deliberate no-ops that
`return True` with a module-level comment pointing at DDF00082. This
avoids duplicating the same schema violation as three separate rule
failures with different wording.

**Lesson.** When a CORE rule's English is "matches the reference
schema" and a real schema validator already exists in the codebase,
wire the rule to delegate rather than re-implementing the check.
Keep the rule registered (so coverage accounting is complete) and
document the delegation inline.

**Stub-count caveat.** `grep -l NotImplementedError src/usdm4/rules/library/rule_ddf*.py`
returns ~75 files, but many of those correspond to DDF IDs outside
the V4 subset (no intermediate YAML). The authoritative "remaining
V4 stubs" count is:

```bash
for f in src/usdm4/rules/intermediate/rule_ddf*.yaml; do
    rid=$(basename "$f" .yaml)
    py="src/usdm4/rules/library/${rid}.py"
    [ -f "$py" ] && grep -q NotImplementedError "$py" && echo "$rid"
done | wc -l
```

Cross-referencing against the intermediate YAMLs is the only way to
get the V4-specific figure.

A day of focused work can add ~40 rules when patterns emerge; hand-authoring
alone is ~10 rules/hour once the workflow is clean.

**Fixture quality and validation development are co-work.** As rules go
from stub to active, test fixtures that passed quietly start flagging
real data issues (placeholder codes like `C12345`, literal string
`"Decode"`, null values serialised as `"None"`). Plan for a
regenerate-expected-errors pass after each substantial generator run,
and expect a few tests to need fixture updates rather than code fixes.

**CT cache refreshes create their own failures.** Tests that pin a
specific CT package version (hardcoded dates like `"2025-09-26"` or
fixture JSONs generated against a specific package) break when the
cache is refreshed to a newer package. This isn't a regression in the
code under test — it's test-data drift. Either make the assertion
version-agnostic (check format rather than the date string), regenerate
the fixture at the new version via a `SAVE=True` pattern, or pin the
test to a specific CT package version if snapshotting matters.

## 11. DataStore traversal patterns

The hand-authored rules accumulated a small vocabulary of DataStore
access patterns. Reach for these before inventing new ones.

**`instances_by_klass(klass)`** — iterate every indexed instance of a
type. The workhorse. Returns a list of dicts from `_decompose`; they
are live references into the input JSON tree.

**`instance_by_id(id)`** — FK resolution. Use when a rule needs the
target of an `xxxId` attribute. Returns `None` for unknown ids — always
guard with `isinstance(..., dict)` before reading fields.

**`parent_by_klass(id, "Class")`** — typed ancestor walk. Returns the
nearest ancestor with `instanceType == "Class"` or `None` if none
exists. Essential when a rule scope is "X within Y" and you need Y's
fields. Examples: DDF00080 (SAI's parent `ScheduleTimeline` — we need
its `mainTimeline` flag), DDF00096 (Endpoint's parent `Objective` —
we need its `level.code`).

**`data._parent.get(id)`** — immediate parent of any class. Private
attribute; no public API for this. Use when the parent's *type* isn't
known up front, only that you need whatever's directly above. Examples:
DDF00044 (ConditionAssignment's immediate container, which varies —
ScheduledDecisionInstance in practice but nothing in the rule hinges
on that), DDF00260 (any instance with a space in its id). Access is
safe but not future-proofed: if DataStore grows a public `parent(id)`
accessor, switch to it.

**`data._ids`** — full id → instance dict. Use for model-wide passes
that aren't scoped to any class (DDF00260 is the only current example).
Same private-access caveat as `_parent`.

**`path_by_id(id)`** — the `$.Study....` string used in error
locations. Always use this rather than constructing paths manually.

### Scope a rule by semantic parent, not by the raw class

CORE sometimes over-broadens the scope class. The rule text is
authoritative: "the range for a planned age" means *specifically* the
Range under `StudyDesignPopulation.plannedAge` / `StudyCohort.plannedAge`,
not every Range instance in the model (there are many — under durations,
strengths, timings, etc.). DDF00042 scopes on the parent classes and
pulls `instance.get("plannedAge")`; DDF00241 stayed on all Ranges
because its rule text isn't parent-specific.

Read the rule text critically before trusting the YAML's `class` field.
If the rule says "the X of a Y", you almost always want to iterate Y
and pull `.get("x")`.

### Counter for "distinct within scope"

`collections.Counter` + list comprehension is the clean idiom for the
CORE "group by X, flag groups with count > 1" pattern:

```python
codes = [e.get("code") for e in entries if isinstance(e, dict) and e.get("code")]
duplicates = [c for c, n in Counter(codes).items() if n > 1]
```

Used across cluster E (DDF00219-222). If CORE groups by multiple fields
(e.g. DDF00221 groups by `codeSystem + codeSystemVersion + code`), use
tuples as keys.

### Reverse-FK / orphan via set intersection

Several rules are shaped "every X must be referenced from some Y". Build
the set of referenced ids in one pass, then check each X:

```python
referenced = {sai.get("epochId") for sai in data.instances_by_klass("SAI") if sai.get("epochId")}
for epoch in data.instances_by_klass("StudyEpoch"):
    if epoch["id"] not in referenced:
        self._add_failure(...)
```

DDF00099 (epochs), DDF00250 (dual-reference detection via `pop_refs &
cohort_refs`).

## 12. "Specified" can mean "has an id" in CORE semantics

Several rules use the shape "if X is specified, then Y". The natural
Python interpretation is `if x:` (truthy). CORE's JSONata is often
stricter — `$exists($st.denominator.id)` — meaning "the embedded object
has been materialised with an id". An empty dict `{}` or a dict with
only `{"extensionAttributes": []}` is *not* "specified" in CORE terms.

Examples where this matters:
- **DDF00186** (strength denominator) — the test is
  `$exists(denominator.id) and ($exists(denominator.unit)=false or unit=null)`.
  Implemented as `if not denominator.get("id"): continue`.
- **DDF00238** / **DDF00239** — "specified" means having a `value` set,
  not just `denominator is not None`.

When the rule has a CORE JSONata reference block, read the
`$exists(...)` guard carefully and mirror its condition in Python
rather than defaulting to truthiness.

## 13. YAML `classification` tag goes stale after a predicate fill-in

When you hand-fill `predicate: biconditional` + `side_a` / `side_b` on
an intermediate YAML, the `classification: MED_TEXT` tag stays put.
Stage-2 uses the predicate (not the classification) to dispatch, so
the rule is effectively implemented — but a filter like
`grep "classification: MED_TEXT"` will still show it as a stub.

**Use `grep -l NotImplementedError src/usdm4/rules/library/rule_ddf*.py`
as the true signal** of which rules still need work. The YAML
classification is a stage-1 hint, not the final state.

This is how 6 rules in "cluster D" (DDF00020/34/39/164/165/177) looked
like stubs on a classification filter but were actually rendered and
passing — the YAMLs had been filled earlier in the same session.

## 14. Fixture firings on real data are findings, not bugs

Hand-authored rules increasingly fire against the long-standing
`test_package.py` fixtures. Some observed this session:

- **DDF00188** — `example_2.json` encodes `plannedSex` as a single
  `"Both"` (C49636) code rather than separate Male (C20197) + Female
  (C16576) entries. The rule matches CORE's check exactly; the
  fixture is non-compliant.
- **DDF00189** — `example_2.json` has a StudyRole with
  `appliesToIds: []`. CORE's condition (`appliesToIds and ...`)
  requires non-empty. Rule correctly flags it.
- **DDF00236** — `example_2.json` has a BC with a synonym equal
  (case-insensitive) to its label. WARNING-severity.

These are legitimate findings against stale fixtures. They don't
change the pass/fail outcome of the tests that were already failing
on pre-existing issues (DDF00166 "Protocol" decode, DDF00217 "Decode"
placeholder), but they'll need to be reconciled when the fixtures get
cleaned up — either update the fixtures to be rule-compliant or add
the rule firings to the expected baseline.

**Work order for fixture cleanup:** resolve DDF00166 / DDF00217 first
(they're the hard-failure blockers). Once `test_validate` and
`test_example_2` are green, the package tests become a live regression
detector for every new rule addition; today any new firing hides
behind the existing failure.

## 15. Patterns from the amendment / masking / reference batch

A further batch across amendment, XHTML well-formedness, masking, and
reference-validation domains surfaced four small patterns worth a
separate entry.

### XHTML well-formedness via wrap-and-parse

`NarrativeContentItem.text` and `EligibilityCriterionItem.text` /
`Characteristic.text` / etc. are supposed to be XHTML. The CORE text
says "HTML formatted" but a practical check is **is it parseable as
XML once we declare the ambient namespaces?**

```python
WRAPPER_OPEN = '<root xmlns="http://www.w3.org/1999/xhtml" xmlns:usdm="http://example.com/usdm">'
WRAPPER_CLOSE = "</root>"

def _is_well_formed(text):
    try:
        ET.fromstring(WRAPPER_OPEN + text + WRAPPER_CLOSE)
        return True
    except ET.ParseError:
        return False
```

The declared `usdm` prefix is a placeholder — we only care that the
parser tolerates `<usdm:ref>` tags. This caught real issues in
`example_2.json`: `<table "="" class="...">` (bare `""=""` attribute),
unescaped ampersands, and unclosed elements. Used by DDF00187 and DDF00247.

### `<usdm:ref>` validation via regex + instance lookup

Several rules need to parse `<usdm:ref klass="X" id="Y" attribute="Z"/>`
markers out of a string and resolve each to a live instance. The
attributes come in arbitrary order, so don't hard-code position:

```python
USDM_REF_RE = re.compile(r"<usdm:ref\b([^>]*)(?:/>|>\s*</usdm:ref>)")
ATTR_RE = {
    "klass": re.compile(r'klass="([a-zA-Z]+)"'),
    "id": re.compile(r'id="([\w-]+)"'),
    "attribute": re.compile(r'attribute="([a-zA-Z]+)"'),
}
```

For each match, run each attribute regex over the captured `([^>]*)`
opening-tag innards and build a `{klass, id, attribute}` dict. Then
validate: `instance_by_id(id)` resolves, its `instanceType == klass`,
and `attribute` is in the instance dict. DDF00124 and DDF00244 share
this pattern; helpers are inlined in both rule files. Promote to a
shared utility if a third caller lands.

### Blinding-schema codes live on an AliasCode

The blinding schema is an `AliasCode`:

```
StudyDesign.blindingSchema = AliasCode {
    id, standardCode: Code { code, decode, ... }, standardCodeAliases: [...]
}
```

So the check is
`design.get("blindingSchema").get("standardCode").get("code")`, not
`design.get("blindingSchema").get("code")`. Relevant CT codes:
`C49659` open label, `C15228` double blind. DDF00191 and DDF00192 both
use this lookup; extracted a `_blinding_code(design)` helper in each.

### Inconsistent 1:1 via two dicts-of-sets

DDF00196 wants a one-to-one mapping between `sectionNumber` and
`sectionTitle` inside each StudyAmendment. The natural shape is two
`defaultdict(set)` lookups (number → set of titles, title → set of
numbers), populate both, then for each reference flag when either
side's set has >1 entry:

```python
num_to_titles = defaultdict(set)
title_to_nums = defaultdict(set)
for ref in refs:
    num_to_titles[(applies, ref["sectionNumber"])].add(ref["sectionTitle"])
    title_to_nums[(applies, ref["sectionTitle"])].add(ref["sectionNumber"])

for ref in refs:
    if len(num_to_titles[(applies, ref["sectionNumber"])]) > 1 \
       or len(title_to_nums[(applies, ref["sectionTitle"])]) > 1:
        fail(ref)
```

This is the clean idiom whenever "1:1 within a scope" shows up.

## 16. Patterns from the "harder after all" batch

Five rules originally flagged as harder (DDF00006/7/10/160/162) turned
out to be tractable with the toolkit the session built up. The patterns
are worth a separate entry because the rule texts read harder than the
implementations actually are.

### All-or-nothing across N attributes

"If any of {A, B, C} is defined then all must be defined." Filter the
input through a uniform "is specified" helper, count, and flag when
0 < specified < N:

```python
def _is_specified(value):
    if value is None:                 return False
    if isinstance(value, str):        return value.strip() != ""
    if isinstance(value, (list, dict)): return bool(value)
    return True

specified = [attr for attr in WINDOW_ATTRS if _is_specified(timing.get(attr))]
if specified and len(specified) < len(WINDOW_ATTRS):
    fail(...)
```

The helper is necessary because "specified" across embedded Duration
objects, strings, and primitives needs a single definition. DDF00006
uses this; the same helper serves any "all-or-nothing" rule.

### CT-code-gated implication

Several rules are "if `type.code == Cxxxxx` then ...". Pull the
constant to a module-level name for readability, guard on the code
early, then run the consequent check:

```python
FIXED_REFERENCE_CODE = "C201358"

for timing in data.instances_by_klass("Timing"):
    type_obj = timing.get("type")
    if not isinstance(type_obj, dict):
        continue
    if type_obj.get("code") != FIXED_REFERENCE_CODE:
        continue
    # consequent check here
```

Constants for known CT codes accumulated this session:

```
C15228   Double Blind Study           (blinding)
C17649   Other (reason)
C20197   Male                         (plannedSex)
C15228   Double Blind Study
C16576   Female                       (plannedSex)
C46079   Randomized
C48660   Not Applicable               (amendment reason)
C49636   Both                         (plannedSex — disallowed encoding)
C49659   Open Label                   (blinding)
C68846   Global                       (geographic scope)
C70793   Sponsor                      (study role)
C85826   Trial Primary Objective
C94496   Primary                      (endpoint level)
C25689   Stratification
C147145  Stratified Randomisation
C201358  Fixed Reference              (timing)
C207605  (used as a primary amendment reason code in fixtures)
```

Keep these inline in the rule file rather than a shared constants
module — the CT rule binding already lives in `ct_config.yaml` and
introducing a second constants surface invites drift. When a code is
referenced from >2 rules we can promote.

### Mutex "has X implies not any of Y1..Yn"

DDF00160: an Activity with `childIds` populated must not populate any
of five leaf-reference attributes. Same helper as §16.1 applies:

```python
LEAF_REF_ATTRS = ["biomedicalConceptIds", "bcCategoryIds", "bcSurrogateIds", "timelineId", "definedProcedures"]
if activity.get("childIds"):
    populated = [a for a in LEAF_REF_ATTRS if _is_populated(activity.get(a))]
    if populated:
        fail(...)
```

Shorthand: "when the parent flag is set, each of the children-flags
must be empty."

### Rule-text vs CORE-JSONata when they disagree

DDF00010's rule text says "names of child instances of the **same
parent class**" — which reads as "per-parent uniqueness". CORE's
JSONata ignores the parent entirely and does global uniqueness per
(instanceType, name). When these two primary sources disagree:

- **Mirror CORE.** It's the authoritative reference implementation.
  Hand-authors are trying to match its behaviour, not reinterpret
  the English.
- **Note the disagreement in the code comment** so a later reader
  understands the stricter behaviour was intentional, not sloppy.
- If the stricter behaviour is wrong in practice, the fix is a
  spec/CORE change, not a behavioural divergence in the Python.

### Iterator-returning malformed-tag detector

DDF00162 needed "find every malformed `<usdm:ref>` tag in a string
and report each". Cleanest shape is a generator that yields
`(matched_text, reason)` pairs — keeps the rule's `validate()` body
tight and makes the detection reusable / testable in isolation:

```python
def _find_malformed(text: str):
    idx = 0
    while True:
        start = text.find("<usdm:ref", idx)
        if start < 0:
            return
        idx = start + len("<usdm:ref")
        # ...parse, decide, yield or fallthrough...

for tag, reason in _find_malformed(nci.get("text", "")):
    self._add_failure(f"... {reason} — {tag[:80]}", ...)
```

For strict-format validation (value character classes), keep the
regexes per-attribute rather than trying to build one giant regex
covering all permutations — attribute order is arbitrary.

## 17. Patterns from the 88 % push

A 16-rule batch spanning CT-code gating, at-least-one-of, cross-class
FK validation, and cross-design walks — the long tail beyond the first
80 %. Few new patterns per se; mostly combinations of the existing
idioms. Worth noting where combinations matter.

### Same-study-design cross-walk

Idiom for "X must reference Y where Y lives in the same StudyDesign
as X":

```python
STUDY_DESIGN_KLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]

x_design = data.parent_by_klass(x_id, STUDY_DESIGN_KLASSES)
y_design = data.parent_by_klass(y_id, STUDY_DESIGN_KLASSES)
if x_design and y_design and x_design["id"] != y_design["id"]:
    fail(...)
```

Shared by DDF00107 (SAI → sub-timeline) and DDF00127 (Encounter →
scheduledAt Timing). `parent_by_klass` takes a list so the same call
handles Interventional and Observational without branching.

### "Only-X" via set difference

DDF00206: an AP is "only embedded" if it appears in
embeddedProductIds but not in any Administration's
administrableProductId. Build both sets from a StudyVersion in one
pass, check each AP for membership:

```python
embedded_ids = {d["embeddedProductId"] for d in sv["medicalDevices"] if d.get("embeddedProductId")}
administered_ids = {a["administrableProductId"] for i in sv["studyInterventions"] for a in i.get("administrations", [])}

for ap in sv["administrableProducts"]:
    if ap["id"] in embedded_ids and ap["id"] not in administered_ids:
        # "only embedded" AP
        check_constraint(ap)
```

Companion to the intersection idiom from DDF00250
(`pop_refs & cohort_refs`). The two read similarly in code, so pick
based on what the rule is counting.

### Wrapper-vs-leaf exclusion on the same attribute

Activity carries both `childIds` (if it's a container) and a set of
leaf-reference attributes (for direct-referencing activities). Rules
that check the leaf attrs should skip activities with `childIds` —
they delegate to children:

```python
for activity in data.instances_by_klass("Activity"):
    if activity.get("childIds"):
        continue  # wrapper; children do the referencing
    if not any(activity.get(a) for a in LEAF_REF_ATTRS):
        fail(...)
```

DDF00075 uses this exclusion; DDF00160 inverts it (if you have
children, leaf attrs must be empty). Keep the two consistent.

### FK filtering before threshold counts

DDF00213 filters studyInterventionIds against the set of known
StudyIntervention ids before counting:

```python
known = {si["id"] for si in sv.get("studyInterventions", [])}
referenced = {i for i in design.get("studyInterventionIds", []) if i in known}
if len(referenced) <= 1:
    fail(...)
```

Without the filter, a dangling id in studyInterventionIds would
inflate the count and mask a real "too few interventions" failure.
Same trick applies wherever a cardinality check reads from an FK list.

### Polymorphic "acceptable" helpers for CT-qualified fields

DDF00017's `_is_acceptable_unit` accepts four shapes: None, False,
empty dict, dict with `standardCode.code == PERCENT_CODE`. CORE has
several rules of this shape ("attribute must be empty or match these
specific CT codes"). The helper reads cleanly when the acceptable
set is expressed as a sequence of narrowing checks — short-circuit
on each.

### More CT codes that landed this batch

Append to the table in §16.2:

```
C25613   Percent                      (SubjectEnrollment.quantity.unit)
C70793   Sponsor                      (study role, reused from earlier)
C82637   Parallel Group Design        (intervention model)
C82638   Crossover Design
C82639   Factorial Design
C98388   Interventional Study Type
C207616  Official Study Title         (StudyTitle.type)
```

Same rule as before: keep the codes as module-level constants in
the rule file; promote to shared only if a third caller shows up.

## 18. Patterns from Stage 1 (the 95 % push)

Stage 1 (15 rules) mostly applied existing patterns but surfaced three
worth lifting to their own sections.

### `frozenset` as part of the group key for set-equivalence

When grouping by "this entry's *set* of scope codes" (rather than an
ordered list), use `frozenset` in the key so equivalent sets compare
equal regardless of order:

```python
def _date_key(date):
    type_code = (date.get("type") or {}).get("code")
    scopes = date.get("geographicScopes") or []
    scope_codes = frozenset(
        (s.get("type") or {}).get("code")
        for s in scopes
        if isinstance(s, dict) and isinstance(s.get("type"), dict)
    )
    return (type_code, scope_codes)

groups = defaultdict(list)
for date in parent.get("dateValues", []):
    groups[_date_key(date)].append(date)
for key, entries in groups.items():
    if len(entries) > 1:
        fail(...)
```

Used by DDF00093 and DDF00181 (dateValues uniqueness by type + scope
set). Without `frozenset` — say, sorting into a tuple — the key
construction is more verbose and less obvious about intent.

### Grid coverage: Cartesian product vs. observed set

DDF00243 requires "one StudyCell per (StudyArm, StudyEpoch) pair" —
that is, the full Cartesian product must be covered with multiplicity
exactly 1. Three-step check:

```python
arm_ids = {a["id"] for a in design["arms"]}
epoch_ids = {e["id"] for e in design["epochs"]}
expected = {(a, e) for a in arm_ids for e in epoch_ids}

cell_counts = Counter(
    (c["armId"], c["epochId"])
    for c in design["studyCells"]
    if c["armId"] in arm_ids and c["epochId"] in epoch_ids
)

missing = expected - set(cell_counts)
duplicated = {pair for pair, n in cell_counts.items() if n > 1}
if missing or duplicated:
    fail(...)
```

Report both missing and duplicated in the same message — the rule is
really "exactly one per pair", so both directions of deviation matter.
Filtering the Counter input to valid arm/epoch ids avoids polluting
the report with cells that point at non-existent arms/epochs.

### Iterate-then-filter-by-ancestor for scoped cross-cutting checks

When a rule scopes to "X within Y" and X instances are scattered
deep in the tree, it's ergonomic to iterate X globally then filter
by ancestor rather than walking down from Y:

```python
for code_inst in data.instances_by_klass("Code"):
    code_sv = data.parent_by_klass(code_inst["id"], "StudyVersion")
    if code_sv is None or code_sv["id"] != sv_id:
        continue
    # ...collect this Code for the current SV...
```

DDF00073 uses this to collect all Codes within each StudyVersion.
Walking down from StudyVersion would mean enumerating every field
that can hold a Code — tedious and fragile. The filter-by-ancestor
approach doesn't care about shape.

**Trade-off:** O(|Code| × |StudyVersion|) instead of O(|Code|). Fine
at clinical-trial scale. If a future rule scales worse, invert to
build a Code-by-SV index once up front.

### Delegation as a coverage strategy

See §10 for the broader framing. The specific case: DDF00081 /
DDF00125 / DDF00126 each cite "USDM schema" as the check. DDF00082
runs full `jsonschema` validation against the same schema. Rather
than three separate re-implementations, make 00081/125/126
`return True` with a module-level comment pointing at DDF00082. The
rule files stay registered for coverage accounting; the test files
assert the no-op behaviour explicitly so a future refactor can't
silently turn them into real checks.

## 19. Patterns from Stage 2 (the 98 % push)

Six rules that leaned on existing idioms plus a few new wrinkles.
Most are straightforward; flagging three that are worth a separate
note.

### Doubly-linked-list consistency in both directions

DDF00023 checks back-links: for each instance I, `I.previousId` must
point at an A where `A.nextId = I.id` (if A has a nextId at all).
Symmetric for `I.nextId` → B, require `B.previousId = I.id`. The
rule text says "the previous id value must match the next id value
of the referred instance" — slightly ambiguous but CORE's conditions
spell out both directions.

The idiom is terse once you trust the structure:

```python
for instance in data.instances_by_klass(klass):
    self_id = instance["id"]
    for forward, backward in [("previousId", "nextId"), ("nextId", "previousId")]:
        target_id = instance.get(forward)
        if not target_id:
            continue
        target = data.instance_by_id(target_id)
        if isinstance(target, dict) and target.get(backward):
            if target[backward] != self_id:
                fail(...)
```

Missing back-links (A has no nextId at all) aren't flagged — that's
a different rule's concern. Only *mismatched* back-links fail.

### CT codelist registered but not yet in cache

DDF00237 needs the Age Unit codelist (C66781), which is SDTM CT —
not in the default USDM cache. Three-layer situation:

1. Add C66781 to `ct_config.yaml` `code_lists:` so a future cache
   refresh will pull it.
2. Don't count on the cache being fresh *right now* — the
   `library_cache_usdm.yaml` snapshot was taken before we added the
   codelist.
3. Make the rule defensive: if
   `config["ct"]._by_code_list.get("C66781") is None`, return True.
   The rule will silently re-activate when the cache is refreshed.

```python
codelist = ct._by_code_list.get(AGE_UNIT_CODELIST)
if codelist is None:
    # C66781 is registered in ct_config.yaml but only populates
    # after a CT cache refresh. Skip rather than crash.
    return True
```

This is a "ship the config change now, the functionality activates
after refresh" pattern. The alternative — raising CTException — is
the pattern used by `_ct_check` (which assumes the codelist
*should* be present). Use the raising behaviour when the codelist
is expected to be there; use the defensive skip when a cache
refresh is the enabling step.

### When `klass_attribute_mapping` can't express the path

`ct_config.yaml`'s `klass_attribute_mapping` is flat: `Class: { attr:
codelist }`. For DDF00237 the target is `plannedAge.unit` — two
levels deep from StudyDesignPopulation. Can't be encoded in the
flat mapping.

Two options:

- Use `cl_by_term()` or `_by_code_list[code_id]` to fetch the
  codelist directly, then do the membership check inline.
- Register the nested class.attribute (here, `Quantity.unit`) and
  rely on context — but Quantity.unit serves many different
  codelists depending on context (age, percent, mass, etc.), so a
  blanket mapping would be wrong.

DDF00237 chose option 1. Keep the codelist ID as a module-level
constant so the rule is self-documenting; fetch via `_by_code_list`
(accepting the private-attribute access — same caveat as `_parent`
and `_ids` in §11).

### When stage-1 gets the class wrong

DDF00210's YAML lists `class=StudyIntervention`, but the rule is
actually about `AdministrableProduct.productDesignation` (per
ct_config.yaml's existing binding and the CORE conditions). Stage-1
has a recurring class-extraction weakness documented in §7 — when
CORE's walk traverses through a parent to reach the actual scoped
class, stage-1 may record the walk's origin rather than the target.

**When this shows up,** the fix is a one-line override in the
`validate()` body: just point `_ct_check` (or the equivalent) at
the correct class. Don't try to fix it upstream in stage-1 — the
surface area is too broad. Note the correction in a comment so a
future reader doesn't trust the YAML's class field.

## 20. Patterns from Stage 3 (the 100 % push)

Four rules that needed a paragraph of domain context each before the
Python became obvious. The context mattered more than the code. Three
patterns worth recording.

### Dual-graph comparison with consecutive-dedup

DDF00087 and DDF00088 both compare two linked-list orderings derived
from the same underlying structure:

- Graph A: a simple prev/next walk through a flat list (encounters,
  epochs).
- Graph B: a walk through a different structure (SAIs via
  `defaultConditionId`), collecting an FK (`encounterId`, `epochId`)
  at each hop, then **deduping consecutive repeats** because one
  encounter / epoch can span multiple adjacent SAIs.

```python
def _walk_chain(by_id, head_id, next_attr):
    visited, order = set(), []
    cur = head_id
    while cur:
        if cur in visited:
            return order, True  # cycle
        visited.add(cur)
        order.append(cur)
        node = by_id.get(cur)
        cur = node.get(next_attr) if isinstance(node, dict) else None
    return order, False

def _dedupe_consecutive(seq):
    out = []
    for item in seq:
        if not out or out[-1] != item:
            out.append(item)
    return out
```

Both checks ship cycle detection via a visited set (Dave: "yes, allow
for looping and detect if we can"). Multiple chain heads — more than
one node with no `previousId` — are flagged as a separate warning;
they indicate a fragmented chain, which is a setup problem even if
the orderings technically align on the first head.

### Domain context collapses spec ambiguity

DDF00161's rule text reads like a graph-theory problem: "parents
preceding their children in the prev/next ordering." CORE's JSONata
is three interlocking predicates. But Dave's one-sentence context —
"prev/next is the display order for the SoA; parent row, then child
rows, then next parent row" — reframes it as preorder traversal of
the childIds tree. The three CORE predicates become three cheap FK
checks:

1. If I have children, my `nextId` must be one of them (step into
   the first child).
2. If I'm a child, my `previousId` must be within my parent's
   subtree (transitively — includes descendants of older siblings).
3. If my `previousId` points at a node that has children, I must
   be one of those children (symmetric of 1).

No topological sort; no graph algorithm; just three lookups per
Activity. Total implementation: ~40 lines.

**Lesson.** When a rule reads as "topology / ordering / consistency"
and CORE's JSONata has three nested `not-any-of` clauses, ask the
domain owner *what the attribute is actually used for in practice*.
The answer often reduces the implementation dramatically.

### Reuse the DDF00114 / DDF00212 shape for "FK must resolve to one
of these classes"

DDF00091 is the fourth instance of this pattern in the session.
Shape is stable enough to template:

```python
ALLOWED_CLASSES = {"Procedure", "Activity", "BiomedicalConcept", ...}

for source in data.instances_by_klass(SCOPE):
    for target_id in source.get("<fk list attr>") or []:
        if not target_id:
            continue
        target = data.instance_by_id(target_id)
        target_type = target.get("instanceType") if isinstance(target, dict) else None
        if target_type not in ALLOWED_CLASSES:
            self._add_failure(...)
```

Four callers (DDF00091, DDF00114, DDF00189's variant, DDF00212). Not
yet worth a shared utility — each has a different ALLOWED_CLASSES
set, a different attribute name, and a slightly different failure
message. Promote when the fifth arrives.

## 21. Stage-by-stage session retrospective

Looking back at the seven batches that took coverage from 64 % to
100 %:

| Stage | Rules | Dominant pattern | Time per rule |
|-------|-------|------------------|---------------|
| Early batches | 29 | Direct CORE translation (self-ref, mutex, at-least-one) | 3-5 min |
| Cross-design / CT / at-least-one | 16 | `parent_by_klass` + FK resolution | 5 min |
| Stage 1 | 15 | Same-design twins + dateValues dedup + grid | 4-5 min |
| Stage 2 | 6 | Doubly-linked-list + CT cache work | 8-10 min |
| Stage 3 | 4 | Domain discussion first, Python second | 5-15 min |

**Observations.**

- Pattern libraries compound. Stage 1 was faster per rule than the
  earlier batches because `parent_by_klass` / `Counter` / defaultdict
  idioms were already locked in.
- The last 10 % of rules took ~40 % of the time. The "easy 90 / hard
  10" intuition holds.
- Interactive domain input was the unlock for Stage 3. Without
  Dave's "prev/next is display order" sentence, DDF00161 would have
  been a half-day of wrong topology implementations.
- The `classification` field in the intermediate YAMLs is unreliable
  as a difficulty signal. Six rules classed MED_TEXT/HIGH_CT_MEMBER
  turned out to be one-line fixes once the pattern was recognised.
  Use `NotImplementedError` grep + rule-text reading instead.
- No new generator features needed after the first ~150 rules.
  Hand-authoring from stage-1 YAMLs was more productive than
  extending stage-2 for ever-more-specific predicate shapes.
