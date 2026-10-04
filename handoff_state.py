#!/usr/bin/env python3
"""One command for an agent taking over: the live state of this checkout, its runs, the spend ledger and
the comparison driver, read from disk rather than from anyone's memory.

    python handoff_state.py [--runs runs] [--ledger runs/spend_ledger.sqlite] [--logs DIR] [--json]

Prints, as Markdown (or JSON with --json): the git state; every run directory with its arm, code commit
and state (finished with a summary, in progress, killed before its summary, contaminated or interrupted)
and its headline numbers; spend per provider from the shared ledger; whether a lab run or driver process
is alive; and the tail of the driver's progress file plus the head of STATE.md (the state whoever runs something on
the machine writes there) when a log directory is given or found.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path

from genemila import REPO_ROOT
from genemila.benchmark.table import run_arm

DEFAULT_LOGS = Path.home() / "Documents" / "Loak-documents" / "genemila_scale_logs"


def sh(*cmd, cwd=None) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def git_state(repo: Path) -> dict:
    return {"branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=repo),
            "head": sh("git", "rev-parse", "--short", "HEAD", cwd=repo),
            "dirty_files": len([l for l in sh("git", "status", "--porcelain", cwd=repo).splitlines() if l.strip()]),
            "last_commit": sh("git", "log", "-1", "--format=%h %cd %s", "--date=iso-strict", cwd=repo)}


def run_state(d: Path) -> dict:
    name = d.name
    cfg = json.loads((d / "config.json").read_text()) if (d / "config.json").exists() else {}
    out = {"dir": name, "arm": run_arm(cfg) if cfg else "?", "workers": cfg.get("run", {}).get("workers"),
           "seed": cfg.get("run", {}).get("seed"), "dataset": cfg.get("run", {}).get("dataset") or cfg.get("run", {}).get("data_dir")}
    if name.endswith("_contaminated") or name.endswith("_interrupted"):
        out["state"] = "excluded (" + name.rsplit("_", 1)[1] + ")"
    summary = d / "summary.json"
    if summary.exists():
        s = json.loads(summary.read_text())
        out.setdefault("state", "finished")
        out["arm"] = run_arm(cfg, s) if cfg else out["arm"]
        out["workers"] = out.get("workers") or s.get("workers")
        ph = s.get("planner") or {}
        if ph.get("exhausted_at_min") is not None:
            out["state"] += f" (lost its planner after {ph['exhausted_at_min']} min; planners used: " + (
                " -> ".join(ph.get("used") or []) or "none") + ")"
        elif ph.get("mixed"):
            out["state"] += " (planner changed mid-run: " + " -> ".join(ph.get("used") or []) + ")"
        gen = s.get("generalization_query_only") or []
        head = next((g for g in gen if g.get("kind") != "baseline"), None)
        out.update({"code": (s.get("base_commit") or "")[:7], "duration_min": round((s.get("duration_s") or 0) / 60, 1),
                    "completed": s.get("experiments_completed"), "best_visible": (s.get("best") or {}).get("score"),
                    "best_sealed": None if head is None else head.get("query_only_score"),
                    "worker_usd": ((s.get("llm_usage") or {}).get("worker") or {}).get("cost_usd"),
                    "duration_note": s.get("duration_note")})
        return out
    db = d / "lab.db"
    if not db.exists():
        out.setdefault("state", "empty (no database)")
        return out
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        run = c.execute("SELECT started_at, deadline, finished_at, base_commit FROM runs LIMIT 1").fetchone()
        counts = dict(c.execute("SELECT status, COUNT(*) FROM experiments GROUP BY status").fetchall())
        c.close()
    except sqlite3.Error as exc:
        out.setdefault("state", f"unreadable database ({exc})")
        return out
    if run is None:
        out.setdefault("state", "empty (no run row)")
        return out
    started, deadline, finished, commit = run
    out["code"] = (commit or "")[:7]
    out["completed"] = counts.get("completed", 0)
    if finished:
        out.setdefault("state", "finished without a summary (run summarize.py)")
    elif deadline and time.time() < deadline:
        out.setdefault("state", f"in progress, {max(0, deadline - time.time()) / 60:.0f} min to its deadline")
    else:
        out.setdefault("state", "killed before its summary (summarize.py --query-only recovers it if it reached its deadline)")
    return out


def ledger_totals(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        rows = c.execute("SELECT provider, role, ROUND(SUM(cost_usd), 4), COUNT(*) FROM spend GROUP BY provider, role").fetchall()
        c.close()
    except sqlite3.Error:
        return {}
    return {f"{p}/{r}": {"usd": usd, "calls": n} for p, r, usd, n in rows}


def processes() -> list[str]:
    out = sh("pgrep", "-fl", "run_research.py")
    return [l for l in out.splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=str(REPO_ROOT / "runs"))
    ap.add_argument("--ledger", default=None, help="shared spend ledger (default: <runs>/spend_ledger.sqlite)")
    ap.add_argument("--logs", default=None, help="driver log directory with progress.md (default: the Mac's, if present)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    runs_dir = Path(args.runs)
    ledger = Path(args.ledger) if args.ledger else runs_dir / "spend_ledger.sqlite"
    logs = Path(args.logs) if args.logs else (DEFAULT_LOGS if DEFAULT_LOGS.exists() else None)
    runs = sorted((run_state(d) for d in runs_dir.iterdir() if d.is_dir()), key=lambda r: r["dir"]) if runs_dir.exists() else []
    state = {"checked_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "repo": str(REPO_ROOT),
             "git": git_state(REPO_ROOT), "runs": runs, "ledger": ledger_totals(ledger), "ledger_path": str(ledger),
             "processes": processes(),
             "progress_tail": (logs / "progress.md").read_text().splitlines()[-15:] if logs and (logs / "progress.md").exists() else [],
             "state_file": str(logs / "STATE.md") if logs and (logs / "STATE.md").exists() else None,
             "state_head": (logs / "STATE.md").read_text().splitlines()[:40] if logs and (logs / "STATE.md").exists() else [],
             "stop_file": bool(logs and (logs / "STOP").exists())}
    if args.json:
        print(json.dumps(state, indent=1, default=str))
        return
    g = state["git"]
    L = [f"# Handoff state, {state['checked_at']}", "", f"Checkout `{state['repo']}`: branch `{g['branch']}` at `{g['head']}`, "
         f"{g['dirty_files']} uncommitted file(s); last commit {g['last_commit']}.", ""]
    L += ["## Runs", "", "| run | arm | workers | seed | code | state | completed | best visible | best sealed | worker $ |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        f = lambda v, nd=4: "" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))
        L.append(f"| {r['dir']} | {r['arm']} | {f(r.get('workers'))} | {f(r.get('seed'))} | {r.get('code', '')} | {r['state']} | "
                 f"{f(r.get('completed'))} | {f(r.get('best_visible'))} | {f(r.get('best_sealed'))} | {f(r.get('worker_usd'), 2)} |")
    if not runs:
        L.append("(no run directories)")
    L += ["", "## Spend ledger", "", f"`{state['ledger_path']}`"]
    total = 0.0
    for k, v in sorted(state["ledger"].items()):
        L.append(f"- {k}: ${v['usd']:.2f} over {v['calls']} calls")
        total += v["usd"] or 0
    L.append(f"- total: ${total:.2f}" if state["ledger"] else "- no ledger found")
    L += ["", "## Processes", ""] + ([f"- {p}" for p in state["processes"]] or ["- no lab run or driver process is alive"])
    if state["stop_file"]:
        L.append("- a STOP file is present: the driver halts after its current step")
    if state["progress_tail"]:
        L += ["", "## Driver progress (tail)", ""] + state["progress_tail"]
    if state["state_head"]:
        L += ["", f"## State written on the machine (`{state['state_file']}`, first 40 lines)", ""] + state["state_head"]
    print("\n".join(L))


if __name__ == "__main__":
    main()
