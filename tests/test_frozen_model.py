"""Frozen inference must preserve a pre-selected estimator and public context."""
import json
import pickle
import shutil
from pathlib import Path

import numpy as np
import pytest
from sklearn.linear_model import Ridge

from genemila.frozen import export_ensemble, predict_ensemble, sha256
from genemila.pipeline import run


def write_json(path, value):
    path.write_text(json.dumps(value))


@pytest.fixture
def archived(tmp_path):
    run_dir = tmp_path / "historical-run"
    public = run_dir / "public_data"
    (public / "knowledge").mkdir(parents=True)
    plugins = run_dir / "feature_store"
    plugins.mkdir()
    control = np.array([[1., 2., 3., 4.], [2., 3., 4., 5.], [3., 1., 5., 2.]])
    genes = ["A", "B", "C", "D"]
    perts, train = ["A1", "B1", "C1", "C_D"], ["A1", "B1"]
    np.savez_compressed(public / "public.npz", genes=np.array(genes), control_cells=control,
                        perts=np.array(perts), train_perts=np.array(train), train_ncells=np.array([20, 30]),
                        train_means=control.mean(0) + np.array([[.2, -.4, .1, .3], [.1, .6, -.2, .7]]))
    write_json(public / "knowledge" / "targets.json", {"A1": ["A"], "B1": ["B"], "C1": ["C"], "C_D": ["C", "D"]})
    (plugins / "batch_switch.py").write_text('''import numpy as np
from genemila.features.api import Feature, register
@register
class BatchSwitch(Feature):
    name = "batch_switch"
    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            if ctx.target_genes(p) == ["C"]:
                out[i, :, 0] = ctx.control_mean
        if np.allclose(out, 0):
            out += ctx.control_mean[None, :, None]
        return out
''')
    (plugins / "training_primed.py").write_text('''import numpy as np
from genemila.features.api import Feature, register
primed = False
@register
class TrainingPrimed(Feature):
    name = "training_primed"
    def compute(self, ctx, perts, params):
        global primed
        if list(perts) == ctx.train_perts:
            primed = True
            ctx.cache["training_primed"] = 17
        scale = 2 if primed and ctx.cache.get("training_primed") == 17 else 99
        return np.broadcast_to(ctx.control_mean[None, :, None] * scale,
                               (len(perts), ctx.n_genes, 1)).copy()
''')
    spec = {"experiment_id": "EXP_0007", "feature_set": ["mean_response", "is_target", "batch_switch", "training_primed"],
            "model_type": "ridge", "hyperparameters": {"alpha_grid": [.3, 3., 30.]}, "seed": 0}
    artifact = run_dir / "artifacts" / "EXP_0007"
    run(spec, public, plugins, artifact)
    write_json(artifact / "run_spec.json", spec)
    # Mimic the worker: predictions keep one alpha; models keep the full grid.
    with np.load(artifact / "predictions.npz", allow_pickle=False) as z:
        saved = z["delta"][1].copy()
        np.savez_compressed(artifact / "pruned.npz", delta=z["delta"][1:2], perts=z["perts"], alphas=z["alphas"][1:2])
    (artifact / "pruned.npz").replace(artifact / "predictions.npz")
    files = [artifact / "models.pkl", artifact / "run_spec.json", artifact / "predictions.npz",
             *public.rglob("*.npz"), *public.rglob("*.json"), *plugins.glob("*.py")]
    receipt = tmp_path / "pin.json"
    write_json(receipt, {"saved_sealed_metrics": {"secret_score": .123456789}, "frozen_members": [{
        "run_directory": str(run_dir), "experiment_id": "EXP_0007", "selected_alpha": 3.,
        "features": spec["feature_set"], "base_commit": "frozen-original", "weight": 1.,
        "files_sha256": {str(p.relative_to(run_dir)): sha256(p) for p in files}}]})
    return {"run": run_dir, "artifact": artifact, "receipt": receipt, "saved": saved,
            "spec": spec, "tmp": tmp_path}


def export(archived):
    package = archived["tmp"] / "export"
    result = export_ensemble(archived["receipt"], sha256(archived["receipt"]), [("EXP_0007", 3.)], package,
                             trust_pickle=True)
    return package, result


def predict(package, queries, output):
    path = output.parent / (output.name + ".queries.json")
    write_json(path, {"schema_version": 1, "queries": queries})
    receipt = predict_ensemble(package, sha256(package / "manifest.json"), path, output)
    with np.load(output / "predictions.npz", allow_pickle=False) as z:
        return z["delta"].copy(), receipt


def query(name, genes):
    return {"condition_id": name, "target_genes": genes}


def test_export_resolves_full_grid_and_reproduces_original_batch_without_fit(archived, monkeypatch):
    monkeypatch.setattr(Ridge, "fit", lambda *a, **k: pytest.fail("frozen export/inference must never fit"))
    package, manifest = export(archived)
    assert manifest["members"][0]["full_grid_index"] == 1
    assert not list(package.rglob("*.pkl"))
    assert "secret_score" not in (package / "manifest.json").read_text()
    assert "saved_sealed" not in (package / "manifest.json").read_text()
    got, receipt = predict(package, [query("C_D", ["C", "D"]), query("C1", ["C"])], archived["tmp"] / "original")
    np.testing.assert_allclose(got, archived["saved"][[1, 0]], rtol=0, atol=1e-7)
    assert receipt["condition_ids"] == ["C_D", "C1"]
    assert receipt["predictions_sha256"] == sha256(archived["tmp"] / "original" / "predictions.npz")


def test_new_query_anchors_are_independent_of_query_batch_and_order(archived):
    package, _ = export(archived)
    single, _ = predict(package, [query("newD", ["D"])], archived["tmp"] / "single")
    batch, _ = predict(package, [query("newC", ["C"]), query("newD", ["D"])], archived["tmp"] / "batch")
    reverse, _ = predict(package, [query("newD", ["D"]), query("newC", ["C"])], archived["tmp"] / "reverse")
    np.testing.assert_array_equal(single[0], batch[1])
    np.testing.assert_array_equal(batch, reverse[::-1])
    # Confirm the synthetic plugin actually distinguishes anchored from standalone computation.
    from genemila.features.api import FeatureContext
    from genemila.features import registry
    ctx = FeatureContext(package / "context")
    ctx._targets["newD"] = ["D"]
    registry.load_plugins(package / "members" / "0" / "plugins")
    alone = registry.get("batch_switch")().compute(ctx, ["newD"], {})
    anchored = registry.get("batch_switch")().compute(ctx, ["C1", "newD"], {})
    assert np.any(alone)
    assert not np.any(anchored[-1])


def test_training_feature_priming_preserves_original_prediction(archived):
    package, _ = export(archived)
    got, _ = predict(package, [query("C1", ["C"])], archived["tmp"] / "primed")
    np.testing.assert_allclose(got[0], archived["saved"][0], rtol=0, atol=1e-7)
    # A context that skips the original training feature phase gives a different
    # feature value, so the equality above exercises both module and context memo.
    from genemila.features.api import FeatureContext
    from genemila.frozen import _plugins
    with _plugins(package / "members" / "0" / "plugins"):
        from genemila.features import registry
        ctx = FeatureContext(package / "context")
        cold = registry.get("training_primed")().compute(ctx, ["C1"], {})
        registry.get("training_primed")().compute(ctx, ctx.train_perts, {})
        warm = registry.get("training_primed")().compute(ctx, ["C1"], {})
        assert not np.allclose(cold, warm)


def test_multiple_weighted_members_have_isolated_plugin_sources_and_contexts(archived, monkeypatch):
    second = archived["tmp"] / "second-run"
    shutil.copytree(archived["run"], second)
    plugin = second / "feature_store" / "batch_switch.py"
    plugin.write_text(plugin.read_text().replace("out[i, :, 0] = ctx.control_mean", "out[i, :, 0] = ctx.control_mean + 0.25"))
    spec = {**archived["spec"], "experiment_id": "EXP_0008", "seed": 1}
    artifact = second / "artifacts" / "EXP_0008"
    run(spec, second / "public_data", second / "feature_store", artifact)
    write_json(artifact / "run_spec.json", spec)
    with np.load(artifact / "predictions.npz", allow_pickle=False) as z:
        second_saved = z["delta"][1].copy()
    receipt = json.loads(archived["receipt"].read_text())
    receipt["frozen_members"][0]["weight"] = .25
    files = [artifact / "models.pkl", artifact / "run_spec.json", *second.glob("public_data/*.npz"),
             *second.glob("public_data/knowledge/*.json"), *second.glob("feature_store/*.py")]
    receipt["frozen_members"].append({"run_directory": str(second), "experiment_id": "EXP_0008", "selected_alpha": 3.,
                                     "features": spec["feature_set"], "weight": .75,
                                     "files_sha256": {str(p.relative_to(second)): sha256(p) for p in files}})
    write_json(archived["receipt"], receipt)
    monkeypatch.setattr(Ridge, "fit", lambda *a, **k: pytest.fail("frozen ensemble must never fit"))
    package = archived["tmp"] / "export"
    export_ensemble(archived["receipt"], sha256(archived["receipt"]), [("EXP_0007", 3.), ("EXP_0008", 3.)], package,
                    trust_pickle=True)
    got, receipt = predict(package, [query("C1", ["C"]), query("C_D", ["C", "D"])], archived["tmp"] / "ensemble")
    expected = (.25 * archived["saved"].astype(np.float64) + .75 * second_saved.astype(np.float64)).astype(np.float32)
    np.testing.assert_allclose(got, expected, rtol=0, atol=1e-7)
    with np.load(archived["tmp"] / "ensemble/predictions.npz", allow_pickle=False) as z:
        np.testing.assert_allclose(z["member_delta"][0], archived["saved"], rtol=0, atol=1e-7)
        np.testing.assert_allclose(z["member_delta"][1], second_saved, rtol=0, atol=1e-7)
    assert [m["weight"] for m in receipt["members"]] == [.25, .75]


@pytest.mark.parametrize("change", ["missing", "duplicate", "model_count", "model_alpha", "nonfinite", "scale"])
def test_invalid_estimator_grid_or_numeric_parameters_fail(archived, change):
    path = archived["artifact"] / "models.pkl"
    with path.open("rb") as fh:
        bundle = pickle.load(fh)
    spec = archived["spec"]
    if change == "missing":
        spec["hyperparameters"]["alpha_grid"][1] = 4.
    elif change == "duplicate":
        spec["hyperparameters"]["alpha_grid"][2] = 3.
    elif change == "model_count":
        bundle["models"].pop()
    elif change == "model_alpha":
        bundle["models"][1].alpha = 4.
    elif change == "nonfinite":
        bundle["models"][1].coef_[0] = np.nan
    else:
        bundle["x_std"][0] = 0.
    with path.open("wb") as fh:
        pickle.dump(bundle, fh)
    write_json(archived["artifact"] / "run_spec.json", spec)
    receipt = json.loads(archived["receipt"].read_text())
    hashes = receipt["frozen_members"][0]["files_sha256"]
    for name in ("models.pkl", "run_spec.json"):
        hashes[f"artifacts/EXP_0007/{name}"] = sha256(archived["artifact"] / name)
    write_json(archived["receipt"], receipt)
    with pytest.raises(ValueError):
        export(archived)
    assert not (archived["tmp"] / "export").exists()


def test_hash_failure_precedes_pickle_deserialization(archived, monkeypatch):
    monkeypatch.setattr(pickle, "loads", lambda *a, **k: pytest.fail("unverified pickle was loaded"))
    with (archived["artifact"] / "models.pkl").open("ab") as fh:
        fh.write(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        export(archived)


@pytest.mark.parametrize("change", ["context_hash", "plugin_hash", "runtime", "genes", "columns", "missing_knowledge", "nonfinite_prediction"])
def test_changed_export_fails(archived, change):
    package, manifest = export(archived)
    if change in ("context_hash", "plugin_hash"):
        path = package / ("context/public.npz" if change == "context_hash" else "members/0/plugins/batch_switch.py")
        with path.open("ab") as fh:
            fh.write(b"tamper")
    elif change == "runtime":
        manifest["runtime"]["python"] = "0.0.0"
    elif change == "genes":
        manifest["genes"] = manifest["genes"][::-1]
    elif change == "columns":
        manifest["members"][0]["columns"] = manifest["members"][0]["columns"][::-1]
    elif change == "missing_knowledge":
        (package / "context/knowledge/targets.json").unlink()
    else:
        path = package / "members/0/numeric.npz"
        with np.load(path, allow_pickle=False) as z:
            values = {k: z[k].copy() for k in z.files}
        values["coef"][:] = 1e308
        values["intercept"][()] = 1e308
        np.savez_compressed(path, **values)
        manifest["files_sha256"][str(path.relative_to(package))] = sha256(path)
    if change not in ("context_hash", "plugin_hash", "missing_knowledge"):
        write_json(package / "manifest.json", manifest)
    with pytest.raises(ValueError):
        predict(package, [query("C1", ["C"])], archived["tmp"] / "bad")
    assert not (archived["tmp"] / "bad").exists()


@pytest.mark.parametrize("queries", [
    [query("C1", ["D"])], [query("C_D", ["D", "C"])], [query("A1", ["A"])],
    [query("new", ["UNKNOWN"])], [query("new", ["C", "C"])],
    [query("new", ["C"]), query("new", ["D"])],
    [{"condition_id": "new", "target_genes": ["C"], "test_response": [1., 2.]}],
])
def test_query_metadata_rejects_identity_or_outcome_changes(archived, queries):
    package, _ = export(archived)
    with pytest.raises(ValueError):
        predict(package, queries, archived["tmp"] / "bad")


def test_trust_flag_and_manifest_pin_are_required(archived):
    with pytest.raises(ValueError, match="explicit trust"):
        export_ensemble(archived["receipt"], sha256(archived["receipt"]), [("EXP_0007", 3.)], archived["tmp"] / "export")
    package, _ = export(archived)
    query_path = archived["tmp"] / "queries.json"
    write_json(query_path, {"schema_version": 1, "queries": [query("C1", ["C"])]})
    with pytest.raises(ValueError, match="hash mismatch"):
        predict_ensemble(package, "0" * 64, query_path, archived["tmp"] / "bad")


def test_outputs_cannot_append_to_historical_source_or_package(archived):
    with pytest.raises(ValueError, match="outside source"):
        export_ensemble(archived["receipt"], sha256(archived["receipt"]), [("EXP_0007", 3.)],
                        archived["run"] / "new-export", trust_pickle=True)
    assert not (archived["run"] / "new-export").exists()
    package, _ = export(archived)
    query_path = archived["tmp"] / "queries.json"
    write_json(query_path, {"schema_version": 1, "queries": [query("C1", ["C"])]})
    with pytest.raises(ValueError, match="outside source"):
        predict_ensemble(package, sha256(package / "manifest.json"), query_path, package / "new-predictions")
    assert not (package / "new-predictions").exists()


def test_predict_targets_matches_the_query_path_and_refuses_outside_the_universe(archived):
    """The new-cohort path of docs/PLAN_R_FRESH_TEST.md: symbols in, the frozen universe's delta matrix out.
    The saved B1 prediction arrays are not in the repository (local to the Mac), so the bit-for-bit reproduction is
    the synthetic fixture's: the original condition's saved delta, and a new target via the strict query path."""
    from tools.frozen_model import main, predict_targets
    package, _ = export(archived)
    pin = sha256(package / "manifest.json")
    got = predict_targets(package, pin, {"C1": ["C"], "newD": ["D"]}, archived["tmp"] / "targets")
    assert got["perts"] == ["C1", "newD"] and got["genes"] == ["A", "B", "C", "D"]
    assert got["delta"].shape == (2, 4) and got["delta"].dtype == np.float32
    np.testing.assert_allclose(got["delta"][0], archived["saved"][0], rtol=0, atol=1e-7)
    via_query, receipt = predict(package, [query("newD", ["D"])], archived["tmp"] / "via-query")
    np.testing.assert_array_equal(got["delta"][1], via_query[0])
    assert got["receipt"]["anchor_sha256"] == receipt["anchor_sha256"]
    assert got["receipt"]["scoring"].startswith("none")
    # The deposit keeps the query bytes the receipt pins, so the holder can verify query_sha256.
    assert sha256(archived["tmp"] / "targets" / "queries.json") == got["receipt"]["query_sha256"]
    assert json.loads((archived["tmp"] / "targets" / "queries.json").read_text())["queries"][1] == {
        "condition_id": "newD", "target_genes": ["D"]}
    with pytest.raises(ValueError, match="outside frozen gene universe"):
        predict_targets(package, pin, {"newZ": ["Z"]}, archived["tmp"] / "refused")
    assert not (archived["tmp"] / "refused").exists()
    with pytest.raises(ValueError, match="nonempty mapping"):
        predict_targets(package, pin, {}, archived["tmp"] / "empty")
    out = archived["tmp"] / "cli"
    assert main(["predict-targets", "--package", str(package), "--manifest-sha256", pin, "--target", "D",
                 "--out", str(out)]) == 0
    with np.load(out / "predictions.npz", allow_pickle=False) as z:
        assert z["perts"].tolist() == ["D"]
        np.testing.assert_array_equal(z["delta"][0], via_query[0])
    assert sha256(out / "queries.json") == json.loads((out / "receipt.json").read_text())["query_sha256"]
    with pytest.raises(SystemExit):
        main(["predict-targets", "--package", str(package), "--manifest-sha256", pin, "--target", "Z",
              "--out", str(archived["tmp"] / "cli-refused")])
