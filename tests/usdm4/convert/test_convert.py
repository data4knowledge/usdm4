from usdm4 import USDM4
from tests.usdm4.helpers.files import (
    read_json_file,
    write_json_file,
    read_yaml_file,
    write_yaml_file,
    file_path,
)
from tests.usdm4.helpers.rule_error import fix_timestamp


SAVE = False


def fix_timestamps(data: list[dict]) -> list[dict]:
    result = []
    for item in data:
        result.append(fix_timestamp(item))
    return result


def run_test(sub_dir: str, file_stem: str, save: bool = False):
    full_path = file_path(sub_dir, f"{file_stem}.json")
    result = USDM4().convert(full_path)
    if save or SAVE:
        write_json_file(sub_dir, f"{file_stem}_expected.json", result.to_json())
    expected = read_json_file(sub_dir, f"{file_stem}_expected.json")
    assert result.to_json() == expected


def run_validate(sub_dir: str, file_stem: str, save: bool = False):
    test_file = file_path("convert", f"{file_stem}_expected.json")
    result = USDM4().validate(test_file)
    errors = result.to_dict()
    errors = [x for x in errors if x["status"] in ["Failure", "Exception"]]
    new_errors = fix_timestamps(
        errors
    )  # Timestamps are dynamic so check exist and then fix
    if save or SAVE:
        write_yaml_file(sub_dir, f"{file_stem}_errors.yaml", new_errors)
    expected = read_yaml_file(sub_dir, f"{file_stem}_errors.yaml")
    assert new_errors == expected


def test_usdm_1():
    run_test("convert", "example_1")


def test_usdm_2():
    run_test("convert", "example_2")


def test_usdm_3():
    run_test("convert", "example_3")


def test_usdm_4():
    run_test("convert", "example_4")


def test_usdm_1_validate():
    run_validate("convert", "example_1")


def test_usdm_2_validate():
    run_validate("convert", "example_2")


def test_usdm_3_validate():
    run_validate("convert", "example_3")


def test_usdm_4_validate():
    run_validate("convert", "example_4")


def test_convert_static_methods():
    """Test static methods to achieve 100% coverage."""
    from usdm4.convert.convert import Convert

    # Test case for line 190: _convert_population with None population
    result_none = Convert._convert_population(None, [])
    assert result_none is None

    # Test case for line 250: _convert_range with falsy range (None)
    result_range = Convert._convert_range(None)
    assert result_range is None

    # Test case for line 250: _convert_range with falsy range (empty dict)
    result_range_empty = Convert._convert_range({})
    assert result_range_empty is None

    # Test case for line 250: _convert_range with falsy range (False)
    result_range_false = Convert._convert_range(False)
    assert result_range_false is None

    # Test case for line 255: _convert_range with range["unit"] being None
    range_no_unit = {
        "id": "test_range",
        "minValue": 10,
        "maxValue": 20,
        "unit": None,  # This will trigger the else branch on line 255
    }
    result_range_no_unit = Convert._convert_range(range_no_unit)
    assert result_range_no_unit["minValue"]["unit"] is None
    assert result_range_no_unit["maxValue"]["unit"] is None

    # Test case for line 255: _convert_range with range["unit"] being False
    range_false_unit = {
        "id": "test_range_2",
        "minValue": 5,
        "maxValue": 15,
        "unit": False,  # This will also trigger the else branch on line 255
    }
    result_range_false_unit = Convert._convert_range(range_false_unit)
    assert result_range_false_unit["minValue"]["unit"] is None
    assert result_range_false_unit["maxValue"]["unit"] is None

    # Test case for line 255: _convert_range with range["unit"] being empty string
    range_empty_unit = {
        "id": "test_range_3",
        "minValue": 1,
        "maxValue": 10,
        "unit": "",  # This will also trigger the else branch on line 255
    }
    result_range_empty_unit = Convert._convert_range(range_empty_unit)
    assert result_range_empty_unit["minValue"]["unit"] is None
    assert result_range_empty_unit["maxValue"]["unit"] is None

    # Test case to ensure we cover both min and max iterations in the loop
    range_with_valid_unit = {
        "id": "test_range_4",
        "minValue": 2,
        "maxValue": 8,
        "unit": {"id": "unit_1", "code": "kg", "decode": "kilogram"},
    }
    result_range_with_unit = Convert._convert_range(range_with_valid_unit)
    assert result_range_with_unit["minValue"]["unit"]["id"] == "unit_1_Unit"
    assert result_range_with_unit["maxValue"]["unit"]["id"] == "unit_1_Unit"

    # Test case for line 280: _convert_code_to_alias with falsy code
    result_code = Convert._convert_code_to_alias(None)
    assert result_code is None


def test_convert_documented_by_edge_cases():
    """Test convert method with different documentedBy values to cover line 49."""
    from usdm4.convert.convert import Convert

    # Create minimal valid data structure
    minimal_study_data = {
        "study": {"name": "Test Study", "instanceType": "Study", "versions": []}
    }

    # Test with None documentedBy (should trigger line 49)
    test_data_none = minimal_study_data.copy()
    test_data_none["study"]["documentedBy"] = None
    result = Convert.convert(test_data_none)
    assert result.study.documentedBy == []

    # Test with empty list documentedBy (should trigger line 49)
    test_data_empty = minimal_study_data.copy()
    test_data_empty["study"]["documentedBy"] = []
    result = Convert.convert(test_data_empty)
    assert result.study.documentedBy == []

    # Test with False documentedBy (should trigger line 49)
    test_data_false = minimal_study_data.copy()
    test_data_false["study"]["documentedBy"] = False
    result = Convert.convert(test_data_false)
    assert result.study.documentedBy == []
