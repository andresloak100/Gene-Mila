#!/bin/bash
# Block F, free preparation (docs/PLAN_F_GENOME_ANNOTATION.md): make data/norman_ga, a copy of data/norman plus the
# genome annotation knowledge file committed next to this script. Never changes data/norman. Run from a clone that has
# this script, e.g.  bash docs/mac/block_f/prepare_norman_ga.sh
# The copy is made under data/norman_ga.partial, checked, and only then renamed, so a failed or interrupted copy never
# leaves a data/norman_ga that looks finished (and that this script would then refuse to replace).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"; SRC="$MAIN/data/norman"; DST="$MAIN/data/norman_ga"; PART="$DST.partial"
GA_MD5=99e0eccb3caae76bc98f1c2e5730cfc0; RP_MD5=d9eff528143dcd4d72c87393df724084
# the Norman bundle's own files (its manifest's knowledge_files), B2's Replogle file and the new one, nothing else
WANT="gene_annotation.json gene_sets.json ppi_network.json prior_network.json replogle2022_k562.json targets.json transcription_factors.json"
no() { echo "NOT DONE: $*"; exit 1; }
[ -e "$DST" ] && no "$DST exists (never overwritten)"
[ -e "$PART" ] && no "$PART exists, left by an earlier attempt: look at it, remove it by hand, then start again"
[ "$(md5 -q "$SRC/knowledge/replogle2022_k562.json")" = "$RP_MD5" ] || no "data/norman's Replogle file is not B2's"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
gunzip -c "$HERE/gene_annotation_norman.json.gz" > "$tmp/gene_annotation.json" || no "cannot unpack the annotation file"
[ "$(md5 -q "$tmp/gene_annotation.json")" = "$GA_MD5" ] || no "annotation file md5 differs"
# the table was built for the Norman gene list committed in docs/results/norman_frozen_export_20261013/manifest.json:
# the bundle's genes must be exactly its genes plus its unmatched symbols, or it must be rebuilt for this bundle
"$MAIN/.venv/bin/python" - "$SRC/public.npz" "$tmp/gene_annotation.json" <<'PY' || no "gene list differs; rebuild with tools/build_gene_annotation.py --genes-from $SRC"
import json, sys
import numpy as np
genes = {str(g) for g in np.load(sys.argv[1], allow_pickle=False)["genes"]}
t = json.load(open(sys.argv[2]))
ok = genes == set(t["genes"]) | set(t["unmatched"])
print(f"bundle genes {len(genes)}, annotated {len(t['genes'])}, unmatched {len(t['unmatched'])}: {'same list' if ok else 'DIFFERENT'}")
sys.exit(0 if ok else 1)
PY
cp -Rp "$SRC" "$PART" || no "copy failed; $PART is left for you to remove"
cp "$tmp/gene_annotation.json" "$PART/knowledge/gene_annotation.json" || no "copy of the annotation file failed"
# the copy is data/norman byte for byte (diff prints only file names), plus the one new knowledge file
diff -rq --exclude=knowledge "$SRC" "$PART" || no "$PART differs from $SRC outside knowledge/"
diff -rq --exclude=gene_annotation.json "$SRC/knowledge" "$PART/knowledge" || no "$PART/knowledge differs from $SRC/knowledge"
[ "$(md5 -q "$PART/knowledge/replogle2022_k562.json")" = "$RP_MD5" ] || no "Replogle file in the copy differs"
[ "$(md5 -q "$PART/knowledge/gene_annotation.json")" = "$GA_MD5" ] || no "annotation file in the copy differs"
got="$(ls -A "$PART/knowledge" | LC_ALL=C sort | tr '\n' ' ' | sed 's/ $//')"
[ "$got" = "$WANT" ] || no "knowledge files are '$got', not '$WANT'"
mv "$PART" "$DST" || no "rename of $PART failed"
echo "done: $DST (knowledge: $got)"
