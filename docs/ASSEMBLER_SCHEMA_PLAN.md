# USDM4 Assembler Input Schema — Implementation Plan

## 1. Summary

The `usdm4.assembler.Assembler.execute()` method currently accepts an untyped `dict` as its input. This plan introduces Pydantic models that formally define the expected structure, providing validation, clear error messages, self-documenting code, and IDE support — while maintaining full backward compatibility with existing callers that pass raw dicts.

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

### 3.1 New Module Location

```
src/usdm4/assembler/
├── assembler.py                    # Modified: accepts AssemblerInput or dict
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
├── base_assembler.py
├── identification_assembler.py
├── document_assembler.py
├── ...
```

### 3.2 Top-Level Schema

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

### 3.3 Domain Schemas

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
    description: str = ""
    sponsor_approval_date: str = ""     # ISO format
    confidentiality: str = ""
    original_protocol: bool | str = ""
```

#### Amendments

```python
# assembler/schema/amendments_schema.py

from pydantic import BaseModel, ConfigDict

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
    model_config = ConfigDict(strict=False)

    global_: bool = False               # Note: aliased from "global" in dict
    unknown: list[str] = []
    countries: list[str] = []
    regions: list[str] = []
    sites: list[str] = []

    model_config = ConfigDict(
        strict=False,
        populate_by_name=True,
    )

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
from typing import Any

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

class FeatureBlock(BaseModel):
    """Generic wrapper for a feature's item list."""
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[Any] = []

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

### 4.1 Backward-Compatible `execute()` Method

The change to `assembler.py` is minimal:

```python
from usdm4.assembler.schema import AssemblerInput

class Assembler:

    def execute(self, data: AssemblerInput | dict) -> None:
        if isinstance(data, dict):
            data = AssemblerInput.model_validate(data)

        try:
            self._identification_assembler.execute(data.identification)
            self._document_assembler.execute(data.document)
            self._population_assembler.execute(data.population)
            self._amendments_assembler.execute(data.amendments, self._document_assembler)

            if data.soa is not None:
                self._timeline_assembler.execute(data.soa)

            self._study_design_assembler.execute(
                data.study_design,
                self._population_assembler,
                self._timeline_assembler,
            )

            self._study_assembler.execute(
                data.study,
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

### 4.2 Sub-Assembler Migration

Each sub-assembler's `execute()` signature changes from `data: dict` to the corresponding schema type. This can be done incrementally — one assembler at a time. Internally, each sub-assembler replaces `data["key"]` access with `data.key` attribute access.

The migration order follows the existing processing sequence:

1. `IdentificationAssembler.execute(data: IdentificationInput)`
2. `DocumentAssembler.execute(data: DocumentInput)`
3. `PopulationAssembler.execute(data: PopulationInput)`
4. `AmendmentsAssembler.execute(data: AmendmentsInput, ...)`
5. `TimelineAssembler.execute(data: TimelineInput)`
6. `StudyDesignAssembler.execute(data: StudyDesignInput, ...)`
7. `StudyAssembler.execute(data: StudyInput, ...)`

Each assembler can be migrated independently. During the transition, an assembler that hasn't been migrated yet can call `data.model_dump()` to get the dict it expects.

---

## 5. Validation Modes

### 5.1 Lenient Mode (Default — Production)

The default `ConfigDict(strict=False)` allows Pydantic to coerce types where reasonable (e.g., `"123"` → `123` for an int field). Combined with default values on all optional fields, this means existing callers that pass raw dicts will continue to work. Validation catches structural problems (wrong nesting, completely wrong types) but is forgiving about edge cases.

### 5.2 Strict Mode (Development / Testing)

A `validate_strict()` class method on `AssemblerInput` enables stricter checking:

```python
class AssemblerInput(BaseModel):

    @classmethod
    def validate_strict(cls, data: dict) -> "AssemblerInput":
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

### 5.3 Error Reporting Integration

Validation errors should integrate with the existing `simple_error_log.Errors` system:

```python
def execute(self, data: AssemblerInput | dict) -> None:
    if isinstance(data, dict):
        try:
            data = AssemblerInput.model_validate(data)
        except ValidationError as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                msg = f"Schema validation: {field_path} — {error['msg']}"
                self._errors.error(msg, location)
            return
```

This translates Pydantic's structured validation errors into the error tracking format that all consumers already know how to handle.

---

## 6. Implementation Approach

### Phase A: Define Schema Models (Non-Breaking)

Add the `assembler/schema/` module with all Pydantic models. No changes to existing code. The models can be imported and used by external callers immediately.

**Tasks:**

1. Create `assembler/schema/` directory and `__init__.py`
2. Implement all seven domain schema files
3. Implement `AssemblerInput` top-level model
4. Add unit tests validating:
   - A minimal valid dict passes validation
   - Missing required fields produce clear errors
   - Type coercion works (string → int, etc.)
   - Extra keys are ignored (forward compatibility)
   - Each domain schema matches what its assembler currently reads

### Phase B: Integrate with Assembler (Backward-Compatible)

Modify `assembler.py` to accept `AssemblerInput | dict`. Existing dict-passing callers continue to work through `model_validate()`.

**Tasks:**

1. Update `Assembler.execute()` to validate input
2. Add validation error → `Errors` integration
3. Add integration tests with real extraction output from M11, CPT, and Legacy

### Phase C: Migrate Sub-Assemblers (Incremental)

Update each sub-assembler to accept its typed schema instead of `dict`. This can be done one assembler at a time, in any order.

**Tasks (per assembler):**

1. Change `execute(data: dict)` to `execute(data: <SchemaType>)`
2. Replace `data["key"]` with `data.key`
3. Replace `data.get("key", default)` with direct attribute access (defaults are on the model)
4. Update unit tests

### Phase D: Public API

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
tests/assembler/schema/
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

### 7.2 Regression Tests

Capture the actual dicts produced by the three existing extraction packages (M11, CPT, Legacy) and validate them against the schema. These become the golden regression set — if the schema rejects a dict that works today, the schema is wrong.

### 7.3 Round-Trip Tests

```python
def test_round_trip():
    """Dict → AssemblerInput → model_dump() → should equal original dict."""
    original = load_sample_extraction_output()
    schema = AssemblerInput.model_validate(original)
    round_tripped = schema.model_dump()
    # Compare (allowing for default-filling of missing optional fields)
```

---

## 8. Dependencies

The only new dependency is **Pydantic v2**, which is already a dependency of `usdm4` (the API layer uses `BaseModel` throughout). No new packages are required.

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
    ├── assembler/schema/ module
    ├── All seven domain schema files
    ├── AssemblerInput top-level model
    └── Unit tests

Phase B: Assembler Integration  ──────────────────────  [Backward-compatible]
    ├── execute() accepts AssemblerInput | dict
    ├── Validation error → Errors integration
    └── Integration tests with real extraction output

Phase C: Sub-Assembler Migration  ────────────────────  [Incremental, any order]
    ├── IdentificationAssembler → IdentificationInput
    ├── DocumentAssembler → DocumentInput
    ├── PopulationAssembler → PopulationInput
    ├── AmendmentsAssembler → AmendmentsInput
    ├── TimelineAssembler → TimelineInput
    ├── StudyDesignAssembler → StudyDesignInput
    └── StudyAssembler → StudyInput

Phase D: Public API  ─────────────────────────────────  [After Phase B]
    └── Export schema types from usdm4 public API
```

Phase A can begin immediately. Phase B is the prerequisite for `usdm4_protocol` Phase 1.
