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

from src.usdm4.ct.cdisc.library import ConfigurationError, Library


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
# _add_missing_ct — dispatch on shape + per-file invariant
# ---------------------------------------------------------------------------


def _extension_entry(target="C66737", source="NCIt-M11", terms=None):
    """Helper — produce an `extends:` entry as it would appear in missing_ct.yaml."""
    return {
        "extends": target,
        "source": source,
        "terms": terms or [
            {
                "conceptId": "C999001",
                "preferredTerm": "Extension Term",
                "definition": "An added term",
                "submissionValue": "",
                "synonyms": [],
            }
        ],
    }


def _whole_codelist_entry(codelist="C217045", source="NCIt-M11", terms=None):
    """Helper — produce a `codelist:` entry as it would appear in m11_codelists.yaml."""
    return {
        "codelist": codelist,
        "source": source,
        "preferredTerm": "Whole Codelist",
        "definition": "A whole codelist",
        "extensible": False,
        "submissionValue": "",
        "synonyms": [],
        "terms": terms or [
            {
                "conceptId": "C999100",
                "preferredTerm": "Whole Term",
                "definition": "A term in the whole codelist",
                "submissionValue": "",
                "synonyms": [],
            }
        ],
    }


def test_add_missing_ct_routes_extends_to_merge(loaded_library):
    """An entry tagged 'missing_ct.yaml' with extends: triggers _merge_extension."""
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "true",
    }
    loaded_library._missing.code_lists = MagicMock(
        return_value=[(_extension_entry("C66737"), "missing_ct.yaml")]
    )
    loaded_library._add_missing_ct()
    assert "C999001" in loaded_library._by_term


def test_add_missing_ct_routes_codelist_to_whole(loaded_library):
    """An entry tagged 'm11_codelists.yaml' with codelist: triggers _add_whole_codelist."""
    loaded_library._missing.code_lists = MagicMock(
        return_value=[(_whole_codelist_entry("C217045"), "m11_codelists.yaml")]
    )
    loaded_library._add_missing_ct()
    assert "C217045" in loaded_library._by_code_list
    assert "C999100" in loaded_library._by_term


def test_add_missing_ct_rejects_codelist_in_missing_ct_file(loaded_library):
    """codelist: shape is not allowed in missing_ct.yaml."""
    loaded_library._missing.code_lists = MagicMock(
        return_value=[(_whole_codelist_entry("C217045"), "missing_ct.yaml")]
    )
    with pytest.raises(ConfigurationError, match="missing_ct.yaml"):
        loaded_library._add_missing_ct()


def test_add_missing_ct_rejects_extends_in_m11_file(loaded_library):
    """extends: shape is not allowed in m11_codelists.yaml."""
    loaded_library._missing.code_lists = MagicMock(
        return_value=[(_extension_entry("C66737"), "m11_codelists.yaml")]
    )
    with pytest.raises(ConfigurationError, match="m11_codelists.yaml"):
        loaded_library._add_missing_ct()


def test_add_missing_ct_rejects_entry_with_both_discriminators(loaded_library):
    """An entry must have exactly one of extends: or codelist:."""
    both = {"extends": "C66737", "codelist": "C217045", "terms": []}
    loaded_library._missing.code_lists = MagicMock(
        return_value=[(both, "missing_ct.yaml")]
    )
    with pytest.raises(ConfigurationError):
        loaded_library._add_missing_ct()


def test_add_missing_ct_rejects_unknown_source_file(loaded_library):
    """Defensive check — Missing should never yield an unknown source name."""
    loaded_library._missing.code_lists = MagicMock(
        return_value=[(_extension_entry("C66737"), "unexpected.yaml")]
    )
    with pytest.raises(ConfigurationError, match="Unknown missing-CT source file"):
        loaded_library._add_missing_ct()


# ---------------------------------------------------------------------------
# _merge_extension
# ---------------------------------------------------------------------------


def test_merge_extension_appends_term_to_target_codelist(loaded_library):
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "true",
    }
    loaded_library._merge_extension(_extension_entry("C66737"))
    target_terms = loaded_library._by_code_list["C66737"]["terms"]
    assert any(t["conceptId"] == "C999001" for t in target_terms)


def test_merge_extension_stamps_source_tag(loaded_library):
    """Each merged-in term carries the entry's source tag."""
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "true",
    }
    loaded_library._merge_extension(_extension_entry("C66737", source="NCIt-M11"))
    new_term = next(
        t for t in loaded_library._by_code_list["C66737"]["terms"]
        if t["conceptId"] == "C999001"
    )
    assert new_term["source"] == "NCIt-M11"


def test_merge_extension_defaults_source_when_missing(loaded_library):
    """If the entry has no source tag, the loader stamps 'extension'."""
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "true",
    }
    entry = _extension_entry("C66737")
    del entry["source"]
    loaded_library._merge_extension(entry)
    new_term = next(
        t for t in loaded_library._by_code_list["C66737"]["terms"]
        if t["conceptId"] == "C999001"
    )
    assert new_term["source"] == "extension"


def test_merge_extension_indexes_new_terms(loaded_library):
    """New terms appear in _by_term, _by_submission, _by_pt indexes."""
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "true",
    }
    loaded_library._merge_extension(
        _extension_entry(
            "C66737",
            terms=[{
                "conceptId": "C999001",
                "preferredTerm": "Extension Term",
                "submissionValue": "EXT_TERM",
            }],
        )
    )
    assert "C999001" in loaded_library._by_term
    assert "EXT_TERM" in loaded_library._by_submission
    assert "Extension Term" in loaded_library._by_pt


def test_merge_extension_raises_when_target_not_loaded(loaded_library):
    loaded_library._by_code_list.pop("C66737", None)
    with pytest.raises(ConfigurationError, match="not loaded"):
        loaded_library._merge_extension(_extension_entry("C66737"))


def test_merge_extension_raises_when_target_not_extensible(loaded_library):
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "false",
    }
    with pytest.raises(ConfigurationError, match="non-extensible"):
        loaded_library._merge_extension(_extension_entry("C66737"))


def test_merge_extension_accepts_extensible_true_as_bool(loaded_library):
    """The extensible flag may be a bool True (CDISC API) or 'true' string (YAML)."""
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": True,
    }
    # Should not raise.
    loaded_library._merge_extension(_extension_entry("C66737"))


# ---------------------------------------------------------------------------
# _add_whole_codelist
# ---------------------------------------------------------------------------


def test_add_whole_codelist_creates_entry(loaded_library):
    loaded_library._add_whole_codelist(_whole_codelist_entry("C217045"))
    assert "C217045" in loaded_library._by_code_list
    assert loaded_library._by_code_list["C217045"]["conceptId"] == "C217045"


def test_add_whole_codelist_stamps_source_on_terms(loaded_library):
    loaded_library._add_whole_codelist(
        _whole_codelist_entry("C217045", source="NCIt-M11")
    )
    terms = loaded_library._by_code_list["C217045"]["terms"]
    assert all(t["source"] == "NCIt-M11" for t in terms)


def test_add_whole_codelist_indexes_terms(loaded_library):
    loaded_library._add_whole_codelist(
        _whole_codelist_entry(
            "C217045",
            terms=[{
                "conceptId": "C15600",
                "preferredTerm": "Phase 1",
                "submissionValue": "",
            }],
        )
    )
    assert "C15600" in loaded_library._by_term
    assert "Phase 1" in loaded_library._by_pt


def test_add_whole_codelist_raises_on_duplicate_id(loaded_library):
    """If conceptId is already loaded, raise — use extends: to add terms."""
    loaded_library._by_code_list["C217045"] = _sample_code_list("C217045")
    with pytest.raises(ConfigurationError, match="already loaded"):
        loaded_library._add_whole_codelist(_whole_codelist_entry("C217045"))


def test_add_whole_codelist_preserves_extensible_flag(loaded_library):
    """The extensible flag on the new codelist is preserved as-given."""
    entry = _whole_codelist_entry("C217045")
    entry["extensible"] = True
    loaded_library._add_whole_codelist(entry)
    assert loaded_library._by_code_list["C217045"]["extensible"] is True


# ---------------------------------------------------------------------------
# has_codelist — companion to is_in_codelist for cache-stale detection
# ---------------------------------------------------------------------------


def test_has_codelist_true_when_loaded(loaded_library):
    assert loaded_library.has_codelist("C1") is True


def test_has_codelist_false_when_absent(loaded_library):
    assert loaded_library.has_codelist("C_DOES_NOT_EXIST") is False


def test_has_codelist_true_after_whole_codelist_added(loaded_library):
    loaded_library._add_whole_codelist(_whole_codelist_entry("C217045"))
    assert loaded_library.has_codelist("C217045") is True


# ---------------------------------------------------------------------------
# is_in_codelist / find_in_codelist — common membership predicate
# ---------------------------------------------------------------------------


def test_is_in_codelist_matches_by_concept_id(loaded_library):
    assert loaded_library.is_in_codelist("T1", "C1", by="concept_id") is True


def test_is_in_codelist_matches_by_preferred_term_case_insensitive(loaded_library):
    assert loaded_library.is_in_codelist("term a", "C1", by="preferred_term") is True
    assert loaded_library.is_in_codelist("TERM A", "C1", by="preferred_term") is True


def test_is_in_codelist_matches_by_submission_value_case_insensitive(loaded_library):
    assert loaded_library.is_in_codelist("term_a", "C1", by="submission_value") is True
    assert loaded_library.is_in_codelist("TERM_A", "C1", by="submission_value") is True


def test_is_in_codelist_any_mode_tries_all_three(loaded_library):
    assert loaded_library.is_in_codelist("T1", "C1", by="any") is True
    assert loaded_library.is_in_codelist("Term A", "C1", by="any") is True
    assert loaded_library.is_in_codelist("TERM_A", "C1", by="any") is True


def test_is_in_codelist_returns_false_on_miss(loaded_library):
    assert loaded_library.is_in_codelist("Nope", "C1", by="any") is False


def test_is_in_codelist_returns_false_when_codelist_unknown(loaded_library):
    assert loaded_library.is_in_codelist("T1", "C_DOES_NOT_EXIST", by="any") is False


def test_is_in_codelist_concept_id_is_case_sensitive(loaded_library):
    """NCI conceptIds are uppercase; lowercase should not match."""
    assert loaded_library.is_in_codelist("t1", "C1", by="concept_id") is False


def test_is_in_codelist_by_concept_id_does_not_match_pt(loaded_library):
    """Specifying by='concept_id' shouldn't fall through to PT/SV matches."""
    assert loaded_library.is_in_codelist("Term A", "C1", by="concept_id") is False


def test_find_in_codelist_returns_cdisc_source_for_loaded_terms(loaded_library):
    term, source = loaded_library.find_in_codelist("T1", "C1", by="concept_id")
    assert term["conceptId"] == "T1"
    assert source == "cdisc"


def test_find_in_codelist_returns_extension_source_after_merge(loaded_library):
    """A term added via _merge_extension is returned with its source tag."""
    loaded_library._by_code_list["C66737"] = {
        **_sample_code_list("C66737"),
        "extensible": "true",
    }
    loaded_library._merge_extension(
        _extension_entry("C66737", source="NCIt-M11")
    )
    term, source = loaded_library.find_in_codelist("C999001", "C66737", by="concept_id")
    assert term["conceptId"] == "C999001"
    assert source == "NCIt-M11"


def test_find_in_codelist_returns_extension_source_for_whole_codelist(loaded_library):
    """A term in a whole codelist added via _add_whole_codelist carries the source tag."""
    loaded_library._add_whole_codelist(
        _whole_codelist_entry("C217045", source="NCIt-M11")
    )
    term, source = loaded_library.find_in_codelist("C999100", "C217045", by="concept_id")
    assert term["conceptId"] == "C999100"
    assert source == "NCIt-M11"


def test_find_in_codelist_miss_returns_none_pair(loaded_library):
    term, source = loaded_library.find_in_codelist("Nope", "C1", by="any")
    assert term is None and source is None


def test_find_in_codelist_unknown_codelist_returns_none_pair(loaded_library):
    term, source = loaded_library.find_in_codelist("T1", "C_NONE", by="any")
    assert term is None and source is None


def test_find_in_codelist_handles_none_value(loaded_library):
    """Defensive: a None or empty value should be a clean miss, not a crash."""
    assert loaded_library.find_in_codelist(None, "C1", by="any") == (None, None)
    assert loaded_library.find_in_codelist("", "C1", by="any") == (None, None)


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
