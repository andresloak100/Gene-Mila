# Block F: can the agents find a new kind of feature in genome annotation? (Norman), fixed before any run

Written 2026-10-16 by a Claude cloud session (claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)) on
Andres's messages of 15 and 16 October: find a new biological feature for the linear model, "you have permission to
run the deep seek agents", and "which data sources are allowed? I want you to suggest the best option". Nothing below
has run. Every number these runs produce is read by the rules here; a change is a new, dated section, never an edit.
The cloud session cannot reach DeepSeek and has no data, so the block runs on the Mac with the scripts in
`docs/mac/block_f/`.

## Question

Every model the agents have built so far gets its gain from one family: copying the responses of training
perturbations whose targets look similar (`docs/NEXT_LEVER.md`). The bundle's knowledge files only say which genes
share pathways, interactions and regulators. Block F gives the agents one new kind of information, a per-gene table
built from the genome sequence (`tools/build_gene_annotation.py`): gene loci, shared (bidirectional) promoters,
neighbours, message architecture, promoter CpG content and amino-acid composition. It is tier 1 of the data-source
policy recommended in `docs/NOVEL_FEATURE_NEEDS.md` (section 7): derived from sequence, with no expression or
perturbation measurement behind it, so it cannot encode a held-out response.

The agents get the file and its one-paragraph description only, and no list of hypotheses. A feature they build from
it is theirs, not a human idea (`docs/NOVEL_FEATURE_NEEDS.md`, M8).

Two things are asked, in this order:
1. Do the agents use the new file, and does any feature they build from it add to the model beyond a matched null?
   This is the feature-level reading, the question the paper is about.
2. Does the arm's combined model beat B2's combined model on the sealed perturbations? This is a worn set (read for
   B1, B2 and B4), so it is one more labelled look, not a clean test.

## Arms

- **B2 arm (exists, not rerun):** `runs/norman_ds_addstart_w4_r0`, `_r2`, `_r3`. DeepSeek planner deepseek-v4-pro,
  4 deepseek-flash workers, 20 minutes, fresh start from `baseline_ridge_additive`, `data/norman` with
  `replogle2022_k562.json` (md5 d9eff528143dcd4d72c87393df724084), code ce1b530. Seed 1 is its own arm (it was
  killed while finishing) and is not used.
- **F arm (new):** the same with `run.data_dir=data/norman_ga`, seeds 0, 2 and 3, run directories
  `runs/norman_ga_ds_addstart_w4_r0`, `_r2`, `_r3`.
  - `data/norman_ga` is a copy of `data/norman` plus `knowledge/gene_annotation.json` (md5
    3f6aca1fc91cccdd5b684656d7f54963), committed gzipped as `docs/mac/block_f/gene_annotation_norman.json.gz`.
  - That file was built in the cloud by `tools/build_gene_annotation.py` at commit 4c72e15. Its inputs were
    GENCODE v27 (`gencode.v27.primary_assembly.annotation.gtf` from Broad's public hg38 bucket, sha256 26b81dd6…) and
    `Homo_sapiens_assembly38.fasta`. It was built for the 2,083 genes of the Norman gene list committed in
    `docs/results/norman_frozen_export_20261013/manifest.json`.
  - 2,041 genes are annotated. The 42 unmatched are retired symbols (SEPP1, KIAA0101, TCEB1, …), listed in the file's
    `unmatched`.
  - Everything else is identical to B2: code ce1b530 from the worktree `gene-mila-ce1b530`, `--no-watchdog`, caps
    `budget.max_total_usd=1.0` and `budget.max_planner_usd=1.5`, shared ledger.

One change only. The planner shows all knowledge files in one section cut at 2,500 characters
(`genemila/research_state.py` at ce1b530). The new file's description is kept short, and each run first checks that
the whole summary stays under the cut, so the Replogle description B2's planner read is not pushed out. A run that
fails this check does not start; the fix would be a new dated section here.

## Money

Andres, 16 October: "you have permission to run the deep seek agents". The ledger overstates real cost about twofold
(`AGENTS.md`). B2's runs cost $1.29, $1.37 and $1.19 by the ledger, so three runs are expected to cost about $4.

- **Block cap:** the shared DeepSeek ledger (provider `deepseek` only) may rise by at most **$8** over its reading when
  the block starts. That is about $4 of real money. The operator writes the cap once, before the chain:
  ```bash
  L=~/Documents/Mila/Gene-Mila/genemila_scale_logs; LEDGER=~/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite
  sqlite3 "$LEDGER" "select coalesce(sum(cost_usd),0) from spend where provider='deepseek'" | awk '{printf "%.2f\n", $1 + 8}' > "$L/block_f_cap.txt"
  ```
- Each run passes `--set budget.cumulative_usd.deepseek=<cap>` and starts only when the ledger plus its two caps
  ($2.50) stays within the cap, so the cumulative cap never binds mid-run.
- The block stops, and the run becomes its own arm, when a run:
  - fails;
  - costs more than $2.00;
  - ends with `planner.mixed` true;
  - shows a knowledge list other than `gene_annotation, replogle2022_k562`.
- The key comes from `API_KEY` in Andres's `~/.zshenv`, as `DEEPSEEK_API_KEY` in the chain's own environment only.
  Never on a command line, in a file or in a log.

## Exact commands (Mac)

1. **State first.** Nothing may run beside a paid run or the comparison driver (`AGENTS.md`). The B4 chain of 15
   October must have finished.
   ```bash
   python handoff_state.py --fetch --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs; pgrep -fl run_research.py
   ```
2. **Free preparation**, from a clone that has this branch. It never changes `data/norman` and refuses if
   `data/norman_ga` exists:
   ```bash
   bash docs/mac/block_f/prepare_norman_ga.sh
   cp docs/mac/block_f/norman_f_run.sh docs/mac/block_f/norman_f_chain.sh ~/Documents/Mila/Gene-Mila/genemila_scale_logs/
   ```
3. **The cap**, as in Money above.
4. **The chain**, from a login zsh. The STOP file is lifted for the block and put back after:
   ```bash
   cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs
   DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i bash norman_f_chain.sh > block_f_chain.log 2>&1 &
   ```
   `progress.md`, `block_f_chain.log` and each run's `.check.txt` say where it is. The `.check.txt` also lists the
   features that read `gene_annotation`. Read no run's log end or `summary.md` before the readings; they hold sealed
   scores.

## Readings, fixed now, made only after all three F runs have ended

All are written to `docs/results/norman_f_*`. The sealed and arm readings use the tools at ce1b530 from the worktree.
`tools/feature_compare.py` comes from this branch (or the integration branch once it is merged).

1. **Feature-level (primary for the paper).**
   - List every plugin in the three F runs' `feature_store/` whose source reads `gene_annotation`, and every
     selected-model feature among them.
   - Copy those plugin files, unchanged, into one directory per run, then:
     ```bash
     python tools/feature_compare.py --data <main>/data/norman_ga --out docs/results/norman_f_feature_compare \
       --source f_r0=<dir r0> --source f_r2=<dir r2> --source f_r3=<dir r3> \
       --source-run f_r0_selected=<main>/runs/norman_ga_ds_addstart_w4_r0 \
       --source-run f_r2_selected=<main>/runs/norman_ga_ds_addstart_w4_r2 \
       --source-run f_r3_selected=<main>/runs/norman_ga_ds_addstart_w4_r3 --null-reps 199
     ```
     The parent is the built-in start (the additive model); out-of-fold tier only, unless Andres has approved
     `--with-val1` by then.
   - **Criterion:** the agents found a usable genome-annotation feature if at least one `gene_annotation` feature is
     "meaningful (development)" in Table 2: gain above twice its overlap-robust SE, wins on more than half the
     perturbations, positive under every fold-seed report, Holm-adjusted matched-null p ≤ 0.05 across all
     `gene_annotation` features of the three runs.
   - Otherwise the reading is negative, and that is reported too.
2. **Per run:** `tools/sealed_reading.py --runs runs/norman_ga_ds_addstart_w4_r<S> --out
   docs/results/norman_f_r<S>_sealed_reading.md`.
3. **Arm against arm (worn sealed set):**
   ```bash
   tools/arm_reading.py combine --members runs/norman_ga_ds_addstart_w4_r0 runs/norman_ga_ds_addstart_w4_r2 runs/norman_ga_ds_addstart_w4_r3 \
     --reference runs/norman_ds_addstart_w4_r0 runs/norman_ds_addstart_w4_r2 runs/norman_ds_addstart_w4_r3 \
     --out docs/results/norman_f_combined_vs_b2.md
   ```
   Reading rule as for B1, B2 and B4: a gain counts only when it exceeds twice its paired standard error and the
   better side wins on more than half the perturbations. Categories under 10 sealed perturbations are reported, not
   read.
4. **Secondary, descriptive:** per run, the number of experiments and of selected features that read
   `gene_annotation`, and which columns or keys they use (from the plugin sources).

Nothing is chosen from a sealed score. A positive feature-level reading is a candidate, not a discovery. It still
needs replication on another cohort with the sign the mechanism predicts, a fresh test held outside the
orchestration, and a wet-lab test (`docs/NOVEL_FEATURE_NEEDS.md`, sections 3–4). The leading mechanism the table
enables, CRISPRa or CRISPRi at one TSS reaching a gene that shares the promoter (96 Norman genes have a measured
bidirectional partner), is known biology. Confirming it would be a methods result, not a new rule.
