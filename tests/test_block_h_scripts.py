"""The block H Mac scripts' two gaps closed on 2026-10-17 (docs/PLAN_H_COMPARISON.md, note of 22:00 UTC): a failed
probe can be reset (block_h_reset_probe.sh moves its files aside, never deletes, and refuses in the cases the plan
names), and run_biomni.py gets its first-call rate from --miss-usd-per-mtok (block_h_common.sh's miss_rate reads the
operator's clone's rate card) because configs/default.toml is not beside the runner in Docker or account mode."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BLOCK_H = ROOT / "docs" / "mac" / "block_h"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "baselines"))
from test_baselines import package, proxy  # noqa: E402,F401  (fixtures)

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="the Mac scripts need bash")


def _mac(tmp_path: Path) -> dict:
    """A fake Mac: HOME under tmp_path, the main checkout's venv python pointing at this interpreter, H_CLONE this
    repository (its configs/default.toml is the rate card the scripts read)."""
    home = tmp_path / "home"
    main = home / "Documents" / "Mila" / "Gene-Mila" / "gene-mila"
    (main / ".venv" / "bin").mkdir(parents=True)
    (main / ".venv" / "bin" / "python").symlink_to(sys.executable)
    h = home / "Documents" / "Mila" / "Gene-Mila" / "genemila_scale_logs" / "block_h"
    (h / "proxy").mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    env.update(HOME=str(home), H_CLONE=str(ROOT))
    return {"home": home, "h": h, "env": env}


def _bash(script: str, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(BLOCK_H / script), *args], env=env, capture_output=True, text=True, timeout=60)


def _failed_probe(h: Path, shared: Path | None = None) -> list[Path]:
    """What a probe that failed in docker mode leaves behind (block_h_common.sh: session_dirs, agent_run, proxy_up,
    session_after), plus another session's files that must stay."""
    made = []
    for rel in ("h_probe.log", "h_probe_codex.log", "h_probe.check.txt", "h_probe.credscan.txt", "h_probe.val1scan.txt",
                "h_probe.handback.log", "proxy/h_probe.jsonl", "proxy/h_probe.proxy.log", "proxy/h_probe_codex.jsonl",
                "work/h_probe.export.json", "work/h_probe/MANIFEST.json", "out/h_probe/run.json",
                "handback/h_probe/manifest.json"):
        p = h / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rel + "\n")
        made.append(p)
    (h / "block_h_stopped.txt").write_text("2026-10-17T21:00Z h_probe: runner exit code biomni=1,codex=0;\n")
    made.append(h / "block_h_stopped.txt")
    if shared is not None:
        for rel in ("work/h_probe/MANIFEST.json", "out/h_probe/run.json", "proxy/h_probe.jsonl"):
            p = shared / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(rel + "\n")
            made.append(p)
    return made


def test_reset_probe_moves_a_failed_probe_aside_and_keeps_other_sessions(tmp_path):
    mac = _mac(tmp_path)
    h = mac["h"]
    made = _failed_probe(h)
    keep = [h / "h_a4_r0.log", h / "proxy" / "h_a4_r0.jsonl", h / "block_h_cap.txt", h / "tier.txt"]
    for p in keep:
        p.write_text("stays\n")
    r = _bash("block_h_reset_probe.sh", mac["env"])  # no note named: usage, nothing moved
    assert r.returncode == 1 and "usage" in r.stdout and all(p.exists() for p in made)
    r = _bash("block_h_reset_probe.sh", mac["env"], "note of 2026-10-17 22:00 UTC")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not any(p.exists() for p in made), [p for p in made if p.exists()]
    assert all(p.exists() for p in keep)
    failed = sorted((h / "failed").iterdir())
    assert len(failed) == 1 and failed[0].name.startswith("h_probe_")
    d = failed[0]
    assert (d / "h_probe.log").exists() and (d / "block_h_stopped.txt").exists()
    assert (d / "proxy" / "h_probe_codex.jsonl").exists() and (d / "work" / "h_probe" / "MANIFEST.json").exists()
    assert (d / "out" / "h_probe" / "run.json").exists() and (d / "handback" / "h_probe" / "manifest.json").exists()
    assert (d / "work" / "h_probe.export.json").exists()
    moved = (d / "moved.txt").read_text().splitlines()
    assert len([m for m in moved if m]) == len(made)  # three directories stand for their three files
    progress = (mac["home"] / "Documents" / "Mila" / "Gene-Mila" / "genemila_scale_logs" / "progress.md").read_text()
    assert "probe reset" in progress and "note of 2026-10-17 22:00 UTC" in progress
    # the probe's files are gone, so the probe script's own refusals no longer trigger on them
    assert not (h / "h_probe.log").exists() and not (h / "block_h_stopped.txt").exists()
    # a second reset finds nothing
    r = _bash("block_h_reset_probe.sh", mac["env"], "again")
    assert r.returncode == 1 and "no failed probe" in r.stdout


def test_reset_probe_refuses_a_passed_probe_and_another_sessions_stop(tmp_path):
    mac = _mac(tmp_path)
    h = mac["h"]
    made = _failed_probe(h)
    (h / "h_probe.passed").write_text("")
    r = _bash("block_h_reset_probe.sh", mac["env"], "note")
    assert r.returncode == 1 and "passed" in r.stdout and all(p.exists() for p in made)
    (h / "h_probe.passed").unlink()
    (h / "block_h_stopped.txt").write_text("2026-10-17T21:00Z h_probe: runner exit code 1;\n"
                                           "2026-10-17T23:00Z h_a4_r0: ledger delta $3.00 over $2.50;\n")
    r = _bash("block_h_reset_probe.sh", mac["env"], "note")
    assert r.returncode == 1 and "another session" in r.stdout and all(p.exists() for p in made)
    assert not (h / "failed").exists()


def test_reset_probe_takes_the_account_modes_shared_copies_too(tmp_path, monkeypatch):
    mac = _mac(tmp_path)
    shared = tmp_path / "shared"
    made = _failed_probe(mac["h"], shared)
    # SHARED is fixed in block_h_common.sh (/Users/Shared/genemila_h); a wrapper redefines it after sourcing
    wrapper = tmp_path / "reset_with_shared.sh"
    text = (BLOCK_H / "block_h_reset_probe.sh").read_text().replace(
        '. "$(dirname "$0")/block_h_common.sh"', f'. "{BLOCK_H}/block_h_common.sh"; SHARED="{shared}"')
    wrapper.write_text(text)
    r = subprocess.run(["bash", str(wrapper), "note"], env=mac["env"], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not any(p.exists() for p in made)
    d = next((mac["h"] / "failed").iterdir())
    assert (d / "shared" / "work" / "h_probe" / "MANIFEST.json").exists()
    assert (d / "shared" / "proxy" / "h_probe.jsonl").exists()


def test_miss_rate_reads_the_rate_card_of_the_operators_clone(tmp_path):
    mac = _mac(tmp_path)
    src = f'. "{BLOCK_H}/block_h_common.sh"; miss_rate "$1"'
    r = subprocess.run(["bash", "-c", src, "x", "deepseek-v4-pro"], env=mac["env"], capture_output=True, text=True)
    assert r.returncode == 0 and float(r.stdout.strip()) == 1.32, r.stdout + r.stderr
    r = subprocess.run(["bash", "-c", src, "x", "no-such-model"], env=mac["env"], capture_output=True, text=True)
    assert r.returncode == 0 and float(r.stdout.strip()) == 3.0  # pricing.default, deliberately pessimistic
    env = {**mac["env"], "H_CLONE": str(tmp_path / "empty")}
    r = subprocess.run(["bash", "-c", src, "x", "deepseek-v4-pro"], env=env, capture_output=True, text=True)
    assert r.returncode == 1 and "NOT STARTED" in r.stdout and "no input_cache_miss rate" in r.stdout
    # the callers' form stops the script on a missing rate
    src2 = f'. "{BLOCK_H}/block_h_common.sh"; R=$(miss_rate deepseek-v4-pro) || exit 1; echo "got $R"'
    r = subprocess.run(["bash", "-c", src2], env=env, capture_output=True, text=True)
    assert r.returncode == 1 and "got" not in r.stdout


def _stub(tmp_path: Path) -> Path:
    stub = tmp_path / "stub_python"
    stub.write_text("#!/bin/sh\nexec python3 -c 'import json, sys; print(json.dumps({\"argv\": sys.argv[1:]})); "
                    "print(\"BIOMNI_ENDED_BY: solution (0 steps)\")' \"$@\"\n")
    stub.chmod(0o755)
    return stub


def test_run_biomni_takes_the_rate_from_the_flag_and_warns_without_any_source(package, tmp_path, proxy):  # noqa: F811
    px, url = proxy
    stub = _stub(tmp_path)
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    runner = ROOT / "tools" / "baselines" / "run_biomni.py"
    out = tmp_path / "flag"
    r = subprocess.run([sys.executable, str(runner), "--package", str(package), "--proxy", url, "--seed", "0",
                        "--out", str(out), "--python", str(stub), "--miss-usd-per-mtok", "9.5"], cwd=tmp_path,
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    argv = json.loads((out / "transcript.txt").read_text().splitlines()[0])["argv"]
    assert argv[argv.index("--miss-usd-per-mtok") + 1] == "9.5"
    run = json.loads((out / "run.json").read_text())
    assert run["first_call_miss_usd_per_mtok"] == 9.5 and run["rate_source"] == "flag"
    assert "warning" not in r.stderr
    # the runner alone, as Docker and the account copy have it (no configs/ beside it), and no flag
    alone = tmp_path / "lab" / "tools" / "baselines"
    alone.mkdir(parents=True)
    shutil.copyfile(runner, alone / "run_biomni.py")
    out2 = tmp_path / "none"
    r = subprocess.run([sys.executable, str(alone / "run_biomni.py"), "--package", str(package), "--proxy", url,
                        "--seed", "0", "--out", str(out2), "--python", str(stub)], cwd=tmp_path, env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "warning: no input_cache_miss rate" in r.stderr
    argv = json.loads((out2 / "transcript.txt").read_text().splitlines()[0])["argv"]
    assert "--miss-usd-per-mtok" not in argv
    run = json.loads((out2 / "run.json").read_text())
    assert run["first_call_miss_usd_per_mtok"] is None and run["rate_source"] == "none"
    # beside the checkout, as before: the config's rate
    out3 = tmp_path / "config"
    r = subprocess.run([sys.executable, str(runner), "--package", str(package), "--proxy", url, "--seed", "0",
                        "--out", str(out3), "--python", str(stub)], cwd=tmp_path, env=env, capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    run = json.loads((out3 / "run.json").read_text())
    assert run["first_call_miss_usd_per_mtok"] == 1.32 and run["rate_source"] == "config"


def _gate(mac: dict, *logs: Path) -> subprocess.CompletedProcess:
    script = f'. "{BLOCK_H / "block_h_common.sh"}"; probe_gate "$@"'
    return subprocess.run(["bash", "-c", script, "gate", *map(str, logs)], env=mac["env"], capture_output=True,
                          text=True, timeout=60)


def _log(path: Path, *statuses: int) -> Path:
    path.write_text("".join(json.dumps({"status": s, "model_served": "deepseek-v4-pro"} if s == 200 else {"status": s})
                            + "\n" for s in (0, *statuses, 0)))
    return path


def test_probe_gate_enforces_the_plans_codex_rule_per_log(tmp_path):
    """Astra's three counterexamples (#51 comment 6550718051) fail; two codex 200s, no 400 and a Biomni 200 pass."""
    mac = _mac(tmp_path)
    p = mac["h"] / "proxy"
    biomni, biomni_none = _log(p / "b.jsonl", 200), _log(p / "b0.jsonl")
    cases = {
        "one_codex_200": (biomni, _log(p / "c1.jsonl", 200), 1),
        "codex_200_then_400": (biomni, _log(p / "c2.jsonl", 200, 400), 1),
        "codex_two_200_and_a_400": (biomni, _log(p / "c3.jsonl", 200, 200, 400), 1),
        "biomni_200_codex_none": (biomni, _log(p / "c4.jsonl"), 1),
        "biomni_none_codex_ok": (biomni_none, _log(p / "c5.jsonl", 200, 200), 1),
        "codex_log_missing": (biomni, p / "absent.jsonl", 1),
        "passes": (biomni, _log(p / "c6.jsonl", 200, 200), 0),
    }
    for name, (b, c, rc) in cases.items():
        r = _gate(mac, b, c)
        assert r.returncode == rc, (name, r.stdout, r.stderr)
        assert ("PROBE GATE" in r.stdout) == bool(rc), name
    assert _gate(mac, biomni).returncode == 0  # the claude client: Biomni's log alone
