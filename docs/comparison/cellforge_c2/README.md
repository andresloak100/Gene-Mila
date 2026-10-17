# CellForge ideas, translated by us (arm A5-C2)

Four feature plugins written by us from design ideas in CellForge's published code and model cards
(gersteinlab/CellForge, commit `6585ff9`, read locally; arXiv 2508.02276). They are the C2 tier of arm A5 in
[`docs/FEATURE_COMPARISON_PROTOCOL.md`](../../FEATURE_COMPARISON_PROTOCOL.md): CellForge itself produces a deep model
and a training script, never features, and ships no weights, so there is nothing of CellForge's to score at the feature
level. **Every file here is our translation of an idea into a feature f(p, g) of a fixed linear model. Nothing in it is
CellForge's output, and no CellForge code ran.** `tools/feature_compare.py` labels a row by its `--source` name, so the
commands below pass the protocol's `A5_C2`; whoever writes the report up (`docs/results/`, the paper) spells that arm
"CellForge ideas, translated by us", as the protocol's section on arm A5 does, never "CellForge". Nothing here has run
on real data yet.

Each plugin is written against `genemila/features/api.py`, passes `genemila.guard.check_plugin_source` and the literal
caps of `tools/task_package/literal.py`, reads training labels only through `ctx.train_delta(exclude=p)`, uses every
target of a pair in a fixed order, and is deterministic (no `hash()`/`id()`). `python -m genemila.pipeline smoke`
records each file's CPU time and its estimate for the whole bundle in `smoke.json` (`smoke_cpu_s`,
`estimated_full_cpu_s`); `cf_latent_offset`, one SVD per perturbation, is the slowest. Feature names are prefixed
`cf_`; the file `<name>.py` registers feature `<name>`.

## Provenance

| file | CellForge idea | where CellForge says it | inputs the plugin reads |
|---|---|---|---|
| `cf_grn_propagation.py` | totalGAT: graph attention over a gene interaction network, "so the perturbation effect propagates along known biology rather than through a dense layer"; gene regulatory networks as a model constraint | `docs/MODELS.md:108-109`; `cellforge/Method_Design/experts.py:583`, `:696`; `cellforge/Method_Design/refinement.py:941` | `targets`, `prior_network` (CollecTRI, signed; `ppi_network` unsigned when absent). No label. |
| `cf_pathway_transfer.py` | pathway constraints in the plan template; a pathway proposal over KEGG, Reactome, GO and MSigDB; the "Pathway modularity" assumption | `cellforge/Method_Design/graph_discussion.py:865-869`, `:882-895`; `cellforge/Method_Design/refinement.py:302-306` | `targets`, `gene_sets`, `train_delta` (leave-one-out) |
| `cf_latent_offset.py` | CPA-X: a disentangled perturbation embedding in a latent space "explicitly factorised: perturbation effect on one axis", perturbations as additive latent offsets; a gene embedding from ontology and pathway information | `docs/MODELS.md:17`, `:31-40`; `cellforge/Method_Design/refinement.py:1022` | `targets`, `ppi_network` (`prior_network` undirected when absent), `train_delta` (leave-one-out) |
| `cf_pair_interaction.py` | scGen-X for Norman: latent arithmetic plus "an explicit interaction term for gene pairs, so the model can represent synergy and antagonism rather than being forced into additivity" | `docs/MODELS.md:18`, `:54-56` | `targets`, `train_delta` (leave-one-out). Two columns: product of the singles' changes, sign-aware minimum. Zero on every gene-grouped out-of-fold row (below). |

(The plan template's `embedding_dimension: 128` and `interaction: element_wise_multiplication` at
`graph_discussion.py:872-879` belong to its cell-type proposal, not to a perturbation embedding or a pair term, so they
are not cited.)

What each translation does, in one line each (the docstrings say more):

- `cf_grn_propagation`: a unit signal on p's targets, propagated up to `steps` hops along out-degree-normalised signed
  regulator -> target edges, damped per hop; the sign of a knockdown's effect is left to the coefficient.
- `cf_pathway_transfer`: the mean training change of perturbations whose targets share gene sets with p's targets,
  weighted by the Jaccard overlap of the two set profiles.
- `cf_latent_offset`: the top-`rank` singular vectors of the training changes are the latent space; p's latent code is
  the kernel-weighted mean of the codes of training perturbations whose targets neighbour its own in the PPI graph,
  decoded back to genes.
- `cf_pair_interaction`: only the interaction (the additive part is the lab's built-in `additive_response`), for a
  perturbation of several genes whose singles are all in training. On a bundle without pairs (Adamson) it is zero
  everywhere, and `tools/feature_compare.py` rejects it there as constant: expected, and the row says so.
  **Its out-of-fold row measures nothing on a bundle with pairs either:** the tool groups the folds by gene there
  (`--groups auto`; `genemila.pipeline.cv_folds_of`), so a predicted pair always has at least one single hidden from
  the fold's view and the term is zero on every predicted row by construction, while it is nonzero on the view's
  training rows (`tests/test_cellforge_c2.py` records this). The ridge can only fit coefficients it then multiplies by
  zero, so the OOF add-one row can show no gain, only the distortion of the other coefficients. The term is measurable
  only where a pair's singles are both in the full training set: the visible-validation tier (`--with-val1`, the
  seen-2 pairs of val1) and the sealed test split, where the lab would use it.

Where a knowledge file is missing the plugin falls back as the table says, or returns zeros; it never fails.

## Scoring (on the Mac, where the data is; free; `nice -n 19`)

Add this directory as one more `--source` of the comparison call the protocol gives (section "Scoring every arm"), so
every arm shares one parent scoring; or alone:

```
nice -n 19 python tools/feature_compare.py --data data/norman --out $HOME/gm_compare/norman_cf_c2 \
  --parent builtin --source A5_C2=docs/comparison/cellforge_c2 --fold-seeds 101,102,103 --null-reps 999 --with-val1
nice -n 19 python tools/feature_compare.py --data data/adamson_cf --out $HOME/gm_compare/adamson_cf_c2 \
  --parent builtin --source A5_C2=docs/comparison/cellforge_c2 --fold-seeds 101,102,103 --null-reps 999
```

The source's add-one family has four rows; every family needs `--null-reps` >= 999 before its family-wise p is read
(`docs/FEATURE_COMPARISON_PROTOCOL.md`, section 4, "Null replicates"; fewer reads "null too coarse"), and 999 is the
tool's default. A `--source` file is scored with its own class params only (the tool reads no params file next
to it). The report is `feature_compare.md` and `feature_compare.json` in `--out`; cite them with the run directory, as
every number in this repository is.

Reading the Norman report:

- `--with-val1` is on because of `cf_pair_interaction`: with it the val1 tier decides every row of the call (the tool
  has one deciding tier), and the OOF cell of the pair row is to be read as "not measurable at this tier", not as a
  null result. The three other rows can be read at either tier; the protocol's own call (OOF-deciding, no
  `--with-val1`) is the one to cite for them when both exist.
- The pair row can also come back `smoke: constant` on Norman. `pipeline.smoke` samples two training and two
  non-training perturbations plus the first training pair and the first non-training pair (`genemila/pipeline.py`,
  `smoke`), and the term is nonzero on a pair only when both its singles are in training; Norman has pair genes
  without a single (`docs/NORMAN_PLAN.md` probes exactly that). If neither sampled pair qualifies, the term is constant
  on the sample, the row is dropped and the `(set)` row has three features. That is a sampling artefact of the smoke
  test, not a property of the data: check the row's `reason` before reading the set row, and say so in the write-up.

## Tests

`python -m pytest -q tests/test_cellforge_c2.py` (about 7 s): guard and literal caps on every file; `python -m
genemila.pipeline smoke` for every file on the synthetic single-target bundle and on a pair bundle given synthetic
knowledge files; the directory as a `--source` of `tools/feature_compare.py` with every row `ok` on the pair bundle
and, on the single-target bundle, every row `ok` except `cf_pair_interaction`, rejected as constant; and, on the pair
bundle under gene-grouped folds, `cf_pair_interaction` zero on every predicted row of every fold and nonzero on the
view's training rows and on the full-context eval rows.
