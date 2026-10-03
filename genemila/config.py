"""Configuration loading. Configs are TOML files merged over configs/default.toml."""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

from . import REPO_ROOT

DEFAULT_CONFIG = REPO_ROOT / "configs" / "default.toml"


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> dict[str, Any]:
    with open(DEFAULT_CONFIG, "rb") as fh:
        cfg = tomllib.load(fh)
    if path:
        with open(path, "rb") as fh:
            cfg = _merge(cfg, tomllib.load(fh))
    if overrides:
        cfg = _merge(cfg, overrides)
    return cfg


def set_dotted(cfg: dict, dotted: str, value: Any) -> None:
    """Set cfg['a']['b'] for dotted='a.b'."""
    keys = dotted.split(".")
    node = cfg
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = value
