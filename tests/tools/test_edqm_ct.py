"""tools/edqm_ct.py — the EDQM dose form generator (GitHub 104), run on a
small workbook shaped like the NCI EVS EDQM-HealthCare file."""

import openpyxl
import yaml

from tools import edqm_ct

HEADER = (
    "NCIt Subset Code",
    "NCIt Subset Name",
    "NCIt Concept Code",
    "NCIt Preferred Term",
    "EDQM-HC Preferred Term",
    "EDQM-HC Source Code",
)
ROWS = [
    (
        "C150103",
        "PDF",
        "C91142",
        "Inhalant Powder Dosage Form",
        "Inhalation powder",
        "11109000",
    ),
    (
        "C150103",
        "PDF",
        "C42945",
        "Injectable Solution Dosage Form",
        "Solution for injection",
        "11201000",
    ),
    ("C150103", "PDF", "C1", "No code", "No code", None),
]


def _workbook(path):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = edqm_ct.SHEET
    sheet.append(HEADER)
    for row in ROWS:
        sheet.append(row)
    workbook.save(path)
    return path


def test_collect_terms_sorted_and_complete_only():
    terms = edqm_ct.collect_terms(ROWS + [("C150103", "PDF")])
    assert terms == [
        {"code": "11109000", "term": "Inhalation powder", "ncit": "C91142"},
        {"code": "11201000", "term": "Solution for injection", "ncit": "C42945"},
    ]


def test_render_keeps_attribution_and_dates():
    text = edqm_ct.render([], "f.xlsx", "2026-05-27", "2026-11-11")
    assert "reproduced with the permission of the European Directorate" in text
    data = yaml.safe_load(text)
    assert data["codeSystem"] == "http://standardterms.edqm.eu"
    assert data["release"] == "2026-05-27"
    assert data["retrieved"] == "2026-11-11"
    assert data["terms"] == []


def test_run_writes_the_file(tmp_path):
    source = _workbook(tmp_path / "edqm.xlsx")
    out = tmp_path / "out" / "dose_forms.yaml"
    summary = edqm_ct.run(source, out, "2026-11-11")
    assert summary["terms"] == 2
    data = yaml.safe_load(out.read_text())
    assert [t["code"] for t in data["terms"]] == ["11109000", "11201000"]


def test_dry_run_writes_nothing(tmp_path):
    source = _workbook(tmp_path / "edqm.xlsx")
    out = tmp_path / "dose_forms.yaml"
    edqm_ct.run(source, out, "2026-11-11", dry_run=True)
    assert not out.exists()


def test_main(tmp_path, capsys):
    source = _workbook(tmp_path / "edqm.xlsx")
    out = tmp_path / "dose_forms.yaml"
    assert edqm_ct.main(["--source", str(source), "--out", str(out)]) == 0
    assert "2 dose forms" in capsys.readouterr().out
    assert out.exists()


def test_main_without_source(capsys):
    assert edqm_ct.main([]) == 1
    assert "pass --source" in capsys.readouterr().err


def test_default_out_path():
    assert edqm_ct._out_path().parts[-3:] == ("ct", "edqm", "dose_forms.yaml")
