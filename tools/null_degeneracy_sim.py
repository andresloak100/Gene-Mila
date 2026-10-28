#!/usr/bin/env python3
"""Simulation for the methods note (docs/NOTE_DEGENERATE_NULL.md): a gene-permutation null cannot reject a feature
that is an existing prediction times one number per perturbation, while a perturbation null can.

Each replicate writes one plugin whose feature is mean_response (a parent column of the fixed model) times a
pseudo-random scalar per perturbation, drawn from the perturbation's name and the replicate's seed only: it reads no
label beyond what mean_response already uses and carries no information about the response, so every pass is a false
positive. tools/feature_compare.py scores it out of fold against both nulls; the raw p of each null is recorded. The
false-positive rate at 0.05 is the share of replicates whose p is at most 0.05, with a 95 percent Wilson interval.

    python tools/null_degeneracy_sim.py --reps 40 --null-reps 199 --out docs/results/null_degeneracy_sim
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

PLUGIN = '''"""Null feature for the degenerate-null simulation: mean_response times a pseudo-random scalar per perturbation
(seed {seed}); it carries no information about the response."""
from __future__ import annotations

import zlib

import numpy as np

from genemila.features.api import Feature, FeatureContext, register


@register
class RandomScale{seed}(Feature):
    name = "random_scale_s{seed}"
    description = "mean_response times a pseudo-random number per perturbation (simulation null, seed {seed})"
    rationale = "none: a null feature for the simulation"
    inputs = ["train_delta"]
    dependencies = ["mean_response"]

    def compute(self, ctx: FeatureContext, perts, params):
        base = ctx.feature("mean_response", perts)
        c = np.array([((zlib.crc32((p + ":{seed}").encode()) % 10007) / 10007.0) * 2.0 - 1.0 for p in perts])
        return base * c[:, None, None]
'''


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def run(reps: int, null_reps: int, out: Path, data: Path | None = None) -> dict:
    import feature_compare as fc
    from genemila.data.synthetic import generate
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="nulldeg-"))
    try:
        bundle = Path(data) if data else generate(work / "bundle", n_genes=120, n_perts=30, n_control=600,
                                                   cells_per_pert=40, seed=1)
        rows = []
        for s in range(reps):
            src = work / f"src{s}"
            src.mkdir()
            (src / f"random_scale_s{s}.py").write_text(PLUGIN.format(seed=s))
            res_dir = work / f"out{s}"
            rc = fc.main(["--data", str(bundle), "--out", str(res_dir), "--source", f"SIM={src}",
                          "--fold-seeds", "101,102", "--null-reps", str(null_reps)])
            rep = json.loads((res_dir / "feature_compare.json").read_text())
            row = next(r for r in rep["rows"] if r["source"] == "SIM" and r["feature"] != "(set)")
            oof = row["tiers"]["oof"]
            rows.append({"seed": s, "rc": rc, "status": row["status"], "proportional": row.get("proportional"),
                         "gain": oof["delta"]["pearson_delta"]["mean_diff"] if oof.get("delta") else None,
                         "p_gene": (oof.get("null") or {}).get("p"),
                         "p_pert": (oof.get("null_pert") or {}).get("p")})
        ok = [r for r in rows if r["status"] == "ok" and r["p_gene"] is not None]
        k_gene = sum(1 for r in ok if r["p_gene"] <= 0.05)
        pert = [r for r in ok if r["p_pert"] is not None]
        k_pert = sum(1 for r in pert if r["p_pert"] <= 0.05)
        summary = {"reps": reps, "null_reps": null_reps, "scored": len(ok), "proportional": sum(bool(r["proportional"]) for r in ok),
                   "false_positive_gene_null": k_gene / max(1, len(ok)), "ci_gene_null": wilson(k_gene, len(ok)),
                   "false_positive_pert_null": k_pert / max(1, len(pert)), "ci_pert_null": wilson(k_pert, len(pert)),
                   "positive_gain_share": sum(1 for r in ok if (r["gain"] or 0) > 0) / max(1, len(ok)),
                   "bundle": "synthetic generate(n_genes=120, n_perts=30, seed=1)" if not data else str(data),
                   "rows": rows}
        (out / "summary.json").write_text(json.dumps(summary, indent=1))
        (out / "summary.md").write_text(
            f"# Degenerate-null simulation\n\n{len(ok)} null features (mean_response times a random per-perturbation "
            f"scalar), {null_reps} null replicates each.\n\n| null | false-positive rate at 0.05 | 95% CI |\n|---|---:|---|\n"
            f"| gene permutation | {summary['false_positive_gene_null']:.2f} | {summary['ci_gene_null'][0]:.2f}–"
            f"{summary['ci_gene_null'][1]:.2f} |\n| perturbation permutation | {summary['false_positive_pert_null']:.2f} | "
            f"{summary['ci_pert_null'][0]:.2f}–{summary['ci_pert_null'][1]:.2f} |\n\nShare with a positive out-of-fold "
            f"gain: {summary['positive_gain_share']:.2f}.\n")
        return summary
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--null-reps", type=int, default=199)
    ap.add_argument("--data", default=None, help="a bundle (default: a synthetic one built here)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    s = run(a.reps, a.null_reps, Path(a.out), Path(a.data) if a.data else None)
    print(json.dumps({k: v for k, v in s.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
