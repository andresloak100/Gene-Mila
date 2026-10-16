"""The block H runners and the hand-back collector (tools/baselines/): collect_handback sorts a session's kept features
into accepted and rejected --source files with a manifest; run_biomni refuses an unsafe place and, where biomni is
installed, runs its probe against the mock endpoint through the proxy; the autoresearch script parses and dry-runs."""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "baselines"))
import collect_handback as ch  # noqa: E402
import export_task_package as etp  # noqa: E402
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


def test_collect_handback_sorts_kept_features_and_writes_the_manifest(package, tmp_path):
    for spec in (HELPFUL, BAD, UNGUARDED):
        _write(package, spec)
    out = tmp_path / "out_r2"
    out.mkdir()
    (out / "run.json").write_text(json.dumps({"arm": "biomni", "seed": 2, "model": "deepseek-v4-pro",
                                              "ended_by": "timeout", "minutes": 20}))
    dest = tmp_path / "handback"
    assert ch.main(["--out", str(out), "--package", str(package), "--dest", str(dest)]) == 0
    assert sorted(p.name for p in (dest / "biomni_r2").iterdir()) == ["ar_target_corr.py"]
    assert sorted(p.name for p in (dest / "rejected" / "biomni_r2").iterdir()) == ["ar_pasted_table.py",
                                                                                    "ar_reads_a_file.py"]
    assert (dest / "biomni_r2" / "ar_target_corr.py").read_bytes() == (package / "features" / "ar_target_corr.py").read_bytes()
    m = json.loads((dest / "manifest.json").read_text())
    s = m["sessions"]["biomni_r2"]
    assert s["origin"] == "features/ (no results.tsv)" and s["run"]["ended_by"] == "timeout" and s["results_tsv_sha256"] is None
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
    env = {k: v for k, v in os.environ.items() if k != "DEEPSEEK_API_KEY"}
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
    # a proxy that is not local
    r = subprocess.run(base + ["--package", str(package), "--proxy", "https://api.deepseek.com"], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 2 and "--proxy" in r.stderr


def test_run_biomni_probe_through_the_proxy(package, tmp_path, monkeypatch):
    pytest.importorskip("biomni")
    pytest.importorskip("langchain_openai")
    from http.server import ThreadingHTTPServer
    import ledger_proxy as lp
    from test_ledger_proxy import KEY, PRICING, Upstream
    up = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    proxy = lp.Proxy(f"http://127.0.0.1:{up.server_address[1]}", tmp_path / "ledger.sqlite", "probe", "biomni", 0.05,
                     100.0, tmp_path / "proxy.jsonl", PRICING, KEY)
    srv = lp.make_server("127.0.0.1:0", proxy)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        env = {k: v for k, v in os.environ.items() if k != "DEEPSEEK_API_KEY"}
        r = subprocess.run([sys.executable, str(BASELINES / "run_biomni.py"), "--package", str(package), "--proxy",
                            f"http://127.0.0.1:{srv.server_address[1]}", "--model", "deepseek-v4-pro", "--seed", "1",
                            "--out", str(tmp_path / "probe"), "--probe"], cwd=tmp_path, env=env, capture_output=True,
                           text=True, timeout=240)
        run = json.loads((tmp_path / "probe" / "run.json").read_text())
        assert run["probe"] and run["minutes"] == 2 and run["ended_by"] in ("solution", "error"), r.stdout + r.stderr
        assert proxy.calls >= 1 and (tmp_path / "probe" / "transcript.txt").exists()
        assert KEY not in (tmp_path / "probe" / "transcript.txt").read_text()
    finally:
        srv.shutdown()
        up.shutdown()


def test_run_autoresearch_script_parses_and_dry_runs(package, tmp_path):
    script = BASELINES / "run_autoresearch.sh"
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True).returncode == 0
    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "API_KEY")}
    r = subprocess.run(["bash", str(script), "--dry-run", str(package), "http://127.0.0.1:8787", "20", "4",
                        str(tmp_path / "out")], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert "claude -p" in r.stdout and "--permission-mode acceptEdits" in r.stdout
    assert "--disallowedTools WebSearch WebFetch" in r.stdout and "--strict-mcp-config" in r.stdout
    assert "ANTHROPIC_BASE_URL=http://127.0.0.1:8787/anthropic" in r.stdout
    assert "ANTHROPIC_AUTH_TOKEN=proxy-token-4" in r.stdout and "ANTHROPIC_API_KEY unset" in r.stdout
    assert "for 1200 s" in r.stdout and "ANTHROPIC_MODEL=deepseek-v4-pro" in r.stdout
    # the refusals that need no claude: a wrong argument count, a key in the shell, a non-local proxy
    assert subprocess.run(["bash", str(script), str(package)], capture_output=True, env=env).returncode == 2
    r = subprocess.run(["bash", str(script), str(package), "http://127.0.0.1:8787", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env={**env, "API_KEY": "x"})
    assert r.returncode == 2 and "only the proxy may hold the key" in r.stderr
    r = subprocess.run(["bash", str(script), str(package), "https://api.deepseek.com", "20", "4", str(tmp_path / "o")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "local ledger proxy" in r.stderr
