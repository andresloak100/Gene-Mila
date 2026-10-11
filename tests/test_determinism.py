"""Feature blocks are the same in every experiment process.

Python salts the hash of every str per process (PYTHONHASHSEED), so a feature that follows str hashes (here the
iteration order of a set of names, which the guard allows) computed different blocks in every experiment process
until every process that runs feature plugins started with a fixed seed (sandbox.HASH_SEED): the fresh subprocess
and the warm fork server, whose forked children inherit the server's hash secret. The smoke test computes a feature
twice in one process and never saw it. hash() and id() themselves are refused by the guard
(test_features_and_guard.py)."""

import json
import os
import re
import subprocess
import sys

import numpy as np
import pytest

from genemila.benchmark.table import run_arm
from genemila.data.bundle import export_public
from genemila.guard import CodeViolation, check_plugin_source
from genemila.isolation import WorktreeManager
from genemila.sandbox import HASH_SEED, Executor
from genemila.spec import PLUGIN_DIR

SET_ORDER = '''import numpy as np
from genemila.features.api import Feature, register


@register
class SetOrder(Feature):
    name = "{name}"
    description = "Position of gene g and of perturbation p in the iteration order of a set of their names."
    rationale = "None: a test of the hash seed; set iteration order over strings follows the process's str hashes."
    inputs = []
    dim = 2

    def compute(self, ctx, perts, params):
        genes = list(set(ctx.genes))
        names = list(set(ctx.perts))
        out = np.zeros((len(perts), ctx.n_genes, 2))
        out[:, [ctx.gene_index[g] for g in genes], 0] = np.arange(ctx.n_genes, dtype=float)
        out[:, :, 1] = np.array([names.index(p) for p in perts], dtype=float)[:, None]
        return out
'''
SPEC = {"feature_set": ["control_mean", "set_order"], "model_type": "ridge",
        "hyperparameters": {"alpha_grid": [0.1, 10.0]}, "seed": 0}


def _blocks(cache):
    """The set_order blocks one execution computed (its training and its evaluation perturbations), by cache key."""
    found = {p.name: np.load(p) for p in cache.glob("features/set_order__*.npy")}
    assert len(found) == 2, sorted(found)
    return found


def _same(a: dict, b: dict) -> bool:
    return a.keys() == b.keys() and all(np.array_equal(a[k], b[k]) for k in a)


def test_set_order_feature_is_identical_across_experiment_processes(code_repo, dataset, tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", "random")  # what every process would inherit without the fixed seed
    code = SET_ORDER.format(name="set_order")
    check_plugin_source(code, "set_order")  # set iteration order is allowed: the fixed seed makes it reproducible
    wm = WorktreeManager(code_repo, tmp_path / "wt", "hs")
    server, wt = wm.create("_server"), wm.create("EXP")
    (wt / PLUGIN_DIR / "set_order.py").write_text(code)
    pub = export_public(dataset, tmp_path / "pub")
    (tmp_path / "spec.json").write_text(json.dumps(SPEC))

    def argv(out):
        return ["run", "--spec", str(tmp_path / "spec.json"), "--public", str(pub), "--plugins",
                str(wt / PLUGIN_DIR), "--out", str(out)]

    # two fresh subprocesses and two fork servers (separate server processes, so separate hash secrets), each
    # with its own feature cache so every execution computes the blocks itself
    runs = {}
    try:
        for key in ("sub1", "sub2"):
            ex = Executor("subprocess", cache_dir=tmp_path / key / "cache")
            r = ex.run(argv(tmp_path / key / "out"), wt, tmp_path / key / "out", 60, env={"PYTHONPATH": str(wt)})
            assert r.returncode == 0, r.stderr_tail
            runs[key] = tmp_path / key
        for key in ("fork1", "fork2"):
            ex = Executor("forkserver", server, pub, tmp_path / key / "cache")
            try:
                r = ex.run(argv(tmp_path / key / "out"), wt, tmp_path / key / "out", 60)
                assert r.returncode == 0, r.stderr_tail
                assert ex.client is not None and ex.fallbacks == 0  # really forked by a warm server
            finally:
                ex.close()
            runs[key] = tmp_path / key
        # the same experiment run directly, with an explicit seed: the lab's blocks are those of HASH_SEED, and
        # the feature does follow the seed (another seed moves it), so the equalities above are not vacuous
        for seed in (HASH_SEED, HASH_SEED + 1):
            key = f"direct{seed}"
            env = {**os.environ, "PYTHONHASHSEED": str(seed), "PYTHONPATH": str(wt)}
            p = subprocess.run([sys.executable, "-m", "genemila.pipeline", *argv(tmp_path / key / "out"), "--cache",
                                str(tmp_path / key / "cache")], cwd=wt, env=env, capture_output=True, text=True)
            assert p.returncode == 0, p.stderr[-2000:]
            runs[key] = tmp_path / key
    finally:
        wm.remove(server)
        wm.remove(wt)

    ref_blocks = _blocks(runs["sub1"] / "cache")
    ref_delta = np.load(runs["sub1"] / "out" / "predictions.npz")["delta"]
    for key in ("sub2", "fork1", "fork2", f"direct{HASH_SEED}"):
        assert _same(_blocks(runs[key] / "cache"), ref_blocks), key
        assert np.array_equal(np.load(runs[key] / "out" / "predictions.npz")["delta"], ref_delta), key
    other = _blocks(runs[f"direct{HASH_SEED + 1}"] / "cache")
    assert other.keys() == ref_blocks.keys() and not any(np.array_equal(other[k], ref_blocks[k]) for k in other)


def test_run_limited_overrides_an_inherited_or_passed_hash_seed(tmp_path, monkeypatch):
    from genemila.sandbox import run_limited
    monkeypatch.setenv("PYTHONHASHSEED", "random")
    code = ("import os, sys; print(os.environ['PYTHONHASHSEED'], sys.flags.hash_randomization, hash('ATF4'), "
            "list({'ATF4', 'XBP1', 'HSPA5', 'DDIT3', 'ERN1'}))")
    outs = []
    for i, env in enumerate([None, {"PYTHONHASHSEED": "7"}]):
        r = run_limited([sys.executable, "-c", code], tmp_path, tmp_path, timeout_s=30, env=env, name=f"h{i}")
        assert r.returncode == 0, r.stderr_tail
        outs.append(r.stdout_tail)
    assert outs[0] == outs[1] and outs[0].startswith(f"{HASH_SEED} 0 ")


def test_lab_records_the_hash_seed_outside_the_arm(lab_factory, tmp_path):
    from conftest import make_cfg
    from genemila.lab import Lab, open_run

    lab = lab_factory()
    assert lab.cfg["run"]["hash_seed"] == HASH_SEED
    row = lab.db.query("SELECT config_json FROM runs WHERE run_id=?", (lab.run_id,))[0]
    assert json.loads(row["config_json"])["run"]["hash_seed"] == HASH_SEED
    plain = {**lab.cfg, "run": {k: v for k, v in lab.cfg["run"].items() if k != "hash_seed"}}
    assert run_arm(lab.cfg) == run_arm(plain)  # a run label already carries the code version
    # a run from before the seed was fixed, reopened (status, reproduce): its processes each drew their own seed,
    # and its config keeps saying nothing about one
    cfg = json.loads(row["config_json"])
    del cfg["run"]["hash_seed"]
    lab.db.execute("UPDATE runs SET config_json=? WHERE run_id=?", (json.dumps(cfg), lab.run_id))
    old = open_run(lab.run_dir)
    try:
        assert "hash_seed" not in old.cfg["run"]
    finally:
        old.close()
    bad = make_cfg(tmp_path)
    bad["run"].update(hash_seed=HASH_SEED + 1, data_dir=lab.cfg["run"]["data_dir"])
    with pytest.raises(RuntimeError, match="hash_seed"):
        Lab(bad, tmp_path / "run_bad", lab.data_dir, repo=lab.repo)


def test_warm_start_refuses_a_past_plugin_built_on_hash(lab_factory):
    """A past run's plugin built on hash() of a name (as two agent plugins on the owner's Mac were) passed the guard
    of its day; continuing that campaign runs every imported plugin through today's guard: it is refused, not
    imported, and left out of the starting model and of the features offered as helpful, and so is a plugin that
    computes it through ctx.feature; the reasons are in warm_start.json and the warm_start event. A deterministic
    plugin of the same run is imported as before, also when it keys a cache by id(), which an agent's new plugin may
    not do."""
    import time
    from genemila.providers.mock import TEMPLATES
    first = lab_factory()
    salted = TEMPLATES["variance"].format(name="salted_e2").replace(
        "return np.broadcast_to", "u = np.array([abs(hash(p)) % 1000 / 1000.0 for p in perts])\n"
                                  "        return u[:, None, None] + np.broadcast_to")
    via = TEMPLATES["variance"].format(name="via_salted_e3").replace(
        "return np.broadcast_to", "return np.asarray(ctx.feature('salted_e2', perts)) + np.broadcast_to")
    # id() as a cache key into a per-context dict, as in the plugins of past runs' reported models: no value changes
    cached = TEMPLATES["variance"].format(name="steady_e4").replace(
        "return np.broadcast_to", "memo = {}\n        memo.setdefault(id(ctx), len(perts))\n"
                                  "        return np.broadcast_to")
    plugins = {"salted_e2": salted, "via_salted_e3": via, "steady_e4": cached}
    for name, code in plugins.items():
        (first.store / f"{name}.py").write_text(code)
        first.db.upsert_feature({"name": name, "description": "d", "rationale": "r", "creator_experiment": "EXP_0009",
                                 "implementation_path": f"feature_store/{name}.py"})
    feats = ["control_mean", "mean_response", "salted_e2", "via_salted_e3", "steady_e4"]
    for i, (new, score) in enumerate((("steady_e4", 0.9), ("salted_e2", 0.5))):
        first.db.insert_experiment({
            "experiment_id": f"EXP_09{i:02d}", "run_id": first.run_id, "status": "completed", "kind": "new_feature",
            "new_feature": new, "feature_set_json": feats, "feature_params_json": {}, "model_type": "ridge",
            "hyperparameters_json": {"alpha": 10.0}, "primary_score": score, "delta_from_parent": 0.05,
            "finished_at": time.time(), "dataset": first.dataset, "split_id": first.split_id})
    second = lab_factory(run__continue_from=str(first.run_dir))
    info = second.warm_start(first.run_dir)
    with pytest.raises(CodeViolation, match=re.escape("call of id() not allowed")):
        check_plugin_source(cached, "steady_e4")
    assert info["imported"] == ["steady_e4"] and info["missing"] == []
    assert set(info["refused"]) == {"salted_e2", "via_salted_e3"}
    assert "use of 'hash' not allowed: hash() and id() differ between processes" in info["refused"]["salted_e2"]
    assert info["refused"]["via_salted_e3"] == "names refused feature(s) salted_e2"
    assert info["features"] == ["control_mean", "mean_response", "steady_e4"]
    assert info["helpful_features"] == ["steady_e4"]
    assert not (second.store / "salted_e2.py").exists() and not (second.store / "via_salted_e3.py").exists()
    assert {f["name"] for f in second.db.features()} >= {"steady_e4"}
    assert not {f["name"] for f in second.db.features()} & {"salted_e2", "via_salted_e3"}
    assert json.loads((second.run_dir / "warm_start.json").read_text())["refused"] == info["refused"]
    (ev,) = second.db.query("SELECT message FROM events WHERE kind='warm_start'")
    assert ev["message"].endswith("; refused by the plugin guard ['salted_e2', 'via_salted_e3']"), ev
    assert second.db.get_experiment(info["start_experiment"])["feature_set_json"] == info["features"]


# ------------------------------------------------------------------ the tools that run plugins in their own process
REEXEC_PROBE = ("import os, sys; sys.path.insert(0, {root!r}); from genemila import sandbox; "
                "r = sandbox.reexec_under_hash_seed('probe'); "
                "print(sandbox.python_hash_seed(), r, sys.flags.dont_write_bytecode, sys._xoptions.get('probe'), "
                "os.environ.get(sandbox.HASH_REEXEC_ENV) == str(os.getpid()), sys.argv[1:])")


@pytest.mark.parametrize("seed", ["random", "7", "0"])
def test_reexec_under_hash_seed_keeps_the_command_and_runs_once(seed, tmp_path):
    """The tools' command line re-executes itself under the lab's seed: interpreter options (-B, -X) and arguments
    survive, and the re-executed process knows it is one; under the lab's seed nothing happens."""
    from pathlib import Path
    root = str(Path(__file__).resolve().parent.parent)
    env = {k: v for k, v in os.environ.items() if k != "GENEMILA_HASHSEED_REEXEC"}
    env["PYTHONHASHSEED"] = seed
    p = subprocess.run([sys.executable, "-B", "-X", "probe=kept", "-c", REEXEC_PROBE.format(root=root), "a", "b c"],
                       env=env, capture_output=True, text=True, cwd=tmp_path, timeout=60)
    assert p.returncode == 0, p.stderr
    again = seed != str(HASH_SEED)
    assert p.stdout.split("\n")[0] == f"{HASH_SEED} {again} 1 kept {again} ['a', 'b c']", p.stdout
    assert p.stderr == ""


def test_reexec_under_hash_seed_never_loops(monkeypatch, capsys):
    """Where the variable cannot take effect (an interpreter that ignores the environment, or a re-execution whose
    seed still is not the lab's), the tool goes on under its own seed and says so; a flag inherited from another
    process (another pid) does not stop a re-execution."""
    from genemila import sandbox
    calls = []

    def fake_exec(path, argv, env):
        calls.append((path, argv, env))
        raise SystemExit(0)
    monkeypatch.setattr(sandbox.os, "execve", fake_exec)
    monkeypatch.setattr(sandbox, "python_hash_seed", lambda: "5")
    monkeypatch.setenv(sandbox.HASH_REEXEC_ENV, str(os.getpid() + 1))  # inherited from another process
    with pytest.raises(SystemExit):
        sandbox.reexec_under_hash_seed("probe")
    (path, argv, env), = calls
    assert path == sys.executable and argv == [sys.executable, *sys.orig_argv[1:]]
    assert env["PYTHONHASHSEED"] == str(HASH_SEED) and env[sandbox.HASH_REEXEC_ENV] == str(os.getpid())
    monkeypatch.setenv(sandbox.HASH_REEXEC_ENV, str(os.getpid()))  # this process is the re-execution already
    assert sandbox.reexec_under_hash_seed("probe") is True and len(calls) == 1
    assert "the str hash seed is 5, not 0" in capsys.readouterr().err
    from pathlib import Path
    root = str(Path(__file__).resolve().parent.parent)
    p = subprocess.run([sys.executable, "-E", "-c", REEXEC_PROBE.format(root=root)], capture_output=True, text=True,
                       env={**os.environ, "PYTHONHASHSEED": "3"}, timeout=60)
    assert p.returncode == 0 and p.stdout.startswith("random False 0 None False"), (p.stdout, p.stderr)
    assert "the interpreter ignores the environment" in p.stderr
