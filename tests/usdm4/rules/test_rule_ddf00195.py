"""Tests for RuleDDF00195 — SubjectEnrollment exactly-one-of geo/site/cohort."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00195 import RuleDDF00195
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00195:
    def test_metadata(self):
        rule = RuleDDF00195()
        assert rule._rule == "DDF00195"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, enrollments=None, sites=None, cohorts=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "SubjectEnrollment": enrollments or [],
            "ManagedSite": sites or [],
            "StudyCohort": cohorts or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_zero_slots_fails(self):
        rule = RuleDDF00195()
        data = self._data(enrollments=[{"id": "E1"}])
        assert rule.validate({"data": data}) is False
        assert "found 0" in rule.errors().dump()

    def test_two_slots_fails(self):
        rule = RuleDDF00195()
        data = self._data(
            enrollments=[
                {"id": "E1", "forGeographicScope": {"x": 1}, "forStudySiteId": "S1"}
            ],
            sites=[{"id": "S1"}],
        )
        assert rule.validate({"data": data}) is False
        assert "found 2" in rule.errors().dump()

    def test_one_geo_passes(self):
        rule = RuleDDF00195()
        data = self._data(enrollments=[{"id": "E1", "forGeographicScope": {"x": 1}}])
        assert rule.validate({"data": data}) is True

    def test_valid_site_passes(self):
        rule = RuleDDF00195()
        data = self._data(
            enrollments=[{"id": "E1", "forStudySiteId": "S1"}],
            sites=[{"id": "S1"}],
        )
        assert rule.validate({"data": data}) is True

    def test_invalid_site_fails(self):
        rule = RuleDDF00195()
        data = self._data(
            enrollments=[{"id": "E1", "forStudySiteId": "S_UNKNOWN"}],
        )
        assert rule.validate({"data": data}) is False
        assert "does not resolve to an existing ManagedSite" in rule.errors().dump()

    def test_invalid_cohort_fails(self):
        rule = RuleDDF00195()
        data = self._data(
            enrollments=[{"id": "E1", "forStudyCohortId": "C_UNKNOWN"}],
        )
        assert rule.validate({"data": data}) is False
        assert "does not resolve to an existing StudyCohort" in rule.errors().dump()
