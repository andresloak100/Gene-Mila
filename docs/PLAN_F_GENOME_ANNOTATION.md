# Block F: can the agents find a new kind of feature in genome annotation? (Norman), fixed before any run

Written 2026-10-16 by a Claude cloud session (claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)) on
Andres's messages of 15 and 16 October: find a new biological feature for the linear model, "you have permission to
run the deep seek agents", and "which data sources are allowed? I want you to suggest the best option". Revised the
same day after a review, still before any run: the sealed arm-against-arm reading is replaced by one the existing
tools can make, the feature-level criterion is one pooled rule, and the scripts check more before spending. Nothing
below has run. Every number these runs produce is read by the rules here; from the first run on, a change is a new,
dated section, never an edit. The cloud session cannot reach DeepSeek and has no data, so the block runs on the Mac
with the scripts in `docs/mac/block_f/`.

## Question

On Adamson, every winning model the agents built gets its gain from one family: copying the responses of training
perturbations whose targets look similar (`docs/NEXT_LEVER.md`, 26 Adamson runs). Norman has no such audit; its
starting model is the additive pair rule, and this plan assumes that the agents' knowledge limits them there too. The
bundle's knowledge files only say which genes share pathways, interactions and regulators. Block F gives the agents
one new kind of information, a per-gene table built from the genome sequence and GENCODE's transcript models
(`tools/build_gene_annotation.py`): gene loci, bidirectional TSS pairs, neighbours, message architecture, promoter
CpG content and amino-acid composition. It is tier 1 of the data-source policy recommended in
`docs/NOVEL_FEATURE_NEEDS.md` (section 7): no perturbation measurement and no measured response is behind it, so it
cannot encode a held-out response. (GENCODE's transcript models do rest on RNA evidence: cDNA, ESTs, RNA-seq.)

The agents get the file and its one-paragraph description only, and no list of hypotheses. A feature they build from
it is theirs, not a human idea (`docs/NOVEL_FEATURE_NEEDS.md`, M8).

Two things are asked, in this order:
1. Do the agents use the new file, and does any feature they build from it add to the model beyond a matched null?
   This is the feature-level reading, the question the paper is about.
2. Do the F arm's selected feature sets do better than B2's under one fixed linear model? This is read on the
   development tier (out-of-fold training perturbations), descriptively. A sealed arm-against-arm reading is not
   made: `tools/arm_reading.py` and `tools/sealed_reading.py --versus` at ce1b530 refuse two runs whose bundle paths
   differ (`_same_question`), and F runs on `data/norman_ga` while B2 ran on `data/norman`. Making one would need a
   new tool commit, named in a dated section before the first run.

## Arms

- **B2 arm (exists, not rerun):** `runs/norman_ds_addstart_w4_r0`, `_r2`, `_r3`. DeepSeek planner deepseek-v4-pro,
  4 deepseek-flash workers, 20 minutes, fresh start from `baseline_ridge_additive`, `data/norman` (split
  `split_a391fa9e7b4eccb7`) with `replogle2022_k562.json` (md5 d9eff528143dcd4d72c87393df724084), code ce1b530. Seed
  1 is its own arm (it was killed while finishing) and is not used.
- **F arm (new):** the same with `run.data_dir=data/norman_ga`, seeds 0, 2 and 3, run directories
  `runs/norman_ga_ds_addstart_w4_r0`, `_r2`, `_r3`.
  - `data/norman_ga` is a copy of `data/norman` (same manifest, so the same split) plus
    `knowledge/gene_annotation.json` (md5 99e0eccb3caae76bc98f1c2e5730cfc0), committed gzipped as
    `docs/mac/block_f/gene_annotation_norman.json.gz`.
  - F keeps B2's Replogle file, a perturbation screen and tier 3 under the proposed policy. F is therefore a
    "Replogle + annotation" arm. Only `gene_annotation` features whose source does not read `replogle2022_k562` can
    support a tier-1 claim (reading 1).
  - The file was built in the cloud by `tools/build_gene_annotation.py` at commit 5ac5b5d from Broad's public hg38
    reference bucket (`broad-references` on S3):
    - https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf, saved as
      `gencode.v27.gtf`, sha256 26b81dd6e74bdc9c9c6ba0c87f1a069cf9b2b4492079b2706604ae679cc5b97c;
    - https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta (with its `.fai`), saved as
      `hg38.fasta`, sha256 93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564.

    Both names and hashes are recorded in the table's `source`. The cloud has no bundle, so `--genes-from` pointed
    at a directory holding a stand-in `public.npz` with only the 2,083 genes listed in
    `docs/results/norman_frozen_export_20261013/manifest.json`. The preparation script checks that the real
    bundle's gene list is the same. Command: `python tools/build_gene_annotation.py --gtf gencode.v27.gtf --fasta
    hg38.fasta --genes-from <that directory> --out norman_gene_annotation.json`, then `gzip -9 -n -c`.
  - 2,041 genes are annotated. The 42 unmatched are retired symbols (SEPP1, KIAA0101, TCEB1, …) and are listed in
    the file's `unmatched`. 96 genes have a measured bidirectional partner.
  - Code ce1b530 from the worktree `gene-mila-ce1b530`, caps `budget.max_total_usd=1.0` and
    `budget.max_planner_usd=1.5`, shared ledger, as B2.

**What differs from B2.**
- The intended change: the knowledge file. The planner shows all knowledge files in one section cut at 2,500
  characters, and cuts its whole state at 20,000 (`genemila/research_state.py` at ce1b530, `SECTION_CHARS`,
  `TOTAL_CHARS`). The file's knowledge line is 895 characters (897 with its separator).
  - Before each run, `norman_f_run.sh` checks that the whole knowledge section stays within 2,500 characters, so the
    Replogle description B2's planner read is not pushed out.
  - It also checks that B2's largest planner state (`max(state_chars)` of `planner_rounds` in the three B2 runs'
    `lab.db`) plus 897 stays within 20,000, so the tail of the state is not cut sooner than it was for B2.
    `state_chars` also counts the focus line added after the cut, so this check errs towards refusing.
  - A run that fails a check does not start; the fix would be a new dated section here.
- Watchdog and backstop: all three F runs use `--no-watchdog` with no backstop. B2's seed 0 ran under
  run_research.py's watchdog. B2's seeds 2 and 3 ran with `--no-watchdog` and a 5,400 s backstop that terminated a
  run still going 90 minutes after it started, and counted that as a stop (`block_b2_run.sh`). For F, the
  operator applies the same rule by hand: a run still going 90 minutes after its start in `progress.md` is ended
  and recorded in `block_f_stopped.txt` as a stop.
- Not repeated from B2: `analyze_run.py` after each run (B2 reported it; no reading uses it) and the `build_config`
  check of the configuration (F's command is fixed in the script).
- The cumulative cap passed to each run is the block cap below instead of $48; it does not bind mid-run in either
  arm.

## Money

Andres allowed DeepSeek runs on 16 October: "you have permission to run the deep seek agents" (issue #41). The $8 cap
below is this plan's proposal; he may lower or veto it before the chain starts. `AGENTS.md` still names
`docs/PLAN_AFTER_N4.md` ($48) as the current block, and the B4 runs of 15 October (PR #39) already went past it. The
chain waits until Andres has confirmed the cap in writing (his message to the operator, recorded on issue #41) and
`HANDOFF.md` section 1 names block F as the current block; `AGENTS.md` names it in the pull request that carries this
plan, so the two files stay true together. The ledger overstates real cost about twofold (`AGENTS.md`). B2's runs cost $1.29, $1.37 and $1.19 by the
ledger, so three runs are expected to cost about $4.

- **Block cap:** the shared DeepSeek ledger (provider `deepseek` only) may rise by at most **$8** over its reading when
  the block starts. That is about $4 of real money. The operator writes the cap once, before the chain, into
  `block_f_cap.txt` as one line `<cap> <ledger at the start> <UTC date>`. The command refuses if the file exists, so
  a stopped or resumed block never gets a fresh $8:
  ```bash
  bash <<'EOF'
  L=~/Documents/Mila/Gene-Mila/genemila_scale_logs; LEDGER=~/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite
  s=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
  case "$s" in ''|*[!0-9.]*) echo "NOT DONE: ledger unreadable ('$s')"; exit 1 ;; esac
  set -o noclobber
  awk -v s="$s" -v d="$(date -u +%Y-%m-%dT%H:%MZ)" 'BEGIN { printf "%.2f %s %s\n", int((s + 8) * 100) / 100, s, d }' \
    > "$L/block_f_cap.txt" || { echo "NOT DONE: block_f_cap.txt exists; the cap is written once per block"; exit 1; }
  echo "- $(date -u +%Y-%m-%dT%H:%MZ) block F cap written: $(cat "$L/block_f_cap.txt") (cap, DeepSeek ledger at the start, UTC date)" >> "$L/progress.md"
  cat "$L/block_f_cap.txt"
  EOF
  ```
  `norman_f_run.sh` reads the cap from that line, refuses a cap more than $8 over the recorded start or a ledger
  below it, and logs the start reading and the cap to `progress.md` with every run.
- Each run passes `--set budget.cumulative_usd.deepseek=<cap>` and starts only when the ledger plus its two caps
  ($2.50) stays within the cap, so the cumulative cap never binds mid-run.
- The block stops, and the run becomes its own arm, when a run:
  - fails;
  - costs more than $2.00, or the ledger cannot be read after it (or reads below its start);
  - ends with `planner.mixed` true;
  - shows a knowledge list other than `gene_annotation, replogle2022_k562`.
- The key comes from `API_KEY` in Andres's `~/.zshenv`, as `DEEPSEEK_API_KEY` in the chain's own environment only.
  The run script unsets `API_KEY`, as B2's did, so no second copy reaches the lab. Never on a command line, in a file
  or in a log.

## Exact commands (Mac)

1. **State first.** Nothing may run beside a paid run or the comparison driver (`AGENTS.md`). The B4 chain of 15
   October must have finished, with its spend recorded, and the conditions under Money must hold.
   ```bash
   python handoff_state.py --fetch --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs; pgrep -fl run_research.py
   ```
2. **Free preparation**, from a clone that has this branch. It never changes `data/norman` and refuses if
   `data/norman_ga` exists. It copies to `data/norman_ga.partial` and renames that only after checking that the copy
   is `data/norman` byte for byte, both knowledge md5s match and the knowledge files are exactly the bundle's five,
   Replogle's and the annotation:
   ```bash
   bash docs/mac/block_f/prepare_norman_ga.sh
   cp docs/mac/block_f/norman_f_run.sh docs/mac/block_f/norman_f_chain.sh ~/Documents/Mila/Gene-Mila/genemila_scale_logs/
   ```
3. **The cap**, as in Money above, once.
4. **The chain**, from a login zsh. The STOP file is lifted for the block and put back after:
   ```bash
   cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs
   DEEPSEEK_API_KEY="$API_KEY" nohup caffeinate -i bash norman_f_chain.sh > block_f_chain.log 2>&1 &
   ```
   - `progress.md`, `block_f_chain.log` and each run's `.check.txt` say where it is. The `.check.txt` also lists the
     features that read `gene_annotation`.
   - Read no run's log end or `summary.md` before the readings; they hold sealed scores.
   - Before spending, each run checks the key, the cap line, the worktree at ce1b530 and clean, that its run
     directory and log do not exist, no STOP file, no stopped block, no lab run and no scaling driver
     (`scale_seq.sh`) running, both knowledge md5s, `added_knowledge` printing exactly
     `gene_annotation replogle2022_k562`, the two planner-state cuts, and the ledger gate.
   - **Resume.** The chain skips a seed whose `norman_ga_ds_addstart_w4_r<S>.passed` exists. If it stopped on a
     pre-run refusal (exit 1 or 2: ledger gate, a lab run or the driver running, no key), fix the cause and start it
     again with the same command; the cap file stays. A stop after a run (`block_f_stopped.txt`) is not resumed: the
     cause is written up here first.

## Readings, fixed now, made only after all three F runs have ended

Free, CPU only: they wait until no lab run or driver is running. Every command runs from the operator's clone of
this branch (never the main checkout) and writes into its `docs/results/`. Set first:
```bash
M=~/Documents/Mila/Gene-Mila/gene-mila; WT=~/Documents/Mila/Gene-Mila/gene-mila-ce1b530; C=<your clone of this branch>
P="$C/docs/results/norman_f_plugins"
```
`tools/feature_compare.py` comes from this branch (or the integration branch once it is merged); the sealed reading
uses the tool at ce1b530 from the worktree.

1. **Feature-level (primary for the paper).**
   - Copy every plugin in the three F runs' `feature_store/` whose source mentions `gene_annotation`, unchanged, into
     one directory per run (committed with the readings). Count them before anything is scored; the matched null gets
     enough replicates for the pooled family, `max(199, 20 × m_total − 1)`:
     ```bash
     for s in 0 2 3; do mkdir -p "$P/r$s"; grep -l gene_annotation "$M/runs/norman_ga_ds_addstart_w4_r$s/feature_store/"*.py | xargs -I{} cp -p {} "$P/r$s/"; done
     m_total=$(ls "$P"/r*/*.py 2> /dev/null | wc -l | tr -d ' '); reps=$(( 20 * m_total - 1 )); [ "$reps" -lt 199 ] && reps=199
     echo "m_total $m_total, null replicates $reps"
     cd "$C" && PYTHONPATH="$C" "$M/.venv/bin/python" tools/feature_compare.py --data "$M/data/norman_ga" \
       --out docs/results/norman_f_feature_compare \
       --source f_r0="$P/r0" --source f_r2="$P/r2" --source f_r3="$P/r3" \
       --source-run f_r0_selected="$M/runs/norman_ga_ds_addstart_w4_r0" \
       --source-run f_r2_selected="$M/runs/norman_ga_ds_addstart_w4_r2" \
       --source-run f_r3_selected="$M/runs/norman_ga_ds_addstart_w4_r3" --null-reps "$reps"
     ```
     The parent is the built-in start (the additive model) and the fold seeds are the tool's default (101, 102,
     103). Out-of-fold tier only, unless Andres has approved `--with-val1` by then; the pooled Holm below always reads
     the OOF tier's null p, whatever tier decides the tool's own verdict. A plugin copied into a per-run directory
     is scored with its class default params (the tool never reads a params file for `--source` files), so a
     feature a run tuned through params is scored at its defaults here; the run's tuned version appears only in
     the descriptive `_selected` rows. With `m_total` 0 the reading is negative without scoring.
   - **Criterion (the one rule).** Holm is applied once, pooled over every `gene_annotation` add-one row of `f_r0`,
     `f_r2` and `f_r3` that the tool scored (status ok, with a null), using the raw null p values in
     `feature_compare.json`. A feature counts as found when two things hold. First, the tool's verdict fails it on
     nothing except its own per-source Holm line: gain above twice its overlap-robust SE, wins on more than half the
     perturbations, every fold-seed report positive, an M2 gain, `mse_top` not significantly worse. Second, its
     pooled Holm p is at most 0.05. For a tier-1 claim, its source must also not read `replogle2022_k562`. Rows
     that fail a check are reported with their reason and count as not found.
     ```bash
     cd "$C" && PYTHONPATH="$C" "$M/.venv/bin/python" - "$P" <<'EOF'
     import json, sys
     from pathlib import Path
     sys.path.insert(0, "tools")
     from feature_compare import holm
     P = Path(sys.argv[1]); r = json.loads(Path("docs/results/norman_f_feature_compare/feature_compare.json").read_text())
     rows = [x for x in r["rows"] if x["source"] in ("f_r0", "f_r2", "f_r3") and x["kind"] == "add_one"
             and x["status"] == "ok" and x["tiers"]["oof"].get("null")]
     out = []
     for x, p in zip(rows, holm([x["tiers"]["oof"]["null"]["p"] for x in rows])):
         other = [f for f in x["failed_criteria"] if not f.startswith(("null p (Holm)", "null too coarse"))]
         rep = "replogle2022_k562" in (P / x["source"].split("_")[1] / f"{x['feature']}.py").read_text()
         out.append({"source": x["source"], "feature": x["feature"], "p": x["tiers"]["oof"]["null"]["p"],
                     "p_holm_pooled": p, "other_failed": other, "reads_replogle": rep,
                     "found": not other and p <= 0.05, "found_tier1": not other and p <= 0.05 and not rep})
     Path("docs/results/norman_f_pooled_holm.json").write_text(json.dumps({"family": len(rows), "rows": out}, indent=1))
     print(f"family {len(rows)}; found {[o['feature'] for o in out if o['found']]}; "
           f"tier 1 {[o['feature'] for o in out if o['found_tier1']]}")
     EOF
     ```
   - The tool's own verdict column (Holm within each run) is reported beside it, but the criterion is the pooled
     one. The `_selected` rows (each run's selected features that the parent lacks, of any kind) are descriptive
     only.
   - Otherwise the reading is negative, and that is reported too.
2. **Per run, sealed:** each F run's selected model against its additive baseline and its start. The tool at ce1b530
   reads a single run on its own bundle (the `data_dir` its config records); only pairs need the same bundle path.
   ```bash
   for s in 0 2 3; do cd "$C" && PYTHONPATH="$WT" "$M/.venv/bin/python" "$WT/tools/sealed_reading.py" \
     --runs "$M/runs/norman_ga_ds_addstart_w4_r$s" --out "docs/results/norman_f_r${s}_sealed_reading.md"; done
   ```
   Reading rule as for B1, B2 and B4: a gain counts only when it exceeds twice its paired standard error and the
   better side wins on more than half the perturbations. Categories under 10 sealed perturbations are reported, not
   read.
3. **Arm against arm, development tier (descriptive).** One `feature_compare` call rebuilds each of the six runs'
   selected models from its recorded features and params, under the same parent (built-in) and fold seeds.
   `feature_compare` checks the split_id, not the path, and B2's models need no `gene_annotation`, so `data/norman_ga`
   serves both arms. No null is computed; the system rows are read by their metrics:
   ```bash
   cd "$C" && PYTHONPATH="$C" "$M/.venv/bin/python" tools/feature_compare.py --data "$M/data/norman_ga" \
     --out docs/results/norman_f_arm_vs_b2 --null-reps 0 \
     --source-run f_r0="$M/runs/norman_ga_ds_addstart_w4_r0" --source-run f_r2="$M/runs/norman_ga_ds_addstart_w4_r2" \
     --source-run f_r3="$M/runs/norman_ga_ds_addstart_w4_r3" --source-run b2_r0="$M/runs/norman_ds_addstart_w4_r0" \
     --source-run b2_r2="$M/runs/norman_ds_addstart_w4_r2" --source-run b2_r3="$M/runs/norman_ds_addstart_w4_r3"
   ```
   - Reported: each run's `(set)` row of Table 1 (OOF M1 to M12, ΔM1 ± SE_adj over the start, wins), and per arm
     the mean ± sd of M1 and ΔM1 over its three runs. A run whose model cannot be rebuilt is named, and its arm is
     reported with fewer runs.
   - With three runs a side no test is made, and no difference is claimed that lies within either arm's spread.
     OOF is not held out for either arm (both selected on these labels and on val1), and the rows refit the tool's
     ridge, not each run's own model type and alpha.
4. **Secondary, descriptive:** per run, the number of experiments and of selected features that read
   `gene_annotation`, and which columns or keys they use (from the plugin sources). The `gene_annotation` features
   are listed in two groups, those whose source also reads `replogle2022_k562` and those that do not.

Nothing is chosen from a sealed score. A positive feature-level reading is a candidate, not a discovery. It still
needs replication on another cohort with the sign the mechanism predicts, a fresh test held outside the
orchestration, and a wet-lab test (`docs/NOVEL_FEATURE_NEEDS.md`, sections 3–4). The leading mechanism the table
enables is known biology: CRISPRa or CRISPRi at one TSS reaching a nearby gene whose TSS is on the opposite strand
within 1 kb (mostly head-to-head shared promoters; 96 Norman genes have such a measured partner). Confirming it
would be a methods result, not a new rule.
