import os
import pathlib
import pytest
from src.usdm4.ct.iso.iso3166.library import Library


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.parent.resolve()
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


def text_code_or_decode(library):
    alpha3, name = library.code_or_decode("Denmark")
    assert alpha3 == "DK"
    assert name == "Denmark"
    alpha3, name = library.code_or_decode("DK")
    assert alpha3 == "DK"
    assert name == "Denmark"


def text_code_or_decode_nonexistant(library):
    alpha3, name = library.code_or_decode("DenmarkX")
    assert alpha3 is None
    assert name is None


def text_code(library):
    alpha3, name = library.code("Denmark")
    assert alpha3 == "DK"
    assert name == "Denmark"


def text_code_nonexistant(library):
    alpha3, name = library.code("DenmarkX")
    assert alpha3 is None
    assert name is None


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


def test_load_method(library):
    """Test that the load method exists and can be called."""
    # Mock the open function to avoid actual file operations
    try:
        Library(root_path()).load()
    except Exception as e:
        pytest.fail(f"load() method raised {e} unexpectedly!")
