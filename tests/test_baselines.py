"""The block H runners and the hand-back collector (tools/baselines/): collect_handback sorts a session's kept features
into accepted and rejected --source files with a manifest that hashes and scans the transcript; run_biomni refuses an
unsafe place or a key, gives its child an allowlisted environment and the package's evaluation timeout, and, where
biomni is installed, runs its probe (one execute round) against the mock endpoint through the proxy; the autoresearch
script parses and dry-runs with one permission rule per word and an env -i environment."""
import hashlib
import json
import os
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "baselines"))
import collect_handback as ch  # noqa: E402
import export_task_package as etp  # noqa: E402
import ledger_proxy as lp  # noqa: E402
import run_biomni  # noqa: E402
from test_ledger_proxy import KEY, PRICING, Upstream  # noqa: E402
from test_task_package import FEATURE, HELPFUL  # noqa: E402

BASELINES = ROOT / "tools" / "baselines"
BAD = ("ar_pasted_table", "a table pasted into code", """\
        table = [{}]
        return np.broadcast_to(np.array(table[:ctx.n_genes] + [0.0] * max(0, ctx.n_genes - len(table)))[None, :, None],
                               (len(perts), ctx.n_genes, 1)).copy()""".format(", ".join(f"{i}.5" for i in range(40))))
UNGUARDED = ("ar_reads_a_file", "reads a file", """\
        open("/etc/hosts").read()
        return np.zeros((len(perts), ctx.n_genes, 1))""")


def _write(pkg: Path, spec):
    name, description, body = spec
    (pkg / "features" / f"{name}.py").write_text(FEATURE.format(name=name, description=description, body=body))


@pytest.fixture
def package(dataset, tmp_path):
    pkg = tmp_path / "pkg"
    assert etp.main(["--data", str(dataset), "--out", str(pkg)]) == 0
    return pkg


@pytest.fixture
def proxy(tmp_path):
    """A mock upstream and a ledger proxy in front of it; yields (proxy object, proxy url)."""
    up = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    px = lp.Proxy(f"http://127.0.0.1:{up.server_address[1]}", tmp_path / "ledger.sqlite", "probe", "biomni", 0.25,
                  100.0, tmp_path / "proxy.jsonl", PRICING, KEY)
    srv = lp.make_server("127.0.0.1:0", px)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield px, f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        up.shutdown()


def test_collect_handback_sorts_kept_features_and_writes_the_manifest(package, tmp_path):
    for spec in (HELPFUL, BAD, UNGUARDED):
        _write(package, spec)
    out = tmp_path / "out_r2"
    out.mkdir()
    (out / "run.json").write_text(json.dumps({"arm": "biomni", "seed": 2, "model": "deepseek-v4-pro",
                                              "ended_by": "timeout", "minutes": 20, "task_sha256": "ab" * 32}))
    (out / "transcript.txt").write_text("step 1\nreading https://example.org/x\nimport socket\nfine\n")
    dest = tmp_path / "handback"
    assert ch.main(["--out", str(out), "--package", str(package), "--dest", str(dest)]) == 0
    assert sorted(p.name for p in (dest / "biomni_r2").iterdir()) == ["ar_target_corr.py"]
    assert sorted(p.name for p in (dest / "rejected" / "biomni_r2").iterdir()) == ["ar_pasted_table.py",
                                                                                    "ar_reads_a_file.py"]
    assert (dest / "biomni_r2" / "ar_target_corr.py").read_bytes() == (package / "features" / "ar_target_corr.py").read_bytes()
    m = json.loads((dest / "manifest.json").read_text())
    s = m["sessions"]["biomni_r2"]
    assert s["origin"] == "features/ (no results.tsv)" and s["run"]["ended_by"] == "timeout" and s["results_tsv_sha256"] is None
    assert s["run"]["task_sha256"] == "ab" * 32 and s["transcript_sha256"] == ch.sha256(out / "transcript.txt")
    assert [(f["line"], f["match"]) for f in s["transcript_flags"]] == [(2, "https://"), (3, "socket")]
    files = s["files"]
    assert files["ar_target_corr"]["ok"] and files["ar_target_corr"]["literal"]["ok"] and files["ar_target_corr"]["guard"]["ok"]
    assert files["ar_target_corr"]["sha256"] == ch.sha256(package / "features" / "ar_target_corr.py")
    assert files["ar_target_corr"]["size"] == (package / "features" / "ar_target_corr.py").stat().st_size
    assert not files["ar_pasted_table"]["ok"] and files["ar_pasted_table"]["guard"]["ok"]
    assert "literal display of 40 elements" in files["ar_pasted_table"]["rejected_reason"]
    assert not files["ar_reads_a_file"]["guard"]["ok"] and "'open'" in files["ar_reads_a_file"]["rejected_reason"]
    assert files["ar_reads_a_file"]["copied_to"] == "rejected/biomni_r2/ar_reads_a_file.py"
    # a second session merges into the same manifest; the kept state wins over features/ once evaluate.py has run
    proc = subprocess.run([sys.executable, "evaluate.py"], cwd=package, capture_output=True, text=True, timeout=600)
    assert "status: rejected" in proc.stdout  # three files at once break the one-change rule; features/ is restored
    for f in (package / "features").glob("*.py"):
        f.unlink()
    assert "status: baseline" in subprocess.run([sys.executable, "evaluate.py"], cwd=package, capture_output=True,
                                                text=True, timeout=600).stdout
    _write(package, HELPFUL)
    proc = subprocess.run([sys.executable, "evaluate.py"], cwd=package, capture_output=True, text=True, timeout=600)
    kept = sorted(p.stem for p in (package / "runs" / "kept" / "features").glob("*.py"))
    out3 = tmp_path / "out_r3"
    out3.mkdir()
    (out3 / "run.json").write_text(json.dumps({"arm": "autoresearch", "seed": 3, "ended_by": "solution"}))
    assert ch.main(["--out", str(out3), "--package", str(package), "--dest", str(dest)]) == 0
    m = json.loads((dest / "manifest.json").read_text())
    assert set(m["sessions"]) == {"biomni_r2", "autoresearch_r3"}
    s3 = m["sessions"]["autoresearch_r3"]
    assert s3["origin"] == "runs/kept/features" and sorted(s3["files"]) == kept
    assert s3["transcript_sha256"] is None and s3["transcript_flags"] is None
    assert s3["results_tsv_sha256"] == ch.sha256(package / "results.tsv")
    assert sorted(p.stem for p in (dest / "autoresearch_r3").glob("*.py")) == kept


def test_collect_handback_reads_results_tsv_without_a_kept_state(package, tmp_path):
    _write(package, HELPFUL)
    _write(package, BAD)
    (package / "results.tsv").write_text("n\toof_pearson_delta\tgain\tgain_se\tstatus\tfeature\tdescription\n"
                                         "1\t0.5\t0\t0\tbaseline\t-\tbaseline\n"
                                         "2\t0.51\t0.01\t0.001\tkeep\tar_target_corr\tx\n"
                                         "3\t0.50\t-0.01\t0.001\tdiscard\tar_pasted_table\ty\n")
    out = tmp_path / "out"
    out.mkdir()
    (out / "run.json").write_text(json.dumps({"arm": "biomni", "seed": 0}))
    assert ch.main(["--out", str(out), "--package", str(package), "--dest", str(tmp_path / "d")]) == 0
    s = json.loads((tmp_path / "d" / "manifest.json").read_text())["sessions"]["biomni_r0"]
    assert s["origin"] == "results.tsv status keep" and list(s["files"]) == ["ar_target_corr"]


def test_run_biomni_refuses_a_checkout_and_a_key_in_its_environment(package, tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    base = [sys.executable, str(BASELINES / "run_biomni.py"), "--out", str(tmp_path / "o"), "--probe"]
    # the package inside this repository's checkout
    r = subprocess.run(base + ["--package", str(ROOT / "tools" / "task_package")], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 2 and "inside a checkout of this repository" in r.stderr
    # the working directory inside the checkout
    r = subprocess.run(base + ["--package", str(package)], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 2 and "inside a checkout of this repository" in r.stderr
    # the key in the runner's own environment
    r = subprocess.run(base + ["--package", str(package)], cwd=tmp_path, env={**env, "DEEPSEEK_API_KEY": "x"},
                       capture_output=True, text=True)
    assert r.returncode == 2 and "DEEPSEEK_API_KEY" in r.stderr
    r = subprocess.run(base + ["--package", str(package)], cwd=tmp_path, env={**env, "API_KEY": "x"},  # the Mac's name
                       capture_output=True, text=True)
    assert r.returncode == 2 and "API_KEY" in r.stderr
    # a proxy that is not local, and one that does not answer
    r = subprocess.run(base + ["--package", str(package), "--proxy", "https://api.deepseek.com"], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 2 and "--proxy" in r.stderr
    r = subprocess.run(base + ["--package", str(package), "--proxy", "http://127.0.0.1:9"], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 2 and "healthz" in r.stderr


def test_run_biomni_child_gets_an_allowlisted_environment_and_the_packages_timeout(package, tmp_path, proxy):
    """A stub in place of the Biomni interpreter prints what the child would see."""
    px, url = proxy
    stub = tmp_path / "stub_python"
    stub.write_text("#!/bin/sh\nexec python3 -c 'import json, os, sys; print(json.dumps({\"env\": dict(os.environ), "
                    "\"argv\": sys.argv[1:]})); print(\"BIOMNI_ENDED_BY: solution (0 steps)\")' \"$@\"\n")
    stub.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    env.update(GH_TOKEN="not-for-the-child", SOME_OTHER_SECRET="nope", OPENAI_API_KEY="nope")
    out = tmp_path / "o"
    r = subprocess.run([sys.executable, str(BASELINES / "run_biomni.py"), "--package", str(package), "--proxy", url,
                        "--seed", "3", "--out", str(out), "--python", str(stub)], cwd=tmp_path, env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    seen = json.loads((out / "transcript.txt").read_text().splitlines()[0])
    child_env = seen["env"]
    assert child_env["OPENAI_BASE_URL"] == url + "/v1" and child_env["OPENAI_API_KEY"] == "proxy-token-3"
    assert "PATH" in child_env and "GH_TOKEN" not in child_env and "SOME_OTHER_SECRET" not in child_env
    shell_added = {"PWD", "OLDPWD", "SHLVL", "_", "LC_CTYPE"}  # the stub is a shell; sh and python add these
    if sys.platform == "darwin":
        shell_added.add("__CF_USER_TEXT_ENCODING")  # macOS adds its non-secret text encoding metadata
    assert set(child_env) - shell_added <= set(("OPENAI_BASE_URL", "OPENAI_API_KEY", "PYTHONUNBUFFERED")
                                                + run_biomni.ENV_ALLOWLIST)
    eval_timeout = json.loads((package / "MANIFEST.json").read_text())["eval_timeout_s"]
    argv = seen["argv"]
    assert argv[argv.index("--timeout-s") + 1] == str(int(eval_timeout) + 30)
    assert argv[argv.index("--session-cap-usd") + 1] == "0.25"
    assert float(argv[argv.index("--miss-usd-per-mtok") + 1]) == PRICING["deepseek-v4-pro"]["input_cache_miss"]
    run = json.loads((out / "run.json").read_text())
    assert run["ended_by"] == "solution" and run["execute_timeout_s"] == int(eval_timeout) + 30
    assert run["task_sha256"] == hashlib.sha256((package / "program.md").read_bytes()).hexdigest()  # program.md alone
    assert run["session_cap_usd"] == 0.25


def test_run_biomni_probe_through_the_proxy(package, tmp_path, proxy):
    """Needs biomni in this interpreter (BIOMNI_PYTHON names another one). The mock answers an <execute> reply, then a
    <solution> once it sees the observation: the probe must send the reply and the observation as two consecutive
    assistant messages, the shape ROADMAP D6 and section 8 have the probe check."""
    python = os.environ.get("BIOMNI_PYTHON") or sys.executable
    if python == sys.executable:
        pytest.importorskip("biomni")
        pytest.importorskip("langchain_openai")
    px, url = proxy
    Upstream.seen.clear()
    Upstream.mode = "biomni"
    try:
        env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
        r = subprocess.run([sys.executable, str(BASELINES / "run_biomni.py"), "--package", str(package), "--proxy", url,
                            "--model", "deepseek-v4-pro", "--seed", "1", "--out", str(tmp_path / "probe"), "--probe",
                            "--python", python], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=240)
    finally:
        Upstream.mode = "ok"
    run = json.loads((tmp_path / "probe" / "run.json").read_text())
    transcript = (tmp_path / "probe" / "transcript.txt").read_text()
    assert run["probe"] and run["minutes"] == 2 and run["ended_by"] == "solution", r.stdout + r.stderr + transcript
    assert run["task_sha256"] == hashlib.sha256(run_biomni.PROBE_TASK.encode()).hexdigest()
    assert px.calls >= 2 and KEY not in transcript and "first main call estimate" in transcript
    roles = [[m.get("role") for m in s["body"].get("messages", [])] for s in Upstream.seen]
    assert any(r[-2:] == ["assistant", "assistant"] or ("assistant", "assistant") in zip(r, r[1:]) for r in roles), roles
    assert (tmp_path / "probe" / "final.txt").read_text().strip().endswith("4") or "4" in transcript


def test_run_autoresearch_script_parses_and_dry_runs(package, tmp_path):
    script = BASELINES / "run_autoresearch.sh"
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True).returncode == 0
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    env["GH_TOKEN"] = "not-for-claude"
    r = subprocess.run(["bash", str(script), "--dry-run", str(package), "http://127.0.0.1:8787", "20", "4",
                        str(tmp_path / "out")], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert "claude -p" in r.stdout and "--permission-mode acceptEdits" in r.stdout
    assert "--disallowedTools WebSearch WebFetch" in r.stdout and "--strict-mcp-config" in r.stdout
    # one permission rule per argv word (printf %q escapes the space inside a word, so a split rule shows unescaped)
    assert "Bash\\(python\\ evaluate.py\\*\\)" in r.stdout and "Bash\\(grep\\ \\*\\)" in r.stdout
    assert "Bash\\(python evaluate.py" not in r.stdout
    assert "env -i" in r.stdout and "ANTHROPIC_BASE_URL=http://127.0.0.1:8787/anthropic" in r.stdout
    assert "ANTHROPIC_AUTH_TOKEN=proxy-token-4" in r.stdout and "ANTHROPIC_API_KEY unset" in r.stdout
    assert "for 1200 s" in r.stdout and "ANTHROPIC_MODEL=deepseek-v4-pro" in r.stdout
    eval_timeout = json.loads((package / "MANIFEST.json").read_text())["eval_timeout_s"]
    assert f"BASH_DEFAULT_TIMEOUT_MS={int((eval_timeout + 30) * 1000)}" in r.stdout
    assert f"BASH_MAX_TIMEOUT_MS={int((eval_timeout + 30) * 1000)}" in r.stdout
    assert hashlib.sha256((package / "program.md").read_bytes()).hexdigest() in r.stdout  # task_sha256
    assert "not-for-claude" not in r.stdout  # nothing of the caller's shell beyond the allowlist
    # the refusals that need no claude: a wrong argument count, a key in the shell, a non-local proxy
    assert subprocess.run(["bash", str(script), str(package)], capture_output=True, env=env).returncode == 2
    r = subprocess.run(["bash", str(script), str(package), "http://127.0.0.1:8787", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env={**env, "API_KEY": "x"})
    assert r.returncode == 2 and "only the proxy may hold the key" in r.stderr
    r = subprocess.run(["bash", str(script), str(package), "https://api.deepseek.com", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "local ledger proxy" in r.stderr


def test_run_codex_script_parses_and_dry_runs(package, tmp_path):
    """The Codex twin of run_autoresearch.sh: the same interface and refusals; a private CODEX_HOME under the out
    directory whose config.toml points one provider at the proxy in the chat wire format with a dummy env key."""
    script = BASELINES / "run_codex.sh"
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True).returncode == 0
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    env["GH_TOKEN"] = "not-for-codex"
    env["OPENAI_API_KEY"] = "not-for-codex-either"
    out = tmp_path / "out"
    r = subprocess.run(["bash", str(script), "--dry-run", str(package), "http://127.0.0.1:8787", "20", "4", str(out)],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    # the command: codex exec, non-interactive, in the package, sandboxed, the model, JSONL, program.md on stdin
    assert "codex exec --skip-git-repo-check -C" in r.stdout and "--sandbox workspace-write" in r.stdout
    assert "--ephemeral" not in r.stdout  # first appears at rust-v0.99.0, a build with no chat wire format
    assert "-m deepseek-v4-pro --json -o" in r.stdout and f"- < {package.resolve()}/program.md" in r.stdout
    assert "for 1200 s" in r.stdout
    # the env -i allowlist: the private CODEX_HOME and the dummy token, nothing of the caller's shell beyond it
    assert "env -i" in r.stdout and f"CODEX_HOME={out.resolve()}/codex_home" in r.stdout
    assert "LEDGER_PROXY_TOKEN=proxy-token-4" in r.stdout and "OPENAI_API_KEY and DEEPSEEK_API_KEY unset" in r.stdout
    assert "not-for-codex" not in r.stdout
    assert hashlib.sha256((package / "program.md").read_bytes()).hexdigest() in r.stdout  # task_sha256
    # the config.toml the dry run wrote (and printed): one provider at the proxy, chat wire format, a dummy env key,
    # web search off, approval never, no MCP server, no real key anywhere
    config = (out / "codex_home" / "config.toml").read_text()
    settings = "\n".join(l for l in config.splitlines() if not l.startswith("#"))
    assert all(line in r.stdout for line in config.splitlines())
    assert 'model = "deepseek-v4-pro"' in config and 'model_provider = "ledger_proxy"' in config
    assert "[model_providers.ledger_proxy]" in config and 'base_url = "http://127.0.0.1:8787/v1"' in config
    assert 'wire_api = "chat"' in config and 'env_key = "LEDGER_PROXY_TOKEN"' in config
    assert 'web_search = "disabled"' in config and 'approval_policy = "never"' in config
    assert "web_search_request" not in settings and "preferred_auth_method" not in settings  # keys no build reads
    assert 'sandbox_mode = "workspace-write"' in config and "network_access = false" in config
    assert "mcp_servers" not in settings and "sk-" not in config and "proxy-token" not in config
    assert "not-for-codex" not in config and "experimental_bearer_token" not in settings
    assert sorted(p.name for p in (out / "codex_home").iterdir()) == ["config.toml"]
    # the variables: another binary, the responses wire format, no sandbox (Docker mode)
    r = subprocess.run(["bash", str(script), "--dry-run", str(package), "http://host.docker.internal:8787", "20", "0",
                        str(tmp_path / "o2")], capture_output=True, text=True,
                       env={**env, "CODEX_BIN": "/Applications/x/codex", "CODEX_WIRE_API": "responses",
                            "CODEX_SANDBOX": "none"})
    assert r.returncode == 0, r.stderr
    assert "/Applications/x/codex exec" in r.stdout and "--dangerously-bypass-approvals-and-sandbox" in r.stdout
    assert "--sandbox" not in r.stdout
    config2 = (tmp_path / "o2" / "codex_home" / "config.toml").read_text()
    assert 'wire_api = "responses"' in config2 and 'base_url = "http://host.docker.internal:8787/v1"' in config2
    # the probe: one line as the prompt, a read-only sandbox, two minutes, the same CODEX_HOME
    r = subprocess.run(["bash", str(script), "--dry-run", "--probe", str(package), "http://127.0.0.1:8787", "20", "0",
                        str(tmp_path / "o3")], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert "--sandbox read-only" in r.stdout and "for 120 s" in r.stdout and "probe_prompt.txt" in r.stdout
    probe_line = "Run the shell command `ls` and then reply with the single word ok.\n"  # one tool round trip
    assert (tmp_path / "o3" / "probe_prompt.txt").read_text() == probe_line
    assert hashlib.sha256(probe_line.encode()).hexdigest() in r.stdout
    assert 'wire_api = "chat"' in (tmp_path / "o3" / "codex_home" / "config.toml").read_text()
    # the refusals that need no codex: a wrong argument count, a key in the shell, a non-local proxy, a bad variable
    assert subprocess.run(["bash", str(script), str(package)], capture_output=True, env=env).returncode == 2
    r = subprocess.run(["bash", str(script), str(package), "http://127.0.0.1:8787", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env={**env, "API_KEY": "x"})
    assert r.returncode == 2 and "only the proxy may hold the key" in r.stderr
    r = subprocess.run(["bash", str(script), str(package), "https://api.deepseek.com", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "local ledger proxy" in r.stderr
    r = subprocess.run(["bash", str(script), str(package), "http://127.0.0.1:8787", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env={**env, "CODEX_WIRE_API": "grpc"})
    assert r.returncode == 2 and "CODEX_WIRE_API" in r.stderr
    assert not (tmp_path / "o").exists()  # a refusal writes nothing


CODEX_STUB = '''import hashlib, json, os, re, sys, urllib.request
# A stand-in for `codex exec`: reads the provider from $CODEX_HOME/config.toml, the prompt from stdin, makes one chat
# completion through base_url with the env_key token, writes the last message to -o and JSONL events to stdout.
args = sys.argv[1:]
cfg = open(os.path.join(os.environ["CODEX_HOME"], "config.toml")).read()
base = re.search(r'base_url = "([^"]+)"', cfg).group(1)
env_key = re.search(r'env_key = "([^"]+)"', cfg).group(1)
prompt = sys.stdin.read()
body = json.dumps({"model": args[args.index("-m") + 1], "messages": [{"role": "user", "content": prompt}]}).encode()
req = urllib.request.Request(base + "/chat/completions", body,
                             {"Authorization": "Bearer " + os.environ[env_key], "Content-Type": "application/json"})
doc = json.load(urllib.request.urlopen(req))
text = doc["choices"][0]["message"]["content"]
open(args[args.index("-o") + 1], "w").write(text)
print(json.dumps({"type": "thread.started", "thread_id": "t"}))
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": text}}))
print(json.dumps({"type": "stub", "env": dict(os.environ), "argv": args, "cwd": os.getcwd(),
                  "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}))
'''


def test_run_codex_session_through_the_proxy_with_a_stub_codex(package, tmp_path, proxy):
    """The real path with a stub in place of codex: the watchdog, the env -i environment, the first-proxy-line check
    on the chat route, the hand-back copies and run.json."""
    px, url = proxy
    Upstream.seen.clear()
    stub_py = tmp_path / "codex_stub.py"
    stub_py.write_text(CODEX_STUB)
    stub = tmp_path / "codex"
    stub.write_text(f"#!/bin/sh\nexec python3 {stub_py} \"$@\"\n")
    stub.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    env.update(GH_TOKEN="not-for-codex", OPENAI_API_KEY="nope", CODEX_BIN=str(stub))
    (tmp_path / "proxy.jsonl").touch()  # the block scripts create the log empty before the proxy starts
    out = tmp_path / "o"  # PROXY_LOG defaults to <out>/../proxy.jsonl, the fixture's log
    r = subprocess.run(["bash", str(BASELINES / "run_codex.sh"), str(package), url, "1", "3", str(out)],
                       cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "served model: deepseek-v4-pro" in r.stdout and "ended_by=solution" in r.stdout
    events = [json.loads(l) for l in (out / "transcript.txt").read_text().splitlines()]
    seen = next(e for e in events if e["type"] == "stub")
    child_env = seen["env"]
    assert child_env["CODEX_HOME"] == str(out.resolve() / "codex_home")
    assert child_env["LEDGER_PROXY_TOKEN"] == "proxy-token-3" and "GH_TOKEN" not in child_env
    assert "OPENAI_API_KEY" not in child_env and "DEEPSEEK_API_KEY" not in child_env
    shell_added = {"PWD", "OLDPWD", "SHLVL", "_", "LC_CTYPE"}
    if sys.platform == "darwin":
        shell_added.add("__CF_USER_TEXT_ENCODING")
    assert set(child_env) - shell_added <= {"CODEX_HOME", "LEDGER_PROXY_TOKEN", "PATH", "HOME", "LANG", "LC_ALL",
                                            "TMPDIR", "TZ", "USER", "TERM", "SHELL"}
    assert seen["cwd"] == str(package.resolve()) and seen["argv"][:4] == ["exec", "--skip-git-repo-check", "-C", str(package.resolve())]
    assert seen["prompt_sha256"] == hashlib.sha256((package / "program.md").read_bytes()).hexdigest()
    # the proxy replaced the dummy token with the key and priced the call on its chat route
    assert Upstream.seen and Upstream.seen[-1]["path"] == "/v1/chat/completions"
    assert Upstream.seen[-1]["auth"] == f"Bearer {KEY}" and px.calls >= 1
    run = json.loads((out / "run.json").read_text())
    assert run["arm"] == "autoresearch" and run["client"] == "codex" and run["ended_by"] == "solution"
    assert run["model_served"] == "deepseek-v4-pro" and run["wire_api"] == "chat" and not run["probe"]
    assert run["task_sha256"] == hashlib.sha256((package / "program.md").read_bytes()).hexdigest()
    assert run["codex_bin"] == str(stub) and run["exit_code"] == 0 and run["shell_timeout"].startswith("codex default 10 s")
    assert (out / "last_message.txt").is_file() and (out / "MANIFEST.json").is_file() and (out / "features").is_dir()
    assert KEY not in (out / "transcript.txt").read_text() and KEY not in (out / "codex_home" / "config.toml").read_text()
