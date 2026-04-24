"""Compare CORE and d4k validation results rule-by-rule.

Reads two YAML files — one produced by ``core.py`` (CDISC CORE engine) and
one produced by ``d4k.py`` (usdm4 rule library) for the same USDM JSON
input — and produces a rule-by-rule alignment report.

Usage::

    python compare.py <core.yaml> <d4k.yaml> [-o alignment.yaml] [--text]

What the report contains
------------------------
For each rule id found in either engine's output:

- ``d4k_status``:  Success / Failure / Exception / Not Implemented / Absent
- ``d4k_findings``: count of findings on the d4k side
- ``core_status``: Fail (rule in findings) / Pass-or-NA (not reported) / Absent-from-Run
- ``core_findings``: count of findings on the CORE side
- ``classification`` — one of:
    - ``aligned_pass``    — d4k Success, CORE did not report findings
    - ``aligned_fail``    — both engines flagged the rule
    - ``count_mismatch``  — both flagged but finding counts differ
    - ``d4k_only``        — d4k flagged, CORE did not
    - ``core_only``       — CORE flagged, d4k did not
    - ``d4k_exception``   — d4k raised an exception for this rule
    - ``d4k_not_impl``    — d4k marks the rule Not Implemented
    - ``core_only_rule``  — rule id only known to CORE (not in d4k library)

The CORE YAML only lists *failing* rules, so the report cannot reliably
distinguish "CORE executed this rule and it passed" from "CORE did not
know about this rule" at the rule-id level. Use the summary counts from
each YAML (``rules_executed`` in CORE, ``counts`` in d4k) to read the
big picture.
"""

import argparse
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_core(path: Path) -> dict:
    """Load and shape CORE YAML (output of ``CoreValidationResult.to_dict``).

    Returns a dict keyed by rule_id with {status, findings_count, message}.
    Rules not in CORE output are implicitly "Pass-or-NA" — we treat
    "absent from findings" as non-failing.
    """
    raw = yaml.safe_load(path.read_text())
    rules: dict[str, dict] = {}
    for finding in raw.get("findings", []) or []:
        rid = finding.get("rule_id", "unknown")
        rules[rid] = {
            "status": "Fail",
            "findings_count": int(finding.get("error_count", 0)),
            "description": finding.get("description", ""),
            "message": finding.get("message", ""),
        }
    return {
        "rules": rules,
        "summary": {
            "file": raw.get("file", ""),
            "is_valid": raw.get("is_valid"),
            "rules_executed": raw.get("rules_executed", 0),
            "rules_skipped": raw.get("rules_skipped", 0),
            "finding_count": raw.get("finding_count", 0),
            "execution_error_count": raw.get("execution_error_count", 0),
        },
    }


def load_d4k(path: Path) -> dict:
    """Load and shape d4k YAML (output of ``d4k.py::results_to_dict``)."""
    raw = yaml.safe_load(path.read_text())
    rules: dict[str, dict] = {}
    for outcome in raw.get("outcomes", []) or []:
        rid = outcome.get("rule_id", "unknown")
        rules[rid] = {
            "status": outcome.get("status", "unknown"),
            "findings_count": int(outcome.get("error_count", 0)),
            "exception": outcome.get("exception"),
        }
    return {
        "rules": rules,
        "summary": {
            "file": raw.get("file", ""),
            "is_valid": raw.get("is_valid"),
            "rules_executed": raw.get("rules_executed", 0),
            "finding_count": raw.get("finding_count", 0),
            "counts": raw.get("counts", {}),
        },
    }


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify(d4k_row: dict | None, core_row: dict | None) -> tuple[str, str, int, str, int]:
    """Return (classification, d4k_status, d4k_count, core_status, core_count)."""
    if d4k_row is None:
        # Rule only seen on CORE side — i.e. failing on CORE, not in d4k library
        return (
            "core_only_rule",
            "Absent",
            0,
            core_row["status"],
            core_row["findings_count"],
        )

    d4k_status = d4k_row["status"]
    d4k_count = d4k_row["findings_count"]
    core_status = core_row["status"] if core_row else "Pass-or-NA"
    core_count = core_row["findings_count"] if core_row else 0

    if d4k_status == "Exception":
        return ("d4k_exception", d4k_status, d4k_count, core_status, core_count)

    if d4k_status == "Not Implemented":
        return ("d4k_not_impl", d4k_status, d4k_count, core_status, core_count)

    d4k_fail = d4k_status == "Failure"
    core_fail = core_status == "Fail"

    if not d4k_fail and not core_fail:
        return ("aligned_pass", d4k_status, d4k_count, core_status, core_count)
    if d4k_fail and core_fail:
        if d4k_count == core_count:
            return ("aligned_fail", d4k_status, d4k_count, core_status, core_count)
        return ("count_mismatch", d4k_status, d4k_count, core_status, core_count)
    if d4k_fail and not core_fail:
        return ("d4k_only", d4k_status, d4k_count, core_status, core_count)
    return ("core_only", d4k_status, d4k_count, core_status, core_count)


# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------


def build_report(core_data: dict, d4k_data: dict) -> dict:
    rule_ids = sorted(set(core_data["rules"]) | set(d4k_data["rules"]))

    rows = []
    tallies: dict[str, int] = {}

    for rid in rule_ids:
        d4k_row = d4k_data["rules"].get(rid)
        core_row = core_data["rules"].get(rid)
        classification, d4k_status, d4k_count, core_status, core_count = classify(
            d4k_row, core_row
        )
        tallies[classification] = tallies.get(classification, 0) + 1
        rows.append(
            {
                "rule_id": rid,
                "classification": classification,
                "d4k_status": d4k_status,
                "d4k_findings": d4k_count,
                "core_status": core_status,
                "core_findings": core_count,
            }
        )

    return {
        "core_file": core_data["summary"].get("file", ""),
        "d4k_file": d4k_data["summary"].get("file", ""),
        "summary": {
            "core": core_data["summary"],
            "d4k": d4k_data["summary"],
            "rule_ids_total": len(rule_ids),
            "rule_ids_shared": len(
                set(core_data["rules"]) & set(d4k_data["rules"])
            ),
            "rule_ids_d4k_only_in_library": len(
                set(d4k_data["rules"]) - set(core_data["rules"])
            ),
            "rule_ids_core_only_in_library": len(
                set(core_data["rules"]) - set(d4k_data["rules"])
            ),
            "classifications": tallies,
        },
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Text rendering
# ---------------------------------------------------------------------------


def format_text(report: dict) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("USDM4 Engine Alignment Report (CORE vs d4k)")
    lines.append("=" * 78)

    core = report["summary"]["core"]
    d4k = report["summary"]["d4k"]
    lines.append(f"CORE file: {report['core_file']}")
    lines.append(f"d4k  file: {report['d4k_file']}")
    lines.append("")
    lines.append(
        f"CORE: rules_executed={core.get('rules_executed', 0)} "
        f"findings={core.get('finding_count', 0)} "
        f"skipped={core.get('rules_skipped', 0)} "
        f"exec_errors={core.get('execution_error_count', 0)}"
    )
    lines.append(
        f"d4k : rules_executed={d4k.get('rules_executed', 0)} "
        f"findings={d4k.get('finding_count', 0)} "
        f"counts={d4k.get('counts', {})}"
    )
    lines.append("")

    lines.append(f"Rule ids total      : {report['summary']['rule_ids_total']}")
    lines.append(f"Rule ids shared     : {report['summary']['rule_ids_shared']}")
    lines.append(
        f"Rule ids d4k-only   : {report['summary']['rule_ids_d4k_only_in_library']}"
    )
    lines.append(
        f"Rule ids CORE-only  : {report['summary']['rule_ids_core_only_in_library']}"
    )
    lines.append("")

    lines.append("Classifications:")
    for cls, n in sorted(report["summary"]["classifications"].items(),
                          key=lambda x: -x[1]):
        lines.append(f"  {cls:18s} {n}")
    lines.append("")

    # Table: only the "interesting" classifications first
    interesting = {
        "count_mismatch",
        "d4k_only",
        "core_only",
        "d4k_exception",
        "core_only_rule",
    }
    lines.append("-" * 78)
    lines.append("Divergent rules (most useful rows first):")
    lines.append("-" * 78)
    header = f"{'rule_id':<12} {'classification':<18} {'d4k':<14} {'core':<14}"
    lines.append(header)
    lines.append("-" * len(header))

    # sort: interesting first (alphabetical within), then the rest
    def sort_key(row):
        return (0 if row["classification"] in interesting else 1, row["rule_id"])

    for row in sorted(report["rows"], key=sort_key):
        if row["classification"] not in interesting:
            continue
        d4k_cell = f"{row['d4k_status']}({row['d4k_findings']})"
        core_cell = f"{row['core_status']}({row['core_findings']})"
        lines.append(
            f"{row['rule_id']:<12} {row['classification']:<18} "
            f"{d4k_cell:<14} {core_cell:<14}"
        )

    lines.append("")
    lines.append("-" * 78)
    lines.append("All rules:")
    lines.append("-" * 78)
    lines.append(header)
    lines.append("-" * len(header))
    for row in sorted(report["rows"], key=lambda r: r["rule_id"]):
        d4k_cell = f"{row['d4k_status']}({row['d4k_findings']})"
        core_cell = f"{row['core_status']}({row['core_findings']})"
        lines.append(
            f"{row['rule_id']:<12} {row['classification']:<18} "
            f"{d4k_cell:<14} {core_cell:<14}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Compare CORE and d4k validation YAML outputs rule-by-rule"
    )
    parser.add_argument("core_yaml", help="YAML file produced by core.py")
    parser.add_argument("d4k_yaml", help="YAML file produced by d4k.py")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output YAML alignment report (default: <core_stem>_vs_d4k.yaml)",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Also write a human-readable .txt report alongside the YAML",
    )
    args = parser.parse_args()

    core_path = Path(args.core_yaml)
    d4k_path = Path(args.d4k_yaml)
    if not core_path.exists():
        print(f"Error: CORE YAML not found: {core_path}", file=sys.stderr)
        sys.exit(1)
    if not d4k_path.exists():
        print(f"Error: d4k YAML not found: {d4k_path}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output)
        if args.output
        else core_path.with_name(f"{core_path.stem}_vs_d4k.yaml")
    )

    core_data = load_core(core_path)
    d4k_data = load_d4k(d4k_path)
    report = build_report(core_data, d4k_data)

    with open(output_path, "w") as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    print(f"Alignment report: {output_path}", file=sys.stderr)

    if args.text:
        text_path = output_path.with_suffix(".txt")
        text_path.write_text(format_text(report))
        print(f"Text report: {text_path}", file=sys.stderr)

    # brief stdout summary
    tallies = report["summary"]["classifications"]
    print("Classification tallies:", file=sys.stderr)
    for cls, n in sorted(tallies.items(), key=lambda x: -x[1]):
        print(f"  {cls:18s} {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
