"""Tests for RuleDDF00238 — Strength.numerator quantity must have a unit."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00238 import RuleDDF00238
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00238:
    def test_metadata(self):
        rule = RuleDDF00238()
        assert rule._rule == "DDF00238"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "If a strength numerator quantity is specified, it must have a unit."
        )

    def _data(self, strengths):
        data = MagicMock()
        data.instances_by_klass.return_value = strengths
        data.path_by_id.return_value = "$.path"
        return data

    def test_numerator_missing_is_skipped(self):
        rule = RuleDDF00238()
        assert rule.validate({"data": self._data([{"id": "s1"}])}) is True
        assert rule.errors().count() == 0

    def test_numerator_not_a_dict_is_skipped(self):
        rule = RuleDDF00238()
        data = self._data([{"id": "s2", "numerator": 42}])
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_numerator_without_value_is_skipped(self):
        """Range-case numerator (no `value`) → out of scope for this rule."""
        rule = RuleDDF00238()
        data = self._data(
            [
                {
                    "id": "s3",
                    "numerator": {
                        "minValue": {"value": 1, "unit": {"id": "U1"}},
                        "maxValue": {"value": 2, "unit": {"id": "U1"}},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_value_without_unit_fails(self):
        rule = RuleDDF00238()
        data = self._data([{"id": "s4", "numerator": {"value": 10}}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_value_with_none_unit_fails(self):
        """None unit counts as "no unit" via falsy check."""
        rule = RuleDDF00238()
        data = self._data([{"id": "s5", "numerator": {"value": 10, "unit": None}}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_value_with_unit_passes(self):
        rule = RuleDDF00238()
        data = self._data(
            [{"id": "s6", "numerator": {"value": 10, "unit": {"id": "U1"}}}]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0
