# Plan DK: the dark genome. Can a model trained on well-studied genes predict knockdowns of genes nobody has studied?

Written 2026-11-01 by the lead (claim #41) on Andres's "yes" in the project chat (1 November). Status: a protocol.
Nothing in it has run, no cohort file has been read for it, and no tool it names as "to build" exists yet. A decision
here changes only by a dated note at the end. It merges with plan R (`docs/PLAN_R_FRESH_TEST.md`): the dark genes
are the fresh test's held-out set.

## 1. Why

Every block so far ends at the same place. The agents' only working idea is response transfer between related
targets, and the tier-1 sources they read (Reactome, GO, CORUM, CollecTRI, STRING) say which targets are related only
for genes someone has studied (`docs/PREPRINT_DRAFT.md`, sections 3.1 to 3.5). Dark genes are exactly where that
knowledge runs out. So the question becomes testable as an interaction:

- **H1.** On dark genes, features read from curated knowledge lose most of their gain, and features read from
  data-driven gene embeddings keep more of theirs.
- **H2.** An agent arm with embeddings beats the same embeddings used directly in the standard linear baseline, on
  dark genes. Without H2 the agents add nothing to the embeddings.

If H1 and H2 hold, the winning model's learned similarity names, for each dark gene, the well-studied genes and
complexes it behaves like. Those are functional hypotheses for uncharacterized genes, which the wet-lab candidate
tool (`tools/wetlab_candidates.py`) turns into experiments. If they fail, the paper states where knowledge-based and
embedding-based prediction both stop.

## 2. Data

Replogle et al. 2022 K562 CRISPRi, the genome-wide file (Zenodo 13350497, md5 `13db594f8f1d2ccb88fec44a13e414dc`).
It has been on the Mac since 10 October, so the dark set is held out by protocol, as plan R section 1 states. Only
single-gene labels are used.

**Eligibility** is computed from metadata and the control and training cells only, by the manifest tool:
- at least 25 cells;
- the target gene among the measured genes;
- the knockdown verified on the target's own expression (Replogle's annotation if the file carries it, otherwise
  measured by the holder).

**Darkness** is fixed before any label is read, from public metadata only. One table records every gene's
publication count (NCBI `gene2pubmed`) and its count of GO biological-process annotations with experimental evidence
codes (EXP, IDA, IPI, IMP, IGI, IEP), with the download date and file hashes.
- **dark**: at most 20 publications and no experimental GO biological-process annotation;
- **lit**: at least 200 publications;
- the genes in between are used for training only.

Sensitivity analyses are fixed in advance: dark at 10 and at 50 publications.

## 3. Split (manifest tool, seed drawn and posted on #41 before the build)

| tier | genes | who reads labels |
|---|---|---|
| train | 1,000 drawn from lit and intermediate eligible targets | the lab |
| visible validation | 250 drawn from the same pool | the lab's controller |
| sealed, dark | every eligible dark target, up to 300 drawn | the holder (plan R); otherwise the capped `QueryOracle` |
| sealed, lit | lit targets matched to the dark set by the holder's strength measure, as many as the dark set | same |

- The gene panel is the 2,000 most variable genes, computed on control and training cells only.
- No dark target's cells are read to build the bundle.
- **The phenotype filter for the sealed sets** is applied by the holder, identically for every arm: the number of
  genes changed at FDR 0.05 against controls. The primary set is targets with at least 10 changed genes, and all
  eligible targets are reported as secondary. The filter reads the held-out data but no model, the same kind of
  filter as Replogle's own "strong phenotype" set.
- **If no holder is named** by the time the bundle is built, the sealed tiers sit in `private/` and are read once by
  the capped oracle, as for Adamson. That fallback is weaker and the paper says so.

## 4. Sources

- **Tier 1, curated:** the clean sources of block G, unchanged (`tools/build_clean_bundle.py`).
- **Tier E, embeddings.** Each source enters only after its training data is checked for perturbation screens and the
  result is recorded:
  - ESM-2 (650M) mean-pooled protein embeddings, sequence only (`tools/build_protein_similarity.py` already computes
    protein similarity; extended to the embedding itself);
  - scGPT whole-human gene embeddings, pretrained on observational CELLxGENE data;
  - GenePT gene-summary embeddings, a sensitivity source only: NCBI summaries can describe knockdown results.
- **Never:** another perturbation screen (Replogle itself beyond training, DepMap, Adamson, Norman). Such a source
  carries the answer; block F showed why.

## 5. Arms (Replogle bundle, 20-minute runs, DeepSeek v4-pro planner, 4 workers, seeds 0, 2, 3)

| arm | what | cost |
|---|---|---|
| L0 | linear baseline, PCA gene embedding (`run_linear_ae.py`) | free |
| LE | linear baseline with the tier-E embedding as the perturbation embedding (to build: a `--embedding` option) | free |
| C0 | no-LLM control with tier 1 and tier E | free |
| K | lab, tier 1 only | paid |
| E | lab, tier E only | paid |
| KE | lab, tier 1 and tier E | paid |

There are nine paid runs, about $1 each on the ledger. The cap is $15 over the ledger's reading at the block's start,
and the block starts only on Andres's cap line on #41. All runs are scored by `tools/fresh_test_score.py` (or the
oracle in the fallback), once.

## 6. Readings, fixed now

Primary metric: pearson_delta on the sealed dark set, mean ± sd over seeds. The paired reading rule is the lab's: a
gain above twice its paired SE, with wins on more than half the targets.

1. **H1:** (E − K) on dark minus (E − K) on lit, paired per seed, with a bootstrap over targets. H1 holds if this is
   positive and its interval excludes 0.
2. **H2:** E − LE on dark by the reading rule, in every seed.
3. **The discovery claim** needs H2, plus at least one agent feature built on a tier-E source that passes the
   corrected fair test (GOAL_CRITERIA A.1) on training and visible data only. Then, for each sealed dark gene, the
   top 5 training genes by that feature's learned similarity are frozen and hashed with the predictions before the
   reveal, and published with the score as hypotheses. Any wet-lab candidate is chosen from them by
   `tools/wetlab_candidates.py`.
4. All three readings are reported as they come out, including H1 and H2 failing.

## 7. To build (free, before any paid run)

1. `tools/build_darkness_table.py`: the publication and GO-evidence table, with tests.
2. A darkness role in `tools/replogle_slice_manifest.py`: dark, lit and training pools from that table, plus the
   lit-matching rule.
3. A Replogle bundle builder from the manifest (extending `tools/build_clean_bundle.py`). It reads no cells of a
   sealed target.
4. Tier-E tables: ESM-2 and scGPT gene embeddings as feature-API tables, each with its provenance check.
5. An `--embedding` option for `tools/baselines_dl/run_linear_ae.py` (arm LE).
6. A free scripted dry run of the whole chain on a synthetic bundle.

## 8. Open, for Andres

- The holder (shared with plan R). Without a holder the fallback in section 3 applies.
- The cap line for the nine paid runs ($15), when the free build is done.
