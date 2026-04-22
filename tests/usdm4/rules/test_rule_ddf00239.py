"""Tests for RuleDDF00239 — Strength.numerator range endpoints must have units."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00239 import RuleDDF00239
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00239:
    def test_metadata(self):
        rule = RuleDDF00239()
        assert rule._rule == "DDF00239"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "If a strength numerator range is specified, both the minValue and maxValue must have a unit."
        )

    def _data(self, strengths):
        data = MagicMock()
        data.instances_by_klass.return_value = strengths
        data.path_by_id.return_value = "$.path"
        return data

    def test_numerator_missing_is_skipped(self):
        """No numerator → loop continues without touching _add_failure."""
        rule = RuleDDF00239()
        data = self._data([{"id": "s1"}])  # no numerator key
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_numerator_not_a_dict_is_skipped(self):
        """Scalar numerator (not a dict) → skipped."""
        rule = RuleDDF00239()
        data = self._data([{"id": "s2", "numerator": "not-a-dict"}])
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_numerator_single_value_is_not_a_range(self):
        """Both minValue and maxValue absent → treated as scalar, no check."""
        rule = RuleDDF00239()
        data = self._data(
            [{"id": "s3", "numerator": {"value": 10, "unit": {"id": "U1"}}}]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_range_with_min_missing_unit_fails(self):
        """minValue has value but no unit → failure logged."""
        rule = RuleDDF00239()
        data = self._data(
            [
                {
                    "id": "s4",
                    "numerator": {
                        "minValue": {"value": 10},  # no unit
                        "maxValue": {"value": 20, "unit": {"id": "U1"}},
                    },
                }
            ]
        )
        result = rule.validate({"data": data})
        assert result is False
        assert rule.errors().count() == 1

    def test_range_with_max_missing_unit_fails(self):
        """maxValue has value but no unit → failure logged."""
        rule = RuleDDF00239()
        data = self._data(
            [
                {
                    "id": "s5",
                    "numerator": {
                        "minValue": {"value": 10, "unit": {"id": "U1"}},
                        "maxValue": {"value": 20},  # no unit
                    },
                }
            ]
        )
        result = rule.validate({"data": data})
        assert result is False
        assert rule.errors().count() == 1

    def test_range_with_both_units_passes(self):
        rule = RuleDDF00239()
        data = self._data(
            [
                {
                    "id": "s6",
                    "numerator": {
                        "minValue": {"value": 10, "unit": {"id": "U1"}},
                        "maxValue": {"value": 20, "unit": {"id": "U1"}},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_endpoint_without_value_is_not_flagged(self):
        """Endpoint dict present but value is None → no failure (guard on the
        `value is not None` check)."""
        rule = RuleDDF00239()
        data = self._data(
            [
                {
                    "id": "s7",
                    "numerator": {
                        "minValue": {"value": None},  # no value, no unit
                        "maxValue": {"value": 20, "unit": {"id": "U1"}},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_non_dict_endpoint_is_skipped(self):
        """If one endpoint is a dict and the other is a non-dict, the
        loop still runs on the non-dict branch and skips it."""
        rule = RuleDDF00239()
        data = self._data(
            [
                {
                    "id": "s8",
                    "numerator": {
                        "minValue": {"value": 10, "unit": {"id": "U1"}},
                        "maxValue": "oops",  # non-dict endpoint
                    },
                }
            ]
        )
        # minValue has a unit, maxValue isn't a dict → no failure.
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0
