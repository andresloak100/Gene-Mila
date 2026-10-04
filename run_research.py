#!/usr/bin/env python3
"""Run the autonomous laboratory under a hard wall-clock budget.

    python run_research.py --minutes 20 --workers 4
    python run_research.py --hours 6 --workers 44
    python run_research.py --minutes 5 --workers 4 --worker-provider mock --planner-provider scripted

The deadline is enforced twice: by the in-process controller (graceful
shutdown) and by this script acting as an external watchdog that kills the
whole lab process group if it overruns, then writes the summary itself.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from genemila import REPO_ROOT
from genemila.config import load_config, set_dotted


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--hours", type=float)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--cpu-slots", type=int)
    ap.add_argument("--config", help="TOML file merged over configs/default.toml")
    ap.add_argument("--dataset", help="dataset name under data/ (default from config)")
    ap.add_argument("--worker-provider")
    ap.add_argument("--worker-model")
    ap.add_argument("--planner-provider")
    ap.add_argument("--planner-model")
    ap.add_argument("--budget", type=float, help="per-run worker LLM budget in USD")
    ap.add_argument("--max-planner-calls", type=int)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override any config value, e.g. --set experiment.timeout_s=120")
    ap.add_argument("--run-dir")
    ap.add_argument("--continue-from", metavar="RUN_DIR",
                    help="warm start: import that run's useful features and start from its best model "
                         "(same dataset and split required)")
    ap.add_argument("--no-watchdog", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    return ap.parse_args(argv)


def build_config(args) -> dict:
    cfg = load_config(args.config)
    if args.hours is not None:
        cfg["run"]["minutes"] = args.hours * 60
    if args.minutes is not None:
        cfg["run"]["minutes"] = args.minutes
    for key, val in [("run.workers", args.workers), ("run.cpu_slots", args.cpu_slots),
                     ("run.dataset", args.dataset), ("worker.provider", args.worker_provider),
                     ("worker.model", args.worker_model), ("planner.provider", args.planner_provider),
                     ("planner.model", args.planner_model), ("budget.max_total_usd", args.budget),
                     ("schedule.max_planner_calls", args.max_planner_calls)]:
        if val is not None:
            set_dotted(cfg, key, val)
    if args.worker_provider == "mock" and args.worker_model is None:
        cfg["worker"]["model"] = "mock"
    for item in args.set:
        k, v = item.split("=", 1)
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            pass
        set_dotted(cfg, k, v)
    cfg["run"]["data_dir"] = str(REPO_ROOT / "data" / cfg["run"]["dataset"])
    if args.continue_from:
        prev = Path(args.continue_from).resolve()
        if not (prev / "lab.db").exists():
            raise SystemExit(f"--continue-from: {prev} holds no run (no lab.db)")
        cfg["run"]["continue_from"] = str(prev)
    return cfg


def child(args) -> int:
    from genemila.controller import Controller, build_providers
    from genemila.lab import Lab
    from genemila.report import render_markdown

    cfg = json.loads((Path(args.run_dir) / "config.json").read_text())
    worker, esc, planner, fallbacks = build_providers(cfg)
    if hasattr(worker, "available") and not worker.available():
        print(f"ERROR: worker provider {worker.name} is not usable here "
              f"(missing {getattr(worker, 'api_key_env', 'credentials')}).", file=sys.stderr)
        return 2
    usable = [p for p in [planner, *fallbacks] if not hasattr(p, "available") or p.available()]
    if not usable:
        print(f"ERROR: planner {planner.name}:{planner.model} is not usable here and no fallback in "
              f"planner.fallback is either. Pass --planner-provider scripted for a no-LLM run, or set "
              f"--set planner.fallback=provider:model (the controller never falls back to the scripted "
              f"planner on its own).", file=sys.stderr)
        return 2
    if usable[0] is not planner:
        print(f"warning: planner {planner.name}:{planner.model} is not usable here; starting on the fallback "
              f"{usable[0].name}:{usable[0].model} (recorded as a planner switch)", file=sys.stderr)
    lab = Lab(cfg, Path(args.run_dir), Path(cfg["run"]["data_dir"]))
    ctl = Controller(lab, int(cfg["run"]["workers"]), float(cfg["run"]["minutes"]) * 60, worker, esc,
                     planner, fallbacks, quiet=args.quiet)
    summary = ctl.run()
    print("\n" + render_markdown(summary))
    sys.stdout.flush()
    os._exit(0)  # abandon any daemon threads still blocked in network calls


def main(argv=None) -> int:
    args = parse_args(argv)
    if args._child:
        return child(args)
    cfg = build_config(args)
    data_dir = Path(cfg["run"]["data_dir"])
    if not (data_dir / "manifest.json").exists():
        if cfg["run"]["dataset"] == "synthetic":
            from genemila.data.synthetic import generate
            generate(data_dir)
            print(f"generated synthetic dataset at {data_dir}")
        else:
            print(f"dataset {data_dir} not found; run prepare_data.py first", file=sys.stderr)
            return 2
    run_dir = Path(args.run_dir) if args.run_dir else REPO_ROOT / "runs" / (
        time.strftime("%Y%m%d_%H%M%S") + f"_{cfg['run']['dataset']}_w{cfg['run']['workers']}")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=1))
    print(f"run directory: {run_dir}")
    cmd = [sys.executable, str(Path(__file__).resolve()), "--_child", "--run-dir", str(run_dir)]
    if args.quiet:
        cmd.append("--quiet")
    if args.no_watchdog:
        args.run_dir = str(run_dir)
        return child(args)
    budget = float(cfg["run"]["minutes"]) * 60 + float(cfg["run"]["shutdown_grace_s"]) + 180
    proc = subprocess.Popen(cmd, start_new_session=True)
    try:
        proc.wait(timeout=budget)
    except subprocess.TimeoutExpired:
        print("WATCHDOG: lab overran its deadline; killing it", file=sys.stderr)
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    except KeyboardInterrupt:
        os.killpg(proc.pid, signal.SIGINT)
        proc.wait(timeout=float(cfg["run"]["shutdown_grace_s"]) + 120)
    if proc.returncode == 0 or (run_dir / "summary.json").exists():
        return 0
    if (run_dir / "lab.db").exists() and (run_dir / "lab.db").stat().st_size > 0:
        from genemila.lab import open_run
        from genemila.report import finalize, render_markdown
        lab = open_run(run_dir)
        lab.db.execute("UPDATE experiments SET status='killed', failure_stage='deadline', "
                       "failure_reason='killed by external watchdog' WHERE status IN "
                       "('claimed','implementing','testing','running')")
        lab.db.execute("UPDATE experiments SET status='cancelled' WHERE status='queued'")
        print(render_markdown(finalize(lab)))
    return proc.returncode or 0


if __name__ == "__main__":
    sys.exit(main())
