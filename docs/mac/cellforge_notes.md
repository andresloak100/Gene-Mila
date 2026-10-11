# CellForge: what its public code actually specifies

Source: https://github.com/gersteinlab/CellForge, shallow clone at commit `6585ff9`
("CellForge"), read on 2026-10-03. 99 tracked files, 2.6 MB. Paths below are relative to
that repository. Nothing in it was executed.

## Headline

**The repository contains no evaluation code and no preprocessing pipeline for the
benchmark.** The metrics, the DE-gene rule and the preprocessing exist only as prose in
`docs/` and as text inside LLM prompts; the training/evaluation script is written afresh
by a coding agent on every run. The only benchmark logic implemented in Python is the
train/val/OOD split. A like-for-like comparison therefore has to be built from the prose
definitions plus the paper, and cannot be obtained by calling CellForge's evaluator.

## (a) Which Adamson files, and how they are combined

- The downloader lists three scPerturb files and fetches all three:
  `scripts/download_datasets.py:66-92`
  - `AdamsonWeissman2016_GSM2406675_10X001.h5ad`, 34,557,246 bytes, md5 `232f7e37...`
  - `AdamsonWeissman2016_GSM2406677_10X005.h5ad`, 139,059,637 bytes, md5 `86573919...`
  - `AdamsonWeissman2016_GSM2406681_10X010.h5ad`, 471,286,951 bytes, md5 `2fa44ea6...`
- **They are not merged.** `README.md:84`, `docs/QUICKSTART.md:143` and
  `docs/RESULTS.md:209` all say the downloader keeps the original filenames and "does not
  create `adamson.h5ad` or merge them"; the user must supply a `<prepared-dataset>.h5ad`.
  No script that prepares that file is in the repository.
- What the code does when pointed at the download directory: `_find_dataset_file` returns
  `sorted(p.glob("*.h5ad"))[0]` (`cellforge/autorun/runner.py:41-48`), which is the
  **10X001** file. Two other places point at 10X001: `scripts/inspect_adamson_case.py:12`
  hard-codes its md5 as the expected one, and a test fixture names the dataset
  `AdamsonWeissman2016_GSM2406675_10X001` (`tests/test_literature_retrieval.py:193`).
- The docs describe Adamson as "111k cells / 33k genes" (`docs/DATASETS.md:20`,
  `docs/MODELS.md:30`, `README.md:207`). No single file has that many cells (see the
  `describe` output in the run report), so the paper's number is not explained by the
  code. **Which file or combination produced the published PCC 0.9883 is not recoverable
  from the repository.**

## (b) Preprocessing

Prose only, `docs/DATASETS.md:70-79`:

- "The scPerturb releases are already normalised and harmonised" (line 72), then
  "Count normalisation: library-size normalise, log1p" (line 76). No target sum is given
  there. The only concrete call in the repository is `sc.pp.normalize_total(adata,
  target_sum=1e4)` followed by `sc.pp.log1p` in the legacy RAG data parser
  (`cellforge/legacy/rag_v1/dataparser.py:445-446`), which is not on the benchmark path.
- Gene filtering: "as distributed by scPerturb" (line 77). **No HVG count is specified
  anywhere.** HVG selection appears only as a suggested tool name in agent prompt
  templates (`cellforge/Method_Design/experts.py:225`), with no `n_top_genes`.
- Cell/gene filters: none on the benchmark path. `min_genes=200`, `min_cells=3` appear as
  default suggestions inside agent prompt templates
  (`cellforge/Method_Design/refinement.py:140,147`,
  `cellforge/Method_Design/graph_discussion.py:796,803`).
- Condition naming: scPerturb's `obs['perturbation']` (line 78); controls are "scPerturb's
  non-targeting / vehicle annotation" (line 79), expected to be labelled `control`,
  `non-targeting` or `NT` (`docs/DATASETS.md:146`). The split code looks for the column in
  the order `perturbation, perturbation_id, gene, target_gene, condition`
  (`cellforge/autorun/runner.py:64-70`).

## (c) Train / validation / test split

Implemented in `_prepare_perturbation_split`, `cellforge/autorun/runner.py:73-147`:

1. Unique perturbation labels are sorted, then shuffled with `random.Random(seed)`
   (lines 88, 94-95). Default seed 42 (`main.py:572`).
2. The first `round(n_labels * ood_ratio)` labels are held out as OOD (lines 97-101).
   Default `ood_ratio` 0.2 (`main.py:570`). **This is a by-perturbation holdout.**
3. The remaining (in-distribution) cells are shuffled and `val_ratio` of them (default
   0.1, `main.py:571`) become validation, the rest training (lines 110-123). **This is a
   by-cell split**: validation perturbations are all seen in training.
4. `train.h5ad`, `val.h5ad` and `split_manifest.json` (with the list of OOD perturbations)
   are written under `<dataset dir>/splits/ood20_val10_seed42/` (lines 125-146, 478-479).

Points that matter for a comparison:

- **The control label is not excluded from the shuffle** (line 88 takes every label), so
  the control group can land in the OOD holdout.
- **The OOD cells are never written to a file.** Only train and val are saved; nothing in
  the repository evaluates on the held-out perturbations.
- The score the autorun loop tracks is `val_pearson` on the by-cell validation set
  (`scripts/collect_score_paths.py:31`), produced by the generated script, not by
  repository code.
- The docs state "5-fold, 3 independent runs, `--split-seed 42`" and per-perturbation
  averaging (`docs/DATASETS.md:107-111`, `docs/RESULTS.md:29-31`). **No 5-fold code
  exists** in the repository; only the single 80/20 perturbation holdout above.
- No split files are shipped.

## (d) Evaluation metrics

**No implementation.** A search for `rank_genes_groups`, `pearsonr`, `r2_score`,
`mean_squared_error`, `top_20` and `val_pearson` finds only prompt text, a keyword list
in the legacy RAG code, and the CSV collector. The definitions available are:

- Task prompt, `main.py:41-47` (same text in `config.json:2`): MSE = "average squared
  difference between predicted and observed gene expression"; PCC = "linear correlation
  between predicted and observed profiles"; R2 = "proportion of variance in the observed
  gene expression that can be explained by the predicted values"; `_DE` variants = "same
  ... but computed specifically for genes identified as differentially expressed".
- `docs/RESULTS.md:44-53`: same table, plus DEG Recall.
- Averaging: "perturbation-centric — averaged over perturbations, not over cells"
  (`docs/RESULTS.md:31`).
- DE genes: "Wilcoxon rank-sum test, perturbed versus control", Benjamini-Hochberg,
  "adjusted p < 0.05 and |log2FC| > 0.5" (`docs/DATASETS.md:117-123`,
  `docs/RESULTS.md:60-61`).

Answers to the specific questions:

| Question | What the repository says |
|---|---|
| Mean expression or deltas? | The wording is "predicted and observed profiles" / "gene expression", i.e. expression, not delta from control. Not stated explicitly, and there is no code to settle it. |
| Per perturbation, then averaged? | Yes according to the docs (`docs/RESULTS.md:31`). Whether the profile is a pseudobulk mean or per-cell is not stated. |
| How are the top-20 DE genes chosen? | **They are not.** The repository never mentions a top-20 (or any top-k) set. The DE set is threshold-based: Wilcoxon, BH, padj < 0.05, abs(log2FC) > 0.5. |
| scanpy method / reference / `rankby_abs` / non-dropout filter | None specified. `scanpy.tl.rank_genes_groups` appears only as a tool name in agent prompts (`cellforge/Method_Design/experts.py:266` and others), with no arguments. |

A PCC of 0.9883 on Adamson is the size one gets when correlating full expression
profiles, where the control mean already explains most of the variance; this is an
inference from the number, not something the repository states.

## Baseline results or prediction files for Adamson

None. The only Adamson number is "CellForge — CPA-X: PCC 0.9883", with the baseline row
reading "Best baseline: lower" (`docs/RESULTS.md:69-74`). `docs/RESULTS.md:98-99` refers
to the paper for the full per-metric tables. There are no prediction files, checkpoints,
metric JSONs or split manifests in the repository; `data/` is gitignored and empty.

## Consequences for Gene-Mila

- A same-game comparison needs the paper's tables for the baseline numbers, and our own
  implementation of their metric definitions: expression-space MSE / PCC / R2 per
  perturbation then averaged, and the same three on the threshold DE set.
- Our `pearson_delta` is a different and harder quantity than their PCC; the two must not
  be put in the same column.
- Their published protocol (5-fold, 3 runs) cannot be replicated from the code. The
  closest reproducible thing is the seed-42 80/20 perturbation holdout from
  `runner.py:73-147`, which can be exported as a `--splits` JSON for `prepare_data.py`.
- Open items: which Adamson file(s) the paper used; whether metrics are on pseudobulk or
  per cell; whether expression or delta. These need the paper or the authors.
