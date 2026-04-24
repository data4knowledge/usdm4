"""Tests for RuleDDF00141 — plannedSex against codelist, OR across SDP/SC."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00141 import RuleDDF00141
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00141:
    def test_metadata(self):
        rule = RuleDDF00141()
        assert rule._rule == "DDF00141"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00141()
        ct = MagicMock()
        ct.klass_and_attribute.return_value = {
            "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
        }
        data = MagicMock()
        data.instances_by_klass.return_value = [
            {"id": "X1", "plannedSex": [{"code": "A", "decode": "DA"}]}
        ]
        data.path_by_id.return_value = "$.path"
        assert rule.validate({"data": data, "ct": ct}) is True
