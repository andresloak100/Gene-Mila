# Norman G six-run descriptive OOF comparison

All six set rows rebuilt successfully. Fixed ridge OOF refits with honest OOF alpha, null-reps 0. OOF is reused development evidence. Mean and sample SD use independent runs 0/2/3.

| arm | n runs | M1 mean ± sample SD | delta M1 versus parent mean ± sample SD |
|---|---:|---|---|
| g0 | 3 | 0.577886422 ± 0.001085220 | 0.009698376 ± 0.001085220 |
| g1 | 3 | 0.579310580 ± 0.007628308 | 0.011122534 ± 0.007628308 |

| source | run directory | M1 | delta M1 | SE_adj | wins / n |
|---|---|---:|---:|---:|---|
| g0_r0 | /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r0 | 0.577847408 | +0.009659362 | 0.007983177 | 54 / 112 |
| g0_r2 | /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r2 | 0.576821235 | +0.008633189 | 0.004049349 | 70 / 112 |
| g0_r3 | /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g0_ds_w4_r3 | 0.578990623 | +0.010802577 | 0.003944015 | 79 / 112 |
| g1_r0 | /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r0 | 0.587423283 | +0.019235236 | 0.009859076 | 69 / 112 |
| g1_r2 | /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r2 | 0.572282844 | +0.004094798 | 0.001300034 | 75 / 112 |
| g1_r3 | /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_g1_ds_w4_r3 | 0.578225614 | +0.010037568 | 0.004210477 | 66 / 112 |

All emitted M1–M7 and M12 per-run metrics, parent drops, selected experiment/model names and arm means/sample SDs are preserved in the JSON twin; M8–M11 are not emitted. No within-noise, fresh-test or CellForge victory claim.

- OOF only: every system has selected on these labels; not held out
- M4-M7 use each perturbation's top 20 genes by |true delta| (genemila.benchmark.evaluator), not CellForge's Wilcoxon DE top 20
- ridge on the tool's alpha grid with an honest OOF alpha; a parent run's own model type and alpha are not reused
- the literal caps make pasting labels into a file expensive, not impossible
