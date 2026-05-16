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


# Baseline captured empirically against sample 7 with CRE 0.16.0. 24
# rules fire, producing ~73 findings (most rules report 1–3 errors each).
#
# This is a *drift-detector* set, not a conformance claim. Reading guide:
#
#  - 23 of the 24 are also in `test_assembler_to_core.py`'s
#    `_KNOWN_FAILING_RULES` — the CRE noise floor that surfaces on
#    essentially any non-trivial USDM input. Same population, same
#    underlying CRE behaviour. See `docs/cre_issues.md` and
#    `docs/d4k_cre_divergence_index.md` for what's behind each.
#  - The 1 unique-to-sample-7 fire is `CORE-000830`. Not yet catalogued
#    in the corpus engine_diff; if it persists, fold it into the
#    divergence index next refresh.
#  - The 2 *real* protocol-level findings (DDF rules d4k also flags)
#    are `CORE-001016` (DDF00153, main timeline plannedDuration) and
#    `CORE-001065` (DDF00101, no procedure→intervention link).
#
# Deliberately *omitted* from the baseline:
#
#  - `CORE-000971` (DDF00194, address-all-attributes-blank). CRE issue
#    9 phantom — null `legalAddress` on Organization is materialised as
#    a blank Address by CRE's traversal; d4k's `rule_ddf00194.py`
#    correctly iterates real Address instances and skips this. The
#    finding appears intermittently across CRE runs (it fired on the
#    first sample-7 run, did not fire on the run that produced this
#    baseline). Keeping it out so the test isn't flaky on a known false
#    positive; if it reappears we'll see it as "new" — fine, then drop
#    this comment and add the line.
#
# If the set drifts, investigate against the assembler-to-core baseline
# and the divergence index before adjusting.
_EXPECTED_FAILING_RULES = frozenset(
    {
        "CORE-000815",
        "CORE-000830",
        "CORE-000854",
        "CORE-000856",
        "CORE-000857",
        "CORE-000858",
        "CORE-000879",
        "CORE-000904",
        "CORE-000905",
        "CORE-000925",
        "CORE-000931",
        "CORE-000933",
        "CORE-000942",
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
