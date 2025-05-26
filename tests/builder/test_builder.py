import os
import pathlib
from src.usdm4.builder.builder import Builder
from tests.helpers.files import write_json_file, read_json_file

SAVE = True


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


def test_minimum():
    instance = Builder(root_path()).minimum("Test Study", "SPONSOR-1234", "1.0.0")
    instance.study.id = "FAKE-UUID"  # UUID is dynamic
    if SAVE:
        write_json_file("minimum", "minimum_expected.json", instance.to_json())
    expected = read_json_file("minimum", "minimum_expected.json")
    assert instance.to_json() == expected


def test_decode_phase_phase_0():
    builder = Builder(root_path())
    result = builder.decode_phase("0")

    assert result.standardCode.code == "C54721"
    assert result.standardCode.decode == "Phase 0 Trial"
    assert result.standardCode.codeSystem == builder._cdisc_code_system
    assert result.standardCode.codeSystemVersion == "2025-03-28"


def test_decode_phase_phase_1():
    builder = Builder(root_path())
    result = builder.decode_phase("1")

    assert result.standardCode.code == "C15600"
    assert result.standardCode.decode == "Phase I Trial"


def test_decode_phase_phase_I():
    builder = Builder(root_path())
    result = builder.decode_phase("I")

    assert result.standardCode.code == "C15600"
    assert result.standardCode.decode == "Phase I Trial"


def test_decode_phase_phase_1_2():
    builder = Builder(root_path())
    result = builder.decode_phase("1-2")

    assert result.standardCode.code == "C15693"
    assert result.standardCode.decode == "Phase I/II Trial"


def test_decode_phase_phase_1_slash_2():
    builder = Builder(root_path())
    result = builder.decode_phase("1/2")

    assert result.standardCode.code == "C15693"
    assert result.standardCode.decode == "Phase I/II Trial"


def test_decode_phase_phase_2a():
    builder = Builder(root_path())
    result = builder.decode_phase("2A")

    assert result.standardCode.code == "C49686"
    assert result.standardCode.decode == "Phase IIa Trial"


def test_decode_phase_phase_3b():
    builder = Builder(root_path())
    result = builder.decode_phase("3B")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C49689"
    assert result.standardCode.decode == "Phase IIIb Trial"


def test_decode_phase_pre_clinical():
    builder = Builder(root_path())
    result = builder.decode_phase("PRE-CLINICAL")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C54721"
    assert result.standardCode.decode == "Phase 0 Trial"


def test_decode_phase_unknown():
    builder = Builder(root_path())
    result = builder.decode_phase("UNKNOWN")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C48660"
    assert result.standardCode.decode == "[Trial Phase] Not Applicable"


def test_decode_phase_empty():
    builder = Builder(root_path())
    result = builder.decode_phase("")

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C48660"
    assert result.standardCode.decode == "[Trial Phase] Not Applicable"


def test_cdisc_code_basic():
    builder = Builder(root_path())
    result = builder.cdisc_code("C12345", "Test Code")

    # assert isinstance(result, Code)
    assert result.code == "C12345"
    assert result.decode == "Test Code"
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == "2025-03-28"


def test_cdisc_code_missing():
    builder = Builder(root_path())
    result = builder.cdisc_code("C12", "Dummy")

    # assert isinstance(result, Code)
    assert result.code == "C12"
    assert result.decode == "Dummy"
    assert result.codeSystem == builder._cdisc_code_system
    assert result.codeSystemVersion == "unknown"


def test_alias_code_basic():
    builder = Builder(root_path())
    sc = builder.cdisc_code("C12345", "Test Code")
    result = builder.alias_code(sc)

    # assert isinstance(result, AliasCode)
    assert result.standardCode.code == "C12345"
    assert result.standardCode.decode == "Test Code"
    assert result.standardCode.codeSystem == builder._cdisc_code_system
    assert result.standardCode.codeSystemVersion == "2025-03-28"
    assert result.standardCodeAliases == []


def test_sponsor_basic():
    builder = Builder(root_path())
    result = builder.sponsor("ACME Pharma")

    # assert isinstance(result, Organization)
    assert result.type.code == "C70793"
    assert result.type.decode == "Clinical Study Sponsor"
    assert result.name == "ACME Pharma"
