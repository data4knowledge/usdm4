"""Tests for RuleDDF00083 — no-op, delegated to DDF00082."""

from usdm4.rules.library.rule_ddf00083 import RuleDDF00083
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00083:
    def test_metadata(self):
        rule = RuleDDF00083()
        assert rule._rule == "DDF00083"
        assert rule._level == RuleTemplate.ERROR

    def test_validate_is_noop(self):
        rule = RuleDDF00083()
        assert rule.validate({"data": None}) is True
