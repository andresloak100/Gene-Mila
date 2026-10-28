#!/usr/bin/env python3
"""Run CellForge on this lab's split and score what it predicts with this lab's evaluator (GOAL_CRITERIA B.5,
docs/PLAN_C_CELLFORGE.md). Two commands, both free of any LLM:

export  Build CellForge's input from a bundle and the screen's own .h5ad files: the control cells and the cells of
        the bundle's TRAINING perturbations only (public.npz train_perts), on the bundle's genes, normalised as the
        bundle was (counts per 10k and log1p when the file holds raw counts), with obs['perturbation'] set to the
        bundle's perturbation key ('control' for controls). It writes the list of held-out perturbations CellForge
        must predict (every bundle perturbation outside training, val1 and val2 together, so the sealed membership
        is not revealed), a task text, and a receipt with hashes and counts. No private/ file and no splits.json is
        read: the held-out list is public.npz's perts minus its train_perts.

score   Read CellForge's predictions (an .npz with `perts` and `means`, or an .h5ad of predicted cells with
        obs['perturbation']), average to one expression profile per perturbation on the bundle's genes, and score
        them once on the sealed set through the lab's QueryOracle (pearson_delta, MSE, top-20 metrics and
        CellForge's own MSE/PCC/R2 on DE genes). With --versus RUN_DIR it adds the oracle's paired comparison of
        CellForge against that run's selected model (two scorings, mean difference, paired SE, wins), the lab's
        reading rule. The oracle is the tool's own and capped at what it needs.

    python tools/cellforge_bridge.py export --bundle data/adamson_cf --h5ad raw/AdamsonWeissman2016_*.h5ad \
        --out ~/cellforge_adamson
    python tools/cellforge_bridge.py score --bundle data/adamson_cf --pred ~/cellforge_adamson/predictions.npz \
        --versus runs/newcode_opus_w4_r0 --out docs/results/cellforge_adamson_matched.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.data.real import CONTROL_LABELS, _looks_like_counts, _normalise_log1p, canonical_key  # noqa: E402

TASK = """# Task for CellForge (Gene-Mila matched comparison)

Predict, for each perturbation listed in `heldout_perturbations.json`, the mean expression of every gene in
`cellforge_input.h5ad` (same genes, same order, same normalisation: counts per 10k, log1p) in K562 cells carrying
that CRISPR perturbation. None of these perturbations has any cell in the training file: this is the unseen-
perturbation setting. Train only on `cellforge_input.h5ad`; do not download or use any other copy of this screen.

Output: `predictions.npz` with `perts` (the held-out keys, as listed) and `means` (n_perts x n_genes, float).
Scored by Gene-Mila's evaluator: pearson_delta (correlation of predicted and true change from control, per
perturbation), MSE, and MSE/PCC/R2 on the top-20 DE genes.
"""


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _public(bundle: Path) -> dict:
    z = np.load(Path(bundle) / "public.npz")
    return {"genes": [str(g) for g in z["genes"]], "perts": [str(p) for p in z["perts"]],
            "train": [str(p) for p in z["train_perts"]], "control_mean": z["control_cells"].astype(np.float64).mean(0)}


def _read(paths: list[Path]):
    import anndata as ad
    parts = [ad.read_h5ad(p) for p in paths]
    return parts[0] if len(parts) == 1 else ad.concat(parts, join="inner", index_unique="-")


def export(bundle: Path, h5ads: list[Path], out: Path, condition_key: str | None = None) -> dict:
    import anndata as ad
    import pandas as pd
    import scipy.sparse as sp
    pub = _public(bundle)
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    adata = _read([Path(p) for p in h5ads])
    key = condition_key or next((k for k in ("perturbation", "condition", "target_gene", "gene") if k in adata.obs),
                                None)
    if key is None:
        raise SystemExit(f"no perturbation column in obs: {list(adata.obs.columns)}")
    genes_file = (adata.var["gene_name"].astype(str).tolist() if "gene_name" in adata.var
                  else adata.var_names.astype(str).tolist())
    gene_set = set(genes_file)
    labels = adata.obs[key].astype(object).fillna("unassigned").to_numpy(dtype=str)
    train = set(pub["train"])
    mapped = np.array(["control" if l.lower() in CONTROL_LABELS else (canonical_key(l, gene_set) or "")
                       for l in labels], dtype=object)
    keep = np.flatnonzero((mapped == "control") | np.isin(mapped, list(train)))
    X = adata.X
    if _looks_like_counts(X):  # normalise on all genes first, as the bundle's ingest did
        X = _normalise_log1p(X)
    X = sp.csr_matrix(X) if not sp.issparse(X) else X.tocsr()
    col = {g: i for i, g in enumerate(genes_file)}
    missing = [g for g in pub["genes"] if g not in col]
    if missing:
        raise SystemExit(f"{len(missing)} bundle genes are not in the file, e.g. {missing[:5]}")
    X = X[keep][:, [col[g] for g in pub["genes"]]].astype(np.float32)
    obs = pd.DataFrame({"perturbation": mapped[keep].astype(str), "cell_type": "K562"},
                       index=[f"c{i}" for i in range(len(keep))])
    found = sorted(set(obs["perturbation"]) - {"control"})
    out_ad = ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=pub["genes"]))
    out_ad.write_h5ad(out / "cellforge_input.h5ad", compression="gzip")
    heldout = sorted(set(pub["perts"]) - train)
    (out / "heldout_perturbations.json").write_text(json.dumps(heldout, indent=1))
    (out / "TASK.md").write_text(TASK)
    manifest = json.loads((Path(bundle) / "manifest.json").read_text()) if (Path(bundle) / "manifest.json").exists() else {}
    receipt = {"bundle": str(bundle), "split_id": manifest.get("split_id"), "n_genes": len(pub["genes"]),
               "n_cells": int(len(keep)), "n_control_cells": int((obs["perturbation"] == "control").sum()),
               "train_perturbations_found": len(found), "train_perturbations_in_bundle": len(train),
               "train_missing_in_file": sorted(train - set(found)), "n_heldout": len(heldout),
               "source_files": {Path(p).name: _sha(Path(p)) for p in h5ads},
               "cellforge_input_sha256": _sha(out / "cellforge_input.h5ad")}
    (out / "export.json").write_text(json.dumps(receipt, indent=1))
    return receipt


def _load_pred(path: Path, genes: list[str]) -> tuple[np.ndarray, list[str]]:
    path = Path(path)
    if path.suffix == ".npz":
        z = np.load(path, allow_pickle=False)
        perts, means = [str(p) for p in z["perts"]], np.asarray(z["means"], dtype=np.float64)
        pgenes = [str(g) for g in z["genes"]] if "genes" in z.files else genes
    else:
        a = _read([path])
        labs = a.obs["perturbation"].astype(str).to_numpy()
        perts = sorted(set(labs) - {"control"})
        X = a.X.toarray() if hasattr(a.X, "toarray") else np.asarray(a.X)
        means = np.stack([X[labs == p].mean(0) for p in perts]).astype(np.float64)
        pgenes = a.var_names.astype(str).tolist()
    if means.shape != (len(perts), len(pgenes)):
        raise SystemExit(f"means has shape {means.shape}, expected {(len(perts), len(pgenes))}")
    col = {g: i for i, g in enumerate(pgenes)}
    missing = [g for g in genes if g not in col]
    if missing:
        raise SystemExit(f"predictions lack {len(missing)} bundle genes, e.g. {missing[:5]}")
    means = means[:, [col[g] for g in genes]]
    if not np.all(np.isfinite(means)):
        raise SystemExit("predictions contain NaN or inf")
    return means, perts


def score(bundle: Path, pred_path: Path, versus: Path | None = None) -> dict:
    from genemila.benchmark.oracle import QueryOracle
    pub = _public(bundle)
    means, perts = _load_pred(pred_path, pub["genes"])
    oracle = QueryOracle(Path(bundle), max_queries=1)
    sealed = oracle.perts
    idx = {p: i for i, p in enumerate(perts)}
    lacking = [p for p in sealed if p not in idx]
    if lacking:
        raise SystemExit(f"predictions lack {len(lacking)} held-out perturbations, e.g. {lacking[:5]}")
    pred = means[[idx[p] for p in sealed]]
    rep = {"bundle": str(bundle), "predictions": str(pred_path), "predictions_sha256": _sha(Path(pred_path)),
           "cellforge": oracle.query("cellforge", pred, sealed, pub["control_mean"])}
    if versus is not None:
        from genemila.lab import open_run
        lab = open_run(Path(versus))
        rec = lab.db.best()
        o2 = QueryOracle(Path(bundle), max_queries=2, selection=lab.selection)
        pb, ob = lab._predict(rec, o2.perts)
        rep["versus"] = {"run": str(versus), "experiment_id": rec["experiment_id"],
                         "paired": o2.query_paired("cellforge", pred, sealed, rec["experiment_id"], pb, ob,
                                                   pub["control_mean"], metric="pearson_delta")}
    return rep


def render(rep: dict) -> str:
    m = rep["cellforge"]["metrics"]
    keys = ["pearson_delta", "mse", "pearson_delta_top", "r2_top", "cellforge_mse_de", "cellforge_pcc_de",
            "cellforge_r2_de"]
    lines = ["# CellForge on Gene-Mila's split, scored once on the sealed set", "",
             f"Bundle `{rep['bundle']}`; predictions `{rep['predictions']}` (sha256 `{rep['predictions_sha256']}`).", "",
             "| metric | CellForge |", "|---|---:|"]
    lines += [f"| {k} | {m[k]:.4f} |" for k in keys if isinstance(m.get(k), (int, float))]
    if "versus" in rep:
        p = rep["versus"]["paired"]["paired"]
        lines += ["", f"Paired against `{rep['versus']['run']}` {rep['versus']['experiment_id']} (CellForge minus the lab's "
                  f"model, pearson_delta per sealed perturbation): {json.dumps(p.get('pooled', p))[:600]}"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--bundle", required=True)
    e.add_argument("--h5ad", nargs="+", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--condition-key", default=None)
    s = sub.add_parser("score")
    s.add_argument("--bundle", required=True)
    s.add_argument("--pred", required=True)
    s.add_argument("--versus", default=None)
    s.add_argument("--out", required=True, help="markdown report; a JSON twin is written beside it")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        print(json.dumps(export(Path(a.bundle), [Path(p) for p in a.h5ad], Path(a.out), a.condition_key), indent=1))
        return 0
    rep = score(Path(a.bundle), Path(a.pred), Path(a.versus) if a.versus else None)
    out = Path(a.out)
    out.write_text(render(rep))
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1, default=float))
    print(render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
