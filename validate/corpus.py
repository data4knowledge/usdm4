"""Run CORE + d4k validation across a USDM JSON corpus.

Walks a corpus directory, runs ``core.py``, ``d4k.py``, and ``compare.py``
against every USDM JSON file it finds, and writes per-file artefacts to an
output directory. Produces a corpus-level manifest summarising what ran and
what failed.

This is the multi-file companion of ``run.sh`` (which handles a single
file). Outputs are flat — one set of YAMLs per protocol, named by the
protocol's id — so ``engine_diff.py`` can aggregate them.

Usage::

    python validate/corpus.py [--corpus ~/Documents/github/protocol_corpus]
                              [--output validate/corpus_out]
                              [--pattern 'protocols/*/results/usdm.json']
                              [--limit 5]
                              [--cache-dir /path/to/core/cache]
                              [--continue-on-error]

The default pattern matches the layout of the public protocol_corpus repo
(``protocols/<id>/results/usdm.json``). Override ``--pattern`` for other
layouts; it is interpreted relative to ``--corpus`` via ``Path.glob``.

Per-file outputs (in ``--output``)::

    <id>.json             # copy of the input (so manifest is self-contained)
    <id>_core.yaml        # CORE engine result
    <id>_d4k.yaml         # d4k engine result
    <id>_vs_d4k.yaml      # rule-by-rule alignment
    <id>_vs_d4k.txt       # human-readable alignment

Corpus-level outputs::

    manifest.yaml         # what ran, per-file status, timings, errors
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import yaml


def discover_inputs(corpus_root: Path, pattern: str) -> list[Path]:
    """Glob ``pattern`` under ``corpus_root`` and return matching .json files."""
    return sorted(p for p in corpus_root.glob(pattern) if p.is_file())


def stem_for_input(corpus_root: Path, input_path: Path) -> str:
    """Build a unique, filesystem-safe stem from the path under the corpus.

    For ``protocols/<id>/results/usdm.json``, returns ``<id>``. For other
    layouts, returns the relative path with separators replaced by ``__``
    so different inputs cannot collide on the same stem.
    """
    rel = input_path.relative_to(corpus_root)
    parts = rel.parts
    # protocols/<id>/results/usdm.json  ->  <id>
    if (
        len(parts) >= 4
        and parts[0] == "protocols"
        and parts[2] == "results"
        and parts[-1].endswith(".json")
    ):
        return parts[1]
    # generic fallback: full relative path, no extension, separators flattened
    rel_no_ext = rel.with_suffix("")
    return "__".join(rel_no_ext.parts)


def run_stage(cmd: list[str], stage: str, log_path: Path) -> tuple[bool, str | None]:
    """Run a subprocess, capture stdout+stderr to ``log_path``.

    Returns ``(ok, error_message)``. ``ok`` is True if the process either
    exited cleanly OR exited non-zero with no exception (the per-file
    validators exit non-zero when findings exist — that is not a runner
    failure). ``ok`` is False only on an unexpected exception (process
    couldn't be launched, etc.).
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError) as exc:
        log_path.write_text(f"$ {' '.join(cmd)}\n[failed to launch: {exc}]\n")
        return False, f"{stage}: failed to launch ({exc})"

    log_path.write_text(
        f"$ {' '.join(cmd)}\n"
        f"[exit {proc.returncode}]\n"
        f"--- stdout ---\n{proc.stdout}\n"
        f"--- stderr ---\n{proc.stderr}\n"
    )
    # core.py / d4k.py / compare.py write their YAMLs even when validation
    # fails — non-zero exit is informational, not a runner error.
    return True, None


def validate_one(
    input_path: Path,
    stem: str,
    output_dir: Path,
    repo_root: Path,
    python: str,
    cache_dir: str | None,
) -> dict:
    """Run the three stages for a single input. Returns a manifest row.

    Stage failures are recorded but do not raise. The caller decides
    whether to halt or continue.
    """
    row: dict = {
        "input": str(input_path),
        "stem": stem,
        "core_yaml": None,
        "d4k_yaml": None,
        "alignment_yaml": None,
        "alignment_txt": None,
        "stages": {},
        "errors": [],
    }

    started = time.time()

    core_yaml = output_dir / f"{stem}_core.yaml"
    d4k_yaml = output_dir / f"{stem}_d4k.yaml"
    alignment_yaml = output_dir / f"{stem}_vs_d4k.yaml"
    alignment_txt = output_dir / f"{stem}_vs_d4k.txt"

    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 1. CORE
    core_cmd = [
        python,
        str(repo_root / "validate" / "core.py"),
        str(input_path),
        "-o",
        str(core_yaml),
    ]
    if cache_dir:
        core_cmd.extend(["--cache-dir", cache_dir])
    t0 = time.time()
    ok, err = run_stage(core_cmd, "core", log_dir / f"{stem}_core.log")
    row["stages"]["core"] = {
        "ok": ok,
        "duration_s": round(time.time() - t0, 2),
        "yaml_exists": core_yaml.exists(),
    }
    if err:
        row["errors"].append(err)
    if core_yaml.exists():
        row["core_yaml"] = str(core_yaml)

    # 2. d4k
    d4k_cmd = [
        python,
        str(repo_root / "validate" / "d4k.py"),
        str(input_path),
        "-o",
        str(d4k_yaml),
    ]
    t0 = time.time()
    ok, err = run_stage(d4k_cmd, "d4k", log_dir / f"{stem}_d4k.log")
    row["stages"]["d4k"] = {
        "ok": ok,
        "duration_s": round(time.time() - t0, 2),
        "yaml_exists": d4k_yaml.exists(),
    }
    if err:
        row["errors"].append(err)
    if d4k_yaml.exists():
        row["d4k_yaml"] = str(d4k_yaml)

    # 3. compare (only if both YAMLs exist)
    if core_yaml.exists() and d4k_yaml.exists():
        compare_cmd = [
            python,
            str(repo_root / "validate" / "compare.py"),
            str(core_yaml),
            str(d4k_yaml),
            "-o",
            str(alignment_yaml),
            "--text",
        ]
        t0 = time.time()
        ok, err = run_stage(compare_cmd, "compare", log_dir / f"{stem}_compare.log")
        row["stages"]["compare"] = {
            "ok": ok,
            "duration_s": round(time.time() - t0, 2),
            "yaml_exists": alignment_yaml.exists(),
        }
        if err:
            row["errors"].append(err)
        if alignment_yaml.exists():
            row["alignment_yaml"] = str(alignment_yaml)
        if alignment_txt.exists():
            row["alignment_txt"] = str(alignment_txt)
    else:
        row["stages"]["compare"] = {
            "ok": False,
            "duration_s": 0.0,
            "yaml_exists": False,
            "skipped_reason": "core or d4k YAML missing",
        }
        row["errors"].append("compare: skipped (core or d4k YAML missing)")

    row["duration_s"] = round(time.time() - started, 2)
    return row


def main():
    parser = argparse.ArgumentParser(
        description="Run CORE + d4k validation across a USDM JSON corpus"
    )
    parser.add_argument(
        "--corpus",
        default=str(Path.home() / "Documents" / "github" / "protocol_corpus"),
        help="Corpus root directory (default: ~/Documents/github/protocol_corpus)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for per-file YAMLs and manifest "
        "(default: <repo_root>/validate/corpus_out)",
    )
    parser.add_argument(
        "--pattern",
        default="protocols/*/results/usdm.json",
        help="Glob pattern (relative to --corpus) for USDM JSON files. "
        "Default matches protocol_corpus's layout.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Validate only the first N matching files (smoke testing).",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Cache directory passed to core.py (--cache-dir).",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter to use for sub-stages (default: this one).",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=True,
        help="Don't abort the corpus run on a per-file failure (default).",
    )
    parser.add_argument(
        "--stop-on-error",
        dest="continue_on_error",
        action="store_false",
        help="Abort the corpus run on the first per-file failure.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    corpus_root = Path(args.corpus).expanduser().resolve()
    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else repo_root / "validate" / "corpus_out"
    )

    if not corpus_root.is_dir():
        print(f"Error: corpus not found: {corpus_root}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    inputs = discover_inputs(corpus_root, args.pattern)
    if args.limit is not None:
        inputs = inputs[: args.limit]

    if not inputs:
        print(
            f"Error: no inputs matched {args.pattern!r} under {corpus_root}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Corpus runner: {len(inputs)} file(s) under {corpus_root}", file=sys.stderr)
    print(f"Output dir   : {output_dir}", file=sys.stderr)
    print(f"Python       : {args.python}", file=sys.stderr)
    if args.cache_dir:
        print(f"Cache dir    : {args.cache_dir}", file=sys.stderr)
    print("", file=sys.stderr)

    rows = []
    started = time.time()
    for idx, input_path in enumerate(inputs, start=1):
        stem = stem_for_input(corpus_root, input_path)
        print(
            f"[{idx}/{len(inputs)}] {stem}  ({input_path.relative_to(corpus_root)})",
            file=sys.stderr,
        )
        row = validate_one(
            input_path=input_path,
            stem=stem,
            output_dir=output_dir,
            repo_root=repo_root,
            python=args.python,
            cache_dir=args.cache_dir,
        )
        rows.append(row)

        # one-line per-file summary to stderr
        durations = " ".join(
            f"{name}={info.get('duration_s', 0):.1f}s"
            for name, info in row["stages"].items()
        )
        flags = " ".join(
            f"{name}=ok"
            if info.get("ok") and info.get("yaml_exists")
            else f"{name}=FAIL"
            for name, info in row["stages"].items()
        )
        print(f"   {flags}   ({durations})", file=sys.stderr)
        if row["errors"]:
            for err in row["errors"]:
                print(f"   ! {err}", file=sys.stderr)
            if not args.continue_on_error:
                print("Stopping on error (--stop-on-error).", file=sys.stderr)
                break

    total_duration = round(time.time() - started, 2)

    manifest = {
        "corpus_root": str(corpus_root),
        "output_dir": str(output_dir),
        "pattern": args.pattern,
        "python": args.python,
        "cache_dir": args.cache_dir,
        "total_inputs": len(inputs),
        "files_processed": len(rows),
        "duration_s": total_duration,
        "tallies": {
            "core_ok": sum(
                1 for r in rows if r["stages"].get("core", {}).get("yaml_exists")
            ),
            "d4k_ok": sum(
                1 for r in rows if r["stages"].get("d4k", {}).get("yaml_exists")
            ),
            "compare_ok": sum(
                1 for r in rows if r["stages"].get("compare", {}).get("yaml_exists")
            ),
            "with_errors": sum(1 for r in rows if r["errors"]),
        },
        "rows": rows,
    }
    manifest_path = output_dir / "manifest.yaml"
    manifest_path.write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    )

    print("", file=sys.stderr)
    print(f"Manifest: {manifest_path}", file=sys.stderr)
    print(
        f"Done. core_ok={manifest['tallies']['core_ok']}/{len(rows)} "
        f"d4k_ok={manifest['tallies']['d4k_ok']}/{len(rows)} "
        f"compare_ok={manifest['tallies']['compare_ok']}/{len(rows)} "
        f"errors={manifest['tallies']['with_errors']} "
        f"({total_duration:.1f}s)",
        file=sys.stderr,
    )

    # Exit non-zero if any file had errors, but only after writing manifest.
    sys.exit(0 if manifest["tallies"]["with_errors"] == 0 else 2)


if __name__ == "__main__":
    main()
