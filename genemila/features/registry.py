"""Feature discovery and loading (runs inside experiment subprocesses)."""

from __future__ import annotations

import importlib.util
import hashlib
import inspect
import json
import sys
from pathlib import Path

from . import builtin  # noqa: F401  (registers baseline features)
from .api import REGISTRY, Feature

BUILTIN_FEATURES = ["control_mean", "mean_response", "is_target"]
_LOADED: dict[str, Path] = {}  # module name -> plugin file, for reloads
_PLUGIN_FEATURES: dict[str, set[str]] = {}
_BUILTIN_REGISTRY = dict(REGISTRY)


class FeatureDependencyError(ValueError):
    """A selected feature cannot be reproduced from the available sources."""


def _exec(path: Path) -> set[str]:
    before = dict(REGISTRY)
    mod_name = f"genemila_plugin_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    # Read the current source, bypassing timestamp/size-based .pyc reuse after an edit.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    _LOADED[mod_name] = path
    names = {name for name, cls in REGISTRY.items() if before.get(name) is not cls}
    _PLUGIN_FEATURES[mod_name] = names
    return names


def load_plugins(plugin_dir: str | Path) -> list[str]:
    """Replace the previous plugin source set with this directory's available sources.

    Available sources include dependencies that need not be selected model columns.
    A source from an earlier experiment must never satisfy a missing dependency.
    """
    for mod_name in list(_LOADED):
        _unload(mod_name)
    loaded = []
    for path in sorted(Path(plugin_dir).glob("*.py")):
        if path.name.startswith("_"):
            continue
        loaded.extend(sorted(_exec(path)))
    return loaded


def reload_plugins() -> None:
    """Re-execute every loaded plugin module, so module-level state (memo dicts, class attributes, default
    arguments) starts fresh. Used between computations that must not share state: the smoke test's
    determinism and leakage checks, and each cross-validation fold."""
    for mod_name, path in list(_LOADED.items()):
        _unload(mod_name)
        if path.exists():
            _exec(path)


def _unload(mod_name: str) -> None:
    for name in _PLUGIN_FEATURES.pop(mod_name, set()):
        cls = REGISTRY.get(name)
        if cls is not None and cls.__module__ == mod_name:
            REGISTRY.pop(name)
            if name in _BUILTIN_REGISTRY:
                REGISTRY[name] = _BUILTIN_REGISTRY[name]
    _LOADED.pop(mod_name, None)
    sys.modules.pop(mod_name, None)


def get(name: str) -> type[Feature]:
    if name not in REGISTRY:
        raise KeyError(f"unknown feature {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name]


def dependency_closure(names: list[str], metadata: dict[str, dict] | None = None) -> list[str]:
    """Required sources in dependency-first order, without adding predictor columns.

    The controller can resolve stored metadata without importing agent-written code.
    Experiment processes omit metadata and inspect their loaded feature classes.
    """
    ordered: list[str] = []
    done: set[str] = set()
    visiting: list[str] = []

    def visit(name: str) -> None:
        if name in visiting:
            chain = " -> ".join(visiting + [name])
            raise FeatureDependencyError(f"feature dependency cycle: {chain}")
        if name in done:
            return
        available = REGISTRY if metadata is None else metadata
        if name not in available:
            chain = " -> ".join(visiting + [name])
            raise FeatureDependencyError(f"missing feature source {name!r} (dependency chain: {chain})")
        dependencies = REGISTRY[name].dependencies if metadata is None else metadata[name].get("dependencies", [])
        if not isinstance(dependencies, (list, tuple)) or any(not isinstance(d, str) for d in dependencies):
            raise FeatureDependencyError(f"feature {name!r} dependencies must be a list of feature names")
        visiting.append(name)
        for dependency in sorted(set(dependencies)):
            visit(dependency)
        visiting.pop()
        done.add(name)
        ordered.append(name)

    for name in names:
        visit(name)
    return ordered


def dependency_fingerprint(name: str, feature_params: dict | None = None,
                           params: dict | None = None) -> str:
    """Hash current sources, versions, edges and effective params for the entire closure.

    Missing declared sources are an error even when a previously computed block exists.
    Source hashes are read afresh so reloading a changed file invalidates warm caches.
    """
    configured = feature_params or {}
    entries = []
    for dependency in dependency_closure([name]):
        cls = get(dependency)
        path = inspect.getsourcefile(cls)
        if path is None or not Path(path).is_file():
            raise FeatureDependencyError(f"source file unavailable for feature {dependency!r}: {path!r}")
        effective = {**cls.params, **configured.get(dependency, {})}
        if dependency == name and params is not None:
            effective.update(params)
        entries.append({"name": dependency, "version": cls.version,
                        "source": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                        "params": effective, "dependencies": sorted(set(cls.dependencies))})
    payload = json.dumps(entries, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()
