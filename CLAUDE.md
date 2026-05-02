# USDM4

A Python package for using the CDISC TransCelerate Unified Study Data Model (USDM), version 4.

## Project overview

USDM4 is a self-contained Python package for the CDISC TransCelerate Unified Study Data Model (USDM) v4: API model classes, validation (the bundled d4k Python rule engine plus a wrapper around CDISC CORE), format conversion, study building, and assembly. (Earlier in the project's life the package depended on `usdm3` for shared infrastructure; that was folded in during the v3→v4 merge — see `docs/lessons_learned.md` §4 — and there is now zero `usdm3` dependency.)

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
  - `rules/` — d4k rule library + engine (one rule per file in `library/`, auto-discovered)
- `tests/` — pytest test suite (mirrors `src/` structure)
- `docs/` — project documentation
- `validate/` — standalone CLIs to run the two engines, samples, and the corpus baseline (see `validate/README.md`)
- `tools/` — developer utilities (CORE cache populator, CT/BC cache refresh)
- `setup.py` — package metadata and dependencies
- `requirements.txt` — development dependencies

## Key dependencies

- `pydantic>=2.0` — model validation and serialisation
- `cdisc-rules-engine>=0.16.0` — CDISC CORE validation engine
- `platformdirs>=3.0` — platform-appropriate cache directory resolution
- `simple_error_log>=0.8.0` — error collection and reporting
- `python-dateutil==2.9.0.post0` — date parsing
- `jsonschema>=4.0` — schema-shape validation (DDF00082)
- `lxml>=4.9` — XHTML well-formedness checks (DDF00187, DDF00247)
- `pyyaml>=6.0` — alignment YAML I/O
- `requests>=2.31` — CDISC Library API access

## CORE validation cache

The `core/` subpackage uses a persistent disk cache for downloaded CDISC resources (rules, CT packages, JSONata files, XSD schemas). The default cache location is platform-appropriate via `platformdirs`:

- macOS: `~/Library/Caches/usdm4/core/`
- Windows: `%LOCALAPPDATA%/usdm4/Cache/core/`
- Linux: `~/.cache/usdm4/core/`

For web-server deployments, pass an explicit `cache_dir` to `USDM4(cache_dir=...)` or `CoreCacheManager(cache_dir=...)`.

## Cache management utilities (`tools/`)

Three standalone scripts manage the CDISC caches the package consumes. All require a CDISC Library API key (set via `CDISC_LIBRARY_API_KEY`, typically via `.development_env` in the repo root which the scripts read with `python-dotenv`). Run from the repo root.

- `tools/prepare_core_cache.py` — populate the CDISC CORE validation cache (rules, CT packages, JSONata files, XSD schemas). Wraps `USDM4.prepare_core(...)`. Run at server startup or before going offline.

  ```bash
  python tools/prepare_core_cache.py [--version 4-0] [--cache-dir PATH]
  ```

- `tools/ct_cache.py` — force-refresh the CDISC CT (Controlled Terminology) library cache bundled inside the `usdm4` package (`src/usdm4/ct/cdisc/library_cache/`). Deletes the on-disk cache, then reloads from the CDISC Library API. Use after the CDISC publishes a new CT package.

  ```bash
  python tools/ct_cache.py
  ```

- `tools/bc_cache.py` — force-refresh the CDISC BC (Biomedical Concept) library cache (`src/usdm4/bc/cdisc/library_cache/`). Loads CT first (BC depends on CT), then deletes the BC cache and reloads. Use after the CDISC publishes a new BC package.

  ```bash
  python tools/bc_cache.py
  ```

The CT and BC caches are committed `library_cache_*.yaml` files under `src/usdm4/`, shipped in the pip wheel via `package_data` in `setup.py`. The CORE cache is platform-local (see "CORE validation cache" above) and is not committed.

## Development

- Format: `ruff format`
- Lint: `ruff check`
- Test: `pytest` (run in VSCode, not in Cowork — see Testing note below)
- Build: `python3 -m build --sdist --wheel`
- Publish: `twine upload dist/*`

## Testing

**Important:** Tests must be run in VSCode (or a local terminal), NOT in Cowork. The test suite depends on installed packages (`cdisc-rules-engine`, `lxml`, etc.) and the project's virtual environment, which are not available in the Cowork sandbox. When writing or modifying tests, create the files but do not attempt to execute them in Cowork.

## Validation CLI tools (`validate/`)

The `validate/` directory holds standalone CLIs for the two engines plus an alignment tool, the standard test set, and the corpus baseline of record. See `validate/README.md` for the directory-local guide and a full layout diagram. Invoke all CLIs from the repo root.

### Layout (in brief)

- `validate/samples/sample_usdm_1.json` … `sample_usdm_6.json` — standard test set; canonical inputs for day-to-day regression checks.
- `validate/corpus_cre_0_16/` — frozen 234-protocol baseline (CRE 0.16.0). Read-only reference; cited from `docs/cre_issues.md`.
- `validate/eval_corpus.py` + `validate/corpus_adapter.py` — assembler eval harness (different workflow — runs `Assembler.execute` over a protocol corpus, then validates the assembled JSON). See `docs/assembler_validation_findings.md`.

### CORE engine — `validate/core.py`

```bash
python validate/core.py validate/samples/sample_usdm_1.json [-o output.yaml] [--cache-dir /path/to/cache]
```

Output is a structured YAML file with findings grouped by rule, each error showing entity, instance_id, path, and relevant details. Execution errors (rules that don't apply to a given entity type) are counted but excluded from findings. Uses `CoreValidator` directly (not the `USDM4` facade) to preserve the full `CoreValidationResult` structure.

### d4k engine — `validate/d4k.py`

```bash
python validate/d4k.py validate/samples/sample_usdm_1.json [-o output.yaml]
```

Runs the usdm4 Python rule library (`USDM4.validate`). YAML emits every rule's outcome (Success / Failure / Exception / Not Implemented), not just failures, so it can be diffed against the CORE YAML.

### Alignment — `validate/compare.py`

```bash
python validate/compare.py <core.yaml> <d4k.yaml> [-o alignment.yaml] [--text]
```

Produces a rule-by-rule alignment report. Classifications per rule: `aligned_pass`, `aligned_fail`, `count_mismatch`, `d4k_only`, `core_only`, `d4k_exception`, `d4k_not_impl`, `core_only_rule`. CORE YAML only lists failing rules, so "CORE passed" and "CORE did not run this rule" collapse into `Pass-or-NA` at the rule-id level.

### One-shot wrapper — `validate/run.sh`

```bash
./validate/run.sh validate/samples/sample_usdm_1.json [output_dir]
```

Runs all three scripts end-to-end on a single JSON file. Honours `PYTHON` (interpreter) and `CACHE_DIR` (passed to core.py) environment overrides.

### Standard test set — run all six samples

The day-to-day regression check after a rule library change is to run `run.sh` over every sample and inspect the alignment outputs:

```bash
for f in validate/samples/sample_usdm_*.json; do
    ./validate/run.sh "$f"
done
```

Outputs land alongside each input as `<stem>_core.yaml`, `<stem>_d4k.yaml`, `<stem>_vs_d4k.yaml`, and `<stem>_vs_d4k.txt`. The four output files per sample are gitignored — re-run to regenerate.

### Execution error filtering

The CDISC Rules Engine reports four types of non-finding errors that are filtered to `execution_errors`: "Column not found in data", "Error occurred during dataset preprocessing", "Error occurred during operation execution", and "Outside scope". The first and last indicate a rule doesn't apply to the entity being checked; the two "Error occurred during ..." variants indicate the engine itself failed mid-rule (e.g. a pandas merge bug on `codeSystemVersion` surfaced repeatedly in a 234-protocol corpus run). None are data quality issues.

## Notes

- Version is defined in `src/usdm4/__info__.py`
- The `cdisc-rules-engine` requires Python 3.12+ (version 0.15.0 onwards).
- The CDISC Rules Engine is not thread-safe (mutates `os.getcwd()` and `sys.stdout`). Callers needing async/background execution should manage threading themselves.
