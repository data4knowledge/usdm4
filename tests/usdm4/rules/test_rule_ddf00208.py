"""Tests for RuleDDF00208 — AdministrableProduct.sourcing against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00208 import RuleDDF00208
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00208:
    def test_metadata(self):
        rule = RuleDDF00208()
        assert rule._rule == "DDF00208"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00208()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "sourcing": {"code": "A", "decode": "DA"}}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
