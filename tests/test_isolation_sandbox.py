import sys
import threading
import time

import pytest

from genemila.guard import CodeViolation, check_diff
from genemila.isolation import WorktreeManager, git
from genemila.sandbox import run_limited
from genemila.spec import PLUGIN_DIR


def test_worktrees_are_isolated_and_pinned(code_repo, tmp_path):
    wm = WorktreeManager(code_repo, tmp_path / "wt", "runX")
    a, b = wm.create("EXP_A"), wm.create("EXP_B")
    (a / PLUGIN_DIR / "fa.py").write_text("x = 1\n")
    assert not (b / PLUGIN_DIR / "fa.py").exists()
    assert not (code_repo / PLUGIN_DIR / "fa.py").exists()
    sha = wm.commit(a, "EXP_A", "test")
    assert git(code_repo, "rev-parse", "refs/genemila/runX/EXP_A") == sha
    wm.remove(a)
    wm.remove(b)
    assert not a.exists()
    assert "fa.py" in git(code_repo, "show", "--name-only", sha)  # code survives worktree removal


def test_diff_check_blocks_protected_and_unlisted_files(code_repo, tmp_path):
    wm = WorktreeManager(code_repo, tmp_path / "wt", "runY")
    wt = wm.create("EXP_C")
    allowed = [f"{PLUGIN_DIR}/ok.py"]
    (wt / PLUGIN_DIR / "ok.py").write_text("x = 1\n")
    assert check_diff(wt, wm.base_commit, allowed, []) == allowed
    ev = wt / "genemila" / "benchmark" / "evaluator.py"
    ev.write_text(ev.read_text() + "\n# tampered\n")
    with pytest.raises(CodeViolation, match="protected"):
        check_diff(wt, wm.base_commit, allowed, [])
    git(wt, "checkout", "--", "genemila/benchmark/evaluator.py")
    (wt / PLUGIN_DIR / "other.py").write_text("y = 2\n")
    with pytest.raises(CodeViolation, match="outside"):
        check_diff(wt, wm.base_commit, allowed, [])
    wm.remove(wt)


def test_timeout_kills_process(tmp_path):
    r = run_limited([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, tmp_path, timeout_s=1)
    assert r.timed_out and r.killed_reason.startswith("timeout")
    assert r.wall_s < 6


def test_memory_limit(tmp_path):
    r = run_limited([sys.executable, "-c", "x = bytearray(1500 * 2**20); import time; time.sleep(2)"],
                    tmp_path, tmp_path, timeout_s=20, ram_mb=300)
    assert r.returncode != 0


def test_external_kill_event(tmp_path):
    ev = threading.Event()
    threading.Timer(0.5, ev.set).start()
    t0 = time.monotonic()
    r = run_limited([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, tmp_path, timeout_s=60,
                    kill_event=ev)
    assert "deadline" in r.killed_reason and time.monotonic() - t0 < 6


def test_cpu_and_rss_are_measured(tmp_path):
    r = run_limited([sys.executable, "-c", "s=0\nfor i in range(3_000_000): s+=i"], tmp_path, tmp_path, timeout_s=30)
    assert r.returncode == 0 and r.cpu_s > 0.05 and r.peak_rss_mb > 1
