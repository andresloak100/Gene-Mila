#!/bin/bash
# GEARS on the Norman export, seeds 0, 2, 3 in sequence (docs/PLAN_DL_BASELINES.md; lead's comment of 3 Nov on #51),
# then one bridge scoring per seed. Free: no LLM, no key in the environment, nice 19, CPU.
set -u
CLONE="$HOME/Documents/Mila/Gene-Mila/gene-mila-norman"; MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"
R="$CLONE/docs/results/gears_norman"; RC="$1"
cd "$CLONE"
for s in 0 2 3; do
  if pgrep -f run_research.py >/dev/null; then echo "paid run detected before seed $s; stopping" > "$R/chain.stopped"; exit 3; fi
  "$RC" "$R" "seed${s}_training" -- nice -n 19 "$HOME/gm_dlenv/bin/python" tools/baselines_dl/run_gears.py \
    --export "$HOME/cellforge_norman_export" --work "$HOME/gears_norman_work_s$s" --out "$HOME/gears_norman_s$s" \
    --seed $s --epochs 20 --device cpu || { echo "seed $s training failed" > "$R/chain.stopped"; exit 1; }
  cp "$HOME/gears_norman_s$s/receipt.json" "$R/seed${s}_runner_receipt.json"
done
for s in 0 2 3; do
  "$RC" "$R" "seed${s}_score" -- nice -n 19 "$MAIN/.venv/bin/python" tools/cellforge_bridge.py score \
    --bundle "$MAIN/data/norman" --pred "$HOME/gears_norman_s$s/predictions.npz" --name "gears_norman_s$s" \
    --versus "$MAIN/runs/norman_ds_from_n2_w4_r1" --out "docs/results/gears_norman_s$s.md" \
    || { echo "seed $s scoring failed" > "$R/chain.stopped"; exit 2; }
done
echo done > "$R/chain.done"
