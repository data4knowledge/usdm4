from usdm4.minimum.minimum import Minimum
from tests.helpers.files import write_json_file, read_json_file

SAVE = False


def test_minimum():
    instance = Minimum.minimum("Test Study", "SPONSOR-1234", "1.0.0")
    instance.study.id = "FAKE-UUID"  # UUID is dynamic
    if SAVE:
        write_json_file("minimum", "minimum_expected.json", instance.to_json())
    expected = read_json_file("minimum", "minimum_expected.json")
    assert instance.to_json() == expected
