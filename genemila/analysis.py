"""Scaling analysis of a finished run: independence of workers, throughput,
token use and cost, bottlenecks, duplicated work and cost projections."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from .lab import Lab


def _max_overlap(intervals: list[tuple[float, float]]) -> int:
    events = sorted([(s, 1) for s, _ in intervals] + [(e, -1) for _, e in intervals])
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best


def analyze(lab: Lab, project_workers=(8, 16, 44), project_hours=(1, 6)) -> dict:
    db = lab.db
    run = db.query("SELECT * FROM runs LIMIT 1")[0]
    exps = db.query("SELECT * FROM experiments WHERE COALESCE(kind, '') NOT IN ('baseline', 'ensemble') "
                    "AND status NOT IN ('reserved','cancelled')")
    calls = db.query("SELECT * FROM llm_calls")
    workers = sorted({e["worker_id"] for e in exps if e.get("worker_id")})
    t0 = min([run["started_at"]] + [c["ts"] - (c["latency_s"] or 0) for c in calls])
    t1 = max([e.get("finished_at") or 0 for e in exps] + [run.get("finished_at") or 0] + [c["ts"] for c in calls])
    minutes = max((t1 - t0) / 60, 1e-9)

    per_worker = defaultdict(lambda: {"experiments": [], "llm_calls": 0, "commits": set()})
    for e in exps:
        if e.get("worker_id"):
            w = per_worker[e["worker_id"]]
            w["experiments"].append(e["experiment_id"])
            if e.get("code_commit"):
                w["commits"].add(e["code_commit"])
    for c in calls:
        if c.get("worker_id"):
            per_worker[c["worker_id"]]["llm_calls"] += 1
    intervals = [(e["started_at"], e["finished_at"]) for e in exps if e.get("started_at") and e.get("finished_at")]
    commits = [e["code_commit"] for e in exps if e.get("code_commit") and e["kind"] == "new_feature"]
    exp_workers = defaultdict(set)
    for c in calls:
        if c["experiment_id"]:
            exp_workers[c["experiment_id"]].add(c["worker_id"])

    worker_calls = [c for c in calls if c["role"] == "worker"]
    tot = lambda rows, k: sum((r.get(k) or 0) for r in rows)  # noqa: E731
    w_cost, p_cost = tot(worker_calls, "cost_usd"), tot([c for c in calls if c["role"] == "planner"], "cost_usd")
    completed = [e for e in exps if e["status"] == "completed"]
    llm_latency = tot(worker_calls, "latency_s")
    exp_wall = tot(exps, "wall_s")
    cpu = tot(exps, "cpu_s")
    planner_latency = tot([c for c in calls if c["role"] == "planner"], "latency_s")

    # duplicated work: same hypothesis group with near-identical outcomes, or identical configurations
    groups = defaultdict(list)
    for e in exps:
        groups[e.get("hypothesis_group")].append(e)
    dup_groups = []
    for g, rows in groups.items():
        scores = [r["primary_score"] for r in rows if r["primary_score"] is not None]
        if len(rows) > 1:
            dup_groups.append({"group": g, "experiments": [r["experiment_id"] for r in rows],
                               "scores": [round(s, 4) for s in scores],
                               "identical_outcome": len(scores) > 1 and max(scores) - min(scores) < 1e-6})
    same_score_as_parent = [e["experiment_id"] for e in completed
                            if e["delta_from_parent"] is not None and abs(e["delta_from_parent"]) < 1e-9]

    n_workers = max(1, int(run.get("workers") or len(workers) or 1))
    cost_per_worker_min = w_cost / n_workers / minutes
    proj = {f"{w}_workers_{h}h": round(cost_per_worker_min * w * 60 * h, 4)
            for w in project_workers for h in project_hours}
    planner_per_min = p_cost / minutes
    return {
        "run_id": lab.run_id, "minutes": round(minutes, 2), "workers_configured": n_workers,
        "independence": {
            "distinct_workers_used": len(workers),
            "per_worker": {w: {"experiments": v["experiments"], "llm_calls": v["llm_calls"],
                               "distinct_commits": len(v["commits"])} for w, v in sorted(per_worker.items())},
            "max_concurrent_experiments": _max_overlap(intervals),
            "every_new_feature_own_commit": len(commits) == len(set(commits)),
            "experiments_touched_by_multiple_workers": [e for e, ws in exp_workers.items() if len(ws) > 1],
        },
        "experiments": [{"id": e["experiment_id"], "worker": e.get("worker_id"), "kind": e["kind"],
                         "status": e["status"], "feature": e.get("new_feature"),
                         "hypothesis": e["hypothesis"][:120], "score": e["primary_score"],
                         "delta": e["delta_from_parent"], "failure": (e.get("failure_reason") or "")[:160],
                         "llm_calls": e.get("llm_calls"), "cost_usd": round(e.get("llm_cost_usd") or 0, 6)}
                        for e in exps],
        "status_counts": dict(Counter(e["status"] for e in exps)),
        "tokens": {"worker": {k: tot(worker_calls, k) for k in ("input_tokens", "output_tokens", "cached_tokens")},
                   "planner": {k: tot([c for c in calls if c["role"] == "planner"], k)
                               for k in ("input_tokens", "output_tokens", "cached_tokens")}},
        "cost_usd": {"worker": round(w_cost, 6), "planner": round(p_cost, 6)},
        "worker_cost_per_completed_experiment": round(w_cost / max(1, len(completed)), 6),
        "experiments_per_minute": round(len(completed) / minutes, 3),
        "time_breakdown_s": {"worker_llm_latency": round(llm_latency, 1), "experiment_wall": round(exp_wall, 1),
                             "experiment_cpu": round(cpu, 1), "planner_latency": round(planner_latency, 1),
                             "worker_capacity": round(n_workers * minutes * 60, 1)},
        "llm_share_of_worker_time": round(llm_latency / max(exp_wall, 1e-9), 3),
        "worker_utilisation": round(exp_wall / max(n_workers * minutes * 60, 1e-9), 3),
        "duplicated_work": {"replicate_groups": dup_groups, "no_change_vs_parent": same_score_as_parent},
        "projection_worker_cost_usd": proj,
        "projection_planner_cost_usd_per_hour": round(planner_per_min * 60, 4),
        "projection_note": ("Linear in workers x time from measured worker-LLM spend per worker-minute; the planner "
                            "is called when the queue runs low, so its cost grows sub-linearly with workers."),
    }


def render(a: dict) -> str:
    L = [f"# Scaling analysis: {a['run_id']} ({a['workers_configured']} workers, {a['minutes']} min)", ""]
    ind = a["independence"]
    L += ["## 1. Independence",
          f"- distinct workers used: {ind['distinct_workers_used']}; max concurrent experiments: "
          f"{ind['max_concurrent_experiments']}",
          f"- every LLM-written feature in its own worktree commit: {ind['every_new_feature_own_commit']}; "
          f"experiments touched by >1 worker: {ind['experiments_touched_by_multiple_workers'] or 'none'}"]
    L += [f"- {w}: {v['experiments']} ({v['llm_calls']} LLM calls)" for w, v in ind["per_worker"].items()]
    L += ["", "## 2-3. Experiments", "| id | worker | status | feature / change | score | delta | LLM calls | cost |",
          "|---|---|---|---|---|---|---|---|"]
    for e in a["experiments"]:
        what = e["feature"] or e["hypothesis"][:50]
        sc = "" if e["score"] is None else f"{e['score']:.4f}"
        de = "" if e["delta"] is None else f"{e['delta']:+.4f}"
        L.append(f"| {e['id']} | {e['worker']} | {e['status']} | {what} | {sc} | {de} | {e['llm_calls']} | ${e['cost_usd']:.5f} |")
        if e["failure"]:
            L.append(f"|  |  | ↳ | {e['failure']} |  |  |  |  |")
    t = a["tokens"]
    L += ["", "## 4. Tokens",
          f"- workers: {t['worker']['input_tokens']} in ({t['worker']['cached_tokens']} cached) / {t['worker']['output_tokens']} out",
          f"- planner: {t['planner']['input_tokens']} in ({t['planner']['cached_tokens']} cached) / {t['planner']['output_tokens']} out",
          "", "## 5-7. Cost and throughput",
          f"- worker LLM cost: ${a['cost_usd']['worker']:.5f}; planner: ${a['cost_usd']['planner']:.5f}",
          f"- worker cost per completed experiment: ${a['worker_cost_per_completed_experiment']:.5f}",
          f"- completed experiments per minute: {a['experiments_per_minute']}",
          "", "## 8. Bottlenecks and duplicated work",
          f"- time: {json.dumps(a['time_breakdown_s'])}",
          f"- LLM latency share of experiment time: {a['llm_share_of_worker_time']:.0%}; worker utilisation: "
          f"{a['worker_utilisation']:.0%}"]
    for g in a["duplicated_work"]["replicate_groups"]:
        L.append(f"- replicate group {g['experiments']}: scores {g['scores']}"
                 + (" (identical outcome: duplicated work)" if g["identical_outcome"] else ""))
    if a["duplicated_work"]["no_change_vs_parent"]:
        L.append(f"- no change vs parent: {a['duplicated_work']['no_change_vs_parent']}")
    L += ["", "## 9. Projection (worker LLM cost)"]
    L += [f"- {k.replace('_', ' ')}: ${v:.2f}" for k, v in a["projection_worker_cost_usd"].items()]
    L += [f"- planner: about ${a['projection_planner_cost_usd_per_hour']:.2f}/hour at the measured call rate",
          f"- {a['projection_note']}"]
    return "\n".join(L)
