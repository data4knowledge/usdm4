import pytest
from pydantic import ValidationError
from src.usdm4.assembler.schema.identification_schema import (
    IdentificationInput,
    StudyIdentifier,
    Titles,
    Address,
)


class TestTitles:
    def test_empty_defaults(self):
        t = Titles()
        assert t.brief == ""
        assert t.official == ""
        assert t.acronym == ""

    def test_partial_titles(self):
        t = Titles.model_validate({"brief": "B", "official": "O"})
        assert t.brief == "B"
        assert t.scientific == ""


class TestAddress:
    def test_empty_defaults(self):
        a = Address()
        assert a.lines == []
        assert a.country == ""

    def test_full_address(self):
        a = Address.model_validate(
            {
                "lines": ["123 Main St"],
                "city": "Boston",
                "state": "MA",
                "postalCode": "02101",
                "country": "USA",
            }
        )
        assert a.city == "Boston"


class TestStudyIdentifier:
    def test_standard_scope(self):
        si = StudyIdentifier.model_validate(
            {
                "identifier": "NCT123",
                "scope": {"standard": "nct"},
            }
        )
        assert si.identifier == "NCT123"
        assert si.scope.standard == "nct"

    def test_non_standard_scope(self):
        si = StudyIdentifier.model_validate(
            {
                "identifier": "CUSTOM-1",
                "scope": {
                    "non_standard": {
                        "type": "registry",
                        "name": "Custom Reg",
                    }
                },
            }
        )
        assert si.scope.non_standard.type == "registry"
        assert si.scope.non_standard.name == "Custom Reg"

    def test_non_standard_scope_without_address(self):
        si = StudyIdentifier.model_validate(
            {
                "identifier": "CUSTOM-2",
                "scope": {
                    "non_standard": {
                        "type": "pharma",
                        "name": "No Address Org",
                    }
                },
            }
        )
        assert si.scope.non_standard.legalAddress is None

    def test_non_standard_scope_with_explicit_none_address(self):
        si = StudyIdentifier.model_validate(
            {
                "identifier": "CUSTOM-3",
                "scope": {
                    "non_standard": {
                        "type": "pharma",
                        "name": "Explicit None Org",
                        "legalAddress": None,
                    }
                },
            }
        )
        assert si.scope.non_standard.legalAddress is None

    def test_non_standard_scope_with_address(self):
        si = StudyIdentifier.model_validate(
            {
                "identifier": "CUSTOM-4",
                "scope": {
                    "non_standard": {
                        "type": "pharma",
                        "name": "With Address Org",
                        "legalAddress": {
                            "lines": ["123 Main St"],
                            "city": "Boston",
                            "country": "USA",
                        },
                    }
                },
            }
        )
        assert si.scope.non_standard.legalAddress is not None
        assert si.scope.non_standard.legalAddress.city == "Boston"

    def test_missing_identifier_raises(self):
        with pytest.raises(ValidationError):
            StudyIdentifier.model_validate({"scope": {"standard": "nct"}})


class TestIdentificationInput:
    def test_empty_defaults(self):
        ii = IdentificationInput()
        assert ii.identifiers == []
        assert ii.roles == {}

    def test_full_input(self):
        data = {
            "titles": {"brief": "Test", "official": "Official Test"},
            "identifiers": [
                {"identifier": "NCT123", "scope": {"standard": "nct"}},
            ],
            "roles": {"co_sponsor": {"name": "Acme Corp"}},
            "other": {
                "medical_expert": {"name": "Dr. Smith"},
                "sponsor_signatory": "J. Doe",
                "compound_names": "CompA",
                "compound_codes": "C001",
            },
        }
        result = IdentificationInput.model_validate(data)
        assert result.titles.brief == "Test"
        assert len(result.identifiers) == 1
        assert result.other.sponsor_signatory == "J. Doe"

    def test_extra_keys_in_nested_dict_ignored(self):
        data = {
            "titles": {"brief": "Test", "unknown_title": "X"},
            "identifiers": [],
        }
        result = IdentificationInput.model_validate(data)
        assert result.titles.brief == "Test"
