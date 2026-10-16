# Candidate literature check (criterion A.6)

The citations behind the KNOWN and OPEN verdicts of `docs/PREREG_G_KNOWN_BIOLOGY.md`, as `docs/GOAL_CRITERIA.md` A.6
and `docs/ROADMAP.md` D3 require. Each entry is marked VERIFIED (an abstract or page was fetched in this session; the
fetch URL is given) or UNVERIFIED (a search summary only). The starting list is the fact-finder's `ground:literature`
findings; the entries below were then fetched from nature.com and arxiv.org through the proxy, from the bioRxiv details
API, from Europe PMC's REST `resultType=core` (which returns the published abstract), and from PubMed Central. Astra
re-checks each entry independently from the Mac before any A.6 verdict leaves "provisional" (`docs/ROADMAP.md`,
section 6, item 11); the VERIFIED marks here mean the abstract was read in this session, not that the independent pass
is done.

## CRISPRa and CRISPRi effector biology

- **Konermann2015.** Genome-scale transcriptional activation by an engineered CRISPR-Cas9 complex. Konermann,
  Brigham, Trevino, ... Zhang. 2015, Nature. VERIFIED, https://www.nature.com/articles/nature14136. Establishes
  structure-guided CRISPRa (SAM) and sgRNA rules for activation; the foundational CRISPRa paper. Makes family 1 KNOWN
  (the abstract states the activation technology and targeting rules; the inverse-basal-expression dependence is in
  its figures, read as UNVERIFIED at the figure level).
- **Chavez2016.** Comparison of Cas9 activators in multiple species. Chavez, Tuttle, Pruitt, ... Church. 2016, Nature
  Methods. VERIFIED, https://www.nature.com/articles/nmeth.3871. Shows VPR, SAM and SunTag activate across cell types
  with strong locus-to-locus variability in achievable fold change. Supports family 1 (activation strength is set by
  the target locus state).
- **Wu2023.** Massively parallel characterization of CRISPR activator efficacy in human induced pluripotent stem cells
  and neurons. Wu, Wu, Karim, ... Bassett. 2023, Molecular Cell (83(7), doi 10.1016/j.molcel.2023.02.011). VERIFIED,
  https://europepmc.org/abstract/MED/36917981. The Mol Cell 2023 CRISPRa-efficacy paper: its abstract states that
  "activation level is anti-correlated with basal gene expression" and that bivalent chromatin responds most. This is
  the clearest published statement of the rule that makes family 1 KNOWN.
- **Horlbeck2016.** Compact and highly active next-generation libraries for CRISPR-mediated gene repression and
  activation. Horlbeck, Gilbert, Villalta, ... Weissman. 2016, eLife (doi 10.7554/eLife.19760). VERIFIED,
  https://europepmc.org/abstract/MED/27661255. A chromatin-, position- and sequence-based model of CRISPRi and CRISPRa
  guide activity. Supports families 1 and 2 (effector outcome tracks promoter chromatin and TSS position).
- **Radzisheuskaya2016.** Optimizing sgRNA position markedly improves the efficiency of CRISPR/dCas9-mediated
  transcriptional repression. Radzisheuskaya, Shlyueva, Muller, Helin. 2016, Nucleic Acids Research (44(18):e141).
  VERIFIED, https://europepmc.org/abstract/MED/27353328. CRISPRi efficiency depends on recruitment near the TSS.
  Makes the TSS-proximity reading of family 2 KNOWN.
- **Gilbert2014.** Genome-Scale CRISPR-Mediated Control of Gene Repression and Activation. Gilbert, Horlbeck, Adamson,
  ... Weissman. 2014, Cell (doi 10.1016/j.cell.2014.09.029). VERIFIED, https://europepmc.org/abstract/MED/25307932.
  Establishes CRISPRi and CRISPRa at endogenous genes and the TSS-window targeting rule. Supports families 1 and 2.
- **Deaton2011.** CpG islands and the regulation of transcription. Deaton, Bird. 2011, Genes & Development (doi
  10.1101/gad.2037511). VERIFIED, https://europepmc.org/abstract/MED/21576262. CpG islands are the GC-rich,
  nonmethylated, broadly-active promoter class. Makes the "CpG o/e is a proxy for an active promoter" step of family 1
  KNOWN.

## Response-magnitude and responsiveness rules

- **Replogle2022.** Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Replogle,
  Saunders, Pogson, ... Weissman. 2022, Cell (185(14):2559, doi 10.1016/j.cell.2022.05.013). VERIFIED,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9380471/. Genome-scale K562 CRISPRi; co-functional genes share
  transcriptional phenotypes. The tier-3 screen the lab excludes from block G, and the source of the known rule behind
  families 5 and 6.
- **Nadig2025.** Transcriptome-wide analysis of differential expression in perturbation atlases (TRADE). Nadig,
  Replogle, Pogson, ... O'Connor. 2025, Nature Genetics (doi 10.1038/s41588-025-02169-3; bioRxiv 2024,
  10.1101/2024.07.03.601903). VERIFIED, https://www.nature.com/articles/s41588-025-02169-3. A typical gene
  perturbation affects about 45 genes, a typical essential gene over 500. Makes the "essential genes respond most"
  rule behind families 6 and 8 KNOWN, and is the confound the residualised family 8 must beat.
- **KangBrent2022.** Predicting which genes will respond to transcription factor perturbations. Kang, Jung, Brent.
  2022, G3: Genes, Genomes, Genetics (12(8):jkac144, doi 10.1093/g3journal/jkac144; bioRxiv 2020,
  10.1101/2020.12.15.422864, titled "Predicting which genes will respond to perturbations of a TF"). VERIFIED,
  https://europepmc.org/abstract/MED/35666184. In K562, ChIP-seq binding locations have very little utility for
  predicting responsiveness, while pre-perturbation expression level and variation predict it well. Makes family 3
  KNOWN and marks the TF-binding feature as already answered (negatively).

## Molecular-architecture determinants

- **Karamyshev2014.** Inefficient SRP interaction with a nascent chain triggers a mRNA quality control pathway.
  Karamyshev, Patrick, Karamysheva, ... Thomas. 2014, Cell (doi 10.1016/j.cell.2013.12.017). VERIFIED,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3931426/. When a signal sequence fails to bind SRP, the message is degraded via
  Ago2. Makes the secretory-pathway interaction of family 7 KNOWN.
- **Adamson2016.** A Multiplexed Single-Cell CRISPR Screening Platform Enables Systematic Dissection of the Unfolded
  Protein Response. Adamson, Norman, Jost, ... Weissman. 2016, Cell (doi 10.1016/j.cell.2016.11.048). VERIFIED,
  https://europepmc.org/abstract/MED/27984733. The Adamson dataset itself: CRISPRi of UPR and secretory-pathway genes
  in K562. Grounds family 7 and names the dataset's perturbation panel.
- **Norman2019.** Exploring genetic interaction manifolds constructed from rich single-cell phenotypes. Norman,
  Horlbeck, Replogle, ... Weissman. 2019, Science (doi 10.1126/science.aax4438). VERIFIED,
  https://europepmc.org/abstract/MED/31395745. The Norman dataset: CRISPRa genetic-interaction panel in K562. Names
  the modality and panel for the Norman arm.
- **Calvo2009.** Upstream open reading frames cause widespread reduction of protein expression and are polymorphic
  among humans. Calvo, Pagliarini, Mootha. 2009, PNAS (doi 10.1073/pnas.0810916106). VERIFIED,
  https://europepmc.org/abstract/MED/19372376. uORFs typically reduce protein expression by 30 to 80 percent with a
  modest effect on mRNA. Makes family 4 KNOWN at the protein level and marks its mRNA-response link as weak.
- **Agarwal2022.** The genetic and biochemical determinants of mRNA degradation rates in mammals. Agarwal, Kelley.
  2022, Genome Biology (doi 10.1186/s13059-022-02811-x). VERIFIED, https://europepmc.org/abstract/MED/36419176. Gene
  and transcript features predict mRNA half-life. Supports the stability reading of family 3.
- **Karczewski2020.** The mutational constraint spectrum quantified from variation in 141,456 humans (gnomAD v2.1.1).
  Karczewski, Francioli, Tiao, ... MacArthur. 2020, Nature (doi 10.1038/s41586-020-2308-7). VERIFIED,
  https://www.nature.com/articles/s41586-020-2308-7. Defines pLI, LOEUF and o/e LoF, the `gene_constraint` columns.
  Grounds families 6 and 8.
- **Collins2022.** A cross-disorder dosage sensitivity map of the human genome (pHaplo, pTriplo). Collins, Glessner,
  Porcu, ... Talkowski. 2022, Cell (doi 10.1016/j.cell.2022.06.036). VERIFIED,
  https://europepmc.org/abstract/MED/35917817. Triplosensitivity, which gnomAD does not measure, would be the
  CRISPRa-side dosage term; noted as not built into block G (`tools/build_gene_constraint.py` docstring).

## Comparison-paper landscape (B-path, not A.6)

- **AhlmannEltze2025.** Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear
  baselines. Ahlmann-Eltze, Huber, Anders. 2025, Nature Methods (doi 10.1038/s41592-025-02772-6). VERIFIED,
  https://www.nature.com/articles/s41592-025-02772-6. No foundation model beat simple linear baselines. The bar the
  "feature + linear model" framing must clear (B.4).
- **Roohani2024 (GEARS).** Predicting transcriptional outcomes of novel multigene perturbations with GEARS. Roohani,
  Huang, Leskovec. 2024, Nature Biotechnology (doi 10.1038/s41587-023-01905-6; first online 2023). VERIFIED,
  https://www.nature.com/articles/s41587-023-01905-6. Uses a gene-gene knowledge graph so that similar-pathway genes
  are predicted to respond similarly; a pathway-similarity feature would restate this prior (bears on family 8's
  pathway proxies).
- **Wu2024 (PerturBench).** PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis. Wu,
  Wershof, Schmon, ... Graepel. 2024, arXiv 2408.10609. VERIFIED, https://arxiv.org/abs/2408.10609. Simple
  architectures are competitive and rank metrics matter; supports the comparison's metric choices (B.1, B.2).
- **Adduri2025 (STATE).** Predicting cellular responses to perturbation across diverse contexts with STATE. Adduri,
  Gautam, Bevilacqua, ... Roohani. 2025, bioRxiv 10.1101/2025.06.26.661135 (published Cell 2026,
  10.1016/j.cell.2026.07.052). VERIFIED, https://api.biorxiv.org/details/biorxiv/10.1101/2025.06.26.661135. Trained on
  Replogle K562 among others, so it cannot be a fair row on the fresh test (`docs/ROADMAP.md` D9).
- **CellForge2025.** AI Scientists for Building Virtual-Cell Models. Tang, Chen, Shao, ... Gerstein. 2025, arXiv
  2508.02276 (v1 2025-08-04; v3 2026-10-14 retitled). VERIFIED, https://arxiv.org/abs/2508.02276. The autonomous
  multi-agent system entered as the C2 translated-ideas arm; its published table is reported not comparable
  (`docs/ROADMAP.md` D9).
- **Biomni2025.** Biomni: A General-Purpose Biomedical AI Agent. Huang, Zhang, Wang, ... Leskovec. 2025, bioRxiv
  10.1101/2025.05.30.656746. VERIFIED, https://api.biorxiv.org/details/biorxiv/10.1101/2025.05.30.656746. The
  general biomedical coding agent run as the A4 comparison arm (B.1).
- **Karpathy2026 (autoresearch).** karpathy/autoresearch, a code repository, Karpathy, March 2026. VERIFIED (README
  fetched), https://github.com/karpathy/autoresearch. The fixed-harness, one-editable-surface, never-stop loop the A3
  autoresearch-style arm imitates (`docs/FEATURE_COMPARISON_PROTOCOL.md`, section 2). Not a peer-reviewed paper.

## Open questions a tier-1 feature could still answer, and what is already known

- **Does constraint predict response magnitude beyond basal expression and essentiality?** OPEN with power (family 8).
  Known: constraint correlates with essentiality [Nadig2025] and with basal expression, and essential genes respond
  most, so the raw link is known [Karczewski2020, Replogle2022]; the residual after removing both confounds is
  untested and testable in-house.
- **Does amino-acid composition predict a gene's mRNA response to its cognate aminoacyl-tRNA synthetase knockdown?**
  OPEN but underpowered (family 5). Known: synthetase inhibition starves one amino acid and impairs translation of
  aa-rich proteins (biochemistry); the mRNA-level response link in Perturb-seq is not published, and Adamson has about
  ten synthetase targets.
- **Do uORFs modulate the transcriptional (mRNA) response beyond their protein-level effect?** OPEN but weak (family 4).
  Known: uORFs reduce protein output with a modest mRNA effect [Calvo2009].
- **Does same-chromatin-loop (not just same-TAD) membership predict cis response?** OPEN but not buildable from the
  three tables; it needs ENCODE K562 Hi-C (`docs/ROADMAP.md` D10). Known: loop beats TAD co-membership in enhancer
  work, cis effects touch few genes, so the gain on a gene-wide metric is expected to be small (`docs/ROADMAP.md`,
  section 9).
- **Does TF ChIP-seq binding predict the sign and size of response?** Already answered, negatively, for K562
  [KangBrent2022]; a plain "TF binds promoter" feature would restate the known negative result. Not an open question.
