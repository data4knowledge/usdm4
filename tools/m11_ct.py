"""Generate usdm4's M11 controlled terminology from the published ICH M11 Terminology.

The CDISC Library API does not serve the ICH M11 codelists, so usdm4 loads them
from two files in ``src/usdm4/ct/cdisc/missing/``:

  1. ``m11_codelists.yaml`` — whole M11 response codelists (the ``codelist:``
     shape, loaded by ``Library._add_whole_codelist``).
  2. ``missing_ct.yaml`` — M11-only codes added to extensible CDISC codelists
     (the ``extends:`` shape, loaded by ``Library._merge_extension``), found by
     diffing an M11 codelist against its SDTM counterpart (``M11_TO_SDTM``).

The source is the ICH M11 Terminology file published by NCI EVS
(https://evs.nci.nih.gov/ftp1/ICH/M11), an ``.xls`` with one row per codelist
or term: Code, Codelist Code, Codelist Extensible (Yes/No), Codelist Name,
ICH Preferred Term, ICH Synonym(s), ICH Definition, NCI Preferred Term. A
codelist row has an empty Codelist Code. Members, preferred terms, definitions,
synonyms and the extensible flag all come from this file — never from the ICH
M11 Technical Specification text, whose printed codelists are not the
published terminology (GitHub 81).

Only response codelists are emitted. The per-section data-element codelists
("ICH M11 Section 1 Terminology" ...) list field names, not permitted values.

No API calls, no key. Run from the repo root after a new terminology release:

    python3 tools/m11_ct.py
    python3 tools/m11_ct.py --dry-run
    python3 tools/m11_ct.py --terminology "/path/ICH M11 Terminology.xls"

The default terminology file is the newest ``ICH M11 Terminology_*.xls`` in the
sibling ``m11_specification`` repo's specification folder.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Any

import yaml

# M11 codelist -> SDTM codelist. An M11 codelist listed here has its codes
# missing from the SDTM codelist written to missing_ct.yaml as extensions.
M11_TO_SDTM: dict[str, str] = {
    "C217045": "C66737",  # Trial Phase
}

M11_SPEC_VERSION = "2025-11-16"
NCIT_M11_SOURCE_TAG = "NCIt-M11"
SECTION_CODELIST_PREFIX = "ICH M11 Section "
SHEET_PREFIX = "ICH M11 Terminology"

# Column order of the published file.
CODE, CODELIST, EXTENSIBLE, CODELIST_NAME, ICH_PT, ICH_SYNONYMS, ICH_DEFINITION, NCI_PT = range(8)


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _missing_dir() -> pathlib.Path:
    return _repo_root() / "src" / "usdm4" / "ct" / "cdisc" / "missing"


def _sdtm_cache_path() -> pathlib.Path:
    return _repo_root() / "src" / "usdm4" / "ct" / "cdisc" / "library_cache" / "library_cache_usdm.yaml"


def default_terminology_path(version: str = M11_SPEC_VERSION) -> pathlib.Path | None:
    """Newest ``ICH M11 Terminology_*.xls`` in the sibling m11_specification
    repo, by the date in its file name; None when there is none."""
    folder = _repo_root().parent / "m11_specification" / "m11_versions" / version / "specification"
    files = sorted(folder.glob("ICH M11 Terminology_*.xls"))
    return files[-1] if files else None


# --------------------------------------------------------------------------
# Reading the terminology file
# --------------------------------------------------------------------------


def read_rows(path: pathlib.Path) -> tuple[str, list[list[str]]]:
    """``(release, rows)`` from the terminology sheet, header row dropped.

    The data sheet is named ``ICH M11 Terminology <release date>`` (a
    ``ReadMe`` sheet may come first); the release is that date, or "" when
    the name carries none."""
    import xlrd  # tool-only dependency

    book = xlrd.open_workbook(str(path))
    sheet = next((s for s in book.sheets() if s.name.startswith(SHEET_PREFIX)), None)
    if sheet is None:
        raise ValueError(f"No '{SHEET_PREFIX} ...' sheet in {path}")
    release = sheet.name[len(SHEET_PREFIX) :].strip()
    rows = [[str(cell.value).strip() for cell in sheet.row(r)] for r in range(1, sheet.nrows)]
    return release, rows


def _synonyms(text: str) -> list[str]:
    return [s.strip() for s in re.split(r";", text or "") if s.strip()]


def is_response_codelist(name: str) -> bool:
    """A response codelist holds permitted values; the per-section
    data-element codelists ("ICH M11 Section 1 Terminology") do not."""
    return not name.startswith(SECTION_CODELIST_PREFIX)


def collect_codelists(rows: list[list[str]], release: str = "") -> dict[str, dict]:
    """``{codelist conceptId: entry}`` for every response codelist, in the
    ``codelist:`` shape. Terms keep the file's order. Each term also carries
    ``nciPreferredTerm`` for the extension diff; it is dropped on output."""
    codelists: dict[str, dict] = {}
    for row in rows:
        row = (row + [""] * 8)[:8]
        if row[CODE] and not row[CODELIST]:
            codelists[row[CODE]] = {
                "codelist": row[CODE],
                "source": NCIT_M11_SOURCE_TAG,
                "effective_date": release,
                "preferredTerm": row[ICH_PT],
                "definition": row[ICH_DEFINITION],
                "extensible": row[EXTENSIBLE].lower() == "yes",
                "synonyms": _synonyms(row[ICH_SYNONYMS]),
                "name": row[CODELIST_NAME],
                "terms": [],
            }
    for row in rows:
        row = (row + [""] * 8)[:8]
        if row[CODE] and row[CODELIST]:
            codelist = codelists.get(row[CODELIST])
            if codelist is None:
                raise ValueError(f"Term {row[CODE]} names codelist {row[CODELIST]} with no codelist row")
            codelist["terms"].append(
                {
                    "conceptId": row[CODE],
                    "preferredTerm": row[ICH_PT],
                    "definition": row[ICH_DEFINITION],
                    "submissionValue": "",
                    "synonyms": _synonyms(row[ICH_SYNONYMS]),
                    "nciPreferredTerm": row[NCI_PT],
                }
            )
    result = {}
    for cid in sorted(codelists):
        entry = codelists[cid]
        if is_response_codelist(entry.pop("name")):
            result[cid] = entry
    return result


def compute_extensions(codelists: dict[str, dict], sdtm_cache: dict[str, dict]) -> list[dict]:
    """M11 codes missing from each SDTM counterpart in ``M11_TO_SDTM``, as
    ``extends:`` entries. The preferred term is the NCI preferred term (the
    form SDTM publishes, e.g. "Phase II/III/IV Trial"), else the ICH one."""
    extensions: list[dict] = []
    for m11_id in sorted(M11_TO_SDTM):
        sdtm_id = M11_TO_SDTM[m11_id]
        m11 = codelists.get(m11_id)
        sdtm = sdtm_cache.get(sdtm_id)
        if not m11 or not sdtm:
            continue
        sdtm_ids = {t.get("conceptId") for t in sdtm.get("terms") or [] if isinstance(t, dict)}
        terms = [
            {
                "conceptId": t["conceptId"],
                "preferredTerm": t["nciPreferredTerm"] or t["preferredTerm"],
                "definition": t["definition"],
                "submissionValue": "",
                "synonyms": [],
            }
            for t in m11["terms"]
            if t["conceptId"] not in sdtm_ids
        ]
        if terms:
            extensions.append({"extends": sdtm_id, "source": NCIT_M11_SOURCE_TAG, "terms": terms})
    return extensions


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def _header(kind: str, source: str, release: str) -> str:
    return (
        f"# {kind}\n"
        f"#\n"
        f"# Generated from the ICH M11 Terminology published by NCI EVS\n"
        f"# ({source}, release {release or 'unknown'}) by usdm4/tools/m11_ct.py.\n"
        f"# DO NOT EDIT — regenerate with the tool.\n"
    )


def _dump(payload: Any) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False)


def render_codelists(codelists: dict[str, dict], source: str, release: str) -> str:
    payload = []
    for cid in sorted(codelists):
        entry = dict(codelists[cid])
        entry["terms"] = [{k: v for k, v in t.items() if k != "nciPreferredTerm"} for t in entry["terms"]]
        payload.append(entry)
    header = _header(
        "Whole ICH M11 response codelists, not served by the CDISC Library API;\n"
        "# loaded by Library._add_whole_codelist.",
        source,
        release,
    )
    return header + (_dump(payload) if payload else "[]\n")


def render_extensions(extensions: list[dict], source: str, release: str) -> str:
    header = _header(
        "ICH M11 codes missing from extensible CDISC codelists, added as\n"
        "# extensions (M11_TO_SDTM in the tool); loaded by Library._merge_extension.",
        source,
        release,
    )
    return header + (_dump(extensions) if extensions else "[]\n")


def _write(path: pathlib.Path, text: str, dry_run: bool) -> None:
    if dry_run:
        print(f"--- {path} (dry run, {len(text)} bytes) ---")
        return
    path.write_text(text, encoding="utf-8")


def run(
    terminology: pathlib.Path,
    sdtm_cache_path: pathlib.Path,
    out_dir: pathlib.Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    release, rows = read_rows(terminology)
    codelists = collect_codelists(rows, release)
    with open(sdtm_cache_path) as f:
        sdtm_cache = yaml.safe_load(f) or {}
    extensions = compute_extensions(codelists, sdtm_cache)
    _write(out_dir / "m11_codelists.yaml", render_codelists(codelists, terminology.name, release), dry_run)
    _write(out_dir / "missing_ct.yaml", render_extensions(extensions, terminology.name, release), dry_run)
    return {
        "release": release,
        "codelists": len(codelists),
        "terms": sum(len(c["terms"]) for c in codelists.values()),
        "extension_terms": sum(len(e["terms"]) for e in extensions),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate usdm4's M11 CT from the ICH M11 Terminology file.")
    parser.add_argument("--terminology", type=pathlib.Path, default=None, help="Path to the ICH M11 Terminology .xls.")
    parser.add_argument("--sdtm-cache", type=pathlib.Path, default=_sdtm_cache_path())
    parser.add_argument("--out-dir", type=pathlib.Path, default=_missing_dir())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    terminology = args.terminology or default_terminology_path()
    if terminology is None or not terminology.exists():
        print("No ICH M11 Terminology file found; pass --terminology", file=sys.stderr)
        return 1
    summary = run(terminology, args.sdtm_cache, args.out_dir, args.dry_run)
    print(
        f"{terminology.name} (release {summary['release']}): {summary['codelists']} codelists, "
        f"{summary['terms']} terms, {summary['extension_terms']} extension terms"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
