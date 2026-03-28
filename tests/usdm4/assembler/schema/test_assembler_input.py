import pytest
from pydantic import ValidationError
from src.usdm4.assembler.schema import AssemblerInput


@pytest.fixture
def minimal_valid_dict():
    return {
        "identification": {"titles": {"brief": "Test"}},
        "document": {"document": {"label": "Doc", "version": "1.0", "status": "final", "template": "T", "version_date": "2024-01-01"}, "sections": []},
        "population": {"label": "Pop", "inclusion_exclusion": {"inclusion": [], "exclusion": []}},
        "study_design": {"label": "Design", "rationale": "R", "trial_phase": "1"},
        "study": {"name": {"acronym": "TST"}, "version": "1.0", "rationale": "R"},
    }


class TestAssemblerInputValidation:

    def test_minimal_valid_dict_passes(self, minimal_valid_dict):
        result = AssemblerInput.model_validate(minimal_valid_dict)
        assert result.identification.titles.brief == "Test"
        assert result.study.version == "1.0"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            AssemblerInput.model_validate({"identification": {}})
        errors = exc_info.value.errors()
        field_paths = [".".join(str(loc) for loc in e["loc"]) for e in errors]
        assert any("document" in p for p in field_paths)
        assert any("population" in p for p in field_paths)
        assert any("study_design" in p for p in field_paths)
        assert any("study" in p for p in field_paths)

    def test_empty_dict_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            AssemblerInput.model_validate({})
        assert len(exc_info.value.errors()) >= 4

    def test_amendments_defaults_when_missing(self, minimal_valid_dict):
        result = AssemblerInput.model_validate(minimal_valid_dict)
        assert result.amendments.identifier == ""
        assert result.amendments.summary == ""

    def test_soa_defaults_to_none(self, minimal_valid_dict):
        result = AssemblerInput.model_validate(minimal_valid_dict)
        assert result.soa is None

    def test_soa_accepted_when_provided(self, minimal_valid_dict):
        minimal_valid_dict["soa"] = {
            "epochs": {"items": [{"text": "Screening"}]},
            "visits": {"items": []},
            "timepoints": {"items": []},
            "windows": {"items": []},
            "activities": {"items": []},
            "conditions": {"items": []},
        }
        result = AssemblerInput.model_validate(minimal_valid_dict)
        assert result.soa is not None
        assert len(result.soa.epochs.items) == 1

    def test_extra_keys_ignored(self, minimal_valid_dict):
        minimal_valid_dict["unexpected"] = "data"
        minimal_valid_dict["another"] = 42
        result = AssemblerInput.model_validate(minimal_valid_dict)
        assert result.study.version == "1.0"

    def test_validate_strict_warns_on_empty_official_title(self, minimal_valid_dict):
        minimal_valid_dict["identification"]["titles"] = {}
        result, warnings = AssemblerInput.validate_strict(minimal_valid_dict)
        assert any("official" in w for w in warnings)

    def test_validate_strict_warns_on_empty_document_version(self, minimal_valid_dict):
        minimal_valid_dict["document"]["document"]["version"] = ""
        result, warnings = AssemblerInput.validate_strict(minimal_valid_dict)
        assert any("document.document.version" in w for w in warnings)

    def test_validate_strict_warns_on_empty_study_version(self, minimal_valid_dict):
        minimal_valid_dict["study"]["version"] = ""
        result, warnings = AssemblerInput.validate_strict(minimal_valid_dict)
        assert any("study.version" in w for w in warnings)

    def test_validate_strict_no_warnings_when_complete(self, minimal_valid_dict):
        minimal_valid_dict["identification"]["titles"]["official"] = "Full Title"
        result, warnings = AssemblerInput.validate_strict(minimal_valid_dict)
        assert len(warnings) == 0

    def test_none_input_raises(self):
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate(None)

    def test_string_input_raises(self):
        with pytest.raises(ValidationError):
            AssemblerInput.model_validate("not a dict")
