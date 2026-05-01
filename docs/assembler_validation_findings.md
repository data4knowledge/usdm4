# Assembler validation findings

**Date:** 2026-05-01
**Corpus:** `~/Documents/github/protocol_corpus` (235 protocol directories)
**Engines exercised:** d4k (the usdm4 Python rule library)
**Engines deferred:** CDISC CORE — not yet exercised because no corpus protocol reaches the validation stage. The integration test for CORE is wired and skipped pending a non-empty assembled study from the corpus. Cache populated at the default location per the user.

This document originally proposed a list of bugs found by running the assembler over the corpus. The first five bugs have now been fixed and are marked applied. The remaining sections record what's still open after that pass.

## How the corpus shape relates to AssemblerInput

The corpus extraction pipeline emits `unvalidated.content` blocks shaped *almost* like `AssemblerInput`. The mismatches are:

| Corpus field | Corpus shape | `AssemblerInput` today | Status |
| --- | --- | --- | --- |
| `soa` | `list[TimelineInput-shaped]` (one main + N sub-timelines) | `TimelineInput \| None` (single) | **Open.** Per the user this is the intended long-term design — USDM4 needs to widen. Adapter currently collapses to first entry. |
| `identification.roles[*]` keys | `sponsor`, `co-sponsor` (hyphenated) | `dict[str, ...]` (any string) | **Resolved.** Schema accepts. Sponsor is created via the identifier scope, not the role loop. The role loop now skips unknown role keys with a warning instead of crashing. |
| `identification.identifiers[*].scope` | exactly one of `standard` / `non_standard` | both keys present (one `None`) after Pydantic normalisation | **Resolved.** Assembler now uses `scope.get("standard")` truthy check. |
| `identification.identifiers[*].scope.non_standard.type` | a role label like `"sponsor"` | expected to be an ORG_CODES key like `pharma`, `cro`, `academic` | **Adapter-bridged.** Corpus owes USDM4 the schema-correct shape (`type: pharma, role: sponsor`). Until the corpus extractor is updated, the adapter remaps unknown `type` values to `role` and defaults `type` to `pharma`. |

`validate/corpus_adapter.py` performs the smallest possible bridge: collapses `soa` to its first entry (loses sub-timelines until #6 ships), normalises `co-sponsor` → `co_sponsor`, drops role keys the assembler doesn't know (now redundant since the assembler skips them itself; safe to remove), and runs the input through Pydantic to inject defaults (also now redundant since the assembler does this itself; safe to remove).

## Headline numbers (with adapter, post-fix, no CORE)

```
Total protocols                                     235
  load_failed (no ground_truth.yaml)                  1   (CORP0020)
  assemble_failed                                   234

First-failing sub-assembler:
  215  AmendmentsAssembler   (enrollment dict is None — see Finding 7)
   19  Builder               (StudyDesignPopulation name='' — see Finding 8)
```

Compared to the pre-fix run, every protocol still fails to assemble — but the failure points have moved several layers deeper into the pipeline. The `IdentificationAssembler` no longer blocks anything; the `DocumentAssembler` no longer blocks the empty-sections case. The remaining blockers are a different family of issue (see Findings 7 and 8).

## Findings — fixed in this pass

### Finding 1 — `Assembler.execute` discarded its own validated dict — **FIXED**

**Was:** `assembler.py:80-91` validated input against `AssemblerInput` and then forwarded the *original* dict, so schema-injected defaults (`other.sponsor_signatory=None`, `non_standard.legalAddress=None`, role addresses, etc.) were never visible to sub-assemblers.

**Fix:** `data = validated.model_dump(by_alias=True)` after the validate. `by_alias=True` is preserved so the `global` alias on `amendments.impact.global` (aliased from `global_`) keeps working — `amendments_assembler.py:313` indexes by alias.

### Finding 2 — `if "standard" in scope:` was broken once defaults were present — **FIXED**

**Was:** `identification_assembler.py:407,425` — tested key presence instead of truthiness; misfired on every normalised scope dict (because Pydantic adds both keys with one set to `None`).

**Fix:** `if scope.get("standard"):` — truthy check. Also tightened the `non_standard` dereference at line 437 to `scope.get("non_standard") or {}`.

### Finding 3 — Role loop crashed on roles not in `ROLE_ORGS` — **FIXED**

**Was:** `ROLE_ORGS` has no entry for `sponsor` (or for `cro`, `investigator`). The role loop did `ROLE_ORGS[role]`, which raised `KeyError: 'sponsor'` on every corpus protocol. The KeyError was caught by the per-iteration try/except, but the next unconditional access (`data["other"]["sponsor_signatory"]` at line 516) escaped because `other` wasn't in the dict — terminating the whole assembler. Net effect: 234 / 234 protocols failed before assembly produced anything.

**Fix:** Sponsor is wired through the identifier scope, as the user clarified. The role loop now normalises hyphens to underscores, skips role keys not present in `ROLE_ORGS` with a warning, and keeps going. The `data["other"][...]` accesses are now guarded by `.get()`. One existing unit test had to flip its expectation (unknown role → warning, not error).

### Finding 4 — `DocumentAssembler._section_to_narrative` IndexError on empty sections — **FIXED**

**Was:** `document_assembler.py:185` indexed `sections[0]` without checking that `sections` was non-empty. `DocumentInput.sections: list[...] = []` is a valid shape (corpus emits empty section lists for several CORP* protocols).

**Fix:** Early-return when `not sections or index >= len(sections)`.

### Finding 5 — `_create_address(None)` raised TypeError — **FIXED**

**Was:** `_create_address` iterated its argument before checking for falsiness; `argument of type 'NoneType' is not iterable` whenever a role/org didn't carry an address.

**Fix:** Early-return `None` on falsy input.

## `non_standard.type` overload — bridged by the adapter

The corpus emits identifier scopes like:

```yaml
identifiers:
- identifier: "18852"
  scope:
    non_standard:
      type: sponsor          # corpus uses `type` to mean "what role"
      name: "Eli Lilly and Company"
      label: "Sponsor identifier"
```

But the USDM4 schema's `NonStandardOrganization` already separates these:

```python
class NonStandardOrganization(BaseModel):
    type: str               # org kind: pharma / cro / academic ...
    role: str | None = None # what role this org plays
```

The corpus is putting the role label into `type` and leaving `role: None`. The corpus extractor needs to be updated to match the USDM4 schema; until that lands, `validate/corpus_adapter.py` performs the remap: when `non_standard.type` isn't a valid `ORG_CODES` key, it moves the value to `role` and sets `type` to `"pharma"`. Surfaces in the per-protocol record as `adapter.non_standard_type_remapped`. Affects 215 / 234 corpus protocols.

## Findings — still open

### Finding 6 — `AssemblerInput.soa` should accept a list — **OPEN, USDM4 design change**

`AssemblerInput.soa` accepts a single `TimelineInput`; the corpus (and the user's stated design) carries one main timeline plus several sub-timelines. The adapter collapses to the first entry today, dropping sub-timelines on 63 protocols.

**Suggested fix direction:** widen `AssemblerInput.soa` to `list[TimelineInput]` and update `TimelineAssembler.execute` to iterate. The first list element drives the main study timeline; subsequent entries become sub-timelines (the existing USDM `Timeline` type already supports parent/child relationships).

### Finding 7 — `AmendmentsAssembler._create_enrollment` accesses `data["enrollment"]["unit"]` unconditionally — **OPEN**

**File:** `src/usdm4/assembler/amendments_assembler.py:263`

```python
if data["enrollment"]["unit"] in ("%", "percent", "percentage"):
```

After the Finding 1 fix, `data["enrollment"]` is `None` (Pydantic-injected default) on every corpus protocol — none have enrollment data extracted. The `[None]["unit"]` access raises `TypeError: 'NoneType' object is not subscriptable`. Same family of bug as Findings 2/3 — assumes a value where the schema permits None.

**Suggested fix direction:** guard with `if data.get("enrollment") and data["enrollment"].get("unit") in (...)`. Same pattern likely applies to the rest of `_create_enrollment` and to the upstream `_create_amendment` callsite.

**Affects:** 215 / 234 corpus protocols (all NCT*).

### Finding 8 — `StudyDesignPopulation` requires non-empty `name`, corpus passes empty — **OPEN, requires a decision**

**Files:** corpus extractor (population), `src/usdm4/api/population_definition.py` (Pydantic constraint).

Pydantic raises `String should have at least 1 character` when the assembler tries to create a `StudyDesignPopulation` with `name=''`. The empty name comes from the corpus's `population.label = ''` for CORP* protocols.

This sits between USDM4 and the corpus — neither side is obviously wrong:

- The USDM4 API model insists on a non-empty name (reasonable).
- The corpus has no population label extracted yet for these 19 protocols (the `population` extractor hasn't run).
- The assembler could synthesise a placeholder, but that would mask missing data.

**Affects:** 19 / 234 corpus protocols (CORP*). These would need either a real population label from the corpus extractor, or a decision to synthesise one in the assembler.

### Likely deeper layers

We didn't probe past Findings 7 and 8. Based on the pattern, expect more `data["x"]["y"]` patterns in `StudyDesignAssembler`, `StudyAssembler`, and possibly `PopulationAssembler` once the current blockers are removed. A targeted grep for `data\[["']\w+["']\]\[` across `src/usdm4/assembler/` would surface them quickly.

## Why no CORE numbers yet

CORE consumes the assembled USDM JSON. Zero corpus protocols reach assembly, so CORE would either skip or run on a degenerate object. The harness is wired (`--cache-dir` plumbed; CORE test in the integration suite); drop `--no-core` once any corpus protocol assembles cleanly.

## Side note: minimum fixture isn't conformant either

The integration tests use a hand-rolled minimum `AssemblerInput` (not from the corpus). On that fixture, d4k now flags 19 rules with 66 findings (and 1 rule exception) — both numbers are slightly higher than pre-fix (was 18 / 54 / 1) because the assembler now produces *more* output (defaults populated, role loop continues), so more rules find things to evaluate. This is forward progress, not regression. Baselines in `test_assembler_to_d4k.py` are pinned to the new numbers.

## Files added / changed in this work

Added:
- `validate/eval_corpus.py` — corpus harness (assemble + d4k + optional CORE).
- `validate/corpus_adapter.py` — corpus → `AssemblerInput` adapter. Now redundant for two of its three transforms (Pydantic injection and unknown-role-key dropping); the SoA list-collapse remains the only essential transform until Finding 6 ships.
- `tests/usdm4/integration/` — pipeline regression tests with baseline assertions.

Changed:
- `src/usdm4/assembler/assembler.py` — Finding 1 fix.
- `src/usdm4/assembler/identification_assembler.py` — Findings 2, 3, 5 fixes.
- `src/usdm4/assembler/document_assembler.py` — Finding 4 fix.
- `tests/usdm4/assembler/test_identification_assembler.py` — two test expectations updated.
- `tests/usdm4/integration/test_assembler_to_d4k.py` — baselines updated for the new "more output" numbers.
- `pytest.ini` — registered `slow` marker for the CORE integration test.
