"""The scripted control's external-screen hypotheses: three fixed features per external screen knowledge file a run
can read (run.external_knowledge), implemented by the mock worker from fixed templates. The third, kernel transfer
(external_krr), was added after the first leave-one-out reading of the Replogle screen."""

import json
import shutil

import numpy as np

from genemila.data.bundle import LabelSet
from genemila.providers.mock import (SCRIPTED_HYPOTHESES, TEMPLATES, MockProvider, ScriptedPlanner, _pick_template,
                                     external_hypotheses)

from test_worker_controller import BASE, new_feature_spec, run_one


def _bundle_with_screen(dataset, tmp_path, name="ext_screen", seed=0):
    """A copy of the synthetic bundle plus a knowledge file shaped like build_external_screen's output: per target
    gene, a noisy copy of that perturbation's true change (as an independent screen of the same cells would
    measure it), with a few genes unmeasured and one target without a row."""
    bundle = tmp_path / "bundle"
    shutil.copytree(dataset, bundle)
    z = np.load(bundle / "public.npz")
    genes = [str(g) for g in z["genes"]]
    ctrl = z["control_cells"].astype(float).mean(axis=0)
    targets = json.loads((bundle / "knowledge" / "targets.json").read_text())
    sets = [LabelSet([str(p) for p in z["train_perts"]], z["train_means"].astype(float))]
    for part in ("val1", "val2"):
        sets.append(LabelSet.load(bundle / "private" / f"{part}.npz"))
    rng = np.random.default_rng(seed)
    unmeasured = set(rng.choice(len(genes), 5, replace=False).tolist())
    perts = {}
    for ls in sets:
        for p, m in zip(ls.perts, ls.means):
            g = targets[p][0]
            d = (m - ctrl) + rng.normal(0, 0.05, len(genes))
            perts[g] = {"n_cells": 50, "labels": [g],
                        "delta": [None if j in unmeasured else round(float(v), 5) for j, v in enumerate(d)]}
    dropped = sorted(perts)[0]
    del perts[dropped]
    k = {"description": "External screen deltas: test fixture.", "source": {}, "genes": genes,
         "measured": [j not in unmeasured for j in range(len(genes))],
         "control": {"n_cells": 100, "mean": [0.0] * len(genes)}, "perts": perts,
         "bundle_targets_missing": [dropped]}
    (bundle / "knowledge" / f"{name}.json").write_text(json.dumps(k))
    return bundle


def test_hypotheses_follow_the_fixed_eight_and_only_with_a_screen():
    assert ScriptedPlanner().hypotheses == SCRIPTED_HYPOTHESES                   # an unchanged control without one
    hyps = ScriptedPlanner(external=["replogle2022_k562"]).hypotheses
    assert len(SCRIPTED_HYPOTHESES) == 8 and len(hyps) == 8 + 3
    assert hyps[:len(SCRIPTED_HYPOTHESES)] == SCRIPTED_HYPOTHESES
    assert [h[2] for h in hyps[len(SCRIPTED_HYPOTHESES):]] == ["external_direct_replogle2022_k562",
                                                               "external_knn_replogle2022_k562",
                                                               "external_krr_replogle2022_k562"]
    assert external_hypotheses(None) == [] and len(external_hypotheses(["a", "b"])) == 6


def test_each_external_hypothesis_triggers_its_own_template_only():
    """The mock worker picks a template by the first keyword found in the feature's name, description and hint;
    each external hypothesis must land on its own template and name its own file, never another external one."""
    for title, cat, name, desc, why in external_hypotheses(["replogle2022_k562"]):
        want = name.removesuffix("_replogle2022_k562")
        assert want in ("external_direct", "external_knn", "external_krr")
        assert _pick_template(desc) == want and _pick_template(f"{name} {desc} {desc}") == want, name
        task = {"new_feature": {"name": name, "description": desc, "implementation_hint": desc}}
        code = MockProvider().implement(task, 1000).text
        assert TEMPLATES[want].format(name=name, knowledge="replogle2022_k562") in code
        assert 'KNOWLEDGE = "replogle2022_k562"' in code
    # the response-components hypothesis also says "kernel ridge"; the external keyword comes first only for its text
    assert _pick_template(SCRIPTED_HYPOTHESES[7][3]) == "components"


def test_build_providers_hands_the_run_s_external_knowledge_to_the_scripted_planner(tmp_path):
    from conftest import make_cfg
    from genemila.controller import build_providers

    cfg = make_cfg(tmp_path)
    assert len(build_providers(cfg)[2].hypotheses) == len(SCRIPTED_HYPOTHESES)
    cfg["run"]["external_knowledge"] = ["ext_screen"]
    assert len(build_providers(cfg)[2].hypotheses) == len(SCRIPTED_HYPOTHESES) + 3


def test_external_features_run_in_the_lab_and_carry_the_screen(dataset, code_repo, tmp_path):
    from conftest import make_cfg
    from genemila.lab import Lab

    bundle = _bundle_with_screen(dataset, tmp_path)
    lab = Lab(make_cfg(tmp_path), tmp_path / "run", bundle, repo=code_repo)
    try:
        assert lab.cfg["run"]["external_knowledge"] == ["ext_screen"]
        scores = {}
        for title, cat, name, desc, why in external_hypotheses(["ext_screen"]) + [SCRIPTED_HYPOTHESES[6]]:
            rec = run_one(lab, new_feature_spec(name, desc))
            assert rec["status"] == "completed", (name, rec["failure_reason"])
            scores[name] = rec["primary_score"]
            if name.startswith("external"):
                assert 'KNOWLEDGE = "ext_screen"' in (lab.store / f"{rec['new_feature']}.py").read_text()
        # a near-copy of the true change beats a feature that knows nothing of the target
        assert scores["external_direct_ext_screen"] > scores["control_variance"] + 0.05, scores
        assert scores["external_knn_ext_screen"] > scores["control_variance"], scores
        assert scores["external_krr_ext_screen"] > scores["control_variance"] + 0.05, scores
    finally:
        lab.close()


def test_krr_template_matches_the_leave_one_out_tool(dataset, tmp_path):
    """The scripted external_krr feature and tools/external_loo.py's external_krr are the same predictor: for every
    training perturbation with a row, the template (labels only through ctx.train_delta(exclude=p)) gives the tool's
    prediction with p held out; without a row it gives the mean training change."""
    import sys
    from pathlib import Path

    from genemila.data.bundle import export_public
    from genemila.features import registry
    from genemila.features.api import FeatureContext

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import external_loo

    pub = export_public(_bundle_with_screen(dataset, tmp_path), tmp_path / "pub")
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "krr_feat.py").write_text(TEMPLATES["external_krr"].format(name="krr_feat", knowledge="ext_screen"))
    registry.load_plugins(plugins)
    ctx = FeatureContext(pub)
    out = registry.get("krr_feat")().compute(ctx, ctx.train_perts, {})
    assert out.shape == (len(ctx.train_perts), ctx.n_genes, 1) and np.isfinite(out).all()

    bundle = external_loo.load_bundle(pub)
    S = external_loo._prepare(bundle, external_loo.load_external(pub, "ext_screen", bundle["genes"]))
    assert bundle["perts"] == ctx.train_perts
    n, used = len(bundle["perts"]), 0
    for i in range(n):
        avail = np.arange(n) != i
        krr = external_loo._krr(i, avail, S)
        want = S["deltas"][avail].mean(axis=0) if krr["pred"] is None else krr["pred"]
        np.testing.assert_allclose(out[i, :, 0], want, rtol=1e-8, atol=1e-10)
        used += krr["pred"] is not None
    assert used == int(S["krr_ok"].sum()) >= n - 1   # the fixture drops one target's row (perhaps a training one)
