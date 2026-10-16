#!/usr/bin/env python3
"""Eligibility manifest of a candidate fresh-test cohort (ROADMAP D7), from its obs and var tables only.

For every perturbation label of an h5ad file this tool records the cell count, the symbol it maps to (a retired HGNC
symbol mapped to its current one when --hgnc is given), the exclusion reasons that apply (a target of a development
bundle, outside the frozen gene universe, fewer than --min-cells cells, a label naming several genes), whether the
target is eligible, and whether it is in-distribution: a member of at least one Reactome or CORUM class that holds a
target of the training panel (the clean bundle's gene_sets.json, tier-1 metadata only). With --draw and --seed it adds
the ordered random draw of the eligible targets: the rank key of a symbol is sha256(seed + "\\n" + symbol), so anyone
with the seed can check the order with sha256sum. Role "both" splits one file into two disjoint halves (alternating
ranks within the in-distribution and the other targets): R1 is the replication slice, R2 the fresh-test slice. Roles
"r1" and "r2" give the file's whole eligible set in draw order under that name, for two different source files.

The file is opened with h5py and only its obs and var groups can be touched: X, layers, obsm, raw and every other
key raise before any read. No expression value enters any choice. Nothing here scores a model.

    python tools/replogle_slice_manifest.py --h5ad ReplogleWeissman2022_K562_gwps.h5ad \\
        --exclude adamson=data/adamson_cf_clean/knowledge/targets.json \\
        --exclude norman=data/norman_clean/knowledge/targets.json \\
        --frozen-manifest /path/to/frozen_package/manifest.json \\
        --panel data/adamson_cf_clean/knowledge/targets.json \\
        --gene-sets data/adamson_cf_clean/knowledge/gene_sets.json \\
        --hgnc hgnc_complete_set.txt --draw --seed '<public value named in PLAN_R>' --role both --out manifest_dir
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genemila.data import external_screen as es  # noqa: E402
from genemila.data.real import CONTROL_LABELS, _LABEL_SPLIT  # noqa: E402
from tools.knowledge_coverage import hgnc_current  # noqa: E402

ALLOWED_GROUPS = ("obs", "var")
CLASS_PREFIXES = ("REACTOME:", "CORUM:")
ACCESS_STATEMENT = (
    "Physical access: the raw file was present on the orchestration machine (Andres's Mac) before this manifest was "
    "written, and the Norman development arms read a knowledge file built from it (replogle2022_k562.json, the "
    "responses of the development bundles' own targets, which this manifest excludes). This tool opened only the obs "
    "and var tables; no expression value of any candidate target was read for any choice here. The holder obtains the "
    "file from the public record, never from the Mac, and scores the deposited predictions once (docs/PLAN_R_FRESH_TEST.md).")


class ObsVarOnly:
    """An h5py file whose only reachable keys are obs and var."""

    def __init__(self, f):
        self._f = f

    def __getitem__(self, key):
        if key not in ALLOWED_GROUPS:
            raise PermissionError(f"this tool reads obs and var only; refused {key!r}")
        return self._f[key]

    def __contains__(self, key):
        return key in ALLOWED_GROUPS and key in self._f


def read_obs_var(h5ad: Path, label_col: str | None = None, gene_col: str | None = None) -> dict:
    """Labels with their cell counts, and the var symbols, through the obs/var guard."""
    import h5py
    with h5py.File(h5ad, "r") as raw:
        f = ObsVarOnly(raw)
        label_col, cats, codes = es.read_label_codes(f, label_col)
        gene_col, symbols = es.read_gene_symbols(f, gene_col)
    n_per_cat = np.bincount(codes[codes >= 0], minlength=len(cats))
    return {"label_col": label_col, "gene_col": gene_col, "n_cells": int(codes.shape[0]),
            "labels": {c: int(n) for c, n in zip(cats, n_per_cat.tolist())}, "var_symbols": symbols}


def load_symbols(path: Path) -> set[str]:
    """A targets.json (perturbation -> target genes) or a text file with one symbol per line."""
    text = Path(path).read_text()
    if text.lstrip().startswith("{"):
        return {str(g) for gs in json.loads(text).values() for g in gs}
    return {line.strip() for line in text.splitlines() if line.strip()}


def in_distribution_classes(gene_sets: dict, panel: set[str]) -> dict[str, list[str]]:
    """The Reactome and CORUM sets that hold at least one panel target, with those targets."""
    out = {}
    for name, members in gene_sets.items():
        if name.startswith(CLASS_PREFIXES):
            hit = sorted(panel & set(members))
            if hit:
                out[name] = hit
    return out


def retired_in_universe(universe: set[str], hgnc: dict) -> dict[str, set[str]]:
    """current symbol -> its retired symbols that the universe still uses (Adamson 2016 names SRPR, not SRPRA)."""
    back: dict[str, set[str]] = {}
    for old, news in hgnc["prev"].items():
        if old in universe:
            for new in news:
                back.setdefault(new, set()).add(old)
    return back


def map_symbol(raw: str, universe: set[str], hgnc: dict | None, back: dict | None = None) -> tuple[str, str | None]:
    """(symbol, note): the raw symbol itself when it is in the universe; a retired symbol mapped to its one current
    symbol; a current symbol mapped to the one retired symbol the universe uses for it; else the raw symbol.
    Aliases are never used: HGNC lets one alias stand for several genes."""
    if raw in universe or hgnc is None:
        return raw, None
    if raw in hgnc["approved"]:
        old = sorted((back or {}).get(raw, ()))
        if len(old) == 1:
            return old[0], f"current symbol mapped to the universe's retired symbol {old[0]}"
        if old:
            return raw, f"current symbol of several retired universe symbols ({', '.join(old)}); not mapped"
        return raw, None
    current = sorted(hgnc["prev"].get(raw, ()))
    if len(current) == 1:
        return current[0], f"retired symbol mapped to {current[0]}"
    if current:
        return raw, f"retired symbol of several genes ({', '.join(current)}); not mapped"
    return raw, None


def rank_key(seed: str, symbol: str) -> str:
    return hashlib.sha256(f"{seed}\n{symbol}".encode()).hexdigest()


def draw(eligible: list[dict], seed: str, role: str) -> dict:
    ordered = sorted(eligible, key=lambda t: rank_key(seed, t["symbol"]))
    out = {"seed": seed, "role": role, "derivation": "ascending sha256(seed + '\\n' + symbol), hex",
           "ranked": [t["symbol"] for t in ordered]}
    if role == "both":
        r1, r2 = [], []
        for group in (True, False):
            for i, t in enumerate(x for x in ordered if bool(x["in_distribution"]) is group):
                (r1 if i % 2 == 0 else r2).append(t["symbol"])
        out["r1"], out["r2"] = r1, r2
        out["split"] = "alternating ranks within the in-distribution targets and within the rest; R1 takes rank 0"
    else:
        out[role] = out["ranked"]
    return out


def build_manifest(h5ad: Path, excluded: dict[str, set[str]], universe: list[str], *, min_cells: int = 20,
                   hgnc: dict | None = None, gene_sets: dict | None = None, panel: set[str] | None = None,
                   label_col: str | None = None, gene_col: str | None = None, control: list[str] | None = None,
                   seed: str | None = None, role: str = "both", h5ad_sha256: str | None = None) -> dict:
    info = read_obs_var(h5ad, label_col, gene_col)
    controls = {c.lower() for c in (control or CONTROL_LABELS)}
    universe_set = set(universe)
    back = retired_in_universe(universe_set, hgnc) if hgnc else None
    classes = in_distribution_classes(gene_sets, panel) if gene_sets is not None and panel is not None else None
    by_symbol: dict[str, dict] = {}
    for label, n in info["labels"].items():
        if label.strip().lower() in controls:
            continue
        tokens = [t for t in _LABEL_SPLIT.split(label.strip()) if t]
        multi = len(tokens) != 1
        raw = label.strip() if multi else tokens[0]
        symbol, note = (raw, None) if multi else map_symbol(raw, universe_set, hgnc, back)
        row = by_symbol.setdefault(symbol, {"symbol": symbol, "labels": [], "raw_symbols": [], "cells": 0,
                                            "mapping": note, "multi_gene_label": multi})
        row["labels"].append(label)
        row["raw_symbols"].append(raw)
        row["cells"] += n
    targets = []
    for symbol in sorted(by_symbol):
        row = by_symbol[symbol]
        names = {symbol, *row["raw_symbols"]}
        reasons = [f"{name} target" for name, syms in excluded.items() if names & syms]
        if symbol not in universe_set and not row["multi_gene_label"]:
            reasons.append("outside the frozen gene universe")
        if row["cells"] < min_cells:
            reasons.append(f"fewer than {min_cells} cells")
        if row["multi_gene_label"]:
            reasons.append("label names more than one gene")
        row["excluded"] = reasons
        row["eligible"] = not reasons
        if classes is None:
            row["in_distribution"], row["classes"] = None, []
        else:
            row["classes"] = sorted(c for c, _ in classes.items() if symbol in set(gene_sets[c]))
            row["in_distribution"] = bool(row["classes"])
        targets.append(row)
    eligible = [t for t in targets if t["eligible"]]
    counts = {"labels": len(info["labels"]), "targets": len(targets), "eligible": len(eligible),
              "eligible_in_distribution": sum(1 for t in eligible if t["in_distribution"]),
              "eligible_other": sum(1 for t in eligible if t["in_distribution"] is False),
              "by_reason": {}}
    for t in targets:
        for r in t["excluded"]:
            counts["by_reason"][r] = counts["by_reason"].get(r, 0) + 1
    control_cells = sum(n for c, n in info["labels"].items() if c.strip().lower() in controls)
    # The scoring panel: universe genes the cohort measures, var symbols mapped like the targets (metadata only).
    measured = {map_symbol(s, universe_set, hgnc, back)[0] for s in info["var_symbols"]}
    panel_genes = [g for g in universe if g in measured]
    manifest = {"schema_version": 1, "tool": "tools/replogle_slice_manifest.py", "roadmap": "D7",
                "h5ad": {"name": Path(h5ad).name, "bytes": Path(h5ad).stat().st_size, "sha256": h5ad_sha256,
                         "label_col": info["label_col"], "gene_col": info["gene_col"], "n_cells": info["n_cells"],
                         "n_var": len(info["var_symbols"]), "control_cells": control_cells,
                         "read": "obs and var only"},
                "rules": {"min_cells": min_cells, "excluded_sets": {k: len(v) for k, v in excluded.items()},
                          "gene_universe_size": len(universe), "hgnc": hgnc is not None,
                          "in_distribution": "member of a Reactome or CORUM class holding a training-panel target"
                          if classes is not None else None,
                          "panel_size": len(panel) if panel is not None else None},
                "in_distribution_classes": classes, "counts": counts, "targets": targets,
                "common_gene_panel": {"n": len(panel_genes), "genes": panel_genes,
                                      "definition": "frozen universe genes the cohort measures, in universe order"},
                "access_statement": ACCESS_STATEMENT}
    if seed is not None:
        manifest["draw"] = draw(eligible, seed, role)
    return manifest


def render(m: dict) -> str:
    c, h = m["counts"], m["h5ad"]
    lines = [f"# Fresh-test eligibility manifest: {h['name']}", "",
             f"{h['n_cells']:,} cells, {h['n_var']:,} measured genes; labels from obs[{h['label_col']!r}] "
             f"({c['labels']} distinct, {h['control_cells']:,} control cells); gene symbols from var[{h['gene_col']!r}]. "
             f"Only obs and var were read. File sha256: {h['sha256'] or 'not given'}.", "",
             f"Targets: {c['targets']}. Eligible: {c['eligible']} (in-distribution {c['eligible_in_distribution']}, "
             f"other {c['eligible_other']}). Rules: at least {m['rules']['min_cells']} cells; not a target of "
             + ", ".join(f"{k} ({n})" for k, n in m["rules"]["excluded_sets"].items())
             + f"; inside the frozen gene universe ({m['rules']['gene_universe_size']} genes); HGNC mapping "
             f"{'on' if m['rules']['hgnc'] else 'off'}. Common gene panel for scoring: {m['common_gene_panel']['n']} "
             f"universe genes the cohort measures.", "", "| exclusion reason | targets |", "|---|---|"]
    lines += [f"| {r} | {n} |" for r, n in sorted(c["by_reason"].items())] or ["| (none) | 0 |"]
    if m["in_distribution_classes"] is not None:
        lines += ["", f"In-distribution classes: {len(m['in_distribution_classes'])} Reactome or CORUM sets holding "
                  f"a target of the {m['rules']['panel_size']}-target training panel."]
    if "draw" in m:
        d = m["draw"]
        lines += ["", f"Draw: seed {d['seed']!r}; rank key {d['derivation']}; role {d['role']}."]
        for key in ("r1", "r2"):
            if key in d:
                lines.append(f"- {key.upper()} ({len(d[key])}): {', '.join(d[key])}")
    lines += ["", "| symbol | labels | cells | mapping | excluded | in-distribution |", "|---|---|---|---|---|---|"]
    for t in m["targets"]:
        ind = {None: "n/a", True: "yes", False: "no"}[t["in_distribution"]]
        lines.append(f"| {t['symbol']} | {', '.join(t['labels'])} | {t['cells']} | {t['mapping'] or ''} | "
                     f"{'; '.join(t['excluded']) or 'eligible'} | {ind} |")
    lines += ["", m["access_statement"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--h5ad", required=True, type=Path)
    ap.add_argument("--h5ad-sha256", default=None, help="the file's sha256, computed elsewhere, to record")
    ap.add_argument("--exclude", action="append", default=[], metavar="NAME=PATH",
                    help="a targets.json or symbol list whose genes are excluded, reason '<NAME> target'")
    ap.add_argument("--frozen-manifest", required=True, type=Path, help="frozen export manifest.json (its genes)")
    ap.add_argument("--panel", type=Path, help="training panel targets.json for the in-distribution subset")
    ap.add_argument("--gene-sets", type=Path, help="the clean bundle's knowledge/gene_sets.json")
    ap.add_argument("--hgnc", type=Path, help="HGNC complete set, tab-separated, to map retired symbols")
    ap.add_argument("--min-cells", type=int, default=20)
    ap.add_argument("--label-col", default=None)
    ap.add_argument("--gene-col", default=None)
    ap.add_argument("--control", action="append", default=None, help="control label(s); default: the ingest's")
    ap.add_argument("--draw", action="store_true", help="add the random draw (needs --seed)")
    ap.add_argument("--seed", default=None, help="the public seed string named in PLAN_R, taken verbatim")
    ap.add_argument("--role", choices=("both", "r1", "r2"), default="both")
    ap.add_argument("--out", required=True, type=Path, help="new directory for manifest.json and manifest.md")
    args = ap.parse_args(argv)
    if args.draw and args.seed is None:
        ap.error("--draw needs --seed")
    if (args.panel is None) != (args.gene_sets is None):
        ap.error("--panel and --gene-sets go together")
    if args.out.exists():
        ap.error(f"{args.out} exists; manifests are never overwritten")
    excluded = {}
    for item in args.exclude:
        name, _, path = item.partition("=")
        if not name or not path:
            ap.error(f"--exclude takes NAME=PATH, got {item!r}")
        excluded[name] = load_symbols(Path(path))
    universe = json.loads(args.frozen_manifest.read_text())["genes"]
    manifest = build_manifest(
        args.h5ad, excluded, universe, min_cells=args.min_cells,
        hgnc=hgnc_current(args.hgnc) if args.hgnc else None,
        gene_sets=json.loads(args.gene_sets.read_text()) if args.gene_sets else None,
        panel=load_symbols(args.panel) if args.panel else None, label_col=args.label_col, gene_col=args.gene_col,
        control=args.control, seed=args.seed if args.draw else None, role=args.role, h5ad_sha256=args.h5ad_sha256)
    args.out.mkdir(parents=True)
    text = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    (args.out / "manifest.json").write_text(text)
    (args.out / "manifest.md").write_text(render(manifest))
    c = manifest["counts"]
    print(f"{c['targets']} targets, {c['eligible']} eligible ({c['eligible_in_distribution']} in-distribution) -> "
          f"{args.out}; manifest.json sha256 {hashlib.sha256(text.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
