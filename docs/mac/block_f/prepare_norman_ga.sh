#!/bin/bash
# Block F, free preparation (docs/PLAN_F_GENOME_ANNOTATION.md): make data/norman_ga, a copy of data/norman plus the
# genome annotation knowledge file committed next to this script. Never changes data/norman. Run from a clone that has
# this script, e.g.  bash docs/mac/block_f/prepare_norman_ga.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"; SRC="$MAIN/data/norman"; DST="$MAIN/data/norman_ga"
[ -e "$DST" ] && { echo "NOT DONE: $DST exists (never overwritten)"; exit 1; }
[ "$(md5 -q "$SRC/knowledge/replogle2022_k562.json")" = d9eff528143dcd4d72c87393df724084 ] || { echo "NOT DONE: data/norman's Replogle file is not B2's"; exit 1; }
tmp="$(mktemp -d)"; gunzip -c "$HERE/gene_annotation_norman.json.gz" > "$tmp/gene_annotation.json"
[ "$(md5 -q "$tmp/gene_annotation.json")" = 3f6aca1fc91cccdd5b684656d7f54963 ] || { echo "NOT DONE: annotation file md5 differs"; exit 1; }
# the table was built for the Norman gene list committed in docs/results/norman_frozen_export_20261013/manifest.json:
# the bundle's genes must be exactly its genes plus its unmatched symbols, or it must be rebuilt for this bundle
"$MAIN/.venv/bin/python" - "$SRC/public.npz" "$tmp/gene_annotation.json" <<'PY' || { echo "NOT DONE: gene list differs; rebuild with tools/build_gene_annotation.py --genes-from $SRC"; exit 1; }
import json, sys
import numpy as np
genes = {str(g) for g in np.load(sys.argv[1], allow_pickle=False)["genes"]}
t = json.load(open(sys.argv[2]))
ok = genes == set(t["genes"]) | set(t["unmatched"])
print(f"bundle genes {len(genes)}, annotated {len(t['genes'])}, unmatched {len(t['unmatched'])}: {'same list' if ok else 'DIFFERENT'}")
sys.exit(0 if ok else 1)
PY
cp -Rp "$SRC" "$DST" && cp "$tmp/gene_annotation.json" "$DST/knowledge/gene_annotation.json" && rm -rf "$tmp"
echo "done: $DST (knowledge: $(ls "$DST/knowledge" | tr '\n' ' '))"
