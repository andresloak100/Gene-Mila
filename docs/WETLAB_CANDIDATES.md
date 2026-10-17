# The wet-lab candidate package (ROADMAP D13)

Andres's answer of 17 October 2026 (`docs/ROADMAP.md`, note of 02:00 UTC): a collaborating lab does the wet-lab step
given solid data and good evidence, so A.5 of `docs/GOAL_CRITERIA.md` is reachable through a collaboration. What the
lab needs is a prediction package for pre-registration, and `tools/wetlab_candidates.py` builds it. It is built now
because it uses the new-target prediction path of the fresh test (`tools/frozen_model.py predict-targets`,
`docs/PLAN_R_FRESH_TEST.md` section 6); it is used only once a feature has passed A.1 to A.4 and A.6 (`docs/ROADMAP.md`,
same note). This page lives apart from `PLAN_R` because the two protocols differ: the fresh test is commit then reveal
against a cohort a holder scores once; the package here goes to a lab that has no cohort yet and will make one.

## What the package is

Two frozen exports (`docs/FROZEN_EXPORT.md`) that share one public context: the model with the candidate feature and
the parent model without it. Both predict every admissible target through the frozen new-target path, and the package
lists where they disagree most, where they agree, what each predicts per gene, and what a readout can detect:

- **Candidates (k, default 10):** the targets with the largest disagreement. A.5 asks for perturbations in no
  dataset, so a candidate is a gene inside the frozen gene universe that is a target of no perturbation of the exports'
  context (training, validation and test alike: the bundle's `knowledge/targets.json` covers every perturbation), of
  no perturbation screen in the context's `knowledge/` (a file with a `perts` mapping, the external-screen schema),
  and of no exclusion list given (another bundle's `targets.json`, an eligibility manifest of
  `tools/replogle_slice_manifest.py`, a symbol list). A manifest given to `--exclude` excludes every target it labels,
  eligible or not: a measured target is in a dataset whatever its cell count, so the Replogle manifests (R1 and R2) are
  exclusion inputs here, never the candidate source. The candidate source is `universe` (every gene of the frozen
  universe that no protected set names; the dropped genes are counted per reason) or a plain list; a listed target
  that is protected or outside the universe is refused and nothing is written. In K562 CRISPRi the genome-wide
  Replogle library covers most expressed genes, so after exclusion few or no candidates may remain: the collaborating
  lab's cell line and modality decide, and `--system` records them in the package as part of the pre-registration.
- **Disagreement, fixed here:** S is the set of genes where either model predicts |delta| at or above `min_effect`
  (default 0.1 on the log-normalised scale of the public bundle: log1p of 10,000 times counts over the cell total, so
  a delta of 0.69 is about a two-fold change where expression is high); `l2` is the Euclidean norm of
  delta_feature minus delta_parent over S, the ranking statistic (ties by symbol); `relative` is `l2` divided by the
  norm over S of the mean of the two profiles; `pearson` is the correlation of the two full profiles over every gene.
  For each candidate the `top_n` genes (default 20) by |delta_feature minus delta_parent| are listed with both
  predicted deltas, their signs (up, down or none against `min_effect`), the gene's control mean and sd.
- **Matched negatives (m, default 10):** targets outside the k candidates where the models agree (`relative` at or
  below `agree_tolerance`, default 0.1, and at least one gene in S, so there is a shared prediction to confirm),
  matched to a candidate on three keys: the expression decile of the target gene's control mean (rank among the
  universe times ten over the number of genes, floored); the membership class of ROADMAP D7, computed inside the tool
  from the context's `knowledge/gene_sets.json` and training panel with the manifest tool's definition (member of a
  Reactome or CORUM set holding a training-panel target; unknown when the context has no `gene_sets.json`); and, when
  `--essential` names a tier-1 essentiality-proxy list (CORUM core complexes, Reactome ribosome, proteasome and
  spliceosome sets, ROADMAP D3), membership of that list. Not matched: the true fitness effect of the knockdown and
  guide efficiency. The draw is round-robin over the candidates in rank order, in ascending
  sha256(seed + newline + symbol), the manifest tool's rank key, so anyone with the seed can check it. A shortfall is
  reported, not filled. The negatives are calibration, not preference: the two models agree on them by construction.
- **Power:** with the per-gene standard deviation of the public bundle's control cells (ddof 1) and `cells` per
  condition (default 50), the minimal detectable delta per gene for a two-sample test at alpha 0.05 (two-sided) and
  power 0.8 is (z_{0.975} + z_{0.8}) sd_g sqrt(2 / n) = 2.8016 sd_g sqrt(2 / n), the normal approximation of the
  t-test with equal n and equal variance. That is detectability against control, not the power of the paired reading;
  beside it, per listed gene, the cells per condition that would detect the between-model difference,
  ceil(2 ((z_{0.975} + z_{0.8}) sd_g / |D|)^2), and in the summary how many listed genes `cells` resolves and the
  median cells needed. These are planning numbers from control-cell noise, not a guarantee: a perturbed condition can
  be noisier, cells share guide and batch, and a qPCR readout has its own scale.
- **The deposit:** `<out>/candidates.json`, `candidates.md`, and `predictions/{feature,parent}/` with each model's
  `predictions.npz`, `receipt.json` and `queries.json` from `predict_targets`. The JSON records the sha256 of every
  input (both export manifests, the candidate list when one is given, every exclusion file, the essentiality list, the
  bundle's `public.npz` and `targets.json` when given) and of both prediction files; the markdown states the sha256 of
  `candidates.json` and asks the lab to recompute the hashes first. The package holds no machine path and no
  timestamp, so the same inputs give the same bytes. An existing output directory is never overwritten, and a refused
  package leaves nothing behind.

The tool never reads an expression response of any candidate cohort: the only expression values it touches are the
public bundle's control cells, and it accepts no response file (no h5ad, no cohort means; the candidate source may
only be `universe`, a `.json` list or a `.txt` list). Nothing in it scores a model.

## Protocol

1. The feature has passed A.1 to A.4 and A.6; its frozen export and its parent's are the ones scored in the fresh
   test, named by their manifest sha256. The cell line and modality the lab will use are fixed in writing and given
   as `--system`; the exclusion inputs are every development bundle's `targets.json` and every Replogle manifest.
2. The seed is a public value fixed in writing before the run (as in `PLAN_R` section 3), and so are `min_effect`,
   `agree_tolerance`, `cells`, k, m and `top_n`.
3. The package is built once; it is pre-registered when its `candidates.json` sha256 is posted on #41 (that post's
   date and link are the record), and the archive goes to the lab after that post. The lab recomputes the hashes
   before reading further. Nothing is rebuilt after the lab has it; a second package is a second pre-registration.
4. The lab measures the candidates and the negatives at the stated cells per condition or more and reports, per
   listed gene, the measured delta: its perturbed mean minus its own control mean on the same log-normalised scale.
   The reading, fixed now and carried in `candidates.json` under `rules.reading`: per candidate, over its listed
   genes, the paired differences |measured minus delta_parent| minus |measured minus delta_feature|; the candidate
   confirms the feature when their mean is positive by a one-sided paired t-test (the sign test when fewer than ten
   genes are listed), Holm-corrected over the k candidates at 0.05; nothing outside the posted candidates is tested.
   A negative passes calibration when, on each listed gene whose shared prediction is at or above the gene's minimal
   detectable delta, the measured delta has the predicted sign and lies within one minimal detectable delta of it.
   The numbers decide; the package carries the predictions, not the verdict.

## Command

    python tools/wetlab_candidates.py --feature <export with feature> --feature-manifest-sha256 <hex> \
        --parent <parent export> --parent-manifest-sha256 <hex> --candidates universe \
        --bundle data/adamson_cf_clean --exclude norman=data/norman_clean/knowledge/targets.json \
        --exclude replogle_r2=<manifest.json> --system 'K562 CRISPRi' \
        --seed '<public value>' --cells 50 --out <new directory>

`--bundle` is optional: the exports' own context is the public bundle they were fitted on and is always used; when
given, the bundle's genes and control cells must equal that context (else refused) and its targets join the
protected set. Tests: `tests/test_wetlab_candidates.py` (two tiny frozen exports from a synthetic bundle that differ on
one target's pathway genes; that target ranks first, bundle, screen and manifest targets are refused, the `universe`
source drops them, negatives are drawn where the models agree on the three matching keys, the power numbers match a
hand computation, the bundle check holds, the hashes reproduce).
