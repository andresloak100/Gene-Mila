# Comparing systems on "feature + linear model = result"

Written 2026-10-16 for Andres and his ML collaborator, claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41).
It is step 2 of the paper proposal in draft [PR #38](https://github.com/andresloak100/Gene-Mila/pull/38)
([`docs/archive/plans/PAPER_FRAMEWORK_PROPOSAL.md`](archive/plans/PAPER_FRAMEWORK_PROPOSAL.md),
archived once its sections became GOAL_CRITERIA, this protocol and ROADMAP). PR #38 says why we compare systems. This file says how. Nothing here has run on real data.
Commands and criteria follow `tools/feature_compare.py` with its review fixes (commit `2136bf3`) and the task
package of commit `dd9a2d8`; if either changes, its own docstring wins over this file.
**Unverified** marks every statement that could not be checked from this repository or the local clones.

## 1. Purpose and the claim

- The unit is the **feature**: a small plugin `compute(ctx, perts, params) -> (len(perts), n_genes, dim)`
  (`genemila/features/api.py:1-14`). The model is fixed: one ridge regression over (perturbation, gene) rows.
  A system is good here when its features make that fixed ridge predict better.
- Each system (an "arm") searches for features on the same public data. It hands back feature files.
  `tools/feature_compare.py` then scores every arm the same way: one **system row** (parent + all the arm's
  features) and one **add-one row** per feature (parent + that feature alone).
- **Headline numbers come only from the fresh test**: labels held outside the Mac by a separate evaluator,
  scored once on frozen predictions ([`docs/FROZEN_TEST_PLAN.md`](FROZEN_TEST_PLAN.md), claim
  [#22](https://github.com/andresloak100/Gene-Mila/issues/22)). That evaluator does not exist yet.
- **Development tiers only screen.** They choose which candidates go to the fresh test. They never make a claim.

| tier | what it is | who saw it before scoring | use |
|---|---|---|---|
| OOF | training perturbations, scored out of fold (gene-grouped folds on Norman) | every arm: every arm selects on OOF scores of the same labels, whatever the fold seed | screen, and parity check |
| V (opt-in `--with-val1`) | visible validation, fit on all training perturbations | lab arms A1/A2 (the lab selects on V + OOF, `genemila/lab.py:426-437`); not the package arms | first unselected number for package arms; optimistic for lab arms (the tool marks their V verdicts "optimistic: source selected on val1") |
| S | sealed set behind the oracle | nobody's features, but people have read it many times | indicative only ("worn") |
| F | fresh test, outside the Mac | nobody | the paper's numbers |

## 2. Arms

Every arm starts from the same parent P0: the lab's starting model, i.e. the built-ins `control_mean`,
`mean_response`, `is_target`, plus `additive_response` on a bundle with pairs (`genemila/features/registry.py:12-16`).
A second parent P1 (a strong known set, for example N2's selected features) tests "adds beyond what is known".

| arm | what runs | cost | status |
|---|---|---|---|
| **A0** classic | Unperturbed, mean response, additive rule (Norman), ridge on P0, linear regression and random forest reruns (`genemila/benchmark/table.py:132-165`) | free | partly run (section 5) |
| **A1** our multi-agent lab | `run_research.py`, DeepSeek planner `deepseek-v4-pro`, 4 `deepseek-flash` workers, 20 min, start from P0, knowledge file `replogle2022_k562` (B2 settings; `block_b2_run.sh` checks its md5 `d9eff528…`) | paid; Andres's go per run | B2 is an A1 instance on Norman; B1 is not (it warm-started from N2) |
| **A2** one worker | the same with `--workers 1` (block B4, draft [PR #39](https://github.com/andresloak100/Gene-Mila/pull/39)) | paid; Andres's go | runs reported in HANDOFF.md section 1 under PR #39 (15 Oct); results not in the repository |
| **A3** autoresearch-style coding agent | Claude Code or Codex on the task package (section 4), `program.md` loop, one `features/` folder, fixed `evaluate.py` | LLM paid by someone (decision 2); paid, so Andres's go per run, inside the block of decision 6 | not run |
| **A4** Biomni | Biomni's A1 agent on the same task package | DeepSeek; about $0.5–2 per run at ledger prices (estimate, **unverified**); Andres's go per run, inside the block of decision 6; the runner writes `provider="deepseek"` ledger rows, so the cap counts them | not run |
| **A5** CellForge | C2 / C1 / C0 below | C2 free; C1 about $0.2 per debate (estimate); C0 needs a GPU | not run |
| **A6** STATE | its own model, scored by our evaluator: an outcome row only | GPU | not feasible here |

**A3 autoresearch-style.** One coding agent with a shell works inside a copy of the task package. It may change
one feature file per step and run `python evaluate.py`. The script keeps or discards the change itself
(OOF pearson_delta, with a noise rule). It works like karpathy/autoresearch: fixed harness, one editable surface,
`results.tsv`, "never stop" until the wall clock kills it. The arm returns `runs/kept/features/`, the state its
keep rule accepted (`evaluate.py` copies `features/` there on a keep). The working `features/` may hold an edit
that was never evaluated or is about to be discarded, so it is kept as an artefact and never scored.

**A4 Biomni** (`snap-stanford/Biomni`, read locally; facts from its code unless marked).
- Biomni is a general coding agent with tool retrieval. It has no Perturb-seq prediction tool. Here it is
  one more agent that writes feature files on the package. It is not a model to compare as such.
- Run it with `A1(path=..., llm="deepseek-v4-pro", source="OpenAI", expected_data_lake_files=[])` and the
  environment variables `OPENAI_BASE_URL=https://api.deepseek.com/v1` and `OPENAI_API_KEY`. `source` must be
  explicit: a model name containing "deepseek" is otherwise routed to Ollama (`biomni/llm.py:75-89`).
  This route was tested only against a local mock server.
- `expected_data_lake_files=[]` skips the data lake download (about 15 GB on S3). A run with the data lake
  is a separate arm ("B-native"), optional.
- **Risks.** (1) Agent code runs with `exec()` inside Biomni's own process (`biomni/tool/support_tools.py:31`),
  with the user's rights and full network. On the Mac it could read `data/*/private` or download the source
  screens. It must run in a container that mounts only the package. (2) Two routes print the key:
  `BIOMNI_CUSTOM_API_KEY` (the full key, through the config print at `biomni/agent/a1.py:124-135`) and
  `api_key=` (last 4 characters, `a1.py:145`). Use neither. (3) Agent code shares the process: deleting the key
  from `os.environ` does not hide it (it stays in the client object and in `/proc/self/environ`). So the real key
  never enters the container: a host-side proxy to api.deepseek.com adds the key and counts tokens, and the
  container gets a dummy key and a network route to that proxy only. (4) There is no token count and no
  budget cap; the recursion limit is 500 (`a1.py:1774`) and the context is never trimmed. The runner must count
  tokens and stop at a cap. (5) Whether `deepseek-v4-pro` accepts Biomni's consecutive assistant messages is
  **unverified** (one paid call would settle it).
- Wall clock: Biomni stops at `<solution>`, not by a timer. Its budget is therefore a step and dollar cap,
  reported as steps and tokens, and the "same wall clock" control holds only approximately.
- PR #38 says CellForge reports that Biomni produced no executable code on Norman. This is **unverified**
  (section 8).

**A5 CellForge** (`gersteinlab/CellForge`, read locally).
- CellForge produces a deep model and a training script, not features. Its docs say it ships no weights
  (`README.md:43-44`). One end-to-end run takes 4–8 GPU-hours (`README.md:41`).
- In the released code the plan that reaches code generation is built from fixed templates. The expert debate
  is saved as transcripts but does not change the plan (per our reading of `graph_discussion.py` and
  `refinement.py`; not run). This may differ from the code behind the paper (**unverified**).
- So three versions are possible, each its own arm and label:
  - **C2, feasible now, free.** We write 3–4 plugins from CellForge's design ideas: gene-network propagation,
    pathway membership, perturbation-embedding similarity, and a pair-interaction term (Norman). Label:
    "CellForge ideas, translated by us".
  - **C1, feasible, paid, needs a patch.** Run only its Method Design stage on DeepSeek, with the prompt at
    `cellforge/Method_Design/expert_discussion.py:78` changed from "model architecture" to "features f(p, g) for
    a fixed ridge", online retrieval off. Harvest the transcripts; one coding agent turns each proposed signal
    into a plugin. Label: "CellForge debate adapted to features". CellForge does not write to our ledger, so
    spend is capped by its token budget setting and recorded by hand.
  - **C0, needs a GPU.** Unmodified CellForge on a training-only `.h5ad`; its predictions for our held-out
    perturbations scored by our evaluator. This is an outcome row, not a feature row.
- Not feasible: scoring "CellForge's features" directly. No CellForge code produces features on our data.

**A6 STATE** (Arc Institute). Needs Python 3.11/3.12 and a CUDA GPU (per the clone; CPU training **unverified**).
Its default perturbation encoding is one-hot, which gives an unseen gene nothing to use; a
`perturbation_features_file` (for example ESM2 gene embeddings) is required. It enters only as an outcome row
(its predictions through our evaluator). "STATE or ESM2 embedding as a feature" would be its own arm and needs
the embedding file as a knowledge file.

## 3. Fairness controls

1. **Same data.** Same bundle and `split_id`. The task package carries the same public data the lab's
   experiments receive (same `public.npz`, same knowledge files). A system that brings its own knowledge (for
   example Biomni's data lake) is a separate arm.
2. **Same parent.** P0 for every arm; P1 as a second reading. The parent cannot be removed.
3. **Same budget.** Same wall clock (20 min, as B2 and B4) and the same dollar cap. Every paid call is counted
   in the shared ledger. The lab does this itself; the Biomni runner must call `SpendLedger.add`
   (`genemila/llm.py:45-68`); for Claude Code or Codex the spend is recorded by hand from their usage report.
   The same LLM (`deepseek-v4-pro`) wherever the system allows it.
4. **Same final scoring.** Every arm's features are scored by `tools/feature_compare.py` with the same
   ridge, alpha grid, honest out-of-fold alpha choice, fold seeds (101, 102, 103 by default) and metrics.
   Numbers a system reports about itself are kept apart.
5. **Repeats.** At least 3 independent searches per arm, reported as mean ± sd. A coding agent has no seed: a
   repeat is a fresh copy of the package and a fresh session. The arm rule of `tools/arm_reading.py:61-65`
   reads an arm against its parent.
6. **No cross-arm contamination.** No arm sees another arm's features, transcripts or results until all arms
   have run. The package contains none of our features or prompts.
7. **Isolation of foreign agents (A3, A4, A5-C1).** Only the package folder is mounted, never the lab checkout.
   Network only to the LLM endpoint. Transcripts are kept and checked for network calls and for reads outside
   the package. Without a container this control does not hold, and the arm must wait.
8. **On the Mac.** First `python handoff_state.py --fetch` and `pgrep -fl run_research.py`. Never run beside a
   paid run or the worker-scaling driver. Run CPU-heavy tools with `nice -n 19`. One paid run at a time.
9. **Embedded labels.** A foreign file could paste training labels into its source and lift its OOF score.
   `tools/task_package/literal.py` caps literals and bans decoding helpers. That makes it expensive, not
   impossible. So OOF alone never decides anything about a foreign file beyond screening (section 6.2 adds a
   V check), and only F makes a claim.

## 4. Exact commands

Run from a clone that is not the main checkout. `data/` and `runs/` exist only in the main checkout, so they are
read through `<MAIN>`, its absolute path (as in `docs/PLAN_AFTER_N4.md`); nothing is written there except the lab's
own run directories. Write paths after `=` with `$HOME`, not `~`: zsh, the Mac's shell, does not expand `~` after
`=`. Never print, echo or log a key. `$API_KEY` stays in the caller's environment (AGENTS.md, "Secrets").

```
# 0. On the Mac, always first. If run_research.py is running, stop here.
python handoff_state.py --fetch
pgrep -fl run_research.py

# 1. Task package, once per bundle, outside the checkout
python tools/export_task_package.py --data <MAIN>/data/norman --out ~/gm_packages/norman

# 2. One working copy per search of a package arm (A3, A4): cp -R, never edit the original
cp -R ~/gm_packages/norman ~/gm_work/norman_A3_r0
```

**A3, launching a coding agent** (only after the payer decision; flags as in the installed CLI, **unverified**):
```
cd ~/gm_work/norman_A3_r0          # inside the no-network container
timeout --kill-after=30 20m claude -p "$(cat program.md)"     # or: codex exec "$(cat program.md)"
```
macOS has no `timeout` by default; Homebrew's coreutils installs it as `gtimeout` (**unverified** on the Mac).
The final state is `runs/kept/features/` at the kill (not `features/`, section 2); also keep `features/`,
`results.tsv`, `runs/` and the transcript.

**A4, Biomni runner outline** (a small script in its own environment, not lab code; not written yet):
1. On the host, outside the container: a forwarding proxy to api.deepseek.com, started with
   `DEEPSEEK_API_KEY="$API_KEY"`. It adds the Authorization header, adds up input, cache-hit and output tokens,
   prices them with `configs/default.toml` `[pricing."deepseek-v4-pro"]`, writes each call to the shared ledger
   (`SpendLedger.add`) and refuses calls past the cap.
2. In the container: `OPENAI_API_KEY=dummy OPENAI_BASE_URL=<proxy URL>/v1 python run_biomni.py`, with network to
   the proxy only. It builds `A1(path=<package>, llm="deepseek-v4-pro", source="OpenAI", expected_data_lake_files=[])`.
3. `agent.go(<program.md text>)`; the agent runs `evaluate.py` from Bash only.
4. Save the transcript and scan it for the real key before keeping it; hand back `runs/kept/features/`.

**A1 and A2, the lab** (paid; Andres's go for each run; run by whoever owns the Mac runs, flags as in B2's
`block_b2_run.sh`; `<cap>` is the block's cap; `data/norman/knowledge/` must hold `replogle2022_k562` only, as for B2):
```
DEEPSEEK_API_KEY="$API_KEY" python run_research.py --minutes 20 --workers 4 --dataset norman \
  --planner-provider deepseek --planner-model deepseek-v4-pro \
  --worker-provider deepseek --worker-model deepseek-flash --no-watchdog \
  --run-dir <MAIN>/runs/<name> --set run.seed=<S> --set run.data_dir=<MAIN>/data/norman \
  --set budget.ledger=<MAIN>/runs/spend_ledger.sqlite --set budget.cumulative_usd.deepseek=<cap> \
  --set budget.max_total_usd=1.0 --set budget.max_planner_usd=1.5
```
A2 is the same with `--workers 1` (PR #39). After the start, check `config.json` in the run directory
(`run.external_knowledge` must read `['replogle2022_k562']`): `--set` accepts misspelled keys silently.

**Scoring every arm** (free; `nice -n 19` on the Mac):
```
nice -n 19 python tools/feature_compare.py --data <MAIN>/data/norman --out $HOME/gm_compare/norman_p0 \
  --parent builtin \
  --source-run A1_r0=<MAIN>/runs/norman_ds_addstart_w4_r0 --source-run A2_r0=<MAIN>/runs/norman_ds_addstart_w1_r0 \
  --source A3_r0=$HOME/gm_work/norman_A3_r0/runs/kept/features \
  --source A4_r0=$HOME/gm_work/norman_A4_r0/runs/kept/features \
  --source A5_C2=<folder of the translated plugins> \
  --fold-seeds 101,102,103 --null-reps 999
```
The report is `feature_compare.md` and `feature_compare.json` in `--out`. For parent P1 use `--parent-run <run>`
and a second `--out`. Run every search seed of every arm in one call, so all rows share one parent scoring; the
families stay per source (section 6), so one call does not change any verdict.

**Null replicates.** The null p is never below 1/(B+1). The family-wise p is a max-gain step-down over a
source's add-one rows (section 6), and every family, a system row or a single candidate included, needs B ≥ 999
(floor 0.001): at 19 replicates the floor 1/20 would equal the 0.05 cutoff, and a pass would mean only that no
replicate exceeded the observed gain (`docs/ROADMAP.md`, section 1). 999 is the tool's default and the figure here. The report lists each source's family size after deduplication; a verdict "null too
coarse for a family of m" means rerun with the B it names, not that the feature failed. The null refits the whole
procedure per replicate, so B drives the run time: the tool prints an estimate, measured on its first replicate,
before it starts.

**Visible validation.** Add `--with-val1` only after Andres allows it (section 7). It makes V the deciding tier
for every row, and the lab arms selected on V, so their V verdicts read "optimistic" and screen nothing. With
`--with-val1`, run the same command a second time without it (another `--out`): the lab arms' screening verdicts
come from that OOF-decided call, the package arms' from the V-decided one.

## 5. The metrics table

### Definitions

All metrics compare predicted with true mean expression per perturbation (log1p of counts per 10k).
"Δ" is expression minus the public control mean. "Top-20 |Δ|" = the 20 genes with the largest true |Δ| of that
perturbation (`evaluator.py:63`). File paths are under `genemila/benchmark/`.

| # | metric | definition | code | needs cells |
|---|---|---|---|---|
| M1 | pearson_delta (primary) | mean over perturbations of Pearson(pred Δ, true Δ), all genes; 0 if a vector is constant | `evaluator.py:25-29,65,83-84` | no |
| M2 | pearson_delta_nontarget | M1 without the perturbation's own target genes (both for a pair) | `evaluator.py:73-77` | no |
| M3 | MSE | mean of (pred − true)² over all (perturbation, gene) entries; equals CellForge's MSE | `evaluator.py:81`; `comparable.py:45` | no |
| M4 | mse_top | MSE on the top-20 \|Δ\| genes, per perturbation, averaged | `evaluator.py:68` | no |
| M5 | r2_top | R² of expression on the top-20 \|Δ\| genes | `evaluator.py:69` | no |
| M6 | pearson_delta_top | Pearson of Δ on the top-20 \|Δ\| genes | `evaluator.py:66` | no |
| M7 | direction_acc_top | share of the top-20 \|Δ\| genes with the right sign of Δ (a predicted 0 counts as wrong) | `evaluator.py:67` | no |
| M8 | CellForge MSE_DE / PCC_DE / R²_DE | on the top-20 genes by Wilcoxon \|z\| from held-out cells (\|log2FC\| breaks ties) | `reference.py:61-70`; `comparable.py:41-58` | yes |
| M9 | VCWorld DE-F1, DIR accuracy | DE = BH p ≤ 0.05 and \|log2FC\| ≥ 0.25; pooled over (perturbation, gene) pairs | `reference.py:71`; `comparable.py:61-86` | yes |
| M10 | cell-eval (overlap_at_N, discrimination_score_l1, ...) | Arc's cell-eval on a point-mass prediction anchored on held-out controls | `celleval.py:71-92` | yes |
| M11 | by category | single, pair_seen0/1/2 (Norman); a category under 3 perturbations reports n only | `evaluator.py:124-158` | no |
| M12 | delta scale ratio | mean \|pred Δ\| / mean \|true Δ\|; shows shrinkage that M1 cannot see | `evaluator.py:104` (rounded diagnostic) | no |

- `feature_compare.py` reports M1–M7 and M12 (M12 computed unrounded from the predictions). M8–M10 need held-out
  cells, so they exist only for V, S and F, never for OOF. M11 for OOF depends on the fold seed.
- **Three "top-20" definitions exist.** M4–M7 rank by |true Δ|; M8 ranks by Wilcoxon |z|; the note in
  `docs/results/cellforge_table1.json` says CellForge ranks by |log fold change|. They give different numbers:
  for the additive rule on Norman's sealed set, MSE on the top 20 is 0.1100 by |Δ| and 0.1016 by Wilcoxon. Every
  DE column names its ranking.
- Statistics for every row against a named reference: n; paired Δ ± SE with SE inflated by the gene-overlap ratio
  (`tools/sealed_reading.py:97-130`); wins/ties; the reading rule (gain > 2·SE and wins > n/2,
  `evaluator.py:172-181`); over search seeds, mean ± sd and the arm rule (`tools/arm_reading.py:61-65`).

### Template, pre-filled with lab-reported numbers

Every number below was checked in the cited file on 2026-10-16. They were made by the lab during its runs
(alpha chosen on V + OOF at the run's own fold seed). They are **not** comparable with `feature_compare.py`
rows, which use an honest OOF alpha and fold seeds 101–103. Tier letters as in section 1.

**Norman**, split `split_a391fa9e7b4eccb7`: 112 train, 63 visible, 56 sealed
(`docs/results/norman_manifest.json`). Sources: N1 = `docs/mac/norman_control_w4_r0/summary.json`;
N2 = `docs/mac/norman_control_replogle_w4_r0/summary.json`; N4 = `docs/mac/norman_ds_from_n2_w4_r0/summary.json`;
b1 = branch `claude/mac-b1-2026-10-11`, b2 = branch `claude/mac-b2-2026-10-11` (not merged), files
`docs/results/norman_b{1,2}_{arm_vs_start,combined_vs_additive}.{md,json}` and `docs/mac/<run>/summary.json`;
paired values and the N1/N2/N4 S M2 from `docs/results/norman_sealed_reading.md` and
`norman_n4_sealed_reading.md`; the additive rule's S M2 and M4/M5/M7, and the combined rows' S M1–M7, from the
b1/b2 `combined_vs_additive.json`.

| system | S M1 | S M2 | S M3 | S M4 / M5 / M7 | S M8 MSE/PCC/R² | S paired vs additive (wins/56) | V M1 | OOF M1 (fold seed) |
|---|---|---|---|---|---|---|---|---|
| Additive rule, EXP_0003 (N1) | 0.7126 | 0.7107 | 0.0059 | 0.1100 / 0.8500 / 0.900 | 0.1016 / 0.9412 / 0.8463 | reference | 0.7259 | 0.5461 (0) |
| N1 no-LLM control, EXP_0076 | 0.7170 | 0.706 | 0.0055 | – | 0.1186 / 0.9335 / 0.8328 | +0.004 ± 0.008 (28) | 0.7749 | 0.5654 (0) |
| N2 control + Replogle, EXP_0198 | 0.7188 | 0.708 | 0.0054 | – | 0.1104 / 0.9374 / 0.8424 | +0.006 ± 0.007 (32) | 0.7746 | 0.5678 (0) |
| N4, EXP_0790 (continued from N2; lost its planner; own arm) | 0.7264 | 0.716 | 0.0055 | – | 0.1285 / 0.9277 / 0.8190 | +0.014 ± 0.008 (37) | 0.7770 | 0.5730 (0) |
| B1 arm, 3 runs, continued from N2 (b1; not A1) | 0.7188 ± 0.0073 | – | – | – | 0.1077 ± 0.0068 / 0.9387 ± 0.0034 / 0.8465 ± 0.0083 | – | 0.7769 / 0.7815 / 0.7763 | 0.5854 / 0.6061 / 0.5765 (1/2/3) |
| B1 combined (delivered model, continued from N2, b1) | 0.7229 | 0.7131 | 0.0052 | 0.1144 / 0.8562 / 0.9045 | not computed | +0.010 ± 0.007 (36) | 0.7801 | – |
| B2 arm, runs r0/r2/r3, from P0 (b2; an A1 instance) | 0.7239 ± 0.0054 | – | – | – | 0.1196 ± 0.0217 / 0.9314 ± 0.0109 / 0.8283 ± 0.0269 | – | 0.7344 / 0.7326 / 0.7735 | 0.5681 / 0.6045 / 0.5799 (0/2/3) |
| B2 combined (b2) | 0.7269 | 0.7196 | 0.0053 | 0.1234 / 0.8466 / 0.9107 | not computed | +0.014 ± 0.003 (45) | 0.7505 | – |
| CellForge-Models, reported, other split: **not comparable** | – | – | 0.0034 | – | 0.1736 / 0.8109 / 0.5975 (their top-20) | – | – | – |
| A2 one worker, A3, A4, A5 (C0/C1/C2), A6 | | | | | | | | |

The additive rule's OOF M1 alone moves with the fold seed: 0.5461, 0.5600, 0.5781, 0.5523 under seeds 0–3 (the
baselines in N1 and the three b1 run summaries). That spread, about 0.03, is larger than most feature gains.

**Adamson**, split `split_450515be1a0d8d2e`: 50 train, 17 visible, 21 sealed (`README.md:69`); the sealed set is
worn. M2 and M11 do not exist on the sealed set here. Sources: R = `docs/mac/control_replogle_w4_r0/summary.json`;
R3 = `docs/mac/control_replogle3_from_opus_r0/summary.json`; `docs/results/scaling.md`, `results_table.md`.

| system | S M1 | S M3 | S M8 MSE/PCC/R² | S M9 DE-F1 / DIR | V M1 | OOF M1 (seed 0) |
|---|---|---|---|---|---|---|
| Start: OLS on built-ins, EXP_0003 (R) | 0.5196 | 0.0070 | 0.1536 / 0.9318 / 0.7341 | 0.111 / 0.929 | 0.5560 | 0.4823 |
| Linear regression, rerun (`results_table.md`) | – | 0.0071 | 0.1602 / 0.9200 / 0.7140 | – | – | – |
| Scripted control @2492e11, n = 6 | 0.554 ± 0.000 | 0.0070 | 0.1451 / 0.9428 / 0.7559 | – | – | – |
| Agents @2492e11, 1 / 4 / 8 / 16 workers, n = 2 each (`scaling.md`) | 0.566 ± 0.032 / 0.602 ± 0.002 / 0.584 ± 0.001 / 0.577 ± 0.022 | | | | | |
| Control + Replogle, EXP_0076 (R) | 0.6214 | 0.0047 | 0.0837 / 0.9642 / 0.8480 | 0.500 / 0.953 | 0.6642 | 0.6113 |
| No-LLM continuation of an agent campaign, EXP_0466 (R3) | 0.6458 | 0.0044 | 0.0735 / 0.9698 / 0.8683 | 0.524 / 0.958 | 0.6737 | 0.6510 |
| CellForge-Models, reported: **not comparable** | – | 0.0051 | 0.2013 / 0.9474 / 0.8912 | – | – | – |
| A1–A6 on the package | | | | | | |

The 8-worker mean includes one hash-sensitive model (`README.md`, note †).

### Template for the comparison itself (from `feature_compare.py`; empty until it runs)

One block per bundle and parent (P0, P1). System rows first (the tool's Table 1), then add-one rows (its
Table 2). Gains are candidate minus parent, so positive is better; for the MSE metrics M3 and M4 the tool takes
parent minus candidate, so a positive ΔM3 or ΔM4 is also an improvement. The tool's tables print ΔM1, ΔM2, ΔM4,
ΔM5 and ΔM7; ΔM6 is in `feature_compare.json`, and ΔM3 (pooled MSE, no paired difference) is the difference of the
two rows' M3.

| arm | search | row | tier | n | P M1 | P+x M1 | ΔM1 ± SE_adj | wins | null p (FWER) | ΔM2 | ΔM3 | ΔM4 | ΔM5 | ΔM6 | ΔM7 | M12 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | – | system | OOF | | | | | | | | | | | | | | |
| A1 | r0 | system | OOF | | | | | | | | | | | | | | |
| A1 | r0 | + feature … | OOF | | | | | | | | | | | | | | |

Arm summary (one row per arm, mean ± sd over its searches): ΔM1 of the system row on OOF, on V (if allowed),
and on F once it exists; number of features; number with a development verdict.

## 6. What counts as a useful feature

1. **Development verdict.** `feature_compare.py` prints "meaningful (development, …)" when, on the deciding tier
   (OOF, or V with `--with-val1`): the mean M1 gain beats twice its overlap-adjusted SE and the minimum effect of
   interest, 0.002 (`docs/ROADMAP.md` D3), with wins on more than half the perturbations; the family-wise null p
   `p_fwer` is at most 0.05 for the gene null and, when the candidate is proportional to a parent column, for the
   perturbation null too; M2 gains and M4 is not significantly worse; every OOF report (fold-seed pair) gains; and
   more than one fold seed was used. The parenthesis says how far a pass can be trusted: "OOF only, not held out",
   "val1", or "optimistic: source selected on val1" (a lab run under `--with-val1`, which screens nothing;
   section 4). The tool's docstring is the exact list. The verdict screens; it proves nothing, because every arm
   selected on OOF. The pieces, fixed on 16 October 2026 after block F (`docs/ROADMAP.md` D2):
   - *Two nulls.* The gene null permutes the candidate across genes within bins of control expression. A candidate
     that is, within every perturbation's row, a per-perturbation scalar times one parent column (block F's
     additive_response × target promoter CpG; `docs/results/norman_f_stage2/feature_compare.json`, null sd 1e-5
     against a gain of 0.00056) cannot fail that null, because the parent factor stays in the model. Such a row is
     marked `proportional` with its `parent_column` and gets the perturbation null `null_pert`: the scalars are
     permuted across the training perturbations within deciles of the targets' mean control expression, the parent
     columns stay in place, and the candidate is rebuilt in every fold view. It must pass both nulls. A row that is
     not proportional passes the gene null alone. Proportionality is read at a relative residual of 1e-6 per row
     (`PROP_RTOL`), so the same product formed in float32 (residual about 4e-8) is still caught; it is read in the
     full training view and checked in every fold view (`proportional_in_folds`): a scalar that depends on the
     view's training data fits the full view only, the perturbation null would then score a different candidate
     than the observed one, so such a row gets no perturbation null and fails the verdict.
   - *Family-wise p.* `p_fwer` is the max-gain step-down permutation p (Westfall and Young) over one source's
     add-one rows, from each row's stored B null gains; the permutation of replicate b is the same for every row of
     the call, so the joint null keeps the dependence between candidates. The floor is 1/(B+1); B = 999 by default
     (floor 0.001), and a family of any size with fewer than 999 replicates reads "null too coarse" (a family of one
     has no exception, see "Null replicates" in section 4). The Holm p of the raw null p stays in the report as
     `p_holm`, for comparison only. A source's system row is a family of one.
   - *Deduplication.* Before the correction, rows of one source with an identical prediction hash (the OOF
     predictions over every report rounded to 1e-9; `docs/ROADMAP.md` D2(c)) collapse to the first; the others get
     status `duplicate` and are not family members, so three copies of one column count once. A column and its
     negation or rescaling predict alike and are one member; each row keeps its own coefficient sign.
   - *Coefficient sign.* The standardised add-one coefficient of the candidate is saved per report
     (`coef_candidate_std`, with its mean and sign) and shown in the table, so the sign can be read against the
     pre-registered one (`docs/GOAL_CRITERIA.md` A.2).
   - *Block F's reading.* `tools/block_f_readings.py pool` applies the same step-down once over the union of the
     three runs' unique rows (duplicates collapsed across runs by hash) and requires, in addition, the gain above
     max(2 SE_adj, 0.002); permutations are shared within one `feature_compare` call but not across calls, so
     pooling rows from separate calls is conservative. Stage 2 must hold every stage-1 row: `select --k` is refused
     without `--partial`, and a stage 2 that omits a stage-1 row is marked `partial` by `pool` (the step-down over a
     subset is not family-wise) and finds nothing.
2. **Pre-registration.** Before `feature_compare.py` runs, each arm's candidate list is fixed and recorded in
   the claim issue: the files and their sha256. Proposal: tier F receives each arm's system row, plus at most 3
   single features per arm, the ones with a development verdict (V-decided for package arms when V is allowed,
   OOF-decided for lab arms) and the largest gain on that tier. Before choosing, read each candidate's literal
   report and its arm's transcript; where V is allowed, drop a package candidate whose V gain falls more than
   2·SE_adj below its OOF gain (a sign of labels pasted into the file, section 3.9). No other feature may be
   added after any score is seen.
3. **Multiplicity.** At the development tier, the max-gain step-down within each source (the tool does it;
   item 1). At tier F
   (proposal, to be fixed before anything is scored): every candidate sent there, system rows and single features
   of all arms, gets a one-sided p from its paired M1 gain, p = 1 − Φ(Δ / SE_adj), with SE_adj widened by the
   gene-overlap ratio as in `tools/sealed_reading.py`; Holm runs over all of them at 0.05. Report raw and adjusted p.
4. **Fresh test.** One scoring of frozen P + x predictions by the separate evaluator. A feature is useful when its
   Holm-adjusted F p is at most 0.05 and it wins on more than half the perturbations; an arm is better than its
   parent when, in addition, its mean gain over searches exceeds the spread between searches (the arm rule).
5. **Biology, then the wet lab.** A useful feature must say which knowledge and which genes carry it (PR #38,
   section 1, point 4). A wet-lab test of the biological hypothesis it encodes is a later, separate decision.

## 7. Decisions for Andres

1. **Visible validation (`--with-val1`).** AGENTS.md says never read `data/*/private/`; `tools/feature_audit.py`
   already reads `private/val1.npz` this way. May `feature_compare.py` do the same? Until you say yes it scores
   OOF only, and package arms have no unselected development number. (2026-10-17: `docs/ROADMAP.md` D5 keeps
   `--with-val1` off and ships the tier to the package arms instead; see the note of that date at the end.)
2. **Who pays for A3 and A4.** A3: your Claude subscription, a Codex account, or Claude Code pointed at
   DeepSeek's Anthropic-compatible endpoint (**unverified**). A4: DeepSeek through the ledger. Neither Claude Code
   nor Codex writes to our ledger.
3. **A no-network container on the Mac** for A3, A4 and A5-C1. Whether Docker is installed there is
   **unverified**. Without it these arms do not run on the Mac.
4. **GPU** for A5-C0 and A6: rent one, or drop these rows. Also: A5-C1 (patched prompt, paid) or only C2.
5. **Fresh-test holder** ([#22](https://github.com/andresloak100/Gene-Mila/issues/22)): the evaluator account
   is deferred. Without it there is no headline number. Also: does it receive held-out cells (then M8–M10 can
   be in the main table) or only means (then M1–M7, M11, M12)?
6. **Cap.** HANDOFF.md section 1 records a ledger of $43.599822392 against the $48 block (last committed);
   PR #39 runs under a $52 cap; the B4 costs are not in the repository. A comparison with 3 searches × 5 paid
   arms × 2 bundles needs a new pre-specified block with its own cap.
7. **Package keep rule.** The noise rule (default) or also autoresearch's strict rule as an ablation.

## 8. Notes on PR #38: items to check before the paper

1. Lines 55 and 138: "CellForge reports Biomni produced no executable code on Norman." Not found in the CellForge
   repository. Its README compares CellForge with Biomni only on LLM-judged research plans (`README.md:197`).
   Search snippets mention an Appendix T with a Biomni score of 0 (**unverified**). Check with
   `pdftotext 2508.02276v2.pdf - | grep -n -i biomni`; arxiv.org is blocked from the cloud sessions.
2. Lines 37–38: "B2: +0.030 visible against +0.004 sealed for a single model." These are N1's numbers
   (`docs/results/norman_sealed_reading.md`, lines 11 and 16). B2's no-LLM control reads +0.031 visible and
   +0.006 sealed (b2 `docs/results/norman_b2_control_sealed_reading.md`).
3. Line 40: "B2's arm beat the additive rule on held-out data, +0.011." The arm reading gives G = +0.0113
   against a bar k·SE = 0.0113, "arm better" (b2 `norman_b2_arm_vs_additive.md`). The margin is below the
   fourth decimal, and the reported jackknife variant does not pass. Say "at the bar".
4. Section 5 table: the B1 row puts 0.114 and 0.856 (top-20 by |Δ|) in the MSE_DE and R2_DE columns, which hold
   Wilcoxon top-20 values for the other rows. The row labels it, but the column mixes two definitions.
5. Section 2 table, "keep or discard" for Gene-Mila: today `best()` is the plain highest selection score
   (`genemila/db.py:203-206`), and a feature "helps" above 0.002 (`genemila/research_state.py:18`). "More than
   fold noise" is a proposal, not the current rule.
6. Section 6, point 4: "$10 to $30 of DeepSeek at about $0.6 per run" is real billing. Caps count the ledger,
   which reads about twice the billed amount (AGENTS.md, "Money and usage"). State budgets in ledger dollars.
7. Section 5, Adamson row "agents' features + Replogle, no LLM" (0.646) is EXP_0466 of
   `control_replogle3_from_opus_r0`: a no-LLM run that continued an Opus agent campaign. Name it that way.

## Note of 2026-10-17: the harness tier and the V check (the lead, `docs/ROADMAP.md` D5)

A task package exported with the harness tier (`tools/export_task_package.py`, the default) ships the visible
validation labels as `harness/val1.npz`, and its `evaluate.py` decides keep or discard on the validation and the
out-of-fold training perturbations together (17 and 50 on Adamson, section 5). For such a package arm V is a seen
tier: its author could read the file. So for those arms the drop rule of section 6, item 2 (a V gain more than
2·SE_adj below the OOF gain) does not apply, and section 3, item 9's "V check" is void; the candidates for the frozen
batch are chosen on out-of-fold seeds 101 to 103 only, the literal report of every kept file is read by hand before
it is listed, and the fresh test (ROADMAP D7) is the one tier whose labels no arm had. `literal.py`'s first paragraph
says the same. A package exported with `--no-harness-val1` (Andres's veto, ROADMAP section 7, item 3) keeps the rule
as written above.
