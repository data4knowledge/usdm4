"""Tests for RuleDDF00112 — StudyIntervention.role against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00112 import RuleDDF00112
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00112:
    def test_metadata(self):
        rule = RuleDDF00112()
        assert rule._rule == "DDF00112"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00112()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "role": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
