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


def _template_against_tool(pub, knowledge, name):
    """The external_krr template's feature on every perturbation of the public bundle, training and not, checked
    against tools/external_loo.py's _krr with the labels the template may read for p: every training perturbation
    except p (for a perturbation outside training, all of them). Such a perturbation gets a NaN label row in the
    tool's matrices that no prediction may read. Where the tool falls back, the template gives the mean of those
    labels. Returns {perturbation: whether kernel ridge was used}."""
    import sys
    from pathlib import Path

    from genemila.features import registry
    from genemila.features.api import FeatureContext

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import external_loo

    plugins = pub.parent / f"plugins_{name}"
    plugins.mkdir()
    (plugins / f"{name}.py").write_text(TEMPLATES["external_krr"].format(name=name, knowledge=knowledge))
    registry.load_plugins(plugins)
    ctx = FeatureContext(pub)
    out = registry.get(name)().compute(ctx, ctx.perts, {})
    assert out.shape == (len(ctx.perts), ctx.n_genes, 1) and np.isfinite(out).all()

    bundle = external_loo.load_bundle(pub)
    assert bundle["perts"] == ctx.train_perts
    others = [p for p in ctx.perts if p not in set(ctx.train_perts)]
    assert others   # the sealed set scores perturbations outside training: that path is checked too
    perts, n_train = ctx.train_perts + others, len(ctx.train_perts)
    targets = json.loads((pub / "knowledge" / "targets.json").read_text())
    placeholder = np.full((len(others), ctx.n_genes), np.nan)
    aug = {**bundle, "perts": perts, "deltas": np.vstack([bundle["deltas"], placeholder]),
           "targets": {p: [str(t) for t in targets.get(p, [])] for p in perts}}
    S = external_loo._prepare(aug, external_loo.load_external(pub, knowledge, bundle["genes"]))
    used = {}
    for i, p in enumerate(perts):
        avail = np.arange(len(perts)) < n_train
        avail[i] = False
        krr = external_loo._krr(i, avail, S)
        want = S["deltas"][avail].mean(axis=0) if krr["pred"] is None else krr["pred"]
        np.testing.assert_allclose(out[ctx.perts.index(p), :, 0], want, rtol=1e-8, atol=1e-10, err_msg=p)
        used[p] = krr["pred"] is not None
    return used


def _public_with_screen(dataset, tmp_path, edit=None):
    """The public part of _bundle_with_screen's bundle; edit(screen, targets) may change the knowledge file and
    targets.json in place before they are written back."""
    from genemila.data.bundle import export_public

    pub = export_public(_bundle_with_screen(dataset, tmp_path), tmp_path / "pub")
    kdir = pub / "knowledge"
    screen = json.loads((kdir / "ext_screen.json").read_text())
    targets = json.loads((kdir / "targets.json").read_text())
    if edit is not None:
        edit(screen, targets)
        (kdir / "ext_screen.json").write_text(json.dumps(screen))
        (kdir / "targets.json").write_text(json.dumps(targets))
    z = np.load(pub / "public.npz")
    return pub, [str(p) for p in z["train_perts"]], [str(p) for p in z["perts"]], screen, targets


def test_krr_template_matches_the_leave_one_out_tool(dataset, tmp_path):
    """The scripted external_krr feature and tools/external_loo.py's external_krr are the same predictor: for every
    perturbation, training or not, the template (labels only through ctx.train_delta(exclude=p)) gives the tool's
    prediction from the other training perturbations; where the tool falls back it gives the mean training change."""
    pub, train, perts, screen, targets = _public_with_screen(dataset, tmp_path)
    used = _template_against_tool(pub, "ext_screen", "krr_feat")
    has_row = {p: targets[p][0] in screen["perts"] for p in perts}
    assert used == has_row and sum(has_row.values()) == len(perts) - 1   # the fixture drops one target's row


def test_krr_template_reads_the_file_as_the_tool_does(dataset, tmp_path):
    """Files the builder does not write, read the same way by both: a target listed with zero cells has no row,
    numbers in genes the file marks unmeasured are ignored, and a perturbation whose first target with a row has an
    unusable (all-null) row falls back rather than reaching for its next target's row."""
    ghosted, zero = [], []

    def edit(screen, targets):
        with_row = sorted(g for g in screen["perts"])
        zero.extend(with_row[:2])
        for g in zero:                                           # zero cells: no measurement, whatever delta says
            screen["perts"][g]["n_cells"] = 0
        rng = np.random.default_rng(7)
        for r in screen["perts"].values():                       # numbers where the mask says unmeasured
            r["delta"] = [round(float(rng.normal()), 5) if not m else v for v, m in zip(r["delta"], screen["measured"])]
        screen["perts"]["GHOST"] = {"n_cells": 50, "labels": ["GHOST"], "delta": [None] * len(screen["genes"])}
        z = np.load(tmp_path / "pub" / "public.npz")
        train = [str(p) for p in z["train_perts"]]
        other = [str(p) for p in z["perts"] if str(p) not in set(train)]
        for p in ([q for q in train if targets[q][0] in with_row[2:]][:1] +
                  [q for q in other if targets[q][0] in with_row[2:]][:1]):
            targets[p] = ["GHOST"] + targets[p]                   # its own row comes second
            ghosted.append(p)

    pub, train, perts, screen, targets = _public_with_screen(dataset, tmp_path, edit)
    assert len(ghosted) == 2 and not all(screen["measured"])
    used = _template_against_tool(pub, "ext_screen", "krr_odd")
    rows = {g for g, r in screen["perts"].items() if r["n_cells"] > 0}
    for p in perts:
        first = next((t for t in targets[p] if t in rows), None)   # the first target with a row, as the tool takes it
        assert used[p] == (first is not None and first != "GHOST"), p
    assert not any(used[p] for p in ghosted)
    assert sum(not used[p] for p in perts if targets[p][0] in zero) == 2


def test_krr_template_at_the_three_row_threshold(dataset, tmp_path):
    """Three training perturbations with an external row: one held out leaves two, so every training perturbation
    falls back, while a perturbation outside training sees all three and gets kernel ridge; both sides agree."""
    keep = {}

    def edit(screen, targets):
        z = np.load(tmp_path / "pub" / "public.npz")
        train = [str(p) for p in z["train_perts"]]
        other = [str(p) for p in z["perts"] if str(p) not in set(train)]
        ours = [targets[p][0] for p in train if targets[p][0] in screen["perts"]][:3]
        theirs = [targets[p][0] for p in other if targets[p][0] in screen["perts"]]
        keep.update(train=ours, other=theirs)
        screen["perts"] = {g: r for g, r in screen["perts"].items() if g in set(ours) | set(theirs)}

    pub, train, perts, screen, targets = _public_with_screen(dataset, tmp_path, edit)
    assert len(keep["train"]) == 3 and sum(targets[p][0] in screen["perts"] for p in train) == 3
    used = _template_against_tool(pub, "ext_screen", "krr_three")
    assert not any(used[p] for p in train)
    outside = [p for p in perts if p not in set(train) and targets[p][0] in keep["other"]]
    assert outside and [p for p in perts if p not in set(train) and used[p]] == outside
