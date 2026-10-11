"""Ingest a real single-cell perturbation screen from one or more .h5ad files.

Handles both common layouts:
  * scPerturb (the files CellForge downloads, e.g. AdamsonWeissman2016_*.h5ad):
    obs['perturbation'] with 'control' for controls, raw counts in X.
  * GEARS (perturb_processed.h5ad): obs['condition'] with 'ctrl', 'GENE+ctrl', log-normalised X.

Steps: detect raw counts and normalise them (counts per 10k, log1p, as in
scanpy/cell-eval); parse target genes out of perturbation labels; optionally
merge labels that target the same gene set (several guides per gene, or one
combination written in either order); split by perturbation, or by gene with
held-out categories; keep highly variable genes plus every measured target gene;
keep pseudobulk means of training perturbations (public), and cells of
held-out perturbations plus a control sample (private, for cell-eval).

CellForge downloads (scPerturb RNA archive, https://zenodo.org/records/13350497):
    AdamsonWeissman2016_GSM2406675_10X001.h5ad
    AdamsonWeissman2016_GSM2406677_10X005.h5ad
    AdamsonWeissman2016_GSM2406681_10X010.h5ad
    NormanWeissman2019_filtered.h5ad
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np

from .bundle import SET_ORDER, make_gene_splits, make_splits, split_id_for, write_bundle

CONTROL_LABELS = {"control", "ctrl", "non-targeting", "nontargeting", "non_targeting", "nt", "neg", "negative"}
_LABEL_SPLIT = re.compile(r"[+_|,;\s]+")
_NEG_CTRL = re.compile(r"^neg_?ctrl\d*$", re.I)  # Norman 2019's negative-control guides, e.g. NegCtrl0
GENE_SELECTIONS = ("control", "control+train")
SPLIT_MODES = ("perturbation", "gene")


def _looks_like_counts(X) -> bool:
    import scipy.sparse as sp
    # sample across the whole matrix: the first entries of a CSC matrix belong to a few low-count genes
    data = X.data[::max(1, X.data.size // 100_000)] if sp.issparse(X) else np.asarray(X[:200]).ravel()
    data = data[data != 0]
    return data.size > 0 and bool(np.allclose(data, np.round(data))) and float(data.max()) > 20


def _normalise_log1p(X):
    import scipy.sparse as sp
    X = sp.csr_matrix(X, dtype=np.float32) if sp.issparse(X) else np.asarray(X, dtype=np.float32)
    totals = np.asarray(X.sum(axis=1)).ravel()
    scale = 1e4 / np.where(totals > 0, totals, 1.0)
    if sp.issparse(X):
        X = sp.diags(scale.astype(np.float32)) @ X
        X.data = np.log1p(X.data)
        return X.tocsr()
    return np.log1p(X * scale[:, None])


def _is_suffix(token: str, gene_set: set[str] | None = None) -> bool:
    """A label token that names a guide or the control rather than a gene (ATF6_guide1, sgATF6, XBP1_1,
    HSPA5+ctrl, p1p2): the external screen's rule, reused so both read labels alike, plus a control label used as
    a token (CEBPE_control, CEBPE_NegCtrl0), so a single written beside a control guide is not an unknown token.
    With the measured genes, a token the rule reads as a guide only through its sg... form is one only when what
    follows "sg" is nothing, a number, a measured gene (sgATF6) or a control label (sgNT); any other such token is a
    gene symbol the screen did not measure (SGK1, SGPL1, SGMS1, SGTA), an unknown token, so a strict ingest drops
    its label and a loose one lists it as partial rather than pool SGK1_TBX2 silently into TBX2. A label with no
    token starting "sg" reads exactly as before."""
    from .external_screen import _SUFFIX  # imported here, since external_screen imports this module
    if token.lower() in CONTROL_LABELS or _NEG_CTRL.match(token):
        return True
    if not _SUFFIX.match(token):
        return False
    core = token[1:] if token[0] in "([" else token  # the rule allows one bracket on either side
    core = core[:-1] if core and core[-1] in ")]" else core
    if gene_set is None or core[:2].lower() != "sg":  # every other guide form: digits, guideN, gN, pNpM, ctrl, ...
        return True
    rest = core[2:]
    return rest == "" or rest.isdigit() or rest in gene_set or rest.lower() in CONTROL_LABELS \
        or bool(_NEG_CTRL.match(rest))


def perturbation_key(targets) -> str:
    """A perturbation's key: its target genes sorted and joined with '+', so CEBPE_KLF1 and KLF1_CEBPE name one
    perturbation, CEBPE+KLF1, and a single's key is its gene."""
    return "+".join(sorted(targets))


def parse_label(label: str, gene_set: set[str]) -> tuple[list[str], list[str]]:
    """A perturbation label split on + _ | , ; and whitespace, as (targets, unknown tokens): the targets are the
    tokens that are measured gene names, sorted and without repeats, so the key does not depend on the order the
    label lists them; the unknown tokens are those that are neither a measured gene nor a guide or control suffix
    (_is_suffix, which takes sg... for a guide only before nothing, a number, a measured gene or a control label),
    such as X in CEBPE_X when X is not measured, which would otherwise pool CEBPE_X into CEBPE."""
    targets, unknown = set(), []
    for t in _LABEL_SPLIT.split(label):
        if not t:
            continue
        if t in gene_set:
            targets.add(t)
        elif not _is_suffix(t, gene_set):
            unknown.append(t)
    return sorted(targets), unknown


def parse_targets(label: str, gene_set: set[str]) -> list[str]:
    """Target genes in a perturbation label, sorted: tokens split on + _ | , ; that are measured gene names."""
    return parse_label(label, gene_set)[0]


def canonical_key(entry: str, gene_set: set[str]) -> str | None:
    """The key of a perturbation named outside this ingest (a split file's entry), read by parse_label: GEARS's
    A+ctrl is A and B_A is A+B; None when the entry names no measured gene or holds a token that is neither a
    measured gene nor a guide or control suffix, so a misspelt entry is reported rather than matched to part of it.
    The gene list is needed because the suffix rule alone would take some symbols for guides (SGK1 for sg...)."""
    tg, unknown = parse_label(str(entry), gene_set)
    return perturbation_key(tg) if tg and not unknown else None


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _code_commit() -> tuple[str | None, bool | None]:
    """(commit, dirty) of the checkout this module runs from, or (None, None) without git."""
    import subprocess
    from .. import REPO_ROOT
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
        if head.returncode != 0:
            return None, None
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO_ROOT,
                                capture_output=True, text=True, timeout=30)
        return head.stdout.strip() or None, bool(status.stdout.strip()) if status.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None, None


def _column_var(read, rows: np.ndarray, n_genes: int, chunk: int = 10_000) -> np.ndarray:
    """Per-gene variance over the given cells (population variance, as numpy's default), from the column sums of
    x and x squared accumulated over chunks of rows, so a sparse matrix is never made dense whole and a dense chunk
    holds at most about 50 million values."""
    import scipy.sparse as sp
    s1, s2 = np.zeros(n_genes), np.zeros(n_genes)
    rows = np.sort(np.asarray(rows))
    chunk = max(1, min(chunk, 50_000_000 // max(n_genes, 1)))
    for i in range(0, len(rows), chunk):
        sub = read(rows[i:i + chunk])
        if sp.issparse(sub):
            sub = sp.csr_matrix(sub, dtype=np.float64)
            s1 += np.asarray(sub.sum(axis=0)).ravel()
            s2 += np.asarray(sub.multiply(sub).sum(axis=0)).ravel()
        else:
            sub = np.asarray(sub, dtype=np.float64)
            s1 += sub.sum(axis=0)
            s2 += (sub * sub).sum(axis=0)
    mean = s1 / max(len(rows), 1)
    return np.maximum(s2 / max(len(rows), 1) - mean * mean, 0.0)


def ingest_h5ad(
    h5ad: Path | list[Path],
    out_dir: Path,
    name: str,
    condition_key: str | None = None,
    control_value: str | list[str] | None = None,
    gene_name_key: str | None = None,
    n_hvg: int = 2000,
    max_control_cells: int = 2000,
    max_eval_cells: int = 300,
    min_cells: int = 20,
    collapse_by_target: bool = True,
    seed: int = 0,
    splits_file: Path | None = None,
    val_frac_of_train: float = 0.25,
    knowledge_dir: Path | None = None,
    strict_labels: bool = False,
    split_mode: str = "perturbation",
    gene_frac=(0.7, 0.15, 0.15),
    seen2_holdout: float = 0.2,
    modality: str | None = None,
    gene_selection: str = "control",
    sample_seed: int | None = None,
    backed: bool = False,
) -> Path:
    """Build a bundle. control_value may list several labels (e.g. different non-targeting guides).

    splits_file: JSON with train/val1/val2 (or train/val/test) perturbation lists. A file with only
    train/test (CellForge's protocol: one held-out test set) keeps their test set as our query-only
    val2 and carves our visible val1 out of their training perturbations (val_frac_of_train, seeded),
    so the held-out test perturbations are exactly theirs.

    Every option below is off by default, and with the defaults a bundle is built exactly as before them.
    gene_name_key: the var column holding gene symbols; None takes var['gene_name'] when present, else var_names,
    while a named column must exist. strict_labels: drop a label with a token that is neither a measured gene nor
    a guide or control suffix instead of pooling it into the perturbation of its measured genes (parse_label);
    such partial labels are listed in the manifest either way. split_mode "gene": make_gene_splits (gene_frac,
    seen2_holdout) instead of make_splits, writing the held-out categories into splits.json. modality: the screen's
    modality (e.g. CRISPRa), recorded in the manifest only when given. gene_selection "control+train": rank genes
    by their variance over the public control sample and every cell of the training perturbations, after the split,
    instead of over the control sample alone. sample_seed: seeds the control and evaluation-cell samples apart from
    the split seed; None uses the split seed, as before. The effective sample seed is recorded in
    private/perturbations.json, and in the manifest only when given and other than the split seed: the manifest
    reaches every run, and the split seed with the public perturbations rebuilds the split. backed: read one h5ad
    on disk, a group of rows at a time, normalising each group as it is read (the counts per 10k and log1p are per
    cell, so the values match the in-memory path), for a file larger than memory comfortably holds."""
    import anndata as ad
    import scipy.sparse as sp

    if split_mode not in SPLIT_MODES:
        raise ValueError(f"split_mode must be one of {SPLIT_MODES}, got {split_mode!r}")
    if gene_selection not in GENE_SELECTIONS:
        raise ValueError(f"gene_selection must be one of {GENE_SELECTIONS}, got {gene_selection!r}")
    if splits_file and split_mode != "perturbation":
        raise ValueError("a splits file defines the split itself; it does not combine with split_mode='gene'")
    paths = [Path(p) for p in (h5ad if isinstance(h5ad, (list, tuple)) else [h5ad])]
    if backed and len(paths) > 1:
        raise ValueError("backed reading takes a single h5ad file")
    source_md5 = [_md5(p) for p in paths]
    code_commit, code_dirty = _code_commit()
    if backed:
        adata = ad.read_h5ad(paths[0], backed="r")
    else:
        parts = [ad.read_h5ad(p) for p in paths]
        adata = parts[0] if len(parts) == 1 else ad.concat(parts, join="inner", label="source_file",
                                                            keys=[p.name for p in paths], index_unique="-")
    try:
        if condition_key is None:
            condition_key = next((k for k in ("perturbation", "condition", "target_gene", "gene", "guide_ids")
                                  if k in adata.obs), None)
            if condition_key is None:
                raise ValueError(f"cannot find the perturbation column in obs: {list(adata.obs.columns)}")
        # unlabelled cells are NaN and stay NaN through astype(str) on recent pandas; name them
        cond = adata.obs[condition_key].astype(object).fillna("unassigned").to_numpy(dtype=str)
        if control_value is None:
            found = [c for c in np.unique(cond) if c.lower() in CONTROL_LABELS]
            if not found:
                raise ValueError(f"cannot identify the control label among {sorted(np.unique(cond))[:20]}; "
                                 "pass --control explicitly")
            control_value = found
        controls = [control_value] if isinstance(control_value, str) else list(control_value)
        missing = [c for c in controls if c not in set(cond)]
        if missing:
            raise ValueError(f"control label(s) {missing} not found in obs[{condition_key!r}]")
        symbol_key = gene_name_key or "gene_name"
        if symbol_key in adata.var:
            genes = adata.var[symbol_key].astype(str).tolist()
        elif gene_name_key is not None:
            raise ValueError(f"var has no column {gene_name_key!r} (columns: {list(adata.var.columns)})")
        else:
            symbol_key, genes = None, adata.var_names.astype(str).tolist()
        gene_set = set(genes)

        if backed:  # X stays on disk; read() fetches rows (sorted) and normalises them as they arrive
            Xd = adata.X
            if getattr(Xd, "format", None) == "csc":
                raise ValueError("backed reading needs X stored by rows (CSR) or dense; this file stores it as CSC")
            probe = np.unique(np.linspace(0, adata.n_obs - 1, num=min(adata.n_obs, 20_000)).astype(np.int64))
            sample = Xd[probe]  # cells spread over the file stand in for the whole matrix
            raw_counts = _looks_like_counts(sp.csr_matrix(sample) if sp.issparse(sample) else np.asarray(sample))

            def read(rows):
                sub = Xd[np.asarray(rows, dtype=np.int64)]
                if raw_counts:
                    return _normalise_log1p(sub)
                return sp.csr_matrix(sub) if sp.issparse(sub) else np.asarray(sub)
        else:
            X = adata.X
            raw_counts = _looks_like_counts(X)
            if raw_counts:
                X = _normalise_log1p(X)
            X = X.tocsr() if sp.issparse(X) else X

            def read(rows):
                return X[rows]

        def dense(rows):
            rows = np.asarray(rows)
            if backed:  # read in increasing row order, then restore the order asked for
                order = np.argsort(rows, kind="stable")
                sub = read(rows[order])
                sub = sub[np.argsort(order, kind="stable")]
            else:
                sub = read(rows)
            return np.asarray(sub.todense() if sp.issparse(sub) else sub, dtype=np.float32)

        is_ctrl = np.isin(cond, controls)
        rng = np.random.default_rng(seed if sample_seed is None else sample_seed)
        ctrl_idx = np.flatnonzero(is_ctrl)
        if len(ctrl_idx) < 50:
            raise ValueError(f"only {len(ctrl_idx)} control cells labelled {controls!r}")
        perm = rng.permutation(ctrl_idx)
        ctrl_public = perm[:max_control_cells]
        ctrl_eval = perm[max_control_cells:max_control_cells + max_eval_cells]
        if len(ctrl_eval) < 50:  # not enough controls to keep the two samples disjoint
            ctrl_eval = perm[-max_eval_cells:]

        # group perturbation labels by their measured target-gene set (sorted, so either order of a combination pools)
        groups: dict[str, list[str]] = {}
        label_to_key: dict[str, str] = {}
        targets: dict[str, list[str]] = {}
        dropped, partial, strict_dropped = [], {}, {}
        labels_seen = np.unique(cond[~is_ctrl])
        for c in labels_seen:
            tg, unknown = parse_label(c, gene_set)
            if not tg:
                dropped.append(c)
                continue
            if unknown:  # a token that is neither a measured gene nor a guide or control suffix
                if strict_labels:
                    strict_dropped[str(c)] = unknown
                    continue
                partial[str(c)] = unknown
            key = perturbation_key(tg) if collapse_by_target else c
            groups.setdefault(key, []).append(c)
            label_to_key[c] = key
            targets[key] = tg
        if not groups:  # say why here: write_bundle would otherwise fail inside np.stack
            source = f"var[{symbol_key!r}]" if symbol_key else "var_names"
            strict_note = (f"; {len(strict_dropped)} label(s) dropped for a token that is no measured gene "
                           "(strict labels)" if strict_dropped else "")
            raise ValueError(
                f"no perturbation label names a measured gene: {len(labels_seen)} non-control labels (e.g. "
                f"{[str(c) for c in labels_seen[:5]]}) against {len(genes)} gene symbols from {source} (e.g. "
                f"{genes[:5]}){strict_note}; if those symbols are not gene names (Ensembl ids, say), pass "
                f"--gene-name-key with the var column that holds the names (var columns: {list(adata.var.columns)})")
        target_genes = {t for ts in targets.values() for t in ts}  # every parsed target, kept beside the HVGs

        pert_ncells, rows_by, dropped_min = {}, {}, {}
        for key, labels in groups.items():
            rows = np.flatnonzero(np.isin(cond, labels))
            if len(rows) < min_cells:
                dropped_min[str(key)] = int(len(rows))
                continue
            rows_by[key] = rows
            pert_ncells[key] = len(rows)
        if not rows_by:
            raise ValueError(f"no perturbation has min_cells={min_cells} cells: {len(groups)} perturbation(s), at most "
                             f"{max(dropped_min.values())} cells each")
        targets = {k: v for k, v in targets.items() if k in rows_by}

        not_in_split, unmatched = [], []
        if splits_file:  # an externally defined split (e.g. CellForge's) instead of our seeded one
            ext = json.loads(Path(splits_file).read_text())
            # entries naming a combination or GEARS's A+ctrl are read by canonical_key, but only for a bundle with
            # combinations, so a single-target bundle maps its split file exactly as before
            canonical = collapse_by_target and any(len(v) > 1 for v in targets.values())
            splits = external_splits(ext, list(rows_by), label_to_key, seed=seed, val_frac_of_train=val_frac_of_train,
                                     canonical_genes=gene_set if canonical else None, unmatched=unmatched)
            splits["seed"] = f"external:{Path(splits_file).name}"
            splits["split_id"] = split_id_for(splits)
            in_split = set(splits["train"]) | set(splits["val1"]) | set(splits["val2"])
            not_in_split = sorted(str(k) for k in rows_by if k not in in_split)
            rows_by = {k: v for k, v in rows_by.items() if k in in_split}
            targets = {k: v for k, v in targets.items() if k in in_split}
        elif split_mode == "gene":
            splits = make_gene_splits(targets, seed=seed, gene_frac=gene_frac, seen2_holdout=seen2_holdout)
        else:
            splits = make_splits(list(rows_by), seed=seed)

        ctrl_dense = dense(ctrl_public)
        if gene_selection == "control":
            var = ctrl_dense.var(axis=0)
        else:  # control+train: after the split, over the public controls and every training cell, never held-out cells
            pool = np.concatenate([ctrl_public] + [rows_by[k] for k in splits["train"]])
            var = _column_var(read, pool, len(genes))
        hvg = set(np.argsort(-var)[:n_hvg].tolist())
        hvg |= {i for i, g in enumerate(genes) if g in target_genes}
        keep = np.array(sorted(hvg))
        pert_means = {key: dense(rows)[:, keep].mean(axis=0) for key, rows in rows_by.items()}

        eval_cells = {"control": dense(ctrl_eval)[:, keep]}
        for key in splits["val1"] + splits["val2"]:
            rows = rows_by[key]
            if len(rows) > max_eval_cells:
                rows = rng.choice(rows, size=max_eval_cells, replace=False)
            eval_cells[key] = dense(np.sort(rows))[:, keep]

        kept_genes = [genes[i] for i in keep]
        knowledge, knowledge_meta = {}, None
        if knowledge_dir:
            from .knowledge import build, summary
            knowledge = build(Path(knowledge_dir), kept_genes)
            knowledge_meta = {"source_dir": str(knowledge_dir), "files": summary(knowledge)}
        part_of = {p: s for s in SET_ORDER for p in splits[s]}
        categories = splits.get("categories") or {}
        # every perturbation's cell count, held-out ones included, so this record stays private: the manifest goes to
        # every run's public directory (export_public) and holds no held-out count
        record = {
            "perturbations": {str(k): {"labels": [str(c) for c in groups[k]], "n_cells": int(pert_ncells[k]),
                                       "n_targets": len(targets[k]), "targets": targets[k], "set": part_of[k],
                                       "category": categories.get(k)} for k in sorted(pert_means)},
            "dropped": {"no_measured_target": [str(c) for c in dropped], "unknown_token": strict_dropped,
                        "min_cells": dropped_min, "not_in_split": not_in_split},
            "partial_labels": partial,
            "split_unmatched_entries": sorted(set(unmatched)),
            "sample_seed": int(seed if sample_seed is None else sample_seed),  # the seed the cell samples drew with
        }
        meta = {"source": [str(p) for p in paths], "condition_key": condition_key,
                "control_value": controls, "raw_counts_normalised": raw_counts, "n_hvg": n_hvg,
                "collapse_by_target": collapse_by_target, "dropped_labels": dropped[:50],
                "n_dropped_labels": len(dropped), "knowledge": knowledge_meta}
        if modality:
            meta["modality"] = str(modality)
        meta.update({
            "source_md5": source_md5, "code_commit": code_commit, "code_dirty": code_dirty,
            "gene_name_key": symbol_key, "strict_labels": bool(strict_labels),
            "partial_labels": dict(list(partial.items())[:50]), "n_partial_labels": len(partial),
            "strict_dropped_labels": dict(list(strict_dropped.items())[:50]),
            "n_strict_dropped_labels": len(strict_dropped),
            "min_cells": min_cells, "dropped_min_cells": dropped_min,
            "split_mode": "external" if splits_file else split_mode, "gene_selection": gene_selection,
            "backed": bool(backed),
        })
        # the split seed never enters the manifest, which every run's public copy holds: with the public perturbation
        # list and targets it would rebuild splits.json (make_splits, make_gene_splits), sealed set and categories
        # included. A sample seed is written only when given and other than the split seed; the effective one is in
        # the private record either way
        if sample_seed is not None and int(sample_seed) != int(seed):
            meta["sample_seed"] = int(sample_seed)
        if splits_file:
            meta.update({"split_unmatched_entries": sorted(set(unmatched))[:50],
                         "n_split_unmatched_entries": len(set(unmatched)), "dropped_not_in_split": not_in_split})
        return write_bundle(
            Path(out_dir), name, kept_genes, ctrl_dense[:, keep], pert_means, pert_ncells,
            targets, splits, knowledge=knowledge, eval_cells=eval_cells, extra_meta=meta,
            private_files={"perturbations.json": record},
        )
    finally:
        if backed and getattr(adata, "file", None) is not None:
            adata.file.close()


def external_splits(ext: dict, perts: list[str], label_to_key: dict[str, str] | None = None, seed: int = 0,
                    val_frac_of_train: float = 0.25, canonical_genes: set[str] | None = None,
                    unmatched: list | None = None) -> dict:
    """Map an external split onto our perturbation keys.

    Entries may be our keys or raw labels (mapped through label_to_key); unknown entries and control
    labels are ignored. A perturbation key placed in more than one external set (e.g. two guides for
    one gene split apart) goes to the most held-out set it appears in, so no test perturbation is
    trained on. canonical_genes (the measured genes): an entry matching neither is also read through canonical_key
    (B_A or A+B for the key A+B, GEARS's A+ctrl for A). unmatched: a list that receives every entry, controls
    aside, that maps to no perturbation."""
    label_to_key = label_to_key or {}
    alias = {"train": ("train",), "val1": ("val1", "val", "valid", "validation"), "val2": ("val2", "test")}
    pick = {ours: next((k for k in names if k in ext), None) for ours, names in alias.items()}
    if pick["train"] is None or pick["val2"] is None:
        raise ValueError(f"splits file needs train and val2/test lists, has {sorted(ext)}")
    known = set(perts)

    def keys(entries):
        out = set()
        for e in entries:
            k = e if e in known else label_to_key.get(e)
            if k not in known and canonical_genes is not None:
                k = canonical_key(e, canonical_genes)
            if k in known:
                out.add(k)
            elif unmatched is not None and str(e).lower() not in CONTROL_LABELS:
                unmatched.append(str(e))
        return out

    test = keys(ext[pick["val2"]])
    val = keys(ext[pick["val1"]]) - test if pick["val1"] else set()
    train = keys(ext[pick["train"]]) - test - val
    note = "external"
    if not pick["val1"]:  # CellForge-style train/test: carve our visible validation out of their train set
        rng = np.random.default_rng(seed)
        pool = sorted(train)
        n_val = max(1, int(round(val_frac_of_train * len(pool))))
        val = set(rng.choice(pool, size=n_val, replace=False).tolist())
        train -= val
        note = f"external train/test; val1 = {val_frac_of_train:.0%} of their train (seed {seed})"
    splits = {"train": sorted(train), "val1": sorted(val), "val2": sorted(test), "note": note}
    splits["split_id"] = split_id_for(splits)
    return splits


def describe_h5ad(path: Path) -> dict:
    """Quick summary used to choose files and arguments before ingesting."""
    import anndata as ad
    a = ad.read_h5ad(path, backed="r")
    out = {"file": str(path), "n_cells": a.n_obs, "n_genes": a.n_vars, "obs_columns": list(a.obs.columns)}
    for k in ("perturbation", "condition", "target_gene", "gene"):
        if k in a.obs:
            vc = a.obs[k].astype(str).value_counts()
            out.update(condition_key=k, n_labels=int(len(vc)), top_labels=vc.head(8).to_dict(),
                       median_cells_per_label=float(vc.median()))
            break
    return out
