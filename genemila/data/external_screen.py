"""Turn an external Perturb-seq screen (h5ad) into a knowledge file for a bundle.

For every perturbation target of the bundle that the external screen also perturbed, the file holds the
external mean response: the mean over that screen's cells of the target minus the mean of the screen's own
non-targeting control cells, over the bundle's genes, in the expression space the bundle uses (counts per
10,000 per cell, log1p, then the mean over cells; genemila.data.real._normalise_log1p does the same to the
bundle). Features can then transfer a response measured in another screen of the same cell line, for example
Replogle 2022 K562 for the Adamson 2016 K562 bundle.

The screen is an outside measurement the agents may read, so the result goes to knowledge/<name>.json in the
bundle directory next to targets.json and the curated knowledge. Nothing else is written or copied: the
manifest's file hashes cover the files it lists, so the integrity check still passes, and the lab's
export_public copies every file in knowledge/ into a run's public directory when the run starts, so the new
file reaches the agents on the next run without any further step.

Inputs are the raw external h5ad and the bundle's public gene list (public.npz) and target list
(knowledge/targets.json) only. X is never loaded whole: it is read with h5py in chunks of at most chunk cells
(CSR, dense) or chunk genes (CSC) holding at most chunk_nnz stored values, whichever limit comes first, so the
memory of a chunk is bounded in every layout.

  CSR   one sweep over row chunks: a chunk's cell totals are known before it is normalised, so the per-label
        sums of log1p(1e4 x / total) over the bundle's columns are accumulated in the same sweep.
  CSC   pass 1 over column chunks accumulates cell totals; pass 2 reads only the bundle's columns (contiguous
        runs of needed columns in one read), scales each stored value by its cell's factor and sums by label.
  dense row chunks, as CSR.

Zero entries contribute log1p(0) = 0, so sparse sums are exact. Labels kept are the control labels and every
label naming exactly one gene that is a bundle target (tokens split on + _ | , ; and space, matched without
regard to case; a label equal to a target gene also matches). Labels naming two or more genes are
combinatorial perturbations and are skipped. A label whose other tokens are neither genes of the screen nor a
recognised guide suffix (guide1, sg2, g1, p1p2, a number, ctrl, kd, ko, tss) may name a second gene the screen
perturbed but did not measure, so it is reported as ambiguous and skipped rather than pooled. Several external
labels for one target gene are pooled by cell count. Raw counts are detected as real.py does (integer values
with a maximum above 20) from windows spread over the stored values plus the start of the most populated
columns (CSC: the highest-expressed genes) or rows (CSR: the deepest cells), because in a large CSC file every
spread window sits inside one column and would inspect only a handful of genes. Anything else is refused
unless already_normalised is set, in which case the stored values are averaged as they are.

Rows are per target gene, so a bundle perturbation of several genes (a Norman pair, CEBPE+KLF1) reads the rows of
all its targets: consumers sum them, and a pair has an external row only when every target has one. The file is
built over every gene named by any bundle perturbation (bundle_targets), so a pair's genes are all looked up.

modality, when given (build(modality=...), tools/build_external_screen.py --modality), names the screen's
modality (CRISPRi for Replogle 2022) and the file then records it in source.modality, the bundle manifest's own
modality in source.bundle_modality, and a top-level sign: -1 when both modalities are known and differ (a CRISPRi
screen read for a CRISPRa bundle, whose same-target response is expected to point the other way), +1 when they
agree or either is unknown. Consumers multiply a target's own delta by sign before using it as that target's
predicted change; similarities between rows do not depend on it. The description then starts with the screen's
modality and the sign. Without modality the file is written exactly as before (no sign key, absent meaning +1). The
planner and workers see the whole description and the file's keys (lab.knowledge_summary; until 11 Oct 2026 only the
first 60 characters of the description).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

from .real import CONTROL_LABELS

LABEL_COLUMNS = ("perturbation", "condition", "target_gene", "gene", "guide_ids")
GENE_COLUMNS = ("gene_name", "gene_symbol", "gene_symbols", "symbol", "feature_name", "features")
DEFAULT_CHUNK_ROWS = 20_000        # cells per chunk (CSR and dense)
DEFAULT_CHUNK_COLS = 500           # genes per chunk (CSC)
DEFAULT_CHUNK_NNZ = 50_000_000     # stored values per chunk in every layout; bounds memory when columns or rows are dense
TARGET_SUM = 1e4
DECIMALS = 5
_SPLIT = re.compile(r"[+_|,;\s]+")
# tokens of a perturbation label that name a guide, not a gene (ATF6_guide1, sgATF6, XBP1_1, HSPA5+ctrl, p1p2)
_SUFFIX = re.compile(r"^[(\[]?(guide\d*|sg\w*|g\d+|p\d+(p\d+)*|\d+|ctrl|kd|ko|tss\d*|crispri|crispra|crispr)[)\]]?$", re.I)


def _log(msg: str) -> None:
    print(f"[external_screen] {msg}", file=sys.stderr, flush=True)


def _as_str(values) -> list[str]:
    out = []
    for v in np.asarray(values).ravel().tolist():
        out.append(v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v))
    return out


# ---- reading the h5ad pieces (obs, var, X layout) ------------------------------------------------------------

def _read_strings(node) -> list[str]:
    """A string array of an h5ad file as str: a plain HDF5 dataset (older anndata), or an encoded group such as
    the "nullable-string-array" that anndata 0.13 writes for string indexes and categories (values plus a mask;
    a masked entry reads as ''). anndata's own reader is used for an encoded group, with a direct read of its
    values as the fallback for an anndata that predates the encoding."""
    import h5py
    if isinstance(node, h5py.Dataset):
        return _as_str(node[...])
    try:
        from anndata.io import read_elem
        values = read_elem(node)
        if hasattr(values, "to_numpy"):
            values = values.to_numpy(dtype=object, na_value="")
        values = ["" if v is None or (isinstance(v, float) and np.isnan(v)) else v
                  for v in np.asarray(values, dtype=object).ravel().tolist()]
        return _as_str(np.array(values, dtype=object))
    except Exception:
        if "values" not in node:
            raise
        out = _as_str(node["values"][...])
        if "mask" in node:
            out = ["" if m else v for v, m in zip(out, np.asarray(node["mask"][...], dtype=bool).tolist())]
        return out


def read_label_codes(f, label_col: str | None = None) -> tuple[str, list[str], np.ndarray]:
    """The perturbation column of obs as (column name, categories, code per cell); code -1 marks a missing
    value. Categorical columns are read as their codes and categories, so a file of millions of cells costs a
    few megabytes; other columns are read whole and factorised."""
    import h5py
    obs = f["obs"]
    if label_col is None:
        label_col = next((k for k in LABEL_COLUMNS if k in obs), None)
        if label_col is None:
            raise ValueError(f"cannot find the perturbation column in obs: {sorted(obs.keys())}")
    if label_col not in obs:
        raise ValueError(f"obs has no column {label_col!r}: {sorted(obs.keys())}")
    elem = obs[label_col]
    if isinstance(elem, h5py.Group) and elem.attrs.get("encoding-type") == "categorical":
        cats = _read_strings(elem["categories"])
        codes = np.asarray(elem["codes"][...], dtype=np.int64)
    else:
        from anndata.io import read_elem
        values = read_elem(elem)
        if hasattr(values, "categories") and hasattr(values, "codes"):
            cats, codes = _as_str(values.categories), np.asarray(values.codes, dtype=np.int64)
        else:
            raw = np.asarray(values)
            missing = np.array([v is None or (isinstance(v, float) and np.isnan(v)) for v in raw.tolist()])
            text = np.array(_as_str(raw), dtype=object)
            cats_arr, inv = np.unique(text[~missing], return_inverse=True)
            cats = cats_arr.tolist()
            codes = np.full(raw.shape[0], -1, dtype=np.int64)
            codes[~missing] = inv
    return label_col, cats, codes


def read_gene_symbols(f, gene_col: str | None = None) -> tuple[str, list[str]]:
    """Gene symbols of var: the index, unless it holds Ensembl ids and a symbol column exists (or gene_col
    names a column). Returns (column used, symbols)."""
    from anndata.io import read_elem
    var = f["var"]
    index_name = var.attrs.get("_index", "_index")
    if isinstance(index_name, bytes):
        index_name = index_name.decode()
    if gene_col is None:
        idx = _read_strings(var[index_name])
        head = idx[:1000]
        if head and sum(1 for g in head if g.startswith("ENS")) > 0.5 * len(head):
            gene_col = next((c for c in GENE_COLUMNS if c in var), None)
            if gene_col is None:
                _log("var index looks like Ensembl ids and no symbol column was found; using the index")
        if gene_col is None:
            return index_name, idx
    if gene_col not in var:
        raise ValueError(f"var has no column {gene_col!r}: {sorted(var.keys())}")
    return gene_col, _as_str(np.asarray(read_elem(var[gene_col])))


def x_layout(f) -> tuple[str, tuple[int, int]]:
    """('csr' | 'csc' | 'dense', (n_cells, n_genes)) from the X group or dataset attributes."""
    import h5py
    X = f["X"]
    if isinstance(X, h5py.Group):
        enc = X.attrs.get("encoding-type", X.attrs.get("h5sparse_format", ""))
        enc = enc.decode() if isinstance(enc, bytes) else str(enc)
        shape = X.attrs.get("shape", X.attrs.get("h5sparse_shape"))
        if shape is None:
            raise ValueError("sparse X without a shape attribute")
        if enc.startswith("csr"):
            return "csr", (int(shape[0]), int(shape[1]))
        if enc.startswith("csc"):
            return "csc", (int(shape[0]), int(shape[1]))
        raise ValueError(f"unsupported X encoding {enc!r}")
    return "dense", (int(X.shape[0]), int(X.shape[1]))


def _sample_values(f, layout: str, n_windows: int = 20, window: int = 5000, n_top: int = 5) -> np.ndarray:
    """Stored values from windows spread over the matrix plus, for sparse X, the first window of the n_top most
    populated columns (CSC) or rows (CSR). The spread windows alone are not enough: the first entries of a CSC
    file belong to a few low-count genes, as real.py notes, and in a file of millions of cells every window of
    5,000 contiguous values sits inside one column, so 20 windows inspect 20 genes drawn with probability
    proportional to their stored values, and a raw-count file whose sampled genes all stay below 21 counts is
    refused. The most populated columns are the highest-expressed genes (the deepest cells in CSR), whose counts
    reach far above 20 whenever X holds raw counts."""
    X = f["X"]
    if layout == "dense":
        n = X.shape[0]
        starts = np.unique(np.linspace(0, max(n - 1, 0), n_windows).astype(int))
        parts = [np.asarray(X[s:min(s + max(1, window // max(1, X.shape[1])), n), :]).ravel() for s in starts]
    else:
        data = X["data"]
        n = data.shape[0]
        starts = np.unique(np.linspace(0, max(n - 1, 0), n_windows).astype(int))
        parts = [np.asarray(data[s:min(s + window, n)]) for s in starts]
        if n_top > 0:
            indptr = np.asarray(X["indptr"][...], dtype=np.int64)
            top = np.argsort(np.diff(indptr), kind="stable")[-n_top:]
            parts += [np.asarray(data[int(indptr[j]):min(int(indptr[j]) + window, n)]) for j in top]
    values = np.concatenate(parts).astype(np.float64) if parts else np.zeros(0)
    return values[values != 0]


def integer_valued(values: np.ndarray) -> bool:
    return values.size > 0 and bool(np.allclose(values, np.round(values)))


def looks_like_counts(values: np.ndarray) -> bool:
    return integer_valued(values) and float(values.max()) > 20


# ---- label matching ------------------------------------------------------------------------------------------

def match_labels(categories: list[str], bundle_targets: list[str], external_genes: list[str],
                 control: list[str] | None = None, aliases: dict[str, str] | None = None) -> dict:
    """What each external label is: a control label, one bundle target gene, a combinatorial perturbation
    (skipped), a bundle target plus a token that is neither a gene of the screen nor a guide suffix (ambiguous:
    it may name a gene the screen perturbed but did not measure, so it is skipped rather than pooled) or
    something else (skipped). control, when given, replaces the automatic detection of the non-targeting labels
    (real.CONTROL_LABELS, matched without regard to case). aliases maps a bundle symbol to the symbol the screen
    uses for the same gene (a renamed gene: SLMO2 is PRELID3B in newer annotations); a label naming the alias
    counts for the bundle target."""
    lower_target = {t.lower(): t for t in bundle_targets}
    for t, a in check_aliases(aliases, bundle_targets).items():
        if t in bundle_targets:
            lower_target.setdefault(a.lower(), t)
    gene_like = {g.lower() for g in external_genes} | set(lower_target)
    if control:
        missing = [c for c in control if c not in set(categories)]
        if missing:
            raise ValueError(f"control label(s) {missing} not found among the perturbation labels")
        ctrl = list(control)
    else:
        ctrl = [c for c in categories if c.lower() in CONTROL_LABELS]
    if not ctrl:
        raise ValueError(f"cannot identify the control label among {sorted(categories)[:20]}; pass --control")
    ctrl_set = set(ctrl)
    by_target: dict[str, list[str]] = {}
    via_alias: set[str] = set()  # targets matched through a label naming their alias
    multi, ambiguous, other = [], [], []
    for label in categories:
        if label in ctrl_set:
            continue
        low = label.lower()
        if low in lower_target:
            by_target.setdefault(lower_target[low], []).append(label)
            if low != lower_target[low].lower():
                via_alias.add(lower_target[low])
            continue
        genes, unknown = [], []
        for tok in _SPLIT.split(label):
            t = tok.lower()
            if not t:
                continue
            if t in gene_like:
                if t not in genes:
                    genes.append(t)
            elif not _SUFFIX.match(tok):
                unknown.append(tok)
        if len(genes) == 1 and genes[0] in lower_target and not unknown:
            by_target.setdefault(lower_target[genes[0]], []).append(label)
            if genes[0] != lower_target[genes[0]].lower():
                via_alias.add(lower_target[genes[0]])
        elif len(genes) == 1 and genes[0] in lower_target:
            ambiguous.append(label)
        elif len(genes) > 1:
            multi.append(label)
        else:
            other.append(label)
    found = sorted(by_target)
    return {"control": ctrl, "by_target": {t: by_target[t] for t in found},
            "missing": sorted(t for t in bundle_targets if t not in by_target),
            "multi_gene": sorted(multi), "ambiguous": sorted(ambiguous), "n_other": len(other),
            "via_alias": sorted(via_alias)}


def check_aliases(aliases: dict[str, str] | None, bundle_names: list[str]) -> dict[str, str]:
    """The alias table, refused when an alias is itself another bundle name (two bundle genes would then claim
    one external gene) or names a gene twice."""
    aliases = dict(aliases or {})
    names = set(bundle_names)
    clash = sorted(f"{k}={v}" for k, v in aliases.items() if v in names and v != k)
    if clash:
        raise ValueError(f"alias(es) {clash} name another gene of the bundle; two bundle genes would share one "
                         "external gene")
    seen: dict[str, str] = {}
    for k, v in aliases.items():
        if v.lower() in seen and seen[v.lower()] != k:
            raise ValueError(f"aliases {seen[v.lower()]}={v} and {k}={v} name the same external gene")
        seen[v.lower()] = k
    return aliases


def parse_aliases(pairs: list[str] | None = None, path: str | Path | None = None) -> dict[str, str]:
    """OLD=NEW pairs (bundle symbol = symbol in the screen) and/or a JSON object file {"OLD": "NEW"}."""
    out: dict[str, str] = {}
    if path:
        data = json.loads(Path(path).read_text())
        if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
            raise ValueError(f"{path}: an alias file is a JSON object of bundle symbol -> screen symbol")
        out.update({k.strip(): v.strip() for k, v in data.items()})
    for pair in pairs or []:
        old, sep, new = pair.partition("=")
        if not sep or not old.strip() or not new.strip():
            raise ValueError(f"alias {pair!r} is not OLD=NEW")
        out[old.strip()] = new.strip()
    return out


def map_genes(bundle_genes: list[str], external_genes: list[str], aliases: dict[str, str] | None = None) -> np.ndarray:
    """Column of each bundle gene in the external screen (-1 when unmeasured): exact symbol match first, then the
    alias's exact match, then either without regard to case; a symbol listed twice in the screen maps to its
    first column."""
    aliases = check_aliases(aliases, bundle_genes)
    exact: dict[str, int] = {}
    lower: dict[str, int] = {}
    for j, g in enumerate(external_genes):
        exact.setdefault(g, j)
        lower.setdefault(g.lower(), j)
    out = np.full(len(bundle_genes), -1, dtype=np.int64)
    for i, g in enumerate(bundle_genes):
        a = aliases.get(g)
        j = exact.get(g, -1)
        if j < 0 and a:
            j = exact.get(a, -1)
        if j < 0:
            j = lower.get(g.lower(), -1)
        if j < 0 and a:
            j = lower.get(a.lower(), -1)
        out[i] = j
    return out


# ---- streaming sums ------------------------------------------------------------------------------------------

def _column_chunks(indptr: np.ndarray, cols: np.ndarray, max_cols: int, max_nnz: int):
    """Split a sorted list of columns into batches of at most max_cols columns holding at most max_nnz stored
    values (a batch always holds at least one column)."""
    start, nnz = 0, 0
    for k, j in enumerate(cols):
        size = int(indptr[j + 1] - indptr[j])
        if k > start and (k - start >= max_cols or nnz + size > max_nnz):
            yield cols[start:k]
            start, nnz = k, 0
        nnz += size
    if start < len(cols):
        yield cols[start:]


def _row_chunks(n_cells: int, chunk: int, chunk_nnz: int, indptr: np.ndarray | None = None,
                n_genes: int | None = None):
    """Row ranges (r0, r1) of at most chunk rows holding at most chunk_nnz stored values (CSR, from indptr) or
    at most chunk_nnz dense entries (n_genes per row); a range always holds at least one row."""
    r0 = 0
    while r0 < n_cells:
        r1 = min(r0 + chunk, n_cells)
        if indptr is not None:
            r1 = min(r1, int(np.searchsorted(indptr, indptr[r0] + chunk_nnz, side="right")) - 1)
        elif n_genes:
            r1 = min(r1, r0 + chunk_nnz // max(1, n_genes))
        r1 = max(r0 + 1, r1)
        yield r0, r1
        r0 = r1


def _runs(cols: np.ndarray):
    """Maximal runs of consecutive column indices as (first, last + 1, position of first in cols)."""
    start = 0
    for k in range(1, len(cols) + 1):
        if k == len(cols) or cols[k] != cols[k - 1] + 1:
            yield int(cols[start]), int(cols[k - 1]) + 1, start
            start = k


def _scale(totals: np.ndarray) -> np.ndarray:
    return TARGET_SUM / np.where(totals > 0, totals, 1.0)


def stream_sums(f, layout: str, shape: tuple[int, int], needed_cols: np.ndarray, cell_code: np.ndarray,
                n_groups: int, normalise: bool = True, chunk: int | None = None,
                chunk_nnz: int = DEFAULT_CHUNK_NNZ) -> np.ndarray:
    """Sum over the cells of each group (cell_code; -1 = not used) of the normalised expression of the needed
    columns. Returns (n_groups, len(needed_cols)) float64. A chunk holds at most chunk cells (CSR, dense) or
    chunk genes (CSC) and at most chunk_nnz stored values in every layout, so memory is bounded by the smaller
    of the two limits times a few words per value, plus n_groups x len(needed_cols)."""
    n_cells, n_genes = shape
    n_needed = len(needed_cols)
    sums = np.zeros((n_groups, n_needed), dtype=np.float64)
    X = f["X"]
    t0 = time.time()

    if layout in ("csr", "dense"):
        chunk = chunk or DEFAULT_CHUNK_ROWS
        col_map = np.full(n_genes, -1, dtype=np.int64)
        col_map[needed_cols] = np.arange(n_needed)
        indptr = None
        if layout == "csr":
            data, indices, indptr = X["data"], X["indices"], np.asarray(X["indptr"][...], dtype=np.int64)
        for r0, r1 in _row_chunks(n_cells, chunk, chunk_nnz, indptr=indptr, n_genes=n_genes):
            codes = cell_code[r0:r1]
            if layout == "csr":
                s, e = int(indptr[r0]), int(indptr[r1])
                d = np.asarray(data[s:e], dtype=np.float64)
                k = col_map[np.asarray(indices[s:e], dtype=np.int64)]
                rows = np.repeat(np.arange(r1 - r0), np.diff(indptr[r0:r1 + 1]))
                row_code = codes[rows]
                keep = (k >= 0) & (row_code >= 0)
                if normalise:
                    scale = _scale(np.bincount(rows, weights=d, minlength=r1 - r0))
                    vals = np.log1p(d[keep] * scale[rows[keep]])
                else:
                    vals = d[keep]
                flat = row_code[keep] * n_needed + k[keep]
                sums += np.bincount(flat, weights=vals, minlength=n_groups * n_needed).reshape(n_groups, n_needed)
            else:
                block = np.asarray(X[r0:r1, :])
                keep = codes >= 0
                sub = np.asarray(block[:, needed_cols], dtype=np.float64)[keep]
                if normalise:
                    scale = _scale(block.sum(axis=1, dtype=np.float64))[keep]
                    sub = np.log1p(sub * scale[:, None])
                import scipy.sparse as sp
                kc = codes[keep]
                ind = sp.csr_matrix((np.ones(kc.size), (kc, np.arange(kc.size))), shape=(n_groups, kc.size))
                sums += np.asarray(ind @ sub)
            _log(f"{layout}: cells {r1:,} / {n_cells:,} ({time.time() - t0:.0f} s)")
        return sums

    # CSC: pass 1 totals over all genes, pass 2 the needed columns only
    chunk = chunk or DEFAULT_CHUNK_COLS
    data, indices, indptr = X["data"], X["indices"], np.asarray(X["indptr"][...], dtype=np.int64)
    scale = None
    if normalise:
        totals = np.zeros(n_cells, dtype=np.float64)
        done = 0
        for cols in _column_chunks(indptr, np.arange(n_genes), chunk, chunk_nnz):
            s, e = int(indptr[cols[0]]), int(indptr[cols[-1] + 1])
            totals += np.bincount(np.asarray(indices[s:e], dtype=np.int64), weights=np.asarray(data[s:e], dtype=np.float64),
                                  minlength=n_cells)
            done += len(cols)
            _log(f"csc pass 1 (cell totals): genes {done:,} / {n_genes:,} ({time.time() - t0:.0f} s)")
        scale = _scale(totals)
    order = np.argsort(needed_cols, kind="stable")
    sorted_cols = needed_cols[order]
    done = 0
    for cols in _column_chunks(indptr, sorted_cols, chunk, chunk_nnz):
        for j0, j1, pos in _runs(cols):
            s, e = int(indptr[j0]), int(indptr[j1])
            d = np.asarray(data[s:e], dtype=np.float64)
            rows = np.asarray(indices[s:e], dtype=np.int64)
            local = np.repeat(np.arange(j1 - j0), np.diff(indptr[j0:j1 + 1]))
            codes = cell_code[rows]
            keep = codes >= 0
            vals = np.log1p(d[keep] * scale[rows[keep]]) if normalise else d[keep]
            flat = codes[keep] * (j1 - j0) + local[keep]
            part = np.bincount(flat, weights=vals, minlength=n_groups * (j1 - j0)).reshape(n_groups, j1 - j0)
            sums[:, order[done + pos:done + pos + (j1 - j0)]] += part
        done += len(cols)
        _log(f"csc pass 2 (bundle genes): columns {done:,} / {n_needed:,} ({time.time() - t0:.0f} s)")
    return sums


# ---- the knowledge file --------------------------------------------------------------------------------------

def md5_file(path: Path, block: int = 1 << 23) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for part in iter(lambda: fh.read(block), b""):
            h.update(part)
    return h.hexdigest()


def bundle_targets(bundle_dir: Path) -> list[str]:
    targets = json.loads((Path(bundle_dir) / "knowledge" / "targets.json").read_text())
    return sorted({g for gs in targets.values() for g in gs})


def bundle_genes(bundle_dir: Path) -> list[str]:
    z = np.load(Path(bundle_dir) / "public.npz", allow_pickle=False)
    return [str(g) for g in z["genes"]]


def bundle_modality(bundle_dir: Path) -> str | None:
    """The modality the bundle's manifest records (prepare_data.py --modality), None for a bundle that records
    none (every bundle built before the field existed, Adamson's included) or has no manifest."""
    path = Path(bundle_dir) / "manifest.json"
    if not path.exists():
        return None
    value = json.loads(path.read_text()).get("modality")
    if value is None:
        return None
    return str(value).strip() or None


def modality_sign(screen_modality: str | None, bundle_modality_: str | None) -> int:
    """-1 when the screen's and the bundle's modalities are both known and differ (compared without regard to case
    or surrounding space: a CRISPRi screen for a CRISPRa bundle), else +1 (the same modality, or either unknown)."""
    a, b = (str(m).strip().lower() if m is not None else "" for m in (screen_modality, bundle_modality_))
    return -1 if a and b and a != b else 1


def _description(space: str, file_name: str, modality: str | None, bundle_mod: str | None, sign: int) -> str:
    """The knowledge file's description. Without a modality it is the sentence every earlier file carries; with one it
    leads with the screen's modality and the sign and says what the sign is for. The planner and workers read it
    whole (lab.knowledge_summary)."""
    body = (f"perts[gene].delta = {space} of that screen's cells of the perturbation minus its own control mean, over "
            "this bundle's genes in bundle order (null where unmeasured there)")
    if not modality:
        return f"External screen deltas: {body}; source: Perturb-seq screen {file_name}."
    where = f"this bundle is {bundle_mod}" if bundle_mod else "bundle modality not recorded"
    if sign < 0:
        why = (f"The screen's modality ({modality}) differs from this bundle's ({bundle_mod}), so a target's response "
               "here is expected to point the other way: multiply a target's delta by sign (-1) before using it as "
               "that target's predicted change")
    elif bundle_mod:
        why = f"The screen and this bundle share a modality ({modality}), so sign is +1"
    else:
        why = "The bundle records no modality, so sign is +1"
    return (f"{modality} screen deltas, sign {sign:+d} ({where}): {body}; source: {modality} Perturb-seq screen "
            f"{file_name}. {why}; correlations between rows do not depend on the sign. A perturbation of several "
            "genes has a row only when every target has one: the sum of its targets' deltas.")


def inspect(h5ad: Path, bundle_dir: Path, label_col: str | None = None, gene_col: str | None = None,
            control: list[str] | None = None, aliases: dict[str, str] | None = None) -> dict:
    """Pass 0: obs, var and the X layout only (no X reads). The label matching the build will use."""
    import h5py
    h5ad, bundle_dir = Path(h5ad), Path(bundle_dir)
    genes, targets = bundle_genes(bundle_dir), bundle_targets(bundle_dir)
    with h5py.File(h5ad, "r") as f:
        layout, shape = x_layout(f)
        label_col, cats, codes = read_label_codes(f, label_col)
        gene_col, symbols = read_gene_symbols(f, gene_col)
    if len(symbols) != shape[1] or codes.shape[0] != shape[0]:
        raise ValueError(f"X is {shape} but var has {len(symbols)} genes and obs {codes.shape[0]} cells")
    match = match_labels(cats, targets, symbols, control, aliases)
    cols = map_genes(genes, symbols, aliases)
    cat_index = {c: i for i, c in enumerate(cats)}
    n_per_cat = np.bincount(codes[codes >= 0], minlength=len(cats))
    n_ctrl = int(sum(n_per_cat[cat_index[c]] for c in match["control"]))
    n_by_target = {t: int(sum(n_per_cat[cat_index[c]] for c in labs)) for t, labs in match["by_target"].items()}
    return {"h5ad": h5ad, "layout": layout, "shape": shape, "label_col": label_col, "gene_col": gene_col,
            "categories": cats, "codes": codes, "symbols": symbols, "match": match, "genes": genes,
            "targets": targets, "cols": cols, "n_control_cells": n_ctrl, "n_cells_by_target": n_by_target,
            "n_measured": int((cols >= 0).sum()), "aliases": dict(aliases or {}),
            "aliases_matched": {"targets": match["via_alias"],
                                "genes": sorted(g for g, j in zip(genes, cols) if j >= 0 and (aliases or {}).get(g)
                                                and symbols[j].lower() != g.lower())}}


def build(h5ad: Path, bundle_dir: Path, name: str, label_col: str | None = None, gene_col: str | None = None,
          control: list[str] | None = None, chunk: int | None = None, chunk_nnz: int = DEFAULT_CHUNK_NNZ,
          already_normalised: bool = False, force: bool = False, with_md5: bool = True,
          aliases: dict[str, str] | None = None, min_cells: int = 0, modality: str | None = None) -> Path:
    """Build knowledge/<name>.json in the bundle directory and return its path. aliases: see match_labels and
    map_genes. A target with fewer than min_cells cells in the screen gets no row (its mean is mostly noise) and
    is listed in bundle_targets_missing and bundle_targets_below_min_cells. modality: the screen's modality; when
    given, the file records it with the bundle's and a top-level sign (see the module docstring), and the
    description leads with it. None writes the file exactly as before."""
    import h5py
    h5ad, bundle_dir = Path(h5ad), Path(bundle_dir)
    out = bundle_dir / "knowledge" / f"{name}.json"
    if out.exists() and not force:
        raise FileExistsError(f"{out} exists; pass force=True (--force) to overwrite it")
    modality = (str(modality).strip() or None) if modality is not None else None
    bundle_mod = bundle_modality(bundle_dir) if modality else None
    sign = modality_sign(modality, bundle_mod)
    if modality:
        _log(f"screen modality {modality}, bundle modality {bundle_mod or 'not recorded'}: sign {sign:+d}")
    t0 = time.time()
    info = inspect(h5ad, bundle_dir, label_col, gene_col, control, aliases)
    match, cats, codes, cols = info["match"], info["categories"], info["codes"], info["cols"]
    if not match["by_target"]:
        raise ValueError("no external label matches a bundle target gene")
    if info["n_measured"] == 0:
        raise ValueError("none of the bundle's genes is measured in the external screen")
    if info["n_control_cells"] == 0:
        raise ValueError(f"no cells carry the control label(s) {match['control']}")

    # group 0 = control, then the found targets in sorted order
    found = sorted(match["by_target"])
    group_of_cat = np.full(len(cats), -1, dtype=np.int64)
    cat_index = {c: i for i, c in enumerate(cats)}
    for c in match["control"]:
        group_of_cat[cat_index[c]] = 0
    for g, t in enumerate(found, start=1):
        for c in match["by_target"][t]:
            group_of_cat[cat_index[c]] = g
    cell_code = np.where(codes >= 0, group_of_cat[np.clip(codes, 0, None)], -1)
    n_groups = len(found) + 1
    counts = np.bincount(cell_code[cell_code >= 0], minlength=n_groups)

    measured = cols >= 0
    needed_cols = cols[measured]
    if len(np.unique(needed_cols)) != len(needed_cols):  # two bundle genes on one external column (case-only match)
        dup = sorted({info["genes"][i] for i in np.flatnonzero(measured)
                      if np.sum(needed_cols == cols[i]) > 1})
        raise ValueError(f"bundle genes {dup[:6]} map to the same external gene column; fix the gene symbols first")
    with h5py.File(h5ad, "r") as f:
        sampled = _sample_values(f, info["layout"])
        raw = looks_like_counts(sampled)
        if not raw and not already_normalised:
            vmax = float(sampled.max()) if sampled.size else 0.0
            if integer_valued(sampled):
                raise ValueError(
                    f"X does not look like raw counts: the {sampled.size:,} sampled non-zero values are integers but "
                    f"their maximum is {vmax:g}, and raw UMI counts reach well above 20 in the most expressed genes. "
                    "Check the file (subsampled, capped or binarised counts?) before using it; --already-normalised "
                    "would average these values without normalising them, which is not the bundle's space")
            raise ValueError(
                f"X does not look like raw counts: the sampled values are not integers (maximum {vmax:g}); if X holds "
                "already normalised expression, pass --already-normalised to average the stored values as they are")
        normalise = not already_normalised
        _log(f"{info['layout']} X of {info['shape'][0]:,} cells x {info['shape'][1]:,} genes; "
             f"{'normalising counts per 10k, log1p' if normalise else 'using the stored values as they are'}; "
             f"{len(needed_cols):,} of {len(info['genes']):,} bundle genes measured; "
             f"{len(found)} of {len(info['targets'])} bundle targets found; {int(counts[0]):,} control cells")
        sums = stream_sums(f, info["layout"], info["shape"], needed_cols, cell_code, n_groups,
                           normalise=normalise, chunk=chunk, chunk_nnz=chunk_nnz)
    means = sums / np.maximum(counts, 1)[:, None]

    def per_gene(values: np.ndarray) -> list:
        full = np.full(len(info["genes"]), np.nan)
        full[measured] = values
        return [None if not np.isfinite(v) else round(float(v), DECIMALS) for v in full]

    space = ("mean over cells of log1p(10,000 x counts / cell total)" if normalise else
             "mean over cells of the stored (already normalised) values")
    # the planner and workers read this sentence whole with the file's keys (lab.knowledge_summary); it leads with
    # the content
    knowledge = {
        "description": _description(space, h5ad.name, modality, bundle_mod, sign),
        "source": {
            "file": h5ad.name, "size_bytes": h5ad.stat().st_size, "md5": md5_file(h5ad) if with_md5 else None,
            "n_cells": info["shape"][0], "n_genes": info["shape"][1], "encoding": info["layout"],
            "label_col": info["label_col"], "gene_col": info["gene_col"], "control_labels": match["control"],
            "raw_counts": bool(raw), "normalisation": space, "n_labels": len(cats),
            "n_labels_multi_gene_skipped": len(match["multi_gene"]),
            "n_labels_ambiguous_skipped": len(match["ambiguous"]), "labels_ambiguous_skipped": match["ambiguous"],
            "n_labels_other": match["n_other"], "aliases": info["aliases"],
            "aliases_matched": info["aliases_matched"], "min_cells": int(min_cells),
            "n_cells_used": int(counts.sum()), "date": dt.date.today().isoformat(),
            "seconds": round(time.time() - t0, 1),
        },
        "genes": info["genes"],
        "measured": [bool(m) for m in measured],
        "control": {"n_cells": int(counts[0]), "mean": per_gene(means[0])},
        "perts": {t: {"n_cells": int(counts[g]), "labels": match["by_target"][t],
                      "delta": per_gene(means[g] - means[0])} for g, t in enumerate(found, start=1)
                  if counts[g] > 0 and counts[g] >= min_cells},
        # a label category with no cells (left behind when an h5ad was subset) is no measurement: listed as missing;
        # so is a target with fewer than min_cells cells
        "bundle_targets_missing": sorted(set(match["missing"]) | {t for g, t in enumerate(found, start=1)
                                                                   if counts[g] == 0 or counts[g] < min_cells}),
        "bundle_targets_below_min_cells": {t: int(counts[g]) for g, t in enumerate(found, start=1)
                                           if 0 < counts[g] < min_cells},
    }
    if modality:
        # only with a modality: a file built without one keeps the keys it always had. sign follows the description,
        # the first key, both of which the planner reads (lab.knowledge_summary).
        knowledge = {"description": knowledge.pop("description"), "sign": int(sign), **knowledge}
        knowledge["source"].update(modality=modality, bundle_modality=bundle_mod)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(knowledge, separators=(",", ":"), allow_nan=False))
    tmp.replace(out)
    _log(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB) in {time.time() - t0:.0f} s")
    return out
