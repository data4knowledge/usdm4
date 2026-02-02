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

