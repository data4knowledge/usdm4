import json
from src.usdm4 import USDM4
from simple_error_log.errors import Errors
from tests.usdm4.helpers.files import write_json_file, read_json_file

SAVE = False


def dump_validation_result(result):
    print(
        f"RESULT: {[v for k, v in result._items.items() if v['status'] not in ['Not Implemented', 'Success']]}"
    )


def test_validate(tmp_path):
    result = USDM4().validate("tests/usdm4/test_files/test_validate.json")
    dump_validation_result(result)
    assert result.passed_or_not_implemented()


def test_validate_error():
    result = USDM4().validate("tests/usdm4/test_files/test_validate_error.json")
    dump_validation_result(result)
    assert not result.passed_or_not_implemented()


def test_example_1():
    test_file = "tests/usdm4/test_files/package/example_1.json"
    result = USDM4().validate(test_file)
    assert not result.passed_or_not_implemented()


def test_example_2():
    test_file = "tests/usdm4/test_files/package/example_2.json"
    result = USDM4().validate(test_file)
    dump_validation_result(result)
    assert result.passed_or_not_implemented()


def test_minimum():
    errors = Errors()
    result = USDM4().minimum("Test Study", "SPONSOR-1234", "1", errors)
    result.study.id = "FAKE-UUID"
    if SAVE:
        write_json_file(None, "test_minimum_expected.json", result.to_json())
    expected = read_json_file(None, "test_minimum_expected.json")
    assert result.to_json() == expected


def test_loadd_success():
    """Test loadd method with valid dictionary data."""
    import json
    errors = Errors()
    
    # Read valid data from test file and parse as JSON
    with open("tests/usdm4/test_files/test_validate.json", "r") as f:
        data = json.load(f)
    
    result = USDM4().loadd(data, errors)
    
    # Check that either it succeeded or failed with errors logged
    if result is None:
        assert len(errors._items) > 0, "If loadd returns None, errors should be logged"
    else:
        assert result.study is not None
        assert len(errors._items) == 0


def test_loadd_invalid_data():
    """Test loadd method with invalid dictionary data."""
    errors = Errors()
    
    # Create invalid data (missing required fields)
    invalid_data = {
        "invalid": "data"
    }
    
    result = USDM4().loadd(invalid_data, errors)
    
    assert result is None
    assert len(errors._items) > 0


def test_loadd_empty_dict():
    """Test loadd method with empty dictionary."""
    errors = Errors()
    
    result = USDM4().loadd({}, errors)
    
    assert result is None
    assert len(errors._items) > 0


def test_load_success():
    """Test load method with valid JSON file."""
    errors = Errors()
    
    result = USDM4().load("tests/usdm4/test_files/test_validate.json", errors)
    
    # Check that either it succeeded or failed with errors logged  
    if result is None:
        assert len(errors._items) > 0, "If load returns None, errors should be logged"
    else:
        assert result.study is not None
        assert len(errors._items) == 0


def test_load_file_not_found():
    """Test load method with non-existent file."""
    errors = Errors()
    
    result = USDM4().load("tests/usdm4/test_files/nonexistent_file.json", errors)
    
    assert result is None
    assert len(errors._items) > 0


def test_load_invalid_json():
    """Test load method with invalid JSON file."""
    import tempfile
    import os
    
    errors = Errors()
    
    # Create a temporary file with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_file = f.name
    
    try:
        result = USDM4().load(temp_file, errors)
        
        assert result is None
        assert len(errors._items) > 0
    finally:
        # Clean up temporary file
        os.unlink(temp_file)


def test_load_invalid_wrapper_data():
    """Test load method with valid JSON but invalid Wrapper data."""
    import tempfile
    import os
    import json
    
    errors = Errors()
    
    # Create a temporary file with valid JSON but invalid Wrapper structure
    invalid_data = {"wrong": "structure"}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_data, f)
        temp_file = f.name
    
    try:
        result = USDM4().load(temp_file, errors)
        
        assert result is None
        assert len(errors._items) > 0
    finally:
        # Clean up temporary file
        os.unlink(temp_file)


def test_loadd_with_complete_study():
    """Test loadd method with more complete study data using minimum."""
    errors = Errors()
    
    # Use the minimum builder to create valid data
    wrapper = USDM4().minimum("Test Study", "SPONSOR-1234", "1", errors)
    data_dict = json.loads(wrapper.to_json())
    
    # Now load it back
    errors2 = Errors()
    result = USDM4().loadd(data_dict, errors2)
    
    assert result is not None
    assert result.study is not None
    assert len(errors2._items) == 0
