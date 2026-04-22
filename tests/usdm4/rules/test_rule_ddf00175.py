"""Tests for RuleDDF00175 — Administration.frequency against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00175 import RuleDDF00175
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00175:
    def test_metadata(self):
        rule = RuleDDF00175()
        assert rule._rule == "DDF00175"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00175()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "frequency": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
