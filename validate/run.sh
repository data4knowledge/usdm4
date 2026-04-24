#!/usr/bin/env bash
# Run CORE + d4k validation on a single USDM JSON file and compare results.
#
# Usage:
#   validate/run.sh <usdm.json> [output_dir]
#
# Produces, next to the input (or in output_dir if given):
#   <stem>_core.yaml      — CDISC CORE engine results
#   <stem>_d4k.yaml       — d4k (usdm4 rule library) results
#   <stem>_vs_d4k.yaml    — rule-by-rule alignment report
#   <stem>_vs_d4k.txt     — human-readable alignment report
#
# Environment overrides:
#   PYTHON                — python interpreter to use (default: python3)
#   CACHE_DIR             — cache dir passed to core.py (--cache-dir)

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
  sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi

input="$1"
if [[ ! -f "$input" ]]; then
  echo "Error: input file not found: $input" >&2
  exit 1
fi

# Resolve repo root = parent of this script's directory (validate/).
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
repo_root="$(cd -- "$script_dir/.." &> /dev/null && pwd)"

# Resolve input to an absolute path so subsequent `cd` is safe.
if [[ "$input" = /* ]]; then
  input_abs="$input"
else
  input_abs="$(cd -- "$(dirname -- "$input")" &> /dev/null && pwd)/$(basename -- "$input")"
fi

# Output directory: arg 2, else same dir as input.
if [[ $# -eq 2 ]]; then
  out_dir="$2"
  mkdir -p "$out_dir"
  out_dir="$(cd -- "$out_dir" &> /dev/null && pwd)"
else
  out_dir="$(dirname -- "$input_abs")"
fi

stem="$(basename -- "$input_abs")"
stem="${stem%.json}"

core_yaml="$out_dir/${stem}_core.yaml"
d4k_yaml="$out_dir/${stem}_d4k.yaml"
report_yaml="$out_dir/${stem}_vs_d4k.yaml"

PYTHON="${PYTHON:-python3}"

echo "== validate: $input_abs"
echo "   repo_root: $repo_root"
echo "   out_dir:   $out_dir"
echo

# Run from repo_root so `from usdm4 import ...` resolves against the installed
# package (or the src/ layout if run in an editable install).
cd "$repo_root"

echo "== [1/3] CORE engine  -> $core_yaml"
core_args=("$input_abs" "-o" "$core_yaml")
if [[ -n "${CACHE_DIR:-}" ]]; then
  core_args+=("--cache-dir" "$CACHE_DIR")
fi
# core.py exits non-zero when the study has findings; that is not a script error.
"$PYTHON" validate/core.py "${core_args[@]}" || echo "   (CORE reported findings — see $core_yaml)"

echo
echo "== [2/3] d4k engine   -> $d4k_yaml"
"$PYTHON" validate/d4k.py "$input_abs" -o "$d4k_yaml" || echo "   (d4k reported findings — see $d4k_yaml)"

echo
echo "== [3/3] compare      -> $report_yaml (+ .txt)"
"$PYTHON" validate/compare.py "$core_yaml" "$d4k_yaml" -o "$report_yaml" --text

echo
echo "Done."
echo "  CORE YAML   : $core_yaml"
echo "  d4k YAML    : $d4k_yaml"
echo "  Alignment   : $report_yaml"
echo "  Alignment   : ${report_yaml%.yaml}.txt"
