# CellForge ideas, translated by us (arm A5-C2)

Four feature plugins written by us from design ideas in CellForge's published code and model cards
(gersteinlab/CellForge, commit `6585ff9`, read locally; arXiv 2508.02276). They are the C2 tier of arm A5 in
[`docs/FEATURE_COMPARISON_PROTOCOL.md`](../../FEATURE_COMPARISON_PROTOCOL.md): CellForge itself produces a deep model
and a training script, never features, and ships no weights, so there is nothing of CellForge's to score at the feature
level. **Every file here is our translation of an idea into a feature f(p, g) of a fixed linear model. Nothing in it is
CellForge's output, and no CellForge code ran.** Rows from this directory are labelled "CellForge ideas, translated by
us" in every table, never "CellForge". Nothing here has run on real data yet.

Each plugin is written against `genemila/features/api.py`, passes `genemila.guard.check_plugin_source` and the literal
caps of `tools/task_package/literal.py`, reads training labels only through `ctx.train_delta(exclude=p)`, uses every
target of a pair in a fixed order, and is deterministic (no `hash()`/`id()`). All four together take a few seconds on
2,000 genes x 120 perturbations. Feature names are prefixed `cf_`; the file `<name>.py` registers feature `<name>`.

## Provenance

| file | CellForge idea | where CellForge says it | inputs the plugin reads |
|---|---|---|---|
| `cf_grn_propagation.py` | totalGAT: graph attention over a gene interaction network, "so the perturbation effect propagates along known biology rather than through a dense layer"; gene regulatory networks as a model constraint | `docs/MODELS.md:108-109`; `cellforge/Method_Design/experts.py:583`, `:696`; `cellforge/Method_Design/refinement.py:941` | `targets`, `prior_network` (CollecTRI, signed; `ppi_network` unsigned when absent). No label. |
| `cf_pathway_transfer.py` | pathway constraints in the plan template; a pathway proposal over KEGG, Reactome, GO and MSigDB; the "Pathway modularity" assumption | `cellforge/Method_Design/graph_discussion.py:865-869`, `:882-895`; `cellforge/Method_Design/refinement.py:302-306` | `targets`, `gene_sets`, `train_delta` (leave-one-out) |
| `cf_latent_offset.py` | CPA-X: a disentangled perturbation embedding in a latent space "explicitly factorised: perturbation effect on one axis", perturbations as additive latent offsets; a gene embedding from ontology and pathway information | `docs/MODELS.md:17`, `:31-40`; `cellforge/Method_Design/graph_discussion.py:874`; `cellforge/Method_Design/refinement.py:1022` | `targets`, `ppi_network` (`prior_network` undirected when absent), `train_delta` (leave-one-out) |
| `cf_pair_interaction.py` | scGen-X for Norman: latent arithmetic plus "an explicit interaction term for gene pairs, so the model can represent synergy and antagonism rather than being forced into additivity"; the template's element-wise multiplication | `docs/MODELS.md:18`, `:54-56`; `cellforge/Method_Design/graph_discussion.py:875` | `targets`, `train_delta` (leave-one-out). Two columns: product of the singles' changes, sign-aware minimum. |

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

Where a knowledge file is missing the plugin falls back as the table says, or returns zeros; it never fails.

## Scoring (on the Mac, where the data is; free; `nice -n 19`)

Add this directory as one more `--source` of the comparison call the protocol gives (section "Scoring every arm"), so
every arm shares one parent scoring; or alone:

```
nice -n 19 python tools/feature_compare.py --data data/norman --out $HOME/gm_compare/norman_cf_c2 \
  --parent builtin --source cf_c2=docs/comparison/cellforge_c2 --fold-seeds 101,102,103 --null-reps 499
nice -n 19 python tools/feature_compare.py --data data/adamson_cf --out $HOME/gm_compare/adamson_cf_c2 \
  --parent builtin --source cf_c2=docs/comparison/cellforge_c2 --fold-seeds 101,102,103 --null-reps 499
```

The source's add-one family has four rows, so the null needs `--null-reps` >= 79 before any row can pass Holm; 499 is
the protocol's default. Add `--with-val1` for the visible-validation tier. A `--source` file is scored with its own
class params only (the tool reads no params file next to it). The report is `feature_compare.md` and
`feature_compare.json` in `--out`; cite them with the run directory, as every number in this repository is.

## Tests

`python -m pytest -q tests/test_cellforge_c2.py` (about 6 s): guard and literal caps on every file; `python -m
genemila.pipeline smoke` for every file on the synthetic single-target bundle and on a pair bundle given synthetic
knowledge files; the directory as a `--source` of `tools/feature_compare.py` with every row `ok` on the pair bundle
and, on the single-target bundle, every row `ok` except `cf_pair_interaction`, rejected as constant.
