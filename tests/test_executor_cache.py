import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

from genemila.data.bundle import export_public
from genemila.isolation import WorktreeManager
from genemila.sandbox import Executor
from genemila.spec import PLUGIN_DIR

SPEC = {"feature_set": ["control_mean", "mean_response", "is_target"], "model_type": "ridge",
        "hyperparameters": {"alpha_grid": [0.1, 10.0]}, "seed": 0}


def _setup(code_repo, dataset, tmp_path, name):
    wm = WorktreeManager(code_repo, tmp_path / "wt", name)
    server = wm.create("_server")
    wt = wm.create("EXP")
    pub = export_public(dataset, tmp_path / "pub")
    (tmp_path / "spec.json").write_text(json.dumps(SPEC))
    return wm, server, wt, pub


def _argv(tmp_path, pub, wt, out):
    return ["run", "--spec", str(tmp_path / "spec.json"), "--public", str(pub), "--plugins",
            str(wt / PLUGIN_DIR), "--out", str(out)]


def test_forkserver_matches_subprocess_and_cache_is_exact(code_repo, dataset, tmp_path):
    wm, server, wt, pub = _setup(code_repo, dataset, tmp_path, "rx")
    plain = Executor("subprocess")
    warm = Executor("forkserver", server, pub, tmp_path / "cache")
    try:
        r1 = plain.run(_argv(tmp_path, pub, wt, tmp_path / "a"), wt, tmp_path / "a", 60, env={"PYTHONPATH": str(wt)})
        r2 = warm.run(_argv(tmp_path, pub, wt, tmp_path / "b"), wt, tmp_path / "b", 60)
        r3 = warm.run(_argv(tmp_path, pub, wt, tmp_path / "c"), wt, tmp_path / "c", 60)  # cache hits
        assert (r1.returncode, r2.returncode, r3.returncode) == (0, 0, 0), r2.stderr_tail
        assert warm.client is not None and warm.fallbacks == 0
        a, b, c = (np.load(tmp_path / d / "predictions.npz")["delta"] for d in "abc")
        assert np.array_equal(a, b) and np.array_equal(b, c)
        cache = json.loads((tmp_path / "c" / "result.json").read_text())["feature_cache"]
        assert set(cache["hits"]) == set(SPEC["feature_set"]) and not cache["misses"]
        assert r2.cpu_s < r1.cpu_s  # no interpreter start-up or imports in the forked child
    finally:
        warm.close()
        wm.remove(server)
        wm.remove(wt)


def test_forkserver_timeout_and_kill(code_repo, dataset, tmp_path):
    wm, server, wt, pub = _setup(code_repo, dataset, tmp_path, "ry")
    (wt / PLUGIN_DIR / "spin.py").write_text(
        "import numpy as np\nfrom genemila.features.api import Feature, register\n\n@register\nclass S(Feature):\n"
        "    name = 'spin'\n    def compute(self, ctx, perts, params):\n        while True:\n            pass\n")
    (tmp_path / "spec.json").write_text(json.dumps({**SPEC, "feature_set": ["spin"]}))
    warm = Executor("forkserver", server, pub, None)
    try:
        r = warm.run(_argv(tmp_path, pub, wt, tmp_path / "t"), wt, tmp_path / "t", timeout_s=2)
        assert r.timed_out and r.returncode != 0
        ev = threading.Event()
        threading.Timer(0.5, ev.set).start()
        t0 = time.monotonic()
        r = warm.run(_argv(tmp_path, pub, wt, tmp_path / "k"), wt, tmp_path / "k", timeout_s=60, kill_event=ev)
        assert "deadline" in r.killed_reason and time.monotonic() - t0 < 8
        # the server keeps serving after its children were killed
        (tmp_path / "spec.json").write_text(json.dumps(SPEC))
        assert warm.run(_argv(tmp_path, pub, wt, tmp_path / "ok"), wt, tmp_path / "ok", 60).returncode == 0
    finally:
        warm.close()
        wm.remove(server)
        wm.remove(wt)


def test_executor_falls_back_when_server_cannot_start(dataset, tmp_path, code_repo):
    wm = WorktreeManager(code_repo, tmp_path / "wt", "rz")
    wt = wm.create("EXP")
    pub = export_public(dataset, tmp_path / "pub")
    (tmp_path / "spec.json").write_text(json.dumps(SPEC))
    ex = Executor("forkserver", tmp_path / "does-not-exist", pub, None)
    r = ex.run(_argv(tmp_path, pub, wt, tmp_path / "f"), wt, tmp_path / "f", 60, env={"PYTHONPATH": str(wt)})
    assert r.returncode == 0 and ex.mode == "subprocess"
    wm.remove(wt)
