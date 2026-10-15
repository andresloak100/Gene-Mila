"""tools/feature_compare.py: the feature-level comparison of research systems. Its out-of-fold predictions are the
lab's cross_validate ones, a planted feature is meaningful and noise is not, foreign files are rejected before they
run, the gene null permutes within bins of control expression, and the visible validation labels are read only on
request, in one function."""

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


# ------------------------------------------------------------------ a full run on the synthetic bundle
@pytest.fixture(scope="module")
def main_run(tmp_path_factory, dataset):
    """One command-line run with --with-val1: a planted feature, a noise feature and four files that must be
    rejected (guard, literal caps, collision with a built-in, a wrong shape)."""
    tmp = tmp_path_factory.mktemp("fc_main")
    bundle = _planted_bundle(dataset, tmp / "bundle")
    _plugin(tmp / "planted", "planted_feat", PLANTED)
    _plugin(tmp / "noise", "noise_feat", NOISE)
    bad = tmp / "bad"
    marker = tmp / "executed_marker"
    _plugin(bad, "guard_feat", NOISE, prefix=f"import os\nos.makedirs({str(marker)!r})\n")
    _plugin(bad, "literal_feat", "        return np.zeros((len(perts), ctx.n_genes, 1)) + sum(W)",
            prefix="W = [" + ", ".join(str(i) for i in range(30)) + "]\n")
    _plugin(bad, "mean_response", NOISE)
    _plugin(bad, "shape_feat", "        return np.ones((len(perts), 3))")
    _plugin(bad, "dep_feat", "        return ctx.feature('guard_feat', perts)")
    out = tmp / "out"
    r = subprocess.run([sys.executable, str(TOOL), "--data", str(bundle), "--out", str(out),
                        "--source", f"planted={tmp / 'planted'}", "--source", f"noise={tmp / 'noise'}",
                        "--source", f"bad={bad}", "--fold-seeds", "101,102", "--null-reps", "39", "--with-val1"],
                       capture_output=True, text=True, cwd=tmp, timeout=600)
    assert r.returncode == 0, r.stderr
    return {"json": json.loads((out / "feature_compare.json").read_text()),
            "md": (out / "feature_compare.md").read_text(), "marker": marker}


def _row(res, feature, source=None):
    return next(r for r in res["rows"] if r["feature"] == feature and (source is None or r["source"] == source))


def test_a_planted_feature_is_meaningful_with_the_smallest_null_p(main_run):
    res = main_run["json"]
    row = _row(res, "planted_feat")
    assert row["status"] == "ok" and row["meaningful"], row.get("failed_criteria")
    assert res["settings"]["families"] == {"add_one": 2, "set": 2}
    for t in ("oof", "val1"):
        assert row["tiers"][t]["null"]["p"] == pytest.approx(1 / 40)
    assert row["tiers"]["val1"]["null"]["p_holm"] == pytest.approx(2 / 40)
    assert all(d > 0 for d in row["tiers"]["oof"]["report_deltas"]) and len(row["tiers"]["oof"]["report_deltas"]) == 2
    assert row["tiers"]["oof"]["delta"]["pearson_delta"]["overlap_ratio"] == pytest.approx(1.0)  # single targets
    assert row["label_dependent"] is False and _row(res, "(set)", "planted")["meaningful"]


def test_a_noise_feature_is_not_meaningful(main_run):
    row = _row(main_run["json"], "noise_feat")
    assert row["status"] == "ok" and not row["meaningful"] and row["failed_criteria"]


def test_rejected_files_are_rows_and_never_run(main_run):
    res = main_run["json"]
    want = {"guard_feat": "guard", "literal_feat": "literal", "mean_response": "collision", "shape_feat": "smoke",
            "dep_feat": "error"}
    assert {f: _row(res, f, "bad")["status"] for f in want} == want
    assert "guard_feat" in _row(res, "dep_feat")["reason"]  # its dependency was rejected, so it cannot compute
    assert "import of 'os'" in _row(res, "guard_feat")["reason"]
    assert "30 elements" in _row(res, "literal_feat")["reason"]
    assert "shape" in _row(res, "shape_feat")["reason"]
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
    assert {"mean", "sd", "p95", "p", "p_holm", "excess", "reps"} <= set(t["null"])
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
    assert s["status"] == "ok" and s["features"] == ["noise_feat", "second_feat"] and s["n_columns"] == 2
    assert fc.OOF_CAVEAT in (out / "feature_compare.md").read_text()


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
def _fake_run(d: Path, features: list[str], plugins: dict[str, str], hp: dict) -> Path:
    """A minimal finished run: lab.db with the selected experiment, and feature_store/."""
    (d / "feature_store").mkdir(parents=True)
    for name, text in plugins.items():
        (d / "feature_store" / f"{name}.py").write_text(text)
    c = sqlite3.connect(d / "lab.db")
    c.execute("CREATE TABLE runs (run_id TEXT, split_id TEXT, dataset TEXT, base_commit TEXT, config_json TEXT)")
    c.execute("CREATE TABLE experiments (experiment_id TEXT, status TEXT, kind TEXT, primary_score REAL, "
              "finished_at REAL, feature_set_json TEXT, new_feature TEXT, feature_params_json TEXT, "
              "hyperparameters_json TEXT, delta_from_parent REAL)")
    c.execute("INSERT INTO runs VALUES ('r', NULL, 'synthetic', '', '{}')")
    c.execute("INSERT INTO experiments VALUES ('EXP_1', 'completed', 'new_feature', 0.5, 1, ?, NULL, '{}', ?, NULL)",
              (json.dumps(features), json.dumps(hp)))
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
