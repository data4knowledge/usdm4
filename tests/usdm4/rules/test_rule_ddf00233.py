"""Tests for RuleDDF00233 — Quantity.unit against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00233 import RuleDDF00233
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00233:
    def test_metadata(self):
        rule = RuleDDF00233()
        assert rule._rule == "DDF00233"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00233()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "unit": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
