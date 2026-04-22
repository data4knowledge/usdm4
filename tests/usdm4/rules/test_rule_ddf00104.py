"""Tests for RuleDDF00104 — Timing.relativeToFrom against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00104 import RuleDDF00104
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00104:
    def test_metadata(self):
        rule = RuleDDF00104()
        assert rule._rule == "DDF00104"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00104()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "T1", "relativeToFrom": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
