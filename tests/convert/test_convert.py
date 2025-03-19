from usdm4 import USDM4
from tests.helpers.files import read_json_file, write_json_file, file_path

SAVE = True


def run_test(sub_dir: str, filename: str, save: bool = False):
    full_path = file_path(sub_dir, filename)
    result = USDM4().convert(full_path)
    if save or SAVE:
        write_json_file(sub_dir, f"{filename}_expected", result.to_json())
    expected = read_json_file(sub_dir, f"{filename}_expected")
    assert result.to_json() == expected


def run_validate(filename: str):
    test_file = file_path("convert", filename)
    result = USDM4().validate(test_file)
    assert not result.passed_or_not_implemented()


def test_usdm_1():
    run_test("convert", "example_1")


def test_usdm_2():
    run_test("convert", "example_2")


def test_usdm_1_validate():
    run_validate("example_1")


def test_usdm_2_validate():
    run_validate("example_2")
