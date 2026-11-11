"""The packaged EDQM dose forms (GitHub 104)."""

from usdm4.ct.edqm import library


def test_dose_form_found_ignoring_case_and_spaces():
    form = library.dose_form("  Solution  FOR injection ")
    assert form == {
        "code": "11201000",
        "term": "Solution for injection",
        "ncit": "C42945",
    }


def test_unknown_and_empty():
    assert library.dose_form("Sterile Solution") is None
    assert library.dose_form("") is None
    assert library.dose_form(None) is None


def test_code_system_version_and_attribution():
    assert library.code_system() == "http://standardterms.edqm.eu"
    assert library.version() == "2026-11-11"
    assert "Council of Europe (EDQM)" in library._load()["attribution"]
