"""Launch the fixed diagnostic with a parent-enforced 7,200 second deadline."""
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
    command = [sys.executable, str(repo / "tools/b1_two_member_test.py"),
               "--package", str(package), "--manifest-sha256",
               "225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45",
               "--out", str(out)]
    try:
        return subprocess.run(command, cwd=repo, timeout=7200, check=False).returncode
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for the child before raising. Retain
        # its last completed fold/summary even if a native operation blocked
        # Python's internal timer. Partial arrays may not have reached disk.
        out.mkdir(parents=True, exist_ok=True)
        def checkpoint(path):
            if not path.exists():
                return {}
            try:
                value = json.loads(path.read_text())
                if not isinstance(value, dict):
                    raise ValueError("checkpoint is not an object")
                return value
            except (ValueError, UnicodeError):
                path.rename(path.with_name(path.stem + ".interrupted.json"))
                return {}

        error = {"type": "ParentDeadline", "message": "7200 second process deadline"}
        baseline_path = out / "summary.json"
        baseline = checkpoint(baseline_path)
        if baseline.get("status") != "complete":
            baseline.update({"status": "timed_out", "error": error,
                             "partial_arrays_may_be_missing": True})
            baseline_path.write_text(json.dumps(baseline, indent=2, allow_nan=False) + "\n")
        comparison_path = out / "comparison.json"
        comparison = checkpoint(comparison_path)
        comparison.update({"status": "timed_out", "decision": "no promotion; B1 unchanged",
                           "error": error, "partial_arrays_may_be_missing": True})
        comparison_path.write_text(json.dumps(comparison, indent=2, allow_nan=False) + "\n")
        return 124


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(launch(args.package.resolve(), args.out.resolve()))
