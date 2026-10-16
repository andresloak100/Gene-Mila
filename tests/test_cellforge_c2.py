"""docs/comparison/cellforge_c2: the features we translated from CellForge's design ideas (arm A5-C2 of
docs/FEATURE_COMPARISON_PROTOCOL.md). Every file passes the plugin guard and the literal caps, smoke-tests on the
synthetic single-target bundle and on a pair bundle, and the directory scores as a --source of
tools/feature_compare.py. The pair-interaction term is zero on a bundle without pairs by construction, so there the
tool rejects it as constant; on the pair bundle every row is ok, but under the gene-grouped folds the tool uses there
the term is zero on every predicted row (a predicted pair always has a single hidden), which the last test records."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import feature_compare as fc  # noqa: E402
from genemila.guard import check_plugin_source  # noqa: E402
from task_package.literal import literal_check  # noqa: E402
from test_norman_lab import make_pair_bundle  # noqa: E402

PLUGINS = ROOT / "docs" / "comparison" / "cellforge_c2"
FILES = sorted(p.stem for p in PLUGINS.glob("cf_*.py"))
PAIR_ONLY = {"cf_pair_interaction"}


@pytest.fixture(scope="module")
def pair_bundle(tmp_path_factory):
    """make_pair_bundle plus the four knowledge files the real bundles carry, built from gene names only (seeded), so
    the knowledge-reading features have something to read; the verdicts do not matter here, only that they run."""
    bundle = make_pair_bundle(tmp_path_factory.mktemp("pair") / "pair")
    genes = [str(g) for g in np.load(bundle / "public.npz")["genes"]]
    rng = np.random.default_rng(0)
    tfs = genes[:24]
    k = bundle / "knowledge"
    (k / "gene_sets.json").write_text(json.dumps({f"SET_{j}": genes[j * 8:(j + 1) * 8 + 3] for j in range(10)}))
    (k / "prior_network.json").write_text(json.dumps(
        [[t, genes[int(i)], float(rng.choice([-1, 1]))] for t in tfs for i in rng.choice(80, 6, replace=False)]))
    (k / "ppi_network.json").write_text(json.dumps(
        [[genes[int(a)], genes[int(b)], 0.9] for a, b in rng.integers(0, 80, (120, 2)) if a != b]))
    (k / "transcription_factors.json").write_text(json.dumps(tfs))
    return bundle


def test_four_files_pass_the_guard_and_the_literal_caps(dataset, pair_bundle):
    assert len(FILES) == 4 and all(f.startswith("cf_") for f in FILES)
    names, pair_ids = set(), set()
    for b in (dataset, pair_bundle):
        d = fc.make_data(b)
        names |= set(d.names)
        pair_ids |= set(d.pair_ids)
    for f in FILES:
        src = (PLUGINS / f"{f}.py").read_text()
        assert check_plugin_source(src, f)["class_name"]
        lit = literal_check(src, pair_ids, names)
        assert lit["ok"], (f, lit["problems"])
        assert "CellForge" in src and "ours" in src  # the docstring cites the idea and owns the implementation


@pytest.mark.parametrize("feature", FILES)
@pytest.mark.parametrize("which", ["single", "pair"])
def test_smoke_on_both_bundles(feature, which, dataset, pair_bundle, tmp_path):
    bundle = dataset if which == "single" else pair_bundle
    r = subprocess.run([sys.executable, "-m", "genemila.pipeline", "smoke", "--feature", feature, "--public",
                        str(bundle), "--plugins", str(PLUGINS), "--out", str(tmp_path)],
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    res = json.loads((tmp_path / "smoke.json").read_text())
    if which == "single" and feature in PAIR_ONLY:
        assert res["status"] == "failed" and res["problems"] == ["feature is constant across all rows (no information)"]
    else:
        assert res["status"] == "ok", (res["problems"], r.stderr[-500:])


def _rows(bundle, out):
    assert fc.main(["--data", str(bundle), "--out", str(out), "--source", f"A5_C2={PLUGINS}",
                    "--fold-seeds", "101,102", "--null-reps", "9"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    return res, {r["feature"]: r for r in res["rows"] if r["source"] == "A5_C2"}


def test_feature_compare_on_the_pair_bundle_scores_every_row(pair_bundle, tmp_path):
    res, rows = _rows(pair_bundle, tmp_path / "out")
    assert {r["status"] for r in rows.values()} == {"ok"}, {f: r["reason"] for f, r in rows.items()}
    assert rows["(set)"]["features"] == FILES and res["settings"]["groups"] == "gene"
    assert rows["cf_grn_propagation"]["label_dependent"] is False  # knowledge only, no training label read
    assert all(rows[f]["label_dependent"] for f in FILES if f != "cf_grn_propagation")
    assert rows["cf_pair_interaction"]["n_columns"] == 2


def test_feature_compare_on_the_single_bundle_rejects_only_the_pair_term(dataset, tmp_path):
    _, rows = _rows(dataset, tmp_path / "out")
    assert {f: r["status"] for f, r in rows.items()} == {**{f: "ok" for f in FILES}, "(set)": "ok",
                                                         "cf_pair_interaction": "smoke"}
    assert "constant" in rows["cf_pair_interaction"]["reason"]
    assert rows["(set)"]["features"] == [f for f in FILES if f not in PAIR_ONLY]


def test_pair_term_is_zero_on_every_gene_grouped_predicted_row(pair_bundle):
    """What the README says of the OOF tier: cv_folds_of hides a single of every predicted pair, so the interaction
    term is zero on the predicted rows of every fold while the view's training rows and the full-context eval rows
    (seen-2 pairs, both singles in training) carry it."""
    res = fc.compute_blocks(pair_bundle, PLUGINS, ["cf_pair_interaction"], {}, [101, 102], 5, "gene", True)
    assert not res["errors"]
    assert (np.abs(res["eval"]["cf_pair_interaction"]).max(axis=(1, 2)) > 0).any()  # the seen-2 held-out pairs
    for folds in res["folds"].values():
        for fd in folds:
            b, n = fd["blocks"]["cf_pair_interaction"], len(fd["rows"]) - len(fd["predict"])
            assert np.abs(b[:n]).max() > 0 and np.abs(b[n:]).max() == 0
