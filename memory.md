# usdm4 — project memory

## 2026-08-07 — CoreValidator fixed on 54-core-engine: executionStatus + bundled schema (issue #54)

- Root causes of the exec-error flood (6,749/file) and dropped findings,
  found by diffing our wrapper against the CORE CLI (same engine 0.16.0,
  same rules — byte-identical; same json):
  1. _classify_errors ignored the engine's per-result executionStatus and
     string-matched error text. "skipped" results (rule doesn't apply to
     entity — SkippedReason lists the very strings we matched) flooded
     execution_errors. Now: skipped→dropped, "issue reported"→findings,
     "execution error"→exec errors; string set kept only as no-status
     fallback. Matches the CLI report logic (usdm_report_data.py).
  2. LibraryMetadataContainer got no standard_schema_definition, so
     JsonSchemaCheckDatasetBuilder rules (CORE-000938/DDF00126 cardinality)
     silently found nothing. The CLI ships usdm-<v>-schema.pkl — a pydantic
     model_json_schema() dump of the API Wrapper (NOT our
     rules/library/schema/usdm_v4-0-0.json, which is the full OpenAPI doc).
     DECIDED (Dave): vendor CORE's shipped schemas, converted pkl→JSON, as
     core/data/usdm-{3-0,4-0}-schema.json (source: cdisc-rules-engine
     v0.16.0, c78b05c); manual refresh when CORE updates. NOTE: our Wrapper
     model has drifted (84 $defs vs shipped 82, Base* classes) — vendoring
     keeps parity with official CORE; disagreements surface as findings.
- Parity verified: NCT04573309 49 findings + 1 exec error; NCT03637764
  84 + 1 — both match the CLI number-for-number per rule.
- Changed: core_validator.py, setup.py (package_data), new core/data/*.json,
  tests (+8, status classification + schema loading). core/ subset: 177
  pass, core_validator.py 100% cov. Ruff default-rules + format clean.
  Stale .git/index.lock present — rm it before committing.
- Dave's full-suite run then surfaced 2 baseline failures = the fix seeing
  what was invisible: (a) sample_usdm_7.json had 'extensionAtrtibutes' key
  typo x3 + mangled instanceType values x7 (extensionClass/extensionCLass/
  ExtensionCLass/extensionAttribute) in its extension subtree — ALL FIXED
  in the file (Dave's call: clean exemplar, not as-received artifact);
  cleared CORE-000937, CORE-000949 and d4k DDF00082 with no baseline edit.
  (b) assembled-minimum: CORE-000938 ADDED to _KNOWN_FAILING_RULES with
  comment — three real assembler gaps on the minimum fixture
  (StudyAmendment.changes, InterventionalStudyDesign.arms, .studyCells all
  emitted []); assembler fix is separate work, candidate for its own issue.
  Full suite GREEN (Dave's run, 2026-08-07) — issue #54 resolved; branch
  ready to merge. Uncommitted: core fix + schema data + sample_usdm_7 fix
  + baseline edit + memory (Dave commits by hand).


## 2026-08-03 — api __all__ gaps: CommentAnnotation + 2 more; suite GREEN (Dave's run)

- usdm4_excel's annotations_and_abbreviations parity fixture exposed:
  CommentAnnotation missing from api/__init__.py __all__, which seeds the
  Builder IdManager → builder.create KeyError, every note creation
  failed. Audit found two more latent ones also builder-created by
  usdm4_excel readers: BiospecimenRetention, ConditionAssignment. All
  three added to imports + __all__.
- Third recurrence of this bug class (12076cf fixed MedicalDevice/
  Substance/ProductOrganizationRole). New guard test
  tests/usdm4/api/test_api_all_complete.py: scans api/*.py class defs,
  subtracts a NON_CONCRETE list (ApiBase*/Base*/Extension/Identifier/
  PopulationDefinition/QuantityRange), asserts the rest are in __all__.
- Why usdm4_excel unit tests never caught it: their SheetFramework mocks
  IdManager.build_id — only real end-to-end imports hit the id index.

## 2026-08-03 — TagResolver fixed and exposed (uncommitted)

- utility/tag_resolver.py already held the recursive usdm:ref/usdm:tag
  resolver (from usdm_utility/to_m11.py) but was broken: imported DataStore
  from usdm3 (eliminated in the v3→v4 merge) → fixed to
  usdm4.data_store.data_store. soup.py MODULE string fixed
  (was "usdm4_fhir.m11.soup.soup").
- beautifulsoup4>=4.9 declared in setup.py + requirements.txt — first
  direct bs4 use in usdm4 (previously only transitive via
  cdisc-rules-engine).
- Public access added: Builder.data_store property (None before seed());
  USDM4.tag_resolver(file_path, errors) → TagResolver over a decomposed
  DataStore. TagResolver + DataStore exported from usdm4 __init__.
- New integration test tests/usdm4/utility/test_tag_resolver_integration.py
  using sample_usdm_7.json (dictionary min_age/max_age tags → nested
  usdm:ref → Quantity values; exercises the recursion for real).
- Placement decision (Dave): usdm:ref + usdm:tag are USDM-standard →
  resolver lives in usdm4. usdm:macro is authoring sugar → expanded at
  workbook import by usdm4_excel; never appears in USDM JSON, resolver
  ignores it by design.
- usdm_utility/to_m11.py stays as-is: throwaway test code (Dave), not to be
  refactored onto the resolver.
- Escaping FIXED (Dave, 2026-08-03): resolver output is destined for
  rendered documents (usdm4_protocol / usdm4), so replace_with now inserts
  parsed soup, not text — refs to XHTML-valued attributes come through as
  markup, nested tags inside resolve too. Verified standalone against
  sample_usdm_7 (scalar, plain, rich cases).
- Stray usdm:macro in USDM content: TagResolver now WARNS ("Unexpanded
  usdm:macro...") and leaves the tag in place (was silent pass-through).
  Macro EXPANSION stays in usdm4_excel only — the engine needs workbook
  context (import-time name/xref registrations, workbook dir for images);
  no second consumer exists. Revisit lifting it into usdm4 only if
  usdm4_protocol or another non-Excel author needs macros.
- Suite state: ALL TESTS PASS (Dave's run, 2026-08-03), incl. the new
  test_tag_resolver_integration.py. Changes still uncommitted — Dave
  commits himself.
