"""Norman-style bundles in the lab (docs/NORMAN_PLAN.md section 4, items 5 to 7): the additive baseline and its
out-of-fold twin, per-category and target-free scores on the visible and sealed sets with a paired sealed query that
returns aggregates only and counts as two queries, and gene-grouped cross-validation folds that hide every training
perturbation sharing a gene with a perturbation they predict. A single-target bundle without a gene split or a
modality (Adamson's kind; the session's synthetic dataset) keeps its folds, hyperparameters, configuration hashes,
baselines and scores exactly as before."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from genemila.benchmark.evaluator import CATEGORY_MIN_N, bundle_strata, categories_of, category_summary, evaluate, \
    hidden_categories, paired_summary
from genemila.benchmark.oracle import QueryBudgetExceeded, QueryOracle
from genemila.data.bundle import LabelSet, export_public, make_gene_splits, split_id_for, write_bundle
from genemila.features.api import FeatureContext
from genemila.pipeline import cv_folds_of, run
from genemila.spec import ExperimentSpec, config_hash

OLD_METRICS = {"rmse", "mae", "mse", "pearson_delta", "pearson_delta_top", "direction_acc_top", "mse_top", "r2_top",
               "pearson_expr", "primary", "selection_rule"}


def _old_folds(train, k, seed):
    """cv_folds_of as it was before gene grouping (random folds over names, each fold its own hidden set)."""
    order = list(np.random.default_rng(seed).permutation(sorted(train)))
    return [sorted(order[i::k]) for i in range(k)]


def make_pair_bundle(out: Path, seed: int = 0, gene_split: bool = True) -> Path:
    """A small additive two-gene screen: 24 genes with a single each, 44 random pairs whose change is the sum of
    their singles' plus a little interaction, keys sorted and joined with '+'. With gene_split the split is
    gene-grouped as section 3 of the plan deals it (60/20/20 of the genes, a pair in the more held-out set of its
    genes, a seeded share of the both-genes-trained pairs held out), with categories; else a random name split."""
    rng = np.random.default_rng(seed)
    n_genes = 80
    genes = [f"G{i:02d}" for i in range(n_genes)]
    base = rng.uniform(0.5, 3.0, n_genes)
    single_genes = genes[:24]
    effect = {}
    for i, g in enumerate(single_genes):
        d = np.zeros(n_genes)
        d[i] = 1.5 * rng.choice([-1, 1])  # the target itself (CRISPRa: up)
        hit = rng.choice(np.arange(24, n_genes), size=12, replace=False)
        d[hit] = rng.normal(0, 0.6, size=12)
        effect[g] = d
    targets = {g: [g] for g in single_genes}
    means = {g: base + effect[g] + rng.normal(0, 0.03, n_genes) for g in single_genes}
    while len(targets) < 24 + 44:
        a, b = sorted(rng.choice(single_genes, size=2, replace=False))
        key = f"{a}+{b}"
        if key in targets:
            continue
        targets[key] = [a, b]
        means[key] = base + effect[a] + effect[b] + rng.normal(0, 0.15, n_genes)
    control = np.maximum(base + rng.normal(0, 0.3, size=(300, n_genes)), 0)
    perts = sorted(targets)
    if gene_split:
        order = [str(g) for g in rng.permutation(sorted(single_genes))]
        gene_set = {g: ("train" if i < 14 else "val1" if i < 19 else "val2") for i, g in enumerate(order)}
        rank = ("train", "val1", "val2")
        part = {p: max((gene_set[g] for g in targets[p]), key=rank.index) for p in perts}
        seen2 = [p for p in perts if len(targets[p]) == 2 and part[p] == "train"]
        held = [str(p) for p in rng.permutation(seen2)][:6]
        for i, p in enumerate(held):
            part[p] = "val1" if i < 3 else "val2"
        splits = {s: sorted(p for p in perts if part[p] == s) for s in rank}
        splits.update(seed=seed, mode="gene", gene_frac=[0.6, 0.2, 0.2], seen2_holdout=0.2,
                      gene_sets=dict(sorted(gene_set.items())),
                      categories=categories_of(splits["val1"] + splits["val2"], targets, splits["train"]))
    else:
        order = [str(p) for p in rng.permutation(perts)]
        splits = {"train": sorted(order[:40]), "val1": sorted(order[40:54]), "val2": sorted(order[54:]), "seed": seed}
    splits["split_id"] = split_id_for(splits)
    return write_bundle(out, "norman_toy", genes, control, means, {p: 50 for p in perts}, targets, splits,
                        extra_meta={"modality": "CRISPRa"})


@pytest.fixture(scope="module")
def pair_bundle(tmp_path_factory):
    return make_pair_bundle(tmp_path_factory.mktemp("norman") / "norman_toy")


@pytest.fixture
def pair_lab(tmp_path, pair_bundle, code_repo):
    from conftest import make_cfg
    from genemila.lab import Lab
    made = []

    def factory(**over):
        cfg = make_cfg(tmp_path, **over)
        cfg["run"]["data_dir"] = str(pair_bundle)
        lab = Lab(cfg, tmp_path / f"run{len(made)}", pair_bundle, repo=code_repo)
        made.append(lab)
        return lab
    yield factory
    for lab in made:
        lab.stop_event.set()
        lab.kill_event.set()
        lab.close()


def _ridge_spec(text="ridge on the built-in features"):
    return ExperimentSpec(hypothesis=text, scientific_rationale="a reference model on the built-in features",
                          feature_set=["control_mean", "mean_response", "is_target"],
                          hyperparameters={"alpha_grid": [1.0, 100.0]})


# ------------------------------------------------------------------ item 7: folds
def test_gene_grouped_folds_hide_every_perturbation_sharing_a_gene(pair_bundle, tmp_path):
    ctx = FeatureContext(export_public(pair_bundle, tmp_path / "pub"))
    train = ctx.train_perts
    targets = {p: ctx.target_genes(p) for p in train}
    assert any(len(v) > 1 for v in targets.values())
    for k, seed in ((5, 0), (3, 1)):
        folds = cv_folds_of(train, k, seed, targets)
        assert cv_folds_of(train, k, seed, targets) == folds  # deterministic
        predicted = [p for fold, _ in folds for p in fold]
        assert sorted(predicted) == sorted(train)  # every training perturbation predicted exactly once
        for i, (fold, hide) in enumerate(folds):
            assert set(fold) <= set(hide)
            view = [p for p in train if p not in set(hide)]
            for p in fold:
                if len(targets[p]) == 1:  # no view holds a perturbation sharing a gene with a single it predicts
                    assert not any(targets[p][0] in targets[q] for q in view), (p, i)
        # a perturbation is hidden from the folds of its genes and predicted in the lowest of them
        for p in train:
            hidden_in = [i for i, (_, h) in enumerate(folds) if p in h]
            predicted_in = [i for i, (f, _) in enumerate(folds) if p in f]
            assert predicted_in == [min(hidden_in)] and 1 <= len(hidden_in) <= len(targets[p])
    assert cv_folds_of(train, 5, 0, targets) != cv_folds_of(train, 5, 1, targets)
    # a predicted single's gene is out of its view altogether: every training perturbation naming it is hidden
    folds = cv_folds_of(train, 5, 0, targets)
    for fold, hide in folds:
        for p in fold:
            if len(targets[p]) == 1:
                assert {q for q in train if targets[p][0] in targets[q]} <= set(hide)
    # without targets, the folds are the old random folds over names, each hiding itself
    assert cv_folds_of(train, 5, 0) == [(f, f) for f in _old_folds(train, 5, 0)]


def test_cross_validate_hides_each_fold_s_hidden_set(pair_bundle, tmp_path, monkeypatch):
    pub = export_public(pair_bundle, tmp_path / "pub")
    seen = []
    orig = FeatureContext.without_train

    def spy(self, exclude):
        seen.append(sorted(exclude))
        return orig(self, exclude)
    monkeypatch.setattr(FeatureContext, "without_train", spy)
    spec = {"experiment_id": "EXP_g", "feature_set": ["control_mean", "mean_response", "is_target"],
            "feature_params": {}, "model_type": "ridge",
            "hyperparameters": {"alpha_grid": [1.0], "cv_folds": 3, "cv_seed": 0, "cv_groups": "gene"}, "seed": 0}
    res = run(spec, pub, tmp_path / "plugins", tmp_path / "out")
    ctx = FeatureContext(pub)
    folds = cv_folds_of(ctx.train_perts, 3, 0, {p: ctx.target_genes(p) for p in ctx.train_perts})
    assert seen == [hide for _, hide in folds] and any(sorted(f) != h for f, h in folds)
    assert res["cv_groups"] == "gene"
    z = np.load(tmp_path / "out" / "cv.npz")
    assert [str(p) for p in z["perts"]] == ctx.train_perts and np.all(np.isfinite(z["delta"]))
    with pytest.raises(ValueError, match="cv_groups"):
        run({**spec, "hyperparameters": {**spec["hyperparameters"], "cv_groups": "label"}}, pub,
            tmp_path / "plugins", tmp_path / "out2")


# ------------------------------------------------------------------ Adamson-style bundles are untouched
def test_single_target_bundle_keeps_folds_hashes_baselines_and_scores(lab_factory, dataset):
    lab = lab_factory(experiment__cv_folds=3)
    assert bundle_strata(dataset) is None and lab._strata is None
    assert lab.cv_groups is None and not lab.has_pairs and not lab._cv_categories
    train = lab._train.perts
    assert lab._cv_folds() == [(f, f) for f in _old_folds(train, 3, lab.cv_seed)]
    # hyperparameters and the configuration hash as before: cv_folds and cv_seed only
    spec = _ridge_spec()
    old_hash = config_hash(replace(spec, hyperparameters={**spec.hyperparameters, "cv_folds": 3,
                                                          "cv_seed": lab.cv_seed}),
                           lab.feature_code_hashes(), lab.split_id)
    assert lab.config_hash_for(spec) == old_hash
    eid, status = lab.queue(spec)
    rec = lab.db.get_experiment(eid)
    assert status == "queued" and rec["hyperparameters_json"] == {"alpha_grid": [1.0, 100.0], "cv_folds": 3,
                                                                   "cv_seed": lab.cv_seed}
    assert rec["config_hash"] == old_hash
    # two analytic baselines, scored as before (the mean-response out-of-fold twin on the old folds)
    lab.record_analytic_baselines()
    groups = [r["hypothesis_group"] for r in lab.db.query("SELECT hypothesis_group FROM experiments "
                                                          "WHERE model_type='none' ORDER BY experiment_id")]
    assert groups == ["baseline_unchanged", "baseline_mean_response"]
    delta = lab._train.means - lab.control_mean
    old = np.tile(lab.control_mean, (len(train), 1))
    pos = {p: i for i, p in enumerate(train)}
    for fold in _old_folds(train, 3, lab.cv_seed):
        rows = [pos[p] for p in fold]
        old[rows] += delta[np.setdiff1d(np.arange(len(train)), rows)].mean(axis=0)
    assert np.array_equal(lab._cv_baseline("baseline_mean_response"), old)
    m = lab.db.query("SELECT val_metrics_json FROM experiments WHERE "
                     "hypothesis_group='baseline_mean_response'")[0]["val_metrics_json"]
    assert not {k for k in m if "category" in k or "nontarget" in k or k == "cv_groups"}
    # the pipeline gets no grouping and writes no cv_groups; visible and sealed scores carry no new key
    out = lab.artifacts / eid
    res = run(ExperimentSpec.from_record(rec).run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
    assert "cv_groups" not in res
    ev = lab.evaluate_artifact(out / "predictions.npz")
    assert not {k for k in ev["metrics"] if "category" in k or "nontarget" in k or k == "cv_groups"}
    q = lab.query_only(lab.best_baseline()["experiment_id"])["metrics"]
    assert OLD_METRICS <= set(q) and not {k for k in q if "category" in k or "nontarget" in k}
    # evaluate without the extras is the old evaluator, key for key
    r = evaluate(lab._val1.means, lab._val1.means, lab.control_mean, lab._val1.perts)
    assert set(r["metrics"]) == OLD_METRICS and "by_category" not in r["metrics"]


# ------------------------------------------------------------------ item 5: additive baseline
def test_additive_baseline_adds_the_training_singles(pair_lab, pair_bundle):
    lab = pair_lab(experiment__cv_folds=3)
    assert lab.has_pairs and lab.cv_groups == "gene"
    splits = json.loads((pair_bundle / "splits.json").read_text())
    cats, targets = splits["categories"], lab._targets
    train = lab._train.perts
    pos = {p: i for i, p in enumerate(train)}
    single_of = {targets[p][0]: p for p in train if len(targets[p]) == 1}
    singles = [pos[p] for p in single_of.values()]
    mean_single = (lab._train.means[singles] - lab.control_mean).mean(axis=0)

    def d(g):
        return lab._train.means[pos[single_of[g]]] - lab.control_mean
    held = splits["val1"] + splits["val2"]
    seen2 = [p for p in held if cats[p] == "pair_seen2"]
    seen1 = [p for p in held if cats[p] == "pair_seen1"]
    lone = [p for p in held if cats[p] == "single"]
    assert seen2 and seen1 and lone
    a, b = targets[seen2[0]]
    got = lab._analytic_baseline("baseline_additive", [seen2[0]])[0]
    assert np.allclose(got, lab.control_mean + d(a) + d(b), rtol=0, atol=1e-12)  # A, B trained: control + ΔA + ΔB
    known = next(g for g in targets[seen1[0]] if g in single_of)
    got = lab._analytic_baseline("baseline_additive", [seen1[0]])[0]
    assert np.allclose(got, lab.control_mean + d(known) + mean_single, rtol=0, atol=1e-12)
    got = lab._analytic_baseline("baseline_additive", [lone[0]])[0]
    assert np.allclose(got, lab.control_mean + mean_single, rtol=0, atol=1e-12)
    # recorded beside the other analytic baselines, scored by category on the visible perturbations
    lab.record_analytic_baselines()
    rec = lab.db.query("SELECT * FROM experiments WHERE hypothesis_group='baseline_additive'")[0]
    m = rec["val_metrics_json"]
    assert {"by_category", "by_category_cv", "by_category_visible", "pearson_delta_nontarget",
            "pearson_delta_nontarget_cv"} <= set(m) and m["cv_groups"] == "gene"
    # its out-of-fold twin predicts each fold from the singles the fold's view keeps
    oof = lab._cv_baseline("baseline_additive")
    for fold, hide in lab._cv_folds():
        kept = [p for p in train if p not in set(hide)]
        kept_single = {targets[p][0]: p for p in kept if len(targets[p]) == 1}
        fill = np.mean([lab._train.means[pos[p]] - lab.control_mean for p in kept_single.values()], axis=0)
        for p in fold:
            want = lab.control_mean + sum((lab._train.means[pos[kept_single[g]]] - lab.control_mean)
                                          if g in kept_single else fill for g in targets[p])
            assert np.allclose(oof[pos[p]], want, rtol=0, atol=1e-10), p
        for p in fold:  # a predicted single's own single is never in its view
            if len(targets[p]) == 1:
                assert targets[p][0] not in kept_single
    # on this additive screen it beats the mean response on the pairs it can build from two trained singles
    base = {r["hypothesis_group"]: r["val_metrics_json"] for r in
            lab.db.query("SELECT hypothesis_group, val_metrics_json FROM experiments WHERE model_type='none'")}
    assert set(base) == {"baseline_unchanged", "baseline_mean_response", "baseline_additive"}
    assert base["baseline_additive"]["primary"] > base["baseline_mean_response"]["primary"]


# ------------------------------------------------------------------ item 6: categories and paired scores
def _walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk(v)
    else:
        yield obj


def test_sealed_categories_match_per_perturbation_and_nothing_per_perturbation_leaves(pair_lab, pair_bundle):
    lab = pair_lab()
    oracle = QueryOracle(pair_bundle, max_queries=5)
    labels = LabelSet.load(pair_bundle / "private" / "val2.npz")
    strata = bundle_strata(pair_bundle)
    perts = oracle.perts
    add = lab._analytic_baseline("baseline_additive", perts)
    mean = lab._analytic_baseline("baseline_mean_response", perts)
    q = oracle.query("additive", add, perts, lab.control_mean)
    direct = evaluate(add, labels.means, lab.control_mean, labels.perts, targets=strata["target_idx"])
    per = direct["per_perturbation"]
    by_cat = q["metrics"]["by_category"]
    cats = strata["categories"]
    assert sum(c["n"] for c in by_cat.values()) == len(labels.perts)
    hidden = hidden_categories({c: e["n"] for c, e in by_cat.items()})
    assert {c for c, e in by_cat.items() if e["n"] < CATEGORY_MIN_N} <= hidden
    assert not hidden or sum(by_cat[c]["n"] for c in hidden) >= CATEGORY_MIN_N
    for cat, entry in by_cat.items():
        members = [p for p in labels.perts if cats[p] == cat]
        assert entry["n"] == len(members)
        if cat in hidden:
            assert set(entry) == {"n"}  # too few to hide its members' values, alone or with the pooled mean
            continue
        for metric in ("pearson_delta", "pearson_delta_nontarget", "r2_top"):
            v = np.array([per[p][metric] for p in members])
            assert entry[metric]["mean"] == pytest.approx(v.mean(), abs=1e-12)
            assert entry[metric]["sd"] == pytest.approx(v.std(ddof=1), abs=1e-12)
    # pearson_delta_nontarget leaves out exactly the perturbation's own target columns
    p0 = next(p for p in labels.perts if "+" in p)
    i0 = labels.perts.index(p0)
    keep = np.ones(len(lab.control_mean), dtype=bool)
    keep[strata["target_idx"][p0]] = False
    want = np.corrcoef((add[i0] - lab.control_mean)[keep], (labels.means[i0] - lab.control_mean)[keep])[0, 1]
    assert per[p0]["pearson_delta_nontarget"] == pytest.approx(want, abs=1e-10)
    assert q["metrics"]["pearson_delta_nontarget"] == pytest.approx(
        np.mean([per[p]["pearson_delta_nontarget"] for p in labels.perts]), abs=1e-12)
    assert q["metrics"]["primary"] == pytest.approx(q["metrics"]["pearson_delta"])  # selection unchanged
    # a paired query: aggregates of a - b, and it counts as two queries
    assert oracle.used == 1
    pq = oracle.query_paired("additive", add, perts, "mean", mean[::-1], perts[::-1], lab.control_mean)
    assert oracle.used == 3
    diff = np.array([per[p]["pearson_delta"] for p in labels.perts]) - np.array(
        [evaluate(mean, labels.means, lab.control_mean, labels.perts)["per_perturbation"][p]["pearson_delta"]
         for p in labels.perts])
    pooled = pq["paired"]
    assert pooled["n"] == len(diff) and pooled["mean_diff"] == pytest.approx(diff.mean(), abs=1e-12)
    assert pooled["se"] == pytest.approx(diff.std(ddof=1) / np.sqrt(len(diff)), abs=1e-12)
    assert pooled["wins_a"] == int((diff > 0).sum()) and pooled["wins_b"] == int((diff < 0).sum())
    want = "a" if diff.mean() > 2 * pooled["se"] and (diff > 0).sum() > len(diff) / 2 else \
        "b" if -diff.mean() > 2 * pooled["se"] and (diff < 0).sum() > len(diff) / 2 else "none"
    assert pooled["verdict"] == want
    for cat, entry in pooled["by_category"].items():
        d = diff[[i for i, p in enumerate(labels.perts) if cats[p] == cat]]
        assert entry["n"] == len(d)
        if cat in hidden:
            assert set(entry) == {"n"}
        else:
            assert entry["mean_diff"] == pytest.approx(d.mean(), abs=1e-12)
    # nothing of a single perturbation leaves the oracle: no name, no per-perturbation value, in either answer
    per_mean = evaluate(mean, labels.means, lab.control_mean, labels.perts,
                        targets=strata["target_idx"])["per_perturbation"]
    values = [v[m] for d in (per, per_mean) for v in d.values() for m in ("pearson_delta", "pearson_delta_nontarget")]
    values += list(diff)
    for answer in (q, pq):
        for item in _walk(answer):
            assert not (isinstance(item, str) and item in set(labels.perts)), item
            if isinstance(item, float):
                assert not any(abs(item - v) < 1e-12 for v in values), item
    # the five-query cap keeps its meaning: a paired query needs two of what is left
    oracle.query("again", add, perts, lab.control_mean)
    assert oracle.used == 4
    with pytest.raises(QueryBudgetExceeded, match="two"):
        oracle.query_paired("a", add, perts, "b", mean, perts, lab.control_mean)
    oracle.query("last", add, perts, lab.control_mean)
    with pytest.raises(QueryBudgetExceeded):
        oracle.query("over", add, perts, lab.control_mean)


def test_lab_scores_pairs_by_category_end_to_end(pair_lab):
    lab = pair_lab(experiment__cv_folds=3)
    lab.record_analytic_baselines()
    spec = _ridge_spec()
    random_hash = config_hash(replace(spec, hyperparameters={**spec.hyperparameters, "cv_folds": 3,
                                                             "cv_seed": lab.cv_seed}),
                              lab.feature_code_hashes(), lab.split_id)
    assert lab.config_hash_for(spec) != random_hash  # the hash follows the fold grouping
    eid, status = lab.queue(spec)
    rec = lab.db.get_experiment(eid)
    assert status == "queued" and rec["hyperparameters_json"]["cv_groups"] == "gene"
    out = lab.artifacts / eid
    res = run(ExperimentSpec.from_record(rec).run_spec(), lab.public_dir, lab.run_dir / "plugins", out)
    assert res["cv_groups"] == "gene"
    ev = lab.evaluate_artifact(out / "predictions.npz")
    m = ev["metrics"]
    n1, nt = len(lab._val1.perts), len(lab._train.perts)
    assert m["primary"] == pytest.approx((n1 * m["pearson_delta"] + nt * m["pearson_delta_cv"]) / (n1 + nt))
    assert sum(c["n"] for c in m["by_category"].values()) == n1
    assert sum(c["n"] for c in m["by_category_cv"].values()) == nt
    assert {c: e["n"] for c, e in m["by_category_visible"].items()} == {
        c: m["by_category"].get(c, {"n": 0})["n"] + m["by_category_cv"].get(c, {"n": 0})["n"]
        for c in set(m["by_category"]) | set(m["by_category_cv"])}
    # out of fold, no pair is predicted with both its singles in view (the folds deal genes, not names)
    assert "pair_seen2" not in m["by_category_cv"] and "single" in m["by_category_cv"]
    lab.db.update_experiment(eid, status="completed", primary_score=m["primary"], best_alpha=ev["best_alpha"],
                             artifact_dir=str(out), val_metrics_json=m)
    # the visible paired comparison against the additive baseline, by category
    add = lab.db.query("SELECT experiment_id FROM experiments WHERE hypothesis_group='baseline_additive'")[0]
    cmp = lab.compare_visible(eid, add["experiment_id"])
    assert cmp["n"] == n1 + nt and cmp["verdict"] in ("a", "b", "none")
    scores_a, cats = lab.visible_scores(eid)
    scores_b, _ = lab.visible_scores(add["experiment_id"])
    assert set(cats) == set(scores_a)   # the scored perturbations' categories only, never a sealed one
    diff = np.array([scores_a[p]["pearson_delta"] - scores_b[p]["pearson_delta"] for p in scores_a])
    assert cmp["mean_diff"] == pytest.approx(diff.mean(), abs=1e-12)
    assert np.mean([scores_a[p]["pearson_delta"] for p in scores_a]) == pytest.approx(m["primary"], abs=1e-9)
    assert set(cmp["by_category"]) == set(m["by_category_visible"])


def test_visible_scores_name_no_sealed_perturbation(pair_lab, pair_bundle):
    """visible_scores returns the categories of the perturbations it scores, never the split's whole map, which also
    names every sealed perturbation and its category."""
    sealed = set(json.loads((pair_bundle / "splits.json").read_text())["val2"])
    for folds in (0, 3):
        lab = pair_lab(experiment__cv_folds=folds)
        lab.record_analytic_baselines()
        add = lab.db.query("SELECT experiment_id FROM experiments WHERE hypothesis_group='baseline_additive'")[0]
        scores, cats = lab.visible_scores(add["experiment_id"])
        want = set(lab._val1.perts) | (set(lab._train.perts) if folds else set())
        assert set(scores) == want and set(cats) <= set(scores) and set(cats) == want
        assert not sealed & set(cats) and not sealed & set(lab._extras("val1")["categories"])


def _isolates(answer_mean: float, n_all: int, reported: list[tuple[int, float]], values: list[float]) -> bool:
    """Whether the pooled mean minus the reported categories' sums gives back one of `values` (one perturbation's)."""
    rest = answer_mean * n_all - sum(n * m for n, m in reported)
    return any(abs(rest - v) < 1e-9 for v in values)


def test_hidden_categories_are_never_hidden_alone():
    """Complementary suppression: with the pooled mean beside the categories, the hidden categories together hold no
    fewer than CATEGORY_MIN_N perturbations, so the pooled sum minus the reported ones never isolates a value."""
    assert hidden_categories({"single": 5, "pair_seen1": 14, "pair_seen2": 3, "pair_seen0": 1}) == \
        {"pair_seen0", "pair_seen2"}
    assert hidden_categories({"single": 5, "pair_seen1": 4}) == set()
    assert hidden_categories({"single": 5, "pair_seen1": 4}, loose=1) == {"pair_seen1"}   # one uncategorised
    assert hidden_categories({"b": 3, "a": 3, "c": 1}) == {"a", "c"}                         # ties by name
    assert hidden_categories({"a": 2, "b": 1}) == {"a", "b"}
    assert hidden_categories({"a": 1, "b": 1, "c": 1, "d": 9}) == {"a", "b", "c"}            # 3 together suffice
    rng = np.random.default_rng(0)
    sizes = {"single": 5, "pair_seen1": 14, "pair_seen2": 3, "pair_seen0": 1}
    cats = {f"{c}_{i}": c for c, n in sizes.items() for i in range(n)}
    per = {p: {"pearson_delta": float(rng.normal()), "r2_top": float(rng.normal())} for p in cats}
    other = {p: float(rng.normal()) for p in cats}
    summary = category_summary(per, cats)
    assert {c for c, e in summary.items() if set(e) == {"n"}} == {"pair_seen0", "pair_seen2"}
    for m in ("pearson_delta", "r2_top"):
        pooled = np.mean([v[m] for v in per.values()])
        reported = [(e["n"], e[m]["mean"]) for e in summary.values() if m in e]
        assert not _isolates(pooled, len(per), reported, [v[m] for v in per.values()])
    a = {p: v["pearson_delta"] for p, v in per.items()}
    pq = paired_summary(a, other, cats)
    assert {c for c, e in pq["by_category"].items() if set(e) == {"n"}} == {"pair_seen0", "pair_seen2"}
    reported = [(e["n"], e["mean_diff"]) for e in pq["by_category"].values() if "mean_diff" in e]
    assert not _isolates(pq["mean_diff"], pq["n"], reported, [a[p] - other[p] for p in a])
    assert pq["wins_a"] - sum(e["wins_a"] for e in pq["by_category"].values() if "wins_a" in e) <= 4
    # the old rule (fewer than CATEGORY_MIN_N only) would have given the lone pair_seen0 value back
    lone = next(p for p in cats if cats[p] == "pair_seen0")
    old = [(n, np.mean([a[p] for p in cats if cats[p] == c])) for c, n in sizes.items() if n >= CATEGORY_MIN_N]
    assert _isolates(np.mean(list(a.values())), len(a), old, [a[lone]])


def test_oracle_answers_never_isolate_a_sealed_perturbation(tmp_path):
    """The reviewer's case: a gene-grouped sealed set with a one-member category. Neither a query nor a paired query
    lets the pooled answer minus the reported categories give back that perturbation's value, difference or win."""
    rng = np.random.default_rng(0)
    genes = [f"G{i:02d}" for i in range(60)]
    targets = {g: [g] for g in genes[:30]}
    while len(targets) < 80:
        a, b = sorted(rng.choice(genes[:30], 2, replace=False))
        targets[f"{a}+{b}"] = [str(a), str(b)]
    base = rng.uniform(0.5, 3, 60)
    means = {p: base + rng.normal(0, 0.5, 60) for p in targets}
    control = np.maximum(base + rng.normal(0, 0.3, (300, 60)), 0)
    for seed in range(500):
        splits = make_gene_splits(targets, seed=seed)
        sizes = {}
        for p in splits["val2"]:
            sizes[splits["categories"][p]] = sizes.get(splits["categories"][p], 0) + 1
        if 1 in sizes.values() and all(splits[s] for s in ("train", "val1", "val2")):
            break
    else:
        pytest.fail("no split with a one-member sealed category")
    bundle = write_bundle(tmp_path / "b", "norman_toy", genes, control, means, {p: 50 for p in targets}, targets,
                          splits, extra_meta={"modality": "CRISPRa"})
    strata = bundle_strata(bundle)
    labels = LabelSet.load(bundle / "private" / "val2.npz")
    cm = control.astype(np.float32).astype(np.float64).mean(axis=0)
    pred = labels.means + rng.normal(0, 0.3, labels.means.shape)
    pred_b = labels.means + rng.normal(0, 0.3, labels.means.shape)
    oracle = QueryOracle(bundle, max_queries=5)
    m = oracle.query("x", pred, labels.perts, cm)["metrics"]
    per = evaluate(pred, labels.means, cm, labels.perts, targets=strata["target_idx"])["per_perturbation"]
    per_b = evaluate(pred_b, labels.means, cm, labels.perts)["per_perturbation"]
    n = len(labels.perts)
    hidden = {c for c, e in m["by_category"].items() if set(e) == {"n"}}
    assert any(sizes[c] == 1 for c in hidden) and sum(sizes[c] for c in hidden) >= CATEGORY_MIN_N
    for metric in ("pearson_delta", "pearson_delta_nontarget", "r2_top"):
        reported = [(e["n"], e[metric]["mean"]) for e in m["by_category"].values() if metric in e]
        assert not _isolates(m[metric], n, reported, [v[metric] for v in per.values()]), metric
    pq = oracle.query_paired("a", pred, labels.perts, "b", pred_b, labels.perts, cm, metric="pearson_delta")["paired"]
    diffs = [per[p]["pearson_delta"] - per_b[p]["pearson_delta"] for p in labels.perts]
    reported = [(e["n"], e["mean_diff"]) for e in pq["by_category"].values() if "mean_diff" in e]
    assert not _isolates(pq["mean_diff"], n, reported, diffs)
    assert {c for c, e in pq["by_category"].items() if set(e) == {"n"}} == hidden
    left = pq["wins_a"] - sum(e["wins_a"] for e in pq["by_category"].values() if "wins_a" in e)
    assert sum(sizes[c] for c in hidden) >= CATEGORY_MIN_N and 0 <= left <= sum(sizes[c] for c in hidden)


def test_paired_sealed_query_is_recorded_and_counted_after_reopening(pair_lab, pair_bundle, code_repo):
    """Lab.query_paired spends two queries and records both in lab.db (with the paired summary and the whole answer),
    so the same run reopened counts them; a paired query on the lab's oracle directly is recorded alike."""
    from genemila.lab import Lab
    lab = pair_lab(final__max_queries=5)
    lab.record_analytic_baselines()
    ids = {r["hypothesis_group"]: r["experiment_id"] for r in lab.db.query("SELECT * FROM experiments")}
    add, mean = ids["baseline_additive"], ids["baseline_mean_response"]
    out = lab.query_paired(add, mean)
    assert out["experiments"] == [add, mean] and lab.oracle.used == 2
    ev = lab.db.query("SELECT kind, experiment_id, message FROM events WHERE kind IN ('query_only', 'query_paired') "
                      "ORDER BY id")
    assert [(e["kind"], e["experiment_id"]) for e in ev] == [("query_only", add), ("query_only", mean),
                                                            ("query_paired", add)]
    note = json.loads(ev[2]["message"])
    assert note["paired"] == out["paired"] and note["experiments"] == [add, mean]
    saved = json.loads((lab.run_dir / "query_paired" / note["file"]).read_text())
    assert saved == json.loads(json.dumps(out))
    # the same answer as the oracle's own paired query on the lab's predictions
    perts = lab.oracle.perts
    pa = lab._analytic_baseline("baseline_additive", perts)
    pb = lab._analytic_baseline("baseline_mean_response", perts)
    other = QueryOracle(pair_bundle, max_queries=5).query_paired(add, pa, perts, mean, pb, perts, lab.control_mean)
    assert other["paired"] == out["paired"] and other["a"] == out["a"] and other["b"] == out["b"]
    cfg, run_dir = lab.cfg, lab.run_dir
    lab.close()
    again = Lab(cfg, run_dir, pair_bundle, repo=code_repo)
    try:
        assert again.oracle.used == 2   # a reopened run remembers the paired query
        again.oracle.query_paired("x", pa, perts, "y", pb, perts, again.control_mean)   # directly: recorded too
        assert again.db.query("SELECT COUNT(*) AS n FROM events WHERE kind='query_only'")[0]["n"] == 4
        again.query_only(add)
        with pytest.raises(QueryBudgetExceeded):
            again.query_only(mean)
        with pytest.raises(QueryBudgetExceeded):
            again.query_paired(add, mean)
    finally:
        again.close()
    third = Lab(cfg, run_dir, pair_bundle, repo=code_repo)
    try:
        assert third.oracle.used == 5
        with pytest.raises(QueryBudgetExceeded):
            third.query_only(add)
    finally:
        third.close()


def test_random_split_with_pairs_is_grouped_and_derives_categories(tmp_path):
    bundle = make_pair_bundle(tmp_path / "pairs_random", seed=3, gene_split=False)
    strata = bundle_strata(bundle)
    splits = json.loads((bundle / "splits.json").read_text())
    assert strata["grouped"] and "categories" not in splits
    z = np.load(bundle / "public.npz")
    assert strata["categories"] == categories_of(splits["val1"] + splits["val2"], strata["targets"],
                                                 [str(p) for p in z["train_perts"]])


def test_feature_audit_folds_follow_the_run_s_grouping(pair_bundle, dataset, tmp_path):
    """tools/feature_audit.py builds its fold units on the run's folds: gene-grouped ones (each unit's training rows
    leave out the fold's hidden set, its predicted rows are the fold) for a run that recorded cv_groups, the old
    random folds otherwise."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import feature_audit as fa
    feats = ["control_mean", "mean_response", "is_target"]
    for bundle, groups in ((pair_bundle, "gene"), (dataset, None)):
        ctx = FeatureContext(export_public(bundle, tmp_path / f"pub_{groups}"))
        val1 = LabelSet.load(bundle / "private" / "val1.npz")
        fits = fa.compute_fits(ctx, feats, {}, [0, 1], 3, val1.perts, val1.means - ctx.control_mean, groups=groups)
        targets = None if groups is None else {p: ctx.target_genes(p) for p in ctx.train_perts}
        for s in (0, 1):
            folds = cv_folds_of(ctx.train_perts, 3, s, targets)
            rows = [list(r) for _, r in fits["seed_units"][s]]
            assert rows == [[ctx.train_perts.index(p) for p in fold] for fold, _ in folds]
            if groups is None:
                assert [f for f, _ in folds] == _old_folds(ctx.train_perts, 3, s)
            else:
                assert any(f != h for f, h in folds)


# ------------------------------------------------------------------ the additive rule in the starting model
def test_additive_response_is_the_additive_baseline_left_out(pair_lab):
    """On a bundle with pairs the built-in additive_response is the additive baseline's predicted change: for a
    validation perturbation exactly that, for a training one the same rule without it, and in a cross-validation
    fold's view the baseline's out-of-fold twin, so ridge on it starts where the additive baseline is."""
    from genemila.additive import additive_delta
    from genemila.features.registry import BUILTIN_FEATURES, get
    lab = pair_lab(experiment__cv_folds=3)
    assert lab.builtin_features == BUILTIN_FEATURES + ["additive_response"]
    assert lab.db.feature("additive_response")["builtin"] and "additive_response" in lab.known_features()
    assert lab.store_files(["additive_response"]) == {}  # no plugin file: experiment processes have it built in
    ctx = FeatureContext(lab.public_dir)
    feat = get("additive_response")()
    val = lab._val1.perts
    got = feat.compute(ctx, val, {})[:, :, 0]
    assert np.allclose(got, lab._analytic_baseline("baseline_additive", val) - lab.control_mean, rtol=0, atol=1e-12)
    train, delta = lab._train.perts, lab._train.means - lab.control_mean
    got = feat.compute(ctx, train, {})[:, :, 0]
    for i, p in enumerate(train):
        keep = [j for j, q in enumerate(train) if q != p]
        want = additive_delta([p], lab._targets, [train[j] for j in keep], delta[keep])[0]
        assert np.allclose(got[i], want, rtol=0, atol=1e-12), p
    oof = lab._cv_baseline("baseline_additive") - lab.control_mean
    pos = {p: i for i, p in enumerate(train)}
    for fold, hide in lab._cv_folds():
        view = ctx.without_train(hide)
        got = feat.compute(view, fold, {})[:, :, 0]
        assert np.allclose(got, oof[[pos[p] for p in fold]], rtol=0, atol=1e-12)


def test_pair_bundle_agents_start_from_ridge_on_the_additive_rule(pair_lab):
    """A bundle with pairs queues ridge on the built-ins plus additive_response beside the three model baselines; on
    this additive screen it is the best model before any agent idea, so the planner's first features hang off it and
    carry the rule."""
    from genemila.controller import Controller
    from genemila.providers.mock import MockProvider, ScriptedPlanner
    lab = pair_lab(experiment__cv_folds=3, schedule__max_planner_calls=1)
    Controller(lab, workers=2, seconds=40, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
               quiet=True).run()
    base = {r["hypothesis_group"]: r for r in lab.db.query("SELECT * FROM experiments WHERE kind='baseline'")}
    assert set(base) == {"baseline_unchanged", "baseline_mean_response", "baseline_additive", "baseline_ols",
                         "baseline_ridge", "baseline_lasso", "baseline_ridge_additive"}
    start = base["baseline_ridge_additive"]
    assert start["status"] == "completed" and start["model_type"] == "ridge"
    assert start["feature_set_json"] == ["control_mean", "mean_response", "is_target", "additive_response"]
    modelled = [b for b in base.values() if b["model_type"] != "none" and b["status"] == "completed"]
    assert max(modelled, key=lambda b: b["primary_score"]) is start
    assert start["primary_score"] > base["baseline_ridge"]["primary_score"]
    first = lab.db.query("SELECT * FROM experiments WHERE kind!='baseline' AND proposer NOT LIKE 'python%' "
                         "ORDER BY created_at LIMIT 1")
    assert first and first[0]["parent_id"] == start["experiment_id"]
    assert "additive_response" in first[0]["feature_set_json"]


def test_single_target_bundle_has_no_additive_built_in(lab_factory):
    """Adamson's kind of bundle keeps its three built-ins and three model baselines."""
    from genemila.features.registry import BUILTIN_FEATURES
    lab = lab_factory()
    assert lab.builtin_features == BUILTIN_FEATURES and "additive_response" not in lab.known_features()
    lab.queue_model_baselines()
    groups = {r["hypothesis_group"] for r in lab.db.query("SELECT hypothesis_group FROM experiments")}
    assert groups == {"baseline_ols", "baseline_ridge", "baseline_lasso"}


def test_reopening_a_pair_run_from_before_the_built_in_writes_nothing(pair_lab, pair_bundle, code_repo):
    """A pair run made before additive_response existed, reopened for a report or a sealed reading, gets no new feature
    row; one made with it keeps it."""
    from genemila.lab import open_run
    lab = pair_lab()
    run_dir = lab.run_dir
    lab.db.execute("DELETE FROM features WHERE name='additive_response'")  # as a run of the old code left it
    lab.close()
    old = open_run(run_dir)
    try:
        assert "additive_response" not in old.builtin_features and old.db.feature("additive_response") is None
    finally:
        old.close()
    new = pair_lab()
    new_dir = new.run_dir
    new.close()
    again = open_run(new_dir)
    try:
        assert "additive_response" in again.builtin_features
    finally:
        again.close()
