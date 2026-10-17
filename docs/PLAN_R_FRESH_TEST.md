# Plan R: the fresh test on Replogle 2022 K562 CRISPRi, commit then reveal

ROADMAP D7 (`docs/ROADMAP.md`), serving GOAL_CRITERIA A.3, A.4, B.3 and B.4. Status: a protocol, fixed before any
deposit. Nothing in it has run. No cohort file has been read for it, no prediction has been deposited, no holder is
named, no seed exists. The "to be filled in" list at the end says what is missing. A decision here changes only by a
dated note at the end.

## 1. Who holds what

- The holder: Andres's ML collaborator, named by Andres on #41 (GitHub handle to be filled in). The holder obtains
  the cohort file from the public record (section 2), never from the Mac or from any agent, records its sha256 on
  #41, and keeps the file and every score on a machine no agent can reach. The holder scores the one deposit once
  and posts two dated reports, R1 first and R2 second (section 7); nothing changes between them.
- The Mac (Astra, under Andres): builds the eligibility manifest from metadata (section 3), produces the frozen
  predictions (section 5), posts hashes on #41 before any reveal.
- The lead (Claude, #41): fixes this plan, the batch and the reading rule before the deposit; reads nothing from
  the holder before the deposit hashes are on #41.
- Andres: names the holder, says yes or no to commit then reveal, and says whether the holder receives
  per-perturbation means or cells (ROADMAP section 7, item 2).

Physical access, to be stated in the paper: the raw genome-wide file `ReplogleWeissman2022_K562_gwps.h5ad`
(Zenodo 13350497, md5 `13db594f8f1d2ccb88fec44a13e414dc`; 1,989,578 cells by 8,248 genes) has been on the Mac since
10 October 2026 at the latest (the knowledge file built from it is dated "built 2026-10-10" in
`docs/results/external_replogle2022_k562_v2.md`; `docs/LAB_STATE.md` records Andres's choice of the screen on
11 October). That knowledge file, `replogle2022_k562.json`, was first built into the Adamson development bundle
(`data/adamson_cf/knowledge/`, LAB_STATE.md: 82 bundle targets with a row; three Adamson runs with it are listed
there), then into the Norman bundle (`docs/results/external_replogle2022_k562_norman.md`) and the B1 frozen export
(`docs/results/norman_frozen_export_20261013/manifest.json` lists `context/knowledge/replogle2022_k562.json`). So the
Adamson development arms, the modality this test scores, read it too. It holds the Replogle responses of each
development bundle's own targets, which section 3 excludes from every slice. The test is therefore held out by
protocol and by the holder, not by physical separation of the raw file from the Mac. The manifest tool writes this
statement into every manifest.

## 2. The cohorts

Replogle et al. 2022 (Cell, "Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq")
ran two K562 CRISPRi experiments: the genome-wide library (the file above, 9,867 distinct labels in
`obs['perturbation']`, 75,328 control cells; `docs/results/external_replogle2022_k562_v2.md`) and the essential-gene
library (a separate, smaller file; its availability, size and public location are UNVERIFIED here and are what
ROADMAP section 8 asks Astra to check before this section is fixed).

- A.3, replication (R1): the essential-gene file, if it is available and its eligible count passes section 3.
- A.4 and B.3, the fresh test (R2): the genome-wide file. The essential-gene library is a subset of the genome-wide
  one, so R2 excludes every target eligible in R1: the R2 manifest is built with `--exclude r1=<R1 manifest.json>`
  (the tool reads the eligible symbols of a manifest it wrote; reason `r1 target`). Without this, the R1 report
  would disclose how every deposited model does on much of R2 before R2 is read, and A.4 calls R2 a fresh test. The
  cost is that R2 loses the essential genes, so its in-distribution count (section 3) is checked after the exclusion.
- Fallback, if only the genome-wide file is available: two disjoint halves of its eligible targets, drawn by the
  manifest tool with `--role both` (within the in-distribution targets and within the rest, R1 takes the even ranks
  and R2 the odd ranks of the draw, as section 3 defines). This is weaker: the two slices share the
  experiment, its batch structure and its controls, so a replication on R1 does not show that a feature survives a
  change of library and run. The paper states this if it is used.

Adamson 2016 is K562 CRISPRi, the same modality, so the scored arms are the Adamson arms. Norman (CRISPRa) gets no
fresh test (ROADMAP D7). A target of either cohort that the frozen models never saw is still a single-gene CRISPRi
knockdown in K562, which is what the Adamson models predict; combinatorial labels are excluded.

## 3. Eligibility and the in-distribution subset

`tools/replogle_slice_manifest.py` (tests in `tests/test_replogle_slice_manifest.py`) reads only the file's obs and
var tables through a guard that refuses every other key (X, layers, obsm, raw, uns), so no expression value enters
any choice. For each label it records the cell count, the mapped symbol and the exclusion reasons:

- a target of the Adamson bundle (88 knockdowns, `README.md`; ROADMAP D7 says 90, and the manifest records the count
  it reads) or the Norman bundle (102 targets), by `knowledge/targets.json` of the clean bundles, matched on the raw
  and the mapped symbol; with `--hgnc` each set also matches under the one-to-one current and retired HGNC forms of
  its symbols, so a target written under a retired symbol still catches a cohort label under the current one;
- outside the frozen gene universe (the `genes` list of the arm's frozen export manifest; Adamson's bundle measures
  2,055 genes);
- fewer than 20 cells;
- a label that does not name exactly one gene. Tokens that are not gene names and look like guide suffixes
  (`_guide1`, `_sg2`, the ingest's rule in `genemila/data/external_screen.py`) or Ensembl ids are dropped first and
  recorded in the mapping note; a gene name is never dropped. What remains must be one symbol.

Symbols: the universe keeps the symbols of the 2016 bundle, so with `--hgnc` (HGNC complete set) a retired cohort
symbol maps to its one current symbol (and on to the one retired symbol the universe uses for that gene, when the
current one is not in the universe), and a current cohort symbol maps to the one retired symbol the universe uses
(SRPRA to SRPR); aliases are never used; an ambiguous mapping is recorded and not applied. The same mapping gives the
common gene panel: the universe genes the cohort measures through exactly one var column, in universe order, each
with the cohort's own var symbol beside it (`common_gene_panel.genes` and `.cohort_symbols`), so the holder aligns
the cohort's columns from the manifest alone. A universe gene matched by several cohort columns is listed under
`common_gene_panel.ambiguous` and left out. The panel is recorded in the manifest and used for every metric.

In-distribution: a target that shares at least one Reactome or CORUM class with a target of the Adamson training
panel, the classes taken from the clean bundle's `knowledge/gene_sets.json` (`REACTOME:` and `CORUM:` sets; GO sets
do not count). The panel is the bundle's whole target list; no split file is read. Eligible targets outside those
classes are the out-of-distribution subset, reported separately and never pooled with the in-distribution reading.

Minimum n: at least 30 in-distribution eligible targets in R2, else B.3 and B.4 are reported as not powered
(ROADMAP section 8) and the out-of-distribution subset is reported descriptively. The same floor applies to R1 for
A.3.

The draw: `--draw --seed '<value>' --role {both,r1,r2}`. The seed is one public string named in section 8 before the
file is opened for the manifest (for example the hash of a Bitcoin block at a stated future height, or a NIST
Randomness Beacon pulse at a stated time). The rank key of a symbol is sha256(seed + newline + symbol), ascending, so
anyone can recompute the order with sha256sum. With `--role both` the halves alternate ranks within the
in-distribution targets and within the rest. The manifest's sha256 is printed and posted on #41.

## 4. The batch (ROADMAP D8)

Only clean arms are scored: arms whose bundle holds no perturbation screen. On Adamson these are block G's G1 and G0
runs (`docs/PLAN_G_CLEAN_ARM.md`), the one-worker lab row, the two foreign arms of block H, CellForge's translated
ideas (C2), the scripted no-LLM control and the additive rule. Every earlier Adamson arm ran on a bundle holding
`replogle2022_k562.json` and is out. Per arm: the three selected system models (one per seed), at most three single
features, each as a frozen export. The batch, with every model's export manifest sha256, is posted on #41 before any
contact with the holder; nothing is added after.

## 5. The deposit

For every eligible target of the slice (R1 and R2 alike), every model in the batch predicts through
`tools/frozen_model.py predict-targets` (section 6): one condition per target, named by its symbol, giving the mean
delta over the frozen gene universe on the original public control scale. The deposit is one archive:
`manifest.json` and `manifest.md` of section 3, one `predictions.npz`, `receipt.json` and `queries.json` per model
(the receipt's `query_sha256` pins the query file, so it is kept), the batch list, and `genes.txt` (the common gene
panel, two columns: universe symbol and cohort symbol). Its sha256, and the sha256 of every file inside, are posted on
#41 before the holder is told the archive exists. The holder receives the archive after that post and checks the hashes first.

What the holder receives from the cohort side is only what Andres says: per-perturbation means (the default; the
holder computes them from the raw file) or cells. The Mac never sends cohort data.

## 6. The adapter

`tools/frozen_model.py` already predicts target-only queries from a frozen export without fitting, refusing a target
outside the frozen gene universe (`genemila/frozen.py`, `docs/FROZEN_EXPORT.md`). This plan adds
`predict_targets(package, manifest_sha256, conditions, out)` and the `predict-targets` command (one single-target
condition per `--target SYMBOL`) in `tools/frozen_model.py`, a wrapper over that path; `genemila/frozen.py` is
unchanged, since its bytes are part of every existing export's runtime pin. No control profile is accepted: the
delta is on the original context's control scale, and the cohort's own control enters only on the holder's side.

Gate before any deposit date (ROADMAP D7): the adapter reproduces an arm's saved predictions bit for bit on its own
conditions. For B1 this was done on 13 October (`docs/results/norman_frozen_export_20261013/report.md`: three members
exact, ensemble within 5.96e-08). The saved arrays are local to the Mac, not in the repository, so the repository
test (`tests/test_frozen_model.py`, `test_predict_targets_matches_the_query_path_and_refuses_outside_the_universe`)
reproduces the synthetic fixture's saved delta and a new target through the strict query path. For each Adamson arm
in the batch the same reproduction runs on the Mac with the verification driver's rule (rtol = atol = 1e-6), and its
summary goes under `docs/results/` before the deposit.

## 7. Scoring and reading

The holder computes, from the cohort's own cells, the per-perturbation mean log-normalised expression and the
control mean (the ingest's normalisation: log1p of 10,000 times counts over the cell total), the true delta on the
common gene panel, and scores each deposited model with the evaluator's existing metrics unchanged
(`genemila/benchmark/`): `pearson_delta` as primary; MSE, PCC and R² on all panel genes and on the top-20 DE genes;
direction accuracy on the top-20 changed genes; the DE definition named beside each. Predicted expression for the
expression metrics is the cohort control mean plus the deposited delta.

Reading, paired per perturbation, fixed here:

- A.4 (a feature): the model with the feature against its parent, gain in `pearson_delta` above twice its paired
  standard error and wins on more than half the perturbations (GOAL_CRITERIA A.4), on the in-distribution subset of
  R2, the predicted sign of A.2 checked on the feature's coefficient as deposited.
- A.3 (replication): the same rule on R1, posted before the R2 reading (below).
- B.3 and B.4 (arms): each arm's three system models against each baseline under `tools/arm_reading.py`'s rule
  (G above k·SE, SE = sqrt(S² + sd_g²/R), one sign, most wins), on the in-distribution subset of R2; the
  out-of-distribution subset is reported beside it.
- Holm over the batch: every paired comparison in the batch, features and arms, enters one Holm correction at 0.05;
  nothing outside the posted batch is tested.

The holder posts two dated reports on #41, both from the same deposit and the same scoring run, with nothing
changed between them: first the R1 report, then the R2 report. Each gives every metric for every deposited model,
both subsets, the paired differences, their standard errors, win counts, the Holm-adjusted p-values (one Holm
correction over the whole batch, R1 and R2 together, so the R2 report repeats the R1 values unchanged), the cohort
file's sha256 and the deposit's sha256. Then nobody refits, re-exports, adds a model, changes a rule or deposits
again. A second deposit on either
cohort is a second test and needs its own plan, its own seed and a new slice disjoint from these. The report goes
into `docs/results/` as posted, unedited.

## 8. To be filled in, before the manifest is built

- Holder: name and GitHub handle (Andres).
- Andres's yes or no to commit then reveal, and means or cells (ROADMAP section 7, item 2).
- The essential-gene file: public location, size, sha256; or the fallback of section 2 declared. The lead confirms
  the rule that R2 excludes R1's eligible targets (section 2) once the R1 eligible count is known.
- The seed: its public source, the exact future height or time, and, once it exists, the value.
- The gene universe: which export's `manifest.json` (the Adamson arm's) fixes it, with that manifest's sha256.
- The batch list with every export manifest's sha256 (section 4), posted on #41.
- The manifest's sha256 (section 3), the deposit's sha256 (section 5), the cohort file's sha256 as the holder reads
  it, and the dates of each post.
- The reproduction summaries of section 6 for every arm in the batch.
