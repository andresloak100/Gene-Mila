#!/usr/bin/env python3
"""The arm reading and the combined model of docs/PLAN_AFTER_N4.md, free of any LLM.

`rule`: the arm reading over the runs of one arm, from each run's own sealed reading (the JSON twins that
tools/sealed_reading.py writes) against one reference: "additive" (each run's selected model against its additive
baseline), "start" (against its starting model) or "versus" (a --versus reading, the run's selected model against
another run's). Each run r gives a pooled sealed paired difference g_r with paired standard error s_r, the latter
multiplied by the run's gene-clustering ratio when it exceeds 1 (the leave-one-gene-out jackknife SE over the plain
SE on visible labels, which tools/sealed_reading.py records); a run that selected its reference enters with g_r = 0
and s_r = 0, and a run whose planner changed or ran out is left out and named (it is its own arm). G = mean g_r;
S = mean s_r bounds the perturbation-sampling part of G's standard error whatever the correlation between runs, and
sd_g, the spread of the g_r, is the run-to-run part: SE = sqrt(S² + sd_g²/R). The gain counts when G exceeds k·SE
with k = max(2, Student t at 0.975 on Welch–Satterthwaite's degrees of freedom), every g_r has G's sign, and summed
over the runs the side G favours wins on more than half the perturbation-run pairs. The same rule is applied in
every category with at least MIN_READ sealed perturbations in each run; the visible and out-of-fold counterpart is
reported beside it, not read; and the arm's selected models are reported as mean ± sd of their sealed
pearson_delta, MSE_DE, PCC_DE and R²_DE. This part reads JSON files only: it scores nothing on the sealed set.

`combine`: an arm's combined model, the plain average of the predicted changes of its runs' selected models (each
run's summary.json "best", chosen on visible data; equal weights, no selection among runs), against a reference that
is one run's selected, additive or starting model or another arm's combined model. One paired query (two scorings) on
an oracle of the tool's own over the members' bundle answers it, pooled and per category, read by the per-run rule of
tools/sealed_reading.py (a gain counts when it exceeds twice its paired standard error and the better side wins on
more than half the perturbations); the visible comparison of the same two models (the visible validation
perturbations and, out of fold, the training ones, each member's stored predictions averaged) is reported beside it.
A model is named only as a run's selected, additive or starting model, so nothing can be picked by a sealed score.
Run directories are read only in content, as tools/sealed_reading.py reads them.

B1 of the plan (N4, runs/norman_ds_from_n2_w4_r0, is its own arm and in neither command):

    python tools/arm_reading.py rule --against start --readings docs/results/norman_b1_r1_sealed_reading.json \\
        docs/results/norman_b1_r2_sealed_reading.json docs/results/norman_b1_r3_sealed_reading.json \\
        --out docs/results/norman_b1_arm_reading.md
    python tools/arm_reading.py combine --members runs/norman_ds_from_n2_w4_r1 runs/norman_ds_from_n2_w4_r2 \\
        runs/norman_ds_from_n2_w4_r3 --reference runs/norman_control_replogle_w4_r0 \\
        --out docs/results/norman_b1_combined_vs_n2.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from genemila.benchmark.evaluator import metric_values, paired_summary  # noqa: E402
from genemila.benchmark.oracle import QueryOracle  # noqa: E402  (combine's only sealed read: one paired query)
from genemila.lab import open_run  # noqa: E402

import sealed_reading as sr  # noqa: E402

METRIC = sr.METRIC
MIN_READ = sr.MIN_READ
RULE = ("the arm's gain G (the mean of the runs' paired differences) counts when it exceeds k·SE, SE = sqrt(S² + "
        "sd_g²/R) with S the mean of the runs' paired standard errors (each inflated by its gene-clustering ratio "
        "when above 1) and sd_g the spread of their differences, k = max(2, t at 0.975 on Welch–Satterthwaite's "
        "degrees of freedom); every run's difference has G's sign; and summed over the runs the side G favours wins "
        "on more than half the perturbation-run pairs")
ARM_METRICS = [(METRIC, "pearson_delta"), ("cellforge_mse_de", "MSE_DE"), ("cellforge_pcc_de", "PCC_DE"),
               ("cellforge_r2_de", "R²_DE")]
ROLES = ("selected", "additive", "start")


# ------------------------------------------------------------------ rule
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_SELECTED_REFERENCE = ("the run selected its starting model", "the run selected its additive baseline")


def _comparison(rep: dict, against: str, source: str) -> dict:
    """One run's reading against the reference from a sealed_reading JSON twin: the run, what it must share with the
    other runs of the arm (dataset, split, bundle, selection rule, external knowledge, the kind of start), its code
    and planner record, its selected model's own sealed scoring, the sealed and visible paired summaries and the
    gene-clustering ratios. A run that selected its reference has no paired summary and is marked
    "selected_reference"."""
    if against == "versus":
        p = rep.get("pair") or {}
        if p.get("mode") != "versus":
            raise ValueError(f"{source} holds no --versus reading")
        r = next((x for x in rep["runs"] if x["run"] == p["a"]["run"]), None)
        if r is None:
            raise ValueError(f"{source}: the run {p['a']['run']} is not among its runs")
        cmp_, why, sel = p, None, p["a"]
        ref, ref_run = f"{p['b']['run']}:{p['b']['experiment_id']}", p["b"]["run"]
        start_kind = None
    else:
        runs = rep.get("runs") or []
        if len(runs) != 1:
            raise ValueError(f"{source} reads {len(runs)} runs; the arm reading takes one run's reading per file")
        r = runs[0]
        sel, ref_run, start_kind = r["selected"], None, None
        if against == "additive":
            cmp_, ref_rec, why = r, r.get("additive"), r.get("note")
        else:
            c = r.get("continuation")
            if c is None:
                raise ValueError(f"{source}: the reading has no starting-model comparison")
            start_kind = c.get("kind", "warm_start")
            if c.get("is_additive"):   # the run's start is its additive baseline: that comparison is this one
                cmp_, ref_rec, why = r, r.get("additive"), r.get("note")
            else:
                cmp_, ref_rec, why = c, c.get("start"), c.get("note")
        ref = f"{r['run']}:{(ref_rec or {}).get('experiment_id')}"
    for key, what in (("planner", "the planner"), ("bundle", "the bundle"), ("has_summary", "summary.json")):
        if key not in r:
            raise ValueError(f"{source} was written before readings recorded {what}; read the run again with the "
                             "current tools/sealed_reading.py")
    if "stored_sealed" not in sel:
        raise ValueError(f"{source} was written before readings recorded the selected model's own sealed scoring; "
                         "read the run again with the current tools/sealed_reading.py")
    cont = r.get("continuation") or {}
    src, st = cont.get("source") or {}, cont.get("start") or {}
    out = {"run": r["run"], "reference": ref, "reference_run": ref_run, "dataset": r["dataset"],
           "split_id": r["split_id"], "bundle": r["bundle"], "selection": r.get("selection"),
           "external_knowledge": sorted(r.get("external_knowledge") or []), "start_kind": start_kind,
           "base_commit": r.get("base_commit"), "planner": r.get("planner"), "has_summary": r["has_summary"],
           "selected": sel["experiment_id"], "stored": sel.get("stored_sealed") or {}, "selected_reference": False,
           "start_alpha": st.get("alpha") if against == "start" else None,
           "source_alpha": src.get("alpha") if against == "start" else None}
    if not cmp_.get("sealed"):
        if not any(str(why or "").startswith(x) for x in _SELECTED_REFERENCE):
            raise ValueError(f"{source}: {r['run']} has no {against} comparison ({why}); the arm cannot be read")
        # the run kept its reference: its difference is zero, with no spread
        return {**out, "selected_reference": True, "sealed": None, "visible": None, "cluster_ratio": None}
    if "cluster_ratio" not in cmp_ or (cmp_["cluster_ratio"] and "estimator" not in cmp_["cluster_ratio"]):
        raise ValueError(f"{source} was written before readings recorded the overlap-robust clustering ratio; read "
                         "the run again with the current tools/sealed_reading.py")
    return {**out, "sealed": cmp_["sealed"]["paired"], "visible": cmp_.get("visible"),
            "cluster_ratio": cmp_.get("cluster_ratio")}


def arm_rule(g: list[float], s: list[float], wins: list[tuple[int, int, int]], n: int) -> dict:
    """The arm rule of docs/PLAN_AFTER_N4.md. g, s: the runs' paired differences and (inflated) standard errors;
    wins: per run (wins of the selected side, wins of the reference, perturbations compared); n: the sealed
    perturbations per run, for the degrees of freedom of S. Verdict "a" (the arm's selected models better), "b"
    (worse) or "none"."""
    g_, s_ = np.asarray(g, dtype=np.float64), np.asarray(s, dtype=np.float64)
    R = len(g_)
    G, S = float(g_.mean()), float(s_.mean())
    sd = float(g_.std(ddof=1)) if R > 1 else 0.0
    se = float(np.sqrt(S ** 2 + sd ** 2 / R))
    den = (S ** 4 / (n - 1) if n > 1 else 0.0) + ((sd ** 2 / R) ** 2 / (R - 1) if R > 1 else 0.0)
    nu = se ** 4 / den if den > 0 else float("inf")
    k = max(2.0, float(stats.t.ppf(0.975, nu))) if np.isfinite(nu) else 2.0
    wa, wb, total = (sum(w[i] for w in wins) for i in range(3))
    if G > k * se and bool((g_ > 0).all()) and wa > total / 2:
        verdict = "a"
    elif -G > k * se and bool((g_ < 0).all()) and wb > total / 2:
        verdict = "b"
    else:
        verdict = "none"
    return {"R": R, "G": G, "S": S, "sd_g": sd, "SE": se, "nu": nu, "k": k, "g": [float(x) for x in g_],
            "s": [float(x) for x in s_], "wins_selected": int(wa), "wins_reference": int(wb), "pairs": int(total),
            "verdict": verdict}


def _spread(values: list) -> dict | None:
    v = [float(x) for x in values if x is not None]
    if not v:
        return None
    return {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None, "n": len(v),
            "missing": len(values) - len(v)}


def _inflation(c: dict, key: str = "ratio") -> float:
    cr = c.get("cluster_ratio") or {}
    return max(1.0, float(cr.get(key) or 1.0))


def _rule_over(comps: list[dict], pick, inflate: str | None) -> dict | None:
    """The arm rule over one summary per run, picked by pick(run) -> paired summary (None for a run that kept its
    reference: g = 0, s = 0, no wins, as many ties as the other runs compare). inflate: the clustering ratio that
    multiplies each run's SE ("ratio", the plan's; "jackknife_ratio", as first specified) or None."""
    per = [pick(c) for c in comps]
    if any(p is not None and "mean_diff" not in p for p in per) or all(p is None for p in per):
        return None
    n = max(p["n"] for p in per if p is not None)
    g = [0.0 if p is None else p["mean_diff"] for p in per]
    s = [0.0 if p is None else p["se"] * (_inflation(c, inflate) if inflate else 1.0) for p, c in zip(per, comps)]
    wins = [(0, 0, n) if p is None else (p.get("wins_a", 0), p.get("wins_b", 0), p["n"]) for p in per]
    return {**arm_rule(g, s, wins, min(p["n"] for p in per if p is not None)),
            "n": [n if p is None else p["n"] for p in per]}


def _check_one_arm(comps: list[dict], against: str) -> None:
    """The runs of one arm answer the same question: one dataset, split, bundle, selection rule and external
    knowledge, one kind of start, and for --versus one reference model that is never itself an arm member."""
    for key in ("dataset", "split_id", "bundle", "selection", "external_knowledge", "start_kind"):
        vals = {json.dumps(c[key]) for c in comps}
        if len(vals) != 1:
            raise ValueError(f"the runs differ in {key}: {[c[key] for c in comps]}")
    if against == "versus":
        refs = {c["reference"] for c in comps}
        if len(refs) != 1:
            raise ValueError(f"the --versus readings compare against different models: {sorted(refs)}")
        members = {c["run"] for c in comps}
        if any(c["reference_run"] in members for c in comps):
            raise ValueError("a run is both a member of the arm and the reference of a --versus reading")


def read_arm(paths: list[Path], against: str) -> dict:
    if against not in ("additive", "start", "versus"):
        raise ValueError(f"--against must be additive, start or versus, not {against!r}")
    all_comps = [_comparison(json.loads(p.read_text()), against, str(p)) for p in paths]
    names = [c["run"] for c in all_comps]
    if len(set(names)) != len(names):
        raise ValueError(f"a run appears twice: {names}")
    _check_one_arm(all_comps, against)
    excluded = []
    for c in all_comps:
        if not c["has_summary"] or c["planner"] is None:
            excluded.append({"run": c["run"], "why": "no summary.json or no planner record", "planner": c["planner"]})
        elif c["planner"].get("mixed"):
            excluded.append({"run": c["run"], "why": "its planner changed or ran out during the run",
                             "planner": c["planner"]})
    comps = [c for c in all_comps if c["run"] not in {e["run"] for e in excluded}]
    if len(comps) < 2:
        raise ValueError(f"an arm reading needs at least two runs with a summary.json and an unchanged planner; "
                         f"{len(comps)} of {len(all_comps)} qualify (left out: {[e['run'] for e in excluded]})")
    pooled = _rule_over(comps, lambda c: c["sealed"], inflate="ratio")
    if pooled is None:
        raise ValueError("every run kept its reference: there is no difference to read")
    first_spec = _rule_over(comps, lambda c: c["sealed"], inflate="jackknife_ratio")
    with_cats = [c for c in comps if c["sealed"] is not None]
    cats = {}
    for cat in sorted(set.intersection(*[set(c["sealed"].get("by_category") or {}) for c in with_cats])):
        ns = [c["sealed"]["by_category"][cat].get("n", 0) for c in with_cats]
        r = (_rule_over(comps, lambda c, cat=cat: None if c["sealed"] is None else c["sealed"]["by_category"][cat],
                        inflate="ratio") if min(ns) >= MIN_READ else None)
        cats[cat] = {**r, "read": True} if r else {"n": ns, "read": False}
    visible, visible_cats = None, {}
    if all(c["selected_reference"] or (c.get("visible") or {}).get("mean_diff") is not None for c in comps):
        visible = _rule_over(comps, lambda c: None if c["selected_reference"] else c["visible"], inflate=None)
        vis = [c for c in comps if not c["selected_reference"]]
        for cat in sorted(set.intersection(*[set(c["visible"].get("by_category") or {}) for c in vis])):
            r = _rule_over(comps, lambda c, cat=cat: None if c["selected_reference"] else
                           c["visible"]["by_category"][cat], inflate=None)
            if r:
                visible_cats[cat] = r
    return {"generated_by": "tools/arm_reading.py rule", "code_commit": sr._commit(),
            "protocol": {"metric": METRIC, "rule": RULE, "min_read": MIN_READ, "against": against,
                         "sealed_scorings": 0, "inflation": "overlap-robust clustering ratio (plan amendment of "
                                                            "2026-10-11 20:30 UTC)"},
            "readings": [{"path": str(p), "sha256": _sha256(p)} for p in paths],
            "dataset": comps[0]["dataset"], "split_id": comps[0]["split_id"], "bundle": comps[0]["bundle"],
            "same_code": len({c["base_commit"] for c in comps}) == 1, "excluded": excluded,
            "runs": [{k: c[k] for k in ("run", "reference", "base_commit", "selected", "selected_reference",
                                        "start_alpha", "source_alpha")} |
                     ({"n": None, "mean_diff": 0.0, "se": 0.0, "inflation": 1.0, "jackknife_inflation": 1.0,
                       "wins_a": 0, "wins_b": 0, "verdict": None} if c["selected_reference"] else
                      {"n": c["sealed"]["n"], "mean_diff": c["sealed"]["mean_diff"], "se": c["sealed"]["se"],
                       "inflation": _inflation(c), "jackknife_inflation": _inflation(c, "jackknife_ratio"),
                       "wins_a": c["sealed"].get("wins_a"), "wins_b": c["sealed"].get("wins_b"),
                       "verdict": c["sealed"].get("verdict")})
                     | {"stored": {k: c["stored"].get(k) for k, _ in ARM_METRICS}} for c in comps],
            "pooled": pooled, "pooled_as_first_specified": first_spec, "by_category": cats, "visible": visible,
            "visible_by_category": visible_cats,
            "selected_spread": {name: _spread([c["stored"].get(k) for c in comps]) for k, name in ARM_METRICS}}


def _alpha(x) -> str:
    return "–" if x is None else f"{x:g}"   # ridge alphas run from 1e-05 to 1e+05


def _arm_verdict(r: dict, what: str) -> str:
    return {"a": f"{what} better", "b": f"{what} worse", "none": "no difference established"}[r["verdict"]]


def render_arm(rep: dict) -> str:
    pr, ag = rep["protocol"], rep["protocol"]["against"]
    ref = {"additive": "its additive baseline", "start": "its starting model",
           "versus": "the other run of its --versus reading"}[ag]
    L = ["# Arm reading", "",
         f"Pre-specified (docs/PLAN_AFTER_N4.md, \"The arm reading\" and its amendment of 20:30 UTC). Each run's "
         f"selected model against {ref}, metric {pr['metric']} per sealed perturbation, paired, from each run's own "
         f"sealed reading (sha256 below). Rule: {pr['rule']}. Each run's SE is inflated by the {pr['inflation']} when "
         f"above 1. A category is read when it holds at least {pr['min_read']} sealed perturbations in every run. The "
         "visible and out-of-fold rows are reported, not read. This reading scored nothing on the sealed set. "
         f"Dataset {rep['dataset']}, split {rep['split_id']}"
         + ("" if rep["same_code"] else "; the runs ran on different code") + f". Tool code "
         f"{str(rep.get('code_commit') or 'unknown')[:7]}.", ""]
    for e in rep.get("excluded") or []:
        L += [f"Left out: {e['run']}, {e['why']}; it is its own arm and is reported beside this one.", ""]
    warm = any(r.get("source_alpha") is not None for r in rep["runs"])
    L += ["| run | code | selected | reference | n | difference (paired SE) | SE inflation | wins | per-run verdict |"
          + (" start alpha / continued run's alpha |" if warm else ""),
          "|---|---|---|---|---|---|---|---|---|" + ("---|" if warm else "")]
    for r in rep["runs"]:
        alphas = (f" {_alpha(r.get('start_alpha'))} / {_alpha(r.get('source_alpha'))} |" if warm else "")
        if r["selected_reference"]:
            L.append(f"| {r['run']} | {str(r.get('base_commit') or 'unknown')[:7]} | {r['selected']} | "
                     f"{r['reference']} | – | 0 (kept its reference) | – | – | – |" + alphas)
            continue
        v = {"a": "selected better", "b": "reference better", "none": "no difference established"}.get(
            r.get("verdict"), "–")
        L.append(f"| {r['run']} | {str(r.get('base_commit') or 'unknown')[:7]} | {r['selected']} | {r['reference']} | "
                 f"{r['n']} | {r['mean_diff']:+.4f} ± {r['se']:.4f} | {r['inflation']:.2f} | "
                 f"{r.get('wins_a')}/{r.get('wins_b')} | {v} |" + alphas)
    p = rep["pooled"]
    L += ["", "| set | G | S | sd_g | SE | k | k·SE | same sign | wins (selected/reference of pairs) | arm verdict |",
          "|---|---|---|---|---|---|---|---|---|---|", _rule_row("sealed, pooled", p, _arm_verdict(p, "arm"))]
    for cat, c in rep["by_category"].items():
        label = f"sealed, {cat} (n {', '.join(map(str, c['n']))})"
        L.append(_rule_row(label, c, _arm_verdict(c, "arm")) if c["read"] else
                 f"| {label} | | | | | | | | | reported, not read |")
    fs = rep.get("pooled_as_first_specified")
    if fs:
        L.append(_rule_row("sealed, pooled, SE inflated by the jackknife ratio first specified", fs,
                           _arm_verdict(fs, "arm") + " (reported, not read)"))
    v = rep.get("visible")
    if v:
        L.append(_rule_row("visible and out-of-fold, pooled (SE not inflated)", v, "not read"))
        for cat, c in (rep.get("visible_by_category") or {}).items():
            L.append(_rule_row(f"visible and out-of-fold, {cat}", c, "not read"))
    L += ["", "The arm's selected models on the sealed set (each run's own end-of-run scoring), mean ± sd over its "
          "runs:", "", "| metric | mean | sd | runs |", "|---|---|---|---|"]
    for name, sp in rep["selected_spread"].items():
        if sp:
            miss = f" ({sp['missing']} without it)" if sp.get("missing") else ""
            L.append(f"| {name} | {sp['mean']:.4f} | {sr._f(sp['sd'], 4)} | {sp['n']}{miss} |")
        else:
            L.append(f"| {name} | not available | | |")
    L += ["", "Readings:", ""] + [f"- {x['path']} (sha256 {x['sha256'][:16]})" for x in rep["readings"]]
    L += ["", "## Reading", "",
          f"Over {p['R']} runs, the arm's selected models against {ref}: G {p['G']:+.4f}, SE {p['SE']:.4f} (S "
          f"{p['S']:.4f}, sd_g {p['sd_g']:.4f}), k {p['k']:.2f}; {_arm_verdict(p, 'the arm')}."]
    return "\n".join(L) + "\n"


def _rule_row(label: str, r: dict, verdict: str) -> str:
    return (f"| {label} | {r['G']:+.4f} | {r['S']:.4f} | {r['sd_g']:.4f} | {r['SE']:.4f} | {r['k']:.2f} | "
            f"{r['k'] * r['SE']:.4f} | {_same_sign(r)} | {r['wins_selected']}/{r['wins_reference']} of "
            f"{r['pairs']} | {verdict} |")


def _same_sign(r: dict) -> str:
    g = np.asarray(r["g"])
    return "yes" if (g > 0).all() or (g < 0).all() else "no"


# ------------------------------------------------------------------ combine
def _parse(spec: str) -> tuple[Path, str]:
    """RUN or RUN:ROLE, ROLE one of selected (the default), additive or start."""
    head, sep, role = spec.rpartition(":")
    if sep and role in ROLES:
        return Path(head), role
    if sep and "/" not in role:
        raise ValueError(f"{spec}: a model is a run's {', '.join(ROLES)} model, not {role!r}")
    return Path(spec), "selected"


def _model_of(lab, role: str) -> dict:
    if role == "selected":
        return sr._selected(lab)
    if role == "additive":
        rec = sr._additive(lab)
        if rec is None:
            raise ValueError(f"{lab.run_dir.name} has no additive baseline")
        return rec
    rec, why = sr._start(lab) if lab.cfg["run"].get("continue_from") else sr._fresh_start(lab)
    if rec is None:
        raise ValueError(f"{lab.run_dir.name}: {why}")
    return rec


def _check_same_bundle(labs: list) -> None:
    first = labs[0]
    for lab in labs[1:]:
        for what, x, y in (("dataset", first.dataset, lab.dataset), ("split", first.split_id, lab.split_id),
                           ("selection rule", first.selection, lab.selection),
                           ("bundle", str(Path(first.data_dir).resolve()), str(Path(lab.data_dir).resolve()))):
            if x != y:
                raise ValueError(f"{first.run_dir.name} and {lab.run_dir.name} differ in {what}: {x} against {y}")
        if not np.allclose(first.control_mean, lab.control_mean, rtol=0, atol=1e-12):
            raise ValueError(f"{first.run_dir.name} and {lab.run_dir.name} differ in their control means")


def _side(labs: dict, specs: list[tuple[Path, str]], perts: list[str]) -> dict:
    """One side of the comparison: its models, their averaged sealed-set predictions (absolute, in perts' order) and
    averaged visible predictions (val1 always; out of fold when every member cross-validates)."""
    models, sealed, val1, cv = [], [], [], []
    for path, role in specs:
        lab = labs[path]
        rec = _model_of(lab, role)
        pred, order = lab._predict(rec, perts)
        if sorted(order) != sorted(perts):
            raise ValueError(f"{lab.run_dir.name}:{rec['experiment_id']} does not predict every sealed perturbation")
        idx = {p: i for i, p in enumerate(order)}
        sealed.append(pred[[idx[p] for p in perts]])
        v, c = lab.visible_predictions(rec["experiment_id"])
        val1.append(v)
        cv.append(c)
        models.append({"run": lab.run_dir.name, "role": role, "seed": lab.cfg["run"].get("seed"),
                       "base_commit": lab.base_commit, "cv": lab._cv_hyperparameters() if lab.cv_folds > 1 else None,
                       "has_summary": (lab.run_dir / "summary.json").exists(), "planner": sr._planner(lab),
                       **sr._model(lab, rec)})
    has_cv = all(c is not None for c in cv)
    return {"models": models, "sealed": np.mean(sealed, axis=0), "val1": np.mean(val1, axis=0),
            "cv": np.mean(cv, axis=0) if has_cv else None}


def _label(models: list[dict]) -> str:
    if len(models) == 1:
        m = models[0]
        return f"{m['run']}:{m['experiment_id']} ({m['role']})"
    return "combined model of " + ", ".join(f"{m['run']}:{m['experiment_id']}" for m in models)


def combine(members: list[str], reference: list[str]) -> dict:
    if len(members) < 2:
        raise ValueError("a combined model needs at least two members")
    a_specs, b_specs = [_parse(m) for m in members], [_parse(r) for r in reference]
    if not b_specs:
        raise ValueError("give the reference: one run's model or several runs' combined model")
    if any(role != "selected" for _, role in a_specs):
        raise ValueError("an arm's combined model averages its runs' selected models only")
    if len({p.resolve() for p, _ in a_specs}) != len(a_specs):
        raise ValueError("a run appears twice among the members")
    paths = {p.resolve() for p, _ in a_specs + b_specs}
    labs = {p: open_run(p) for p in sorted(paths)}
    try:
        lab_list = [labs[p] for p in sorted(paths)]
        _check_same_bundle(lab_list)
        first = labs[a_specs[0][0].resolve()]
        oracle = QueryOracle(first.data_dir, max_queries=2, selection=first.selection)
        perts = list(oracle.perts)
        a = _side(labs, [(p.resolve(), r) for p, r in a_specs], perts)
        b = _side(labs, [(p.resolve(), r) for p, r in b_specs], perts)
        # an arm's members are runs that finished with their planner unchanged (AGENTS.md: a run whose planner
        # changed or ran out is its own arm); a reference of several runs is an arm too
        for side in (a, b) if len(b_specs) > 1 else (a,):
            for m in side["models"]:
                if not m["has_summary"] or m["planner"] is None:
                    raise ValueError(f"{m['run']} has no summary.json or no planner record: it cannot be an arm "
                                     "member")
                if m["planner"].get("mixed"):
                    raise ValueError(f"{m['run']}'s planner changed or ran out during the run: it is its own arm "
                                     "and cannot be an arm member")
        if [(m["run"], m["experiment_id"]) for m in a["models"]] == [(m["run"], m["experiment_id"])
                                                                     for m in b["models"]]:
            raise ValueError("the reference is the combined model itself")
        la, lb = _label(a["models"]), _label(b["models"])
        sealed = oracle.query_paired("combined", a["sealed"], perts, "reference", b["sealed"], perts,
                                     first.control_mean, metric=METRIC)
        cvs = {json.dumps(m["cv"], sort_keys=True) for m in a["models"] + b["models"]}
        a_cv, b_cv = (a["cv"], b["cv"]) if a["cv"] is not None and b["cv"] is not None else (None, None)
        same_folds = a_cv is not None and len(cvs) == 1
        sa, cats = first.score_visible(a["val1"], a_cv, cv_categories=same_folds)
        sb, _ = first.score_visible(b["val1"], b_cv, cv_categories=same_folds)
        visible = {"metric": METRIC, "out_of_fold": a_cv is not None, "same_folds": same_folds,
                   **paired_summary(metric_values(sa, METRIC, first.selection),
                                    metric_values(sb, METRIC, first.selection), cats or None)}
        # the visible validation perturbations alone, the same for every run whatever its folds: the score that
        # chooses the delivered Norman model (docs/PLAN_AFTER_N4.md, "The combined model of an arm")
        va, _ = first.score_visible(a["val1"], None)
        vb, _ = first.score_visible(b["val1"], None)
        ma, mb = metric_values(va, METRIC, first.selection), metric_values(vb, METRIC, first.selection)
        validation = {"metric": METRIC, "n": len(ma), "a": float(np.mean(list(ma.values()))),
                      "b": float(np.mean(list(mb.values())))}
        out = {"generated_by": "tools/arm_reading.py combine", "code_commit": sr._commit(),
               "protocol": {"metric": METRIC, "rule": "a gain counts when it exceeds twice its paired standard error "
                                                      "and the better side wins on more than half the perturbations",
                            "min_read": MIN_READ, "sealed_scorings": 2,
                            "combination": "the plain average of the members' predicted changes, equal weights"},
               "dataset": first.dataset, "split_id": first.split_id,
               "a": {"label": la, "models": a["models"]}, "b": {"label": lb, "models": b["models"]},
               "sealed": {"paired": sealed["paired"], "a_metrics": sealed["a"]["metrics"],
                          "b_metrics": sealed["b"]["metrics"]},
               "visible": visible, "visible_validation": validation}
    finally:
        for lab in labs.values():
            lab.close()
    return json.loads(json.dumps(out, default=float))


def render_combined(rep: dict) -> str:
    pr = rep["protocol"]
    L = ["# Combined model reading", "",
         f"Pre-specified (docs/PLAN_AFTER_N4.md, \"The combined model of an arm\"). A: {rep['a']['label']}; B: "
         f"{rep['b']['label']}. Combination: {pr['combination']}. Metric {pr['metric']} per sealed perturbation, "
         f"paired, A minus B; rule, pooled and in every category: {pr['rule']}; a category with fewer than "
         f"{pr['min_read']} sealed perturbations is reported, not read. One paired query ({pr['sealed_scorings']} "
         f"sealed scorings) on an oracle of the tool's own. Dataset {rep['dataset']}, split {rep['split_id']}. Tool "
         f"code {str(rep.get('code_commit') or 'unknown')[:7]}.", "",
         "| side | run | role | experiment | model | features | visible | seed | code |",
         "|---|---|---|---|---|---|---|---|---|"]
    for side in ("a", "b"):
        for m in rep[side]["models"]:
            L.append(f"| {side.upper()} | {m['run']} | {m['role']} | {m['experiment_id']} | {m['model_type']} | "
                     f"{len(m['features'] or [])} | {sr._f(m['visible_score'])} | {m['seed']} | "
                     f"{str(m.get('base_commit') or 'unknown')[:7]} |")
    sealed = {"a": {"metrics": rep["sealed"]["a_metrics"]}, "b": {"metrics": rep["sealed"]["b_metrics"]},
              "paired": rep["sealed"]["paired"]}
    v = rep["visible"]
    L += [""] + sr._table(sealed, v, "A", "B", visible_read=False) + [""]
    other = sr._other_metrics(sealed, "A", "B")
    L += ([other, ""] if other else [])
    if v.get("out_of_fold") and not v.get("same_folds"):
        L += ["The models drew different cross-validation folds, so the out-of-fold perturbations count in the "
              "visible row without their categories.", ""]
    vv = rep.get("visible_validation")
    if vv:
        L += [f"Pooled {vv['metric']} on the {vv['n']} visible validation perturbations alone (the score that chooses "
              f"the delivered model, docs/PLAN_AFTER_N4.md): A {vv['a']:.4f}, B {vv['b']:.4f}.", ""]
    pp = rep["sealed"]["paired"]
    L += ["## Reading", "", f"Sealed pooled: {sr._sentence(pp, 'A', 'B')}; by category: "
          f"{sr._category_sentences(pp, 'A', 'B')}. The visible row is reported, not read."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rule", help="the arm reading over the runs' own sealed readings (JSON twins)")
    r.add_argument("--readings", nargs="+", required=True)
    r.add_argument("--against", required=True, choices=("additive", "start", "versus"))
    c = sub.add_parser("combine", help="an arm's combined model against a reference, one paired sealed query")
    c.add_argument("--members", nargs="+", required=True, help="the arm's run directories (their selected models)")
    c.add_argument("--reference", nargs="+", required=True,
                   help="RUN[:selected|additive|start], or several runs for another arm's combined model")
    for p in (r, c):
        p.add_argument("--out", required=True, help="markdown report")
        p.add_argument("--json", default=None, help="JSON twin (default: the report's path with .json)")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.cmd == "rule":
        rep = read_arm([Path(p) for p in args.readings], args.against)
        md = render_arm(rep)
    else:
        rep = combine(args.members, args.reference)
        md = render_combined(rep)
    Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1))
    out.write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
