"""Tests for RuleDDF00136 — Encounter.contactModes against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00136 import RuleDDF00136
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00136:
    def test_metadata(self):
        rule = RuleDDF00136()
        assert rule._rule == "DDF00136"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00136()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "contactModes": [{"code": "A", "decode": "DA"}]}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
