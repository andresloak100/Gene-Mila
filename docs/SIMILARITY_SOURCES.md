# Two tier-1 similarity sources: paralogs and protein-sequence embeddings

Claim [#74](https://github.com/andresloak100/Gene-Mila/issues/74), 18 October 2026. Code: `tools/build_paralogs.py`,
`tools/build_protein_similarity.py`; tests `tests/test_similarity_builders.py` and the round trip in
`tests/test_clean_bundle.py`; the clean bundle takes the files through `tools/build_clean_bundle.py --table`
(`genemila/data/knowledge_clean.py`, `NETWORK_NAMES` and the two new `TABLE_NAMES`). Off by default: a bundle built
without them is unchanged, and nothing in the run code changes.

## 1. Why these two

`docs/results/ceiling_analysis.md` says the limit is information, not search: the hindsight copy of the most similar
training knockdown reaches 0.66 and the hindsight linear mix of other responses 0.78, against 0.60 to 0.65 out of
fold, and the gap sits in knockdowns with no close relative in training. Every winning model carries one family, the
response of training perturbations whose targets resemble the new target through gene sets, interaction partners or
co-expression; block G added complexes, regulations and physical interactions, and the agents found nothing that
passes the fair test on either dataset. What has never been given to the agents is a similarity that does not come
from annotation or from expression:

- **Paralogy** (Ensembl Compara): gene duplication inferred from protein sequence trees. Named in tier 1 of the
  data-source policy (`docs/NOVEL_FEATURE_NEEDS.md` section 7, "paralogs (Ensembl Compara)") and never built. A
  paralog in training is a candidate relative of a new target that no curated set may connect; a target's own paralogs
  among the measured genes are a gene-side relation (duplicate genes that a knockdown may spare, or that may
  compensate). Both change the pattern across genes, which is what `pearson_delta` reads.
- **Protein-sequence embeddings** (UniProt's per-protein embeddings of the human reference proteome): a protein
  language model's vector of each protein from its amino-acid sequence alone. Two proteins with similar vectors share
  folds, domains and often function, including pairs too diverged for Ensembl to call paralogs and pairs no set
  connects. Sequence only, so tier 1 by the policy's rule ("measured or derived without perturbing genes and does not
  contain the expression responses the lab predicts"), though the policy's table does not name it: the lead confirms
  the tier before a run uses it, and a run with it is its own labelled arm either way.

Both were put to the lead on #41 (comment of 17 October, 21:47 UTC, items 1 and 2) before being built. They describe
the data; they propose no feature, so a feature an agent builds on them still counts under A.1 of
`docs/GOAL_CRITERIA.md`, and the fair test (`docs/FEATURE_COMPARISON_PROTOCOL.md`) decides whether it is evidence.

## 2. The files

All four are self-describing JSON (a `description` the planner reads in the knowledge section, `columns`, a `source`
record with the input files' sha256, URL, release and parameters, and `unmatched`, the bundle genes the source does
not name). Only the bundle's genes appear (`--genes-from`), as in the three block G tables.

| file | shape | built by |
|---|---|---|
| `paralogs` | `edges: [gene_a, gene_b, identity_a, identity_b, lca, homology_type]`, each measured pair once with `gene_a < gene_b`; `identity_a` the fraction of gene_a's protein identical to gene_b's, `identity_b` the reverse; `lca` the taxon of the duplication; Ensembl's `homology_type` | `build_paralogs.py --out` |
| `paralog_annotation` | per-gene table: `n_paralogs` (human paralogs, measured or not), `n_within_species_paralogs`, `max_identity`, `n_paralogs_measured`, `max_identity_measured`; zeros for a gene with none | `build_paralogs.py --table-out` |
| `protein_similarity` | `edges: [gene_a, gene_b, cosine]`: the union of each gene's `k` (default 10) most similar other measured genes by the cosine of their unit vectors, each pair once | `build_protein_similarity.py --out` |
| `protein_embedding` | per-gene table `pc1..pcN`: the first N principal components of the measured genes' unit vectors (centred over them); the explained variance in `source` | `build_protein_similarity.py --table-out --components N` (optional) |

`gene_split` rows (one gene annotated as two) are skipped and counted. For both UniProt files one entry stands for a
gene: the longest protein that has an embedding, the same rule as `protein_annotation`'s longest protein, and the
accession chosen for each gene is in `source.accessions`.

## 3. How to build them (Mac; the hosts are refused from the cloud sessions)

The cloud sessions cannot reach `ensembl.org`, `uniprot.org` or `ebi.ac.uk` (the proxy answers 403), so the inputs are
fetched on the Mac, into `data_downloads/` as the other sources, never into the repository. Free, no key, no lab run;
a few minutes.

1. **Paralogues.** On https://www.ensembl.org/biomart/martview choose Ensembl Genes, Human genes
   (`hsapiens_gene_ensembl`); under Filters, Gene, paste the bundle's gene symbols as the "Input external references ID
   list" with Gene Name (so a gene without paralogues still appears with empty columns); under Attributes choose
   Homologues (Max select 6 orthologues), Paralogues: Gene stable ID, Gene name, Human paralogue gene stable ID, Human
   paralogue associated gene name, Paralogue %id. target Human gene identical to query gene, Paralogue %id. query gene
   identical to target Human gene, Paralogue last common ancestor with Human, Paralogue homology type; export TSV. The
   bundle's symbols come from `public.npz` (`python -c "import numpy as np; print('\n'.join(map(str, np.load('data/adamson_cf_clean/public.npz', allow_pickle=False)['genes'])))"`).
   The header names are to be verified on the page when the export is made; the builder refuses a file lacking a
   required column and names it. Note the Ensembl release shown on the page.
2. **Embeddings.** `https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/embeddings/UP000005640_9606/per-protein.h5`
   (path and layout to be verified on https://www.uniprot.org/help/embeddings; about 80 MB), and the reviewed-human
   TSV that `tools/build_protein_annotation.py` already uses (its export has the three columns this builder needs).
   The builder reads the HDF5 file with `h5py`, which `anndata` (in `requirements.txt`) already brings to the Mac's
   environment (`python -c "import h5py"` confirms). Note the UniProt release (https://www.uniprot.org/release-notes).
3. **Build, per bundle** (the Adamson clean bundle shown; Norman the same with its directory):

```
python tools/build_paralogs.py --tsv data_downloads/similarity/paralogues_adamson_cf.tsv --release <ensembl release> \
    --genes-from data/adamson_cf_clean --out data_downloads/similarity/adamson_cf/paralogs.json \
    --table-out data_downloads/similarity/adamson_cf/paralog_annotation.json
python tools/build_protein_similarity.py --h5 data_downloads/similarity/per-protein.h5 \
    --tsv data_downloads/clean_knowledge/uniprot_human_reviewed.tsv --release <uniprot release> \
    --genes-from data/adamson_cf_clean --k 10 --out data_downloads/similarity/adamson_cf/protein_similarity.json
```

4. **A bundle with them**, named apart from block G's two bundles because the results table groups runs by the
   bundle's name (`genemila/benchmark/table.py`): the clean sources and the three block G tables as in
   `docs/mac/block_g`, plus the new files and `--name`:

```
python tools/build_clean_bundle.py --bundle data/adamson_cf --sources data_downloads/clean_knowledge \
    --out data/adamson_cf_clean_similarity --name adamson_cf_clean_similarity \
    --table gene_annotation=... --table gene_constraint=... --table protein_annotation=... \
    --table paralogs=data_downloads/similarity/adamson_cf/paralogs.json \
    --table paralog_annotation=data_downloads/similarity/adamson_cf/paralog_annotation.json \
    --table protein_similarity=data_downloads/similarity/adamson_cf/protein_similarity.json
```

The builder prints each file's entries and genes covered, the planner's knowledge-summary lines and their total
against `research_state.KNOWLEDGE_SECTION_CHARS` (8,000): block G's three tables take about 2,400 characters, the
two edge files and the paralog table about 2,100 more (measured on the toy files of the tests: 692, 705 and 682), so
the summary stays near 4,800 and fits. The bundle verifies (`verify_bundle`, `added_knowledge == []`) and
the input bundle is asserted unchanged.

## 4. What a run with them is, and is not

- A run on such a bundle is its own arm (a different bundle name, so never pooled with G0 or G1), on the lead's
  dated plan, with Andres's cap line, one paid run at a time (`AGENTS.md`). In discovery mode (`docs/DISCOVERY_MODE.md`,
  PR #71) the two edge files and the table columns appear in the planner's INPUTS UNEXPLORED list by name, so a feature
  that reads them can be judged new by the lab's rule rather than by the planner's wording.
- Nothing here reads `private/`, `splits.json`, a held-out label or a sealed score; the builders read `public.npz`'s
  gene names and the source files only (`tests/test_similarity_builders.py` and the guard apply to features as before).
- The honest odds are those of `docs/DISCOVERY_MODE.md` section 5: the ceiling analysis says a similarity source is
  where the room is, and the learned similarity from the bundle's existing knowledge gained +0.010, inside noise. A
  paralog or sequence relative helps only where a new target's closest training relative is found by sequence and not
  by the sets, partners or co-expression the model already has; the first run says how often that happens, and the
  fair test says whether it counts.
- The in-vitro reading, if a sequence-based feature passes: the feature names which training knockdown a new target
  should copy; a CRISPRi of the new target in K562 with RNA-seq, compared with the copied knockdown's profile, is the
  test, through `tools/wetlab_candidates.py` as for any passing feature.
