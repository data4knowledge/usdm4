# USDM4

A Python package for using the CDISC TransCelerate Unified Study Data Model (USDM), version 4.

## Project overview

USDM4 extends the `usdm3` base library with USDM v4 support: API model classes, validation (including CDISC CORE conformance), format conversion, study building, and assembly. It depends on `usdm3` for shared infrastructure.

## Structure

- `src/usdm4/` — package source
  - `api/` — Pydantic domain model classes (v4)
  - `assembler/` — Study assembly from structured input
  - `bc/cdisc/` — Biomedical concept library and cache
  - `builder/` — Programmatic study construction
  - `convert/` — Format conversion utilities
  - `core/` — CDISC CORE validation (wraps `cdisc-rules-engine`)
  - `ct/` — Controlled terminology (CDISC CT, ISO 3166/639)
  - `expander/` — Timeline expansion
  - `rules/` — Rule-based validation (non-CORE)
- `tests/` — pytest test suite (mirrors `src/` structure)
- `docs/` — project documentation
- `setup.py` — package metadata and dependencies
- `requirements.txt` — development dependencies

## Key dependencies

- `usdm3>=0.12.2` — base USDM infrastructure
- `pydantic>=2.0` — model validation and serialisation
- `cdisc-rules-engine>=0.15.0` — CDISC CORE validation engine
- `platformdirs>=3.0` — platform-appropriate cache directory resolution
- `simple_error_log>=0.7.0` — error collection and reporting
- `python-dateutil==2.9.0.post0` — date parsing

## CORE validation cache

The `core/` subpackage uses a persistent disk cache for downloaded CDISC resources (rules, CT packages, JSONata files, XSD schemas). The default cache location is platform-appropriate via `platformdirs`:

- macOS: `~/Library/Caches/usdm4/core/`
- Windows: `%LOCALAPPDATA%/usdm4/Cache/core/`
- Linux: `~/.cache/usdm4/core/`

For web-server deployments, pass an explicit `cache_dir` to `USDM4(cache_dir=...)` or `CoreCacheManager(cache_dir=...)`.

## Development

- Format: `ruff format`
- Lint: `ruff check`
- Test: `pytest` (run in VSCode, not in Cowork — see Testing note below)
- Build: `python3 -m build --sdist --wheel`
- Publish: `twine upload dist/*`

## Testing

**Important:** Tests must be run in VSCode (or a local terminal), NOT in Cowork. The test suite depends on installed packages (`cdisc-rules-engine`, `usdm3`, etc.) and the project's virtual environment, which are not available in the Cowork sandbox. When writing or modifying tests, create the files but do not attempt to execute them in Cowork.

## CORE CLI tool

`core.py` is a standalone CLI for running CDISC CORE validation:

```bash
python core.py study.json [-o output.yaml] [--cache-dir /path/to/cache]
```

Output is a structured YAML file with findings grouped by rule, each error showing entity, instance_id, path, and relevant details. Execution errors (rules that don't apply to a given entity type) are counted but excluded from findings.

The validator uses `CoreValidator` directly (not the `USDM4` facade) to preserve the full `CoreValidationResult` structure in the output.

### Execution error filtering

The CDISC Rules Engine reports three types of non-finding errors that are filtered to `execution_errors`: "Column not found in data", "Error occurred during dataset preprocessing", and "Outside scope". These indicate a rule doesn't apply to the entity being checked — they are not data quality issues.

## Notes

- Version is defined in `src/usdm4/__info__.py`
- The `cdisc-rules-engine` requires Python 3.12+ (version 0.15.0 onwards).
- The CDISC Rules Engine is not thread-safe (mutates `os.getcwd()` and `sys.stdout`). Callers needing async/background execution should manage threading themselves.
