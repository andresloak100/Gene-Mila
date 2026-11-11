"""Synthetic checks for fixed-penalty singleton transfer; no real bundle is read."""

import json
from pathlib import Path

import numpy as np
import pytest

from genemila.features.api import FeatureContext
from genemila.features.builtin import AdditiveResponse
from genemila.features.plugins.singleton_transfer import (
    DirectExternalAdditive,
    OrdinaryExternalTransfer,
    SingletonTransferAdditive,
    SingletonTransferCorrection,
    singleton_coverage,
)
from genemila.guard import check_plugin_source


FEATURES = [OrdinaryExternalTransfer, SingletonTransferAdditive, SingletonTransferCorrection]
ALL_FEATURES = [*FEATURES, DirectExternalAdditive]


@pytest.fixture
def ctx(tmp_path):
    genes = [f"G{i}" for i in range(6)]
    train = ["A1", "A2", "B", "C", "D", "AB"]
    targets = {"A1": ["A"], "A2": ["A"], "B": ["B"], "C": ["C"], "D": ["D"],
               "AB": ["A", "B"], "known_A": ["A"], "known_AB": ["A", "B"],
               "AX": ["A", "X"], "XA": ["X", "A"], "AXA": ["A", "X", "A"],
               "BX": ["B", "X"], "X": ["X"], "unknown": []}
    rng = np.random.default_rng(42)
    deltas = rng.normal(size=(len(train), len(genes)))
    deltas[-1] += 5  # Pair labels deliberately differ from a sum and from the singles' mean.
    controls = np.full((3, len(genes)), 10.0)
    np.savez(tmp_path / "public.npz", genes=genes, perts=list(targets), train_perts=train,
             train_means=deltas + controls.mean(axis=0), control_cells=controls)
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "targets.json").write_text(json.dumps(targets))
    screen = {"genes": genes, "measured": [True] * len(genes), "sign": -1,
              "perts": {g: {"n_cells": 30, "delta": rng.normal(size=len(genes)).tolist()}
                        for g in ["A", "B", "C", "D", "X"]}}
    (knowledge / "replogle2022_k562.json").write_text(json.dumps(screen))
    return FeatureContext(tmp_path)


def _compute(cls, ctx, perts):
    return cls().compute(ctx, perts, {})[:, :, 0]


def _write_screen(ctx, screen):
    (ctx.public_dir / "knowledge" / "replogle2022_k562.json").write_text(json.dumps(screen))


def _unit(vec):
    centered = vec - vec.mean()
    return centered / np.linalg.norm(centered)


def _manual_singleton_x(ctx):
    """Independent fixed-penalty calculation, including duplicate-target averaging."""
    names, deltas = ctx.train_delta()
    screen = ctx.knowledge("replogle2022_k562")
    responses = np.array([deltas[[names.index("A1"), names.index("A2")]].mean(axis=0),
                          *[deltas[names.index(g)] for g in ["B", "C", "D"]]])
    z = np.array([_unit(np.array(screen["perts"][g]["delta"])) for g in ["A", "B", "C", "D"]])
    query = _unit(np.array(screen["perts"]["X"]["delta"]))
    mean = deltas[:5].mean(axis=0)  # All singleton condition rows, including both A replicates.
    return mean + (z @ query) @ np.linalg.solve(z @ z.T + np.eye(4), responses - mean)


@pytest.mark.parametrize("feature", ALL_FEATURES)
@pytest.mark.parametrize("query", ["A1", "AB"])
def test_own_query_label_cannot_change_its_feature(ctx, feature, query):
    before = _compute(feature, ctx, [query])
    ctx._train_delta[ctx._train_pos[query]] += np.arange(ctx.n_genes) * 1000
    np.testing.assert_array_equal(_compute(feature, ctx, [query]), before)


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_training_single_also_excludes_all_same_target_singleton_replicates(ctx, feature):
    before = _compute(feature, ctx, ["A1"])
    ctx._train_delta[ctx._train_pos["A2"]] += np.arange(ctx.n_genes) * 1000
    np.testing.assert_array_equal(_compute(feature, ctx, ["A1"]), before)


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_gene_group_view_excludes_single_and_all_touching_pairs(ctx, feature):
    hidden = [p for p in ctx.train_perts if "B" in ctx.target_genes(p)]
    first = ctx.without_train(hidden)
    before = _compute(feature, first, ["BX", "B"])
    for p in hidden:
        ctx._train_delta[ctx._train_pos[p]] += np.arange(ctx.n_genes) * 1000
    second = ctx.without_train(hidden)
    np.testing.assert_array_equal(_compute(feature, second, ["BX", "B"]), before)
    assert first.cache == second.cache == {}


def test_known_singletons_and_pair_preserved_exactly(ctx):
    names, deltas = ctx.train_delta()
    a = deltas[[names.index("A1"), names.index("A2")]].mean(axis=0)
    b = deltas[names.index("B")]
    np.testing.assert_array_equal(_compute(SingletonTransferAdditive, ctx, ["known_A", "known_AB"]),
                                  np.array([a, a + b]))
    np.testing.assert_array_equal(_compute(SingletonTransferCorrection, ctx, ["known_A", "known_AB"]),
                                  np.zeros((2, ctx.n_genes)))
    np.testing.assert_array_equal(_compute(DirectExternalAdditive, ctx, ["known_A", "known_AB"]),
                                  np.array([a, a + b]))


def test_missing_target_transfer_preserves_known_contribution_and_groups_duplicates(ctx):
    names, deltas = ctx.train_delta()
    a = deltas[[names.index("A1"), names.index("A2")]].mean(axis=0)
    transferred = _manual_singleton_x(ctx)
    actual = _compute(SingletonTransferAdditive, ctx, ["X", "AX"])
    np.testing.assert_allclose(actual, np.array([transferred, a + transferred]), rtol=1e-13, atol=1e-13)
    base = _compute(AdditiveResponse, ctx, ["X", "AX"])
    np.testing.assert_allclose(_compute(SingletonTransferCorrection, ctx, ["X", "AX"]), actual - base,
                               rtol=1e-13, atol=1e-13)


@pytest.mark.parametrize("case", ["no_knowledge", "missing_query", "two_donors", "constant_query",
                                  "few_measured", "zero_cells", "nonfinite_query"])
def test_unavailable_transfer_falls_back_exactly_to_additive(ctx, case):
    screen = ctx.knowledge("replogle2022_k562")
    if case == "no_knowledge":
        (ctx.public_dir / "knowledge" / "replogle2022_k562.json").unlink()
    else:
        if case == "missing_query":
            del screen["perts"]["X"]
        elif case == "two_donors":
            screen["perts"]["C"]["n_cells"] = 0
            screen["perts"]["D"]["n_cells"] = -1
        elif case == "constant_query":
            screen["perts"]["X"]["delta"] = [1.0] * ctx.n_genes
        elif case == "few_measured":
            screen["measured"] = [True, True, False, False, False, False]
        elif case == "zero_cells":
            screen["perts"]["X"]["n_cells"] = 0
        elif case == "nonfinite_query":
            screen["perts"]["X"]["delta"] = [1.0, 2.0, None, float("nan"), float("inf"), float("-inf")]
        _write_screen(ctx, screen)
    queries = ["X", "AX", "known_AB", "unknown"]
    np.testing.assert_array_equal(_compute(SingletonTransferAdditive, ctx, queries),
                                  _compute(AdditiveResponse, ctx, queries))
    np.testing.assert_array_equal(_compute(SingletonTransferCorrection, ctx, queries),
                                  np.zeros((len(queries), ctx.n_genes)))


@pytest.mark.parametrize("feature", ALL_FEATURES)
def test_target_order_duplicates_and_query_batch_do_not_change_prediction(ctx, feature):
    pair = _compute(feature, ctx, ["AX"])[0]
    batched = _compute(feature, ctx, ["XA", "known_AB", "AXA", "AX"])
    np.testing.assert_array_equal(batched[[0, 2, 3]], np.broadcast_to(pair, (3, ctx.n_genes)))


@pytest.mark.parametrize("feature", FEATURES)
def test_external_gene_alignment_and_screen_sign_invariance(ctx, feature):
    screen = ctx.knowledge("replogle2022_k562")
    screen["measured"][1] = False
    screen["perts"]["X"]["delta"][2] = None
    _write_screen(ctx, screen)
    expected = _compute(feature, ctx, ["X", "AX"])
    order = [5, 0, 3, 2, 4, 1]
    screen["genes"] = [screen["genes"][i] for i in order] + ["outside_bundle"]
    screen["measured"] = [screen["measured"][i] for i in order] + [True]
    for rec in screen["perts"].values():
        rec["delta"] = [rec["delta"][i] for i in order] + [1e9]
    screen["sign"] = 1
    _write_screen(ctx, screen)
    np.testing.assert_array_equal(_compute(feature, ctx, ["X", "AX"]), expected)


def test_ordinary_transfer_matches_whole_condition_krr_and_is_distinct(ctx):
    names, deltas = ctx.train_delta()
    screen = ctx.knowledge("replogle2022_k562")
    external = {g: np.array(rec["delta"]) for g, rec in screen["perts"].items()}
    z = np.array([_unit(sum((external[g] for g in ctx.target_genes(p)), np.zeros(ctx.n_genes)))
                  for p in names])
    q = _unit(external["A"] + external["X"])
    mean = deltas.mean(axis=0)
    expected = mean + (z @ q) @ np.linalg.solve(z @ z.T + np.eye(len(z)), deltas - mean)
    ordinary = _compute(OrdinaryExternalTransfer, ctx, ["AX"])[0]
    np.testing.assert_allclose(ordinary, expected, rtol=1e-13, atol=1e-13)
    assert not np.allclose(ordinary, _compute(SingletonTransferAdditive, ctx, ["AX"])[0])


@pytest.mark.parametrize("feature", FEATURES)
def test_empty_training_returns_finite_zeros_and_correct_shape(ctx, feature):
    empty = ctx.without_train(ctx.train_perts)
    result = feature().compute(empty, ["X", "AX"], {})
    np.testing.assert_array_equal(result, np.zeros((2, ctx.n_genes, 1)))
    assert feature().compute(empty, [], {}).shape == (0, ctx.n_genes, 1)


def test_no_singletons_uses_all_training_mean(ctx):
    only_pair = ctx.without_train([p for p in ctx.train_perts if p != "AB"])
    np.testing.assert_array_equal(_compute(SingletonTransferAdditive, only_pair, ["X", "AX"]),
                                  _compute(AdditiveResponse, only_pair, ["X", "AX"]))
    np.testing.assert_array_equal(_compute(SingletonTransferCorrection, only_pair, ["X", "AX"]),
                                  np.zeros((2, ctx.n_genes)))


def test_pair_labels_never_enter_singleton_transfer_fit_when_singles_exist(ctx):
    before = _compute(SingletonTransferAdditive, ctx, ["X", "AX"])
    ctx._train_delta[ctx._train_pos["AB"]] += np.arange(ctx.n_genes) * 1000
    np.testing.assert_array_equal(_compute(SingletonTransferAdditive, ctx, ["X", "AX"]), before)


@pytest.mark.parametrize("record", [None, "malformed", []])
def test_malformed_external_record_uses_additive_fallback(ctx, record):
    screen = ctx.knowledge("replogle2022_k562")
    screen["perts"]["X"] = record
    _write_screen(ctx, screen)
    for feature in (SingletonTransferAdditive, DirectExternalAdditive):
        np.testing.assert_array_equal(_compute(feature, ctx, ["X", "AX"]),
                                      _compute(AdditiveResponse, ctx, ["X", "AX"]))


def test_global_unmeasured_columns_do_not_affect_transfer(ctx):
    screen = ctx.knowledge("replogle2022_k562")
    screen["measured"][0] = False
    _write_screen(ctx, screen)
    before = _compute(SingletonTransferAdditive, ctx, ["X", "AX"])
    for i, rec in enumerate(screen["perts"].values()):
        rec["delta"][0] = float(1e12 * (i + 1))
    _write_screen(ctx, screen)
    np.testing.assert_array_equal(_compute(SingletonTransferAdditive, ctx, ["X", "AX"]), before)


def test_direct_reference_sign_alignment_and_per_gene_mean_fill(ctx):
    screen = ctx.knowledge("replogle2022_k562")
    screen["measured"][1] = False
    screen["perts"]["X"]["delta"][2] = None
    _write_screen(ctx, screen)
    _, deltas = ctx.train_delta()
    mean = deltas[:5].mean(axis=0)
    a = deltas[:2].mean(axis=0)
    x = -np.array(screen["perts"]["X"]["delta"], dtype=float)
    x[[1, 2]] = mean[[1, 2]]
    np.testing.assert_array_equal(_compute(DirectExternalAdditive, ctx, ["X", "AX"]), np.array([x, a + x]))
    screen["perts"]["X"]["n_cells"] = 0
    _write_screen(ctx, screen)
    np.testing.assert_array_equal(_compute(DirectExternalAdditive, ctx, ["X", "AX"]),
                                  _compute(AdditiveResponse, ctx, ["X", "AX"]))


@pytest.mark.parametrize("sign", [0, 2, True, "-1"])
def test_direct_reference_refuses_invalid_sign(ctx, sign):
    screen = ctx.knowledge("replogle2022_k562")
    screen["sign"] = sign
    _write_screen(ctx, screen)
    with pytest.raises(ValueError, match="sign"):
        _compute(DirectExternalAdditive, ctx, ["X"])


def test_coverage_uses_actual_known_transfer_and_fallback_routes(ctx):
    known, mixed, training, empty = singleton_coverage(ctx, ["known_AB", "AX", "A1", "unknown"])
    assert (known["known_targets"], known["transferred_targets"]) == (2, 0)
    assert (mixed["known_targets"], mixed["missing_targets"], mixed["transferred_targets"]) == (1, 1, 1)
    assert training["singleton_training_targets"] == 3  # Neither same-target A condition remains.
    assert training["known_targets"] == 0 and training["transferred_targets"] == 1
    assert empty["n_targets"] == 0 and empty["fallback_reasons"]["unknown_target"] == 1
    screen = ctx.knowledge("replogle2022_k562")
    screen["perts"]["C"]["n_cells"] = 0
    screen["perts"]["D"]["n_cells"] = 0
    _write_screen(ctx, screen)
    assert singleton_coverage(ctx, ["X"])[0]["fallback_reasons"]["too_few_singletons"] == 1
    screen["perts"]["X"]["delta"] = [1.0] * ctx.n_genes
    _write_screen(ctx, screen)
    unusable = singleton_coverage(ctx, ["X"])[0]["fallback_reasons"]
    assert unusable["unusable_external"] == 1 and unusable["too_few_singletons"] == 0
    screen["perts"]["X"]["n_cells"] = 0
    _write_screen(ctx, screen)
    assert singleton_coverage(ctx, ["X"])[0]["fallback_reasons"]["missing_external"] == 1


def test_optional_plugin_obeys_existing_guard():
    source = (Path(__file__).resolve().parents[1] /
              "genemila/features/plugins/singleton_transfer.py").read_text()
    assert check_plugin_source(source, "singleton_transfer_correction") == {
        "class_name": "SingletonTransferCorrection"}
