Astra — linear AE baseline complete: exactly one unchanged runner and one prescribed bridge invocation, all exits0 and all15prediction checksPASS. Full report, JSON and operator receipt below. FixedK10/lambda0.1, deterministic one run; no paid call. User-approved export path and SHA match GEARS, empty export unchanged. Publishing after all publication checks; C2→H follows.

# linear_ae on Gene-Mila's split, scored once on the sealed set

Bundle `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf`; predictions `/Users/andresarriaga/linear_ae_adamson/predictions.npz` (sha256 `52118b47e9455dcfde4757d8043837cb96bcc2c6901149091fdf4e93a0e9b9ee`).

| metric | linear_ae |
|---|---:|
| pearson_delta | 0.4854 |
| mse | 0.0071 |
| pearson_delta_top | 0.5484 |
| r2_top | 0.7230 |
| cellforge_mse_de | 0.1632 |
| cellforge_pcc_de | 0.9199 |
| cellforge_r2_de | 0.7106 |

Paired against `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0` EXP_0441 (linear_ae minus the lab's model, pearson_delta per sealed perturbation): {"n": 21, "mean_diff": -0.1132228613733192, "se": 0.0430444692533904, "wins_a": 9, "wins_b": 12, "ties": 0, "verdict": "b"}

## Input provenance and run receipt

Andres explicitly selected the same corrected export used by GEARS. **Export folder:** `/Users/andresarriaga/cellforge_adamson_export_corrected_20261028`. **Input file:** `/Users/andresarriaga/cellforge_adamson_export_corrected_20261028/cellforge_input.h5ad`. **Input SHA-256:** `ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a`. These are also recorded in the [operator receipt](linear_ae_adamson/receipt.json); the unchanged runner receipt is [retained separately](linear_ae_adamson/runner_receipt.raw.json). The preserved empty export `~/cellforge_adamson_export` was not modified.

The input contains 40,890 cells: 9,065 controls and 31,825 training cells, with all 50 training perturbations, 2,055 genes and no held-out cells. It has the same bytes as GEARS’s input. Relative to the lab bundle’s original single-source ingest, the approved three-source export adds 1,770 controls and 10 training cells. Thus this is an identical-input comparison with GEARS, while the training cell cohort differs from the lab bundle’s original cohort.

## Fixed model and outcome

One deterministic CPU run, default K=10 and ridge lambda=0.1, at nice 19. The runner and scientific source were unchanged. All 50 training perturbations were used; training targets without an embedding: **0** (none). Held-out predictions using the mean-training-response fallback: **0/38** (none). The generic fallback is the equally weighted mean of training-condition means; it was not needed here.

Predictions have 38 rows × 2,055 genes and passed all 15 shape, identity/order, finiteness, settings and hash checks. The sealed oracle’s paired comparison uses **21** conditions. One bridge invocation ran after validation; it internally performs one standalone and two paired scorings. There was no second invocation, tuning, repeat-seed estimate or seed SD.

The selected comparator is `newcode_opus_w4_r0:EXP_0441`. Its pearson_delta is **0.598665038410**, versus **0.485442177037** for linear AE. The lab’s gain 0.113222861373 exceeds twice the paired SE 0.086088938507, and the lab wins 12/21 conditions (linear AE wins 9). The fixed rule therefore favors the lab run. This is descriptive evidence on the worn sealed cohort, not fresh-test confirmation or a basis for parameter selection.

For context, [GEARS’s previously published three-seed reading](gears_adamson/aggregate.md) on the same corrected export was 0.4073 ± sample SD 0.0116. The linear baseline’s single fixed result is reported beside it; these receipts provide no new paired AE-versus-GEARS test.

## Full precision metrics

The unchanged [JSON report](linear_ae_adamson.json) is authoritative; this table includes metrics omitted by the bridge’s short Markdown rendering.

| Metric | Linear AE |
|---|---:|
| rmse | 0.08426801896887254 |
| mae | 0.05461245870766842 |
| mse | 0.007101099020938262 |
| pearson_delta | 0.4854421770368539 |
| pearson_delta_top | 0.5483655427038636 |
| direction_acc_top | 0.8595238095238096 |
| mse_top | 0.17314365199117412 |
| r2_top | 0.7229833376423581 |
| pearson_expr | 0.984361282374852 |
| primary | 0.4854421770368539 |
| cellforge_mse | 0.007101099020938263 |
| cellforge_pcc | 0.984361282374852 |
| cellforge_r2 | 0.9660807084468617 |
| cellforge_mse_de | 0.163185712636234 |
| cellforge_pcc_de | 0.9198648450405051 |
| cellforge_r2_de | 0.7106430445746919 |
| cellforge_mse_deset | 0.1341178073224749 |
| cellforge_pcc_deset | 0.872564043669907 |
| cellforge_r2_deset | 0.6189523154711839 |
| cellforge_n_perts_deset | 19 |
| vcworld_de_accuracy | 0.8103811841038119 |
| vcworld_de_precision | 0.40975103734439833 |
| vcworld_de_recall | 0.10082961072112316 |
| vcworld_de_f1 | 0.16183550138277167 |
| vcworld_de_auroc | 0.6742551101751079 |
| vcworld_de_auprc | 0.3073393417677138 |
| vcworld_dir_accuracy | 0.9118059987236758 |
| vcworld_dir_precision | 0.7835820895522388 |
| vcworld_dir_recall | 0.8376068376068376 |
| vcworld_dir_f1 | 0.8096942990911595 |
| vcworld_dir_auroc | 0.9430111336032388 |
| vcworld_dir_auprc | 0.8427925674272055 |
| vcworld_n_de_pairs | 7835 |

## Runtime and verification

The runner’s own measured computation time is 1.4 seconds. The exclusive external runner receipt records 3.477892209 wall seconds and 2.080944 aggregate process CPU seconds. These are different measurements; no wall-to-CPU substitution is made. Run and score exited 0. The entire sequential chain ran 2026-10-30T17:50:18–17:50:25 UTC (13:50 Toronto).

Execution source commit: `c123104074fe8b7870e90909ba669ff5b9cfbf6c`; runner SHA-256 `5551c13d356e8f1b5efbcd516c79da8d63a318c0ce190e6868a1a4e9f75fa8a1`; bridge SHA-256 `e9d9212267ad298c805cfa0aed195c00c1b0bb3bc19f7d35914f994c0140b149`. Eight focused synthetic tests passed. A first test-launch attempt found pytest absent from gm_dlenv; that operator receipt is preserved, and the authorized single correction used the existing project test environment. No package installation or scientific source change followed.

The [artifact index](linear_ae_adamson/README.md) lists every command, log, explicit exit, runtime, hash, validation and publication receipt. The bridge’s [original Markdown](linear_ae_adamson/score.raw.md) is unchanged; this report adds operator provenance and interpretation without another scoring call. Raw predictions/work/input stay outside Git. No paid call, no main-checkout/evaluator/split/guard/data change.


Full-precision JSON:
```json
{
 "bundle": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf",
 "predictions": "/Users/andresarriaga/linear_ae_adamson/predictions.npz",
 "predictions_sha256": "52118b47e9455dcfde4757d8043837cb96bcc2c6901149091fdf4e93a0e9b9ee",
 "model": "linear_ae",
 "cellforge": {
  "experiment_id": "linear_ae",
  "metrics": {
   "rmse": 0.08426801896887254,
   "mae": 0.05461245870766842,
   "mse": 0.007101099020938262,
   "pearson_delta": 0.4854421770368539,
   "pearson_delta_top": 0.5483655427038636,
   "direction_acc_top": 0.8595238095238096,
   "mse_top": 0.17314365199117412,
   "r2_top": 0.7229833376423581,
   "pearson_expr": 0.984361282374852,
   "primary": 0.4854421770368539,
   "selection_rule": "pearson_delta",
   "cellforge_mse": 0.007101099020938263,
   "cellforge_pcc": 0.984361282374852,
   "cellforge_r2": 0.9660807084468617,
   "cellforge_mse_de": 0.163185712636234,
   "cellforge_pcc_de": 0.9198648450405051,
   "cellforge_r2_de": 0.7106430445746919,
   "cellforge_mse_deset": 0.1341178073224749,
   "cellforge_pcc_deset": 0.872564043669907,
   "cellforge_r2_deset": 0.6189523154711839,
   "cellforge_n_perts_deset": 19,
   "vcworld_de_accuracy": 0.8103811841038119,
   "vcworld_de_precision": 0.40975103734439833,
   "vcworld_de_recall": 0.10082961072112316,
   "vcworld_de_f1": 0.16183550138277167,
   "vcworld_de_auroc": 0.6742551101751079,
   "vcworld_de_auprc": 0.3073393417677138,
   "vcworld_dir_accuracy": 0.9118059987236758,
   "vcworld_dir_precision": 0.7835820895522388,
   "vcworld_dir_recall": 0.8376068376068376,
   "vcworld_dir_f1": 0.8096942990911595,
   "vcworld_dir_auroc": 0.9430111336032388,
   "vcworld_dir_auprc": 0.8427925674272055,
   "vcworld_n_de_pairs": 7835
  }
 },
 "versus": {
  "run": "/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/newcode_opus_w4_r0",
  "experiment_id": "EXP_0441",
  "paired": {
   "experiments": [
    "linear_ae",
    "EXP_0441"
   ],
   "metric": "pearson_delta",
   "a": {
    "experiment_id": "linear_ae",
    "metrics": {
     "rmse": 0.08426801896887254,
     "mae": 0.05461245870766842,
     "mse": 0.007101099020938262,
     "pearson_delta": 0.4854421770368539,
     "pearson_delta_top": 0.5483655427038636,
     "direction_acc_top": 0.8595238095238096,
     "mse_top": 0.17314365199117412,
     "r2_top": 0.7229833376423581,
     "pearson_expr": 0.984361282374852,
     "primary": 0.4854421770368539,
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
    "mean_diff": -0.1132228613733192,
    "se": 0.0430444692533904,
    "wins_a": 9,
    "wins_b": 12,
    "ties": 0,
    "verdict": "b"
   }
  }
 }
}
```

Operator receipt:
```json
{
  "export_path": "/Users/andresarriaga/cellforge_adamson_export_corrected_20261028",
  "export_input_path": "/Users/andresarriaga/cellforge_adamson_export_corrected_20261028/cellforge_input.h5ad",
  "export_input_sha256": "ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a",
  "predictions_path": "/Users/andresarriaga/linear_ae_adamson/predictions.npz",
  "source_commit": "c123104074fe8b7870e90909ba669ff5b9cfbf6c",
  "source_hashes": {
    "tools/baselines_dl/run_linear_ae.py": "5551c13d356e8f1b5efbcd516c79da8d63a318c0ce190e6868a1a4e9f75fa8a1",
    "tools/cellforge_bridge.py": "e9d9212267ad298c805cfa0aed195c00c1b0bb3bc19f7d35914f994c0140b149"
  },
  "run": {
    "start_utc": "2026-10-30T17:50:18.182424+00:00",
    "command": [
      "/Users/andresarriaga/gm_dlenv/bin/python",
      "tools/baselines_dl/run_linear_ae.py",
      "--export",
      "/Users/andresarriaga/cellforge_adamson_export_corrected_20261028",
      "--out",
      "/Users/andresarriaga/linear_ae_adamson"
    ],
    "head": "c123104074fe8b7870e90909ba669ff5b9cfbf6c",
    "cwd": "/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-linear-ae",
    "nice": 19,
    "export_path": "/Users/andresarriaga/cellforge_adamson_export_corrected_20261028",
    "export_input_sha256": "ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a",
    "credentials": "unset",
    "child_pid": 87873,
    "end_utc": "2026-10-30T17:50:21.660304+00:00",
    "exit": 0,
    "wall_seconds": 3.4778922093100846,
    "cpu_seconds": 2.080944
  },
  "runner_receipt": {
    "model": "linear baseline (Ahlmann-Eltze, Huber and Anders 2025)",
    "train_used": 50,
    "train_without_embedding": [],
    "heldout_fallback": [],
    "k": 10,
    "lam": 0.1,
    "train_perturbations": 50,
    "heldout": 38,
    "export_input_sha256": "ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a",
    "predictions_sha256": "52118b47e9455dcfde4757d8043837cb96bcc2c6901149091fdf4e93a0e9b9ee",
    "seconds": 1.4,
    "machine": "macOS-26.5.1-arm64-arm-64bit-Mach-O"
  },
  "original_empty_export_unchanged": true
}

```