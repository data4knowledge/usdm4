"""Tests for RuleDDF00157 — Encounter.environmentalSettings against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00157 import RuleDDF00157
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00157:
    def test_metadata(self):
        rule = RuleDDF00157()
        assert rule._rule == "DDF00157"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00157()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "environmentalSettings": [{"code": "A", "decode": "DA"}]}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
