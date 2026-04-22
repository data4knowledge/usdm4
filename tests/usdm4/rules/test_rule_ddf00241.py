"""Tests for RuleDDF00241 — Range min < max when units match."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00241 import RuleDDF00241, _unit_code
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _unit_code helper
# ---------------------------------------------------------------------------


def test_unit_code_non_dict_endpoint_returns_none():
    assert _unit_code(None) is None
    assert _unit_code("scalar") is None


def test_unit_code_missing_unit_returns_none():
    assert _unit_code({"value": 1}) is None


def test_unit_code_non_dict_unit_returns_none():
    assert _unit_code({"unit": "kg"}) is None


def test_unit_code_prefers_standard_code():
    ep = {"unit": {"standardCode": {"code": "STD"}, "code": "FALLBACK"}}
    assert _unit_code(ep) == "STD"


def test_unit_code_falls_back_to_unit_code():
    """standardCode missing but unit.code present → use unit.code."""
    ep = {"unit": {"code": "FALLBACK"}}
    assert _unit_code(ep) == "FALLBACK"


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00241:
    def test_metadata(self):
        rule = RuleDDF00241()
        assert rule._rule == "DDF00241"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, ranges):
        data = MagicMock()
        data.instances_by_klass.return_value = ranges
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_dict_endpoints_skipped(self):
        rule = RuleDDF00241()
        data = self._data([{"id": "R1", "minValue": None, "maxValue": None}])
        assert rule.validate({"data": data}) is True

    def test_non_numeric_values_skipped(self):
        rule = RuleDDF00241()
        data = self._data(
            [
                {
                    "id": "R1",
                    "minValue": {"value": "a"},
                    "maxValue": {"value": 10},
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_different_units_skip_comparison(self):
        rule = RuleDDF00241()
        data = self._data(
            [
                {
                    "id": "R1",
                    "minValue": {
                        "value": 10,
                        "unit": {"standardCode": {"code": "A"}},
                    },
                    "maxValue": {
                        "value": 5,
                        "unit": {"standardCode": {"code": "B"}},
                    },
                }
            ]
        )
        # Units differ → no failure even though max <= min.
        assert rule.validate({"data": data}) is True

    def test_same_unit_max_less_or_equal_min_fails(self):
        rule = RuleDDF00241()
        data = self._data(
            [
                {
                    "id": "R1",
                    "minValue": {
                        "value": 10,
                        "unit": {"standardCode": {"code": "A"}},
                    },
                    "maxValue": {
                        "value": 5,
                        "unit": {"standardCode": {"code": "A"}},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_both_units_missing_compares_values(self):
        """Both units None → same_unit=True, still compares."""
        rule = RuleDDF00241()
        data = self._data(
            [
                {
                    "id": "R1",
                    "minValue": {"value": 10},
                    "maxValue": {"value": 10},  # equal → fails (<= check)
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_happy_path_passes(self):
        rule = RuleDDF00241()
        data = self._data(
            [
                {
                    "id": "R1",
                    "minValue": {
                        "value": 1,
                        "unit": {"standardCode": {"code": "A"}},
                    },
                    "maxValue": {
                        "value": 10,
                        "unit": {"standardCode": {"code": "A"}},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is True
