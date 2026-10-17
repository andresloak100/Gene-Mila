#!/usr/bin/env python3
"""One command for an agent taking over: the live state of this checkout, its runs, the spend ledger and
the comparison driver, read from disk rather than from anyone's memory.

    python handoff_state.py [--runs runs] [--ledger runs/spend_ledger.sqlite] [--logs DIR] [--json]

Prints, as Markdown (or JSON with --json): the git state; every run directory with its arm, code commit
and state (finished with a summary, in progress, killed before its summary, contaminated or interrupted)
and its headline numbers; spend per provider from the shared ledger; whether a lab run or driver process
is alive; and the tail of the driver's progress file plus the latest notes in STATE.md (the state whoever runs something on
the machine writes there) when a log directory is given or found.
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import time
from pathlib import Path

from genemila import REPO_ROOT
from genemila.benchmark.table import run_arm

# The Mac keeps the lab in ~/Documents/Mila/Gene-Mila (moved out of ~/Documents/Loak-documents on 11 Oct 2026): the
# log directory beside this checkout, else the one there.
LOG_DIRS = (REPO_ROOT.parent / "genemila_scale_logs",
            Path.home() / "Documents" / "Mila" / "Gene-Mila" / "genemila_scale_logs")


def sh(*cmd, cwd=None) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


INTEGRATION_BRANCH = "claude/autonomous-research-system-3k435s"


def git_state(repo: Path, fetch: bool = False) -> dict:
    """Branch, head, dirty files, and how far HEAD is from the integration branch as last fetched (an agent
    in a stale clone sees "behind by N"); --fetch refreshes the remote ref first."""
    if fetch:
        sh("git", "fetch", "-q", "origin", INTEGRATION_BRANCH, cwd=repo)
    remote = f"origin/{INTEGRATION_BRANCH}"
    counts = sh("git", "rev-list", "--left-right", "--count", f"HEAD...{remote}", cwd=repo).split()
    ahead, behind = (int(counts[0]), int(counts[1])) if len(counts) == 2 else (None, None)
    return {"branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=repo),
            "head": sh("git", "rev-parse", "--short", "HEAD", cwd=repo),
            "dirty_files": len([l for l in sh("git", "status", "--porcelain", cwd=repo).splitlines() if l.strip()]),
            "last_commit": sh("git", "log", "-1", "--format=%h %cd %s", "--date=iso-strict", cwd=repo),
            "integration_branch": INTEGRATION_BRANCH,
            "integration_head": sh("git", "rev-parse", "--short", remote, cwd=repo) or None,
            "integration_fetched": sh("git", "log", "-1", "--format=%cd", "--date=iso-strict", remote, cwd=repo) or None,
            "ahead": ahead, "behind": behind, "fetched_now": fetch}


def is_paid(cfg: dict) -> bool:
    """A run that can spend money: an LLM worker, or an LLM planner (anything but mock / scripted)."""
    w = (cfg.get("worker") or {}).get("provider")
    p = (cfg.get("planner") or {}).get("provider")
    return bool(cfg) and (w not in ("mock", None) or p not in ("scripted", "loadtest", "mock", None))


def ledger_of(cfg: dict, run_dir: Path) -> Path | None:
    raw = (cfg.get("budget") or {}).get("ledger")
    if not raw:
        return None
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def stop_evidence(logs: Path | None, run_names: set[str]) -> tuple[dict, set[str], list[str]]:
    """Read explicit, small operational markers, never run logs or their sealed-score tails.

    Return standardized reasons, runs whose evidence could not be checked, and safe warnings.
    Marker contents and exception messages are deliberately not copied into the report.
    """
    evidence, incomplete, warnings = {}, set(), []
    if logs is None:
        return evidence, incomplete, warnings
    try:
        markers = sorted(p for p in logs.iterdir() if
                         ("_stopped" in p.name and p.name.endswith(".txt")) or
                         (p.name.endswith(".backstop.txt") and p.name[:-13] in run_names))
    except OSError:
        return {}, set(run_names), ["Cannot inspect stop evidence directory; run status is unverified."]
    record = re.compile(r"^(?:\d{4}-\d{2}-\d{2}T\S+\s+)?([^:\s]+):\s*(.*)$")
    for path in markers:
        backstop_run = path.name[:-13] if path.name.endswith(".backstop.txt") else None
        affected = {backstop_run} if backstop_run else run_names
        try:
            with path.open() as f:
                content = f.read(65537)
            if len(content) > 65536:
                raise ValueError("stop marker too large")
        except (OSError, UnicodeError, ValueError):
            incomplete.update(affected)
            warnings.append(f"Cannot read stop evidence {path.name}; affected run status is unverified.")
            continue
        matched = False
        for line in content.splitlines():
            match = record.match(line)
            if not match or match[1] not in run_names or (backstop_run and match[1] != backstop_run):
                continue
            if backstop_run and not re.search(r"\bterminated\b", match[2], re.IGNORECASE):
                continue
            matched = True
            reason = "block stop recorded"
            if backstop_run:
                reason = "backstop termination recorded"
            elif re.search(r"\b(killed|interrupted)\b", match[2], re.IGNORECASE):
                reason = "killed or interrupted"
            item = {"reason": reason, "file": path.name}
            if item not in evidence.setdefault(match[1], []):
                evidence[match[1]].append(item)
        if backstop_run and not matched:
            incomplete.add(backstop_run)
            warnings.append(f"No matching run identity in {path.name}; run status is unverified.")
    return evidence, incomplete, warnings


def run_state(d: Path, shared_ledger: Path | None = None, evidence: list[dict] | None = None,
              evidence_incomplete: bool = False) -> dict:
    name = d.name
    cfg = json.loads((d / "config.json").read_text()) if (d / "config.json").exists() else {}
    out = {"dir": name, "arm": run_arm(cfg) if cfg else "?", "workers": cfg.get("run", {}).get("workers"),
           "seed": cfg.get("run", {}).get("seed"), "dataset": cfg.get("run", {}).get("dataset") or cfg.get("run", {}).get("data_dir"),
           "paid": is_paid(cfg), "ledger_ok": None}
    if out["paid"] and shared_ledger is not None:  # a paid run outside the shared ledger bypasses the cumulative cap
        mine = ledger_of(cfg, d)
        out["ledger_ok"] = mine is not None and mine == shared_ledger.resolve()
        if not out["ledger_ok"]:
            out["ledger"] = None if mine is None else str(mine)
    if name.endswith("_contaminated") or name.endswith("_interrupted"):
        out["state"] = "excluded (" + name.rsplit("_", 1)[1] + ")"
    summary = d / "summary.json"
    if evidence or evidence_incomplete:
        details = list(dict.fromkeys(e["reason"] for e in evidence or []))
        if evidence_incomplete:
            details.append("stop evidence unavailable")
        details.append("summary exists" if summary.exists() else "no summary")
        if evidence:
            out["stop_evidence"] = evidence
            details.append("evidence: " + ", ".join(dict.fromkeys(e["file"] for e in evidence)))
        status = ("stopped" if evidence else "status unverified") + " (" + "; ".join(details) + ")"
        out["state"] = out["state"] + "; " + status if "state" in out else status
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
    ap.add_argument("--logs", default=None, help="driver log directory with progress.md (default: the first of LOG_DIRS that exists)")
    ap.add_argument("--fetch", action="store_true", help="fetch the integration branch first (needs network)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    runs_dir = Path(args.runs)
    ledger = Path(args.ledger) if args.ledger else runs_dir / "spend_ledger.sqlite"
    logs = Path(args.logs) if args.logs else next((d for d in LOG_DIRS if d.exists()), None)
    run_dirs = sorted(d for d in runs_dir.iterdir() if d.is_dir()) if runs_dir.exists() else []
    evidence, incomplete, evidence_warnings = stop_evidence(logs, {d.name for d in run_dirs})
    runs = [run_state(d, ledger, evidence.get(d.name), d.name in incomplete) for d in run_dirs]
    state_file = logs / "STATE.md" if logs and (logs / "STATE.md").exists() else None
    state_lines = state_file.read_text().splitlines() if state_file else []
    state = {"checked_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "repo": str(REPO_ROOT),
             "git": git_state(REPO_ROOT, fetch=args.fetch), "runs": runs, "ledger": ledger_totals(ledger), "ledger_path": str(ledger),
             "ledger_bypass": [r["dir"] for r in runs if r.get("paid") and r.get("ledger_ok") is False],
             "processes": processes(),
             "progress_tail": (logs / "progress.md").read_text().splitlines()[-15:] if logs and (logs / "progress.md").exists() else [],
             "state_file": str(state_file) if state_file else None,
             "state_head": state_lines[:40], "state_tail": state_lines[-40:],
             "stop_evidence_warnings": evidence_warnings,
             "stop_file": bool(logs and (logs / "STOP").exists())}
    if args.json:
        print(json.dumps(state, indent=1, default=str))
        return
    g = state["git"]
    if g["integration_head"] is None:
        sync = f"no local copy of origin/{g['integration_branch']} (run `git fetch origin {g['integration_branch']}`)"
    elif g["ahead"] == 0 and g["behind"] == 0:
        sync = f"level with origin/{g['integration_branch']} ({g['integration_head']})"
    else:
        sync = (f"ahead by {g['ahead']} and behind by {g['behind']} commit(s) against origin/{g['integration_branch']} "
                f"({g['integration_head']})")
    sync += " as fetched just now" if g["fetched_now"] else f", as last fetched (its newest commit is from {g['integration_fetched']})"
    L = [f"# Handoff state, {state['checked_at']}", "", f"Checkout `{state['repo']}`: branch `{g['branch']}` at `{g['head']}`, "
         f"{g['dirty_files']} uncommitted file(s); last commit {g['last_commit']}.", f"HEAD is {sync}.", ""]
    L += ["## Runs", "", "| run | arm | workers | seed | code | state | completed | best visible | best sealed | worker $ |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        f = lambda v, nd=4: "" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))
        L.append(f"| {r['dir']} | {r['arm']} | {f(r.get('workers'))} | {f(r.get('seed'))} | {r.get('code', '')} | {r['state']} | "
                 f"{f(r.get('completed'))} | {f(r.get('best_visible'))} | {f(r.get('best_sealed'))} | {f(r.get('worker_usd'), 2)} |")
    if not runs:
        L.append("(no run directories)")
    for warning in state["stop_evidence_warnings"]:
        L += ["", "**WARNING:** " + warning]
    if state["ledger_bypass"]:
        L += ["", "**WARNING: paid runs not on the shared ledger** (their spend does not count toward the cumulative cap): "
              + ", ".join(f"{r['dir']} (ledger: {r.get('ledger') or 'none'})" for r in runs if r["dir"] in state["ledger_bypass"])]
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
    if state["state_tail"]:
        L += ["", f"## Latest appended state notes (`{state['state_file']}`, last 40 lines)", ""] + state["state_tail"]
    print("\n".join(L))


if __name__ == "__main__":
    main()
