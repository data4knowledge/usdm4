# USDM4 Assembler Wiring — Action Plan

Follow-up to the schema-only work on branch `31-schema` (issue #31, merged). This plan covers the encoder methods and assembler rewrites that were deliberately kept out of that PR. Read alongside `docs/ASSEMBLER_SCHEMA_PLAN.md §11` and the GitHub issue body at `usdm4_issue_assembler_wiring.md`.

## What's already landed

- `StudyDesignInput` carries `intervention_model`, `arms`, `interventions`, `cells`, `elements` (new nested `ArmInput`, `InterventionInput`, `CellInput`, `ElementInput`).
- `PopulationInput` carries `demographics`, `cohorts` (with `arm_names`), `planned_enrollment` (new nested `DemographicsInput`, `CohortInput`).
- Cross-reference invariants enforced at schema validation time: cell → element (on `StudyDesignInput`), cohort → arm (on `AssemblerInput`).
- 705 assembler tests still pass unchanged — the schema extensions are inert for existing callers.

## What's left

The assembler still hardcodes empty arms / cells / interventions / cohorts and a `True` healthy-subjects default. The work below converts those hardcodes into real consumers of the input fields.

## Branch + PR strategy

Three PRs, each small enough to review in one sitting. PR #1 is a clean refactor (no behaviour change at the assembler call-site); PRs #2 and #3 can land in parallel since they touch different assemblers.

```
main
 └─ 32-encoder-methods   ← PR #1 (Scope A)
     ├─ 33-sd-assembler  ← PR #2 (Scope B, StudyDesignAssembler)
     └─ 34-pop-assembler ← PR #3 (Scope B, PopulationAssembler)
```

Rebase each downstream branch onto `main` after the encoder PR lands.

---

## PR #1 — Encoder methods (branch `32-encoder-methods`)

**Files touched:** `src/usdm4/assembler/encoder.py`, `tests/usdm4/assembler/test_encoder.py`.

### Six new methods

Mirror the existing `phase()` / `document_status()` pattern: a class-level lookup table paired with a method that normalises input, looks up, emits an info log on hit and a warning on miss, and returns a CDISC `Code` or `AliasCode`.

| Method | Input strings | Returns | Notes |
|---|---|---|---|
| `intervention_model(str)` | Parallel / Crossover / Sequential / Factorial / Single Group | `Code` | `C82639 / C82638 / C82637 / C82640 / C142568`. Empty → Parallel + warning. |
| `arm_type(str)` | Experimental / Placebo Comparator / Active Comparator / Sham Comparator / No Intervention / Other | `Code` | Look up CDISC CT code for `Type of Arm`. |
| `intervention_type(str)` | Drug / Device / Behavioral / Procedure / Biological | `Code` | CDISC CT code for `Intervention Type`. |
| `intervention_role(str)` | Investigational Treatment / Placebo Comparator / Background Treatment | `Code` | CDISC CT code for `Intervention Role`. |
| `age_unit(str)` | Years / Months / Weeks / Days | `Code` | UCUM or CDISC age unit code. |
| `route(str)` / `frequency(str)` | e.g. Oral / Once daily | `AliasCode` | Free-text CDISC alias lookup, mirrors `phase()`'s AliasCode return. |

### Template for each lookup (adapted from `phase()`)

```python
INTERVENTION_MODEL_MAP = [
    (("PARALLEL",), {"code": "C82639", "decode": "Parallel Study"}),
    (("CROSSOVER",), {"code": "C82638", "decode": "Crossover Study"}),
    # ...
]

def intervention_model(self, text: str) -> Code:
    value = text.upper().strip() if text else ""
    for keys, entry in self.INTERVENTION_MODEL_MAP:
        if value in keys:
            code = self._builder.cdisc_code(entry["code"], entry["decode"])
            self._errors.info(
                f"Intervention model '{value}' decoded as '{entry['code']}'",
                location=KlassMethodLocation(self.MODULE, "intervention_model"),
            )
            return code
    # default: Parallel + warning
    default_code = self._builder.cdisc_code("C82639", "Parallel Study")
    self._errors.warning(
        f"Intervention model '{value}' not decoded; defaulting to Parallel",
        location=KlassMethodLocation(self.MODULE, "intervention_model"),
    )
    return default_code
```

Do not invent codes you don't know — look up the actual CDISC code for each enum label from `src/usdm4/ct/cdisc/` or the published CDISC CT package before filling in the maps. For `arm_type`, `intervention_type`, `intervention_role`, `age_unit`, `route`, `frequency` you will need to pull the real codes; leaving them as `"TODO"` will fail tests and downstream validation.

### Tests

One test per method, each covering: (a) one valid lookup returning the correct code+decode, (b) empty string returns default + records a warning, (c) unknown string returns default + records a warning. Match the pattern in `tests/usdm4/assembler/test_encoder.py` for `phase()`.

### Verify before merging

```bash
ruff format src/usdm4/assembler/encoder.py tests/usdm4/assembler/test_encoder.py
ruff check src/usdm4/assembler/encoder.py
pytest tests/usdm4/assembler/test_encoder.py -v
pytest tests/usdm4/assembler/ -v    # nothing should regress
```

### Acceptance

- All six methods landed with full test coverage.
- No changes to any assembler call site. Existing assembler tests pass unchanged.
- Ruff clean.

---

## PR #2 — `StudyDesignAssembler` wiring (branch `33-sd-assembler`)

**Files touched:** `src/usdm4/assembler/study_design_assembler.py`, `tests/usdm4/assembler/test_study_design_assembler.py`.

### Current call site (to replace)

Lines 86–113 hardcode `arms=[]`, `studyCells=[]`, `studyInterventions=[]`, and the intervention model code. That block becomes a two-pass build.

### Two-pass build recipe

1. **Pass 1 — build `StudyIntervention` objects.** One `StudyIntervention` per `data["interventions"][*]`. Resolve `type` via `encoder.intervention_type(i.type)`, `role` via `encoder.intervention_role(i.role)`. If the input carries `dose`/`route`/`frequency`, assemble a `list[Administration]` (one entry per intervention today — future work can split doses across administrations). Capture `{intervention.name: intervention.id}` in a local dict for the second pass.

2. **Pass 2a — build `StudyElement` objects.** One `StudyElement` per `data["elements"][*]`. Resolve `element.intervention_names` → `studyInterventionIds` using the name-to-id dict from pass 1. Capture `{element.name: element.id}`.

3. **Pass 2b — build `StudyArm` objects.** One `StudyArm` per `data["arms"][*]`. Resolve `type` via `encoder.arm_type(a.type)`. Use `label` as `description` fallback. `populationIds` stays `[]` for now (populated in PR #3 once `StudyCohort`s have IDs — or can be wired once both PRs merge). Capture `{arm.name: arm.id}`.

4. **Pass 2c — build `StudyCell` objects.** One `StudyCell` per `data["cells"][*]`. Resolve `cell.arm` → `armId`, `cell.epoch` → `epochId` (via `timeline_assembler.epoch_by_label()` — check the exact accessor name), `cell.elements[*]` → `elementIds` using the element-name dict. If `data["cells"]` is empty but `data["arms"]` is non-empty, synthesise a default grid: one cell per (arm, epoch) pair with empty `elementIds`. Keep all comparisons case-insensitive, matching `_add_epochs` convention.

5. **Intervention model.** Replace the hardcoded `cdisc_code("C82639", "Parallel Study")` with `self._encoder.intervention_model(data.get("intervention_model", ""))`.

6. **Plug into the `create(InterventionalStudyDesign, ...)` call.** `arms=arms_list`, `studyCells=cells_list`, `studyInterventions=interventions_list`. Pass the element list as well (check if `InterventionalStudyDesign` has a `studyElements` field — if not, it rides on cells via `elementIds` and the separate list may not be needed at the study_design level).

### Name-to-id dict pattern

The builder already generates an `id` for each created object. The cleanest way to capture them:

```python
interventions_by_name: dict[str, StudyIntervention] = {}
for i in data.get("interventions", []):
    obj = self._builder.create(StudyIntervention, {...})
    interventions_by_name[i["name"]] = obj
# Pass 2a uses interventions_by_name[name].id
```

### Backward compat

When `data.get("interventions", [])` is empty (legacy payloads), all four lists degrade to empty — identical to today's hardcoded behaviour. The existing test `test_study_design_assembler.py` should pass unchanged because its fixtures don't set the new fields.

### New integration tests

- **Multi-arm multi-intervention**: 2 arms, 2 interventions, 2 cells — verify `StudyDesign.arms` has length 2, `studyCells[0].armId` resolves to the correct arm, `studyInterventions[0].role.code.code` is the CDISC code for Investigational Treatment.
- **Cross-reference resolution**: arm with `intervention_names: ["DrugX"]` resolves correctly; arm with an unknown intervention name should have already been caught by the schema-level validator, so assembler-level error handling is belt-and-braces.
- **Empty cells synthesis**: arms present, `cells=[]`, epochs from timeline — assembler generates the full arm × epoch grid.

### Verify before merging

```bash
pytest tests/usdm4/assembler/test_study_design_assembler.py -v
pytest tests/usdm4/assembler/ -v    # full assembler suite
pytest tests/usdm4/ -v              # full repo
ruff format && ruff check
```

### Acceptance

- The four hardcoded empty lists are gone.
- Existing tests pass without modification.
- New integration tests land alongside.
- Assembling a real protocol_corpus draft (see §Smoke test below) produces a non-empty `arms` and `studyCells` block.

---

## PR #3 — `PopulationAssembler` wiring (branch `34-pop-assembler`)

**Files touched:** `src/usdm4/assembler/population_assembler.py`, `tests/usdm4/assembler/test_population_assembler.py`.

### Current call site (to replace)

Lines 79–96 hardcode `includesHealthySubjects=True` and emit no cohorts / plannedAge / plannedSex / plannedEnrollmentNumber. That becomes a proper demographics pass plus a cohorts pass.

### Demographics → `StudyDesignPopulation` fields

```python
demographics = data.get("demographics") or {}

includes_healthy = demographics.get("healthy_volunteers", True)

planned_sex: list[Code] = []
sex = demographics.get("sex", "ALL")
if sex in ("ALL", "FEMALE"):
    planned_sex.append(self._encoder.sex("FEMALE"))  # or builder lookup
if sex in ("ALL", "MALE"):
    planned_sex.append(self._encoder.sex("MALE"))

planned_age: Range | None = None
age_min = demographics.get("age_min")
age_max = demographics.get("age_max")
if age_min is not None or age_max is not None:
    unit = self._encoder.age_unit(demographics.get("age_unit", "Years"))
    planned_age = Range(
        min=Quantity(value=age_min, unit=unit) if age_min is not None else None,
        max=Quantity(value=age_max, unit=unit) if age_max is not None else None,
    )

planned_enrollment = data.get("planned_enrollment")
if planned_enrollment is None and data.get("cohorts"):
    planned_enrollment = sum(
        (c.get("planned_enrollment") or 0) for c in data["cohorts"]
    ) or None

planned_enrollment_qty = (
    Quantity(value=planned_enrollment, unit=None)
    if planned_enrollment is not None else None
)
```

For the `sex` code lookup, decide whether to add an `encoder.sex(str) -> Code` method in PR #1 or do the lookup inline here via `self._builder.cdisc_code(...)`. The encoder path is cleaner for consistency — suggest adding it to PR #1 as a seventh method.

### Cohorts pass

```python
cohort_objs: list[StudyCohort] = []
for c in data.get("cohorts", []):
    characteristics = [
        self._builder.create(Characteristic, {"text": ch})
        for ch in c.get("characteristics", [])
    ]
    # Cohort's own plannedEnrollmentNumber / plannedSex / plannedAge can be
    # per-cohort if the input carries them; otherwise inherit from the parent
    # demographics by leaving them None.
    cohort_obj = self._builder.create(StudyCohort, {
        "name": c["name"].upper().replace(" ", "-"),
        "label": c.get("label") or c["name"],
        "description": c.get("description") or "",
        "includesHealthySubjects": includes_healthy,
        "plannedEnrollmentNumber": (
            Quantity(value=c["planned_enrollment"], unit=None)
            if c.get("planned_enrollment") is not None else None
        ),
        "characteristics": characteristics,
    })
    cohort_objs.append(cohort_obj)
```

### Wire into the `StudyDesignPopulation` create

```python
params = {
    "name": data["label"].upper().replace(" ", "-"),
    "label": data["label"],
    "description": "The study population",
    "includesHealthySubjects": includes_healthy,
    "criterionIds": [x.id for x in self._ec_items],
    "plannedSex": planned_sex,
    "plannedAge": planned_age,
    "plannedEnrollmentNumber": planned_enrollment_qty,
    "cohorts": cohort_objs,
}
```

### Backward compat

When `demographics` is absent and `cohorts` is empty (legacy payload), the block degrades to `includesHealthySubjects=True` (the old default), empty `plannedSex`, `plannedAge=None`, empty `cohorts` — which is what `StudyDesignPopulation` already accepts. Existing `test_population_assembler.py` should pass unchanged.

### Cohort → arm wiring

`CohortInput.arm_names` carries the mapping, but `StudyCohort` has no back-reference to arms in the USDM API. The current convention is arm → cohort via `StudyArm.populationIds`. Wire it the other way:

```python
# After PR #2's arms + PR #3's cohorts exist, a separate pass in
# StudyDesignAssembler.execute populates arm.populationIds from
# cohort.arm_names:
for cohort in study_design_population.cohorts:
    for arm_name in _input_cohort_arm_names_for(cohort):
        arm = arms_by_name[arm_name]
        arm.populationIds.append(cohort.id)
```

This is the one cross-PR touch-point. Either land it in PR #3 (and accept a temporary lookup into the input dict) or defer to a PR #4 once both have merged. Simpler: do it in PR #3 as a small finalisation method, reading the input cohort list once more.

### New integration tests

- **Full demographics + two cohorts**: verify `plannedAge.min.value == 18`, `plannedAge.max.value == 65`, `plannedSex` has two codes, `cohorts` has length 2, `cohorts[0].characteristics[0].text == "treatment-naive"`.
- **Partial demographics (sex only)**: age range is `None`, `plannedSex` populated, `includesHealthySubjects=True` default holds.
- **Cohort → arm cross-wiring**: when PR #2 has landed, assembling an input with cohort `arm_names: ["A1"]` results in `arms[0].populationIds == [cohort.id]`.

### Verify before merging

```bash
pytest tests/usdm4/assembler/test_population_assembler.py -v
pytest tests/usdm4/assembler/ -v
pytest tests/usdm4/ -v
ruff format && ruff check
```

### Acceptance

- `includesHealthySubjects=True` hardcode is gone.
- `plannedAge`, `plannedSex`, `plannedEnrollmentNumber`, `cohorts` all wired.
- Existing tests pass without modification.
- Real protocol_corpus draft assembles end-to-end.

---

## Smoke test across both repos

After all three PRs merge, validate end-to-end with protocol_corpus's existing composite files. On the corpus repo:

```bash
cd ../protocol_corpus
python3 scripts/export_training_pairs.py --print-report
```

The error-pattern report should still show only the three known empty-field warnings for NCT04232553, plus zero warnings for NCT03637764. No new validation failures should appear; if they do, they represent real assembler output issues.

For a true end-to-end round-trip (input → USDM JSON → assembler object graph), write a small one-off script:

```python
# /tmp/round_trip.py
import yaml
from usdm4.assembler.schema import AssemblerInput
from usdm4.assembler.assembler import Assembler  # or the right entry point

data = yaml.safe_load(open(
    "protocols/NCT03637764/ground_truth.yaml"
))["validated"]["input"]
ai = AssemblerInput.model_validate(data)

# Assemble — exact API depends on the Assembler facade in usdm4.
result = Assembler().assemble(ai.model_dump())
print(result.study_design.arms)   # expect 8 StudyArm objects for NCT03637764
print(result.study_design.population.cohorts)  # expect 4 StudyCohorts
```

If that prints populated lists, the whole pipeline is green.

---

## Scope-creep traps to avoid

Resist expanding any of the three PRs:

- **No new schema fields.** Every shape needed is already on `StudyDesignInput` / `PopulationInput`. If a field is missing, add it in a follow-up PR, not this wave.
- **No refactor of unrelated assemblers.** `identification_assembler`, `document_assembler`, `amendments_assembler`, `timeline_assembler`, `study_assembler` are out of scope.
- **No new API classes.** Every `StudyArm` / `StudyIntervention` / `StudyCell` / `StudyElement` / `StudyCohort` / `Characteristic` already exists in `src/usdm4/api/`.
- **No encoder lookups you don't have real codes for.** If a CDISC code for an arm type isn't verified, note it in the PR description and stub it with a warning rather than inventing a code.

---

## TL;DR checklist for the other machine

- [ ] Pull `main` (includes the merged `31-schema` work).
- [ ] Branch `32-encoder-methods`. Implement encoder methods + tests. Open PR #1.
- [ ] Once PR #1 merges, rebase and branch `33-sd-assembler` for PR #2.
- [ ] In parallel, branch `34-pop-assembler` for PR #3.
- [ ] After both merge, run the corpus smoke test.
- [ ] Flip the §11 Next Steps section of `docs/ASSEMBLER_SCHEMA_PLAN.md` to "Done" with a findings paragraph, mirroring how `protocol_corpus/docs/pipeline.md` tracks step findings.

Estimated effort: PR #1 ≈ 2–3 h (tests are the bulk), PR #2 ≈ 3–4 h (two-pass build + 3 integration tests), PR #3 ≈ 2–3 h (more straightforward wiring). Total ≈ 7–10 h spread across three focused sessions.
