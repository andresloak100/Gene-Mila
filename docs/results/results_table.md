# Results in CellForge's Table 1 layout

Metrics on query-only held-out perturbations: MSE, Pearson correlation and R² between predicted and true mean expression (log1p of counts per 10k) per perturbation, averaged over perturbations; the DE columns restrict each perturbation to its top-20 DE genes. Sources: **ours** = this lab (mean ± sd over n independent runs); **rerun** = the paper's simple baselines refitted on the same split and scored with the same code (Random Forest: mean ± sd over seeds); **reported** = quoted from the paper, scored by its authors on their split and preprocessing. Bold and ¹²³ mark the three best means per column.

**Gene knockout perturbation, scRNA-seq (Adamson et al. 2016)**

| Method | Source | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---|---|---|---|---|---|---|
| Unperturbed | reported | 0.9840 | 0.0001 | -0.0127 | 3.7865 | 0.0012 | -4.2437 |
| Random Forest | reported | 0.3053 | 0.2063 | 0.0504 | 0.5923 | 0.2632 | 0.1653 |
| Linear Regression | reported | 0.5803 | 0.0026 | 0.0435 | 0.6995 | 0.0257 | 0.1074 |
| CPA | reported | 0.0067 | 0.9833 | **0.9845**¹ | 0.1447 | 0.9024 | 0.8896 |
| scGen | reported | 0.0082 | 0.9805 | 0.9611 | 0.1301 | 0.8994 | 0.7263 |
| CondOT | reported | 0.0062 | 0.9608 | 0.9740 | 0.1997 | 0.9341 | 0.9002² |
| Biolord | reported | **0.0044**¹ | 0.7799 | 0.9844² | 0.1256 | 0.9097 | **0.9276**¹ |
| scGPT | reported | 0.0100 | 0.9861 | 0.9649 | 0.2562 | 0.9088 | 0.7911 |
| CellForge-Models | reported | 0.0051 ± 0.0063² | **0.9883 ± 0.0459**¹ | 0.9761 ± 0.0803³ | 0.2013 ± 0.0444 | 0.9474 ± 0.0601 | 0.8912 ± 0.0518³ |
| Unperturbed (rerun) | rerun | 0.0103 | 0.9785 | 0.9505 | 0.2263 | 0.8995 | 0.6060 |
| Linear Regression (rerun) | rerun | 0.0071 | 0.9845 | 0.9660 | 0.1602 | 0.9200 | 0.7140 |
| Random Forest (rerun) | rerun | 0.0095 ± 0.0000 | 0.9803 ± 0.0000 | 0.9547 ± 0.0000 | 0.1983 ± 0.0004 | 0.9091 ± 0.0001 | 0.6499 ± 0.0005 |
| Gene-Mila starting model | ours | 0.0070 ± 0.0000 | 0.9846 ± 0.0000 | 0.9663 ± 0.0000 | 0.1536 ± 0.0000 | 0.9318 ± 0.0000 | 0.7341 ± 0.0000 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 1 workers (n=2) | ours | 0.0062 ± 0.0004 | 0.9862 ± 0.0009 | 0.9702 ± 0.0018 | **0.1086 ± 0.0049**¹ | 0.9572 ± 0.0007² | 0.8173 ± 0.0063 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 4 workers (n=2) | ours | 0.0058 ± 0.0003 | 0.9873 ± 0.0007³ | 0.9722 ± 0.0016 | 0.1167 ± 0.0023³ | 0.9554 ± 0.0007³ | 0.8028 ± 0.0031 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 8 workers (n=2) | ours | 0.0062 ± 0.0003 | 0.9866 ± 0.0006 | 0.9705 ± 0.0013 | 0.1194 ± 0.0034 | 0.9544 ± 0.0006 | 0.8020 ± 0.0013 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 16 workers (n=2) | ours | 0.0057 ± 0.0001³ | 0.9875 ± 0.0003² | 0.9727 ± 0.0005 | 0.1106 ± 0.0093² | **0.9578 ± 0.0039**¹ | 0.8157 ± 0.0200 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f, 4 workers (n=2) | ours | 0.0063 ± 0.0001 | 0.9863 ± 0.0001 | 0.9697 ± 0.0005 | 0.1236 ± 0.0081 | 0.9527 ± 0.0033 | 0.7905 ± 0.0167 |
| Gene-Mila, deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f, 4 workers (n=2) | ours | 0.0064 ± 0.0010 | 0.9862 ± 0.0021 | 0.9695 ± 0.0047 | 0.1325 ± 0.0221 | 0.9461 ± 0.0101 | 0.7759 ± 0.0384 |
| Gene-Mila, scripted control (no LLM) @ 2492e11, 4 workers (n=6) | ours | 0.0070 ± 0.0000 | 0.9847 ± 0.0000 | 0.9665 ± 0.0000 | 0.1451 ± 0.0000 | 0.9428 ± 0.0000 | 0.7559 ± 0.0000 |
| Gene-Mila, scripted control (no LLM) @ 537344f, 4 workers (n=1) | ours | 0.0073 | 0.9839 | 0.9649 | 0.1628 | 0.9355 | 0.7259 |
| Gene-Mila, scripted control (no LLM) @ 72a53c5, 4 workers (n=6) | ours | 0.0075 ± 0.0001 | 0.9835 ± 0.0003 | 0.9640 ± 0.0007 | 0.1688 ± 0.0047 | 0.9326 ± 0.0022 | 0.7153 ± 0.0082 |

- Lab runs: claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 1 workers: scale_w1_r0, scale_w1_r1 (split split_450515be1a0d8d2e); claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 4 workers: scale_w4_r0, scale_w4_r1 (split split_450515be1a0d8d2e); claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 8 workers: scale_w8_r0, scale_w8_r1 (split split_450515be1a0d8d2e); claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 16 workers: scale_w16_r0, scale_w16_r1 (split split_450515be1a0d8d2e); claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f, 4 workers: newcode_opus_w4_r0, newcode_opus_w4_r1 (split split_450515be1a0d8d2e); deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f, 4 workers: newcode_ds_w4_r0, newcode_ds_w4_r1 (split split_450515be1a0d8d2e); scripted control (no LLM) @ 2492e11, 4 workers: scale_control_r0, scale_control_r1, scale_control_r2, scale_control_r3, scale_control_r4, scale_control_r5 (split split_450515be1a0d8d2e); scripted control (no LLM) @ 537344f, 4 workers: newcode2_control_r0 (split split_450515be1a0d8d2e); scripted control (no LLM) @ 72a53c5, 4 workers: newcode_control_r0, newcode_control_r1, newcode_control_r2, newcode_control_r3, newcode_control_r4, newcode_control_r5 (split split_450515be1a0d8d2e)
- Starting model: OLS on baseline features (control mean, mean response, target indicator).
- Reported rows are the paper's reruns of those methods; their split, preprocessing and metric scale are not stated, so they are not directly comparable until the calibration below reproduces the paper's simple-baseline rows.

**Gene knockout perturbation, scRNA-seq (Adamson et al. 2016) — DE columns on CellForge's documented DE set (Wilcoxon BH p < 0.05 and |log2FC| > 0.5), ours and reruns only**

| Method | Source | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---|---|---|---|
| Unperturbed (rerun) | rerun | 0.1551 | 0.8479 | 0.5507 |
| Linear Regression (rerun) | rerun | 0.1338 | 0.8749 | 0.6170 |
| Random Forest (rerun) | rerun | 0.1464 ± 0.0002 | 0.8670 ± 0.0005 | 0.5661 ± 0.0006 |
| Gene-Mila starting model | ours | 0.0916 ± 0.0000 | 0.9021 ± 0.0000 | 0.7240 ± 0.0000 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 1 workers (n=2) | ours | 0.0296 ± 0.0011 | 0.9685 ± 0.0002 | 0.9102 ± 0.0031 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 4 workers (n=2) | ours | 0.0326 ± 0.0020 | 0.9678 ± 0.0017 | 0.8978 ± 0.0012 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 8 workers (n=2) | ours | 0.0338 ± 0.0013 | 0.9662 ± 0.0009 | 0.8930 ± 0.0073 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 2492e11, 16 workers (n=2) | ours | 0.0311 ± 0.0025 | 0.9701 ± 0.0024 | 0.9003 ± 0.0114 |
| Gene-Mila, claude_cli:opus planner, deepseek:deepseek-flash workers @ 537344f, 4 workers (n=2) | ours | 0.0339 ± 0.0063 | 0.9662 ± 0.0027 | 0.8917 ± 0.0227 |
| Gene-Mila, deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers @ 537344f, 4 workers (n=2) | ours | 0.0528 ± 0.0119 | 0.9495 ± 0.0081 | 0.8372 ± 0.0480 |
| Gene-Mila, scripted control (no LLM) @ 2492e11, 4 workers (n=6) | ours | 0.0408 ± 0.0000 | 0.9600 ± 0.0000 | 0.8569 ± 0.0000 |
| Gene-Mila, scripted control (no LLM) @ 537344f, 4 workers (n=1) | ours | 0.0568 | 0.9426 | 0.8139 |
| Gene-Mila, scripted control (no LLM) @ 72a53c5, 4 workers (n=6) | ours | 0.0636 ± 0.0053 | 0.9340 ± 0.0066 | 0.7959 ± 0.0140 |

## Notes on the reported rows

- Every row is CellForge's own rerun of that method ('All baseline methods are reproduced on the corresponding dataset under the unseen perturbation setting').
- CellForge-Models rows are mean +- standard deviation across three automatically designed models, chosen from N = 5 independent runs by an unstated rule.
- The paper's rank markers use best-case bounds (mean - std where lower is better, mean + std where higher is better) and break that rule in places; ranks here are recomputed from the means.
- DE metrics are restricted to the top 20 DE genes of the true response per perturbation, ranked by |log fold change| (Appendix E.4).
- The paper does not state the expression scale of the metrics, the preprocessing, or what the Unperturbed baseline predicts; see the calibration section of the generated table.
- Source: CellForge, arXiv 2508.02276v2, Table 1 (Post-perturbation gene expression prediction results)
