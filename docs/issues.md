# USDM4 — open issues

Problems that need solving. Open items only: when one is closed, delete its row and its
section (the session log in `next_steps.md` records how it was closed). `next_steps.md` says
which of these is being worked and in what order.

Numbered `N<n>`; numbers are never reused. A group of related issues shares one number with
sub-issues `N<n>.<m>`, `m` from 1; the group closes when its last sub-issue does. A GitHub issue, when one is raised, is noted on the
row.

| #  | Issue | Area |
|----|-------|------|
| N1 | Placeholder procedure code `12345` in every assembled USDM | assembler |
| N2 | Minimum assembled study fails CORE and d4k rules | assembler |
| N3 | Small timeline output defects | assembler |
| N4 | Amendment enrollment geographic scope untested | assembler |
| N5 | `test_example_2` xfail — 339 findings on `example_2.json` | rules / fixtures |
| N6 | d4k–CORE divergences with no verdict (DDF00031, 00045, 00087, 00088) | rules |
| N7 | Upstream CRE bugs not yet raised with the CRE team | CORE |
| N8 | CORE engine output always suppressed | CORE |
| N9 | `udp_prism` as a validation set — keep or retire | validation |
| N10 | ~87 hand-authored rule tests have no behavioural fixture | rules / tests |
| N11 | Empty population label fails assembly | assembler |
| N12 | Timings in a unit other than the anchor's are not converted | assembler |
| N13 | Convert is USDM3 → USDM4 but nothing says or checks so | convert |
| N14 | Convert fails on more than one study design and emits duplicate ids | convert |
| N15 | CT and BC libraries read a different API-key variable | ct / bc |
| N16 | CT refresh deletes the cache before fetching | tools / ct |
| N17 | Typos in assembler lookup keys and names | assembler |
| N18 | Empty extensions always emitted | assembler |
| N19 | `errors.exception` called without the exception | assembler |
| N20 | Error messages print a literal `{...}` | package / data_store |
| N21 | BC library: `valid` inverted, CT class stored not instance | bc |
| N22 | Rule loader silently drops rules that fail to load | rules |
| N23 | CORE reports a file valid when no rules ran | CORE |
| N24 | Structural tidy-up (N24.1–N24.11, below) | package |
| N24.1 | Tests import the package as both `src.usdm4` and `usdm4` | tests |
| N24.2 | Assembler validates typed input then works on dicts | assembler |
| N24.3 | Exception handling layered several deep | assembler |
| N24.4 | CT code tables scattered; `m11_phase_aliases` in the wrong package | assembler / ct |
| N24.5 | `encoder.py` is a lookup module and a parsing module in one | assembler |
| N24.6 | Rule library copy-paste; leftover generator markers; delegated rules report success | rules |
| N24.7 | Data store loses duplicate ids; rules read its private fields | data_store / rules |
| N24.8 | CORE wrapper mutates global and installed state, duplicates the cache manager | CORE |
| N24.9 | `StudyVersion` carries a query layer | api |
| N24.10 | The two validation result types are not parallel | rules / CORE |
| N24.11 | Packaging, stray file, coverage-gate artefacts | package |
| N25 | Arms name interventions but no epochs exist, so no cells and the arm → intervention link is lost | assembler |
| N26 | A required string attribute accepts `""` (no minimum length): `StudyVersion.versionIdentifier` empty passes | schema / rules |

---

## N1 — Placeholder procedure code `12345`

`src/usdm4/assembler/timeline/build.py` (~line 390) builds each activity's `Procedure` with
`Code(code="12345", codeSystem="LOINC", codeSystemVersion="1")`. Every assembled USDM carries a
made-up code presented as real LOINC. Either a real code comes from the input, or the
`Procedure` is not built without one.

## N2 — Minimum assembled study fails CORE and d4k rules

The minimum `AssemblerInput` fixture (`tests/usdm4/integration/conftest.py`) does not assemble
into a conformant study. Both engines' integration tests are regression detectors on today's
failures, not conformance tests.

**d4k.** `tests/usdm4/integration/test_assembler_to_d4k.py` pins ceilings — at most 12 failing
rules, 15 findings, 0 rule exceptions — and fails if any is exceeded. The strict "all rules
pass" test is `xfail(strict=False)`. Which rules fail is not recorded; list them before working
this. As they clear, lower the ceilings, then drop them and the xfail.

**CORE.** `tests/usdm4/integration/test_assembler_to_core.py` pins the failing rule ids as
`_KNOWN_FAILING_RULES`: CORE-000815, 000938, 000973, 001016, 001036, 001054, 001065, 001076,
001077. The test is a regression detector — it passes while the set is unchanged. The ones
with a known cause:

- **CORE-000938** (DDF00126, schema cardinality) — `StudyAmendment.changes`,
  `InterventionalStudyDesign.arms` and `.studyCells` emitted as `[]` where the schema needs at
  least one.
- **CORE-000973** — exactly one `StudyRole(code="sponsor")`. No code path creates it;
  `IdentificationAssembler` wires the sponsor through the identifier scope only. Smallest fix:
  `_create_organization` emits a sponsor `StudyRole` when the org's role is `sponsor`.
- **CORE-001016** — `ScheduleTimeline.plannedDuration` on the main timeline. `build.py`
  (~line 811) sets it `None`; the input has no duration.
- **CORE-001036** — at least one primary endpoint. `StudyDesignInput` has no objectives or
  endpoints; needs schema and an assembler.

The rest are not decoded. A 2026-05-02 bisection tried three fixture additions (sponsor
identifier, demographics with age range, activity BCs); all three cleared some rules and
introduced more, so all were reverted. The BC variant produced 8 CORE-001013 name-uniqueness
errors — look at that before any fixture references BCs.

## N3 — Small timeline output defects

- `≥ 1 weeks` — `gate_condition` and `render_delay` pluralise without checking the value.
- Instances in a second period or a copied timeline are named by de-duplication (`D1-2`,
  `D-1-2`, `ED-2`), not by period or timeline.

## N4 — Amendment enrollment geographic scope untested

`AmendmentsAssembler._enrollment_geographic_scope` (2026-06-18, branch
`39-further-ich-m11-updates`) derives the enrollment scope from the amendment scope. No unit
tests exist and the `udp_prism` end-to-end check (TCBCPT_03 renders "Locally") was never
confirmed. Tests needed: global, country in `countries`, country in `unknown`, region, site
fallback. Known gap: a site- or cohort-scoped amendment has no C207412 code, so it falls back
to Global with a warning.

## N5 — `test_example_2` xfail

`tests/usdm4/test_package.py::test_example_2` is `xfail(strict=True)`: the V4 rule library
fires 339 findings on `example_2.json` across ~30 rules. When the file produces none, the
xfail turns XPASS and the run fails — the signal to remove the marker.

- **Fixture drift** — DDF00051 (timing type labels, not decodes), DDF00157, DDF00199, DDF00218
  (invalid CT codes/decodes), DDF00075 (activities with no leaf references). Fix the fixture,
  or for DDF00075 reconsider the rule's strictness.
- **Rule interpretation** — DDF00010 checks `(instanceType, name)` model-wide, matching CORE's
  JSONata; the rule text says "same parent class", and `SubjectEnrollment` names repeat across
  amendments. The mirror-CORE policy (`cre_issues.md`) says keep it; the question is whether
  this is a case for a spec change.
- **The rest** — the xfail reason lists them. The list is a pre-rewrite snapshot; re-run and
  triage per finding before working it.

## N6 — d4k–CORE divergences with no verdict

From the CRE 0.16.0 corpus baseline (`validate/corpus_cre_0_16/engine_diff.md`); rows and
counts in `cre_issues.md` § *Divergence index*.

- **DDF00031** (d4k over, 213 files) — timing FK consistency. Not categorised.
- **DDF00045** (d4k over, 25 files) — the V3 rule kept alongside V4 DDF00194; CORE runs only
  DDF00194. Retire the V3 duplicate, or show the over-fire is a real finding DDF00194 misses.
- **DDF00087 / DDF00088** (d4k over, 210 / 177 files) — first-chain-head selection. Needs a
  design decision.

When one is decided, move its row in `cre_issues.md` to the matching category and delete it
here.

## N7 — Upstream CRE bugs not yet raised

`cre_issues.md` issues 1–10 each carry a *Suggested fix* for the CRE team. None is recorded as
raised. Issue 5 (execution errors mixed with findings) is no longer a cost to us: since #54
`_classify_errors` follows the engine's own `executionStatus`, with the string set kept only as
a fallback for items that carry none. Ask for the rest anyway; each still needs a workaround here.

## N8 — CORE engine output always suppressed

`core_validator.py` `_run_validation` redirects stdout/stderr to a `StringIO` unconditionally.
During the CRE 0.16.0 upgrade this hid the engine's own tracebacks. Make it switchable (env var
or flag) for diagnostic runs.

## N9 — `udp_prism` as a validation set

A plan to run the rules over 21 `udp_prism` protocols predates the 234-protocol corpus baseline,
which already covers what they exercise. Decide: give it its own frozen baseline under
`validate/`, or drop the plan.

## N10 — Hand-authored rule tests without fixtures

About 87 hand-authored rule tests have their positive/negative fixture cases marked
`@pytest.mark.skip` (metadata-only coverage). A minimal JSON per rule makes each a behavioural
test — roughly 15 minutes a pair. Start with the structurally unusual ones: DDF00189 (mutex),
DDF00196 (1:1 dict of sets), DDF00124 (regex ref), DDF00010 (model-wide uniqueness), DDF00161
(preorder walk).

## N11 — Empty population label fails assembly

The population input (`src/usdm4/assembler/schema/`) defaults `label` to `""`.
`PopulationAssembler` (`population_assembler.py` ~line 92) builds the `StudyDesignPopulation`
`name` as `data["label"].upper()…`, and the API model requires `name` to have at least one
character. An input with no population label therefore fails Pydantic validation instead of
assembling with a warning. Seen on the 19 CORP* corpus protocols (2026-05-01). Decide: require
a label in the input schema, or have the assembler supply a name and warn.

## N12 — Timings in a unit other than the anchor's are not converted

The timeline spec said a column timed in a different unit from the anchor is converted where
exact (weeks to days, hours to minutes). It never was: `plan.py` (`_interval`,
`interval_from_anchor`) warns and uses the column's printed number as its distance from the anchor, ignoring where
the anchor sits and the crossing-zero rule. `_convert` exists and is used only for cycle
lengths.
Spec: `docs/spec/timeline_assembler.md` R4.6.

## N13 — Convert is USDM3 → USDM4 but nothing says or checks so

`Convert.convert` (`src/usdm4/convert/convert.py`) rewrites a USDM3 study into USDM4 shape
and stamps `usdmVersion` with the v4 model version. It never reads the input's
`usdmVersion`, so any file is converted as if it were USDM3. The README calls it "transform
USDM data structures between formats". The test inputs (`tests/usdm4/test_files/convert/`)
say `usdmVersion` `2.11.0` in two files (a pre-release number for what became USDM3) and
`3.0.0` in two. Needed: say it is USDM3 → USDM4 (README, docstring), check the input version
(accept 3.x and 2.11, warn otherwise), and label the fixtures `3.0.0`.

## N14 — Convert fails on more than one study design and emits duplicate ids

`src/usdm4/convert/convert.py`:

- The second design loop runs `version.pop("studyPhase")` and `version.pop("studyType")` per
  design (~line 156). The second design raises `KeyError`.
- `version["eligibilityCriterionItems"] = ec_items` (~line 146) takes the last design's items,
  not the accumulated `version_ec_items`.
- Fixed ids: `documentType` and `type` both get `DocumentTypeCode_1` (lines 28, 36) — a
  duplicate id in every converted study. Also `LangaugeCode_1` (typo, line 20) and
  `Population_Empty` (line 126), which repeats if more than one design has an empty population.
- `convert` mutates the caller's dict.

No test has two designs. Needed: a two-design fixture, the fixes above, ids from `IdManager`.
Related: N13.

## N15 — CT and BC libraries read a different API-key variable

`ct/cdisc/library_api.py:14` and `bc/cdisc/library_api.py:16` read `CDISC_API_KEY`. `core/`,
`tools/prepare_core_cache.py` and `CLAUDE.md` use `CDISC_LIBRARY_API_KEY`. One key in
`.development_env` cannot serve both. Settle on `CDISC_LIBRARY_API_KEY`; accept the old name
with a warning.

## N16 — CT refresh deletes the cache before fetching

`tools/ct_cache.py` calls `library._cache.delete()` then `library.load()`. If a fetch fails,
`LibraryAPI.code_list` returns `None` and `_get_usdm_ct` (`ct/cdisc/library.py` ~line 328)
fails on `response["conceptId"]` — the committed CT cache is gone and the package has no CT.
`tools/bc_cache.py` has the same shape. Fetch into a temporary file; replace only on success.

## N17 — Typos in assembler lookup keys and names

- ~~`ROLE_CODES` key `"project maanger"`~~ — fixed in GitHub 83 (2026-10-07), with the
  `"adjudication Committee"` key case and the trailing spaces in two decodes.
- `"SPONSOR-APPORVAL-DATE"` (`study_assembler.py:270`) — the `GovernanceDate` name in every
  assembled study with an approval date.

## N18 — Empty extensions always emitted

`StudyInput` (`assembler/schema/study_schema.py:19-21`) defaults `sponsor_approval_date`,
`confidentiality` and `original_protocol` to `""`. `Assembler.execute` dumps the model to a dict,
so the `"key" in data` guards in `StudyAssembler.execute` (`study_assembler.py` ~lines 115-123)
are always true. Every assembled study gets a confidentiality extension with `valueString: ""`,
an original-protocol extension, and a sponsor-approval extension with `""` whenever no approval
date was parsed. Test on value, not presence.

## N19 — `errors.exception` called without the exception

`identification_assembler.py` ~lines 461-469 and ~509-511 call
`self._errors.exception(message, KlassMethodLocation(...))`. The signature is
`exception(message, e, location=None)`: the location lands in the exception slot and the
recorded location is `None`. There is no exception at those points — use `error()`.

## N20 — Error messages print a literal `{...}`

Missing `f` prefix:

- `USDM4.load` (`src/usdm4/__init__.py` ~line 175): `"Failed to load file '{filepath}' …"`.
  Also `loadd` records its location as `"from_dict"`.
- `DataStore` (`data_store/data_store.py:90`): `"Duplicate id '{id}' detected"`.

## N21 — BC library: `valid` inverted, CT class stored not instance

- `bc/cdisc/library_api.py:38-39` — `valid()` returns `self._errors.error_count()`: truthy when
  there are errors.
- `bc/cdisc/library.py:12` — `self._ct_library = CtLibrary` stores the class, not the
  `ct_library` argument.

## N22 — Rule loader silently drops rules that fail to load

`RulesValidationEngine._load_rules` (`src/usdm4/rules/engine.py` ~lines 44-76) wraps each rule
file in `except Exception: continue`. A rule file with an import or syntax error is left out of
the run and nothing records it — the results look the same as if the rule were never in the
library. `tests/usdm4/rules/test_engine.py::test_load_rules_skips_files_with_syntax_error`
asserts this silence.

In `_execute_rules` (~lines 78-93), `rule = rule_class()` sits inside the `try`. If a
constructor raises, the `except` reports `rule._rule` — the previous iteration's rule, or
`UnboundLocalError` on the first. The glob is unsorted, so run order is filesystem order.

Needed: a load or construction failure recorded as an `EXCEPTION` outcome keyed by file name;
construct outside the `try` that reports; sort the glob; a test that the loaded rule count
equals the number of `rule_ddf*.py` files.

## N23 — CORE reports a file valid when no rules ran

`CoreValidator` (`src/usdm4/core/core_validator.py`): `_load_rules` (~line 545) and the CT
package load (~line 452) catch every exception and return `[]`. `validate` then returns early
when there are no rules (~line 373). `CoreValidationResult.is_valid` is `len(findings) == 0`,
so the caller gets `is_valid=True` with `rules_executed=0` — a failed download or a bad cache
reads as a clean file.

Needed: record the failure as an execution error; `is_valid` false when no rules ran.

## N24 — Structural tidy-up

From a structure and design review on 2026-09-27. The design holds; the problems are layers of
guards, copies and workarounds added session by session. Sub-issues are closed one at a time
(delete the row and section); N24 closes when the last one does. Order is set in
`next_steps.md`. Leave alone: the `timeline/` split, `Naming`, `IdManager`, `TagResolver`,
`FileCache`, the `RuleTemplate` contract and `RuleOutcome`.

### N24.1 — Tests import the package as both `src.usdm4` and `usdm4`

65 test files import `src.usdm4`, the rest `usdm4`; some files mix both. `pytest.ini`
`pythonpath = .` allows it. In one run every class exists twice: `patch("src.usdm4.X")` does
not reach code that imported `usdm4.X`, and `isinstance`/`issubclass` depend on which copy
(`test_engine.py` has a comment working round it). Some tests may not test what they appear
to. Needed: editable install, every import and patch target `usdm4`, `pythonpath = src`,
`--cov=usdm4`. First, because every other N24 item needs tests that can be trusted.

### N24.2 — Assembler validates typed input then works on dicts

`Assembler.execute` (`assembler.py` ~lines 92-95) validates `AssemblerInput` then
`model_dump()`s it; the sub-assemblers index raw dicts (~290 `["key"]` / `.get()` uses).
The schema gives no type safety past the entry point, and guards like N18's look meaningful but
are not. Needed: pass the typed sub-models into each `execute()`. While there: break up the
largest methods (`IdentificationAssembler.execute` ~233 lines, `StudyAssembler.execute` ~178,
`StudyDesignAssembler` ~1,000 lines — products, ingredients and administrations could be their
own assembler); replace assemblers passing other assemblers into `execute` with a small
results object each step returns.

### N24.3 — Exception handling layered several deep

47 `except Exception` blocks across 11 assembler files. `Builder.create` already catches, logs
and returns `None`; callers wrap it again per item, then per assembler, then in
`Assembler.execute`. Some handlers cannot fire (`StudyAssembler._create_extension`), and a
`None` from `create` can be appended to a list. Messages are copy-pasted
(`timeline_assembler.py` ~line 88 says "study design"). Needed: catch once per item, check
`create()` for `None`.

### N24.4 — CT code tables scattered; `m11_phase_aliases` in the wrong package

Hard-coded C-codes: ~112 in `encoder.py`, ~45 in `identification_assembler.py`, more in
`m11_phase_aliases.py`, `document_assembler.py`, `study_assembler.py` (Global `C68846` written
out three times). `Builder.cdisc_code` ignores `decode`, so every decode in these tables is dead
data. `ROLE_ORGS` and `ROLE_CODES` use different keys (`co_sponsor` / `co-sponsor`).
`m11_phase_aliases.py` sits in `assembler/` but `rules/library/rule_ddf00229.py` imports it, so
`rules` depends on `assembler`; `Encoder.PHASE_MAP` repeats its strings. Needed: one
label → code module under `ct/`, keyed by codelist, no decodes; move `m11_phase_aliases` there.

### N24.5 — `encoder.py` is a lookup module and a parsing module in one

813 lines: ~360 of lookup tables, the rest CT lookup plus `to_date`, `iso8601_duration`,
`to_boolean`. `MODULE` names a path that does not exist (`usdm4.encoder.encoder.Encoder`).
Each assembler builds its own `Encoder`. Needed: split into the CT lookup (N24.4) and a small
parsing module. `_create_date` is duplicated in `document_assembler.py` and
`study_assembler.py` — one shared helper.

### N24.6 — Rule library copy-paste; leftover generator markers; delegated rules report success

About 86 of 213 rule files fall into 13 groups with identical `validate` bodies (41 one-line CT
checks, 10 "reference must resolve", 8 "values distinct", 6 "required"). `_is_specified` is
copied into 6 files and the copies disagree on whitespace. 10 files still say
`GENERATED — … please review` and 122 say `MANUAL: do not regenerate`; there is no generator.
DDF00081, 00125 and 00126 `return True` and report SUCCESS. Needed: a few parameterised base
classes (CT, reference, distinct, required); shared helpers into `primitives.py`, unused
primitives removed; review and strip the markers; a "delegated" outcome instead of success.

### N24.7 — Data store loses duplicate ids; rules read its private fields

`DataStore` (`data_store.py` ~lines 88-94) overwrites an earlier instance with the same id; the
`DUP_ID` error it records is never read. DDF00083 re-walks the raw JSON to find duplicates;
four rules read `_ids` / `_parent` directly (00010, 00260, 00027, 00044). Needed: keep every
instance; expose `duplicate_ids()`, `parent_of()`, `all_instances()`; the engine reports the
store's errors.

### N24.8 — CORE wrapper mutates global and installed state, duplicates the cache manager

`core_validator.py` changes the working directory, `sys.stdout`/`sys.stderr`, logging and
`os.environ`, and copies files into the installed `cdisc_rules_engine` package (skipped if
present, so `--force` never reaches them; fails on a read-only install). It downloads rules and
CT itself, duplicating `core_cache_manager.py`. Docstrings advertise async execution that does
not exist. Cache resources come from GitHub `main`, unpinned. Needed: the validator reads only
from the cache manager; side effects in one context manager, or the engine in a subprocess.
Related: N8, N23.

### N24.9 — `StudyVersion` carries a query layer

`api/study_version.py`: ~77 methods on a data class, ~20 hard-coded NCI codes, return types
wrong on several (`*_identifier_text` annotated `StudyIdentifier`, return `str`;
`official_title` etc. annotated `StudyIdentifier`, return `StudyTitle`).
`_identifier_scoped_by_org` raises `KeyError` on a dangling organisation reference. Needed: a
query module with named constants; thin delegates on `StudyVersion` for downstream callers.

### N24.10 — The two validation result types are not parallel

`results.py` says `RulesValidationResults` and `CoreValidationResult` are parallel. They are
not: `is_valid` means "every rule succeeded" in one and "no findings" in the other; `to_dict()`
returns a list in one and a summary dict in the other; `RulesValidationResults.to_errors()`
leaves out exceptions. `validate/` rebuilds serialisation in three places. Needed: one shared
interface; move `validate/d4k.py`'s serialisation into `results.py`.

### N24.11 — Packaging, stray file, coverage-gate artefacts

- `setup.py`: no `python_requires` (the engine needs 3.12+); `python-dateutil` pinned exactly;
  `typing_extensions` imported but not declared; `tests_require` deprecated;
  `requirements.txt` repeats every runtime dependency.
- `src/usdm4/minimum/test_write_2` — empty file from an old test run. Delete.
- `--cov-fail-under=100` with no `pragma: no cover`: 7 `*_branches.py` test files and ~21
  test docstrings citing source line numbers that go stale on every edit; deprecated methods
  (`USDM4.from_json`, `StudyVersion.sponsor`) kept alive by their tests. Needed: allow
  `pragma: no cover` on defensive branches, drop the line-number docstrings, remove deprecated
  methods with their tests.
- Tests use paths relative to the working directory; ~20 files each define their own
  `"src/usdm4"` root helper. One `conftest` fixture based on `__file__`.

## N25 — Arms name interventions but no epochs exist: the arm → intervention link is lost

Raised 2026-10-02 from udp_prism N8. Agreed approach (Dave, 2026-10-02): synthesise one
Treatment Epoch. Not pretty, keeps the round trip going. Built 2026-10-02 on `main`
(`study_design_assembler._synthesised_epochs`, `EPP_EXT_URL` in `extensions_d4k.py`, tests
in `test_study_design_assembler_arm_interventions.py`); tests pass (Dave); udp_prism run
confirms. Open until merged. Not yet run: `validate/run.sh` on a step-3 file.

**What happens.** USDM links an arm to its interventions only through
`StudyCell.armId` → `elementIds` → `StudyElement.studyInterventionIds`, and
`StudyCell.epochId` is required. `StudyDesignAssembler` gets epochs only from the timeline
build. With arms that carry `intervention_names` and no SoA input, `_build_cells` builds
nothing (the grid needs epochs), and `_attach_arm_element` creates `EL-<ARM>` with the right
interventions but on no cell. Nothing in the output ties the element to the arm except its
name. Every arm reads as having no intervention on the DDF-RA path.

Who hits it: the PRISM3 FHIR import (the message carries arm → product, no epochs, no SoA),
so every round-tripped study; and any extraction with arms but no SoA (udp_prism step 1 for
IGBJ, LZZT, IG_Example_CPT).

**Change (spec, for approval before code).** In `StudyDesignAssembler.execute`, before pass
2c:

1. Trigger: the timeline build produced no epochs, the input has no `cells` and no
   `elements`, and at least one arm's `intervention_names` resolves to an intervention.
2. Build one `StudyEpoch`: name and label `Treatment Epoch`, type C101526 Treatment Epoch
   (`klass_and_attribute_value(StudyEpoch, "type", "Treatment Epoch")`, as `timeline/build.py`
   does), no previous / next, and a new d4k extension `017` (epoch provenance,
   `extensions_d4k.py`) with `valueString` `synthesised: no epochs supplied; holds the arm →
   intervention link`.
3. Pass it to `_build_cells` and to the design's `epochs`. The existing grid then gives one
   cell per arm, and `_attach_arm_element` puts `EL-<ARM>` on it. No other code changes.

Not triggered with explicit elements: that mode only checks reachability, and an
element-bearing input with no epochs is a different defect.

**The extension is the only marker** (kept by decision, Dave, 2026-10-02). It carries one
fact, that the epoch was synthesised, and nothing reads it today. Rejected: inferring it
(an epoch no scheduled activity instance references — holds only while usdm4 is the
producer) and the `description` field (visible, not testable). The timeline build types every epoch Treatment Epoch
already, so the type tells a consumer nothing. Anything that counts or exports epochs must
check `017`, and any future epoch or SoA export (usdm4_fhir) must skip an epoch carrying it,
or the synthesised epoch gets laundered as stated (compare 015 and udp_prism N9).

**Tests.** No arms → no epoch. Arms without interventions → no epoch. Arms with
interventions and SoA epochs → unchanged. Arms with interventions, no epochs → one epoch with
`017`, one cell per arm, `EL-<ARM>` on it, interventions reachable. Explicit elements → no
epoch. Run d4k and CORE on one udp_prism step-3 file afterwards: a lone epoch with no
scheduled activity instances fires nothing in the d4k library (DDF00021–24, 27, 69, 72, 80,
88 checked); CORE not checked.

**The model half.** `StudyArm` has no direct intervention reference, so a source that states
arm → intervention and no periods (the M11 FHIR IG) cannot be held without an epoch. An arm
extension carrying intervention ids was considered and rejected as code: d4k-only, so other
USDM consumers still see no link, and a second place for the same fact. Kept as the shape of
a DDF proposal (`StudyArm.studyInterventionIds`, meaning every treatment period), not built.


## N26 — A required string attribute accepts `""`: `versionIdentifier` empty passes

Found 2026-10-06 in udp_prism (its N43). ICH M11 makes Version Number optional; a protocol
that prints none (ICH_M11 1776 / 2060, both amendments) has no version to give.
usdm4_protocol stores `StudyVersion.versionIdentifier = ""` (and the protocol document
version `""`) rather than invent one. usdm4_fhir's export wrote `"1"` in its place, so the
round trip changed the value; udp_prism chose to keep the empty value end to end (Dave,
2026-10-06), which needs this USDM behaviour to stay as it is today.

**The point.** In the USDM 4 schema (`rules/library/schema/usdm_v4-0-0.json`)
`versionIdentifier` is required, typed `string`, with no `minLength`, so `""` is valid.
The same holds for `StudyDefinitionDocumentVersion.version`. A required identifier that may
be empty is against the spirit of USDM (Dave): it should be `minLength: 1`, and a source
that does not state a version should say so in a recognisable way rather than with an
empty string.

**No rule catches it.** d4k: nothing on `versionIdentifier`; DDF00125 / DDF00126
(required properties present / "required properties have at least one value") are
delegated to DDF00082's schema validation (`rule_ddf00126.py`, a no-op on purpose), and the
schema has no `minLength`, so `""` passes. CORE: DDF00126 is CORE-000938, the same
schema-driven cardinality check, reported only for empty arrays so far; no CORE rule seen in
the corpus results checks string emptiness. The full CORE catalogue was not read (the CORE
cache is local), so a rule elsewhere is not ruled out.

**Not a usdm4 code change on its own.** The schema is the DDF's; `usdm4` follows it. Options:
raise with DDF (`minLength: 1` on required identifier strings, or a rule that required
strings are non-empty), and decide what a producer writes when the source has no version.
Until then usdm4 accepts `""` and udp_prism keeps it.
