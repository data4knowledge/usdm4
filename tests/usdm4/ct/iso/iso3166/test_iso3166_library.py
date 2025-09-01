import os
import pathlib
import pytest
from src.usdm4.ct.iso.iso3166.library import Library


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def library():
    lib = Library(root_path())
    lib.db = [
        {
            "alpha-2": "US",
            "alpha-3": "USA",
            "name": "United States of America",
            "region": "Americas",
            "region-code": "019",
            "sub-region": "Northern America",
            "sub-region-code": "021",
            "intermediate-region": "",
            "intermediate-region-code": "",
        },
        {
            "alpha-2": "GB",
            "alpha-3": "GBR",
            "name": "United Kingdom",
            "region": "Europe",
            "region-code": "150",
            "sub-region": "Northern Europe",
            "sub-region-code": "154",
            "intermediate-region": "",
            "intermediate-region-code": "",
        },
        {
            "alpha-2": "DK",
            "alpha-3": "DNK",
            "name": "Denmark",
            "region": "Europe",
            "region-code": "150",
            "sub-region": "Northern Europe",
            "sub-region-code": "154",
            "intermediate-region": "",
            "intermediate-region-code": "",
        },
    ]
    return lib


def test_init(library):
    """Test that the Library class initializes with the expected attributes."""
    assert library.system == "ISO 3166 1 alpha3"
    assert library.version == "2020-08"
    assert library.filepath.endswith("ct/iso/iso3166/iso3166.json")


def test_code_or_decode_by_name(library):
    """Test code_or_decode method with country name."""
    alpha3, name = library.code_or_decode("Denmark")
    assert alpha3 == "DNK"
    assert name == "Denmark"


def test_code_or_decode_by_code(library):
    """Test code_or_decode method with country code."""
    alpha3, name = library.code_or_decode("DK")
    assert alpha3 == "DNK"
    assert name == "Denmark"


def test_code_or_decode_by_alpha3(library):
    """Test code_or_decode method with alpha-3 code."""
    alpha3, name = library.code_or_decode("DNK")
    assert alpha3 == "DNK"
    assert name == "Denmark"


def test_code_or_decode_nonexistent(library):
    """Test code_or_decode method with nonexistent country."""
    alpha3, name = library.code_or_decode("DenmarkX")
    assert alpha3 is None
    assert name is None


def test_code_method(library):
    """Test code method with country name."""
    alpha3, name = library.code("Denmark")
    assert alpha3 == "DNK"
    assert name == "Denmark"


def test_code_method_nonexistent(library):
    """Test code method with nonexistent country name."""
    alpha3, name = library.code("DenmarkX")
    assert alpha3 is None
    assert name is None


def test_code_method_case_insensitive(library):
    """Test code method is case insensitive."""
    alpha3, name = library.code("denmark")
    assert alpha3 == "DNK"
    assert name == "Denmark"


def test_decode_alpha2(library):
    """Test that the decode method returns the correct tuple for alpha-2 codes."""
    alpha3, name = library.decode("US")
    assert alpha3 == "USA"
    assert name == "United States of America"


def test_decode_alpha3(library):
    """Test that the decode method returns the correct tuple for alpha-3 codes."""
    alpha3, name = library.decode("GBR")
    assert alpha3 == "GBR"
    assert name == "United Kingdom"


def test_decode_nonexistent(library):
    """Test that the decode method returns (None, None) for nonexistent codes."""
    alpha3, name = library.decode("XYZ")
    assert alpha3 is None
    assert name is None


def test_region_code_region(library):
    """Test that the region_code method returns the correct tuple for a region."""
    code, name = library.region_code("Europe")
    assert code == "150"
    assert name == "Europe"


def test_region_code_subregion(library):
    """Test that the region_code method returns the correct tuple for a sub-region."""
    code, name = library.region_code("Northern Europe")
    assert code == "154"
    assert name == "Northern Europe"


def test_region_code_case_insensitive(library):
    """Test that the region_code method is case-insensitive."""
    code, name = library.region_code("europe")
    assert code == "150"
    assert name == "Europe"


def test_region_code_nonexistent(library):
    """Test that the region_code method returns (None, None) for nonexistent regions."""
    code, name = library.region_code("Nonexistent Region")
    assert code is None
    assert name is None


def test_region_code_intermediate_region(library):
    """Test region_code method with intermediate region (if available in test data)."""
    # Add test data with intermediate region
    library.db.append(
        {
            "alpha-2": "FR",
            "alpha-3": "FRA",
            "name": "France",
            "region": "Europe",
            "region-code": "150",
            "sub-region": "Western Europe",
            "sub-region-code": "155",
            "intermediate-region": "Western Europe Intermediate",
            "intermediate-region-code": "999",
        }
    )

    code, name = library.region_code("Western Europe Intermediate")
    assert code == "999"
    assert name == "Western Europe Intermediate"


def test_load_method_with_actual_file(library):
    """Test load method with actual file operations."""
    import tempfile
    import json

    # Create a temporary JSON file
    test_data = [
        {
            "alpha-2": "XX",
            "alpha-3": "XXX",
            "name": "Test Country",
            "region": "Test Region",
            "region-code": "999",
            "sub-region": "Test Sub-region",
            "sub-region-code": "888",
            "intermediate-region": "",
            "intermediate-region-code": "",
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name

    try:
        # Create a new library instance and set the filepath to our temp file
        test_lib = Library("/fake/path")
        test_lib.filepath = temp_file
        test_lib.load()

        # Test that the data was loaded correctly
        assert test_lib.db == test_data

        # Test that we can use the loaded data
        alpha3, name = test_lib.decode("XX")
        assert alpha3 == "XXX"
        assert name == "Test Country"

    finally:
        # Clean up the temporary file
        import os

        os.unlink(temp_file)


def test_get_decode_with_different_code_lengths(library):
    """Test _get_decode method with different code lengths."""
    # Test with alpha-2 code
    alpha3, name = library.decode("US")
    assert alpha3 == "USA"
    assert name == "United States of America"

    # Test with alpha-3 code
    alpha3, name = library.decode("USA")
    assert alpha3 == "USA"
    assert name == "United States of America"


def test_get_code_case_sensitivity(library):
    """Test _get_code method case sensitivity."""
    # Test exact case
    alpha3, name = library.code("United States of America")
    assert alpha3 == "USA"
    assert name == "United States of America"

    # Test different case
    alpha3, name = library.code("united states of america")
    assert alpha3 == "USA"
    assert name == "United States of America"

    # Test mixed case
    alpha3, name = library.code("United STATES of AMERICA")
    assert alpha3 == "USA"
    assert name == "United States of America"


def test_load_method(library):
    """Test that the load method exists and can be called."""
    # Mock the open function to avoid actual file operations
    try:
        Library(root_path()).load()
    except Exception as e:
        pytest.fail(f"load() method raised {e} unexpectedly!")
