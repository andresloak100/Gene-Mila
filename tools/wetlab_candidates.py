#!/usr/bin/env python3
"""Pre-registered wet-lab prediction package (ROADMAP D13): where the model with a candidate feature and the parent
model without it disagree most, matched negatives where they agree, the expected effect per gene and a power statement.

Inputs are two frozen exports (tools/frozen_model.py, docs/FROZEN_EXPORT.md) that share one public context: the model
with the candidate feature and its parent; the candidate targets, from an eligibility manifest of
tools/replogle_slice_manifest.py (its eligible targets) or a plain list (one symbol per line, or a JSON list);
exclusion lists (a targets.json of every development bundle, a manifest's exclusions); and the public bundle (its
public.npz control cells and knowledge/targets.json), which must be the context the exports were fitted on. A target
that is in the frozen gene universe but appears as a target of any perturbation of the bundles (training, validation
or test alike), in any exclusion list, or among a manifest's excluded symbols is refused: every candidate is a
perturbation in no dataset the models saw.

Both models predict every candidate through tools/frozen_model.py's new-target path (predict_targets), and the
disagreement between the two predicted delta profiles is scored with the statistics fixed in docs/WETLAB_CANDIDATES.md.
The k candidates are the targets with the largest disagreement; the m matched negatives are targets of the same
expression decile of the target gene and the same membership class where the two models agree within tolerance, drawn
in the order of sha256(seed + newline + symbol). The power paragraph uses the per-gene standard deviation of the public
bundle's control cells and a given number of cells per condition to give the minimal detectable delta per gene for a
two-sample test at alpha 0.05 and power 0.8 (normal approximation; a planning number, not a guarantee).

This tool never reads expression responses of any candidate cohort. The only expression values it touches are the
public bundle's control cells; everything else is a frozen model's prediction. It accepts no response file: no h5ad,
no cohort means, no npz other than the public bundle's public.npz, and the candidate list may only be a manifest.json
of tools/replogle_slice_manifest.py, a .json list of symbols or a .txt file with one symbol per line. Nothing here
scores a model.

    python tools/wetlab_candidates.py --feature exports/g1_with_feature --feature-manifest-sha256 <hex> \\
        --parent exports/g1_parent --parent-manifest-sha256 <hex> --candidates manifest_dir/manifest.json \\
        --bundle data/adamson_cf_clean --exclude norman=data/norman_clean/knowledge/targets.json \\
        --seed '<public value named in the plan>' --cells 50 --out wetlab_package
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genemila.features.api import FeatureContext  # noqa: E402
from genemila.frozen import sha256  # noqa: E402
from tools.frozen_model import predict_targets  # noqa: E402
from tools.replogle_slice_manifest import load_symbols, rank_key  # noqa: E402

ALPHA, POWER = 0.05, 0.8
Z_SUM = float(norm.ppf(1 - ALPHA / 2) + norm.ppf(POWER))   # 2.80158...
RESPONSE_SUFFIXES = {".h5ad", ".h5", ".hdf5", ".loom", ".mtx", ".csv", ".tsv", ".npz", ".npy", ".pkl", ".parquet"}
POWER_FORMULA = (
    "minimal detectable delta per gene = (z_{1-alpha/2} + z_{power}) * sd_g * sqrt(2 / n), with alpha 0.05 two-sided "
    "(z 1.95996), power 0.8 (z 0.84162), sd_g the standard deviation of gene g over the public bundle's control cells "
    "(ddof 1, log-normalised expression) and n the cells per condition, both conditions with n cells and the same "
    "variance; the two-sample z approximation of the t-test. Cells per condition to detect a difference D at the same "
    "alpha and power = ceil(2 * ((z_{1-alpha/2} + z_{power}) * sd_g / |D|)^2). Planning numbers from control-cell "
    "noise: a perturbed condition can be noisier, cells are not independent of guide and batch, and the readout's own "
    "scale differs; they are not a guarantee.")


def load_candidates(path: Path) -> dict:
    """The candidate targets and what the source says about them. A manifest.json of tools/replogle_slice_manifest.py
    gives its eligible symbols, their membership class (in_distribution) and its excluded symbols; a .json file gives
    a list of symbols; a .txt file one symbol per line. Any other file is refused: no response file enters."""
    path = Path(path)
    if path.suffix.lower() in RESPONSE_SUFFIXES or path.suffix.lower() not in {".json", ".txt"}:
        raise ValueError(f"candidates must be a manifest.json, a .json list or a .txt list, never a data file: {path.name}")
    text = path.read_text()
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict) and data.get("tool") == "tools/replogle_slice_manifest.py":
            symbols = [t["symbol"] for t in data["targets"] if t["eligible"]]
            classes = {t["symbol"]: t.get("in_distribution") for t in data["targets"] if t["eligible"]}
            excluded = {t["symbol"] for t in data["targets"] if not t["eligible"]}
            return {"symbols": symbols, "classes": classes, "excluded": excluded, "kind": "manifest"}
        if not isinstance(data, list) or not all(isinstance(s, str) and s for s in data):
            raise ValueError("a JSON candidate list must be a list of symbols")
        symbols = list(data)
    else:
        symbols = [line.strip() for line in text.splitlines() if line.strip()]
    if len(set(symbols)) != len(symbols):
        raise ValueError("duplicate candidate symbol")
    return {"symbols": symbols, "classes": {s: None for s in symbols}, "excluded": set(), "kind": "list"}


def context_of(package: Path) -> FeatureContext:
    return FeatureContext(Path(package) / "context", cache_dir=None)


def bundle_targets(ctx: FeatureContext) -> set[str]:
    """Every target gene of every perturbation of the bundle: training, validation and test alike (targets.json
    covers every perturbation of the public context)."""
    return {g for genes in ctx._targets.values() for g in genes}


def refusals(symbols: list[str], universe: list[str], protected: dict[str, set[str]]) -> dict[str, list[str]]:
    """symbol -> the reasons it cannot be a candidate (empty for an admissible one)."""
    out = {}
    for s in symbols:
        reasons = [f"{name} target" for name, syms in protected.items() if s in syms]
        if s not in universe:
            reasons.append("outside the frozen gene universe")
        out[s] = reasons
    return out


def deciles(control_mean: np.ndarray) -> np.ndarray:
    """Expression decile of every gene: rank of its control mean (ascending, ties by gene order) times ten over the
    number of genes, floored, so decile 0 holds the lowest tenth and decile 9 the highest."""
    order = np.argsort(control_mean, kind="stable")
    rank = np.empty(len(order), dtype=int)
    rank[order] = np.arange(len(order))
    return np.minimum(9, (10 * rank) // len(order))


def pearson(a: np.ndarray, b: np.ndarray) -> float | None:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def disagreement(feature: np.ndarray, parent: np.ndarray, min_effect: float) -> dict:
    """The pre-registered statistics (docs/WETLAB_CANDIDATES.md): S is the set of genes where either model predicts
    |delta| at or above the minimum effect; l2 the Euclidean norm of the difference of the two predicted profiles
    over S; relative the l2 divided by the norm over S of the mean of the two profiles (0 when both are below the
    minimum everywhere, None when the mean profile is zero on S); pearson the correlation of the two full profiles
    over every gene (None when a profile is constant)."""
    f, p = np.asarray(feature, dtype=np.float64), np.asarray(parent, dtype=np.float64)
    s = (np.abs(f) >= min_effect) | (np.abs(p) >= min_effect)
    diff = f[s] - p[s]
    l2 = float(np.sqrt(np.sum(diff ** 2)))
    scale = float(np.sqrt(np.sum(((f[s] + p[s]) / 2) ** 2)))
    relative = 0.0 if l2 == 0 else (l2 / scale if scale > 0 else None)   # None: the mean profile is zero on S
    return {"l2": l2, "relative": relative, "pearson": pearson(f, p), "n_effect_genes": int(s.sum())}


def sign(delta: float, min_effect: float) -> str:
    return "up" if delta >= min_effect else "down" if delta <= -min_effect else "none"


def mde(sd: float, cells: int) -> float:
    return Z_SUM * sd * math.sqrt(2.0 / cells)


def cells_needed(sd: float, difference: float) -> int | None:
    if difference == 0:
        return None
    if sd == 0:
        return 1
    return int(math.ceil(2 * (Z_SUM * sd / abs(difference)) ** 2))


def gene_rows(genes: list[str], f: np.ndarray, p: np.ndarray, sd: np.ndarray, top_n: int, min_effect: float,
              cells: int) -> list[dict]:
    """The top-n genes by |delta_feature - delta_parent|, ties by gene order, each with both predicted deltas, their
    signs, the control sd, the minimal detectable delta at the given cells per condition, and the cells per condition
    that would detect the between-model difference."""
    diff = np.abs(np.asarray(f, dtype=np.float64) - np.asarray(p, dtype=np.float64))
    order = np.lexsort((np.arange(len(genes)), -diff))[:top_n]
    rows = []
    for j in order:
        fj, pj, sj = float(f[j]), float(p[j]), float(sd[j])
        rows.append({"gene": genes[j], "delta_feature": fj, "delta_parent": pj, "difference": fj - pj,
                     "sign_feature": sign(fj, min_effect), "sign_parent": sign(pj, min_effect),
                     "control_sd": sj, "min_detectable_delta": mde(sj, cells),
                     "cells_to_detect_difference": cells_needed(sj, fj - pj),
                     "detectable_feature": abs(fj) >= mde(sj, cells), "detectable_parent": abs(pj) >= mde(sj, cells)})
    return rows


def draw_negatives(candidates: list[str], pool: list[str], strata: dict[str, tuple], seed: str, m: int) -> list[dict]:
    """Round-robin over the candidates in rank order: each takes the first unused pool target of its stratum in the
    order of sha256(seed + newline + symbol), until m negatives are drawn or no stratum has a target left."""
    ordered = sorted(pool, key=lambda s: rank_key(seed, s))
    used: set[str] = set()
    out: list[dict] = []
    progress = True
    while len(out) < m and progress:
        progress = False
        for c in candidates:
            if len(out) >= m:
                break
            for s in ordered:
                if s not in used and strata[s] == strata[c]:
                    used.add(s)
                    out.append({"symbol": s, "matches_candidate": c})
                    progress = True
                    break
    return out


def build_package(feature: Path, feature_sha256: str, parent: Path, parent_sha256: str, candidates: dict,
                  protected: dict[str, set[str]], out: Path, *, k: int = 10, m: int = 10, top_n: int = 20,
                  min_effect: float = 0.1, agree_tolerance: float = 0.1, cells: int = 50, seed: str,
                  inputs_sha256: dict[str, str]) -> dict:
    out = Path(out)
    if out.exists():
        raise ValueError(f"{out} exists; packages are never overwritten")
    f_manifest = json.loads((Path(feature) / "manifest.json").read_text())
    p_manifest = json.loads((Path(parent) / "manifest.json").read_text())
    if f_manifest.get("anchor_sha256") != p_manifest.get("anchor_sha256") or f_manifest.get("genes") != p_manifest.get("genes"):
        raise ValueError("the two exports must share one public context (anchor_sha256 and genes differ)")
    ctx = context_of(feature)
    genes = ctx.genes
    protected = {"export context": bundle_targets(ctx), **protected}
    reasons = refusals(candidates["symbols"], genes, protected)
    refused = {s: r for s, r in reasons.items() if r}
    for s in candidates["symbols"]:
        if s in candidates["excluded"]:
            refused.setdefault(s, []).append("excluded by the eligibility manifest")
    if refused:
        raise ValueError("refused candidate targets: " + "; ".join(f"{s} ({', '.join(r)})" for s, r in sorted(refused.items())))
    symbols = list(candidates["symbols"])
    if len(symbols) < 2:
        raise ValueError("at least two candidate targets are needed (one candidate, one possible negative)")
    conditions = {s: [s] for s in symbols}
    out.mkdir(parents=True)
    try:
        pf = predict_targets(Path(feature), feature_sha256, conditions, out / "predictions" / "feature")
        pp = predict_targets(Path(parent), parent_sha256, conditions, out / "predictions" / "parent")
    except Exception:
        shutil.rmtree(out, ignore_errors=True)
        raise
    if pf["perts"] != symbols or pp["perts"] != symbols or pf["genes"] != genes or pp["genes"] != genes:
        raise ValueError("prediction order differs from the candidate list")
    control_mean = ctx.control_mean
    control_sd = ctx.control_cells.std(axis=0, ddof=1) if len(ctx.control_cells) > 1 else np.zeros(len(genes))
    decile = deciles(control_mean)
    scores = {s: disagreement(pf["delta"][i], pp["delta"][i], min_effect) for i, s in enumerate(symbols)}
    ranked = sorted(symbols, key=lambda s: (-scores[s]["l2"], s))
    chosen = ranked[:k]
    strata = {s: (int(decile[genes.index(s)]), candidates["classes"].get(s)) for s in symbols}
    pool = [s for s in ranked[k:] if scores[s]["relative"] is not None and scores[s]["relative"] <= agree_tolerance
            and scores[s]["n_effect_genes"] >= 1]
    negatives = draw_negatives(chosen, pool, strata, seed, m)
    index = {s: i for i, s in enumerate(symbols)}

    def row(s: str) -> dict:
        i = index[s]
        return {"symbol": s, "rank": ranked.index(s) + 1, "disagreement": scores[s],
                "control_mean_of_target": float(control_mean[genes.index(s)]), "expression_decile": strata[s][0],
                "membership_class": strata[s][1],
                "genes": gene_rows(genes, pf["delta"][i], pp["delta"][i], control_sd, top_n, min_effect, cells)}

    all_mde = mde(control_sd, cells)
    candidate_rows = [row(s) for s in chosen]
    negative_rows = [{**row(n["symbol"]), "matches_candidate": n["matches_candidate"]} for n in negatives]
    detectable = sum(1 for c in candidate_rows for g in c["genes"] if g["detectable_feature"] or g["detectable_parent"])
    package = {
        "schema_version": 1, "tool": "tools/wetlab_candidates.py", "roadmap": "D13",
        "parameters": {"k": k, "m": m, "top_n": top_n, "min_effect": min_effect, "agree_tolerance": agree_tolerance,
                       "cells_per_condition": cells, "alpha": ALPHA, "power": POWER, "seed": seed},
        "rules": {
            "candidates": "every candidate target is inside the frozen gene universe and absent from the targets of "
                          "every perturbation of the bundle (training, validation and test), from every exclusion "
                          "list and from the eligibility manifest's excluded symbols",
            "disagreement": "S = genes where either model predicts |delta| >= min_effect; l2 = Euclidean norm of "
                            "(delta_feature - delta_parent) over S; relative = l2 / norm over S of the mean profile; "
                            "pearson = correlation of the two full profiles; candidates are the k largest l2, ties by "
                            "symbol",
            "negatives": "targets outside the k candidates with relative <= agree_tolerance and at least one gene in S, "
                         "matched to a candidate on (expression decile of the target gene's control mean, membership "
                         "class), drawn round-robin over the candidates in rank order in ascending "
                         "sha256(seed + '\\n' + symbol)",
            "expression_decile": "rank of the gene's control mean among the universe (ascending, ties by gene order) "
                                 "times 10 over the number of genes, floored",
            "genes": "the top_n genes by |delta_feature - delta_parent|, ties by gene order",
            "power": POWER_FORMULA,
            "responses": "no expression response of any candidate cohort was read; the control cells of the public "
                         "bundle are the only expression values used"},
        "universe": {"n_genes": len(genes), "n_candidate_targets_scored": len(symbols),
                     "protected_targets": {k_: len(v) for k_, v in protected.items()},
                     "candidate_source": candidates["kind"]},
        "models": {"feature": {"manifest_sha256": feature_sha256, "members": pf["receipt"]["members"],
                               "predictions_sha256": pf["receipt"]["predictions_sha256"],
                               "query_sha256": pf["receipt"]["query_sha256"], "anchor_sha256": pf["receipt"]["anchor_sha256"]},
                   "parent": {"manifest_sha256": parent_sha256, "members": pp["receipt"]["members"],
                              "predictions_sha256": pp["receipt"]["predictions_sha256"],
                              "query_sha256": pp["receipt"]["query_sha256"], "anchor_sha256": pp["receipt"]["anchor_sha256"]}},
        "ranking": [{"symbol": s, **scores[s], "expression_decile": strata[s][0], "membership_class": strata[s][1]}
                    for s in ranked],
        "candidates": candidate_rows,
        "negatives": negative_rows,
        "negatives_shortfall": max(0, m - len(negatives)),
        "power": {"z_sum": Z_SUM, "cells_per_condition": cells,
                  "min_detectable_delta_median": float(np.median(all_mde)),
                  "min_detectable_delta_quartiles": [float(np.percentile(all_mde, 25)), float(np.percentile(all_mde, 75))],
                  "reported_genes_detectable": detectable,
                  "reported_genes": sum(len(c["genes"]) for c in candidate_rows)},
        "inputs_sha256": inputs_sha256,
    }
    text = json.dumps(package, indent=1, sort_keys=True, allow_nan=False) + "\n"
    (out / "candidates.json").write_text(text)
    package_sha = hashlib.sha256(text.encode()).hexdigest()
    (out / "candidates.md").write_text(render(package, package_sha))
    return package


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.4f}"


def _cls(value) -> str:
    return {None: "n/a", True: "in-distribution", False: "other"}[value]


def render(p: dict, package_sha256: str) -> str:
    q, w = p["parameters"], p["power"]
    lines = [
        "# Wet-lab candidate package (ROADMAP D13)", "",
        f"Pre-registered predictions of two frozen models on {p['universe']['n_candidate_targets_scored']} admissible "
        f"targets in no dataset the models saw: the model with the candidate feature (export manifest sha256 "
        f"{p['models']['feature']['manifest_sha256']}) and its parent ({p['models']['parent']['manifest_sha256']}). "
        f"Frozen gene universe: {p['universe']['n_genes']} genes. Candidate source: {p['universe']['candidate_source']}. "
        f"Protected target sets: " + ", ".join(f"{k} ({n})" for k, n in p["universe"]["protected_targets"].items()) + ".",
        "", f"Parameters: k {q['k']}, m {q['m']}, top_n {q['top_n']}, min_effect {q['min_effect']}, agree_tolerance "
        f"{q['agree_tolerance']}, cells per condition {q['cells_per_condition']}, seed {q['seed']!r}.", "",
        "Rules: " + " ".join(f"{k}: {v}." for k, v in p["rules"].items() if k != "power"), "",
        "## Candidates (largest disagreement first)", "",
        "| rank | target | l2 over S | relative | pearson | genes in S | decile | class |", "|---|---|---|---|---|---|---|---|"]
    for c in p["candidates"]:
        d = c["disagreement"]
        lines.append(f"| {c['rank']} | {c['symbol']} | {d['l2']:.4f} | {_fmt(d['relative'])} | "
                     f"{_fmt(d['pearson'])} | {d['n_effect_genes']} | {c['expression_decile']} | {_cls(c['membership_class'])} |")
    for c in p["candidates"]:
        lines += ["", f"### {c['symbol']}: top {len(c['genes'])} genes by |delta_feature - delta_parent|", "",
                  "| gene | delta with feature | sign | delta parent | sign | difference | control sd | MDE at n | cells to detect difference |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for g in c["genes"]:
            lines.append(f"| {g['gene']} | {g['delta_feature']:.4f} | {g['sign_feature']} | {g['delta_parent']:.4f} | "
                         f"{g['sign_parent']} | {g['difference']:.4f} | {g['control_sd']:.4f} | {g['min_detectable_delta']:.4f} | "
                         f"{g['cells_to_detect_difference'] if g['cells_to_detect_difference'] is not None else 'n/a'} |")
    lines += ["", f"## Matched negatives ({len(p['negatives'])} drawn, shortfall {p['negatives_shortfall']})", "",
              "| target | matches candidate | l2 over S | relative | pearson | genes in S | decile | class |",
              "|---|---|---|---|---|---|---|---|"]
    for n in p["negatives"]:
        d = n["disagreement"]
        lines.append(f"| {n['symbol']} | {n['matches_candidate']} | {d['l2']:.4f} | {_fmt(d['relative'])} | {_fmt(d['pearson'])} | "
                     f"{d['n_effect_genes']} | {n['expression_decile']} | {_cls(n['membership_class'])} |")
    lines += ["", "## Power", "",
              f"With {w['cells_per_condition']} cells per condition the median minimal detectable delta over the universe is "
              f"{w['min_detectable_delta_median']:.4f} (quartiles {w['min_detectable_delta_quartiles'][0]:.4f} and "
              f"{w['min_detectable_delta_quartiles'][1]:.4f}); {w['reported_genes_detectable']} of the {w['reported_genes']} "
              f"reported candidate genes have a predicted |delta| from either model at or above their gene's minimal "
              f"detectable delta. Formula: {p['rules']['power']}", "",
              "## Hashes (the deposit)", "", "| input | sha256 |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(p["inputs_sha256"].items())]
    lines += [f"| predictions.npz (feature) | {p['models']['feature']['predictions_sha256']} |",
              f"| queries.json (feature) | {p['models']['feature']['query_sha256']} |",
              f"| predictions.npz (parent) | {p['models']['parent']['predictions_sha256']} |",
              f"| queries.json (parent) | {p['models']['parent']['query_sha256']} |",
              f"| candidates.json | {package_sha256} |", "",
              p["rules"]["responses"][0].upper() + p["rules"]["responses"][1:] + "."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--feature", required=True, type=Path, help="frozen export of the model with the candidate feature")
    ap.add_argument("--feature-manifest-sha256", required=True)
    ap.add_argument("--parent", required=True, type=Path, help="frozen export of the parent model without it")
    ap.add_argument("--parent-manifest-sha256", required=True)
    ap.add_argument("--candidates", required=True, type=Path,
                    help="manifest.json of tools/replogle_slice_manifest.py, a .json list or a .txt list of symbols")
    ap.add_argument("--bundle", type=Path, default=None,
                    help="the public bundle directory (public.npz, knowledge/targets.json); must equal the exports' context")
    ap.add_argument("--exclude", action="append", default=[], metavar="NAME=PATH",
                    help="a targets.json, manifest.json or symbol list whose genes are refused, reason '<NAME> target'")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--m", type=int, default=10)
    ap.add_argument("--top-n", type=int, default=20)
    ap.add_argument("--min-effect", type=float, default=0.1)
    ap.add_argument("--agree-tolerance", type=float, default=0.1)
    ap.add_argument("--cells", type=int, default=50, help="cells per condition for the power statement")
    ap.add_argument("--seed", required=True, help="the public seed string of the plan, taken verbatim")
    ap.add_argument("--out", required=True, type=Path, help="new directory for candidates.json, candidates.md, predictions/")
    args = ap.parse_args(argv)
    if args.k < 1 or args.m < 0 or args.top_n < 1 or args.cells < 2 or args.min_effect < 0 or args.agree_tolerance < 0:
        ap.error("k >= 1, m >= 0, top-n >= 1, cells >= 2, min-effect >= 0 and agree-tolerance >= 0")
    try:
        inputs = {"feature manifest.json": args.feature_manifest_sha256, "parent manifest.json": args.parent_manifest_sha256,
                  f"candidates ({args.candidates.name})": sha256(args.candidates)}
        candidates = load_candidates(args.candidates)
        protected = {}
        for item in args.exclude:
            name, _, path = item.partition("=")
            if not name or not path or name in ("export context", "public bundle"):
                ap.error(f"--exclude takes NAME=PATH with a name of its own, got {item!r}")
            protected[name] = load_symbols(Path(path))
            inputs[f"exclude {name} ({Path(path).name})"] = sha256(Path(path))
        if args.bundle is not None:
            bundle = FeatureContext(args.bundle, cache_dir=None)
            ctx = context_of(args.feature)
            if bundle.genes != ctx.genes or not np.array_equal(bundle.control_cells, ctx.control_cells):
                raise ValueError("the public bundle's genes or control cells differ from the exports' context")
            protected["public bundle"] = {g for genes in bundle._targets.values() for g in genes}
            inputs["bundle public.npz"] = sha256(args.bundle / "public.npz")
            inputs["bundle knowledge/targets.json"] = sha256(args.bundle / "knowledge" / "targets.json")
        package = build_package(args.feature, args.feature_manifest_sha256, args.parent, args.parent_manifest_sha256,
                                candidates, protected, args.out, k=args.k, m=args.m, top_n=args.top_n,
                                min_effect=args.min_effect, agree_tolerance=args.agree_tolerance, cells=args.cells,
                                seed=args.seed, inputs_sha256=inputs)
    except (ValueError, KeyError, OSError) as exc:
        ap.exit(2, f"wet-lab candidates refused input: {exc}\n")
    print(f"{len(package['candidates'])} candidates, {len(package['negatives'])} matched negatives "
          f"(shortfall {package['negatives_shortfall']}) -> {args.out}; candidates.json sha256 "
          f"{sha256(args.out / 'candidates.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
