from usdm4 import USDM4
from tests.helpers.files import (
    read_json_file,
    write_json_file,
    read_yaml_file,
    write_yaml_file,
    file_path,
)
from tests.helpers.rule_error import fix_timestamp


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
