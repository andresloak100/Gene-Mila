#!/usr/bin/env python3
"""Feature audit of finished runs: are the features redundant, which of them earn their place, and how compact can
the model be while keeping its accuracy? A pre-specified protocol replayed over finished runs, free of any LLM, on
visible data only (with an optional sealed check fenced into one function).

For each run the tool audits the run's selected single model (the completed experiment, neither ensemble nor
baseline, with the highest visible score) and, unless --no-pool, a pool of features: that model's features, every
feature that improved on its parent, and the three built-ins. Every score is pearson_delta per visible perturbation:
out-of-fold predictions for the training perturbations (features that read training labels recomputed without each
fold, label dependence detected per feature on a fresh view with the plugins re-executed, so no other feature's memo
can hide it) plus predictions for the visible validation perturbations from a fit on all training perturbations.
Each subset's ridge penalty is chosen on the training perturbations' out-of-fold scores under one fold partition and
reported under another, both directions averaged; the training perturbations are the same under both
partitions, so only the validation perturbations are independent of that choice. The greedy paths and the compact
set (one-standard-error rule on the backward path) are chosen on the training perturbations' scores alone, and the
compact model is compared with the full one on the validation perturbations, which no choice of the tool touched.
On that engine the tool measures redundancy, single-feature and drop-one scores, Lasso selection stability (penalty
by cross-validation over the fold-recomputed designs), a merge test for correlated clusters and a verdict per
feature; every feature that is not kept goes into a failed-feature box a lab component can import, except the ones a
kept feature computes through ctx.feature (a composite's inputs, recorded per feature, transitively), which a lab that
banned them could no longer compute the kept feature without.

Python salts every str hash per process, so a plugin built on hash() of a name is a different pseudo-random feature
in every process. From the command line the tool therefore re-executes itself under PYTHONHASHSEED=0, the seed every
experiment process of the lab runs with (genemila.sandbox.HASH_SEED; once: an environment flag stops a second time),
so that two identical invocations write the same report, and it computes each audited feature's full-training block
once more in each of three fresh processes under PYTHONHASHSEED 0, 1 and 2, through the same plugin loading and on
the public data alone. A feature whose block differs between any two of them depends on the hash seed. In a run that
recorded the seed its experiment processes ran under (run.hash_seed), audited under that same seed, such a feature is
the lab's own and is audited as any other, unless a second process under that seed computes it differently too (it
follows memory addresses, which no seed fixes); otherwise (a run from before the seed was fixed, whose processes each
drew their own) it is unstable: left out of every score, path and compact set, and boxed. Ties between training scores
(within 1e-9, as for exact duplicates) are broken by feature name, never by the order in which features happen to be
listed.

Run directories are strictly read only: the database through a read-only SQLite URI (a private copy when a
write-ahead log is present, so no -wal or -shm file is ever created next to it), plugins imported file by file
without writing bytecode (a file that fails to import makes only its own features unrecomputable), and no feature
block is cached on disk. The tool's --cache directory holds one checkpoint per audited run: pass it for long jobs,
so that an interrupted job resumes from the runs already audited (and never scores their sealed models twice); the
default is a temporary directory, lost on exit.

    python tools/feature_audit.py --runs runs/a runs/b --out docs/results/feature_audit.md --cache ~/.fa_cache
    python tools/feature_audit.py --runs runs/a runs/b --out audit.md --cache ~/.fa_cache --score-sealed
    python tools/feature_audit.py --from-json docs/results/feature_audit.json --out docs/results/feature_audit.md
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import warnings
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.benchmark.table import run_arm  # noqa: E402
from genemila.data.bundle import LabelSet  # noqa: E402  (visible validation labels only)
from genemila.features import registry  # noqa: E402
from genemila.features.api import REGISTRY, FeatureContext  # noqa: E402
from genemila.features.registry import BUILTIN_FEATURES  # noqa: E402
from genemila.pipeline import cv_fold_targets, cv_folds_of, feature_blocks, make_model  # noqa: E402
from genemila.sandbox import (HASH_REEXEC_ENV, python_hash_seed, reexec_under_hash_seed,  # noqa: E402
                              reexecuted_under_hash_seed)

FIXED_ALPHAS = (1.0, 10.0, 100.0, 1e3, 1e4, 3e4, 1e5)
POOL_MIN_GAIN = 0.0005      # a feature joins the pool when adding it raised its parent's visible score by more
CORR_HIGH = 0.9             # clusters, redundancy verdicts
CORR_MID = 0.7
DUPLICATE_R = 0.9999        # exact duplicates
STABLE_FREQ = 0.8           # Lasso-stable: selected in at least this share of the half-samples
TOP_PAIRS = 15
LASSO_LAMBDAS = 25
LASSO_RATIO = 1e-4          # smallest lambda of the grid, relative to the largest (which zeroes every column)
SEALED_FLAG = 0.002         # sealed reproduction difference that is flagged
REPRO_FLAG = 0.002          # visible reproduction difference that marks a run (†)
NOISE_FLOOR = 0.001         # margin of practical equivalence: a paired difference within max(SE, this) is either not
                            # established or smaller than 0.001. It is not a noise estimate: two models that differ
                            # only by an exact duplicate column differ systematically by about 1e-5 with a paired SE
                            # smaller still, and fold seeds alone move a score by about 0.02.
CONST_REL = 1e-20           # a prediction whose within-perturbation variance is below this share of its sum of
                            # squares is constant up to rounding: pearson_delta 0, as for an exactly constant one
SHOW_COMPACT_RUNS = 10      # compact sets listed by name in the report, at most (the rest are in the JSON), and only
COMPACT_LIST_BYTES = 850    # as many as fit in this many bytes: long names, or composites' inputs, list fewer
AUDIT_FORMAT = 4            # what a checkpointed audit of a run holds; 2: the dependency map, required inputs and the
                            # merge test's weakest links; 3: what each feature's own calls returned (per feature) and
                            # the full model expanded too; 4: the hash-seed check and the verdict unstable, with
                            # rounding ties broken by name. No checkpoint of another format is ever reused
TIE_TOL = 1e-9              # two training scores closer than this are tied (rounding: exact duplicate columns in
                            # another order score the same up to about 1e-15), and the tie is broken by feature name,
                            # never by the order the features happen to be listed in; six orders below the margin
HASH_SEEDS = (0, 1, 2)      # the PYTHONHASHSEED values of the processes that compute every feature's block again: 0
                            # is the lab's (sandbox.HASH_SEED) and the command line's own, and three seeds miss the
                            # order of a two-name set a quarter of the time where two would miss it half the time
HASH_TOL = 1e-6             # a block whose two computations differ by more than this, in units of a column's standard
                            # deviation over the training rows (what the engine divides it by), is unstable: a change of
                            # 1e-6 in a standardised value is far below any score effect (the margin is 0.001), while a
                            # feature built on hash() of a name changes by O(1); rounding noise is about 1e-15
HASH_WORKER_ARG = "--hash-seed-worker"            # internal: the process that computes blocks for the hash-seed check
VERDICTS = ("kept", "required_input", "unstable", "redundant", "substitutable", "harmful", "no_gain", "unrecomputable")
BOXED_VERDICTS = VERDICTS[2:]  # the verdicts that go into the failed-feature box
RULE = ("kept: in the compact set, the smallest feature set on the greedy backward path (chosen on the training "
        "perturbations' out-of-fold scores) whose score is within max(one paired SE, 0.001) of the path's best; a "
        "feature kept in the selected model's or the pool's compact set is not boxed. required_input: a feature that "
        "a kept feature computes through ctx.feature, directly or transitively (recorded while the kept feature is "
        "computed), whatever its own scores; it is not boxed either, since a lab that banned it could no longer "
        "compute the kept feature. unstable: its full-training block, computed again in three fresh processes under "
        "PYTHONHASHSEED 0, 1 and 2 by the audit's own plugin loading, differs between two of them by more than 1e-6 "
        "of a column's standard deviation (or in shape, or raises under some seeds only), so its values depend on "
        "Python's per-process str hash, and the run did not record the seed its experiment processes ran under "
        "(run.hash_seed, recorded since that seed was fixed) or the audit runs under another one, so no score of it "
        "can be reproduced; a feature that computes an unstable one through ctx.feature is unstable too. An unstable "
        "feature is left out of every score, path and compact set, so it is never kept and no kept feature needs it, "
        "and it is always boxed. A feature that depends on the seed in a run audited under the seed it recorded "
        "computes the lab's own values: it is listed (hash_check.seed_dependent) and audited as any other, unless a "
        "second process under that same seed computes its block differently too (hash_check.same_seed: it follows "
        "memory addresses, which no seed fixes), which makes it unstable there as well. "
        "Otherwise, in this order: "
        "harmful: dropping it from the full model raises the visible score by more than max(paired SE, 0.001); "
        "redundant: one of its columns correlates |r| >= 0.9 with a column of a kept feature (partner named); "
        "substitutable: dropping it from the full model lowers the visible score by more than max(paired SE, 0.001), "
        "yet the compact set does without it (kept features substitute for it); no_gain: any other feature outside "
        "the compact set (drop-one effect within max(paired SE, 0.001)); unrecomputable: it raised while being "
        "computed, or its plugin failed to import. Scores: pearson_delta per visible perturbation; each subset's "
        "ridge penalty chosen on the training perturbations' out-of-fold scores under one fold partition and "
        "reported under another, so only the validation perturbations are independent of it. 0.001 is a margin of "
        "practical equivalence, not a noise estimate. Built-in features are never boxed. Ties (training scores within "
        "1e-9, as for exact duplicates) are broken by feature name: the forward path adds, and the backward path "
        "keeps, the feature first by name.")
COMPOSITES = ("a feature that computes other registered features through ctx.feature (a composite) is audited as one "
              "feature with its own columns; every name it calls, directly or through the features it calls, is "
              "recorded on its fresh view and on every view derived from it, also a name outside the pool or one "
              "that is not registered (the per-run 'dependencies' map); a feature that a kept feature of either scope "
              "needs gets the verdict required_input in each scope where it is not kept and is never boxed; compact "
              "sets and full models are reported as listed and with their required inputs expanded (the features and "
              "columns their members' own calls computed, each distinct computation once; a name whose every call "
              "raised is listed apart as a failed input and counted nowhere)")


class Skip(Exception):
    """A run that cannot be audited (missing data, plugins or experiments): reported, never a crash."""


# ================================================================== the visible scoring engine (pure numpy)
def pearson_rows(P: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """pearson_delta along the last axis, exactly as genemila.benchmark.evaluator._pearson (0 when a side is
    constant). P may carry leading axes (alphas) that broadcast against Y. The engine scores from sufficient
    statistics instead (unit_scores); this is the reference it is tested against."""
    P = np.asarray(P, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    Pc = P - P.mean(axis=-1, keepdims=True)
    Yc = Y - Y.mean(axis=-1, keepdims=True)
    num = (Pc * Yc).sum(axis=-1)
    den = np.sqrt((Pc * Pc).sum(axis=-1) * (Yc * Yc).sum(axis=-1))
    out = np.zeros(np.shape(num))
    ok = den > 0
    out[ok] = num[ok] / den[ok]
    return out


def standardise(X_train: np.ndarray, *others: np.ndarray):
    """Columns standardised by the training mean and standard deviation (a zero deviation becomes 1), as
    genemila.pipeline.run does. Returns (X_train_std, [others_std], mean, sd)."""
    mu = X_train.mean(axis=0)
    sd = X_train.std(axis=0)
    sd[sd == 0] = 1.0
    return (X_train - mu) / sd, [(X - mu) / sd for X in others], mu, sd


@dataclass
class Unit:
    """One fit of the engine: ridge sufficient statistics of a standardised training design, and per predicted
    perturbation p the sufficient statistics of its standardised rows X_p (n_genes x C) and true deltas y_p, from
    which pearson_delta of any linear prediction X_p w + ybar follows exactly."""
    G: np.ndarray       # (C, C) Xtr^T Xtr, columns standardised by this fit's training rows
    b: np.ndarray       # (C,) Xtr^T (y - ybar)
    ybar: float
    n: int              # training rows
    M: np.ndarray       # (n_out, C, C) Xc_p^T Xc_p, Xc_p = X_p centred over genes
    c: np.ndarray       # (n_out, C) Xc_p^T (y_p - mean y_p)
    m: np.ndarray       # (n_out, C) mean of X_p over genes
    yy: np.ndarray      # (n_out,) |y_p - mean y_p|^2
    ym: np.ndarray      # (n_out,) mean of y_p over genes
    n_genes: int

    @property
    def n_out(self) -> int:
        return int(self.yy.shape[0])

    def subset(self, idx) -> "Unit":
        idx = np.asarray(idx, dtype=int)
        return Unit(self.G[np.ix_(idx, idx)], self.b[idx], self.ybar, self.n, self.M[:, idx[:, None], idx[None, :]],
                    self.c[:, idx], self.m[:, idx], self.yy, self.ym, self.n_genes)

    def transform(self, T: np.ndarray) -> "Unit":
        """The unit of the design X @ T (T: C x C_new), for training and predicted rows alike."""
        return Unit(T.T @ self.G @ T, T.T @ self.b, self.ybar, self.n, np.matmul(np.matmul(T.T, self.M), T),
                    self.c @ T, self.m @ T, self.yy, self.ym, self.n_genes)


def unit_from_standardised(Xs: np.ndarray, y: np.ndarray, Xo: np.ndarray, Yout: np.ndarray) -> Unit:
    """A unit from training rows Xs already standardised by their own mean and sd, targets y, and predicted rows Xo
    (n_out * n_genes, C) standardised with the same statistics; Yout (n_out, n_genes) true deltas."""
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    Yout = np.asarray(Yout, dtype=np.float64)
    n_out, n_genes = Yout.shape
    ybar = float(y.mean())
    X3 = np.asarray(Xo, dtype=np.float64).reshape(n_out, n_genes, -1)
    m = X3.mean(axis=1)
    Xc = X3 - m[:, None, :]
    ym = Yout.mean(axis=1)
    Yc = Yout - ym[:, None]
    return Unit(Xs.T @ Xs, Xs.T @ (y - ybar), ybar, int(Xs.shape[0]), np.matmul(Xc.transpose(0, 2, 1), Xc),
                np.einsum("pgc,pg->pc", Xc, Yc), m, (Yc * Yc).sum(axis=1), ym, int(n_genes))


def make_unit(Xtr: np.ndarray, ytr: np.ndarray, Xout: np.ndarray, Yout: np.ndarray) -> Unit:
    """A fit on raw (unstandardised) training rows Xtr with targets ytr, predicting Xout (true deltas Yout)."""
    Xs, (Xo,), _, _ = standardise(np.asarray(Xtr, dtype=np.float64), np.asarray(Xout, dtype=np.float64))
    return unit_from_standardised(Xs, ytr, Xo, Yout)


def ridge_weights(G: np.ndarray, b: np.ndarray, idx, alpha: float) -> np.ndarray:
    """w = (G[S,S] + alpha I)^-1 b[S]; with standardised (mean-zero) columns and intercept ybar this is sklearn
    Ridge(alpha, fit_intercept=True). alpha = 0 (ols) by least squares, the minimum-norm solution."""
    idx = np.asarray(idx, dtype=int)
    if idx.size == 0:
        return np.zeros(0)
    A = G[np.ix_(idx, idx)]
    if alpha <= 0:
        return np.linalg.lstsq(A, b[idx], rcond=None)[0]
    return np.linalg.solve(A + float(alpha) * np.eye(idx.size), b[idx])


def ridge_weight_grid(G: np.ndarray, b: np.ndarray, idx, alphas) -> np.ndarray:
    """(|S|, n_alpha) ridge weights for every alpha from one eigendecomposition; alpha = 0 by least squares."""
    idx = np.asarray(idx, dtype=int)
    W = np.zeros((idx.size, len(alphas)))
    if idx.size == 0:
        return W
    A, r = G[np.ix_(idx, idx)], b[idx]
    pos = [k for k, a in enumerate(alphas) if a > 0]
    if pos:
        lam, V = np.linalg.eigh(A)
        c = V.T @ r
        for k in pos:
            W[:, k] = V @ (c / (lam + float(alphas[k])))
    for k, a in enumerate(alphas):
        if a <= 0:
            W[:, k] = np.linalg.lstsq(A, r, rcond=None)[0]
    return W


def stats_pearson(M: np.ndarray, c: np.ndarray, m: np.ndarray, yy: np.ndarray, n_genes: int,
                  W: np.ndarray) -> np.ndarray:
    """(n_alpha, n_out) pearson_delta of the predictions X_p W[:, a] + const from per-perturbation statistics: the
    covariance is c_p . w, the prediction's variance w^T M_p w (both over genes, centred), so no design is formed."""
    num = c @ W
    var = np.einsum("psa,sa->pa", np.matmul(M, W), W)
    mw = m @ W
    total = var + n_genes * mw * mw
    den = np.sqrt(np.clip(var, 0.0, None) * yy[:, None])
    ok = (den > 0) & (var > CONST_REL * total)
    out = np.zeros(num.shape)
    out[ok] = np.clip(num[ok] / den[ok], -1.0, 1.0)
    return out.T


def unit_scores(unit: Unit, idx, alphas) -> np.ndarray:
    """(n_alpha, n_out) pearson_delta of the fit's predictions on columns idx, per alpha."""
    idx = np.asarray(idx, dtype=int)
    if idx.size == 0:
        return np.zeros((len(alphas), unit.n_out))  # the intercept alone is a constant prediction: pearson_delta 0
    W = ridge_weight_grid(unit.G, unit.b, idx, alphas)
    if idx.size == unit.G.shape[0] and np.array_equal(idx, np.arange(idx.size)):
        return stats_pearson(unit.M, unit.c, unit.m, unit.yy, unit.n_genes, W)
    return stats_pearson(unit.M[:, idx[:, None], idx[None, :]], unit.c[:, idx], unit.m[:, idx], unit.yy,
                         unit.n_genes, W)


def unit_sse(unit: Unit, W: np.ndarray) -> np.ndarray:
    """(n_w,) sum of squared errors of the predictions X_p W[:, j] + ybar over every predicted row of the unit."""
    d = unit.ym - unit.ybar
    A = unit.M.sum(axis=0) + unit.n_genes * unit.m.T @ unit.m
    v = unit.c.sum(axis=0) + unit.n_genes * unit.m.T @ d
    s0 = float(unit.yy.sum() + unit.n_genes * d @ d)
    return s0 - 2.0 * (v @ W) + np.einsum("sa,sa->a", A @ W, W)


def seed_matrix(fold_units, val_scores: np.ndarray, idx, alphas, n_train: int) -> np.ndarray:
    """(n_alpha, n_train + n_val) per-perturbation scores under one fold seed: out of fold for the training
    perturbations (fold_units: [(Unit, positions of the fold's perturbations)]), then the validation fit's scores."""
    M = np.empty((len(alphas), n_train + val_scores.shape[1]))
    M[:, :n_train] = np.nan
    for unit, rows in fold_units:
        M[:, np.asarray(rows, dtype=int)] = unit_scores(unit, idx, alphas)
    if np.isnan(M[:, :n_train]).any():
        raise ValueError("the folds do not cover every training perturbation")
    M[:, n_train:] = val_scores
    return M


def honest_choice(mats, n_train: int, alphas, seeds=None) -> tuple[np.ndarray, list[dict]]:
    """mats[i]: (n_alpha, n) scores under fold seed i, the first n_train entries the training perturbations. For every
    ordered pair (A, B), A != B, the alpha maximising seed A's mean TRAINING score is chosen (nothing else of A, and
    nothing of B, is looked at) and seed B's whole vector at that alpha is reported; the result is the mean of the
    reports, with the choices. Both seeds score the same training perturbations, so only the validation entries are
    independent of the choice."""
    if len(mats) < 2:
        raise ValueError("the honest penalty choice needs at least two fold seeds")
    seeds = list(range(len(mats))) if seeds is None else list(seeds)
    reports, chosen = [], []
    for i, A in enumerate(mats):
        k = int(np.argmax(np.asarray(A)[:, :n_train].mean(axis=1)))
        for j, B in enumerate(mats):
            if j != i:
                reports.append(np.asarray(B)[k])
                chosen.append({"select_seed": seeds[i], "report_seed": seeds[j], "alpha": float(alphas[k])})
    return np.mean(reports, axis=0), chosen


def paired(u: np.ndarray, v: np.ndarray) -> dict:
    """Paired comparison of two per-perturbation vectors: mean of u - v, its standard error (sd / sqrt(n)), and the
    perturbations where u is higher (wins) or lower (losses)."""
    d = np.asarray(u, dtype=np.float64) - np.asarray(v, dtype=np.float64)
    n = int(d.size)
    return {"diff": float(d.mean()) if n else 0.0, "se": float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0,
            "wins": int((d > 0).sum()), "losses": int((d < 0).sum()), "n": n}


def vector_summary(v: np.ndarray) -> dict:
    v = np.asarray(v, dtype=np.float64)
    return {"mean": float(v.mean()) if v.size else 0.0,
            "se": float(v.std(ddof=1) / np.sqrt(v.size)) if v.size > 1 else 0.0, "n": int(v.size)}


def grid_alpha(chosen_alphas, grid) -> float:
    """The mean of the chosen alphas, rounded to the nearest grid value on a log scale (0 stays 0)."""
    m = float(np.mean(chosen_alphas))
    pos = [float(g) for g in grid if g > 0]
    if m <= 0 or not pos:
        return 0.0
    return min(pos, key=lambda g: (abs(np.log10(g) - np.log10(m)), -g))


class Engine:
    """Honest visible scores of column subsets. seed_units: {fold seed: [(Unit, fold positions), ...]};
    val_unit: the fit on all training perturbations predicting the visible validation perturbations;
    columns_of: feature -> its column indices. A score holds the whole visible vector (training perturbations
    first) and its training and validation parts."""

    def __init__(self, seed_units: dict, val_unit: Unit, n_train: int, alphas, columns_of: dict | None = None):
        if len(seed_units) < 2:
            raise ValueError("the honest penalty choice needs at least two fold seeds")
        self.seed_units = seed_units
        self.seeds = list(seed_units)
        self.val_unit = val_unit
        self.n_train = int(n_train)
        self.n_val = int(val_unit.n_out)
        self.alphas = [float(a) for a in alphas]
        self.columns_of = dict(columns_of or {})
        self._cache: dict = {}

    def columns(self, features) -> list[int]:
        return sorted(c for f in features for c in self.columns_of[f])

    def matrices(self, idx, alphas=None) -> dict:
        alphas = self.alphas if alphas is None else [float(a) for a in alphas]
        val = unit_scores(self.val_unit, idx, alphas)
        return {s: seed_matrix(self.seed_units[s], val, idx, alphas, self.n_train) for s in self.seeds}

    def score_idx(self, idx) -> dict:
        key = tuple(sorted(int(i) for i in idx))
        if key not in self._cache:
            mats = self.matrices(key)
            vec, chosen = honest_choice([mats[s] for s in self.seeds], self.n_train, self.alphas, self.seeds)
            tr, va = vector_summary(vec[:self.n_train]), vector_summary(vec[self.n_train:])
            self._cache[key] = {"vector": vec, **vector_summary(vec), "train_mean": tr["mean"], "train_se": tr["se"],
                                "val_mean": va["mean"], "val_se": va["se"], "chosen": chosen,
                                "alpha": grid_alpha([c["alpha"] for c in chosen], self.alphas)}
        return self._cache[key]

    def score(self, features) -> dict:
        return self.score_idx(self.columns(features))

    def train_part(self, v: np.ndarray) -> np.ndarray:
        return np.asarray(v)[:self.n_train]

    def val_part(self, v: np.ndarray) -> np.ndarray:
        return np.asarray(v)[self.n_train:]


def static_engine(X: np.ndarray, Y: np.ndarray, X_val: np.ndarray, Y_val: np.ndarray, columns_of: dict, seeds,
                  k: int, alphas) -> Engine:
    """An engine over fixed per-perturbation designs (no label-dependent recomputation): X (n_train, n_genes, C),
    Y (n_train, n_genes), X_val (n_val, n_genes, C), Y_val (n_val, n_genes); folds from cv_folds_of."""
    n_train, n_genes, C = X.shape
    names = [f"p{i:04d}" for i in range(n_train)]
    pos = {p: i for i, p in enumerate(names)}
    seed_units = {}
    for s in seeds:
        units = []
        for fold, hide in cv_folds_of(names, k, s):  # random folds over names: hide is the fold itself
            rows = np.array([pos[p] for p in fold])
            tr = np.setdiff1d(np.arange(n_train), [pos[p] for p in hide])
            units.append((make_unit(X[tr].reshape(-1, C), Y[tr].reshape(-1), X[rows].reshape(-1, C), Y[rows]), rows))
        seed_units[s] = units
    val = make_unit(X.reshape(-1, C), Y.reshape(-1), X_val.reshape(-1, C), Y_val)
    return Engine(seed_units, val, n_train, alphas, columns_of)


# ------------------------------------------------------------------ paths and the compact choice
def _step(engine: Engine, features: list[str], res: dict, **extra) -> dict:
    return {**extra, "features": list(features), "n_features": len(features),
            "n_columns": len(engine.columns(features)), "mean": res["mean"], "se": res["se"],
            "train_mean": res["train_mean"], "val_mean": res["val_mean"],
            "alphas": [c["alpha"] for c in res["chosen"]], "alpha": res["alpha"]}


def _quiet(_msg: str) -> None:
    return None


def best_by_name(scored: list[tuple[dict, str]], last: bool = False) -> tuple[dict, str]:
    """The (result, feature) with the highest training mean; candidates within TIE_TOL of it are tied, and the tie
    goes to the feature first by name (last: the one last by name), whatever order the candidates come in."""
    top = max(r["train_mean"] for r, _ in scored)
    tied = [(r, f) for r, f in scored if r["train_mean"] >= top - TIE_TOL]
    return (max if last else min)(tied, key=lambda rf: rf[1])


def forward_path(engine: Engine, features: list[str], log=_quiet, label: str = "forward") -> list[dict]:
    """Greedy by whole feature from nothing: add the feature that raises the honest TRAINING score most (ties within
    TIE_TOL: the feature first by name); the validation perturbations play no part in the choice."""
    chosen, remaining, steps, t0 = [], list(features), [], time.perf_counter()
    while remaining:
        r, f = best_by_name([(engine.score(chosen + [g]), g) for g in remaining])
        chosen.append(f)
        remaining.remove(f)
        steps.append(_step(engine, chosen, r, added=f))
        log(f"{label} {len(chosen)}/{len(features)}: +{f}, training {r['train_mean']:.4f} "
            f"({time.perf_counter() - t0:.0f} s)")
    return steps


def backward_path(engine: Engine, features: list[str], log=_quiet, label: str = "backward") -> list[dict]:
    """Greedy by whole feature from the full model: drop the feature whose removal leaves the highest honest
    TRAINING score (ties within TIE_TOL: the feature last by name is dropped, so that of two exact duplicates both
    paths keep the one first by name), down to one feature; the first step is the full model."""
    current, t0 = list(features), time.perf_counter()
    steps = [_step(engine, current, engine.score(current), removed=None)]
    while len(current) > 1:
        r, f = best_by_name([(engine.score([g for g in current if g != h]), h) for h in current], last=True)
        current = [g for g in current if g != f]
        steps.append(_step(engine, current, r, removed=f))
        log(f"{label} {len(current)} left: -{f}, training {r['train_mean']:.4f} ({time.perf_counter() - t0:.0f} s)")
    return steps


def noise_band(se: float, floor: float = NOISE_FLOOR) -> float:
    """One paired SE, never less than the margin of practical equivalence."""
    return max(float(se), float(floor))


def one_se_choice(vectors: list[np.ndarray], sizes: list, floor: float = NOISE_FLOOR) -> tuple[int, int, list[dict]]:
    """One-standard-error rule: the best set is the highest mean; a candidate qualifies when its mean is within one
    paired SE (between the candidate's and the best set's vectors, at least `floor`) of the best; the smallest
    qualifying set wins (sizes: sortable, e.g. (features, columns)). Means within TIE_TOL of the highest are tied, and
    the smallest of them (then the first) is the best set, so rounding never picks it. Returns (chosen index, best
    index, comparisons best - candidate). The audit passes the training parts of the vectors only."""
    means = [float(np.mean(v)) for v in vectors]
    best = min((i for i, m in enumerate(means) if m >= max(means) - TIE_TOL), key=lambda i: (sizes[i], i))
    cmp = [paired(vectors[best], v) for v in vectors]
    ok = [i for i, c in enumerate(cmp) if c["diff"] <= noise_band(c["se"], floor)]
    pick = min(ok, key=lambda i: (sizes[i], -means[i], i))
    return pick, best, cmp


def classify(diff: float, se: float, floor: float = NOISE_FLOOR) -> str:
    """A paired difference: 'not_established' (|diff| <= SE), 'below_margin' (beyond one SE but within the margin
    of practical equivalence), or 'higher' / 'lower' (beyond both)."""
    if abs(diff) <= se:
        return "not_established"
    if abs(diff) <= floor:
        return "below_margin"
    return "higher" if diff > 0 else "lower"


# ------------------------------------------------------------------ redundancy
def corr_from_gram(G: np.ndarray, constant=None) -> np.ndarray:
    """Correlation matrix of standardised (mean-zero) columns from their Gram matrix; constant columns get 0."""
    d = np.sqrt(np.clip(np.diag(G), 0.0, None))
    bad = d <= 0
    if constant is not None:
        bad = bad | np.asarray(constant, dtype=bool)
    dd = np.where(bad, 1.0, d)
    R = G / np.outer(dd, dd)
    R[bad, :] = 0.0
    R[:, bad] = 0.0
    np.fill_diagonal(R, np.where(bad, 0.0, 1.0))
    return np.clip(R, -1.0, 1.0)


def weakest_link(A: np.ndarray) -> float:
    """The smallest weight of a maximum spanning tree of the complete graph with weights A (symmetric, |r| of a
    cluster's columns), by Prim's algorithm: the strongest chain of correlations that joins every member, so for a
    single-linkage cluster at a threshold it is at least the threshold, however weakly its two ends correlate (that
    all-pairs minimum is another number). 1.0 for a single column."""
    A = np.asarray(A, dtype=np.float64)
    k = A.shape[0]
    if k < 2:
        return 1.0
    inside = np.zeros(k, dtype=bool)
    inside[0] = True
    best = A[0].copy()
    links = []
    for _ in range(k - 1):
        j = int(np.argmax(np.where(inside, -np.inf, best)))
        links.append(float(best[j]))
        inside[j] = True
        best = np.maximum(best, A[j])
    return min(links)


def union_find(n: int, edges) -> list[list[int]]:
    """Connected groups (two or more members) of n items under the given edges, members sorted, groups by first."""
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, j in edges:
        ri, rj = find(int(i)), find(int(j))
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return sorted((g for g in groups.values() if len(g) > 1), key=lambda g: g[0])


def redundancy(X: np.ndarray, columns: list[str], feature_of: list[str], constant=None) -> dict:
    """Redundancy of a standardised design X (rows x C): constant columns, exact duplicates, highly correlated pairs,
    clusters at |r| >= 0.9 (union-find), rank, effective rank (participation ratio of the correlation eigenvalues)
    and condition number of the correlation matrix (None when singular). A cluster is single linkage, a chain of
    pairs at |r| >= 0.9, so its two ends may hardly correlate: its weakest link (the smallest |r| of a maximum
    spanning tree, at least 0.9) is what defines it, and the all-pairs minimum is kept apart as min_pair_abs_r."""
    X = np.asarray(X, dtype=np.float64)
    C = X.shape[1]
    constant = (X.std(axis=0) <= 1e-12) if constant is None else np.asarray(constant, dtype=bool)
    R = corr_from_gram(X.T @ X, constant)
    iu, ju = np.triu_indices(C, 1)
    ok = ~constant[iu] & ~constant[ju]
    iu, ju = iu[ok], ju[ok]
    a = np.abs(R[iu, ju])
    order = np.lexsort((ju, iu, -a))
    top = [{"a": columns[iu[k]], "b": columns[ju[k]], "r": float(R[iu[k], ju[k]])} for k in order[:TOP_PAIRS]]
    dup = union_find(C, [(i, j) for i, j, v in zip(iu, ju, a) if v >= DUPLICATE_R])
    clus = union_find(C, [(i, j) for i, j, v in zip(iu, ju, a) if v >= CORR_HIGH])
    nc = np.flatnonzero(~constant)
    lam = np.clip(np.linalg.eigvalsh(R[np.ix_(nc, nc)]), 0.0, None) if nc.size else np.zeros(0)
    eff = float(lam.sum() ** 2 / (lam ** 2).sum()) if lam.size and (lam ** 2).sum() > 0 else 0.0
    cond = float(lam.max() / lam.min()) if lam.size and lam.min() > lam.max() * 1e-12 else None

    def rec(g):
        A = np.abs(R[np.ix_(g, g)])
        sub = A[np.triu_indices(len(g), 1)]
        return {"columns": [columns[i] for i in g], "index": [int(i) for i in g],
                "features": list(dict.fromkeys(feature_of[i] for i in g)),
                "weakest_link_abs_r": weakest_link(A), "min_pair_abs_r": float(sub.min()),
                "max_abs_r": float(sub.max())}
    return {"n_columns": C, "constant_columns": [columns[i] for i in np.flatnonzero(constant)],
            "duplicate_groups": [[columns[i] for i in g] for g in dup],
            "n_duplicate_columns": int(sum(len(g) - 1 for g in dup)),
            "n_pairs_above_0.9": int((a >= CORR_HIGH).sum()), "n_pairs_above_0.7": int((a >= CORR_MID).sum()),
            "top_pairs": top, "clusters": [rec(g) for g in clus],
            "rank": int(np.linalg.matrix_rank(X)) if X.size else 0, "effective_rank": eff, "condition_number": cond}


def strongest_partner(R: np.ndarray, cols_f, others: dict, columns: list[str]) -> dict | None:
    """The column of another feature (others: feature -> column indices) most correlated with a column of this one;
    partners within TIE_TOL in |r| (exact duplicates) are tied, and the tie goes to the feature first by name."""
    cands = []
    for g, cols_g in others.items():
        if not cols_g or not len(cols_f):
            continue
        sub = R[np.ix_(cols_f, cols_g)]
        i, j = np.unravel_index(int(np.argmax(np.abs(sub))), sub.shape)
        r = float(sub[i, j])
        cands.append({"feature": g, "column": columns[cols_g[j]], "own_column": columns[cols_f[i]], "r": r})
    if not cands:
        return None
    top = max(abs(c["r"]) for c in cands)
    return min((c for c in cands if abs(c["r"]) >= top - TIE_TOL), key=lambda c: c["feature"])


# ------------------------------------------------------------------ merge test
def merge_transform(G: np.ndarray, n: int, clusters) -> tuple[np.ndarray, list[int], list[np.ndarray]]:
    """T (C x C_new) replacing each cluster's columns by their standardised projection on the first principal
    component, computed from G alone: the Gram matrix of THIS fit's standardised training rows, so the component
    never sees the rows the fit predicts. Kept columns come first, then one column per cluster."""
    C = G.shape[0]
    inside = {int(c) for cl in clusters for c in cl}
    keep = [c for c in range(C) if c not in inside]
    T = np.zeros((C, len(keep) + len(clusters)))
    for j, c in enumerate(keep):
        T[c, j] = 1.0
    loadings = []
    for m, cl in enumerate(clusters):
        cl = [int(c) for c in cl]
        A = G[np.ix_(cl, cl)]
        v = np.linalg.eigh(A)[1][:, -1]
        if v[int(np.argmax(np.abs(v)))] < 0:
            v = -v
        var = float(v @ A @ v) / max(int(n), 1)
        T[cl, len(keep) + m] = v / (np.sqrt(var) if var > 0 else 1.0)
        loadings.append(v)
    return T, keep, loadings


def merge_unit(unit: Unit, clusters) -> tuple[Unit, list[np.ndarray]]:
    T, _, loadings = merge_transform(unit.G, unit.n, clusters)
    return unit.transform(T), loadings


def merged_engine(engine: Engine, idx, clusters) -> Engine:
    """The engine of the model on columns idx with each cluster (indices into idx) merged into one column."""
    seed_units = {s: [(merge_unit(u.subset(idx), clusters)[0], rows) for u, rows in us]
                  for s, us in engine.seed_units.items()}
    return Engine(seed_units, merge_unit(engine.val_unit.subset(idx), clusters)[0], engine.n_train, engine.alphas)


def merge_test(engine: Engine, idx, clusters: list[dict]) -> list[dict]:
    """The merge test of the model on columns idx: each cluster at |r| >= 0.9 (redundancy's records, indices into
    idx) that spans two or more features replaced by its first principal component, then, when there are several,
    all of them at once; each with the cluster's weakest link (what joins it, at least 0.9) and its all-pairs minimum
    (the combined row: the smallest of each), the merged model's score and its paired difference from the full one."""
    idx = list(idx)
    full_vec = engine.score_idx(idx)["vector"]
    merges, qualifying = [], []
    for cl in clusters:
        if len(cl["features"]) < 2:
            continue
        qualifying.append(cl["index"])
        res = merged_engine(engine, idx, [cl["index"]]).score_idx(range(len(idx) - len(cl["index"]) + 1))
        merges.append({"columns": cl["columns"], "features": cl["features"],
                       "weakest_link_abs_r": cl["weakest_link_abs_r"], "min_pair_abs_r": cl["min_pair_abs_r"],
                       "n_columns": len(idx) - len(cl["index"]) + 1, "mean": res["mean"], "se": res["se"],
                       "alphas": [c["alpha"] for c in res["chosen"]], "vs_full": paired(res["vector"], full_vec)})
    if len(qualifying) > 1:
        n_new = len(idx) - sum(len(c) for c in qualifying) + len(qualifying)
        res = merged_engine(engine, idx, qualifying).score_idx(range(n_new))
        merges.append({"columns": "all clusters above", "features": sorted({f for m in merges for f in m["features"]}),
                       "weakest_link_abs_r": min(m["weakest_link_abs_r"] for m in merges),
                       "min_pair_abs_r": min(m["min_pair_abs_r"] for m in merges), "n_columns": n_new,
                       "mean": res["mean"], "se": res["se"], "alphas": [c["alpha"] for c in res["chosen"]],
                       "vs_full": paired(res["vector"], full_vec)})
    return merges


# ------------------------------------------------------------------ Lasso stability
def lasso_gram_path(G: np.ndarray, b: np.ndarray, n: int, lambdas) -> np.ndarray:
    """(C, n_lambda) Lasso coefficients minimising (1/(2n)) |yc - X w|^2 + lambda |w|_1 from G = X^T X and
    b = X^T yc alone (X: n rows with mean-zero columns, yc centred), by sklearn's coordinate descent on a square
    root Z of G (Z^T Z = G, Z^T t = b), scaled so that its objective is the same up to a constant."""
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import lasso_path
    lambdas = np.asarray(lambdas, dtype=np.float64)
    C = G.shape[0]
    lam, V = np.linalg.eigh((G + G.T) / 2.0)
    keep = lam > max(float(lam.max()) if lam.size else 0.0, 0.0) * 1e-12
    out = np.zeros((C, lambdas.size))
    if not keep.any():
        return out
    Vk, lk = V[:, keep], lam[keep]
    Z = np.sqrt(lk)[:, None] * Vk.T
    t = (Vk.T @ b) / np.sqrt(lk)
    s = np.sqrt(Z.shape[0] / max(int(n), 1))
    order = np.argsort(-lambdas, kind="stable")  # sklearn computes the path from the largest lambda down
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        _, coefs, _ = lasso_path(Z * s, t * s, alphas=lambdas[order], max_iter=100000, tol=1e-10)
    out[:, order] = coefs
    return out


def lasso_cv(cv_units: list[Unit], grid) -> np.ndarray:
    """Mean squared error per lambda of the grid, averaged over the folds: each fold's Lasso fitted on its own
    standardised training design (features recomputed without the fold) and scored on the fold's rows."""
    mse = np.zeros(len(grid))
    for u in cv_units:
        W = lasso_gram_path(u.G, u.b, u.n, grid)
        mse += unit_sse(u, W) / (u.n_out * u.n_genes) / len(cv_units)
    return mse


def _lasso_at_edge(lasso: dict) -> bool:
    """Whether cross-validation chose the smallest penalty of the grid (its error still falling there): the
    stable count then reflects an almost unpenalised fit and is flagged in the report."""
    lam, low = lasso.get("lambda"), lasso.get("grid_min")
    return lam is not None and low is not None and float(lam) <= float(low) * (1 + 1e-9)


def lasso_stability(X: np.ndarray, y: np.ndarray, groups: np.ndarray, cv_units: list[Unit], resamples: int,
                    seed: int, columns: list[str], feature_of: list[str]) -> dict:
    """sklearn Lasso on the standardised full-training design X (rows grouped by perturbation, groups[i] in
    0..n_groups-1). The penalty is chosen once by cross-validation over cv_units, the folds' own designs with every
    feature recomputed without the fold (minimum mean squared error over a log grid from the smallest lambda that
    zeroes every column of X); then `resamples` draws of half of the perturbations (seeded, without replacement) are
    fitted at that penalty and each column's selection frequency is recorded (a feature's frequency is the maximum
    over its columns). Also a short path: the columns kept at five lambdas spanning the grid."""
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import lasso_path
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    groups = np.asarray(groups, dtype=int)
    n_groups = int(groups.max()) + 1
    C = X.shape[1]

    def fit(rows, lams):
        Xr, yr = X[rows], y[rows]
        xm, ym = Xr.mean(axis=0), yr.mean()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            lam, coefs, _ = lasso_path(Xr - xm, yr - ym, alphas=np.asarray(lams, dtype=np.float64), max_iter=10000)
        return lam, coefs

    Xc = X - X.mean(axis=0)
    lam_max = float(np.max(np.abs(Xc.T @ (y - y.mean()))) / len(y)) if C else 0.0
    del Xc
    if lam_max <= 0:
        lam_max = 1.0
    grid = lam_max * np.logspace(0, np.log10(LASSO_RATIO), LASSO_LAMBDAS)
    mse = lasso_cv(cv_units, grid)
    k = int(np.argmin(mse))  # ties: the larger lambda
    chosen = float(grid[k])
    rng = np.random.default_rng(int(seed))
    counts = np.zeros(C)
    mag = np.zeros(C)
    for _ in range(int(resamples)):
        sub = rng.choice(n_groups, n_groups // 2, replace=False)
        _, coefs = fit(np.isin(groups, sub), [chosen])
        counts += np.abs(coefs[:, 0]) > 1e-12
        mag += np.abs(coefs[:, 0])
    freq = counts / max(int(resamples), 1)
    ranking = sorted(range(C), key=lambda i: (-freq[i], -mag[i], columns[i]))  # ties: by column name
    path_lams = grid[np.unique(np.round(np.linspace(0, len(grid) - 1, 5)).astype(int))]
    lam_p, coefs_p = fit(np.ones(len(y), dtype=bool), path_lams)
    path = [{"lambda": float(lam_p[i]), "n_columns": int((np.abs(coefs_p[:, i]) > 1e-12).sum()),
             "columns": [columns[c] for c in np.flatnonzero(np.abs(coefs_p[:, i]) > 1e-12)]}
            for i in range(len(lam_p))]
    feat_freq: dict[str, float] = {}
    for i, f in enumerate(feature_of):
        feat_freq[f] = max(feat_freq.get(f, 0.0), float(freq[i]))
    return {"lambda": chosen, "lambda_max": lam_max, "grid_min": float(grid[-1]), "n_lambdas": len(grid),
            "cv_mse": [float(m) for m in mse], "cv_folds": len(cv_units), "resamples": int(resamples),
            "seed": int(seed), "column_frequency": {columns[i]: float(freq[i]) for i in range(C)},
            "feature_frequency": feat_freq, "ranking": [columns[i] for i in ranking], "path": path,
            "stable_features": [f for f, v in feat_freq.items() if v >= STABLE_FREQ], "stable_threshold": STABLE_FREQ}


# ------------------------------------------------------------------ verdicts
def assign_verdicts(features: list[str], kept, n_columns: dict, single: dict, drop_one: dict, partner: dict,
                    kept_partner: dict, lasso_freq: dict | None, failed: dict,
                    unstable: dict | None = None) -> list[dict]:
    """One verdict per feature (the features analysed, then the unstable ones, then the unrecomputable ones), with
    its evidence. Order of the rules: unrecomputable, unstable, kept, harmful, redundant, substitutable, no_gain (see
    RULE). unstable: {feature: {"reason", "evidence"}} (unstable_records), features left out of the analysis, so none
    of them is ever kept. required_input, which outranks every verdict but kept and unstable, needs the kept features
    of both scopes and is set afterwards (mark_required); no kept feature ever needs an unstable one, since a feature
    that computes an unstable one is unstable itself."""
    kept = set(kept)
    unstable = {f: u for f, u in (unstable or {}).items() if f not in failed}
    out = []
    for f in list(features) + [g for g in unstable if g not in features] + [g for g in failed if g not in features]:
        if f in failed:
            out.append({"feature": f, "verdict": "unrecomputable", "reason": str(failed[f])[:200],
                        "evidence": {"columns": None, "single": None, "drop_one": None, "lasso_frequency": None,
                                     "partner": None}})
            continue
        if f in unstable:
            u = unstable[f]
            out.append({"feature": f, "verdict": "unstable", "reason": str(u["reason"])[:300],
                        "evidence": {"columns": u.get("columns"), "single": None, "drop_one": None,
                                     "lasso_frequency": None, "partner": None,
                                     "hash_check": dict(u.get("evidence") or {})}})
            continue
        d, s, kp = drop_one[f], single[f], kept_partner.get(f)
        ev = {"columns": int(n_columns[f]), "single": {"mean": s["mean"], "se": s["se"]},
              "drop_one": {"diff": d["diff"], "se": d["se"], "wins": d["wins"], "losses": d["losses"], "n": d["n"]},
              "lasso_frequency": None if lasso_freq is None else lasso_freq.get(f), "partner": partner.get(f)}
        band = noise_band(d["se"])
        if f in kept:
            v, why = "kept", "in the compact set (one-SE rule on the backward path, training scores)"
        elif d["diff"] < -band:
            v, why = "harmful", (f"dropping it raises the visible score by {-d['diff']:.4f}, more than max(paired SE "
                                 f"{d['se']:.4f}, {NOISE_FLOOR:g}); {d['losses']} of {d['n']} perturbations score "
                                 f"higher without it")
        elif kp is not None and abs(kp["r"]) >= CORR_HIGH:
            v, why = "redundant", (f"not in the compact set; its column {kp['own_column']} correlates "
                                   f"r = {kp['r']:+.3f} with {kp['column']} of kept feature {kp['feature']}")
        elif d["diff"] > band:
            v, why = "substitutable", (
                f"its gain in the full model is established (drop-one {d['diff']:+.4f}, paired SE {d['se']:.4f}), "
                f"yet the compact set does without it"
                + (f"; most correlated kept feature {kp['feature']} (r = {kp['r']:+.3f})" if kp else ""))
        else:
            v, why = "no_gain", (f"not in the compact set; dropping it from the full model changes the visible score "
                                 f"by {-d['diff']:+.4f} (paired SE {d['se']:.4f}), within max(SE, {NOISE_FLOOR:g})")
        out.append({"feature": f, "verdict": v, "reason": why, "evidence": ev})
    return out


# ------------------------------------------------------------------ composites: what a kept feature needs
def _params_key(params) -> str:
    """The parameters a feature was called with, as FeatureContext.feature keys its memo (None and {} alike)."""
    return json.dumps(params or {}, sort_keys=True, default=str)


def dependency_map(calls: dict, computed: dict | None = None) -> dict:
    """The features each feature computes through ctx.feature. calls: {feature: {caller: [callees]}}, the calls
    recorded on that feature's own fresh view (and the views derived from it), where the caller is the feature itself
    or a feature it called; computed: {feature: [{"name", "params", "columns"}]}, the distinct computations those
    calls returned on the same view. Returns {feature: {"direct": names it called itself, "transitive": every name
    reached on its view, "computed": what returned there, sorted}}, for the features that called any. The walk stays
    on the feature's own view, and that is complete: the view starts with empty memos after the plugins were
    re-executed, and a call is recorded before any memo is consulted, so it holds every name the feature computes,
    nested calls included. What a callee calls on its own view, with the run's parameters rather than the ones the
    feature passed it, is not something the feature needs, so it is not added."""
    computed = computed or {}
    out = {}
    for f, edges in calls.items():
        seen, todo = set(), list(edges.get(f, []))
        while todo:
            g = todo.pop()
            if g != f and g not in seen:
                seen.add(g)
                todo.extend(edges.get(g, []))
        if seen:
            done = sorted((c for c in computed.get(f, []) if c["name"] in seen),
                          key=lambda c: (c["name"], _params_key(c.get("params"))))
            out[f] = {"direct": sorted(set(edges.get(f, [])) - {f}), "transitive": sorted(seen),
                      "computed": [{"name": c["name"], "params": c.get("params") or {}, "columns": int(c["columns"])}
                                   for c in done]}
    return out


def required_by(kept, deps: dict) -> dict[str, list[str]]:
    """Every feature that a kept feature needs (deps: dependency_map, transitive), with the kept features that need
    it, in the order they are given."""
    out: dict[str, list[str]] = {}
    for k in dict.fromkeys(kept):
        for g in (deps.get(k) or {}).get("transitive", []):
            if g != k:
                out.setdefault(g, []).append(k)
    return out


def mark_required(verdicts: list[dict], req: dict[str, list[str]]) -> None:
    """In place: every verdict but kept and unstable of a feature that kept features need becomes required_input,
    naming them; the verdict it would otherwise have stays in its evidence (verdict_otherwise), and so does its own
    evidence. Applying it again with more kept features only widens required_by. An unstable feature stays unstable
    and boxed: no kept feature needs one (a feature computing it is unstable itself, outside every compact set)."""
    for v in verdicts:
        f = v["feature"]
        if v["verdict"] in ("kept", "unstable") or f not in req:
            continue
        ev = dict(v.get("evidence") or {})
        if v["verdict"] != "required_input":
            ev["verdict_otherwise"] = v["verdict"]
            ev["reason_otherwise"] = v["reason"]
        ev["required_by"] = list(req[f])
        v["verdict"] = "required_input"
        v["reason"] = (f"computed through ctx.feature by kept feature(s) {_names(req[f], 3)}, which a lab that banned "
                       f"it could not compute" + (f"; otherwise {ev['verdict_otherwise']}"
                                                  if ev.get("verdict_otherwise") else ""))
        v["evidence"] = ev


def expanded_size(features: list[str], n_columns: int, deps: dict) -> dict:
    """A model's size with its required inputs expanded (a compact set's or a full model's): the features its members
    compute through ctx.feature on their own views (transitively) that are not members themselves, and the features
    and columns computed in all, the model's own plus each distinct computation of an input (name and parameters as
    called) once, with the columns it returned on a member's view, never what a call by a feature outside the model
    returned. A name whose every call raised there (a composite may catch that) was never computed: it is listed
    apart (failed_inputs; a kept member still needs it) and counted nowhere."""
    own = set(features)
    needed = {g for f in features for g in (deps.get(f) or {}).get("transitive", [])} - own
    done: dict[tuple, int] = {}
    for f in features:
        for c in (deps.get(f) or {}).get("computed", []):
            if c["name"] in needed:
                key = (c["name"], _params_key(c.get("params")))
                done[key] = max(done.get(key, 0), int(c["columns"]))
    inputs = sorted({name for name, _ in done})
    return {"required_inputs": inputs, "failed_inputs": sorted(needed - set(inputs)),
            "n_features_expanded": len(features) + len(inputs),
            "n_columns_expanded": int(n_columns) + int(sum(done.values()))}


def apply_dependencies(r: dict) -> None:
    """In place, on one run, with whatever verdicts it has so far (it is applied again when the pool's are in, and
    when the audit fails after the selected model's): a feature kept in either scope's compact set (or with the
    verdict kept) that computes others through ctx.feature (r["dependencies"]) makes each of them required_input in
    every scope where it is not kept itself, and each scope's full model and compact set get their size with their
    required inputs expanded."""
    deps = r.get("dependencies") or {}
    scopes = [a for a in (r.get("selected_analysis"), r.get("pool")) if a]
    kept = [f for a in scopes for f in (a.get("compact") or {}).get("features", [])]
    kept += [v["feature"] for a in scopes for v in a.get("verdicts") or [] if v["verdict"] == "kept"]
    req = required_by(kept, deps)
    for a in scopes:
        mark_required(a.get("verdicts") or [], req)
        for key in ("census", "compact"):
            if a.get(key):
                a[key].update(expanded_size(a[key]["features"], a[key]["n_columns"], deps))


def analyse_model(engine: Engine, features: list[str], R: np.ndarray, columns: list[str], failed: dict,
                  lasso_freq: dict | None = None, log=_quiet, label: str = "", unstable: dict | None = None) -> dict:
    """Census, single-feature and drop-one scores, forward and backward paths, the compact choice and verdicts of
    one feature set on an engine. R: the correlation matrix of the engine's columns (full training design). The
    paths and the compact set are chosen on the training perturbations; the compact model is compared with the full
    one on the validation perturbations (and, for reference, on the training ones that chose it). failed and
    unstable (unstable_records) are the scope's features left out of it, which only get their verdicts."""
    full = engine.score(features)
    single = {f: engine.score([f]) for f in features}
    drop = {f: paired(full["vector"], engine.score([g for g in features if g != f])["vector"]) for f in features}
    fwd = forward_path(engine, features, log, f"{label} forward".strip())
    bwd = backward_path(engine, features, log, f"{label} backward".strip())
    tvecs = [engine.train_part(engine.score(st["features"])["vector"]) for st in bwd]
    pick, best, cmp = one_se_choice(tvecs, [(st["n_features"], st["n_columns"]) for st in bwd])
    for st, c in zip(bwd, cmp):
        st["vs_best"] = {"diff": c["diff"], "se": c["se"]}
    comp_feats = bwd[pick]["features"]
    comp = engine.score(comp_feats)
    cols_of = {f: engine.columns_of[f] for f in features}
    partner = {f: strongest_partner(R, cols_of[f], {g: cols_of[g] for g in features if g != f}, columns)
               for f in features}
    kept_partner = {f: strongest_partner(R, cols_of[f], {g: cols_of[g] for g in comp_feats if g != f}, columns)
                    for f in features if f not in comp_feats}
    verdicts = assign_verdicts(features, comp_feats, {f: len(cols_of[f]) for f in features}, single, drop, partner,
                               kept_partner, lasso_freq, failed, unstable)
    vs_val = paired(engine.val_part(comp["vector"]), engine.val_part(full["vector"]))
    vs_val["class"] = classify(vs_val["diff"], vs_val["se"])

    def summ(r):
        return {"mean": r["mean"], "se": r["se"], "n": r["n"], "train_mean": r["train_mean"],
                "train_se": r["train_se"], "val_mean": r["val_mean"], "val_se": r["val_se"],
                "alphas": [c["alpha"] for c in r["chosen"]], "chosen": r["chosen"], "alpha": r["alpha"]}
    return {
        "census": {"features": list(features), "columns_per_feature": {f: len(cols_of[f]) for f in features},
                   "n_features": len(features), "n_columns": len(engine.columns(features))},
        "full": summ(full),
        "single": {f: {"mean": r["mean"], "se": r["se"], "alpha": r["alpha"]} for f, r in single.items()},
        "drop_one": drop, "forward": fwd, "backward": bwd,
        "compact": {"features": comp_feats, "n_features": len(comp_feats),
                    "n_columns": len(engine.columns(comp_feats)), **summ(comp),
                    "backward_step": pick, "best_step": best, "vs_full": vs_val,
                    "vs_full_train": paired(engine.train_part(comp["vector"]), engine.train_part(full["vector"])),
                    "vs_best": cmp[pick]},
        "verdicts": verdicts,
    }


# ================================================================== opening a run, read only
def open_db_readonly(run_dir: Path, scratch: Path) -> sqlite3.Connection:
    """lab.db through a read-only URI. With no write-ahead log next to it the file is opened immutable (SQLite
    creates nothing beside it); with one (an unclean or live run) the database and its log are copied into the
    tool's scratch directory first and the copy is opened, so nothing is ever created in the run directory."""
    db = Path(run_dir) / "lab.db"
    if not db.exists():
        raise Skip("no lab.db")
    wal = Path(run_dir) / "lab.db-wal"
    if wal.exists() and wal.stat().st_size > 0:
        dst = Path(scratch) / "labdb"
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(db, dst / "lab.db")
        shutil.copyfile(wal, dst / "lab.db-wal")
        uri = f"file:{quote(str(dst / 'lab.db'))}?mode=ro"
    else:
        uri = f"file:{quote(str(db))}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


JSON_COLUMNS = ("feature_set_json", "feature_params_json", "hyperparameters_json", "val_metrics_json",
                "query_metrics_json")


def _rows(conn: sqlite3.Connection, sql: str, params=()) -> list[dict]:
    out = []
    for r in conn.execute(sql, params).fetchall():
        d = dict(r)
        for k in JSON_COLUMNS:
            if k in d and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except ValueError:
                    d[k] = None
        out.append(d)
    return out


def read_run(run_dir: Path, scratch: Path) -> dict:
    conn = open_db_readonly(run_dir, scratch)
    try:
        runs = _rows(conn, "SELECT * FROM runs LIMIT 1")
        if not runs:
            raise Skip("no run recorded in lab.db")
        cfg = json.loads(runs[0]["config_json"] or "{}")
        sel = _rows(conn, "SELECT * FROM experiments WHERE status='completed' AND primary_score IS NOT NULL "
                          "AND COALESCE(kind, '') NOT IN ('baseline', 'ensemble') "
                          "ORDER BY primary_score DESC, COALESCE(finished_at, 1e300) ASC, experiment_id ASC")
        sel = [r for r in sel if r.get("feature_set_json")]
        gains = _rows(conn, "SELECT experiment_id, new_feature, feature_params_json, delta_from_parent, finished_at "
                            "FROM experiments WHERE status='completed' AND new_feature IS NOT NULL "
                            "AND new_feature != '' ORDER BY COALESCE(finished_at, 1e300) ASC, experiment_id ASC")
        try:
            feats = {r["name"]: r for r in _rows(conn, "SELECT name, code_hash, description FROM features")}
        except sqlite3.Error:
            feats = {}
    finally:
        conn.close()
    return {"run_id": runs[0]["run_id"], "split_id": runs[0].get("split_id"), "dataset": runs[0].get("dataset"),
            "base_commit": runs[0].get("base_commit"), "cfg": cfg, "selected": sel[0] if sel else None,
            "gains": gains, "features": feats}


def _resolve_data_dir(raw) -> Path | None:
    if not raw:
        return None
    p = Path(str(raw))
    for cand in ([p] if p.is_absolute() else [REPO_ROOT / p, Path.cwd() / p]):
        if cand.exists():
            return cand.resolve()
    return p


@contextlib.contextmanager
def _no_bytecode():
    """Plugins are imported from the run's feature store: no __pycache__ may be written there."""
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = old


def _err(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"[:200]


def _module_features() -> dict[str, list[str]]:
    """Plugin module name -> the registered features whose class it defines."""
    out: dict[str, list[str]] = {}
    for name, cls in REGISTRY.items():
        out.setdefault(getattr(cls, "__module__", ""), []).append(name)
    return out


def load_run_plugins(store: Path) -> dict[str, str]:
    """The run's feature plugins, afresh and one file at a time: no feature of a previous run survives by name, a file
    that raises while importing (a missing package, a syntax error) is recorded and skipped while every other file
    still loads, and reloads before each fold re-execute only this run's modules. Returns {file stem: error}."""
    for name in list(REGISTRY):
        if name not in BUILTIN_FEATURES:
            del REGISTRY[name]
    registry._LOADED.clear()
    errors: dict[str, str] = {}
    for path in sorted(Path(store).glob("*.py")):
        if path.name.startswith("_"):
            continue
        before = set(REGISTRY)
        try:
            registry._exec(path)
        except BaseException as exc:  # noqa: BLE001  (a plugin may even call sys.exit)
            if isinstance(exc, KeyboardInterrupt):
                raise
            errors[path.stem] = _err(exc)
            for name in set(REGISTRY) - before:  # half-executed module: none of its features is trusted
                del REGISTRY[name]
            sys.modules.pop(f"genemila_plugin_{path.stem}", None)
    return errors


def reload_run_plugins() -> dict[str, str]:
    """Re-execute every loaded plugin module, as registry.reload_plugins does before each fold, so module-level state
    starts fresh; a module that raises on re-execution makes the features it defines unrecomputable instead of
    stopping the run. Returns {feature: error}."""
    owned = _module_features()
    failed: dict[str, str] = {}
    for mod_name, path in list(registry._LOADED.items()):
        if not Path(path).exists():
            continue
        try:
            registry._exec(Path(path))
        except BaseException as exc:  # noqa: BLE001
            if isinstance(exc, KeyboardInterrupt):
                raise
            for name in owned.get(mod_name, []):
                failed[name] = f"plugin {Path(path).name} failed on re-execution: {_err(exc)}"[:200]
    return failed


def missing_feature_errors(features: list[str], store: Path, plugin_errors: dict[str, str]) -> dict[str, str]:
    """Why a feature is not registered after loading: its own plugin file failed to import, or no file defines it."""
    out = {}
    for f in features:
        if f in REGISTRY:
            continue
        if f in plugin_errors:
            out[f] = f"plugin {f}.py failed to import: {plugin_errors[f]}"[:200]
        elif plugin_errors:
            out[f] = (f"no imported plugin defines it ({len(plugin_errors)} plugin file(s) failed to import, "
                      f"e.g. {next(iter(plugin_errors))}.py: {next(iter(plugin_errors.values()))})")[:200]
        else:
            out[f] = f"no plugin in {Path(store).name} defines it"
    return out


def _pool(meta: dict, sel_feats: list[str], sel_params: dict) -> tuple[list[str], dict, dict]:
    """The selected model's features, every new feature of a completed experiment that raised its parent's visible
    score by more than POOL_MIN_GAIN (largest gain first), and the built-ins; parameters of each, and the experiment
    that introduced each."""
    pool, params = list(sel_feats), {f: dict(sel_params.get(f, {})) for f in sel_feats}
    gains = sorted((g for g in meta["gains"] if (g.get("delta_from_parent") or 0.0) > POOL_MIN_GAIN),
                   key=lambda g: (-(g["delta_from_parent"]), g["experiment_id"]))
    for g in gains:
        f = g["new_feature"]
        if f not in pool:
            pool.append(f)
            params[f] = dict((g.get("feature_params_json") or {}).get(f, {}))
    for f in BUILTIN_FEATURES:
        if f not in pool:
            pool.append(f)
            params[f] = {}
    introduced = {}
    for g in meta["gains"]:
        introduced.setdefault(g["new_feature"], g["experiment_id"])
    return pool, params, introduced


# ------------------------------------------------------------------ the fits of one run
class LabelWatch(FeatureContext):
    """A fresh view of a context (empty memos, the same training set) that counts every read of the training labels,
    through train_delta or directly through the private _train_delta, also from views a feature derives from it (the
    counter is shared by copies), so that a feature's label dependence is detected however it reaches the labels.
    It records, the same way, every registered feature computed through ctx.feature: who called which name (the
    owner, or a feature the owner called, and so on down), before the name is even looked up, so that a call of a
    name that is not registered, or that a memo answers, is recorded too; and, per name and parameters as called, how
    many columns the call returned (nothing for a call that raised)."""

    def __init__(self, base: FeatureContext, owner: str | None = None):  # a view: __init__ would reload the data
        state = dict(base.without_train([]).__dict__)
        state.pop("label_reads", None)
        state["_watched_delta"] = state.pop("_train_delta")
        state["_watch_counter"] = [0]
        state["_watch_calls"] = {}                              # caller -> {callee: None}, an ordered set
        state["_watch_stack"] = [] if owner is None else [str(owner)]
        state["_watch_computed"] = {}                           # (callee, parameters) -> columns returned
        self.__dict__.update(state)

    def feature(self, name: str, perts: list[str], params: dict | None = None) -> np.ndarray:
        stack = self.__dict__["_watch_stack"]
        self.__dict__["_watch_calls"].setdefault(stack[-1] if stack else None, {}).setdefault(str(name), None)
        stack.append(str(name))
        try:
            arr = super().feature(name, perts, params)
        finally:
            stack.pop()
        shape = np.shape(arr)
        if len(shape) in (2, 3):
            done, key = self.__dict__["_watch_computed"], (str(name), _params_key(params))
            done[key] = max(done.get(key, 0), 1 if len(shape) == 2 else int(shape[2]))
        return arr

    @property
    def feature_calls(self) -> dict:
        """{caller: [callees]} in the order first called (caller None: a call made with no owner)."""
        return {k: list(v) for k, v in self.__dict__["_watch_calls"].items()}

    @property
    def feature_computed(self) -> list[dict]:
        """[{"name", "params" (as called), "columns"}]: each distinct computation that returned, in the order it did."""
        return [{"name": n, "params": json.loads(k), "columns": c}
                for (n, k), c in self.__dict__["_watch_computed"].items()]

    @property
    def label_reads(self) -> int:
        return self.__dict__["_watch_counter"][0]

    @label_reads.setter
    def label_reads(self, value: int) -> None:
        self.__dict__["_watch_counter"][0] = int(value)

    @property
    def _train_delta(self) -> np.ndarray:
        self.__dict__["_watch_counter"][0] += 1
        return self.__dict__["_watched_delta"]

    @_train_delta.setter
    def _train_delta(self, value: np.ndarray) -> None:
        self.__dict__["_watched_delta"] = value


def compute_fits(ctx: FeatureContext, features: list[str], params: dict, seeds: list[int], k: int,
                 val_perts: list[str], Y_val: np.ndarray, failed: dict | None = None,
                 groups: str | None = None) -> dict:
    """Feature blocks and engine units of one run, as genemila.pipeline computes them but with label dependence
    detected per feature on a clean slate: each feature's blocks of the training perturbations and of every
    perturbation outside the training set are computed on its own fresh view (plugins re-executed first, so neither
    another feature's memo nor a module-level memo can hide a read of the labels), which counts every read of the
    training labels and every feature it computes through ctx.feature (calls: {feature: {caller: [callees]}},
    computed: {feature: what those calls returned on its view, with their columns}). Then, for each fold seed and
    fold, plugins re-executed and the label-dependent features recomputed on the view without the fold (training rows
    plus fold rows in one call); a label-free feature's rows are sliced from its full-training block, which no label
    shaped. Nothing is cached on disk. A feature that raises anywhere is dropped (failed), the calls it made before
    raising still recorded; `failed` may carry features already known to be unrecomputable. The folds are the run's
    (genemila.pipeline.cv_folds_of under its cv_groups setting, `groups`): a fold's view hides its hidden set and
    its unit predicts the fold's own perturbations, which under random folds are one and the same."""
    train = list(ctx.train_perts)
    evals = [p for p in ctx.perts if p not in set(train)]
    G = ctx.n_genes
    timings: dict = {}
    failed = dict(failed or {})
    label_dep: dict[str, bool] = {}
    full_tr, full_ev = {}, {}
    calls: dict[str, dict] = {}
    computed: dict[str, list] = {}

    def reload_marking():
        for f, e in reload_run_plugins().items():
            if f in features and f not in failed:
                failed[f] = e
    for f in features:
        if f in failed:
            continue
        reload_marking()
        if f in failed:
            continue
        view = LabelWatch(ctx, owner=f)
        try:
            full_tr[f] = feature_blocks(view, [f], params, train, timings, None, None, label_dep)[f]
            blk = feature_blocks(view, [f], params, evals, timings, None, None, label_dep)[f]
            if blk.shape[2] != full_tr[f].shape[2]:
                raise ValueError(f"feature {f} returned {blk.shape[2]} columns for held-out perturbations, "
                                 f"{full_tr[f].shape[2]} for training ones")
            full_ev[f] = blk
        except Exception as exc:  # missing dependency, bad shape, NaN: unrecomputable
            failed[f] = _err(exc)
            full_tr.pop(f, None)
        calls[f], computed[f] = view.feature_calls, view.feature_computed  # per feature: its own calls only
    _, D = ctx.train_delta()
    pos = {p: i for i, p in enumerate(train)}
    raw_units: dict[int, list] = {}
    for s in seeds:
        units = []
        for fold, hide in cv_folds_of(train, k, s, cv_fold_targets(ctx, groups)):
            reload_marking()
            view = ctx.without_train(hide)
            both = view.train_perts + fold
            n_tr = len(view.train_perts)
            fresh = {}
            for f in features:
                if f in failed or not label_dep.get(f, True):
                    continue
                try:
                    blk = feature_blocks(view, [f], params, both, timings, None)[f]
                    if blk.shape[2] != full_tr[f].shape[2]:
                        raise ValueError(f"feature {f} returned {blk.shape[2]} columns without a fold, "
                                         f"{full_tr[f].shape[2]} on the full training set")
                    fresh[f] = blk
                except Exception as exc:
                    failed[f] = _err(exc)
            ok = [f for f in features if f not in failed]
            if not ok:
                raise Skip("no feature could be recomputed: " + "; ".join(f"{f}: {e}" for f, e in failed.items())[:300])
            tr_rows = [pos[p] for p in view.train_perts]
            fo_rows = [pos[p] for p in fold]
            Xtr = np.concatenate([fresh[f][:n_tr] if f in fresh else full_tr[f][tr_rows] for f in ok], axis=2)
            Xfo = np.concatenate([fresh[f][n_tr:] if f in fresh else full_tr[f][fo_rows] for f in ok], axis=2)
            _, d_tr = view.train_delta()
            unit = make_unit(Xtr.reshape(n_tr * G, -1), d_tr.reshape(-1), Xfo.reshape(len(fold) * G, -1), D[fo_rows])
            units.append((unit, np.asarray(fo_rows), ok))
            del Xtr, Xfo, fresh
        raw_units[s] = units
    ok = [f for f in features if f not in failed]
    if not ok:
        raise Skip("no feature could be recomputed")
    dims = {f: int(full_tr[f].shape[2]) for f in ok}
    columns, feature_of, columns_of = [], [], {}
    for f in ok:
        columns_of[f] = list(range(len(columns), len(columns) + dims[f]))
        columns += [f] if dims[f] == 1 else [f"{f}[{j}]" for j in range(dims[f])]
        feature_of += [f] * dims[f]

    def final_idx(unit_feats):
        off, at = {}, 0
        for f in unit_feats:
            off[f] = at
            at += int(full_tr[f].shape[2])
        return [off[f] + j for f in ok for j in range(dims[f])]
    seed_units = {s: [(u if fs == ok else u.subset(final_idx(fs)), rows) for u, rows, fs in us]
                  for s, us in raw_units.items()}
    Xtr_raw = np.concatenate([full_tr[f] for f in ok], axis=2).reshape(len(train) * G, -1)
    Xev_raw = np.concatenate([full_ev[f] for f in ok], axis=2).reshape(len(evals) * G, -1)
    mu, sd_raw = Xtr_raw.mean(axis=0), Xtr_raw.std(axis=0)
    constant = sd_raw <= 1e-12 * np.maximum(1.0, np.abs(mu))
    Xtr_s, (Xev_s,), _, _ = standardise(Xtr_raw, Xev_raw)
    del Xtr_raw, Xev_raw
    ev_pos = {p: i for i, p in enumerate(evals)}
    C = len(columns)
    Xval = Xev_s.reshape(len(evals), G, C)[[ev_pos[p] for p in val_perts]].reshape(-1, C)
    y = D.reshape(-1)
    val_unit = unit_from_standardised(Xtr_s, y, Xval, np.asarray(Y_val, dtype=np.float64))
    return {"features": ok, "columns": columns, "feature_of": feature_of, "columns_of": columns_of,
            "seed_units": seed_units, "val_unit": val_unit, "Xtr": Xtr_s, "Xev": Xev_s, "y": y, "evals": evals,
            "constant": constant, "failed": failed, "label_dependent": sorted(f for f in ok if label_dep.get(f, True)),
            "feature_cpu_s": {f: float(v) for f, v in timings.items()}, "calls": calls, "computed": computed}


# ------------------------------------------------------------------ the hash-seed check
# python_hash_seed (the seed of this process's str hashes) comes from genemila.sandbox, shared with the other tools


def _hash_seed_worker() -> int:
    """One process of the hash-seed check (hash_check starts it with PYTHONHASHSEED set). It reads its spec as JSON on
    stdin, loads the run's plugins as the audit does (load_run_plugins after seeding numpy with the model's seed),
    opens the run's public data and nothing else (no label of any held-out perturbation), and for each feature in
    order, with the plugins re-executed and numpy seeded afresh, so that no other feature's state reaches it, computes
    its block of the training perturbations on a fresh watched view, as compute_fits does, and writes a JSON header
    line and the block's float64 bytes to its data stream. A feature that raises sends the error instead. Whatever a
    plugin prints goes to stderr, never into the stream."""
    data = os.fdopen(os.dup(1), "wb")
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    spec = json.loads(sys.stdin.read())
    params, seed = spec.get("params") or {}, int(spec.get("seed") or 0)
    with _no_bytecode():
        np.random.seed(seed)
        load_run_plugins(Path(spec["store"]))
        ctx = FeatureContext(Path(spec["public"]), None)
        train = list(ctx.train_perts)
        for f in spec["features"]:
            head, blk = {"feature": f}, None
            try:
                failed = reload_run_plugins()
                if f in failed:
                    raise RuntimeError(failed[f])
                np.random.seed(seed)
                blk = np.ascontiguousarray(feature_blocks(LabelWatch(ctx, owner=f), [f], params, train, {}, None,
                                                          None, {})[f], dtype="<f8")
                head.update(ok=True, shape=list(blk.shape), nbytes=int(blk.nbytes))
            except BaseException as exc:  # noqa: BLE001  (a plugin may even call sys.exit)
                if isinstance(exc, KeyboardInterrupt):
                    raise
                head.update(ok=False, error=_err(exc))
                blk = None
            data.write(json.dumps(head).encode() + b"\n")
            if blk is not None:
                data.write(memoryview(blk).cast("B"))
            data.flush()
            del blk
    data.close()
    return 0


def _read_record(stream) -> dict | None:
    """One feature's record from a worker's data stream (its header, with the block under "block" when it returned
    one), or None when the stream ended or broke."""
    try:
        line = stream.readline()
        if not line:
            return None
        head = json.loads(line)
        if head.get("ok"):
            n = int(head["nbytes"])
            buf = stream.read(n)
            if len(buf) != n:
                return None
            head["block"] = np.frombuffer(buf, dtype="<f8").reshape(head["shape"])
        return head
    except (OSError, ValueError, KeyError, TypeError):
        return None


def compare_blocks(a: np.ndarray, b: np.ndarray) -> dict:
    """Two computations of one feature block (n_perts, n_genes, dim): its columns, the largest absolute difference and
    the largest difference in units of the column's scale, its standard deviation over all rows (the larger of the
    two; what the engine divides the column by), at least 1e-6 of its largest magnitude, so that a constant column is
    measured against its size; 0 for identical blocks. Blocks of different shapes have no difference (None)."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.shape != b.shape:
        return {"columns": None, "shapes": [list(a.shape), list(b.shape)], "max_abs_diff": None,
                "max_std_diff": None}
    C = int(a.shape[2]) if a.ndim == 3 else 1
    A, B = a.reshape(-1, C), b.reshape(-1, C)
    if np.array_equal(A, B):
        return {"columns": C, "max_abs_diff": 0.0, "max_std_diff": 0.0}
    d = np.abs(A - B).max(axis=0)
    scale = np.maximum(np.maximum(A.std(axis=0), B.std(axis=0)),
                       1e-6 * np.maximum(np.abs(A).max(axis=0), np.abs(B).max(axis=0)))
    rel = np.where(scale > 0, d / np.where(scale > 0, scale, 1.0), 0.0)
    return {"columns": C, "max_abs_diff": float(d.max()), "max_std_diff": float(rel.max())}


NO_SEED_FIXES = ("something no hash seed fixes (memory addresses: id(), or the order of a set of objects other than "
                 "strings and numbers)")


def hash_check(public_dir: Path, store: Path, features: list[str], params: dict, model_seed: int,
               seeds=HASH_SEEDS, repeat: bool = False) -> dict:
    """Every feature's block of the training perturbations computed once in each of several fresh processes, one per
    hash seed (PYTHONHASHSEED 0, 1 and 2) and, with repeat, a second one under the first seed, all running this
    file's own plugin loading (_hash_seed_worker) on the run's public data alone, side by side, and compared pair by
    pair as their blocks arrive, one block per process in memory at a time. A feature whose blocks differ between
    any two processes by more than HASH_TOL of a column's scale (compare_blocks), whose blocks differ in shape, or
    that raises in some processes only, depends on the seed (unstable); one whose two blocks under the same seed
    differ that way (repeat) follows something no hash seed fixes (same_seed), so the seed a run recorded does not
    reproduce it either. Returns {"seeds", "repeat", "tolerance", "checked" (the features computed in every process),
    "blocks" ({feature: the largest differences over every pair of processes, and the seeds of the "pair" with the
    largest scaled one}), "unstable" ({feature: reason}), "same_seed" (those of them that differ under one seed),
    "errors" ({feature: why it was not compared}; every feature when a process cannot even start, and then nothing
    is unstable, the audit going on as before the check existed)}."""
    seeds = [int(s) for s in seeds]
    if len(set(seeds)) != len(seeds) or len(seeds) < 2:
        raise ValueError("the hash-seed check compares at least two distinct seeds")
    out = {"seeds": seeds, "repeat": bool(repeat), "tolerance": HASH_TOL, "checked": [], "blocks": {},
           "unstable": {}, "same_seed": [], "errors": {}}
    features = list(features)
    if not features:
        return out
    run_seeds = seeds + ([seeds[0]] if repeat else [])  # one process each; the repeat is the last one
    labels = [str(s) for s in seeds] + ([f"{seeds[0]} (again)"] if repeat else [])
    same = (0, len(seeds)) if repeat else None
    spec = json.dumps({"public": str(public_dir), "store": str(store), "features": features, "params": params,
                       "seed": int(model_seed)}, default=str).encode()
    procs, alive, ended = [], [], {}
    try:
        for s, label in zip(run_seeds, labels):
            env = {k: v for k, v in os.environ.items() if k != HASH_REEXEC_ENV}
            env["PYTHONHASHSEED"] = str(s)
            try:
                procs.append(subprocess.Popen([sys.executable, str(Path(__file__).resolve()), HASH_WORKER_ARG],
                                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env))
            except OSError as exc:
                out["errors"] = {f: f"not compared: the process under PYTHONHASHSEED {label} did not start: "
                                    f"{_err(exc)}" for f in features}
                return out  # (finally stops the ones that did start)
            alive.append(True)
        for p in procs:
            with contextlib.suppress(OSError):  # one that died before reading its spec ends its stream at once
                p.stdin.write(spec)
                p.stdin.close()

        def end(i):
            if alive[i]:
                alive[i] = False
                with contextlib.suppress(subprocess.TimeoutExpired):
                    procs[i].wait(timeout=30)
                ended[i] = procs[i].poll()
        for f in features:
            recs = []
            for i, p in enumerate(procs):
                rec = _read_record(p.stdout) if alive[i] else None
                if rec is not None and rec.get("feature") != f:
                    rec = None
                if rec is None:
                    end(i)
                recs.append(rec)
            if any(r is None for r in recs):
                gone = [i for i, r in enumerate(recs) if r is None]
                out["errors"][f] = (f"not compared: the process under PYTHONHASHSEED "
                                    f"{'/'.join(labels[i] for i in gone)} ended early (exit code "
                                    f"{', '.join(str(ended.get(i)) for i in gone)})")
                continue
            bad = [i for i, r in enumerate(recs) if not r.get("ok")]
            if len(bad) == len(recs):
                out["errors"][f] = f"raised under every seed: {recs[0]['error']}"[:200]
                continue
            out["checked"].append(f)
            if bad:
                one_of_same = same is not None and (same[0] in bad) != (same[1] in bad)
                out["unstable"][f] = (f"it raised under PYTHONHASHSEED {'/'.join(labels[i] for i in bad)} only "
                                      f"({recs[bad[0]]['error'][:80]}), so whether it can be computed depends on "
                                      + (NO_SEED_FIXES if one_of_same else "Python's salted str hash"))
                if one_of_same:
                    out["same_seed"].append(f)
                continue
            pairs = {(i, j): compare_blocks(recs[i]["block"], recs[j]["block"])
                     for i in range(len(recs)) for j in range(i + 1, len(recs))}
            del recs
            shaped = sorted(ij for ij, c in pairs.items() if c["max_std_diff"] is None)
            if shaped:
                (i, j) = same if same in shaped else shaped[0]
                c = pairs[(i, j)]
                out["blocks"][f] = {**c, "pair": [run_seeds[i], run_seeds[j]]}
                out["unstable"][f] = (f"it returned {c['shapes'][0][-1]} column(s) under PYTHONHASHSEED {labels[i]} "
                                      f"and {c['shapes'][1][-1]} under {labels[j]}: its shape depends on "
                                      + (NO_SEED_FIXES if (i, j) == same else "Python's salted str hash"))
                if (i, j) == same:
                    out["same_seed"].append(f)
                continue
            i, j = max(pairs, key=lambda ij: pairs[ij]["max_std_diff"])
            if same is not None and pairs[same]["max_std_diff"] > HASH_TOL:
                i, j = same  # what no seed fixes is the finding, whatever the seeds add to it
            worst = pairs[(i, j)]
            cmp = {"columns": worst["columns"], "max_abs_diff": max(c["max_abs_diff"] for c in pairs.values()),
                   "max_std_diff": max(c["max_std_diff"] for c in pairs.values())}
            if cmp["max_std_diff"] > 0:
                cmp["pair"] = [run_seeds[i], run_seeds[j]]
            out["blocks"][f] = cmp
            if worst["max_std_diff"] > HASH_TOL:
                diff = (f"by up to {worst['max_abs_diff']:.3g} ({worst['max_std_diff']:.3g} column SDs, tolerance "
                        f"{HASH_TOL:g})")
                if (i, j) == same:
                    out["same_seed"].append(f)
                    out["unstable"][f] = (f"its training block differs between two processes under the same "
                                          f"PYTHONHASHSEED {labels[i]} {diff}: its values follow {NO_SEED_FIXES}, "
                                          "so its scores cannot be reproduced")
                else:
                    out["unstable"][f] = (f"its training block differs between processes under PYTHONHASHSEED "
                                          f"{labels[i]} and {labels[j]} {diff}: its values depend on Python's salted "
                                          "str hash (hash() of a name, or set order), so its scores cannot be "
                                          "reproduced")
        for i in range(len(procs)):
            end(i)
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
                p.wait()
            with contextlib.suppress(OSError):
                p.stdout.close()
    return out


def unstable_records(check: dict, deps: dict, features) -> dict:
    """{feature: {"reason", "columns", "evidence"}} of the unstable features among `features`: those the hash-seed
    check found unstable, then, since a lab that kept a composite would compute its inputs, every feature that
    computes one of them through ctx.feature on its own view (deps: dependency_map, transitive, so nested calls
    included), even when its own block agrees (evidence "via" names them)."""
    direct = check.get("unstable") or {}
    blocks = check.get("blocks") or {}
    out = {}
    for f in features:
        if f in direct:
            out[f] = {"reason": direct[f], "columns": (blocks.get(f) or {}).get("columns"),
                      "evidence": {"seeds": check.get("seeds"), **(blocks.get(f) or {})}}
    for f in features:
        via = sorted(set((deps.get(f) or {}).get("transitive", [])) & set(direct))
        if f not in out and via:
            out[f] = {"reason": (f"it computes unstable feature(s) {_names(via, 3)} through ctx.feature, so a lab "
                                 "keeping it would compute values that change with Python's hash seed"),
                      "columns": (blocks.get(f) or {}).get("columns"),
                      "evidence": {"seeds": check.get("seeds"), **(blocks.get(f) or {}), "via": via}}
    return out


def _model_alpha(sel: dict) -> tuple[str, float, int]:
    model_type = sel.get("model_type") or "ridge"
    hp = sel.get("hyperparameters_json") or {}
    alpha = 0.0 if model_type == "ols" else sel.get("best_alpha")
    if alpha is None:
        alpha = hp.get("alpha", 1.0)
    return model_type, float(alpha), int(sel.get("seed") or 0)


def _own_grid(sel: dict) -> list[float]:
    hp = sel.get("hyperparameters_json") or {}
    if (sel.get("model_type") or "ridge") == "ols":
        return [0.0]
    return [float(a) for a in (hp.get("alpha_grid") or [hp.get("alpha", 1.0)])]


def visible_reproduction(engine: Engine, idx, sel: dict, run_cv_folds: int, k: int, cv_seed: int) -> dict:
    """The lab's own visible scores of the selected model, recomputed by the engine at its best alpha: the validation
    perturbations always, the out-of-fold ones when the run used the same folds."""
    model_type, alpha, _ = _model_alpha(sel)
    if model_type not in ("ridge", "ols"):
        return {"available": False, "reason": f"{model_type} is audited as ridge"}
    stored = sel.get("val_metrics_json") or {}
    mats = engine.matrices(idx, [alpha])
    some = mats[engine.seeds[0]]
    out = {"available": True, "alpha": alpha,
           "validation": {"tool": float(some[0, engine.n_train:].mean()), "stored": stored.get("pearson_delta")},
           "out_of_fold": None}
    if run_cv_folds > 1 and run_cv_folds == k and cv_seed in mats:
        out["out_of_fold"] = {"tool": float(mats[cv_seed][0, :engine.n_train].mean()),
                              "stored": stored.get("pearson_delta_cv")}
    diffs = []
    for key in ("validation", "out_of_fold"):
        part = out[key]
        if part is not None:
            part["diff"] = None if part["stored"] is None else float(part["tool"] - part["stored"])
            if part["diff"] is not None:
                diffs.append(abs(part["diff"]))
    out["max_abs_diff"] = max(diffs) if diffs else None
    out["flag"] = bool(diffs and max(diffs) > REPRO_FLAG)
    return out


# ------------------------------------------------------------------ sealed scoring (off by default)
def score_sealed(data_dir: Path, selection: str, control_mean: np.ndarray, eval_perts: list[str],
                 predictions: dict, label: str) -> dict:
    """The tool's only read of the sealed perturbations, fixed before any result: one oracle instance of the tool's
    own with a budget of exactly two queries, scoring the two pre-computed predictions ("selected" then "compact",
    predicted deltas of every perturbation outside the training set) once each. Nothing returned here feeds back
    into any choice."""
    from genemila.benchmark.oracle import QueryOracle
    oracle = QueryOracle(Path(data_dir), max_queries=2, used=None, selection=selection)
    perts = oracle.perts
    pos = {p: i for i, p in enumerate(eval_perts)}
    missing = [p for p in perts if p not in pos]
    if missing:
        raise ValueError(f"sealed perturbations {missing[:3]} are not among the predicted ones")
    rows = [pos[p] for p in perts]
    out = {}
    for key in ("selected", "compact"):
        q = oracle.query(f"feature_audit:{label}:{key}", predictions[key][rows] + control_mean, perts, control_mean)
        out[key] = float(q["metrics"]["pearson_delta"])
    out["n_queries"] = len(oracle.queries)
    return out


def sealed_predictions(fits: dict, sel: dict, sel_idx, compact_idx, compact_alpha: float) -> dict:
    """Predicted deltas of every perturbation outside the training set: (a) the selected model's feature set refitted
    as the pipeline fits it (its model type, best alpha and seed, on the 50 training perturbations), (b) the compact
    model by ridge at its visibly chosen alpha; both stored at single precision, as the lab stores predictions."""
    model_type, alpha, seed = _model_alpha(sel)
    n_ev, n_genes = len(fits["evals"]), fits["val_unit"].n_genes
    model = make_model(model_type, alpha, seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(fits["Xtr"][:, sel_idx], fits["y"])
    pa = model.predict(fits["Xev"][:, sel_idx]).reshape(n_ev, n_genes)
    vu = fits["val_unit"]
    w = ridge_weights(vu.G, vu.b, compact_idx, compact_alpha)
    pb = (fits["Xev"][:, compact_idx] @ w + vu.ybar).reshape(n_ev, n_genes)
    return {"selected": pa.astype(np.float32).astype(np.float64), "compact": pb.astype(np.float32).astype(np.float64)}


# ------------------------------------------------------------------ one run
def arm_class(cfg: dict) -> str:
    """'no_llm' for the scripted controls and no-LLM continuations (fixed template features), else 'agent'."""
    return "no_llm" if (cfg.get("planner") or {}).get("provider") == "scripted" else "agent"


def audit_run(run_dir: Path, fold_seeds: list[int] | None = None, resamples: int = 50, use_pool: bool = True,
              sealed: bool = False, log=None) -> dict:
    """The audit of one run. A run that cannot be audited is returned as skipped with its reason (and whatever was
    known by then, such as its arm); an unexpected error is reported the same way, never raised."""
    run_dir = Path(run_dir).resolve()
    say = log or (lambda msg: print(msg, file=sys.stderr, flush=True))
    out = {"run": run_dir.name, "path": str(run_dir), "status": "skipped", "reason": None}
    try:
        _audit_run(out, run_dir, fold_seeds, resamples, use_pool, sealed,
                   lambda msg: say(f"[feature_audit] {run_dir.name}: {msg}"))
    except Skip as exc:
        out["status"], out["reason"] = "skipped", str(exc)
    except Exception as exc:  # one broken run must not lose the others; the traceback goes to stderr
        print(traceback.format_exc(), file=sys.stderr)
        out["status"], out["reason"] = "skipped", f"unexpected error: {_err(exc)}"
    if out["status"] != "audited" and out.get("dependencies") and out.get("selected_analysis"):
        with contextlib.suppress(Exception):  # whatever verdicts a failed audit left, the box takes them as they are:
            apply_dependencies(out)           # the inputs of what they keep must stay out of it on every path
    return out


def _audit_run(out: dict, run_dir: Path, fold_seeds, resamples: int, use_pool: bool, sealed: bool, log) -> None:
    t0 = time.perf_counter()
    timings: dict[str, float] = {}

    def lap(name, since):
        timings[name] = round(time.perf_counter() - since, 3)
        return time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="feature_audit_db_") as scratch:
        meta = read_run(run_dir, Path(scratch))
    cfg = meta["cfg"]
    if (run_dir / "config.json").exists():
        try:
            cfg = json.loads((run_dir / "config.json").read_text())
        except ValueError:
            pass
    summary = {}
    if (run_dir / "summary.json").exists():
        try:
            summary = json.loads((run_dir / "summary.json").read_text())
        except ValueError:
            summary = {}
    out.update(run_id=meta["run_id"], arm=run_arm(cfg, summary), arm_class=arm_class(cfg), dataset=meta["dataset"],
               split_id=meta["split_id"],
               selection_rule=str((cfg.get("experiment") or {}).get("selection") or "pearson_delta"))
    data_dir = _resolve_data_dir((cfg.get("run") or {}).get("data_dir"))
    out["data_dir"] = None if data_dir is None else str(data_dir)
    sel = meta["selected"]
    if data_dir is None or not data_dir.exists():
        raise Skip(f"data dir {out['data_dir']} is missing")
    if not (data_dir / "private" / "val1.npz").exists():
        raise Skip(f"visible validation labels missing under {data_dir}")
    manifest = json.loads((data_dir / "manifest.json").read_text()) if (data_dir / "manifest.json").exists() else {}
    if meta["split_id"] and manifest.get("split_id") and manifest["split_id"] != meta["split_id"]:
        raise Skip(f"data dir {data_dir} holds split {manifest['split_id']}, the run used {meta['split_id']}")
    if not (run_dir / "public_data" / "public.npz").exists():
        raise Skip("public_data/public.npz is missing")
    if not (run_dir / "feature_store").is_dir():
        raise Skip("feature_store (the run's plugins) is missing")
    if sel is None:
        raise Skip("no completed single experiment with a visible score")

    model_type, best_alpha, model_seed = _model_alpha(sel)
    hp = sel.get("hyperparameters_json") or {}
    ecfg, rcfg = cfg.get("experiment") or {}, cfg.get("run") or {}
    run_cv_folds = int(hp.get("cv_folds") or ecfg.get("cv_folds") or 0)
    k = run_cv_folds if run_cv_folds > 1 else 5
    cv_seed = int(hp.get("cv_seed", ecfg.get("cv_seed", rcfg.get("seed", 0))) or 0)
    cv_groups = hp.get("cv_groups")  # the run's fold grouping: "gene" for a bundle with pairs or a gene split
    seeds = list(dict.fromkeys(int(s) for s in (fold_seeds or [cv_seed, cv_seed + 1])))
    if len(seeds) < 2:
        raise ValueError("--fold-seeds needs at least two distinct seeds")
    alphas = sorted({a for a in _own_grid(sel) + list(FIXED_ALPHAS) if a >= 0})
    sel_feats_all = list(sel["feature_set_json"])
    sel_params = sel.get("feature_params_json") or {}
    if use_pool:
        pool, params, introduced = _pool(meta, sel_feats_all, sel_params)
    else:
        pool, params = list(sel_feats_all), {f: dict(sel_params.get(f, {})) for f in sel_feats_all}
        introduced = {}
        for g in meta["gains"]:
            introduced.setdefault(g["new_feature"], g["experiment_id"])
    out.update(selected={"experiment_id": sel["experiment_id"], "model_type": model_type,
                         "audited_as": "ridge", "best_alpha": best_alpha, "seed": model_seed,
                         "primary_score": sel.get("primary_score"), "features": sel_feats_all,
                         "feature_params": sel_params},
               folds=k, run_cv_folds=run_cv_folds, run_cv_seed=cv_seed, fold_seeds=seeds, alpha_grid=alphas,
               pool_features=pool if use_pool else None, introduced_by=introduced,
               feature_info={f: {"code_hash": (meta["features"].get(f) or {}).get("code_hash"),
                                 "description": ((meta["features"].get(f) or {}).get("description") or "")[:200]}
                             for f in pool})
    log(f"auditing {sel['experiment_id']} ({len(sel_feats_all)} features"
        + (f", pool of {len(pool)}" if use_pool else "") + f"), {k} folds, seeds {seeds}")
    t = time.perf_counter()
    store = run_dir / "feature_store"
    with _no_bytecode():
        np.random.seed(model_seed)  # as genemila.pipeline.run seeds before it loads the plugins
        plugin_errors = load_run_plugins(store)
        out["plugin_errors"] = plugin_errors
        if plugin_errors:
            log(f"{len(plugin_errors)} plugin file(s) failed to import: {', '.join(sorted(plugin_errors))}")
        ctx = FeatureContext(run_dir / "public_data", None)  # no disk cache: nothing outlives this run's audit
        val1 = LabelSet.load(data_dir / "private" / "val1.npz")
        train_set = set(ctx.train_perts)
        if any(p in train_set or p not in set(ctx.perts) for p in val1.perts) or val1.means.shape[1] != ctx.n_genes:
            raise Skip("the visible validation labels do not match the run's public data")
        pre_failed = missing_feature_errors(pool, store, plugin_errors)
        fits = compute_fits(ctx, pool, params, seeds, k, val1.perts, val1.means - ctx.control_mean, pre_failed,
                            groups=cv_groups)
    t = lap("features_and_fits", t)
    log(f"features computed, {len(fits['label_dependent'])} label-dependent ones recomputed for {len(seeds)} x {k} "
        f"folds, in {timings['features_and_fits']:.0f} s")
    failed = fits["failed"]
    out.update(n_train=len(ctx.train_perts), n_val=len(val1.perts), n_genes=ctx.n_genes,
               unrecomputable=failed, label_dependent=fits["label_dependent"], feature_cpu_s=fits["feature_cpu_s"],
               audit_format=AUDIT_FORMAT, dependencies=dependency_map(fits["calls"], fits["computed"]))
    if out["dependencies"]:
        log(f"{len(out['dependencies'])} composite feature(s) compute others through ctx.feature: "
            + _names(sorted(out["dependencies"]), 3))
    # ---- the hash-seed check: each feature's training block again under hash seeds 0, 1 and 2, in fresh processes.
    # A run that recorded the seed its experiment processes ran under (run.hash_seed, since the lab fixed it), audited
    # under that same seed, computed exactly the values this audit computes: its seed-dependent features (a set of
    # names iterated in order, which the guard allows) are the lab's own and are audited as any other. A run without
    # the record drew a seed in every process, and an audit under another seed computes other values: unstable
    run_seed, own = rcfg.get("hash_seed"), python_hash_seed()
    recorded = run_seed is not None and own.isdigit() and str(run_seed) == own
    # under the run's seed, a second process under it tells what no seed fixes (addresses) from what it does fix
    hc = out["hash_check"] = hash_check(run_dir / "public_data", store, fits["features"], params, model_seed,
                                        repeat=recorded)
    dependent = unstable_records(hc, out["dependencies"], fits["features"])
    noisy = unstable_records({**hc, "unstable": {f: why for f, why in hc["unstable"].items() if f in hc["same_seed"]}},
                             out["dependencies"], fits["features"])
    hc.update(via={f: u["evidence"]["via"] for f, u in dependent.items() if "via" in u["evidence"]},
              seed_dependent=sorted(dependent), run_hash_seed=run_seed, audit_hash_seed=own, reproducible=recorded)
    unstable = noisy if recorded else dependent
    t = lap("hash_check", t)
    log(f"hash-seed check of {len(hc['checked'])} feature(s) under PYTHONHASHSEED "
        f"{', '.join(map(str, HASH_SEEDS))} in {timings['hash_check']:.0f} s: "
        + ("none depends on the seed" if not dependent else
           f"{len(dependent) - len(unstable)} depend on it ({_names([f for f in dependent if f not in unstable], 3)}),"
           f" audited as any other: the run recorded hash seed {run_seed} and the audit runs under it"
           + (f"; {len(unstable)} unstable under that seed too ({_names(list(unstable), 3)})" if unstable else "")
           if recorded else
           f"{len(unstable)} unstable ({_names(list(unstable), 3)}): the run recorded "
           + ("no hash seed" if run_seed is None else f"hash seed {run_seed}, the audit runs under {own}")))
    engine = Engine(fits["seed_units"], fits["val_unit"], len(ctx.train_perts), alphas, fits["columns_of"])
    columns, feature_of = fits["columns"], fits["feature_of"]
    sel_feats = [f for f in sel_feats_all if f in fits["columns_of"] and f not in unstable]
    sel_failed = {f: failed[f] for f in sel_feats_all if f in failed}
    sel_unstable = {f: unstable[f] for f in sel_feats_all if f in unstable}
    out["selected_missing"] = sorted(sel_failed)
    out["selected_unstable"] = sorted(sel_unstable)
    if not sel_feats:
        out["selected_analysis"] = {"verdicts": assign_verdicts([], [], {}, {}, {}, {}, {}, None, sel_failed,
                                                                sel_unstable)}
        raise Skip("no feature of the selected model could be recomputed"
                   + (" with values independent of the hash seed" if sel_unstable else ""))
    sel_idx = engine.columns(sel_feats)
    R_all = corr_from_gram(fits["val_unit"].G, fits["constant"])
    out["visible_reproduction"] = (visible_reproduction(engine, sel_idx, sel, run_cv_folds, k, cv_seed)
                                   if not sel_failed and not sel_unstable else
                                   {"available": False, "flag": False,
                                    "reason": ("a feature of the model is unrecomputable" if sel_failed else
                                               "a feature of the model is unstable (its values change with the hash "
                                               "seed)")})
    # ---- the selected model: everything
    red = redundancy(fits["Xtr"][:, sel_idx], [columns[i] for i in sel_idx], [feature_of[i] for i in sel_idx],
                     fits["constant"][sel_idx])
    t = lap("redundancy", t)
    n_train, n_genes = len(ctx.train_perts), ctx.n_genes
    groups = np.repeat(np.arange(n_train), n_genes)
    cv_units = [u.subset(sel_idx) for u, _ in engine.seed_units[seeds[0]]]
    lasso = lasso_stability(fits["Xtr"][:, sel_idx], fits["y"], groups, cv_units, resamples, seeds[0],
                            [columns[i] for i in sel_idx], [feature_of[i] for i in sel_idx])
    lasso["cv"] = f"the {k} folds of seed {seeds[0]}, every feature recomputed without the fold"
    t = lap("lasso", t)
    analysis = analyse_model(engine, sel_feats, R_all, columns, sel_failed, lasso["feature_frequency"], log,
                             "selected", unstable=sel_unstable)
    t = lap("selected_paths", t)
    analysis["redundancy"] = red
    analysis["lasso"] = lasso
    analysis["merge"] = merge_test(engine, sel_idx, red["clusters"])  # clusters spanning two or more features
    t = lap("merge", t)
    out["selected_analysis"] = analysis
    apply_dependencies(out)  # at once: should anything below fail, these verdicts already keep inputs out of the box
    # ---- the pool: census, single and drop-one, paths, compact choice and verdicts
    if use_pool:
        pool_ok = [f for f in pool if f in fits["columns_of"] and f not in unstable]
        pool_failed = {f: failed[f] for f in pool if f in failed}
        out["pool"] = analyse_model(engine, pool_ok, R_all, columns, pool_failed, None, log, "pool",
                                    unstable={f: unstable[f] for f in pool if f in unstable})
        t = lap("pool_paths", t)
    else:
        out["pool"] = None
    apply_dependencies(out)  # again: a composite kept in either scope keeps its inputs out of the box in both
    marks = []
    if sel_failed:
        marks.append(f"{len(sel_failed)} selected feature(s) unrecomputable")
    if sel_unstable:
        marks.append(f"{len(sel_unstable)} selected feature(s) unstable under the hash seed")
    if out["visible_reproduction"].get("flag"):
        marks.append(f"visible reproduction off by {out['visible_reproduction']['max_abs_diff']:.4f}")
    out["marks"] = marks
    out["status"] = "audited"
    out["sealed"] = None
    if sealed:  # pre-specified: the two models are fixed by now, and nothing below changes any of the above
        comp = analysis["compact"]
        comp_alpha = grid_alpha(comp["alphas"], alphas)
        preds = sealed_predictions(fits, sel, sel_idx, engine.columns(comp["features"]), comp_alpha)
        res = score_sealed(data_dir, out["selection_rule"], ctx.control_mean, fits["evals"], preds,
                           f"{run_dir.name}:{sel['experiment_id']}")
        stored = (sel.get("query_metrics_json") or {}).get("pearson_delta")
        diff = None if stored is None else float(res["selected"] - stored)
        out["sealed"] = {"selected": res["selected"], "compact": res["compact"],
                         "difference": float(res["compact"] - res["selected"]), "n_queries": res["n_queries"],
                         "selected_model": model_type, "selected_alpha": best_alpha, "compact_alpha": comp_alpha,
                         "compact_features": comp["features"], "stored_selected": stored, "reproduction_diff": diff,
                         "reproduction_flag": bool(diff is not None and abs(diff) > SEALED_FLAG),
                         "selected_features_missing": sorted(sel_failed),
                         "selected_features_unstable": sorted(sel_unstable)}
        t = lap("sealed", t)
    timings["total"] = round(time.perf_counter() - t0, 3)
    out["timings"] = timings
    log(f"done in {timings['total']:.1f} s")


# ================================================================== across runs
def _family(name: str) -> str:
    return re.sub(r"_e\d+$", "", str(name))


def combined_verdicts(r: dict) -> list[dict]:
    """One verdict per (run, feature) over both scopes: kept when the feature is kept in the selected model's or the
    pool's compact set; otherwise required_input when a kept feature needs it in either scope; otherwise the selected
    model's verdict when the feature is in it, else the pool's. Each entry carries both scopes' verdicts."""
    scopes = {s: {v["feature"]: v for v in ((r.get(key) or {}).get("verdicts") or [])}
              for s, key in (("selected", "selected_analysis"), ("pool", "pool"))}
    out = []
    for f in dict.fromkeys(list(scopes["selected"]) + list(scopes["pool"])):
        here = {s: d[f] for s, d in scopes.items() if f in d}
        kept_in = [s for s, v in here.items() if v["verdict"] == "kept"]
        needed_in = [s for s, v in here.items() if v["verdict"] == "required_input"]
        scope = (kept_in or needed_in or ["selected" if "selected" in here else "pool"])[0]
        v = here[scope]
        out.append({"feature": f, "verdict": v["verdict"], "reason": v["reason"], "scope": scope, "kept_in": kept_in,
                    "evidence": v["evidence"], "builtin": f in BUILTIN_FEATURES,
                    "scopes": {s: {"verdict": x["verdict"], "reason": x["reason"]} for s, x in here.items()}})
    return out


def _median(xs):
    return float(np.median(xs)) if len(xs) else None


def _aggregate_class(runs: list[dict]) -> dict:
    audited = [r for r in runs if r["status"] == "audited"]
    counts = {scope: {v: 0 for v in VERDICTS} for scope in ("selected", "pool")}
    for r in runs:
        for scope, key in (("selected", "selected_analysis"), ("pool", "pool")):
            for v in ((r.get(key) or {}).get("verdicts") or []):
                counts[scope][v["verdict"]] += 1
    families: dict[str, dict] = {}
    for r in audited:
        for v in combined_verdicts(r):
            if v["builtin"]:
                continue
            fam = families.setdefault(_family(v["feature"]), {"n": 0, "kept": 0, "boxed": 0,
                                                              **{x: 0 for x in VERDICTS if x != "kept"}})
            fam["n"] += 1
            if v["verdict"] == "kept":
                fam["kept"] += 1
            elif v["verdict"] == "required_input":  # neither kept for its own columns nor boxed
                fam["required_input"] += 1
            else:
                fam["boxed"] += 1
                fam[v["verdict"]] += 1
    rows = []
    for r in audited:
        a = r["selected_analysis"]
        c, cen = a["compact"], a["census"]
        rows.append({"run": r["run"], "n_features": cen["n_features"], "n_columns": cen["n_columns"],
                     "compact_features": c["n_features"], "compact_columns": c["n_columns"],
                     "n_inputs": len(c.get("required_inputs") or []),
                     "expanded_features": c.get("n_features_expanded", c["n_features"]),
                     "expanded_columns": c.get("n_columns_expanded", c["n_columns"]),
                     # the full model counted the same way (None from an audit that expanded only the compact set)
                     "full_expanded_features": cen.get("n_features_expanded"),
                     "full_expanded_columns": cen.get("n_columns_expanded"),
                     "diff": c["vs_full"]["diff"], "se": c["vs_full"]["se"], "n_val": c["vs_full"]["n"],
                     "class": classify(c["vs_full"]["diff"], c["vs_full"]["se"]),
                     "train_diff": c["vs_full_train"]["diff"]})
    smaller = [x for x in rows if x["compact_features"] < x["n_features"]]
    cls = {k: sum(1 for x in smaller if x["class"] == k) for k in ("not_established", "below_margin", "higher",
                                                                    "lower")}
    kept_fams = sorted((kv for kv in families.items() if kv[1]["kept"]),
                       key=lambda kv: (-kv[1]["kept"], kv[1]["boxed"], kv[0]))
    boxed_fams = sorted((kv for kv in families.items() if kv[1]["boxed"]),
                        key=lambda kv: (-kv[1]["boxed"], kv[1]["kept"], kv[0]))
    sealed = [r["sealed"] for r in audited if r.get("sealed")]
    return {
        "n_runs": len(runs), "n_audited": len(audited), "n_skipped": len(runs) - len(audited),
        "verdict_counts": counts,
        "families_kept": [{"family": k, **v} for k, v in kept_fams],
        "families_boxed": [{"family": k, **v} for k, v in boxed_fams],
        "compact_vs_full": {"n": len(rows), "n_smaller": len(smaller), **cls,
                            "below_margin_lower": sum(1 for x in smaller
                                                      if x["class"] == "below_margin" and x["diff"] < 0),
                            "mean_diff": float(np.mean([x["diff"] for x in smaller])) if smaller else None,
                            "median_se": _median([x["se"] for x in smaller]),
                            "mean_train_diff": float(np.mean([x["train_diff"] for x in smaller])) if smaller else None,
                            "n_val": _median([x["n_val"] for x in rows]),
                            "median_features": _median([x["compact_features"] for x in rows]),
                            "median_full_features": _median([x["n_features"] for x in rows]),
                            "median_columns": _median([x["compact_columns"] for x in rows]),
                            "median_full_columns": _median([x["n_columns"] for x in rows]),
                            "n_with_inputs": sum(1 for x in rows if x["n_inputs"]),
                            "median_features_expanded": _median([x["expanded_features"] for x in rows]),
                            "median_columns_expanded": _median([x["expanded_columns"] for x in rows
                                                                if x["expanded_columns"] is not None]),
                            "median_full_features_expanded": _median([x["full_expanded_features"] for x in rows
                                                                     if x["full_expanded_features"] is not None]),
                            "median_full_columns_expanded": _median([x["full_expanded_columns"] for x in rows
                                                                    if x["full_expanded_columns"] is not None])},
        "sealed": {"n": len(sealed),
                   "mean_difference": float(np.mean([s["difference"] for s in sealed])) if sealed else None,
                   "compact_higher": sum(1 for s in sealed if s["difference"] > 0),
                   "flagged": sum(1 for s in sealed if s["reproduction_flag"])},
    }


def aggregate(runs: list[dict]) -> dict:
    """Across runs, split by arm class: the agent runs are what the audit is about; the scripted controls and other
    no-LLM runs repeat the same template features in every run and are kept apart as a reference."""
    audited = [r for r in runs if r["status"] == "audited"]
    classes = {c: _aggregate_class([r for r in runs if r.get("arm_class") == c]) for c in ("agent", "no_llm")}
    primary = "agent" if classes["agent"]["n_audited"] or not classes["no_llm"]["n_audited"] else "no_llm"
    checked = [r for r in audited if (r.get("visible_reproduction") or {}).get("max_abs_diff") is not None]
    repro = [r["visible_reproduction"]["max_abs_diff"] for r in checked]
    best = max(audited, key=lambda r: (r["selected_analysis"]["full"]["mean"], r["run"]))["run"] if audited else None
    return {
        "n_runs": len(runs), "n_audited": len(audited), "n_skipped": len(runs) - len(audited),
        "primary": primary, "classes": classes,
        "visible_reproduction": {"n_checked": len(checked), "n_within": sum(1 for x in repro if x <= REPRO_FLAG),
                                 "n_beyond": sum(1 for x in repro if x > REPRO_FLAG),
                                 "max_abs_diff": max(repro) if repro else None, "threshold": REPRO_FLAG},
        "n_selected_missing": sum(1 for r in audited if r.get("selected_missing")),
        "n_selected_unstable": sum(1 for r in audited if r.get("selected_unstable")),
        "n_marked": sum(1 for r in audited if r.get("marks")),
        "detail_run": best,
    }


def _checkpoint_key(run_dir: Path, proto: dict) -> str:
    """Identifies an audit by everything it depends on: this tool's code, the protocol and the format of what it
    records (AUDIT_FORMAT), the run's path, database, configuration and plugins. A run that changed, or a changed
    tool, is audited afresh."""
    h = hashlib.sha256()
    h.update(Path(__file__).read_bytes())
    h.update(json.dumps({**proto, "audit_format": AUDIT_FORMAT}, sort_keys=True, default=str).encode())
    h.update(str(Path(run_dir).resolve()).encode())
    files = [run_dir / n for n in ("lab.db", "lab.db-wal", "config.json", "summary.json")]
    files += sorted((run_dir / "feature_store").glob("*.py")) if (run_dir / "feature_store").is_dir() else []
    for p in files:
        if p.is_file():
            h.update(p.name.encode())
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
    return h.hexdigest()[:24]


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def analyse(run_dirs: list[Path], cache_dir: Path, fold_seeds=None, resamples: int = 50, use_pool: bool = True,
            sealed: bool = False, log=None) -> dict:
    """Every run, one after the other. Each audited run is written to a checkpoint in cache_dir/audits as soon as it
    is done, and a run whose checkpoint matches (same tool, protocol and run contents) is taken from it, so an
    interrupted job resumes where it stopped and never scores a run's sealed models twice. The hash seed the plugins
    run under is part of a checkpoint's key: a checkpoint written under another seed is never taken."""
    say = log or (lambda msg: print(msg, file=sys.stderr, flush=True))
    seed = python_hash_seed()
    proto_key = {"fold_seeds": list(fold_seeds) if fold_seeds else None, "resamples": int(resamples),
                 "pool": bool(use_pool), "sealed": bool(sealed), "python_hash_seed": seed}
    runs = []
    for i, d in enumerate(run_dirs):
        d = Path(d).resolve()
        ck = None
        try:
            if (d / "lab.db").exists():
                ck = Path(cache_dir) / "audits" / f"{d.name}__{_checkpoint_key(d, proto_key)}.json"
        except OSError:
            ck = None
        if ck is not None and ck.exists():
            try:
                cached = json.loads(ck.read_text())
            except ValueError:
                cached = None
            if isinstance(cached, dict) and cached.get("audit_format") == AUDIT_FORMAT:  # never an older audit's
                runs.append(cached)
                say(f"[feature_audit] {d.name}: taken from the checkpoint {ck.name} ({i + 1}/{len(run_dirs)})")
                continue
        say(f"[feature_audit] run {i + 1}/{len(run_dirs)}: {d}")
        try:
            r = _plain(audit_run(d, fold_seeds, resamples, use_pool, sealed, say))
        except Exception as exc:  # audit_run reports its own errors; this guards the guard
            print(traceback.format_exc(), file=sys.stderr)
            r = {"run": d.name, "path": str(d), "status": "skipped", "reason": f"unexpected error: {_err(exc)}"}
        if ck is not None and r["status"] == "audited":
            _write_atomic(ck, json.dumps(r, indent=1))
        runs.append(r)
    return {"generated_by": "tools/feature_audit.py",
            "protocol": {"fold_seeds": list(fold_seeds) if fold_seeds else "run cv_seed and cv_seed + 1",
                         "resamples": int(resamples), "pool": bool(use_pool), "score_sealed": bool(sealed),
                         "fixed_alphas": list(FIXED_ALPHAS), "pool_min_gain": POOL_MIN_GAIN,
                         "corr_high": CORR_HIGH, "duplicate_r": DUPLICATE_R, "stable_frequency": STABLE_FREQ,
                         "sealed_flag": SEALED_FLAG, "reproduction_flag": REPRO_FLAG, "noise_floor": NOISE_FLOOR,
                         "rule": RULE, "composites": COMPOSITES, "audit_format": AUDIT_FORMAT,
                         # the seed of the str hashes the plugins ran under ('0' from the command line, which
                         # re-executes itself under it, and whether it did; a call from Python keeps its own)
                         "python_hash_seed": seed, "hash_seed_reexec": reexecuted_under_hash_seed(),
                         "hash_check": {"seeds": list(HASH_SEEDS), "tolerance": HASH_TOL, "tie_tolerance": TIE_TOL}},
            "runs": runs, "aggregate": aggregate(runs)}


def build_box(rep: dict) -> dict:
    """Every feature an agent might propose again that the audit did not keep: one entry per (run, feature), with
    the combined verdict over the selected model's and the pool's analyses (a feature kept in either is not boxed,
    nor is one that a kept feature computes through ctx.feature), its reason and evidence (both scopes' verdicts
    inside). Built-in features are never boxed. The features left out because a kept feature needs them are listed
    apart (required_inputs: one record per run and feature, naming the kept features that need it and the verdict it
    would otherwise have), with each run's dependency map, so that a lab importing only the box knows why they are
    missing from it and that pruning them would break a kept feature; entries keep their meaning."""
    entries, required, deps = [], [], {}
    for r in rep["runs"]:
        sel = r.get("selected") or {}
        intro = r.get("introduced_by") or {}
        info = r.get("feature_info") or {}
        where = {"run": r["run"], "run_id": r.get("run_id"), "arm": r.get("arm"), "arm_class": r.get("arm_class"),
                 "dataset": r.get("dataset"), "split_id": r.get("split_id")}
        if r.get("dependencies"):
            deps[r["run"]] = r["dependencies"]
        for v in combined_verdicts(r):
            f = v["feature"]
            if v["builtin"]:
                continue
            if v["verdict"] == "required_input":
                ev = v["evidence"] or {}
                required.append({**where, "scope": v["scope"], "feature": f, "family": _family(f),
                                 "code_hash": (info.get(f) or {}).get("code_hash"),
                                 "required_by": list(ev.get("required_by") or []),
                                 "verdict_otherwise": ev.get("verdict_otherwise"), "reason": v["reason"],
                                 "scopes": v["scopes"]})
                continue
            if v["verdict"] not in BOXED_VERDICTS:
                continue
            entries.append({**where,
                            "experiment": (sel.get("experiment_id") if v["scope"] == "selected"
                                           else intro.get(f) or sel.get("experiment_id")),
                            "introduced_by": intro.get(f), "scope": v["scope"], "feature": f, "family": _family(f),
                            "code_hash": (info.get(f) or {}).get("code_hash"),
                            "description": (info.get(f) or {}).get("description"),
                            "verdict": v["verdict"], "reason": v["reason"],
                            "evidence": {**(v["evidence"] or {}), "scopes": v["scopes"]}})
    return {"generated_by": "tools/feature_audit.py", "rule": RULE, "entries": entries, "required_inputs": required,
            "dependencies": deps}


# ================================================================== rendering
CLASS_LABEL = {"agent": "agent", "no_llm": "no-LLM"}


def _f(x, nd=4):
    return "n/a" if x is None else f"{x:.{nd}f}"


def _d(x, nd=4):
    return "n/a" if x is None else f"{x:+.{nd}f}"


def _a(x):
    return "n/a" if x is None else f"{x:g}"


def _alphas(xs):
    return "/".join(_a(x) for x in xs) if xs else "n/a"


def _pd(p, nd=4):
    return "n/a" if p is None else f"{p['diff']:+.{nd}f} ({p['se']:.{nd}f})"


def _arms(runs: list[dict]) -> dict[str, str]:
    arms = []
    for r in runs:
        if r.get("arm") and r["arm"] not in arms:
            arms.append(r["arm"])
    return {a: f"A{i + 1}" for i, a in enumerate(arms)}


def _head_tail(n: int, head: int, tail: int) -> list:
    """Row indices shown of n rows: all when few, else the first `head`, a gap (None) and the last `tail`."""
    if n <= head + tail + 1:
        return list(range(n))
    return list(range(head)) + [None] + list(range(n - tail, n))


def _with_gaps(indices: list[int]) -> list:
    """Sorted row indices with None wherever rows were skipped."""
    out = []
    for i in indices:
        if out and i > out[-1] + 1:
            out.append(None)
        out.append(i)
    return out


def _short(x, n: int) -> str:
    s = str(x)
    return s if len(s) <= n else s[:n - 1] + "…"


def _cell(x) -> str:
    """Free text in a table cell: a pipe would split the cell."""
    return str(x).replace("|", "\\|").replace("\n", " ")


def _names(xs, k: int = 2) -> str:
    xs = list(xs)
    return ", ".join(xs[:k]) + (f" +{len(xs) - k}" if len(xs) > k else "")


def _names_within(xs, width: int) -> str:
    """As many names as fit in about `width` characters (at least one), then how many more."""
    xs = list(xs)
    k = 1
    while k < len(xs) and len(", ".join(xs[:k + 1])) <= width:
        k += 1
    return _names(xs, k)


def _items_within(items: list[str], width: int) -> str:
    """As many items as fit in about `width` characters (at least one), joined; 'none' when there are none."""
    k = 1
    while k < len(items) and len(", ".join(items[:k + 1])) <= width:
        k += 1
    return ", ".join(items[:k]) or "none"


def _plus_inputs(m: dict) -> str:
    """' (+k)' for a model (census or compact set) whose members compute k other features through ctx.feature, its
    required inputs, which are not columns of the model; '' when none."""
    k = len(m.get("required_inputs") or [])
    return f" (+{k})" if k else ""


def _compact_fc(c: dict) -> str:
    """A compact set's size for the Runs table: features (+ required inputs) / columns of the model."""
    return f"{c['n_features']}{_plus_inputs(c)}/{c['n_columns']}"


def _inputs_clause(c: dict) -> str:
    """A compact set's required inputs and its expanded size, counts only, for its list line ('' when none; the
    names are in the JSON). Failed inputs (called, never returned) are counted apart, since they are counted nowhere
    else; an audit written before them has none, and may lack a column count."""
    inputs, failed = c.get("required_inputs") or [], c.get("failed_inputs") or []
    cols = c.get("n_columns_expanded")
    return ((f"; +{_plural(len(inputs), 'input')}: {c.get('n_features_expanded', 'n/a')} features, "
             f"{'n/a' if cols is None else cols} columns computed" if inputs else "")
            + (f"; {_plural(len(failed), 'failed input')}" if failed else ""))


def render(rep: dict) -> str:
    runs, agg, proto = rep["runs"], rep["aggregate"], rep["protocol"]
    audited = [r for r in runs if r["status"] == "audited"]
    arms = _arms(runs)
    n_tr = "/".join(str(x) for x in sorted({r["n_train"] for r in audited})) or "n/a"
    n_v = "/".join(str(x) for x in sorted({r["n_val"] for r in audited})) or "n/a"
    ks = "/".join(str(x) for x in sorted({r["folds"] for r in audited})) or "n/a"
    any_sealed = any(r.get("sealed") for r in audited)
    nonridge = any(r["selected"]["model_type"] != "ridge" for r in audited)
    any_marked = any(r.get("marks") for r in audited)
    composites = "composites" in proto  # the audit recorded what each feature computes through ctx.feature
    hashed = "hash_check" in proto  # the audit looked for features whose values change with the str hash seed
    any_inputs = any(r["selected_analysis"][m].get("required_inputs") for r in audited for m in ("census", "compact"))
    floor = proto.get("noise_floor", NOISE_FLOOR)
    fs = proto.get("fold_seeds")
    seeds_txt = (f"fold seeds {', '.join(map(str, fs))}" if isinstance(fs, list)
                 else "two fold seeds (the run's own and the next)")
    L = ["# Feature audit: redundancy, compact model and the failed-feature box", "",
         "Protocol, fixed before any result under it was read. Per run: the selected single model (highest visible "
         "score among completed non-ensemble, non-baseline experiments)"
         + ("; a pool adds the features that raised their parent's score by more than 0.0005, and the built-ins"
            if proto.get("pool") else "")
         + f". Scores are pearson_delta per visible perturbation: out of fold for the {n_tr} training perturbations "
         f"({ks} folds; features that read training labels, detected per feature on a fresh view, recomputed without "
         f"each fold) and, from a fit on all of them, for the {n_v} visible validation perturbations; every fit is "
         "ridge on columns standardised by its training rows"
         + (" (other model types audited as ridge, marked *)" if nonridge else "")
         + f". With {seeds_txt}, each subset's penalty is chosen on the training perturbations' out-of-fold scores "
         "under one fold partition and reported under the other (both ways averaged), so only the validation "
         "perturbations are independent of it. The greedy paths and the compact model (smallest set on the backward "
         f"path within max(paired SE, {floor:g}) of its best) are chosen on the training perturbations alone; compact "
         "and full are compared, paired, on the validation perturbations, untouched by any choice of this tool (the "
         f"lab chose the selected model partly on them). A difference within max(SE, {floor:g}) is either not "
         f"established or below {floor:g}, a margin of practical equivalence. Lasso: "
         f"penalty by cross-validation over the fold-recomputed designs, then {proto.get('resamples')} half-samples; "
         f"stable = selected in at least {proto.get('stable_frequency', STABLE_FREQ):.0%}. Verdicts, in order: kept, "
         + ("required_input, " if composites else "")
         # the seeds, the tolerance, the seed the plugins ran under (0 from the command line) and the rule of unstable
         # are in the JSON (protocol and rule): the report stays pasteable
         + ("unstable (changes with the hash seed), " if hashed else "")
         + "harmful, redundant (|r| ≥ 0.9 with a kept feature), substitutable (established drop-one gain the compact "
         "set does without), no_gain, unrecomputable."
         + (" A composite (a feature computing others through ctx.feature) is one feature; what a kept one computes "
            "is a required input (+k), never boxed." if composites else ""), ""]
    if any_sealed:
        L += ["Sealed scores, read before the numbers: the sealed perturbations have already been read for dozens of "
              "finalists across about thirty runs, so these are one more look at a used set, not a clean test; the "
              "Norman bundle (or a new split) is the clean test. Per run exactly two models, fixed before any sealed "
              "score was read, are scored once each through the tool's own oracle: the selected model as reproduced "
              "here and the compact model (ridge at its visibly chosen alpha). Nothing about them feeds back into any "
              f"choice. !: reproduction off the run's own sealed score by more than "
              f"{proto.get('sealed_flag', SEALED_FLAG):g}.", ""]
    head = "| run | arm | feat. | cols | rank | dup. | r≥0.9 | compact f/c | full | compact | Δ val (SE) | Lasso |"
    sep = "|---|---|---|---|---|---|---|---|---|---|---|---|"
    if any_sealed:
        head += " sealed full | sealed compact |"
        sep += "---|---|"
    L += ["## Runs", "", head, sep]
    for r in runs:
        if r["status"] != "audited":
            why = _cell(_short(r.get("reason"), 60))
            L.append(f"| {r['run']} | {arms.get(r.get('arm'), 'n/a')} | skipped: {why} |")
            continue
        a, s = r["selected_analysis"], r["selected"]
        c, red, n_f = a["compact"], a["redundancy"], a["census"]["n_features"]
        row = (f"| {r['run']}{'*' if s['model_type'] != 'ridge' else ''}{' †' if r.get('marks') else ''} | "
               f"{arms.get(r['arm'])} | {n_f}{_plus_inputs(a['census'])} | {a['census']['n_columns']} | "
               f"{red['rank']} | {red['n_duplicate_columns']} | "
               f"{red['n_pairs_above_0.9']} | {_compact_fc(c)} | {_f(a['full']['mean'])} | "
               f"{_f(c['mean'])} | {_pd(c['vs_full'])} | {len(a['lasso']['stable_features'])}/{n_f}"
               f"{' ᵉ' if _lasso_at_edge(a['lasso']) else ''} |")
        if any_sealed:
            sd = r.get("sealed")
            row += (" n/a | n/a |" if not sd else
                    f" {_f(sd['selected'])}{' !' if sd['reproduction_flag'] else ''} | {_f(sd['compact'])} |")
        L.append(row)
    L += ["", ("Arms: " + "; ".join(f"{code} = {arm}" for arm, code in arms.items()) + ".") if arms else "Arms: none.",
          "feat./cols: the selected model; dup.: exact duplicate columns; r≥0.9: column pairs with |r| ≥ 0.9; "
          "compact f/c: the compact set; full, compact: visible scores (the compact set was chosen on the training "
          "perturbations, which flatter it); Δ val: compact − full on the validation perturbations, paired; Lasso: "
          "Lasso-stable features."
          + (" ᵉ: the cross-validated Lasso penalty is the smallest of its grid, so nearly every column "
             "survives and the stable count says little." if any(
                 _lasso_at_edge(r["selected_analysis"]["lasso"]) for r in audited) else "")
          + (" (+k): k required inputs, computed through ctx.feature." if any_inputs else "")
          + (" *: the selected model is not ridge (its type is in the JSON) and is audited as ridge on the same "
             "columns (ols: alpha 0 by least squares)." if nonridge else "")
          + (" †: the audited model is not exactly the run's (selected features unrecomputable"
             + (" or unstable" if hashed else "") + ", or the lab's visible score not reproduced within "
             f"{proto.get('reproduction_flag', REPRO_FLAG):g})." if any_marked else "")]
    prim = agg["primary"]
    shown = [r for r in audited if r.get("arm_class") == prim]
    if shown:
        L += ["", f"Compact sets ({CLASS_LABEL[prim]} runs):", ""]
        lines: list[str] = []
        for r in shown[:SHOW_COMPACT_RUNS]:
            c = r["selected_analysis"]["compact"]
            clause = _inputs_clause(c)  # its names give way to it, so a line stays about as long
            line = f"- {r['run']}: {_names_within(c['features'], max(40, 90 - len(clause)))}" + clause
            if lines and len("\n".join(lines + [line]).encode()) > COMPACT_LIST_BYTES:
                break
            lines.append(line)
        L += lines
        if len(shown) > len(lines):
            L.append(f"- … {len(shown) - len(lines)} more runs")
    present = [c for c in ("agent", "no_llm") if agg["classes"][c]["n_runs"]] or [agg["primary"]]
    L += ["", "## Verdicts", "",
          "| verdict | " + " | ".join(f"{CLASS_LABEL[c]}: selected | {CLASS_LABEL[c]}: pools" for c in present) + " |",
          "|---|" + "---|---|" * len(present)]
    for v in VERDICTS:
        if (v == "required_input" and not composites) or (v == "unstable" and not hashed):
            continue  # an older audit never looked: no count, rather than a false 0
        L.append(f"| {v} | " + " | ".join(f"{agg['classes'][c]['verdict_counts']['selected'].get(v, 0)} | "
                                         f"{agg['classes'][c]['verdict_counts']['pool'].get(v, 0)}" for c in present)
                 + " |")
    pa = agg["classes"][prim]
    if pa["families_kept"] or pa["families_boxed"]:
        kept = _items_within([f"{x['family']} {x['kept']}/{x['n']}" for x in pa["families_kept"][:4]], 200)
        boxed = _items_within([f"{x['family']} {x['boxed']}/{x['n']} ("
                               + ", ".join(f"{x[v]} {v}" for v in BOXED_VERDICTS if x.get(v)) + ")"
                               for x in pa["families_boxed"][:4]], 200)
        L += ["", f"Feature families of the {CLASS_LABEL[prim]} runs (name without its _e<experiment> suffix, "
              "built-ins left out; one verdict per run and feature, kept in either scope counts as kept), most often "
              f"kept: {kept}. Most often boxed: {boxed}."]
    det = next((r for r in audited if r["run"] == agg.get("detail_run")), None)
    if det is not None:
        L += _render_detail(det)
    L += ["", "## Reading", "", _reading(rep)]
    return "\n".join(L) + "\n"


def _render_detail(r: dict) -> list[str]:
    a, s = r["selected_analysis"], r["selected"]
    red, comp = a["redundancy"], a["compact"]
    vr = r.get("visible_reproduction") or {}
    para = (f"Selected model {s['experiment_id']}: {s['model_type']}"
            + (" (audited as ridge)" if s["model_type"] != "ridge" else "")
            + f", best alpha {_a(s['best_alpha'])}, {a['census']['n_features']} features, {a['census']['n_columns']} "
            f"columns; {r['folds']} folds, seeds {', '.join(map(str, r['fold_seeds']))}; alpha grid "
            f"{', '.join(_a(x) for x in r['alpha_grid'])}. Full model {_f(a['full']['mean'])} (alphas "
            f"{_alphas(a['full']['alphas'])}), compact {_f(comp['mean'])} (alphas {_alphas(comp['alphas'])}). "
            f"Compact − full on the {comp['vs_full']['n']} validation perturbations {_pd(comp['vs_full'])}, "
            f"{comp['vs_full']['wins']} wins; on the {comp['vs_full_train']['n']} training perturbations that chose it "
            f"{_pd(comp['vs_full_train'])}.")
    inputs, failed, cen = comp.get("required_inputs") or [], comp.get("failed_inputs") or [], a["census"]
    if inputs or failed:  # their names are in the JSON
        cols = comp.get("n_columns_expanded")
        para += (f" With its {_plural(len(inputs), 'required input')} the compact set computes "
                 f"{comp.get('n_features_expanded', 'n/a')} features and {'n/a' if cols is None else cols} columns"
                 + (f" (full model: {cen['n_features_expanded']}, {cen['n_columns_expanded']})"
                    if cen.get("n_features_expanded") is not None else "") if inputs else " The compact set has")
        para += (f"{';' if inputs else ''} {_plural(len(failed), 'failed input')}" if failed else "") + "."
    if vr.get("available"):
        parts = [f"{k.replace('_', '-')} {_f(vr[k]['tool'])} vs stored {_f(vr[k]['stored'])}"
                 for k in ("validation", "out_of_fold") if vr.get(k)]
        para += f" Lab's visible scores recomputed at alpha {_a(vr['alpha'])}: " + "; ".join(parts) + "."
    if r.get("unrecomputable"):
        items = list(r["unrecomputable"].items())
        para += (f" Unrecomputable: {items[0][0]} ({items[0][1][:60]})" + "".join(f"; {f}" for f, _ in items[1:3])
                 + (f"; +{len(items) - 3} more in the JSON" if len(items) > 3 else "") + ".")
    L = ["", f"## Detail: {r['run']} (highest visible full score)", "", para]
    bwd = a["backward"]
    L += ["", "Backward path (each step drops the feature whose removal leaves the highest training score; ← compact "
          "set, * best; train: out-of-fold training score, val: validation score):", "",
          "| feat. | cols | removed | train | best − this (SE) | val | alpha |", "|---|---|---|---|---|---|---|"]
    keep = set(range(len(bwd))) if len(bwd) <= 8 else {0, comp["backward_step"], comp["best_step"],
                                                          *range(len(bwd) - 4, len(bwd))}
    for i in _with_gaps(sorted(keep)):
        if i is None:
            L.append("| … | | (steps omitted, in the JSON) | | | | |")
            continue
        st = bwd[i]
        mark = (" ←" if i == comp["backward_step"] else "") + (" *" if i == comp["best_step"] else "")
        L.append(f"| {st['n_features']}{mark} | {st['n_columns']} | {st['removed'] or '(full model)'} | "
                 f"{_f(st['train_mean'])} | {_pd(st['vs_best'])} | {_f(st['val_mean'])} | {_alphas(st['alphas'])} |")
    fwd = a["forward"]
    L += ["", "Forward path (add the feature that raises the training score most):", "",
          "| feat. | cols | added | train | val | alpha |", "|---|---|---|---|---|---|"]
    for i in _head_tail(len(fwd), 3, 1):
        if i is None:
            L.append(f"| … | | {len(fwd) - 4} steps in the JSON | | | |")
            continue
        st = fwd[i]
        L.append(f"| {st['n_features']} | {st['n_columns']} | {st['added']} | {_f(st['train_mean'])} | "
                 f"{_f(st['val_mean'])} | {_alphas(st['alphas'])} |")
    verdict = {v["feature"]: v["verdict"] for v in a["verdicts"]}
    order = sorted(a["drop_one"], key=lambda f: (-a["drop_one"][f]["diff"], f))
    L += ["", "Drop-one (full − without, paired over all visible perturbations; wins = perturbations where the full "
          "model is higher) and single-feature scores:", "",
          "| feature | cols | single | full − without (SE) | wins | Lasso | verdict |",
          "|---|---|---|---|---|---|---|"]
    for i in _head_tail(len(order), 3, 3):
        if i is None:
            L.append(f"| … {len(order) - 6} features in the JSON | | | | | | |")
            continue
        f = order[i]
        d = a["drop_one"][f]
        L.append(f"| {f} | {a['census']['columns_per_feature'][f]} | {_f(a['single'][f]['mean'])} | {_pd(d)} | "
                 f"{d['wins']}/{d['n']} | {_f(a['lasso']['feature_frequency'].get(f), 2)} | {verdict.get(f)} |")
    cond = "singular" if red["condition_number"] is None else f"{red['condition_number']:.3g}"
    top = "; ".join(f"{p['a']} ~ {p['b']} {p['r']:+.3f}" for p in red["top_pairs"][:1])
    L += ["", f"Redundancy of the {red['n_columns']} columns: rank {red['rank']}, effective rank "
          f"{red['effective_rank']:.1f}, condition number {cond}; {len(red['constant_columns'])} constant, "
          f"{red['n_duplicate_columns']} exact duplicates, {red['n_pairs_above_0.9']} pairs with |r| ≥ 0.9, "
          f"{red['n_pairs_above_0.7']} with |r| ≥ 0.7" + (f"; most correlated: {top}" if top else "")
          + f". Lasso penalty {a['lasso']['lambda']:.3g}; {len(a['lasso']['stable_features'])} stable features"
          + (f": {_names(a['lasso']['stable_features'], 2)}." if a["lasso"]["stable_features"] else ".")]
    merges = a.get("merge") or []
    links = [m.get("weakest_link_abs_r") for m in merges]
    L += ["", "Merge test (a cluster at |r| ≥ 0.9 spanning two or more features replaced by its first principal "
          "component, fitted on each fit's training rows only"
          + ("; weakest link: the smallest |r| joining it, ≥ 0.9; its ends may correlate less (min_pair_abs_r in the "
             "JSON)" if any(x is not None for x in links) else "")
          + "):", ""]
    if merges:
        L += ["| cluster features | weakest link \\|r\\| | cols | merged score | merged − full (SE) |",
              "|---|---|---|---|---|"]
        for m, link in zip(merges[:2], links):
            name = "all clusters" if isinstance(m["columns"], str) else _names_within(m["features"], 60)
            L.append(f"| {name} | {_f(link, 3)} | {m['n_columns']} | {_f(m['mean'])} | {_pd(m['vs_full'])} |")
        if len(merges) > 2:
            L.append(f"| … {len(merges) - 2} more in the JSON | | | | |")
    else:
        L.append("No cluster at |r| ≥ 0.9 spans two or more features of this model.")
    return L


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def _reading(rep: dict) -> str:
    agg = rep["aggregate"]
    if not agg["n_audited"]:
        return f"No run could be audited ({agg['n_skipped']} skipped); there is nothing to read."
    band = rep["protocol"].get("noise_floor", NOISE_FLOOR)
    prim = agg["primary"]
    other = "no_llm" if prim == "agent" else "agent"
    A, B = agg["classes"][prim], agg["classes"][other]
    lab = CLASS_LABEL[prim]
    parts = [f"{_plural(A['n_audited'], lab + ' run')} audited"
             + (f", {_plural(B['n_audited'], CLASS_LABEL[other] + ' run')} as a reference" if B["n_audited"] else "")
             + (f", {agg['n_skipped']} skipped" if agg["n_skipped"] else "") + "."]
    if prim == "no_llm":
        parts.append(" No agent run was audited, so what follows describes the scripted, no-LLM runs.")
    cf = A["compact_vs_full"]
    if cf["n"]:
        parts.append(f" The compact model keeps a median of {cf['median_features']:g} of "
                     f"{cf['median_full_features']:g} features ({cf['median_columns']:g} of "
                     f"{cf['median_full_columns']:g} columns) and is smaller than the full model in {cf['n_smaller']} "
                     f"of {cf['n']} runs.")
        if cf.get("n_with_inputs"):  # both sizes on one basis: the full model's inputs expanded the same way
            cols = cf.get("median_columns_expanded")
            full_f, full_c = cf.get("median_full_features_expanded"), cf.get("median_full_columns_expanded")
            parts.append(f" With its composites' required inputs ({cf['n_with_inputs']} of {cf['n']} runs), it "
                         f"computes a median of {cf['median_features_expanded']:g}"
                         + ("" if full_f is None else f" of {full_f:g}") + " features"
                         + ("" if cols is None else f" ({cols:g}" + ("" if full_c is None else f" of {full_c:g}")
                            + " columns)")
                         + ("" if full_f is None else ", the full model's counted alike") + ".")
    if cf["n_smaller"]:
        cats = [f"within one paired SE in {cf['not_established']} of {cf['n_smaller']} runs"]
        if cf["below_margin"]:
            cats.append(f"beyond one SE but within {band:g} in {cf['below_margin']} "
                        f"({cf['below_margin_lower']} of them lower)")
        if cf["higher"]:
            cats.append(f"higher by more than max(SE, {band:g}) in {cf['higher']}")
        if cf["lower"]:
            cats.append(f"lower by more than max(SE, {band:g}) in {cf['lower']}")
        parts.append(
            " It was chosen on the training perturbations' out-of-fold scores, which flatter it (mean compact − "
            f"full there {cf['mean_train_diff']:+.4f}). On the {cf['n_val']:g} validation perturbations of each run, "
            "which no choice of this tool touched, compact − full is " + ", ".join(cats)
            + f" (mean {cf['mean_diff']:+.4f}, median paired SE {cf['median_se']:.4f}); the lab chose each selected "
            "model partly on them, which if anything favours the full model.")
        if cf["lower"]:
            parts.append(f" In {_plural(cf['lower'], 'run')} the dropped features carry signal on perturbations "
                         "outside the choice that the compact set does not.")
        else:
            parts.append(f" No run shows a loss beyond max(SE, {band:g}) there"
                         + (f" ({cf['below_margin_lower']} established but smaller than {band:g})"
                            if cf["below_margin_lower"] else "")
                         + "; with so few perturbations per run that band is wide, so this bounds the loss rather "
                         "than showing it is zero.")
    elif cf["n"]:
        parts.append(" No model can be made smaller within that band on the training perturbations.")
    vc = A["verdict_counts"]["selected"]
    req = vc.get("required_input", 0)  # absent from an audit that predates composites
    dropped = vc["redundant"] + vc["substitutable"] + vc["harmful"] + vc["no_gain"]
    if dropped + req:
        share = vc["redundant"] / dropped if dropped else 0.0
        if not req:  # the share is of every feature outside the compact sets
            explains = ("near-duplication explains most of the feature count" if share >= 0.5 else
                        "near-duplication explains a minority of the count: most dropped features are not copies of "
                        "kept ones" if share > 0 else
                        "near-duplication explains none of the count: no dropped feature is a copy of a kept one")
        elif dropped == 1:  # of the one feature neither kept nor required, which the sentence names
            explains = ("near-duplication explains it" if share else
                        "near-duplication does not explain it: it is not a copy of a kept one")
        else:  # of the features neither kept nor required, which the sentence names: never of the required inputs
            explains = (f"near-duplication explains most of those {dropped}" if share >= 0.5 else
                        f"near-duplication explains a minority of those {dropped}: most are not copies of kept ones"
                        if share > 0 else
                        f"near-duplication explains none of those {dropped}: none is a copy of a kept one")
        listed = ("" if not dropped else
                  (f"{vc['redundant']} are redundant" if not req else
                   f"of the other {'one' if dropped == 1 else dropped}, {vc['redundant']} redundant")
                  + f" (|r| ≥ 0.9 with a kept feature), {vc['substitutable']} substitutable (an established drop-one "
                  f"gain that kept features take over), {vc['no_gain']} no_gain and {vc['harmful']} harmful; "
                  + explains
                  + (f"; a no_gain feature's drop-one effect is within max(paired SE, {band:g}), which is not proof "
                     "of zero effect." if vc["no_gain"] else "."))
        parts.append(f" Of the {dropped + req} features of the selected models outside their compact sets, "
                     + ("" if not req else
                        f"{req} {'is a required input' if req == 1 else 'are required inputs'} of kept features (not "
                        "boxed)" + ("; " if dropped else "."))
                     + listed)
    if vc["unrecomputable"]:
        parts.append(f" {vc['unrecomputable']} feature(s) of the selected models could not be recomputed and are "
                     "boxed as such.")
    if vc.get("unstable"):  # absent from an audit that predates the hash-seed check
        parts.append(f" {vc['unstable']} feature(s) of the selected models are unstable (boxed).")
    vr = agg["visible_reproduction"]
    if vr["n_checked"]:
        parts.append(f" The engine reproduces the lab's stored visible scores within {vr['threshold']:g} for "
                     f"{vr['n_within']} of {vr['n_checked']} selected models"
                     + (f"; {vr['n_beyond']} beyond (marked †)" if vr["n_beyond"] else "") + ".")
    if agg["n_selected_missing"]:
        parts.append(f" In {_plural(agg['n_selected_missing'], 'run')} features of the selected model could not be "
                     "recomputed, so the audited model is smaller than the run's (marked †).")
    if B["n_audited"]:
        cb = B["compact_vs_full"]
        ref = CLASS_LABEL[other][0].upper() + CLASS_LABEL[other][1:]
        parts.append(f" {ref} runs (reference): the compact model keeps a median of {cb['median_features']:g} of "
                     f"{cb['median_full_features']:g} features"
                     + (f"; on the validation perturbations it is lower than full by more than max(SE, {band:g}) in "
                        f"{cb['lower']} of the {cb['n_smaller']} runs where it is smaller." if cb["n_smaller"] else
                        " and is never smaller than the full model."))
    sealed = [agg["classes"][c]["sealed"] for c in ("agent", "no_llm") if agg["classes"][c]["sealed"]["n"]]
    if sealed:
        n = sum(s["n"] for s in sealed)
        mean = sum(s["mean_difference"] * s["n"] for s in sealed) / n
        parts.append(f" On the sealed set (one more look at a used set) the compact model scored {mean:+.4f} relative "
                     f"to the selected model on average, higher in {sum(s['compact_higher'] for s in sealed)} of {n} "
                     f"runs; {sum(s['flagged'] for s in sealed)} reproduction(s) flagged. No sealed number entered any "
                     "choice, and none should be read as a clean test.")
    if "hash_check" in rep["protocol"]:  # the paired-SE and margin rules are stated once, in the protocol paragraph,
        parts.append(" Single fold-seed differences below about 0.02 never were established.")  # room for unstable
    else:  # a report from before the hash-seed check re-renders as it was written, byte for byte
        parts.append(f" A difference within one paired SE is not established and one below {band:g} is treated as "
                     "practically nil; single fold-seed differences below about 0.02 never were established.")
    return "".join(parts)


def _plain(obj):
    """JSON-ready copy: numpy scalars and arrays become Python numbers and lists, so the JSON twin re-renders the
    markdown byte for byte."""
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def main(argv=None) -> int:
    """The command line (argv None: sys.argv, re-executed under PYTHONHASHSEED=0, the lab's seed, when it is not
    already that: genemila.sandbox.reexec_under_hash_seed), or a call from Python with its arguments (argv), which
    runs in this process under whatever hash seed it has; the protocol records the seed and whether it re-executed."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", nargs="*", default=[],
                    help="finished run directories (lab.db, public_data/, feature_store/)")
    ap.add_argument("--out", required=True, help="markdown report")
    ap.add_argument("--json", default=None, help="JSON twin (default: the report's path with .json)")
    ap.add_argument("--box", default=None, help="failed-feature box (default: <report stem>_feature_box.json)")
    ap.add_argument("--fold-seeds", nargs="+", type=int, default=None,
                    help="fold seeds, at least two (default: the run's cv_seed and cv_seed + 1)")
    ap.add_argument("--resamples", type=int, default=50, help="Lasso half-samples (default 50)")
    ap.add_argument("--no-pool", action="store_true", help="audit the selected model only")
    ap.add_argument("--score-sealed", action="store_true",
                    help="score the selected and the compact model once each on the sealed set (off by default)")
    ap.add_argument("--cache", default=None,
                    help="the tool's working directory: one checkpoint per audited run, so an interrupted job "
                         "resumes (default: a temporary directory, lost on exit; recommended for long jobs)")
    ap.add_argument("--from-json", default=None, help="re-render the markdown from a JSON twin; no run is opened")
    args = ap.parse_args(argv)
    if argv is None and not args.from_json:
        reexec_under_hash_seed("feature_audit")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.from_json:
        rep = json.loads(Path(args.from_json).read_text())
    else:
        if not args.runs:
            ap.error("--runs is required unless --from-json is given")
        if args.fold_seeds is not None and len(set(args.fold_seeds)) < 2:
            ap.error("--fold-seeds needs at least two distinct seeds")
        if args.resamples < 1:
            ap.error("--resamples must be at least 1")
        kw = dict(fold_seeds=args.fold_seeds, resamples=args.resamples, use_pool=not args.no_pool,
                  sealed=args.score_sealed)
        if args.cache:
            rep = analyse([Path(r) for r in args.runs], Path(args.cache), **kw)
        else:
            if len(args.runs) > 1:
                print("[feature_audit] no --cache: checkpoints go to a temporary directory, so an interrupted job "
                      "restarts from the first run", file=sys.stderr, flush=True)
            with tempfile.TemporaryDirectory(prefix="feature_audit_") as tmp:
                rep = analyse([Path(r) for r in args.runs], Path(tmp), **kw)
        rep = _plain(rep)
        Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1))
        box = Path(args.box) if args.box else out.with_name(out.stem + "_feature_box.json")
        box.write_text(json.dumps(_plain(build_box(rep)), indent=1))
    md = render(rep)
    out.write_text(md)
    print(f"wrote {out} ({len(md.encode())} bytes)")
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == [HASH_WORKER_ARG]:  # one process of the hash-seed check, started by hash_check
        sys.exit(_hash_seed_worker())
    sys.exit(main())
