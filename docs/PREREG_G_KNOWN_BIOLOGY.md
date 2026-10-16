# Pre-registration: the known biology, before any block G score is read

Fixed 2026-10-17 (UTC), before any block G feature-level score is read. The run checkout is pinned at `baa7dfd`
(`docs/PLAN_G_CLEAN_ARM.md`, note of 2026-10-16 23:40 UTC; `docs/ROADMAP.md` D1), which predates this file, so no
agent in block G ever sees it. This file is the lead's pre-registration of what is already known for each feature
family the agents can build from the clean bundle's three per-gene tables, so the KNOWN or OPEN call is made by a
written record fixed in advance, not after the numbers (`docs/GOAL_CRITERIA.md` A.2 and A.6; `docs/ROADMAP.md` D3).
A change is a dated note at the end, never an edit above it.

The three tables and their columns are `tools/build_gene_annotation.py` (`gene_annotation`: `gene_span_kb`,
`n_transcripts`, `n_exons`, `transcript_length`, `cds_length`, `utr5_length`, `utr3_length`, `intron_length_kb`,
`gc_cds`, `gc_utr3`, `gc_promoter`, `cpg_oe_promoter`, `n_upstream_atg`, `nearest_tss_kb`, `n_tss_within_100kb`,
`aa_<X>`; plus `loci`, `bidirectional`, `neighbours`), `tools/build_gene_constraint.py` (`gene_constraint`: `oe_lof`,
`oe_lof_lower`, `oe_lof_upper` = LOEUF, `pLI`, `pNull`, `pRec`, `oe_mis`, `oe_mis_upper`, `mis_z`, `syn_z`, `lof_z`,
`obs_lof`, `exp_lof`, `oe_lof_upper_bin`), and `tools/build_protein_annotation.py` (`protein_annotation`:
`protein_length`, `has_signal_peptide`, `signal_peptide_length`, `n_transmembrane`, and the location flags `secreted`,
`membrane`, `endoplasmic_reticulum`, `golgi`, `mitochondrion`, `nucleus`, `cytoplasm`, `lysosome`, `peroxisome`).

Citation keys are defined in `docs/CANDIDATE_LITERATURE_CHECK.md`, each marked VERIFIED or UNVERIFIED there.

## The rules that read these families

- **Minimum effect of practical interest.** A family counts only if its mean out-of-fold M1 gain over the parent is
  above `max(2 * SE_adj, 0.002)`, where `SE_adj` is the overlap-robust paired standard error
  (`tools/feature_compare.py`; the 0.002 floor is the task package's noise rule, `genemila/research_state.py:18`).
  A gain below this bar is not read as a pass whatever its p-value.
- **The null (`docs/ROADMAP.md` D2).** Two matched nulls. The **gene null** permutes the candidate column across genes
  within deciles of control expression. The **perturbation-level null** permutes a candidate's per-perturbation factor
  across perturbations within deciles of the targets' mean control expression, with the parent columns left in place.
  A candidate that is, within each perturbation row, proportional to a parent column (for example `additive_response`
  times a per-perturbation scalar) must pass **both**. Family-wise correction is the max-gain step-down permutation
  over the whole family at 999 or more replicates (floor 0.001), rows deduplicated by prediction hash first.
- **The A.2 sign rule.** The pre-registered sign below must hold for the standardised add-one coefficient in **every**
  fold seed and on **both** datasets where the modality applies. A sign that flips in any fold seed or dataset drops
  the mechanism claim; the feature is then reported as predictive but unexplained (`docs/ROADMAP.md`, section 5, A.2).
- **Modality.** Norman is CRISPRa (102 targets, transcription-factor and genetic-interaction panel). Adamson is
  CRISPRi (90 targets, the unfolded-protein-response and secretory-pathway panel, `docs/mac/adamson_cf_ncells.json`).
  "Not predicted" means the direction is OPEN for that modality; "N/A" means that modality has no matching
  perturbations.

## The families

### 1. Promoter CpG o/e and promoter GC class
- **Formula shape.** `additive_response` times the targets' mean `cpg_oe_promoter` (or `gc_promoter`, or a GC-class
  indicator). This is exactly the block F candidate (`docs/results/norman_f_stage2`).
- **Inputs.** `gene_annotation.cpg_oe_promoter`, `gene_annotation.gc_promoter`.
- **Sign.** Norman CRISPRa: **negative** (higher CpG o/e scales the response down). Adamson CRISPRi: **not predicted**.
- **Null.** Both (parent-proportional per-perturbation factor).
- **Verdict.** KNOWN [Konermann2015, Chavez2016, Wu2023, Deaton2011; Horlbeck2016, Radzisheuskaya2016, Gilbert2014].
- **Why.** CRISPRa raises already-active, high-basal-expression genes least, and a CpG-island promoter (high CpG o/e)
  is the broadly-active class, so the feature restates the published inverse dependence of CRISPRa on basal activity.

### 2. TSS distance, nearest TSS and bidirectional promoters
- **Formula shape.** A cis term: a target affects a response gene that shares or sits near its promoter; or
  `additive_response` times the targets' mean `nearest_tss_kb`.
- **Inputs.** `gene_annotation.nearest_tss_kb`, `n_tss_within_100kb`, `bidirectional`, `loci` (chromosome, TSS, strand).
- **Sign.** Not predicted for either modality (the block F TSS-distance plugin ignored chromosome and strand and never
  read the bidirectional table, so its name was not its mechanism; `docs/results/norman_f_readings.md`).
- **Null.** Gene null for the gene-side cis term; both for the per-perturbation scaler form.
- **Verdict.** KNOWN [Radzisheuskaya2016, Horlbeck2016, Gilbert2014].
- **Why.** dCas9 efficacy tracks proximity to the TSS, and a dCas9 effector at a shared or bidirectional promoter acts
  in cis on the neighbour; both are published, and cis effects touch few genes so the gain on a gene-wide metric is
  expected to be small.

### 3. Gene length, exon count, transcript count, UTR lengths
- **Formula shape.** The response gene's own size as a gene-side term, or `additive_response` times the targets' mean
  of these columns.
- **Inputs.** `gene_annotation.gene_span_kb`, `transcript_length`, `cds_length`, `n_exons`, `n_transcripts`,
  `utr5_length`, `utr3_length`, `intron_length_kb`.
- **Sign.** Not predicted (these columns are confounded proxies for basal expression and mRNA stability).
- **Null.** Gene null for the gene-side term; both for the per-perturbation scaler form.
- **Verdict.** KNOWN [KangBrent2022, Agarwal2022].
- **Why.** Basal expression level and variability, which gene length and UTR length track, already predict
  responsiveness and mRNA stability, so a length feature restates a known determinant rather than a new one.

### 4. Upstream ATGs
- **Formula shape.** `additive_response` times the targets' mean `n_upstream_atg`, or the response gene's own count.
- **Inputs.** `gene_annotation.n_upstream_atg`.
- **Sign.** Not predicted on the measured mRNA delta.
- **Null.** Gene null for the gene-side term; both for the scaler form.
- **Verdict.** KNOWN [Calvo2009].
- **Why.** Upstream open reading frames are a published determinant of reduced expression, though their effect is on
  protein output with only a modest effect on mRNA, which is what the lab measures, so the mRNA-response link is weak.

### 5. Amino-acid composition
- **Formula shape.** An interaction: an aminoacyl-tRNA synthetase knockdown (Adamson has `AARS`, `CARS`, `DARS`,
  `FARSB`, `HARS`, `IARS2`, `MARS`, `QARS`, `SARS`, `TARS`) times the response gene's content of the cognate amino
  acid.
- **Inputs.** `gene_annotation.aa_<X>`, crossed with the perturbed gene's identity.
- **Sign.** Pre-registered hypothesis for Adamson CRISPRi: **positive** (an aa-rich message responds more to its
  cognate synthetase knockdown). Norman CRISPRa: N/A (no synthetase targets).
- **Null.** Both.
- **Verdict.** OPEN (underpowered) [Replogle2022].
- **Why.** The biochemistry of synthetase inhibition starving one amino acid is textbook, but the specific link from a
  gene's aa-composition to its mRNA response in Perturb-seq is not published; with about ten synthetase perturbations
  on Adamson it is unlikely to clear the effect bar, so a positive result would be mechanistically unsurprising.

### 6. gnomAD constraint (pLI, LOEUF, o/e LoF), raw
- **Formula shape.** `additive_response` times the targets' mean `pLI` (or `1 - oe_lof_upper`), or the response gene's
  own constraint as a gene-side term.
- **Inputs.** `gene_constraint.pLI`, `oe_lof_upper` (LOEUF), `oe_lof`.
- **Sign.** Adamson CRISPRi: **positive** (constrained, LoF-intolerant genes scale the response up). Norman CRISPRa:
  not predicted.
- **Null.** Both for the scaler form; gene null for the gene-side term.
- **Verdict.** KNOWN [Karczewski2020, Nadig2025, Replogle2022].
- **Why.** Constraint is a proxy for essentiality and basal expression, and essential genes already produce the
  largest transcriptional responses, so a raw constraint feature restates that known dependence through its confounds.

### 7. UniProt signal peptide, transmembrane, subcellular location, keywords
- **Formula shape.** An interaction: a secretory-pathway or UPR knockdown (Adamson's SRP `SRP68`, `SRP72`, `SRPR`,
  `SRPRB`; translocon `SEC61A1`, `SEC61B`, `SEC61G`, `SEC63`; OST `DDOST`, `OST4`, `STT3A`; signal peptidase `SPCS2`,
  `SPCS3`; `SEL1L`, `SYVN1`, `HSPA5`, `XBP1`) times an ER-targeted indicator of the response gene
  (`has_signal_peptide`, `n_transmembrane > 0`, or `endoplasmic_reticulum`).
- **Inputs.** `protein_annotation.has_signal_peptide`, `signal_peptide_length`, `n_transmembrane`, location flags.
- **Sign.** Adamson CRISPRi: **positive** (ER-targeted messages respond more to secretory-pathway knockdowns). Norman
  CRISPRa: N/A (no secretory-pathway targets).
- **Null.** Both.
- **Verdict.** KNOWN [Karamyshev2014, Adamson2016].
- **Why.** Loss of SRP, translocon or OST function triggers regulated decay of ER-targeted messages, and the Adamson
  dataset was built to dissect exactly this response, so an ER-targeting feature recovers a published interaction.

### 8. Constraint residualised on control expression and tier-1 essentiality proxies
- **Formula shape.** The residual of the targets' mean constraint after regressing out their mean control expression
  (`ctx.control_mean`) and membership indicators for tier-1 essentiality proxies, then times `additive_response`.
- **Inputs.** `gene_constraint` columns; `ctx.control_mean`; `gene_sets` for CORUM core complexes and the Reactome
  ribosome, proteasome and spliceosome sets. DepMap is tier 3 and is excluded (`docs/NOVEL_FEATURE_NEEDS.md` section 7).
- **Sign.** Pre-registered hypothesis: Adamson CRISPRi **positive** (residual constraint scales the response up beyond
  basal expression and essentiality). Norman CRISPRa: not predicted.
- **Null.** Both.
- **Verdict.** OPEN (the one open family with power, `docs/ROADMAP.md` D3) [Nadig2025, Karczewski2020].
- **Why.** No published result tests whether population constraint predicts response magnitude after removing the two
  known confounds, basal expression and essentiality, so a residual effect here would be a genuinely new rule.

## Reading this file against the goal criteria

A KNOWN family that passes A.1 is recorded as methods-level: it gets no replication, no wet-lab list and no novelty
sentence (`docs/GOAL_CRITERIA.md` A.6; `docs/ROADMAP.md`, section 5). An OPEN family that passes A.1 and A.2 stays
provisional until the citation pass of `docs/CANDIDATE_LITERATURE_CHECK.md` confirms its keys. The lead also scores the
residualised constraint hypothesis (family 8) as a hand-written plugin, reported as a human hypothesis and never as
A.1 (`docs/ROADMAP.md` D4).
