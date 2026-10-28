#!/usr/bin/env python3
"""Run Biomni's A1 agent on a task package, through the ledger proxy, under a wall-clock limit (protocol arm A4).

    python tools/baselines/run_biomni.py --package <package dir> --proxy http://127.0.0.1:8787 --model deepseek-v4-pro \\
        --minutes 20 --seed 0 --out <dir> [--python <the Biomni environment's python>] [--probe]

The parent (this process) starts one child, `<python> run_biomni.py --child ...`, with cwd = the package directory and
an environment built from an allowlist (PATH, HOME, LANG, LC_ALL, TMPDIR, TZ, USER when set) plus
OPENAI_BASE_URL=<proxy>/v1, OPENAI_API_KEY=proxy-token-<seed> and PYTHONUNBUFFERED=1: the child never holds a real key,
the proxy adds it. The child builds `A1(path=<package>/scratch/biomni_home, llm=<model>, source="OpenAI",
use_tool_retriever=True, expected_data_lake_files=[], timeout_seconds=<eval_timeout_s of MANIFEST.json + 30>)` (no
15 GB data lake; `source` explicit, since Biomni routes a model named "deepseek" to Ollama otherwise; the execute
timeout covers one full `python evaluate.py`, whose own limit is eval_timeout_s, so this arm can wait for a score as
the Claude Code arm can) and calls `agent.go(task)`, where the task is program.md, exactly as the Claude Code arm gets
it; run.json records its sha256 as task_sha256. The parent enforces --minutes: SIGTERM to the child's process group,
then SIGKILL after 20 s. stdout and stderr go to <out>/transcript.txt; <out>/run.json records the exit reason
(ended_by: solution when the agent returned a <solution>, timeout, cap when the proxy refused with 402, refused when
the child refused to start, error otherwise); results.tsv, features/ and runs/kept/features/ are copied into <out>/.

Before the first call the child prints the system prompt length and an estimate of the first main call's cost at the
lab's deepseek rate for the model (characters / 4 tokens, an estimate, times input_cache_miss: the rate given as
--miss-usd-per-mtok, else read from configs/default.toml next to this script when the checkout is there), and refuses
(ended_by refused, nothing sent) when that estimate reaches the proxy's session cap (read from /healthz): a probe whose
cap is below its first call would end in a 402 by construction. Biomni's retriever call goes out before the main call,
so the estimate is a lower bound. In Docker and account mode only tools/baselines/ is beside the runner, never
configs/, so the Mac scripts pass --miss-usd-per-mtok from the operator's clone (block_h_common.sh, miss_rate); without
either source the parent warns on stderr, run.json records rate_source "none", and the pre-estimate is skipped.

Biomni executes the agent's code with exec() inside its own process (biomni/tool/support_tools.py), with the user's
rights and whatever network the process has. So the package must be the only writable place the child can reach
and the proxy its only network route: the Mac script runs it in Docker or under a second user account (ROADMAP D6).
This tool only refuses what it can see itself: a package or a working directory inside a git checkout of this
repository, DEEPSEEK_API_KEY or API_KEY (the name the key has on the Mac) in its own environment, a non-local proxy,
and a proxy whose /healthz does not answer.

--probe sends one short task with a 2 minute limit: one <execute> round (print(2 + 2)), then the <solution>. That is
the shape ROADMAP D6 and section 8 want checked (Biomni appends its reply and the observation as two consecutive
assistant messages; only an execute round creates that), the first paid command of block H.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

PROBE_TASK = ("Run exactly one <execute> block containing: print(2 + 2). Read the <observation>, then answer "
              "<solution>4</solution> and stop.")
ENV_ALLOWLIST = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TZ", "USER")
KEY_NAMES = ("DEEPSEEK_API_KEY", "API_KEY")
CHARS_PER_TOKEN = 4  # an estimate for the cost check; no tokenizer is run


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
    task = PROBE_TASK if args.probe else (pkg / "program.md").read_text()
    from biomni.agent import A1  # noqa: PLC0415  (the Biomni environment, not the lab's)
    home = pkg / "scratch" / "biomni_home"
    home.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):  # the constructor prints its configuration; keep it out of the transcript
        agent = A1(path=str(home), llm=args.model, source="OpenAI", use_tool_retriever=True,
                   expected_data_lake_files=[], timeout_seconds=int(args.timeout_s))
    n_chars = len(agent.system_prompt)
    print(f"biomni A1 ready: model {args.model}, execute timeout {int(args.timeout_s)} s, system prompt {n_chars} chars, "
          f"config output {len(buf.getvalue())} chars (not shown)", flush=True)
    if args.miss_usd_per_mtok is not None and args.session_cap_usd is not None:
        est = n_chars / CHARS_PER_TOKEN * args.miss_usd_per_mtok / 1e6
        print(f"first main call estimate: {n_chars} chars / {CHARS_PER_TOKEN} per token x ${args.miss_usd_per_mtok} per "
              f"million = ${est:.4f} (a lower bound: the retriever call is extra); session cap ${args.session_cap_usd:.2f}",
              flush=True)
        if est >= args.session_cap_usd:
            print(f"\nBIOMNI_ENDED_BY: refused (first call estimate ${est:.4f} reaches the session cap "
                  f"${args.session_cap_usd:.2f}; nothing sent)", flush=True)
            return 2
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


def session_cap(proxy: str) -> float | None:
    """The proxy's session cap from /healthz, or None when it does not answer."""
    import urllib.request
    try:
        with urllib.request.urlopen(proxy.rstrip("/") + "/healthz", timeout=10) as r:
            return float(json.loads(r.read())["session_cap_usd"])
    except (OSError, ValueError, KeyError):
        return None


def miss_rate(model: str) -> float | None:
    """input_cache_miss for the model from configs/default.toml next to this script, when the checkout is there."""
    cfg = Path(__file__).resolve().parent.parent.parent / "configs" / "default.toml"
    if not cfg.is_file():
        return None
    import tomllib
    pricing = tomllib.loads(cfg.read_text()).get("pricing", {})
    entry = pricing.get(model) or pricing.get("default")
    return float(entry["input_cache_miss"]) if entry else None


def parent(args) -> int:
    pkg, out = Path(args.package).resolve(), Path(args.out).resolve()
    for name in KEY_NAMES:
        if name in os.environ:
            print(f"refusing: {name} is in this process's environment; only the proxy may hold a key", file=sys.stderr)
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
    cap = session_cap(args.proxy)
    if cap is None:
        print(f"refusing: {args.proxy}/healthz does not answer; start the ledger proxy first", file=sys.stderr)
        return 2
    minutes = 2.0 if args.probe else float(args.minutes)
    try:
        eval_timeout_s = float(json.loads((pkg / "MANIFEST.json").read_text())["eval_timeout_s"])
    except (OSError, ValueError, KeyError):
        eval_timeout_s = 600.0  # tools/export_task_package.py's default
    timeout_s = int(eval_timeout_s) + 30
    task_text = PROBE_TASK if args.probe else (pkg / "program.md").read_text()
    out.mkdir(parents=True, exist_ok=True)
    final = out / "final.txt"
    env = {k: os.environ[k] for k in ENV_ALLOWLIST if k in os.environ}
    env.update(OPENAI_BASE_URL=args.proxy.rstrip("/") + "/v1", OPENAI_API_KEY=f"proxy-token-{args.seed}",
               PYTHONUNBUFFERED="1")
    if args.miss_usd_per_mtok is not None:
        rate, rate_source = float(args.miss_usd_per_mtok), "flag"
    else:
        rate = miss_rate(args.model)
        rate_source = "config" if rate is not None else "none"
    if rate is None:
        print(f"warning: no input_cache_miss rate for {args.model}: configs/default.toml is not beside this runner "
              "and no --miss-usd-per-mtok was given, so the first-call cost pre-estimate is skipped", file=sys.stderr)
    cmd = [args.python, str(Path(__file__).resolve()), "--child", "--model", args.model, "--final", str(final),
           "--timeout-s", str(timeout_s), "--session-cap-usd", str(cap)]
    if rate is not None:
        cmd += ["--miss-usd-per-mtok", str(rate)]
    if args.probe:
        cmd.append("--probe")
    run = {"arm": "biomni", "seed": int(args.seed), "model": args.model, "minutes": minutes, "probe": bool(args.probe),
           "package": str(pkg), "out": str(out), "proxy": args.proxy, "python": args.python,
           "task_sha256": hashlib.sha256(task_text.encode()).hexdigest(), "execute_timeout_s": timeout_s,
           "session_cap_usd": cap, "first_call_miss_usd_per_mtok": rate, "rate_source": rate_source,
           "started": time.time()}
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
    ap.add_argument("--timeout-s", type=float, default=630, help=argparse.SUPPRESS)
    ap.add_argument("--session-cap-usd", type=float, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--miss-usd-per-mtok", type=float, default=None,
                    help="the model's input_cache_miss rate in USD per million tokens for the first-call pre-estimate; "
                         "default: configs/default.toml next to this runner, when the checkout is there")
    args = ap.parse_args(argv)
    if args.child:
        return child(args)
    if not args.package or not args.out:
        ap.error("--package and --out are required")
    return parent(args)


if __name__ == "__main__":
    sys.exit(main())
