"""Tests for RuleDDF00017 — SubjectEnrollment.quantity unit must be empty or Percent."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00017 import (
    PERCENT_CODE,
    RuleDDF00017,
    _is_acceptable_unit,
)
from usdm4.rules.rule_template import RuleTemplate


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


def test_unit_percent_acceptable():
    assert _is_acceptable_unit({"standardCode": {"code": PERCENT_CODE}}) is True


def test_unit_other_code_rejected():
    assert _is_acceptable_unit({"standardCode": {"code": "OTHER"}}) is False


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
