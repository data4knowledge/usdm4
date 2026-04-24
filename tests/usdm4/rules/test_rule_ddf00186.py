"""Tests for RuleDDF00186 — Strength.denominator must have a unit once specified."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00186 import RuleDDF00186
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00186:
    def test_metadata(self):
        rule = RuleDDF00186()
        assert rule._rule == "DDF00186"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "If a strength denominator is specified, it must have a unit."
        )

    def _data(self, strengths):
        data = MagicMock()
        data.instances_by_klass.return_value = strengths
        data.path_by_id.return_value = "$.path"
        return data

    def test_denominator_missing_is_skipped(self):
        rule = RuleDDF00186()
        assert rule.validate({"data": self._data([{"id": "s1"}])}) is True
        assert rule.errors().count() == 0

    def test_denominator_not_a_dict_is_skipped(self):
        rule = RuleDDF00186()
        data = self._data([{"id": "s2", "denominator": "scalar"}])
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_denominator_without_id_is_skipped(self):
        """Per CORE, "specified" means the denominator has an id."""
        rule = RuleDDF00186()
        data = self._data([{"id": "s3", "denominator": {"value": 10}}])
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_specified_but_missing_unit_fails(self):
        rule = RuleDDF00186()
        data = self._data([{"id": "s4", "denominator": {"id": "D1", "value": 10}}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_specified_with_unit_passes(self):
        rule = RuleDDF00186()
        data = self._data(
            [
                {
                    "id": "s5",
                    "denominator": {
                        "id": "D1",
                        "value": 10,
                        "unit": {"id": "U1"},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0
