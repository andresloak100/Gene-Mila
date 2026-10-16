#!/bin/bash
# Block G, free preparation (docs/PLAN_G_CLEAN_ARM.md): the three tier-1 tables per dataset, then the four clean
# bundles. Never changes data/norman or data/adamson_cf; refuses if any output exists. Run from the clone that is at
# <G_COMMIT> (the integration head that carries tools/build_clean_bundle.py), e.g.
#   bash docs/mac/block_g/prepare_clean_bundles.sh
# Raw inputs: the files listed in the plan under "Raw downloads", fetched by the operator into $DL (names below).
# Every bundle is built under <name>.partial, checked, and renamed only then, so an interrupted build never leaves a
# bundle that looks finished (and that this script would then refuse to replace).
set -u
MAIN="$HOME/Documents/Mila/Gene-Mila/gene-mila"; DL="$HOME/Documents/Mila/Gene-Mila/data_downloads/clean_knowledge"
PY="$MAIN/.venv/bin/python"; C="$(cd "$(dirname "$0")/../../.." && pwd)"   # the clone this script is in
T="$DL/tables"                                                               # the built tables, one directory per dataset
no() { echo "NOT DONE: $*"; exit 1; }
cd "$C" || no "no clone at $C"
[ -e tools/build_clean_bundle.py ] || no "tools/build_clean_bundle.py is not in this clone; it must be at <G_COMMIT>"
for f in goa_human.gaf.gz go-basic.obo corum_allComplexes.txt string_physical_detailed.txt.gz string_info.txt.gz \
         collectri.tsv uniprot_human_reviewed.tsv gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz gencode.v27.gtf hg38.fasta \
         hg38.fasta.fai reactome.gmt.zip; do
  [ -s "$DL/$f" ] || no "$DL/$f is missing or empty (plan, Raw downloads)"
done
for ds in norman adamson_cf; do
  SRC="$MAIN/data/$ds"
  [ -e "$SRC/manifest.json" ] || no "$SRC is not a bundle"
  for out in "$MAIN/data/${ds}_clean" "$MAIN/data/${ds}_clean_tables"; do
    [ -e "$out" ] && no "$out exists (never overwritten)"
    [ -e "$out.partial" ] && no "$out.partial exists, left by an earlier attempt: look at it, remove it by hand, then start again"
  done
  [ -e "$T/$ds" ] && no "$T/$ds exists (the tables were built before; remove the directory by hand to rebuild)"
done
# 1. the three tables per dataset, each restricted to the bundle's gene list (--genes-from the existing bundle)
for ds in norman adamson_cf; do
  SRC="$MAIN/data/$ds"; mkdir -p "$T/$ds" || no "cannot make $T/$ds"
  "$PY" tools/build_gene_annotation.py --gtf "$DL/gencode.v27.gtf" --fasta "$DL/hg38.fasta" --genes-from "$SRC" \
    --out "$T/$ds/gene_annotation.json" || no "gene_annotation for $ds failed"
  "$PY" tools/build_gene_constraint.py --table "$DL/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz" --genes-from "$SRC" \
    --out "$T/$ds/gene_constraint.json" || no "gene_constraint for $ds failed"
  "$PY" tools/build_protein_annotation.py --tsv "$DL/uniprot_human_reviewed.tsv" --genes-from "$SRC" \
    --out "$T/$ds/protein_annotation.json" || no "protein_annotation for $ds failed"
done
# 2. the four bundles: the existing bundle's public.npz, private/ and splits (so the same split_id) with knowledge/
#    rebuilt from the tier-1 inputs only; the _tables bundle also carries the three tables as build-time knowledge
build() {  # build <dataset> <bundle name> [--table <name>=<table file>]...
  local ds="$1" name="$2"; shift 2
  local SRC="$MAIN/data/$ds" OUT="$MAIN/data/$name" PART="$MAIN/data/$name.partial"
  "$PY" tools/build_clean_bundle.py --bundle "$SRC" --sources "$DL" --out "$PART" "$@" || no "build of $name failed; $PART is left for you to look at"
  # byte for byte the source outside knowledge/ and manifest.json (diff prints only file names; nothing is read)
  diff -rq --exclude=knowledge --exclude=manifest.json "$SRC" "$PART" || no "$PART differs from $SRC outside knowledge/ and manifest.json"
  "$PY" - "$SRC" "$PART" "$#" <<'PY' || no "$name failed its checks (above)"
import json, sys
from pathlib import Path
from genemila.data.bundle import added_knowledge, verify_bundle
src, part, n_tables = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
ms, mp = json.loads((src / "manifest.json").read_text()), json.loads((part / "manifest.json").read_text())
want = ["gene_sets.json", "ppi_network.json", "prior_network.json", "targets.json", "transcription_factors.json"]
if n_tables:
    want += ["gene_annotation.json", "gene_constraint.json", "protein_annotation.json"]
problems = verify_bundle(part)
# the GO evidence codes the plan fixes (PLAN_G, Bundles): HMP and HGI, high-throughput perturbation annotations, are out
go_want = ["EXP", "HDA", "IC", "IDA", "IGI", "IMP", "IPI", "NAS", "TAS"]
go_got = sorted(((mp.get("clean_knowledge") or {}).get("provenance") or {}).get("go_evidence_codes") or [])
bad = [m for m, h in [(f"split_id {mp.get('split_id')} is not the source's {ms.get('split_id')}", mp.get("split_id") != ms.get("split_id")),
                      (f"GO evidence codes {go_got}, not the plan's {go_want}", go_got != go_want),
                      (f"knowledge_files {mp.get('knowledge_files')}, not {sorted(want)}", sorted(mp.get("knowledge_files") or []) != sorted(want)),
                      (f"verify_bundle: {problems}", bool(problems)),
                      (f"added_knowledge {added_knowledge(part)} (must be empty)", bool(added_knowledge(part)))] if h]
for m in bad: print("PROBLEM:", m)
print(f"{part.name}: split_id {mp['split_id']}, {mp['n_genes']} genes, knowledge_files {mp['knowledge_files']}")
sys.exit(1 if bad else 0)
PY
  mv "$PART" "$OUT" || no "rename of $PART failed"
  echo "done: $OUT"
}
for ds in norman adamson_cf; do
  build "$ds" "${ds}_clean"
  build "$ds" "${ds}_clean_tables" --table gene_annotation="$T/$ds/gene_annotation.json" \
    --table gene_constraint="$T/$ds/gene_constraint.json" --table protein_annotation="$T/$ds/protein_annotation.json"
  # G0 is G1's control only if the five shared files are byte for byte the same in both bundles (two builder calls)
  for f in gene_sets ppi_network prior_network targets transcription_factors; do
    cmp -s "$MAIN/data/${ds}_clean/knowledge/$f.json" "$MAIN/data/${ds}_clean_tables/knowledge/$f.json" \
      || no "$f.json differs between ${ds}_clean and ${ds}_clean_tables; the builder is not deterministic"
  done
done
# 3. the record: every knowledge file's md5, and the length of its line in the planner's knowledge summary
#    (genemila.lab.Lab.knowledge_summary at 60f1f44: a self-describing file shows its description cut at 900
#    characters and its keys). The whole-section length is printed for the record only; no cut is checked here (plan,
#    "What differs from B2").
for b in norman_clean norman_clean_tables adamson_cf_clean adamson_cf_clean_tables; do
  echo "== $b"; (cd "$MAIN/data/$b/knowledge" && md5 -r ./*.json)
  "$PY" - "$MAIN/data/$b/knowledge" <<'PY'
import json, sys
from pathlib import Path
parts = []
for p in sorted(Path(sys.argv[1]).glob("*.json")):
    o = json.loads(p.read_text())
    if isinstance(o, dict) and isinstance(o.get("description"), str):
        parts.append(f"{p.stem}: {o['description'][:900]} (a dict with keys {', '.join(map(str, o))})")
    elif isinstance(o, dict):
        k = next(iter(o), None); parts.append(f"{p.stem}: dict of {len(o)} entries, e.g. {k!r}: {str(o[k])[:60]}")
    else:
        parts.append(f"{p.stem}: list of {len(o)}, e.g. {str(o[0])[:60] if o else ''}")
    print(f"  {p.name}: knowledge-summary line {len(parts[-1])} characters")
print(f"  whole knowledge summary: {len('; '.join(parts))} characters")
PY
done
echo "done: four bundles under $MAIN/data/; tables under $T"
