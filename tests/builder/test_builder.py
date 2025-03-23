from src.usdm4.builder.builder import Builder
from src.usdm4.api.alias_code import AliasCode
from src.usdm4.api.code import Code
from src.usdm4.api.organization import Organization
from tests.helpers.files import write_json_file, read_json_file

SAVE = False


def test_minimum():
    instance = Builder().minimum("Test Study", "SPONSOR-1234", "1.0.0")
    instance.study.id = "FAKE-UUID"  # UUID is dynamic
    if SAVE:
        write_json_file("minimum", "minimum_expected.json", instance.to_json())
    expected = read_json_file("minimum", "minimum_expected.json")
    assert instance.to_json() == expected


def test_decode_phase_phase_0():
    builder = Builder()
    result = builder.decode_phase("0")

    assert result.standardCode.code == "C54721"
    assert result.standardCode.decode == "Phase 0 Trial"
    assert result.standardCode.codeSystem == builder._cdisc_code_system
    assert result.standardCode.codeSystemVersion == builder._cdisc_code_system_version


def test_decode_phase_phase_1():
    builder = Builder()
    result = builder.decode_phase("1")

    assert result.standardCode.code == "C15600"
    assert result.standardCode.decode == "Phase I Trial"


def test_decode_phase_phase_I():
    builder = Builder()
    result = builder.decode_phase("I")

    assert result.standardCode.code == "C15600"
    assert result.standardCode.decode == "Phase I Trial"


def test_decode_phase_phase_1_2():
    builder = Builder()
    result = builder.decode_phase("1-2")

    assert result.standardCode.code == "C15693"
    assert result.standardCode.decode == "Phase I/II Trial"


def test_decode_phase_phase_1_slash_2():
    builder = Builder()
    result = builder.decode_phase("1/2")

    assert result.standardCode.code == "C15693"
    assert result.standardCode.decode == "Phase I/II Trial"


def test_decode_phase_phase_2a():
    builder = Builder()
    result = builder.decode_phase("2A")

    assert result.standardCode.code == "C49686"
    assert result.standardCode.decode == "Phase IIa Trial"


def test_decode_phase_phase_3b():
    builder = Builder()
    result = builder.decode_phase("3B")

    #assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C49689"
    assert result.standardCode.decode == "Phase IIIb Trial"


def test_decode_phase_pre_clinical():
    builder = Builder()
    result = builder.decode_phase("PRE-CLINICAL")

    #assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C54721"
    assert result.standardCode.decode == "Phase 0 Trial"


def test_decode_phase_unknown():
    builder = Builder()
    result = builder.decode_phase("UNKNOWN")

    #assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C48660"
    assert result.standardCode.decode == "[Trial Phase] Not Applicable"


def test_decode_phase_empty():
    builder = Builder()
    result = builder.decode_phase("")

    #assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C48660"
    assert result.standardCode.decode == "[Trial Phase] Not Applicable"


def test_cdisc_code_basic():
    builder = Builder()
    result = builder.cdisc_code("C12345", "Test Code")

    #assert isinstance(result, Code)
    assert result.code == "C12345"
    assert result.decode == "Test Code"
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == builder._cdisc_code_system_version


def test_cdisc_code_empty_values():
    builder = Builder()
    result = builder.cdisc_code("", "")

    #assert isinstance(result, Code)
    assert result.code == ""
    assert result.decode == ""
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == builder._cdisc_code_system_version


def test_cdisc_code_special_characters():
    builder = Builder()
    result = builder.cdisc_code("C99999", "Special & Characters: 123!@#")

    #assert isinstance(result, Code)
    assert result.code == "C99999"
    assert result.decode == "Special & Characters: 123!@#"
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == builder._cdisc_code_system_version


def test_cdisc_code_system_values():
    builder = Builder()
    # Store original values
    original_system = builder._cdisc_code_system
    original_version = builder._cdisc_code_system_version

    # Modify the system values
    builder._cdisc_code_system = "test.system"
    builder._cdisc_code_system_version = "test-version"

    result = builder.cdisc_code("C54321", "Test with custom system")

    #assert isinstance(result, Code)
    assert result.code == "C54321"
    assert result.decode == "Test with custom system"
    assert result.codeSystem == "test.system"
    assert result.codeSystemVersion == "test-version"

    # Restore original values
    builder._cdisc_code_system = original_system
    builder._cdisc_code_system_version = original_version


def test_alias_code_basic():
    builder = Builder()
    sc = builder.cdisc_code("C12345", "Test Code")
    result = builder.alias_code(sc)

    #assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C12345"
    assert result.standardCode.decode == "Test Code"
    assert result.standardCode.codeSystem == builder._cdisc_code_system
    assert result.standardCode.codeSystemVersion == builder._cdisc_code_system_version
    assert result.standardCodeAliases == []


def test_sponsor_basic():
    builder = Builder()
    result = builder.sponsor("ACME Pharma")

    #assert isinstance(result, Organization)
    assert result.type.code == "C70793"
    assert result.type.decode == "Clinical Study Sponsor"
    assert result.name == "ACME Pharma"
