"""Tests for RuleDDF00017 — SubjectEnrollment.quantity unit must be empty or the Percent AliasCode."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00017 import (
    CDISC_CODE_SYSTEM,
    PERCENT_CODE,
    PERCENT_DECODE,
    RuleDDF00017,
    _is_acceptable_unit,
)
from usdm4.rules.rule_template import RuleTemplate


def _percent_unit():
    return {
        "standardCode": {
            "codeSystem": CDISC_CODE_SYSTEM,
            "code": PERCENT_CODE,
            "decode": PERCENT_DECODE,
        }
    }


# ---------------------------------------------------------------------------
# _is_acceptable_unit helper
# ---------------------------------------------------------------------------


def test_unit_none_is_acceptable():
    assert _is_acceptable_unit(None) is True


def test_unit_false_is_acceptable():
    assert _is_acceptable_unit(False) is True


def test_unit_non_dict_rejected():
    assert _is_acceptable_unit("some-string") is False


def test_unit_empty_dict_acceptable():
    assert _is_acceptable_unit({}) is True


def test_unit_fully_specified_percent_acceptable():
    assert _is_acceptable_unit(_percent_unit()) is True


def test_unit_correct_code_but_wrong_decode_rejected():
    """Regression: decode must be '%' not 'Percentage'.

    CORE-000806 requires codeSystem, code AND decode to match. A unit that
    uses the preferred-term decode 'Percentage' alongside code C25613 does
    NOT satisfy the rule. The earlier d4k implementation checked only the
    code and let this through.
    """
    unit = _percent_unit()
    unit["standardCode"]["decode"] = "Percentage"
    assert _is_acceptable_unit(unit) is False


def test_unit_wrong_code_system_rejected():
    unit = _percent_unit()
    unit["standardCode"]["codeSystem"] = "http://other.example.com"
    assert _is_acceptable_unit(unit) is False


def test_unit_wrong_code_rejected():
    unit = _percent_unit()
    unit["standardCode"]["code"] = "OTHER"
    assert _is_acceptable_unit(unit) is False


def test_unit_non_dict_standard_code_rejected():
    assert _is_acceptable_unit({"standardCode": "bad"}) is False


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00017:
    def test_metadata(self):
        rule = RuleDDF00017()
        assert rule._rule == "DDF00017"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, enrollments):
        data = MagicMock()
        data.instances_by_klass.return_value = enrollments
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_dict_quantity_skipped(self):
        rule = RuleDDF00017()
        data = self._data([{"id": "E1", "quantity": None}])
        assert rule.validate({"data": data}) is True

    def test_fully_specified_percent_passes(self):
        rule = RuleDDF00017()
        data = self._data([{"id": "E1", "quantity": {"unit": _percent_unit()}}])
        assert rule.validate({"data": data}) is True

    def test_code_only_fails(self):
        """Sample-driven regression: code C25613 but decode 'Percentage'
        must be rejected (this is what the d4k<->CORE divergence exposed)."""
        rule = RuleDDF00017()
        unit = _percent_unit()
        unit["standardCode"]["decode"] = "Percentage"
        data = self._data([{"id": "E1", "quantity": {"unit": unit}}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_unacceptable_unit_fails(self):
        rule = RuleDDF00017()
        data = self._data(
            [{"id": "E1", "quantity": {"unit": {"standardCode": {"code": "X"}}}}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_empty_unit_passes(self):
        rule = RuleDDF00017()
        data = self._data([{"id": "E1", "quantity": {"unit": {}}}])
        assert rule.validate({"data": data}) is True
