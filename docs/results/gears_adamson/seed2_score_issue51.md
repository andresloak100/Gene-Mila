Astra — GEARS seed 2: full prescribed score report and JSON (one bridge invocation, exit 0). Predictions cover 38 held-out identities; the oracle's paired sealed comparison uses n=21. Same fixed CPU settings and disclosed corrected-export cohort caveat; this worn-cohort result is descriptive. Raw outputs below are unchanged.

# gears_s2 on Gene-Mila's split, scored once on the sealed set

Bundle `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf`; predictions `/Users/andresarriaga/gears_adamson_s2/predictions.npz` (sha256 `e0bae73fbfff0cfb6420879d7b65bdfe298c130d0635312540976c16db884632`).

| metric | gears_s2 |
|---|---:|
| pearson_delta | 0.4040 |
| mse | 0.0094 |
| pearson_delta_top | 0.5068 |
| r2_top | 0.7860 |
| cellforge_mse_de | 0.1301 |
| cellforge_pcc_de | 0.9272 |
| cellforge_r2_de | 0.7524 |

Paired against `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0` EXP_0441 (gears_s2 minus the lab's model, pearson_delta per sealed perturbation): {"n": 21, "mean_diff": -0.19468852456683816, "se": 0.041440529101269795, "wins_a": 2, "wins_b": 19, "ties": 0, "verdict": "b"}


Full-precision JSON:
```json
{
 "bundle": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
 "predictions": "/Users/andresarriaga/gears_adamson_s2/predictions.npz",
 "predictions_sha256": "e0bae73fbfff0cfb6420879d7b65bdfe298c130d0635312540976c16db884632",
 "model": "gears_s2",
 "cellforge": {
  "experiment_id": "gears_s2",
  "metrics": {
   "rmse": 0.09671474189892776,
   "mae": 0.07011630713606519,
   "mse": 0.009353741300576212,
   "pearson_delta": 0.4039765138433349,
   "pearson_delta_top": 0.506803796511664,
   "direction_acc_top": 0.8285714285714285,
   "mse_top": 0.13651371819312608,
   "r2_top": 0.785981153140058,
   "pearson_expr": 0.9793480791835523,
   "primary": 0.4039765138433349,
   "selection_rule": "pearson_delta",
   "cellforge_mse": 0.009353741300576214,
   "cellforge_pcc": 0.979348079183552,
   "cellforge_r2": 0.9553530953445049,
   "cellforge_mse_de": 0.13012799370241362,
   "cellforge_pcc_de": 0.927215446796463,
   "cellforge_r2_de": 0.7523516475066412,
   "cellforge_mse_deset": 0.12930729530760396,
   "cellforge_pcc_deset": 0.8853356937785705,
   "cellforge_r2_deset": 0.632398530183094,
   "cellforge_n_perts_deset": 19,
   "vcworld_de_accuracy": 0.697161394971614,
   "vcworld_de_precision": 0.2892914653784219,
   "vcworld_de_recall": 0.4585832801531589,
   "vcworld_de_f1": 0.35477659837077263,
   "vcworld_de_auroc": 0.6391077980805991,
   "vcworld_de_auprc": 0.3143208717047397,
   "vcworld_dir_accuracy": 0.848627951499681,
   "vcworld_dir_precision": 0.6187891440501044,
   "vcworld_dir_recall": 0.8444444444444444,
   "vcworld_dir_f1": 0.7142168674698796,
   "vcworld_dir_auroc": 0.918225371120108,
   "vcworld_dir_auprc": 0.8229247481806925,
   "vcworld_n_de_pairs": 7835
  }
 },
 "versus": {
  "run": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
  "experiment_id": "EXP_0441",
  "paired": {
   "experiments": [
    "gears_s2",
    "EXP_0441"
   ],
   "metric": "pearson_delta",
   "a": {
    "experiment_id": "gears_s2",
    "metrics": {
     "rmse": 0.09671474189892776,
     "mae": 0.07011630713606519,
     "mse": 0.009353741300576212,
     "pearson_delta": 0.4039765138433349,
     "pearson_delta_top": 0.506803796511664,
     "direction_acc_top": 0.8285714285714285,
     "mse_top": 0.13651371819312608,
     "r2_top": 0.785981153140058,
     "pearson_expr": 0.9793480791835523,
     "primary": 0.4039765138433349,
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
    "mean_diff": -0.19468852456683816,
    "se": 0.041440529101269795,
    "wins_a": 2,
    "wins_b": 19,
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
  "start_utc": "2026-10-29T03:09:07.367785+00:00",
  "seed": 2,
  "command": [
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python",
    "tools/cellforge_bridge.py",
    "score",
    "--bundle",
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
    "--pred",
    "/Users/andresarriaga/gears_adamson_s2/predictions.npz",
    "--name",
    "gears_s2",
    "--versus",
    "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
    "--out",
    "docs/results/gears_adamson_s2.md"
  ],
  "cwd": "/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-gears-baselines",
  "source_commit": "37d991d94b414ca8f8475b066bad5ec4451acc9f",
  "nice": 19,
  "credential_policy": "API keys unset; free oracle scoring",
  "child_pid": 74242,
  "end_utc": "2026-10-29T03:09:08.559779+00:00",
  "exit": 0,
  "wall_seconds": 1.191913875285536,
  "cpu_seconds": 1.1771380000000002
}

```