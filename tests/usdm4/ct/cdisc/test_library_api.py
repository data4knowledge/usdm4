"""Mock-heavy tests for the CDISC CT LibraryAPI.

All ``requests.get`` calls are patched to return fake responses so no
network is hit. Each LibraryAPI method is exercised both on the happy
path and on the 200-vs-non-200/error branches.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.usdm4.ct.cdisc.library_api import LibraryAPI


def _make_response(status_code: int, body):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    return resp


@pytest.fixture
def api():
    return LibraryAPI(packages=["sdtmct", "adamct"])


def test_url_prepends_api_root(api):
    assert api._url("/foo") == f"{LibraryAPI.API_ROOT}/foo"


def test_extract_ct_name_matches_trailing_date(api):
    assert api._extract_ct_name("/mdr/ct/packages/sdtmct-2024-01-01") == "sdtmct"


def test_extract_ct_name_returns_none_for_no_match(api):
    assert api._extract_ct_name("/no-date-here") is None


def test_extract_effective_date_matches(api):
    assert api._extract_effective_date("Package Effective 2024-01-01") == "2024-01-01"


def test_extract_effective_date_returns_none(api):
    assert api._extract_effective_date("No date in this title") is None


def test_package_version_returns_latest(api):
    api._packages = {
        "sdtmct": [
            {"effective": "2023-01-01", "url": "/a"},
            {"effective": "2024-01-01", "url": "/b"},
        ]
    }
    assert api._package_version("sdtmct") == "2024-01-01"


def test_package_version_returns_none_when_missing(api):
    api._packages = {}
    assert api._package_version("missing") is None


def test_package_version_returns_none_when_packages_uninitialised(api):
    # _packages starts as None
    assert api._package_version("sdtmct") is None


# ---------------------------------------------------------------------------
# _get_packages / refresh
# ---------------------------------------------------------------------------


def test_get_packages_parses_response(api):
    body = {
        "_links": {
            "packages": [
                {
                    "href": "/mdr/ct/packages/sdtmct-2024-01-01",
                    "title": "SDTM CT Package Effective 2024-01-01",
                },
                {
                    "href": "/mdr/ct/packages/sdtmct-2023-01-01",
                    "title": "SDTM CT Package Effective 2023-01-01",
                },
                # malformed entry — should be skipped
                {"href": "/bogus", "title": "No date"},
            ]
        }
    }
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(200, body),
    ):
        result = api._get_packages()
    assert "sdtmct" in result
    assert len(result["sdtmct"]) == 2


def test_get_packages_returns_none_on_non_200(api):
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(500, {}),
    ):
        assert api._get_packages() is None


def test_refresh_populates_packages(api):
    body = {
        "_links": {
            "packages": [
                {
                    "href": "/mdr/ct/packages/sdtmct-2024-01-01",
                    "title": "x Effective 2024-01-01",
                }
            ]
        }
    }
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(200, body),
    ):
        api.refresh()
    assert api._packages is not None
    assert "sdtmct" in api._packages


# ---------------------------------------------------------------------------
# code_list — the happy path and the "nothing found" branch
# ---------------------------------------------------------------------------


def test_code_list_returns_none_when_no_version(api):
    # _packages is empty -> _package_version returns None for all packages
    api._packages = {}
    assert api.code_list("C1") is None


def test_code_list_returns_matching_response(api):
    api._packages = {
        "sdtmct": [{"effective": "2024-01-01", "url": "/x"}],
    }

    body = {
        "_links": {"self": {"href": "/foo"}},
        "conceptId": "C1",
        "terms": [],
    }
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(200, body),
    ):
        result = api.code_list("C1")

    assert result is not None
    assert result["conceptId"] == "C1"
    # _links stripped, source added
    assert "_links" not in result
    assert result["source"] == {"effective_date": "2024-01-01", "package": "sdtmct"}


def test_code_list_falls_through_on_non_200(api):
    api._packages = {
        "sdtmct": [{"effective": "2024-01-01", "url": "/x"}],
        "adamct": [{"effective": "2024-01-01", "url": "/y"}],
    }

    # first 404 (sdtmct), second 404 (adamct) -> returns None
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(404, {}),
    ):
        assert api.code_list("C1") is None


# ---------------------------------------------------------------------------
# all_code_lists
# ---------------------------------------------------------------------------


def test_all_code_lists_returns_results(api):
    api._packages = {
        "sdtmct": [{"effective": "2024-01-01", "url": "/x"}],
    }

    body = {
        "_links": {
            "codelists": [
                {"href": "/mdr/ct/packages/sdtmct-2024-01-01/codelists/C1"},
                {"href": "/mdr/ct/packages/sdtmct-2024-01-01/codelists/C2"},
            ]
        }
    }
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(200, body),
    ):
        result = api.all_code_lists()

    assert len(result) == 1
    assert result[0]["effective_date"] == "2024-01-01"
    assert result[0]["package"] == "sdtmct"
    assert result[0]["code_lists"] == ["C1", "C2"]


def test_all_code_lists_skips_non_200(api):
    api._packages = {
        "sdtmct": [{"effective": "2024-01-01", "url": "/x"}],
    }
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(500, {}),
    ):
        result = api.all_code_lists()
    assert result == []


def test_all_code_lists_skips_packages_without_version(api):
    # _packages lacks sdtmct entry, _package_version returns None
    api._packages = {}
    result = api.all_code_lists()
    assert result == []


# ---------------------------------------------------------------------------
# package_code_list
# ---------------------------------------------------------------------------


def test_package_code_list_returns_payload_on_200(api):
    body = {
        "_links": {"self": {"href": "/foo"}},
        "conceptId": "C1",
    }
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(200, body),
    ):
        result = api.package_code_list("sdtmct", "2024-01-01", "C1")
    assert result["conceptId"] == "C1"
    assert result["source"] == {"effective_date": "2024-01-01", "package": "sdtmct"}
    assert "_links" not in result


def test_package_code_list_returns_none_on_non_200(api):
    with patch(
        "src.usdm4.ct.cdisc.library_api.requests.get",
        return_value=_make_response(404, {}),
    ):
        assert api.package_code_list("sdtmct", "2024-01-01", "C1") is None
