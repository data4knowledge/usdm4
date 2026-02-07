# USDM4

A Python library for the CDISC TransCelerate Unified Study Data Model (USDM) Version 4.

## Overview

USDM4 provides tools for building, assembling, validating, converting, and expanding clinical study definitions using the USDM Version 4 specification. It enables programmatic creation and manipulation of machine-readable study definitions that conform to CDISC standards.

## Features

- **Build** - Create USDM4 study structures programmatically with a fluent builder interface
- **Assemble** - Orchestrate complete study assembly from structured input data
- **Validate** - Validate USDM4 JSON files against defined rules
- **Load** - Load USDM4 data from JSON files or dictionaries
- **Convert** - Transform USDM data structures between formats
- **Expand** - Expand schedule timelines for study designs

## Installation

```bash
pip install usdm4
```

### Requirements

- Python 3.10 or higher

## Quick Start

```python
from usdm4 import USDM4
from simple_error_log.errors import Errors

# Initialize
usdm = USDM4()
errors = Errors()

# Create a minimal study
wrapper = usdm.minimum("My Study", "SPONSOR-001", "1.0", errors)

# Access the study
print(wrapper.study.id)
```

## Usage

### Loading Studies

Load a study from a JSON file:

```python
errors = Errors()
wrapper = USDM4().load("study.json", errors)
```

Load from a dictionary:

```python
data = {...}
wrapper = USDM4().loadd(data, errors)
```

### Validating Studies

```python
result = USDM4().validate("study.json")

if result.passed_or_not_implemented():
    print("Validation passed")
else:
    print("Validation failed")
```

### Building Studies

Use the builder for programmatic study creation with access to controlled terminology:

```python
errors = Errors()
builder = USDM4().builder(errors)

# Get CDISC codes
code = builder.cdisc_code("C207616", "Official Study Title")

# Get ISO codes
country = builder.iso3166_code("USA")
language = builder.iso639_code("en")

# Create organizations
sponsor = builder.sponsor("My Pharma Corp")

# Create any USDM4 class
study_version = builder.create("StudyVersion", {"versionNumber": "1.0"})
```

### Assembling Studies

For structured assembly of complete studies from domain-organized input:

```python
errors = Errors()
assembler = USDM4().assembler(errors)

assembler.execute({
    "identification": {...},
    "document": {...},
    "population": {...},
    "study_design": {...},
    "amendments": {...},
    "study": {...}
})

wrapper = assembler.wrapper("MySystem", "1.0")
```

### Assembler JSON Input Structure

The assembler accepts a single dictionary with the following top-level keys, each processed by a dedicated sub-assembler:

```json
{
  "identification": { ... },
  "document": { ... },
  "population": { ... },
  "amendments": { ... },
  "study_design": { ... },
  "soa": { ... },
  "study": { ... }
}
```

All top-level keys are required except `soa`, which is optional.

---

#### `identification`

Study identification, titles, identifiers, organizations, and roles.

```json
{
  "titles": {
    "brief": "string",
    "official": "string",
    "public": "string",
    "scientific": "string",
    "acronym": "string"
  },
  "identifiers": [
    {
      "identifier": "string",
      "scope": {
        "standard": "string",
        "non_standard": {
          "type": "string",
          "role": "string | null",
          "name": "string",
          "description": "string",
          "label": "string",
          "identifier": "string",
          "identifierScheme": "string",
          "legalAddress": {
            "lines": ["string"],
            "city": "string",
            "district": "string",
            "state": "string",
            "postalCode": "string",
            "country": "string"
          }
        }
      }
    }
  ],
  "roles": {
    "co_sponsor": {
      "name": "string",
      "address": {
        "lines": ["string"],
        "city": "string",
        "district": "string",
        "state": "string",
        "postalCode": "string",
        "country": "string"
      }
    },
    "local_sponsor": { },
    "device_manufacturer": { }
  },
  "other": {
    "sponsor_signatory": "string | null",
    "medical_expert": "string | null",
    "compound_names": "string | null",
    "compound_codes": "string | null"
  }
}
```

**Notes:**

- `titles` is optional (defaults to empty). Valid title types: `brief`, `official`, `public`, `scientific`, `acronym`.
- `identifiers` is optional (defaults to empty list). Each identifier `scope` must contain either `standard` or `non_standard`, not both.
- Valid `standard` keys: `ct.gov`, `ema`, `fda`. These resolve to predefined organizations with complete address information.
- Valid `non_standard` type values: `registry`, `regulator`, `healthcare`, `pharma`, `lab`, `cro`, `gov`, `academic`, `medical_device`.
- Valid `role` values: `co-sponsor`, `manufacturer`, `investigator`, `pharmacovigilance`, `project manager`, `local sponsor`, `laboratory`, `study subject`, `medical expert`, `statistician`, `idmc`, `care provider`, `principal investigator`, `outcomes assessor`, `dec`, `clinical trial physician`, `sponsor`, `adjudication committee`, `study site`, `dsmb`, `regulatory agency`, `contract research`.
- `roles` is optional (defaults to empty). Each role key (`co_sponsor`, `local_sponsor`, `device_manufacturer`) can be `null` to skip. The `address` field within each role is optional.
- `other` is optional. When present, all four sub-fields are read directly.

---

#### `document`

Protocol document metadata and hierarchical content sections.

```json
{
  "document": {
    "label": "string",
    "version": "string",
    "status": "string",
    "template": "string",
    "version_date": "string"
  },
  "sections": [
    {
      "section_number": "string",
      "section_title": "string",
      "text": "string"
    }
  ]
}
```

**Notes:**

- All fields in `document` are required.
- Valid `status` values: `APPROVED`, `DRAFT`, `DFT`, `FINAL`, `OBSOLETE`, `PENDING`, `PENDING REVIEW` (case-insensitive).
- `version_date` should be in ISO format (e.g. `2024-01-15`).
- Section hierarchy is determined by `section_number` depth: `"1"` = level 1, `"1.1"` = level 2, `"1.1.1"` = level 3.
- `text` content may contain HTML.

---

#### `population`

Population definitions and eligibility criteria.

```json
{
  "label": "string",
  "inclusion_exclusion": {
    "inclusion": ["string"],
    "exclusion": ["string"]
  }
}
```

**Notes:**

- All fields are required.
- Each inclusion and exclusion item is a text string describing the criterion.
- The `label` is used to generate the internal name (uppercased, spaces replaced with hyphens).

---

#### `amendments`

Study amendment information. Can be `null` or empty to skip amendment processing entirely.

```json
{
  "identifier": "string",
  "summary": "string",
  "reasons": {
    "primary": "string",
    "secondary": "string"
  },
  "impact": {
    "safety_and_rights": {
      "safety": { "substantial": boolean, "reason": "string" },
      "rights": { "substantial": boolean, "reason": "string" }
    },
    "reliability_and_robustness": {
      "reliability": { "substantial": boolean, "reason": "string" },
      "robustness": { "substantial": boolean, "reason": "string" }
    }
  },
  "enrollment": {
    "value": "integer | string",
    "unit": "string"
  },
  "scope": {
    "global": boolean,
    "countries": ["string"],
    "regions": ["string"],
    "sites": ["string"],
    "unknown": ["string"]
  },
  "changes": [
    {
      "section": "string",
      "description": "string",
      "rationale": "string"
    }
  ]
}
```

**Notes:**

- `reasons` values use `CODE:DECODE` format (e.g. `"C207609:New Safety Information Available"`).
- Valid reason codes: `C207612` (Regulatory Agency Request), `C207608` (New Regulatory Guidance), `C207605` (IRB/IEC Feedback), `C207609` (New Safety Information), `C207606` (Manufacturing Change), `C207602` (IMP Addition), `C207601` (Change In Strategy), `C207600` (Change In Standard Of Care), `C207607` (New Data Available), `C207604` (Investigator/Site Feedback), `C207611` (Recruitment Difficulty), `C207603` (Inconsistency/Error In Protocol), `C207610` (Protocol Design Error), `C17649` (Other), `C48660` (Not Applicable).
- `enrollment` is optional. The `value` is converted to integer internally.
- `scope` is optional. Items in `unknown` are resolved to country or region codes via ISO 3166 lookup. Empty strings in `unknown` are skipped.
- `changes` section references use `"NUMBER, TITLE"` format (e.g. `"1.5, Safety Considerations"`), which are matched against document sections.

---

#### `study_design`

Study design structure and trial phase.

```json
{
  "label": "string",
  "rationale": "string",
  "trial_phase": "string"
}
```

**Notes:**

- All fields are required.
- Valid `trial_phase` values: `0`, `PRE-CLINICAL`, `1`, `I`, `1-2`, `1/2`, `1/2/3`, `1/3`, `1A`, `IA`, `1B`, `IB`, `2`, `II`, `2-3`, `II-III`, `2A`, `IIA`, `2B`, `IIB`, `3`, `III`, `3A`, `IIIA`, `3B`, `IIIB`, `4`, `IV`, `5`, `V`, `2/3/4`. Prefixes `PHASE` or `TRIAL` are automatically stripped.
- Default intervention model is Parallel Study (CDISC code C82639).

---

#### `soa` (Schedule of Activities)

Timeline data including epochs, visits, timepoints, activities, and conditions. This entire section is optional.

```json
{
  "epochs": {
    "items": [
      { "text": "string" }
    ]
  },
  "visits": {
    "items": [
      {
        "text": "string",
        "references": ["string"]
      }
    ]
  },
  "timepoints": {
    "items": [
      {
        "index": "string | integer",
        "text": "string",
        "value": "string | integer",
        "unit": "string"
      }
    ]
  },
  "windows": {
    "items": [
      {
        "before": integer,
        "after": integer,
        "unit": "string"
      }
    ]
  },
  "activities": {
    "items": [
      {
        "name": "string",
        "visits": [
          {
            "index": integer,
            "references": ["string"]
          }
        ],
        "children": [
          {
            "name": "string",
            "visits": [
              {
                "index": integer,
                "references": ["string"]
              }
            ],
            "actions": {
              "bcs": ["string"]
            }
          }
        ],
        "actions": {
          "bcs": ["string"]
        }
      }
    ]
  },
  "conditions": {
    "items": [
      {
        "reference": "string",
        "text": "string"
      }
    ]
  }
}
```

**Notes:**

- Epochs, visits, and timepoints arrays must be parallel (same length, aligned by index).
- `windows` must also be parallel with timepoints.
- Negative timepoint `value` indicates before the reference anchor. The first non-negative value determines the anchor point.
- `references` on visits and activities are condition keys that link to entries in the `conditions` array.
- `children` are sub-activities nested under a parent activity.
- `actions.bcs` lists Biomedical Concept names. Known concepts are resolved from the CDISC BC library; unknown names create surrogate BiomedicalConcept objects.
- Supported time units: `years`/`yrs`/`yr`, `months`/`mths`/`mth`, `weeks`/`wks`/`wk`, `days`/`dys`/`dy`, `hours`/`hrs`/`hr`, `minutes`/`mins`/`min`, `seconds`/`secs`/`sec` (case-insensitive).

---

#### `study`

Core study information and metadata.

```json
{
  "name": {
    "identifier": "string",
    "acronym": "string",
    "compound": "string"
  },
  "label": "string",
  "version": "string",
  "rationale": "string",
  "description": "string",
  "sponsor_approval_date": "string",
  "confidentiality": "string",
  "original_protocol": "string | boolean"
}
```

**Notes:**

- `name` is required. At least one of `identifier`, `acronym`, or `compound` must be non-empty. Priority order: `identifier` > `acronym` > `compound`. The name is auto-generated (uppercased, non-alphanumeric characters removed).
- `version` and `rationale` are required.
- `label` is optional; used as fallback if name generation produces an empty string.
- `description`, `sponsor_approval_date`, `confidentiality`, and `original_protocol` are all optional.
- `original_protocol` is converted to boolean: `"true"`, `"1"`, `"yes"`, `"y"` map to `true` (case-insensitive).
- `sponsor_approval_date` should be in ISO format (e.g. `2024-01-15`).
- When present, `confidentiality`, `original_protocol`, `compound_codes`, `compound_names`, `sponsor_signatory`, and `medical_expert` are stored as extension attributes on the study version.

---

### Converting Studies

```python
converter = USDM4().convert()
# Transform data structures as needed
```

### Expanding Timelines

```python
expander = USDM4().expander(wrapper)
# Process schedule timeline expansion
```

## API Classes

USDM4 includes 73 domain model classes covering:

| Domain | Classes |
|--------|---------|
| Study Structure | `Study`, `StudyVersion`, `StudyDesign`, `StudyArm`, `StudyEpoch`, `StudyElement` |
| Interventions | `StudyIntervention`, `Activity`, `Administration`, `Procedure`, `Encounter` |
| Population | `StudyDesignPopulation`, `AnalysisPopulation`, `EligibilityCriterion`, `SubjectEnrollment` |
| Documents | `StudyDefinitionDocument`, `StudyDefinitionDocumentVersion`, `Amendment` |
| Coding | `Code`, `AliasCode`, `BiomedicalConcept`, `Objective`, `Endpoint` |
| Timelines | `ScheduleTimeline`, `ScheduledActivityInstance`, `ScheduledDecisionInstance` |
| Organization | `StudyIdentifier`, `Organization`, `StudySite` |

## Development

### Running Tests

```bash
pytest
```

Tests require 100% code coverage.

### Code Formatting

```bash
ruff format
ruff check
```

### Building the Package

```bash
python3 -m build --sdist --wheel
```

### Publishing

```bash
twine upload dist/*
```

## Related Projects

- [usdm3](https://pypi.org/project/usdm3/) - USDM Version 3 support

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

