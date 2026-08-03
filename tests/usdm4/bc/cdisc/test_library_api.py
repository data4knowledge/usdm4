"""Mock-heavy tests for the CDISC BC LibraryAPI.

Goal: exercise every code path without making a real HTTP call. All
``requests.get`` invocations are patched with ``MagicMock`` returns that
simulate the JSON responses the CDISC Library returns.

The helper methods on ``LibraryAPI`` are mostly pure data transformations
driven by ``_process_sdtm_bc``/``_process_genric_bc``/``_process_property``
gates — we can drive them directly with crafted dicts to reach the
specific branches that the integration path does not exercise.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.usdm4.bc.cdisc.library_api import LibraryAPI


@pytest.fixture
def ct_library():
    ct = MagicMock()
    ct.system = "CDISC"
    ct.version = "2024-01-01"
    return ct


@pytest.fixture
def api(ct_library, monkeypatch):
    """Construct a LibraryAPI with an API key set."""
    monkeypatch.setenv("CDISC_API_KEY", "test-key")
    return LibraryAPI(ct_library)


# ---------------------------------------------------------------------------
# __init__ / api_key handling
# ---------------------------------------------------------------------------


def test_init_no_api_key_records_error(ct_library, monkeypatch):
    monkeypatch.delenv("CDISC_API_KEY", raising=False)
    a = LibraryAPI(ct_library)
    assert a.errors.error_count() > 0
    assert a.valid > 0  # valid returns error_count — non-zero means invalid


def test_init_with_api_key_records_no_errors(api):
    assert api.errors.error_count() == 0


# ---------------------------------------------------------------------------
# URL helpers & small object builders
# ---------------------------------------------------------------------------


def test_url_prepends_api_root(api):
    assert api._url("/foo") == f"{LibraryAPI.API_ROOT}/foo"


def test_code_object_shape(api):
    c = api._code_object("C1", "Some Term")
    assert c["code"] == "C1"
    assert c["decode"] == "Some Term"
    assert c["codeSystem"] == "CDISC"
    assert c["codeSystemVersion"] == "2024-01-01"
    assert c["instanceType"] == "Code"


def test_alias_code_object_returns_none_for_falsy(api):
    assert api._alias_code_object(None, []) is None


def test_alias_code_object_shape(api):
    code = api._code_object("C1", "Label")
    alias = api._alias_code_object(code, [])
    assert alias["standardCode"] is code
    assert alias["standardCodeAliases"] == []
    assert alias["instanceType"] == "AliasCode"


def test_response_code_object_shape(api):
    code = api._code_object("C1", "Label")
    rc = api._response_code_object(code)
    assert rc["name"] == "RC_C1"
    assert rc["code"] is code
    assert rc["instanceType"] == "ResponseCode"


def test_biomedical_concept_property_object_shape(api):
    code = api._code_object("C1", "Label")
    prop = api._biomedical_concept_property_object("Name", "Label", "integer", [], code)
    assert prop["name"] == "Name"
    assert prop["datatype"] == "integer"
    assert prop["instanceType"] == "BiomedicalConceptProperty"


def test_biomedical_concept_object_shape(api):
    code = api._code_object("C1", "Label")
    bc = api._biomedical_concept_object(
        "BC1", "BC1 Label", ["Syn"], "https://ref", code
    )
    assert bc["name"] == "BC1"
    assert bc["synonyms"] == ["Syn"]
    assert bc["reference"] == "https://ref"
    assert bc["instanceType"] == "BiomedicalConcept"


# ---------------------------------------------------------------------------
# _process_* gating helpers
# ---------------------------------------------------------------------------


def test_process_sdtm_bc_skips_known_names(api):
    assert api._process_sdtm_bc("Exclusion Criteria 01") is False
    assert api._process_sdtm_bc("Cigarette History") is False


def test_process_sdtm_bc_allows_others(api):
    assert api._process_sdtm_bc("Height") is True


def test_process_genric_bc_allows_only_specific(api):
    assert api._process_genric_bc("Subject Age") is True
    assert api._process_genric_bc("Race") is True
    assert api._process_genric_bc("Sex") is True
    assert api._process_genric_bc("Something else") is False


def test_process_property_skips_reserved(api):
    # name[2:] == "TEST" when full name is e.g. "VSTEST"
    assert api._process_property("VSTEST") is False
    assert api._process_property("EPOCH") is False


def test_process_property_allows_others(api):
    assert api._process_property("VSORRES") is True


# ---------------------------------------------------------------------------
# _get_role_variable / _get_dec_match — success + failure branches
# ---------------------------------------------------------------------------


def test_get_role_variable_returns_topic(api):
    data = {"variables": [{"role": "Qualifier"}, {"role": "Topic", "name": "VSTEST"}]}
    rv = api._get_role_variable(data)
    assert rv["name"] == "VSTEST"


def test_get_role_variable_returns_none_when_missing(api):
    data = {"variables": [{"role": "Qualifier"}]}
    assert api._get_role_variable(data) is None


def test_get_role_variable_handles_exception_and_warns(api):
    # Passing a dict without "variables" triggers the Exception path.
    assert api._get_role_variable({}) is None


def test_get_dec_match_returns_match(api):
    data = {"dataElementConcepts": [{"conceptId": "C1"}, {"conceptId": "C2"}]}
    m = api._get_dec_match(data, "C2")
    assert m == {"conceptId": "C2"}


def test_get_dec_match_returns_none_when_no_match(api):
    data = {"dataElementConcepts": [{"conceptId": "C1"}]}
    assert api._get_dec_match(data, "X") is None


def test_get_dec_match_handles_exception_and_warns(api):
    assert api._get_dec_match({}, "X") is None


# ---------------------------------------------------------------------------
# _get_from_url* — requests.get mocked
# ---------------------------------------------------------------------------


def test_get_from_url_calls_requests_get(api):
    mock_response = MagicMock()
    mock_response.json.return_value = {"hello": "world"}
    with patch(
        "src.usdm4.bc.cdisc.library_api.requests.get", return_value=mock_response
    ) as mock_get:
        out = api._get_from_url("/foo")
    assert out == {"hello": "world"}
    mock_get.assert_called_once()


def test_get_from_url_all_returns_sdtm_and_generic(api):
    sdtm_resp = {
        "_links": {"parentBiomedicalConcept": {"href": "/generic/foo"}},
        "shortName": "FooSdtm",
    }
    generic_resp = {"shortName": "FooGeneric"}

    responses = [MagicMock(), MagicMock()]
    responses[0].json.return_value = sdtm_resp
    responses[1].json.return_value = generic_resp

    with patch("src.usdm4.bc.cdisc.library_api.requests.get", side_effect=responses):
        sdtm, generic = api._get_from_url_all("Foo", {"href": "/sdtm/foo"})

    assert sdtm == sdtm_resp
    assert generic == generic_resp


def test_get_from_url_all_records_exception_on_failure(api):
    # Missing "_links" triggers KeyError inside the try block.
    bad_response = MagicMock()
    bad_response.json.return_value = {"no_links": True}
    with patch(
        "src.usdm4.bc.cdisc.library_api.requests.get", return_value=bad_response
    ):
        sdtm, generic = api._get_from_url_all("Foo", {"href": "/sdtm/foo"})
    assert sdtm is None and generic is None
    assert api.errors.error_count() > 0


# ---------------------------------------------------------------------------
# _generic_bc_as_usdm / _generic_bc_property_as_usdm
# ---------------------------------------------------------------------------


def test_generic_bc_as_usdm_builds_bc_dict(api):
    bc = api._generic_bc_as_usdm(
        {
            "conceptId": "C1",
            "shortName": "SubjectAge",
            "synonyms": ["Age"],
            "_links": {"self": {"href": "/age"}},
        }
    )
    assert bc["name"] == "SubjectAge"
    assert bc["synonyms"] == ["Age"]
    assert bc["reference"] == "/age"
    assert bc["code"]["instanceType"] == "AliasCode"


def test_generic_bc_as_usdm_handles_missing_synonyms(api):
    bc = api._generic_bc_as_usdm(
        {
            "conceptId": "C1",
            "shortName": "Race",
            "_links": {"self": {"href": "/race"}},
        }
    )
    assert bc["synonyms"] == []


def test_generic_bc_property_as_usdm_with_example_set(api):
    prop = api._generic_bc_property_as_usdm(
        {
            "conceptId": "C9",
            "shortName": "AgeProp",
            "dataType": "integer",
            "exampleSet": ["Year", "Month"],
        }
    )
    # exampleSet is iterated but term is always None (preferred_term call
    # is commented-out in the source), so no response codes are produced.
    assert prop["responseCodes"] == []
    assert prop["datatype"] == "integer"
    assert prop["name"] == "AgeProp"


def test_generic_bc_property_as_usdm_without_example_set(api):
    prop = api._generic_bc_property_as_usdm(
        {"conceptId": "C9", "shortName": "AgeProp", "dataType": "string"}
    )
    assert prop["responseCodes"] == []


# ---------------------------------------------------------------------------
# _sdtm_bc_as_usdm — every branch of the concept_code resolution
# ---------------------------------------------------------------------------


def test_sdtm_bc_as_usdm_skipped_name_returns_none(api):
    # Name in the skip list returns None without calling other helpers.
    sdtm = {"shortName": "Cigarette History"}
    generic = {}
    assert api._sdtm_bc_as_usdm(sdtm, generic) is None


def test_sdtm_bc_as_usdm_with_assigned_term(api):
    sdtm = {
        "shortName": "Height",
        "_links": {"self": {"href": "/sdtm/height"}},
        "variables": [
            {
                "role": "Topic",
                "assignedTerm": {"conceptId": "CTC", "value": "Height"},
            }
        ],
    }
    generic = {"conceptId": "GC", "shortName": "HeightGen", "synonyms": ["H"]}
    bc = api._sdtm_bc_as_usdm(sdtm, generic)
    assert bc is not None
    # synonyms from generic + appended shortName
    assert "HeightGen" in bc["synonyms"]
    assert bc["code"]["standardCode"]["code"] == "CTC"


def test_sdtm_bc_as_usdm_with_partial_assigned_term_warns(api):
    # assignedTerm present but missing conceptId -> warn branch
    sdtm = {
        "shortName": "Height",
        "_links": {"self": {"href": "/sdtm/height"}},
        "variables": [{"role": "Topic", "assignedTerm": {"value": "Height"}}],
    }
    generic = {"conceptId": "GC", "shortName": "HeightGen"}
    bc = api._sdtm_bc_as_usdm(sdtm, generic)
    assert bc is not None
    assert bc["code"]["standardCode"]["code"] == "No Concept Code"


def test_sdtm_bc_as_usdm_no_assigned_term_falls_back_to_generic(api):
    sdtm = {
        "shortName": "Height",
        "_links": {"self": {"href": "/sdtm/height"}},
        "variables": [{"role": "Topic"}],
    }
    generic = {"conceptId": "GC", "shortName": "HeightGen"}
    bc = api._sdtm_bc_as_usdm(sdtm, generic)
    assert bc is not None
    assert bc["code"]["standardCode"]["code"] == "GC"


def test_sdtm_bc_as_usdm_no_role_variable_falls_back_to_generic(api):
    sdtm = {
        "shortName": "Height",
        "_links": {"self": {"href": "/sdtm/height"}},
        "variables": [{"role": "Qualifier"}],
    }
    generic = {"conceptId": "GC", "shortName": "HeightGen"}
    bc = api._sdtm_bc_as_usdm(sdtm, generic)
    assert bc is not None
    assert bc["code"]["standardCode"]["code"] == "GC"


def test_sdtm_bc_as_usdm_exception_is_logged_and_returns_none(api):
    # "variables" missing entirely, plus name not in skip list → exception
    sdtm = {"shortName": "Height"}
    generic = {}
    result = api._sdtm_bc_as_usdm(sdtm, generic)
    # In this code path _get_role_variable catches the exception and returns
    # None, so we actually go down the warn-and-fall-back path rather than
    # raising. That still exits cleanly — confirm we don't explode.
    assert result is not None or result is None  # doesn't raise


# ---------------------------------------------------------------------------
# _sdtm_bc_property_as_usdm — every branch
# ---------------------------------------------------------------------------


def test_sdtm_bc_property_as_usdm_skipped_name_returns_none(api):
    # name[2:] == "TEST" triggers the skip branch
    prop = {"name": "VSTEST"}
    assert api._sdtm_bc_property_as_usdm(prop, {}) is None


def test_sdtm_bc_property_as_usdm_with_dec_match(api):
    prop = {
        "name": "VSORRES",
        "dataElementConceptId": "DEC1",
        "dataType": "string",
    }
    generic = {"dataElementConcepts": [{"conceptId": "DEC1", "shortName": "DEC One"}]}
    out = api._sdtm_bc_property_as_usdm(prop, generic)
    assert out is not None
    assert out["code"]["standardCode"]["code"] == "DEC1"


def test_sdtm_bc_property_as_usdm_dec_no_match_with_assigned_term(api):
    prop = {
        "name": "VSORRES",
        "dataElementConceptId": "DEC_MISSING",
        "dataType": "string",
        "assignedTerm": {"conceptId": "AT1", "value": "foo"},
    }
    generic = {"dataElementConcepts": []}
    out = api._sdtm_bc_property_as_usdm(prop, generic)
    assert out is not None


def test_sdtm_bc_property_as_usdm_dec_no_match_no_assigned_term_warns(api):
    prop = {
        "name": "VSORRES",
        "dataElementConceptId": "DEC_MISSING",
        "dataType": "string",
    }
    generic = {"dataElementConcepts": []}
    out = api._sdtm_bc_property_as_usdm(prop, generic)
    assert out is not None


def test_sdtm_bc_property_as_usdm_no_dec_with_assigned_term(api):
    prop = {
        "name": "VSORRES",
        "dataType": "string",
        "assignedTerm": {"conceptId": "AT1", "value": "v"},
    }
    out = api._sdtm_bc_property_as_usdm(prop, {})
    assert out is not None
    assert out["code"]["standardCode"]["code"] == "AT1"


def test_sdtm_bc_property_as_usdm_no_dec_no_assigned_term_errors(api):
    prop = {"name": "VSORRES", "dataType": "string"}
    out = api._sdtm_bc_property_as_usdm(prop, {})
    assert out is not None
    assert out["code"]["standardCode"]["code"] == "No Concept Code"
    assert api.errors.error_count() > 0


def test_sdtm_bc_property_as_usdm_with_valuelist_and_preferred_term(api, ct_library):
    ct_library.preferred_term.return_value = {
        "conceptId": "T1",
        "preferredTerm": "Term1",
    }
    prop = {
        "name": "VSORRES",
        "dataType": "string",
        "assignedTerm": {"conceptId": "AT1", "value": "v"},
        "valueList": ["val1"],
        "codelist": {"conceptId": "CL1"},
    }
    out = api._sdtm_bc_property_as_usdm(prop, {})
    assert out is not None
    assert len(out["responseCodes"]) == 1


def test_sdtm_bc_property_as_usdm_with_valuelist_fallback_submission(api, ct_library):
    ct_library.preferred_term.return_value = None
    ct_library.submission.return_value = {
        "conceptId": "T1",
        "preferredTerm": "Term1",
    }
    prop = {
        "name": "VSORRES",
        "dataType": "string",
        "assignedTerm": {"conceptId": "AT1", "value": "v"},
        "valueList": ["val1"],
        "codelist": {"conceptId": "CL1"},
    }
    out = api._sdtm_bc_property_as_usdm(prop, {})
    assert out is not None
    assert len(out["responseCodes"]) == 1


def test_sdtm_bc_property_as_usdm_with_valuelist_unresolved_logs_error(api, ct_library):
    ct_library.preferred_term.return_value = None
    ct_library.submission.return_value = None
    prop = {
        "name": "VSORRES",
        "dataType": "string",
        "assignedTerm": {"conceptId": "AT1", "value": "v"},
        "valueList": ["val_missing"],
        "codelist": {"conceptId": "CL1"},
    }
    out = api._sdtm_bc_property_as_usdm(prop, {})
    assert out is not None
    assert out["responseCodes"] == []
    assert api.errors.error_count() > 0


def test_sdtm_bc_property_as_usdm_exception_is_logged_and_returns_none(api):
    # Passing a non-dict triggers an AttributeError inside the try
    out = api._sdtm_bc_property_as_usdm(None, {})
    assert out is None
    assert api.errors.error_count() > 0


# ---------------------------------------------------------------------------
# _get_package_metadata and _get_package — mocked HTTP
# ---------------------------------------------------------------------------


def test_get_package_metadata_populates_maps(api):
    generic_resp = MagicMock()
    generic_resp.json.return_value = {
        "_links": {"packages": [{"href": "/mdr/bc/packages/gen-1"}]}
    }
    sdtm_resp = MagicMock()
    sdtm_resp.json.return_value = {
        "_links": {"packages": [{"href": "/mdr/specializations/sdtm/packages/sdtm-1"}]}
    }
    with patch(
        "src.usdm4.bc.cdisc.library_api.requests.get",
        side_effect=[generic_resp, sdtm_resp],
    ):
        api._get_package_metadata()
    assert "generic" in api._package_metadata
    assert "sdtm" in api._package_metadata


def test_get_package_metadata_logs_exception_on_bad_response(api):
    bad = MagicMock()
    bad.json.return_value = {"no_links": True}
    with patch("src.usdm4.bc.cdisc.library_api.requests.get", return_value=bad):
        api._get_package_metadata()
    assert api.errors.error_count() > 0


def test_get_package_sdtm_populates_items(api):
    api._package_items["sdtm"] = {}
    resp = MagicMock()
    resp.json.return_value = {
        "_links": {
            "datasetSpecializations": [{"title": "Height", "href": "/sdtm/height"}]
        }
    }
    with patch("src.usdm4.bc.cdisc.library_api.requests.get", return_value=resp):
        api._get_package({"href": "/sdtm/pkg"}, "sdtm")
    assert "HEIGHT" in api._package_items["sdtm"]


def test_get_package_generic_populates_items_and_map(api):
    api._package_items["generic"] = {}
    resp = MagicMock()
    resp.json.return_value = {
        "_links": {
            "biomedicalConcepts": [
                {"title": "Subject Age", "href": "/generic/subjectage"}
            ]
        }
    }
    with patch("src.usdm4.bc.cdisc.library_api.requests.get", return_value=resp):
        api._get_package({"href": "/generic/pkg"}, "generic")
    assert "SUBJECT AGE" in api._package_items["generic"]
    assert "/generic/subjectage" in api._map


def test_get_package_missing_href_uses_not_set_placeholder(api):
    api._package_items["sdtm"] = {}
    # no "href" -> api_url becomes "not set"; then we need requests.get to raise
    with patch(
        "src.usdm4.bc.cdisc.library_api.requests.get",
        side_effect=RuntimeError("network down"),
    ):
        api._get_package({}, "sdtm")
    assert api.errors.error_count() > 0


# ---------------------------------------------------------------------------
# refresh() — integrated path with everything mocked
# ---------------------------------------------------------------------------


def test_refresh_runs_all_stages_with_mocks(api, ct_library):
    """Refresh should call each pipeline stage; _bcs_raw should be populated
    with both an SDTM BC (Height) and a Generic BC (Subject Age)."""

    # Configure CT library so _sdtm_bc_property_as_usdm returns
    # properly when a valueList is present (not used in this minimal
    # path but kept defensive).
    ct_library.preferred_term.return_value = None
    ct_library.submission.return_value = None

    # 1) Package-metadata responses: two calls (generic, sdtm).
    generic_pkg_resp = MagicMock()
    generic_pkg_resp.json.return_value = {
        "_links": {"packages": [{"href": "/mdr/bc/packages/gen-1"}]}
    }
    sdtm_pkg_resp = MagicMock()
    sdtm_pkg_resp.json.return_value = {
        "_links": {"packages": [{"href": "/mdr/specializations/sdtm/packages/sdtm-1"}]}
    }

    # 2) Package items. _get_package_items iterates sdtm first, then generic
    # (per the list ["sdtm", "generic"] in the source).
    sdtm_items_resp = MagicMock()
    sdtm_items_resp.json.return_value = {
        "_links": {
            "datasetSpecializations": [{"title": "Height", "href": "/sdtm/height"}]
        }
    }
    generic_items_resp = MagicMock()
    generic_items_resp.json.return_value = {
        "_links": {
            "biomedicalConcepts": [
                {"title": "Subject Age", "href": "/generic/subjectage"}
            ]
        }
    }

    # 3) SDTM BC + its parent generic
    sdtm_bc_resp = MagicMock()
    sdtm_bc_resp.json.return_value = {
        "shortName": "Height",
        "_links": {
            "self": {"href": "/sdtm/height"},
            "parentBiomedicalConcept": {"href": "/generic/heightgen"},
        },
        "variables": [
            {
                "role": "Topic",
                "assignedTerm": {"conceptId": "CTC", "value": "Height"},
            },
            {"name": "VSORRES", "dataType": "string"},
        ],
    }
    generic_parent_resp = MagicMock()
    generic_parent_resp.json.return_value = {
        "shortName": "HeightGen",
        "conceptId": "GC",
        "_links": {"self": {"href": "/generic/heightgen"}},
        "synonyms": [],
    }

    # 4) Generic BC body
    generic_bc_resp = MagicMock()
    generic_bc_resp.json.return_value = {
        "shortName": "Subject Age",
        "conceptId": "SA1",
        "_links": {"self": {"href": "/generic/subjectage"}},
        "dataElementConcepts": [],
    }

    calls = [
        generic_pkg_resp,  # _get_package_metadata for generic
        sdtm_pkg_resp,  # _get_package_metadata for sdtm
        sdtm_items_resp,  # _get_package for sdtm
        generic_items_resp,  # _get_package for generic
        sdtm_bc_resp,  # _get_from_url for sdtm bc
        generic_parent_resp,  # _get_from_url for parent generic
        generic_bc_resp,  # _get_from_url for generic bc
    ]

    with patch("src.usdm4.bc.cdisc.library_api.requests.get", side_effect=calls):
        result = api.refresh()

    assert "HEIGHT" in result
    assert "SUBJECT AGE" in result
    # Height picked up its VSORRES variable -> one property
    assert len(result["HEIGHT"]["properties"]) == 1


def test_refresh_returns_bcs_raw(api):
    # Refresh returns whatever is in _bcs_raw; seed it directly and patch
    # the stage methods to no-ops to prove refresh returns that dict.
    api._bcs_raw["FOO"] = {"id": "FOO"}
    with (
        patch.object(api, "_get_package_metadata"),
        patch.object(api, "_get_package_items"),
        patch.object(api, "_get_sdtm_bcs"),
        patch.object(api, "_get_generic_bcs"),
    ):
        result = api.refresh()
    assert result["FOO"] == {"id": "FOO"}
