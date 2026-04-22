"""Tests for RuleDDF00199 — StudyAmendmentImpact.type against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00199 import RuleDDF00199
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00199:
    def test_metadata(self):
        rule = RuleDDF00199()
        assert rule._rule == "DDF00199"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00199()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "type": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
