# Lead H8 protocol frozen before scoring

Clarification: https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6236891780

Plugin SHA256: d561229865326a42fd0e562f7cb294f40b77788aa0b6ce547c277935311a23ad

Current integration README copied verbatim below; scores still absent.

# The lead's hypothesis: residualised constraint (family 8)

One feature plugin written by the lead, `h8_constraint_residual.py` (feature `h8_constraint_residual`). It is the
hand-written hypothesis test of [`docs/ROADMAP.md`](../../ROADMAP.md) D4, pre-registered as family 8 of
[`docs/PREREG_G_KNOWN_BIOLOGY.md`](../../PREREG_G_KNOWN_BIOLOGY.md): constraint residualised on control expression
and tier-1 essentiality proxies. **It is a human hypothesis.** `tools/feature_compare.py` scores it like any other
`--source`, and whoever reports it says "the lead's hypothesis", never GOAL_CRITERIA A.1: no agent found it, and the
agents of block G never see this file (their checkout is pinned at `baa7dfd`, which predates it). Fixed now, before
any block G score exists. The section "Where this departs from the wording of family 8" below, and the dated note of
2026-10-17 at the end of the pre-registration, record how the family's one-sentence formula shape was turned into
code. **Nothing here has run on real data.**

## The pre-registration (family 8)

- Sign: Adamson CRISPRi **positive** (residual constraint scales the response up beyond basal expression and
  essentiality). Norman CRISPRa: not predicted.
- Verdict before reading: **OPEN** (the one open family with power, ROADMAP D3).
- Null: **both** (the gene null and the perturbation null), because the candidate is a parent column times a
  per-perturbation scalar.
- Minimum effect of practical interest: mean out-of-fold M1 gain above `max(2 SE_adj, 0.002)`.
- A family of one: the step-down correction has one member, so `p_fwer` equals the raw null p.

## The feature, exactly

Per output gene j of the bundle: constraint `s_j = -oe_lof_upper_j` (minus LOEUF, so larger means more constrained),
taken from `ctx.knowledge("gene_constraint")` (`tools/build_gene_constraint.py`: `genes[symbol]` is one value per
entry of `columns`, `null` where gnomAD has none). Genes without a value are left out of the fit and get `rho_j = 0`
below. Genes gnomAD flags (`flags` in the table: `lof_too_many`, `syn_outlier`, `no_variants` and the others) are used
like any other gene with a value: the pre-registration says nothing about the flags, and LOEUF is defined for them.

Confounds, per gene: `x1_j = ctx.control_mean[j]`, the mean of the control cells, which the bundle stores already
log1p-normalised (counts per 10k, `prepare_data.py`), so this is log basal expression and no further log is applied;
`e_j = 1` if gene j belongs to any CORUM complex set in `ctx.knowledge("gene_sets")` (the clean bundle names them
`CORUM:<complex>`, `genemila/data/knowledge_clean.py`), else 0; `r_j = 1` if it belongs to any Reactome set
(`REACTOME:<pathway>`) whose name contains `ribosom`, `proteasom` or `mrna splicing` (case-insensitive;
`ESSENTIAL_WORDS` in the file), else 0. The sets these words select are listed in the next section. If the bundle
has no `gene_sets`, or none of those sets, the indicators are all zero and the residual then removes basal expression
only; that case is reported as such, not as family 8 (see the pre-run command under Scoring).

Fit, once per context (cached on `ctx.cache`), ordinary least squares over the genes that have a constraint value:
`s_j ~ 1 + x1_j + e_j + r_j`; residual `rho_j = s_j - fitted_j`; genes without a value get `rho_j = 0`. The fit is
skipped, and every `rho_j` is 0, when fewer than 5 genes have a value (a four-parameter fit needs them; no real bundle
is near that).

Per perturbation p: `c_p` = mean of `rho` over p's target genes that have a constraint value (`ctx.target_genes(p)`;
targets outside the bundle or without a value skipped; no such target gives `c_p = 0`).

Output `(len(perts), n_genes, 1)`: `additive_response[i, :] * c_p`, with `additive_response` from
`ctx.feature("additive_response", perts)` (`dependencies = ["additive_response"]`). The candidate is therefore
proportional to a parent column, and `tools/feature_compare.py` applies both nulls to it, as the pre-registration
requires. The file is deterministic (no `hash()` or `id()`, sets iterated in sorted order), reads training labels only
through `additive_response`, passes `genemila.guard.check_plugin_source` and the literal caps of
`tools/task_package/literal.py` (2,026 of 2,500 string bytes), and passes `python -m genemila.pipeline smoke`.

## The gene sets the words match

The clean bundle's Reactome sets come from the public `ReactomePathways.gmt.zip` (`knowledge_clean.reactome()`),
kept when 3 to 500 bundle genes belong to them. In that file as read on 2026-10-17 (2,868 pathways; the bundle's own
copy is the one that counts, hence the pre-run command below) the three words select these pathway names, with the
file's gene counts:

- `ribosom` (7): GTP hydrolysis and joining of the 60S ribosomal subunit (117); Ribosomal scanning and start codon
  recognition (60); Ribosome-associated quality control (149); Ribosome Quality Control (RQC) complex extracts and
  degrades nascent peptide (106); ZNF598 and the Ribosome-associated Quality Trigger (RQT) complex dissociate a
  ribosome stalled on a no-go mRNA (101); PELO:HBS1L and ABCE1 dissociate a ribosome on a non-stop mRNA (95);
  Mitochondrial ribosome-associated quality control (114). The cytosolic ribosomal proteins enter through the first
  two and the quality-control sets.
- `proteasom` (9): Proteasome assembly (52); Antigen processing: Ub, ATP-independent proteasomal degradation (19);
  Antigen processing: Ubiquitination & Proteasome degradation (296, the proteasome subunits together with the
  ubiquitination machinery, E3 ligases and the APC/C among them); Degradation of GLI1 by the proteasome (47);
  Degradation of GLI2 by the proteasome (47); GLI3 is processed to GLI3R by the proteasome (47); GSK3B-mediated
  proteasomal degradation of PD-L1(CD274) (44); SPOP-mediated proteasomal degradation of PD-L1(CD274) (46); Regulation
  of activated PAK-2p34 by proteasome mediated degradation (37). The word is wider than the proteasome itself; the
  indicator is a covariate that only has to carry the proteasome, and the choice is fixed here before any score.
- `mrna splicing` (3): mRNA Splicing (215); mRNA Splicing - Major Pathway (204); mRNA Splicing - Minor Pathway (53).
  No Reactome pathway name contains "spliceosome"; these three are Reactome's spliceosome sets. The word does not
  match FGFR2 alternative splicing (28).

`tests/test_lead_h8_constraint.py` holds this selection as a test on the names.

## Where this departs from the wording of family 8

Family 8's formula shape is one sentence: "the residual of the targets' mean constraint after regressing out their
mean control expression (`ctx.control_mean`) and membership indicators for tier-1 essentiality proxies, then times
`additive_response`". The code is fixed as follows, recorded here and in the dated note of 2026-10-17 at the end of
`docs/PREREG_G_KNOWN_BIOLOGY.md`, before any block G score exists.

1. **The fit is at the gene level, then averaged over the targets.** The regression runs once over every bundle gene
   with a LOEUF value (about two thousand), on per-gene covariates, and `c_p` is the mean residual of p's targets.
   The sentence read literally would fit over the perturbations (88 on Adamson, 102 on Norman) using the targets'
   means; on a single-gene panel that is the same regression restricted to the target genes, a biased subset (the
   UPR and secretory panel on Adamson) with twenty times fewer points. The two give different `c_p` vectors (on the
   test fixture they correlate at about 0.97), so this is an operationalisation, not a rewording.
2. **`e_j` is membership in any CORUM complex of the clean bundle.** The pre-registration and ROADMAP D3 say "CORUM
   core complexes"; the clean bundle is built from `corum_allComplexes.txt` (`knowledge_clean.corum()`) and carries
   no core-complex table, so every complex counts.
3. **The Reactome sets are selected by name.** The pre-registration names "the Reactome ribosome, proteasome and
   spliceosome sets" without listing them; the words above and the pathways they select are the fixed reading.
4. **The covariate is `ctx.control_mean` itself**, as the pre-registration names it (the first draft of the plugin
   applied `log1p` to it a second time; corrected before any score, with the test).

## Why each confound is removed

Family 6 of the pre-registration (raw constraint) is KNOWN: constraint is a proxy for essentiality and basal
expression, and essential, highly expressed genes already produce the largest transcriptional responses, so a raw
constraint feature restates that known dependence through its confounds. Family 8 removes both: the control mean
takes out basal expression, and the CORUM and Reactome ribosome, proteasome and mRNA splicing indicators are the
tier-1 essentiality proxies (DepMap is tier 3 and excluded, `docs/NOVEL_FEATURE_NEEDS.md` section 7). What is left,
if it predicts the response, is the new rule the hypothesis claims.

## Scoring (Astra, on the Mac, after block G; free; ROADMAP section 6 note of 2026-10-17)

Never beside a paid run, at `nice -n 19`, with `<MAIN>` the main checkout and `<ds>` each of `adamson_cf` and
`norman`. First, the sets and counts the real bundle gives the feature, posted on #41 with the result:

```
python -c "
import json, sys
b = sys.argv[1]
sets = json.load(open(b + '/knowledge/gene_sets.json')); con = json.load(open(b + '/knowledge/gene_constraint.json'))
k = con['columns'].index('oe_lof_upper'); genes = set(con['genes'])
words = ('ribosom', 'proteasom', 'mrna splicing')
r = [n for n in sorted(sets) if n.startswith('REACTOME:') and any(w in n.lower() for w in words)]
e = {g for n in sets if n.startswith('CORUM:') for g in sets[n]}
print('valued', sum(v[k] is not None for v in con['genes'].values()), 'of', len(genes))
rg = {g for n in r for g in sets[n]} & genes
print('corum genes', len(e & genes), 'reactome sets', len(r), 'reactome genes', len(rg))
print('\n'.join(r))
" <MAIN>/data/<ds>_clean_tables
```

If a word selects no set, the row is reported as "residualised on expression and CORUM only", not as family 8. Then:

```
nice -n 19 python tools/feature_compare.py --data <MAIN>/data/<ds>_clean_tables --out docs/results/<ds>_lead_h8 \
  --source LEAD_H8=docs/comparison/lead_h8_constraint --null-reps 999
```

The report is `feature_compare.md` and `feature_compare.json` in `--out`; cite them with the directory, as every
number in this repository is. Fewer than 999 replicates reads "null too coarse" and decides nothing. The tool's
default fold seeds are 101, 102 and 103, the protocol's.

## How to read the result

In the row `h8_constraint_residual` of each report (a family of one):

1. `proportional` is `true` and `parent_column` is `additive_response` on Norman and `mean_response` on Adamson
   (the note of 2026-10-17 16:45 UTC below says why); otherwise the file did not run as written.
2. Both nulls pass: `null.p_fwer` and `null_pert.p_fwer` are each at most 0.05.
3. The gain is above the minimum effect: the mean out-of-fold M1 gain exceeds `max(2 SE_adj, 0.002)`.
4. The sign: `coef_candidate_std` is positive in every fold seed on Adamson (the prediction); on Norman the sign is
   recorded, not predicted. A sign that flips in any fold seed on Adamson drops the mechanism claim and the feature
   is reported as predictive but unexplained.

A pass on 1 to 4 is reported as "the lead's pre-registered hypothesis, OPEN, supported on Adamson", provisional until
the citation pass of `docs/CANDIDATE_LITERATURE_CHECK.md` confirms its keys; a failure is reported as such. Neither
is A.1. **Nothing has run.**

## Tests

`python -m pytest -q tests/test_lead_h8_constraint.py`: the guard and the literal caps; on a pair bundle with a
synthetic `gene_constraint` table and `CORUM:` and `REACTOME:` sets (a ribosome set, an mRNA splicing set, two sets
the words must not match), the shape, a zero row for a perturbation whose targets have no value, and equality with
`additive_response` times the hand-computed residual mean; the fit without `gene_sets`; the word rule against the
public Reactome pathway names; the pipeline smoke; `tools/feature_compare.py` reporting the row as proportional to
`additive_response` with a `null_pert` on the pair bundle; and, on a single-target bundle, the same row proportional
to `mean_response` with a `null_pert` (the Adamson reading below).

## Note, 2026-10-17 16:45 UTC: what `parent_column` reads on Adamson

Written before any score of this plugin exists, in answer to the operator's source-only question of 03:25 UTC on
[#51](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6229018744). The comparison tool's default
parent is the three built-in features (`control_mean`, `mean_response`, `is_target`) plus `additive_response` only on
a bundle with pairs (`tools/feature_compare.py`, the `data.pair_ids` test; `genemila/features/registry.py` builds
`additive_response` in on pair bundles only). On Adamson, a single-target bundle, the parent therefore has no
`additive_response` column, and the detector can never name it. The plugin still computes `additive_response`
times its scalar, as written: on unique single targets `additive_response` leaving p out is the mean training change
(`additive_delta`, the fill for a gene without a training single), which is the column `mean_response`, so the row is
proportional to `mean_response` and the perturbation null is applied with that parent. The reading rule, fixed now:
on Adamson, check 1 passes with `parent_column` equal to `mean_response`; on Norman it must read
`additive_response`. Nothing else changes: not the formula, the sign, the nulls, the minimum effect or the verdict
vocabulary. If the Adamson row came out not proportional (`proportional` false, no `null_pert`), the operator posts
the row and stops; the lead reads it, and no rule is adjusted after the fact.
`tests/test_lead_h8_constraint.py::test_on_a_singles_bundle_the_parent_column_reads_mean_response` checks this
reading on a synthetic single-target bundle.
