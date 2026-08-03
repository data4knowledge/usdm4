"""Tests for RuleDDF00212 — ProductOrganizationRole.appliesToIds target class."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00212 import RuleDDF00212
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00212:
    def test_metadata(self):
        rule = RuleDDF00212()
        assert rule._rule == "DDF00212"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products."
        )

    def _data(self, roles, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = roles
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        return data

    def test_empty_applies_to_is_skipped(self):
        rule = RuleDDF00212()
        assert (
            rule.validate(
                {"data": self._data([{"id": "R1"}, {"id": "R2", "appliesToIds": None}])}
            )
            is True
        )
        assert rule.errors().count() == 0

    def test_falsy_target_id_is_skipped(self):
        """Empty-string / None entries in appliesToIds skip the resolution
        step without logging failure."""
        rule = RuleDDF00212()
        assert (
            rule.validate(
                {"data": self._data([{"id": "R1", "appliesToIds": ["", None]}])}
            )
            is True
        )
        assert rule.errors().count() == 0

    def test_unresolved_target_logs_failure(self):
        """instance_by_id returns None → 'does not resolve to any instance'."""
        rule = RuleDDF00212()
        result = rule.validate(
            {
                "data": self._data(
                    [{"id": "R1", "appliesToIds": ["ghost"]}],
                    id_map={},
                )
            }
        )
        assert result is False
        assert rule.errors().count() == 1

    def test_target_resolves_to_wrong_class_logs_failure(self):
        """Target resolves but instanceType isn't allowed → failure."""
        rule = RuleDDF00212()
        result = rule.validate(
            {
                "data": self._data(
                    [{"id": "R1", "appliesToIds": ["bad"]}],
                    id_map={"bad": {"id": "bad", "instanceType": "Procedure"}},
                )
            }
        )
        assert result is False
        assert rule.errors().count() == 1

    def test_administrable_product_passes(self):
        rule = RuleDDF00212()
        assert (
            rule.validate(
                {
                    "data": self._data(
                        [{"id": "R1", "appliesToIds": ["ap1"]}],
                        id_map={
                            "ap1": {"id": "ap1", "instanceType": "AdministrableProduct"}
                        },
                    )
                }
            )
            is True
        )

    def test_medical_device_passes(self):
        rule = RuleDDF00212()
        assert (
            rule.validate(
                {
                    "data": self._data(
                        [{"id": "R1", "appliesToIds": ["md1"]}],
                        id_map={"md1": {"id": "md1", "instanceType": "MedicalDevice"}},
                    )
                }
            )
            is True
        )
