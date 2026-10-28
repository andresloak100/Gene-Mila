# For the fresh-test holder: what you do, in one page

You are the one person who sees the answers of Gene-Mila's fresh test. Nobody else on the project (Andres, the AI
agents, the operators) sees them. Your job takes about an hour, on your own computer or on the Mila cluster. The full
protocol is `docs/PLAN_R_FRESH_TEST.md`; this page is what you do.

## Why you

The lab's models have been scored on the same held-out genes many times, so their scores may be optimistic. A test
whose answers only you hold, scored once after the models are frozen and their predictions published as hashes,
cannot have been tuned to.

## Before anything (5 minutes)

1. Reply on [#41](https://github.com/andresloak100/Gene-Mila/issues/41) that you accept, with your GitHub handle.
2. Do not open the lab's runs or talk about the cohort with the operators until you have posted both reports.

## Step 1: get the cohort yourself

Download `ReplogleWeissman2022_K562_gwps.h5ad` from the public record (Zenodo 13350497, about 9 GB; md5
`13db594f8f1d2ccb88fec44a13e414dc`). Never take it from the lab's Mac. Post its sha256 on #41:

```
shasum -a 256 ReplogleWeissman2022_K562_gwps.h5ad
```

## Step 2: receive the deposit

The lab posts on #41 the sha256 of a deposit archive (every frozen model's predictions) before it tells you where the
archive is. Download it, check its sha256 against that post, and unpack it. It holds `manifest.json` (the targets,
the R1/R2 draw, the gene panel), `batch.json` (the models and the comparisons fixed in advance), one folder per model
and `deposit_sha256.json` (each file's hash, checked by the tool).

## Step 3: score, twice, from one run of the tool

In a clone of the repository (`git clone https://github.com/andresloak100/Gene-Mila`) with its Python environment
(`pip install -r requirements-lock.txt`):

```
python tools/fresh_test_score.py --cohort ReplogleWeissman2022_K562_gwps.h5ad --manifest deposit/manifest.json \
    --deposit deposit --part r1 --out r1_report.md
python tools/fresh_test_score.py --cohort ReplogleWeissman2022_K562_gwps.h5ad --manifest deposit/manifest.json \
    --deposit deposit --part r1 r2 --out r2_report.md
```

The first command gives the R1 report. The second scores both parts with one Holm correction over all comparisons;
its R1 numbers repeat the first report's.

## Step 4: post, in order

1. Post `r1_report.md` on #41 (paste it; attach the `.json` twin).
2. Then post `r2_report.md` and its `.json` the same way.

Change nothing between them, re-run nothing and accept no new deposit. If the tool refuses (a hash mismatch, a missing
prediction), post its message as it is and stop. That is a result too.

## What you never do

Share the cohort's per-gene answers, score a model that is not in the deposit, or score anything twice.
