import json
from usdm4 import USDM4
from tests.helpers.files import (
    read_json_file,
    write_json_file,
    read_yaml_file,
    write_yaml_file,
    file_path,
)

SAVE = True


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
    if save or SAVE:
        errors = result.to_dict()
        errors = [x for x in errors if x["status"] in ["Failure", "Exception"]]
        write_yaml_file(sub_dir, f"{file_stem}_errors.yaml", errors)
    assert result.passed_or_not_implemented()
    expected = read_yaml_file(sub_dir, f"{file_stem}_errors.yaml")
    assert errors == expected


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
