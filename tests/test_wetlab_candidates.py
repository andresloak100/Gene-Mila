"""tools/wetlab_candidates.py: the target the two frozen models disagree on ranks first, bundle targets are refused,
negatives are drawn where the models agree, the power number is a hand computation, the deposit's hashes reproduce."""
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from genemila.frozen import export_ensemble, sha256  # noqa: E402
from genemila.pipeline import run  # noqa: E402
from tools import wetlab_candidates as wc  # noqa: E402

# 30 genes, so each expression decile holds three: D, E and F share one (control means 4, 5, 6), G and H the next.
GENES = ["A", "B", "C", "D", "E", "F", "G", "H"] + [f"X{i}" for i in range(22)]
PLUGIN = '''import numpy as np
from genemila.features.api import Feature, register
PATHWAY = {"A": ["B"], "B": ["A"], "E": ["F", "G"]}
@register
class PathwayHint(Feature):
    name = "pathway_hint"
    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            for t in ctx.target_genes(p):
                for g in PATHWAY.get(t, ()):
                    out[i, ctx.gene_index[g], 0] = 1.0
        return out
'''


def write_json(path, value):
    path.write_text(json.dumps(value))


def make_export(tmp_path: Path, name: str, experiment: str, features: list[str], plugin: str | None) -> tuple[Path, str]:
    """A run directory fitted on the fixture bundle (genes A to H; perturbations A1, B1 in training, C1 held out),
    pinned by a receipt and exported. Returns the package and its manifest sha256."""
    run_dir = tmp_path / f"run-{name}"
    public = run_dir / "public_data"
    (public / "knowledge").mkdir(parents=True)
    plugins = run_dir / "feature_store"
    plugins.mkdir()
    rng = np.random.default_rng(7)
    n = len(GENES)
    control = rng.normal(loc=np.arange(1, n + 1, dtype=float), scale=0.05 + 0.01 * np.arange(n), size=(30, n))
    delta = np.zeros((2, n))
    delta[0, [0, 1]] = [-0.5, 0.4]   # A1 lowers A and raises its pathway partner B
    delta[1, [1, 0]] = [-0.5, 0.4]   # B1 the reverse
    np.savez_compressed(public / "public.npz", genes=np.array(GENES), control_cells=control,
                        perts=np.array(["A1", "B1", "C1"]), train_perts=np.array(["A1", "B1"]),
                        train_means=control.mean(0) + delta)
    write_json(public / "knowledge" / "targets.json", {"A1": ["A"], "B1": ["B"], "C1": ["C"]})
    if plugin:
        (plugins / "pathway_hint.py").write_text(plugin)
    spec = {"experiment_id": experiment, "feature_set": features, "model_type": "ridge",
            "hyperparameters": {"alpha_grid": [.3, 3., 30.]}, "seed": 0}
    artifact = run_dir / "artifacts" / experiment
    run(spec, public, plugins, artifact)
    write_json(artifact / "run_spec.json", spec)
    files = [artifact / "models.pkl", artifact / "run_spec.json", *public.rglob("*.npz"), *public.rglob("*.json"),
             *plugins.glob("*.py")]
    receipt = tmp_path / f"pin-{name}.json"
    write_json(receipt, {"frozen_members": [{
        "run_directory": str(run_dir), "experiment_id": experiment, "selected_alpha": 3., "features": features,
        "weight": 1., "files_sha256": {str(p.relative_to(run_dir)): sha256(p) for p in files}}]})
    package = tmp_path / f"export-{name}"
    export_ensemble(receipt, sha256(receipt), [(experiment, 3.)], package, trust_pickle=True)
    return package, sha256(package / "manifest.json")


@pytest.fixture
def exports(tmp_path):
    parent, parent_sha = make_export(tmp_path, "parent", "EXP_0001", ["mean_response", "is_target"], None)
    feature, feature_sha = make_export(tmp_path, "feature", "EXP_0002", ["mean_response", "is_target", "pathway_hint"],
                                       PLUGIN)
    targets = tmp_path / "candidates.txt"
    targets.write_text("D\nE\nF\nG\nH\nX0\nX1\n")
    return {"parent": parent, "parent_sha": parent_sha, "feature": feature, "feature_sha": feature_sha,
            "candidates": targets, "tmp": tmp_path}


def argv(e, out, *extra):
    return ["--feature", str(e["feature"]), "--feature-manifest-sha256", e["feature_sha"], "--parent", str(e["parent"]),
            "--parent-manifest-sha256", e["parent_sha"], "--candidates", str(e["candidates"]), "--seed", "public seed",
            "--k", "1", "--m", "2", "--top-n", "3", "--min-effect", "0.001", "--agree-tolerance", "0.5", "--cells", "50",
            "--out", str(out), *extra]


def test_the_target_the_feature_acts_on_ranks_first_with_its_pathway_genes(exports, capsys):
    out = exports["tmp"] / "pkg"
    assert wc.main(argv(exports, out)) == 0
    p = json.loads((out / "candidates.json").read_text())
    assert [r["symbol"] for r in p["ranking"]][0] == "E"
    assert [c["symbol"] for c in p["candidates"]] == ["E"]
    top = p["candidates"][0]
    assert {g["gene"] for g in top["genes"][:2]} == {"F", "G"}   # the plugin's pathway of E
    for g in top["genes"][:2]:
        assert g["delta_feature"] > g["delta_parent"] and g["difference"] == g["delta_feature"] - g["delta_parent"]
        assert g["sign_feature"] in ("up", "down", "none") and g["cells_to_detect_difference"] >= 1
    assert top["disagreement"]["l2"] > max(r["l2"] for r in p["ranking"][1:])
    # The disagreement statistics are what the predictions say, recomputed here from the deposited arrays.
    with np.load(out / "predictions" / "feature" / "predictions.npz", allow_pickle=False) as zf, \
            np.load(out / "predictions" / "parent" / "predictions.npz", allow_pickle=False) as zp:
        assert zf["perts"].tolist() == zp["perts"].tolist() == ["D", "E", "F", "G", "H", "X0", "X1"]
        f, pr = zf["delta"][1].astype(np.float64), zp["delta"][1].astype(np.float64)
    s = (np.abs(f) >= 0.001) | (np.abs(pr) >= 0.001)
    assert top["disagreement"]["l2"] == pytest.approx(float(np.sqrt(np.sum((f[s] - pr[s]) ** 2))))
    assert top["disagreement"]["pearson"] == pytest.approx(float(np.corrcoef(f, pr)[0, 1]))
    assert p["models"]["feature"]["predictions_sha256"] == sha256(out / "predictions" / "feature" / "predictions.npz")
    assert p["models"]["parent"]["manifest_sha256"] == exports["parent_sha"]
    assert p["universe"]["protected_targets"] == {"export context": 3}
    text = (out / "candidates.md").read_text()
    assert "| 1 | E |" in text and "### E: top 3 genes" in text
    assert "no expression response of any candidate cohort was read" in text.lower()
    assert sha256(out / "candidates.json") in capsys.readouterr().out
    assert sha256(out / "candidates.json") in text


def test_a_bundle_target_or_an_excluded_target_is_refused(exports):
    bad = exports["tmp"] / "bad.txt"
    bad.write_text("C\nD\nE\n")   # C is the held-out perturbation C1's target: validation or test, still refused
    e = {**exports, "candidates": bad}
    with pytest.raises(SystemExit) as ex:
        wc.main(argv(e, exports["tmp"] / "refused"))
    assert ex.value.code == 2 and not (exports["tmp"] / "refused").exists()
    reasons = wc.refusals(["A", "C", "Z"], GENES, {"export context": {"A", "B", "C"}})
    assert reasons == {"A": ["export context target"], "C": ["export context target"],
                       "Z": ["outside the frozen gene universe"]}
    other = exports["tmp"] / "norman_targets.json"
    write_json(other, {"D_E": ["D", "E"]})
    with pytest.raises(SystemExit):
        wc.main(argv(exports, exports["tmp"] / "refused2", "--exclude", f"norman={other}"))
    assert not (exports["tmp"] / "refused2").exists()
    # A manifest of tools/replogle_slice_manifest.py: only its eligible rows are candidates and its excluded ones are refused.
    manifest = exports["tmp"] / "manifest.json"
    write_json(manifest, {"tool": "tools/replogle_slice_manifest.py", "targets": [
        {"symbol": "D", "eligible": True, "in_distribution": True, "excluded": []},
        {"symbol": "E", "eligible": True, "in_distribution": True, "excluded": []},
        {"symbol": "H", "eligible": False, "in_distribution": False, "excluded": ["fewer than 20 cells"]}]})
    loaded = wc.load_candidates(manifest)
    assert loaded["symbols"] == ["D", "E"] and loaded["excluded"] == {"H"} and loaded["classes"]["D"] is True
    # No response file enters: only a manifest, a .json list or a .txt list is accepted.
    for name in ("cohort.h5ad", "means.npz", "table.csv"):
        (exports["tmp"] / name).write_text("x")
        with pytest.raises(ValueError, match="never a data file"):
            wc.load_candidates(exports["tmp"] / name)


def test_negatives_are_drawn_where_the_models_agree_and_match_the_candidate(exports):
    out = exports["tmp"] / "pkg"
    assert wc.main(argv(exports, out)) == 0
    p = json.loads((out / "candidates.json").read_text())
    scores = {r["symbol"]: r for r in p["ranking"]}
    assert p["negatives"], "the fixture has agreeing targets in E's stratum"
    for n in p["negatives"]:
        assert n["matches_candidate"] == "E" and n["symbol"] != "E"
        assert n["disagreement"]["relative"] <= 0.5 and n["disagreement"]["l2"] < scores["E"]["l2"]
        assert n["expression_decile"] == p["candidates"][0]["expression_decile"] == 1   # control means 4, 5, 6
        assert n["membership_class"] is None and p["candidates"][0]["membership_class"] is None
    # The draw order is the manifest tool's rank key and the stratum is the decile; checked by hand on the pool.
    pool = [s for s in ["D", "F", "G", "H", "X0", "X1"] if scores[s]["relative"] <= 0.5
            and scores[s]["n_effect_genes"] >= 1 and scores[s]["expression_decile"] == 1]
    assert set(pool) <= {"D", "F"} and pool
    expected = sorted(pool, key=lambda s: hashlib.sha256(f"public seed\n{s}".encode()).hexdigest())[:2]
    assert [n["symbol"] for n in p["negatives"]] == expected
    assert p["negatives_shortfall"] == 2 - len(expected)
    strata = {"E": (3, None), "D": (3, None), "F": (3, None), "G": (4, None)}
    drawn = wc.draw_negatives(["E"], ["D", "F", "G"], strata, "public seed", 5)
    assert sorted(n["symbol"] for n in drawn) == ["D", "F"] and all(n["matches_candidate"] == "E" for n in drawn)
    assert wc.draw_negatives(["E"], ["G"], strata, "public seed", 5) == []
    # Deciles: rank of the control mean, ascending, times ten over the number of genes.
    assert wc.deciles(np.array([5., 1., 3., 4.])).tolist() == [7, 0, 2, 5]


def test_power_matches_a_hand_computation():
    z = 1.959963984540054 + 0.8416212335729143
    assert wc.Z_SUM == pytest.approx(z, abs=1e-9)
    assert wc.mde(0.3, 50) == pytest.approx(z * 0.3 * math.sqrt(2 / 50))
    assert wc.mde(0.3, 200) == pytest.approx(wc.mde(0.3, 50) / 2)
    assert wc.cells_needed(0.3, 0.2) == math.ceil(2 * (z * 0.3 / 0.2) ** 2) == 36
    assert wc.cells_needed(0.3, 0.0) is None
    rows = wc.gene_rows(["A", "B"], np.array([0.5, 0.0]), np.array([0.1, 0.0]), np.array([0.3, 0.2]), 2, 0.1, 50)
    assert [r["gene"] for r in rows] == ["A", "B"]
    assert rows[0]["min_detectable_delta"] == pytest.approx(z * 0.3 * math.sqrt(2 / 50))
    assert rows[0]["detectable_feature"] and not rows[0]["detectable_parent"]
    assert rows[0]["sign_feature"] == "up" and rows[0]["sign_parent"] == "up" and rows[1]["sign_feature"] == "none"
    d = wc.disagreement(np.array([0.5, 0.0, 0.2]), np.array([0.1, 0.0, 0.2]), 0.1)
    assert d["l2"] == pytest.approx(0.4) and d["n_effect_genes"] == 2
    assert d["relative"] == pytest.approx(0.4 / math.sqrt(0.3 ** 2 + 0.2 ** 2))
    assert wc.disagreement(np.zeros(3), np.zeros(3), 0.1) == {"l2": 0.0, "relative": 0.0, "pearson": None,
                                                              "n_effect_genes": 0}


def test_the_package_is_deterministic_and_the_md_states_the_json_hash(exports):
    a, b = exports["tmp"] / "a", exports["tmp"] / "b"
    assert wc.main(argv(exports, a)) == 0
    assert wc.main(argv(exports, b)) == 0
    assert sha256(a / "candidates.json") == sha256(b / "candidates.json")
    assert sha256(a / "candidates.md") == sha256(b / "candidates.md")
    for model in ("feature", "parent"):
        assert sha256(a / "predictions" / model / "predictions.npz") == sha256(b / "predictions" / model / "predictions.npz")
        receipt = json.loads((a / "predictions" / model / "receipt.json").read_text())
        assert receipt["query_sha256"] == sha256(a / "predictions" / model / "queries.json")
    p = json.loads((a / "candidates.json").read_text())
    assert p["inputs_sha256"]["candidates (candidates.txt)"] == sha256(exports["candidates"])
    assert str(exports["tmp"]) not in (a / "candidates.json").read_text()   # no machine paths in the deposit
    assert sha256(a / "candidates.json") in (a / "candidates.md").read_text()
    with pytest.raises(SystemExit):
        wc.main(argv(exports, a))   # never overwritten
    # A different seed changes only the draw, never the ranking or the scores.
    c = exports["tmp"] / "c"
    args = argv(exports, c)
    args[args.index("--seed") + 1] = "another public value"
    assert wc.main(args) == 0
    q = json.loads((c / "candidates.json").read_text())
    assert q["ranking"] == p["ranking"] and q["candidates"] == p["candidates"]
    assert q["models"] == p["models"] and q["parameters"]["seed"] == "another public value"


def test_the_exports_must_share_one_public_context(exports, tmp_path):
    other = tmp_path / "other-context"
    shutil.copytree(exports["parent"], other)
    manifest = json.loads((other / "manifest.json").read_text())
    manifest["anchor_sha256"] = "0" * 64
    (other / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="share one public context"):
        wc.build_package(exports["feature"], exports["feature_sha"], other, sha256(other / "manifest.json"),
                         wc.load_candidates(exports["candidates"]), {}, tmp_path / "x", seed="s", inputs_sha256={})
    assert not (tmp_path / "x").exists()
