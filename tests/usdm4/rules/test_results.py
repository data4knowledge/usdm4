"""Tests for RulesValidationResults, RuleOutcome, and RuleStatus.

Uses only stdlib + simple_error_log Errors — no real rules loaded, no
CT library touched. Every branch of to_dict, to_errors, format_text,
_items, and _row is exercised directly.
"""

import pytest

from simple_error_log.errors import Errors

from src.usdm4.rules.results import (
    RuleOutcome,
    RuleStatus,
    RulesValidationResults,
)
from src.usdm4.rules.rule_template import ValidationLocation


# ---------------------------------------------------------------------------
# RuleStatus / RuleOutcome
# ---------------------------------------------------------------------------


def test_rule_status_values():
    assert RuleStatus.SUCCESS.value == "Success"
    assert RuleStatus.FAILURE.value == "Failure"
    assert RuleStatus.EXCEPTION.value == "Exception"
    assert RuleStatus.NOT_IMPLEMENTED.value == "Not Implemented"


def test_rule_outcome_defaults():
    o = RuleOutcome("R1", RuleStatus.SUCCESS)
    assert o.rule_id == "R1"
    assert o.status == RuleStatus.SUCCESS
    assert o.error_count == 0
    assert o.exception is None


def test_rule_outcome_error_count_reflects_errors():
    errs = Errors()
    errs.error("boom")
    errs.error("bang")
    o = RuleOutcome("R2", RuleStatus.FAILURE, errors=errs)
    assert o.error_count == 2


# ---------------------------------------------------------------------------
# Writer API
# ---------------------------------------------------------------------------


@pytest.fixture
def results():
    return RulesValidationResults()


def test_add_success(results):
    results.add_success("R1")
    assert results.outcomes["R1"].status == RuleStatus.SUCCESS


def test_add_failure_records_errors(results):
    errs = Errors()
    errs.error("bad")
    results.add_failure("R2", errs)
    outcome = results.outcomes["R2"]
    assert outcome.status == RuleStatus.FAILURE
    assert outcome.error_count == 1


def test_add_exception_with_traceback(results):
    results.add_exception("R3", RuntimeError("boom"), traceback="tb-text")
    outcome = results.outcomes["R3"]
    assert outcome.status == RuleStatus.EXCEPTION
    assert "boom" in outcome.exception
    assert "tb-text" in outcome.exception


def test_add_exception_without_traceback(results):
    results.add_exception("R4", RuntimeError("boom"))
    outcome = results.outcomes["R4"]
    assert outcome.status == RuleStatus.EXCEPTION
    assert outcome.exception == "boom"


def test_add_not_implemented(results):
    results.add_not_implemented("R5")
    assert results.outcomes["R5"].status == RuleStatus.NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# Query API
# ---------------------------------------------------------------------------


def test_count_and_finding_count(results):
    errs = Errors()
    errs.error("x")
    errs.error("y")
    results.add_success("R1")
    results.add_failure("R2", errs)
    results.add_not_implemented("R3")

    assert results.count() == 3
    assert results.finding_count == 2


def test_is_valid_and_passed_all_success(results):
    results.add_success("R1")
    results.add_success("R2")
    assert results.passed() is True
    assert results.is_valid is True


def test_passed_false_when_any_failure(results):
    errs = Errors()
    errs.error("x")
    results.add_success("R1")
    results.add_failure("R2", errs)
    assert results.passed() is False
    assert results.is_valid is False


def test_passed_or_not_implemented_allows_ni(results):
    results.add_success("R1")
    results.add_not_implemented("R2")
    assert results.passed() is False  # NI still not "passed"
    assert results.passed_or_not_implemented() is True


def test_passed_or_not_implemented_false_on_failure(results):
    errs = Errors()
    errs.error("x")
    results.add_failure("R1", errs)
    assert results.passed_or_not_implemented() is False


def test_by_status_groups_outcomes(results):
    errs = Errors()
    errs.error("x")
    results.add_success("R1")
    results.add_failure("R2", errs)
    results.add_not_implemented("R3")

    assert [o.rule_id for o in results.by_status(RuleStatus.SUCCESS)] == ["R1"]
    assert [o.rule_id for o in results.by_status(RuleStatus.FAILURE)] == ["R2"]
    assert [o.rule_id for o in results.by_status(RuleStatus.NOT_IMPLEMENTED)] == ["R3"]
    assert results.by_status(RuleStatus.EXCEPTION) == []


# ---------------------------------------------------------------------------
# to_dict — default filtering and include_* toggles
# ---------------------------------------------------------------------------


def _failure_errors_with_location():
    """An Errors instance with one ValidationLocation-tagged error."""
    errs = Errors()
    loc = ValidationLocation("R1", "rule text", "Study", "name", "$.study.name")
    errs.error("oops", loc)
    return errs


def test_to_dict_defaults_drop_success_and_not_implemented(results):
    results.add_success("R1")
    results.add_not_implemented("R2")
    results.add_failure("R3", _failure_errors_with_location())

    rows = results.to_dict()
    rule_ids = [r["rule_id"] for r in rows]
    assert rule_ids == ["R3"]


def test_to_dict_row_populates_location_and_message(results):
    results.add_failure("R3", _failure_errors_with_location())
    rows = results.to_dict()
    assert len(rows) == 1
    row = rows[0]
    assert row["rule_id"] == "R3"
    assert row["status"] == "Failure"
    assert row["message"] == "oops"
    assert row["klass"] == "Study"
    assert row["attribute"] == "name"
    assert row["path"] == "$.study.name"


def test_to_dict_include_success_produces_row(results):
    results.add_success("R1")
    rows = results.to_dict(include_success=True)
    assert len(rows) == 1
    assert rows[0]["status"] == "Success"
    assert rows[0]["message"] == ""
    assert rows[0]["klass"] == ""


def test_to_dict_include_not_implemented_produces_row(results):
    results.add_not_implemented("R1")
    rows = results.to_dict(include_not_implemented=True)
    assert len(rows) == 1
    assert rows[0]["status"] == "Not Implemented"


def test_to_dict_exception_row_uses_exception_text(results):
    results.add_exception("R5", RuntimeError("boom"))
    rows = results.to_dict()
    assert len(rows) == 1
    assert rows[0]["status"] == "Exception"
    assert rows[0]["exception"] == "boom"


def test_to_dict_sorts_by_rule_id(results):
    results.add_failure("R_B", _failure_errors_with_location())
    results.add_failure("R_A", _failure_errors_with_location())
    rows = results.to_dict()
    assert [r["rule_id"] for r in rows] == ["R_A", "R_B"]


# ---------------------------------------------------------------------------
# to_errors bridge
# ---------------------------------------------------------------------------


def test_to_errors_merges_only_failure_errors(results):
    errs = _failure_errors_with_location()
    results.add_success("RS")
    results.add_not_implemented("RN")
    results.add_exception("RE", RuntimeError("x"))
    results.add_failure("RF", errs)

    merged = results.to_errors()
    assert merged.count() >= 1
    dumped = merged.to_dict(level=Errors.DEBUG)
    messages = [e.get("message") for e in dumped]
    assert "oops" in messages


# ---------------------------------------------------------------------------
# format_text
# ---------------------------------------------------------------------------


def test_format_text_passed_branch(results):
    results.add_success("R1")
    text = results.format_text()
    assert "USDM4 Rule Library Validation Report" in text
    assert "Validation PASSED" in text


def test_format_text_failure_branch_with_location(results):
    results.add_failure("RF", _failure_errors_with_location())
    text = results.format_text()
    assert "Validation FAILED" in text
    assert "RF" in text
    assert "Study.name" in text
    assert "oops" in text


def test_format_text_exception_branch(results):
    results.add_exception("RE", RuntimeError("boom"))
    text = results.format_text()
    assert "Validation FAILED" in text
    assert "RE: EXCEPTION" in text
    assert "boom" in text


def test_format_text_failure_without_location(results):
    errs = Errors()
    errs.error("no-loc")  # no ValidationLocation attached
    results.add_failure("RN", errs)
    text = results.format_text()
    # Row still prints, just with empty head and no tail
    assert "no-loc" in text


# ---------------------------------------------------------------------------
# _items back-compat
# ---------------------------------------------------------------------------


def test_items_back_compat_shape(results):
    results.add_success("RS")
    results.add_failure("RF", _failure_errors_with_location())
    results.add_exception("RE", RuntimeError("x"))
    results.add_not_implemented("RN")

    items = results._items

    assert items["RS"]["status"] == "Success"
    assert items["RS"]["errors"] is None

    assert items["RF"]["status"] == "Failure"
    assert isinstance(items["RF"]["errors"], list)
    assert items["RF"]["errors"][0]["message"] == "oops"

    assert items["RE"]["status"] == "Exception"
    assert items["RE"]["errors"] is None
    assert items["RE"]["exception"] == "x"

    assert items["RN"]["status"] == "Not Implemented"
    assert items["RN"]["errors"] is None


# ---------------------------------------------------------------------------
# _row edge cases — hit the "error has no location / unknown location keys"
# branch.
# ---------------------------------------------------------------------------


def test_row_with_no_error():
    outcome = RuleOutcome("R1", RuleStatus.SUCCESS)
    row = RulesValidationResults._row(outcome, error=None)
    assert row["rule_id"] == "R1"
    assert row["status"] == "Success"
    assert row["message"] == ""
    # All validation location keys initialised to empty string
    for key in ValidationLocation.headers():
        assert row[key] == ""


def test_row_drops_unknown_location_keys():
    outcome = RuleOutcome("R1", RuleStatus.FAILURE)
    error = {
        "level": "Error",
        "message": "m",
        "type": "t",
        "timestamp": "ts",
        "location": {"klass": "Study", "surprise": "ignored"},
    }
    row = RulesValidationResults._row(outcome, error=error)
    assert row["klass"] == "Study"
    assert "surprise" not in row


def test_row_without_location_key_in_error():
    outcome = RuleOutcome("R1", RuleStatus.FAILURE)
    error = {"message": "m"}  # no "location" at all
    row = RulesValidationResults._row(outcome, error=error)
    assert row["message"] == "m"
    for key in ValidationLocation.headers():
        assert row[key] == ""
