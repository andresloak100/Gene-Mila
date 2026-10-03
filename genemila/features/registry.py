"""Feature discovery and loading (runs inside experiment subprocesses)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from . import builtin  # noqa: F401  (registers baseline features)
from .api import REGISTRY, Feature

BUILTIN_FEATURES = ["control_mean", "mean_response", "is_target"]


def load_plugins(plugin_dir: str | Path) -> list[str]:
    """Import every plugin module in plugin_dir; return names it registered."""
    loaded = []
    for path in sorted(Path(plugin_dir).glob("*.py")):
        if path.name.startswith("_"):
            continue
        before = set(REGISTRY)
        mod_name = f"genemila_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        loaded.extend(sorted(set(REGISTRY) - before))
    return loaded


def get(name: str) -> type[Feature]:
    if name not in REGISTRY:
        raise KeyError(f"unknown feature {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name]
