"""A results table in the layout of CellForge's Table 1, generated from run outputs.

One block per dataset; one row per method; columns MSE, PCC, R^2 on all genes
and on the top-20 DE genes. Rows come from three places and are labelled:

* ``ours``: the lab's best model and its starting model (the best linear
  model on the built-in features, before any agent-discovered feature), read
  from each run's ``summary.json`` and aggregated over repeat runs on the same
  dataset and split (mean +- standard deviation, n runs);
* ``rerun``: the simple baselines the paper describes (Unperturbed, Linear
  Regression and Random Forest on one-hot perturbations concatenated with
  expression), fitted here on the same split and scored with the same code;
* ``reported``: every other row, quoted from the paper.

Ranks and bold are recomputed from the means. The ``calibrate`` entry point
scores the simple baselines under several candidate metric definitions, so the
definition behind the paper's numbers can be identified (the paper does not
state the expression scale, and its repository has no evaluation code).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..data.bundle import LabelSet
from . import comparable, reference

COLUMNS = ("mse", "pcc", "r2", "mse_de", "pcc_de", "r2_de")
HEADERS = ("MSE ↓", "PCC ↑", "R² ↑", "MSE_DE ↓", "PCC_DE ↑", "R²_DE ↑")
LOWER_BETTER = {"mse", "mse_de"}
DESET_COLUMNS = ("mse_deset", "pcc_deset", "r2_deset")
RF_SEEDS = (0, 1, 2)


# ------------------------------------------------------------------ lab rows
def run_arm(cfg: dict, summary: dict | None = None) -> str:
    """Which arm a run belongs to, from its config: the LLM planner/worker pair, or the scripted no-LLM
    control (fixed hypotheses implemented by hand-written template features). With the run's summary, a run
    whose planner was replaced by a fallback during the run is its own arm, named by the planners that
    actually produced its plans ("claude_cli:opus -> deepseek:deepseek-v4-pro planner"), and one that lost
    every planner says so; neither is pooled with the clean runs of its configured arm."""
    p, w = cfg.get("planner", {}), cfg.get("worker", {})
    src = cfg.get("run", {}).get("continue_from")
    source = Path(str(src)).name if src else ""  # a warm start carries the campaign it continues in its name
    cont = ""
    if "python_exploit" in cfg.get("schedule", {}) and not cfg["schedule"]["python_exploit"]:
        cont += " (no exploit)"
    rule = str(cfg.get("experiment", {}).get("selection") or "pearson_delta")
    if rule != "pearson_delta":  # another selection rule is another arm
        cont += f" (selection {rule})"
    if p.get("provider") == "scripted" and w.get("provider") in ("mock", None):
        if source:  # re-searches another campaign's features without an LLM: its result is theirs, not a control's
            return f"no-LLM continuation of {source}" + cont
        return "scripted control (no LLM)" + cont
    if source:
        cont = f" (continued from {source})" + cont
    planner = f"{p.get('provider', '?')}:{p.get('model', '')}"
    ph = (summary or {}).get("planner") or {}
    if ph.get("mixed"):
        used = ph.get("used") or []
        chain = [ph.get("configured") or planner] + [u for u in used if u != (ph.get("configured") or planner)]
        planner = " -> ".join(chain)
        if ph.get("exhausted_at_min") is not None:
            cont += " (lost its planner)"
    return f"{planner} planner, {w.get('provider', '?')}:{w.get('model', '')} workers" + cont


def run_rows(run_dir: Path, part: str = "val2") -> dict | None:
    """The best model and the starting model of one run, with CellForge metrics on `part`
    (val2 = query-only held-out perturbations; val1 = visible validation)."""
    run_dir = Path(run_dir)
    path = run_dir / "summary.json"
    if not path.exists():
        return None
    s = json.loads(path.read_text())
    gen = s.get("generalization_query_only") or []
    best = next((g for g in gen if g.get("kind") != "baseline"), None)
    start = next((g for g in gen if g.get("kind") == "baseline"), None)

    def metrics(g):
        comp = ((g or {}).get("comparable") or {}).get(part) or {}
        if not comp:
            return None
        return {c: comp.get(f"cellforge_{c}") for c in COLUMNS + DESET_COLUMNS}

    cfg = json.loads((run_dir / "config.json").read_text()) if (run_dir / "config.json").exists() else {}
    arm = run_arm(cfg, s)
    return {"run_id": s.get("run_id", run_dir.name), "dataset": s.get("dataset"), "split_id": s.get("split_id"),
            "workers": s.get("workers") or cfg.get("run", {}).get("workers"), "duration_s": s.get("duration_s"),
            "data_dir": cfg.get("run", {}).get("data_dir"), "arm": arm, "code": (s.get("base_commit") or "")[:7],
            "best": None if best is None else {"experiment_id": best["experiment_id"],
                                               "features": ((s.get("ensemble") or {}).get("features") if best.get("kind") == "ensemble"
                                                            else (s.get("best") or {}).get("features")),
                                               "model": ("ensemble of top finalists" if best.get("kind") == "ensemble"
                                                         else (s.get("best") or {}).get("model")),
                                               "primary": best.get("query_only_pearson_delta", best.get("query_only_score")),  # by name, whatever the rule
                                               "metrics": metrics(best)},
            "start": None if start is None else {"experiment_id": start["experiment_id"],
                                                 "description": (s.get("baseline") or {}).get("description"),
                                                 "primary": start.get("query_only_pearson_delta", start.get("query_only_score")),
                                                 "metrics": metrics(start)}}


def aggregate(rows: list[dict]) -> dict:
    """mean, std and n per column over runs; None where no run has the value."""
    out = {}
    for c in COLUMNS + DESET_COLUMNS:
        vals = [r[c] for r in rows if r.get(c) is not None]
        out[c] = {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                  "n": len(vals)} if vals else None
    return out


# ----------------------------------------------------------- simple baselines
def _load_bundle(data_dir: Path, part: str):
    data_dir = Path(data_dir)
    z = np.load(data_dir / "public.npz", allow_pickle=False)
    labels = LabelSet.load(data_dir / "private" / f"{part}.npz")
    ref = reference.load(data_dir, part)
    if ref is None:
        raise FileNotFoundError(f"{data_dir} has no held-out cells for {part}; the DE reference cannot be built")
    return z, labels, ref


def simple_baseline_predictions(z, perts: list[str], rf_seeds=RF_SEEDS) -> dict[str, np.ndarray]:
    """Unperturbed (control mean), the mean training response, and the paper's Linear Regression and Random
    Forest on one-hot perturbation codes concatenated with the expression profile. Under the unseen-perturbation
    protocol a held-out perturbation's one-hot code is all zeros and the expression input is the same control
    profile, so both learners return one profile for every held-out perturbation."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    ctrl = z["control_cells"].astype(np.float64).mean(axis=0)
    train = z["train_means"].astype(np.float64)
    n_tr, n_te = train.shape[0], len(perts)
    x_tr = np.hstack([np.eye(n_tr), np.tile(ctrl, (n_tr, 1))])
    x_te = np.hstack([np.zeros((n_te, n_tr)), np.tile(ctrl, (n_te, 1))])
    out = {"Unperturbed": np.tile(ctrl, (n_te, 1)),
           "Mean training response": np.tile(train.mean(axis=0), (n_te, 1)),
           "Linear Regression": LinearRegression().fit(x_tr, train).predict(x_te)}
    for seed in rf_seeds:
        rf = RandomForestRegressor(n_estimators=200, random_state=seed, n_jobs=-1).fit(x_tr, train)
        out[f"Random Forest@{seed}"] = rf.predict(x_te)
    return out


def simple_baselines(data_dir: Path, part: str = "val2", rf_seeds=RF_SEEDS) -> dict:
    """CellForge metrics of the simple baselines on `part`, in the same aggregated shape as the lab rows."""
    z, labels, ref = _load_bundle(data_dir, part)
    preds = simple_baseline_predictions(z, labels.perts, rf_seeds)
    ctrl = z["control_cells"].astype(np.float64).mean(axis=0)
    per_seed: dict[str, list[dict]] = {}
    for name, pred in preds.items():
        m = comparable.score(pred, labels.means, labels.perts, ref, ctrl)
        row = {c: m.get(f"cellforge_{c}") for c in COLUMNS + DESET_COLUMNS}
        per_seed.setdefault(name.split("@")[0], []).append(row)
    return {name: aggregate(rows) for name, rows in per_seed.items()}


# ----------------------------------------------------------------- rendering
def _fmt(cell: dict | None, digits: int = 4) -> str:
    if cell is None:
        return "–"
    s = f"{cell['mean']:.{digits}f}"
    if cell.get("n", 1) > 1 or cell.get("std"):
        s += f" ± {cell['std']:.{digits}f}"
    return s


def rank_marks(rows: dict[str, dict]) -> dict[str, dict[str, int]]:
    """1, 2, 3 per column by the mean (lower is better for MSE columns)."""
    marks: dict[str, dict[str, int]] = {name: {} for name in rows}
    for c in COLUMNS:
        have = [(name, rows[name][c]["mean"]) for name in rows if rows[name].get(c)]
        have.sort(key=lambda t: t[1] if c in LOWER_BETTER else -t[1])
        for r, (name, _) in enumerate(have[:3], start=1):
            marks[name][c] = r
    return marks


SUP = {1: "¹", 2: "²", 3: "³"}


def render_block(title: str, rows: dict[str, dict], sources: dict[str, str], columns=COLUMNS,
                 headers=HEADERS) -> list[str]:
    marks = rank_marks({n: r for n, r in rows.items() if any(r.get(c) for c in columns)}) if columns == COLUMNS else {}
    L = [f"**{title}**", "", "| Method | Source | " + " | ".join(headers) + " |",
         "|---|---|" + "---|" * len(headers)]
    for name, r in rows.items():
        cells = []
        for c in columns:
            s = _fmt(r.get(c))
            rk = marks.get(name, {}).get(c)
            if rk == 1:
                s = f"**{s}**"
            if rk:
                s += SUP[rk]
            cells.append(s)
        L.append(f"| {name} | {sources.get(name, '')} | " + " | ".join(cells) + " |")
    return L + [""]


def build(run_dirs: list[Path], paper_json: Path | None, dataset_key: str | None = None, part: str = "val2",
          label: str = "Gene-Mila") -> dict:
    """Collect everything the table needs. Lab runs are grouped by (dataset, split, workers)."""
    runs = [r for r in (run_rows(Path(d), part) for d in run_dirs) if r]
    if len({r["code"] for r in runs if r.get("code")}) > 1:  # runs on different code are different arms
        for r in runs:
            r["arm"] = f"{r['arm']} @ {r['code'] or 'unknown code'}"
    groups: dict[tuple, list[dict]] = {}
    for r in runs:
        groups.setdefault((r["dataset"], r["split_id"], r["arm"], r["workers"]), []).append(r)
    blocks = []
    for (dataset, split_id, arm, workers), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][3] or 0)):
        best = aggregate([r["best"]["metrics"] for r in rs if r["best"] and r["best"]["metrics"]])
        start = aggregate([r["start"]["metrics"] for r in rs if r["start"] and r["start"]["metrics"]])
        blocks.append({"dataset": dataset, "split_id": split_id, "arm": arm, "workers": workers, "n_runs": len(rs),
                       "run_ids": [r["run_id"] for r in rs], "data_dir": next((r["data_dir"] for r in rs), None),
                       "best": best, "start": start,
                       "best_primary": [r["best"]["primary"] for r in rs if r["best"]],
                       "start_description": next((r["start"]["description"] for r in rs if r["start"]), None)})
    baselines, start_all = {}, {}
    for b in blocks:
        key = (b["dataset"], b["split_id"])
        if key not in baselines and b["data_dir"] and (Path(b["data_dir"]) / "public.npz").exists():
            baselines[key] = simple_baselines(Path(b["data_dir"]), part)
        if key not in start_all:  # the starting model is the same fit in every run of a dataset and split
            start_all[key] = aggregate([r["start"]["metrics"] for r in runs if (r["dataset"], r["split_id"]) == key
                                        and r["start"] and r["start"]["metrics"]])
    paper = json.loads(Path(paper_json).read_text()) if paper_json and Path(paper_json).exists() else None
    return {"part": part, "label": label, "blocks": blocks,
            "baselines": {f"{k[0]}|{k[1]}": v for k, v in baselines.items()},
            "start_all": {f"{k[0]}|{k[1]}": v for k, v in start_all.items()},
            "paper": paper, "dataset_key": dataset_key}


def render(t: dict) -> str:
    part_name = {"val2": "query-only held-out perturbations", "val1": "visible validation perturbations"}.get(
        t["part"], t["part"])
    L = ["# Results in CellForge's Table 1 layout", "",
         f"Metrics on {part_name}: MSE, Pearson correlation and R² between predicted and true mean expression "
         "(log1p of counts per 10k) per perturbation, averaged over perturbations; the DE columns restrict each "
         "perturbation to its top-20 DE genes. Sources: **ours** = this lab (mean ± sd over n independent runs); "
         "**rerun** = the paper's simple baselines refitted on the same split and scored with the same code "
         "(Random Forest: mean ± sd over seeds); **reported** = quoted from the paper, scored by its authors on "
         "their split and preprocessing. Bold and ¹²³ mark the three best means per column.", ""]
    by_dataset: dict[str, list[dict]] = {}
    for b in t["blocks"]:
        by_dataset.setdefault(b["dataset"], []).append(b)
    paper = t.get("paper") or {}
    for dataset, blocks in by_dataset.items():
        rows, sources = {}, {}
        pkey = t.get("dataset_key") or next((k for k in paper.get("datasets", {}) if k in dataset.lower()), None)
        pd = paper.get("datasets", {}).get(pkey) if pkey else None
        if pd:
            for name, vals in pd["rows"].items():
                std = pd.get("std", {}).get(name)
                rows[name] = {c: {"mean": v, "std": (std[i] if std else 0.0), "n": 1}
                              for i, (c, v) in enumerate(zip(COLUMNS, vals))}
                sources[name] = "reported"
        base = t["baselines"].get(f"{dataset}|{blocks[0]['split_id']}", {})
        for name in ("Unperturbed", "Linear Regression", "Random Forest"):
            if name in base:
                key = f"{name} (rerun)" if name in rows else name
                rows[key] = base[name]
                sources[key] = "rerun"
        for b in blocks:
            start_name = f"{t['label']} starting model"
            start = (t.get("start_all") or {}).get(f"{dataset}|{b['split_id']}") or b["start"]
            if start_name not in rows and any(start.get(c) for c in COLUMNS):
                rows[start_name] = start
                sources[start_name] = "ours"
            name = f"{t['label']}, {b['arm']}, {b['workers']} workers (n={b['n_runs']})"
            rows[name] = b["best"]
            sources[name] = "ours"
        title = (pd or {}).get("title") or dataset
        L += render_block(title, rows, sources)
        notes = [f"Lab runs: " + "; ".join(
            f"{b['arm']}, {b['workers']} workers: {', '.join(b['run_ids'])} (split {b['split_id']})" for b in blocks)]
        if not any("scripted control" in b["arm"] for b in blocks):
            notes.append("No scripted no-LLM control run on this split yet: the agents' gain is measured over the "
                         "starting model only. Run the same time budget with `--planner-provider scripted "
                         "--worker-provider mock` to add that row.")
        if blocks[0].get("start_description"):
            notes.append(f"Starting model: {blocks[0]['start_description']}")
        if pd:
            notes.append("Reported rows are the paper's reruns of those methods; their split, preprocessing and "
                         "metric scale are not stated, so they are not directly comparable until the calibration "
                         "below reproduces the paper's simple-baseline rows.")
        L += [f"- {n}" for n in notes] + [""]
        # supplementary: CellForge's documented DE set
        sup = {name: {"mse": r.get("mse_deset"), "pcc": r.get("pcc_deset"), "r2": r.get("r2_deset")}
               for name, r in rows.items() if sources.get(name) != "reported"}
        if any(any(v for v in r.values()) for r in sup.values()):
            L += render_block(f"{title} — DE columns on CellForge's documented DE set "
                              "(Wilcoxon BH p < 0.05 and |log2FC| > 0.5), ours and reruns only",
                              sup, sources, columns=("mse", "pcc", "r2"), headers=("MSE_DE ↓", "PCC_DE ↑", "R²_DE ↑"))
    if paper:
        L += ["## Notes on the reported rows", ""] + [f"- {n}" for n in paper.get("notes", [])] + [
            f"- Source: {paper.get('source')}", ""]
    return "\n".join(L)


# --------------------------------------------------------------- calibration
def _pooled(truth: np.ndarray, pred: np.ndarray, de: list[np.ndarray] | None) -> list[float]:
    """MSE, PCC and R^2 pooled over samples as in the paper's Appendix E: means over samples per gene, then
    one correlation / one variance ratio over all (sample, gene) entries."""
    def three(t, p):
        tc, pc = t - t.mean(axis=0), p - p.mean(axis=0)
        den = np.sqrt((tc * tc).sum() * (pc * pc).sum())
        pcc = float((tc * pc).sum() / den) if den > 0 else 0.0
        ss_tot = (tc * tc).sum()
        r2 = float(1 - ((t - p) ** 2).sum() / ss_tot) if ss_tot > 0 else 0.0
        return [float(np.mean((t - p) ** 2)), pcc, r2]
    out = three(truth, pred)
    if de is not None:  # DE genes differ per perturbation: pool each sample's selected entries
        out += three(np.stack([truth[i][d] for i, d in enumerate(de)]), np.stack([pred[i][d] for i, d in enumerate(de)]))
    return out


def calibration(data_dir: Path, part: str = "val2", rf_seeds=(0,)) -> dict:
    """Score the simple baselines under candidate definitions of the paper's metrics.

    Definitions (pred = predicted profile per held-out perturbation):
      means/log1p            per-perturbation metrics on mean log1p expression, averaged (this lab's table)
      means/log1p/pooled     the same values pooled over all (perturbation, gene) entries (Appendix E formulas)
      means/delta            metrics on change from control, per perturbation, averaged
      means/delta/pooled     change from control, pooled
      means/z-train/pooled   genes standardised by the training pseudobulk (mean, sd over training perturbations)
      means/z-cells/pooled   genes standardised by the control cells (mean, sd over cells)
      cells/log1p/pooled     every held-out cell is a sample; the prediction is broadcast to its cells
      cells/z-cells/pooled   the same on genes standardised by the control cells
    """
    import scipy.sparse as sp
    data_dir = Path(data_dir)
    z, labels, ref = _load_bundle(data_dir, part)
    preds = simple_baseline_predictions(z, labels.perts, rf_seeds)
    ctrl = z["control_cells"].astype(np.float64).mean(axis=0)
    truth = labels.means
    idx = {p: i for i, p in enumerate(ref["perts"])}
    rows = [idx[p] for p in labels.perts]
    top = [ref["top_de"][r] for r in rows]
    train = z["train_means"].astype(np.float64)
    mu_tr, sd_tr = train.mean(axis=0), train.std(axis=0) + 1e-8
    cells_ctrl = z["control_cells"].astype(np.float64)
    mu_c, sd_c = cells_ctrl.mean(axis=0), cells_ctrl.std(axis=0) + 1e-8
    X = sp.load_npz(data_dir / "private" / f"{part}_cells.npz")
    cell_labels = np.load(data_dir / "private" / f"{part}_cells_labels.npy", allow_pickle=False).astype(str)
    cells = {p: np.asarray(X[cell_labels == p].todense(), dtype=np.float64) for p in labels.perts}

    def per_pert(t, p):
        m = comparable.cellforge(p, t, np.array(top))
        return [m[f"cellforge_{c}"] for c in COLUMNS]

    out = {}
    for name, pred in preds.items():
        d = {}
        d["means/log1p"] = per_pert(truth, pred)
        d["means/log1p/pooled"] = _pooled(truth, pred, top)
        d["means/delta"] = per_pert(truth - ctrl, pred - ctrl)
        d["means/delta/pooled"] = _pooled(truth - ctrl, pred - ctrl, top)
        d["means/z-train/pooled"] = _pooled((truth - mu_tr) / sd_tr, (pred - mu_tr) / sd_tr, top)
        d["means/z-cells/pooled"] = _pooled((truth - mu_c) / sd_c, (pred - mu_c) / sd_c, top)
        t_cells = np.concatenate([cells[p] for p in labels.perts])
        p_cells = np.concatenate([np.tile(pred[i], (cells[p].shape[0], 1)) for i, p in enumerate(labels.perts)])
        de_cells = [top[i] for i, p in enumerate(labels.perts) for _ in range(cells[p].shape[0])]
        d["cells/log1p/pooled"] = _pooled(t_cells, p_cells, de_cells)
        d["cells/z-cells/pooled"] = _pooled((t_cells - mu_c) / sd_c, (p_cells - mu_c) / sd_c, de_cells)
        out[name.split("@")[0]] = d
    return {"part": part, "n_perts": len(labels.perts), "n_cells": int(sum(c.shape[0] for c in cells.values())),
            "definitions": out}


def render_calibration(cal: dict, paper_rows: dict | None) -> str:
    L = [f"# Which metric definition reproduces CellForge's simple-baseline rows?", "",
         f"{cal['n_perts']} held-out perturbations ({cal['part']}), {cal['n_cells']} held-out cells. "
         "Each candidate definition is applied to the same predictions; the paper's row is listed first.", ""]
    for name, defs in cal["definitions"].items():
        L += [f"**{name}**", "", "| definition | " + " | ".join(HEADERS) + " |", "|---|" + "---|" * len(HEADERS)]
        target = (paper_rows or {}).get(name)
        if target:
            L.append("| paper (reported) | " + " | ".join(f"{v:.4f}" for v in target) + " |")
        best, best_err = None, None
        for dname, vals in defs.items():
            L.append(f"| {dname} | " + " | ".join(f"{v:.4f}" for v in vals) + " |")
            if target:
                err = float(np.mean([abs(a - b) / (abs(b) + 1e-3) for a, b in zip(vals, target)]))
                if best_err is None or err < best_err:
                    best, best_err = dname, err
        if target:
            L.append("")
            L.append(f"Closest to the paper: `{best}` (mean relative error {best_err:.2f}; below about 0.1 "
                     "means the definition reproduces the row).")
        L.append("")
    return "\n".join(L)
