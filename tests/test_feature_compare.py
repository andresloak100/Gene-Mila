"""tools/feature_compare.py: the feature-level comparison of research systems. Its out-of-fold predictions are the
lab's cross_validate ones, a planted feature is meaningful and noise is not, foreign files are rejected before they
run, the gene null permutes within bins of control expression, and the visible validation labels are read only on
request, in one function. The corrected test (docs/ROADMAP.md D2): a candidate proportional to a parent column gets
the perturbation null and is not found when its scalars are random, identical candidates collapse to one family
member, the family-wise p is a max-gain step-down over shared permutations, and the candidate's standardised
coefficient carries a sign."""

import argparse
import ast
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import feature_compare as fc  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.pipeline import cross_validate  # noqa: E402
from test_norman_lab import make_pair_bundle  # noqa: E402

TOOL = ROOT / "tools" / "feature_compare.py"
SEEDS = [101, 102]

PLUGIN = '''{prefix}import numpy as np
from genemila.features.api import Feature, register


@register
class F(Feature):
    name = "{name}"

    def compute(self, ctx, perts, params):
{body}
'''
NOISE = ("        v = np.sin(1e3 * ctx.control_mean)\n"
         "        return np.broadcast_to(v[None, :, None], (len(perts), ctx.n_genes, 1)).copy()")
PLANTED = ("        k = ctx.knowledge('planted')\n"
           "        return np.array([k[p] for p in perts], dtype=float)[:, :, None]")
NEG_PLANTED = PLANTED.replace("return np.array", "return -np.array")
# a parent column times a pseudo-random per-perturbation scalar (from the name): the shape of block F's e428
PROP = ("        q = ctx.feature('{parent}', perts)[:, :, 0]\n"
        "        c = np.array([np.sin(1.0 + sum(ord(ch) for ch in p)) for p in perts])\n"
        "        return (q * c[:, None])[:, :, None]")


def _plugin(d: Path, name: str, body: str, prefix: str = "") -> Path:
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{name}.py"
    path.write_text(PLUGIN.format(prefix=prefix, name=name, body=body))
    return path


def _planted_bundle(dataset: Path, dst: Path) -> Path:
    """A copy of the synthetic bundle with knowledge/planted.json: every perturbation's true delta plus a little
    noise (the test reads the bundle's own held-out files to build it; the tool never does)."""
    shutil.copytree(dataset, dst)
    z = np.load(dst / "public.npz")
    cm = z["control_cells"].astype(np.float64).mean(axis=0)
    means = dict(zip([str(p) for p in z["train_perts"]], z["train_means"].astype(np.float64)))
    for part in ("val1", "val2"):
        h = np.load(dst / "private" / f"{part}.npz")
        means.update(zip([str(p) for p in h["perts"]], h["means"].astype(np.float64)))
    rng = np.random.default_rng(0)
    planted = {p: list(m - cm + rng.normal(0, 0.05 * np.std(m - cm), len(cm))) for p, m in means.items()}
    (dst / "knowledge" / "planted.json").write_text(json.dumps(planted))
    return dst


# ------------------------------------------------------------------ hygiene
def test_source_never_names_the_sealed_labels_and_reads_held_out_labels_in_one_function():
    src = TOOL.read_text()
    for word in ("val2", "splits.json", "QueryOracle", "open_run", "query_only"):
        assert word not in src, word
    fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "load_val1")
    lines = [i for i, line in enumerate(src.splitlines(), start=1) if "private" in line]
    assert lines and all(fn.lineno <= i <= fn.end_lineno for i in lines), lines


# ------------------------------------------------------------------ parity with the lab
@pytest.fixture(scope="module")
def pair_bundle(tmp_path_factory):
    return make_pair_bundle(tmp_path_factory.mktemp("pair") / "pair")


@pytest.mark.parametrize("which", ["single", "pair"])
def test_out_of_fold_predictions_equal_cross_validate(which, dataset, pair_bundle):
    bundle, groups = (dataset, None) if which == "single" else (pair_bundle, "gene")
    feats = ["control_mean", "mean_response", "is_target"] + (["additive_response"] if groups else [])
    alphas = fc.alpha_grid()
    res = fc.compute_blocks(bundle, None, feats, {}, SEEDS, 5, groups, False)
    assert not res["errors"]
    data = fc.make_data(bundle)
    data.folds = res["folds"]
    O = fc.oof_predictions([(res, feats, None)], data, SEEDS, alphas)
    ctx = FeatureContext(bundle)
    for s in SEEDS:
        ref = cross_validate(ctx, feats, {}, "ridge", alphas, 0, 5, s, {}, None, None, {}, {}, groups)
        np.testing.assert_allclose(O[s], ref, atol=1e-5)


def test_the_gene_null_permutes_within_bins_and_is_fixed_by_its_seed(dataset):
    cm = FeatureContext(dataset).control_mean
    edges = np.quantile(cm, np.linspace(0, 1, 11)[1:-1])
    bins = np.digitize(cm, edges)
    perm = fc.gene_permutation(cm, 10, 3)
    assert sorted(perm) == list(range(len(cm)))
    assert np.array_equal(bins[perm], bins) and (perm != np.arange(len(cm))).any()
    assert np.array_equal(perm, fc.gene_permutation(cm, 10, 3))
    assert not np.array_equal(perm, fc.gene_permutation(cm, 10, 4))
    assert fc.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_the_perturbation_null_permutes_within_target_expression_bins_and_is_fixed_by_its_seed(dataset):
    data = fc.make_data(dataset)
    bins = fc.pert_bins(data, 10)
    assert len(bins) == len(data.train) and set(bins) <= set(range(11))
    # the bins follow the mean control expression of the measured targets; a perturbation without one is in bin 10
    m = np.array([np.mean(data.cm[data.tidx[p]]) if data.tidx[p] else np.nan for p in data.train])
    assert all((bins[i] == 10) == np.isnan(m[i]) for i in range(len(m)))
    ok = ~np.isnan(m)
    assert all(m[i] <= m[j] for i in np.flatnonzero(ok) for j in np.flatnonzero(ok) if bins[i] < bins[j])
    perm = fc.pert_permutation(bins, 7)
    assert sorted(perm) == list(range(len(bins))) and np.array_equal(bins[perm], bins)
    assert np.array_equal(perm, fc.pert_permutation(bins, 7)) and not np.array_equal(perm, fc.pert_permutation(bins, 8))


def test_the_step_down_p_values_on_a_hand_made_gains_matrix():
    """Westfall-Young max-gain step-down: the largest observed gain is compared with the max over every row, the
    next with the max over the rows at or below it, and the p values never decrease down the order."""
    observed = [0.5, 0.1, 0.3]
    gains = np.array([[0.2, 0.6, 0.1, 0.0],    # row 0: beaten by replicate 1 only
                      [0.05, 0.0, 0.2, 0.15],  # row 1
                      [0.4, 0.1, 0.0, 0.2]])   # row 2
    p = fc.max_gain_step_down(observed, gains)
    # row 0 (0.5): max over all rows per replicate = [0.4, 0.6, 0.2, 0.2] -> 1 at or above -> (1 + 1) / 5
    # row 2 (0.3): max over rows 2 and 1 = [0.4, 0.1, 0.2, 0.2] -> 1 -> 2/5, kept at max(2/5, 2/5)
    # row 1 (0.1): own gains [0.05, 0, 0.2, 0.15] -> 2 -> 3/5
    assert p == pytest.approx([2 / 5, 3 / 5, 2 / 5])
    order = np.argsort(-np.array(observed))
    assert all(p[order[j]] <= p[order[j + 1]] for j in range(len(order) - 1))
    # monotonicity is enforced: a later row with a smaller raw count inherits the earlier p
    p2 = fc.max_gain_step_down([0.5, 0.49], [[0.6, 0.6, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]])
    assert p2 == pytest.approx([3 / 5, 3 / 5])
    assert fc.max_gain_step_down([0.1], [[0.0] * 999]) == [1 / 1000]  # the floor
    assert fc.max_gain_step_down([], []) == []
    with pytest.raises(ValueError):
        fc.max_gain_step_down([0.1, 0.2], [[0.0, 0.0]])


def test_proportional_to_parent_detects_a_per_perturbation_scalar_times_one_parent_column():
    rng = np.random.default_rng(0)
    parent = rng.normal(size=(6, 20, 3))
    parent[2, :, 1] = 0.0  # a row where parent column 1 is all zero
    c = rng.normal(size=6)
    c[4] = 0.0  # a zero scalar is allowed
    cand = (parent[:, :, 1] * c[:, None])[:, :, None]
    cand[2] = 0.0  # the candidate is zero where the parent column is
    idx, got = fc.proportional_to_parent(cand, parent)
    assert idx == [1] and got.shape == (6, 1)
    assert got[:, 0] == pytest.approx(np.where(np.arange(6) == 2, 0.0, c))
    # the same product formed in float32 (relative residual about 4e-8) is still proportional at rtol 1e-6, not 1e-9
    f32 = (parent[:, :, 1].astype(np.float32) * c.astype(np.float32)[:, None]).astype(np.float64)[:, :, None]
    f32[2] = 0.0
    assert fc.proportional_to_parent(f32, parent)[0] == [1] and fc.PROP_RTOL == 1e-6
    assert fc.proportional_to_parent(f32, parent, rtol=1e-9) is None
    nz = np.linalg.norm(cand[:, :, 0], axis=1) > 0
    rel = np.linalg.norm(f32[nz, :, 0] - cand[nz, :, 0], axis=1) / np.linalg.norm(cand[nz, :, 0], axis=1)
    assert 1e-9 < np.max(rel) < 1e-6
    # one entry off, a different scaling per gene, or a column not in the parent: not proportional
    bad = cand.copy()
    bad[0, 3, 0] += 1e-3
    assert fc.proportional_to_parent(bad, parent) is None
    assert fc.proportional_to_parent(cand * rng.normal(size=(1, 20, 1)), parent) is None
    assert fc.proportional_to_parent(rng.normal(size=(6, 20, 1)), parent) is None
    # a candidate that is non-zero where the parent column is zero has information of its own
    own = cand.copy()
    own[2, :, 0] = 1.0
    assert fc.proportional_to_parent(own, parent) is None
    # several columns: every one must fit, each with its own parent column
    two = np.concatenate([cand, (parent[:, :, 0] * 2.0)[:, :, None]], axis=2)
    assert fc.proportional_to_parent(two, parent)[0] == [1, 0]
    assert fc.parent_column_names([({"full": {"a": np.zeros((1, 1, 1)), "b": np.zeros((1, 1, 2))}}, ["a", "b"],
                                    None)]) == ["a", "b[0]", "b[1]"]


# ------------------------------------------------------------------ a full run on the synthetic bundle
@pytest.fixture(scope="module")
def main_run(tmp_path_factory, dataset):
    """One command-line run with --with-val1: a planted feature, a noise feature, three copies of the negated
    planted feature (one family member, with a negative coefficient) and four files that must be rejected (guard,
    literal caps, collision with a built-in, a wrong shape)."""
    tmp = tmp_path_factory.mktemp("fc_main")
    bundle = _planted_bundle(dataset, tmp / "bundle")
    _plugin(tmp / "planted", "planted_feat", PLANTED)
    _plugin(tmp / "noise", "noise_feat", NOISE)
    for name in ("neg_a", "neg_b", "neg_c"):
        _plugin(tmp / "dup", name, NEG_PLANTED)
    bad = tmp / "bad"
    marker = tmp / "executed_marker"
    _plugin(bad, "guard_feat", NOISE, prefix=f"import os\nos.makedirs({str(marker)!r})\n")
    _plugin(bad, "literal_feat", "        return np.zeros((len(perts), ctx.n_genes, 1)) + sum(W)",
            prefix="W = [" + ", ".join(str(i) for i in range(30)) + "]\n")
    _plugin(bad, "mean_response", NOISE)
    _plugin(bad, "shape_feat", "        return np.ones((len(perts), 3))")
    _plugin(bad, "dep_feat", "        return ctx.feature('guard_feat', perts)")
    _plugin(bad, "zz_broken", NOISE, prefix="X = 1 // 0\n")  # passes the guard, raises on import
    out = tmp / "out"
    r = subprocess.run([sys.executable, str(TOOL), "--data", str(bundle), "--out", str(out),
                        "--source", f"planted={tmp / 'planted'}", "--source", f"noise={tmp / 'noise'}",
                        "--source", f"bad={bad}", "--source", f"dup={tmp / 'dup'}",
                        "--fold-seeds", "101,102", "--null-reps", "39", "--with-val1"],
                       capture_output=True, text=True, cwd=tmp, timeout=600)
    assert r.returncode == 0, r.stderr
    return {"json": json.loads((out / "feature_compare.json").read_text()),
            "md": (out / "feature_compare.md").read_text(), "marker": marker}


def _row(res, feature, source=None):
    return next(r for r in res["rows"] if r["feature"] == feature and (source is None or r["source"] == source))


def test_a_planted_feature_passes_every_criterion_but_the_replicate_count(main_run):
    """39 replicates keep the run cheap; the rule is 999 for a family of any size (a family of one at 19 would put
    the floor 1/20 at the cutoff, docs/ROADMAP.md section 1), so the only failed criterion is the replicate count."""
    res = main_run["json"]
    row = _row(res, "planted_feat")
    assert row["status"] == "ok" and not row["meaningful"]
    assert row["failed_criteria"] == ["null too coarse for a family of 1 (need --null-reps >= 999)"]
    assert row["verdict"] == "not: " + row["failed_criteria"][0]
    # the correction runs within each source: planted's family is itself, whatever the other sources sent; the
    # three identical copies of dup are one member
    assert res["settings"]["families"] == {"planted": {"add_one": 1, "set": 1}, "noise": {"add_one": 1, "set": 1},
                                           "bad": {"add_one": 0, "set": 0}, "dup": {"add_one": 1, "set": 1}}
    for t in ("oof", "val1"):
        assert row["tiers"][t]["null"]["p"] == pytest.approx(1 / 40)
        assert row["tiers"][t]["null"]["p_holm"] == pytest.approx(1 / 40)
        assert row["tiers"][t]["null"]["p_fwer"] == pytest.approx(1 / 40)  # a family of one: the floor
        assert len(row["tiers"][t]["null"]["gains"]) == 39
    # (b) an informative non-proportional candidate is found, on the gene null alone
    assert row["proportional"] is False and row["parent_column"] is None and row["tiers"]["oof"]["null_pert"] is None
    assert row["exposure"] == "oof"
    assert all(d > 0 for d in row["tiers"]["oof"]["report_deltas"])
    assert len(row["tiers"]["oof"]["report_deltas"]) == 2
    assert row["tiers"]["oof"]["delta"]["pearson_delta"]["overlap_ratio"] == pytest.approx(1.0)  # single targets
    assert row["label_dependent"] is False
    assert _row(res, "(set)", "planted")["failed_criteria"] == ["null too coarse for a family of 1 (need --null-reps >= 999)"]
    assert res["settings"]["p_floor"] == pytest.approx(1 / 40) and res["settings"]["min_gain"] == 0.002


def test_identical_candidates_collapse_to_one_family_member_and_the_coefficient_sign_is_read(main_run):
    """(c) three copies of one column: the first is kept and lists the others, which get status duplicate and no
    null; (f) the planted feature's standardised coefficient is positive and its negation's negative."""
    res, md = main_run["json"], main_run["md"]
    kept, dups = _row(res, "neg_a"), [_row(res, "neg_b"), _row(res, "neg_c")]
    assert kept["status"] == "ok" and kept["duplicates"] == ["neg_b", "neg_c"]
    assert kept["failed_criteria"] == ["null too coarse for a family of 1 (need --null-reps >= 999)"]
    for d in dups:
        assert d["status"] == "duplicate" and d["reason"].startswith("duplicate of neg_a") and not d["meaningful"]
        assert d["prediction_hash"] == kept["prediction_hash"] and "null" not in d["tiers"]["oof"]
        assert d["verdict"] == "duplicate of neg_a"
    planted = _row(res, "planted_feat")
    # the hash is the predictions alone: the negation predicts alike, so in one source it would be a duplicate
    # (ROADMAP D2(c)); here they are in different sources and both are family members, each with its own sign
    assert planted["prediction_hash"] == kept["prediction_hash"]
    fam = res["settings"]["families"]
    assert fam["planted"]["add_one"] == fam["dup"]["add_one"] == 1
    assert all(d["coef_candidate_sign"] == "-" for d in dups)  # a duplicate row keeps its own sign
    assert len(planted["coef_candidate_std"]) == 2 and all(c > 0 for c in planted["coef_candidate_std"])
    assert planted["coef_candidate_sign"] == "+" and planted["coef_candidate_mean"] > 0
    assert kept["coef_candidate_sign"] == "-" and all(c < 0 for c in kept["coef_candidate_std"])
    assert kept["coef_candidate_mean"] == pytest.approx(-planted["coef_candidate_mean"], rel=1e-6)
    assert "| + (2/2 reports) |" in md and "| - (2/2 reports) |" in md and "| duplicate |" in md
    assert _row(res, "(set)", "dup")["status"] == "ok"  # the set row keeps every passing file


def test_a_noise_feature_is_not_meaningful(main_run):
    row = _row(main_run["json"], "noise_feat")
    assert row["status"] == "ok" and not row["meaningful"] and row["failed_criteria"]


def test_rejected_files_are_rows_and_never_run(main_run):
    res = main_run["json"]
    want = {"guard_feat": "guard", "literal_feat": "literal", "mean_response": "collision", "shape_feat": "smoke",
            "dep_feat": "error", "zz_broken": "error"}
    assert {f: _row(res, f, "bad")["status"] for f in want} == want
    assert "guard_feat" in _row(res, "dep_feat")["reason"]  # its dependency was rejected, so it cannot compute
    assert "import of 'os'" in _row(res, "guard_feat")["reason"]
    assert "30 elements" in _row(res, "literal_feat")["reason"]
    assert "shape" in _row(res, "shape_feat")["reason"]
    # a file that raises on import costs only its own row
    assert "ZeroDivisionError" in _row(res, "zz_broken")["reason"]
    assert not any("ZeroDivisionError" in _row(res, f, "bad")["reason"] for f in ("shape_feat", "dep_feat"))
    assert not main_run["marker"].exists()  # the guard-rejected file never executed, anywhere
    assert _row(res, "(set)", "bad")["status"] == "error"


def test_output_schema_and_tables(main_run):
    res, md = main_run["json"], main_run["md"]
    s = res["settings"]
    assert s["tiers"] == ["oof", "val1"] and s["deciding_tier"] == "val1" and s["groups"] is None
    assert s["fold_seeds"] == SEEDS and s["alphas"] == sorted(s["alphas"]) and 1e5 in s["alphas"]
    assert any("val1.npz" in x for x in s["labels_read"])
    assert res["parent"]["features"] == ["control_mean", "mean_response", "is_target"]
    assert set(res["parent"]["tiers"]["val1"]["metrics"]) == set(fc.LABEL)
    t = _row(res, "noise_feat")["tiers"]["oof"]
    assert {"n", "honest", "metrics", "delta", "report_deltas", "alphas", "null"} <= set(t)
    assert {"mean", "sd", "p95", "p", "p_holm", "p_fwer", "excess", "reps", "observed", "gains"} <= set(t["null"])
    assert "null_pert" in t and {"null_pert", "correction", "p_floor", "min_gain"} <= set(s)
    assert "| null p raw / Holm / FWER | excess | pert null p raw / FWER (parent column) | coef sign |" in md
    assert "## Table 1. Systems: feature set + linear model" in md
    assert "## Table 2. Single features added to the parent" in md
    assert "| row | tier | n features | n columns | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M12 | ΔM1 ± SE_adj |" in md
    assert "| source | feature | tier | status | ΔM1 ± SE_adj | wins/n | ΔM2 | ΔM4 | ΔM5 | ΔM7 |" in md
    assert "Wilcoxon" in md and fc.OOF_CAVEAT not in md  # val1 decides here


# ------------------------------------------------------------------ the pair bundle, without val1
def test_pair_bundle_groups_by_gene_reports_overlap_and_a_set_row(pair_bundle, tmp_path):
    _plugin(tmp_path / "src", "noise_feat", NOISE)
    _plugin(tmp_path / "src", "second_feat", "        return np.cos(3.0 * ctx.control_mean)[None, :, None] "
                                             "* np.ones((len(perts), 1, 1))")
    out = tmp_path / "out"
    assert fc.main(["--data", str(pair_bundle), "--out", str(out), "--source", f"s={tmp_path / 'src'}",
                    "--fold-seeds", "101,102", "--null-reps", "19"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    assert res["settings"]["groups"] == "gene" and res["settings"]["tiers"] == ["oof"]
    assert res["parent"]["features"][-1] == "additive_response"
    assert res["settings"]["labels_read"] == ["training labels (public.npz)"]
    ratio = _row(res, "noise_feat")["tiers"]["oof"]["delta"]["pearson_delta"]["overlap_ratio"]
    assert ratio is not None and ratio > 0 and ratio != pytest.approx(1.0)
    s = _row(res, "(set)", "s")
    assert s["status"] == "ok" and s["features"] == ["noise_feat", "second_feat"]
    assert s["model"] == res["parent"]["features"] + ["noise_feat", "second_feat"]
    assert s["n_columns"] == res["parent"]["n_columns"] + 2
    assert fc.OOF_CAVEAT in (out / "feature_compare.md").read_text()
    # (b) with 19 replicates a family of two is too coarse for the step-down, and the verdict says so
    assert "null too coarse for a family of 2 (need --null-reps >= 999)" in _row(res, "noise_feat")["failed_criteria"]


def test_a_parent_column_times_a_random_scalar_is_proportional_and_not_found(pair_bundle, tmp_path):
    """(a) The shape of block F's e428: additive_response times a per-perturbation scalar. The gene null cannot
    fail it (it scrambles the parent factor the model holds, so its replicates are worthless), the perturbation
    null can: the scalars are exchangeable with their permutation, so its p is not small."""
    _plugin(tmp_path / "src", "prop_feat", PROP.format(parent="additive_response"))
    # a scalar computed from the view's own parent column: proportional in the full view, not in the fold views
    _plugin(tmp_path / "src2", "view_feat", "        q = ctx.feature('additive_response', perts)[:, :, 0]\n"
                                            "        return (q * q.mean(axis=1)[:, None])[:, :, None]")
    out = tmp_path / "out"
    assert fc.main(["--data", str(pair_bundle), "--out", str(out), "--source", f"s={tmp_path / 'src'}",
                    "--source", f"s2={tmp_path / 'src2'}", "--fold-seeds", "101,102", "--null-reps", "39"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    view = _row(res, "view_feat")
    assert view["status"] == "ok" and view["proportional"] is True and view["proportional_in_folds"] is False
    assert view["tiers"]["oof"]["null_pert"] is None and not view["meaningful"]
    assert ("proportional to a parent column but no perturbation null (proportional in the full view only)"
            in view["failed_criteria"])
    row = _row(res, "prop_feat")
    assert row["status"] == "ok" and row["proportional"] is True and row["parent_column"] == "additive_response"
    assert row["proportional_in_folds"] is True
    nul, pert = row["tiers"]["oof"]["null"], row["tiers"]["oof"]["null_pert"]
    assert pert["parent_column"] == "additive_response" and pert["reps"] == 39 and len(pert["gains"]) == 39
    assert {"p", "p_holm", "p_fwer", "mean", "sd", "p95", "excess", "observed"} <= set(pert)
    assert pert["observed"] == pytest.approx(nul["observed"])
    # the gene null's replicates barely move (the parent factor stays in the model), the perturbation null's do
    assert pert["sd"] > 2 * nul["sd"]
    assert pert["p"] > 0.05 and pert["p_fwer"] > 0.05 and not row["meaningful"]
    # 39 replicates are too coarse for any family, so the verdict names that rather than the pert p
    assert "null too coarse for a family of 1 (need --null-reps >= 999)" in row["failed_criteria"], row["failed_criteria"]
    assert res["settings"]["families"]["s"]["add_one"] == 1
    md = (out / "feature_compare.md").read_text()
    assert "(additive_response)" in md and "not proportional" not in md


def test_val1_is_required_to_exist_and_not_read_without_the_flag(dataset, tmp_path):
    pub = tmp_path / "public_only"
    pub.mkdir()
    shutil.copyfile(dataset / "public.npz", pub / "public.npz")
    shutil.copytree(dataset / "knowledge", pub / "knowledge")
    _plugin(tmp_path / "src", "noise_feat", NOISE)
    args = ["--data", str(pub), "--out", str(tmp_path / "out"), "--source", f"s={tmp_path / 'src'}",
            "--fold-seeds", "101", "--null-reps", "0"]
    assert fc.main(args + ["--with-val1"]) == 2 and not (tmp_path / "out").exists()
    assert fc.main(args) == 0  # a public directory without a manifest is enough
    res = json.loads((tmp_path / "out" / "feature_compare.json").read_text())
    assert res["split_id"] is None and res["rows"][0]["tiers"]["oof"]["honest"] is False
    assert res["rows"][0]["tiers"]["oof"]["null"] is None and "not honest" in " ".join(res["caveats"])


# ------------------------------------------------------------------ run directories as parent and source
def _fake_run(d: Path, features: list[str], plugins: dict[str, str], hp: dict, params: dict | None = None,
              split_id: str | None = None) -> Path:
    """A minimal finished run: lab.db with the selected experiment, and feature_store/."""
    (d / "feature_store").mkdir(parents=True)
    for name, text in plugins.items():
        (d / "feature_store" / f"{name}.py").write_text(text)
    c = sqlite3.connect(d / "lab.db")
    c.execute("CREATE TABLE runs (run_id TEXT, split_id TEXT, dataset TEXT, base_commit TEXT, config_json TEXT)")
    c.execute("CREATE TABLE experiments (experiment_id TEXT, status TEXT, kind TEXT, primary_score REAL, "
              "finished_at REAL, feature_set_json TEXT, new_feature TEXT, feature_params_json TEXT, "
              "hyperparameters_json TEXT, delta_from_parent REAL)")
    c.execute("INSERT INTO runs VALUES ('r', ?, 'synthetic', '', '{}')", (split_id,))
    c.execute("INSERT INTO experiments VALUES ('EXP_1', 'completed', 'new_feature', 0.5, 1, ?, NULL, ?, ?, NULL)",
              (json.dumps(features), json.dumps(params or {}), json.dumps(hp)))
    c.commit()
    c.close()
    return d


def test_runs_as_parent_and_as_source(dataset, tmp_path):
    base = ["control_mean", "mean_response", "is_target"]
    noise = PLUGIN.format(prefix="", name="noise_feat", body=NOISE)
    bad = PLUGIN.format(prefix="import os\n", name="bad_feat", body=NOISE)
    src_run = _fake_run(tmp_path / "src_run", base + ["noise_feat"], {"noise_feat": noise, "bad_feat": bad},
                        {"cv_folds": 5})
    out = tmp_path / "out"
    common = ["--data", str(dataset), "--fold-seeds", "101,102", "--null-reps", "3"]
    assert fc.main(common + ["--out", str(out), "--source-run", f"r={src_run}"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    assert [r["feature"] for r in res["rows"]] == ["noise_feat", "(set)"]
    assert _row(res, "noise_feat")["status"] == "ok" and "literal" in _row(res, "noise_feat")
    # the same run as the parent: its recorded grouping (none) wins, a contradicting flag is refused
    par_run = _fake_run(tmp_path / "par_run", base + ["noise_feat"], {"noise_feat": noise}, {"cv_folds": 5})
    _plugin(tmp_path / "src", "second_feat", "        return np.cos(3.0 * ctx.control_mean)[None, :, None] "
                                             "* np.ones((len(perts), 1, 1))")
    out2 = tmp_path / "out2"
    args = common + ["--out", str(out2), "--parent-run", str(par_run), "--source", f"s={tmp_path / 'src'}"]
    assert fc.main(args + ["--groups", "gene"]) == 2
    assert fc.main(args) == 0
    res = json.loads((out2 / "feature_compare.json").read_text())
    assert res["parent"]["features"] == base + ["noise_feat"] and res["parent"]["files"]["noise_feat"]["status"] == "ok"
    assert _row(res, "second_feat")["status"] == "ok"


LEAKY = ("        if not params.get('leak'):\n"
         "            return np.cos(ctx.control_mean)[None, :, None] * np.ones((len(perts), 1, 1))\n"
         "        names, Y = ctx.train_delta()\n"
         "        pos = {p: i for i, p in enumerate(names)}\n"
         "        return np.array([Y[pos[p]] if p in pos else ctx.control_mean for p in perts])[:, :, None]")


def test_a_source_run_is_scored_as_its_own_model_from_its_own_split(dataset, tmp_path):
    """The set row of a --source-run is the run's selected model (a parent feature it dropped stays out), a feature
    is smoke-tested with the params the run recorded for it, and a run from another split is refused."""
    noise = PLUGIN.format(prefix="", name="noise_feat", body=NOISE)
    leaky = PLUGIN.format(prefix="", name="leaky_feat", body=LEAKY)
    dropped = _fake_run(tmp_path / "dropped", ["control_mean", "mean_response", "noise_feat"], {"noise_feat": noise},
                        {"cv_folds": 5})
    leak = _fake_run(tmp_path / "leak", ["control_mean", "mean_response", "is_target", "leaky_feat"],
                     {"leaky_feat": leaky}, {"cv_folds": 5}, params={"leaky_feat": {"leak": True}})
    out = tmp_path / "out"
    common = ["--data", str(dataset), "--fold-seeds", "101,102", "--null-reps", "3"]
    # "parent" as a source name must not collide with the parent's own work directory
    assert fc.main(common + ["--out", str(out), "--source-run", f"parent={dropped}", "--source-run",
                             f"leak={leak}"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    s = _row(res, "(set)", "parent")
    assert s["status"] == "ok" and s["model"] == ["control_mean", "mean_response", "noise_feat"]
    assert s["dropped_parent"] == ["is_target"] and s["n_columns"] == 3 and s["exposure"] == "val1+oof"
    assert _row(res, "noise_feat")["exposure"] == "val1+oof"
    lk = _row(res, "leaky_feat")
    assert lk["status"] == "smoke" and "label leakage" in lk["reason"]
    assert _row(res, "(set)", "leak")["status"] == "error"
    assert "dropped: is_target" in (out / "feature_compare.md").read_text()
    other = _fake_run(tmp_path / "other", ["control_mean", "noise_feat"], {"noise_feat": noise}, {"cv_folds": 5},
                      split_id="split_OTHER")
    assert fc.main(common + ["--out", str(tmp_path / "out2"), "--source-run", f"o={other}"]) == 2


def test_a_source_params_file_is_ignored(dataset, tmp_path):
    """A params file next to a --source would carry training labels past the guard and the literal caps."""
    src = tmp_path / "src"
    _plugin(src, "table_feat", "        t = params.get('t')\n"
                               "        if t is None:\n"
                               "            i = np.arange(len(perts))[:, None]\n"
                               "            return np.sin(ctx.control_mean + i)[:, :, None]\n"
                               "        return np.array([t[p] for p in perts])[:, :, None]")
    names, Y = FeatureContext(dataset).train_delta()
    (src / "params.json").write_text(json.dumps({"table_feat": {"t": dict(zip(names, Y.tolist()))}}))
    out = tmp_path / "out"
    assert fc.main(["--data", str(dataset), "--out", str(out), "--source", f"s={src}", "--fold-seeds", "101",
                    "--null-reps", "0"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    row = _row(res, "table_feat")
    assert row["status"] == "ok" and row["params"] == {}
    assert row["tiers"]["oof"]["metrics"]["pearson_delta"] < 0.99
    assert {"one fold seed: alpha chosen and reported on the same OOF predictions",
            "no null (--null-reps 0, or nothing beyond the parent to permute)"} <= set(row["failed_criteria"])


def test_the_verdict_names_a_null_too_coarse_for_its_family():
    """The step-down needs 999 replicates for a family of any size (updated with the corrected test: the old rule
    was 20m - 1 on a Holm p, whose floor equalled the cutoff); the verdict reads p_fwer, both nulls for a proportional
    row, and the minimum effect."""
    d = {"mean_diff": 1.0, "se_adj": 0.1, "wins_a": 9, "n": 10}
    row = {"exposure": "oof", "tiers": {"oof": {"delta": dict.fromkeys(("pearson_delta", "pearson_delta_nontarget",
                                                                         "mse_top"), d),
                                                "report_deltas": [1.0, 1.0],
                                                "null": {"p": 0.01, "p_holm": 0.06, "p_fwer": 0.06}}}}
    a = argparse.Namespace(null_reps=99, seeds=[1, 2])
    fc.verdict(row, "oof", 6, a)
    assert row["failed_criteria"] == ["null too coarse for a family of 6 (need --null-reps >= 999)"]
    a.null_reps = 999
    fc.verdict(row, "oof", 5, a)
    assert row["failed_criteria"] == ["null p (FWER) > 0.05"]
    row["tiers"]["oof"]["null"]["p_fwer"] = 0.01
    fc.verdict(row, "oof", 5, a)
    assert row["meaningful"] and row["verdict"] == "meaningful (development, OOF only, not held out)"
    a.null_reps = 998  # a family of one has no exception: at 19 replicates its floor 1/20 would equal the cutoff
    fc.verdict(row, "oof", 1, a)
    assert row["failed_criteria"] == ["null too coarse for a family of 1 (need --null-reps >= 999)"]
    a.null_reps = 999
    fc.verdict(row, "oof", 1, a)
    assert row["meaningful"]
    row["proportional"] = True
    fc.verdict(row, "oof", 1, a)
    assert row["failed_criteria"] == ["proportional to a parent column but no perturbation null"]
    row["proportional_in_folds"] = False
    fc.verdict(row, "oof", 1, a)
    assert row["failed_criteria"] == ["proportional to a parent column but no perturbation null (proportional in "
                                      "the full view only)"]
    del row["proportional_in_folds"]
    row["tiers"]["oof"]["null_pert"] = {"p": 0.2, "p_fwer": 0.2}
    fc.verdict(row, "oof", 1, a)
    assert row["failed_criteria"] == ["perturbation null p (FWER) > 0.05"]
    row["tiers"]["oof"]["null_pert"]["p_fwer"] = 0.001
    fc.verdict(row, "oof", 1, a)
    assert row["meaningful"]
    d["mean_diff"] = 0.0015  # above 2 SE_adj but under the minimum effect of interest
    d["se_adj"] = 0.0001
    fc.verdict(row, "oof", 1, a)
    assert row["failed_criteria"] == ["M1 gain not above the minimum effect 0.002"]


def test_the_permutation_of_a_replicate_is_shared_by_every_candidate(dataset, tmp_path, monkeypatch):
    """(e) The joint null keeps the dependence between candidates: replicate b uses the same gene permutation and
    the same perturbation permutation for every row of the call, functions of (null seed, b) alone."""
    _plugin(tmp_path / "src", "noise_feat", NOISE)
    _plugin(tmp_path / "src", "second_feat", "        return np.cos(3.0 * ctx.control_mean)[None, :, None] "
                                             "* np.ones((len(perts), 1, 1))")
    _plugin(tmp_path / "src", "prop_feat", PROP.format(parent="mean_response"))
    gene_seeds, pert_seeds, g0, p0 = [], [], fc.gene_permutation, fc.pert_permutation

    def spy_gene(cm, n_bins, seed):
        gene_seeds.append(seed)
        return g0(cm, n_bins, seed)

    def spy_pert(bins, seed):
        pert_seeds.append(seed)
        return p0(bins, seed)

    monkeypatch.setattr(fc, "gene_permutation", spy_gene)
    monkeypatch.setattr(fc, "pert_permutation", spy_pert)
    out = tmp_path / "out"
    assert fc.main(["--data", str(dataset), "--out", str(out), "--source", f"s={tmp_path / 'src'}",
                    "--fold-seeds", "101,102", "--null-reps", "5", "--null-seed", "40"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    rows = {r["feature"]: r for r in res["rows"]}
    assert rows["prop_feat"]["proportional"] and rows["prop_feat"]["parent_column"] == "mean_response"
    assert not rows["noise_feat"]["proportional"] and not rows["second_feat"]["proportional"]
    # four gene nulls (three add-one rows and the set row), one perturbation null, each the seeds 40..44 in order
    assert gene_seeds == [40, 41, 42, 43, 44] * 4 and pert_seeds == [40, 41, 42, 43, 44]
    assert len(rows["prop_feat"]["tiers"]["oof"]["null_pert"]["gains"]) == 5
    assert all(len(r["tiers"]["oof"]["null"]["gains"]) == 5 for r in rows.values())


def test_fast_null_equals_the_refit_from_scratch(dataset, tmp_path, monkeypatch):
    """NullEngine computes only what a gene permutation changes; its replicate gains must equal a full refit. The
    perturbation null of a proportional candidate (nn_prop, control_mean times a scalar) is checked the same way
    against score() on the candidate rebuilt from the permuted scalars (pert_parts)."""
    src = tmp_path / "src"
    src.mkdir()
    _plugin(src, "nn_std", "return np.broadcast_to(ctx.control_std[None, :, None], (len(perts), ctx.n_genes, 1)).copy()")
    _plugin(src, "nn_prop", PROP.format(parent="control_mean"))
    _plugin(src, "nn_lab", """\
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            out[i, :, 0] = np.abs(d).mean(axis=0)
        return out""")
    got = {}
    for fast in (True, False):
        monkeypatch.setattr(fc, "FAST_NULL", fast)
        out = tmp_path / f"out_{fast}"
        assert fc.main(["--data", str(dataset), "--out", str(out), "--source", f"s={src}", "--fold-seeds",
                        "101,102", "--null-reps", "4", "--with-val1"]) == 0
        rows = json.loads((out / "feature_compare.json").read_text())["rows"]
        got[fast] = {(r["source"], r["feature"], r["kind"], t): r["tiers"][t]["null"]
                     for r in rows if r["status"] == "ok" for t in r["tiers"]}
        got[fast].update({(r["source"], r["feature"], r["kind"], "pert"): r["tiers"]["oof"]["null_pert"]
                          for r in rows if r["status"] == "ok" and r["tiers"]["oof"].get("null_pert")})
    assert set(got[True]) == set(got[False]) and len(got[True]) >= 7
    assert ("s", "nn_prop", "add_one", "pert") in got[True]
    for key, slow in got[False].items():
        fast = got[True][key]
        assert fast["reps"] == slow["reps"] == 4
        for field in ("mean", "sd", "p95", "excess"):
            assert abs(fast[field] - slow[field]) < 1e-8, (key, field, fast[field], slow[field])
        assert np.allclose(fast["gains"], slow["gains"], atol=1e-8) and fast["p"] == slow["p"]
