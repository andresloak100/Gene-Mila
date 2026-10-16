#!/usr/bin/env python3
"""Residual mining on training folds: what does the current model miss, and does any public description of the
targets or the genes explain it? (docs/NOVEL_FEATURE_NEEDS.md, M1; claim issue #41.)

Hypothesis generation only. The next knowledge source should be chosen from evidence about where the model fails,
and that evidence must come from the training perturbations scored out of fold, never from the held-out sets:
choosing a source on a held-out failure list would make every later number on that set a tuned one (the planner's
visible worst-5 list has exactly this problem, docs/NOVEL_FEATURE_NEEDS.md section 2.1). So this tool refits the parent
model of tools/feature_compare.py on its out-of-fold folds, with its honest alpha rule (chosen on one fold seed's OOF
score, reported on another), keeps the out-of-fold predictions and asks three questions of the residuals:

  (a) which training perturbations score worst, and do they lack close relatives among the other training targets by
      the three public measures a similarity feature can use (gene-set membership, STRING partners, control-cell
      co-expression)? A rank correlation of the score with each measure tests "targets without neighbours score
      worse"; a target with no gene set and no partner may be a retired symbol (R0) rather than missing biology;
  (b) which genes carry the squared residual, and does it follow control expression, its spread, or a column of
      knowledge/gene_annotation.json? A per-gene property the model lacks shows up as a correlated residual;
  (c) is the residual matrix (perturbations x genes) low-rank, one shared program the features do not carry, or
      diffuse? Measured by the variance its first five singular components explain, against the same shares after
      each gene's residuals are permuted across perturbations, which keeps per-gene variance and destroys shared
      structure.

Nothing here is evidence: every perturbation and gene named is one the NEXT source should help with, and that help is
then tested by tools/feature_compare.py on its own folds. Reads the training labels (public.npz) and knowledge/ only,
through feature_compare's public copy; the held-out labels, the split file and the oracle are never touched. The parent
is feature_compare's (the built-in start, or a run's selected single model with its recorded feature params), its
blocks computed in feature_compare's limited "_blocks" child process; this process only fits ridge in closed form.

    python tools/residual_mining.py --data data/adamson --out out/rm
    python tools/residual_mining.py --data data/norman --out out/rm --parent-run <run_dir> --top 20
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import feature_compare as fc  # noqa: E402  (public copy, parent run, folds, child blocks, honest ridge scoring)
from genemila import sandbox  # noqa: E402
from genemila.benchmark.evaluator import categories_of  # noqa: E402
from genemila.features.registry import BUILTIN_FEATURES  # noqa: E402

MEASURES = {"gene_sets": "Jaccard of the gene-set memberships of the targets (knowledge/gene_sets.json)",
            "ppi": "Jaccard of the targets' STRING partner sets, each target counted among its own partners so a "
                   "direct interaction counts (knowledge/ppi_network.json; scores ignored)",
            "coexpr": "largest |r| over control cells between a measured target and another perturbation's "
                      "(ctx.gene_corr)"}
HEADER = ("Hypothesis generation on training folds only. Nothing in this file is evidence and none of it may be cited "
          "as a result: the parent model was refitted out of fold on the training perturbations, whose labels every "
          "feature has already seen. The perturbations and genes named are those the NEXT knowledge source should "
          "help with; whether it does is tested by tools/feature_compare.py. No held-out label was read.")
N_COMPONENTS = 5
NULL_REPS = 5


# ================================================================== the parent and its out-of-fold predictions
def parent_model(a, data: fc.Data, work: Path, pub: Path, pr: dict | None) -> tuple[list[str], dict, dict, dict]:
    """The parent exactly as feature_compare.run builds it (its lines are copied here because they sit inside run()):
    the built-ins, or a run's selected model with its guard-passing plugin files; the blocks come from
    feature_compare's limited "_blocks" child, every feature recomputed in every fold view."""
    pdir = work / "parent" / "exec"
    pdir.mkdir(parents=True)
    files = {}
    if pr:
        feats, params = pr["features"], {f: dict(v) for f, v in pr["params"].items()}
        for f in sorted((Path(a.parent_run) / "feature_store").glob("*.py")):
            files[f.stem] = fc.static_check(f, data, imported=True, enforce_literal=False)
        fc.copy_files([Path(c["file"]) for c in files.values() if c["status"] == "ok"], pdir)
    else:
        feats, params = list(BUILTIN_FEATURES) + (["additive_response"] if data.pair_ids else []), {}
    res = fc.run_child(work / "parent" / "blocks", pub, pdir, feats, params, a)
    if "failed" in res or res["errors"]:
        raise fc.Unusable(f"the parent cannot be computed: {res.get('failed') or res['errors']}")
    return feats, params, files, res


# ================================================================== (a) perturbations and their relatives
def target_similarity(data: fc.Data) -> tuple[dict, dict]:
    """Per training perturbation: the largest similarity of its targets to any other training perturbation's by each
    MEASURE, in [0, 1], with the nearest perturbation, and its knowledge coverage (gene sets, partners). A measure
    whose knowledge file the bundle lacks is None. Memberships and edges only, so a perturbation whose targets have no
    annotation scores 0 against everyone: the coverage counts say when that is the reason."""
    ctx, train = data.ctx, data.train
    sets, ppi = ctx.knowledge("gene_sets"), ctx.knowledge("ppi_network")
    member, partner = defaultdict(set), defaultdict(set)
    for name, genes in (sets or {}).items():
        for g in genes:
            member[g].add(name)
    for x, y, *_ in ppi or []:
        partner[x].add(y)
        partner[y].add(x)
    prof = {p: (set().union(*(member[g] for g in data.genes_of[p])),
                set(data.genes_of[p]) | set().union(*(partner[g] for g in data.genes_of[p])),
                data.tidx[p]) for p in train}

    def jac(x, y):
        return len(x & y) / len(x | y) if x | y else 0.0

    def coex(i, j):
        return float(np.abs(ctx.gene_corr[np.ix_(i, j)]).max()) if i and j else 0.0

    fns = {"gene_sets": (lambda p, q: jac(prof[p][0], prof[q][0])) if sets is not None else None,
           "ppi": (lambda p, q: jac(prof[p][1], prof[q][1])) if ppi is not None else None,
           "coexpr": lambda p, q: coex(prof[p][2], prof[q][2])}
    rows = {}
    for p in train:
        row = {"n_gene_sets": len(prof[p][0]), "n_ppi_partners": len(prof[p][1] - set(data.genes_of[p]))}
        for m, fn in fns.items():
            if fn is None:
                row[f"sim_{m}"] = row[f"nearest_{m}"] = None
                continue
            best = max(((fn(p, q), q) for q in train if q != p), default=(0.0, None))
            row[f"sim_{m}"] = min(1.0, max(0.0, best[0]))
            row[f"nearest_{m}"] = best[1] if best[0] > 0 else None  # nothing in common with anyone: no nearest
        rows[p] = row
    return rows, {m: fn is not None for m, fn in fns.items()}


def screen_rows(public: Path) -> dict[str, set[str]]:
    """Every knowledge file with a "perts" dict (an external screen, as tools/knowledge_coverage.py reads them) and the
    names it has rows for."""
    out = {}
    for path in sorted((public / "knowledge").glob("*.json")):
        obj = json.loads(path.read_text())
        if isinstance(obj, dict) and isinstance(obj.get("perts"), dict):
            out[path.stem] = set(map(str, obj["perts"]))
    return out


def perturbation_table(tm: dict, data: fc.Data, sims: dict, screens: dict, cats: dict | None) -> list[dict]:
    """One row per training perturbation, worst OOF pearson_delta first (rank 1 = worst)."""
    rows = []
    for p in data.train:
        per = tm["per_pert"][p]
        rows.append({"pert": p, "category": cats.get(p) if cats else None,
                     "oof_pearson_delta": per["pearson_delta"],
                     "oof_pearson_delta_nontarget": per["pearson_delta_nontarget"], "oof_mse_top": per["mse_top"],
                     "n_targets": len(data.ctx.target_genes(p)), "n_targets_measured": len(data.tidx[p]), **sims[p],
                     "screen_rows": {n: bool(names & (data.genes_of[p] | {p})) for n, names in screens.items()}})
    rows.sort(key=lambda r: (r["oof_pearson_delta"], r["pert"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def spearman(x, y) -> dict:
    """Spearman rank correlation over the finite pairs (None counts as missing); n only below 3 pairs or when a side
    is constant. Ranks, because squared residuals are heavy-tailed and the similarity measures are bounded."""
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.ptp(x[ok]) == 0 or np.ptp(y[ok]) == 0:
        return {"n": int(ok.sum())}
    rho, p = spearmanr(x[ok], y[ok])[:2]
    return {"rho": float(rho), "p": float(p), "n": int(ok.sum())}


# ================================================================== (b) genes
def gene_table(E: np.ndarray, msr: np.ndarray, data: fc.Data, top: int) -> dict:
    """Per gene: the mean squared OOF residual (msr) and its rank correlation with the control mean, the control
    standard deviation and every numeric column of knowledge/gene_annotation.json when the bundle has one (a null value
    is missing); the --top genes by msr with their share of the total, their signed mean residual (bias: a gene the
    model always under- or over-predicts) and how many training perturbations target them."""
    ctx = data.ctx
    corr = {"control_mean": spearman(msr, data.cm), "control_std": spearman(msr, ctx.control_std)}
    ann = ctx.knowledge("gene_annotation")
    cols = list(ann.get("columns") or []) if isinstance(ann, dict) and isinstance(ann.get("genes"), dict) else []
    for j, col in enumerate(cols):
        vals = [ann["genes"].get(g) for g in ctx.genes]
        corr[f"gene_annotation.{col}"] = spearman(msr, [v[j] if v and len(v) > j else None for v in vals])
    targeted = Counter(g for p in data.train for g in data.genes_of[p])
    total = max(float(msr.sum()), 1e-300)
    rows = [{"gene": ctx.genes[i], "msr": float(msr[i]), "share": float(msr[i] / total), "bias": float(E[:, i].mean()),
             "control_mean": float(data.cm[i]), "control_std": float(ctx.control_std[i]),
             "n_train_targeting": targeted[ctx.genes[i]]} for i in np.argsort(-msr, kind="stable")[:top]]
    return {"n_genes": ctx.n_genes, "annotation_columns": cols, "correlations": corr, "top": rows}


# ================================================================== (c) structure
def residual_structure(E: np.ndarray, data: fc.Data, top: int) -> dict:
    """The share of the residual matrix's variance that each of its first N_COMPONENTS singular components explains,
    against the mean share over NULL_REPS permutations of every gene's residuals across perturbations (seed 0): a
    component above twice its permuted share is more structure than independent per-gene noise would give. For the
    first two components, the genes and perturbations with the largest loadings (SVD signs are arbitrary: read a
    component's gene and perturbation signs together)."""
    U, s, Vt = np.linalg.svd(E, full_matrices=False)
    share = (s ** 2 / (s ** 2).sum())[:N_COMPONENTS]
    rng = np.random.default_rng(0)
    null = []
    for _ in range(NULL_REPS):
        t = np.linalg.svd(rng.permuted(E, axis=0), compute_uv=False)
        null.append((t ** 2 / (t ** 2).sum())[:N_COMPONENTS])
    null = np.mean(null, axis=0)
    comps = []
    for i in range(min(2, len(s))):
        comps.append({"component": i + 1, "share": float(share[i]), "null_share": float(null[i]),
                      "genes": [[data.ctx.genes[j], float(Vt[i, j])] for j in np.argsort(-np.abs(Vt[i]))[:top]],
                      "perts": [[data.train[j], float(U[j, i] * s[i])] for j in np.argsort(-np.abs(U[:, i]))[:top]]})
    low = bool(share[0] > 2 * null[0])
    return {"n_components": int(len(share)), "share": share.tolist(), "null_share": null.tolist(),
            "cumulative": np.cumsum(share).tolist(), "null_reps": NULL_REPS, "low_rank": low,
            "reading": ("low-rank: component 1 explains more than twice its permuted share, a shared program the "
                        "features do not carry" if low else
                        "diffuse: component 1 explains at most twice its permuted share"),
            "components": comps}


# ================================================================== the run
def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="bundle or public directory (public.npz, knowledge/)")
    ap.add_argument("--out", required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--parent", choices=["builtin"], default="builtin")
    g.add_argument("--parent-run", help="finished run: its selected single model is the parent")
    ap.add_argument("--fold-seeds", default="101,102,103")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--groups", choices=["auto", "none", "gene"], default="auto")
    ap.add_argument("--alpha-rule", choices=["honest"], default="honest",
                    help="alpha chosen on one fold seed's OOF score and reported on another (feature_compare.score)")
    ap.add_argument("--top", type=int, default=30, help="rows of the worst perturbations and of the top genes shown")
    ap.add_argument("--timeout-s", type=float, default=1800)
    ap.add_argument("--ram-mb", type=float, default=8192)
    a = ap.parse_args(argv)
    a.seeds = list(dict.fromkeys(int(s) for s in a.fold_seeds.split(",") if s.strip()))
    if not a.seeds or a.k < 2 or a.top < 1:
        raise fc.Unusable("need at least one fold seed, --k >= 2 and --top >= 1")
    a.alphas = fc.alpha_grid()
    a.with_val1 = False  # read by feature_compare.run_child's job record; this tool never scores held-out labels
    return a


def main(argv=None) -> int:
    try:
        return run(parse(argv))
    except fc.Unusable as exc:
        print(f"residual_mining: {exc}", file=sys.stderr)
        return 2


def run(a) -> int:
    t0 = time.perf_counter()
    data_dir, out_dir = Path(a.data), Path(a.out)
    with tempfile.TemporaryDirectory(prefix="residual_mining_") as tmp:
        work = Path(tmp)
        pub = work / "public"
        manifest = fc.public_copy(data_dir, pub)  # refuses a directory without public.npz and knowledge/targets.json
        data = fc.make_data(pub)
        pr = fc.read_selected(Path(a.parent_run)) if a.parent_run else None
        if pr:
            fc.same_split(pr, manifest, "the parent run")
        a.groups = fc.resolve_groups(a.groups, data, manifest, pr["cv_groups"] if pr else None)
        feats, params, files, res = parent_model(a, data, work, pub, pr)
        data.folds = {s: [{"predict": fd["predict"], "rows": fd["rows"]} for fd in fs]
                      for s, fs in res["folds"].items()}
        fixed = [(res, feats, None)]
        sc = fc.score(fixed, data, a.seeds, a.alphas)
        tm = fc.tier_metrics(sc, data, "oof")
        n_columns = int(fc.design(fixed, ("full",)).shape[2])
        sims, have = target_similarity(data)
        screens = screen_rows(pub)
        targets = {p: data.ctx.target_genes(p) for p in data.ctx.perts}
        cats = categories_of(data.train, targets, data.train) if data.pair_ids else None
        preds = sc["oof"]["preds"]
        E = data.Y - np.mean(preds, axis=0)                              # mean residual over the reports
        msr = np.mean([(data.Y - P) ** 2 for P in preds], axis=(0, 1))   # per gene, over reports and perturbations
        rows = perturbation_table(tm, data, sims, screens, cats)
        genes = gene_table(E, msr, data, a.top)
        structure = residual_structure(E, data, min(a.top, 10))
        record = fc.data_record(data_dir, manifest)
    score = [r["oof_pearson_delta"] for r in rows]
    corr = {m: spearman(score, [r[f"sim_{m}"] for r in rows]) if have[m] else None for m in MEASURES}
    honest = len(a.seeds) > 1
    caveats = [fc.OOF_CAVEAT + "; hypothesis generation, never evidence",
               "ridge on feature_compare's alpha grid with its honest OOF alpha; a parent run's own model type and "
               "alpha are not reused",
               "similarity measures use memberships and edges only (gene-set sizes and STRING scores ignored); a "
               "target with no gene set and no partner may be a retired symbol (docs/NOVEL_FEATURE_NEEDS.md, R0)",
               "the structure null permutes genes independently, so it tests shared structure, not the size of the "
               "residual"]
    if not honest:
        caveats.append("one fold seed: alpha chosen and reported on the same OOF predictions (not honest)")
    result = {
        "tool": "residual_mining", "format": 1, "lab_commit": fc._commit(), "header": HEADER,
        "data": record, "split_id": manifest.get("split_id"),
        "settings": {"model": "ridge", "alphas": a.alphas, "alpha_rule": "honest_oof", "honest": honest,
                     "fold_seeds": a.seeds, "k": a.k, "groups": a.groups, "top": a.top,
                     "reports": sc["oof"]["reports"], "labels_read": ["training labels (public.npz)"],
                     "measures": MEASURES, "measures_available": have, "screens": sorted(screens),
                     "timeout_s": a.timeout_s, "ram_mb": a.ram_mb},
        "caveats": caveats,
        "parent": {"source": pr["run"] if pr else "builtin",
                   **({"run_id": pr["run_id"], "split_id": pr["split_id"], "experiment_id": pr["experiment_id"]}
                      if pr else {}),
                   "features": feats, "params": params, "n_columns": n_columns, "files": files,
                   "n_train": len(data.train), "metrics": tm["metrics"]},
        "per_perturbation": rows, "similarity_correlation": corr, "per_gene": genes, "structure": structure,
        "wall_s": round(time.perf_counter() - t0, 1),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "residual_mining.json").write_text(json.dumps(result, indent=1, default=float))
    (out_dir / "residual_mining.md").write_text(markdown(result))
    print(f"residual_mining: {len(rows)} training perturbations -> {out_dir / 'residual_mining.md'}")
    return 0


# ================================================================== the report
def _sim(r: dict, m: str) -> str:
    if r[f"sim_{m}"] is None:
        return ""
    return f"{r[f'sim_{m}']:.2f}" + (f" ({r[f'nearest_{m}']})" if r[f"nearest_{m}"] else "")


def _corr(c: dict | None) -> str:
    return "file absent" if c is None else (f"{c['rho']:+.3f} (p {c['p']:.3f}, n {c['n']})" if "rho" in c
                                            else f"n {c['n']}: too few or constant")


def markdown(r: dict) -> str:
    s, p, dd, st = r["settings"], r["parent"], r["data"], r["structure"]
    L = [f"# Residual mining: {dd['name']}", "", f"**{HEADER}**", "",
         f"- data: `{dd['name']}`" + (f", split `{r['split_id']}`" if r["split_id"] else "")
         + f", knowledge added after the build: {', '.join(dd['added_knowledge'] or []) or 'none'}"
         + f" (public.npz sha256 {dd['sha256']['public.npz'][:12]}); lab commit `{r['lab_commit']}`",
         f"- parent: `{p['source']}`" + (f" ({p['experiment_id']})" if p.get("experiment_id") else "")
         + f", {len(p['features'])} features, {p['n_columns']} columns: {', '.join(p['features'])}; "
         f"{p['n_train']} training perturbations, mean OOF pearson_delta {p['metrics']['pearson_delta']:.4f}",
         f"- fold seeds {s['fold_seeds']}, k = {s['k']}, groups {s['groups']}; ridge, alpha grid {s['alphas']}, "
         f"alphas used {sorted({x['alpha'] for x in s['reports']})}, "
         + ("chosen on one seed's OOF and reported on another" if s["honest"] else "one seed: not honest"),
         f"- labels read: {'; '.join(s['labels_read'])}", ""]
    L += [f"**Caveat:** {c}." for c in r["caveats"]] + [""]
    L += [f"## 1. The {min(s['top'], len(r['per_perturbation']))} worst training perturbations out of fold", "",
          "Similarity columns: the largest value against any other training perturbation, nearest in brackets. "
          + "; ".join(f"{m}: {d}" for m, d in s["measures"].items()) + ".", "",
          fc._md(["rank", "perturbation", "category", "OOF M1", "OOF M2", "n targets", "gene sets", "PPI",
                  "co-expr max abs r", "n sets / partners", "screen row"]), "|" + "---|" * 11]
    for row in r["per_perturbation"][:s["top"]]:
        L.append(fc._md([row["rank"], row["pert"], row["category"] or "", fc._f(row["oof_pearson_delta"]),
                         fc._f(row["oof_pearson_delta_nontarget"]), row["n_targets"], _sim(row, "gene_sets"),
                         _sim(row, "ppi"), _sim(row, "coexpr"), f"{row['n_gene_sets']} / {row['n_ppi_partners']}",
                         ", ".join(n for n, v in row["screen_rows"].items() if v) or ("no" if s["screens"] else "")]))
    L += ["", "Spearman correlation of the OOF score with each similarity measure over all training perturbations "
          "(positive: perturbations with closer relatives score better):", "",
          fc._md(["measure", "rho (p, n)"]), "|---|---|"]
    L += [fc._md([m, _corr(c)]) for m, c in r["similarity_correlation"].items()]
    g = r["per_gene"]
    L += ["", f"## 2. The {len(g['top'])} genes with the largest mean squared OOF residual", "",
          fc._md(["gene", "msr", "share of total", "bias", "control mean", "control sd", "training perturbations "
                  "targeting it"]), "|" + "---|" * 7]
    L += [fc._md([x["gene"], fc._f(x["msr"], 5), f"{100 * x['share']:.2f}%", fc._f(x["bias"]), fc._f(x["control_mean"]),
                  fc._f(x["control_std"]), x["n_train_targeting"]]) for x in g["top"]]
    ann = (f"; gene_annotation.json columns: {', '.join(g['annotation_columns'])}" if g["annotation_columns"]
           else "; no knowledge/gene_annotation.json in this bundle")
    L += ["", f"Spearman correlation of the per-gene squared residual (all {g['n_genes']} genes) with each gene "
          f"property{ann}:", "", fc._md(["property", "rho (p, n)"]), "|---|---|"]
    L += [fc._md([k, _corr(c)]) for k, c in g["correlations"].items()]
    L += ["", "## 3. Residual structure", "",
          f"Variance explained by the first {st['n_components']} singular components of the mean residual matrix "
          f"(perturbations x genes), against the mean over {st['null_reps']} permutations of each gene's residuals "
          "across perturbations:", "", fc._md(["component", "share", "cumulative", "permuted share"]),
          "|---|---|---|---|"]
    L += [fc._md([i + 1, fc._f(a), fc._f(c), fc._f(n)])
          for i, (a, c, n) in enumerate(zip(st["share"], st["cumulative"], st["null_share"]))]
    L += ["", f"Reading: {st['reading']}.", ""]
    for c in st["components"]:
        L += [f"Component {c['component']} ({100 * c['share']:.1f}% of the residual variance): genes "
              + ", ".join(f"{g_} ({v:+.2f})" for g_, v in c["genes"]) + "; perturbations "
              + ", ".join(f"{p_} ({v:+.2f})" for p_, v in c["perts"]) + ".", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sandbox.reexec_under_hash_seed("residual_mining")
    sys.exit(main())
