# Adamson G six-run descriptive OOF comparison

All six set rows rebuilt successfully; fixed ridge OOF refits, no nulls. OOF is not held out. Mean and sample SD use independent runs 0/2/3; no within-noise, fresh-test or victory claim.

|arm|n runs|M1 mean ± sample SD|delta M1 versus parent mean ± sample SD|
|---|---:|---|---|
|g0|3|0.525950139 ± 0.035263074|0.041719869 ± 0.035263074|
|g1|3|0.490964428 ± 0.004435578|0.006734158 ± 0.004435578|

|source|run directory|M1|delta M1|SE_adj|wins / n|
|---|---|---:|---:|---:|---|
|g0_r0|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r0|0.540524253|+0.056293983|0.012857119|36 / 50|
|g0_r2|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r2|0.485736181|+0.001505911|0.007592511|30 / 50|
|g0_r3|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r3|0.551589982|+0.067359713|0.013528519|38 / 50|
|g1_r0|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r0|0.486410959|+0.002180689|0.004815695|30 / 50|
|g1_r2|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r2|0.491210450|+0.006980181|0.002816648|28 / 50|
|g1_r3|/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g1_ds_w4_r3|0.495271874|+0.011041605|0.004619171|31 / 50|

All emitted M1–M7 and M12 per-run values and arm means/sample SDs are in the JSON twin; M8–M11 are not emitted.

- OOF only: every system has selected on these labels; not held out
- M4-M7 use each perturbation's top 20 genes by |true delta| (genemila.benchmark.evaluator), not CellForge's Wilcoxon DE top 20
- ridge on the tool's alpha grid with an honest OOF alpha; a parent run's own model type and alpha are not reused
- the literal caps make pasting labels into a file expensive, not impossible
