Astra — GEARS seed 0: full prescribed score report and JSON (one bridge invocation, exit 0). Predictions cover 38 held-out identities; the oracle's paired sealed comparison uses n=21. Same fixed CPU settings and disclosed corrected-export cohort caveat; this worn-cohort result is descriptive. Raw outputs below are unchanged.

# gears_s0 on Gene-Mila's split, scored once on the sealed set

Bundle `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf`; predictions `/Users/andresarriaga/gears_adamson_s0/predictions.npz` (sha256 `780b0239464f7ea84e2a43d97f774eaad58e99ef49cfec3e0f4cd956ca62f3ee`).

| metric | gears_s0 |
|---|---:|
| pearson_delta | 0.3976 |
| mse | 0.0086 |
| pearson_delta_top | 0.5103 |
| r2_top | 0.7747 |
| cellforge_mse_de | 0.1372 |
| cellforge_pcc_de | 0.9269 |
| cellforge_r2_de | 0.7442 |

Paired against `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0` EXP_0441 (gears_s0 minus the lab's model, pearson_delta per sealed perturbation): {"n": 21, "mean_diff": -0.2010199096055358, "se": 0.040661401648259925, "wins_a": 1, "wins_b": 20, "ties": 0, "verdict": "b"}


Full-precision JSON:
```json
{
 "bundle": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
 "predictions": "/Users/andresarriaga/gears_adamson_s0/predictions.npz",
 "predictions_sha256": "780b0239464f7ea84e2a43d97f774eaad58e99ef49cfec3e0f4cd956ca62f3ee",
 "model": "gears_s0",
 "cellforge": {
  "experiment_id": "gears_s0",
  "metrics": {
   "rmse": 0.09266945915592383,
   "mae": 0.06507699804779048,
   "mse": 0.008587628660251433,
   "pearson_delta": 0.39764512880463726,
   "pearson_delta_top": 0.5102653381115134,
   "direction_acc_top": 0.838095238095238,
   "mse_top": 0.14682282742151567,
   "r2_top": 0.7747248250127734,
   "pearson_expr": 0.9811682558818365,
   "primary": 0.39764512880463726,
   "selection_rule": "pearson_delta",
   "cellforge_mse": 0.008587628660251433,
   "cellforge_pcc": 0.9811682558818366,
   "cellforge_r2": 0.9590623274749761,
   "cellforge_mse_de": 0.13723175862028733,
   "cellforge_pcc_de": 0.9268996207801927,
   "cellforge_r2_de": 0.744216814528525,
   "cellforge_mse_deset": 0.13105751395839235,
   "cellforge_pcc_deset": 0.8766976399636964,
   "cellforge_r2_deset": 0.6326428209765399,
   "cellforge_n_perts_deset": 19,
   "vcworld_de_accuracy": 0.7467964314679643,
   "vcworld_de_precision": 0.32069125492925077,
   "vcworld_de_recall": 0.35290363752393106,
   "vcworld_de_f1": 0.3360272224585283,
   "vcworld_de_auroc": 0.6324743669150175,
   "vcworld_de_auprc": 0.30469264464374335,
   "vcworld_dir_accuracy": 0.8481174218251436,
   "vcworld_dir_precision": 0.6207781103035486,
   "vcworld_dir_recall": 0.8273504273504273,
   "vcworld_dir_f1": 0.7093307278944798,
   "vcworld_dir_auroc": 0.9081804805817965,
   "vcworld_dir_auprc": 0.7945475044523423,
   "vcworld_n_de_pairs": 7835
  }
 },
 "versus": {
  "run": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
  "experiment_id": "EXP_0441",
  "paired": {
   "experiments": [
    "gears_s0",
    "EXP_0441"
   ],
   "metric": "pearson_delta",
   "a": {
    "experiment_id": "gears_s0",
    "metrics": {
     "rmse": 0.09266945915592383,
     "mae": 0.06507699804779048,
     "mse": 0.008587628660251433,
     "pearson_delta": 0.39764512880463726,
     "pearson_delta_top": 0.5102653381115134,
     "direction_acc_top": 0.838095238095238,
     "mse_top": 0.14682282742151567,
     "r2_top": 0.7747248250127734,
     "pearson_expr": 0.9811682558818365,
     "primary": 0.39764512880463726,
     "selection_rule": "pearson_delta"
    }
   },
   "b": {
    "experiment_id": "EXP_0441",
    "metrics": {
     "rmse": 0.07941805961997553,
     "mae": 0.05133823741220218,
     "mse": 0.006307228193801987,
     "pearson_delta": 0.598665038410173,
     "pearson_delta_top": 0.7447539694476231,
     "direction_acc_top": 0.9190476190476189,
     "mse_top": 0.1251129661213442,
     "r2_top": 0.817816421004432,
     "pearson_expr": 0.9863005621191437,
     "primary": 0.598665038410173,
     "selection_rule": "pearson_delta"
    }
   },
   "paired": {
    "n": 21,
    "mean_diff": -0.2010199096055358,
    "se": 0.040661401648259925,
    "wins_a": 1,
    "wins_b": 20,
    "ties": 0,
    "verdict": "b"
   }
  }
 }
}
```

Exclusive score/runtime receipt:
```json
{
  "start_utc": "2026-10-29T03:09:04.856667+00:00",
  "seed": 0,
  "command": [
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python",
    "tools/cellforge_bridge.py",
    "score",
    "--bundle",
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
    "--pred",
    "/Users/andresarriaga/gears_adamson_s0/predictions.npz",
    "--name",
    "gears_s0",
    "--versus",
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
    "--out",
    "docs/results/gears_adamson_s0.md"
  ],
  "cwd": "/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-gears-baselines",
  "source_commit": "37d991d94b414ca8f8475b066bad5ec4451acc9f",
  "nice": 19,
  "credential_policy": "API keys unset; free oracle scoring",
  "child_pid": 74235,
  "end_utc": "2026-10-29T03:09:07.366893+00:00",
  "exit": 0,
  "wall_seconds": 2.510111624840647,
  "cpu_seconds": 1.345298
}

```