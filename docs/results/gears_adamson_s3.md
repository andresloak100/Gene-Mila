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
