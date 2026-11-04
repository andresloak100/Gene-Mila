# GEARS on Norman, seeds 0, 2, 3, scored once each on the sealed set

GEARS 0.1.2 on CPU, 20 epochs, export `~/cellforge_norman_export` (input sha256 in each receipt). Run by `chain.sh` beside this file; per-seed reports `../gears_norman_s{0,2,3}.md`.

| metric | seed 0 | seed 2 | seed 3 | mean ± sd |
|---|---:|---:|---:|---:|
| cellforge_mse | 0.0074 | 0.0073 | 0.0081 | 0.0076 ± 0.0004 |
| cellforge_pcc | 0.9849 | 0.9851 | 0.9835 | 0.9845 ± 0.0008 |
| cellforge_r2 | 0.9650 | 0.9655 | 0.9620 | 0.9642 ± 0.0019 |
| cellforge_mse_de | 0.1185 | 0.1223 | 0.1318 | 0.1242 ± 0.0069 |
| cellforge_pcc_de | 0.9334 | 0.9296 | 0.9273 | 0.9301 ± 0.0031 |
| cellforge_r2_de | 0.8289 | 0.8232 | 0.8149 | 0.8223 ± 0.0070 |
| pearson_delta | 0.6140 | 0.6130 | 0.5943 | 0.6071 ± 0.0111 |

Paired against the lab model `norman_ds_from_n2_w4_r1` EXP_0681 (GEARS minus lab, pearson_delta per sealed perturbation):

| seed | n | mean diff | se | GEARS wins | lab wins |
|---|---:|---:|---:|---:|---:|
| 0 | 56 | -0.1052 | 0.0135 | 6 | 50 |
| 2 | 56 | -0.1062 | 0.0155 | 5 | 51 |
| 3 | 56 | -0.1249 | 0.0147 | 5 | 51 |

| seed | held out | fallback to mean change | training conditions outside the gene graph | wall time, h |
|---|---:|---:|---:|---:|
| 0 | 119 | 0 | 2 | 8.98 |
| 2 | 119 | 0 | 2 | 3.03 |
| 3 | 119 | 0 | 2 | 2.11 |

Seed 0 was paused from 2026-11-03T23:42:54Z to 2026-11-04T02:08:45Z while paid block T ran (`pauses.txt`), and shared the CPU before that, so its wall time is not a speed measurement. Seeds 2 and 3 ran alone.
