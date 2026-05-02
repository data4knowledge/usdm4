"""Integration: minimum AssemblerInput -> assemble -> validate_core (CDISC CORE).

This test runs the assembler over the minimum fixture and validates the
result with CDISC CORE. The minimum fixture isn't fully CORE-conformant
(known gaps include missing primary endpoint, planned timeline duration,
schema-level support for objectives/endpoints, encoder gaps for
trial_phase, sponsor StudyRole emission, and others — see fixture commit
history and ``docs/`` for context).

Rather than fail outright on those known gaps, the test pins the set of
rule ids currently failing as ``_KNOWN_FAILING_RULES`` and behaves as a
regression detector:

  * passes when ``result.is_valid`` (no findings — desired end state);
  * passes when the failing rule-id set exactly matches the baseline;
  * fails when new rules appear (regression) or known rules clear
    (improvement — the maintainer should remove them from the set).

Per-rule error counts are not pinned, only the set of failing rule ids,
so small CRE-side count drift won't churn the test.

Gated by:

  * the ``slow`` pytest marker (CORE downloads + executes ~hundreds of
    rules and is genuinely slow on a cold cache);
  * a skip-if-cache-not-populated check (CORE needs a populated cache;
    locally a developer who hasn't pre-cached should not have this test
    fail).

Run::

    pytest -m slow tests/usdm4/integration/test_assembler_to_core.py
    # or, explicitly:
    pytest -m slow tests/usdm4/integration -k core
"""

from __future__ import annotations

import os
import pathlib

import pytest

from usdm4 import USDM4


pytestmark = [pytest.mark.slow]


# Frozen baseline of CORE rule ids currently failing on the minimum
# assembled study, captured 2026-05-02. Update this set (in either
# direction) when the assembler / fixture / CRE changes the set of rules
# that fire — the test will tell you which to add or remove.
_KNOWN_FAILING_RULES = frozenset(
    {
        "CORE-000815",
        "CORE-000854",
        "CORE-000856",
        "CORE-000857",
        "CORE-000858",
        "CORE-000879",
        "CORE-000904",
        "CORE-000905",
        "CORE-000925",
        "CORE-000930",
        "CORE-000931",
        "CORE-000933",
        "CORE-000942",
        "CORE-000943",
        "CORE-000951",
        "CORE-000959",
        "CORE-000972",
        "CORE-000973",
        "CORE-000988",
        "CORE-001016",
        "CORE-001036",
        "CORE-001054",
        "CORE-001058",
        "CORE-001059",
        "CORE-001065",
        "CORE-001076",
        "CORE-001077",
    }
)


def _cache_populated(usdm: USDM4) -> bool:
    """True if the CDISC CORE cache appears populated for v4-0.

    We don't want to fail the test on a developer machine that simply hasn't
    run ``usdm.prepare_core()`` yet — instead we skip with a clear message.
    """
    try:
        status = usdm.core_cache_status(version="4-0")
    except Exception:
        return False
    # CacheStatus exposes ``ready`` (bool); fall back to truthiness on older
    # versions so the check is forward-compatible.
    return bool(getattr(status, "ready", status))


def test_core_minimum_assembled_study(
    assembled_study_json_path: pathlib.Path, usdm4_facade: USDM4
) -> None:
    """CORE validation on the minimum assembled study.

    Passes when CORE is_valid OR when the failing rule-id set matches
    ``_KNOWN_FAILING_RULES`` exactly. See module docstring.
    """
    if os.environ.get("USDM4_SKIP_CORE"):
        pytest.skip("USDM4_SKIP_CORE set in environment")
    if not _cache_populated(usdm4_facade):
        pytest.skip(
            "CDISC CORE cache is not populated for version 4-0. "
            "Run USDM4().prepare_core() once to populate, "
            "or set USDM4_SKIP_CORE=1 to skip this test entirely."
        )

    result = usdm4_facade.validate_core(str(assembled_study_json_path))

    if result.is_valid:
        return

    actual = frozenset(f.rule_id for f in result.findings)
    if actual == _KNOWN_FAILING_RULES:
        return  # known gaps unchanged — regression detector at rest

    new_rules = sorted(actual - _KNOWN_FAILING_RULES)
    cleared_rules = sorted(_KNOWN_FAILING_RULES - actual)
    lines = ["CORE failing rule-id set differs from baseline:"]
    if new_rules:
        lines.append(
            f"  New rules (regression — fix or add to _KNOWN_FAILING_RULES): "
            f"{new_rules}"
        )
    if cleared_rules:
        lines.append(
            f"  Cleared rules (improvement — remove from _KNOWN_FAILING_RULES): "
            f"{cleared_rules}"
        )
    lines.append(
        f"  Totals: {result.finding_count} error(s) across "
        f"{len(result.findings)} rule(s)"
    )
    if getattr(result, "execution_error_count", 0):
        lines.append(f"  ({result.execution_error_count} execution errors filtered)")
    pytest.fail("\n".join(lines))
