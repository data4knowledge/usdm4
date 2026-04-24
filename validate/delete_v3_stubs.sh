#!/usr/bin/env bash
# Delete the 47 V3-only rule stub files.
#
# These files contain only `raise NotImplementedError("rule is not implemented")`
# and correspond to rules marked Version 4.0 = N in DDF-RA/Deliverables/RULES/USDM_CORE_Rules.xlsx.
# They are not applicable to USDM V4 and are correctly excluded by
# tools/generate_rule_intermediate.py; the stubs are residue from an earlier
# generation pass before the V4 filter existed.
#
# Safety checks performed:
#   - src/usdm4/rules/engine.py loads rules via Path(...).glob("rule_*.py"),
#     so removal does not break the loader — missing files are simply not loaded.
#   - No direct imports of any of these files anywhere in src/ or tests/.
#   - No test_rule_ddfNNNNN.py files exist for any of the 47 (nothing orphaned).
#   - Only other references are the generated yaml reports in validate/, which
#     regenerate on next `run.sh`.
#
# Does NOT touch rule_ddf00045.py or rule_ddf00140.py — those are also marked
# V4=N in the xlsx but have real implementations; keep/delete TBD separately.
#
# Run from the repo root.

set -euo pipefail

cd "$(dirname "$0")/../src/usdm4/rules/library" 2>/dev/null || {
  echo "Run this from anywhere — it resolves src/usdm4/rules/library relative to itself." >&2
  echo "Or cd to usdm4/src/usdm4/rules/library and run the rm block directly." >&2
  exit 1
}

rm -v \
  rule_ddf00003.py rule_ddf00004.py rule_ddf00005.py \
  rule_ddf00015.py rule_ddf00016.py rule_ddf00043.py \
  rule_ddf00048.py rule_ddf00049.py rule_ddf00053.py \
  rule_ddf00055.py rule_ddf00056.py rule_ddf00057.py \
  rule_ddf00064.py rule_ddf00065.py rule_ddf00066.py \
  rule_ddf00067.py rule_ddf00068.py rule_ddf00070.py \
  rule_ddf00074.py rule_ddf00077.py rule_ddf00078.py \
  rule_ddf00079.py rule_ddf00085.py rule_ddf00086.py \
  rule_ddf00089.py rule_ddf00092.py rule_ddf00095.py \
  rule_ddf00103.py rule_ddf00109.py rule_ddf00111.py \
  rule_ddf00113.py rule_ddf00116.py rule_ddf00117.py \
  rule_ddf00118.py rule_ddf00119.py rule_ddf00120.py \
  rule_ddf00121.py rule_ddf00122.py rule_ddf00123.py \
  rule_ddf00129.py rule_ddf00130.py rule_ddf00131.py \
  rule_ddf00134.py rule_ddf00135.py rule_ddf00138.py \
  rule_ddf00139.py rule_ddf00145.py

echo
echo "Removed 47 V3-only stub files."
