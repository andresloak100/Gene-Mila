import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from genemila.config import load_config  # noqa: E402
from genemila.data.synthetic import generate  # noqa: E402


@pytest.fixture(scope="session")
def dataset(tmp_path_factory):
    return generate(tmp_path_factory.mktemp("data") / "synthetic", n_genes=120, n_perts=30, n_control=600,
                    cells_per_pert=40, seed=1)


@pytest.fixture(scope="session")
def code_repo(tmp_path_factory):
    """A throwaway git repository holding a copy of the lab code (worktrees are made from it)."""
    repo = tmp_path_factory.mktemp("repo")
    shutil.copytree(ROOT / "genemila", repo / "genemila", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "configs", repo / "configs")
    (repo / ".gitignore").write_text("__pycache__/\nruns/\n")
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    import os
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "init"]):
        subprocess.run(cmd, cwd=repo, check=True, env={**os.environ, **env})
    return repo


def make_cfg(tmp_path, **over):
    cfg = load_config()
    cfg["run"].update(workers=2, cpu_slots=2, shutdown_grace_s=3, status_interval_s=1000)
    cfg["experiment"].update(timeout_s=60, cpu_limit_s=120, ram_limit_mb=4096)
    cfg["worker"].update(provider="mock", model="mock", llm_retries=1)
    cfg["planner"].update(provider="scripted", model="scripted")
    cfg["schedule"].update(planner_min_interval_s=0.5, max_planner_calls=6)
    cfg["budget"]["ledger"] = str(tmp_path / "ledger.sqlite")
    for k, v in over.items():
        sect, key = k.split("__")
        cfg[sect][key] = v
    return cfg


@pytest.fixture
def lab_factory(tmp_path, dataset, code_repo):
    from genemila.lab import Lab

    made = []

    def factory(**over):
        cfg = make_cfg(tmp_path, **over)
        cfg["run"]["data_dir"] = str(dataset)
        lab = Lab(cfg, tmp_path / f"run{len(made)}", dataset, repo=code_repo)
        made.append(lab)
        return lab

    yield factory
    for lab in made:
        lab.stop_event.set()
        lab.kill_event.set()
