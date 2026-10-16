# Reading 4 addendum: fitted promoter-CpG coefficient signs

Andres requested this after the original readings were published in commit 7e02a4f / draft PR #46. The values below are extracted from existing fitted artifacts, without refitting, scoring or changing any model. The original primary and sealed readings remain unchanged.

## Existing feature-creation fits

| Run directory | Feature / experiment | Ridge alpha | Exact saved coefficient | Sign |
|---|---|---:|---:|---|
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0` | `additive_times_target_promoter_cpg_e428` / EXP_0428 | 100 | +0.014724067753942987 | positive |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0` | `additive_times_target_promoter_cpg_e666` / EXP_0666 | 100 | +0.01434165272419911 | positive |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3` | `additive_response_x_target_promoter_cpg_e412` / EXP_0412 | 100 | -0.0099610544698675099 | negative |

The signs are **positive, positive, negative**, respectively. They do not uniformly agree with the proposed negative-coefficient mechanism. These are coefficients conditional on each experiment’s other model columns, not an independent test of CRISPRa efficiency or a causal effect of CpG content.

## Presence in the already selected final models

| Run directory | Selected experiment | Feature | Coefficient |
|---|---|---|---|
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0` | EXP_0715 | `additive_times_target_promoter_cpg_e428` | absent from model (not a fitted zero) |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0` | EXP_0715 | `additive_times_target_promoter_cpg_e666` | +0.019034352796861696 (positive; alpha 100) |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3` | EXP_0603 | `additive_response_x_target_promoter_cpg_e412` | absent from model (not a fitted zero) |

## Provenance and interpretation

- `genemila/pipeline.py::run` fits one shared linear model to the full training perturbation × output-gene design, standardising each column by its training mean and positive standard deviation. Coefficients are in delta-expression units per training-column SD; positive rescaling does not change their sign.
- The alpha is the experiment’s original saved `best_alpha`, chosen by the original visible rule. This addendum makes no new alpha/model choice.
- Each coefficient comes from `artifacts/EXP_*/result.json`, checked against the database’s five-decimal diagnostic coefficient. The JSON twin records full artifact paths/SHA256, exact coefficients, alphas and all model columns. Databases use the existing read-only snapshot helper. No private label, sealed score, prediction artifact, summary.md or run-log end was read.
- The column is signed additive response × target CpG, not CpG alone. A positive coefficient multiplying a negative additive response can lower predicted expression; its sign is not a standalone CpG-to-expression effect.
- These search-model fits have different feature sets, including correlated response terms. The primary tool’s common-parent add-one coefficient is not saved; it must not be substituted with or inferred from these coefficients. No post-hoc refit was performed.
- The three primary CpG rows had identical prediction/null reports under the fixed common-parent test; that does not make their original multifeature-fit coefficients identical or independent replications.
- No mechanism confirmation, model promotion or follow-on run follows from this addendum.

Reproduction: read `experiment_id, model_type, best_alpha, artifact_dir, diagnostics_json` for the named completed feature-creation experiments (and the pre-existing selected EXP_0715/EXP_0603) through `tools/feature_audit.py::open_db_readonly`; in each artifact’s `result.json`, select the existing coefficient record whose alpha equals saved `best_alpha`, then look up the exact feature column. Do not refit or query labels.
