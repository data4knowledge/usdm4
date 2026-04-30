#!/usr/bin/env bash
# End-to-end corpus run: validate every USDM JSON in the corpus with both
# engines, then aggregate into a single engine-diff report.
#
# Usage:
#   validate/corpus.sh [output_dir]
#
# Environment overrides:
#   PYTHON       — python interpreter to use (default: python3)
#   CORPUS       — path to protocol_corpus (default: ~/Documents/github/protocol_corpus)
#   PATTERN      — glob (relative to CORPUS) for input JSONs
#                  (default: protocols/*/results/usdm.json)
#   LIMIT        — only process the first N files (smoke testing)
#   CACHE_DIR    — cache dir passed through to core.py
#
# Outputs (in output_dir, default validate/corpus_out):
#   <id>_core.yaml        per file: CORE engine result
#   <id>_d4k.yaml         per file: d4k engine result
#   <id>_vs_d4k.yaml      per file: rule-by-rule alignment
#   <id>_vs_d4k.txt       per file: human-readable alignment
#   manifest.yaml         corpus-level run summary
#   engine_diff.yaml      cross-corpus engine diff (structured)
#   engine_diff.md        cross-corpus engine diff (human-readable)

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
repo_root="$(cd -- "$script_dir/.." &> /dev/null && pwd)"

PYTHON="${PYTHON:-python3}"
CORPUS="${CORPUS:-$HOME/Documents/github/protocol_corpus}"
PATTERN="${PATTERN:-protocols/*/results/usdm.json}"

if [[ $# -ge 1 ]]; then
  out_dir="$1"
else
  out_dir="$repo_root/validate/corpus_out"
fi
mkdir -p "$out_dir"
out_dir="$(cd -- "$out_dir" &> /dev/null && pwd)"

cd "$repo_root"

echo "== corpus run"
echo "   corpus : $CORPUS"
echo "   pattern: $PATTERN"
echo "   output : $out_dir"
echo "   python : $PYTHON"
echo

corpus_args=(
  "validate/corpus.py"
  "--corpus" "$CORPUS"
  "--output" "$out_dir"
  "--pattern" "$PATTERN"
)
if [[ -n "${LIMIT:-}" ]]; then
  corpus_args+=("--limit" "$LIMIT")
fi
if [[ -n "${CACHE_DIR:-}" ]]; then
  corpus_args+=("--cache-dir" "$CACHE_DIR")
fi

# corpus.py exits 2 if any file had a stage error; that's still a successful
# run from the orchestrator's POV — the diff aggregator can use whatever
# YAMLs landed on disk.
"$PYTHON" "${corpus_args[@]}" || echo "(corpus.py reported per-file errors — see manifest.yaml)"

echo
echo "== engine-diff aggregation"
"$PYTHON" validate/engine_diff.py --reports "$out_dir"

echo
echo "Done."
echo "  Manifest    : $out_dir/manifest.yaml"
echo "  Engine diff : $out_dir/engine_diff.md"
echo "  Engine diff : $out_dir/engine_diff.yaml"
