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

## 8. Coverage realism — don't over-promise

After all the generator infrastructure (stage-1 YAML, stage-2 dispatch,
JSONata translator, MED_TEXT predicate dispatch, HAS_IMPLEMENTATION
preservation, CT codelist precheck, CT config extended with 8 new
(class, attribute) bindings), **92 of 210 V4 rules have real
implementations** (~44 %). The remaining 118 fall into predictable buckets:

- 62 LOW_CUSTOM — rule-specific logic the JSONata translator can't help with
- 31 MED_TEXT stubs — mostly `predicate: conditional` (24), plus smaller
  edge cases (format kind not ISO 8601, uniqueness without scope, etc.)
- 17 HIGH_CT_MEMBER — class / attribute pair has no registered CT
  codelist; several of these are stage-1 bugs where CORE's condition
  walked into `codeSystemVersion` of a nested Code object and the
  extractor took that as the attribute. Salvageable with a stage-2
  fallback that prefers the xlsx "Attributes" column when CORE's
  attribute is `codeSystemVersion`.
- 4 STUB — not in CORE at all
- 3 HIGH_UNIQUE_WITHIN_SCOPE — scope not inferable from CORE or rule text
- 1 HIGH_FORMAT — format kind not identified

Getting from 92 to, say, 150 means domain-knowledge hand-authoring per
rule, not more generator engineering. The generator ceiling for rules of
this shape is roughly 45 %. Know this going in; don't chase an 80 % auto-
generation target — you'll either produce quietly-wrong rules or spend
exponentially more effort for diminishing returns.

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
