"""Tests for RuleDDF00258 — at most one randomisation-set characteristic."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00258 import RuleDDF00258
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00258:
    def test_metadata(self):
        rule = RuleDDF00258()
        assert rule._rule == "DDF00258"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_zero_passes(self):
        rule = RuleDDF00258()
        data = self._data(
            interventional=[{"id": "SD1", "characteristics": [{"code": "OTHER"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_one_passes(self):
        rule = RuleDDF00258()
        data = self._data(
            interventional=[{"id": "SD1", "characteristics": [{"code": "C46079"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_two_fails(self):
        rule = RuleDDF00258()
        data = self._data(
            observational=[
                {
                    "id": "SD1",
                    "characteristics": [{"code": "C46079"}, {"code": "C25689"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
