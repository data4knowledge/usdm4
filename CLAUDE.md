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

Standalone CLIs for the two engines, the alignment tool, the standard test set (`validate/samples/`), and the frozen corpus baseline (`validate/corpus_cre_0_16/`) all live under `validate/`. See `validate/README.md` for layout, per-CLI usage, flags, and output conventions. Invoke from the repo root.

The day-to-day regression check after a rule library change is to run `run.sh` over every sample:

```bash
for f in validate/samples/sample_usdm_*.json; do
    ./validate/run.sh "$f"
done
```

## Execution error filtering

The wrapper at `src/usdm4/core/core_validator.py` filters a known set of CRE non-finding error strings out of the findings list and into `execution_errors`. The authoritative list of sentinels and the rationale for each is maintained in `docs/cre_issues.md` (Issue 5); do not duplicate it here.

## Notes

- Version is defined in `src/usdm4/__info__.py`
- The `cdisc-rules-engine` requires Python 3.12+ (version 0.15.0 onwards).
- The CDISC Rules Engine is not thread-safe (mutates `os.getcwd()` and `sys.stdout`). Callers needing async/background execution should manage threading themselves.
