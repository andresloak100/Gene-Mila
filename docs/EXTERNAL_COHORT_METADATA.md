# External evaluation cohorts: metadata audit, 13 October 2026

Neither candidate is yet approved as an untouched Norman test. This audit identifies source files and
intervention mismatches before response data is opened. Replogle experiment 8 primarily varies guide
combinations for the same gene. Pacalin's guide dictionary contains both promoter-like and enhancer
identifiers; only four of its putative promoter targets are outside the entire Norman target context
and inside the frozen model's gene universe. Those four are candidates for further checks, not four
eligible test conditions.

Claim [#18](https://github.com/andresloak100/Gene-Mila/issues/18), branch `astra/external-cohort-metadata`,
Astra/Codex chat 2. Chat 1 owns the export, README and shared HANDOFF/Mac STATE updates. This report
extends the prospective [test protocol in PR #13](https://github.com/andresloak100/Gene-Mila/pull/13).
The verified frozen adapter is in [PR #19](https://github.com/andresloak100/Gene-Mila/pull/19).
The [machine-readable audit](results/external_cohort_metadata_20261013.json) retains source hashes,
metadata extraction rules, target/guide mappings, overlap flags and unresolved decisions.

## Access and evidence

The only candidate data file read was Pacalin's guide-design dictionary, whose verified columns are
identifiers, sequences, capture configuration and target annotations. Candidate expression matrices,
perturbation-efficacy tables, per-cell annotations and mixed supplementary workbooks were not downloaded
or inspected. Public paper methods and GEO descriptions were consulted. Aggregate published results
can appear in search snippets; none informed inclusion. This limited audit does not certify zero prior
exposure across all agents or establish an isolated evaluator.

For the existing frozen B1 context, only `knowledge/targets.json` and the `genes`, `perts`, `train_perts`
arrays in `public.npz` were inspected. No expression array or private/split file was opened. The source
is `runs/norman_ds_from_n2_w4_r1/public_data` under the unchanged Mac checkout. It defines 112 training
conditions with 71 distinct target genes, 231 full-context conditions with 102 distinct targets, and
2,083 predictor genes. Full-context identity coverage is not a claim about which genes were in a sealed
split. The manifest records those sets and their fingerprints without reading split assignments.

## Replogle 2020: same-gene activation and guide dosage

[Experiment 8, GSM4367986](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4367986&targ=self&form=text&view=full)
is K562 CRISPRa using dCas9-SunTag/scFV-VP64. Its 49 designed targets compare single targeting guide plus
non-targeting guide with two targeting guides, generally for the same gene; alternative transcription
start sites and guide spacing add configurations. Cells were captured eight days after infection.
Dual-guide constructs therefore do not establish distinct-gene activation pairs.
[Primary methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7416462/).

GEO identifies BioSample SAMN14258018, SRA SRX7826831, 10x 3′ v3, eight gemgroups, no L1000 enrichment,
Cell Ranger 3.0.0 and GRCh38-1.2.0. The exact listed metadata candidate is
[GSM4367986_exp8.cell_identities.csv.gz](https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4367nnn/GSM4367986/suppl/GSM4367986_exp8.cell_identities.csv.gz).
A HEAD request returned HTTP 200 and 2,556,477 bytes at 19:47:28 UTC. Its body was not downloaded;
its columns and absence of response-derived fields remain unverified. The paper references guide
information in Supplementary Table 6, but the publisher packages Tables 1–8 in one workbook with a
generic caption. It was not opened. Table 6 must not be confused with Supplementary Figure 6.
[Supplementary source listing](https://www.nature.com/articles/s41587-020-0470-y#Sec24).

Exact target/guide identities, control configurations, overlap and observed condition availability are
still unknown. The 49 designed genes are not an eligible unseen-target count. No explicit statement
that the panel was selected from Norman 2019 was established by this audit.

## Pacalin/Steinhart: guide dictionary and intervention identity

The [GEO guide dictionary](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE220nnn/GSE220974/suppl/GSE220974_features.csv.gz)
is described as the Cell Ranger input for guide calling. Two independent reads matched its compressed
SHA256 `6c7c33e931ffb17bd40eb93de0116f68bd4f5596420a9530d269e44291bed40e` and all 94 records.
Its eight columns are `id`, `name`, `read`, `pattern`, `sequence`, `feature_type`, `target_gene_id`,
`target_gene_name`. There are 42 activation, 40 inhibition and 12 non-targeting guide identifiers.
Four activation identifiers are enhancer-labelled: `GATA1-e1-a1/a2` and `MYC-e1-a1/a2`. The other 38
map to 19 genes, two guides each. Calling those guides promoter-targeting is provisional until genomic
locus annotation is independently checked. The manifest publishes the relevant identifier/target
projection, without guide sequences. Dictionary entries do not prove observed cell or condition counts.

| Existing-context comparison of the 19 putative promoter targets | Genes |
|---|---|
| Training targets (8) | ARID1A, CEBPA, IRF1, JUN, KLF1, LYL1, MAP2K3, SPI1 |
| Other full-context targets (2) | CEBPB, ETS2 |
| Outside full context, inside frozen gene universe (4) | FAM83A, GATA1, MYC, YY1 |
| Outside full context and frozen gene universe (5) | ATF5, BTF3, FOSL1, HBE1, RIPK2 |

The last five fail the current adapter's target-universe requirement. The four above them merely pass
these two metadata checks; prior exposure, guide locus, samples, controls, feature coverage and all
other eligibility checks remain open. A new guide for an already studied gene is not an unseen-gene
intervention. None of these counts is a measure of model performance.

GEO's sample mapping distinguishes RNA capture from activation/inhibition guide capture:

| Study portion | scRNA sample(s) | Guide capture sample(s) |
|---|---|---|
| Activation singles S1 | GSM6833424 | GSM6833430 |
| Inhibition singles S2 | GSM6833425 | GSM6833431 |
| Activation or inhibition singles S3 | GSM6833426 | GSM6833432, GSM6833433 |
| Double perturbations, replicate 1 | GSM6833427 | GSM6833434, GSM6833435 |
| Double perturbations, replicate 2 | GSM6833428 | GSM6833436, GSM6833437 |
| Double perturbations, replicate 3 | GSM6833429 | GSM6833438, GSM6833439 |

These are K562 captures with lentiviral guides, non-targeting controls and doxycycline. A sample title
such as “gRNA CRISPRa double perturbations” names the activation-guide capture library; it does not
prove that a cell received two activation perturbations.
[GEO series metadata](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE220974&targ=self&form=text&view=brief).
The paper describes 22 designed double configurations, 18 bidirectional and four unidirectional
controls. The exact activation/activation versus inhibition/inhibition split is unverified here.
The guide dictionary contains no pair membership, and the combined supplementary workbook also has
outcomes, so it was not downloaded. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/mid/NIHMS2012655/).

## Frozen-model compatibility and next steps

The current query schema contains condition identity and distinct target genes. It has no explicit
encoding for guide dosage, enhancer locus or mixed activation/repression. Do not silently map those
interventions to a standard Norman pair. The ensemble, alphas, original context and per-query anchor
recipe remain fixed; this audit does not authorize adapting them to a candidate cohort.

There is also a feature-availability question. The existing external-screen builder obtains target
profiles from the original bundle's target set (`bundle_targets` → `inspect` → `build` in
[`external_screen.py`](../genemila/data/external_screen.py)). Newly represented genes outside that set
need a review of each selected plugin's missing-input behavior. This is a code-based compatibility
warning, not verification of every frozen knowledge row. This audit did not inspect numeric external
profiles. Adding new profiles would change the frozen predictor and require a new prospective plan.

The exact next bounded task is a metadata-only projection by the separate evaluator, followed by review:

1. Export source/sample, condition and guide identifiers, target gene IDs, activation direction, locus
   class, same-gene dosage versus distinct-gene configuration, replicate and matched control mapping.
   Exclude expression, efficacy, DE labels, embedding, cell-state and response-derived QC fields.
   Treat unknown fields or unknown file purity as unresolved, not as permission to open the full file.
2. Verify those identities against the manifest's training/full-context sets and frozen gene order.
   Audit all feature-source provenance and earlier agent exposure. Distinguish unseen genes, unseen
   combinations of known genes, and replication in independent cells. Fix the question before choosing
   eligible conditions. Do not select guides by measured efficacy.
3. Review frozen feature coverage, symbol/Ensembl mapping, intervention timing, control treatment,
   common measured gene panel and preprocessing. Define any sample-size/QC rule before inspecting
   candidate responses, with its response-bearing computation confined to the evaluator.
4. Fix the complete prediction/baseline batch, metrics, shared-gene uncertainty and the evaluator's
   access boundary. Prove the orchestration identity cannot read labels or reports. Only then obtain
   approval for the concrete cohort/evaluation and acquire responses on the evaluator side.

No expression download, isolated account setup, paid run, model query or new evaluation follows from
this report. The complete condition-level eligibility manifest is deliberately still pending; a
metadata-only rejection or unresolved audit must not be described as a scored model failure. Chat 1
will link this draft PR from the shared handoff so the next agent can continue without repeating it.
