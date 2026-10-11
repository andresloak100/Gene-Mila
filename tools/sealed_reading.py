#!/usr/bin/env python3
"""The pre-specified sealed readings of docs/NORMAN_PLAN.md section 5, over finished runs, free of any LLM: each
run's selected model against its additive baseline, and, given two runs on the same bundle and split, one recording
an external knowledge file and the other none, the first's selected model against the second's (N2, the scripted
control with the external screen, against N1, without), whatever order the runs are given in. A run that continued
another (run.continue_from) is also read against its own starting model, the previous run's best re-fitted as its
first experiment, so its search's own contribution is read by the same rule.

Each comparison is the oracle's paired query (QueryOracle.query_paired): both models scored on the sealed
perturbations, the per-perturbation pearson_delta differences summarised as mean, paired standard error, wins and
the reading rule's verdict (a gain counts only when it exceeds twice its paired standard error and the better side
wins on more than half the perturbations), pooled and per category, each model's aggregate metrics beside it; no
single perturbation's value leaves the oracle. The visible paired comparison of the same two models
(Lab.compare_visible) is shown next to the sealed one. The tool compares no other models: the selected model is the
one the run reports (its best completed non-ensemble experiment by visible score, summary.json "best"), the additive
baseline the run's own `baseline_additive`, so nothing can be picked by a sealed score. A run scores on the sealed
set only its finalists, its best baseline by visible score and its ensemble when it ends, so its additive baseline
may never have been scored: the report names every model this tool scores on the sealed set for the first time
(no stored sealed score), and each run's own query count against its cap. The tool's oracles are its own, outside
the runs' caps, as the readings were fixed in the plan before any run. Each run's code version is recorded, and a
pair of runs on different code versions is flagged. A category with fewer than MIN_READ sealed perturbations is
reported but not read (NORMAN_PLAN.md section 3); every other category is read by the same rule as the pool.

Run directories are read only in content: predictions come from the runs' stored artifacts (Lab._predict, no plugin
code runs), the tool uses oracle instances of its own and adds nothing to a run, its database or its query log
(opening a database may let SQLite remove its empty -wal and -shm sidecar files).

    python tools/sealed_reading.py --runs runs/norman_control_w4_r0 runs/norman_control_replogle_w4_r0 \
        --out docs/results/norman_sealed_reading.md
    python tools/sealed_reading.py --from-json docs/results/norman_sealed_reading.json --out report.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.benchmark.oracle import QueryOracle  # noqa: E402  (the only sealed read: two scorings per comparison)
from genemila.lab import open_run  # noqa: E402

METRIC = "pearson_delta"
MIN_READ = 10   # a category with fewer sealed perturbations is reported, not read (NORMAN_PLAN.md section 3)
EXPECTED = "the run with the external screen above the one without, pooled and on singles"  # NORMAN_PLAN.md s. 5


def _commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True,
                              check=True).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _model(lab, rec: dict) -> dict:
    """What the report says of one model: its run's record, visible score and the sealed metrics the run stored."""
    stored = rec.get("query_metrics_json") or {}
    return {"experiment_id": rec["experiment_id"], "kind": rec["kind"], "model_type": rec.get("model_type"),
            "hypothesis_group": rec.get("hypothesis_group"), "alpha": rec.get("best_alpha"),
            "features": rec.get("feature_set_json"), "visible_score": rec.get("primary_score"),
            "stored_sealed_pearson_delta": stored.get(METRIC), "sealed_before": bool(stored)}


def _paired_query(lab_a, rec_a: dict, lab_b, rec_b: dict) -> dict:
    """The oracle's paired answer for rec_a (of lab_a) minus rec_b (of lab_b), on an oracle of the tool's own over
    lab_a's bundle (two scorings), with each model's pooled pearson_delta checked against what its run stored."""
    oracle = QueryOracle(lab_a.data_dir, max_queries=2, selection=lab_a.selection)
    perts = oracle.perts
    (pa, oa), (pb, ob) = lab_a._predict(rec_a, perts), lab_b._predict(rec_b, perts)
    out = oracle.query_paired(rec_a["experiment_id"], pa, oa, rec_b["experiment_id"], pb, ob, lab_a.control_mean,
                              metric=METRIC)
    for side, rec in (("a", rec_a), ("b", rec_b)):
        stored = (rec.get("query_metrics_json") or {}).get(METRIC)
        now = out[side]["metrics"].get(METRIC)
        out[side]["matches_stored"] = None if stored is None else bool(abs(float(stored) - float(now)) <= 1e-9)
    return out


def _selected(lab) -> dict:
    rec = lab.db.best()
    if rec is None:
        raise ValueError(f"{lab.run_dir.name} has no completed experiment")
    return rec


def _additive(lab) -> dict | None:
    rows = lab.db.query("SELECT * FROM experiments WHERE kind='baseline' AND hypothesis_group='baseline_additive' "
                        "AND status='completed' LIMIT 1")
    return rows[0] if rows else None


def _start(lab) -> tuple[dict | None, str | None]:
    """A continued run's starting model, or None and why there is none to compare. Lab.warm_start records the
    experiment it queued (warm_start.json "start_experiment"; the warm_start_<run id> hypothesis group otherwise); a
    start queued as a duplicate of an identical experiment of the run (a model baseline, say) is that experiment, and
    a start the lab rejected (an analytic baseline, which no spec can rebuild) or that failed is named as such."""
    warm = lab.run_dir / "warm_start.json"
    eid = json.loads(warm.read_text()).get("start_experiment") if warm.exists() else None
    if eid is None:
        rows = lab.db.query("SELECT experiment_id FROM experiments WHERE hypothesis_group LIKE 'warm_start_%' "
                            "ORDER BY created_at LIMIT 1")
        eid = rows[0]["experiment_id"] if rows else None
    if eid is None:
        return None, "the run recorded no starting model: nothing to compare"
    rec, seen = lab.db.get_experiment(eid), set()
    while rec is not None and rec["status"] == "duplicate" and rec.get("duplicate_of") and \
            rec["experiment_id"] not in seen:
        seen.add(rec["experiment_id"])
        rec = lab.db.get_experiment(rec["duplicate_of"])
    if rec is None:
        return None, f"the run's starting model {eid} is not in its database: nothing to compare"
    if rec["status"] != "completed":
        via = "" if rec["experiment_id"] == eid else f" (queued as {eid}, a duplicate of it)"
        return None, (f"the run's starting model {rec['experiment_id']}{via} ended with status {rec['status']}: "
                      "nothing to compare")
    return rec, None


def read_run(lab) -> dict:
    """One run: its selected model against its additive baseline, visible and sealed; for a continued run also
    against its starting model, which is what the run's own search added (NORMAN_PLAN.md section 8, N4)."""
    sel, add = _selected(lab), _additive(lab)
    out = {"run": lab.run_dir.name, "run_id": lab.run_id, "dataset": lab.dataset, "split_id": lab.split_id,
           "selection": lab.selection, "external_knowledge": list(lab.cfg["run"].get("external_knowledge") or []),
           "hash_seed": lab.cfg["run"].get("hash_seed"), "base_commit": lab.base_commit,
           "run_queries": {"used": int(lab.oracle.used), "cap": int(lab.oracle.max_queries)},
           "selected": _model(lab, sel),
           "additive": None if add is None else _model(lab, add), "visible": None, "sealed": None, "note": None}
    if add is None:
        out["note"] = "no additive baseline in this run (a bundle without pairs records none)"
    elif add["experiment_id"] == sel["experiment_id"]:
        out["note"] = "the run selected its additive baseline: nothing to compare"
    else:
        out["visible"] = lab.compare_visible(sel["experiment_id"], add["experiment_id"], metric=METRIC)
        out["sealed"] = _paired_query(lab, sel, lab, add)
    if lab.cfg["run"].get("continue_from"):
        start, why = _start(lab)
        cont = {"from": Path(lab.cfg["run"]["continue_from"]).name, "start": None if start is None else
                _model(lab, start), "visible": None, "sealed": None, "note": None}
        if start is None:
            cont["note"] = why
        elif start["experiment_id"] == sel["experiment_id"]:
            cont["note"] = "the run selected its starting model: its search added nothing it kept"
        else:
            cont["visible"] = lab.compare_visible(sel["experiment_id"], start["experiment_id"], metric=METRIC)
            cont["sealed"] = _paired_query(lab, sel, lab, start)
        out["continuation"] = cont
    return out


def _knowledge(lab) -> list[str]:
    return sorted(lab.cfg["run"].get("external_knowledge") or [])


def read_pair(lab_x, lab_y) -> dict:
    """The selected model of the run with external knowledge minus that of the run without, on the sealed
    perturbations, in whichever order the two are given; both runs must share the bundle, split, selection rule and
    control mean, so the two models answer the same question, and exactly one may record external knowledge."""
    for what, x, y in (("dataset", lab_x.dataset, lab_y.dataset), ("split", lab_x.split_id, lab_y.split_id),
                       ("selection rule", lab_x.selection, lab_y.selection),
                       ("bundle", str(Path(lab_x.data_dir).resolve()), str(Path(lab_y.data_dir).resolve()))):
        if x != y:
            raise ValueError(f"the two runs differ in {what}: {x} against {y}")
    if not np.allclose(lab_x.control_mean, lab_y.control_mean, rtol=0, atol=1e-12):
        raise ValueError("the two runs' control means differ")
    kx, ky = _knowledge(lab_x), _knowledge(lab_y)
    if bool(kx) == bool(ky):
        raise ValueError(f"exactly one of the two runs must record external knowledge (run.external_knowledge): "
                         f"{lab_x.run_dir.name} {kx or 'none'}, {lab_y.run_dir.name} {ky or 'none'}")
    lab_a, lab_b = (lab_y, lab_x) if kx else (lab_x, lab_y)   # a: without, b: with (the comparison is b minus a)
    sa, sb = _selected(lab_a), _selected(lab_b)
    return {"a": {"run": lab_b.run_dir.name, "external_knowledge": _knowledge(lab_b), "base_commit": lab_b.base_commit,
                  **_model(lab_b, sb)},
            "b": {"run": lab_a.run_dir.name, "external_knowledge": [], "base_commit": lab_a.base_commit,
                  **_model(lab_a, sa)},
            "same_code": lab_a.base_commit == lab_b.base_commit,
            "sealed": _paired_query(lab_b, sb, lab_a, sa), "expected": EXPECTED}


def analyse(run_dirs: list[Path]) -> dict:
    if not 1 <= len(run_dirs) <= 2:
        raise ValueError("give one run, or two runs on the same bundle, one of them with external knowledge")
    labs = [open_run(d) for d in run_dirs]
    try:
        runs = [read_run(lab) for lab in labs]
        pair = read_pair(labs[0], labs[1]) if len(labs) == 2 else None
    finally:
        for lab in labs:
            lab.close()
    conts = [(r["run"], r["selected"], r["continuation"]) for r in runs if (r.get("continuation") or {}).get("sealed")]
    scorings = sum(2 for r in runs if r["sealed"]) + 2 * len(conts) + (2 if pair else 0)
    compared = [(r["run"], r[k]) for r in runs if r["sealed"] for k in ("selected", "additive")]
    compared += [(run, m) for run, sel, c in conts for m in (sel, c["start"])]
    compared += [(pair[k]["run"], pair[k]) for k in ("a", "b")] if pair else []
    first = sorted({f"{run}:{m['experiment_id']}" for run, m in compared if not m["sealed_before"]})
    return {"generated_by": "tools/sealed_reading.py", "code_commit": _commit(),
            "protocol": {"metric": METRIC, "rule": "a gain counts when it exceeds twice its paired standard error "
                                                   "and the better side wins on more than half the perturbations",
                         "min_read": MIN_READ, "expected": EXPECTED if pair else None, "sealed_scorings": scorings,
                         "first_sealed_scorings": first},
            "runs": runs, "pair": pair}


# ------------------------------------------------------------------ the report
def _f(x, nd: int = 3) -> str:
    return "–" if x is None else f"{x:.{nd}f}"


def _diff(p: dict) -> str:
    if "mean_diff" not in p:
        return "–"
    nd = 3 if max(abs(p["mean_diff"]), p["se"]) >= 0.005 else 5   # a difference that rounds to zero still shows
    return f"{p['mean_diff']:+.{nd}f} ± {p['se']:.{nd}f}"


def _wins(p: dict) -> str:
    return "–" if "wins_a" not in p else f"{p['wins_a']}/{p['wins_b']}"


def _verdict(p: dict, a: str, b: str, n_read: int | None = None) -> str:
    if "verdict" not in p:
        return "too few to report"
    if n_read is not None and n_read < MIN_READ:
        return "reported, not read"
    return {"a": f"{a} better", "b": f"{b} better", "none": "no difference established"}[p["verdict"]]


def _cat_mean(metrics: dict, cat: str) -> float | None:
    e = (metrics.get("by_category") or {}).get(cat) or {}
    return (e.get(METRIC) or {}).get("mean")


def _table(sealed: dict, visible: dict | None, a: str, b: str) -> list[str]:
    """Pooled and per-category rows of one paired comparison, a minus b."""
    ma, mb, p = sealed["a"]["metrics"], sealed["b"]["metrics"], sealed["paired"]
    L = [f"| set | n | {a} | {b} | {a} − {b} (SE) | wins {a}/{b} | verdict |", "|---|---|---|---|---|---|---|"]
    L.append(f"| sealed, pooled | {p['n']} | {_f(ma.get(METRIC))} | {_f(mb.get(METRIC))} | {_diff(p)} | "
             f"{_wins(p)} | {_verdict(p, a, b)} |")
    for cat, pc in (p.get("by_category") or {}).items():
        L.append(f"| sealed, {cat} | {pc['n']} | {_f(_cat_mean(ma, cat))} | {_f(_cat_mean(mb, cat))} | {_diff(pc)} | "
                 f"{_wins(pc)} | {_verdict(pc, a, b, pc['n'])} |")
    if visible:
        L.append(f"| visible and out-of-fold, pooled | {visible['n']} | | | {_diff(visible)} | {_wins(visible)} | "
                 f"{_verdict(visible, a, b)} |")
        for cat, pc in (visible.get("by_category") or {}).items():
            L.append(f"| visible and out-of-fold, {cat} | {pc['n']} | | | {_diff(pc)} | {_wins(pc)} | "
                     f"{_verdict(pc, a, b)} |")
    return L


def _other_metrics(sealed: dict, a: str, b: str) -> str:
    keys = [("cellforge_mse_de", "MSE_DE"), ("cellforge_pcc_de", "PCC_DE"), ("cellforge_r2_de", "R²_DE"),
            ("pearson_delta_nontarget", "pearson_delta without own targets")]
    ma, mb = sealed["a"]["metrics"], sealed["b"]["metrics"]
    parts = [f"{name} {_f(ma.get(k))} against {_f(mb.get(k))}" for k, name in keys if k in ma and k in mb]
    return f"Other sealed metrics, {a} against {b}: " + "; ".join(parts) + "." if parts else ""


def _check(sealed: dict) -> str:
    """The reproduction check: each model's pooled sealed pearson_delta here against what its run stored."""
    bad = [sealed[s]["experiment_id"] for s in ("a", "b") if sealed[s].get("matches_stored") is False]
    none = [sealed[s]["experiment_id"] for s in ("a", "b") if sealed[s].get("matches_stored") is None]
    out = ""
    if bad:
        out += (f" The oracle's pooled pearson_delta differs from what the run stored for {', '.join(bad)}: read "
                "nothing until that is explained.")
    if none:
        out += f" No stored sealed score to check for {', '.join(none)} (scored on the sealed set here first)."
    return out


def _scorings(rep: dict) -> str:
    pr = rep["protocol"]
    first = pr.get("first_sealed_scorings") or []
    text = f"The tool made {pr['sealed_scorings']} sealed scorings on oracles of its own, outside the runs' caps"
    if first:
        return (text + f"; {len(first)} of the compared models had never been scored on the sealed set and are scored "
                f"here for the first time ({', '.join(first)}); every other one was scored when its run ended.")
    return text + "; every compared model was already scored on the sealed set when its run ended."


def _category_sentences(paired: dict, a: str, b: str) -> str:
    """The reading of every category: by the rule when it holds at least MIN_READ perturbations, else reported only."""
    parts = []
    for cat, pc in (paired.get("by_category") or {}).items():
        if "verdict" not in pc:
            parts.append(f"{cat} (n {pc['n']}) too few to report")
        elif pc["n"] < MIN_READ:
            parts.append(f"{cat} (n {pc['n']}) reported, not read")
        else:
            parts.append(f"{cat} {_sentence(pc, a, b)}")
    return "; ".join(parts)


def render(rep: dict) -> str:
    pr = rep["protocol"]
    expected = f" Expected direction, fixed before any run: {pr['expected']}." if pr.get("expected") else ""
    L = ["# Sealed reading", "",
         f"Pre-specified (docs/NORMAN_PLAN.md section 5). Metric {pr['metric']} per sealed perturbation, paired. "
         f"Reading rule, pooled and in every category: {pr['rule']}; a category with fewer than {pr['min_read']} "
         f"sealed perturbations is reported, not read.{expected} {_scorings(rep)} Wins are counted per perturbation; "
         "the visible and out-of-fold rows pair the same models on the visible validation perturbations and, out of fold, "
         "the training ones. "
         f"Tool code {str(rep.get('code_commit') or 'unknown')[:7]}.", ""]
    for r in rep["runs"]:
        s, a = r["selected"], r["additive"]
        ext = ", ".join(r["external_knowledge"]) or "none"
        q = r.get("run_queries") or {}
        L += [f"## {r['run']}: selected model against the additive baseline", "",
              f"Selected {s['experiment_id']} ({s['model_type']}, {len(s['features'] or [])} features, visible "
              f"{_f(s['visible_score'])}); additive baseline "
              + (f"{a['experiment_id']} (visible {_f(a['visible_score'])})" if a else "none")
              + f". External knowledge: {ext}. Code {str(r.get('base_commit') or 'unknown')[:7]}; hash seed "
              f"recorded: {r['hash_seed']}; the run's own sealed queries: {q.get('used')} of {q.get('cap')}.", ""]
        if r["sealed"] is None:
            L += [r["note"] or "No comparison.", ""]
            continue
        L += _table(r["sealed"], r["visible"], "selected", "additive") + [""]
        line = _other_metrics(r["sealed"], "selected", "additive") + _check(r["sealed"])
        L += ([line.strip(), ""] if line else [])
    for r in rep["runs"]:
        c = r.get("continuation")
        if not c:
            continue
        st = c["start"]
        L += [f"## {r['run']}: selected model against its starting model", "",
              f"The run continued {c['from']}; its starting model "
              + (f"{st['experiment_id']} ({len(st['features'] or [])} features, visible {_f(st['visible_score'])})"
                 if st else "is not available")
              + f", selected {r['selected']['experiment_id']}. The difference is what the run's own search added.", ""]
        if c["sealed"] is None:
            L += [c["note"] or "No comparison.", ""]
            continue
        L += _table(c["sealed"], c["visible"], "selected", "start") + [""]
        line = _other_metrics(c["sealed"], "selected", "start") + _check(c["sealed"])
        L += ([line.strip(), ""] if line else [])
    p = rep.get("pair")
    if p:
        a, b = p["a"], p["b"]
        code = ("both on code " + str(a.get("base_commit") or "unknown")[:7] if p.get("same_code") else
                f"on different code ({str(a.get('base_commit') or 'unknown')[:7]} with the screen, "
                f"{str(b.get('base_commit') or 'unknown')[:7]} without), so the difference mixes the screen with "
                "a code change")
        L += [f"## {a['run']} (with {', '.join(a['external_knowledge'])}) against {b['run']} (without): selected "
              "models", "",
              f"With the screen: {a['experiment_id']} (visible {_f(a['visible_score'])}); without: {b['experiment_id']} "
              f"(visible {_f(b['visible_score'])}); {code}. Expected: {p['expected']}.", ""]
        L += _table(p["sealed"], None, "with screen", "without") + [""]
        line = _other_metrics(p["sealed"], "with screen", "without") + _check(p["sealed"])
        L += ([line.strip(), ""] if line else [])
    L += ["## Reading", "", _reading(rep)]
    return "\n".join(L) + "\n"


def _sentence(paired: dict, a: str, b: str) -> str:
    if "verdict" not in paired:
        return f"{a} minus {b}: too few perturbations to report"
    return (f"{a} minus {b} {_diff(paired)} paired SE, {a} better on {paired['wins_a']} and worse on "
            f"{paired['wins_b']} of {paired['n']}: {_verdict(paired, a, b)}")


def _reading(rep: dict) -> str:
    parts = []
    for r in rep["runs"]:
        if r["sealed"]:
            pp = r["sealed"]["paired"]
            parts.append(f"{r['run']}, sealed pooled: {_sentence(pp, 'selected', 'additive')}; by category: "
                         f"{_category_sentences(pp, 'selected', 'additive')}.")
        c = r.get("continuation") or {}
        if c.get("sealed"):
            pp = c["sealed"]["paired"]
            parts.append(f"{r['run']} against its starting model, sealed pooled: {_sentence(pp, 'selected', 'start')}"
                         f"; by category: {_category_sentences(pp, 'selected', 'start')}.")
        elif c:
            parts.append(f"{r['run']} against its starting model: {c['note']}.")
    p = rep.get("pair")
    if p:
        pp = p["sealed"]["paired"]
        single = (pp.get("by_category") or {}).get("single") or {}
        single_txt = (_sentence(single, "with screen", "without") if single.get("n", 0) >= MIN_READ
                      else "reported, not read" if single else "none")
        parts.append(f"{p['a']['run']} against {p['b']['run']}, sealed pooled: "
                     f"{_sentence(pp, 'with screen', 'without')}; on singles: {single_txt}; by category: "
                     f"{_category_sentences(pp, 'with screen', 'without')}. Expected: {p['expected']}"
                     + ("." if p.get("same_code") else "; the two runs ran on different code."))
    parts.append(f"Each verdict follows the rule as stated, pooled and in every category of at least {MIN_READ} "
                 "sealed perturbations; smaller categories are reported, not read.")
    return " ".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", nargs="*", default=[], help="one run, or two runs on the same bundle (second minus first)")
    ap.add_argument("--out", required=True, help="markdown report")
    ap.add_argument("--json", default=None, help="JSON twin (default: the report's path with .json)")
    ap.add_argument("--from-json", default=None, help="re-render the markdown from a JSON twin; no run is opened")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.from_json:
        rep = json.loads(Path(args.from_json).read_text())
    else:
        if not args.runs:
            ap.error("--runs is required unless --from-json is given")
        rep = json.loads(json.dumps(analyse([Path(r) for r in args.runs]), default=float))
        Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1))
    md = render(rep)
    out.write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
