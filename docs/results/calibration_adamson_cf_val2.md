# Which metric definition reproduces CellForge's simple-baseline rows?

21 held-out perturbations (val2), 5652 held-out cells. Each candidate definition is applied to the same predictions; the paper's row is listed first.

**Unperturbed**

| definition | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---|---|---|---|---|---|
| paper (reported) | 0.9840 | 0.0001 | -0.0127 | 3.7865 | 0.0012 | -4.2437 |
| means/log1p | 0.0103 | 0.9785 | 0.9505 | 0.2263 | 0.8995 | 0.6060 |
| means/log1p/pooled | 0.0103 | -0.0000 | -0.5255 | 0.2263 | 0.8363 | 0.6432 |
| means/delta | 0.0103 | 0.0000 | -0.1228 | 0.2263 | 0.0000 | -1.2282 |
| means/delta/pooled | 0.0103 | 0.0000 | -0.5255 | 0.2263 | 0.0000 | -0.0517 |
| means/z-train/pooled | 1.7521 | 0.0000 | -0.4850 | 12.5684 | -0.4047 | -0.3411 |
| means/z-cells/pooled | 0.0465 | 0.0000 | -0.5175 | 0.8111 | 0.0000 | -0.0550 |
| cells/log1p/pooled | 0.2303 | 0.0000 | -0.0160 | 0.5791 | 0.6643 | 0.3946 |
| cells/z-cells/pooled | 1.1423 | 0.0000 | -0.0143 | 2.1453 | 0.0000 | -0.0243 |

Closest to the paper: `cells/z-cells/pooled` (mean relative error 0.39; below about 0.1 means the definition reproduces the row).

**Mean training response**

| definition | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---|---|---|---|---|---|
| means/log1p | 0.0071 | 0.9845 | 0.9660 | 0.1602 | 0.9200 | 0.7140 |
| means/log1p/pooled | 0.0071 | 0.0000 | -0.0481 | 0.1602 | 0.8764 | 0.7474 |
| means/delta | 0.0071 | 0.4945 | -0.2644 | 0.1602 | 0.5195 | -0.3860 |
| means/delta/pooled | 0.0071 | -0.0000 | -0.0481 | 0.1602 | 0.7151 | 0.2554 |
| means/z-train/pooled | 1.2517 | 0.0000 | -0.0609 | 10.5899 | 0.0000 | -0.1300 |
| means/z-cells/pooled | 0.0321 | 0.0000 | -0.0491 | 0.6041 | 0.6920 | 0.2142 |
| cells/log1p/pooled | 0.2271 | 0.0000 | -0.0016 | 0.5085 | 0.6979 | 0.4684 |
| cells/z-cells/pooled | 1.1279 | 0.0000 | -0.0015 | 1.9270 | 0.4357 | 0.0800 |

**Linear Regression**

| definition | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---|---|---|---|---|---|
| paper (reported) | 0.5803 | 0.0026 | 0.0435 | 0.6995 | 0.0257 | 0.1074 |
| means/log1p | 0.0071 | 0.9845 | 0.9660 | 0.1602 | 0.9200 | 0.7140 |
| means/log1p/pooled | 0.0071 | 0.0000 | -0.0481 | 0.1602 | 0.8764 | 0.7474 |
| means/delta | 0.0071 | 0.4945 | -0.2644 | 0.1602 | 0.5195 | -0.3860 |
| means/delta/pooled | 0.0071 | -0.0000 | -0.0481 | 0.1602 | 0.7151 | 0.2554 |
| means/z-train/pooled | 1.2517 | -0.0000 | -0.0609 | 10.5899 | 0.0000 | -0.1300 |
| means/z-cells/pooled | 0.0321 | 0.0000 | -0.0491 | 0.6041 | 0.6920 | 0.2142 |
| cells/log1p/pooled | 0.2271 | 0.0000 | -0.0016 | 0.5085 | 0.6979 | 0.4684 |
| cells/z-cells/pooled | 1.1279 | 0.0000 | -0.0015 | 1.9270 | 0.4357 | 0.0800 |

Closest to the paper: `cells/z-cells/pooled` (mean relative error 3.34; below about 0.1 means the definition reproduces the row).

**Random Forest**

| definition | MSE ↓ | PCC ↑ | R² ↑ | MSE_DE ↓ | PCC_DE ↑ | R²_DE ↑ |
|---|---|---|---|---|---|---|
| paper (reported) | 0.3053 | 0.2063 | 0.0504 | 0.5923 | 0.2632 | 0.1653 |
| means/log1p | 0.0094 | 0.9804 | 0.9547 | 0.1987 | 0.9090 | 0.6494 |
| means/log1p/pooled | 0.0094 | -0.0000 | -0.3951 | 0.1987 | 0.8563 | 0.6868 |
| means/delta | 0.0094 | 0.3513 | -0.0115 | 0.1987 | 0.4081 | -0.9729 |
| means/delta/pooled | 0.0094 | 0.0000 | -0.3951 | 0.1987 | 0.5735 | 0.0767 |
| means/z-train/pooled | 1.5968 | 0.0000 | -0.3534 | 11.6038 | -0.2615 | -0.2382 |
| means/z-cells/pooled | 0.0426 | -0.0000 | -0.3920 | 0.7152 | 0.5568 | 0.0697 |
| cells/log1p/pooled | 0.2294 | 0.0000 | -0.0118 | 0.5490 | 0.6808 | 0.4260 |
| cells/z-cells/pooled | 1.1382 | -0.0000 | -0.0107 | 2.0415 | 0.3411 | 0.0253 |

Closest to the paper: `cells/log1p/pooled` (mean relative error 0.95; below about 0.1 means the definition reproduces the row).
