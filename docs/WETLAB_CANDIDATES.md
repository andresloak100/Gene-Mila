# The wet-lab candidate package (ROADMAP D13)

Andres's answer of 17 October 2026 (`docs/ROADMAP.md`, note of 02:00 UTC): a collaborating lab does the wet-lab step
given solid data and good evidence, so A.5 of `docs/GOAL_CRITERIA.md` is reachable through a collaboration. What the
lab needs is a pre-registered prediction package, and `tools/wetlab_candidates.py` builds it. It is built now because
it uses the new-target prediction path of the fresh test (`tools/frozen_model.py predict-targets`,
`docs/PLAN_R_FRESH_TEST.md` section 6); it is used only once a feature has passed A.1 to A.4 and A.6 (`docs/ROADMAP.md`,
same note). This page lives apart from `PLAN_R` because the two protocols differ: the fresh test is commit then reveal
against a cohort a holder scores once; the package here goes to a lab that has no cohort yet and will make one.

## What the package is

Two frozen exports (`docs/FROZEN_EXPORT.md`) that share one public context: the model with the candidate feature and
the parent model without it. Both predict every admissible target through the frozen new-target path, and the package
lists where they disagree most, where they agree, what each predicts per gene, and what a readout can detect:

- **Candidates (k, default 10):** the targets with the largest disagreement. A candidate is a gene inside the frozen
  gene universe that is a target of no perturbation of the bundles the models saw (training, validation and test
  alike: the bundle's `knowledge/targets.json` covers every perturbation), of no exclusion list given (another bundle's
  `targets.json`, a manifest of `tools/replogle_slice_manifest.py`, a symbol list) and not among a manifest's excluded
  symbols. Any other target is refused and nothing is written.
- **Disagreement, fixed here:** S is the set of genes where either model predicts |delta| at or above `min_effect`
  (default 0.1 on the log-normalised scale of the public bundle); `l2` is the Euclidean norm of
  delta_feature minus delta_parent over S, the ranking statistic (ties by symbol); `relative` is `l2` divided by the
  norm over S of the mean of the two profiles; `pearson` is the correlation of the two full profiles over every gene.
  For each candidate the `top_n` genes (default 20) by |delta_feature minus delta_parent| are listed with both
  predicted deltas and their signs (up, down or none against `min_effect`).
- **Matched negatives (m, default 10):** targets outside the k candidates where the models agree (`relative` at or
  below `agree_tolerance`, default 0.1, and at least one gene in S, so there is a shared prediction to confirm),
  matched to a candidate on the expression decile of the target gene's control mean (rank among the universe times
  ten over the number of genes, floored) and on the membership class (`in_distribution` of the manifest; unknown for a
  plain list). The draw is round-robin over the candidates in rank order, in ascending sha256(seed + newline + symbol),
  the manifest tool's rank key, so anyone with the seed can check it. A shortfall is reported, not filled.
- **Power:** with the per-gene standard deviation of the public bundle's control cells (ddof 1) and `cells` per
  condition (default 50), the minimal detectable delta per gene for a two-sample test at alpha 0.05 (two-sided) and
  power 0.8 is (z_{0.975} + z_{0.8}) sd_g sqrt(2 / n) = 2.8016 sd_g sqrt(2 / n), the normal approximation of the
  t-test with equal n and equal variance; beside it, the cells per condition that would detect the between-model
  difference on each listed gene, ceil(2 ((z_{0.975} + z_{0.8}) sd_g / |D|)^2). These are planning numbers from
  control-cell noise, not a guarantee: a perturbed condition can be noisier, cells share guide and batch, and a qPCR
  readout has its own scale.
- **The deposit:** `<out>/candidates.json`, `candidates.md`, and `predictions/{feature,parent}/` with each model's
  `predictions.npz`, `receipt.json` and `queries.json` from `predict_targets`. The JSON records the sha256 of every
  input (both export manifests, the candidate source, every exclusion file, the bundle's `public.npz` and
  `targets.json` when given) and of both prediction files; the markdown states the sha256 of `candidates.json`. The
  package holds no machine path and no timestamp, so the same inputs give the same bytes. An existing output directory
  is never overwritten.

The tool never reads an expression response of any candidate cohort: the only expression values it touches are the
public bundle's control cells, and it accepts no response file (no h5ad, no cohort means; the candidate list may only
be a manifest, a `.json` list or a `.txt` list). Nothing in it scores a model.

## Protocol

1. The feature has passed A.1 to A.4 and A.6; its frozen export and its parent's are the ones scored in the fresh
   test, named by their manifest sha256.
2. The seed is a public value fixed in writing before the run (as in `PLAN_R` section 3).
3. The package is built once, its `candidates.json` sha256 posted on #41, and the archive goes to the lab after that
   post. Nothing is rebuilt after the lab has it; a second package is a second pre-registration.
4. The lab measures the candidates and the negatives at the stated cells per condition or more. The reading, fixed
   now: a candidate confirms the feature when the measured delta on its listed genes sits closer to the
   feature model's prediction than to the parent's (paired over the listed genes, sign and magnitude), and the
   negatives show no such preference. The numbers decide; the package carries the predictions, not the verdict.

## Command

    python tools/wetlab_candidates.py --feature <export with feature> --feature-manifest-sha256 <hex> \
        --parent <parent export> --parent-manifest-sha256 <hex> --candidates <manifest.json or list> \
        --bundle data/adamson_cf_clean --exclude norman=data/norman_clean/knowledge/targets.json \
        --seed '<public value>' --cells 50 --out <new directory>

`--bundle` is optional: the exports' own context is the public bundle they were fitted on and is always used; when
given, the bundle's genes and control cells must equal that context (else refused) and its targets join the
protected set. Tests: `tests/test_wetlab_candidates.py` (two tiny frozen exports from a synthetic bundle that differ on
one target's pathway genes; that target ranks first, a bundle target is refused, negatives are drawn where the models
agree, the power numbers match a hand computation, the hashes reproduce).
