# Block G: the clean tier-1 arm, with and without the three tables (Adamson and Norman), fixed before any run

Written 2026-10-16 by a Claude cloud session on Andres's decisions of 16 October: tier 1 only as the clean inputs
(`docs/NOVEL_FEATURE_NEEDS.md` §7; his approval of 21:08 UTC on issue #41, in `HANDOFF.md` section 1), no Replogle
screen and no Enrichr GO or Hallmark sets; block G is that clean bundle with and without the three new tables, three
seeds each, Norman and Adamson; "approved, do what you think is best" and "please don't overengineer" (Claude project,
16 October). **Nothing below has run.** Every number these runs produce is read by the rules here; from the first run
on, a change is a new, dated section, never an edit. The session has no data and no DeepSeek, so the block runs on the
Mac with `docs/mac/block_g/`.

**The code commit is not fixed yet.** Block G runs on the integration branch head after the pull request that carries
this plan merges: it brings the clean-bundle builder (`tools/build_clean_bundle.py`, `genemila/data/knowledge_clean.py`),
the Mac scripts, and the planner-state change (`genemila/research_state.py`: the knowledge section gets its own
8,000-character budget, `KNOWLEDGE_SECTION_CHARS`, so the planner sees every knowledge file). That file is inside
Astra's open claim #40, so the change is announced to Astra on #40 when it merges (one constant and three lines in
`render_state`; nothing else in `research_state.py`, `planner.py` or `prompts.py` changes). That head, or a later one
that changes none of the code the runs use, is `<G_COMMIT>` here. A dated note at the end of this file names it, with its date, before the chain starts, and the same
commit fills `G_COMMIT=` at the top of `block_g_run.sh`, which refuses to run until then and refuses unless the
checkout it runs from is at that commit and clean.

## Question

Block F gave the agents one new table next to the Replogle screen, so a feature that read it could still be lifted by
the screen (tier 3). Block G removes every tier-2 and tier-3 input from the bundle and asks, on two datasets:
1. With only tier-1 knowledge, do the agents build a feature from the three per-gene tables (genome annotation,
   gnomAD constraint, UniProt protein annotation) that adds to the model beyond a matched null? The feature-level
   reading, the paper's question; `docs/GOAL_CRITERIA.md` A.1 is read from it.
2. Do the agents do better with the tables than without them, on the same clean bundle? G0 is G1's control; the two
   arms share code, bundle base, split, settings and seeds. Read on the development tier, descriptively.

The agents get the files and their own descriptions, no hypothesis (`docs/NOVEL_FEATURE_NEEDS.md`, M8).

## Arms, bundles and what differs from B2

- **G1** (tables): `run.data_dir=data/<ds>_clean_tables`. **G0** (no tables): `data/<ds>_clean`. For `<ds>` =
  `adamson_cf` (Adamson, start: the built-in baseline) and `norman` (Norman, pairs, gene split, start:
  `baseline_ridge_additive`, as B2; the lab picks the start from the bundle, no flag). Seeds 0, 2, 3 (B2's seeds).
  12 runs: `runs/<ds>_g1_ds_w4_r<S>` and `runs/<ds>_g0_ds_w4_r<S>`.
- **Settings as B2** (`runs/norman_ds_addstart_w4_r{0,2,3}`, `docs/PLAN_AFTER_N4.md`): DeepSeek planner
  `deepseek-v4-pro`, 4 `deepseek-flash` workers, 20 minutes, fresh start, `--no-watchdog`, caps
  `budget.max_total_usd=1.0`, `budget.max_planner_usd=1.5`, the shared ledger, one run at a time. As in F, the
  operator ends by hand a run still going 90 minutes after its start in `progress.md` and records it in
  `block_g_stopped.txt` as a stop.
- **Bundles**, built by `prepare_clean_bundles.sh` and never touching `data/norman` or `data/adamson_cf`:
  - `data/<ds>_clean`: the existing bundle's `public.npz`, `private/` and `splits.json` byte for byte (so the same
    `split_id`: Norman `split_a391fa9e7b4eccb7`), with `knowledge/` rebuilt by `tools/build_clean_bundle.py` from
    the raw inputs below: `gene_sets.json` (Reactome; GO restricted to curated and experimental evidence codes;
    CORUM complexes), `prior_network.json` and `transcription_factors.json` (CollecTRI), `ppi_network.json` (STRING
    physical links, experimental and database channels only), `targets.json`. Five files, the same names as today,
    so every existing feature plugin still loads. This plan fixes the file names, the split, the exclusions (no
    Replogle, no Enrichr GO BP, no Hallmark, no STRING text-mining or co-expression channel) and the **GO evidence
    codes admitted: EXP, IDA, IPI, IMP, IGI, HDA, TAS, IC, NAS.** Out: IEP, HEP (inferred from expression), IEA, the
    computational codes, and **HMP, HGI** (high-throughput mutant-phenotype and genetic-interaction annotations come
    from perturbation screens: tier 3 by §7); IMP and IGI stay (a single-gene mutant phenotype is not a screen and
    carries no expression response). `prepare_clean_bundles.sh` refuses a bundle whose manifest records another list
    (`clean_knowledge.provenance.go_evidence_codes`); the builder's `GO_CURATED_EVIDENCE` must match.
  - `data/<ds>_clean_tables`: the same plus `gene_annotation.json`, `gene_constraint.json` and
    `protein_annotation.json`, passed to the builder as build-time knowledge, so the manifest hashes cover them and
    `added_knowledge` is empty for both arms: neither run records an `external_knowledge` list, and
    `run.external_knowledge` other than empty stops the block. The script refuses unless the five shared files are
    byte for byte the same in both bundles (G0 is G1's control).
  - The tables are built first, per dataset, with `--genes-from` the existing bundle: `tools/build_gene_annotation.py`,
    `tools/build_gene_constraint.py`, `tools/build_protein_annotation.py`.
    The script prints each knowledge file's md5 and summary-line length for the dated note (on record before any run).
  - The builder's command line: `tools/build_clean_bundle.py --bundle <bundle> --sources <dir> --out <dir>
    [--table <name>=<file>]...`, the sources directory being the download directory below (the builder reads the
    seven files `knowledge_clean.SOURCE_FILES` names from it). The checks after each build: same `split_id`,
    `verify_bundle` clean, exactly the expected files, `added_knowledge` empty, the GO code list above, everything
    outside `knowledge/` and `manifest.json` byte for byte the source.
- **Differences from B2**, all intended: the code (`<G_COMMIT>` instead of ce1b530), the knowledge files (B2:
  the five Enrichr-and-STRING-700 files plus Replogle; G: the five clean files, with or without the three tables),
  and no Replogle screen in either arm. B2 is therefore not G0's control: G0 is. B2's numbers appear only as context.
- **Planner-state size.** The run script checks the bundle's knowledge summary against the knowledge-section budget
  of the code it runs (`research_state.KNOWLEDGE_SECTION_CHARS`, 8,000 after the change; `SECTION_CHARS`, 2,500,
  before it, which the eight-file bundle exceeds), so a g1 run on a head without the change is refused before any
  money. The whole state is still cut at 20,000 characters (`TOTAL_CHARS`); a G1 state is longer than a G0 state by
  the three table lines (about 2,300 characters), so near that cut G1 loses more of its tail (`feature_registry`,
  rendered last). No arm on this code has state sizes to match (block F matched B2's), so each run's `.check.txt`
  records its largest `planner_rounds.state_chars` and whether 20,000 was reached; reading 4 reports it per arm.

## Raw downloads (operator, Mac, into `~/Documents/Mila/Gene-Mila/data_downloads/clean_knowledge/`)

Saved under the names in the left column (the script checks they exist and are not empty). UNVERIFIED marks a URL
whose exact path may have moved; the operator records the URL actually used and the file's sha256 in the dated note.

| file | source |
|---|---|
| `goa_human.gaf.gz` | https://current.geneontology.org/annotations/goa_human.gaf.gz |
| `go-basic.obo` | https://purl.obolibrary.org/obo/go/go-basic.obo |
| `corum_allComplexes.txt` | CORUM current release, allComplexes: https://mips.helmholtz-muenchen.de/corum/download (UNVERIFIED path) |
| `string_physical_detailed.txt.gz` | https://stringdb-downloads.org/download/protein.physical.links.detailed.v12.0/9606.protein.physical.links.detailed.v12.0.txt.gz (UNVERIFIED path; new to this repository) |
| `string_info.txt.gz` | https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz (the file `genemila/data/knowledge.py` already uses) |
| `collectri.tsv` | https://omnipathdb.org/interactions?datasets=collectri&genesymbols=yes&loops=yes (as `knowledge.py`) |
| `reactome.gmt.zip` | copy of the existing raw knowledge directory's file (`data/raw/knowledge/reactome.gmt.zip` in the main checkout, from `prepare_data.py knowledge`); if absent, https://reactome.org/download/current/ReactomePathways.gmt.zip |
| `uniprot_human_reviewed.tsv` | the UniProt REST TSV URL in `tools/build_protein_annotation.py`'s docstring (field names TO BE VERIFIED there; the builder refuses a wrong header) |
| `gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz` | https://gnomad-public-us-east-1.s3.amazonaws.com/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz |
| `gencode.v27.gtf` | https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf (block F: sha256 26b81dd6…) |
| `hg38.fasta`, `hg38.fasta.fai` | https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta and `.fasta.fai` (block F: sha256 93157a16…) |

## Money

Andres approved the block on 16 October ("approved, do what you think is best") without naming an amount. The $20 cap
below is this plan's proposal; he may lower or veto it. **The chain waits until he has confirmed the cap in writing**
(recorded with its date in the dated note below and on the claim issue), as block F did; `AGENTS.md` names block G in
the pull request that carries this plan. The ledger overstates real cost about twofold (`AGENTS.md`). B2's runs cost
$1.29, $1.37 and $1.19 by the ledger; twelve runs are expected to cost about $14 to $16 by the ledger, about $8 billed.

- **Block cap:** the shared DeepSeek ledger (provider `deepseek` only) may rise by at most **$20** over its reading
  when the block starts. The operator writes the cap once, before the chain, into `block_g_cap.txt` as one line
  `<cap> <ledger at the start> <UTC date>`; the command refuses if the file exists, so a stopped or resumed block never
  gets a fresh $20:
  ```bash
  bash <<'EOF'
  L=~/Documents/Mila/Gene-Mila/genemila_scale_logs; LEDGER=~/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite
  s=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
  case "$s" in ''|*[!0-9.]*) echo "NOT DONE: ledger unreadable ('$s')"; exit 1 ;; esac
  set -o noclobber
  awk -v s="$s" -v d="$(date -u +%Y-%m-%dT%H:%MZ)" 'BEGIN { printf "%.2f %s %s\n", int((s + 20) * 100) / 100, s, d }' \
    > "$L/block_g_cap.txt" || { echo "NOT DONE: block_g_cap.txt exists; the cap is written once per block"; exit 1; }
  echo "- $(date -u +%Y-%m-%dT%H:%MZ) block G cap written: $(cat "$L/block_g_cap.txt") (cap, DeepSeek ledger at the start, UTC date)" >> "$L/progress.md"
  cat "$L/block_g_cap.txt"
  EOF
  ```
- Each run passes `--set budget.cumulative_usd.deepseek=<cap>` and starts only when the ledger plus its two caps
  ($2.50) stays within the cap, so the cumulative cap never binds mid-run. If the runs cost more than expected, the
  gate refuses a later run (exit 2) and the block ends incomplete, with the arms balanced by the chain order; what
  ran is reported as it is, and more money is a new dated section on Andres's word.
- The block stops, and the run becomes its own arm, when a run fails; costs more than $2.00, or the ledger cannot be
  read after it (or reads below its start); ends with `planner.mixed` true; or records a knowledge list other than
  the bundle's own (`run.external_knowledge` not empty).
- The key comes from `API_KEY` in Andres's `~/.zshenv`, as `DEEPSEEK_API_KEY` in the chain's own environment only;
  the run script unsets `API_KEY`. Never on a command line, in a file or in a log.

## Exact commands (Mac)

1. **State first.** Nothing may run beside a paid run or the comparison driver (`AGENTS.md`). Block F's readings
   must have finished (no `feature_compare` at nice 19 still going), and the conditions under Money must hold.
   ```bash
   python handoff_state.py --fetch --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs; pgrep -fl 'run_research.py|feature_compare.py|scale_seq.sh'
   ```
2. **The code.** The runs use a dedicated checkout `~/Documents/Mila/Gene-Mila/gene-mila-<G_COMMIT>` at `<G_COMMIT>`
   and clean, made without touching the main checkout (as block F's `gene-mila-ce1b530`; `G_WT=<path>` names another
   one), never the main checkout; the main checkout's `.venv` as before. The operator's clone of this branch is at a
   descendant of `<G_COMMIT>` that carries the filled-in `block_g_run.sh` and the dated note.
3. **Free preparation**, from the operator's clone, after the raw downloads. Builds the six tables and four bundles,
   refuses if any exists, prints the md5s and line lengths (into the dated note):
   ```bash
   bash docs/mac/block_g/prepare_clean_bundles.sh 2>&1 | tee ~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_g_prepare.log
   cp docs/mac/block_g/block_g_run.sh docs/mac/block_g/block_g_chain.sh ~/Documents/Mila/Gene-Mila/genemila_scale_logs/
   ```
4. **The cap**, as in Money, once.
5. **The chain**, detached, from a login zsh (block F's note of 02:05 UTC), the STOP file lifted for the block and
   put back after:
   ```bash
   cd ~/Documents/Mila/Gene-Mila/genemila_scale_logs
   screen -dmS blockg zsh -lc 'DEEPSEEK_API_KEY="$API_KEY" caffeinate -i bash block_g_chain.sh > block_g_chain.log 2>&1'
   screen -ls; pgrep -fl block_g_chain.sh; tail -3 block_g_chain.log
   ```
   - Order: `adamson_cf` g0 r0, g1 r0, g0 r2, g1 r2, g0 r3, g1 r3, then the same for `norman`. One run at a time.
   - `progress.md`, `block_g_chain.log` and each run's `.check.txt` say where it is; the `.check.txt` counts the
     features reading each of the three tables. Read no run's log end or `summary.md` before the readings.
   - Before spending, each run checks: the key; `G_COMMIT` filled in; the cap line (at most $20 over the start);
     the checkout at `<G_COMMIT>` and clean; no run directory or log; no STOP file; no stopped block; no lab run, no
     scaling driver and no `feature_compare` reading; the bundle (`verify_bundle` clean, `added_knowledge` empty,
     exactly the arm's files, the existing bundle's `split_id`, the knowledge summary within the code's
     knowledge-section budget); the ledger gate.
   - **Resume.** The chain skips a run whose `.passed` marker exists. A pre-run refusal (exit 1 or 2) is fixed and
     the chain restarted the same way; the cap file stays. A stop after a run (`block_g_stopped.txt`) is not
     resumed: the cause is written up here first.

## Readings, fixed now, made only after the chain has ended

Free, CPU only, after no lab run or driver is running; from the operator's clone of this branch at `<G_COMMIT>` or
later (never the main checkout), into its `docs/results/`. Per dataset `<ds>` in `adamson_cf`, `norman`:
```bash
M=~/Documents/Mila/Gene-Mila/gene-mila; C=<your clone>; ds=<adamson_cf|norman>; P="$C/docs/results/${ds}_g_plugins"
```

1. **Feature-level, G1 arm, primary (the two-stage rule of PLAN_F's amendment of 04:20 UTC, unchanged).** The
   per-run plugin directories are named `r0`, `r2`, `r3` and the stage sources `f_r0`, `f_r2`, `f_r3`, the names
   `tools/block_f_readings.py` expects (`SOURCES`), so the tool runs unchanged; one `--out` tree per dataset keeps
   the two datasets apart. The family is every plugin whose source reads any of the three tables.
   ```bash
   for s in 0 2 3; do mkdir -p "$P/r$s"; grep -lE 'gene_annotation|gene_constraint|protein_annotation' \
     "$M/runs/${ds}_g1_ds_w4_r$s/feature_store/"*.py | xargs -I{} cp -p {} "$P/r$s/"; done
   cd "$C"
   PYTHONPATH="$C" "$M/.venv/bin/python" tools/feature_compare.py --data "$M/data/${ds}_clean_tables" \
     --out docs/results/${ds}_g_stage1 --null-reps 0 \
     --source f_r0="$P/r0" --source f_r2="$P/r2" --source f_r3="$P/r3" \
     --source-run f_r0_selected="$M/runs/${ds}_g1_ds_w4_r0" --source-run f_r2_selected="$M/runs/${ds}_g1_ds_w4_r2" \
     --source-run f_r3_selected="$M/runs/${ds}_g1_ds_w4_r3"
   "$M/.venv/bin/python" tools/block_f_readings.py select --stage1 docs/results/${ds}_g_stage1/feature_compare.json \
     --plugins "$P" --out docs/results/${ds}_g_top --k 20
   reps=$("$M/.venv/bin/python" -c "import json; print(json.load(open('docs/results/${ds}_g_top/selection.json'))['null_reps'])")
   S2=(); for s in 0 2 3; do [ -d docs/results/${ds}_g_top/r$s ] && S2+=(--source f_r$s=docs/results/${ds}_g_top/r$s); done
   PYTHONPATH="$C" nice -n 19 "$M/.venv/bin/python" tools/feature_compare.py --data "$M/data/${ds}_clean_tables" \
     --out docs/results/${ds}_g_stage2 --null-reps "$reps" "${S2[@]}"
   "$M/.venv/bin/python" tools/block_f_readings.py pool --stage1 docs/results/${ds}_g_stage1/feature_compare.json \
     --stage2 docs/results/${ds}_g_stage2/feature_compare.json --plugins "$P" --out docs/results/${ds}_g_pooled_holm
   ```
   Stage 1 scores every row with no null; `m_total` is its status-ok add-one rows; stage 2 scores the top 20 by
   gain / SE_adj with `20·m_total − 1` replicates (at least 199); `pool` applies one Holm of size `m_total` with
   untested rows at p = 1. The `S2` loop leaves a `--source` with no top file out of stage 2 (block F's r2). Parent: the
   built-in start; fold seeds the tool's default; OOF tier only (no `--with-val1`). A plugin is scored with its
   class defaults; the run's tuned version appears only in the `_selected` rows. With `m_total` 0 the reading is
   negative without scoring. No Replogle split: the bundle has no screen, so the tool's `reads_replogle` column
   is "no" for every row and `found_tier1` equals `found`.
   - **Criterion, and its mapping onto `docs/GOAL_CRITERIA.md` A.1.** A row is found when `pooled_holm.json` says
     `found` (pooled Holm p ≤ 0.05 and no other failed criterion). A.1's parts are read from the tool's columns:
     "pooled Holm p ≤ 0.05 against the matched gene-permutation null" = `p_holm_pooled`; "mean gain above twice its
     overlap-robust SE" and "wins on more than half" = `other_failed` has no "M1 gain not above 2 SE_adj with
     wins > n/2"; "every fold-seed report positive" = no "an OOF report does not gain" and no "one fold seed"
     line; "a gain outside the targets" = no "no M2 gain"; "`mse_top` not worse" = no "mse_top significantly
     worse"; "source reads no perturbation screen" holds by construction (clean bundle). A.1
     is met for a dataset when at least one row is found there; the dated status line of `GOAL_CRITERIA.md` then
     names the row and run. A feature found on both datasets is a second-cohort observation, not A.3: A.2 (the
     mechanism and its sign) is written first, and the pre-registered replication is a later block.
2. **Arm against arm, development tier (descriptive).** One call per dataset rebuilds the six runs' selected models
   from their recorded features and params under the same parent and fold seeds; `data/<ds>_clean_tables` serves
   both arms (the tool checks `split_id`, and G0's models need no table):
   ```bash
   PYTHONPATH="$C" "$M/.venv/bin/python" tools/feature_compare.py --data "$M/data/${ds}_clean_tables" \
     --out docs/results/${ds}_g1_vs_g0 --null-reps 0 \
     --source-run g1_r0="$M/runs/${ds}_g1_ds_w4_r0" --source-run g1_r2="$M/runs/${ds}_g1_ds_w4_r2" --source-run g1_r3="$M/runs/${ds}_g1_ds_w4_r3" \
     --source-run g0_r0="$M/runs/${ds}_g0_ds_w4_r0" --source-run g0_r2="$M/runs/${ds}_g0_ds_w4_r2" --source-run g0_r3="$M/runs/${ds}_g0_ds_w4_r3"
   ```
   Reported: each run's `(set)` row (OOF M1 to M12, ΔM1 ± SE_adj over the start, wins), and per arm the mean ± sd of
   M1 and ΔM1 over its three runs. A run whose model cannot be rebuilt is named and its arm reported with fewer runs.
   No test; no difference is claimed that lies within either arm's spread. OOF is not held out for either arm.
3. **Per run, sealed**, with the tool from `$C` (at `<G_COMMIT>` or later, as the other readings); the reading rule
   as for B1, B2, B4 and F (a gain counts only
   above twice its paired SE with wins on more than half; categories under 10 perturbations reported, not read):
   ```bash
   for arm in g0 g1; do for s in 0 2 3; do PYTHONPATH="$C" "$M/.venv/bin/python" tools/sealed_reading.py \
     --runs "$M/runs/${ds}_${arm}_ds_w4_r$s" --out "docs/results/${ds}_${arm}_r${s}_sealed_reading.md"; done; done
   ```
   Adamson's sealed set has been read in every earlier Adamson block and is worn: its readings are indicative
   only. Norman's has been read for B1, B2, B4 and F; this is its fifth reading, said so in the report.
4. **Descriptive:** per run (from its `.check.txt` and plugin sources), the number of experiments and of selected
   features that read each table, which columns or keys they use, and the largest planner state (whether the
   20,000-character cut was reached), per arm.

Nothing is chosen from a sealed score. A positive reading 1 is a candidate, not a discovery
(`docs/NOVEL_FEATURE_NEEDS.md` §3–4, `GOAL_CRITERIA.md` A.2–A.5).

## To be filled in before the chain (dated notes go below this line)

- `<G_COMMIT>`: the integration head after the builder and the planner-state change are merged; the same commit in
  `block_g_run.sh`. Andres's written confirmation of the $20 cap (or the amount he names), with its date.
- The raw downloads' URLs as used and their sha256; the prepare script's output (md5 and line length per file).
- The cap record line, and the ledger reading at the start.

## Note, 2026-10-16 23:40 UTC: the code is `baa7dfd`; the cap awaits Andres's line; the readings wait for the corrected test

- **`<G_COMMIT>` = `baa7dfd`**, the integration head after PR #48 (the builder, this plan, the scripts and the
  planner-state change together, one pull request rather than the two the text above expected). `block_g_run.sh` now
  carries `G_COMMIT="baa7dfd"`; the runs use the dedicated checkout `gene-mila-baa7dfd` (step 2), and the operator's
  clone is at this note's commit or later. Full test suite at `baa7dfd`: 552 passed.
- **The cap:** $20 over the ledger's reading at the start, as Money says, decided by the lead under Andres's delegation
  of 16 October (`docs/ROADMAP.md`, D1). The chain starts only after Andres has written his one line on #41
  (ROADMAP, section 7, item 1); the operator records that line, with its date, below.
- **The readings wait for the corrected fair test** (`docs/ROADMAP.md`, D2): the gene-permutation null above cannot fail
  for a candidate that is a parent column times a per-perturbation number, and the 20·m − 1 rule puts the p floor at
  the cutoff. Reading 1 therefore uses `tools/feature_compare.py` and `tools/block_f_readings.py` at or after the
  commit of that fix, with the perturbation-level null and the family-wise max-gain correction in place of the text
  above under "Criterion"; the other criteria, readings 2 to 4, the arms, the chain, the caps and the stop rules are
  unchanged. The runs themselves do not depend on the tool, so the chain need not wait for it.
- **Known biology is pre-registered before reading** in `docs/PREREG_G_KNOWN_BIOLOGY.md` and
  `docs/CANDIDATE_LITERATURE_CHECK.md` (ROADMAP, D3); the run checkout `baa7dfd` predates them, so the agents never see
  them.
- **Raw downloads:** the nine files are on the Mac with URL, UTC time and sha256 receipts (issue #47, 21:50 UTC; the
  CORUM file comes from the project's public API, the static path having moved). The operator stores them under the
  names in the table above and commits the receipts as `docs/mac/block_g/downloads.md`.
- Still to be filled in by the operator, below: Andres's cap line and its date; the prepare script's output (md5 and
  summary-line length per file); the cap record line and the ledger reading at the start.
- **2026-10-17, reading 1 under the corrected tool** (`docs/ROADMAP.md` D2, the `tools/feature_compare.py` and
  `tools/block_f_readings.py` of that fix): the `select` command above drops `--k 20` (the family-wise step-down needs
  every stage-1 row; `select --k` is now refused without `--partial`, and `pool` marks a stage 2 that omits a stage-1
  row `partial` and finds nothing), `reps` from `selection.json` is 999 or more, and under "Criterion" the column is
  `p_fwer_pooled` (the pooled max-gain step-down p), with `p_fwer_pert_pooled` ≤ 0.05 also required for a row
  proportional to a parent column and the gain above max(2 SE_adj, 0.002); `p_holm_pooled` is no longer written.
  The rest of reading 1 and readings 2 to 4 are unchanged.

## Operator note, 2026-10-17 01:52 UTC: cap confirmed and written once

Andres directly instructed Astra to use the confirmation recorded on #41 and start G when the corrected F re-read
is not running. The confirmation is dated **17 October 2026, 01:46 UTC**, recorded by Claude in
[#41/comment6228138730](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6228138730):

> **Block G's cap is confirmed**: the ledger may rise at most **$20** over its reading when the block starts, inside the balance he has given (`docs/PLAN_G_CLEAN_ARM.md`, Money; `docs/ROADMAP.md` D1). Operator: copy this line and its date into the plan's dated note, write `block_g_cap.txt` as the plan says, and start the chain under the timing rule of my 01:30 UTC comment (never beside the block F re-read).

The Money section's write-once command succeeded, recording this immutable line in
`~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_g_cap.txt` and appending its receipt to `progress.md`:

```text
67.26 47.264645 2026-10-17T01:52Z
```

This is the cumulative ledger ceiling, original ledger reading, and UTC creation date. It is not reset on a resume.
No paid G run has started at this checkpoint. The corrected F re-read has not started either: G will run first,
after the required free bundle preparation passes, then the corrected F re-read after the chain ends and no lab
run or driver remains. The dedicated research checkout stays clean at `baa7dfd`; this note changes no scripts,
run code, arms, data rules or reading criteria. Raw receipts are in `docs/mac/block_g/downloads.md`; the full
prepare output and its checks will be appended before the chain starts.

## Operator note, 2026-10-17 02:03 UTC: preparation refused; no chain started

The unchanged preparation script ran once from validated own checkout `gene-mila-string-header` at `d34bd93`
([draft PR #54](https://github.com/andresloak100/Gene-Mila/pull/54)). The compatibility patch accepts STRING's actual
`experimental` header; the research checkout remains clean at `baa7dfd`. Required validation passed: 589 tests,
one optional integration skip, eight existing warnings, 720.81 seconds, exit 0. Credentials were unset for preparation.

Preparation exited **1** at its shared-knowledge determinism check:

```text
NOT DONE: gene_sets.json differs between norman_clean and norman_clean_tables; the builder is not deterministic
```

The six per-gene tables were written under `data_downloads/clean_knowledge/tables/{norman,adamson_cf}`.
`data/norman_clean` and `data/norman_clean_tables` passed their individual checks and were renamed from `.partial`;
the subsequent cross-arm `gene_sets.json` byte comparison refused. Neither Adamson clean bundle was built.
No partial bundle remains, no G run directory/log exists, the chain scripts were not copied or started, STOP remains
present, and corrected F has not started. Existing source bundles and all new outputs are preserved unchanged.
The final MD5/line-length recording loop was not reached, so its complete output is not claimed.

The full stdout/stderr is preserved verbatim in [prepare_20261017T0201Z.txt](mac/block_g/prepare_20261017T0201Z.txt),
SHA256 `3a5bf5cf4ce797d7f4c9331ae2ad17ea5b89c637fffef97c5f238bff7169803f`, and live `block_g_prepare.log`.
The cap stays `67.26 47.264645 2026-10-17T01:52Z`; no new paid call occurred.
Do not repeat preparation over its existing outputs, change the inputs/criteria/run pin, or bypass the failed check.
The immediate next step is a read-only diagnosis of the public knowledge difference and a reviewed recovery
that preserves the existing files; the chain and corrected F remain held.

Read-only diagnosis (independently repeated by Astra and a second reader): both `gene_sets.json` files have
5,773 identical keys and equal list values, but 2,293 dictionary key positions differ, all in the GO sections.
`go_curated()` iterates the set from `_ancestors()`; separate Python processes use different hash iteration orders,
and `build_clean_bundle.py` writes the insertion order without sorting. The other four shared knowledge files
are byte-identical. Canonical compact sorted-JSON SHA256 is the same for both:
`738be120526d87f75970fdddb1f45d1620e060dcd364498e9db23f9ed0e160be`.
Raw hashes and absolute paths are in [the diagnosis receipt](results/block_g_prepare_refusal_20261017.json).
The failed check is valid: plugins can observe order. A minimal stable GO-ordering source fix and regression
are needed before any rebuild; do not edit the existing files or their manifests to force a pass. The proposed
recovery preserves both unused Norman bundles and both table directories unchanged under dated archive names,
then reruns the original preparation from a reviewed, tested operator checkout, retaining the same cap and run pin.
No archive, source fix, retry, paid G run or corrected F re-read has been performed at this checkpoint.

## Andres's direct instruction, 2026-10-17 02:15 UTC: merge before rebuilding

> Open the ordering fix as a pull request into the integration branch; Claude merges it when its tests pass. Rebuild the bundles from a clone at that merge, then start the chain, and run the block F re-read after the chain ends.

This supersedes the earlier proposed use of an unmerged operator checkout for the ordering recovery.
Astra opens the ordering fix as its own PR (dependent on header compatibility PR #54). Claude merges the fixes;
Astra never merges its own PR. The rebuild waits for the ordering PR's actual integration merge commit and uses
a clean own checkout at that commit. Existing unused outputs remain unchanged until that gate. The original
`baa7dfd` research pin, cap record and G-before-F timing stay fixed. No rebuild or paid run has begun.

## Operator note, 2026-10-17 02:37 UTC: rebuilt at the merged ordering fix; all preparation checks pass

Claude merged ordering PR #55 at 02:31:40 UTC, commit `a77e0ff2d79dc27924eeab08cfad390c076cc1d3`.
Following Andres's direct instruction, Astra rebuilt from a clean own checkout at that exact merge,
`gene-mila-g-prep-a77e0ff` / `astra/block-g-preparation`. Relevant code matches tested `b8d80fe` exactly
(590 tests passed, one optional skip; no new suite run claimed here). Independent source/pin/script review passed.

The two UNUSED first-attempt Norman bundles, both table directories and first preparation log were renamed
unchanged with suffix `.stale-20261017T023543Z`, never deleted or overwritten. Device/inode preservation is
recorded in [archive_20261017T023543Z.jsonl](mac/block_g/archive_20261017T023543Z.jsonl); children, private labels
and splits were not opened for archiving. Original source bundles were not renamed or edited.

The unchanged preparation script then ran once with credentials unset and exited **0** (session19476).
All six tables and four bundles passed the prescribed checks: same source split, exact knowledge files,
manifest verification, empty added knowledge, fixed GO evidence codes, byte-identical copies outside knowledge
and manifest, and all five shared knowledge files identical between G0/G1. Both datasets' Replogle file is absent.
Full stdout/stderr is preserved in [prepare_20261017T023543Z.txt](mac/block_g/prepare_20261017T023543Z.txt),
SHA256 `408c0e8b80f5693db93b33d46e2918718fb4009cad35dcd2e3d4535c4b3dba3a`. The complete final MD5/line-length record follows, before any G run starts:

```text
== norman_clean
a371f8a284d011e81efe78792f99aca2 ./gene_sets.json
300d37d2a2b19f7f0511b8b8c8e643a7 ./ppi_network.json
f8e5a3dbd20c5f57a95456ca73e8ff7d ./prior_network.json
3d2d0315668bd31b7b1949d0c2d3dc68 ./targets.json
977acfad1aa9d63131ebb7167d6ffd59 ./transcription_factors.json
  gene_sets.json: knowledge-summary line 118 characters
  ppi_network.json: knowledge-summary line 57 characters
  prior_network.json: knowledge-summary line 53 characters
  targets.json: knowledge-summary line 49 characters
  transcription_factors.json: knowledge-summary line 44 characters
  whole knowledge summary: 329 characters
== norman_clean_tables
69fd252c113b3d72911a64842c05fe81 ./gene_annotation.json
37734b9a50b4777037d0dfe3f2e122e8 ./gene_constraint.json
a371f8a284d011e81efe78792f99aca2 ./gene_sets.json
300d37d2a2b19f7f0511b8b8c8e643a7 ./ppi_network.json
f8e5a3dbd20c5f57a95456ca73e8ff7d ./prior_network.json
c148d7462bf44ec89d90e63e6d6b1dec ./protein_annotation.json
3d2d0315668bd31b7b1949d0c2d3dc68 ./targets.json
977acfad1aa9d63131ebb7167d6ffd59 ./transcription_factors.json
  gene_annotation.json: knowledge-summary line 895 characters
  gene_constraint.json: knowledge-summary line 650 characters
  gene_sets.json: knowledge-summary line 118 characters
  ppi_network.json: knowledge-summary line 57 characters
  prior_network.json: knowledge-summary line 53 characters
  protein_annotation.json: knowledge-summary line 846 characters
  targets.json: knowledge-summary line 49 characters
  transcription_factors.json: knowledge-summary line 44 characters
  whole knowledge summary: 2726 characters
== adamson_cf_clean
e6d0c6a576440f10feece6a00744017f ./gene_sets.json
185b66ad5aa3028ec4010c8e55bb4877 ./ppi_network.json
0d112bba005a3d611fd64c238cb3208c ./prior_network.json
336a4e84c5f79c032fc109a70be1242f ./targets.json
66a90a708dbc8027e4a3ecd597f81d12 ./transcription_factors.json
  gene_sets.json: knowledge-summary line 109 characters
  ppi_network.json: knowledge-summary line 57 characters
  prior_network.json: knowledge-summary line 55 characters
  targets.json: knowledge-summary line 50 characters
  transcription_factors.json: knowledge-summary line 45 characters
  whole knowledge summary: 324 characters
== adamson_cf_clean_tables
3bcc3d8fd55adb656f9c77bf589de7be ./gene_annotation.json
e4a8b96126cceca780f30c30789b85da ./gene_constraint.json
e6d0c6a576440f10feece6a00744017f ./gene_sets.json
185b66ad5aa3028ec4010c8e55bb4877 ./ppi_network.json
0d112bba005a3d611fd64c238cb3208c ./prior_network.json
7ee3dccebc91de2708b443cc4b987260 ./protein_annotation.json
336a4e84c5f79c032fc109a70be1242f ./targets.json
66a90a708dbc8027e4a3ecd597f81d12 ./transcription_factors.json
  gene_annotation.json: knowledge-summary line 895 characters
  gene_constraint.json: knowledge-summary line 650 characters
  gene_sets.json: knowledge-summary line 109 characters
  ppi_network.json: knowledge-summary line 57 characters
  prior_network.json: knowledge-summary line 55 characters
  protein_annotation.json: knowledge-summary line 846 characters
  targets.json: knowledge-summary line 50 characters
  transcription_factors.json: knowledge-summary line 45 characters
  whole knowledge summary: 2721 characters
done: four bundles under /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/; tables under /Users/andresarriaga/Documents/Mila/Gene-Mila/data_downloads/clean_knowledge/tables
```

The cap remains `67.26 47.264645 2026-10-17T01:52Z`; research code stays pinned clean at `baa7dfd`.
No paid G run or corrected F re-read has started at this checkpoint. Next: unchanged scripts, final process/pin/
cap gates, detached G chain; post every run progress line on #41. Corrected F follows only after the chain ends.
