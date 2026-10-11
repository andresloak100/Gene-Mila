"""Feature discovery and loading (runs inside experiment subprocesses)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from . import builtin  # noqa: F401  (registers baseline features)
from .api import REGISTRY, Feature

BUILTIN_FEATURES = ["control_mean", "mean_response", "is_target"]
_LOADED: dict[str, Path] = {}  # module name -> plugin file, for reloads


def _exec(path: Path) -> set[str]:
    before = set(REGISTRY)
    mod_name = f"genemila_plugin_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)  # a registered class replaces the previous one of the same name
    _LOADED[mod_name] = path
    return set(REGISTRY) - before


def load_plugins(plugin_dir: str | Path) -> list[str]:
    """Import every plugin module in plugin_dir; return names it registered."""
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
    for path in list(_LOADED.values()):
        if path.exists():
            _exec(path)


def get(name: str) -> type[Feature]:
    if name not in REGISTRY:
        raise KeyError(f"unknown feature {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name]
