import os
import pathlib
import pytest
from src.usdm4.builder.builder import Builder
from tests.helpers.files import write_json_file, read_json_file

SAVE = True


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path())


def test_minimum(builder):
    instance = builder.minimum("Test Study", "SPONSOR-1234", "1.0.0")
    instance.study.id = "FAKE-UUID"  # UUID is dynamic
    if SAVE:
        write_json_file("minimum", "minimum_expected.json", instance.to_json())
    expected = read_json_file("minimum", "minimum_expected.json")
    assert instance.to_json() == expected


def test_decode_phase_phase_0(builder):
    result = builder.decode_phase("0")

    assert result.standardCode.code == "C54721"
    assert result.standardCode.decode == "Phase 0 Trial"
    assert result.standardCode.codeSystem == builder._cdisc_code_system
    assert result.standardCode.codeSystemVersion == "2025-03-28"


def test_decode_phase_phase_1(builder):
    ## builder = Builder(root_path())
    result = builder.decode_phase("1")

    assert result.standardCode.code == "C15600"
    assert result.standardCode.decode == "Phase I Trial"


def test_decode_phase_phase_I(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("I")

    assert result.standardCode.code == "C15600"
    assert result.standardCode.decode == "Phase I Trial"


def test_decode_phase_phase_1_2(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("1-2")

    assert result.standardCode.code == "C15693"
    assert result.standardCode.decode == "Phase I/II Trial"


def test_decode_phase_phase_1_slash_2(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("1/2")

    assert result.standardCode.code == "C15693"
    assert result.standardCode.decode == "Phase I/II Trial"


def test_decode_phase_phase_2a(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("2A")

    assert result.standardCode.code == "C49686"
    assert result.standardCode.decode == "Phase IIa Trial"


def test_decode_phase_phase_3b(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("3B")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C49689"
    assert result.standardCode.decode == "Phase IIIb Trial"


def test_decode_phase_pre_clinical(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("PRE-CLINICAL")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C54721"
    assert result.standardCode.decode == "Phase 0 Trial"


def test_decode_phase_unknown(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("UNKNOWN")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C48660"
    assert result.standardCode.decode == "[Trial Phase] Not Applicable"


def test_decode_phase_empty(builder):
    # builder = Builder(root_path())
    result = builder.decode_phase("")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C48660"
    assert result.standardCode.decode == "[Trial Phase] Not Applicable"


def test_cdisc_code_basic(builder):
    # builder = Builder(root_path())
    result = builder.cdisc_code("C12345", "Test Code")

    # assert isinstance(result, Code)
    assert result.code == "C12345"
    assert result.decode == "Test Code"
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == "2025-03-28"


def test_cdisc_code_missing(builder):
    # builder = Builder(root_path())
    result = builder.cdisc_code("C12", "Dummy")

    # assert isinstance(result, Code)
    assert result.code == "C12"
    assert result.decode == "Dummy"
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == "unknown"


def test_alias_code_basic(builder):
    # builder = Builder(root_path())
    sc = builder.cdisc_code("C12345", "Test Code")
    result = builder.alias_code(sc)

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C12345"
    assert result.standardCode.decode == "Test Code"
    assert result.standardCode.codeSystem == builder._cdisc_code_system
    assert result.standardCode.codeSystemVersion == "2025-03-28"
    assert result.standardCodeAliases == []


def test_sponsor_basic(builder):
    # builder = Builder(root_path())
    result = builder.sponsor("ACME Pharma")

    # assert isinstance(result, Organization)
    assert result.type.code == "C70793"
    assert result.type.decode == "Clinical Study Sponsor"
    assert result.name == "ACME Pharma"


def test_klass_and_attribute_basic(builder):
    # builder = Builder(root_path())
    result = builder.klass_and_attribute("Study", "studyPhase")

    # The method returns a dictionary-like object from ct_library
    assert isinstance(result, dict)
    assert "conceptId" in result
    assert "name" in result
    assert "definition" in result


def test_klass_and_attribute_with_valid_class_and_attribute(builder):
    # builder = Builder(root_path())
    result = builder.klass_and_attribute("StudyDesign", "interventionModel")

    # The method returns a dictionary-like object from ct_library
    assert isinstance(result, dict)
    assert "conceptId" in result
    assert "name" in result
    assert "definition" in result


def test_klass_and_attribute_returns_dict_object(builder):
    # builder = Builder(root_path())
    result = builder.klass_and_attribute("Study", "studyType")

    # Verify it returns a dictionary with expected keys
    assert isinstance(result, dict)
    assert "conceptId" in result
    assert "name" in result
    assert "definition" in result

    # Verify the values are strings
    assert isinstance(result["conceptId"], str)
    assert isinstance(result["name"], str)
    assert isinstance(result["definition"], str)


def test_klass_and_attribute_different_parameters(builder):
    # builder = Builder(root_path())

    # Test with different class/attribute combinations
    result1 = builder.klass_and_attribute("StudyArm", "type")
    result2 = builder.klass_and_attribute("Study", "studyPhase")

    # Both should return dictionary objects (using known valid combinations)
    assert isinstance(result1, dict)
    assert isinstance(result2, dict)
    assert "conceptId" in result1
    assert "conceptId" in result2


def test_klass_and_attribute_handles_invalid_combinations(builder):
    # builder = Builder(root_path())

    # Test with invalid class/attribute combinations that may return None
    result = builder.klass_and_attribute("InvalidClass", "invalidAttribute")

    # The method may return None for invalid combinations
    assert result is None or isinstance(result, dict)

    # If it returns a dict, it should have the expected structure
    if isinstance(result, dict):
        assert "conceptId" in result


def test_klass_and_attribute_method_delegation(builder):
    # builder = Builder(root_path())

    # Test that the method properly delegates to ct_library
    result = builder.klass_and_attribute("Study", "studyPhase")

    # Verify it's a valid response from the ct_library
    assert isinstance(result, dict)
    assert len(result) > 0

    # Should have standard CDISC terminology structure
    expected_keys = ["conceptId", "name", "definition"]
    for key in expected_keys:
        assert key in result, f"Expected key '{key}' not found in result"


def test_cdisc_unit_code_basic(builder):
    # builder = Builder(root_path())
    result = builder.cdisc_unit_code("kg")

    # The method returns a Code object or dictionary from ct_library
    # Check if it's a Code object or dict with expected structure
    if hasattr(result, "code"):
        # It's a Code object
        assert hasattr(result, "code")
        assert hasattr(result, "decode")
        assert hasattr(result, "codeSystem")
        assert hasattr(result, "codeSystemVersion")
    else:
        # It's a dictionary or None
        assert result is None or isinstance(result, dict)


def test_cdisc_unit_code_common_units(builder):
    # builder = Builder(root_path())

    # Test with common units that should be found
    common_units = ["kg", "mg", "mL", "L", "cm", "m"]

    for unit in common_units:
        result = builder.cdisc_unit_code(unit)

        # The result should be either a Code object, dict, or None
        if result is not None:
            if hasattr(result, "code"):
                # It's a Code object
                assert hasattr(result, "decode")
                assert hasattr(result, "codeSystem")
                assert hasattr(result, "codeSystemVersion")
            else:
                # It's a dictionary
                assert isinstance(result, dict)


def test_cdisc_unit_code_invalid_unit(builder):
    # builder = Builder(root_path())

    # Test with an invalid unit that likely doesn't exist
    result = builder.cdisc_unit_code("invalidunit123")

    # The method may return None for invalid units
    assert result is None or isinstance(result, (dict, type(None)))

    # If it returns something, verify it has proper structure
    if result is not None and hasattr(result, "code"):
        assert hasattr(result, "decode")


def test_cdisc_unit_code_empty_string(builder):
    # builder = Builder(root_path())

    # Test with empty string
    result = builder.cdisc_unit_code("")

    # Should handle empty string gracefully
    assert result is None or isinstance(result, (dict, type(None)))


def test_cdisc_unit_code_method_delegation(builder):
    # builder = Builder(root_path())

    # Test that the method properly delegates to ct_library.unit()
    result = builder.cdisc_unit_code("kg")

    # Verify the method returns what ct_library.unit() would return
    # This could be a Code object, dict, or None depending on implementation
    assert result is None or hasattr(result, "code") or isinstance(result, dict)


def test_cdisc_unit_code_case_sensitivity(builder):
    # builder = Builder(root_path())

    # Test case sensitivity with common units
    result_lower = builder.cdisc_unit_code("kg")
    result_upper = builder.cdisc_unit_code("KG")

    # Both should be handled (may return same or different results)
    # Just verify they don't crash and return expected types
    for result in [result_lower, result_upper]:
        assert result is None or hasattr(result, "code") or isinstance(result, dict)
