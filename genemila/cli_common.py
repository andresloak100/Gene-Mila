"""Helpers shared by the command-line entry points."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import REPO_ROOT
from .lab import Lab, latest_run, open_run


def add_run_arg(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--run", help="run directory (default: most recent under runs/)")


def resolve_run(args) -> Lab:
    return open_run(Path(args.run) if args.run else latest_run(REPO_ROOT / "runs"))
