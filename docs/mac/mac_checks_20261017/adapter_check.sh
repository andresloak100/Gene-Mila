#!/bin/bash
# Mac checks of 17 Oct 2026 (claim #68), step 4: the frozen adapter check (docs/PLAN_R_FRESH_TEST.md section 6) on the
# B1 Norman export of 13 October. Free, CPU only, nice 19, from the clone gene-mila-macchecks. Run from the clone's root:
#   bash docs/mac/mac_checks_20261017/adapter_check.sh
# A: the 31 single-gene anchors through `predict-targets` (condition id == symbol for each of them);
# B: the 88 pair anchors through `predict`, queries serialised exactly as predict_targets() does;
# C: all 119 anchors through `predict`, query bytes identical to the export's original_target_only_queries.json.
set -u
A=docs/results/frozen_adapter_check_20261017
PY="$HOME/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python"
PKG="$HOME/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-export/runs/norman_frozen_export_20261013/package"
SHA=225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45
RUN=(nice -n 19 env PYTHONPATH="$PWD" PYTHONHASHSEED=0 "$PY" tools/frozen_model.py)
TARGETS=(); while read -r s; do TARGETS+=(--target "$s"); done < "$A/inputs/single_targets.txt"
echo "# clone $(pwd) at $(git rev-parse --short=7 HEAD); $(date -u +%Y-%m-%dT%H:%M:%SZ)"
step() { local name="$1"; shift; echo "## $name start $(date -u +%Y-%m-%dT%H:%M:%SZ)"; printf '%q ' "$@"; echo
  local t0=$(date +%s); "$@"; local rc=$?; echo "## $name exit=$rc end $(date -u +%Y-%m-%dT%H:%M:%SZ) ($(( $(date +%s) - t0 )) s)"; }
step A "${RUN[@]}" predict-targets --package "$PKG" --manifest-sha256 "$SHA" "${TARGETS[@]}" --out "$A/predict_targets_out"
step B "${RUN[@]}" predict --package "$PKG" --manifest-sha256 "$SHA" --queries "$A/inputs/pairs_queries.json" --out "$A/predict_pairs_out"
step C "${RUN[@]}" predict --package "$PKG" --manifest-sha256 "$SHA" --queries "$A/inputs/all_anchors_queries.json" --out "$A/predict_all_anchors_out"
