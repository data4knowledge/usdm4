"""Tests for RuleDDF00051 — Timing.type against codelist."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00051 import RuleDDF00051
from usdm4.rules.rule_template import RuleTemplate


def _ct_config(klass_instances):
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {
        "terms": [{"conceptId": "A", "preferredTerm": "DA"}]
    }
    data = MagicMock()
    data.instances_by_klass.return_value = klass_instances
    data.path_by_id.return_value = "$.path"
    return {"data": data, "ct": ct}


class TestRuleDDF00051:
    def test_metadata(self):
        rule = RuleDDF00051()
        assert rule._rule == "DDF00051"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_ct_pass(self):
        rule = RuleDDF00051()
        config = _ct_config([{"id": "T1", "type": {"code": "A", "decode": "DA"}}])
        assert rule.validate(config) is True
