"""Mock-heavy tests for the CDISC CT Library loader.

The loader wires together Config, Missing, LibraryAPI, and LibraryCache.
These tests mock LibraryAPI + LibraryCache at the import site to keep
everything local — the Config and Missing loaders do read YAML from disk
but that's cheap and hermetic.
"""

from unittest.mock import MagicMock, patch

import os
import pathlib

import pytest

from src.usdm4.ct.cdisc.library import Library


ROOT = os.path.join(
    pathlib.Path(__file__).parent.parent.parent.parent.parent.resolve(),
    "src",
    "usdm4",
)


def _sample_code_list(concept_id="C1", source_date="2024-01-01"):
    return {
        "conceptId": concept_id,
        "source": {"effective_date": source_date},
        "terms": [
            {
                "conceptId": "T1",
                "submissionValue": "TERM_A",
                "preferredTerm": "Term A",
            },
            {
                "conceptId": "T2",
                "submissionValue": "TERM_B",
                "preferredTerm": "Term B",
            },
        ],
    }


# ---------------------------------------------------------------------------
# __init__ / basic init paths
# ---------------------------------------------------------------------------


def test_init_default_type_is_usdm():
    lib = Library(ROOT)
    assert lib._type == Library.USDM


def test_init_explicit_all_type():
    lib = Library(ROOT, type="all")
    assert lib._type == Library.ALL


def test_init_unknown_type_falls_back_to_usdm():
    lib = Library(ROOT, type="something-unknown")
    assert lib._type == Library.USDM


def test_init_sets_default_system_and_version():
    lib = Library(ROOT)
    assert lib.system == "http://www.cdisc.org"
    assert lib.version == "2023-12-15"


# ---------------------------------------------------------------------------
# load() — cache hit and cache miss
# ---------------------------------------------------------------------------


@patch("src.usdm4.ct.cdisc.library.LibraryCache")
@patch("src.usdm4.ct.cdisc.library.LibraryAPI")
def test_load_cache_hit_uses_cache(mock_api_cls, mock_cache_cls):
    lib = Library(ROOT)
    lib._cache.exists = MagicMock(return_value=True)
    lib._cache.read = MagicMock(return_value={"C1": _sample_code_list("C1")})
    # missing loader returns nothing extra
    lib._missing.code_lists = MagicMock(return_value=[])

    lib.load()

    assert "C1" in lib._by_code_list
    assert "T1" in lib._by_term
    lib._cache.read.assert_called_once()


@patch("src.usdm4.ct.cdisc.library.LibraryCache")
@patch("src.usdm4.ct.cdisc.library.LibraryAPI")
def test_load_cache_miss_calls_api_and_saves(mock_api_cls, mock_cache_cls):
    lib = Library(ROOT)
    lib._cache.exists = MagicMock(return_value=False)
    lib._cache.save = MagicMock()
    lib._missing.code_lists = MagicMock(return_value=[])

    # Stub _get_usdm_ct to populate _by_code_list without hitting the API
    def fake_get_usdm_ct():
        lib._by_code_list["C1"] = _sample_code_list("C1")

    lib._get_usdm_ct = fake_get_usdm_ct
    lib._api.refresh = MagicMock()

    lib.load()

    lib._api.refresh.assert_called_once()
    lib._cache.save.assert_called_once_with(lib._by_code_list)


@patch("src.usdm4.ct.cdisc.library.LibraryCache")
@patch("src.usdm4.ct.cdisc.library.LibraryAPI")
def test_load_cache_miss_all_type_uses_get_all_ct(mock_api_cls, mock_cache_cls):
    lib = Library(ROOT, type="all")
    lib._cache.exists = MagicMock(return_value=False)
    lib._cache.save = MagicMock()
    lib._missing.code_lists = MagicMock(return_value=[])

    def fake_get_all_ct():
        lib._by_code_list["CX"] = _sample_code_list("CX")

    lib._get_all_ct = fake_get_all_ct
    lib._api.refresh = MagicMock()

    lib.load()

    assert "CX" in lib._by_code_list


# ---------------------------------------------------------------------------
# klass_and_attribute / klass_and_attribute_value
# ---------------------------------------------------------------------------


@pytest.fixture
def loaded_library():
    lib = Library(ROOT)
    lib._by_code_list = {"C1": _sample_code_list("C1")}
    # rebuild term indexes
    for term in lib._by_code_list["C1"]["terms"]:
        lib._by_term.setdefault(term["conceptId"], []).append("C1")
        lib._by_submission.setdefault(term["submissionValue"], []).append("C1")
        lib._by_pt.setdefault(term["preferredTerm"], []).append("C1")
    return lib


def test_klass_and_attribute_returns_codelist(loaded_library):
    loaded_library._config.klass_and_attribute = MagicMock(return_value="C1")
    cl = loaded_library.klass_and_attribute("Klass", "attr")
    assert cl["conceptId"] == "C1"


def test_klass_and_attribute_returns_none_on_lookup_failure(loaded_library):
    loaded_library._config.klass_and_attribute = MagicMock(side_effect=ValueError("x"))
    assert loaded_library.klass_and_attribute("Klass", "attr") is None


def test_klass_and_attribute_value_returns_item_and_date(loaded_library):
    loaded_library._config.klass_and_attribute = MagicMock(return_value="C1")
    item, date = loaded_library.klass_and_attribute_value("Klass", "attr", "TERM_A")
    assert item["conceptId"] == "T1"
    assert date == "2024-01-01"


def test_klass_and_attribute_value_returns_none_pair_on_failure(loaded_library):
    loaded_library._config.klass_and_attribute = MagicMock(side_effect=ValueError("x"))
    item, date = loaded_library.klass_and_attribute_value("K", "a", "v")
    assert item is None and date is None


# ---------------------------------------------------------------------------
# unit / unit_code_list / cl_by_term
# ---------------------------------------------------------------------------


def test_unit_uses_c71620_codelist(loaded_library):
    loaded_library._by_code_list["C71620"] = _sample_code_list("C71620")
    unit = loaded_library.unit("TERM_A")
    assert unit["conceptId"] == "T1"


def test_unit_returns_none_when_codelist_missing(loaded_library):
    # C71620 not in _by_code_list
    assert loaded_library.unit("TERM_A") is None


def test_unit_code_list_returns_c71620_list(loaded_library):
    loaded_library._by_code_list["C71620"] = _sample_code_list("C71620")
    cl = loaded_library.unit_code_list()
    assert cl["conceptId"] == "C71620"


def test_cl_by_term_returns_parent_list(loaded_library):
    cl = loaded_library.cl_by_term("T1")
    assert cl["conceptId"] == "C1"


def test_cl_by_term_returns_none_when_missing(loaded_library):
    assert loaded_library.cl_by_term("nonexistent") is None


# ---------------------------------------------------------------------------
# submission / preferred_term
# ---------------------------------------------------------------------------


def test_submission_returns_term(loaded_library):
    result = loaded_library.submission("TERM_A")
    assert result["conceptId"] == "T1"


def test_submission_returns_none_when_value_not_in_index(loaded_library):
    assert loaded_library.submission("NOT_PRESENT") is None


def test_preferred_term_returns_term(loaded_library):
    result = loaded_library.preferred_term("Term A")
    assert result["conceptId"] == "T1"


def test_preferred_term_returns_none_when_not_present(loaded_library):
    assert loaded_library.preferred_term("Not a term") is None


# ---------------------------------------------------------------------------
# _find_in_collection — all branches
# ---------------------------------------------------------------------------


def test_find_in_collection_empty_returns_none(loaded_library):
    assert loaded_library._find_in_collection([], "submissionValue", "TERM_A") is None


def test_find_in_collection_single_returns_match(loaded_library):
    result = loaded_library._find_in_collection(["C1"], "submissionValue", "TERM_A")
    assert result["conceptId"] == "T1"


def test_find_in_collection_single_returns_none_when_no_match(loaded_library):
    result = loaded_library._find_in_collection(["C1"], "submissionValue", "UNKNOWN")
    assert result is None


def test_find_in_collection_multi_with_cl_match(loaded_library):
    loaded_library._by_code_list["C2"] = _sample_code_list("C2")
    result = loaded_library._find_in_collection(
        ["C1", "C2"], "submissionValue", "TERM_A", cl="C2"
    )
    assert result["conceptId"] == "T1"


def test_find_in_collection_multi_without_cl_returns_none(loaded_library):
    loaded_library._by_code_list["C2"] = _sample_code_list("C2")
    result = loaded_library._find_in_collection(
        ["C1", "C2"], "submissionValue", "TERM_A"
    )
    assert result is None


# ---------------------------------------------------------------------------
# _get_item — iterates field candidates
# ---------------------------------------------------------------------------


def test_get_item_matches_by_submission_value(loaded_library):
    cl = _sample_code_list("C1")
    result = loaded_library._get_item(cl, "TERM_A")
    assert result["conceptId"] == "T1"


def test_get_item_matches_by_preferred_term(loaded_library):
    cl = _sample_code_list("C1")
    result = loaded_library._get_item(cl, "Term A")
    assert result["conceptId"] == "T1"


def test_get_item_returns_none_when_no_match(loaded_library):
    cl = _sample_code_list("C1")
    assert loaded_library._get_item(cl, "Nothing here") is None


def test_get_item_handles_exception(loaded_library):
    # Missing "terms" triggers KeyError -> returns None
    assert loaded_library._get_item({}, "anything") is None


# ---------------------------------------------------------------------------
# _get_usdm_ct / _get_all_ct — driven through a mock API
# ---------------------------------------------------------------------------


def test_get_usdm_ct_populates_indexes(loaded_library):
    loaded_library._by_code_list = {}
    loaded_library._by_term = {}
    loaded_library._by_submission = {}
    loaded_library._by_pt = {}

    loaded_library._config.required_code_lists = MagicMock(return_value=["C1"])
    loaded_library._api.code_list = MagicMock(return_value=_sample_code_list("C1"))

    loaded_library._get_usdm_ct()

    assert "C1" in loaded_library._by_code_list
    assert "T1" in loaded_library._by_term
    assert "TERM_A" in loaded_library._by_submission
    assert "Term A" in loaded_library._by_pt


def test_get_all_ct_populates_indexes(loaded_library):
    loaded_library._by_code_list = {}
    loaded_library._by_term = {}
    loaded_library._by_submission = {}
    loaded_library._by_pt = {}

    loaded_library._api.all_code_lists = MagicMock(
        return_value=[
            {
                "package": "sdtmct",
                "effective_date": "2024-01-01",
                "code_lists": ["C1"],
            }
        ]
    )
    loaded_library._api.package_code_list = MagicMock(
        return_value=_sample_code_list("C1")
    )

    loaded_library._get_all_ct()

    assert "C1" in loaded_library._by_code_list


# ---------------------------------------------------------------------------
# _add_missing_ct
# ---------------------------------------------------------------------------


def test_add_missing_ct_appends_lists(loaded_library):
    loaded_library._missing.code_lists = MagicMock(
        return_value=[_sample_code_list("EXTRA")]
    )
    loaded_library._add_missing_ct()
    assert "EXTRA" in loaded_library._by_code_list


# ---------------------------------------------------------------------------
# _check_in_and_add
# ---------------------------------------------------------------------------


def test_check_in_and_add_creates_list(loaded_library):
    coll = {}
    loaded_library._check_in_and_add(coll, "ID", "VAL")
    assert coll == {"ID": ["VAL"]}


def test_check_in_and_add_appends_to_existing(loaded_library):
    coll = {"ID": ["A"]}
    loaded_library._check_in_and_add(coll, "ID", "B")
    assert coll == {"ID": ["A", "B"]}
