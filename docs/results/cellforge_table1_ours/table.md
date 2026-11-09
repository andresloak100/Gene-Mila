# CellForge's Table 1, our rows on our split

Built by `build.py` beside this file from committed reports and the run summaries' sealed (val2) scores. Scored once for this table and nothing else: the Unperturbed rows (`unperturbed.py`) and three runs' selected models (`score_selected.py`); no setting was chosen on any of these scores. Our rows are on our split and bundle, CellForge's rows are copied from its paper (`docs/results/cellforge_table1.json`) and are **not comparable**: its split, preprocessing and metric scale cannot be reproduced (AGENTS.md). Both sealed sets are worn, so every row is descriptive. Agent rows are mean ± sample sd over three seeds; GEARS over seeds 0, 2, 3; the other rows are deterministic, one run. pearson_delta is the lab's primary metric (correlation of predicted and true change from control); CellForge's PCC is on absolute expression and is near 0.98 for every model.

## Gene knockout perturbation, scRNA-seq (Adamson et al. 2016)

| Model | n | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ | pearson_delta ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unperturbed (control mean) | 1 | 0.0116 | 0.9738 | 0.9446 | 0.2312 | 0.8937 | 0.6003 | 0.0262 |
| Mean response (lab's start, OLS) | 1 | 0.0070 | 0.9846 | 0.9663 | 0.1536 | 0.9318 | 0.7341 | 0.5196 |
| Linear, Ahlmann-Eltze 2025 | 1 | 0.0071 | 0.9844 | 0.9661 | 0.1632 | 0.9199 | 0.7106 | 0.4854 |
| GEARS, Roohani 2023 | 3 | 0.0087 ± 0.0006 | 0.9807 ± 0.0012 | 0.9584 ± 0.0027 | 0.1330 ± 0.0037 | 0.9277 ± 0.0011 | 0.7515 ± 0.0069 | 0.4073 ± 0.0116 |
| Gene-Mila agents, DeepSeek, clean tier 1 (block G0) | 3 | 0.0065 ± 0.0006 | 0.9860 ± 0.0013 | 0.9690 ± 0.0028 | 0.1299 ± 0.0148 | 0.9456 ± 0.0089 | 0.7792 ± 0.0274 | 0.5663 ± 0.0362 |
| Gene-Mila agents, DeepSeek, clean tier 1 + tables (G1) | 3 | 0.0221 ± 0.0260 | 0.9841 ± 0.0010 | 0.8944 ± 0.1240 | 0.1586 ± 0.0171 | 0.9374 ± 0.0045 | 0.7132 ± 0.0515 | 0.4906 ± 0.0687 |
| Gene-Mila agents, DeepSeek, clean tier 1 (block T0, code d53edff) | 3 | 0.0067 ± 0.0006 | 0.9854 ± 0.0012 | 0.9677 ± 0.0027 | 0.1368 ± 0.0137 | 0.9432 ± 0.0032 | 0.7670 ± 0.0203 | 0.5553 ± 0.0203 |
| CellForge pipeline, run by us, DeepSeek v4-pro (block U, 1 of 3 runs finished) | 1 | 0.0116 | 0.9738 | 0.9447 | 0.2310 | 0.8935 | 0.6002 | 0.0329 |

CellForge's own rows (its paper, not comparable):

| Model | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---:|---:|---:|---:|---:|---:|
| Unperturbed | 0.9840 | 0.0001 | -0.0127 | 3.7865 | 0.0012 | -4.2437 |
| Random Forest | 0.3053 | 0.2063 | 0.0504 | 0.5923 | 0.2632 | 0.1653 |
| Linear Regression | 0.5803 | 0.0026 | 0.0435 | 0.6995 | 0.0257 | 0.1074 |
| CPA | 0.0067 | 0.9833 | 0.9845 | 0.1447 | 0.9024 | 0.8896 |
| scGen | 0.0082 | 0.9805 | 0.9611 | 0.1301 | 0.8994 | 0.7263 |
| CondOT | 0.0062 | 0.9608 | 0.9740 | 0.1997 | 0.9341 | 0.9002 |
| Biolord | 0.0044 | 0.7799 | 0.9844 | 0.1256 | 0.9097 | 0.9276 |
| scGPT | 0.0100 | 0.9861 | 0.9649 | 0.2562 | 0.9088 | 0.7911 |
| CellForge-Models | 0.0051 | 0.9883 | 0.9761 | 0.2013 | 0.9474 | 0.8912 |

## Gene knockout perturbation, scRNA-seq (Norman et al. 2019)

| Model | n | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ | pearson_delta ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Unperturbed (control mean) | 1 | 0.0140 | 0.9729 | 0.9331 | 0.3153 | 0.8386 | 0.5881 | 0.0343 |
| Additive singles (lab's start) | 1 | 0.0059 | 0.9879 | 0.9722 | 0.1016 | 0.9412 | 0.8463 | 0.7126 |
| Linear, Ahlmann-Eltze 2025 | 1 | 0.0074 | 0.9841 | 0.9650 | 0.1802 | 0.8996 | 0.7511 | 0.6526 |
| GEARS, Roohani 2023 | 3 | 0.0076 ± 0.0004 | 0.9845 ± 0.0008 | 0.9642 ± 0.0019 | 0.1242 ± 0.0069 | 0.9301 ± 0.0031 | 0.8223 ± 0.0070 | 0.6071 ± 0.0111 |
| Gene-Mila agents, DeepSeek, clean tier 1 (block G0) | 3 | 0.0054 ± 0.0002 | 0.9888 ± 0.0003 | 0.9747 ± 0.0008 | 0.1045 ± 0.0040 | 0.9393 ± 0.0021 | 0.8479 ± 0.0041 | 0.7193 ± 0.0012 |
| Gene-Mila agents, DeepSeek, clean tier 1 + tables (G1) | 3 | 0.0056 ± 0.0005 | 0.9885 ± 0.0007 | 0.9735 ± 0.0024 | 0.1065 ± 0.0027 | 0.9380 ± 0.0015 | 0.8442 ± 0.0035 | 0.7201 ± 0.0065 |
| Gene-Mila agents, DeepSeek, clean tier 1 (block T0, code d53edff) | 3 | 0.0054 ± 0.0001 | 0.9887 ± 0.0004 | 0.9747 ± 0.0007 | 0.1060 ± 0.0056 | 0.9380 ± 0.0026 | 0.8444 ± 0.0057 | 0.7209 ± 0.0026 |
| CellForge pipeline, run by us, DeepSeek v4-pro (block U, 0 of 3 runs finished) | – | – | – | – | – | – | – | – |

CellForge's own rows (its paper, not comparable):

| Model | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---:|---:|---:|---:|---:|---:|
| Unperturbed | 0.9251 | 0.0000 | -0.1738 | 5.1214 | -0.0021 | -4.2047 |
| Random Forest | 0.4059 | 0.1625 | 0.0623 | 0.6817 | 0.1428 | 0.0498 |
| Linear Regression | 0.4989 | 0.0244 | 0.0314 | 0.7331 | 0.0265 | 0.0238 |
| CPA | 0.0051 | 0.9779 | 0.9603 | 0.3400 | 0.5754 | 0.4555 |
| scGen | 0.0053 | 0.9221 | 0.9521 | 0.3877 | 0.5605 | 0.3220 |
| CondOT | 0.0420 | 0.9847 | 0.9619 | 0.2791 | 0.8022 | 0.7470 |
| Biolord | 0.0027 | 0.4374 | 0.9830 | 0.2450 | 0.4646 | 0.8112 |
| scGPT | 0.0076 | 0.9823 | 0.9536 | 0.5318 | 0.8630 | 0.5652 |
| CellForge-Models | 0.0034 | 0.9846 | 0.9609 | 0.1736 | 0.8109 | 0.5975 |

## Srivatsan 2020 (sci-Plex 3, drugs)

No row of ours. The lab models genetic perturbations only, and no Srivatsan bundle exists; building one is assigned to the Mila agent (`docs/BRIEF_MILA_AGENT.md` section 3).

## Caveats

- Adamson GEARS, linear and Unperturbed rows use the corrected three-source export (`~/cellforge_adamson_export_corrected_20261028`), which has 1,770 more controls and 10 more training cells than the bundle the agents saw. Norman's export follows the bundle's single source exactly.
- The agent rows are each run's selected model; the block G0 and G1 bundles (`adamson_cf_clean`, `norman_clean`, with or without three tables) share the split of `adamson_cf` and `norman`.
- Three agent runs (adamson_cf_g0 r3, adamson_cf_g1 r2, norman_g1 r2) had not stored CellForge's metrics for their selected model; `score_selected.py` scored that fixed model once, and its pearson_delta matches the published block G sealed reading.
- Block T0 (`docs/PLAN_T_TABLE_AGENTS.md`) repeats block G0's design on code d53edff: six fresh DeepSeek runs, 20 minutes each, run on 3-4 Nov 2026 for this table; $4.34 by the shared ledger. Every planner stayed DeepSeek and no feature read a table (`genemila_t_logs/*.check.txt`).
- The CellForge rows are CellForge's own pipeline (gersteinlab/CellForge 6585ff9, unchanged) run by us on the same exports, every agent DeepSeek v4-pro, each model's predictions scored once by the bridge like GEARS (`docs/PLAN_U_CELLFORGE.md`; receipts `cellforge_ours/cf_*/`, outcome `cellforge_ours/block_u_outcome.md`). Block U attempted three Adamson and three Norman runs on the 24 GB Mac under a 6-hour limit per training step and, after the first Norman script reached 47 GB, a 12 GB memory cap; one Adamson run finished and no Norman run did. $9.20 for the block by its proxy ledger (1,005 calls, cap $15).
- The one finished CellForge model (`cf_adamson_s42`) gave the same prediction, to five decimals, for every held-out perturbation: its output did not vary with its hashed perturbation token (own validation correlation 0.10 per cell), so the row equals the Unperturbed row to three decimals. n = 1, no ranking claim.
- The five failed CellForge runs each reached their training script (analysis, design and code generation cost $1.3 to $1.9 per run); every script trains the plan's 4-layer, 8-head, 512-wide transformer over gene tokens. Adamson s0 (2,048 gene tokens, CPU) and Norman s42 (1,024 tokens, Apple GPU) ran out the 6-hour limit still training (peak 8.7 and 4.7 GB); Norman s0, Norman s2 and Adamson s2 passed 12 GB within 27, 85 and 24 s of their script starting (12.4, 12.4 and 21.6 GB), before any epoch could have finished; the training files are under 1 GB dense, so the model's activations, not the data, are the likely cause (not measured). No metric exists for them; the Norman row is empty.
- GEARS falls back to the mean training change for held-out perturbations outside its gene graph; see each seed's receipt. On Norman no held-out perturbation needed the fallback (`../gears_norman/aggregate.md`).
