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
