# CDISC Rules Engine — Known Issues and Workarounds

Feedback notes for the CDISC Rules Engine (CRE) development team, based on
integrating cdisc-rules-engine 0.15.x with USDM validation in the usdm4
package (March 2026).


## 1. Singleton caching prevents sequential multi-file validation

**Severity:** High — silent data corruption (wrong results, no error raised)

When the CRE is used to validate multiple USDM files in the same process, every
file after the first returns the results from the first file. Two independent
singletons cause this.

### 1a. InMemoryCacheService retains dataset data across runs

`InMemoryCacheService` (in `services/cache/in_memory_cache_service.py`) is a
class-level singleton. Its `dataset_cache` dict is populated during the first
validation run and never cleared. Subsequent calls to `RulesEngine` with
different `dataset_paths` still read the stale cache entries.

**Workaround:**

```python
cache = CacheServiceFactory(config).get_cache_service()
with cache.dataset_cache_lock:
    cache.dataset_cache.clear()
```

This must be called before each validation run. However, it is not sufficient on
its own — see 1b.

### 1b. USDMDataService singleton never reloads file data

`USDMDataService` (in `services/data_services/usdm_data_service.py`) is also a
singleton via a `_instance` class variable. It loads and parses the USDM JSON
file in `__init__` (around line 85–86). Because `get_instance()` returns the
existing `_instance` without re-initialising, subsequent validation runs
continue to use the data from the first file.

**Workaround:**

```python
from cdisc_rules_engine.services.data_services import USDMDataService
USDMDataService._instance = None
```

This must be called before each validation run, in addition to clearing the
in-memory cache.

**Suggested fix:** Either make these services non-singleton (create fresh
instances per `RulesEngine` invocation), or provide an official `reset()` /
`clear()` API that callers can use between runs. At minimum, the dataset cache
and data service should be scoped to a single `RulesEngine` lifetime rather than
to the process.


## 2. Thread safety — global state mutation

**Severity:** High — unsafe for concurrent use

The engine mutates two pieces of global process state during validation:

- **`os.getcwd()`** — The engine resolves resource paths (JSONata files, XSD
  schemas) relative to the current working directory. Callers must `chdir` to
  the engine's package directory before calling `validate_single_rule`. This
  means two threads cannot validate simultaneously without corrupting each
  other's working directory.

- **`sys.stdout` / `sys.stderr`** — The engine writes verbose progress output
  directly to stdout. Callers who want clean output must redirect these streams,
  which is inherently thread-unsafe.

**Workaround:** We redirect stdout/stderr to `io.StringIO()` and save/restore
the working directory in a `try/finally` block. This works for single-threaded
sequential use but is not safe for concurrent execution.

**Suggested fix:** Use `pathlib` absolute paths for resource resolution instead
of relying on `os.getcwd()`. Replace `print()` calls with `logging` at an
appropriate level so callers can control verbosity via standard log
configuration.


## 3. jsonata JList leaks into validation results

**Severity:** Medium — breaks downstream serialisation

Some validation rule results contain values of type `jsonata.utils.JList`
instead of plain Python `list`. `JList` is a subclass of `list` but carries
extra attributes that cause problems:

- **YAML serialisation** produces `!!python/object:jsonata.utils.JList` tags,
  making the output unloadable by `yaml.safe_load()`.
- **JSON serialisation** may work (since `JList` is a list subclass) but the
  round-trip through YAML is broken.

This was observed in the `value` sub-dicts within error records returned by
`validate_single_rule`.

**Workaround:** We recursively walk all error values and convert any iterable
that is not a plain `list`, `dict`, or scalar into a plain `list`:

```python
@staticmethod
def _sanitise_value(obj):
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _sanitise_value(v) for k, v in obj.items()}
    try:
        return [_sanitise_value(item) for item in obj]
    except TypeError:
        return str(obj)
```

**Suggested fix:** Ensure rule evaluation results are normalised to plain Python
types before being returned to callers. A post-processing step in
`validate_single_rule` (or in the JSONata evaluation layer) that converts JList
→ list would prevent this from leaking to every consumer.


## 4. Resource files missing from pip package

**Severity:** Medium — first-run failure without workaround

Three sets of resource files required at runtime are not included in the
`cdisc-rules-engine` pip distribution:

- **JSONata custom function files** (2 files) — needed by rules that use JSONata
  expressions.
- **USDM XHTML schema** (`cdisc-usdm-xhtml-1.0/`, 3 files) — needed by
  CORE-000945 and CORE-001069.
- **XHTML 1.1 base schemas** (`xhtml-1.1/`, 70+ files) — dependencies of the
  USDM XHTML schema via `xs:redefine` / `xs:include` chains.

Without these files, certain rules fail with file-not-found errors.

**Workaround:** We download these from the cdisc-rules-engine GitHub repository
on first use and cache them locally in a persistent disk cache. See
`CoreCacheManager.ensure_resources()`.

**Suggested fix:** Include these resource files in the pip package (via
`package_data` or `data_files` in setup configuration), or provide a documented
post-install step / CLI command that fetches them.


## 5. Execution errors indistinguishable from validation findings

**Severity:** Low-Medium — noisy output, requires filtering

When a rule is executed against an entity type it does not apply to, the engine
returns error records rather than an empty result. Three error types fall into
this category:

- `"Column not found in data"`
- `"Error occurred during dataset preprocessing"`
- `"Outside scope"`

These are not data quality issues — they simply mean the rule's preconditions
were not met for that entity. However, they are returned in the same `errors`
list as real validation findings, requiring callers to inspect the `error` field
and filter them out.

**Workaround:** We classify errors by checking the `error` field against the
three known strings and separate them into an `execution_errors` list.

**Suggested fix:** Either skip rules whose preconditions are not met (return an
empty result), or return execution errors in a separate field / with a distinct
status code so callers do not need to maintain a list of sentinel strings.


## 6. Rules with known JSONata bugs

**Severity:** Low — crashes during execution, requires exclusion

Two rules crash with JSONata NoneType errors during execution:

- **CORE-000955**
- **CORE-000956**

These rules cannot be executed without causing an unhandled exception.

**Workaround:** We maintain an exclusion list (`_EXCLUDED_RULES`) and skip these
rules before calling `validate_single_rule`.

**Suggested fix:** Fix the underlying JSONata evaluation bugs, or mark these
rules as disabled/draft in the rule catalogue so they are not returned by
`get_rules_by_catalog`.


## Summary of workarounds in usdm4

All workarounds are implemented in `src/usdm4/core/core_validator.py` and
`src/usdm4/core/core_validation_result.py`. The key interventions:

| Issue | Location | Workaround |
|-------|----------|------------|
| Singleton cache not clearing | `_run_validation_inner()` | Clear `dataset_cache` before each run |
| USDMDataService singleton | `_run_validation_inner()` | Set `USDMDataService._instance = None` |
| Working directory mutation | `_execute_validation()` | Save/restore `os.getcwd()` in try/finally |
| Stdout pollution | `_run_validation()` | Redirect sys.stdout/stderr to StringIO |
| JList in results | `CoreRuleFinding._sanitise_value()` | Recursive type normalisation |
| Missing resource files | `CoreCacheManager.ensure_resources()` | Download from GitHub, disk-cache |
| Execution error noise | `_classify_errors()` | Filter by known error type strings |
| Crashing rules | `_run_validation_inner()` | Skip rules in `_EXCLUDED_RULES` set |
