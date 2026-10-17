# Pre-registration: the known biology, before any block G score is read

Fixed 2026-10-17 (UTC) by the commit that carries this file, before any block G feature-level score is read; its
first version was committed at `4118f0d`, 2026-10-16 23:14 UTC, and the corrections since are listed in the note at
the end. Nothing in block G has run: the plan's cap still awaits Andres's line (`docs/PLAN_G_CLEAN_ARM.md`, closing
note in commit `fee6e79`). The run checkout is pinned at `baa7dfd` (same note; `docs/ROADMAP.md` D1), which predates
this file, so no agent in block G ever sees it. This file is the lead's pre-registration of what is already known
for each feature family the agents can build from the clean bundle's three per-gene tables, so the verdict is made
by a written record fixed in advance, not after the numbers (`docs/GOAL_CRITERIA.md` A.2 and A.6; `docs/ROADMAP.md` D3).
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
- **What the verdicts mean.** **KNOWN**: a published result already predicts this feature's sign for this modality
  (`docs/GOAL_CRITERIA.md` A.6). **KNOWN by confound**: the published result is about a determinant the column proxies
  (basal expression, mRNA stability, essentiality), not about the column itself, so no published result predicts the
  feature's sign. Such a family that passes A.1 is reported as predictive but explained by the confound, unless the
  same column residualised on `ctx.control_mean` also passes both nulls, in which case it is read as OPEN, like
  family 8. **OPEN**: no published result either way.
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
- **Already seen.** Block F's in-run fits of this same CpG term were read before this file and were mixed: +0.0147
  (r0 e428), +0.0143 (r0 e666), -0.0100 (r3 e412) (`docs/GOAL_CRITERIA.md`, note of 2026-10-16 22:55 UTC). Those are
  in-run coefficients, not the standardised add-one coefficient the D2 tool saves. The negative sign above is the
  literature's prediction, and it is read on block G only.

### 2. TSS distance, nearest TSS and bidirectional promoters
- **Formula shape.** A cis term: a target affects a response gene that shares or sits near its promoter; or
  `additive_response` times the targets' mean `nearest_tss_kb`.
- **Inputs.** `gene_annotation.nearest_tss_kb`, `n_tss_within_100kb`, `bidirectional`, `loci` (chromosome, TSS, strand).
- **Sign.** The cis term: the affected neighbour moves in the modality's direction (Adamson CRISPRi negative, Norman
  CRISPRa positive). The `nearest_tss_kb` or `n_tss_within_100kb` scaler form: not predicted (the block F
  TSS-distance plugin ignored chromosome and strand and never read the bidirectional table, so its name was not its
  mechanism; `docs/results/norman_f_readings.md`).
- **Null.** Gene null for the gene-side cis term; both for the per-perturbation scaler form.
- **Verdict.** Cis term: KNOWN [Radzisheuskaya2016, Horlbeck2016, Gilbert2014]. Scaler form: KNOWN by confound (TSS
  density tracks promoter class and basal expression), sign not published.
- **Why.** dCas9 efficacy tracks proximity to the target's own TSS, and a dCas9 effector at a shared or bidirectional
  promoter acts in cis on the neighbour; both are published, and cis effects touch few genes so the gain on a
  gene-wide metric is expected to be small. The cited papers model the guide's position relative to the target's own
  TSS, while `nearest_tss_kb` is the distance to another gene's TSS, which is why the scaler form is only a confound
  reading.

### 3. Gene length, exon count, transcript count, UTR lengths
- **Formula shape.** The response gene's own size as a gene-side term, or `additive_response` times the targets' mean
  of these columns.
- **Inputs.** `gene_annotation.gene_span_kb`, `transcript_length`, `cds_length`, `n_exons`, `n_transcripts`,
  `utr5_length`, `utr3_length`, `intron_length_kb`.
- **Sign.** Not predicted (these columns are confounded proxies for basal expression and mRNA stability).
- **Null.** Gene null for the gene-side term; both for the per-perturbation scaler form.
- **Verdict.** KNOWN by confound (basal expression level and variation, and mRNA half-life), sign not published
  [KangBrent2022, Agarwal2022].
- **Why.** Basal expression level and variability, which gene length and UTR length track, already predict
  responsiveness and mRNA stability, so a length feature restates a known determinant rather than a new one.

### 4. Upstream ATGs
- **Formula shape.** `additive_response` times the targets' mean `n_upstream_atg`, or the response gene's own count.
- **Inputs.** `gene_annotation.n_upstream_atg`.
- **Sign.** Not predicted on the measured mRNA delta.
- **Null.** Gene null for the gene-side term; both for the scaler form.
- **Verdict.** OPEN (weak: the published effect is on protein output, not on the measured mRNA delta) [Calvo2009].
- **Why.** Upstream open reading frames are a published determinant of reduced expression, though their effect is on
  protein output with only a modest effect on mRNA, which is what the lab measures, so the mRNA-response link is weak.

### 5. Amino-acid composition
- **Formula shape.** An interaction: an aminoacyl-tRNA synthetase knockdown (Adamson has `AARS`, `CARS`, `DARS`,
  `FARSB`, `HARS`, `MARS`, `QARS`, `SARS`, `TARS`) times the response gene's content of the cognate amino acid. The
  panel's tenth synthetase, `IARS2`, is the mitochondrial isoleucyl-tRNA synthetase, so its knockdown does not starve
  cytosolic isoleucine charging; it is excluded from this family.
- **Inputs.** `gene_annotation.aa_<X>`, crossed with the perturbed gene's identity.
- **Sign.** Pre-registered hypothesis for Adamson CRISPRi: **positive** (an aa-rich message responds more to its
  cognate synthetase knockdown). Norman CRISPRa: N/A (no synthetase targets).
- **Null.** Both.
- **Verdict.** OPEN (underpowered) [Replogle2022].
- **Why.** The biochemistry of synthetase inhibition starving one amino acid is textbook, but the specific link from a
  gene's aa-composition to its mRNA response in Perturb-seq is not published; with nine cytosolic synthetase
  perturbations on Adamson it is unlikely to clear the effect bar, so a positive result would be mechanistically
  unsurprising.

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
- **Verdict.** KNOWN [Karamyshev2014, Hollien2006, Adamson2016].
- **Why.** Loss of SRP function triggers decay of the secretory-protein messages whose nascent chains fail to bind it
  [Karamyshev2014], and ER stress, which the UPR and ERAD knockdowns (`HSPA5`, `XBP1`, `SEL1L`, `SYVN1`) induce,
  drives IRE1-dependent decay of messages selected by their localisation to the ER membrane [Hollien2006]. The
  Adamson dataset was built to dissect exactly this response, so an ER-targeting feature recovers a published
  interaction.

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
provisional until the citation pass of `docs/CANDIDATE_LITERATURE_CHECK.md` confirms its keys. A KNOWN-by-confound
family that passes A.1 is reported as predictive but explained by its confound, and is read as OPEN only if the same
column residualised on `ctx.control_mean` passes both nulls too. The lead also scores the
residualised constraint hypothesis (family 8) as a hand-written plugin, reported as a human hypothesis and never as
A.1 (`docs/ROADMAP.md` D4).

## Note, 2026-10-17 (UTC): corrections made before this file was merged

Made after the lead's review of the first version (`4118f0d`) and before any block G run started, so no score was read
in between. Six corrections. (1) The dateline now names the commit that fixes the file and its first version, and
cites the PLAN_G note by commit rather than by a wall-clock that postdates it. (2) The verdict vocabulary gained
"KNOWN by confound", because A.6 defines KNOWN as a published result that predicts the feature's sign, which the gene
length and TSS-density citations do not; such a family now carries a reading rule (residualise on `ctx.control_mean`).
(3) Family 2's cis term keeps KNOWN with a sign; its `nearest_tss_kb` scaler form is KNOWN by confound. (4) Family 4
is OPEN (weak), matching `docs/CANDIDATE_LITERATURE_CHECK.md`; the first version said KNOWN in one file and OPEN in
the other. (5) `IARS2` is dropped from family 5 as mitochondrial, leaving nine cytosolic synthetases. (6) Family 7
cites [Hollien2006] for the UPR and ERAD targets, which [Karamyshev2014] does not cover, and family 1 now discloses
that block F's mixed in-run CpG coefficients were seen before the sign was fixed.
