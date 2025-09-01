import os
import pathlib
import pytest
from src.usdm4.ct.iso.iso639.library import Library


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def library():
    return Library(root_path())


def test_init(library):
    """Test that the Library class initializes with the expected attributes."""
    assert library.system == "ISO 639-1"
    assert library.version == "2007"


def test_decode_en(library):
    """Test that the decode method returns 'English' for the code 'en'."""
    result = library.decode("en")
    assert result == ("en", "English")


def test_decode_other(library):
    """Test that the decode method returns None for codes other than 'en'."""
    result = library.decode("fr")
    assert result == (None, None)


def test_decode_empty(library):
    """Test that the decode method returns None for an empty string."""
    result = library.decode("")
    assert result == (None, None)


def test_decode_none(library):
    """Test that the decode method handles None gracefully."""
    # The method might handle None by returning None instead of raising an exception
    result = library.decode(None)
    assert result == (None, None)


def test_load_method(library):
    """Test that the load method exists and can be called."""
    # The load method is currently empty, so we just test that it can be called
    # without raising an exception
    try:
        Library(root_path()).load()
    except Exception as e:
        pytest.fail(f"load() method raised {e} unexpectedly!")
