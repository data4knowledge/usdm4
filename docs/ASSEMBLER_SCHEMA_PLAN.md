# USDM4 Assembler Input Schema — Implementation Plan

## 1. Summary

The `usdm4.assembler.Assembler.execute()` method currently accepts an untyped `dict` as its input. This plan introduces Pydantic models that formally define the expected structure, providing validation, clear error messages, self-documenting code, and IDE support — while maintaining full backward compatibility with existing callers that pass raw dicts.

The schema validates input at the `Assembler.execute()` boundary. Once validated, the data is converted back to dicts via `model_dump()` and passed to sub-assemblers unchanged. Sub-assemblers and the Builder continue to work with dicts — this plan does not change their internal code.

The schema belongs in `usdm4` because the assembler lives here. Any package that calls the assembler — `usdm4_protocol`, `study_definitions_workbench`, or future consumers — should work against a single canonical schema definition owned by the same package that processes it.

---

## 2. Current State

### 2.1 How the Assembler Works Today

The `Assembler` class orchestrates seven specialized sub-assemblers in sequence:

```
execute(data: dict)
    ├── IdentificationAssembler.execute(data["identification"])
    ├── DocumentAssembler.execute(data["document"])
    ├── PopulationAssembler.execute(data["population"])
    ├── AmendmentsAssembler.execute(data["amendments"], document_assembler)
    ├── TimelineAssembler.execute(data["soa"])           # optional
    ├── StudyDesignAssembler.execute(data["study_design"], population, timeline)
    └── StudyAssembler.execute(data["study"], identification, study_design, document, population, amendments, timeline)
```

Each sub-assembler reads specific keys from its portion of the dict. There is no validation — if a key is misspelled, has the wrong type, or is missing an expected nested field, the failure surfaces deep inside the assembler as a `KeyError`, `TypeError`, or `AttributeError` with no context about what was expected.

### 2.2 Known Issues

- **Silent failures**: Missing optional fields often default to empty values without warning, making it hard to tell whether data was genuinely absent or was lost during extraction.
- **Opaque errors**: A `KeyError` on line 47 of `identification_assembler.py` tells you nothing about what the caller should have provided.
- **No discoverability**: The only way to understand the expected dict structure is to read all seven assembler source files and trace what they access.
- **Inconsistent handling**: Some assemblers use `.get()` with defaults, others use direct key access. Some check for empty strings, others don't. There's no consistent contract.

---

## 3. Proposed Design

### 3.1 Architecture

The schema acts as a **validation gate** at the assembler entry point:

```
Caller passes dict
    → AssemblerInput.model_validate(dict)     # Validate structure and types
    → model_dump() per domain                 # Convert back to dicts
    → Sub-assemblers receive dicts as before   # No internal changes
    → Builder receives dicts as before         # No internal changes
```

This keeps the change surface minimal: only `assembler.py` is modified. Sub-assemblers, `BaseAssembler`, the Builder, and all existing tests remain untouched.

### 3.2 New Module Location

```
src/usdm4/assembler/
├── assembler.py                    # Modified: validates input, then passes dicts to sub-assemblers
├── schema/                         # NEW: Pydantic schema models
│   ├── __init__.py                 # Re-exports AssemblerInput and all sub-schemas
│   ├── assembler_input.py          # Top-level AssemblerInput model
│   ├── identification_schema.py    # Identification domain
│   ├── document_schema.py          # Document domain
│   ├── population_schema.py        # Population domain
│   ├── amendments_schema.py        # Amendments domain
│   ├── study_design_schema.py      # Study design domain
│   ├── study_schema.py             # Study domain
│   └── timeline_schema.py          # SoA/Timeline domain
├── base_assembler.py               # Unchanged
├── identification_assembler.py     # Unchanged
├── document_assembler.py           # Unchanged
├── ...
```

### 3.3 Top-Level Schema

```python
# assembler/schema/assembler_input.py

from pydantic import BaseModel, ConfigDict
from usdm4.assembler.schema.identification_schema import IdentificationInput
from usdm4.assembler.schema.document_schema import DocumentInput
from usdm4.assembler.schema.population_schema import PopulationInput
from usdm4.assembler.schema.amendments_schema import AmendmentsInput
from usdm4.assembler.schema.study_design_schema import StudyDesignInput
from usdm4.assembler.schema.study_schema import StudyInput
from usdm4.assembler.schema.timeline_schema import TimelineInput

class AssemblerInput(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    identification: IdentificationInput
    document: DocumentInput
    population: PopulationInput
    study_design: StudyDesignInput
    study: StudyInput
    amendments: AmendmentsInput = AmendmentsInput()
    soa: TimelineInput | None = None
```

### 3.4 Domain Schemas

Each schema mirrors the structure currently consumed by the corresponding assembler.

#### Identification

```python
# assembler/schema/identification_schema.py

from pydantic import BaseModel, ConfigDict

class Titles(BaseModel):
    model_config = ConfigDict(strict=False)

    brief: str = ""
    official: str = ""
    public: str = ""
    scientific: str = ""
    acronym: str = ""

class Address(BaseModel):
    model_config = ConfigDict(strict=False)

    lines: list[str] = []
    city: str = ""
    district: str = ""
    state: str = ""
    postalCode: str = ""
    country: str = ""

class NonStandardOrganization(BaseModel):
    model_config = ConfigDict(strict=False)

    type: str                           # "registry", "regulator", "pharma", etc.
    role: str | None = None             # "co-sponsor", "manufacturer", etc.
    name: str = ""
    description: str = ""
    label: str = ""
    identifier: str = ""
    identifierScheme: str = ""
    legalAddress: Address = Address()

class IdentifierScope(BaseModel):
    model_config = ConfigDict(strict=False)

    standard: str | None = None         # "nct", "ema", "fda-ind", etc.
    non_standard: NonStandardOrganization | None = None

class StudyIdentifier(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str
    scope: IdentifierScope

class RoleOrganization(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str = ""
    address: Address | None = None

class MedicalExpert(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str | None = None
    reference: list[str] | None = None

class OtherIdentification(BaseModel):
    model_config = ConfigDict(strict=False)

    medical_expert: MedicalExpert | None = None
    sponsor_signatory: str | None = None
    compound_names: str | None = None
    compound_codes: str | None = None

class IdentificationInput(BaseModel):
    model_config = ConfigDict(strict=False)

    titles: Titles = Titles()
    identifiers: list[StudyIdentifier] = []
    roles: dict[str, RoleOrganization] = {}
    other: OtherIdentification = OtherIdentification()
```

#### Document

```python
# assembler/schema/document_schema.py

from pydantic import BaseModel, ConfigDict, field_validator

class DocumentMetadata(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    version: str = ""
    status: str = "Draft"               # Draft, Final, Approved, Obsolete, Pending Review
    template: str = ""
    version_date: str = ""              # ISO format: YYYY-MM-DD

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"draft", "final", "approved", "obsolete", "pending review"}
        if v.lower() not in valid:
            return "Draft"              # Safe default, matches current assembler behaviour
        return v

class Section(BaseModel):
    model_config = ConfigDict(strict=False)

    section_number: str
    section_title: str = ""
    text: str = ""

class DocumentInput(BaseModel):
    model_config = ConfigDict(strict=False)

    document: DocumentMetadata = DocumentMetadata()
    sections: list[Section] = []
```

#### Population

```python
# assembler/schema/population_schema.py

from pydantic import BaseModel, ConfigDict

class InclusionExclusion(BaseModel):
    model_config = ConfigDict(strict=False)

    inclusion: list[str] = []
    exclusion: list[str] = []

class PopulationInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    inclusion_exclusion: InclusionExclusion = InclusionExclusion()
```

#### Study Design

```python
# assembler/schema/study_design_schema.py

from pydantic import BaseModel, ConfigDict

class StudyDesignInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    rationale: str = ""
    trial_phase: str = ""               # "I", "II", "III", "IV", "1", "2", etc.
```

#### Study

```python
# assembler/schema/study_schema.py

from pydantic import BaseModel, ConfigDict

class StudyName(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str = ""
    acronym: str = ""
    compound: str = ""

class StudyInput(BaseModel):
    model_config = ConfigDict(strict=False)

    name: StudyName = StudyName()
    label: str = ""
    version: str = ""
    rationale: str = ""
    sponsor_approval_date: str = ""     # ISO format
    confidentiality: str = ""
    original_protocol: str = ""
```

#### Amendments

```python
# assembler/schema/amendments_schema.py

from pydantic import BaseModel, ConfigDict, Field

class AmendmentReasons(BaseModel):
    model_config = ConfigDict(strict=False)

    primary: str = ""
    secondary: str = ""

class SubstantialChange(BaseModel):
    model_config = ConfigDict(strict=False)

    substantial: bool = False
    reason: str = ""

class SafetyAndRights(BaseModel):
    model_config = ConfigDict(strict=False)

    safety: SubstantialChange = SubstantialChange()
    rights: SubstantialChange = SubstantialChange()

class ReliabilityAndRobustness(BaseModel):
    model_config = ConfigDict(strict=False)

    reliability: SubstantialChange = SubstantialChange()
    robustness: SubstantialChange = SubstantialChange()

class AmendmentImpact(BaseModel):
    model_config = ConfigDict(strict=False)

    safety_and_rights: SafetyAndRights = SafetyAndRights()
    reliability_and_robustness: ReliabilityAndRobustness = ReliabilityAndRobustness()

class AmendmentEnrollment(BaseModel):
    model_config = ConfigDict(strict=False)

    value: int | str = ""
    unit: str = ""

class AmendmentScope(BaseModel):
    model_config = ConfigDict(
        strict=False,
        populate_by_name=True,
    )

    global_: bool = Field(False, alias="global")
    unknown: list[str] = []
    countries: list[str] = []
    regions: list[str] = []
    sites: list[str] = []

class AmendmentChange(BaseModel):
    model_config = ConfigDict(strict=False)

    section: str = ""
    description: str = ""
    rationale: str = ""

class AmendmentsInput(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str = ""
    summary: str = ""
    reasons: AmendmentReasons = AmendmentReasons()
    impact: AmendmentImpact = AmendmentImpact()
    enrollment: AmendmentEnrollment = AmendmentEnrollment()
    scope: AmendmentScope = AmendmentScope()
    changes: list[AmendmentChange] = []
```

#### Timeline (SoA)

```python
# assembler/schema/timeline_schema.py

from pydantic import BaseModel, ConfigDict

class EpochItem(BaseModel):
    model_config = ConfigDict(strict=False)

    text: str = ""

class VisitItem(BaseModel):
    model_config = ConfigDict(strict=False)

    text: str = ""
    references: list[str] = []

class TimepointItem(BaseModel):
    model_config = ConfigDict(strict=False, extra="allow")

    text: str = ""
    value: int | float = 0
    unit: str = "day"
    index: int = 0

class WindowItem(BaseModel):
    model_config = ConfigDict(strict=False)

    before: int = 0
    after: int = 0
    unit: str = "day"

class ActivityVisit(BaseModel):
    model_config = ConfigDict(strict=False)

    index: int
    references: list[str] = []

class ActivityActions(BaseModel):
    model_config = ConfigDict(strict=False)

    bcs: list[str] = []

class ActivityItem(BaseModel):
    model_config = ConfigDict(strict=False, extra="allow")

    name: str = ""
    visits: list[ActivityVisit] = []
    children: list["ActivityItem"] = []
    actions: ActivityActions = ActivityActions()

class ConditionItem(BaseModel):
    model_config = ConfigDict(strict=False)

    reference: str = ""
    text: str = ""

class EpochsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[EpochItem] = []

class VisitsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[VisitItem] = []

class TimepointsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[TimepointItem] = []

class WindowsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[WindowItem] = []

class ActivitiesBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[ActivityItem] = []

class ConditionsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[ConditionItem] = []

class TimelineInput(BaseModel):
    model_config = ConfigDict(strict=False)

    epochs: EpochsBlock = EpochsBlock()
    visits: VisitsBlock = VisitsBlock()
    timepoints: TimepointsBlock = TimepointsBlock()
    windows: WindowsBlock = WindowsBlock()
    activities: ActivitiesBlock = ActivitiesBlock()
    conditions: ConditionsBlock = ConditionsBlock()
```

---

## 4. Integration with the Assembler

### 4.1 Validated `execute()` Method

The change to `assembler.py` validates input and then passes dicts to sub-assemblers as before:

```python
from pydantic import ValidationError
from usdm4.assembler.schema import AssemblerInput

class Assembler:

    def execute(self, data: AssemblerInput | dict) -> None:
        # Validate input
        if isinstance(data, dict):
            try:
                validated = AssemblerInput.model_validate(data)
            except ValidationError as e:
                location = KlassMethodLocation(self.MODULE, "execute")
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    msg = f"Schema validation: {field_path} — {error['msg']}"
                    self._errors.error(msg, location)
                return
        else:
            validated = data

        # Convert back to dicts for sub-assemblers
        dumped = validated.model_dump(by_alias=True)

        try:
            self._identification_assembler.execute(dumped["identification"])
            self._document_assembler.execute(dumped["document"])
            self._population_assembler.execute(dumped["population"])
            self._amendments_assembler.execute(
                dumped["amendments"], self._document_assembler
            )

            if dumped.get("soa") is not None:
                self._timeline_assembler.execute(dumped["soa"])

            self._study_design_assembler.execute(
                dumped["study_design"],
                self._population_assembler,
                self._timeline_assembler,
            )

            self._study_assembler.execute(
                dumped["study"],
                self._identification_assembler,
                self._study_design_assembler,
                self._document_assembler,
                self._population_assembler,
                self._amendments_assembler,
                self._timeline_assembler,
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during assembler", e, location)
```

Key points:
- **`model_dump(by_alias=True)`** ensures aliased fields like `global_` → `"global"` round-trip correctly back to the dict keys sub-assemblers expect.
- Sub-assemblers, `BaseAssembler`, and the Builder are completely untouched.
- Validation errors are reported through the existing `Errors` system and abort early — no point running assemblers on structurally invalid data.

### 4.2 What Does NOT Change

- **`BaseAssembler`**: Retains `execute(self, data: dict)` signature.
- **All seven sub-assemblers**: Continue to receive dicts and use `data["key"]` / `data.get("key")` access.
- **Builder**: Continues to receive dicts for object construction.
- **Existing tests**: All sub-assembler tests pass without modification since they still pass dicts.

---

## 5. Validation Modes

### 5.1 Lenient Mode (Default — Production)

The default `ConfigDict(strict=False)` allows Pydantic to coerce types where reasonable (e.g., `"123"` → `123` for an int field). Combined with default values on all optional fields, this means existing callers that pass raw dicts will continue to work. Validation catches structural problems (wrong nesting, completely wrong types) but is forgiving about edge cases.

### 5.2 Strict Mode (Development / Testing)

A `validate_strict()` class method on `AssemblerInput` enables stricter checking:

```python
class AssemblerInput(BaseModel):

    @classmethod
    def validate_strict(cls, data: dict) -> tuple["AssemblerInput", list[str]]:
        """Validate with warnings for empty required fields."""
        instance = cls.model_validate(data)
        warnings = []
        if not instance.identification.titles.official:
            warnings.append("identification.titles.official is empty")
        if not instance.document.document.version:
            warnings.append("document.document.version is empty")
        if not instance.study.version:
            warnings.append("study.version is empty")
        # ... additional checks
        return instance, warnings
```

This gives callers the option to catch quality issues during development without breaking production flows.

---

## 6. Implementation Approach

### Phase A: Define Schema Models (Non-Breaking)

Add the `assembler/schema/` module with all Pydantic models. No changes to existing code. The models can be imported and used by external callers immediately.

**Tasks:**

1. Add `pydantic>=2.0` to `requirements.txt`
2. Create `assembler/schema/` directory and `__init__.py`
3. Implement all seven domain schema files
4. Implement `AssemblerInput` top-level model
5. Add unit tests validating:
   - A minimal valid dict passes validation
   - Missing required fields produce clear errors
   - Type coercion works (string → int, etc.)
   - Extra keys are ignored (forward compatibility)
   - `model_dump(by_alias=True)` round-trips correctly (especially `AmendmentScope.global_` → `"global"`)
   - Each domain schema matches what its assembler currently reads

### Phase B: Integrate with Assembler (Backward-Compatible)

Modify `assembler.py` to validate input via the schema, then `model_dump()` back to dicts for sub-assemblers. Existing dict-passing callers continue to work. Sub-assemblers are not modified.

**Tasks:**

1. Update `Assembler.execute()` to validate input and convert to dicts
2. Add validation error → `Errors` integration
3. Verify all existing assembler tests still pass (they should — sub-assemblers are unchanged)
4. Add integration tests with real extraction output from M11, CPT, and Legacy

### Phase C: Public API

Export the schema from `usdm4` so external packages can import it directly:

```python
# In usdm4/__init__.py or a public API module
from usdm4.assembler.schema import AssemblerInput
from usdm4.assembler.schema import (
    IdentificationInput,
    DocumentInput,
    PopulationInput,
    StudyDesignInput,
    StudyInput,
    AmendmentsInput,
    TimelineInput,
)
```

This allows `usdm4_protocol` format handlers to construct typed `AssemblerInput` objects directly.

---

## 7. Testing Strategy

### 7.1 Schema Unit Tests

```
tests/usdm4/assembler/schema/
├── test_assembler_input.py         # Top-level validation
├── test_identification_schema.py   # Per-domain validation
├── test_document_schema.py
├── test_population_schema.py
├── test_amendments_schema.py
├── test_study_design_schema.py
├── test_study_schema.py
└── test_timeline_schema.py
```

Each test file covers:

- **Valid minimal input**: smallest dict that passes validation
- **Valid full input**: dict with all fields populated
- **Missing required fields**: confirm clear error messages
- **Type coercion**: string-to-int, bool-to-string, etc.
- **Extra keys ignored**: forward compatibility
- **Nested validation**: errors in deeply nested fields surface with full path
- **Default values**: confirm defaults match current assembler behaviour
- **Round-trip**: `dict → model_validate() → model_dump(by_alias=True)` preserves keys sub-assemblers expect

### 7.2 Regression Tests

Capture the actual dicts produced by the three existing extraction packages (M11, CPT, Legacy) and validate them against the schema. These become the golden regression set — if the schema rejects a dict that works today, the schema is wrong.

### 7.3 Existing Test Preservation

All existing sub-assembler tests must continue to pass without modification. Since sub-assemblers still receive dicts, this should be automatic. The schema is additive — it validates before the existing code runs, it does not replace the existing code.

---

## 8. Dependencies

**Pydantic v2 is a new dependency.** It must be added to `requirements.txt`:

```
pydantic>=2.0
```

The project's runtime dependencies (per `setup.py`) include `pydantic>=2.0`, `simple_error_log>=0.8.0`, `cdisc-rules-engine>=0.16.0`, `platformdirs>=3.0`, `python-dateutil`, `jsonschema`, `lxml`, `pyyaml`, and `requests`. Pydantic v2 is a well-established, widely-used library with no transitive dependency conflicts expected.

---

## 9. Relationship to usdm4_protocol

The `usdm4_protocol` package (being developed separately) consolidates three format-specific import packages into one. Its format handlers produce the assembler input dict and call `Assembler.execute()`.

Once this schema work is complete:

- Each format handler's `ExtractStudy` will construct and return an `AssemblerInput` instance (imported from `usdm4`) instead of a raw dict
- Validation happens at the natural boundary — right where unstructured document data becomes structured assembler input
- The `common.assemble.AssembleUSDM` wrapper in `usdm4_protocol` passes the typed `AssemblerInput` to the assembler rather than a dict
- The `usdm4_protocol` package does **not** define its own schema — it uses the one from `usdm4`

This is documented as a **prerequisite** in the `usdm4_protocol` implementation plan (Phase 0).

---

## 10. Implementation Order Summary

```
Phase A: Schema Models  ─────────────────────────────  [Non-breaking]
    ├── Add pydantic>=2.0 dependency
    ├── assembler/schema/ module
    ├── All seven domain schema files
    ├── AssemblerInput top-level model
    └── Unit tests

Phase B: Assembler Integration  ──────────────────────  [Backward-compatible]
    ├── execute() validates via schema, then model_dump() to dicts
    ├── Validation error → Errors integration
    ├── Existing sub-assembler tests still pass (unchanged)
    └── Integration tests with real extraction output

Phase C: Public API  ─────────────────────────────────  [After Phase B]
    └── Export schema types from usdm4 public API
```

Phase A can begin immediately. Phase B is the prerequisite for `usdm4_protocol` Phase 1.

---

## 11. Next Steps (post schema extension)

Branch `31-schema` extended `StudyDesignInput` and `PopulationInput` with arms / interventions / cells / elements and demographics / cohorts (with `arm_names`) / planned_enrollment. The schema changes are backward-compatible and inert — every new field has a default, so today's `AssemblerInput(**existing_data)` still validates. Existing assembler tests pass unchanged.

Two cross-reference invariants are now enforced at schema validation time (folded in from protocol_corpus Step 5 findings):

- **Cell -> element resolution** (on `StudyDesignInput`): every `CellInput.elements[*]` must appear in `StudyDesignInput.elements[*].name`. Captures the Step 5 invariant that elements carry load-bearing regimen information and cannot be synthesised.
- **Cohort -> arm subset** (on `AssemblerInput`): every `PopulationInput.cohorts[*].arm_names[*]` must appear in `StudyDesignInput.arms[*].name`. Cross-model check; lives on `AssemblerInput` because cohorts and arms are siblings.

The following follow-up work is deliberately **not** on `31-schema` and is tracked as a separate issue:

### 11.1 Encoder methods (new)

Add to `usdm4.assembler.encoder.Encoder` (mirrors the existing `phase()` lookup pattern):

- `intervention_model(str) -> Code` — `"Parallel" → C82639`, `"Crossover" → C82638`, `"Sequential" → C82637`, `"Factorial" → C82640`, `"Single Group" → C142568`. Default to Parallel with a warning if empty.
- `arm_type(str) -> Code` — `"Experimental" | "Placebo Comparator" | "Active Comparator" | "Sham Comparator" | "No Intervention" | "Other"`.
- `intervention_type(str) -> Code` — `"Drug" | "Device" | "Behavioral" | "Procedure" | "Biological"`.
- `intervention_role(str) -> Code` — `"Investigational Treatment" | "Placebo Comparator" | "Background Treatment"`.
- `age_unit(str) -> Code` — `"Years" | "Months" | "Weeks" | "Days"`.
- `route(str) -> Code` and `frequency(str) -> Code` — `AliasCode` lookup for intervention administration.

### 11.2 Assembler wiring

- `StudyDesignAssembler.execute` stops hardcoding `arms=[]`, `studyCells=[]`, `studyInterventions=[]`. Walks the new input lists instead. Two-pass build: create interventions first, then arms / elements with resolved intervention IDs via label-based refs. If `cells` is empty, derive a default arm × epoch grid.
- `PopulationAssembler.execute` replaces hardcoded `includesHealthySubjects=True` with `demographics.healthy_volunteers`; builds `plannedAge: Range(min=Quantity(age_min, unit), max=Quantity(age_max, unit))` when either endpoint is set; composes `plannedSex: list[Code]` from the sex literal (`"ALL"` → `[FEMALE, MALE]`; `"MALE"` → `[MALE]`; `"FEMALE"` → `[FEMALE]`); adds a new `_cohorts` pass emitting `StudyCohort` objects with their own characteristic wiring (each free-text string becomes a `Characteristic(SyntaxTemplate)`).

### 11.3 Tests

- Unit tests for each new encoder method (valid lookups, empty-string default, unknown-value warning).
- Integration tests for `StudyDesignAssembler` with multi-arm / multi-intervention payloads and cross-reference resolution.
- Integration tests for `PopulationAssembler` with demographics + cohorts payloads.
- Regression: existing assembler tests (all seven sub-assemblers) must continue to pass unchanged.
