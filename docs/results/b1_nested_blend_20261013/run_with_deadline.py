"""One fixed nested-calibration run with a parent-enforced 7,200s deadline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def launch(package: Path, out: Path) -> int:
    repo = Path(__file__).resolve().parents[3]
    if out.exists():
        raise FileExistsError(f"refusing to reuse run directory: {out}")
    command = [sys.executable, str(repo / "tools/b1_nested_blend.py"),
               "--package", str(package), "--manifest-sha256",
               "225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45",
               "--out", str(out)]
    try:
        return subprocess.run(command, cwd=repo, timeout=7200, check=False).returncode
    except subprocess.TimeoutExpired:
        # subprocess.run has killed and waited for the child. Preserve the
        # last checkpoint fields; partial prediction arrays may be absent.
        out.mkdir(parents=True, exist_ok=True)
        path = out / "summary.json"
        summary = {}
        if path.exists():
            try:
                summary = json.loads(path.read_text())
                if not isinstance(summary, dict):
                    raise ValueError("checkpoint is not an object")
            except (ValueError, UnicodeError):
                path.rename(out / "summary.interrupted.json")
                summary = {}
        summary.update({"status": "timed_out", "decision": "no promotion; original B1 unchanged",
                        "error": {"type": "ParentDeadline", "message": "7200 second process deadline"},
                        "partial_arrays_may_be_missing": True})
        path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        return 124


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(launch(args.package.resolve(), args.out.resolve()))
