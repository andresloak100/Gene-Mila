import numpy as np

from genemila.benchmark import comparable, reference
from genemila.data.bundle import LabelSet


def _setup(dataset, part="val1"):
    z = np.load(dataset / "public.npz", allow_pickle=False)
    lab = LabelSet.load(dataset / "private" / f"{part}.npz")
    ref = reference.load(dataset, part)
    return z["control_cells"].astype(np.float64).mean(0), z["train_means"].astype(np.float64).mean(0), lab, ref


def test_bh_adjustment():
    p = np.array([0.01, 0.04, 0.03, 0.2])
    # sorted 0.01,0.03,0.04,0.2 -> 0.04,0.0533,0.0533,0.2
    assert np.allclose(reference._bh(p), [0.04, 0.16 / 3, 0.16 / 3, 0.2])


def test_reference_saved_with_bundle(dataset):
    assert (dataset / "private" / "val1_de.npz").exists() and (dataset / "private" / "val2_de.npz").exists()
    ctrl, _, lab, ref = _setup(dataset)
    assert ref["perts"] == lab.perts
    assert ref["top_de"].shape == (len(lab.perts), reference.TOP_K)
    assert ref["de"].shape == ref["direction"].shape == (len(lab.perts), lab.means.shape[1])
    assert 0 < ref["de"].mean() < 0.5  # some, not all, genes respond
    # true DE genes move in the direction of the true mean shift
    shift = np.sign(lab.means - ctrl)[ref["de"]]
    assert np.mean(shift == ref["direction"][ref["de"]]) > 0.9


def test_truth_beats_baselines_on_comparable_metrics(dataset):
    ctrl, mean_resp, lab, ref = _setup(dataset)
    truth = comparable.score(lab.means, lab.means, lab.perts, ref, ctrl)
    base = comparable.score(np.tile(mean_resp, (len(lab.perts), 1)), lab.means, lab.perts, ref, ctrl)
    unchanged = comparable.score(np.tile(ctrl, (len(lab.perts), 1)), lab.means, lab.perts, ref, ctrl)
    assert truth["cellforge_mse"] == 0 and truth["cellforge_pcc"] == 1 and truth["cellforge_r2_de"] == 1
    assert base["cellforge_mse_de"] > 0 and base["cellforge_pcc_de"] < 1
    assert truth["vcworld_de_auprc"] > base["vcworld_de_auprc"]
    assert truth["vcworld_dir_accuracy"] > 0.9 and truth["vcworld_dir_accuracy"] > base["vcworld_dir_accuracy"]
    assert unchanged["vcworld_de_recall"] < 0.05  # predicting no change finds (almost) no DE genes
    assert truth["vcworld_n_de_pairs"] == int(ref["de"].sum())


def test_order_independent_and_partial(dataset):
    ctrl, mean_resp, lab, ref = _setup(dataset)
    pred = lab.means + 0.05
    a = comparable.score(pred, lab.means, lab.perts, ref, ctrl)
    order = np.arange(len(lab.perts))[::-1]
    b = comparable.score(pred[order], lab.means[order], [lab.perts[i] for i in order], ref, ctrl)
    assert all(np.isclose(a[k], b[k]) for k in a if a[k] is not None)
    assert comparable.score(pred, lab.means, lab.perts, None, ctrl) == {}


def test_every_experiment_and_report_get_comparable_metrics(lab_factory):
    from genemila.report import finalize
    lab = lab_factory(final__top_k=1)
    lab.record_analytic_baselines()
    rec = lab.db.query("SELECT * FROM experiments WHERE kind='baseline'")[0]
    assert "cellforge_pcc_de" in rec["val_metrics_json"] and "vcworld_de_auprc" in rec["val_metrics_json"]
    s = finalize(lab, query=True)
    row = s["generalization_query_only"][0]
    assert "cellforge_mse" in row["comparable"]["val2"] and "vcworld_dir_f1" in row["comparable"]["val1"]
    md = (lab.run_dir / "summary.md").read_text()
    assert "## CELLFORGE METRICS" in md and "## VCWORLD METRICS" in md
    # a plain re-summary keeps the sealed-set rows from stored scores without a new oracle query
    n_queries = len(lab.oracle.queries)
    s2 = finalize(lab, query=False)
    assert [r["experiment_id"] for r in s2["generalization_query_only"]] == \
        [r["experiment_id"] for r in s["generalization_query_only"]]
    assert len(lab.oracle.queries) == n_queries
    assert "## CELLFORGE METRICS" in (lab.run_dir / "summary.md").read_text()
    assert "single-gene targets" in lab.data_summary()
