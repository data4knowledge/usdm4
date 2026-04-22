"""Tests for RuleDDF00210 — AdministrableProduct.productDesignation against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00210 import RuleDDF00210
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00210:
    def test_metadata(self):
        rule = RuleDDF00210()
        assert rule._rule == "DDF00210"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00210()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "productDesignation": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
