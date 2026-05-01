# Corpus extractor fix list

Each entry below is a corpus-side issue that the eval harness's adapter is currently bridging. The adapter is a stop-gap — the long-term fix is in the corpus extractor pipeline (`protocol_corpus/scripts/extractors/`). When the corpus produces the schema-correct shape, the corresponding adapter transform can be removed.

The numbering matches `validate/corpus_adapter.py`'s `AdapterReport` fields so a per-protocol record can be traced back to a fix.

> **Status snapshot at the time of writing:** all entries below are *open* on the corpus side; the adapter handles them so evaluation can proceed.

---

## 1. `roles` keys use hyphens (`co-sponsor`) instead of underscores (`co_sponsor`)

**Adapter transform:** `_adapt_roles` — normalises `co-sponsor` → `co_sponsor`. Tracked as `adapter.role_keys_normalised`.

**Corpus output today:**
```yaml
identification:
  roles:
    co-sponsor: {name: "Some CRO"}
```

**Schema-correct output:**
```yaml
identification:
  roles:
    co_sponsor: {name: "Some CRO"}
```

**Affected protocols:** 58 / 234 (those with a co-sponsor entry).

**Where to fix:** wherever `identification.roles` keys are produced. Likely the identification extractor.

---

## 2. `roles.sponsor` is redundant when an identifier scope already names the sponsor

**Adapter transform:** `_adapt_roles` — drops role keys not in `IdentificationAssembler.ROLE_ORGS` (which doesn't include `sponsor`). Tracked as `adapter.role_keys_dropped`.

**Corpus output today:**
```yaml
identification:
  roles:
    sponsor: {name: "Eli Lilly and Company"}
  identifiers:
  - identifier: "18852"
    scope:
      non_standard:
        type: sponsor               # the corpus already names the sponsor here
        name: "Eli Lilly and Company"
```

**Schema-correct output:** drop the `roles.sponsor` entry entirely. The protocol identifier's organisation IS the sponsor; the assembler creates the org via the identifier scope. The role entry is redundant data that can drift out of sync with the identifier.

**Affected protocols:** 234 / 234 (every protocol).

**Where to fix:** identification extractor — stop emitting `roles.sponsor` when the sponsor is already captured on an identifier. If the *only* sponsor info is in the role entry (no identifier), the corpus should instead synthesise an identifier with the sponsor as a non-standard scope.

---

## 3. `non_standard.type` is being used as a role label instead of an org kind

**Adapter transform:** `_adapt_non_standard_orgs` — when `non_standard.type` isn't a recognised `ORG_CODES` key, moves it to `role` and sets `type` to `"pharma"`. Tracked as `adapter.non_standard_type_remapped`.

**Corpus output today:**
```yaml
identifiers:
- identifier: "18852"
  scope:
    non_standard:
      type: sponsor                   # role label in the type field
      name: "Eli Lilly and Company"
      label: "Sponsor identifier"
```

**Schema-correct output:**
```yaml
identifiers:
- identifier: "18852"
  scope:
    non_standard:
      type: pharma                    # org kind from ORG_CODES
      role: sponsor                   # role label
      name: "Eli Lilly and Company"
      label: "Sponsor identifier"
```

The USDM4 schema (`NonStandardOrganization`) already separates the two fields; the corpus is conflating them.

**Valid `type` values:** `pharma`, `cro`, `academic`, `gov`, `medical_device`, `lab`, `regulator`, `registry`, `healthcare`, `unknown`. See `IdentificationAssembler.ORG_CODES`.

**Affected protocols:** 215 / 234 (those with a `non_standard` sponsor identifier — all the NCT protocols).

**Where to fix:** identification extractor — wherever the `non_standard` block is built for a sponsor or other named org. Default `type` to `pharma` for sponsored trials; populate `role` separately.

---

## 4. `amendments.enrollment` not populated

**Adapter transform:** when `amendments.enrollment` is `None`, sets `{"value": 0, "unit": ""}`. Tracked as `adapter.enrollment_defaulted`.

**Corpus output today:** `amendments.enrollment` is consistently `None` (key absent / null).

**Schema-correct output:** when known, populate with the planned enrollment. When unknown, omitting is also acceptable (USDM4's `_create_enrollment` falls through to a zero-persons default after the truthy fix landed). The adapter default is purely a belt-and-braces.

**Open question for the corpus:** is enrollment data extractable from the protocol PDF? If so, the amendments / enrollment extractor should pick it up. If not, leaving it as `None` is fine — USDM4 handles that.

**Affected protocols:** 234 / 234.

---

## 5. `study_design.label` is empty

**Adapter transform:** when `study_design.label` is empty, sets it to `"STUDY-DESIGN"`. Tracked as `adapter.placeholder_labels` (with `study_design`).

**Corpus output today:**
```yaml
study_design:
  label: ""
  rationale: ""
  ...
```

**Schema-correct output:** non-empty `label` (e.g. derived from study acronym + design type, or from text in the protocol's "Study Design" section). USDM4's API model insists on `min_length=1` for the resulting `name`/`label` fields.

**Affected protocols:** 234 / 234 (the corpus design extractor doesn't populate this field at all today).

**Where to fix:** `protocol_corpus/scripts/extractors/study_design.py`. Until the extractor is implemented, the placeholder is harmless but obviously wrong.

---

## 6. `population.label` is empty

**Adapter transform:** when `population.label` is empty, sets it to `"POPULATION"`. Tracked as `adapter.placeholder_labels` (with `population`).

**Corpus output today:**
```yaml
population:
  label: ""
  inclusion_exclusion:
    inclusion: [...]   # may be populated
    exclusion: [...]
  ...
```

**Schema-correct output:** non-empty `label` describing the study population (e.g. "Adults with major depressive disorder"). Used for both `name` and `label` on the USDM4 `StudyDesignPopulation`.

**Affected protocols:** at least 19 / 234 (CORP*); likely more after USDM4 fixes propagate further down the pipeline.

**Where to fix:** `protocol_corpus/scripts/extractors/population.py`.

---

## 7. `study.name.identifier` is empty although the protocol_id is right there

**No adapter transform yet** — surfaces as a Pydantic `min_length=1` ValidationError on the top-level `Study` for protocols where `name.identifier`, `name.acronym`, and `name.compound` are all empty (CORP* protocols).

**Corpus output today:**
```yaml
protocol: CORP0001                # the protocol_id is right here
unvalidated:
  content:
    study:
      name:
        identifier: ''            # but it didn't make it into the study block
        acronym: ''
        compound: ''
```

**Schema-correct output:**
```yaml
study:
  name:
    identifier: CORP0001          # at minimum, populate from the protocol_id
    acronym: ''                   # extract if present in the protocol document
    compound: ''                  # extract if present
```

The assembler walks `[identifier, acronym, compound]` looking for the first non-empty value (`study_assembler._get_study_name_label`) and uses that as both the Study `name` and `label`. As long as one of the three is populated, this works.

**Affected protocols:** 19 / 234 (CORP*). NCT* protocols already populate `acronym` (or `identifier`) so this doesn't bite them.

**Where to fix:** `protocol_corpus/scripts/extractors/study.py` — set `name.identifier = <protocol_id>` as the floor; populate `acronym`/`compound` when extractable from the protocol document. No adapter bridge has been added; this should be a cheap corpus-side fix.

---

## 8. `soa` is a list, USDM4 takes a single timeline

**Adapter transform:** `_adapt_soa` — collapses to the first list entry, drops sub-timelines. Tracked as `adapter.soa_list_collapsed` and `adapter.soa_subtimelines_dropped`.

**This is NOT a corpus bug** — per the user, the corpus shape (one main + N sub-timelines) is the correct long-term USDM4 design. The adapter is a stop-gap *until USDM4 widens* (Finding 6 in `assembler_validation_findings.md`). Listed here for completeness; remove this section once USDM4 supports the list shape.

---

## How the adapter and this list relate

Each adapter transform exists because the corpus diverges from the USDM4 `AssemblerInput` schema. When a corpus extractor is fixed:

1. Confirm the new corpus output matches the schema-correct shape.
2. Remove the corresponding transform from `validate/corpus_adapter.py`.
3. Remove the matching field from `AdapterReport` and the `eval_corpus.py` `adapter_info` block.
4. Re-run the harness — `adapter.<field>` should be empty for the fixed protocols.
5. Strike the entry from this doc.

The adapter should shrink over time. When it has no transforms left, delete it.
