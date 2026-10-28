#!/usr/bin/env python3
"""The holder's scoring of the fresh test (docs/PLAN_R_FRESH_TEST.md, section 7), in one command. Run by the holder
only, on a machine no agent can reach, after the deposit's hashes are on #41.

It reads the cohort file (the Replogle 2022 K562 CRISPRi h5ad the holder downloaded from the public record), the
slice manifest (tools/replogle_slice_manifest.py: the targets, their labels, the R1/R2 draw, the common gene panel)
and the deposit (one folder per model, each with predictions.npz from tools/frozen_model.py predict-targets, plus
batch.json naming the models and the comparisons). Then, for the part asked (r1 or r2):

1. From the cohort's own cells, the control mean and every target's mean on the common gene panel, normalised as the
   lab's ingest (log1p of 10,000 times counts over the cell's total over all genes; a file already normalised is used
   as it is). Control cells are capped by --max-control (a seeded sample), every target's cells are used.
2. Every model: predicted expression = cohort control mean + deposited delta; the lab's evaluator unchanged
   (pearson_delta primary, MSE, top-20 metrics), on all targets of the part and on its in-distribution and other
   subsets; with --de, CellForge-comparable DE metrics from a DE reference built on the cohort's cells.
3. Every comparison in batch.json, a minus b, paired per target on pearson_delta (the lab's reading rule: gain above
   twice its paired SE and wins on more than half), per subset; one Holm correction over all comparisons and both
   parts, on two-sided normal p-values of mean/SE, as the plan fixes.

It never edits a deposit file: it checks each against deposit_sha256.json when present, and records the cohort's
sha256. Output: a Markdown report and its JSON twin, posted on #41 unedited.

    python tools/fresh_test_score.py --cohort K562_gwps.h5ad --manifest manifest.json --deposit deposit/ \
        --part r1 --out r1_report.md
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

from genemila.benchmark.evaluator import evaluate, metric_values, paired_summary  # noqa: E402

KEYS = ("pearson_delta", "mse", "pearson_delta_top", "r2_top", "mse_top", "direction_acc_top")


def sha256(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _part_targets(manifest: dict, part: str) -> list[dict]:
    draw = manifest.get("draw") or {}
    if part not in draw:
        raise SystemExit(f"the manifest has no draw for {part!r} (built without --draw?)")
    rows = {t["symbol"]: t for t in manifest["targets"] if t.get("eligible")}
    missing = [s for s in draw[part] if s not in rows]
    if missing:
        raise SystemExit(f"{len(missing)} drawn targets are not eligible in the manifest, e.g. {missing[:3]}")
    return [rows[s] for s in draw[part]]


def cohort_means(cohort: Path, manifest: dict, targets: list[dict], max_control: int, seed: int,
                 keep_cells: bool = False) -> dict:
    """Control mean and per-target means on the panel genes, in panel order; optionally the cells themselves."""
    import anndata as ad
    import scipy.sparse as sp
    from genemila.data.real import CONTROL_LABELS, _looks_like_counts, _normalise_log1p
    a = ad.read_h5ad(cohort, backed="r")
    label_col, gene_col = manifest["h5ad"]["label_col"], manifest["h5ad"].get("gene_col")
    symbols = (a.var[gene_col].astype(str).tolist() if gene_col and gene_col in a.var
               else a.var_names.astype(str).tolist())
    col = {s: i for i, s in enumerate(symbols)}
    panel = manifest["common_gene_panel"]
    cols = np.array([col[s] for s in panel["cohort_symbols"]])
    labels = a.obs[label_col].astype(str).to_numpy()
    rng = np.random.default_rng(seed)
    ctrl_rows = np.flatnonzero(np.isin(np.char.lower(labels.astype(str)), list(CONTROL_LABELS)))
    if len(ctrl_rows) == 0:
        raise SystemExit("no control cells found in the cohort")
    if len(ctrl_rows) > max_control:
        ctrl_rows = np.sort(rng.choice(ctrl_rows, max_control, replace=False))
    probe = a.X[np.sort(rng.choice(a.n_obs, min(a.n_obs, 2000), replace=False))]
    counts = _looks_like_counts(sp.csr_matrix(probe) if sp.issparse(probe) else np.asarray(probe))

    def block(rows: np.ndarray) -> np.ndarray:
        out = []
        for i in range(0, len(rows), 5000):
            sub = a.X[np.sort(rows[i:i + 5000])]
            sub = _normalise_log1p(sub) if counts else sub  # totals over all genes, then the panel
            sub = sub[:, cols]
            out.append(np.asarray(sub.todense() if sp.issparse(sub) else sub, dtype=np.float64))
        return np.vstack(out)

    ctrl = block(ctrl_rows)
    means, cells, cell_labels = [], [ctrl] if keep_cells else [], ["control"] * len(ctrl_rows) if keep_cells else []
    for t in targets:
        rows = np.flatnonzero(np.isin(labels, t["labels"]))
        X = block(rows)
        means.append(X.mean(0))
        if keep_cells:
            cells.append(X)
            cell_labels += [t["symbol"]] * len(rows)
    out = {"control_mean": ctrl.mean(0), "means": np.stack(means), "n_control": len(ctrl_rows),
           "normalised_here": bool(counts), "genes": panel["genes"]}
    if keep_cells:
        out["cells"], out["cell_labels"] = np.vstack(cells), np.array(cell_labels)
    return out


def _load_model(folder: Path, symbols: list[str], genes: list[str]) -> np.ndarray:
    with np.load(folder / "predictions.npz", allow_pickle=False) as z:
        delta, perts, g = np.asarray(z["delta"], dtype=np.float64), [str(p) for p in z["perts"]], [str(x) for x in z["genes"]]
    pi, gi = {p: i for i, p in enumerate(perts)}, {x: i for i, x in enumerate(g)}
    lack = [s for s in symbols if s not in pi]
    if lack:
        raise SystemExit(f"{folder.name}: no prediction for {len(lack)} targets, e.g. {lack[:3]}")
    lack = [x for x in genes if x not in gi]
    if lack:
        raise SystemExit(f"{folder.name}: no prediction for {len(lack)} panel genes, e.g. {lack[:3]}")
    return delta[np.ix_([pi[s] for s in symbols], [gi[x] for x in genes])]


def _holm(ps: list[float]) -> list[float]:
    order = np.argsort(ps)
    out, running = [0.0] * len(ps), 0.0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - k) * ps[i]))
        out[i] = running
    return out


def _p(mean: float | None, se: float | None) -> float | None:
    if mean is None or not se:
        return None
    from scipy.stats import norm
    return float(2 * norm.sf(abs(mean / se)))


def score(cohort: Path, manifest_path: Path, deposit: Path, part: str, max_control: int = 20000, seed: int = 0,
          de: bool = False) -> dict:
    manifest = json.loads(Path(manifest_path).read_text())
    batch = json.loads((Path(deposit) / "batch.json").read_text())
    checks = {}
    pinned = Path(deposit) / "deposit_sha256.json"
    if pinned.exists():
        for rel, want in json.loads(pinned.read_text()).items():
            got = sha256(Path(deposit) / rel)
            checks[rel] = got == want
        if not all(checks.values()):
            raise SystemExit(f"deposit hash mismatch: {[k for k, v in checks.items() if not v]}")
    targets = _part_targets(manifest, part)
    symbols = [t["symbol"] for t in targets]
    subsets = {"all": symbols, "in_distribution": [t["symbol"] for t in targets if t.get("in_distribution")],
               "other": [t["symbol"] for t in targets if t.get("in_distribution") is False]}
    c = cohort_means(Path(cohort), manifest, targets, max_control, seed, keep_cells=de)
    ref = None
    if de:
        from genemila.benchmark import reference
        ref = reference.build(c["cells"], c["cell_labels"])
    truth, ctrl = c["means"], c["control_mean"]
    models, per = {}, {}
    for m in batch["models"]:
        delta = _load_model(Path(deposit) / m["dir"], symbols, c["genes"])
        pred = ctrl + delta
        res = evaluate(pred, truth, ctrl, symbols)
        per[m["name"]] = metric_values(res["per_perturbation"], "pearson_delta")
        entry = {}
        for sub, members in subsets.items():
            if not members:
                continue
            idx = [symbols.index(s) for s in members]
            r = evaluate(pred[idx], truth[idx], ctrl, members)
            entry[sub] = {k: r["metrics"].get(k) for k in KEYS} | {"n": len(members)}
        if ref is not None:
            from genemila.benchmark import comparable
            entry["all"].update(comparable.score(pred, truth, symbols, ref, ctrl))
        models[m["name"]] = entry
    comps = []
    for a_name, b_name in batch.get("comparisons", []):
        row = {"a": a_name, "b": b_name}
        for sub, members in subsets.items():
            if members:
                pa = {s: per[a_name][s] for s in members}
                pb = {s: per[b_name][s] for s in members}
                ps = paired_summary(pa, pb)
                ps["p_normal"] = _p(ps.get("mean_diff"), ps.get("se"))
                row[sub] = ps
        comps.append(row)
    return {"part": part, "cohort": {"name": Path(cohort).name, "sha256": sha256(Path(cohort))},
            "manifest_sha256": sha256(Path(manifest_path)), "deposit_checks": checks,
            "n_targets": len(symbols), "subset_sizes": {k: len(v) for k, v in subsets.items()},
            "n_control_cells": c["n_control"], "normalised_here": c["normalised_here"],
            "n_panel_genes": len(c["genes"]), "models": models, "comparisons": comps}


def holm_over(reports: list[dict], subset: str = "in_distribution") -> None:
    """One Holm correction over every comparison of every report given (the plan: R1 and R2 together), on the
    subset the plan reads (in-distribution); written into each comparison as p_holm."""
    cells = [(r, i) for r in reports for i, c in enumerate(r["comparisons"]) if subset in c
             and c[subset].get("p_normal") is not None]
    adj = _holm([r["comparisons"][i][subset]["p_normal"] for r, i in cells])
    for (r, i), p in zip(cells, adj):
        r["comparisons"][i][subset]["p_holm"] = p


def render(rep: dict) -> str:
    f = lambda x: "—" if x is None else f"{x:.4f}"  # noqa: E731
    lines = [f"# Fresh test, {rep['part'].upper()}: every deposited model scored once", "",
             f"Cohort `{rep['cohort']['name']}` (sha256 `{rep['cohort']['sha256']}`); manifest sha256 "
             f"`{rep['manifest_sha256']}`; {rep['n_targets']} targets ({rep['subset_sizes']['in_distribution']} "
             f"in distribution), {rep['n_panel_genes']} panel genes, {rep['n_control_cells']} control cells.", "",
             "| model | subset | n | pearson_delta | mse | pearson_delta_top | r2_top |", "|---|---|---:|---:|---:|---:|---:|"]
    for name, entry in rep["models"].items():
        for sub, m in entry.items():
            lines.append(f"| {name} | {sub} | {m['n']} | {f(m.get('pearson_delta'))} | {f(m.get('mse'))} | "
                         f"{f(m.get('pearson_delta_top'))} | {f(m.get('r2_top'))} |")
    lines += ["", "| a minus b | subset | n | mean diff ± SE | wins a/b | verdict | p | p (Holm) |",
              "|---|---|---:|---:|---|---|---:|---:|"]
    for c in rep["comparisons"]:
        for sub in ("in_distribution", "other", "all"):
            s = c.get(sub)
            if s and "mean_diff" in s:
                lines.append(f"| {c['a']} − {c['b']} | {sub} | {s['n']} | {s['mean_diff']:+.4f} ± {s['se']:.4f} | "
                             f"{s['wins_a']}/{s['wins_b']} | {s['verdict']} | {f(s.get('p_normal'))} | "
                             f"{f(s.get('p_holm'))} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--deposit", required=True)
    ap.add_argument("--part", choices=["r1", "r2"], nargs="+", required=True,
                    help="r1, or r1 r2 for the R2 report (one Holm over both, R1's values repeated unchanged)")
    ap.add_argument("--max-control", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--de", action="store_true", help="also CellForge-comparable DE metrics (slower)")
    ap.add_argument("--out", required=True, help="Markdown report of the last part; JSON twin beside it")
    a = ap.parse_args(argv)
    reps = [score(Path(a.cohort), Path(a.manifest), Path(a.deposit), p, a.max_control, a.seed, a.de) for p in a.part]
    holm_over(reps)
    out = Path(a.out)
    out.write_text("\n".join(render(r) for r in reps))
    out.with_suffix(".json").write_text(json.dumps(reps, indent=1, default=float))
    print(out.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
