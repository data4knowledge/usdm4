# CDISC CORE Validation Module

The `usdm4.core` module integrates the CDISC Rules Engine (CORE) into the usdm4 package, allowing validation of USDM JSON files against the full set of CDISC CORE conformance rules.

## Prerequisites

A CDISC Library API key is required. Obtain one from [CDISC Library](https://www.cdisc.org/cdisc-library) and set it as an environment variable:

```bash
export CDISC_API_KEY="your-api-key-here"
# or
export CDISC_LIBRARY_API_KEY="your-api-key-here"
```

The `cdisc-rules-engine` package is installed automatically as a dependency of usdm4.

## Quick Start

### Validation via the USDM4 Facade

```python
from usdm4 import USDM4

usdm = USDM4()
result = usdm.validate_core("study.json")

if result.is_valid:
    print("Validation passed")
else:
    print(result.format_text())
```

### Using CoreValidator Directly

For more control, use the `CoreValidator` class without going through the `USDM4` facade:

```python
from usdm4.core import CoreValidator

validator = CoreValidator(
    cache_dir="/path/to/my/cache",
    api_key="my-api-key",
)

result = validator.validate("study.json", version="4-0")
```

## API Reference

### USDM4 Methods

**`validate_core(file_path, version="4-0", cache_dir=None, api_key=None)`**

Synchronous validation. Returns a `CoreValidationResult`. Parameters:

- `file_path` — Path to the USDM JSON file.
- `version` — `"3-0"` or `"4-0"` (default `"4-0"`).
- `cache_dir` — Optional path to the cache directory. Defaults to `~/.cache/usdm4/core/`.
- `api_key` — Optional CDISC Library API key. Falls back to `CDISC_LIBRARY_API_KEY` or `CDISC_API_KEY` environment variables.

### CoreValidationResult

**Properties:**

- `is_valid` — `True` if no validation findings were reported.
- `finding_count` — Total number of individual validation errors across all findings.
- `execution_error_count` — Number of rule execution errors (rules that don't apply to this file).
- `rules_executed` — Total rules that were run.
- `rules_skipped` — Rules skipped due to known engine bugs.
- `ct_packages_available` — Number of CT packages known to CDISC Library.
- `ct_packages_loaded` — List of CT package names actually loaded for this file.
- `findings` — List of `CoreRuleFinding` objects.

**Methods:**

- `format_text()` — Human-readable text report.
- `to_dict()` — JSON-serialisable dictionary.

### CoreRuleFinding

Each finding represents one CORE rule that reported validation errors.

- `rule_id` — The CORE rule identifier (e.g. `"CORE-000996"`).
- `description` — Human-readable description of what the rule checks.
- `message` — The error message template from the rule.
- `errors` — List of error detail dicts from the engine.
- `error_count` — Number of errors for this rule.

### CoreCacheManager

Access via `validator.cache_manager` (on a `CoreValidator` instance).

- `cache_dir` — The root cache directory path.
- `clear()` — Remove all cached resources. They will be re-downloaded on next use.
- `ensure_resources()` — Download JSONata and XSD schema files if not already cached.

## Caching Strategy

The module uses a three-level caching strategy to avoid redundant downloads:

1. **Disk cache** (persistent, survives process restarts and package upgrades)
2. **In-memory cache** (used by the CDISC Rules Engine within a single process)
3. **CDISC Library** (remote download, only when cache misses)

### What Gets Cached

| Resource | Location | First-run Source |
|----------|----------|------------------|
| Validation rules | `{cache_dir}/rules/usdm/4-0.json` | CDISC Library API |
| CT package list | `{cache_dir}/ct/published_packages.json` | CDISC Library API |
| CT codelist data | `{cache_dir}/ct/data/{package}.json` | CDISC Library API |
| JSONata functions | `{cache_dir}/resources/jsonata/` | GitHub (cdisc-rules-engine repo) |
| XSD schemas | `{cache_dir}/resources/schema/xml/` | GitHub (cdisc-rules-engine repo) |

### Default Cache Location

`~/.cache/usdm4/core/`

Override by passing `cache_dir` to `validate_core()` or `CoreValidator()`:

```python
result = usdm.validate_core("study.json", cache_dir="/tmp/usdm_cache")
```

### Clearing the Cache

```python
from usdm4.core import CoreValidator

validator = CoreValidator()
validator.cache_manager.clear()
```

This forces a fresh download of all resources on the next validation run.

## Relationship to Existing Validation

The usdm4 package now has two validation approaches:

| Method | Engine | Rules | Use Case |
|--------|--------|-------|----------|
| `validate()` | usdm4 d4k rule library (`usdm4.rules`) | V4 DDF rules (Python) | Fast, local checks |
| `validate_core()` | CDISC Rules Engine (CORE) | Full CORE rule set | Comprehensive CDISC conformance |

Both can be used independently. `validate()` runs local Python rule implementations. `validate_core()` runs the official CDISC CORE rules which are downloaded from CDISC Library and executed by the CDISC Rules Engine.

## Architecture Notes

### Thread Safety

The CDISC Rules Engine is not thread-safe — it mutates `os.getcwd()` and `sys.stdout` during execution. Callers needing async or background execution should manage their own threading.

### Output Suppression

The rules engine produces extensive logging and print output. The module suppresses this by redirecting `sys.stdout`/`sys.stderr` to `io.StringIO()` and disabling the root logger during validation. Original streams are always restored in a `finally` block.

### Working Directory

The rules engine resolves resource paths relative to `os.getcwd()`. During validation, the module temporarily changes the working directory to the engine's site-packages location and restores it afterwards. File paths passed to the engine are converted to absolute paths before the `chdir`.

### Resource Files Not in the Pip Package

Three sets of resource files are required by the engine but not included in the `cdisc-rules-engine` pip package:

- **JSONata custom functions** (2 files) — Required for certain rules using JSONata expressions.
- **USDM XHTML schemas** (3 files) — Required for rules CORE-000945 and CORE-001069.
- **XHTML 1.1 schemas** (70+ files) — Dependencies of the USDM XHTML schemas. All files are required due to `xs:redefine`/`xs:include` chains.

These are downloaded from the cdisc-rules-engine GitHub repository on first use and cached locally.

### Excluded Rules

Two rules are excluded from execution due to known bugs in the CDISC Rules Engine:

- `CORE-000955` — JSONata NoneType error
- `CORE-000956` — JSONata NoneType error

### Execution Errors vs Validation Findings

Not all errors from the engine indicate data quality issues. Some rules apply to entity types that may not be present in every USDM file. The module separates these into:

- **Findings** — Real data issues reported by rules.
- **Execution errors** — Rules that couldn't run because the expected fields or datasets don't exist in this file. These include "Column not found in data", "Error occurred during dataset preprocessing", and "Outside scope" errors.

Only findings are surfaced via `result.findings`. Execution errors are available separately via `result.execution_errors` for debugging.

## Module Structure

```
src/usdm4/core/
    __init__.py                  # Exports CoreValidator, CoreValidationResult, CoreCacheManager
    core_validator.py            # Main validator with validate()
    core_validation_result.py    # Result dataclasses (CoreValidationResult, CoreRuleFinding)
    core_cache_manager.py        # Persistent disk cache for rules, CT, schemas

tests/usdm4/core/
    __init__.py
    test_core_cache_manager.py   # Tests for cache, results, and static methods
```

## Troubleshooting

**"No CDISC API key"** — Set `CDISC_API_KEY` or `CDISC_LIBRARY_API_KEY` in your environment.

**Slow first run** — The first validation downloads rules, CT packages, and schema files. Subsequent runs use the cache and are significantly faster.

**CT validation failures** — Ensure the `codeSystemVersion` values in your USDM file correspond to published CT packages. Check `result.ct_packages_loaded` to see which packages were loaded.

**Stale cache** — If rules or CT packages have been updated, clear the cache: `validator.cache_manager.clear()`.

## References

- [CDISC Rules Engine (CORE)](https://github.com/cdisc-org/cdisc-rules-engine)
- [CDISC Library](https://www.cdisc.org/cdisc-library)
- [USDM Specification](https://www.cdisc.org/standards/foundational/usdm)
- [cdisc-rules-engine on PyPI](https://pypi.org/project/cdisc-rules-engine/)
