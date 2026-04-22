"""Tests for RuleDDF00234 — no unit on plannedEnrollmentNumber."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00234 import RuleDDF00234
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00234:
    def test_metadata(self):
        rule = RuleDDF00234()
        assert rule._rule == "DDF00234"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, populations=None, cohorts=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "StudyDesignPopulation": populations or [],
            "StudyCohort": cohorts or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_number_skipped(self):
        rule = RuleDDF00234()
        data = self._data(populations=[{"id": "P1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_number_skipped(self):
        rule = RuleDDF00234()
        data = self._data(populations=[{"id": "P1", "plannedEnrollmentNumber": 42}])
        assert rule.validate({"data": data}) is True

    def test_quantity_with_unit_fails(self):
        rule = RuleDDF00234()
        data = self._data(
            populations=[
                {
                    "id": "P1",
                    "plannedEnrollmentNumber": {"unit": {"code": "subj"}},
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_range_endpoint_with_unit_fails(self):
        rule = RuleDDF00234()
        data = self._data(
            cohorts=[
                {
                    "id": "C1",
                    "plannedEnrollmentNumber": {
                        "minValue": {"value": 1, "unit": {"code": "subj"}},
                        "maxValue": {"value": 10},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_no_unit_passes(self):
        rule = RuleDDF00234()
        data = self._data(
            populations=[
                {
                    "id": "P1",
                    "plannedEnrollmentNumber": {
                        "minValue": {"value": 1},
                        "maxValue": {"value": 10},
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is True
