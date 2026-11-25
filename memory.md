# USDM4 — Working Memory

The session log. **Rate of change: per session, appended. Never retired.**

An entry is a dated record of what happened, and the file's one job is total
recall — a cold start on another machine reads this plus `docs/lessons_learned.md`
plus `CLAUDE.md` and resumes without the chat. Nothing is removed.

Entries are appended at the END, headed `## YYYY-MM-DD — title` and nothing else.
Several entries may share a date. The plan is `docs/next_steps.md`, rewritten
wholesale; it holds no log.

Every session that works a `usdm4` issue is entered here in full, whichever
Claude project drove it. Entries up to 2026-10-02 were moved verbatim from the
Session Log formerly in `docs/next_steps.md`.

References in entries up to 2026-09-27 to "design § n" and "plan …" are to
`timeline_assembler_design.md` and `timeline_assembler_plan.md`, both retired that day (git
history). The design's as-built sections are now in the entries they belong to; the current
rules and decisions (U4-n) are in `docs/spec/timeline_assembler.md`.

## 2026-11-07 — GitHub 98, 99, 100: 1.1.2 assignment in extensions, repeating secondary reasons and sponsor-type parties

**Repos.** usdm4 (this work). Callers: usdm4_protocol 144 to 146, usdm4_fhir 58 to 60. Pointer in udp_prism `memory.md` 2026-11-07.

**What it was.** M11 1.1.2 Intervention Assignment Method and stratification have a USDM 4.1 home that 4.0 lacks, and usdm4 validates against the strict 4.0 schema, so they cannot sit on the design as attributes. An amendment could hold one secondary reason, and a sponsor-type party one organisation; M11 and sheet 03.13 repeat both.

**What changed.**
- Assembler inputs — `randomisation_type`, `other_assignment_method`, `stratified`, held in extension `IA_EXT_URL` with children for method, stratified, other method and randomisation type (GitHub 98); list `secondary` (99); list `roles` (100).
- Accessors — `secondary_reasons_as_text()`, `co_sponsor_organizations()` and siblings.
- `tests/conftest.py` — parses the packaged CT and BC caches once per run. The 15 new tests reloaded them each time; a Builder is shared and the file stays.
- `docs/issues.md` — N28: M11 Primary Reason repeats on an element USDM holds once.

**Figures.** `pytest` passed on each branch (Dave). Version 0.31.0.

**Rejected.** Attributes on the design under 4.0: the schema refuses them.

**Found, not this work.** None.

## 2026-11-07 — GitHub 101: region lookup accepts a name or a code

**Repos.** usdm4 (this entry). Found by udp_prism: pointer in its `memory.md`.

**What it was.** `Library.region_code` searched only the three region name columns. The amendment assembler finds a region by name, then passes its code (150) through `Builder.iso3166_region_code`, and the FHIR import passes a code too, so a region scope got no code and the region was lost on the round trip.

**What changed.**
- `src/usdm4/ct/iso/iso3166/library.py` — `_get_region` matches a name, ignoring case, or a code, across region, sub-region and intermediate region, and returns code and name.
- `tests/usdm4/ct/iso/iso3166/test_iso3166_library.py`, `tests/usdm4/assembler/test_amendments_assembler.py`, `tests/usdm4/builder/test_builder.py` — updated.

**Figures.** Dave's udp_prism run on the Air 2026-11-07: TCBCPT_02 "Not Global Europe" gives Amendment Scope Not Global and Region Identifier Europe (150) to step 3. `pytest` passed (Dave). Version not changed.

**Rejected.** A narrower fix in `Builder.iso3166_region_code` alone: it left the FHIR import failing.

**Found, not this work.** udp_prism N86: `Encoder.amendment_reason` loses the Other text.

## 2026-11-08 — GitHub 102: amendment reason takes the free text

**Repos.** usdm4 (this entry), branch `102-amendment-reason-takes-bare-value`. Released with usdm4_protocol GitHub 150 and usdm4_fhir GitHub 62. Found by udp_prism N86: pointer in its `memory.md`.

**What it was.** `Encoder.amendment_reason` split the reason on ":" and decoded only the second part. The README documented the input as CODE:DECODE; usdm4_protocol and usdm4_fhir sent "Primary: <text>", the heading in the code place. "Primary: Other: Regulatory agency request" matched Other on "Other" and returned no text. Dave: the assembler input never carries a code; the assembler builds codes.

**What changed.**
- `src/usdm4/assembler/encoder.py` — `amendment_reason` takes the free text: a C217276 term, matched ignoring case, gives its code; "Other: text" gives C17649 and keeps the text, further colons included; any other text gives Other with the whole text.
- `README.md` — the reasons note: free text, no code, no heading.
- `tests/usdm4/assembler/test_encoder.py` — "Reason:" prefixes removed; tests for "Other: text", Other text with a colon, "Other:" with no text.
- `tests/usdm4/assembler/test_amendments_assembler.py` — code prefixes removed from every reason input.

**Figures.** `pytest` passed (Dave). udp_prism run on the Air 2026-11-08 with all three branches: TCBCPT_03, 04 Other reason text kept, title page round trip 0 unexplained. Version not changed.

**Rejected.** Keeping CODE:DECODE with a third part for Other text: puts code lookup in every caller.

**Found, not this work.** None.

## 2026-11-11 — GitHub 103: combination product as a MedicalDevice; coverage to 100%

**Repos.** usdm4 (this entry), branch `103-assembler-builds-no-medicaldevice`. Released with usdm4_protocol GitHub 154 and usdm4_fhir GitHub 63. Found by udp_prism N82, N79: pointer in its `memory.md`.

**What it was.** The study design input had products, interventions and administrations but no devices, so no MedicalDevice was ever built and a drug/device combination product (a device with an embedded product) could not be expressed; the M11 Drug-Device Combination Product Indicator was always No. `Encoder.INTERVENTION_TYPE_MAP` had no Combination Product (C54696), Diagnostic, Dietary Supplement, Non-Surgical Procedure or Surgery, so each fell to the Drug default with a warning. Dave then asked for the coverage gaps (99.46%, 65 lines) to be closed on the branch.

**What changed.**
- `src/usdm4/assembler/schema/study_design_schema.py` — `DeviceInput` (name, label, description, `embedded_product`, sourcing); `StudyDesignInput.devices`; `AdministrationInput.device_name`; validator for undeclared embedded products and devices.
- `src/usdm4/assembler/study_design_assembler.py` — pass 0b `_build_devices` (embeddedProductId from the named product, sourcing through the encoder, warned when unresolved); administrations set `medicalDeviceId`, and leave `administrableProductId` unset when the device embeds that product (DDF00205); `medical_devices` property.
- `src/usdm4/assembler/study_assembler.py` — devices placed on `StudyVersion.medicalDevices`.
- `src/usdm4/assembler/encoder.py` — the five M11 intervention types C99078 holds.
- `src/usdm4/assembler/identification_assembler.py` — a role organisation that failed to create was logged with `errors.exception(message, location)` (the location in the exception's place); now `errors.error` with the location.
- `src/usdm4/rules/engine.py` — a try/except around `self.rules.append(obj)`, which cannot raise, removed.
- `README.md` — products and devices note with an example.
- Tests: `test_study_design_assembler_devices.py` (15), `test_study_design_schema.py` (6 added), `test_assembler.py` (device on StudyVersion), `test_encoder.py` (new types), `test_encoder_intervention_type_ct.py` (every mapped type resolves in the packaged CT); coverage: `timeline/test_plan_build_edges.py`, `test_assembler_edges.py`, `builder/test_builder_duplicate.py` (kept: usdm4_excel calls `duplicate`), `convert/test_convert_dates.py`, `rules/test_rule_edges.py`, `utility/test_soup_warnings.py`, `expander/test_timepoint_code_dict.py`, additions to `core/test_core_cache_manager_branches.py` and `bc/cdisc/test_library_api.py`.

**Figures.** Dave's pytest before the coverage work: 4077 passed, 99.46%. After it: only the new and changed files run here (262 and 25 passed); Dave's full run not yet reported. udp_prism run on the Air 2026-11-11: TCBCPT_04 device and indicator Yes at step 1 and step 3, round trip 0 unexplained. Version not changed.

**Rejected.** Comparing classes with `is` in tests (the suite imports both `src.usdm4` and `usdm4`; compare by name). Patching `get_validator` by module path in the DDF00247 test (the rule engine reloads library modules under the same name; patch `validate.__globals__`).

**Found, not this work.** None.

## 2026-11-11 — GitHub 104: ISO 11239 dose forms coded, with the EDQM term as an alias

**Repos.** usdm4 (this entry), branch `104-dose-form-ignores-iso-11239-terms` (cut from main, which holds GitHub 103). Found by udp_prism N78: pointer in its `memory.md`.

**What it was.** M11 Pharmaceutical Dose Form is "IDMP (ISO 11239) or CDISC SDTM Terminology". `StudyDesignAssembler._dose_form` matched CDISC C66726 only, so EDQM Standard Terms names ("Solution for injection", "Inhalation powder", "Powder for concentrate for solution for infusion") became Unknown and the term was lost. usdm4 held no EDQM terms. NCI EVS publishes them with an NCIt concept code per term (EDQM-HealthCare Terminology Subsets); 36 of the 523 dose forms share their NCIt concept with a C66726 term.

**What changed.**
- `tools/edqm_ct.py` (new) — reads the workbook's "Pharmaceutical Dosage Form" sheet into `src/usdm4/ct/edqm/dose_forms.yaml`: EDQM code, term, NCIt code, with EDQM's attribution, the NCI release (workbook modified date) and the retrieval date. Terms not modified (EDQM's conditions).
- `src/usdm4/ct/edqm/dose_forms.yaml` (new, generated) — 523 terms, NCI release 2026-05-27, retrieved 2026-11-11.
- `src/usdm4/ct/edqm/library.py` (new) — lookup by term ignoring case and spacing; code system and version (the retrieval date).
- `src/usdm4/assembler/study_design_assembler.py` — `_dose_form`: CDISC as before; else EDQM → C66726 term of the same NCIt concept, or Unknown with a warning; the EDQM term in `standardCodeAliases` (`http://standardterms.edqm.eu`). Neither: Unknown as before.
- `setup.py` — packages the YAML. `requirements.txt` — `openpyxl` for the tool. `README.md` — dose form note with the EDQM attribution. `CLAUDE.md` — the tool and its command.
- Tests: `tests/tools/test_edqm_ct.py`, `tests/usdm4/ct/edqm/test_edqm_library.py`, four cases in `test_study_design_assembler_products.py`.

**Figures.** New and changed tests run here with `pytest.ini`: 35 passed, `ct/edqm` 100%. Dave's full pytest not yet reported. Checked on the real file: Solution for injection → C42945 + EDQM 11201000; Inhalation powder → Unknown + 11109000; Powder for concentrate for solution for infusion → Unknown + 50043000; Sterile Solution → Unknown. No change end to end in udp_prism: the dose form is not carried in PRISM3 (usdm4_fhir I-13). Version not changed.

**Rejected.** A hand-chosen nearest C66726 term for EDQM terms with no shared NCIt concept (Dave: Unknown with the alias). Fetching EDQM terms from EDQM's own API (account and API privileges needed; the NCI file is free and attributable).

**Found, not this work.** None.

## 2026-11-12 — GitHub 105: no enrollment built when none is given

**Repos.** usdm4 (this entry), branch `105-enrollment-built-without-input`. Found by udp_prism N53: pointer in its `memory.md`; with usdm4_protocol GitHub 158 and usdm4_fhir GitHub 64.

**What it was.** `AmendmentsAssembler._create_enrollment` built a SubjectEnrollment with a quantity of 0 when the input had no enrollment, so every amendment that states none carried "0 enrolled".

**What changed.**
- `src/usdm4/assembler/amendments_assembler.py` — `_create_enrollment` returns None when `data["enrollment"]` is missing or empty; `_create_amendment` keeps only a built enrollment, so `enrollments` is empty. The 0-quantity default branch removed.
- `tests/usdm4/assembler/test_amendments_assembler.py` — no enrollment gives `enrollments == []`; `_create_enrollment({})` and the edge cases give None. `tests/usdm4/assembler/test_assembler_edges.py` — the failure test passes an enrollment.

**Figures.** ruff clean. pytest not reported (Dave). udp_prism run on the Air 2026-11-12: 8 protocols have no enrollment at step 1 and step 3. Version not changed.

**Rejected.** None.

**Found, not this work.** None.

## 2026-11-20 — GitHub 106: USDM JSON auto-fix for ids and CT version/decode

**Repos.** usdm4 (this entry), branch `106-auto-fix-duplicate-ids-and-ct`. Not in usdm4, recorded here: the backbone (d4k_architecture stack) could not load study NCT05676931 because it builds `urn:usdm:study:{slug}/{id}` from raw ids; after the fix it then hit Fuseki's 25 MB form limit (`413: form too large`) on one `INSERT DATA`; Dave changed the backbone's graph load and the study now loads.

**What it was.** Extraction output for NCT05676931 had 183 ids reused 2,338 times (CORE-001015 / DDF00083), ids that are not URI-safe (`10^12/L`, `ADJUDICATION COMMITTEE`), and CT codes with wrong decodes. Nothing in usdm4 repaired a file; validators only reported.

**What changed.**
- `src/usdm4/fixer/` (new) — `USDM4().fix(path, ids=True, ct=True)` returns `FixResult` (`data`, `changes`, `issues`, `save`, `save_log`). Input never changed.
- `fixer/id_fixer.py` — references found from the model's Ref attributes and `usdm:ref` tags. Cross-class duplicate: class of the first occurrence keeps the id, others become `<id>_2`… and their references follow; a reference that could point at more than one of the classes is reported, id unchanged. Same-class duplicate: renumbered when unreferenced; reported, unchanged, when referenced (Dave's rule: the subset is assumed clean, reuse is an input error). Then every id outside `[A-Za-z0-9_.-]` has each unsafe run replaced by `_`, on every object with that id and every reference (Dave: a shared unsafe id is renamed too; it stays a reported duplicate).
- `fixer/ct_fixer.py` — a CDISC `codeSystemVersion` that is not a release date (DDF00155's list plus the cache dates) gets the release date most used in the file; valid dates untouched. Decode set to the preferred term on attributes mapped in `ct_config.yaml` unless it equals the preferred term or submission value. Code not in its codelist, or CDISC code with another codeSystem: reported. No code swaps.
- `fixer/references.py` (generated) and `tools/references_map.py` (new) — 83 Ref attributes and superclass → subclasses from DDF-RA v4.0.0 `dataStructure.yml` (identical to main for Ref attributes).
- `fixer/walk.py`, `fixer/fix_result.py`, `fixer/fixer.py` (new) — instance walk with DDF00083-style paths, result and log, step runner.
- `tools/fix_usdm.py` (new) — CLI: input JSON → fixed JSON + `<output>.log.json`; refuses output == input.
- `src/usdm4/__init__.py` — `USDM4.fix`. `CLAUDE.md` — fixer and both tools. `tests/usdm4/integration/README.md` — new test row.
- Tests: `tests/usdm4/fixer/`, `tests/tools/test_references_map.py`, `tests/tools/test_fix_usdm.py`; `tests/usdm4/integration/test_fixer_d4k.py` (sample 7 with injected duplicate, cross-class clash, bad version, bad decode; fixed file must fail exactly what the sample fails; shown to fail with reference rewriting off); four enrollment scope tests in `test_amendments_assembler.py` (lines 419-446 lost coverage when GitHub 105 stopped building an enrollment without input).

**Figures.** NCT05676931, d4k, before the URI-safe pass: 3,259 → 1,538 findings; DDF00083 2,338 → 3 (one decision instance used in three timelines, referenced: reported); 53 decodes changed, 0 versions; 36 codes reported not in codelist. Dave's full pytest passed at 100% before the URI-safe pass; after it, fixer, tools and integration tests pass here, Dave's full run not reported. Version not changed.

**Rejected.** Setting mapped codes to the CT cache date (left 1,183 codes on 2024-09-27 beside 593 on 2026-03-27: DDF00073 fired). Guessing which object a referenced same-class duplicate meant. Decoding the 667 CORE-000427 findings: nearly all are BC AliasCode.standardCode misuse (C17998 "Unknown" with ~150 decodes) and unit strings as ResponseCode codes, which only a code swap fixes.

**Found, not this work.** N29, N30.

## 2026-11-20 — GitHub 107: builder CT libraries load on first access

**Repos.** usdm4 (this entry), branch `107-iso-3166-loading`. Closes N29.

**What it was.** `Builder` loaded its CT, BC, ISO 3166 and ISO 639 libraries only in `_ensure_ct_loaded`, which its own CT methods call. `AmendmentsAssembler._create_scopes` and `_enrollment_geographic_scope` read `iso3166_library` directly, and `assembler/timeline/build.py` reads `cdisc_bc_library.exists`. On a fresh builder the ISO 3166 lookup raised `TypeError`, was caught, and the scope was lost. A full `Assembler.execute` always loaded the libraries first, so no output was wrong; the GitHub 106 enrollment scope tests failed when run on their own.

**What changed.**
- `src/usdm4/builder/builder.py` — the four libraries are held as `_cdisc_ct_library`, `_cdisc_bc_library`, `_iso3166_library`, `_iso639_library`; public names are properties that call `_ensure_ct_loaded` first.
- `tests/usdm4/assembler/test_amendments_assembler.py` — the GitHub 106 fixture that forced loading removed; new test resolves a country scope on a fresh builder.

**Figures.** Dave's full pytest passed. Version not changed.

**Rejected.** Calling `_ensure_ct_loaded` in the amendments assembler: fixes one caller, leaves `timeline/build.py` and any later direct reader exposed.

**Found, not this work.** None.


## 2026-11-21 — GitHub 108: the assembler builds several study designs

**Repos.** usdm4 (GitHub 108, branch `108-assembler-builds-multiple-studydesigns`); used by usdm4_protocol GitHub 163.

**What it was.** `AssemblerInput` took one `study_design`, so a protocol with substudies could not carry one StudyDesign per substudy.

**What changed.**
- `assembler/schema/design_schema.py` — `DesignInput`: one design's design fields, population, objectives and SoA.
- `assembler/assembler_input.py` — `study_designs`; `study_design` required unless `study_designs` is given.
- `assembler/assembler.py` — `_execute_designs`: one pass of the design assemblers per design.
- `assembler/design_assemblers.py` — the per-design assemblers.
- `assembler/population_assembler.py` — inclusion and exclusion criteria shared across designs, built once and reused.
- `assembler/study_assembler.py` — gathers the designs; design roles apply to their own design.
- `builder/cross_reference.py` — a name scope, so the same names in two designs do not collide.
- Tests: `tests/usdm4/assembler/test_assembler_study_designs.py`. Dave's pytest passed, coverage 100%.

**Figures.** None measured on protocols here.

**Rejected.** Sharing objectives and endpoints across designs (Dave: they tend to be specific; criteria are shared).

**Found, not this work.** None.

## 2026-11-25 — GitHub 109: safety event reporting rows held as extension classes

**Repos.** usdm4 (this entry), branch `109-safety-event-reporting-table-extension`. Used by usdm4_protocol GitHub 165 and usdm4_fhir GitHub 65 (full entries in their logs); checked in udp_prism.

**What it was.** USDM 4.0 has no home for the M11 9.2 reporting table. CDISC has proposed a USDM 4.1 class, one row per event type (DDF5 SME meeting, 10 November 2026, a suggestion with open questions; Dave: good enough for the FHIR work). The strict 4.0 schema refuses it as an attribute.

**What changed.**
- `src/usdm4/api/extensions_d4k.py` — URLs 024 to 033 and `SER_TEXT_URLS` (input name → URL).
- `src/usdm4/assembler/schema/study_schema.py` — `SafetyEventReportingInput`; `StudyInput.safety_event_reporting`.
- `src/usdm4/assembler/study_assembler.py` — one ExtensionAttribute (024) per row on StudyVersion, in input order, its value an ExtensionClass (025) holding a child per stated column; nothing defaulted. First use of a class extension. A row with a blank event type is dropped with a warning; other event type given when the event type is not Other is dropped with a warning.
- `src/usdm4/assembler/encoder.py` — `safety_event_type`: a C217287 term, ignoring case and a trailing full stop, gives its code; any other text is Other (C17649) with the text kept.
- `src/usdm4/assembler/base_assembler.py`, `study_design_assembler.py` — `_base_code` moved to the base.
- `src/usdm4/api/study_version.py` — `safety_event_reporting()`. `README.md` — the input.
- Tests: `test_study_assembler_safety_event_reporting.py`, `test_study_schema.py`.

**Figures.** Dave's pytest passed. udp_prism run 2026-11-25: 55 rows in 7 protocols, 0 unexplained. A script validated a small study against the 4.0 schema: the rows add no fault. The d4k rules add DDF00073 (M11 terminology date beside the CDISC one), as control type does. CORE not run. Version not changed.

**Rejected.** Nested attribute extensions (table, row, column), built first and replaced by the class extension (Dave). StudyDesign as the home: M11 has one table per protocol and every column is text.

**Found, not this work.** None.
