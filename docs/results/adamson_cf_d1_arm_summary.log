# Block D, reading 3: D1 against G1 and G0 on the development tier (descriptive)

One `tools/feature_compare.py --null-reps 0` call rebuilt the nine selected models under the same parent (the built-in start: M1 0.484230270) and fold seeds, on `data/adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`). OOF is not held out for any arm: every system selected on these labels. No test; no difference is claimed inside either arm's spread. D1 differs from G1 by discovery mode and PR #71's code; G0 is the same bundle without the three tables (context).

|arm|n runs|M1 mean ± sample SD|delta M1 versus parent mean ± sample SD|
|---|---:|---|---|
|d1|3|0.523155270 ± 0.029324927|0.038925000 ± 0.029324927|
|g1|3|0.490964428 ± 0.004435578|0.006734158 ± 0.004435578|
|g0|3|0.525950139 ± 0.035263074|0.041719869 ± 0.035263074|

|source|columns|M1|delta M1|SE_adj|wins / n|
|---|---:|---:|---:|---:|---|
|d1_r0|23|0.537740474|+0.053510205|0.012004390|36 / 50|
|d1_r2|25|0.489397499|+0.005167229|0.001977883|30 / 50|
|d1_r3|11|0.542327838|+0.058097568|0.012875323|33 / 50|
|g1_r0|23|0.486410959|+0.002180689|0.004815695|30 / 50|
|g1_r2|26|0.491210450|+0.006980181|0.002816648|28 / 50|
|g1_r3|22|0.495271874|+0.011041605|0.004619171|31 / 50|
|g0_r0|19|0.540524253|+0.056293983|0.012857119|36 / 50|
|g0_r2|23|0.485736181|+0.001505911|0.007592511|30 / 50|
|g0_r3|19|0.551589982|+0.067359713|0.013528519|38 / 50|

Every emitted OOF metric per run, and per arm its mean and sample SD, is in the JSON twin.

- OOF only: every system has selected on these labels; not held out
- M4-M7 use each perturbation's top 20 genes by |true delta| (genemila.benchmark.evaluator), not CellForge's Wilcoxon DE top 20
- ridge on the tool's alpha grid with an honest OOF alpha; a parent run's own model type and alpha are not reused
- the literal caps make pasting labels into a file expensive, not impossible
