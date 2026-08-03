# usdm4 — project memory

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
