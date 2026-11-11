"""Generate usdm4's EDQM (ISO 11239) pharmaceutical dose form terms.

M11 Pharmaceutical Dose Form is "IDMP (ISO 11239) or CDISC SDTM
Terminology" (GitHub 104). The CDISC dose forms (C66726) come with the CDISC
CT cache; the ISO 11239 terms are the EDQM Standard Terms, which NCI EVS
publishes with an NCIt concept code for each term in the EDQM-HealthCare
Terminology Subsets workbook
(https://evs.nci.nih.gov/ftp1/EDQM-HealthCare/,
``NCIt_EDQM-HealthCare_Terminology_Subsets.xlsx``). This tool reads its
"Pharmaceutical Dosage Form" sheet into ``src/usdm4/ct/edqm/dose_forms.yaml``:
one entry per term with the EDQM code, the EDQM term and the NCIt code.

EDQM's conditions for reproducing Standard Terms are kept in the file
header: the data is from the EDQM Standard Terms database
(http://standardterms.edqm.eu), reproduced with the permission of the EDQM,
Council of Europe; terms are not modified; the retrieval date is stated, and
the database is not a static list.

No API calls, no key. Run from the repo root after downloading a new
workbook:

    python3 tools/edqm_ct.py --source /path/NCIt_EDQM-HealthCare_Terminology_Subsets.xlsx --retrieved 2026-11-11
    python3 tools/edqm_ct.py --source ... --dry-run
"""

from __future__ import annotations

import argparse
import datetime
import pathlib
import sys
from typing import Any

import yaml

SHEET = "Pharmaceutical Dosage Form"
SOURCE_URL = "https://evs.nci.nih.gov/ftp1/EDQM-HealthCare/"
CODE_SYSTEM = "http://standardterms.edqm.eu"
ATTRIBUTION = (
    "Data from the EDQM Standard Terms database (http://standardterms.edqm.eu), "
    "reproduced with the permission of the European Directorate for the Quality "
    "of Medicines & HealthCare, Council of Europe (EDQM). The EDQM Standard Terms "
    "database is not a static list and content can change over time."
)

# Column order of the published sheet.
NCIT_CODE, EDQM_TERM, EDQM_CODE = 2, 4, 5


def _out_path() -> pathlib.Path:
    return (
        pathlib.Path(__file__).resolve().parent.parent
        / "src"
        / "usdm4"
        / "ct"
        / "edqm"
        / "dose_forms.yaml"
    )


def read_rows(path: pathlib.Path) -> tuple[str, list[tuple]]:
    """The NCI release date (the workbook's modified date) and the sheet's
    rows after the header."""
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True)
    modified = workbook.properties.modified
    release = modified.date().isoformat() if modified else ""
    rows = list(workbook[SHEET].iter_rows(values_only=True))[1:]
    return release, rows


def collect_terms(rows: list[tuple]) -> list[dict]:
    """One entry per EDQM term, as published (not modified), sorted by term."""
    terms = {}
    for row in rows:
        row = tuple(row) + (None,) * (6 - len(row))
        code = str(row[EDQM_CODE] or "").strip()
        term = str(row[EDQM_TERM] or "").strip()
        ncit = str(row[NCIT_CODE] or "").strip()
        if code and term:
            terms[code] = {"code": code, "term": term, "ncit": ncit}
    return sorted(terms.values(), key=lambda t: t["term"].lower())


def render(terms: list[dict], source: str, release: str, retrieved: str) -> str:
    header = (
        "# EDQM (ISO 11239) pharmaceutical dose forms\n"
        "#\n"
        f"# {ATTRIBUTION}\n"
        "#\n"
        f"# Generated from the NCI EVS EDQM-HealthCare Terminology Subsets ({source},\n"
        f"# NCI release {release or 'unknown'}, retrieved {retrieved}, {SOURCE_URL})\n"
        "# by usdm4/tools/edqm_ct.py. DO NOT EDIT — regenerate with the tool.\n"
    )
    payload: dict[str, Any] = {
        "codeSystem": CODE_SYSTEM,
        "attribution": ATTRIBUTION,
        "release": release,
        "retrieved": retrieved,
        "terms": terms,
    }
    body = yaml.safe_dump(
        payload, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    return header + body


def run(
    source: pathlib.Path, out: pathlib.Path, retrieved: str, dry_run: bool = False
) -> dict[str, Any]:
    release, rows = read_rows(source)
    terms = collect_terms(rows)
    text = render(terms, source.name, release, retrieved)
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return {"release": release, "terms": len(terms)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate usdm4's EDQM dose forms from the NCI EDQM-HealthCare workbook."
    )
    parser.add_argument("--source", type=pathlib.Path, default=None)
    parser.add_argument(
        "--retrieved",
        default=datetime.date.today().isoformat(),
        help="Date the workbook was downloaded (YYYY-MM-DD).",
    )
    parser.add_argument("--out", type=pathlib.Path, default=_out_path())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.source is None or not args.source.exists():
        print("No EDQM-HealthCare workbook found; pass --source", file=sys.stderr)
        return 1
    summary = run(args.source, args.out, args.retrieved, args.dry_run)
    print(
        f"{args.source.name} (NCI release {summary['release']}): {summary['terms']} dose forms"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
