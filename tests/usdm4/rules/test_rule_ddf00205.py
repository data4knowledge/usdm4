"""Tests for RuleDDF00205 — Admin AP must not also be device embedded product."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00205 import RuleDDF00205
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00205:
    def test_metadata(self):
        rule = RuleDDF00205()
        assert rule._rule == "DDF00205"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, admins, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = admins
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        return data

    def test_missing_ap_or_md_skipped(self):
        rule = RuleDDF00205()
        data = self._data(
            [
                {"id": "A1", "administrableProductId": "AP"},  # no MD
                {"id": "A2", "medicalDeviceId": "MD"},  # no AP
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_medical_device_not_resolved_skipped(self):
        rule = RuleDDF00205()
        data = self._data(
            [{"id": "A1", "administrableProductId": "AP", "medicalDeviceId": "MD"}],
            id_map={},  # MD doesn't resolve
        )
        assert rule.validate({"data": data}) is True

    def test_device_embedded_matches_ap_fails(self):
        rule = RuleDDF00205()
        data = self._data(
            [{"id": "A1", "administrableProductId": "AP", "medicalDeviceId": "MD"}],
            id_map={"MD": {"id": "MD", "embeddedProductId": "AP"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_device_embedded_differs_passes(self):
        rule = RuleDDF00205()
        data = self._data(
            [{"id": "A1", "administrableProductId": "AP", "medicalDeviceId": "MD"}],
            id_map={"MD": {"id": "MD", "embeddedProductId": "OTHER"}},
        )
        assert rule.validate({"data": data}) is True
