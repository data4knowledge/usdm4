# USDM4 Validation Engine — Plan

April 2026. Design notes for building a self-contained validation engine inside `usdm4`. Deliverable: an engine and a rule library that together execute the 210 V4-applicable rules from the CDISC `USDM_CORE_Rules.xlsx` catalogue against USDM JSON, independent of the CDISC CORE engine.

Follow-on work — adding M11 protocol validation on top of this engine — is covered in a separate plan in the `usdm4_protocol` repo (`usdm4_protocol/docs/m11_validation_plan.md`). That work does not start until this plan is complete.

## Goal

Ship a USDM4 validation engine with three properties:

1. **Self-contained inside `usdm4`.** No `usdm3` imports anywhere. No runtime dependency on any other rules package.
2. **Independent of CDISC CORE.** The CDISC CORE engine (`cdisc_rules_engine`, accessed via `USDM4.validate_core(...)`) stays where it is. It runs the same rule catalogue, in JSONata, and is useful as a cross-check. Our engine runs the catalogue in Python. The two are siblings, not substitutes.
3. **Extensible.** Adding a rule means dropping one file into `usdm4/rules/library/`. No registration. Auto-discovery picks it up. Every rule is self-contained — one `RuleTemplate` subclass per file, one class per rule ID.

The engine runs the full set of **210 DDF rules** where `Version 4.0 = Y` in `DDF-RA/Deliverables/RULES/USDM_CORE_Rules.xlsx`.

## CDISC CORE vs USDM4 engine

Two engines running the same rule catalogue:

| | CDISC CORE engine | USDM4 validation engine |
|---|---|---|
| Lives in | `cdisc_rules_engine` pip package | `usdm4.rules` |
| Rule format | JSONata, downloaded from CDISC Library | Python, one file per rule |
| Invoked via | `USDM4.validate_core(path)` | `USDM4.validate(path)` |
| Rule catalogue | 207 DDF rules from CORE download | 210 DDF rules (V4=Y from xlsx) |
| Role | Authoritative CDISC reference implementation | Our own implementation we control and extend |

We are not replacing CORE. We are building a parallel, Python-native engine that we own, can extend (e.g. with M11 rules later), and can integrate cleanly into the round-trip pipeline.

## Architectural decisions

### Fold usdm3 into usdm4 with zero remnants

v3 support is being removed. Everything `usdm4` currently imports from `usdm3` moves into the `usdm4` namespace, and `usdm3` as a dependency is deleted. Target state: `grep -r "usdm3" usdm4/ usdm4_protocol/ udp_prism/` returns nothing. (`usdm4_protocol` and `udp_prism` are already clean — the entire footprint is inside `usdm4`.)

| From (v3) | To (v4) |
|---|---|
| `usdm3.rules.rules_validation.RulesValidationEngine` | `usdm4.rules.engine.Engine` |
| `usdm3.rules.rules_validation_results.RulesValidationResults` | `usdm4.rules.results.Results` |
| `usdm3.rules.library.rule_template` (`RuleTemplate`, `ValidationLocation`) | `usdm4.rules.rule_template` |
| `usdm3.rules.library.schema.*` | `usdm4.rules.schema.*` |
| `usdm3.data_store.data_store.DataStore` | `usdm4.data_store.*` |
| `usdm3.base.singleton`, `id_manager`, `api_instance` | `usdm4.base.*` |
| `usdm3.ct.cdisc.library.Library` | fold into existing `usdm4.ct.*` |
| `usdm3.bc.cdisc.library.Library` | fold into existing `usdm4.bc.*` |

While relocating, generalise the engine's `config` dict so it accepts any shape, not just `{"data": DataStore, "ct": CTLibrary}` — needed so the same engine can later run M11 rules (with a docx-shaped config) without modification.

### Rule ID scheme — DDF only

The authoritative catalogue is `DDF-RA/Deliverables/RULES/USDM_CORE_Rules.xlsx`: 259 rules total, **210 applicable to v4** (`Version 4.0 = Y`), 209 ERROR / 50 WARNING. Each row carries a `Final CORE Rule ID` (`DDF#####`) and a transitional `Check_ID` (`CHK####`). The DDF ID is canonical; CHK is retired.

- Every rule file is named `rule_ddf#####.py` with class `RuleDDF#####`.
- The 85 existing `rule_chk*.py` files are consolidated into their DDF equivalents (mapping via the `Check_ID` column) and deleted.
- Rules where `Version 4.0 = N` (49 rules) are v3-only and removed from the library.
- Existing `rule_ddf*.py` files that wrap v3 implementations have the v3 body inlined and the `usdm3` import removed.

### Rules are self-contained, one class per file

No shared state, no central manifest, no registry. Auto-discovery walks `usdm4/rules/library/`, imports every `rule_*.py`, picks up every `RuleTemplate` subclass. Adding a rule = drop a file. Same property makes the library easy to diff and to generate mechanically.

## Rule generation — two-stage pipeline

The 210 V4 rules won't be hand-authored. A two-stage generator produces most of them from structured inputs, with a human-review pause in the middle so the domain interpretation gets a second set of eyes before Python is emitted.

```
CORE JSON (4-0.json)    ┐
USDM_CORE_Rules.xlsx    ├──→  [stage 1]  →  per-rule intermediate YAML
                        ┘                           │
                                                    ▼
                                             [you review / refine]
                                                    │
                                                    ▼
                                            [stage 2]  →  rule_ddf#####.py
                                                       →  test_rule_ddf#####.py
```

### What CDISC CORE gives us

The CORE rule cache (populated via `USDM4.prepare_core(...)`) writes `rules/usdm/4-0.json` to disk. One JSON file, **207 rules**, each a structured object with `core_id`, `reference[].Rule_Identifier.Id` (the DDF id), `entities.Include`, `conditions` (a boolean tree over named operators), and `actions` (failure message string).

Coverage: 207/207 rules carry a DDF identifier — mechanical 1:1 join with the xlsx. 207/207 carry an action message — failure text is free.

Condition vocabulary across the whole catalogue is small: **17 distinct operators**, with `equal_to`, `non_empty`, `empty`, `exists`, `is_contained_by` dominating. Each maps to one or two lines of Python against the DataStore:

| CORE operator | Python equivalent |
|---|---|
| `equal_to`, `not_equal_to`, `equal_to_case_insensitive` | `==`, `!=`, `.lower() ==` |
| `empty`, `non_empty` | presence / non-empty check on attribute |
| `exists`, `not_exists` | `attr in item` / not |
| `is_contained_by`, `is_not_contained_by` | codelist / list membership |
| `is_not_unique_set` | duplicate detection |
| `invalid_duration` | ISO 8601 duration validation |
| `greater_than` | `>` |
| `contains`, `contains_case_insensitive`, `does_not_contain_case_insensitive` | substring / membership |
| `not_matches_regex` | regex test |
| `shares_no_elements_with` | set disjoint |

Condition top-level shape: 114 rules use `all` (conjunction), 1 uses `any`. The remaining 92 rules have a different shape that hasn't been inspected yet — those are the unknown in the feasibility estimate.

### Intermediate YAML format

Stage 1 emits one YAML document per rule, structured (not free-form English). Example for DDF00171:

```yaml
ddf00171:
  class: Abbreviation
  attribute: expandedText
  scope:
    type: parent-of-class
    klass: StudyVersion
  predicate: unique-within-scope
  severity: WARNING
  text: "The expanded text for all abbreviations defined for a study version are expected to be unique."
  message: "Duplicate expandedText within study version"
```

Fields a stage-1 generator has to populate:

- `class` — from CORE `entities.Include` or xlsx "Applies to"
- `attribute` — from CORE `conditions` target, or xlsx "Attributes"
- `scope` — parsed out of rule text ("for a X", "within a Y", "globally") or inferred from CORE's conditions. This is the hardest field to populate automatically.
- `predicate` — mapped from CORE's condition operators (see table above). Small, enumerated set.
- `severity`, `text` — direct from xlsx
- `message` — direct from CORE `actions[0].params.message`

Any field stage 1 cannot populate is emitted as `UNKNOWN` with a comment pointing at the source it was trying to use. Those rules surface in the human-review pass.

### Predicate vocabulary for the generator

| Predicate | What it means | Code template |
|---|---|---|
| `ct-member` | Value in named codelist | `self._ct_check(config, klass, attr)` |
| `required-attribute` | Attribute must be present / non-empty | iterate klass, check presence |
| `mutual-exclusion` | At most one of listed attrs may be set | iterate klass, count non-empty |
| `unique-within-scope` | Attr values unique per scope | `parent_by_klass` + dict grouping |
| `id-reference-resolves` | Attr holds id; must resolve via `instance_by_id` | iterate klass, resolve id |
| `conditional` | If attr-A set, attr-B must also be set | iterate klass, check implication |
| `format` | String attribute matches format (ISO duration, etc.) | per-format helper |
| `custom` | Doesn't fit above | hand-authored body |

Seven generic predicates plus `custom` for the long tail.

### Test coverage — generated alongside rules

Stage 2 emits both a rule file and a matching test file, both keyed on the same DDF id. Test layout mirrors `tests/usdm4/rules/` (existing convention — `test_rule_ddf00105.py` etc.), one test class per rule.

Three tiers of test, driven by the intermediate YAML:

- **Metadata-assertion tests** (all 210 rules). Instantiate, assert `_rule == "DDF00081"`, `_level == ERROR`, `_rule_text == "..."`. Trivial to generate, catches merge/rename typos.
- **Stub-lock tests** (rules with `predicate: custom` or `UNKNOWN`). Instantiate, call `validate(dummy_config)`, assert `NotImplementedError` is raised. Fails loudly the moment someone implements a rule without adding a real test, forcing the real test to get written.
- **Implementation tests** (rules with a known predicate). Skeleton with `test_pass` and `test_fail` methods, fixtures marked `# TODO: craft positive/negative USDM`. For CT-member rules, fixtures can be almost auto-generated by reading `CTLibrary`. For other predicates, the test **data** is hand-crafted.

## Work order

```
0. Inspect the 92 odd-shaped CORE rules                           (read-only, small)
1. Merge usdm3 → usdm4 (zero remnants)
2. Stage 1 generator: CORE JSON + xlsx  →  per-rule intermediate YAML
   [you review / refine the YAMLs; correct scope / predicate where needed]
3. Stage 2 generator: reviewed YAML  →  rule_ddf#####.py + test_rule_ddf#####.py
   [emits working rules + tests where YAML is complete;
    stubs + TODOs elsewhere]
4. Hand-finish, two flavours:
   4a. Refine YAMLs for rules where stage 1 was incomplete; re-run stage 2.
   4b. Hand-author Python for `custom` predicate rules; mark as MANUAL so
       stage 2 leaves them alone on regeneration.
5. Full test suite green.
```

Step 0 is a cheap sanity check: those 92 rules may be CORE rules that aren't implemented (empty conditions), in which case they fall straight through to stub-lock tests. Or they may have a different but still structured shape that stage 1 can absorb. Finding out takes minutes; guessing wastes days.

Step 1 has to run before steps 2 and 3, because the generator emits code importing from `usdm4.rules.rule_template`, `usdm4.data_store`, etc. Those paths don't exist until after the merge.

## Data sources

| Source | What it gives | Consumed by |
|---|---|---|
| `DDF-RA/Deliverables/RULES/USDM_CORE_Rules.xlsx` | Authoritative rule catalogue: 210 V4 rules with DDF IDs, text, severity, class, attributes | Rule list; metadata fields in intermediate YAML |
| `<cache>/rules/usdm/4-0.json` (CORE) | 207 rules with structured `conditions`, `actions`, `entities`, DDF cross-reference | Scope / predicate inference in stage 1; failure messages |
| `<cache>/ct/published_packages.json` | CDISC CT codelists | CT-member tests; ct-check rule bodies |
| `usdm4.data_store.DataStore` | Decomposed USDM JSON: `instances_by_klass`, `instance_by_id`, `path_by_id`, `parent_by_klass` | Rule implementations (runtime) |
| `usdm4.ct.CTLibrary` | Codelist lookup for `_ct_check` helper | CT-based rule implementations |

The CORE cache is populated on the developer machine via `tools/prepare_core_cache.py` (already present). Its contents are read-only inputs to stage 1.

## Regeneration behaviour

Two-stage means: correct the intermediate YAML, code regenerates cleanly. But hand-authored Python for `custom` rules must not be overwritten on the next run. Two mechanisms work equally well — pick one:

- **Sentinel comment in the Python file** (e.g. `# MANUAL: do not regenerate`) — stage 2 skips files containing it.
- **Flag in the YAML** (e.g. `implementation: manual`) — stage 2 emits a stub that defers to a hand-authored sibling file, or skips generation entirely.

Decide when the generator is being written.

## Deliberate non-choices

- No separate validation package. The engine and rules live inside `usdm4`.
- No optional install extra. Validation is core to `usdm4`.
- No YAML or DSL rule format *at runtime*. Rules are Python. YAML is an authoring intermediate, not a runtime artefact.
- No runtime dependency on the CORE cache or xlsx. Both are read at authoring / regeneration time only.
- No parallel engine, `Rule` ABC, or result type. Single engine in `usdm4` after the v3 merge.
- CDISC CORE wrapper (`USDM4.validate_core`) is kept, unchanged. It serves as an independent cross-check and is not being replaced.

## Open items, not blockers

- The 92 CORE rules with non-`all`/`any` condition shape. Step 0 inspects them; action depends on what they look like.
- Regeneration sentinel choice (see above).
- Version handling. CORE cache is `rules/usdm/4-0.json`. When USDM 4.1 ships, the generator needs to know which CORE version to read against. Probably a `--usdm-version 4-0` flag, default to the newest cache file present.
