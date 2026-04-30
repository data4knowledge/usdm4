"""Aggregate per-file CORE vs d4k results into a single engine-diff report.

Reads every ``<stem>_vs_d4k.yaml`` in a directory (produced by
``compare.py`` via ``corpus.py`` or ``run.sh``) plus the matching
``<stem>_core.yaml`` and ``<stem>_d4k.yaml`` files for evidence, and
classifies each rule as:

- ``d4k_under_reporting`` — at least one file where CORE flagged findings
  d4k did not (CORE-only) OR where CORE's finding count exceeded d4k's
  (count_mismatch with core > d4k). Assuming CORE findings are valid,
  these are the cases where d4k is missing errors.

- ``d4k_over_reporting`` — at least one file where d4k flagged findings
  CORE did not (d4k-only) OR where d4k's finding count exceeded CORE's
  (count_mismatch with d4k > core).

- ``mixed`` — both kinds of disagreement appear across the corpus
  (a rule disagrees in both directions on different files).

- ``aligned`` — no disagreement on any file (every file is aligned_pass
  or aligned_fail with matching counts).

- ``d4k_exception`` / ``d4k_not_impl`` — d4k could not run or is a stub
  on at least one file. These are surfaced separately because they're a
  different failure mode from genuine logic divergence.

- ``core_only_rule`` — CORE-NNNNNN rule with no DDF mapping; d4k has no
  counterpart implementation by design.

Usage::

    python validate/engine_diff.py [--reports validate/corpus_out]
                                   [--output validate/corpus_out/engine_diff.yaml]
                                   [--md validate/corpus_out/engine_diff.md]
                                   [--max-evidence 5]

The report sorts ``d4k_under_reporting`` first (the punch list of likely
d4k bugs) and includes per-rule evidence: which files exhibited the
divergence, the finding counts, and a sample CORE / d4k error message.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml


# Classifications produced by compare.py.
ALIGNED_PASS = "aligned_pass"
ALIGNED_FAIL = "aligned_fail"
COUNT_MISMATCH = "count_mismatch"
D4K_ONLY = "d4k_only"
CORE_ONLY = "core_only"
D4K_EXCEPTION = "d4k_exception"
D4K_NOT_IMPL = "d4k_not_impl"
CORE_ONLY_RULE = "core_only_rule"


def discover_alignment_yamls(reports_dir: Path) -> list[Path]:
    """Find every ``*_vs_d4k.yaml`` under ``reports_dir``."""
    return sorted(reports_dir.glob("*_vs_d4k.yaml"))


def file_id_from_alignment_path(path: Path) -> str:
    """Strip the ``_vs_d4k`` suffix to get the per-file stem."""
    name = path.name
    if name.endswith("_vs_d4k.yaml"):
        return name[: -len("_vs_d4k.yaml")]
    return path.stem


def load_alignment(path: Path) -> dict | None:
    try:
        return yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(f"engine_diff: cannot read {path}: {exc}", file=sys.stderr)
        return None


def load_engine_yaml(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(f"engine_diff: cannot read {path}: {exc}", file=sys.stderr)
        return None


def index_core_findings(core_data: dict | None) -> dict[str, dict]:
    """Index CORE findings by the rule_id reported in the YAML.

    Note: CORE YAML keys findings under the original CORE-NNNNNN id. The
    alignment YAML reconciles to DDF id when possible. For evidence
    lookup we also need to handle the reconciliation, so callers provide
    both the DDF id (from the alignment row) and the CORE id (when the
    alignment row carries ``core_id`` for a reconciled finding).
    """
    if not core_data:
        return {}
    indexed: dict[str, dict] = {}
    for finding in core_data.get("findings", []) or []:
        rid = finding.get("rule_id", "")
        if rid:
            indexed[rid] = finding
    return indexed


def index_d4k_outcomes(d4k_data: dict | None) -> dict[str, dict]:
    if not d4k_data:
        return {}
    indexed: dict[str, dict] = {}
    for outcome in d4k_data.get("outcomes", []) or []:
        rid = outcome.get("rule_id", "")
        if rid:
            indexed[rid] = outcome
    return indexed


def first_message(items: list[dict] | None, keys: list[str]) -> str:
    """Pull the first non-empty message field from a list of dicts."""
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for key in keys:
            val = item.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ""


def core_sample_message(finding: dict | None) -> str:
    if not finding:
        return ""
    msg = finding.get("message")
    if isinstance(msg, str) and msg.strip():
        return msg.strip()
    return first_message(finding.get("errors"), ["message"])


def core_sample_description(finding: dict | None) -> str:
    if not finding:
        return ""
    desc = finding.get("description")
    return desc.strip() if isinstance(desc, str) else ""


def d4k_sample_message(outcome: dict | None) -> str:
    if not outcome:
        return ""
    return first_message(outcome.get("errors"), ["message"])


def d4k_rule_text(outcome: dict | None) -> str:
    if not outcome:
        return ""
    return first_message(outcome.get("errors"), ["rule_text"])


def divergence_kind(row: dict) -> str | None:
    """Return 'under', 'over', or None for an alignment row.

    'under' = d4k is reporting *less* than CORE for this rule on this
    file (assuming CORE is right, d4k is missing errors).
    'over'  = d4k is reporting *more* than CORE.
    None    = no divergence on this file (aligned_pass / aligned_fail).
    """
    cls = row.get("classification")
    d4k_n = int(row.get("d4k_findings", 0) or 0)
    core_n = int(row.get("core_findings", 0) or 0)

    if cls == CORE_ONLY:
        return "under"
    if cls == D4K_ONLY:
        return "over"
    if cls == COUNT_MISMATCH:
        if core_n > d4k_n:
            return "under"
        if d4k_n > core_n:
            return "over"
        # Equal counts but compare.py marked count_mismatch — shouldn't
        # happen, but if it does, treat as no divergence.
        return None
    return None


def aggregate(reports_dir: Path) -> dict:
    """Walk per-file alignment YAMLs and aggregate by rule.

    Returns a dict structured for both YAML serialisation and
    human-readable rendering.
    """
    alignment_paths = discover_alignment_yamls(reports_dir)
    if not alignment_paths:
        raise SystemExit(f"engine_diff: no *_vs_d4k.yaml files under {reports_dir}")

    # Per-rule accumulator. We intentionally store per-file evidence,
    # not just counts — the user wants to investigate causes, so they
    # need to be able to jump to a file that exhibits the divergence.
    rule_state: dict[str, dict] = defaultdict(
        lambda: {
            "files_total": 0,
            "files_aligned_pass": 0,
            "files_aligned_fail": 0,
            "files_d4k_under": 0,
            "files_d4k_over": 0,
            "files_d4k_exception": 0,
            "files_d4k_not_impl": 0,
            "core_id_mappings": set(),  # CORE ids that reconciled to this DDF id
            "ddf_text": "",
            "core_description": "",
            "evidence_under": [],  # per-file rows where d4k under-reports
            "evidence_over": [],  # per-file rows where d4k over-reports
            "evidence_exception": [],
            "evidence_not_impl": [],
            "is_core_only_rule": False,
        }
    )

    files_seen = 0
    files_with_alignment = 0

    for align_path in alignment_paths:
        files_seen += 1
        align = load_alignment(align_path)
        if not align:
            continue
        files_with_alignment += 1

        stem = file_id_from_alignment_path(align_path)
        core_yaml = reports_dir / f"{stem}_core.yaml"
        d4k_yaml = reports_dir / f"{stem}_d4k.yaml"
        core_data = load_engine_yaml(core_yaml)
        d4k_data = load_engine_yaml(d4k_yaml)
        core_idx = index_core_findings(core_data)
        d4k_idx = index_d4k_outcomes(d4k_data)

        for row in align.get("rows", []) or []:
            rid = row.get("rule_id", "")
            if not rid:
                continue
            cls = row.get("classification")
            state = rule_state[rid]
            state["files_total"] += 1
            if cls == CORE_ONLY_RULE:
                state["is_core_only_rule"] = True

            # Track which CORE ids the reconciler folded into this rid.
            if row.get("core_id") and row["core_id"] != rid:
                # core_id may be comma-separated when multiple CORE rules
                # collapsed into one DDF id.
                for cid in str(row["core_id"]).split(","):
                    cid = cid.strip()
                    if cid:
                        state["core_id_mappings"].add(cid)

            # Snapshot rule text / description if we don't have it yet.
            if not state["ddf_text"]:
                # d4k carries rule_text on its error location; only
                # available when the rule actually fired with findings
                # on some file.
                d4k_outcome = d4k_idx.get(rid)
                txt = d4k_rule_text(d4k_outcome)
                if txt:
                    state["ddf_text"] = txt
            if not state["core_description"]:
                core_finding = core_idx.get(rid)
                if not core_finding:
                    # If alignment row points at a reconciled CORE id,
                    # try that one in the CORE YAML.
                    if row.get("core_id"):
                        for cid in str(row["core_id"]).split(","):
                            cid = cid.strip()
                            if cid and cid in core_idx:
                                core_finding = core_idx[cid]
                                break
                desc = core_sample_description(core_finding)
                if desc:
                    state["core_description"] = desc

            # Aligned cases — no evidence to record beyond the count.
            if cls == ALIGNED_PASS:
                state["files_aligned_pass"] += 1
                continue
            if cls == ALIGNED_FAIL:
                state["files_aligned_fail"] += 1
                continue

            # Lookup engine details for evidence.
            core_finding = core_idx.get(rid)
            if not core_finding and row.get("core_id"):
                for cid in str(row["core_id"]).split(","):
                    cid = cid.strip()
                    if cid and cid in core_idx:
                        core_finding = core_idx[cid]
                        break
            d4k_outcome = d4k_idx.get(rid)

            evidence = {
                "file": stem,
                "d4k_status": row.get("d4k_status", ""),
                "d4k_findings": int(row.get("d4k_findings", 0) or 0),
                "core_status": row.get("core_status", ""),
                "core_findings": int(row.get("core_findings", 0) or 0),
                "core_message": core_sample_message(core_finding),
                "d4k_message": d4k_sample_message(d4k_outcome),
            }
            if row.get("core_id"):
                evidence["core_id"] = row["core_id"]

            if cls == D4K_EXCEPTION:
                state["files_d4k_exception"] += 1
                exc = d4k_outcome.get("exception") if d4k_outcome else None
                if exc:
                    evidence["d4k_exception"] = (
                        exc if isinstance(exc, str) else str(exc)
                    )
                state["evidence_exception"].append(evidence)
                continue

            if cls == D4K_NOT_IMPL:
                state["files_d4k_not_impl"] += 1
                state["evidence_not_impl"].append(evidence)
                continue

            kind = divergence_kind(row)
            if kind == "under":
                state["files_d4k_under"] += 1
                state["evidence_under"].append(evidence)
            elif kind == "over":
                state["files_d4k_over"] += 1
                state["evidence_over"].append(evidence)

    return {
        "_meta": {
            "files_seen": files_seen,
            "files_with_alignment": files_with_alignment,
        },
        "rules": rule_state,
    }


def classify_rule(state: dict) -> str:
    """Bucket a per-rule accumulator into one of the engine-diff classes."""
    if state["is_core_only_rule"]:
        return CORE_ONLY_RULE
    under = state["files_d4k_under"] > 0
    over = state["files_d4k_over"] > 0
    if state["files_d4k_exception"] > 0 and not (under or over):
        return D4K_EXCEPTION
    if state["files_d4k_not_impl"] > 0 and not (under or over):
        return D4K_NOT_IMPL
    if under and over:
        return "mixed"
    if under:
        return "d4k_under_reporting"
    if over:
        return "d4k_over_reporting"
    return "aligned"


def trim_evidence(items: list[dict], max_n: int) -> list[dict]:
    """Cap the per-rule evidence list, sorted by largest divergence first."""

    def divergence_size(item):
        return abs(int(item.get("core_findings", 0)) - int(item.get("d4k_findings", 0)))

    sorted_items = sorted(items, key=divergence_size, reverse=True)
    return sorted_items[:max_n]


def build_report(agg: dict, max_evidence: int) -> dict:
    rules_out: dict[str, dict] = {}
    bucket_counts: dict[str, int] = defaultdict(int)

    for rid, state in agg["rules"].items():
        bucket = classify_rule(state)
        bucket_counts[bucket] += 1
        rules_out[rid] = {
            "rule_id": rid,
            "bucket": bucket,
            "ddf_text": state["ddf_text"],
            "core_description": state["core_description"],
            "core_id_mappings": sorted(state["core_id_mappings"]),
            "files_total": state["files_total"],
            "files_aligned_pass": state["files_aligned_pass"],
            "files_aligned_fail": state["files_aligned_fail"],
            "files_d4k_under": state["files_d4k_under"],
            "files_d4k_over": state["files_d4k_over"],
            "files_d4k_exception": state["files_d4k_exception"],
            "files_d4k_not_impl": state["files_d4k_not_impl"],
            "evidence_under": trim_evidence(state["evidence_under"], max_evidence),
            "evidence_over": trim_evidence(state["evidence_over"], max_evidence),
            "evidence_exception": trim_evidence(
                state["evidence_exception"], max_evidence
            ),
            "evidence_not_impl": trim_evidence(
                state["evidence_not_impl"], max_evidence
            ),
        }

    # Sort rules: d4k_under first, then mixed, d4k_over, exception/not_impl,
    # then aligned, then core_only_rule. Within each bucket, sort by impact.
    bucket_priority = {
        "d4k_under_reporting": 0,
        "mixed": 1,
        "d4k_over_reporting": 2,
        D4K_EXCEPTION: 3,
        D4K_NOT_IMPL: 4,
        "aligned": 5,
        CORE_ONLY_RULE: 6,
    }

    def sort_key(rid_and_data):
        rid, data = rid_and_data
        bucket = data["bucket"]
        # Primary: bucket priority.
        # Secondary: how many files exhibit the divergence (descending).
        impact = (
            data["files_d4k_under"]
            + data["files_d4k_over"]
            + data["files_d4k_exception"]
            + data["files_d4k_not_impl"]
        )
        return (bucket_priority.get(bucket, 99), -impact, rid)

    sorted_rules = [data for _rid, data in sorted(rules_out.items(), key=sort_key)]

    return {
        "summary": {
            "files_seen": agg["_meta"]["files_seen"],
            "files_with_alignment": agg["_meta"]["files_with_alignment"],
            "rules_total": len(rules_out),
            "buckets": dict(bucket_counts),
        },
        "rules": sorted_rules,
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    buckets = summary["buckets"]
    lines: list[str] = []
    lines.append("# USDM4 Engine Diff Report")
    lines.append("")
    lines.append(
        f"Files seen: **{summary['files_seen']}**, "
        f"with alignment YAML: **{summary['files_with_alignment']}**, "
        f"distinct rules observed: **{summary['rules_total']}**."
    )
    lines.append("")
    lines.append("## Bucket counts")
    lines.append("")
    lines.append("| Bucket | Rules |")
    lines.append("|---|---:|")
    bucket_order = [
        "d4k_under_reporting",
        "mixed",
        "d4k_over_reporting",
        D4K_EXCEPTION,
        D4K_NOT_IMPL,
        "aligned",
        CORE_ONLY_RULE,
    ]
    for b in bucket_order:
        if b in buckets:
            lines.append(f"| `{b}` | {buckets[b]} |")
    lines.append("")
    lines.append("**Reading guide.**")
    lines.append("")
    lines.append(
        "- `d4k_under_reporting` — CORE finds errors d4k misses. "
        "**Treat each as a candidate d4k bug**, assuming the CORE finding is valid."
    )
    lines.append(
        "- `d4k_over_reporting` — d4k finds errors CORE doesn't. "
        "Either CORE is wrong (worth disputing upstream), or d4k is "
        "interpreting the rule more strictly than the spec intends."
    )
    lines.append(
        "- `mixed` — both kinds of disagreement appear across the corpus. "
        "Usually means the d4k implementation has both a missing case and "
        "an extra case."
    )
    lines.append(
        "- `d4k_exception` — d4k crashed on the rule. Investigate the "
        "stack trace before drawing conclusions."
    )
    lines.append(
        "- `d4k_not_impl` — the d4k rule is a stub. "
        "Implement it before treating it as a real comparison."
    )
    lines.append(
        "- `core_only_rule` — CORE-native rule with no DDF authority. "
        "d4k correctly has no counterpart; nothing to fix."
    )
    lines.append("")

    # Per-bucket sections.
    headers = {
        "d4k_under_reporting": (
            "d4k under-reporting — CORE finds errors d4k misses",
            True,
        ),
        "mixed": (
            "mixed — d4k diverges in both directions across the corpus",
            True,
        ),
        "d4k_over_reporting": (
            "d4k over-reporting — d4k finds errors CORE doesn't",
            True,
        ),
        D4K_EXCEPTION: ("d4k exceptions", True),
        D4K_NOT_IMPL: ("d4k not implemented", False),
        "aligned": ("Aligned (no divergence on any file)", False),
        CORE_ONLY_RULE: ("CORE-only rules (no DDF mapping)", False),
    }

    for bucket in bucket_order:
        rules_in_bucket = [r for r in report["rules"] if r["bucket"] == bucket]
        if not rules_in_bucket:
            continue
        title, with_evidence = headers[bucket]
        lines.append(f"## {title}")
        lines.append("")
        for r in rules_in_bucket:
            lines.append(
                f"### {r['rule_id']}  "
                f"(under={r['files_d4k_under']}, "
                f"over={r['files_d4k_over']}, "
                f"exc={r['files_d4k_exception']}, "
                f"not_impl={r['files_d4k_not_impl']}, "
                f"aligned_fail={r['files_aligned_fail']}, "
                f"aligned_pass={r['files_aligned_pass']}, "
                f"total_files={r['files_total']})"
            )
            lines.append("")
            if r["core_id_mappings"]:
                lines.append(f"_CORE id(s)_: {', '.join(r['core_id_mappings'])}")
            if r["ddf_text"]:
                lines.append(f"**DDF text.** {r['ddf_text']}")
                lines.append("")
            if r["core_description"]:
                lines.append(f"**CORE description.** {r['core_description']}")
                lines.append("")

            if with_evidence:
                if r["evidence_under"]:
                    lines.append("**Sample files where d4k under-reports:**")
                    lines.append("")
                    lines.append("| file | d4k | core | core message |")
                    lines.append("|---|---:|---:|---|")
                    for ev in r["evidence_under"]:
                        msg = (ev.get("core_message") or "").replace("|", "\\|")
                        lines.append(
                            f"| `{ev['file']}` | "
                            f"{ev['d4k_status']}({ev['d4k_findings']}) | "
                            f"{ev['core_status']}({ev['core_findings']}) | "
                            f"{msg} |"
                        )
                    lines.append("")
                if r["evidence_over"]:
                    lines.append("**Sample files where d4k over-reports:**")
                    lines.append("")
                    lines.append("| file | d4k | core | d4k message |")
                    lines.append("|---|---:|---:|---|")
                    for ev in r["evidence_over"]:
                        msg = (ev.get("d4k_message") or "").replace("|", "\\|")
                        lines.append(
                            f"| `{ev['file']}` | "
                            f"{ev['d4k_status']}({ev['d4k_findings']}) | "
                            f"{ev['core_status']}({ev['core_findings']}) | "
                            f"{msg} |"
                        )
                    lines.append("")
                if r["evidence_exception"]:
                    lines.append("**Sample d4k exceptions:**")
                    lines.append("")
                    for ev in r["evidence_exception"]:
                        exc = ev.get("d4k_exception") or "(no message)"
                        lines.append(f"- `{ev['file']}` — {exc}")
                    lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate per-file CORE vs d4k YAMLs into a single engine-diff report."
    )
    parser.add_argument(
        "--reports",
        default=None,
        help="Directory containing <stem>_vs_d4k.yaml files. "
        "Default: <repo_root>/validate/corpus_out",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output YAML path (default: <reports>/engine_diff.yaml)",
    )
    parser.add_argument(
        "--md",
        default=None,
        help="Output Markdown path (default: <reports>/engine_diff.md)",
    )
    parser.add_argument(
        "--max-evidence",
        type=int,
        default=5,
        help="Per-rule cap on evidence rows in each direction (default: 5).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    reports_dir = (
        Path(args.reports).expanduser().resolve()
        if args.reports
        else repo_root / "validate" / "corpus_out"
    )
    if not reports_dir.is_dir():
        print(f"Error: reports directory not found: {reports_dir}", file=sys.stderr)
        sys.exit(1)

    output_yaml = (
        Path(args.output).expanduser().resolve()
        if args.output
        else reports_dir / "engine_diff.yaml"
    )
    output_md = (
        Path(args.md).expanduser().resolve()
        if args.md
        else reports_dir / "engine_diff.md"
    )

    agg = aggregate(reports_dir)
    report = build_report(agg, max_evidence=args.max_evidence)

    output_yaml.write_text(yaml.dump(report, default_flow_style=False, sort_keys=False))
    output_md.write_text(render_markdown(report))

    summary = report["summary"]
    print(
        f"Engine diff: files_seen={summary['files_seen']} "
        f"files_with_alignment={summary['files_with_alignment']} "
        f"rules={summary['rules_total']}",
        file=sys.stderr,
    )
    for bucket, count in sorted(summary["buckets"].items(), key=lambda kv: -kv[1]):
        print(f"  {bucket:24s} {count}", file=sys.stderr)
    print(f"YAML: {output_yaml}", file=sys.stderr)
    print(f"MD  : {output_md}", file=sys.stderr)


if __name__ == "__main__":
    main()
