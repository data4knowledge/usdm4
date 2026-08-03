"""Integration: validate sample_usdm_7.json with the d4k engine.

Sample 7 started life as a real protocol (NCT01750580, Berber et al.)
which carries codelist hygiene quirks that the synthetic samples
1–6 don't cover — chief among them, the use of CDISC `submissionValue`
labels rather than `preferredTerm` for many coded attributes.

The pytest fixture lives at
`tests/usdm4/test_files/integration/sample_usdm_7.json` so the test
suite is self-contained and doesn't depend on `validate/samples/`,
which is engine-comparison territory. A copy in `validate/samples/`
is maintained separately for the `validate/run.sh` sweep.

This test pins the *exact* set of rule ids d4k flags on that file so
the rule library doesn't silently drift. The pattern mirrors
`test_assembler_to_core.py`: the test passes when

  * the result is fully valid (desired end state), or
  * the failing rule-id set matches the captured baseline.

On any other outcome the test reports new vs cleared rules so the
maintainer knows which direction the drift went.

Why a rule-id set instead of just counts: a set-match test surfaces
*which* rule changed, not just that the totals moved. For sample 7
that's the load-bearing question — if DDF00155 stops firing, that's
an improvement worth recording; if DDF00101 stops firing, something
in the CT pipeline has regressed.

Note: this test does NOT execute in the Cowork sandbox. Run it
locally:

    pytest tests/usdm4/integration/test_sample_usdm_7_d4k.py
"""

from __future__ import annotations

import pathlib

import pytest

from usdm4 import USDM4
from usdm4.rules.results import RuleStatus


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


# Baseline captured against sample 7 with the rule library's `_ct_check`
# accepting both `preferredTerm` and `submissionValue` (the CDISC-wide
# policy fix) and HISTORICAL_VERSIONS including "2025-09-26". Three rules
# still legitimately fail on this file:
#
#   DDF00101   — Interventional design with no Procedure→Intervention link
#   DDF00153   — main ScheduleTimeline has no plannedDuration
#   DDFSDW001  — wrapper usdmVersion is '4.0', rule expects '4.0.0'
#
# Adjust this set if a rule is intentionally retired or the underlying
# protocol is regenerated. New rules failing here are a regression unless
# you can point at why.
_EXPECTED_FAILING_RULES = frozenset(
    {
        "DDF00101",
        "DDF00153",
        "DDFSDW001",
    }
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sample_7_path() -> pathlib.Path:
    """Skip the suite cleanly if the sample file isn't on disk."""
    if not SAMPLE_PATH.exists():
        pytest.skip(f"Sample file not found: {SAMPLE_PATH}")
    return SAMPLE_PATH


@pytest.fixture(scope="module")
def d4k_result(sample_7_path: pathlib.Path):
    """Run the d4k validator once per module — it's deterministic."""
    return USDM4().validate(str(sample_7_path))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_d4k_runs_without_engine_error(d4k_result) -> None:
    """The engine itself must run to completion and produce outcomes."""
    assert d4k_result is not None
    assert d4k_result.outcomes, "d4k returned no per-rule outcomes"


def test_d4k_no_rule_exceptions(d4k_result) -> None:
    """No rule may raise on this file. Exceptions almost always indicate a
    rule predicate hitting data it didn't expect — a real bug, not a
    conformance gap."""
    exceptions = [
        (rid, outcome.exception)
        for rid, outcome in d4k_result.outcomes.items()
        if outcome.status == RuleStatus.EXCEPTION
    ]
    assert not exceptions, "d4k raised on these rules:\n" + "\n".join(
        f"  {rid}: {exc}" for rid, exc in exceptions
    )


def test_d4k_failing_rule_set_matches_baseline(d4k_result) -> None:
    """Failing rule ids on sample 7 should exactly match the baseline.

    If the set differs in either direction the assertion message
    explains what to do — a *new* rule failing is a regression; a
    *cleared* rule is an improvement that should be removed from
    `_EXPECTED_FAILING_RULES`.
    """
    actual = frozenset(
        rid
        for rid, outcome in d4k_result.outcomes.items()
        if outcome.status == RuleStatus.FAILURE
    )
    if actual == _EXPECTED_FAILING_RULES:
        return

    new_rules = sorted(actual - _EXPECTED_FAILING_RULES)
    cleared_rules = sorted(_EXPECTED_FAILING_RULES - actual)
    lines = ["d4k failing rule-id set differs from baseline on sample 7:"]
    if new_rules:
        lines.append(
            "  New failures (regression — fix or add to _EXPECTED_FAILING_RULES): "
            f"{new_rules}"
        )
    if cleared_rules:
        lines.append(
            "  Cleared failures (improvement — remove from _EXPECTED_FAILING_RULES): "
            f"{cleared_rules}"
        )
    pytest.fail("\n".join(lines))


def test_d4k_ct_cluster_now_passes_on_sample_7(d4k_result) -> None:
    """Regression guard for the preferredTerm/submissionValue widening.

    Before that fix the file failed on ~10 `_ct_check` rules because it
    encodes decodes using each codelist's `submissionValue` (e.g.
    'Pharmaceutical Company' for C54149). After the widening, every
    one of these rules should pass on sample 7.
    """
    cluster = [
        "DDF00051",
        "DDF00110",
        "DDF00112",
        "DDF00128",
        "DDF00140",
        "DDF00147",
        "DDF00200",
        "DDF00216",
        "DDF00217",
        "DDF00259",
    ]
    still_failing = [
        rid
        for rid in cluster
        if rid in d4k_result.outcomes
        and d4k_result.outcomes[rid].status == RuleStatus.FAILURE
    ]
    assert not still_failing, (
        "These `_ct_check` rules should pass on sample 7 once both "
        "preferredTerm and submissionValue are accepted as valid decodes, "
        f"but are still failing: {still_failing}. "
        "Check src/usdm4/rules/rule_template.py::_codes_and_decodes."
    )
