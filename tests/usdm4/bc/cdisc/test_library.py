"""Tests for the BC (Biomedical Concepts) Library loader.

Covers:
- load() cache-miss path → _get_bcs() → cache.save() (lines 26-27)
- catalogue() (line 34)
- _get_bcs (line 43)
"""

from unittest.mock import MagicMock, patch

from src.usdm4.bc.cdisc.library import Library


def _sample_bcs():
    return {
        "HEIGHT": {
            "synonyms": ["Height", "HT"],
            "label": "Height",
        },
        "WEIGHT": {
            "synonyms": ["Weight", "WT"],
            "label": "Weight",
        },
    }


@patch("src.usdm4.bc.cdisc.library.LibraryAPI")
@patch("src.usdm4.bc.cdisc.library.LibraryCache")
def test_load_cache_hit_reads_from_cache(mock_cache_cls, mock_api_cls, tmp_path):
    mock_cache = MagicMock()
    mock_cache.exists.return_value = True
    mock_cache.read.return_value = _sample_bcs()
    mock_cache_cls.return_value = mock_cache

    lib = Library(str(tmp_path), ct_library=MagicMock())
    lib.load()

    mock_cache.read.assert_called_once()
    mock_cache.save.assert_not_called()
    assert "HEIGHT" in lib._bcs


@patch("src.usdm4.bc.cdisc.library.LibraryAPI")
@patch("src.usdm4.bc.cdisc.library.LibraryCache")
def test_load_cache_miss_fetches_from_api_and_saves(
    mock_cache_cls, mock_api_cls, tmp_path
):
    """Covers lines 26-27 (cache miss branch) and 43 (_get_bcs)."""
    mock_cache = MagicMock()
    mock_cache.exists.return_value = False
    mock_cache_cls.return_value = mock_cache

    mock_api = MagicMock()
    mock_api.refresh.return_value = _sample_bcs()
    mock_api_cls.return_value = mock_api

    lib = Library(str(tmp_path), ct_library=MagicMock())
    lib.load()

    mock_api.refresh.assert_called_once()
    mock_cache.save.assert_called_once_with(_sample_bcs())
    assert lib._bcs == _sample_bcs()


@patch("src.usdm4.bc.cdisc.library.LibraryAPI")
@patch("src.usdm4.bc.cdisc.library.LibraryCache")
def test_exists_uses_bc_index_case_insensitively(
    mock_cache_cls, mock_api_cls, tmp_path
):
    mock_cache = MagicMock()
    mock_cache.exists.return_value = True
    mock_cache.read.return_value = _sample_bcs()
    mock_cache_cls.return_value = mock_cache

    lib = Library(str(tmp_path), ct_library=MagicMock())
    lib.load()

    assert lib.exists("HEIGHT") is True
    assert lib.exists("Height") is True
    assert lib.exists("ht") is True
    assert lib.exists("unknown") is False


@patch("src.usdm4.bc.cdisc.library.LibraryAPI")
@patch("src.usdm4.bc.cdisc.library.LibraryCache")
def test_catalogue_returns_top_level_keys(mock_cache_cls, mock_api_cls, tmp_path):
    """Covers Library.catalogue — line 34."""
    mock_cache = MagicMock()
    mock_cache.exists.return_value = True
    mock_cache.read.return_value = _sample_bcs()
    mock_cache_cls.return_value = mock_cache

    lib = Library(str(tmp_path), ct_library=MagicMock())
    lib.load()

    assert sorted(lib.catalogue()) == ["HEIGHT", "WEIGHT"]


@patch("src.usdm4.bc.cdisc.library.LibraryAPI")
@patch("src.usdm4.bc.cdisc.library.LibraryCache")
def test_usdm_returns_bc_dict_for_known_and_none_for_unknown(
    mock_cache_cls, mock_api_cls, tmp_path
):
    mock_cache = MagicMock()
    mock_cache.exists.return_value = True
    mock_cache.read.return_value = _sample_bcs()
    mock_cache_cls.return_value = mock_cache

    lib = Library(str(tmp_path), ct_library=MagicMock())
    lib.load()

    assert lib.usdm("Height") == _sample_bcs()["HEIGHT"]
    assert lib.usdm("Unknown") is None
