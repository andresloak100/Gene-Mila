#!/usr/bin/env python3
"""How much prior knowledge does each perturbation target have in a bundle, and is any of it lost to a gene symbol?

The knowledge loader (genemila/data/knowledge.py) keeps an entry only when its gene symbol matches one of the bundle's
measured genes letter for letter, and it has no alias handling. A bundle built from an older screen can name a gene by
a symbol HGNC has since retired (Adamson 2016 uses SRPR, MARS and ATP5B, now SRPRA, MARS1 and ATP5F1B), while the
current Reactome, GO, CollecTRI and STRING files use the new symbol. That target then has no gene set, no interaction
partner and no regulatory edge, and every feature that finds a perturbation's relatives through those files has
nothing to work with: a naming problem that looks like missing biology. This check comes before any new knowledge
source is judged (docs/FEATURE_COMPARISON_PROTOCOL.md).

For every perturbation target the report gives: whether the target is a measured gene, the number of gene sets that
contain it, its interaction partners (ppi_network), its regulatory edges as source and as target (prior_network), and
whether each external screen file (a knowledge file with a "perts" dict) has a row for it. With --hgnc (HGNC's
complete set, tab-separated, columns symbol, prev_symbol and alias_symbol) every target without gene sets, partners
or edges is looked up among the previous and alias symbols, and with --sources (the raw files genemila.data.knowledge
downloaded) the entries each current symbol would bring are counted with the loader's own parsers.

Read only: the bundle's public.npz, its knowledge/ files and the optional HGNC and source files. Never private/ or
splits.json. Free, a few seconds.

    python tools/knowledge_coverage.py --data data/adamson_cf --out coverage.md
    python tools/knowledge_coverage.py --data data/adamson_cf --hgnc hgnc_complete_set.txt --sources data_downloads/knowledge
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.data import knowledge as kn  # noqa: E402


def _load(kdir: Path, name: str):
    path = kdir / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def coverage(data_dir: Path) -> dict:
    """Per-target counts from the bundle's public files."""
    z = np.load(Path(data_dir) / "public.npz", allow_pickle=False)
    genes = {str(g) for g in z["genes"]}
    kdir = Path(data_dir) / "knowledge"
    targets = _load(kdir, "targets") or {}
    sets = collections.Counter(g for members in (_load(kdir, "gene_sets") or {}).values() for g in members)
    ppi = collections.Counter(x for a, b, *_ in (_load(kdir, "ppi_network") or []) for x in (a, b))
    out_edges = collections.Counter(a for a, b, *_ in (_load(kdir, "prior_network") or []))
    in_edges = collections.Counter(b for a, b, *_ in (_load(kdir, "prior_network") or []))
    screens = {}
    for path in sorted(kdir.glob("*.json")):
        obj = json.loads(path.read_text())
        if isinstance(obj, dict) and isinstance(obj.get("perts"), dict):
            screens[path.stem] = set(map(str, obj["perts"]))
    rows = []
    for gene in sorted({str(g) for v in targets.values() for g in v}):
        row = {"target": gene, "measured": gene in genes, "gene_sets": sets[gene], "ppi_partners": ppi[gene],
               "edges_out": out_edges[gene], "edges_in": in_edges[gene],
               "screens": {name: gene in rows_ for name, rows_ in screens.items()}}
        row["unannotated"] = not (row["gene_sets"] or row["ppi_partners"] or row["edges_out"] or row["edges_in"])
        rows.append(row)
    return {"n_genes": len(genes), "n_targets": len(rows), "screens": sorted(screens), "rows": rows,
            "genes_without_set": sum(1 for g in genes if not sets[g]),
            "has": {k: _load(kdir, k) is not None for k in ("gene_sets", "ppi_network", "prior_network")}}


def hgnc_current(path: Path) -> dict[str, set[str]]:
    """Retired or alias symbol -> current approved symbols, from HGNC's complete set (tab-separated)."""
    current: dict[str, set[str]] = collections.defaultdict(set)
    with open(path, newline="") as fh:
        for rec in csv.DictReader(fh, delimiter="\t"):
            symbol = (rec.get("symbol") or "").strip()
            for col in ("prev_symbol", "alias_symbol"):
                for old in (rec.get(col) or "").strip('"').split("|"):
                    old = old.strip().strip('"')
                    if old and symbol and old != symbol:
                        current[old].add(symbol)
    return current


def recoverable(sources: Path, names: set[str], universe: set[str]) -> dict[str, dict]:
    """Entries the raw knowledge sources would give each symbol in `names` in a bundle measuring `universe` plus those
    symbols, counted with the loader's own parsers and filters (set sizes, both ends of an edge measured)."""
    genes = set(universe) | set(names)
    sets = collections.Counter(g for m in kn.gene_sets(sources, genes).values() for g in m)
    net, _ = kn.collectri(sources, genes)
    edges = collections.Counter(x for a, b, _ in net for x in (a, b))
    ppi = collections.Counter(x for a, b, _ in kn.string_ppi(sources, genes) for x in (a, b))
    return {n: {"gene_sets": sets[n], "edges": edges[n], "ppi_partners": ppi[n]} for n in names}


def render(rep: dict) -> str:
    rows = rep["rows"]
    bad = [r for r in rows if r["unannotated"]]
    lines = [f"# Knowledge coverage of perturbation targets: {rep['data']}", "",
             f"{rep['n_targets']} targets, {rep['n_genes']} measured genes; {len(bad)} targets have no gene set, "
             f"interaction partner or regulatory edge; {sum(not r['measured'] for r in rows)} targets are not measured "
             f"genes; {rep['genes_without_set']} measured genes are in no gene set. Knowledge files present: "
             + ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in rep["has"].items())
             + (f"; external screens: {', '.join(rep['screens'])}" if rep["screens"] else "") + ".", ""]
    head = ["target", "measured", "gene sets", "PPI partners", "edges out", "edges in", *rep["screens"]]
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in sorted(rows, key=lambda r: (not r["unannotated"], r["target"])):
        cells = [f"**{r['target']}**" if r["unannotated"] else r["target"], "yes" if r["measured"] else "**no**",
                 r["gene_sets"], r["ppi_partners"], r["edges_out"], r["edges_in"],
                 *("row" if r["screens"][s] else "-" for s in rep["screens"])]
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    if "renames" in rep:
        lines += ["", "## Unannotated targets with a current HGNC symbol", "",
                  "Retired or alias symbol, the current symbol(s) HGNC gives, and what the raw sources hold under the "
                  "current symbol (blank without --sources). A bundle copy with the symbol mapped is its own arm, "
                  "a data-hygiene fix and not a discovery.", "",
                  "| target | current symbol | gene sets | regulatory edges | PPI partners |", "|---|---|---|---|---|"]
        for t, news in sorted(rep["renames"].items()):
            for new, got in sorted(news.items()):
                got = got or {}
                lines.append(f"| {t} | {new} | {got.get('gene_sets', '')} | {got.get('edges', '')} | "
                             f"{got.get('ppi_partners', '')} |")
        if not rep["renames"]:
            lines.append("| (none) | | | | |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="bundle or public directory (public.npz and knowledge/)")
    ap.add_argument("--hgnc", help="HGNC complete set (tab-separated) to look up retired and alias symbols")
    ap.add_argument("--sources", help="raw knowledge sources as genemila.data.knowledge.download wrote them")
    ap.add_argument("--out", help="Markdown report (a JSON twin is written next to it); default: print")
    args = ap.parse_args(argv)
    data = Path(args.data)
    if not (data / "public.npz").exists():
        print(f"no public.npz in {data}", file=sys.stderr)
        return 2
    rep = {"data": data.name, **coverage(data)}
    if args.hgnc:
        current = hgnc_current(Path(args.hgnc))
        renames = {r["target"]: {new: None for new in sorted(current.get(r["target"], ()))}
                   for r in rep["rows"] if r["unannotated"] and current.get(r["target"])}
        if args.sources and renames:
            universe = {str(g) for g in np.load(data / "public.npz", allow_pickle=False)["genes"]}
            got = recoverable(Path(args.sources), {n for v in renames.values() for n in v}, universe)
            renames = {t: {n: got[n] for n in v} for t, v in renames.items()}
        rep["renames"] = renames
    text = render(rep)
    if args.out:
        Path(args.out).write_text(text)
        Path(args.out).with_suffix(".json").write_text(json.dumps(rep, indent=1, sort_keys=True))
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
