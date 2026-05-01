"""Integration: minimum AssemblerInput -> assemble -> validate_core (CDISC CORE).

CORE conformance is the gating standard for "is this a valid USDM document?"
This test pins the minimum fixture against CORE. It is gated by:

  * the ``slow`` pytest marker (CORE downloads + executes ~hundreds of
    rules and is genuinely slow on a cold cache), and
  * a skip-if-cache-not-populated check (CORE needs a populated cache to
    run; in CI the cache is provisioned in a setup step, but locally a
    developer who hasn't pre-cached should not have this test fail).

Run::

    pytest -m slow tests/usdm4/integration/test_assembler_to_core.py
    # or, explicitly:
    pytest -m slow tests/usdm4/integration -k core

If the test fails with FAILURE rules, look at the per-rule list it prints —
those are real CDISC CORE conformance gaps in what the assembler emits and
should be tracked as findings, not test bugs.
"""

from __future__ import annotations

import os
import pathlib

import pytest

from usdm4 import USDM4


pytestmark = [pytest.mark.slow]


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
    """CORE validation on the minimum assembled study must report is_valid."""
    if os.environ.get("USDM4_SKIP_CORE"):
        pytest.skip("USDM4_SKIP_CORE set in environment")
    if not _cache_populated(usdm4_facade):
        pytest.skip(
            "CDISC CORE cache is not populated for version 4-0. "
            "Run USDM4().prepare_core() once to populate, "
            "or set USDM4_SKIP_CORE=1 to skip this test entirely."
        )

    result = usdm4_facade.validate_core(str(assembled_study_json_path))

    if not result.is_valid:
        # Build a compact summary so the test failure is actionable.
        lines = [
            f"CORE reported {result.finding_count} finding(s) "
            f"across {len(result.findings)} rule(s):"
        ]
        for f in sorted(result.findings, key=lambda x: x.rule_id):
            lines.append(f"  {f.rule_id}: {len(f.errors)} error(s)")
        if getattr(result, "execution_error_count", 0):
            lines.append(
                f"({result.execution_error_count} execution errors filtered)"
            )
        pytest.fail("\n".join(lines))
