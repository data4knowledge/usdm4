"""Tests for RuleDDF00006 — Timing window attrs all-or-nothing."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00006 import RuleDDF00006, _is_specified
from usdm4.rules.rule_template import RuleTemplate


def test_is_specified_variants():
    assert _is_specified(None) is False
    assert _is_specified("  ") is False
    assert _is_specified("x") is True
    assert _is_specified([]) is False
    assert _is_specified({}) is False
    assert _is_specified([1]) is True
    assert _is_specified({"a": 1}) is True
    assert _is_specified(42) is True


class TestRuleDDF00006:
    def test_metadata(self):
        rule = RuleDDF00006()
        assert rule._rule == "DDF00006"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_none_set_passes(self):
        rule = RuleDDF00006()
        data = self._data([{"id": "T1"}])
        assert rule.validate({"data": data}) is True

    def test_all_set_passes(self):
        rule = RuleDDF00006()
        data = self._data(
            [
                {
                    "id": "T1",
                    "windowLabel": "w",
                    "windowLower": {"value": 1},
                    "windowUpper": {"value": 2},
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_partial_fails(self):
        rule = RuleDDF00006()
        data = self._data(
            [{"id": "T1", "windowLabel": "w", "windowLower": {"value": 1}}]
        )
        assert rule.validate({"data": data}) is False
        assert "windowUpper" in rule.errors().dump()
