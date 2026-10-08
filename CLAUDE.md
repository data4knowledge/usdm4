# USDM4

A Python package for using the CDISC TransCelerate Unified Study Data Model (USDM), version 4.

## Project overview

USDM4 is a self-contained Python package for the CDISC TransCelerate Unified Study Data Model (USDM) v4: API model classes, validation (the bundled d4k Python rule engine plus a wrapper around CDISC CORE), format conversion, study building, and assembly. (Earlier in the project's life the package depended on `usdm3` for shared infrastructure; that was folded in during the v3→v4 merge — see `docs/lessons_learned.md` §4 — and there is now zero `usdm3` dependency.)

## Structure

- `src/usdm4/` — package source
  - `api/` — Pydantic domain model classes (v4)
  - `assembler/` — Study assembly from structured input
  - `base/` — id manager and API instance helpers used by the builder
  - `bc/cdisc/` — Biomedical concept library and cache
  - `builder/` — Programmatic study construction
  - `convert/` — USDM3 → USDM4 conversion
  - `core/` — CDISC CORE validation (wraps `cdisc-rules-engine`)
  - `ct/` — Controlled terminology (CDISC CT, ISO 3166/639)
  - `data_store/` — a loaded study indexed by id, class and parent
  - `expander/` — Timeline expansion
  - `file_cache/` — YAML cache reader used by the CT and BC libraries
  - `rules/` — d4k rule library + engine (one rule per file in `library/`, auto-discovered)
  - `utility/` — `TagResolver` (`usdm:ref` / `usdm:tag` in narrative text)
- `tests/` — pytest test suite (mirrors `src/` structure)
- `docs/` — project documentation: `aims.md` (what the package is for), `issues.md` (open problems, `N<n>`), `next_steps.md` (the plan only), `spec/` (designs), `cre_issues.md` (CORE vs d4k reference), `lessons_learned.md`
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
- `beautifulsoup4>=4.13.1` — XHTML handling in `TagResolver` (4.12.x warns "looks like a filename" on any text containing `/`; 4.13.0 was yanked)
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

- `tools/prepare_core_cache.py` — populate the CDISC CORE validation cache (rules, CT packages, JSONata files, XSD schemas). Wraps `USDM4.prepare_core(...)`. Run at server startup or before going offline. By default only fills in what's missing; pass `--force` to wipe the cache and re-download everything (e.g. after a `cdisc-rules-engine` upgrade, or to adopt newly published rules/CT). Reads the API key from `--api-key`, `$CDISC_LIBRARY_API_KEY`, or `.development_env`.

  ```bash
  python tools/prepare_core_cache.py [--version 4-0] [--cache-dir PATH] [--force]
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

- `tools/m11_ct.py` — generate the ICH M11 controlled terminology the CDISC Library does not serve: `src/usdm4/ct/cdisc/missing/m11_codelists.yaml` (whole M11 response codelists) and `missing_ct.yaml` (M11-only codes added to extensible CDISC codelists, `M11_TO_SDTM`). Source: the ICH M11 Terminology `.xls` published by NCI EVS (https://evs.nci.nih.gov/ftp1/ICH/M11), by default the newest `ICH M11 Terminology_*.xls` in the sibling `m11_specification/m11_versions/2025-11-16/specification/`. Members, terms, definitions and the extensible flag come from that file, never from the M11 Technical Specification text (GitHub 81). Per-section data-element codelists are not emitted. No API key. Needs `xlrd`. Other packages read these codelists through `USDM4().ct_library()` (loaded once per instance) and `Library.codelist(codelist_id)` (a copy, with its terms), never a copy of their own.

  ```bash
  python3 tools/m11_ct.py [--terminology PATH] [--dry-run]
  ```

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

## Session log

Session state lives in four files, as in `protocol_corpus`, written by the `save-session` skill:

- `memory.md` (repo root) — the session log. Appended at the END, headed
  `## YYYY-MM-DD — title` and nothing else. Never retired.
- `docs/next_steps.md` — the plan only. Rewritten wholesale, never appended to; a finished
  item is deleted.
- `docs/issues.md` — open problems, `N<n>`, never reused.
- `docs/lessons_learned.md` — durable lessons.

Every session that works a `usdm4` issue or branch writes a full entry in `memory.md`,
whichever Claude project drove it. The other repo's log carries only a short pointer. A cold
start in this repo must be able to resume from this repo alone.

## Notes

- Version is defined in `src/usdm4/__info__.py`
- The `cdisc-rules-engine` requires Python 3.12+ (version 0.15.0 onwards).
- The CDISC Rules Engine is not thread-safe (mutates `os.getcwd()` and `sys.stdout`). Callers needing async/background execution should manage threading themselves.

## GitHub Issues

**GitHub issue titles are four or five words** (Dave, 2026-10-04) — a short name for the issue, not a statement of it. The issue text carries the detail.

**GitHub issue and PR text has no line breaks inside a paragraph** (Dave, 2026-10-08) — issue bodies, closing statements, PR descriptions and anything else written to be pasted into GitHub: one line per paragraph, a blank line between paragraphs. Never hard-wrap at a fixed width, whatever width the repo's own files use.
