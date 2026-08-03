"""Tests for RuleDDF00185 — Administration: dose ↔ administrable product."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00185 import RuleDDF00185
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00185:
    def test_metadata(self):
        rule = RuleDDF00185()
        assert rule._rule == "DDF00185"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_dose_with_direct_ap_passes(self):
        rule = RuleDDF00185()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [
                        {
                            "administrations": [
                                {
                                    "id": "A1",
                                    "dose": 1,
                                    "administrableProductId": "AP1",
                                }
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_dose_with_embedded_ap_passes(self):
        rule = RuleDDF00185()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "medicalDevices": [{"id": "D1", "embeddedProductId": "EP1"}],
                    "studyInterventions": [
                        {
                            "administrations": [
                                {
                                    "id": "A1",
                                    "dose": 1,
                                    "medicalDeviceId": "D1",
                                }
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_dose_without_ap_fails(self):
        rule = RuleDDF00185()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [
                        {"administrations": [{"id": "A1", "dose": 1}]}
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "no administrable product" in rule.errors().dump()

    def test_ap_without_dose_fails(self):
        rule = RuleDDF00185()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [
                        {
                            "administrations": [
                                {"id": "A1", "administrableProductId": "AP1"}
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "no dose" in rule.errors().dump()

    def test_neither_passes(self):
        rule = RuleDDF00185()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [{"administrations": [{"id": "A1"}]}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
