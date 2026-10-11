"""Build a knowledge file from an external Perturb-seq screen (h5ad) for a bundle.

For every perturbation target of the bundle that the external screen also perturbed, the file holds the mean
response measured there (log1p counts per 10k, mean over cells, minus the screen's own non-targeting control
mean) over the bundle's genes, so features can transfer responses measured in another screen of the same cell
line. The h5ad is streamed with h5py in bounded chunks; X is never loaded whole. See
genemila/data/external_screen.py for the exact rules (label matching, pooling, count detection).

    python tools/build_external_screen.py --h5ad ReploglePlus2022_K562_gwps.h5ad --bundle data/adamson_cf \\
        --name replogle2022_k562 --dry-run       # pass 0 over obs: how many targets match, nothing written
    python tools/build_external_screen.py --h5ad ReploglePlus2022_K562_gwps.h5ad --bundle data/adamson_cf \\
        --name replogle2022_k562 --report docs/results/external_replogle2022_k562.md
    # renamed genes: the bundle symbol on the left, the screen's symbol on the right (repeat, or --alias-file)
    ... --alias SLMO2=PRELID3B --alias SRPR=SRPRA --alias ATP5B=ATP5F1B --min-cells 20 --force

A target with fewer than --min-cells cells in the screen (default 20) gets no row: the mean of a handful of cells
is mostly noise.

--modality names the screen's modality (docs/NORMAN_PLAN.md section 4 item 8): the file then records it, the
bundle manifest's modality and a top-level sign, -1 when the two differ (the Replogle CRISPRi screen for the CRISPRa
Norman bundle) and +1 when they agree or either is unknown, and its description leads with the modality and sign.
Without --modality the file is written exactly as before. Rows stay per target gene; a perturbation of several
genes is read as the sum of all its targets' rows, by the consumers.

    python tools/build_external_screen.py --h5ad ReplogleWeissman2022_K562_gwps.h5ad --bundle data/norman \\
        --name replogle2022_k562 --min-cells 20 --alias-file <table> --modality CRISPRi --dry-run

The knowledge file goes to <bundle>/knowledge/<name>.json; the lab's export_public copies it into a run's
public directory when the next run starts. The markdown report is rendered from the knowledge file alone, so
--from-json re-renders it without the h5ad.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genemila.data import external_screen as es  # noqa: E402

TOP_GENES = 5


def render_matching(info: dict, min_cells: int = 0) -> str:
    """The label matching of pass 0 (what --dry-run prints)."""
    m = info["match"]
    few = {t: n for t, n in info["n_cells_by_target"].items() if n < min_cells}
    am = info.get("aliases_matched") or {}
    L = [f"# Label matching: {info['h5ad'].name}", "",
         f"X is {info['layout']} with {info['shape'][0]:,} cells and {info['shape'][1]:,} genes; labels from "
         f"obs[{info['label_col']!r}] ({len(info['categories'])} distinct), gene symbols from var[{info['gene_col']!r}].",
         "",
         f"- control labels: {m['control']} ({info['n_control_cells']:,} cells)",
         f"- bundle targets found: {len(m['by_target'])} of {len(info['targets'])}",
         f"- bundle targets missing: {len(m['missing'])}" + (f": {', '.join(m['missing'])}" if m["missing"] else ""),
         f"- bundle genes measured: {info['n_measured']:,} of {len(info['genes']):,}",
         f"- labels naming two or more genes (skipped): {len(m['multi_gene'])}",
         f"- labels naming a bundle target plus an unrecognised token, possibly a second gene the screen did not "
         f"measure (ambiguous, skipped): {len(m['ambiguous'])}" + (f": {', '.join(m['ambiguous'])}" if m["ambiguous"] else ""),
         f"- other labels (no bundle target): {m['n_other']}",
         f"- aliases given: {len(info.get('aliases') or {})}"
         + (f"; targets matched through one: {', '.join(am['targets'])}" if am.get("targets") else "")
         + (f"; genes measured through one: {', '.join(am['genes'])}" if am.get("genes") else ""),
         f"- targets below --min-cells {min_cells} (no row would be written): {len(few)}"
         + (f": {', '.join(f'{t} ({n})' for t, n in few.items())}" if few else "")]
    if info.get("modality"):   # only with --modality, so a dry run without it prints what it always printed
        L.append(f"- modality: screen {info['modality']}, bundle {info.get('bundle_modality') or 'not recorded'}; "
                 f"sign {info['sign']:+d} would be written")
    L += ["", "| target | external labels | cells |", "|---|---|---|"]
    for t, labs in m["by_target"].items():
        L.append(f"| {t} | {', '.join(labs)} | {info['n_cells_by_target'][t]:,} |")
    return "\n".join(L) + "\n"


def _alias_sentence(src: dict, knowledge: dict) -> str:
    out = ""
    aliases = src.get("aliases") or {}
    if aliases:
        am = src.get("aliases_matched") or {}
        out += (f" Aliases (bundle symbol = screen symbol): {', '.join(f'{k}={v}' for k, v in sorted(aliases.items()))}; "
                f"targets matched through one: {', '.join(am.get('targets') or []) or 'none'}; genes measured through "
                f"one: {', '.join(am.get('genes') or []) or 'none'}.")
    few = knowledge.get("bundle_targets_below_min_cells") or {}
    if src.get("min_cells"):
        out += (f" Targets with fewer than {src['min_cells']} cells in the screen get no row: "
                + (", ".join(f"{t} ({n} cells)" for t, n in few.items()) if few else "none") + ".")
    return out


def _modality_sentence(src: dict, knowledge: dict) -> str:
    """Only for a file built with --modality (an older file renders as it always did)."""
    if not src.get("modality"):
        return ""
    sign = int(knowledge.get("sign", 1))
    out = (f" Screen modality {src['modality']}, bundle modality {src.get('bundle_modality') or 'not recorded'}: "
           f"sign {sign:+d}")
    if sign < 0:
        return out + (", since the two differ: a target's response in the bundle is expected to point against the "
                      "screen's, so a consumer multiplies a target's own delta by -1 before using it as that target's "
                      "predicted change (correlations between rows do not depend on the sign).")
    return out + "."


def _own_delta_note(src: dict) -> str:
    """What the target's own delta should be in the screen: a knockdown lowers it (every file before --modality, and
    a CRISPRi screen), an activation raises it."""
    if str(src.get("modality") or "").strip().lower() == "crispra":
        return "(an activation should be positive)"
    return "(a knockdown should be negative)"


def render(knowledge: dict) -> str:
    """A report for a scientist, rendered from the knowledge file alone (deterministic)."""
    src, genes = knowledge["source"], knowledge["genes"]
    measured = knowledge["measured"]
    n_meas = sum(measured)
    perts = knowledge["perts"]
    L = [f"# External screen {src['file']}", "",
         knowledge["description"], "",
         f"Source: {src['n_cells']:,} cells x {src['n_genes']:,} genes ({src['encoding']} X, "
         f"{src['size_bytes'] / 1e9:.2f} GB, md5 {src['md5'] or 'not computed'}), labels from obs[{src['label_col']!r}] "
         f"({src['n_labels']} distinct), gene symbols from var[{src['gene_col']!r}], built {src['date']} in "
         f"{src['seconds']:.0f} s. Control labels {src['control_labels']} ({knowledge['control']['n_cells']:,} cells); "
         f"{'raw counts normalised' if src['raw_counts'] else 'stored values used as they are'}: {src['normalisation']}."
         + _modality_sentence(src, knowledge),
         "",
         f"Bundle genes measured in the screen: {n_meas:,} of {len(genes):,}. Bundle targets with an external "
         f"response: {len(perts)}; missing: {len(knowledge['bundle_targets_missing'])}"
         + (f" ({', '.join(knowledge['bundle_targets_missing'])})" if knowledge["bundle_targets_missing"] else "")
         + f". Labels naming two or more genes were skipped: {src['n_labels_multi_gene_skipped']}; labels naming a bundle "
         f"target plus an unrecognised token were skipped as ambiguous: {src.get('n_labels_ambiguous_skipped', 0)}"
         + (f" ({', '.join(src['labels_ambiguous_skipped'])})" if src.get("labels_ambiguous_skipped") else "")
         + f"; labels matching no bundle target: {src['n_labels_other']}."
         + _alias_sentence(src, knowledge), "",
         "Per target: cells pooled, external labels pooled, mean absolute delta over the measured genes, the delta of "
         f"the target gene itself {_own_delta_note(src)}, and the largest absolute deltas.", "",
         "| target | cells | labels | mean abs delta | own delta | largest deltas |", "|---|---|---|---|---|---|"]
    gi = {g: i for i, g in enumerate(genes)}
    for t, p in perts.items():
        d = [(g, v) for g, v in zip(genes, p["delta"]) if v is not None]
        mean_abs = sum(abs(v) for _, v in d) / max(1, len(d))
        own = p["delta"][gi[t]] if t in gi else None
        top = sorted(d, key=lambda gv: -abs(gv[1]))[:TOP_GENES]
        L.append(f"| {t} | {p['n_cells']:,} | {', '.join(p['labels'])} | {mean_abs:.4f} | "
                 f"{'n/a' if own is None else f'{own:+.3f}'} | {', '.join(f'{g} {v:+.2f}' for g, v in top)} |")
    L += ["", "## Reading", "",
          "A target whose own delta is clearly negative was knocked down in the external screen as it was in the bundle; "
          "a target with a small mean absolute delta had little effect there, and transferring its response adds little. "
          "The deltas are differences within the external screen (its perturbed cells minus its own controls), so "
          "batch differences between the two screens cancel only to the extent they are additive in log space."
          + (f" The screen is {src['modality']} and the bundle {src.get('bundle_modality')}, so a target's own "
             "change in the bundle is expected to point against its delta here: the file's sign of -1 records that, "
             "and a perturbation of several genes is read as the sum of its targets' rows, present only when every "
             "target has one." if int(knowledge.get("sign", 1)) < 0 and src.get("modality") else "")]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--h5ad", help="external screen (scPerturb-style h5ad: raw counts in X, a label per cell in obs)")
    ap.add_argument("--bundle", help="bundle directory (public.npz, knowledge/targets.json)")
    ap.add_argument("--name", help="knowledge file name without .json (default external_<h5ad stem>)")
    ap.add_argument("--label-col", default=None, help="obs column with the perturbation label (default: detect)")
    ap.add_argument("--gene-col", default=None, help="var column with gene symbols (default: the index, or a symbol "
                                                      "column when the index holds Ensembl ids)")
    ap.add_argument("--control", nargs="+", default=None, help="control label(s); default: detect non-targeting labels")
    ap.add_argument("--chunk", type=int, default=None, help=f"cells per chunk for CSR and dense X (default "
                    f"{es.DEFAULT_CHUNK_ROWS}), genes per chunk for CSC X (default {es.DEFAULT_CHUNK_COLS})")
    ap.add_argument("--chunk-nnz", type=int, default=es.DEFAULT_CHUNK_NNZ,
                    help="stored values per chunk in every layout: a chunk shrinks below --chunk genes (CSC) or cells "
                         "(CSR, dense) when they hold more values than this; the memory bound on a small machine")
    ap.add_argument("--alias", action="append", default=[], metavar="OLD=NEW",
                    help="a bundle gene symbol and the screen's symbol for the same gene (a renamed gene); repeatable")
    ap.add_argument("--alias-file", default=None, help='JSON object {"OLD": "NEW"} of such aliases')
    ap.add_argument("--min-cells", type=int, default=20,
                    help="targets with fewer cells than this in the screen get no row (default 20)")
    ap.add_argument("--modality", default=None,
                    help="the screen's modality (e.g. CRISPRi): recorded in the file with the bundle manifest's "
                         "modality and a top-level sign, -1 when the two differ, else +1 (default: none, the file is "
                         "written as before)")
    ap.add_argument("--already-normalised", action="store_true", help="X is not raw counts: average it as stored")
    ap.add_argument("--no-md5", action="store_true", help="skip the md5 of the h5ad (saves one read of the file)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing knowledge file")
    ap.add_argument("--dry-run", action="store_true", help="print the label matching after pass 0 (obs only); write nothing")
    ap.add_argument("--report", default=None, help="write the markdown report here (it is always printed)")
    ap.add_argument("--from-json", default=None, help="re-render the report from an existing knowledge file; no h5ad needed")
    args = ap.parse_args(argv)

    if args.from_json:
        md = render(json.loads(Path(args.from_json).read_text()))
    else:
        if not args.h5ad or not args.bundle:
            ap.error("--h5ad and --bundle are required unless --from-json is given")
        h5ad, bundle = Path(args.h5ad), Path(args.bundle)
        name = args.name or f"external_{h5ad.stem}"
        aliases = es.parse_aliases(args.alias, args.alias_file)
        if args.dry_run:
            info = es.inspect(h5ad, bundle, args.label_col, args.gene_col, args.control, aliases)
            if args.modality and args.modality.strip():
                bundle_mod = es.bundle_modality(bundle)
                info.update(modality=args.modality.strip(), bundle_modality=bundle_mod,
                            sign=es.modality_sign(args.modality, bundle_mod))
            print(render_matching(info, args.min_cells))
            return 0
        out = es.build(h5ad, bundle, name, label_col=args.label_col, gene_col=args.gene_col, control=args.control,
                       chunk=args.chunk, chunk_nnz=args.chunk_nnz, already_normalised=args.already_normalised,
                       force=args.force, with_md5=not args.no_md5, aliases=aliases, min_cells=args.min_cells,
                       modality=args.modality)
        md = render(json.loads(out.read_text()))
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
