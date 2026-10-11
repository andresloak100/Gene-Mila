# Norman 2019: plan for the clean test

The plan any agent (Claude, Astra or another) follows to run the lab on Norman 2019. Written 2026-10-11 from a reading
of the code at commit 220cc97 in a cloud container with no Norman data; every file:line refers to that commit, and
every statement about the Norman file itself is an assumption until the checks of section 2 have run on the Mac.
docs/LAB_STATE.md stays the record of what happened; this file is the protocol.

## 1. Goal and what counts as a clean test

The Adamson sealed set has been scored for dozens of finalists across about 30 runs (docs/LAB_STATE.md:46-49), so
Norman is the first fresh test of what Adamson suggested: the gain over the starting model comes from one feature
family, transfer of responses between related perturbations, and the Replogle 2022 K562 CRISPRi screen adds
information beyond it (leave-one-out stack +0.072 ± 0.020 over gene-set kNN, better for 34 of 50,
docs/LAB_STATE.md:81; scripted control with the screen 0.621 sealed against 0.593 without, docs/LAB_STATE.md:65,
137-141). Norman adds what Adamson could not test: two-gene combinations, and CRISPRa, the opposite modality to the
Replogle screen, so the same target's external response is expected to point the other way.

The test is clean only if four rules hold. (1) The split, code and checks of sections 3 to 5 are committed, with the
hash in docs/LAB_STATE.md, before any expression value of the Norman file is read; until then only obs labels, cell
counts, the var table and 500 control cells are read (section 2). (2) Every choice of model, feature, penalty,
selection rule or protocol uses visible data only: out-of-fold training plus visible validation (lab.py:363-374), or
the leave-one-out check of section 5. (3) The sealed set is read only through `QueryOracle` at the end of a run
(oracle.py:50-76; at most five queries, configs/default.toml:116-117); each labelled arm is one run whose sealed number
is reported whatever it is, nothing is re-run to improve it, and a repeat is a replicate beside the first, never a
replacement. (4) Arms are labelled by code version and knowledge files and never pooled (knowledge files:
benchmark/table.py:39-60, lab.py:47-56; code version: benchmark/table.py:213-215, which appends it only when the
runs in one table differ in code); means carry their spread, nothing inside the noise is claimed, all-gene PCC is
never a headline (docs/LAB_STATE.md:50-52).

## 2. Data

The file is `NormanWeissman2019_filtered.h5ad` from the scPerturb archive, Zenodo record 13350497 (real.py:15-19,
docs/LAB_STATE.md:217-221), to be downloaded into ~/Documents/Loak-documents/data_downloads (docs/LAB_STATE.md:29;
not downloaded yet, docs/LAB_STATE.md:220-221). Expected, to be checked: K562 CRISPRa, about 111,000 cells, about
237 labels in `obs['perturbation']` (about 105 single genes, about 131 pairs written like `CEBPE_KLF1`), controls
labelled `control`, raw counts in X.

What the ingest code expects: the condition column and control labels are detected automatically (real.py:95-107,
`CONTROL_LABELS` at real.py:32); symbols come from `var['gene_name']` or else var_names (real.py:112) with no flag for
another column (prepare_data.py:27-45), so a var of Ensembl ids only drops every label and fails at `np.stack` with an
unhelpful error (bundle.py:83-84); raw counts are detected and normalised (real.py:35-52, 116-118); a label is split on
`+ _ | , ;` and whitespace and keeps, in label order, the tokens that exactly match a measured gene (real.py:55-62),
keyed `A+B` (real.py:146). Running `parse_targets` shows three failures, the first two silent: `KLF1_CEBPE` is a
different perturbation from `CEBPE_KLF1`; `CEBPE_X` with X not a var name is pooled into the single CEBPE without a
warning; a lower-case label is dropped (recorded only in the manifest's `dropped_labels`, first 50, and
`n_dropped_labels`, real.py:196-197). The whole file is read into memory (real.py:92) and copied to normalise it
(real.py:45-51); I estimate a peak of several GB.

Read-only checks on the Mac, from the lab checkout; save the output to genemila_scale_logs/norman_check.txt:

```
cd ~/Documents/Loak-documents/gene-mila && source .venv/bin/activate
F=~/Documents/Loak-documents/data_downloads/NormanWeissman2019_filtered.h5ad
ls -l "$F"; md5 -q "$F"; sysctl -n hw.memsize; python prepare_data.py describe "$F"
python - "$F" <<'EOF'
import collections, re, sys; import numpy as np, pandas as pd, anndata as ad
from genemila.data.real import CONTROL_LABELS, parse_targets
a = ad.read_h5ad(sys.argv[1], backed="r")
print("cells x genes:", a.n_obs, a.n_vars, "| obs:", list(a.obs.columns), "| var:", list(a.var.columns))
for c in a.obs.columns:
    if a.obs[c].nunique() <= 10: print(" ", c, a.obs[c].astype(str).value_counts().to_dict())
genes = (a.var["gene_name"] if "gene_name" in a.var else a.var_names).astype(str).tolist()
print("symbols from gene_name:", "gene_name" in a.var, genes[:3], "| var_names", list(a.var_names[:3]),
      "| duplicated symbols:", len(genes) - len(set(genes)))
gs, cond = set(genes), a.obs["perturbation"].astype(object).fillna("unassigned").to_numpy(dtype=str)
n = {str(k): int(c) for k, c in zip(*np.unique(cond, return_counts=True))}
ctrl = [l for l in n if l.lower() in CONTROL_LABELS]
print("control", ctrl, sum(n[c] for c in ctrl), "cells | unassigned", n.get("unassigned", 0))
keys, partial, dropped = collections.defaultdict(list), [], []
for l in n:
    if l in ctrl or l == "unassigned": continue
    tg = parse_targets(l, gs)
    if not tg: dropped.append(l); continue
    if len(tg) < len([t for t in re.split(r"[+_|,;\s]+", l) if t]): partial.append(l)
    keys["+".join(sorted(tg))].append(l)
singles = {k for k in keys if "+" not in k}; pairs = [k for k in keys if "+" in k]
print("singles", len(singles), "| pairs", len(pairs), "| more than 2 genes", sum(k.count("+") > 1 for k in keys))
print("partial parses (merge silently today):", len(partial), partial[:15], "| dropped:", len(dropped), dropped[:15])
print("one gene set, several labels:", {k: v for k, v in keys.items() if len(v) > 1})
print("genes in pairs without a single:", sorted({g for k in pairs for g in k.split("+")} - singles))
cells = {k: sum(n[l] for l in v) for k, v in keys.items()}
print("cells per perturbation: min", min(cells.values(), default=None),
      "median", np.median(list(cells.values()) or [np.nan]), "| under 20:", sorted((c, k) for k, c in cells.items() if c < 20))
if "nperts" in a.obs:
    first = pd.Series(a.obs["nperts"].to_numpy()).groupby(cond).first()
    print("nperts disagrees with parse:", [l for k, v in keys.items() for l in v if first[l] != k.count("+") + 1][:15])
x = a.X[np.flatnonzero(np.isin(cond, ctrl))[:500]]; v = (x.toarray() if hasattr(x, "toarray") else np.asarray(x)).ravel(); v = v[v != 0]
print("X, 500 control cells: integers", bool(np.allclose(v, np.round(v))), "max", float(v.max()))
EOF
find ~/Documents ~/Downloads -iname '*split*' \( -name '*.json' -o -name '*.pkl' -o -name '*.csv' \) 2>/dev/null | head -50
```

The snippet was tested on a synthetic scPerturb-style file, not on Norman. Build only when: the control cells number at
least 2,300 (every detected control label is pooled, real.py:103-108, 125), so the 2,000 public and 300 evaluation
controls are drawn without overlap (below 2,050 the evaluation sample is the last 300 of the permutation and overlaps
the public one, real.py:130-134); symbols are found and none is duplicated (a duplicated target symbol keeps both
columns, real.py:154, and the Replogle build then refuses the bundle, external_screen.py:520-523); partial parses
and dropped labels are zero or each is understood and handled by item 1; "one gene set, several labels" lists only
reversed pairs or guides; no label names more than two genes; every perturbation has 20 cells or is noted (today it is
skipped without a record, real.py:160-161); `nperts`, if present, agrees; the control sample is integer-valued with a
maximum above 20 (real.py:40); and RAM leaves a wide margin over the file size, otherwise item 12 comes first. The
last command lists any CellForge split file on the Mac.

## 3. Split

Use our own split, grouped by gene and pre-registered, modelled on GEARS's "simulation" split. The default
`make_splits` permutes names, blind to shared genes (bundle.py:42-56): on synthetic labels (105 singles, 131 random
pairs; not Norman's structure; a simulation not committed to the repo, whose counts move with the random pairs),
seeds 0 to 2 put 17 to 27 singles in the sealed set, 12 to 23 of them with their gene in a training pair, so not
unseen.

The rule (item 2 of section 4):

1. Take every gene named by a kept perturbation, sorted; shuffle with seed 0; 70% training, 15% visible, 15% sealed.
2. A single goes to its gene's set; a pair goes to the more held-out set of its two genes (sealed, then visible, then
   training), so a held-out gene's single and every pair containing that gene are never trained on.
3. Of the pairs whose two genes are both training genes, a seeded 20% are held out, half visible and half sealed
   ("both singles seen"); the rest train.
4. Each held-out perturbation gets a category: `single`, or `pair_seen0/1/2` by how many of its genes have their single
   in training. Visible validation follows the same rule as sealed, so its mix of categories mirrors the sealed one.
5. `splits.json` records the rule, seed, fractions, gene-to-set map and categories, and `split_id` hashes the
   categories too. Labels only, never expression; never redrawn, even if a category is small; a category with fewer
   than 10 sealed perturbations is reported but not read.

On the same synthetic labels this gives 126 to 131 training perturbations (74 singles, about 55 pairs), 46 to 57
visible and 48 to 63 sealed, and only 2 to 8 `pair_seen0` pairs per held-out set (unverified: a re-check with other
random pairs gave 120 to 132 training perturbations and 1 to 13 `pair_seen0` pairs per set). CV folds are grouped
alike (item 7).

**What is unknown about CellForge's Norman split.** The repo holds only their reported Table 1 rows for Norman
(docs/results/cellforge_table1.json:29-45), described as the "unseen perturbation setting" (line 5); not their split
file or script, sizes, seed, whether they held out labels or genes, or whether singles and pairs were scored together.
The paper titles Norman "Gene knockout perturbation" (line 30) although it is CRISPRa, and on Adamson their split held
out guides, not genes (docs/LAB_STATE.md:94-95). Their Norman numbers stay "as reported, not comparable". If their
split turns up, it becomes a separate bundle `norman_cf`, built with `--splits` after item 13 and shown side by side
only. Without `--dataset-key`, the results table quotes the paper's Norman rows only for a dataset whose name
contains "norman" (benchmark/table.py:259; `calibrate` matches the bundle directory name, results_table.py:56); with
`--dataset-key norman` every dataset block of that table gets the Norman rows (benchmark/table.py:259), so it is
given Norman runs only.

## 4. Code changes, ranked

Items 1 to 4 change the bundle and land before the build; items 5 to 11 land before the first run. Each is gated on
the bundle (pairs, categories or a recorded modality) wherever it would otherwise change an Adamson run, and a test
asserts that Adamson's split, folds, features and selection are unchanged.

1. **Order-independent, strict labels.** real.py:141-149: sort the targets before forming the key (singles unchanged).
   Behind `--strict-labels`, on for Norman, drop and list a label with any token that is neither a measured gene nor a
   guide or control suffix (reuse external_screen.py:63 as external_screen.py:223-240 does) instead of pooling it into
   the single; always list partial parses in the manifest; same key rule in tools/count_target_cells.py:46-50. Test:
   add `G3_G2` and `G4_NOTAGENE` to `fake_screen` (tests/test_real_data_celleval.py:10-37); `G2+G3` pools both orders,
   G4 keeps only its own cells, the bad label is listed.
2. **Gene-grouped split with categories.** `make_gene_splits` next to `make_splits` (bundle.py:42-56), called at
   real.py:175-176, flags `--split-mode gene --gene-frac 0.7 0.15 0.15 --seen2-holdout 0.2` (prepare_data.py:27-45);
   `split_id_for` (bundle.py:37-39) hashes categories only when present. Test: no held-out gene's single or pair is in
   training, each pair sits in the more held-out set of its genes, categories match a recount, the same seed gives the
   same `split_id`, and an Adamson-style split keeps its `split_id`.
3. **Modality and per-perturbation metadata.** `--modality CRISPRa` into the manifest (real.py:194-197);
   private/perturbations.json with raw labels, every perturbation's n_cells, number of targets and category; record
   min_cells drops (real.py:160-161), all dropped labels, the source md5, the code commit, and a sampling seed apart
   from the split seed (real.py:126, 182). Held-out n_cells never go into the manifest, which every run's public
   directory receives (bundle.py:191-195). Test: the manifest has the modality and no held-out counts.
4. **Gene selection after the split.** Highly variable genes are ranked on 2,000 control cells only (real.py:151-155),
   which under CRISPRa can miss genes silent in control and switched on by activation. Behind
   `--gene-selection control+train`, select after the split (real.py:167-176) on control plus training cells, with
   sparse column moments, and record the method. Test: a gene induced only by a training perturbation is kept, one
   induced only by a held-out perturbation is not (unless it is a target).
5. **Additive baseline**, for bundles with pairs: `baseline_additive` beside the analytic baselines (lab.py:455-484),
   out-of-fold twin in `_cv_baseline` (lab.py:376-387). A pair is predicted as control mean plus its two singles'
   training deltas, a single missing from training replaced by the mean training single delta; a single as control
   mean plus that mean. Test: A and B in training, A+B held out gives exactly control + Δ_A + Δ_B.
6. **Per-category and paired scores** (protected paths, spec.py:17-21: a maintainer commit). `evaluate` returns
   per-perturbation values (evaluator.py:44-54, 82) but the oracle passes on only the means (oracle.py:60-64). Add
   per-category mean, sd and n, a `pearson_delta` that leaves out each perturbation's own targets, and a paired oracle
   query for two experiments (mean difference, paired SE, wins; aggregates only), and the same on visible scores
   (lab.py:345-349). Test: category means equal those of `per_perturbation`; no per-perturbation value leaves the
   oracle.
7. **Gene-grouped cross-validation folds.** Folds are random over names (pipeline.py:112-115). `cv_folds_of` returns
   predict and hide sets: a fold's view hides every training perturbation containing a gene of the fold and predicts
   those assigned to it (a pair goes to the lower fold of its genes); `cross_validate` (pipeline.py:131-143),
   `_cv_baseline` (lab.py:383) and the config hash (lab.py:501-506) follow. `cv_folds_of` is also called by
   tools/feature_audit.py:359, 997, tools/compact_model_curve.py:58 and tests (test_cv_selection.py:17-21,
   test_feature_audit.py:267, 447), which use each fold as the hidden set: a new return type breaks them, and a new
   function they do not call leaves them on the random folds, so update them too. Test: no view holds a perturbation
   sharing a gene with a single it predicts; Adamson's folds are unchanged.
8. **External screen: pairs and sign.** A pair's external row is the sum of its targets' rows, and exists only when
   every target has one. Today the first target in label order is taken: mock.py:320-324, 369-373 with 388-392,
   445-446 with 503-509, and tools/external_loo.py:369-373 (`n_cells_external`, line 431, becomes the minimum); `_unit`
   (mock.py:484-500) becomes per perturbation, since the unit vector of a sum is not the sum of unit vectors.
   (tools/learned_kernel_experiment.py:36 and tools/ceiling_analysis.py:56 also keep one target per perturbation, but
   both are hard-wired to Adamson files, lines 27 and 49, and are not on this plan's path.)
   `--modality` in tools/build_external_screen.py:122-146; external_screen.py:552-570 writes `source.modality`, a
   top-level `sign` (-1 when the screen's modality differs from the bundle's, else +1) and a description starting
   "CRISPRi screen", as the planner sees only its first 60 characters (lab.py:532). `external_direct` is multiplied by
   the sign before the `mean_response` fill (external_loo.py:192-200) and the zero fill (mock.py:323). Tests in
   tests/test_external_screen_control.py: templates and tool give the same row for a pair, [A,B] and [B,A] the same
   output, changing B's row changes it, single-gene outputs are unchanged.
9. **`similar` template.** mock.py:110 indexes `gene_corr[t, tq]`, pairing targets by position (A with C, B with D,
   never A with D) and raising IndexError for 2 against 3 targets (checked). Use the `np.ix_` block mean of
   mock.py:182. Test: the result does not depend on target order.
10. **Smoke test.** It samples `train_perts[:2] + evals[:2]` alphabetically (pipeline.py:262-263) and rejects a feature
    constant on them (pipeline.py:277-278), so a pair-only feature fails when no pair is sampled; leakage is checked
    on `train_perts[0]` only (pipeline.py:286-298). With pairs: sample a training and a held-out pair, check leakage
    on a training pair too, and check the output under swapped target order. Test: a feature zero on singles passes.
11. **Prompts, only for bundles with pairs or a recorded modality**, so Adamson's text stays byte-identical: modality
    and training singles and pairs in the DATASET line (lab.py:516-524; it already switches to "targets of 1 to N
    genes; M of K perturbations hit more than one gene" when any target list is longer than one, counted over every
    perturbation in targets.json, held-out ones included, lab.py:518-522); in the worker API (prompts.py:79-80),
    targets are an unordered set of 1 or 2 genes, use all and never `[0]`, keys look like `A+B`, a gene's single is the
    key equal to its name; feature "combination" (prompts.py:16, 31) becomes "feature-set combination"; an additivity area
    in `IDEA_BANK` (research_state.py:19-31); a scripted additive hypothesis and template keyed before "similar"
    (mock.py:539-554, 640-660), since such a text falls to the `variance` template today; modality-neutral wording in
    builtin.py:39-40, mock.py:27, 47, 72, 197, 221, 313, 357, 429-431, 640-683 and research_state.py:28; update
    docs/PROMPTS.md (line 277 gives only the "(single-gene targets)" form of the DATASET line, lines 281-282 say
    `targets` names the gene each perturbation knocks down; the script that generated the file, docs/PROMPTS.md:3-5,
    is not in the repo).
12. **Ingest conveniences.** `--max-eval-cells`, `--max-control-cells`, `--gene-name-key` (prepare_data.py:27-45 to
    real.py:71-74); a clear error when nothing survives (bundle.py:83-84); backed reading (real.py:92) if RAM is short.
13. **External split files**, only for `norman_cf` (real.py:201-237): canonicalise entries through the new parser and
    accept GEARS-style `A+ctrl`, which today matches nothing and is dropped silently (real.py:216-222); report
    unmatched entries and perturbations dropped for being absent (real.py:172-174).

## 5. Pre-specified checks, fixed before the data is opened

**Additive baseline.** `baseline_additive` (item 5) is recorded in every Norman run beside the existing baselines
(lab.py:463-466), and each arm's selected model is compared with it per category by the reading rule below; to my
recollection published Norman comparisons use it as the reference for pairs (Ahlmann-Eltze et al.; verify before
citing). The rerun Linear Regression and Random Forest rows encode one-hot perturbation ids (benchmark/table.py:
132-150), so every held-out pair gets the same profile; they stay CellForge's baselines, the additive one is the fair
reference for pairs.

**External-screen leave-one-out, protocol `norman_v1`**, added to tools/external_loo.py behind `--protocol norman_v1`
(recorded in the JSON) and committed before the dry run of section 6. Public data only: public.npz, targets.json,
gene_sets.json and replogle2022_k562.json built with `--min-cells 20`, the Norman rename table and `--modality
CRISPRi`, md5s recorded; private/ is never read (tests/test_external_loo.py:21, 42). Holding out p hides p and, when p
is a single, every training pair containing its gene, as on the sealed set. Primary score: `pearson_delta` over all
bundle genes (external_loo.py:67); secondary: the same without p's own targets; also reported, the median share of a
training perturbation's summed squared delta that lies on its targets. External rows follow item 8, with the sign
fixed at s = -1 inside `external_direct` before the fill (s = +1 only as a diagnostic). Predictors: `mean_response`;
`geneset_knn` (k = 5, Jaccard over the union of the targets' gene sets, external_loo.py:365); `additive_singles`
(Δ_A + Δ_B when both singles are available, else `geneset_knn`); signed `external_direct`; `external_knn` (k = 5);
`external_krr` (`LAMBDA_GRID`, `KRR_MIN_ROWS` = 3, external_loo.py:80-81); `stack_inbundle`, a ridge over
`mean_response`, `geneset_knn` and `additive_singles`; `external_stack`, the same plus the three external columns. The
alpha grid is 0.1 to 1e7 in decades (the Adamson second-look grid), never widened afterwards. The one primary
comparison is `external_stack` against `stack_inbundle`, paired: no best-of-two as at external_loo.py:536, and none
of the "added after the first reading" text (external_loo.py:25-37, 588-607, 689-690). Gate: read only if at least
half the training perturbations and at least 10 training singles have an external row, else report inconclusive.
Secondary, not the verdict: every predictor against `mean_response` and `geneset_knn`; strata for singles, pairs, and
targets expressed or silent in public controls (nonzero in at least 5% of cells); median same-target agreement over
singles without the target gene, expected below 0 (rewording external_loo.py:527-531); the s = +1 `external_direct`,
expected below `mean_response`. Cost grows as about n⁴ × genes (external_loo.py:344-348, 389-397) and a synthetic
case of Adamson's size, 50 × 2,055, took about 12 s in a 4-core cloud container (external_loo.py:39-41,
docs/LAB_STATE.md:157-158; no Mac timing is recorded), so I extrapolate 10 to 20 minutes at n ≈ 130 (2.6⁴ × 12 s is
about 9 minutes before the added columns).

**Reading rule, as on Adamson.** A gain counts only if the mean paired gain exceeds twice its paired standard error and
the better side wins on more than half the perturbations (external_loo.py:543-547). It applies to the leave-one-out
primary comparison, to each arm against the additive baseline, and to the sealed comparison of N2 (scripted control
with the screen) against N1 (without), on each run's selected model, pooled `pearson_delta`, with the per-category
table beside it. Expected direction, fixed now: N2 above N1, pooled and on singles. When the leave-one-out and sealed
readings agree, the Adamson finding is confirmed; a disagreement is reported as one.

## 6. Run order on the Mac

1. Free: land items 1 to 11 and `norman_v1` with `python -m pytest -q` passing; record the commit hash in LAB_STATE.
2. Free: download the file, run section 2, save the output; if a check fails, revise items 1 or 12 and stop there.
3. Free: build the bundle (curated knowledge here, so the manifest lists it, bundle.py:136; a file added later is an
   external arm, bundle.py:162-173; a rebuild deletes data/norman and anything added since, bundle.py:78-79), then
   copy splits.json and manifest.json to docs/results/norman_splits.json and norman_manifest.json, and commit them:
   `python prepare_data.py h5ad --name norman --h5ad "$F" --knowledge data/raw/knowledge --hvg 2000 --min-cells 20 --seed 0 --split-mode gene --strict-labels --gene-selection control+train --modality CRISPRa`
4. Free: run N1, the scripted control, before any Replogle file is in the bundle, since `export_public` copies every
   knowledge file into each run (bundle.py:189-190):
   `python run_research.py --minutes 20 --workers 4 --dataset norman --worker-provider mock --planner-provider scripted --run-dir runs/norman_control_w4_r0`
5. Free: build the Norman rename table (bundle symbol = Replogle symbol, matched by Ensembl id; nothing in the repo
   builds it; `check_aliases` refuses clashes, external_screen.py:250-264), apply the gate of section 5 to the counts of
   `python tools/build_external_screen.py --h5ad ~/Documents/Loak-documents/data_downloads/ReplogleWeissman2022_K562_gwps.h5ad --bundle data/norman --name replogle2022_k562 --min-cells 20 --alias-file <table> --modality CRISPRi --dry-run`,
   then build without `--dry-run`.
6. Free: run the leave-one-out (the protocol fixes its own grid, so no `--alpha-grid`) and push its report:
   `python tools/external_loo.py --bundle data/norman --knowledge replogle2022_k562 --protocol norman_v1 --out ~/Documents/Loak-documents/genemila_scale_logs/external_loo_norman_v1.md`
7. Free: run N2, as N1 with `--run-dir runs/norman_control_replogle_w4_r0`; it records the file (lab.py:49-56).
8. Paid: a DeepSeek-planned agent arm with the screen (N3) starts only on Andres's own typed words in the build thread
   and stays under the cap in docs/LAB_STATE.md:41-45 ($34 ledger total, `--set budget.cumulative_usd.deepseek=34`).
   At 04:03 UTC on 11 Oct the ledger was $31.78 with run B (about $1.20) planned (docs/LAB_STATE.md:5, 42,
   198-205); past runs cost $1.13 to $1.28, so if what is left will not cover a full run, ask Andres rather than start
   a short one.
9. Free: render the results table with `--dataset-key norman`, Norman runs only and an `--out` other than the default,
   which would overwrite the committed Adamson docs/results/results_table.md and .json (results_table.py:34, 49-50);
   then the per-category tables, and update LAB_STATE.

## 7. Open questions

- Who takes Norman, Claude or Astra (docs/LAB_STATE.md:214); every assumption of section 2 (the answers may change
  items 1, 4 and 12); whether CellForge's Norman split, or the script behind the Adamson seed-42 split, exists.
- How many Norman targets have a Replogle row. CRISPRa targets silent in K562 may be absent from a screen of expressed
  genes; if the gate fails, this file cannot test the screen on Norman, and the repo has no CRISPRa screen.
- Whether to try Adamson's agent features on Norman: `warm_start` refuses another dataset (lab.py:206-208), so this
  needs a new mechanism and would be its own arm.
- Whether 300 evaluation controls (real.py:74) suffice for cell-eval on Norman, and whether cell-eval accepts `+` in
  labels (untested); whether selection should weight categories (fixed here as the pooled visible mean, as on Adamson).

## 8. Log: steps 2 and 3 on the Mac (11 Oct 2026)

Andres chose Claude for Norman (build-thread card, 12:02 UTC) and typed "download norman" (12:04 UTC). Plan commit
at the time: 02e7021. Nothing below read an expression value beyond the 500 control cells section 2 allows.

- **File:** NormanWeissman2019_filtered.h5ad, Zenodo 13350497, 698,680,199 bytes, md5
  c870e6967d91c017d9da827bab183cd6 (matches Zenodo). 111,445 cells, 33,694 genes; 237 labels in
  obs['perturbation'] (102 singles, 129 pairs, none with three genes); 11,855 `control` cells; symbols from var_names
  (var carries `ensemble_id`, no `gene_name`), no duplicates; cells per perturbation minimum 54, median 358; X holds
  integers. Every section 2 check passes (docs/results/norman_check.txt). No CellForge Norman split exists on the Mac.
- **Bundle** (section 6 step 3's exact command, 52 s): 231 perturbations, 2,083 genes, 2,000 public controls,
  split_a391fa9e7b4eccb7, modality CRISPRa. Training 112 (71 singles, 41 pairs); visible validation 63 (15 singles;
  pairs 8 pair_seen0, 35 pair_seen1, 5 pair_seen2); sealed 56 (16 singles; pairs 8, 27, 5). No held-out single's
  gene appears in any training perturbation. The sealed pair_seen0 (8) and pair_seen2 (5) categories are under 10,
  so they are reported and not read (section 5).

Decisions on what the plan did not anticipate, made before any score on this bundle existed:

1. **Old gene symbols.** C19orf26, C3orf72 and KIAA1804 are not in var (current names CBARP, FOXL2NB, MAP3K21), so
   those three singles drop, and the pairs C3orf72_FOXL2 and TGFBR2_C19orf26 drop under `--strict-labels` (listed in
   the manifest's strict_dropped_labels, never pooled into FOXL2 or TGFBR2). Kept as built: five of 236 labels, and
   an ingest alias step would be new code after the protocol was fixed. A later rebuild that recovers them is a new
   bundle and split, never mixed with this one.
2. **Cell-quality flags.** good_coverage is False for 6,938 cells and number_of_cells is 2 or more for 13,339; the
   ingest uses neither, so they are in the pseudobulks, as pre-specified. Every comparison of this test (N1 against
   N2, the norman_v1 leave-one-out) is within one bundle, so multiplets dilute both sides alike. A filtered bundle
   (good_coverage and number_of_cells == 1) is a sensitivity arm after N2, labelled as such, never a replacement.
3. **perturbation_type** reads `CRISPR`; the modality the code uses is the manifest's CRISPRa from `--modality`.

Replogle coverage, from the labels and var tables only: 85 of the 102 Norman target genes have a Replogle row by
symbol (Ensembl ids add none; the 17 without are ATL1, CDKN1A, CKS1B, CNNM4, COL1A1, IGDCC3, MAML2, MAP2K6, PRTG,
PTPN13, RUNX1T1, S1PR2, SLC4A1, SLC6A9, TGFBR2, UBASH3A, UBASH3B, mostly silent in K562); 139 of 2,083 bundle genes
lack a symbol match and 84 of them match by Ensembl id (rename table, 84 aliases). The section 5 gate is judged on
step 5's dry-run counts for training perturbations.
