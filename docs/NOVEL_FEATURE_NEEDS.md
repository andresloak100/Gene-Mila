# What it takes to find a new biological feature

Written 2026-10-15/16 for Andres's question "what do you need to be able to find a new critical feature" (claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)). A read-only review by one Claude cloud session and its reviewers; nothing here was run on real data (this container has none). It is a plan, not a result.

*Read-only review on 2026-10-15. The repository was checked at `/home/user/Gene-Mila`, and GitHub through `gh api` and `git ls-remote`. **UNVERIFIED** marks anything that could not be checked from this cloud session. This container has no `data/` and no `runs/`, and it cannot reach api.deepseek.com, UniProt, NCBI/GEO, ENCODE's portal, Zenodo or DepMap.*

## 0. Summary

1. **The limit is information, not search.** On Adamson, every winning model carries the same feature family: copying the response of training knockdowns whose targets resemble the new target, by co-expression, gene sets, PPI or symbol family (`docs/NEXT_LEVER.md:12-15`). The lab's own conclusion: "the limit is information about the targets, not search" (`docs/LAB_STATE.md:163`). The metric, pearson_delta, is a per-perturbation correlation across genes and does not depend on scale. So a per-perturbation magnitude cannot raise it. A new feature must change the *pattern across genes* (`docs/NEXT_LEVER.md:15-18`). `docs/NEXT_LEVER.md` covers Adamson only; on Norman the starting model is the additive pair rule (B2 starts from `baseline_ridge_additive`), and no Norman audit of what the gains are made of exists yet.
2. **How much room is left, stated precisely.** On the 50 training perturbations:
   - A pure mix of the *other* perturbations' responses, fitted on the truth with hindsight, reaches 0.734 (non-negative weights) to 0.780 (any sign).
   - The lab's models score about 0.60 out of fold.
   - Cell-sampling noise caps the score at 0.889 (`docs/results/ceiling_analysis.md:10,13-15,19`).
   - The visible-validation noise ceiling is 0.944 (`docs/results/noise_ceiling.md:29`).
   
   This bounds a pure response mix. It does not bound every linear model.
3. **The only measured lever so far was a perturbation screen.** Replogle 2022 K562 added +0.072 ± 0.020 over gene-set kNN in free leave-one-out (`docs/results/external_loo_replogle2022_k562.md:23`). Recombining the bundle's own prior knowledge with a learned similarity added +0.010, "inside the noise" (`docs/results/ceiling_analysis.md:32`). The agents' features named after a mechanism added little: `half_life_modulated_pathway_response_e926` +0.0043 (SE 0.0028); the half-life × PPI and splicing × intron features ≤ 0 (`docs/results/feature_audit_v3.md:104-110`). **Prior expectation: new annotation-type tables will usually add ≤ 0.01.**
4. **Nothing today separates a real gain from noise or from proxies.** The planner is told a feature "helps" if any experiment that added it raised the visible score by more than 0.002 over its parent (`genemila/research_state.py:18`; `genemila/exploit.py:25-37`; `genemila/worker.py:113-116`). That 0.002 is compared with one parent-to-child difference on the visible validation perturbations (the largest, if the feature was added more than once), which carries no standard error. For scale, the leave-one-out paired SE on Adamson is about 0.017–0.035 (`docs/results/external_loo_replogle2022_k562.md:19-23`). No matched-null test of a feature exists (Part 3).

## 1. Prerequisites

| # | Need | Evidence | Who / cost |
|---|---|---|---|
| **R0** | **Gene-symbol check (hygiene, done first).** The knowledge loader keeps a gene only on an exact string match and has no alias handling (`genemila/data/knowledge.py:95,116,141`; `grep -i alias` finds nothing). The Adamson bundle uses outdated symbols: SRPR, ATP5B, SLMO2, MARS, AARS, DARS and others (`docs/mac/adamson_cf_ncells.json`). The Replogle build needed `--alias SLMO2=PRELID3B, SRPR=SRPRA, ATP5B=ATP5F1B`, and its first build missed SLMO2 and SRPR (`docs/LAB_STATE.md:199-200`). If the current Reactome, GO 2023, CollecTRI and STRING v12 sources use HGNC symbols (SRPRA, MARS1, AARS1, ...), those targets would have no gene sets and no edges. That would fit SRPR scoring about 0.02 under every similarity predictor although SRPRB is its hindsight best relative at 0.79 (`docs/results/ceiling_analysis.md:39,89`). **UNVERIFIED** until counted on the Mac. An alias-fixed bundle copy would be its own arm and a data-hygiene fix, not a discovery | Mac, free, read-only |
| R1 | **The Mac.** No `data/` or `runs/` exists here (checked with `ls`). Plugin sources and `cv.npz` files are only in the Mac's runs. Only one example plugin is committed (`docs/example_run/tf_gated_coexpression_e26.py`) | Mac owner, free |
| R2 | **DeepSeek is reachable only from the Mac.** Free runs (`--planner-provider scripted --worker-provider mock`) need no approval (`AGENTS.md`, "Money and usage") | Mac |
| R3 | **A current ledger reading and a cap decision.** The ledger is the shared record of DeepSeek spend. The last committed figure is $43.599822392 against the $48 block (`HANDOFF.md` section 1, the 14 October model-quality entry). The B4 one-worker runs of 15 Oct ran "under PR39" (`HANDOFF.md` section 1, Astra's #40 entry of 15 October 22:04 UTC). PR #39 (open draft) uses `budget.cumulative_usd.deepseek=52` and starts a run only at a ledger of $49.50 or less (PR #39 diff: `docs/PLAN_B4_SINGLE_WORKER.md`, `docs/mac/block_b4/norman_b4_run.sh`). The B4 costs are not in the repo. Block F (`docs/PLAN_F_GENOME_ANNOTATION.md`) proposes an $8 ledger cap under Andres's general permission of 16 October ("you have permission to run the deep seek agents", issue #41); the amount itself awaits his OK | Mac reading, then Andres |
| R4 | **Network.** Reachable from here: the S3 buckets `encode-public`, `4dn-open-data-public`, `gnomad-public-us-east-1` and `ngi-igenomes` (GTF/FASTA), plus PyPI (`pyjaspar`) and GitHub. Blocked: encodeproject.org, zenodo, NCBI, rest.uniprot.org, depmap.org, data.4dnucleome.org and api.deepseek.com (reviewer probes, curl 000/403). Everything else must be downloaded on the Mac, as Replogle was (`docs/LAB_STATE.md:196-200`) | Here or Mac |
| R5 | **No overlapping paid runs, nothing else while a driver runs** (`AGENTS.md`, Money and Mac sections). Astra's entry says no run was active at 22:04 UTC on 15 Oct (`HANDOFF.md` section 1, Astra's #40 entry); this was not re-checked | Whoever runs |
| R6 | **Gene lists.** The Norman gene list is committed (`docs/results/norman_frozen_export_20261013/manifest.json:1179`). The Adamson 2,055-gene list is not; only its 90 perturbation names are (`docs/mac/adamson_cf_ncells.json`). Adamson tables must be restricted on the Mac | — |

## 2. Getting new information to the agents

### 2.0 Plumbing (all free)

| Need | Detail | Evidence | Who |
|---|---|---|---|
| Builder for non-screen tables (per-gene table or edge list with a `description` of units and columns) | The only builder writes screen-format `perts[gene].delta` rows | `genemila/data/external_screen.py:289-346,563-680`; `tools/build_external_screen.py:1-31` | Lab-code owner or me; new file |
| Leave-one-out check that accepts tables, **with a matched-null mode** | Today it handles screens only, and it scores the 50 training perturbations | `tools/external_loo.py:5-24` | Same |
| The planner must see the file | The planner's state sections are cut at 2,500 characters; since 16 October the knowledge section has its own 8,000-character budget (`KNOWLEDGE_SECTION_CHARS`, below). Files are listed in sorted order. "Unexplored" is a substring match over `IDEA_BANK` keys, which have no mechanism, chromatin, turnover or dosage areas. Workers get the summary without the cut | `genemila/research_state.py:20-32,112-115,142,171,188-189`; `genemila/lab.py:767`; `genemila/worker.py:181` | **Astra, Claim #40.** Its branch `astra/biology-feature-discovery` is not on the remote (`git ls-remote`). We hand over these findings. One edit was made under Andres's approval of 16 October: `research_state.py` gained `KNOWLEDGE_SECTION_CHARS = 8000` and a three-line change in `render_state` that applies it to the knowledge section; nothing else in the file, `planner.py` or `prompts.py` changed |
| Free scripted controls on non-screen tables | The mock adds screen-format templates for every added file, which give constant features on tables; the smoke test rejects them | `genemila/providers/mock.py:364-378,786-809`; `genemila/pipeline.py:320-326` | Lab-code owner |
| Bundle copy, never an in-place add | A file dropped into `knowledge/` reaches every later run and makes its own arm. `write_bundle` deletes its output directory. Use `--set run.data_dir=<copy>` | `genemila/data/bundle.py:142-143,229-240,256-257`; `run_research.py:76-79,137-138` | Mac owner |

### 2.1 Candidate sources, re-ranked

Ranking rules:
- A source must be **fittable on the training perturbations**. A p × g interaction gets its coefficient only from training perturbations where the p-indicator is non-zero.
- Sources are motivated by **training out-of-fold failures** (GNPNAT1, SRPR, ERN1, CAD, MRGBP, ASCC3, MANF; `docs/results/ceiling_analysis.md:19,89`), not by visible-validation failures. The visible ones are listed only as anecdote, because choosing on them repeats the steering problem in M1. Visible failures from one run, scale_w16_r1: XRN1 0.181 vs ceiling 0.948, PSMD4 0.408 vs 0.992, MARS 0.652 vs 0.991, MRPL39 0.641, IDH3A 0.634 (`docs/results/noise_ceiling.md:73-95`). DNAJC19 (0.943 vs 0.995) and TIMM23 (0.836 vs 0.971) are *not* failures (`noise_ceiling.md:83,93`).
- Policy is read against `genemila/data/knowledge.py:13-16`, which excludes resources derived from perturbation screens or expression atlases.

**Data-source table**

| # | Resource | Cell line | Feature f(p,g) and training support | Policy risk | Build where | In-vitro test |
|---|---|---|---|---|---|---|
| 1 | UniProt signal peptide / TM topology | none (sequence) | ER-targeting class of g × p in a **pre-registered** SRP / translocon / OST / ERAD list. Fitted on in-training members SRPR, SRPRB, SRP68, SEC61A1, SEC63, DDOST, STT3A, SEL1L, SYVN1, DERL2 (`ceiling_analysis.md:37-88`). Biology: RAPP, SRP-dependent decay of secretory mRNAs (Karamyshev 2014, Cell, [PMC3931426](https://pmc.ncbi.nlm.nih.gov/articles/PMC3931426)). Mammalian RIDD is narrow; broad RIDD was shown in *Drosophila* (Hollien & Weissman 2006; Hollien et al. 2009 J Cell Biol), so it is not the main rationale. This **does not fix SRPR**, which is a target-similarity miss (see R0 and the complex control). It tests whether gene-side ER targeting adds anything beyond kNN within the branch | Clean | Mac (UniProt blocked here), <10 MB | SRP54 (**not** in Adamson) CRISPRi in K562 with paired reporters, functional vs scrambled signal sequence. Better: M9-style predictions for knockdowns absent from every dataset |
| 2 | Codon / amino-acid demand (GTF + FASTA) | none | Per transcript, the demand for the amino acid of a **cytosolic** aaRS × that aaRS knockdown. Fitted on training TARS, HARS, CARS. **Exclude IARS2** (mitochondrial; its demand comes from the 13 mtDNA proteins). Must beat an ISR/ATF4-target covariate, since aaRS loss acts mostly through GCN2–eIF2α–ATF4, which kNN already copies | Clean | Genome-wide **here** (iGenomes S3); restrict to Adamson genes on the Mac | CRISPRi MARS1 plus Ribo-seq/RNA-seq: is loss ordered by Met demand? **UNVERIFIED** that this is a measurable mRNA-level effect in human cells |
| 3 | MitoCarta3.0 sub-compartment ([PMC7778944](https://pmc.ncbi.nlm.nih.gov/articles/PMC7778944)) | mostly non-K562 | Compartment of g × mito-import or mito-ribosome p. Training support: TIMM44, SAMM50, HSPA9, SLMO2. Add an ATF4 column for the OMA1–DELE1–HRI relay (Guo 2020, Nature 579:427) | **Borderline**: its integration uses expression and co-expression evidence, which may count as "expression atlas" | Mac, <5 MB | CRISPRi TIMM44 in a DELE1- or HRI-null background; the ATF4 arm should disappear |
| 4 | ENCODE K562 TF ChIP-seq; JASPAR motifs × K562 DNase/ATAC | K562 | "p binds the promoter or enhancer of g". **Norman TF subset only.** CRISPRa switches on TFs that are silent in K562 (e.g. CEBPA, FOXA1, HNF4A, SPI1 in the Norman list, `manifest.json`). K562 ChIP covers only expressed TFs; silent TFs need motif × accessibility (FOXA1 is a pioneer, a caveat). Many Norman targets are not TFs | Clean; unlike CollecTRI, cell-line-specific | Peaks on S3 here, but choosing files needs the blocked portal (**UNVERIFIED** workaround); motifs via PyPI here | CRISPRa the TF + CUT&RUN; mutate predicted sites in 5–10 genes; the response should be lost only at mutated sites |
| 5 | Effector-domain strength of the **target TF protein** (Tycko 2020 Cell; DelRosso 2023 Nature; both K562 tiling screens) | K562 | Activation/repression-domain strength of TF p × CollecTRI or motif targets. Applies to Norman TF pairs only. Norman's activator (dCas9-SunTag/VP64) is the same for every pair member, so the domain is the TF's own | **Screen-derived** by the literal wording; Andres's call; its own arm | Mac (supplements; accession **UNVERIFIED**) | Mutate or swap the TF's own activation domain in an exogenous construct; the pair profile should shift as predicted |
| 6 | K562 mRNA half-lives: TimeLapse-seq (Schofield 2018, [PMC5831505](https://pmc.ncbi.nlm.nih.gov/articles/PMC5831505)), TT-seq (Schwalb 2016 Science; GEO GSE75792, **UNVERIFIED**) | K562 | **Cannot be fitted as half-life × "RNA-decay p" on the Adamson split**: no RNA-decay factor is in training, and XRN1 is visible validation. Use half-life (residualised on `control_mean`) × a perturbation property present in training (e.g. ISR/stress strength), or keep it for a cohort with decay factors in training | Borderline (kinetic, not an atlas) | Mac (GEO blocked) | CRISPRi XRN1 with a 4sU pulse; the delta profile should track the pre-measured half-life |
| 7 | Hi-C compartments, SON/lamina TSA-seq (Kim 2020 JCB) | K562 | Residual after expression × stress/induction p. Risks being a proxy for `control_mean` | Clean | Hard: GB-scale; the 4DN bucket is reachable, its portal is not | DNA-FISH relative to SON before and after knockdown |

**Controls every candidate must beat. These are covariates, not discoveries:**

- **C1:** alias-fixed gene sets, PPI and CollecTRI (R0).
- **C2:** curated complex membership (CORUM, literature-curated). Many targets are complex subunits whose partners are in the library: SRPR/SRPRB, TTI1/TTI2/TELO2, EIF2B2/3/4 with EIF2S1, the OST complex, SEC61A1/B/G (`docs/mac/adamson_cf_ncells.json`).
- **C3:** shared or bidirectional promoters and TSS distance from the GTF (buildable here). This catches CRISPRi spill-over to the neighbouring gene (Goyal et al. 2017, NAR, [PMC5665645](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5665645/), **verify**) and, for Norman, CRISPRa activation of the neighbour. It changes only a few genes per perturbation, so it is a weak control for gene-wide pattern features.
- **C4:** for rank 1, matched-size ER and secretory gene sets already in the bundle.
- **Cheap extras:** gnomAD constraint and pHaplo/pTriplo (dosage buffering for CRISPRa), and paralogs.

**Why real data matters, without overstating it.** The best models already carry features *named* after half-life, chromatin state, TF motifs and splicing (`docs/results/feature_audit_v3.json:96059-96075`), while the bundle holds no such data (`genemila/data/knowledge.py:5-11`). Their sources are on the Mac, so whether they are proxies or gene lists the LLM recalled from memory is **UNVERIFIED**. Supplying the real measurement turns a named proxy into a measured predictor. Its mechanism still has to be tested.

## 3. Method that makes a found feature credible

The three claims are: (a) it predicts better, (b) the specific biology carries the gain, (c) it is worth a wet-lab test. Costs: M1–M5 are free CPU work, M6 needs a Mac build, M7 needs a cohort and an external host, and M8 needs paid runs.

| # | Need | State today | Evidence | Who |
|---|---|---|---|---|
| M1 | **Training-only residual mining, used only to generate hypotheses.** Out-of-fold residuals and a per-perturbation table (gap to ceiling, maximum similarity to any training target). Mine on one half of the training perturbations, grouped by target, and score on the other half; or send outputs to M6/M7. M1 output never counts as evidence. It replaces the visible-validation worst-5 list the planner sees now | No tool writes residuals. `cv.npz` holds `delta, perts, alphas, folds` when `cv_folds > 1` (default 5) and is pruned to the chosen alpha | `genemila/pipeline.py:259-264`; `genemila/worker.py:39-48,104-107`; `configs/default.toml:24`; `genemila/benchmark/evaluator.py:90-105`; `genemila/research_state.py:149-151` | Me (synthetic tests) → Mac |
| M2 | **Matched nulls.** Permute gene labels within mean × variance bins, use degree-preserving rewiring of networks, permute target identities, shuffle cells per gene; ≥200 replicates, refitted exactly like the real feature. A `FeatureContext` subclass intercepts everything, because the guard bans other access | No null or permutation test of features exists; `rng.permutation` is used only for splits, folds and half-split ceilings | `genemila/guard.py:25-41`; `genemila/features/api.py:126-148`; `genemila/data/real.py:297`; `tools/noise_ceiling.py:94`; `tools/ceiling_analysis.py:68` | Me, new file |
| M3 | **Admission rule.** Compare *incumbent stack + candidate* against *incumbent stack + matched-null candidate*, not against gene-set kNN alone (0.545; the stack reaches 0.616 with Replogle). Require a paired gain positive on ≥3 fixed gene-fold partitions, with mean ≥ max(2·SE with clustering inflation, partition SD, null 95th percentile, 0.01), and MSE / top-20 MSE ratio ≤ 1.01. **Fix the number of sources and variants (m) before scoring and apply Holm.** With m = 8, the bar rises to about 2.7·SE ≈ 0.055 at SE 0.020 | `Lab.compare_visible` exists but is not used for admission. The B1 rule has a similar form | `genemila/lab.py:550-558`; `docs/B1_TWO_MEMBER_PLAN.md:41-63`; `external_loo_replogle2022_k562.md:19-23` | Lab-code owner |
| M4 | **Novelty beyond correlation** | **Exists:** \|r\| ≥ 0.9 redundancy, drop-one/compact-set "substitutable" verdicts, Lasso stability, label-read and `ctx.feature` call tracking (`tools/feature_audit.py:132-139,1164-1224`). **Missing:** nonlinear derivability (held-out R² of the candidate from incumbent columns plus products, logs and ranks; ≥ 0.8 means derived), tracking of which knowledge files and control statistics a feature reads, and a scan of plugin sources for hard-coded gene-symbol lists | as stated | Me |
| M5 | **Pre-registration with a sign**: a hashed record of formula, inputs, p-list, expected sign per modality (CRISPRi/CRISPRa), null family and m | No sign or pre-registration field. Overlaps Astra's "falsifier" contract | `genemila/spec.py:31-51`; `genemila/prompts.py:24-40` | Align with #40 |
| M6 | **Replication** on Norman (CRISPRa) and on a held-out slice of Replogle K562 CRISPRi that excludes Adamson and Norman targets and does not offer the Replogle knowledge file | No such bundle. `prepare_data.py h5ad --backed` is untested at genome-wide size | `prepare_data.py:33-70` | Mac + Andres |
| M7 | **One untouched test**, scored from frozen predictions by an evaluator the agents cannot reach. **Match the modality:** both candidate cohorts are CRISPRa (exp8, 49 genes; Pacalin, a 19-gene panel with a dSaCas9-VPR activator), so they can confirm Norman/CRISPRa features only. CRISPRi features (ranks 1–3) need a sealed CRISPRi slice (M6) | No isolation exists; frozen export exists | `docs/FROZEN_TEST_PLAN.md:42-46,78-81`; `genemila/frozen.py` | Andres |
| M8 | **Attribution**: equal-budget arms of agents without the human list, agents with it, and the list run without an LLM; the list is hashed first | Missing | `genemila/research_state.py:20-42` | Andres's decision, paid |
| M9 | **Wet-lab list**: perturbations in no dataset where incumbent and incumbent + feature disagree most, plus matched negatives and a power calculation | Missing | — | After M1–M7 |

**Bars to stand out from noise:** about +0.04 paired on Adamson leave-one-out for a single pre-specified test (2·SE, SE ≈ 0.020; `docs/results/external_loo_replogle2022_k562.md:23`), higher after the multiplicity correction. On a three-repeat Norman arm the bar was 0.0118 (`docs/NORMAN_PLAN.md:530-531`).

## 4. Credibility chain

R0 alias check → build the table into a bundle copy → pre-register (M5) → free leave-one-out against the stack + matched null (M2, M3), with Holm over m → novelty audit (M4) → agent arm with the file (paid; M8 attribution) → replicate with the expected sign (M6) → one untouched, modality-matched test (M7) → wet-lab predictions (M9).

A hand-built feature scored by humans first is a **human-led positive control for the plumbing**, not agent discovery (`HANDOFF.md` section 1, Astra's #40 entry: Andres asked that the agents choose and test "automatically"). If agent discovery is the claim, run the agent arm before any human scores a hand-built version, and hash and seal the hand-built version.

## 5. Decisions for Andres

| # | Decision | Options and consequences | Status |
|---|---|---|---|
| D1 | Allowed sources | Clean: ranks 1, 2, 4, 7 and controls C1–C3. Borderline: 3 (MitoCarta) and 6 (half-lives). Screen-derived: 5 (effector domains), ENCODE-rE2G and thresholded ABC. Each is its own arm, not CellForge-comparable (`docs/NEXT_LEVER.md:96-100`) | Open; the Replogle exception was chosen 11 Oct (`HANDOFF.md` section 1, the "Results on Adamson" paragraph) |
| D2 | Which spend cap and block | Last committed $43.60 of $48 (`HANDOFF.md` section 1, the 14 October model-quality entry). B4 ran under a $52 block, gate $49.50 (PR #39, open draft), costs not in the repo. PR #38 (open draft) asks for $10–30 more. Money is needed only for agent arms (M8) and agent runs with new files | Block F (`docs/PLAN_F_GENOME_ANNOTATION.md`) proposes an $8 ledger cap under Andres's general permission of 16 October ("you have permission to run the deep seek agents"); the amount itself awaits his OK |
| D3 | Feed human hypotheses (Astra's 200, your review) to the agents? | Yes → the claim becomes "the agent selected a human hypothesis" unless M8 shows otherwise; each reviewed list adds to m | Open; #40 is building the bank |
| D4 | Fresh test cohort and evaluator holder | CRISPRa cohorts (GSM4367986, GSE220974) confirm Norman features only; CRISPRi needs a sealed Replogle slice. Without these, no "beats CellForge on test" claim. CellForge is not comparable today (`docs/results/norman_b1_frozen_test_review_20261013.md:68-83`) | Deferred 13 Oct, "deferred, not approved" (#22, last updated 2026-10-13T22:41Z; `HANDOFF.md` section 1, the 14 October model-quality entry); re-raised in PR #38 §6 (reviewer-reported, not re-read) |
| D5 | Build the Replogle K562 replication bundle (M6) | Free, Mac CPU, untested size | Not yet asked |
| D6 | Adapt CellForge's multi-expert discussion | No claim, plan or PR covers it. `docs/comparison/cellforge_notes.md:49-53` cites CellForge's `Method_Design/experts.py`, `graph_discussion.py` and `refinement.py` only for preprocessing defaults. It overlaps the planner files held by #40 | Open, unowned |

**Fit with in-flight work.** Astra's #40 owns the hypothesis side: `genemila/biology.py`, the planner, `research_state`, prompts and `configs/biological_discovery.toml` (issue #40 body). We supply data, M1 tables, the M2 null context and the M4 checks as new files. PR #38 sets the paper criteria; Part 3 is a concrete implementation of them. PR #39 matters here only for the ledger.

**What cannot be promised.**
- A novel feature may not exist in these data.
- RAPP, ISR and the mitochondrial relay are known biology. Confirming them would be a strong methods result, not Nature-level novelty, unless a surprising prediction is confirmed in the wet lab.
- Possible hidden leakage (**UNVERIFIED**): Enrichr GO BP carries no evidence codes, so some annotations may come from expression (`genemila/data/knowledge.py:30`); plugins may hard-code recalled gene lists; cache hits may hide label reads (`genemila/pipeline.py:173-179`).
- The Norman sealed singles show no difference against the additive rule (0.495 vs 0.504; `docs/results/norman_sealed_reading.md:15`). This is context only and must not steer source choice (`AGENTS.md`, Scientific integrity). The visible singles favour the model, +0.034 ± 0.015 (`:20`).

## 6. Smallest first step: exact commands (free, read-only, no protected files)

**Step A, Mac, from any clone. Read the state and the ledger.** The default `--runs` is the clone's own `runs/` (`handoff_state.py:152-153`), so point it at the main checkout (`HANDOFF.md` section 1, the "Live sources" table):
```bash
python handoff_state.py --fetch --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs
sqlite3 ~/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite \
  "SELECT provider, ROUND(SUM(cost_usd),2) FROM spend GROUP BY provider"
```

**Step B, Mac. R0 symbol-coverage check.** `tools/knowledge_coverage.py` (added with this document) reads only the
bundle's `public.npz` and `knowledge/`, never `private/` or `splits.json`. It lists every target's gene sets, interaction
partners, regulatory edges and external-screen rows; with HGNC's complete set (download `hgnc_complete_set.txt` from
genenames.org on the Mac) and the raw knowledge sources it also reports, in three separate sections, targets under a
retired symbol with what the current symbol would bring, targets that are only an alias of another gene (to check by
Ensembl id before mapping), and unannotated targets that are themselves approved symbols (labelled, never renamed):
```bash
MAIN=~/Documents/Mila/Gene-Mila/gene-mila
python tools/knowledge_coverage.py --data "$MAIN/data/adamson_cf" --out coverage_adamson.md \
  --hgnc hgnc_complete_set.txt --sources <the directory genemila.data.knowledge.download wrote>
```
Targets in bold have no annotation at all. A mapped symbol goes into a **bundle copy** as its own arm, then is
re-scored with `tools/external_loo.py` or `tools/feature_compare.py`.

**Step C, later. Residual dump for M1.** Read `$MAIN/runs/<run>` read-only and write only into your own clone or a scratch directory, never under the main checkout (`AGENTS.md`, Mac section):
```python
import numpy as np, sys
run, eid, out = sys.argv[1:4]          # out: <own clone>/runs/residuals_<run>.npz
pub = np.load(f"{run}/public_data/public.npz")
cv  = np.load(f"{run}/artifacts/{eid}/cv.npz")   # exists only if cv_folds > 1
assert cv["alphas"].shape == (1,), "not pruned: index by the experiment's best_alpha"
order = [list(pub["train_perts"]).index(p) for p in cv["perts"]]
y = pub["train_means"][order] - pub["control_cells"].mean(0)
np.savez_compressed(out, resid=y - cv["delta"][0], perts=cv["perts"], genes=pub["genes"])
```

**Step D, free tools (claim #41).** `tools/feature_compare.py` scores any feature file against the same parent model
with a matched null and Holm correction, and `tools/export_task_package.py` gives other systems the identical task.
`feature_compare` is a first, partial implementation of M2 (gene permutation within control-mean bins only) and a
weaker form of M3 (2·SE, wins on most perturbations, Holm-adjusted null p, top-20 MSE not significantly worse).
Still missing from M2: bins on mean × variance, degree-preserving network rewiring, target-identity permutation and
cell shuffles; from M3: the partition-SD term, the 0.01 floor and the MSE ratio guard (≤ 1.01). Also still open: the residual dump as a tool (M1), per-gene table builders for the sources in
section 2.1 (the genome annotation is reachable from the cloud through the iGenomes S3 bucket; most others must be
downloaded on the Mac), and the nonlinear-derivability check (M4). The genome annotation builder is done
(`tools/build_gene_annotation.py`; section 9).

## 7. Recommended data-source policy (Andres asked for one on 16 October; approved by him at 21:08 UTC that day, #41)

Rule: **a source is allowed if it was measured or derived without perturbing genes and does not contain the expression
responses the lab predicts.** Unperturbed K562 measurements are allowed for the same reason the control cells are.

| Tier | Admission | Sources | Why |
|---|---|---|---|
| 1 | Allowed by default; any system in a comparison gets the same files | genome sequence and annotation (GENCODE, hg38: built, `tools/build_gene_annotation.py`); protein sequence features (UniProt signal peptides, transmembrane topology); curated physical complexes (CORUM); paralogs (Ensembl Compara); population constraint (gnomAD LOEUF; Collins 2022 pHaplo/pTriplo); unperturbed-K562 measurements (ENCODE TF ChIP-seq, DNase/ATAC, histone marks; Hi-C) | No perturbation or expression response behind them; K562 measurements describe the starting state, like `control_cells` |
| 2 | Allowed, each as its own labelled arm, never pooled with tier 1 | Each is an explicit exception to the tier-3 criterion: MitoCarta3.0 (excepted from the co-expression exclusion; its integration uses expression and co-expression evidence); K562 mRNA half-lives (excepted as an expression measurement; metabolic labelling of unperturbed cells, a kinetic rate rather than an atlas); effector-domain recruitment screens (Tycko 2020, DelRosso 2023; excepted from the perturbation-screen exclusion; they score protein domains recruited to a reporter, not responses of the genes the lab measures) | Clean in intent; each carries an expression-derived or screen-derived component that must be visible in the arm's name |
| 3 | Not allowed for the main claim | anything derived from perturbation screens (Replogle 2022, already its own arm; DepMap fitness), expression atlases or co-expression (GTEx, STRING's co-expression channel, Enrichr GEO libraries), and anything built from the evaluated datasets themselves | They can carry the answer: a response measured for the same target in another screen, or genes that move together because they respond together |

Tier 1 extends the "only curated knowledge" rule of `genemila/data/knowledge.py:13-16` to unperturbed measurements
(ENCODE, Hi-C, gnomAD). The bundle's existing `gene_sets` fall under this policy too: MSigDB Hallmark sets were refined
with expression data and Enrichr's GO BP carries no evidence codes, so some annotations may be expression-derived.
Whether they stay in tier 1, as today, is Andres's call.

Recommended first step: approve tier 1 and start with the genome annotation table (block F,
`docs/PLAN_F_GENOME_ANNOTATION.md`); next, signal peptides and CORUM complexes, which match Adamson's ER-stress
knockdowns. Tier 2 one arm at a time afterwards. The existing Replogle arm stays as it is and is labelled.

## 8. 2,000 genes instead of 20,000 (Andres's question of 16 October)

- **The lab already works on about 2,000 genes:** each bundle keeps the 2,000 most variable genes, ranked on control
  cells (Adamson) or on control plus training-perturbation cells (Norman, `--gene-selection control+train`), plus
  every target (`prepare_data.py --hvg 2000`; Adamson 2,055 and Norman 2,083 genes; `README.md`,
  `docs/NORMAN_PLAN.md` §3 item 4).
- **The DeepSeek bill does not depend on the number of genes.** The agents write feature code; their prompts carry the
  research state, never the expression matrix (`docs/ARCHITECTURE.md`, "Token efficiency"). What grows with genes is
  CPU time and memory: the design matrix has perturbations × genes rows, and a gene-by-gene matrix such as the control
  co-expression `FeatureContext.gene_corr` grows with the square: about 32 MB at 2,000 genes, about 3.2 GB at 20,000.
- **A feature found on 2,000 genes transfers at no LLM cost:** it is code, f(p, g), so it can be refitted and scored
  on a bundle with more genes by CPU alone. Proposal: search on 2,000 genes as now, freeze the features, then score
  them once on a bundle of all genes expressed in K562 control cells (about 8,000–11,000, since many of the 20,000 are
  not expressed there; UNVERIFIED count) built from the same h5ad with the same perturbation split, and report both.
  The perturbation split is the same, so `split_id` is the same; the bundle name must tell the two apart.
- **Two cautions.** Highly variable genes are the responsive ones, so scores on 2,000 genes are higher than on all
  genes; every number names its gene set. And the axis that adds evidence is the number of perturbations, not genes:
  pearson_delta is averaged over perturbations, so its standard error shrinks with perturbations. Replogle's K562
  essential-gene screen (about 2,000 knockdowns, about 10,000 genome-wide) is where a feature can show it generalises
  (M6).

## 9. Findings in this session (16 October)

- **Retired symbols also affect Norman's measured genes.** Building the genome annotation for the committed Norman
  gene list (`docs/results/norman_frozen_export_20261013/manifest.json`) against GENCODE v27 matched 2,041 of 2,083
  genes; the 42 unmatched are retired or renamed symbols (for example SEPP1, KIAA0101, TCEB1, SEP15, HN1). The knowledge
  loader matches symbols exactly, so the current gene-set, interaction and regulatory files may miss these genes too.
  Counting it needs the Mac (`tools/knowledge_coverage.py`, R0).
- **96 Norman genes have their TSS within 1 kb of another measured gene's TSS on the opposite strand** (48 pairs, for
  example ALYREF and ANAPC11, AAMP and PNKD). Most are head-to-head shared promoters; in 16 of the 48 pairs the two
  genes overlap at their 5' ends instead. A CRISPRa or CRISPRi guide at one of these TSSs can reach the other gene; the lab
  had no way to represent this before the annotation table.
- **Values checked by hand** on the representative transcripts: KLF1 362 amino acids, CEBPA 358, SET 290 and HBG1 147,
  as in UniProt; MYC's CCDS transcript with the longest coding sequence is the 454-residue CUG-initiated isoform.

## 10. Second batch (16 October): constraint and protein builders, residual mining, CellForge-translated features

- `tools/build_gene_constraint.py` turns gnomAD v2.1.1 by-gene constraint (LOEUF, pLI, observed/expected LoF and
  missense, z scores, flags) into a knowledge file; built for Norman: 2,018 of 2,083 genes matched, 65 unmatched (mostly
  non-coding RNAs, which gnomAD does not score, plus about 18 symbols gnomAD lists under GENCODE v19 names). Tier 1.
- **A limit found while building it:** the planner reads every knowledge file's description in one section cut at
  2,500 characters. Norman's five bundle files plus the Replogle file take about 2,320; `gene_annotation` adds 895, so
  block F fits, but `gene_constraint` (546) on top does not: the cut would hide the Replogle description. Adding a
  second new file to the same bundle needs the planner state to render knowledge differently
  (`genemila/research_state.py`, held by #40) or its own arm without Replogle. The item is for the lab-code owner.
  **Done, 16 October, with Andres's approval:** `render_state` gives the knowledge section its own budget,
  `KNOWLEDGE_SECTION_CHARS = 8000` (every other section keeps 2,500; the 20,000 total is unchanged), so the clean
  bundle with the three tables fits. The pre-run gate of any later block reads the constant rather than `2500`.
- `tools/build_protein_annotation.py` reads a UniProt TSV export (signal peptide, transmembrane segments, localisation)
  into a knowledge file; UniProt is not reachable from the cloud, so it runs on the Mac, and it refuses an export whose
  header names differ from the ones it expects rather than guess.
- `tools/residual_mining.py` (M1) ranks the training perturbations the parent model predicts worst, out of fold, next
  to their similarity to other training targets (gene sets, PPI, co-expression) and finds per-gene residual
  correlations with control statistics and with every numeric `gene_annotation` column. Hypothesis generation only:
  a source chosen from it is selected on the labels `feature_compare`'s OOF tier scores, so that tier only screens it.
- `docs/comparison/cellforge_c2/`: four features we translated from CellForge's design ideas (arm A5-C2 of the
  comparison protocol), with their source citations and the statement that they are our translations. One of them,
  the pair interaction term, is zero on every out-of-fold row under gene-grouped folds (a pair's singles are hidden
  with it), so on Norman it can only be read on the visible-validation tier.

