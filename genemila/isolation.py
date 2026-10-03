"""Experiment isolation with git worktrees.

Each experiment gets its own detached worktree at the run's base commit, with
the feature-store files it needs installed into the plugin directory. After
implementation the worktree is committed and pinned under
refs/genemila/<run>/<experiment> so the exact code can be recovered later,
even after the worktree directory is removed.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import threading
from pathlib import Path

from .spec import PLUGIN_DIR

_GIT_LOCK = threading.Lock()  # git's worktree bookkeeping is not safe under concurrent mutation
_GIT_ENV = {"GIT_AUTHOR_NAME": "genemila-lab", "GIT_AUTHOR_EMAIL": "lab@genemila.local",
            "GIT_COMMITTER_NAME": "genemila-lab", "GIT_COMMITTER_EMAIL": "lab@genemila.local"}


def git(cwd: Path, *args: str, check: bool = True) -> str:
    import os
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env={**os.environ, **_GIT_ENV})
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class WorktreeManager:
    def __init__(self, repo: Path, root: Path, run_id: str, base_commit: str | None = None):
        self.repo = Path(repo).resolve()
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.base_commit = base_commit or git(self.repo, "rev-parse", "HEAD")

    def create(self, experiment_id: str, base: str | None = None) -> Path:
        path = self.root / experiment_id
        with _GIT_LOCK:
            if path.exists():
                self._remove_locked(path)
            git(self.repo, "worktree", "add", "--detach", str(path), base or self.base_commit)
        return path

    def install_features(self, worktree: Path, store_files: dict[str, Path]) -> dict[str, str]:
        """Copy feature-store files into the worktree. Returns {relpath: sha256}."""
        installed = {}
        for name, src in store_files.items():
            rel = f"{PLUGIN_DIR}/{name}.py"
            dst = worktree / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            installed[rel] = sha256_text(dst.read_text())
        return installed

    def commit(self, worktree: Path, experiment_id: str, message: str) -> str:
        with _GIT_LOCK:
            git(worktree, "add", "-A")
            if git(worktree, "status", "--porcelain"):
                git(worktree, "commit", "-q", "-m", message)
            sha = git(worktree, "rev-parse", "HEAD")
            git(self.repo, "update-ref", f"refs/genemila/{self.run_id}/{experiment_id}", sha)
        return sha

    def remove(self, worktree: Path) -> None:
        with _GIT_LOCK:
            self._remove_locked(worktree)

    def _remove_locked(self, worktree: Path) -> None:
        git(self.repo, "worktree", "remove", "--force", str(worktree), check=False)
        if worktree.exists():
            shutil.rmtree(worktree, ignore_errors=True)
        git(self.repo, "worktree", "prune", check=False)
