"""Compare CORE and d4k validation results rule-by-rule.

Reads two YAML files — one produced by ``core.py`` (CDISC CORE engine) and
one produced by ``d4k.py`` (usdm4 rule library) for the same USDM JSON
input — and produces a rule-by-rule alignment report.

Usage::

    python compare.py <core.yaml> <d4k.yaml> [-o alignment.yaml] [--text]
        [--core-rules-json /path/to/core/rules/usdm/4-0.json]

ID reconciliation
-----------------
CORE reports findings under its own ``CORE-NNNNNN`` namespace. d4k reports
under the ``DDF000NN`` namespace. Historically this comparer matched rule
ids as raw strings, producing duplicate rows for the same rule — once under
its CORE id and once under its DDF id.

To reconcile, at startup the comparer loads the CDISC CORE rules JSON
cache (the one populated by ``tools/prepare_core_cache.py``) and builds a
``CORE-id -> DDF-id`` map from each rule's ``authorities[].Standards[]
.References[].Rule_Identifier.Id`` (Version 4.0 only). CORE findings whose
ids resolve to a DDF id are re-keyed under the DDF id before classification,
so aligned failures appear on a single row and divergence counts reflect
genuine disagreement. CORE findings with no DDF mapping retain their CORE
id and are classified as ``core_only_rule``.

What the report contains
------------------------
For each rule id found in either engine's output:

- ``d4k_status``:  Success / Failure / Exception / Not Implemented / Absent
- ``d4k_findings``: count of findings on the d4k side
- ``core_status``: Fail (rule in findings) / Pass-or-NA (not reported) / Absent-from-Run
- ``core_findings``: count of findings on the CORE side
- ``core_id`` (when applicable): the original CORE-NNNNNN id, preserved for
  rows where a CORE finding was reconciled to a DDF id
- ``classification`` — one of:
    - ``aligned_pass``    — d4k Success, CORE did not report findings
    - ``aligned_fail``    — both engines flagged the rule
    - ``count_mismatch``  — both flagged but finding counts differ
    - ``d4k_only``        — d4k flagged, CORE did not
    - ``core_only``       — CORE flagged, d4k did not
    - ``d4k_exception``   — d4k raised an exception for this rule
    - ``d4k_not_impl``    — d4k marks the rule Not Implemented
    - ``core_only_rule``  — CORE id with no DDF mapping (CORE-native rule
                            with no DDF authority; d4k has no counterpart)

The CORE YAML only lists *failing* rules, so the report cannot reliably
distinguish "CORE executed this rule and it passed" from "CORE did not
know about this rule" at the rule-id level. Use the summary counts from
each YAML (``rules_executed`` in CORE, ``counts`` in d4k) to read the
big picture.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# CORE -> DDF id map
# ---------------------------------------------------------------------------

# Default locations to probe for the CORE rules JSON. Order matters.
DEFAULT_CORE_JSON_CANDIDATES = [
    Path.home() / "Library" / "Caches" / "usdm4" / "core" / "rules" / "usdm" / "4-0.json",
    Path.home() / ".cache" / "usdm4" / "core" / "rules" / "usdm" / "4-0.json",
]


def load_core_to_ddf_map(core_rules_json: Path | None) -> dict[str, str]:
    """Build {CORE-id: DDF-id} from the CORE rules JSON cache (V4 authorities).

    Returns an empty dict if the JSON isn't available or unreadable — the
    comparer falls back to raw string matching (original behaviour).
    """
    candidates: list[Path] = []
    if core_rules_json is not None:
        candidates.append(core_rules_json)
    candidates.extend(DEFAULT_CORE_JSON_CANDIDATES)

    path = next((p for p in candidates if p and p.is_file()), None)
    if path is None:
        print(
            "compare.py: no CORE rules JSON found — CORE/DDF id reconciliation "
            "disabled. Pass --core-rules-json or run tools/prepare_core_cache.py.",
            file=sys.stderr,
        )
        return {}

    try:
        entries = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"compare.py: failed to read {path}: {exc}; "
            "CORE/DDF id reconciliation disabled.",
            file=sys.stderr,
        )
        return {}

    if not isinstance(entries, list):
        return {}

    mapping: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("core_id")
        if not cid:
            continue
        ddf_ids: set[str] = set()
        for authority in entry.get("authorities") or []:
            if not isinstance(authority, dict):
                continue
            for standard in authority.get("Standards") or []:
                if not isinstance(standard, dict):
                    continue
                if standard.get("Version") != "4.0":
                    continue
                for ref in standard.get("References") or []:
                    if not isinstance(ref, dict):
                        continue
                    rid_obj = ref.get("Rule_Identifier") or {}
                    rid = rid_obj.get("Id") if isinstance(rid_obj, dict) else None
                    if isinstance(rid, str) and rid.startswith("DDF"):
                        ddf_ids.add(rid)
        if len(ddf_ids) == 1:
            mapping[cid] = next(iter(ddf_ids))
        # Multiple or zero DDF mappings: leave this CORE id unmapped.

    print(
        f"compare.py: loaded CORE->DDF id map ({len(mapping)} entries) "
        f"from {path}",
        file=sys.stderr,
    )
    return mapping


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_core(path: Path, core_to_ddf: dict[str, str]) -> dict:
    """Load and shape CORE YAML (output of ``CoreValidationResult.to_dict``).

    Returns a dict keyed by rule id (DDF id where reconcilable, otherwise
    the original CORE id) with {status, findings_count, description,
    message, core_id}. Rules not in CORE output are implicitly "Pass-or-NA" —
    we treat "absent from findings" as non-failing.
    """
    raw = yaml.safe_load(path.read_text())
    rules: dict[str, dict] = {}
    for finding in raw.get("findings", []) or []:
        core_rid = finding.get("rule_id", "unknown")
        # Reconcile CORE-NNNNNN -> DDF000NN where a V4 authority exists.
        effective_rid = core_to_ddf.get(core_rid, core_rid)
        row = {
            "status": "Fail",
            "findings_count": int(finding.get("error_count", 0)),
            "description": finding.get("description", ""),
            "message": finding.get("message", ""),
            "core_id": core_rid,
        }
        if effective_rid in rules:
            # Two CORE findings reconciling to the same DDF id is rare but
            # possible in principle — merge finding counts and preserve both
            # CORE ids for traceability.
            existing = rules[effective_rid]
            existing["findings_count"] += row["findings_count"]
            prev_ids = existing.get("core_id", "")
            existing["core_id"] = (
                f"{prev_ids},{core_rid}" if prev_ids else core_rid
            )
        else:
            rules[effective_rid] = row
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


def classify(
    d4k_row: dict | None, core_row: dict | None
) -> tuple[str, str, int, str, int]:
    """Return (classification, d4k_status, d4k_count, core_status, core_count)."""
    if d4k_row is None:
        # Rule only seen on CORE side — no DDF authority mapped or no d4k
        # implementation present.
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
        row = {
            "rule_id": rid,
            "classification": classification,
            "d4k_status": d4k_status,
            "d4k_findings": d4k_count,
            "core_status": core_status,
            "core_findings": core_count,
        }
        # Preserve CORE id for traceability when the row came from a reconciled
        # CORE finding (i.e. core_row exists and its core_id differs from rid).
        if core_row is not None and core_row.get("core_id") and core_row["core_id"] != rid:
            row["core_id"] = core_row["core_id"]
        rows.append(row)

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
    for cls, n in sorted(
        report["summary"]["classifications"].items(), key=lambda x: -x[1]
    ):
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
    header = (
        f"{'rule_id':<12} {'classification':<18} "
        f"{'d4k':<14} {'core':<14} {'core_id':<14}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    def sort_key(row):
        return (0 if row["classification"] in interesting else 1, row["rule_id"])

    for row in sorted(report["rows"], key=sort_key):
        if row["classification"] not in interesting:
            continue
        d4k_cell = f"{row['d4k_status']}({row['d4k_findings']})"
        core_cell = f"{row['core_status']}({row['core_findings']})"
        core_id_cell = row.get("core_id", "")
        lines.append(
            f"{row['rule_id']:<12} {row['classification']:<18} "
            f"{d4k_cell:<14} {core_cell:<14} {core_id_cell:<14}"
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
        core_id_cell = row.get("core_id", "")
        lines.append(
            f"{row['rule_id']:<12} {row['classification']:<18} "
            f"{d4k_cell:<14} {core_cell:<14} {core_id_cell:<14}"
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
    parser.add_argument(
        "--core-rules-json",
        default=None,
        help=(
            "Path to the CDISC CORE rules JSON cache "
            "(default: ~/Library/Caches/usdm4/core/rules/usdm/4-0.json). "
            "Used to reconcile CORE-NNNNNN ids to DDF000NN ids."
        ),
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

    core_to_ddf = load_core_to_ddf_map(
        Path(args.core_rules_json) if args.core_rules_json else None
    )

    core_data = load_core(core_path, core_to_ddf)
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
