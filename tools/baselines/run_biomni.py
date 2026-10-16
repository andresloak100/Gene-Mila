#!/usr/bin/env python3
"""Run Biomni's A1 agent on a task package, through the ledger proxy, under a wall-clock limit (protocol arm A4).

    python tools/baselines/run_biomni.py --package <package dir> --proxy http://127.0.0.1:8787 --model deepseek-v4-pro \\
        --minutes 20 --seed 0 --out <dir> [--python <the Biomni environment's python>] [--probe]

The parent (this process) starts one child, `<python> run_biomni.py --child ...`, with cwd = the package directory and
only OPENAI_BASE_URL=<proxy>/v1 and OPENAI_API_KEY=proxy-token-<seed> added to its environment: the child never holds a
real key, the proxy adds it. The child builds `A1(path=<package>/scratch/biomni_home, llm=<model>, source="OpenAI",
use_tool_retriever=True, expected_data_lake_files=[], timeout_seconds=60)` (no 15 GB data lake; `source` explicit, since
Biomni routes a model named "deepseek" to Ollama otherwise) and calls `agent.go(task)`, where the task is program.md
with one framing paragraph in front: the agent works in the package directory, edits only features/, runs
`python evaluate.py`, and hands back the kept features. The parent enforces --minutes: SIGTERM to the child's process
group, then SIGKILL after 20 s. stdout and stderr go to <out>/transcript.txt; <out>/run.json records the exit reason
(ended_by: solution when the agent returned a <solution>, timeout, cap when the proxy refused with 402, error
otherwise); results.tsv, features/ and runs/kept/features/ are copied into <out>/.

Biomni executes the agent's code with exec() inside its own process (biomni/tool/support_tools.py), with the user's
rights and whatever network the process has. So the package must be the only writable place the child can reach
and the proxy its only network route: the Mac script runs it in Docker or under a second user account (ROADMAP D6).
This tool only refuses two things it can see itself: a package or a working directory inside a git checkout of this
repository, and DEEPSEEK_API_KEY in its own environment.

--probe sends one short task ("write the number 4 and stop") with a 2 minute limit, to check that the endpoint
accepts Biomni's message shapes (the first paid command of block H, cap $0.05).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

FRAMING = ("You are working in the task package directory {pkg}, which is your current directory. Follow program.md "
           "below. Edit only files under features/ (and your own notes under scratch/); never modify evaluate.py, "
           "literal.py, MANIFEST.json, harness/ or data/. Run every evaluation with the shell command "
           "`python evaluate.py > run.log 2>&1` and read run.log. Keep going until you are stopped; what you hand back "
           "is runs/kept/features/ (the kept state), results.tsv and your transcript.\n\n")
PROBE_TASK = "Write the number 4 and stop. Do not run any code and do not call any tool."


def inside_lab_checkout(path: Path) -> str | None:
    """The top of the git checkout holding `path` when it is a checkout of this repository (it has genemila/)."""
    try:
        top = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                             timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if top.returncode != 0:
        return None
    root = Path(top.stdout.strip())
    return str(root) if (root / "genemila").is_dir() or (root / "AGENTS.md").is_file() else None


def child(args) -> int:
    """Inside the Biomni environment: build the agent, run the task, print the end marker."""
    import io
    import contextlib
    pkg = Path.cwd()
    task = PROBE_TASK if args.probe else FRAMING.format(pkg=pkg) + (pkg / "program.md").read_text()
    from biomni.agent import A1  # noqa: PLC0415  (the Biomni environment, not the lab's)
    home = pkg / "scratch" / "biomni_home"
    home.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):  # the constructor prints its configuration; keep it out of the transcript
        agent = A1(path=str(home), llm=args.model, source="OpenAI", use_tool_retriever=True,
                   expected_data_lake_files=[], timeout_seconds=60)
    print(f"biomni A1 ready: model {args.model}, system prompt {len(agent.system_prompt)} chars, "
          f"config output {len(buf.getvalue())} chars (not shown)", flush=True)
    try:
        log, final = agent.go(task)
    except Exception as exc:  # noqa: BLE001  (any client error ends the session; the parent reads the marker)
        text = f"{type(exc).__name__}: {exc}"
        kind = "cap" if ("402" in text or "budget_cap" in text) else "error"
        print(f"\nBIOMNI_ENDED_BY: {kind}\n{text[:2000]}", flush=True)
        return 3
    (Path(args.final)).write_text(str(final))
    print(f"\nBIOMNI_ENDED_BY: solution ({len(log)} steps)", flush=True)
    return 0


def parent(args) -> int:
    pkg, out = Path(args.package).resolve(), Path(args.out).resolve()
    if "DEEPSEEK_API_KEY" in os.environ:
        print("refusing: DEEPSEEK_API_KEY is in this process's environment; only the proxy may hold it",
              file=sys.stderr)
        return 2
    for label, p in (("--package", pkg), ("the working directory", Path.cwd())):
        top = inside_lab_checkout(p)
        if top:
            print(f"refusing: {label} {p} is inside a checkout of this repository ({top}); Biomni runs agent code "
                  "with exec() and must see only the package", file=sys.stderr)
            return 2
    if not (pkg / "program.md").is_file() or not (pkg / "evaluate.py").is_file():
        print(f"refusing: {pkg} is not a task package (no program.md or evaluate.py)", file=sys.stderr)
        return 2
    if not args.proxy.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]", "http://host.docker.internal")):
        print(f"refusing: --proxy must be the local ledger proxy, got {args.proxy!r}", file=sys.stderr)
        return 2
    minutes = 2.0 if args.probe else float(args.minutes)
    out.mkdir(parents=True, exist_ok=True)
    final = out / "final.txt"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI_", "ANTHROPIC_", "DEEPSEEK_"))}
    env.update(OPENAI_BASE_URL=args.proxy.rstrip("/") + "/v1", OPENAI_API_KEY=f"proxy-token-{args.seed}",
               PYTHONUNBUFFERED="1")
    cmd = [args.python, str(Path(__file__).resolve()), "--child", "--model", args.model, "--final", str(final)]
    if args.probe:
        cmd.append("--probe")
    run = {"arm": "biomni", "seed": int(args.seed), "model": args.model, "minutes": minutes, "probe": bool(args.probe),
           "package": str(pkg), "out": str(out), "proxy": args.proxy, "python": args.python, "started": time.time()}
    t0 = time.monotonic()
    with (out / "transcript.txt").open("wb") as log:
        proc = subprocess.Popen(cmd, cwd=pkg, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            proc.wait(timeout=minutes * 60)
        except subprocess.TimeoutExpired:
            timed_out = True
            for sig, grace in ((signal.SIGTERM, 20), (signal.SIGKILL, 10)):
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    proc.wait(timeout=grace)
                    break
                except subprocess.TimeoutExpired:
                    continue
    transcript = (out / "transcript.txt").read_text(errors="replace")
    marker = [ln for ln in transcript.splitlines() if ln.startswith("BIOMNI_ENDED_BY: ")]
    if timed_out:
        ended = "timeout"
    elif marker:
        ended = marker[-1].split(": ", 1)[1].split()[0]
    else:
        ended = "error"
    run.update(ended=time.time(), wall_s=round(time.monotonic() - t0, 1), exit_code=proc.returncode, ended_by=ended)
    for name in ("results.tsv", "MANIFEST.json"):
        if (pkg / name).is_file():
            shutil.copyfile(pkg / name, out / name)
    for src, dst in ((pkg / "features", out / "features"), (pkg / "runs" / "kept" / "features", out / "kept_features")):
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
    (out / "run.json").write_text(json.dumps(run, indent=1) + "\n")
    print(f"biomni session ended_by={ended} exit={proc.returncode} wall={run['wall_s']}s; see {out}")
    return 0 if ended in ("solution", "timeout") else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--package")
    ap.add_argument("--proxy", default="http://127.0.0.1:8787")
    ap.add_argument("--model", default="deepseek-v4-pro")
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out")
    ap.add_argument("--python", default=sys.executable, help="the interpreter of the Biomni environment")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--final", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.child:
        return child(args)
    if not args.package or not args.out:
        ap.error("--package and --out are required")
    return parent(args)


if __name__ == "__main__":
    sys.exit(main())
