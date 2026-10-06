"""Tests for tools/m11_ct.py — the M11 CT generator (GitHub 81).

Pure functions run against small in-memory rows shaped like the published
ICH M11 Terminology sheet. One test reads the real terminology file from the
sibling m11_specification repo and is skipped when it is absent.
"""

import yaml
import pytest

from tools import m11_ct


def _rows():
    # Code, Codelist Code, Extensible, Codelist Name, ICH PT, ICH Synonyms, ICH Definition, NCI PT
    return [
        ["C217045", "", "No", "Trial Phase Response Terminology", "Trial Phase Response Terminology",
         "Trial Phase Response Terminology", "Trial phase codelist.", "ICH M11 Trial Phase Value Set Terminology"],
        ["C15600", "C217045", "", "Trial Phase Response Terminology", "Phase 1", "", "Phase 1 def.", "Phase I Trial"],
        ["C217024", "C217045", "", "Trial Phase Response Terminology", "Phase 2/Phase 3/Phase 4", "",
         "Phase 2/3/4 def.", "Phase II/III/IV Trial"],
        ["C217272", "", "No", "Protocol Section Name and Number Response Terminology",
         "Protocol Section Name and Number Response Terminology", "A; B", "Section codelist.", "Section VS"],
        ["C218515", "C217272", "", "Protocol Section Name and Number Response Terminology",
         "1.1 Protocol Synopsis", "", "Section 1.1.", "ICH M11 Protocol Section 1.1 Protocol Synopsis"],
        ["C222769", "C217272", "", "Protocol Section Name and Number Response Terminology", "Title Page", "",
         "Title Page section.", "ICH M11 Protocol Section Title Page"],
        ["C217342", "", "No", "ICH M11 Section 1 Terminology", "ICH M11 Section 1 Terminology", "",
         "Section 1 data elements.", "ICH M11 Protocol Section 1 Data Element Terminology"],
        ["C49647", "C217342", "", "ICH M11 Section 1 Terminology", "Control Type", "", "Control type.", "Control Type"],
    ]


class TestIsResponseCodelist:
    def test_response(self):
        assert m11_ct.is_response_codelist("Trial Phase Response Terminology") is True
        assert m11_ct.is_response_codelist("Unit of Measure Terminology") is True

    def test_section_data_elements(self):
        assert m11_ct.is_response_codelist("ICH M11 Section 1 Terminology") is False
        assert m11_ct.is_response_codelist("ICH M11 Section Title Page Terminology") is False


class TestCollectCodelists:
    def test_response_codelists_only(self):
        codelists = m11_ct.collect_codelists(_rows(), "2025-12-19")
        assert list(codelists) == ["C217045", "C217272"]

    def test_members_in_file_order(self):
        codelists = m11_ct.collect_codelists(_rows())
        assert [t["conceptId"] for t in codelists["C217272"]["terms"]] == ["C218515", "C222769"]
        assert codelists["C217272"]["terms"][0]["preferredTerm"] == "1.1 Protocol Synopsis"

    def test_codelist_fields(self):
        entry = m11_ct.collect_codelists(_rows(), "2025-12-19")["C217272"]
        assert entry["source"] == "NCIt-M11"
        assert entry["effective_date"] == "2025-12-19"
        assert entry["extensible"] is False
        assert entry["synonyms"] == ["A", "B"]
        assert entry["definition"] == "Section codelist."

    def test_extensible_yes(self):
        rows = _rows()
        rows[0][2] = "Yes"
        assert m11_ct.collect_codelists(rows)["C217045"]["extensible"] is True

    def test_term_without_codelist_row_raises(self):
        rows = _rows() + [["C1", "C999", "", "X", "x", "", "", ""]]
        with pytest.raises(ValueError):
            m11_ct.collect_codelists(rows)

    def test_short_rows_padded(self):
        rows = [["C217046", "", "No", "No Yes Response Terminology", "No Yes"], ["C49488", "C217046", "", "N", "Yes"]]
        terms = m11_ct.collect_codelists(rows)["C217046"]["terms"]
        assert terms[0]["preferredTerm"] == "Yes"
        assert terms[0]["definition"] == ""


class TestComputeExtensions:
    def test_codes_missing_from_sdtm_use_nci_pt(self):
        codelists = m11_ct.collect_codelists(_rows())
        sdtm = {"C66737": {"terms": [{"conceptId": "C15600"}]}}
        extensions = m11_ct.compute_extensions(codelists, sdtm)
        assert extensions == [
            {
                "extends": "C66737",
                "source": "NCIt-M11",
                "terms": [
                    {
                        "conceptId": "C217024",
                        "preferredTerm": "Phase II/III/IV Trial",
                        "definition": "Phase 2/3/4 def.",
                        "submissionValue": "",
                        "synonyms": [],
                    }
                ],
            }
        ]

    def test_ich_pt_when_no_nci_pt(self):
        rows = _rows()
        rows[2][7] = ""
        extensions = m11_ct.compute_extensions(m11_ct.collect_codelists(rows), {"C66737": {"terms": []}})
        assert extensions[0]["terms"][-1]["preferredTerm"] == "Phase 2/Phase 3/Phase 4"

    def test_nothing_missing(self):
        codelists = m11_ct.collect_codelists(_rows())
        sdtm = {"C66737": {"terms": [{"conceptId": "C15600"}, {"conceptId": "C217024"}]}}
        assert m11_ct.compute_extensions(codelists, sdtm) == []

    def test_unknown_sdtm_codelist_skipped(self):
        assert m11_ct.compute_extensions(m11_ct.collect_codelists(_rows()), {}) == []


class TestRender:
    def test_codelists_yaml_drops_nci_pt(self):
        codelists = m11_ct.collect_codelists(_rows(), "2025-12-19")
        text = m11_ct.render_codelists(codelists, "terms.xls", "2025-12-19")
        assert text.startswith("# Whole ICH M11 response codelists")
        assert "release 2025-12-19" in text
        data = yaml.safe_load(text)
        assert [c["codelist"] for c in data] == ["C217045", "C217272"]
        assert all("nciPreferredTerm" not in t for c in data for t in c["terms"])

    def test_empty_outputs(self):
        assert m11_ct.render_codelists({}, "f.xls", "").endswith("[]\n")
        assert m11_ct.render_extensions([], "f.xls", "").endswith("[]\n")
        assert "release unknown" in m11_ct.render_extensions([], "f.xls", "")


class TestRun:
    def test_run_writes_both_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(m11_ct, "read_rows", lambda path: ("2025-12-19", _rows()))
        sdtm = tmp_path / "sdtm.yaml"
        sdtm.write_text(yaml.safe_dump({"C66737": {"terms": [{"conceptId": "C15600"}]}}))
        summary = m11_ct.run(tmp_path / "t.xls", sdtm, tmp_path)
        assert summary == {"release": "2025-12-19", "codelists": 2, "terms": 4, "extension_terms": 1}
        loaded = yaml.safe_load((tmp_path / "missing_ct.yaml").read_text())
        assert loaded[0]["extends"] == "C66737"
        assert (tmp_path / "m11_codelists.yaml").exists()

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(m11_ct, "read_rows", lambda path: ("", _rows()))
        sdtm = tmp_path / "sdtm.yaml"
        sdtm.write_text("{}")
        m11_ct.run(tmp_path / "t.xls", sdtm, tmp_path, dry_run=True)
        assert not (tmp_path / "m11_codelists.yaml").exists()


class TestRealTerminologyFile:
    def test_section_codelist_has_every_section(self):
        path = m11_ct.default_terminology_path()
        if path is None:
            pytest.skip("m11_specification terminology file not present")
        pytest.importorskip("xlrd")
        release, rows = m11_ct.read_rows(path)
        codelists = m11_ct.collect_codelists(rows, release)
        section = codelists["C217272"]["terms"]
        assert len(section) == 160
        assert section[0]["preferredTerm"] == "1 PROTOCOL SUMMARY"
        assert "C217342" not in codelists
