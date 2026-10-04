"""Programmatic enforcement for agent-written code.

1. Static check: feature plugins may import only numeric libraries and the
   feature API, may not do I/O, reflection, process or network access, and
   may not touch FeatureContext internals.
2. Diff check: a worktree may only differ from its base commit in the
   experiment's allowed files.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from .spec import PROTECTED_PATHS

ALLOWED_IMPORT_ROOTS = {"numpy", "scipy", "sklearn", "math", "itertools", "functools", "collections",
                        "typing", "__future__", "dataclasses", "statistics", "heapq"}
ALLOWED_GENEMILA = {"genemila.features.api"}
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "globals", "locals", "vars", "input",
                "breakpoint", "getattr", "setattr", "delattr", "memoryview", "exit", "quit"}
BANNED_ATTRS = {"load", "save", "savez", "savez_compressed", "loadtxt", "genfromtxt", "fromfile", "tofile",
                "memmap", "system", "popen", "read_csv", "read_table", "read_pickle", "to_csv",
                "_train_delta", "_train_pos", "_targets", "_feature_cache", "public_dir", "cache_dir",
                "_preloaded", "shared", "without_train", "_disk_cached", "__dict__",
                "__class__", "__subclasses__", "__globals__", "__builtins__", "__code__", "__bases__",
                "__mro__", "f_globals", "f_locals"}


class CodeViolation(ValueError):
    pass


def check_plugin_source(source: str, expected_name: str) -> dict:
    """Validate a feature plugin. Returns {class_name}. Raises CodeViolation."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise CodeViolation(f"syntax error: {exc}") from exc
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORT_ROOTS and a.name not in ALLOWED_GENEMILA:
                    problems.append(f"import of {a.name!r} not allowed")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level or (mod.split(".")[0] not in ALLOWED_IMPORT_ROOTS and mod not in ALLOWED_GENEMILA):
                problems.append(f"import from {mod!r} not allowed")
            if mod.split(".")[0] in ("numpy", "scipy") and any(a.name in BANNED_ATTRS for a in node.names):
                problems.append("importing file I/O helpers is not allowed")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            problems.append(f"use of {node.id!r} not allowed")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRS:
            problems.append(f"access to .{node.attr} not allowed")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            problems.append("global/nonlocal statements not allowed")
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    registered = []
    for c in classes:
        if any((isinstance(d, ast.Name) and d.id == "register") for d in c.decorator_list):
            for stmt in c.body:
                if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "name" for t in stmt.targets):
                    if isinstance(stmt.value, ast.Constant):
                        registered.append((c.name, stmt.value.value))
    if len(registered) != 1:
        problems.append(f"file must register exactly one feature class (found {len(registered)})")
    elif registered[0][1] != expected_name:
        problems.append(f"feature name must be {expected_name!r}, got {registered[0][1]!r}")
    for stmt in tree.body:  # no top-level side effects beyond imports/classes/constants/functions
        if not isinstance(stmt, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.Assign,
                                 ast.AnnAssign, ast.Expr)):
            problems.append(f"top-level {type(stmt).__name__} statement not allowed")
        if isinstance(stmt, ast.Expr) and not isinstance(stmt.value, ast.Constant):
            problems.append("top-level expressions (other than docstrings) not allowed")
    if problems:
        raise CodeViolation("; ".join(sorted(set(problems))))
    return {"class_name": registered[0][0]}


def changed_files(worktree: Path, base_commit: str) -> list[str]:
    def git(*args):
        return subprocess.run(["git", *args], cwd=worktree, capture_output=True, text=True, check=True).stdout
    files = set(git("diff", "--name-only", base_commit).split())
    files |= set(git("ls-files", "--others", "--exclude-standard").split())
    return sorted(files)


def check_diff(worktree: Path, base_commit: str, allowed_files: list[str], installed: list[str]) -> list[str]:
    """Return changed files; raise CodeViolation if any change is not allowed.

    `installed` are feature-store files the controller itself copied in."""
    files = changed_files(worktree, base_commit)
    bad = [f for f in files if f not in allowed_files and f not in installed]
    protected = [f for f in bad if any(f == p or f.startswith(p) for p in PROTECTED_PATHS)]
    if protected:
        raise CodeViolation(f"modified protected files: {protected}")
    if bad:
        raise CodeViolation(f"modified files outside the allowed set: {bad}")
    return [f for f in files if f not in installed]
