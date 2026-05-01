"""Integration: minimum AssemblerInput -> assemble -> validate (d4k).

These tests guard against regressions in the assembler-output-to-d4k pipeline.
A break here means either:

  * the assembler stopped producing a valid USDM JSON shape from a
    previously-valid input (e.g. a refactor changed required fields), or
  * d4k started rejecting output the assembler still emits (e.g. a new
    or stricter rule), or
  * the AssemblerInput schema tightened in a way that broke the fixture.

Current status (2026-05-01)
---------------------------

Per ``docs/assembler_validation_findings.md``, even the minimum fixture
produces output that d4k flags. Until those findings are fixed, the strict
"all implemented rules pass" test is ``xfail``-ed and we instead enforce
two regression guards:

  * No d4k rule may *raise* on the assembled study (Exception status). New
    exceptions almost always mean a real bug — either in d4k or in the
    assembler output it's looking at.
  * The total finding count must not increase beyond a known baseline.
    Lower it (or remove the baseline assertion entirely) once the
    findings are addressed.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from usdm4 import USDM4
from usdm4.rules.results import RuleStatus


# Baselines captured 2026-05-01 against the minimum fixture in conftest.py.
# These numbers reflect *current* assembler output, not desired conformance.
# When the assembler is fixed to satisfy more rules, lower these.
BASELINE_D4K_FAILING_RULE_COUNT = 14
BASELINE_D4K_FINDING_COUNT = 25
BASELINE_D4K_EXCEPTION_RULE_COUNT = 1


def test_assembled_json_is_well_formed(
    assembled_study_json_path: pathlib.Path,
) -> None:
    """The Wrapper JSON has the expected top-level shape.

    Cheap structural check that catches accidental shape changes (e.g. a
    refactor that drops the ``study`` envelope or reorders required keys).
    """
    with assembled_study_json_path.open() as fh:
        wrapper = json.load(fh)

    assert set(wrapper.keys()) >= {
        "study",
        "usdmVersion",
        "systemName",
        "systemVersion",
    }, f"Unexpected top-level keys: {sorted(wrapper.keys())}"

    study = wrapper["study"]
    assert isinstance(study, dict)
    assert study.get("instanceType") == "Study"
    assert study.get("versions"), "Study must have at least one version"


def test_d4k_runs_without_engine_error(
    assembled_study_json_path: pathlib.Path, usdm4_facade: USDM4
) -> None:
    """The d4k engine itself must run to completion and return outcomes."""
    result = usdm4_facade.validate(str(assembled_study_json_path))
    assert result is not None
    assert result.outcomes, "d4k returned no per-rule outcomes"


def test_d4k_exception_rule_count_at_or_below_baseline(
    assembled_study_json_path: pathlib.Path, usdm4_facade: USDM4
) -> None:
    """Number of rules that *raise* must not grow beyond the baseline.

    Exception status means a rule predicate hit data it didn't expect — a
    real bug, not a conformance gap. The baseline is intentionally tight
    so this test is sensitive to new exception sources.
    """
    result = usdm4_facade.validate(str(assembled_study_json_path))
    exceptions = [
        (rid, outcome.exception)
        for rid, outcome in result.outcomes.items()
        if outcome.status == RuleStatus.EXCEPTION
    ]
    assert len(exceptions) <= BASELINE_D4K_EXCEPTION_RULE_COUNT, (
        f"d4k exception count {len(exceptions)} exceeds baseline "
        f"{BASELINE_D4K_EXCEPTION_RULE_COUNT}:\n"
        + "\n".join(f"  {rid}: {exc}" for rid, exc in exceptions)
    )


def test_d4k_finding_count_at_or_below_baseline(
    assembled_study_json_path: pathlib.Path, usdm4_facade: USDM4
) -> None:
    """Total finding count must not grow beyond the baseline.

    A growing finding count means either the assembler started emitting
    less-conformant output, or d4k tightened a rule. Either way we want
    to be told.
    """
    result = usdm4_facade.validate(str(assembled_study_json_path))
    failing_rules = [
        rid
        for rid, outcome in result.outcomes.items()
        if outcome.status == RuleStatus.FAILURE
    ]
    assert (
        result.finding_count <= BASELINE_D4K_FINDING_COUNT
    ), (
        f"d4k finding count {result.finding_count} exceeds baseline "
        f"{BASELINE_D4K_FINDING_COUNT} ({len(failing_rules)} failing rule(s))"
    )
    assert (
        len(failing_rules) <= BASELINE_D4K_FAILING_RULE_COUNT
    ), (
        f"d4k failing-rule count {len(failing_rules)} exceeds baseline "
        f"{BASELINE_D4K_FAILING_RULE_COUNT}"
    )


@pytest.mark.xfail(
    reason=(
        "Minimum fixture fails 14 d4k rules with 25 findings as of 2026-05-01 "
        "(post sponsor / org-wiring fixes: Bug 1 sponsor.appliesToIds wiring, "
        "Bug 2 canonical CT decodes, Bug 3 dynamic version list); "
        "see docs/assembler_validation_findings.md. Flip this to a regular "
        "test (drop xfail) once the assembler is fixed and the baseline test "
        "is no longer needed."
    ),
    strict=False,
)
def test_d4k_passes_or_not_implemented(
    assembled_study_json_path: pathlib.Path, usdm4_facade: USDM4
) -> None:
    """Goal state: every implemented d4k rule passes on the minimum fixture."""
    result = usdm4_facade.validate(str(assembled_study_json_path))
    failures = [
        {"rule_id": rid, "errors": outcome.error_count}
        for rid, outcome in result.outcomes.items()
        if outcome.status == RuleStatus.FAILURE
    ]
    assert result.passed_or_not_implemented(), (
        f"d4k rule failures on minimum assembled study "
        f"({result.finding_count} findings across {len(failures)} rule(s)):\n"
        + "\n".join(f"  {f['rule_id']}: {f['errors']} error(s)" for f in failures)
    )
