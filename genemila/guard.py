"""Programmatic enforcement for agent-written code.

1. Static check: feature plugins may import only numeric libraries and the
   feature API, may not do I/O, reflection, process or network access, may
   not touch FeatureContext internals, and may not use hash() or id(), whose
   values differ between processes, nor iterate a set of objects, whose
   order follows their memory addresses.
2. Diff check: a worktree may only differ from its base commit in the
   experiment's allowed files.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from .spec import PROTECTED_PATHS

# zlib and hashlib only compute (crc32, adler32, sha256 ... of bytes; no file or network access): they are the stable
# replacement for hash() that PROCESS_NOISE recommends
ALLOWED_IMPORT_ROOTS = {"numpy", "scipy", "sklearn", "math", "itertools", "functools", "collections",
                        "typing", "__future__", "dataclasses", "statistics", "heapq", "zlib", "hashlib"}
ALLOWED_GENEMILA = {"genemila.features.api"}
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "globals", "locals", "vars", "input",
                "breakpoint", "getattr", "setattr", "delattr", "memoryview", "exit", "quit",
                "type", "__file__", "__build_class__", "super", "__builtins__"}
BANNED_ATTRS = {"load", "save", "savez", "savez_compressed", "loadtxt", "genfromtxt", "fromfile", "tofile",
                "memmap", "system", "popen", "read_csv", "read_table", "read_pickle", "to_csv",
                "_train_delta", "_train_pos", "_targets", "_feature_cache", "public_dir", "cache_dir",
                "_preloaded", "shared", "without_train", "_disk_cached", "__init__", "__new__",
                "__init_subclass__", "__dict__",
                "__class__", "__subclasses__", "__globals__", "__builtins__", "__code__", "__bases__",
                "__mro__", "f_globals", "f_locals",
                # the builtins module (hash, id, open, __import__ ... by attribute) as allowed modules expose it:
                # dataclasses.builtins, dataclasses.sys.modules["builtins"], collections._sys,
                # numpy._globals.enum.bltns, a builtin function's __self__ (len.__self__), a frame's f_builtins; os
                # as they expose it (genemila.features.api.os, statistics.random._os); and attribute lookup by
                # string, object.__getattribute__(x, "__hash__"), past every name above
                "builtins", "bltns", "sys", "_sys", "modules", "__self__", "f_builtins", "os", "_os",
                "__getattribute__", "__getattr__"}


class CodeViolation(ValueError):
    pass


# Python salts the hash of every str and bytes per process (PYTHONHASHSEED), and id() is a memory address, so a
# feature built on either is a different pseudo-random number in every process that computes it: the lab's stored
# scores of a model holding it cannot be reproduced, and two identical feature audits disagree. The same holds for
# the iteration order of a set of objects other than strings and numbers (functions, arrays, instances), which hash
# by address, so that not even the fixed hash seed every experiment process runs with (sandbox.HASH_SEED) fixes it.
# The smoke test computes a feature twice in one process, where both agree, so its determinism check never sees this.
PROCESS_NOISE = ("hash() and id() differ between processes (str hashes are salted per process, id() is a memory "
                 "address), and so does the order of a set of objects other than strings and numbers, such as "
                 "functions or arrays (it follows their addresses), so a feature built on them is noise that no "
                 "other process reproduces; use a stable mapping instead, such as sorted order, a tuple or list in "
                 "place of such a set, or an index into ctx.perts or ctx.genes (ctx.gene_index), or, if a hash is "
                 "truly needed, zlib.crc32 or hashlib (both allowed imports) on encoded bytes, e.g. "
                 "zlib.crc32(name.encode())")
PROCESS_BUILTINS = ("hash", "id")  # the builtins behind PROCESS_NOISE, unless the plugin binds the name itself
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
_ORDER_FREE = ("len", "any", "all", "bool", "set", "frozenset", "sorted")  # consume a set whatever its order (sorted:
                                                                          # without a key, whose ties would keep it)


class _Scope:
    """One scope of a parsed plugin (module, class, function or lambda, comprehension): the names it binds, each with
    the index of the first statement of the module or class body that binds it, and, while that body is walked, the
    index of the statement being walked. A module or class body runs top to bottom, so in it a name is bound only by
    an earlier statement: until then (and in `hash = hash` itself) the name is still the builtin."""
    __slots__ = ("kind", "bound", "at")

    def __init__(self, kind: str):
        self.kind, self.bound, self.at = kind, {}, 0

    def bind(self, name: str) -> None:
        self.bound.setdefault(name, self.at)


def _scoped_loads(tree: ast.AST, names) -> list[tuple[ast.Name, list[tuple[_Scope, int]]]]:
    """Every load of one of `names` in a parsed plugin, with the scopes it can see at that point (innermost first,
    each with the index of its body statement then running), once every binding of the plugin has been recorded on
    its scope: an argument, an assignment or loop target, a def or class, an import, an except or match capture, a
    := (in the nearest scope that is not a comprehension). As in Python, a function's decorators, defaults and
    annotations, a class's decorators, bases and keywords, and a comprehension's first iterable are evaluated in the
    enclosing scope."""
    loads = []

    def walk(node, chain):
        scope = chain[-1]
        if isinstance(node, ast.Module):
            for i, stmt in enumerate(node.body):
                scope.at = i
                walk(stmt, chain)
            return
        if isinstance(node, _FUNCTIONS):
            a = node.args
            params = [x for x in (*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg) if x is not None]
            outer = [*getattr(node, "decorator_list", []), *a.defaults, *(d for d in a.kw_defaults if d is not None),
                     *(x.annotation for x in params if x.annotation is not None)]
            for n in outer + ([node.returns] if getattr(node, "returns", None) else []):
                walk(n, chain)
            if not isinstance(node, ast.Lambda):
                scope.bind(node.name)
            inner = _Scope("function")
            for x in params:
                inner.bind(x.arg)
            for n in node.body if isinstance(node.body, list) else [node.body]:
                walk(n, chain + [inner])
            return
        if isinstance(node, ast.ClassDef):
            for n in (*node.decorator_list, *node.bases, *node.keywords):
                walk(n, chain)
            scope.bind(node.name)
            inner = _Scope("class")
            for i, stmt in enumerate(node.body):
                inner.at = i
                walk(stmt, chain + [inner])
            return
        if isinstance(node, _COMPREHENSIONS):
            walk(node.generators[0].iter, chain)
            inner = chain + [_Scope("comprehension")]
            for j, gen in enumerate(node.generators):
                walk(gen.target, inner)
                if j:
                    walk(gen.iter, inner)
                for cond in gen.ifs:
                    walk(cond, inner)
            for n in ([node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]):
                walk(n, inner)
            return
        if isinstance(node, ast.NamedExpr):
            next(s for s in reversed(chain) if s.kind != "comprehension").bind(node.target.id)
            walk(node.value, chain)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for al in node.names:
                scope.bind(al.asname or al.name.split(".")[0])
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            scope.bind(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            scope.bind(node.rest)
        elif isinstance(node, ast.Name):
            if not isinstance(node.ctx, ast.Load):
                scope.bind(node.id)
            elif node.id in names:
                loads.append((node, [(s, s.at) for s in reversed(chain)]))
        for child in ast.iter_child_nodes(node):
            walk(child, chain)

    walk(tree, [_Scope("module")])
    return loads


def _is_builtin(name: str, scopes: list[tuple[_Scope, int]]) -> bool:
    """Whether a load of `name` that sees these scopes (innermost first) reaches the builtin: none of them binds it
    by then. A class body's names are invisible inside its functions and comprehensions. A function binding the name
    anywhere makes it local throughout. A module or class body binds it only from the statement after its binding
    one, unless the load sits in a function body, which is taken to run once the module has run (as compute() does)."""
    deferred = False
    for i, (scope, at) in enumerate(scopes):
        if scope.kind == "class" and i:
            continue
        if name in scope.bound and (deferred or scope.kind not in ("module", "class") or scope.bound[name] < at):
            return False
        deferred = deferred or scope.kind == "function"
    return True


def _fixed_hash(node: ast.AST) -> bool:
    """A literal whose hash, and so its place in a set, is the same in every process under the fixed hash seed: a
    str, bytes or number constant (also negated), or a tuple of such."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        node = node.operand
    if isinstance(node, ast.Tuple):
        return all(_fixed_hash(e) for e in node.elts)
    return isinstance(node, ast.Constant)


def _unordered_sets(tree: ast.AST) -> list[str]:
    """Set displays, {f, g} or set([f, g]) / frozenset((f, g)), holding anything but fixed-hash literals (functions,
    arrays, any variable), used other than in an order-free way (a membership test, len, any, all, bool, set,
    frozenset, sorted without a key): iterated, their order follows the elements' hashes, which for any object but a
    str or number is its address. A set built at run time (set(xs), a set comprehension) cannot be judged here."""
    parent = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Set):
            elts = node.elts
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("set", "frozenset")
              and len(node.args) == 1 and isinstance(node.args[0], (ast.List, ast.Tuple, ast.Set))):
            elts = node.args[0].elts
        else:
            continue
        if all(_fixed_hash(e) for e in elts):
            continue
        p = parent.get(node)
        if isinstance(p, ast.Compare) and any(c is node and isinstance(op, (ast.In, ast.NotIn))
                                              for op, c in zip(p.ops, p.comparators)):
            continue
        if (isinstance(p, ast.Call) and any(a is node for a in p.args) and isinstance(p.func, ast.Name)
                and p.func.id in _ORDER_FREE and not (p.func.id == "sorted" and any(k.arg == "key"
                                                                                    for k in p.keywords))):
            continue
        out.append(f"iteration over a set of objects (line {node.lineno})")
    return out


def process_dependent_uses(tree: ast.AST, builtins: tuple[str, ...] = PROCESS_BUILTINS) -> list[str]:
    """What in a parsed plugin differs between processes: the builtins hash and id wherever the name reaches them (a
    call, and also an alias such as h = hash, key=hash or key=id), the name __hash__ and any attribute .__hash__
    (x.__hash__(), str.__hash__) always, and a set display of objects whose order is used (_unordered_sets). A name
    the plugin binds itself is not the builtin where its binding reaches, by Python's scoping (_is_builtin): a local
    variable or loop variable called hash or id, an argument, or a helper def hash(s) built on zlib.crc32; a binding
    elsewhere in the module (another function's argument id) does not hide the builtin, and neither does one in the
    same statement (hash = hash at module level). Routes to the builtins module itself are banned attributes.
    `builtins` narrows which of the two builtins count (check_plugin_source(imported=True) passes ("hash",))."""
    called = {n.func for n in ast.walk(tree) if isinstance(n, ast.Call)}
    uses = []
    for node, scopes in _scoped_loads(tree, builtins):
        if _is_builtin(node.id, scopes):
            uses.append("call of id()" if node.id == "id" and node in called else f"use of {node.id!r}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "__hash__":
            uses.append("use of '__hash__'")
        elif isinstance(node, ast.Attribute) and node.attr == "__hash__":
            uses.append("access to .__hash__")
    return sorted(set(uses + _unordered_sets(tree)))


def check_plugin_source(source: str, expected_name: str, imported: bool = False) -> dict:
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
            elif any(a.name in BANNED_ATTRS for a in node.names):  # from dataclasses import builtins, sys
                problems.append(f"import of {sorted(a.name for a in node.names if a.name in BANNED_ATTRS)} from "
                                f"{mod!r} not allowed")
        elif isinstance(node, ast.Call) and (
                (isinstance(node.func, ast.Name) and node.func.id == "FeatureContext")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "FeatureContext")):
            problems.append("constructing a FeatureContext is not allowed (use the ctx you are given)")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            problems.append(f"use of {node.id!r} not allowed")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRS:
            problems.append(f"access to .{node.attr} not allowed")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            problems.append("global/nonlocal statements not allowed")
    # a past run's plugin that a warm start imports may still use id(): in the models the lab has reported, every
    # use is a cache key into a per-context dict or a count of distinct objects, which changes no value (the scan
    # of all runs' feature stores, docs/LAB_STATE.md); hash(), .__hash__ and a set of objects whose order is used
    # are refused there too, as they put process noise into the values
    noise = process_dependent_uses(tree, ("hash",) if imported else PROCESS_BUILTINS)
    if noise:
        problems.append(f"{', '.join(noise)} not allowed: {PROCESS_NOISE}")
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
