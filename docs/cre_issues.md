# CORE vs d4k — known issues, divergences and workarounds

Reference for the two validation engines: the d4k Python rule library and the CDISC Rules
Engine (CRE, "CORE"). Read it when CORE and d4k disagree on a rule. It is not a to-do list —
anything here still to be solved is a row in `issues.md` (N6–N8).

**Current target: cdisc-rules-engine 0.16.0.** Counts are from the 234-protocol corpus baseline
`validate/corpus_cre_0_16/engine_diff.md`, frozen 2026-05-02 (5 d4k under-reporting, 13 d4k
over-reporting, 195 aligned, 1 CORE-only). Historical 0.15.x detail is kept where it explains
how a workaround came about.

The baseline predates #54 (2026-08-07), which changed how CORE results are classified
(`executionStatus`, issue 5) and gave `CoreValidator` the bundled USDM schema. CORE-side counts
may move when the corpus is re-run.

The numbered issues 1–10 are also the feedback for the CRE team.

Contents: *Policy* · *Divergence index* · *New divergences* · issues 1–10 · *Summary of
workarounds* · *CRE 0.16.0 upgrade notes* · *Defensibly d4k-stricter*.


## Policy — rule text vs CORE's JSONata

When a DDF rule's English text and CORE's JSONata disagree about what the rule means, **mirror
CORE in the d4k rule** and note the disagreement in the rule's source comment. CORE is the
reference implementation. If the stricter behaviour is wrong in practice, the fix is a spec or
CORE change, not a divergence in the Python. (First captured in `lessons_learned.md` §16.4,
with DDF00010 as the example.)

Two settled exceptions, where the DDF text is ambiguous and d4k keeps its own reading. They are
exceptions, not precedents.

- **DDF00164 / DDF00165 — `"0"` as a section number.** d4k: `displayX=true` iff `X` is truthy;
  `bool("0")` is `True`, so `sectionNumber="0"` counts as specified and a
  `displaySectionNumber=false` is flagged. CORE treats `"0"` as no section. The DDF text ("If a
  section number is to be displayed then a number must be specified and vice versa") doesn't
  decide it. Leave d4k as is unless the spec says `"0"` means unset.
- **DDF00187 — XHTML wrapping of self-namespacing fragments.** A `NarrativeContentItem` whose
  text opens with its own `<div xmlns="http://www.w3.org/1999/xhtml">` passes d4k but CORE flags
  "body has non-whitespace character content". d4k wraps as
  `<html>…<body><div>FRAGMENT</div></body></html>`; CORE wraps straight in `<body>`. Aligning
  needs per-source heuristics; not worth it for one outlier per protocol.


## Divergence index

One row per rule that diverges on the corpus baseline. If a divergence has a row, read the
explanation it points to and stop.

- **Direction** — `under`: CORE finds errors d4k misses. `over`: d4k finds errors CORE doesn't.
- **Files** — corpus protocols (of 234) where it fires.

### d4k under-reporting

| DDF id   | CORE id     | Files | Category    | Explanation |
|----------|-------------|------:|-------------|-------------|
| DDF00010 | CORE-001013 |   204 | CRE issue 8 | § 8         |
| DDF00093 | CORE-000873 |   230 | CRE issue 8 | § 8         |
| DDF00094 | CORE-000814 |   204 | CRE issue 8 | § 8         |
| DDF00151 | CORE-000834 |   204 | CRE issue 8 | § 8         |
| DDF00181 | CORE-001068 |   230 | CRE issue 8 | § 8         |

All five are one upstream bug: CORE visits a `GovernanceDate` shared between
`StudyVersion.dateValues` and `StudyDefinitionDocumentVersion.dateValues` once per parent
reference, not once per instance. d4k is correct; no d4k change.

### d4k over-reporting

| DDF id   | CORE id     | Files | Category                    | Explanation |
|----------|-------------|------:|-----------------------------|-------------|
| DDF00031 | —           |   213 | Open                        | `issues.md` N6 |
| DDF00045 | —           |    25 | Open                        | `issues.md` N6 |
| DDF00075 | —           |   216 | d4k stricter (CT / scope)   | *Defensibly d4k-stricter* |
| DDF00084 | —           |   234 | CRE issue 7 + d4k stricter  | § 7; *Defensibly d4k-stricter* |
| DDF00087 | —           |   210 | Open                        | `issues.md` N6 |
| DDF00088 | CORE-001048 |   177 | Open                        | `issues.md` N6 |
| DDF00110 | —           |   200 | d4k stricter (CT)           | *Defensibly d4k-stricter* |
| DDF00140 | —           |   227 | d4k stricter (CT)           | *Defensibly d4k-stricter* |
| DDF00155 | —           |   234 | d4k stricter (CT)           | *Defensibly d4k-stricter* |
| DDF00166 | —           |   234 | d4k stricter (CT)           | *Defensibly d4k-stricter* |
| DDF00200 | —           |   227 | d4k stricter (CT)           | *Defensibly d4k-stricter* |
| DDF00227 | —           |   234 | Legit data finding          | corpus doesn't populate `studyType`; the rule is right |
| DDF00259 | —           |   227 | d4k stricter (CT)           | *Defensibly d4k-stricter* |

The CT-membership cluster (DDF00075, 084, 110, 140, 155, 166, 200, 259) shares one fingerprint:
d4k's `_ct_check` and rule-side helpers complete where CORE's `codelist_extensible` operation
drops into no-data mode (§ 7). Where d4k flags a real invalid decode or `codeSystemVersion`,
CORE returns pass-or-NA because its operation emitted an execution-error sentinel the wrapper
filters out.

### Workarounds in place (corpus shows aligned)

These would diverge without the workaround. Listed so it isn't removed in a refactor.

| DDF id    | CORE id     | Category      | Workaround |
|-----------|-------------|---------------|------------|
| DDF00114  | CORE-000878 | CRE issue 5/7 | `core_validator.py::_classify_errors` (`executionStatus`, #54) |
| DDF00141  | CORE-000857 | CRE issue 5/7 | `core_validator.py::_classify_errors` |
| DDF00152  | CORE-000840 | CRE issue 5/7 | `core_validator.py::_classify_errors` |
| DDF00161  | —           | CRE issue 10  | `rule_ddf00161.py` (multi-parent allowed-set union) |
| DDF00194  | CORE-000971 | CRE issue 9   | `rule_ddf00194.py` iterates real `Address` instances; null `legalAddress` skipped |
| DDF00237  | CORE-001061 | CRE issue 5/7 | `core_validator.py::_classify_errors` |
| —         | CORE-000955 | CRE issue 6   | `_EXCLUDED_RULES` in `core_validator.py` (rule skipped) |
| —         | CORE-000956 | CRE issue 6   | `_EXCLUDED_RULES` in `core_validator.py` (rule skipped) |

### Resolved between baselines

If one of these diverges again, read the reason before re-investigating.

| DDF id   | Was (0.15.x) | Now (0.16.0)     | Reason |
|----------|--------------|------------------|--------|
| DDF00025 | under=103    | aligned_fail=103 | CORE behaviour change — *CRE 0.16.0 upgrade notes* |
| DDF00229 | under=222    | aligned_fail=222 | CORE behaviour change — *CRE 0.16.0 upgrade notes* |
| DDF00249 | over=200     | aligned (0/0/0)  | d4k rule rewritten — *CRE 0.16.0 upgrade notes* |


## New divergences

1. Look it up in the index. If it has a row, read the explanation — done.
2. Otherwise put it in the first category that fits:
   - **CRE issue n** — known upstream behaviour, one of issues 1–10 below.
   - **d4k stricter** — d4k does work CORE can't (upstream limitation, or wider scope such as
     DDF00082's full schema check). See *Defensibly d4k-stricter*.
   - **Settled exception** — ambiguous DDF text, d4k's reading kept. See *Policy*.
   - **Legit data finding** — d4k is right about the data; CORE misses it.
3. Nothing fits: add the row as **Open** and raise it in `issues.md`.

Refresh the index on a CRE upgrade (re-run the corpus per `validate/README.md`, regenerate
`engine_diff.md`, walk every row) or after a rule change that could move a row. Update the
baseline date and CRE version at the top when you do.

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

### 1c. Main in-memory cache retains per-dataset state across runs

Clearing `dataset_cache` (1a) and resetting `USDMDataService._instance` (1b) is
*still* not sufficient. The `InMemoryCacheService.cache` dict — the main store
written via `.add()` / read via `.get()`, separate from `dataset_cache` — also
accumulates per-file data keyed by dataset *name* rather than by file path
(variable/operation metadata cached during rule evaluation). The **first** file
validated in a process populates these entries; any later file that has a
dataset of the same name reuses the stale entry, which silently changes that
file's rule **scope** (which rules are deemed "in scope" vs "Outside scope") and
therefore its findings.

Observed symptom: `sample_usdm_7.json` yields 3, 13, or 24 findings depending on
which file was validated before it in the same process (3 when validated first /
in isolation). This made any fixed CORE baseline order-dependent and flaky in
the test suite.

**Workaround:** Clear the whole in-memory cache between runs, not just the
dataset cache:

```python
with cache.dataset_cache_lock:
    cache.dataset_cache.clear()
cache.clear_all()
```

This is safe in `core_validator.py` because the shared resources we want to
reuse (USDM rules and CT packages) are re-loaded from the *disk* cache later in
the same validation call. With the full clear, every file validates as if it
were the first → results are deterministic and order-independent.


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
returns error records rather than an empty result. Six error types fall into
this category, four originally observed in CRE 0.15.x and two added after CRE
0.16.0:

- `"Column not found in data"`           (CRE 0.15.x)
- `"Error occurred during dataset preprocessing"`  (CRE 0.15.x)
- `"Error occurred during operation execution"`    (CRE 0.15.x — see issue 7)
- `"Outside scope"`                      (CRE 0.15.x)
- `"Domain not found"`                   (CRE 0.16.0)
- `"Empty dataset"`                      (CRE 0.16.0)

The first and last group indicate that the rule's preconditions were not met for
the entity. The two `"Error occurred during ..."` variants indicate the engine
itself failed mid-rule (e.g. a pandas merge bug on `codeSystemVersion` — see
issue 7). `"Domain not found"` indicates the rule queries a domain (like
`Condition`) that has zero instances in the protocol. `"Empty dataset"`
indicates a dataset became empty after the engine's preprocessing. None are
data quality issues, but they are returned in the same `errors` list as real
validation findings, requiring callers to inspect the `error` field and filter
them out.

In a 234-file corpus run against CRE 0.16.0, the new sentinel strings produced
6336 `"Domain not found"` entries (across CORE-000840/871/878) and 235
`"Empty dataset"` entries (across CORE-000857/001068). Without filtering, these
masquerade as `d4k_under_reporting` on rules where d4k correctly produces zero
findings (DDF00114, DDF00141, DDF00152).

**Workaround:** Since #54 (2026-08-07), `_classify_errors` in
`src/usdm4/core/core_validator.py` follows each result's `executionStatus`, as the CORE CLI
report does: `skipped` is dropped, `issue reported` is a finding, `execution error` goes to
`execution_errors`. The six strings in `_EXECUTION_ERROR_TYPES` are the fallback for results
with no `executionStatus` — how this was handled before #54.

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


## 7. `codelist_extensible` operation crashes with pandas merge type mismatch

> **Status (CRE 0.16.0): symptom changed, outcome unchanged.** A 234-file
> corpus run against 0.16.0 (May 2026) shows that what looked at first like an
> upstream fix is actually a relabelling: the engine no longer crashes on the
> pandas merge but reports the same rules as `"Domain not found"` or
> `"Empty dataset"` execution errors instead. Once the issue 5 sentinel set was
> extended with both new strings, every per-rule outcome reverted to its 0.15.x
> baseline.
>
> | CORE id     | DDF id    | 0.15.x state             | 0.16.0 state (after issue 5 sentinels updated) |
> |-------------|-----------|--------------------------|------------------------------------------------|
> | CORE-000871 | DDF00084  | over=234                 | over=234 (unchanged; pre-filter-update CORE emitted 234 phantom `"Domain not found"` entries, mis-classified as `aligned_fail`) |
> | CORE-000878 | DDF00114  | aligned_pass=234         | aligned_pass=234 (pre-filter-update an apparent under=224 was 6099 phantom `"Domain not found"` entries) |
> | CORE-000857 | DDF00141  | aligned_pass=234         | aligned_pass=234 (pre-filter-update an apparent under=234 was 234 phantom `"Empty dataset"` entries) |
> | CORE-000840 | DDF00152  | aligned_pass=234         | aligned_pass=234 (pre-filter-update an apparent under=3 was 3 phantom `"Domain not found"` entries) |
> | CORE-001061 | DDF00237  | aligned_pass=234         | aligned_pass=234 (no findings either way on this corpus) |
>
> Net read of CRE 0.16.0 for this issue:
>
> - The pandas merge on `codeSystemVersion` no longer crashes — that part is
>   genuinely fixed. The engine now correctly recognises empty-input
>   conditions instead of raising mid-rule.
> - However, CRE 0.16.0 still emits the empty-input recognition as an entry
>   in the rule's `errors` list rather than skipping the rule with no
>   findings. From a consumer's perspective, the leak shape is identical to
>   issue 5; only the sentinel string changed.
> - DDF00084 stays in `d4k_over_reporting` exactly as in 0.15.x. d4k still
>   catches 234 real failures CORE does not. This is a long-standing
>   divergence, not a 0.16 regression and not a 0.16 fix.
> - The `_EXECUTION_ERROR_TYPES` sentinel `"Error occurred during operation
>   execution"` (the original 0.15-era workaround below) is left in place as
>   defence-in-depth against any other rule still hitting the merge path.
>
> Net work required of usdm4 for the upgrade: the two new sentinels
> (`"Domain not found"`, `"Empty dataset"`) added to issue 5's set, plus the
> wrapper-side fix to `validate_single_rule`'s signature change (see
> `core_validator.py` line ~351). No new d4k rules are required for the five
> rules in the table.
>
> The historical analysis below is preserved as an audit trail for the
> original 0.15.x diagnosis.

When the engine evaluates rules backed by the `codelist_extensible` operation,
the underlying pandas merge can fail with:

```
Failed to execute rule operation. Operation: codelist_extensible, Target: None,
Domain: <DomainName>, Error: You are trying to merge on object and float64
columns for key 'codeSystemVersion'. If you wish to proceed you should use
pd.concat
```

The crash is reported as an entry in the rule's `errors` list with
`error: "Error occurred during operation execution"` and the message above.
Because it occupies the same `errors` list as real findings, naïve consumers
will count it as a finding.

In a 234-file run of the protocol_corpus, this single failure mode produced
**6792** spurious "findings" across five rules — every one of them with **zero**
real findings on the same data:

| CORE id    | DDF id    | Spurious errors |
|------------|-----------|----------------:|
| CORE-000840 | DDF00152 |               3 |
| CORE-000857 | DDF00141 |             234 |
| CORE-000871 | DDF00084 |             234 |
| CORE-000878 | DDF00114 |            6099 |
| CORE-001061 | DDF00237 |             222 |

Likely root cause: `codeSystemVersion` is being held as `object` dtype in one
DataFrame and `float64` (most likely because of `NaN` from missing values) in
the other. Pandas refuses the merge.

**Workaround:** We added `"Error occurred during operation execution"` to the
execution-error sentinel set (issue 5). Affected rules now correctly report no
findings on the corpus instead of false positives.

**Suggested fix:** In the `codelist_extensible` operation, coerce the
`codeSystemVersion` column to a common dtype (string) on both DataFrames before
merging. As a defence-in-depth measure, fail the rule cleanly (Exception status,
empty findings) when an internal merge raises rather than emitting the failure
as a finding-shaped error record.


## 8. Cross-reference traversal: shared instances counted twice across containers

**Severity:** Medium — affects five rules so far in the corpus, producing
phantom findings (DDF00181, DDF00010, DDF00151) and inflated counts on real
findings (DDF00093, DDF00094). No caller workaround possible against the
engine itself.

The `dateValues` relationship is the same `GovernanceDate` collection
referenced from two different containers in USDM:

- `StudyVersion.dateValues`
- `StudyDefinitionDocumentVersion.dateValues` ("SDDV")

Five separate rules trip on this shape:

- `CORE-001068` (DDF00181) — uniqueness *within* `SDDV.dateValues`
- `CORE-000873` (DDF00093) — uniqueness *within* `StudyVersion.dateValues`
- `CORE-001013` (DDF00010) — name uniqueness across instances of the same class
- `CORE-000814` (DDF00094) — within a study version, if any date of a given
  type has global geographic scope, no other date of that type is expected
- `CORE-000834` (DDF00151) — if any geographic scope on a `GovernanceDate`
  is global, the date must have exactly one geographic scope

In a 234-file protocol_corpus run, all five rules disagreed with the d4k
implementation in a way that points at the same root cause: when a single
`GovernanceDate` instance (and any nested children, such as its
`geographicScopes`) is referenced from **both** lists, the engine visits it
twice during data traversal. Each rule then sees the second visit as a
separate instance and reports a duplicate or extra entry.

The per-rule counts that result:

### CORE-001068 / DDF00181 — phantom findings

| `SDDV.dateValues` count | `StudyVersion.dateValues` count | shared id with SDDV? | files | CORE finds | actually duplicated? |
|------------------------:|--------------------------------:|----------------------|------:|-----------:|----------------------|
|                       1 |                               2 | yes                  |   203 |          2 | no                   |
|                       0 |                               0 | n/a                  |    29 |          0 | no                   |
|                       1 |                               1 | yes                  |     1 |          0 | no                   |
|                       0 |                               1 | n/a                  |     1 |          0 | no                   |

Across all 234 files **zero** have any real duplicate `(type.code,
geographicScopes)` group inside `SDDV.dateValues`. The 231 failing CORE
findings are all phantom.

### CORE-000873 / DDF00093 — inflated counts on real findings

| classification | files | d4k count | CORE count | true count |
|---|---:|---:|---:|---:|
| `count_mismatch`  (real dup, inflated) | 203 |  2 |  3 |  2 |
| `core_only`       (no dup, phantom)    |  26 |  0 |  1 |  0 |
| `core_only`       (no dup, phantom)    |   1 |  0 |  2 |  0 |
| `aligned_pass`    (empty dateValues)   |   4 |  0 |  0 |  0 |

The d4k count matches the ground-truth violation count on **all 234 files**.
The CORE count for any file equals d4k_count + (number of `GovernanceDate`
ids appearing in both `SDDV.dateValues` and `StudyVersion.dateValues`).

### CORE-001013 / DDF00010 — phantom name-uniqueness findings

| classification | files | d4k count | CORE count | true count |
|---|---:|---:|---:|---:|
| `core_only`       (phantom)            | 204 |  0 |  2 |  0 |
| `aligned_pass`    (no shared dateValue) |  30 |  0 |  0 |  0 |

Across all 234 files **zero** have any genuine cross-instance name collision.
On the 204 affected files every CORE finding is two error rows for the **same
instance_id** (e.g. `GovernanceDate_1`) seen at two different paths
(`/study/versions/0/dateValues/1` and
`/study/documentedBy/0/versions/0/dateValues/0`). CORE's group-by-name logic
treats those as two distinct GovernanceDates, then complains that they share
the same `name`. The d4k rule iterates `data._ids` (id-keyed), so the shared
instance appears once and no false collision arises.

### CORE-000814 / DDF00094 — inflated counts on global-scope uniqueness

| classification | files | d4k count | CORE count | true count |
|---|---:|---:|---:|---:|
| `count_mismatch`  (real violation, inflated) | 203 |  2 |  3 |  2 |
| `core_only`       (no violation, phantom)    |   1 |  0 |  2 |  0 |
| `aligned_pass`    (empty/unshared)           |  30 |  0 |  0 |  0 |

Identical fingerprint to DDF00093: d4k count matches the ground-truth
violation count on **all 234 files**, and the CORE count is exactly d4k_count
+ (number of cross-referenced `GovernanceDate` ids whose scope feeds the
violation). The shared `GovernanceDate.geographicScopes[*]` is visited via
both `StudyVersion.dateValues[*].geographicScopes[*]` and
`SDDV.dateValues[*].geographicScopes[*]`, so the global-scope condition fires
once per visit instead of once per real GovernanceDate.

### CORE-000834 / DDF00151 — phantom "more than one scope" findings

| classification | files | d4k count | CORE count | true count |
|---|---:|---:|---:|---:|
| `core_only`       (phantom)         | 204 |  0 |  2 |  0 |
| `aligned_pass`    (empty/unshared)  |  30 |  0 |  0 |  0 |

Across all 234 files **zero** `GovernanceDate` instances have more than one
geographic scope when one of those scopes is global. On the 204 affected
files every `GovernanceDate` has exactly one (global) scope, but CORE
reaches that single scope via both `StudyVersion.dateValues[*]` and
`SDDV.dateValues[*]`, sees it twice, and concludes the date has "2 scopes"
when global expects 1. Both error rows on each file cite the same
`instance_id` (the shared `GovernanceDate`).

### Mechanism

In the typical protocol_corpus shape (203/234 files), `SDDV.dateValues =
[GovernanceDate_1]` and `StudyVersion.dateValues = [GovernanceDate_1,
GovernanceDate_2]`. The shared id `GovernanceDate_1` is being counted twice
within whichever container's rule is running, because the engine's data
traversal visits it via both containers' `dateValues` references rather than
restricting to the rule's own container.

- DDF00181 (1 direct entry → counts as 2): the result is a phantom finding.
- DDF00093 (2 direct entries with a real `(type, scope)` collision → counts
  as 3): the violation is real but the count is off by the number of
  cross-referenced ids.
- DDF00010 (one shared `GovernanceDate` reached via two paths → counts as 2
  instances with the same `name`): phantom name-uniqueness violation. This
  rule's data scope is "all instances", so anything that surfaces an instance
  twice in the engine's traversal is enough to manufacture a false finding.
- DDF00094 (one shared `GovernanceDate` whose scope is reached via two
  paths → its global-scope condition fires twice): same shape as DDF00093
  but at the geographic-scope layer; same off-by-cross-reference count
  inflation.
- DDF00151 (one global geographic scope reached via two paths → counted
  as 2 scopes when global expects exactly 1): purely phantom; the
  `GovernanceDate` actually has one scope, but the engine sees it twice.

**Workaround:** None at the engine level — the false positives and inflated
counts are emitted as genuine findings, not execution errors, so issue 5's
sentinel mechanism cannot filter them. The d4k Python rules
(`src/usdm4/rules/library/rule_ddf00181.py`,
`src/usdm4/rules/library/rule_ddf00093.py`,
`src/usdm4/rules/library/rule_ddf00010.py`,
`src/usdm4/rules/library/rule_ddf00094.py`, and
`src/usdm4/rules/library/rule_ddf00151.py`) each work from id-keyed structures
(direct list iteration for the dateValues rules, `data._ids` for the
name-uniqueness rule, and `instances_by_klass` for the per-`GovernanceDate`
rules), so a shared instance is visited exactly once.

**Suggested fix:** Make the engine's traversal id-aware so a single instance
visited via multiple parent references is treated as a single instance, not
multiple. For the dateValues uniqueness rules specifically, the JSONata /
Record Data condition should also restrict the rule's data scope to the
container's *direct* `dateValues` entries. Verifying both layers — engine-wide
de-duplication of cross-referenced instances **and** per-rule scope discipline
— should surface the same bug at all three points (and likely others not yet
exercised by the corpus).


## 9. Missing relation reported as a blank instance (no identity)

**Severity:** Low — false positive when an optional relation is null

When a rule scoped to a relation type encounters a `null` reference, the engine
emits a finding shaped as if the relation existed but had every attribute
blank. The finding has no `path`, no `instance_id`, no `entity` — only a
`details` dict listing each declared attribute as `Missing`.

### Example — CORE-000971 / DDF00194

DDF text: *"At least one attribute must be specified for an address."*

Run against `validate/sample_usdm_3.json` (re-run 2026-05-01 17:40 with the
issue 5 + 7 leak fix in place). The file has six `Organization` instances —
five with a populated `legalAddress`, one (`Organization_5` / "WHO") with
`legalAddress: null`. There are five Address instances, none of them blank.

CORE emits:

```yaml
- rule_id: CORE-000971
  description: At least one attribute must be specified for an address.
  message: All attributes of the address are blank.
  errors:
  - details:
      city: Missing
      country: Missing
      district: Missing
      lines: Missing
      postalCode: Missing
      state: Missing
      text: Missing
```

No `path`, no `instance_id`, no `entity`. The "all-blank Address" being
reported does not exist — it's the absence of `legalAddress` on
`Organization_5`.

The V4 API model (`src/usdm4/api/organization.py`) declares the relation as
optional:

```python
legalAddress: Union[Address, None] = None
```

The DDF text scopes the rule to addresses, not to organizations that ought to
have one. d4k's mirror rule (`src/usdm4/rules/library/rule_ddf00194.py`)
iterates `data.instances_by_klass("Address")` and never visits a null
reference, so the rule is correctly silent. The same pattern applies to the V3
twin `DDF00045`.

**Workaround:** None at the engine level — the finding is shaped like a real
validation result, not an execution error, so the issue 5 sentinel mechanism
cannot filter it. Callers must recognise findings that lack instance identity
as the missing-relation case.

**Suggested fix:** Either (a) skip the rule when its scope target resolves to
null and rely on a separate cardinality rule for "Organization must have a
legalAddress" if that semantic is intended, or (b) emit the finding against
the parent (`Organization`) so it carries a real instance_id and path. The
current shape is ambiguous between "bug in the data" and "the rule didn't
have anything to evaluate".


## 10. JSONata `in` operator doesn't flatten nested arrays — affects DDF00161 on multi-parent activities

**Affected rule:** DDF00161 (Activity preorder-walk consistency).

**Symptom.** When an Activity appears as a child in two different parents'
`childIds` lists, CORE produces extra `count_mismatch` findings for valid
siblings. On a sample where Activity_23 and Activity_24 each have two
parents, d4k reported 2 findings while CORE reported 4.

**Mechanism.** CORE's JSONata predicate is shaped like:

```text
$pacts[self in children.id].[id, children[id!=self].id,
                             children[id!=self].**.children.id]
```

For multi-parent activities this produces a nested array
`[[id1, [siblings1], [deep1]], [id2, [siblings2], [deep2]]]`. JSONata's
`in` operator does not flatten across the inner sibling arrays, so valid
siblings that appear in CORE's own reported "Parent Activity's other
descendants' ids" still fail the `in` check, generating spurious findings.

**d4k workaround.** `rule_ddf00161.py` builds the parent-of map across
all parents (not single-parent / last-writer-wins) and explicitly unions
the allowed set across them. d4k handles multi-parent activities
correctly; CORE does not.

**Suggested fix (upstream).** Flatten the array before applying `in`, or
restructure the predicate so each parent's allowed set is evaluated
independently and unioned afterwards.


## Summary of workarounds in usdm4

All workarounds are implemented in `src/usdm4/core/core_validator.py` and
`src/usdm4/core/core_validation_result.py`. The key interventions:

| Issue | Location | Workaround |
|-------|----------|------------|
| Singleton dataset_cache not clearing | `_run_validation_inner()` | Clear `dataset_cache` before each run |
| Singleton main cache not clearing | `_run_validation_inner()` | `cache.clear_all()` before each run (§1c) |
| USDMDataService singleton | `_run_validation_inner()` | Set `USDMDataService._instance = None` |
| Working directory mutation | `_execute_validation()` | Save/restore `os.getcwd()` in try/finally |
| Stdout pollution | `_run_validation()` | Redirect sys.stdout/stderr to StringIO |
| JList in results | `CoreRuleFinding._sanitise_value()` | Recursive type normalisation |
| Missing resource files | `CoreCacheManager.ensure_resources()` | Download from GitHub, disk-cache |
| Execution error noise | `_classify_errors()` | Follow `executionStatus` (#54); the 6 known error strings are the fallback for results without one |
| `codelist_extensible` pandas crash | `_classify_errors()` | CRE 0.16.0 stopped crashing but reports the same condition via `"Domain not found"` / `"Empty dataset"` sentinels (see issue 7); original `"Error occurred during operation execution"` sentinel retained as defence-in-depth |
| Cross-reference traversal (DDF00181, DDF00093, DDF00010, DDF00094, DDF00151) | n/a (CRE-side bug) | d4k rules `rule_ddf00181.py`, `rule_ddf00093.py`, `rule_ddf00010.py`, `rule_ddf00094.py`, `rule_ddf00151.py` work from id-keyed structures — see issue 8 |
| Missing relation reported as blank instance (CORE-000971 / DDF00194) | n/a (CRE-side bug) | d4k iterates real `Address` instances; null `legalAddress` on `Organization` is correctly skipped — see issue 9 |
| JSONata `in` flattening (DDF00161 multi-parent activities) | n/a (CRE-side bug) | `rule_ddf00161.py` tracks all parents and unions allowed sets — see issue 10 |
| Crashing rules | `_run_validation_inner()` | Skip rules in `_EXCLUDED_RULES` set |


## CRE 0.16.0 upgrade notes (May 2026)

### What broke when 0.16.0 was first installed

`RulesEngine.validate_single_rule` lost its `datasets` positional argument (now
takes only `(self, rule)` — datasets are reached internally via
`self.data_service`). Our wrapper at `core_validator.py` line ~352 still passed
`datasets`, raising `TypeError: validate_single_rule() takes 2 positional
arguments but 3 were given` on every rule. The bare `except Exception:` in the
same loop swallowed the TypeError and recorded it as `"Rule execution
crashed"`, then issue 5's filter promoted it to a non-finding execution error,
producing 0 findings on every protocol — including the well-formed CDISC Pilot
— while reporting `is_valid: true`. Symptom looked like a deep upstream
regression; root cause was a 1-line API change.

### Wrapper changes made for the upgrade

1. **`core_validator.py` line ~352** — drop the `datasets` argument:
   `rules_engine.validate_single_rule(rule)`.
2. **`core_validator.py` line 318** — remove the now-unused
   `datasets = rules_engine.data_service.get_datasets()` local.
3. **`core_validator.py` lines ~365–372** — bind the swallowed exception as
   `exc` and store `repr(exc)` under a new `detail` key on the execution
   error record, so the next CRE upgrade reveals problems immediately.
4. **`core_validator.py` `_EXECUTION_ERROR_TYPES`** — add `"Domain not found"`
   and `"Empty dataset"` (issue 5).

### Net behaviour change vs CRE 0.15.x (234-file corpus)

After all four wrapper changes, three rules genuinely moved between buckets:

| Rule | 0.15.x | 0.16.0 | Reading |
|---|---|---|---|
| DDF00025 | under=103 | aligned_fail=103 | CORE and d4k now agree on 103 failures |
| DDF00229 | under=222 | aligned_fail=222 | CORE and d4k now agree on 222 failures |
| DDF00249 | over=200 | aligned (0/0/0) | d4k rule rewritten between baselines (not a CRE side-effect) — see follow-ups below |

All other 211 rules are in the same bucket as 0.15. In particular, issue 7
DDF00084 stays in `over=234`, and the issue 8 cross-reference traversal rules
(DDF00010/093/094/151/181) stay in their respective `under`/`over` buckets —
0.16.0 did not address that bug.

### DDF00249 — resolved, not a CRE issue

The d4k rule was rewritten between the 0.15 and 0.16 baseline runs. The original auto-generated
stub iterated `EligibilityCriterion` and called `.get("criterionItem")` — a
non-existent field on the API model (the real field is `criterionItemId`) — so it fired on
every criterion regardless of data, which is what the 0.15 corpus run captured. The
current rule at `src/usdm4/rules/library/rule_ddf00249.py` correctly walks
`criterionItemId` references and reports unused `EligibilityCriterionItem` instances; on
the 234-file corpus there are zero. The 0.15 baseline's `over=200` was therefore the
*buggy* number, not a CRE-related signal, and 0.16's `aligned (0/0/0)` is the correct one.
The rule rewrite predates the 0.16 baseline run.

### Still open

Always-suppressed engine output is open (`issues.md` N8). The sentinel-string burden was
removed by #54 (`executionStatus`); raising it upstream is part of N7.


## Defensibly d4k-stricter — won't change

For the record, d4k is legitimately stricter than CORE on these cases —
by design, not bug. Don't reach for a CRE-issue framing when investigating
divergences on these rules.

- **DDF00082** — d4k validates the JSON against
  `src/usdm4/rules/library/schema/usdm_v4-0-0.json` (full JSON Schema). CORE
  handles schema-shape checks outside its rule engine. d4k will surface
  schema findings (missing required fields, wrong types, cardinality
  violations) that CORE doesn't. Scope difference, not a divergence to fix.

- **CT-membership family — on the corpus baseline DDF00075, 00084, 00110, 00140, 00155,
  00166, 00200, 00259; seen earlier on the samples also DDF00051, 00249.**
  d4k's `_ct_check` and the rule-side helpers complete correctly when
  CORE's `codelist_extensible` dtype merge fails (see issue 7). On samples
  where CORE drops into "no data" mode for these rules, d4k continues to
  surface real CT-membership issues (invalid decode, invalid
  `codeSystemVersion`, missing criterion item, etc.). Keep flagging — d4k
  is doing real work CORE can't.
