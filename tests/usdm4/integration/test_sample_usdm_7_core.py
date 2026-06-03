"""Integration: validate sample_usdm_7.json with the CDISC CORE engine.

Companion to `test_sample_usdm_7_d4k.py`. Same fixture file, different
engine — pins the exact set of CORE rule ids that fire on
`tests/usdm4/test_files/integration/sample_usdm_7.json` so engine-side
drift surfaces.

Gating mirrors `test_assembler_to_core.py`:

  * marked `slow` — CORE is genuinely slow and runs hundreds of rules;
  * skipped if the CORE cache for v4-0 isn't populated;
  * skipped if `USDM4_SKIP_CORE` is set (developer escape hatch).

Run::

    pytest -m slow tests/usdm4/integration/test_sample_usdm_7_core.py

Not executed in the Cowork sandbox.
"""

from __future__ import annotations

import os
import pathlib

import pytest

from usdm4 import USDM4


pytestmark = [pytest.mark.slow]


# ---------------------------------------------------------------------------
# Sample-file resolution
# ---------------------------------------------------------------------------
#
# Anchored to the test file's location, not cwd, so the test passes
# regardless of where pytest is invoked from.

SAMPLE_PATH: pathlib.Path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "test_files/integration/sample_usdm_7.json"
)


# Baseline captured empirically against sample 7 with CRE 0.16.0
# (the version pinned by `setup.py`, `cdisc-rules-engine>=0.16.0`).
# 3 rules fire, stable across repeated runs.
#
# This is a *drift-detector* set, not a conformance claim. Reading guide:
#
#  - The 2 *real* protocol-level findings (DDF rules d4k also flags)
#    are `CORE-001016` (DDF00153, main timeline plannedDuration) and
#    `CORE-001065` (DDF00101, no procedure→intervention link).
#  - `CORE-000971` (DDF00194, address-all-attributes-blank) is the
#    CRE issue 9 phantom — null `legalAddress` on Organization is
#    materialised as a blank Address by CRE's traversal; d4k's
#    `rule_ddf00194.py` correctly iterates real Address instances and
#    skips this. It was previously kept out of the baseline as flaky; on
#    CRE 0.16.0 it fires consistently, so it is now pinned here.
#
# Note: an earlier baseline pinned 24 rules. That set was an artefact of
# CRE singleton-cache contamination — when another CORE validation ran
# *first* in the same process (e.g. test_assembler_to_core), it left
# per-dataset state in the engine cache that changed sample 7's rule
# scope (sample 7 yielded 3 / 13 / 24 findings depending on what ran
# before it). The wrapper now fully clears the in-memory cache between
# runs (core_validator.py; docs/cre_issues.md §1c), so sample 7 is
# order-independent and yields these 3 findings on a clean engine.
#
# If the set drifts:
#   * Zero findings → confirm `cdisc-rules-engine` is 0.16.0. A version
#     mismatch makes the wrapper's `validate_single_rule(rule)` call fail
#     and *every* rule crash, so CORE reports nothing.
#   * Set grows / changes → suspect cache-isolation regression first
#     (does the result depend on test order?), then investigate against
#     the assembler-to-core baseline and the divergence index.
_EXPECTED_FAILING_RULES = frozenset(
    {
        "CORE-000971",
        "CORE-001016",
        "CORE-001065",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cache_populated(usdm: USDM4) -> bool:
    """True if the CDISC CORE cache appears populated for v4-0."""
    try:
        status = usdm.core_cache_status(version="4-0")
    except Exception:
        return False
    return bool(getattr(status, "ready", status))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sample_7_path() -> pathlib.Path:
    if not SAMPLE_PATH.exists():
        pytest.skip(f"Sample file not found: {SAMPLE_PATH}")
    return SAMPLE_PATH


@pytest.fixture(scope="module")
def core_result(sample_7_path: pathlib.Path):
    """Run CORE once per module — the call is expensive."""
    if os.environ.get("USDM4_SKIP_CORE"):
        pytest.skip("USDM4_SKIP_CORE set in environment")
    usdm = USDM4()
    if not _cache_populated(usdm):
        pytest.skip(
            "CDISC CORE cache is not populated for version 4-0. "
            "Run USDM4().prepare_core(version='4-0') once to populate, "
            "or set USDM4_SKIP_CORE=1 to skip this test entirely."
        )
    return usdm.validate_core(str(sample_7_path))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_core_runs_without_engine_error(core_result) -> None:
    assert core_result is not None


def test_core_failing_rule_set_matches_baseline(core_result) -> None:
    """Failing CORE rule ids on sample 7 should exactly match the baseline.

    Set-match (not count-match) — small CRE-side count drift on a given
    rule shouldn't churn the test, but the *set* of firing rules is the
    real engine signal worth pinning.
    """
    if core_result.is_valid:
        # If CORE clears the file entirely, the baseline is over-broad.
        if _EXPECTED_FAILING_RULES:
            pytest.fail(
                "CORE reports no findings on sample 7, but "
                f"_EXPECTED_FAILING_RULES is non-empty ({sorted(_EXPECTED_FAILING_RULES)}). "
                "Clear the baseline."
            )
        return

    actual = frozenset(f.rule_id for f in core_result.findings)
    if actual == _EXPECTED_FAILING_RULES:
        return

    new_rules = sorted(actual - _EXPECTED_FAILING_RULES)
    cleared_rules = sorted(_EXPECTED_FAILING_RULES - actual)
    lines = ["CORE failing rule-id set differs from baseline on sample 7:"]
    if new_rules:
        lines.append(
            "  New rules (regression — fix or add to _EXPECTED_FAILING_RULES): "
            f"{new_rules}"
        )
    if cleared_rules:
        lines.append(
            "  Cleared rules (improvement — remove from _EXPECTED_FAILING_RULES): "
            f"{cleared_rules}"
        )
    lines.append(
        f"  Totals: {core_result.finding_count} error(s) across "
        f"{len(core_result.findings)} rule(s)"
    )
    if getattr(core_result, "execution_error_count", 0):
        lines.append(
            f"  ({core_result.execution_error_count} execution errors filtered)"
        )
    pytest.fail("\n".join(lines))
