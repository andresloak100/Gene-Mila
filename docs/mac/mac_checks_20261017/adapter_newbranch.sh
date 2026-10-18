#!/bin/bash
# Mac checks of 17 Oct 2026 (claim #68), step 4, EXTRA diagnostic (not part of the PLAN_R section 6 gate): the 31
# single-gene anchors again, under renamed condition ids "<SYMBOL>__new" with the same target, so predict_ensemble takes
# its new-condition branch (original anchors plus one new condition per feature batch), the branch a Replogle target
# takes, instead of the anchor branch run A took. Compared afterwards with the saved anchor predictions. Free, nice 19.
set -u
A=docs/results/frozen_adapter_check_20261017
PY="$HOME/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python"
PKG="$HOME/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-export/runs/norman_frozen_export_20261013/package"
SHA=225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45
echo "# clone $(pwd) at $(git rev-parse --short=7 HEAD); $(date -u +%Y-%m-%dT%H:%M:%SZ)"
CMD=(nice -n 19 env PYTHONPATH="$PWD" PYTHONHASHSEED=0 "$PY" tools/frozen_model.py predict --package "$PKG" --manifest-sha256 "$SHA" --queries "$A/inputs/newbranch_queries.json" --out "$A/predict_newbranch_out")
printf '%q ' "${CMD[@]}"; echo
t0=$(date +%s); "${CMD[@]}"; rc=$?; echo "## D exit=$rc end $(date -u +%Y-%m-%dT%H:%M:%SZ) ($(( $(date +%s) - t0 )) s)"
