# Integration tests

End-to-end tests that wire the assembler to a validation engine. Each test
takes an `AssemblerInput` dict, runs `Assembler.execute`, serialises the
resulting `Wrapper`, and validates the JSON output with d4k or CDISC CORE.

## Why these are separate from `tests/usdm4/assembler/`

The unit tests under `assembler/` exercise individual sub-assemblers in
isolation with mocked dependencies. They're fast and they catch unit-level
regressions.

These integration tests answer a different question: **does the assembler
produce output that passes validation?** That requires a real run of the
whole pipeline, which is slower and depends on the validation engines.
Keeping them separate means `pytest tests/usdm4/assembler` stays snappy and
deterministic.

## What's here

| File | Engine | Run by default? |
| --- | --- | --- |
| `conftest.py` | — | builds the minimum AssemblerInput + assembled JSON fixture |
| `test_assembler_to_d4k.py` | d4k (Python rules) | yes |
| `test_assembler_to_core.py` | CDISC CORE | no — gated on `@pytest.mark.slow` |

## Current state and the baseline tests

Per `docs/assembler_validation_findings.md`, the minimum fixture currently
produces output that flags 16 d4k rules with 54 findings (and 1 rule
exception). Until those findings are addressed, the integration tests use
**baseline assertions** rather than strict pass assertions:

- The number of finding-count, failing-rule-count, and exception-rule-count
  values are pinned to current observed values.
- Tests fail if those counts grow.
- The "all rules pass" test is `xfail`ed with a `strict=False` flag and a
  pointer back to the findings doc.

This is deliberate. A regression test that records "today's broken state"
is not strong protection, but it does catch any change that makes things
worse, which is the most common regression direction. As findings are
fixed and counts come down, lower the baselines (or — better — delete
them entirely and remove the `xfail`).

## Running

```bash
# Default — d4k integration tests
pytest tests/usdm4/integration

# Slow (CORE) tests
pytest -m slow tests/usdm4/integration

# Skip slow tests explicitly
pytest -m "not slow" tests/usdm4/integration
```

## CDISC CORE prerequisites

`test_assembler_to_core.py` skips itself if the cache for USDM v4-0 isn't
populated. To populate it once:

```python
from usdm4 import USDM4
USDM4().prepare_core(version="4-0")
```

CI should do this in a setup step. Setting `USDM4_SKIP_CORE=1` skips the
test unconditionally (use this on a developer laptop where you don't want
to wait for CORE).

## Where the corpus harness lives

`validate/eval_corpus.py` runs the same pipeline against a real protocol
corpus. That's a research / triage tool, not a test. It writes a structured
YAML report and is the right place to evaluate the assembler at scale.
