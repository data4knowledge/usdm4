import pytest
from src.usdm4.assembler.schema.amendments_schema import (
    AmendmentsInput,
    AmendmentScope,
    AmendmentImpact,
    AmendmentChange,
)


class TestAmendmentsInput:

    def test_defaults(self):
        a = AmendmentsInput()
        assert a.identifier == ""
        assert a.enrollment is None
        assert a.scope is None
        assert a.changes == []

    def test_full_amendment(self):
        data = {
            "identifier": "AMD-001",
            "summary": "Safety update",
            "reasons": {"primary": "Safety signal", "secondary": "Efficacy review"},
            "impact": {
                "safety_and_rights": {
                    "safety": {"substantial": True, "reason": "New adverse event"},
                    "rights": {"substantial": False, "reason": ""},
                },
                "reliability_and_robustness": {
                    "reliability": {"substantial": False, "reason": ""},
                    "robustness": {"substantial": False, "reason": ""},
                },
            },
            "enrollment": {"value": 100, "unit": "%"},
            "scope": {"global": True},
            "changes": [
                {"section": "1.2, Background", "description": "Updated safety info", "rationale": "New data"},
            ],
        }
        result = AmendmentsInput.model_validate(data)
        assert result.identifier == "AMD-001"
        assert result.enrollment.value == 100
        assert len(result.changes) == 1


class TestAmendmentScope:

    def test_global_alias(self):
        """Test that 'global' key in dict maps to global_ field."""
        s = AmendmentScope.model_validate({"global": True, "countries": ["US", "UK"]})
        assert s.global_ is True
        assert s.countries == ["US", "UK"]

    def test_defaults(self):
        s = AmendmentScope()
        assert s.global_ is False
        assert s.countries == []
        assert s.sites == []


class TestAmendmentImpact:

    def test_defaults(self):
        i = AmendmentImpact()
        assert i.safety_and_rights.safety.substantial is False
        assert i.reliability_and_robustness.robustness.reason == ""

    def test_flat_impact_ignored_gracefully(self):
        """Test data with flat structure (as in existing test fixtures) doesn't crash."""
        i = AmendmentImpact.model_validate({"safety": False, "reliability": False})
        assert i.safety_and_rights.safety.substantial is False
