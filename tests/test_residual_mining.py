"""tools/residual_mining.py: training-only residual mining. Its out-of-fold per-perturbation scores are the lab's
cross_validate predictions scored by the evaluator, the similarity measures are bounded and read the bundle's own
knowledge files, a per-gene property shows up as a correlated residual, the source never names the held-out labels or
the oracle, and a directory that is not a bundle is refused."""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import residual_mining as rm  # noqa: E402
from genemila.benchmark.evaluator import evaluate  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.pipeline import cross_validate  # noqa: E402
from test_norman_lab import make_pair_bundle  # noqa: E402

TOOL = ROOT / "tools" / "residual_mining.py"
BUILTINS = ["control_mean", "mean_response", "is_target"]


# ------------------------------------------------------------------ hygiene
def test_source_never_names_the_held_out_labels_the_split_file_or_the_oracle():
    src = TOOL.read_text()
    for word in ("val2", "splits.json", "QueryOracle", "private", "open_run", "query_only", "LabelSet"):
        assert word not in src, word


def test_a_directory_that_is_not_a_bundle_is_refused(dataset, tmp_path):
    out = tmp_path / "out"
    assert rm.main(["--data", str(tmp_path), "--out", str(out)]) == 2
    half = tmp_path / "half"
    half.mkdir()
    shutil.copyfile(dataset / "public.npz", half / "public.npz")  # no knowledge/targets.json
    assert rm.main(["--data", str(half), "--out", str(out)]) == 2
    assert rm.main(["--data", str(dataset), "--out", str(out), "--k", "1"]) == 2
    assert not out.exists()


# ------------------------------------------------------------------ the synthetic bundle, with extra knowledge
@pytest.fixture(scope="module")
def mined(tmp_path_factory, dataset):
    """One run on a copy of the synthetic bundle with three knowledge files added: a STRING-format ppi_network built
    from the prior network, a gene_annotation table (one column a monotone function of the control mean, one with
    missing values) and an external screen with a row for the first training perturbation's target."""
    tmp = tmp_path_factory.mktemp("rm")
    bundle = tmp / "bundle"
    shutil.copytree(dataset, bundle)
    k = bundle / "knowledge"
    edges = json.loads((k / "prior_network.json").read_text())
    (k / "ppi_network.json").write_text(json.dumps([[a, b, 0.9] for a, b, _ in edges]))
    ctx = FeatureContext(bundle)
    rows = {g: [float(2 * ctx.control_mean[i] + 1), None if i % 5 == 0 else float(np.sin(i))]
            for i, g in enumerate(ctx.genes)}
    (k / "gene_annotation.json").write_text(json.dumps({"description": "toy", "columns": ["cm_rank", "noisy"],
                                                        "genes": rows}))
    target = ctx.target_genes(ctx.train_perts[0])[0]
    (k / "toy_screen.json").write_text(json.dumps({"description": "toy screen", "perts": {target: {"delta": [0.0]}}}))
    out = tmp / "out"
    assert rm.main(["--data", str(bundle), "--out", str(out), "--fold-seeds", "101", "--top", "5"]) == 0
    return {"json": json.loads((out / "residual_mining.json").read_text()),
            "md": (out / "residual_mining.md").read_text(), "bundle": bundle, "screened": ctx.train_perts[0]}


def test_outputs_exist_with_the_right_keys_and_the_caveats(mined):
    r, md = mined["json"], mined["md"]
    assert {"tool", "header", "data", "split_id", "settings", "caveats", "parent", "per_perturbation",
            "similarity_correlation", "per_gene", "structure", "wall_s"} <= set(r)
    s = r["settings"]
    assert s["labels_read"] == ["training labels (public.npz)"] and s["honest"] is False and s["groups"] is None
    assert s["measures_available"] == {"gene_sets": True, "ppi": True, "coexpr": True}
    assert s["screens"] == ["toy_screen"]
    assert r["parent"]["features"] == BUILTINS and r["parent"]["n_columns"] == 3
    rows = r["per_perturbation"]
    assert [x["rank"] for x in rows] == list(range(1, len(rows) + 1))
    assert [x["oof_pearson_delta"] for x in rows] == sorted(x["oof_pearson_delta"] for x in rows)
    assert {"pert", "category", "oof_pearson_delta", "oof_pearson_delta_nontarget", "n_targets", "sim_gene_sets",
            "nearest_gene_sets", "sim_ppi", "sim_coexpr", "nearest_coexpr", "n_gene_sets", "n_ppi_partners",
            "screen_rows"} <= set(rows[0])
    assert all(x["category"] is None for x in rows)  # no pairs in this bundle
    assert set(r["similarity_correlation"]) == set(rm.MEASURES)
    assert {"n_genes", "annotation_columns", "correlations", "top"} <= set(r["per_gene"])
    assert len(r["per_gene"]["top"]) == 5 and "msr" in r["per_gene"]["top"][0]
    st = r["structure"]
    assert len(st["share"]) == len(st["null_share"]) == 5 and 0 < sum(st["share"]) <= 1 + 1e-9
    assert st["cumulative"] == pytest.approx(np.cumsum(st["share"]).tolist()) and len(st["components"]) == 2
    assert "Hypothesis generation on training folds only" in md and "tools/feature_compare.py" in md
    assert "## 1. The 5 worst training perturbations out of fold" in md
    assert "## 2. The 5 genes with the largest mean squared OOF residual" in md and "## 3. Residual structure" in md
    assert any("one fold seed" in c for c in r["caveats"]) and "never evidence" in " ".join(r["caveats"])


def test_oof_pearson_delta_equals_cross_validate_scored_by_the_evaluator(mined):
    r = mined["json"]
    alpha = r["settings"]["reports"][0]["alpha"]
    ctx = FeatureContext(mined["bundle"])
    names, Y = ctx.train_delta()
    ref = cross_validate(ctx, BUILTINS, {}, "ridge", [alpha], 0, 5, 101, {}, None, None, {}, {}, None)
    ev = evaluate(ref[0] + ctx.control_mean, Y + ctx.control_mean, ctx.control_mean, names)["per_perturbation"]
    for row in r["per_perturbation"]:
        assert row["oof_pearson_delta"] == pytest.approx(ev[row["pert"]]["pearson_delta"], abs=1e-5)
    assert r["parent"]["metrics"]["pearson_delta"] == pytest.approx(
        np.mean([v["pearson_delta"] for v in ev.values()]), abs=1e-5)


def test_similarity_columns_are_bounded_and_read_the_bundle_s_knowledge(mined):
    r, ctx = mined["json"], FeatureContext(mined["bundle"])
    rows = {x["pert"]: x for x in r["per_perturbation"]}
    for x in rows.values():
        for m in rm.MEASURES:
            assert 0.0 <= x[f"sim_{m}"] <= 1.0 and x[f"nearest_{m}"] != x["pert"]
            assert (x[f"nearest_{m}"] is None) == (x[f"sim_{m}"] == 0.0)
        assert set(x["screen_rows"]) == {"toy_screen"}
    assert rows[mined["screened"]]["screen_rows"]["toy_screen"] is True
    assert sum(x["screen_rows"]["toy_screen"] for x in rows.values()) == 1
    # co-expression by hand: the largest |r| between a perturbation's target and any other training target
    train = ctx.train_perts
    idx = {p: ctx.gene_index[ctx.target_genes(p)[0]] for p in train}
    for p in train[:3]:
        others = [idx[q] for q in train if q != p]
        assert rows[p]["sim_coexpr"] == pytest.approx(np.abs(ctx.gene_corr[idx[p], others]).max())
    # gene sets by hand: Jaccard of the memberships of the two targets
    sets = ctx.knowledge("gene_sets")
    member = {p: {n for n, gs in sets.items() if ctx.target_genes(p)[0] in gs} for p in train}
    for p in train:
        want = max((len(member[p] & member[q]) / len(member[p] | member[q]) if member[p] | member[q] else 0.0)
                   for q in train if q != p)
        assert rows[p]["sim_gene_sets"] == pytest.approx(want) and rows[p]["n_gene_sets"] == len(member[p])
    for c in r["similarity_correlation"].values():
        assert c["n"] == len(train) and -1 <= c["rho"] <= 1


def test_a_per_gene_property_shows_up_in_the_residual_correlations(mined):
    g = mined["json"]["per_gene"]
    corr = g["correlations"]
    assert g["annotation_columns"] == ["cm_rank", "noisy"]
    assert set(corr) == {"control_mean", "control_std", "gene_annotation.cm_rank", "gene_annotation.noisy"}
    # the same ranks as the control mean give the same Spearman rho; null values are left out
    assert corr["gene_annotation.cm_rank"]["rho"] == pytest.approx(corr["control_mean"]["rho"])
    assert corr["control_mean"]["n"] == g["n_genes"] and corr["gene_annotation.noisy"]["n"] == g["n_genes"] - 24
    assert "gene_annotation.noisy" in mined["md"] and "cm_rank" in mined["md"]
    top = g["top"]
    assert [x["msr"] for x in top] == sorted((x["msr"] for x in top), reverse=True)
    assert sum(x["share"] for x in top) < 1.0


# ------------------------------------------------------------------ a bundle with pairs
def test_pair_bundle_groups_by_gene_categorises_and_marks_absent_knowledge(tmp_path):
    bundle = make_pair_bundle(tmp_path / "pair")
    out = tmp_path / "out"
    assert rm.main(["--data", str(bundle), "--out", str(out), "--fold-seeds", "101,102", "--top", "3"]) == 0
    r = json.loads((out / "residual_mining.json").read_text())
    s = r["settings"]
    assert s["groups"] == "gene" and s["honest"] is True and len(s["reports"]) == 2
    assert r["parent"]["features"] == BUILTINS + ["additive_response"]
    assert s["measures_available"] == {"gene_sets": False, "ppi": False, "coexpr": True}
    assert r["similarity_correlation"]["gene_sets"] is None and "coexpr" in r["similarity_correlation"]
    ctx = FeatureContext(bundle)
    genes_of = {p: set(ctx.target_genes(p)) for p in ctx.train_perts}
    cats = {x["pert"]: x["category"] for x in r["per_perturbation"]}
    assert set(cats.values()) <= {"single", "pair_seen0", "pair_seen1", "pair_seen2"} and "single" in cats.values()
    for x in r["per_perturbation"]:
        assert x["sim_gene_sets"] is None and x["sim_ppi"] is None and 0.0 <= x["sim_coexpr"] <= 1.0
        assert x["n_targets"] == len(genes_of[x["pert"]]) and x["screen_rows"] == {}
        if any(genes_of[x["pert"]] & genes_of[q] for q in ctx.train_perts if q != x["pert"]):
            # a shared target gene is its own co-expression partner (|r| = 1), so the nearest shares a gene
            assert x["sim_coexpr"] == pytest.approx(1.0) and genes_of[x["nearest_coexpr"]] & genes_of[x["pert"]]
    assert "file absent" in (out / "residual_mining.md").read_text()
