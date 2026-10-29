Astra — GEARS seed 3: full prescribed score report and JSON (one bridge invocation, exit 0). Predictions cover 38 held-out identities; the oracle's paired sealed comparison uses n=21. Same fixed CPU settings and disclosed corrected-export cohort caveat; this worn-cohort result is descriptive. Raw outputs below are unchanged.

# gears_s3 on Gene-Mila's split, scored once on the sealed set

Bundle `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf`; predictions `/Users/andresarriaga/gears_adamson_s3/predictions.npz` (sha256 `aea8a91e73cef518abaa61f493c3b6361971c5599f23dde8ab4ca48d663a648f`).

| metric | gears_s3 |
|---|---:|
| pearson_delta | 0.4202 |
| mse | 0.0082 |
| pearson_delta_top | 0.5230 |
| r2_top | 0.7860 |
| cellforge_mse_de | 0.1316 |
| cellforge_pcc_de | 0.9289 |
| cellforge_r2_de | 0.7579 |

Paired against `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0` EXP_0441 (gears_s3 minus the lab's model, pearson_delta per sealed perturbation): {"n": 21, "mean_diff": -0.1784380603792845, "se": 0.041418618055280534, "wins_a": 1, "wins_b": 20, "ties": 0, "verdict": "b"}


Full-precision JSON:
```json
{
 "bundle": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
 "predictions": "/Users/andresarriaga/gears_adamson_s3/predictions.npz",
 "predictions_sha256": "aea8a91e73cef518abaa61f493c3b6361971c5599f23dde8ab4ca48d663a648f",
 "model": "gears_s3",
 "cellforge": {
  "experiment_id": "gears_s3",
  "metrics": {
   "rmse": 0.09081984797664486,
   "mae": 0.06459954363521149,
   "mse": 0.008248244786500882,
   "pearson_delta": 0.4202269780308886,
   "pearson_delta_top": 0.5229584787799723,
   "direction_acc_top": 0.8738095238095239,
   "mse_top": 0.14027070882178333,
   "r2_top": 0.7859622067053383,
   "pearson_expr": 0.9817064154078411,
   "primary": 0.4202269780308886,
   "selection_rule": "pearson_delta",
   "cellforge_mse": 0.00824824478650088,
   "cellforge_pcc": 0.9817064154078413,
   "cellforge_r2": 0.9606616587632182,
   "cellforge_mse_de": 0.13163606651835483,
   "cellforge_pcc_de": 0.9289477209455959,
   "cellforge_r2_de": 0.7579312303401234,
   "cellforge_mse_deset": 0.13056781374923435,
   "cellforge_pcc_deset": 0.8812622678736733,
   "cellforge_r2_deset": 0.63605347604364,
   "cellforge_n_perts_deset": 19,
   "vcworld_de_accuracy": 0.7230216660873595,
   "vcworld_de_precision": 0.30910439458557387,
   "vcworld_de_recall": 0.42552648372686663,
   "vcworld_de_f1": 0.3580903281241609,
   "vcworld_de_auroc": 0.6483923916334997,
   "vcworld_de_auprc": 0.3109276481661257,
   "vcworld_dir_accuracy": 0.8781110402042118,
   "vcworld_dir_precision": 0.6872659176029963,
   "vcworld_dir_recall": 0.8364672364672364,
   "vcworld_dir_f1": 0.754561809303521,
   "vcworld_dir_auroc": 0.9287557167491377,
   "vcworld_dir_auprc": 0.8418410509327788,
   "vcworld_n_de_pairs": 7835
  }
 },
 "versus": {
  "run": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
  "experiment_id": "EXP_0441",
  "paired": {
   "experiments": [
    "gears_s3",
    "EXP_0441"
   ],
   "metric": "pearson_delta",
   "a": {
    "experiment_id": "gears_s3",
    "metrics": {
     "rmse": 0.09081984797664486,
     "mae": 0.06459954363521149,
     "mse": 0.008248244786500882,
     "pearson_delta": 0.4202269780308886,
     "pearson_delta_top": 0.5229584787799723,
     "direction_acc_top": 0.8738095238095239,
     "mse_top": 0.14027070882178333,
     "r2_top": 0.7859622067053383,
     "pearson_expr": 0.9817064154078411,
     "primary": 0.4202269780308886,
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
    "mean_diff": -0.1784380603792845,
    "se": 0.041418618055280534,
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
  "start_utc": "2026-10-29T03:09:08.560558+00:00",
  "seed": 3,
  "command": [
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python",
    "tools/cellforge_bridge.py",
    "score",
    "--bundle",
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
    "--pred",
    "/Users/andresarriaga/gears_adamson_s3/predictions.npz",
    "--name",
    "gears_s3",
    "--versus",
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
    "--out",
    "docs/results/gears_adamson_s3.md"
  ],
  "cwd": "/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-gears-baselines",
  "source_commit": "37d991d94b414ca8f8475b066bad5ec4451acc9f",
  "nice": 19,
  "credential_policy": "API keys unset; free oracle scoring",
  "child_pid": 74249,
  "end_utc": "2026-10-29T03:09:09.726300+00:00",
  "exit": 0,
  "wall_seconds": 1.1656563328579068,
  "cpu_seconds": 1.157203
}

```