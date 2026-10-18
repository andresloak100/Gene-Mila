"""Discovery mode: hypothesis generation driven by the data, not by a fixed idea list (claim #69).

Andres, 17 October 2026: the agents should find the biological feature the linear model lacks, the generation should
be automated rather than a list of any fixed size, and a find should be testable in vitro. Blocks F and G showed what
the planner does with a fixed idea list and no view of its own errors: of the 499 features the block G agents built on
the clean bundles, about 180 describe themselves as a product of two existing quantities or a random projection of a
table, 101 call ctx.feature to transform a feature the model already had, and none passed the fair test. When
schedule.discovery is on (off by default: every state, prompt, hash and summary of a run without it is unchanged) the
planner gets three things it did not have:

  1. residual evidence: where the current best model fails, from the training perturbations out of fold only (the
     best experiment's cv.npz): the worst-predicted perturbations and what the knowledge files say about their
     targets, the genes that carry the squared residual and the annotation columns, gene sets and regulators they
     share, and whether the residual holds a shared program the features lack. No visible-validation or sealed label
     is read, so the evidence steers nothing the model is selected on.
  2. inputs instead of idea areas: the bundle's inputs (control statistics, training labels, targets, every knowledge
     file and every column of its per-gene tables) and which of them no completed feature has read, so "unexplored"
     is measured rather than matched by keyword; the planner names the input each feature brings.
  3. a measured "derived" flag: the pipeline fits each new feature's columns from its parent's columns (linear terms,
     squares, pairwise products) out of fold by perturbation; the feature lists of the state show the R² as
     derived_r2 and, at or above schedule.discovery_derived_r2, flag the feature as derived: the lab meeting's
     "stale", a product, log or interaction of what the model already has.

The planner is dry (Planner.dry) once schedule.discovery_dry_rounds consecutive counted rounds (rounds asked for new
features that proposed at least one) name no unread input, so the number of hypotheses a run generates is decided by
the data and the inputs, never by a count. tools/residual_mining.py (docs/NOVEL_FEATURE_NEEDS.md, M1) asks the same
questions of a finished run offline; this is the live version. Hypothesis generation only: nothing here is evidence,
and a feature it leads to is tested like any other, by the fair test (tools/feature_compare.py) on a tier the
generator never read. A run in discovery mode must be reported as its own arm; genemila/benchmark/table.py's run_arm
does not label it yet (issue #72), so until that lands its run directory carries the suffix _discovery and its rows
are tabulated apart by hand.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

STATE_EVIDENCE = "residual_evidence"     # research-state keys (rendered as "## RESIDUAL EVIDENCE", "## INPUTS UNEXPLORED")
STATE_INPUTS = "inputs_unexplored"
EVIDENCE_HEADING = "## RESIDUAL EVIDENCE"  # prompts.planner_user reads the mode from the state text, like dataset_flags
DEFAULTS = {"discovery": False, "discovery_dry_rounds": 3, "discovery_derived_r2": 0.8}

# the inputs every bundle offers, by the name feature code reads them under (FeatureContext)
CONTROL_INPUTS = {
    "control_cells": "the per-cell control matrix (distribution shape: dropout, bimodality, cell-to-cell variance)",
    "control_mean": "mean control expression per gene", "control_std": "control standard deviation per gene",
    "gene_corr": "gene-gene Pearson correlation across control cells"}
LABEL_INPUTS = {"train_delta": "the training responses, leave-one-out (response transfer)"}
TARGET_INPUTS = {"target_genes": "the perturbation's targets (identity, measured knockdown)"}
BUILTIN_READS = {"control_mean": {"control_mean"}, "mean_response": {"train_delta"}, "is_target": {"target_genes"},
                 "additive_response": {"train_delta", "target_genes"}}
FORMS = ("gene-side g(g): the response gene's own property; perturbation-side a(p): the targets' property, which alone "
         "cannot raise pearson_delta; interaction a(p)*b(g); transfer: a similarity-weighted copy of training responses")
RULE = ("a feature is new when it reads an input listed as unread, plainly, and names it in new_input; a product, "
        "ratio, log, rank or projection of existing columns is derived (measured after each experiment as "
        "derived_r2 in the feature lists: at or above {thr:g} the feature is flagged derived)")
GROUP_CHARS = 40     # a gene set or regulator name is cut to this in the evidence lines

TOP_PERTS = 6        # worst perturbations shown
TOP_GENES = 8        # genes named per list
TOP_SETS = 4         # enriched groups named
TOP_SHARE = 0.05     # the genes carrying the residual: this share of genes, at least MIN_TOP
MIN_TOP = 20
MIN_GROUP = 5        # a gene set or regulator's targets must have this many measured genes to be tested
MIN_OVERLAP = 3
NULL_REPS = 3        # permutations behind the structure reading (cheap: it runs every planner round)
LIST_CAP = 12        # names listed before "and N more"

_KNOWLEDGE: dict = {}   # (public_dir, name) -> classified knowledge file; files never change during a run
_EVIDENCE: dict = {}    # (run_dir, experiment_id) -> evidence; recomputed only when the best model changes
_LOCK = threading.Lock()


def setting(cfg: dict, key: str):
    return (cfg.get("schedule") or {}).get(key, DEFAULTS[key])


def enabled(cfg: dict) -> bool:
    return bool(setting(cfg, "discovery"))


# ================================================================== the bundle's inputs
def classify(obj) -> dict:
    """What a knowledge file is, by its shape: an external screen (perts), a per-gene table (columns + genes), gene
    sets (name -> list), a network (edge list), a gene list, or other."""
    if isinstance(obj, dict):
        if isinstance(obj.get("perts"), dict):
            return {"kind": "screen", "n": len(obj["perts"])}
        if isinstance(obj.get("columns"), list) and isinstance(obj.get("genes"), dict):
            return {"kind": "table", "columns": [str(c) for c in obj["columns"]], "genes": obj["genes"],
                    "n": len(obj["genes"])}
        if obj and all(isinstance(v, (list, tuple)) for v in obj.values()):
            return {"kind": "sets", "sets": {str(k): [str(g) for g in v] for k, v in obj.items()}, "n": len(obj)}
        return {"kind": "other", "n": len(obj)}
    if isinstance(obj, list):
        if obj and all(isinstance(e, (list, tuple)) and len(e) >= 2 for e in obj):
            return {"kind": "network", "edges": [[str(e[0]), str(e[1])] for e in obj], "n": len(obj)}
        return {"kind": "list", "genes": [str(g) for g in obj], "n": len(obj)}
    return {"kind": "other", "n": 0}


def knowledge_files(ctx) -> dict[str, dict]:
    """Every knowledge file of the context's bundle but targets, classified (cached per bundle: the files do not
    change during a run)."""
    out = {}
    for name in ctx.available_knowledge():
        if name == "targets":
            continue
        key = (str(ctx.public_dir), name)
        with _LOCK:
            if key not in _KNOWLEDGE:
                _KNOWLEDGE[key] = classify(ctx.knowledge(name))
            out[name] = _KNOWLEDGE[key]
    return out


def input_names(files: dict) -> list[str]:
    names = [*CONTROL_INPUTS, *LABEL_INPUTS, *TARGET_INPUTS]
    for name, k in files.items():
        names.append(name)
        if k["kind"] == "table":
            names += [f"{name}.{c}" for c in k["columns"]]
    return names


_CTX_ATTR = re.compile(r"\bctx\.([A-Za-z_]\w*)")
_KNOW = re.compile(r"ctx\.knowledge\(\s*[\"']([^\"']+)[\"']")
_LITERAL = re.compile(r"[\"']([A-Za-z0-9_]{2,})[\"']")


def feature_reads(source: str, files: dict) -> dict:
    """What a plugin reads, from its source: the context inputs it names, the knowledge files it opens (by a literal
    in ctx.knowledge, by a literal anywhere in the file, or all of them when it iterates ctx.available_knowledge) and,
    for a per-gene table, the columns it names as string literals (a plugin that projects a whole table names none,
    so the table counts as read and its columns do not); derived when it composes another feature through
    ctx.feature."""
    attrs = set(_CTX_ATTR.findall(source))
    inputs = {a for a in attrs if a in CONTROL_INPUTS or a in LABEL_INPUTS}
    if attrs & {"target_genes", "target_indices"}:
        inputs.add("target_genes")
    literals = set(_LITERAL.findall(source))
    opened = (set(_KNOW.findall(source)) | literals) & set(files)
    if "available_knowledge(" in source:
        opened = set(files)
    for k in opened:
        inputs.add(k)
        if files[k]["kind"] == "table":
            inputs |= {f"{k}.{c}" for c in files[k]["columns"] if c in literals}
    return {"inputs": inputs, "derived": "ctx.feature(" in source}


def coverage(lab, files: dict) -> dict[str, dict]:
    """Per input: the completed features that read it, split into plain readers and derived ones (those that compose
    another feature). Only features in the run's store count, which are the ones an experiment completed with; a
    built-in reads what its code reads, and a plugin's declared `inputs` count with what its source shows."""
    cov = {n: {"plain": [], "derived": []} for n in input_names(files)}
    for meta in lab.db.features():
        name = meta["name"]
        if name in BUILTIN_READS:
            reads, derived = BUILTIN_READS[name], False
        else:
            path = lab.store / f"{name}.py"
            if not path.exists():
                continue
            r = feature_reads(path.read_text(), files)
            reads, derived = r["inputs"], r["derived"]
            declared = meta.get("inputs_json") or []
            reads = reads | {"target_genes" if d == "targets" else str(d) for d in declared if isinstance(d, str)}
        for inp in reads:
            if inp in cov:
                cov[inp]["derived" if derived else "plain"].append(name)
    return cov


def _names(items: list[str], cap: int = LIST_CAP) -> str:
    return ", ".join(items[:cap]) + (f" and {len(items) - cap} more" if len(items) > cap else "")


def render_inputs(files: dict, cov: dict, thr: float = DEFAULTS["discovery_derived_r2"]) -> list[str]:
    """The INPUTS UNEXPLORED section: what the bundle offers and whether a completed feature has read it. An input
    read only inside a feature that transforms another feature (ctx.feature) counts as unread, here and for the
    judge (unread_inputs)."""
    def tag(name):
        c = cov[name]
        if c["plain"]:
            return f"{name} (read by {len(c['plain'])})"
        return f"{name} (unread; derived features only)" if c["derived"] else f"{name} (unread)"

    lines = ["Inputs the bundle offers and whether a completed feature reads them plainly; an input read only inside "
             "a feature that transforms another feature (ctx.feature) counts as unread. Name in new_input the unread "
             "input a new feature brings."]
    lines.append("control statistics: " + ", ".join(tag(n) for n in CONTROL_INPUTS)
                 + "; training labels: " + ", ".join(tag(n) for n in LABEL_INPUTS)
                 + "; targets: " + ", ".join(tag(n) for n in TARGET_INPUTS))
    for name, k in files.items():
        c = cov[name]
        line = f"{name} ({k['kind']}, {k['n']}): read by {len(c['plain'])} plain, {len(c['derived'])} derived"
        if k["kind"] == "table":
            unread = [col for col in k["columns"] if not cov[f'{name}.{col}']["plain"] and not cov[f'{name}.{col}']["derived"]]
            derived = [col for col in k["columns"] if not cov[f'{name}.{col}']["plain"] and cov[f'{name}.{col}']["derived"]]
            if unread:
                line += f"; columns unread: {_names(unread)}"
            if derived:
                line += f"; columns unread (derived features only): {_names(derived)}"
        lines.append(line)
    lines.append(f"forms: {FORMS}")
    lines.append("rule: " + RULE.format(thr=thr))
    return lines


# ================================================================== residual evidence (training folds only)
def best_modelled(lab) -> dict | None:
    """The best completed experiment with a fitted model and an artifact (a cv.npz when the run cross-validates): the
    analytic baselines have no artifact and the ensemble no folds."""
    rows = lab.db.query("SELECT * FROM experiments WHERE status='completed' AND primary_score IS NOT NULL AND "
                        "artifact_dir IS NOT NULL AND COALESCE(kind, '') != 'ensemble' ORDER BY primary_score DESC LIMIT 1")
    return rows[0] if rows else None


def oof_delta(lab, rec: dict) -> np.ndarray | None:
    """An experiment's out-of-fold predicted change for the training perturbations at its chosen alpha (its cv.npz,
    as Lab.visible_predictions reads it), or None when the run does not cross-validate."""
    path = Path(rec["artifact_dir"]) / "cv.npz"
    if lab.cv_folds <= 1 or not path.exists():
        return None
    c = np.load(path, allow_pickle=False)
    if [str(p) for p in c["perts"]] != lab._train.perts:
        return None
    alphas = list(map(float, c["alphas"]))
    i = alphas.index(rec["best_alpha"]) if rec.get("best_alpha") in alphas else 0
    return c["delta"][i].astype(np.float64)


def row_pearson(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a - a.mean(axis=1, keepdims=True)
    b = b - b.mean(axis=1, keepdims=True)
    den = np.sqrt((a * a).sum(axis=1) * (b * b).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        r = (a * b).sum(axis=1) / den
    return np.where(np.isfinite(r), r, 0.0)


def spearman(x, y) -> float | None:
    """Rank correlation over the finite pairs (None is missing); None below 3 pairs or when a side is constant."""
    from scipy.stats import spearmanr
    x = np.array([np.nan if v is None else v for v in x], dtype=np.float64)
    y = np.array([np.nan if v is None else v for v in y], dtype=np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.ptp(x[ok]) == 0 or np.ptp(y[ok]) == 0:
        return None
    return float(spearmanr(x[ok], y[ok])[0])


def groups_of(files: dict, universe: set[str]) -> dict[str, set[str]]:
    """Every gene group the knowledge files define, restricted to measured genes: each gene set, and each network
    node's neighbours (a regulator's targets in a directed file, a protein's partners in an undirected one)."""
    out = {}
    for name, k in files.items():
        if k["kind"] == "sets":
            for s, members in k["sets"].items():
                out[f"{name}:{s}"] = set(members) & universe
        elif k["kind"] == "network":
            nb = defaultdict(set)
            for a, b in k["edges"]:
                nb[a].add(b)
                nb[b].add(a)
            for node, members in nb.items():
                out[f"{name}:{node} neighbours"] = members & universe
    return {g: m for g, m in out.items() if len(m) >= MIN_GROUP}


def enrichment(top: set[str], universe: set[str], groups: dict[str, set[str]], k: int = TOP_SETS) -> list[dict]:
    """Hypergeometric over-representation of `top` in each group, the k smallest p first; hypothesis generation, so no
    multiplicity correction is applied and none is implied."""
    from scipy.stats import hypergeom
    N, n = len(universe), len(top & universe)
    out = []
    for name, members in groups.items():
        hit = len(members & top)
        if hit < MIN_OVERLAP:
            continue
        p = float(hypergeom.sf(hit - 1, N, len(members), n))
        out.append({"group": name, "hit": hit, "size": len(members), "p": p})
    out.sort(key=lambda r: (r["p"], -r["hit"], r["group"]))
    return out[:k]


def target_coexpression(ctx, train: list[str]) -> dict[str, float]:
    """|Pearson r| across control cells between every pair of distinct measured training targets, keyed by sorted
    gene pair; a small corrcoef over the target columns only, never the full gene-by-gene matrix."""
    idx = sorted({i for q in train for i in ctx.target_indices(q)})
    if len(idx) < 2:
        return {}
    with np.errstate(invalid="ignore", divide="ignore"):
        C = np.nan_to_num(np.corrcoef(ctx.control_cells[:, idx].T))
    return {(idx[a], idx[b]): float(abs(C[a, b])) for a in range(len(idx)) for b in range(a + 1, len(idx))}


def perturbation_row(p: str, score: float, ctx, files: dict, train: list[str], true_delta: np.ndarray, i: int,
                     set_members: dict[str, set[str]], neighbours: dict[str, set[str]],
                     coexpr: dict | None = None) -> dict:
    """One badly predicted training perturbation: its OOF score, how far its targets moved, and what the knowledge
    files hold about its targets (the agents' similarity features copy responses along exactly these)."""
    tg, ti = ctx.target_genes(p), ctx.target_indices(p)
    change = None
    if ti:
        base = float(ctx.control_mean[ti].mean())
        change = float(true_delta[i, ti].mean() / base) if base > 0 else None
    sets = set().union(*(set_members.get(g, set()) for g in tg)) if tg else set()
    partners = set().union(*(neighbours.get(g, set()) for g in tg)) - set(tg) if tg else set()
    nearest, best = None, 0.0
    for q in train:
        if q == p:
            continue
        qs = set().union(*(set_members.get(g, set()) for g in ctx.target_genes(q)))
        j = len(sets & qs) / len(sets | qs) if sets | qs else 0.0
        if j > best:
            nearest, best = q, j
    coex, coex_with = 0.0, None
    if ti:
        coexpr = target_coexpression(ctx, train) if coexpr is None else coexpr
        for q in train:
            if q == p:
                continue
            for a in ti:
                for b in ctx.target_indices(q):
                    if a != b:  # a shared target gene (a pair and its single) is identity, not co-expression
                        v = coexpr.get((min(a, b), max(a, b)), 0.0)
                        if v > coex:
                            coex, coex_with = v, q
    return {"pert": p, "oof_pearson_delta": float(score), "n_targets_measured": len(ti), "target_change": change,
            "n_gene_sets": len(sets), "n_partners": len(partners), "nearest_by_sets": nearest,
            "nearest_jaccard": best, "coexpr_max": coex, "coexpr_with": coex_with}


def residual_evidence(lab, rec: dict, ctx, files: dict) -> dict:
    """The three readings of tools/residual_mining.py on the run's own best model, from its out-of-fold predictions of
    the training perturbations: no refit, no held-out label."""
    pred = oof_delta(lab, rec)
    if pred is None:
        return {"available": False, "experiment_id": rec["experiment_id"],
                "reason": "no out-of-fold predictions (experiment.cv_folds must be above 1)"}
    train = lab._train.perts
    Y = lab._train.means - lab.control_mean
    E = Y - pred
    r = row_pearson(pred, Y)
    universe = set(ctx.genes)
    set_members, neighbours = defaultdict(set), defaultdict(set)
    for name, k in files.items():
        if k["kind"] == "sets":
            for s, members in k["sets"].items():
                for g in members:
                    set_members[g].add(f"{name}:{s}")
        elif k["kind"] == "network":
            for a, b in k["edges"]:
                neighbours[a].add(b)
                neighbours[b].add(a)
    order = np.argsort(r, kind="stable")
    coexpr = target_coexpression(ctx, train)
    worst = [perturbation_row(train[i], r[i], ctx, files, train, Y, i, set_members, neighbours, coexpr)
             for i in order[:TOP_PERTS]]

    msr = (E ** 2).mean(axis=0)
    bias = E.mean(axis=0)
    top_n = max(MIN_TOP, int(TOP_SHARE * ctx.n_genes))
    top_idx = np.argsort(-msr, kind="stable")[:top_n]
    top = {ctx.genes[i] for i in top_idx}
    corr = {"control_mean": spearman(msr, ctx.control_mean), "control_std": spearman(msr, ctx.control_std)}
    for name, k in files.items():
        if k["kind"] != "table":
            continue
        for j, col in enumerate(k["columns"]):
            vals = [(v[j] if isinstance(v, (list, tuple)) and len(v) > j else None) for v in (k["genes"].get(g) for g in ctx.genes)]
            if all(v is None or isinstance(v, (int, float)) for v in vals):
                corr[f"{name}.{col}"] = spearman(msr, vals)
    groups = groups_of(files, universe)
    scale = float(np.sqrt(msr).mean()) or 1.0
    under = [ctx.genes[i] for i in np.argsort(-bias, kind="stable")[:TOP_GENES] if bias[i] > 0.5 * scale]
    over = [ctx.genes[i] for i in np.argsort(bias, kind="stable")[:TOP_GENES] if bias[i] < -0.5 * scale]

    U, s, Vt = np.linalg.svd(E, full_matrices=False)
    share = s ** 2 / max(float((s ** 2).sum()), 1e-300)
    rng = np.random.default_rng(0)
    null = [np.linalg.svd(rng.permuted(E, axis=0), compute_uv=False) for _ in range(NULL_REPS)]
    null1 = float(np.mean([(t ** 2 / (t ** 2).sum())[0] for t in null]))
    load = Vt[0]
    comp_genes = [ctx.genes[i] for i in np.argsort(-np.abs(load), kind="stable")[:TOP_GENES]]
    comp_perts = [train[i] for i in np.argsort(-np.abs(U[:, 0]), kind="stable")[:5]]
    comp_top = {ctx.genes[i] for i in np.argsort(-np.abs(load), kind="stable")[:max(MIN_TOP, TOP_GENES * 6)]}
    return {
        "available": True, "experiment_id": rec["experiment_id"], "cv_folds": lab.cv_folds, "n_train": len(train),
        "oof_pearson_delta": float(r.mean()), "labels_read": ["training labels (public.npz)"],
        "worst": worst,
        "genes": {"top_n": top_n, "share": float(msr[top_idx].sum() / max(float(msr.sum()), 1e-300)),
                  "correlations": corr, "enriched": enrichment(top, universe, groups),
                  "under_predicted": under, "over_predicted": over},
        "structure": {"share": float(share[0]), "null_share": null1, "low_rank": bool(share[0] > 2 * null1),
                      "top_pert_share": float((U[:, 0] ** 2).max()), "genes": comp_genes, "perts": comp_perts,
                      "enriched": enrichment(comp_top, universe, groups, 3)},
        "generated_at": time.time(),
    }


def _group(name: str) -> str:
    return name if len(name) <= GROUP_CHARS else name[:GROUP_CHARS - 1] + "…"


def _enriched(rows: list[dict]) -> str:
    return "; ".join(f"{_group(e['group'])} ({e['hit']}/{e['size']}, p {e['p']:.0e})" for e in rows) or "none"


def render_evidence(ev: dict) -> list[str]:
    """The RESIDUAL EVIDENCE section: the structure reading and the gene properties first, the worst perturbations
    last, so a cut at the section budget (research_state.EVIDENCE_SECTION_CHARS) drops the least telling lines."""
    if not ev.get("available"):
        return [f"not available: {ev.get('reason', 'no completed model yet')}; propose from the inputs"]
    g, st = ev["genes"], ev["structure"]
    lines = [f"From the {ev['n_train']} training perturbations out of fold only ({ev['experiment_id']}, "
             f"{ev['cv_folds']} folds, mean OOF pearson_delta {ev['oof_pearson_delta']:.3f}); no held-out label read. "
             "pearson_delta ignores a per-perturbation scale: a feature must change the pattern across genes."]
    if st["low_rank"]:
        lines.append(f"residual structure: component 1 holds {st['share']:.0%} of the residual variance (permuted "
                     f"{st['null_share']:.0%}), a shared pattern the features lack"
                     + (" (mostly one perturbation)" if st["top_pert_share"] > 0.5 else "")
                     + f"; its genes {', '.join(st['genes'])}; perturbations {', '.join(st['perts'])}; "
                     f"enriched in {_enriched(st['enriched'])}")
    else:
        lines.append(f"residual structure: diffuse (component 1 holds {st['share']:.0%} of the variance, permuted "
                     f"{st['null_share']:.0%}): no shared program is missing; look at the gene properties and the "
                     "worst perturbations")
    corr = sorted(((k, v) for k, v in g["correlations"].items() if v is not None), key=lambda kv: -abs(kv[1]))[:4]
    lines.append(f"genes carrying the residual (top {g['top_n']} by squared OOF residual hold {g['share']:.0%} of it): "
                 f"their residual follows " + (", ".join(f"{k} (rho {v:+.2f})" for k, v in corr) or "no listed property")
                 + f"; enriched in {_enriched(g['enriched'])}")
    if g["under_predicted"] or g["over_predicted"]:
        lines.append(f"consistently under-predicted (true change above the prediction): {', '.join(g['under_predicted']) or 'none'}; "
                     f"over-predicted: {', '.join(g['over_predicted']) or 'none'}")
    for w in ev["worst"]:
        parts = [f"worst: {w['pert']} r {w['oof_pearson_delta']:.2f}"]
        if w["target_change"] is not None:
            parts.append(f"targets moved {w['target_change']:+.2f} of control")
        parts.append(f"targets in {w['n_gene_sets']} sets, {w['n_partners']} partners")
        if w["nearest_by_sets"]:
            parts.append(f"nearest by sets {w['nearest_by_sets']} ({w['nearest_jaccard']:.2f})")
        if w["coexpr_with"]:
            parts.append(f"co-expr max |r| {w['coexpr_max']:.2f} with {w['coexpr_with']}")
        lines.append("; ".join(parts))
    return lines


# ================================================================== the planner's view and judgement
def state_sections(lab) -> dict:
    """The two discovery sections of the research state (research_state.build_state), computed from the run's public
    data and store; the evidence is cached per best experiment and written once under planner/."""
    from .features.api import FeatureContext
    ctx = FeatureContext.shared(lab.public_dir)
    files = knowledge_files(ctx)
    cov = coverage(lab, files)
    rec = best_modelled(lab)
    if rec is None:
        ev = {"available": False, "reason": "no completed model yet"}
    else:
        key = (str(lab.run_dir), rec["experiment_id"])
        with _LOCK:
            ev = _EVIDENCE.get(key)
        if ev is None:
            ev = residual_evidence(lab, rec, ctx, files)
            with _LOCK:
                _EVIDENCE[key] = ev
            out = lab.run_dir / "planner"
            out.mkdir(exist_ok=True)
            (out / f"discovery_{rec['experiment_id']}.json").write_text(json.dumps(ev, indent=1, default=float))
    thr = float(setting(lab.cfg, "discovery_derived_r2"))
    return {STATE_EVIDENCE: render_evidence(ev), STATE_INPUTS: render_inputs(files, cov, thr)}


def unread_inputs(lab) -> set[str]:
    """The inputs no completed feature reads plainly (one read only inside a ctx.feature transform is unread)."""
    from .features.api import FeatureContext
    files = knowledge_files(FeatureContext.shared(lab.public_dir))
    return {n for n, c in coverage(lab, files).items() if not c["plain"]}


def _mentions(name: str, text: str) -> bool:
    return re.search(rf"(?<![a-z0-9_]){re.escape(name.lower())}(?![a-z0-9_])", text) is not None


def judge_plan(hypotheses: list, unread: set[str]) -> list[list[str]]:
    """Per hypothesis, the unread inputs it names, so the lab, not the planner, decides what is new: its new_input
    field (an input's full name, or a table column's bare name, which resolves to every unread column of that name),
    or an input's full name in its feature text. A bare column name in prose never counts (a protein table's columns
    are words such as membrane and nucleus), a hypothesis whose feature composes another through ctx.feature is
    derived, and only a new-feature hypothesis can name an input."""
    out = []
    for h in hypotheses:
        if not isinstance(h, dict) or h.get("action", "new_feature") != "new_feature":
            out.append([])
            continue
        nf = h.get("new_feature") if isinstance(h.get("new_feature"), dict) else {}
        code = " ".join(str(nf.get(k, "")) for k in ("description", "implementation_hint"))
        if "ctx.feature(" in code:
            out.append([])
            continue
        text = " ".join(str(nf.get(k, "")) for k in ("name", "description", "implementation_hint"))
        text = (text + " " + str(h.get("hypothesis", ""))).lower()
        found = {n for n in unread if _mentions(n, text)}
        named = str(nf.get("new_input", "")).strip().lower()
        if named:
            found |= {n for n in unread if n.lower() == named or ("." in n and n.split(".", 1)[1].lower() == named)}
        out.append(sorted(found))
    return out


def _read_rounds(path: Path) -> list[dict]:
    try:
        rows = json.loads(path.read_text()) if path.exists() else []
    except (OSError, ValueError):  # a torn file (the controller died mid-write) costs no planner call and no summary
        rows = []
    return rows if isinstance(rows, list) else []


def record_round(lab, rnd: int, novel: list[list[str]], n: int, counted: bool = True) -> dict:
    """Append one round to planner/discovery_rounds.json (the summary reads it) and return its entry. `counted` says
    whether the round counts toward the dry rule: a round asked for new features that proposed at least one."""
    entry = {"round": rnd, "hypotheses": n, "novel": sum(1 for v in novel if v), "counted": bool(counted),
             "inputs": sorted({x for v in novel for x in v}), "ts": time.time()}
    path = lab.run_dir / "planner" / "discovery_rounds.json"
    with _LOCK:
        path.parent.mkdir(exist_ok=True)
        rows = _read_rounds(path)
        rows.append(entry)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp.json")
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(rows, indent=1))
        os.replace(tmp, path)
    return entry


def dry_round(rows: list[dict], limit: int) -> int | None:
    """The round at which the dry rule fired: `limit` counted rounds in a row without an unread input (a round that
    names one resets the count, counted or not)."""
    run = 0
    for e in rows:
        if e["novel"]:
            run = 0
        elif e.get("counted", True):
            run += 1
        if run >= limit:
            return e["round"]
    return None


def summary(lab) -> dict:
    """summary.json["discovery"]: how the generation went, from the round ledger and the experiments."""
    rows = _read_rounds(lab.run_dir / "planner" / "discovery_rounds.json")
    limit = int(setting(lab.cfg, "discovery_dry_rounds"))
    thr = float(setting(lab.cfg, "discovery_derived_r2"))
    dry_at = dry_round(rows, limit)
    derived, plain, scored = [], [], 0
    for e in lab.db.query("SELECT new_feature, diagnostics_json, proposed_feature_json FROM experiments WHERE "
                          "status='completed' AND new_feature IS NOT NULL"):
        d = (e.get("diagnostics_json") or {}).get("derivability")
        if d is not None and d.get("r2") is not None:  # None: the feature's columns were not in the design matrix
            scored += 1
            (derived if d["r2"] >= thr else plain).append({"feature": e["new_feature"], "r2": round(d["r2"], 3),
                                                            "novel_inputs": (e.get("proposed_feature_json") or {}).get("novel_inputs", [])})
    return {"enabled": True, "rounds": len(rows), "rounds_counted": sum(1 for e in rows if e.get("counted", True)),
            "hypotheses": sum(e["hypotheses"] for e in rows),
            "hypotheses_naming_an_unread_input": sum(e["novel"] for e in rows),
            "inputs_proposed": sorted({x for e in rows for x in e["inputs"]}),
            "dry_rule": f"{limit} consecutive counted rounds (asked for new features, proposed at least one) without "
                        "an unread input", "dry_at_round": dry_at,
            "features_scored_for_derivability": scored, "derived_r2_threshold": thr,
            "derived_features": sorted(derived, key=lambda r: -r["r2"]), "new_input_features": plain,
            "evidence_files": sorted(p.name for p in (lab.run_dir / "planner").glob("discovery_EXP_*.json"))}


# ================================================================== derivability (runs inside the experiment process)
def derivability(X: np.ndarray, new_idx: list[int], old_idx: list[int], n_perts: int, n_genes: int, seed: int = 0,
                 folds: int = 5, max_rows: int = 20000, max_products: int = 10, alpha: float = 1e-3,
                 max_parent: int = 150) -> dict:
    """How well a new feature's columns are predicted from the parent's columns, out of fold by perturbation: ridge on
    the parent columns, their squares and the pairwise products of the first max_products of them (no products once
    the parent has more than max_parent columns), on a seeded sample of (perturbation, gene) rows of the standardised
    design matrix (rows ordered perturbation-major, as pipeline._concat lays them out). R² near 1 means the feature is
    a transform of what the model already has. One Gram matrix per fold serves every new column, so the cost does not
    grow with the feature's dimension."""
    if not new_idx:
        return {"r2": None, "per_column": [], "n_rows": 0, "n_basis": 0}
    rng = np.random.default_rng(seed)
    n_rows = X.shape[0]
    rows = np.sort(rng.choice(n_rows, size=min(max_rows, n_rows), replace=False))
    fold_of_pert = rng.permutation(n_perts) % max(2, min(folds, n_perts))
    fold = fold_of_pert[rows // n_genes]
    old = X[rows][:, old_idx].astype(np.float64)
    parts = [np.ones((len(rows), 1)), old, old ** 2]
    k = min(max_products, old.shape[1]) if old.shape[1] <= max_parent else 0  # a wide parent: linear and squares only
    parts += [old[:, [i]] * old[:, [j]] for i in range(k) for j in range(i + 1, k)]
    B = np.concatenate(parts, axis=1)
    mu, sd = B[:, 1:].mean(axis=0), B[:, 1:].std(axis=0)
    sd[sd == 0] = 1.0
    B[:, 1:] = (B[:, 1:] - mu) / sd
    Y = X[rows][:, new_idx].astype(np.float64)
    pred = np.zeros_like(Y)
    for f in np.unique(fold):  # one Gram matrix and one solve per fold, for every new column at once
        tr, te = fold != f, fold == f
        if tr.sum() == 0 or te.sum() == 0:
            continue
        A = B[tr].T @ B[tr] + alpha * tr.sum() * np.eye(B.shape[1])
        pred[te] = B[te] @ np.linalg.solve(A, B[tr].T @ Y[tr])
    per = []
    for j in range(Y.shape[1]):
        y = Y[:, j]
        if np.ptp(y) == 0:
            per.append(1.0)  # a constant column is the intercept
            continue
        ss_res, ss_tot = float(((y - pred[:, j]) ** 2).sum()), float(((y - y.mean()) ** 2).sum())
        per.append(max(-1.0, 1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0)
    return {"r2": float(np.mean(per)), "per_column": [float(v) for v in per], "n_rows": int(len(rows)),
            "n_basis": int(B.shape[1]),
            "basis": "parent columns, their squares" + (f" and the pairwise products of the first {k}" if k else "")
                     + "; ridge out of fold by perturbation"}
