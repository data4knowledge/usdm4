"""Corpus evaluation harness for the USDM4 assembler.

For every protocol in a corpus directory, this script:

  1. Loads ``ground_truth.yaml`` and pulls out ``unvalidated.content``
     (which has the canonical AssemblerInput shape).
  2. Runs ``Assembler.execute`` and ``.wrapper(...)`` to produce a USDM JSON.
  3. Runs the d4k engine (``USDM4.validate``) on that JSON.
  4. Optionally runs the CDISC CORE engine (``USDM4.validate_core``) on that JSON.

The result is a per-protocol record stored under ``<output_dir>/per_protocol/``
plus an aggregated ``summary.yaml`` that buckets protocols by failure stage
and tabulates the most common failing rule IDs across both engines.

Outcome buckets
----------------

- ``schema_rejected``  — AssemblerInput Pydantic validation failed; nothing else ran.
- ``assemble_failed``  — Assembler ran but produced no Study (caught exceptions).
- ``wrapper_failed``   — Study assembled, Wrapper construction failed.
- ``serialise_failed`` — Wrapper built, JSON encode raised.
- ``d4k_failed``       — JSON written but d4k validation raised.
- ``core_failed``      — d4k ran but CORE validation raised.
- ``ok``               — Pipeline ran end to end; the per-protocol record holds
                         the d4k / CORE outcomes for further analysis.

Note that ``ok`` does NOT mean d4k or CORE passed — it just means the pipeline
completed. Look at ``d4k.passed`` / ``core.is_valid`` in the per-protocol
record for that.

Usage
-----

  python validate/eval_corpus.py <corpus_root> -o <output_dir> [--no-core]
                                  [--limit N] [--ids id1,id2,...]
                                  [--cache-dir PATH]

The harness is single-process and synchronous; CORE is not thread-safe (per
CLAUDE.md).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import sys
import tempfile
import time
import traceback
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import yaml

# usdm4 must import cleanly before we import anything from it.
from simple_error_log.errors import Errors

import usdm4 as _usdm4_pkg  # noqa: E402
from usdm4 import USDM4  # noqa: E402
from usdm4.assembler.assembler import Assembler  # noqa: E402
from usdm4.rules.results import RuleStatus  # noqa: E402

# Local: corpus -> AssemblerInput shape adapter.
# Sibling import — works whether the script is run as ``python validate/eval_corpus.py``
# (no package context) or as ``python -m validate.eval_corpus``.
sys.path.insert(0, os.path.dirname(__file__))
from corpus_adapter import adapt as adapt_corpus  # noqa: E402
from d4k import results_to_dict as d4k_results_to_dict  # noqa: E402


def _root_path() -> str:
    return os.path.dirname(_usdm4_pkg.__file__)


# ----------------------------------------------------------------------------
# Per-protocol record
# ----------------------------------------------------------------------------


@dataclass
class ProtocolResult:
    protocol_id: str
    bucket: str = "ok"
    elapsed_s: float = 0.0
    error: Optional[str] = None  # short reason for non-ok buckets
    error_detail: Optional[str] = None  # truncated traceback / dump
    assembler_errors: int = 0
    adapter: dict = field(default_factory=dict)  # what the corpus adapter changed
    d4k: dict = field(default_factory=dict)
    core: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "protocol_id": self.protocol_id,
            "bucket": self.bucket,
            "elapsed_s": round(self.elapsed_s, 2),
            "assembler_errors": self.assembler_errors,
        }
        if self.adapter:
            d["adapter"] = self.adapter
        if self.error:
            d["error"] = self.error
        if self.error_detail:
            d["error_detail"] = self.error_detail
        if self.d4k:
            d["d4k"] = self.d4k
        if self.core:
            d["core"] = self.core
        return d


# ----------------------------------------------------------------------------
# Pipeline stages
# ----------------------------------------------------------------------------


def _load_content(
    corpus_root: pathlib.Path,
    pid: str,
    *,
    strip_soa: bool = False,
    use_adapter: bool = True,
) -> tuple[dict, dict]:
    """Read corpus ground_truth.yaml; optionally adapt to AssemblerInput shape.

    Returns ``(content, adapter_info)``. ``adapter_info`` is a dict with what
    the adapter changed (empty when ``use_adapter=False``).
    """
    gt_path = corpus_root / "protocols" / pid / "ground_truth.yaml"
    gt = yaml.safe_load(gt_path.read_text())
    content = gt["unvalidated"]["content"]
    adapter_info: dict = {}
    if use_adapter:
        content, report = adapt_corpus(content)
        adapter_info = {
            k: v
            for k, v in {
                "soa_list_collapsed": report.soa_list_collapsed,
                "soa_subtimelines_dropped": report.soa_subtimelines_dropped,
                # Tuples don't safe-dump cleanly — flatten to lists.
                "role_keys_normalised": [
                    list(t) for t in report.role_keys_normalised
                ],
                "role_keys_dropped": list(report.role_keys_dropped),
                "non_standard_type_remapped": list(
                    report.non_standard_type_remapped
                ),
                "enrollment_defaulted": report.enrollment_defaulted,
                "placeholder_labels": list(report.placeholder_labels),
                "pydantic_defaults_injected": report.pydantic_defaults_injected,
            }.items()
            if v
        }
    if strip_soa:
        # Hard escape hatch: bypass the SoA branch entirely.
        content.pop("soa", None)
        adapter_info["soa_stripped"] = True
    return content, adapter_info


def _assemble(
    content: dict, asm: Assembler, errors: Errors
) -> dict | None:
    """Assemble and return wrapper_dict. None on failure.

    The Assembler is expensive to construct (boots BC + CT libraries), so
    callers reuse a single instance and call ``clear()`` between protocols.
    """
    asm.execute(content)
    if asm.study is None:
        return None
    wrapper = asm.wrapper("usdm4-eval-harness", "0.0.1")
    if wrapper is None:
        return None
    return wrapper.model_dump(by_alias=True)


def _summarise_d4k(result) -> dict:
    counts = Counter()
    failing = []
    exceptions = []
    for rid, outcome in result.outcomes.items():
        counts[outcome.status.value] += 1
        if outcome.status == RuleStatus.FAILURE:
            failing.append({"rule_id": rid, "errors": outcome.error_count})
        elif outcome.status == RuleStatus.EXCEPTION:
            exceptions.append({"rule_id": rid, "exception": outcome.exception})
    return {
        "passed": result.passed(),
        "passed_or_ni": result.passed_or_not_implemented(),
        "finding_count": result.finding_count,
        "counts": dict(counts),
        "failures": sorted(failing, key=lambda r: r["rule_id"]),
        "exceptions": sorted(exceptions, key=lambda r: r["rule_id"]),
    }


def _summarise_core(result) -> dict:
    by_rule = Counter()
    for f in result.findings:
        by_rule[f.rule_id] += len(f.errors)
    return {
        "is_valid": result.is_valid,
        "finding_count": result.finding_count,
        "execution_error_count": getattr(result, "execution_error_count", 0),
        "failing_rules": sorted(
            ({"rule_id": rid, "errors": n} for rid, n in by_rule.items()),
            key=lambda r: r["rule_id"],
        ),
    }


def evaluate_protocol(
    pid: str,
    corpus_root: pathlib.Path,
    usdm: USDM4,
    asm: Assembler,
    errors: Errors,
    per_engine_dir: pathlib.Path | None,
    *,
    run_core: bool,
    cache_dir: str | None,
    strip_soa: bool = False,
    use_adapter: bool = True,
) -> ProtocolResult:
    res = ProtocolResult(protocol_id=pid)
    t0 = time.monotonic()

    # Reset the shared assembler/errors between protocols.
    asm.clear()
    errors.clear()

    # --- load -------------------------------------------------------------
    try:
        content, adapter_info = _load_content(
            corpus_root, pid, strip_soa=strip_soa, use_adapter=use_adapter
        )
        res.adapter = adapter_info
    except Exception as e:
        res.bucket = "load_failed"
        res.error = type(e).__name__
        res.error_detail = traceback.format_exc(limit=4)
        res.elapsed_s = time.monotonic() - t0
        return res

    # --- assemble ---------------------------------------------------------
    try:
        wrapper_dict = _assemble(content, asm, errors)
    except Exception as e:  # genuinely unexpected — Assembler.execute swallows most
        res.bucket = "assemble_failed"
        res.error = f"unexpected: {type(e).__name__}"
        res.error_detail = traceback.format_exc(limit=8)
        res.elapsed_s = time.monotonic() - t0
        return res

    res.assembler_errors = errors.error_count()
    if wrapper_dict is None:
        # Distinguish schema rejection (no traceback in error) vs
        # caught exception (Errors.dump contains stack).
        dump = errors.dump(level=Errors.ERROR)
        res.error_detail = dump[:4000]
        if "Schema validation:" in dump:
            res.bucket = "schema_rejected"
            res.error = "AssemblerInput schema validation failed"
        else:
            res.bucket = "assemble_failed"
            res.error = "Assembler produced no Study"
        res.elapsed_s = time.monotonic() - t0
        return res

    # --- serialise --------------------------------------------------------
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{pid}.json", delete=False
        ) as fh:
            json.dump(wrapper_dict, fh, default=str)
            json_path = fh.name
    except Exception as e:
        res.bucket = "serialise_failed"
        res.error = type(e).__name__
        res.error_detail = traceback.format_exc(limit=4)
        res.elapsed_s = time.monotonic() - t0
        return res

    try:
        # --- d4k ----------------------------------------------------------
        try:
            d4k_result = usdm.validate(json_path)
            res.d4k = _summarise_d4k(d4k_result)
            # Per-engine YAML in the shape ``compare.py`` / ``engine_diff.py``
            # consume — same schema as ``validate/d4k.py``'s output.
            if per_engine_dir is not None:
                with (per_engine_dir / f"{pid}_d4k.yaml").open("w") as fh:
                    yaml.safe_dump(
                        d4k_results_to_dict(d4k_result, json_path),
                        fh,
                        default_flow_style=False,
                        sort_keys=False,
                    )
        except Exception as e:
            res.bucket = "d4k_failed"
            res.error = f"d4k: {type(e).__name__}"
            res.error_detail = traceback.format_exc(limit=8)
            res.elapsed_s = time.monotonic() - t0
            return res

        # --- core ---------------------------------------------------------
        if run_core:
            try:
                core_result = usdm.validate_core(json_path, cache_dir=cache_dir)
                res.core = _summarise_core(core_result)
                # Per-engine YAML in the shape ``compare.py`` consumes —
                # same schema as ``validate/core.py``'s output.
                if per_engine_dir is not None:
                    with (per_engine_dir / f"{pid}_core.yaml").open("w") as fh:
                        yaml.safe_dump(
                            core_result.to_dict(),
                            fh,
                            default_flow_style=False,
                            sort_keys=False,
                        )
            except Exception as e:
                res.bucket = "core_failed"
                res.error = f"core: {type(e).__name__}"
                res.error_detail = traceback.format_exc(limit=8)
                res.elapsed_s = time.monotonic() - t0
                return res
    finally:
        try:
            os.unlink(json_path)
        except OSError:
            pass

    res.elapsed_s = time.monotonic() - t0
    return res


# ----------------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------------


def aggregate(results: list[ProtocolResult]) -> dict:
    by_bucket = Counter(r.bucket for r in results)
    d4k_rule_failures = Counter()
    d4k_rule_exceptions = Counter()
    core_rule_failures = Counter()

    d4k_passed = 0
    d4k_passed_or_ni = 0
    core_valid = 0
    core_runs = 0
    d4k_runs = 0

    for r in results:
        if r.d4k:
            d4k_runs += 1
            d4k_passed += int(r.d4k.get("passed", False))
            d4k_passed_or_ni += int(r.d4k.get("passed_or_ni", False))
            for f in r.d4k.get("failures", []):
                d4k_rule_failures[f["rule_id"]] += 1
            for e in r.d4k.get("exceptions", []):
                d4k_rule_exceptions[e["rule_id"]] += 1
        if r.core:
            core_runs += 1
            core_valid += int(r.core.get("is_valid", False))
            for f in r.core.get("failing_rules", []):
                core_rule_failures[f["rule_id"]] += 1

    return {
        "totals": {
            "protocols": len(results),
            "by_bucket": dict(by_bucket),
        },
        "d4k": {
            "runs": d4k_runs,
            "passed": d4k_passed,
            "passed_or_not_implemented": d4k_passed_or_ni,
            "top_failing_rules": d4k_rule_failures.most_common(30),
            "top_exception_rules": d4k_rule_exceptions.most_common(30),
        },
        "core": {
            "runs": core_runs,
            "valid": core_valid,
            "top_failing_rules": core_rule_failures.most_common(30),
        },
    }


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------


def _list_protocols(
    corpus_root: pathlib.Path,
    explicit: list[str] | None,
    limit: int | None,
) -> list[str]:
    if explicit:
        return explicit
    proto_dir = corpus_root / "protocols"
    pids = sorted(p.name for p in proto_dir.iterdir() if p.is_dir())
    return pids[:limit] if limit else pids


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the USDM4 assembler over a protocol corpus and validate "
            "each output with d4k and (optionally) CORE."
        )
    )
    parser.add_argument(
        "corpus_root",
        type=pathlib.Path,
        help="Path to corpus root (must contain protocols/<id>/ground_truth.yaml)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("eval_output"),
        help="Directory where per-protocol records and summary.yaml go",
    )
    parser.add_argument(
        "--no-core", action="store_true", help="Skip CDISC CORE validation"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Process at most N protocols"
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help="Comma-separated list of protocol IDs to evaluate (overrides --limit)",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="CDISC cache dir (passed to USDM4.validate_core)",
    )
    # Progress is on by default — these calls take long enough that no
    # output at all is unhelpful. Pass --quiet for batch / CI usage.
    progress_group = parser.add_mutually_exclusive_group()
    progress_group.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        default=True,
        help="Print one-line progress per protocol (default).",
    )
    progress_group.add_argument(
        "--quiet",
        dest="progress",
        action="store_false",
        help="Suppress per-protocol progress output.",
    )
    parser.add_argument(
        "--strip-soa",
        action="store_true",
        help=(
            "Drop ``soa`` from input before assembly. Last-resort workaround "
            "for SoA shape problems the adapter cannot handle."
        ),
    )
    parser.add_argument(
        "--no-adapter",
        action="store_true",
        help=(
            "Skip the corpus->AssemblerInput adapter and feed raw "
            "ground_truth content to the assembler. Use this to measure "
            "the gap between corpus shape and current AssemblerInput."
        ),
    )
    args = parser.parse_args()

    corpus_root = args.corpus_root.resolve()
    if not (corpus_root / "protocols").is_dir():
        print(f"Error: {corpus_root} has no protocols/ subdir", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir.resolve()
    per_proto_dir = output_dir / "per_protocol"
    per_proto_dir.mkdir(parents=True, exist_ok=True)
    # Per-engine YAMLs in the shapes that ``validate/compare.py`` and
    # ``validate/engine_diff.py`` consume. Always emitted alongside the
    # consolidated record so the cross-engine corpus aggregate can be
    # produced by chaining: compare.py per file, then engine_diff.py.
    per_engine_dir = output_dir / "per_engine"
    per_engine_dir.mkdir(parents=True, exist_ok=True)

    explicit_ids = [s.strip() for s in args.ids.split(",")] if args.ids else None
    pids = _list_protocols(corpus_root, explicit_ids, args.limit)

    print(
        f"Evaluating {len(pids)} protocol(s) "
        f"(core={'no' if args.no_core else 'yes'})",
        file=sys.stderr,
    )

    # Quiet down USDM4's per-call cache-populated INFO logs — they fire on
    # every CORE validation and dominate the output. WARNING and above
    # (genuine cache breakage, network failures) still surface.
    logging.getLogger(
        "usdm4.core.core_cache_manager"
    ).setLevel(logging.WARNING)

    usdm = USDM4(cache_dir=args.cache_dir)
    shared_errors = Errors()
    shared_asm = Assembler(_root_path(), shared_errors)

    results: list[ProtocolResult] = []
    for i, pid in enumerate(pids, 1):
        res = evaluate_protocol(
            pid,
            corpus_root,
            usdm,
            shared_asm,
            shared_errors,
            per_engine_dir,
            run_core=not args.no_core,
            cache_dir=args.cache_dir,
            strip_soa=args.strip_soa,
            use_adapter=not args.no_adapter,
        )
        results.append(res)
        with (per_proto_dir / f"{pid}.yaml").open("w") as fh:
            yaml.safe_dump(
                res.to_dict(), fh, default_flow_style=False, sort_keys=False
            )
        if args.progress:
            print(
                f"[{i:>4}/{len(pids)}] {pid:<24} bucket={res.bucket:<18} "
                f"d4k_findings={res.d4k.get('finding_count', '-'):<5} "
                f"core_findings={res.core.get('finding_count', '-')}",
                file=sys.stderr,
            )

    summary = aggregate(results)
    summary["corpus_root"] = str(corpus_root)
    summary["output_dir"] = str(output_dir)
    with (output_dir / "summary.yaml").open("w") as fh:
        yaml.safe_dump(summary, fh, default_flow_style=False, sort_keys=False)

    by_bucket = summary["totals"]["by_bucket"]
    print("\n=== summary ===", file=sys.stderr)
    for bucket, n in sorted(by_bucket.items(), key=lambda x: -x[1]):
        print(f"  {bucket:<20} {n:>4}", file=sys.stderr)
    print(f"\nWrote {output_dir}/summary.yaml", file=sys.stderr)


if __name__ == "__main__":
    main()
