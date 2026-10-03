#!/usr/bin/env python3
"""Re-run a completed experiment from its recorded code commit, data split,
feature configuration, model, hyperparameters and seed, and compare scores.

    python reproduce.py --experiment EXP_0037 [--run DIR]
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from genemila.cli_common import add_run_arg, resolve_run
from genemila.isolation import git
from genemila.sandbox import run_limited
from genemila.spec import PLUGIN_DIR, ExperimentSpec


def reproduce(lab, experiment_id: str, tol: float = 1e-6) -> dict:
    rec = lab.db.get_experiment(experiment_id)
    if rec is None or rec["status"] != "completed":
        raise SystemExit(f"{experiment_id} is not a completed experiment")
    if rec["split_id"] != lab.split_id:
        raise SystemExit(f"split mismatch: experiment used {rec['split_id']}, dataset now {lab.split_id}")
    if not rec.get("artifact_dir"):
        return {"experiment_id": experiment_id, "reproducible": True, "note": "analytic baseline (no code)"}
    spec = ExperimentSpec.from_record(rec)
    ref = f"refs/genemila/{lab.run_id}/{experiment_id}"
    commit = git(lab.repo, "rev-parse", ref)
    assert commit == rec["code_commit"], "pinned ref does not match recorded commit"
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "wt"
        git(lab.repo, "worktree", "add", "--detach", str(wt), commit)
        try:
            out = Path(tmp) / "out"
            out.mkdir()
            (out / "run_spec.json").write_text(json.dumps(spec.run_spec()))
            proc = run_limited([sys.executable, "-m", "genemila.pipeline", "run", "--spec", str(out / "run_spec.json"),
                                "--public", str(lab.public_dir), "--plugins", str(wt / PLUGIN_DIR), "--out", str(out)],
                               cwd=wt, log_dir=out, timeout_s=spec.timeout_s, ram_mb=spec.ram_limit_mb,
                               env={"PYTHONPATH": str(wt)}, name="reproduce")
            if proc.returncode != 0:
                raise SystemExit(f"reproduction failed: {proc.stderr_tail[-800:]}")
            ev = lab.evaluate_artifact(out / "predictions.npz")
        finally:
            git(lab.repo, "worktree", "remove", "--force", str(wt), check=False)
    score = ev["metrics"]["primary"]
    return {"experiment_id": experiment_id, "commit": commit, "dataset": rec["dataset"], "split_id": rec["split_id"],
            "features": spec.feature_set, "model": spec.model_type, "hyperparameters": spec.hyperparameters,
            "seed": spec.seed, "recorded_score": rec["primary_score"], "reproduced_score": score,
            "reproducible": abs(score - rec["primary_score"]) <= tol}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_run_arg(ap)
    ap.add_argument("--experiment", required=True)
    args = ap.parse_args()
    r = reproduce(resolve_run(args), args.experiment)
    print(json.dumps(r, indent=1))
    sys.exit(0 if r["reproducible"] else 1)


if __name__ == "__main__":
    main()
