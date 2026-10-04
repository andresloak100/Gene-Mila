"""On-disk dataset layout shared by every dataset (synthetic or real).

data/<name>/
    manifest.json          dataset metadata, split identifier, file hashes
    splits.json            perturbation ids for train / val1 / val2 (protected)
    public.npz             everything feature code may see: control cells,
                           train pseudobulk labels, perturbation metadata
    knowledge/             optional prior knowledge (gene sets, networks)
    private/val1.npz       visible-validation labels: evaluator only
    private/val2.npz       query-only labels: QueryOracle only

The unit of prediction is a perturbation: given control cells and the
identity of the perturbation, predict the pseudobulk (mean) expression of the
perturbed population. Control and perturbed cells are unpaired.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def split_id_for(splits: dict) -> str:
    payload = json.dumps({k: sorted(splits[k]) for k in ("train", "val1", "val2")}, sort_keys=True)
    return "split_" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def make_splits(perts: list[str], seed: int, frac=(0.6, 0.2, 0.2)) -> dict:
    """Split perturbations (not cells) so validation perturbations are unseen."""
    rng = np.random.default_rng(seed)
    order = list(rng.permutation(sorted(perts)))
    n = len(order)
    n_train = int(round(frac[0] * n))
    n_val1 = int(round(frac[1] * n))
    splits = {
        "train": sorted(order[:n_train]),
        "val1": sorted(order[n_train:n_train + n_val1]),
        "val2": sorted(order[n_train + n_val1:]),
        "seed": seed,
    }
    splits["split_id"] = split_id_for(splits)
    return splits


def write_bundle(
    out_dir: Path,
    name: str,
    genes: list[str],
    control_cells: np.ndarray,
    pert_means: dict[str, np.ndarray],
    pert_ncells: dict[str, int],
    targets: dict[str, list[str]],
    splits: dict,
    knowledge: dict | None = None,
    extra_meta: dict | None = None,
    eval_cells: dict | None = None,
    de_non_dropout: bool = False,
) -> Path:
    """eval_cells (optional): {"control": matrix, "<pert>": matrix of cells} with cells x genes in
    log-normalised space. Cells of validation perturbations (and a control sample) are stored
    privately so held-out predictions can be scored with cell-eval, together with the ground-truth
    DE reference (top DE genes, DE labels and directions) used by the comparable metrics."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "private").mkdir(parents=True)
    (out_dir / "knowledge").mkdir()

    def stack(ids):
        return np.stack([pert_means[p] for p in ids]).astype(np.float32)

    all_perts = sorted(pert_means)
    np.savez_compressed(
        out_dir / "public.npz",
        genes=np.array(genes),
        control_cells=control_cells.astype(np.float32),
        perts=np.array(all_perts),
        train_perts=np.array(splits["train"]),
        train_means=stack(splits["train"]),
        train_ncells=np.array([pert_ncells[p] for p in splits["train"]]),
    )
    for part in ("val1", "val2"):
        np.savez_compressed(
            out_dir / "private" / f"{part}.npz",
            perts=np.array(splits[part]),
            means=stack(splits[part]),
        )
    if eval_cells:
        import scipy.sparse as sp
        for part in ("val1", "val2"):
            perts = [p for p in splits[part] if p in eval_cells]
            blocks = [eval_cells["control"]] + [eval_cells[p] for p in perts]
            labels = ["control"] * eval_cells["control"].shape[0]
            for p in perts:
                labels += [p] * eval_cells[p].shape[0]
            X = sp.vstack([sp.csr_matrix(np.asarray(b, dtype=np.float32)) if not sp.issparse(b)
                           else b.astype(np.float32) for b in blocks]).tocsr()
            sp.save_npz(out_dir / "private" / f"{part}_cells.npz", X)
            np.save(out_dir / "private" / f"{part}_cells_labels.npy", np.array(labels))
            if perts:
                from ..benchmark import reference
                reference.save(reference.build(X, np.array(labels), non_dropout=de_non_dropout),
                               out_dir / "private" / f"{part}_de.npz")
    with open(out_dir / "splits.json", "w") as fh:
        json.dump(splits, fh, indent=1)
    with open(out_dir / "knowledge" / "targets.json", "w") as fh:
        json.dump(targets, fh)
    for fname, content in (knowledge or {}).items():
        with open(out_dir / "knowledge" / fname, "w") as fh:
            json.dump(content, fh)

    files = sorted(p for p in out_dir.rglob("*") if p.is_file())
    manifest = {
        "name": name,
        "n_genes": len(genes),
        "n_control_cells": int(control_cells.shape[0]),
        "n_perturbations": len(all_perts),
        "n_train": len(splits["train"]),
        "n_val1": len(splits["val1"]),
        "n_val2": len(splits["val2"]),
        "split_id": splits["split_id"],
        "knowledge_files": sorted(p.name for p in (out_dir / "knowledge").iterdir()),
        "file_sha256": {str(p.relative_to(out_dir)): sha256_file(p) for p in files},
        **(extra_meta or {}),
    }
    with open(out_dir / "manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=1)
    return out_dir


def verify_bundle(data_dir: Path) -> list[str]:
    """Return a list of problems if any protected dataset file changed."""
    data_dir = Path(data_dir)
    manifest = json.loads((data_dir / "manifest.json").read_text())
    problems = []
    for rel, digest in manifest["file_sha256"].items():
        p = data_dir / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif sha256_file(p) != digest:
            problems.append(f"modified {rel}")
    splits = json.loads((data_dir / "splits.json").read_text())
    if split_id_for(splits) != manifest["split_id"]:
        problems.append("split identifier mismatch")
    return problems


def export_public(data_dir: Path, dest: Path) -> Path:
    """Materialise only the public part of a dataset for experiment subprocesses."""
    data_dir, dest = Path(data_dir), Path(dest)
    (dest / "knowledge").mkdir(parents=True, exist_ok=True)

    def put(src: Path, dst: Path) -> None:  # atomic, and skipped when unchanged, so readers never see a partial file
        if dst.exists() and dst.stat().st_size == src.stat().st_size and sha256_file(dst) == sha256_file(src):
            return
        tmp = dst.with_name(dst.name + ".tmp")
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)

    put(data_dir / "public.npz", dest / "public.npz")
    for f in sorted((data_dir / "knowledge").glob("*")):
        put(f, dest / "knowledge" / f.name)
    manifest = json.loads((data_dir / "manifest.json").read_text())
    public_manifest = {k: v for k, v in manifest.items() if k != "file_sha256"}
    tmp = dest / "manifest.json.tmp"
    tmp.write_text(json.dumps(public_manifest, indent=1))
    os.replace(tmp, dest / "manifest.json")
    return dest


@dataclass
class LabelSet:
    perts: list[str]
    means: np.ndarray  # (n_perts, n_genes)

    @classmethod
    def load(cls, path: Path) -> "LabelSet":
        z = np.load(path, allow_pickle=False)
        return cls([str(p) for p in z["perts"]], z["means"].astype(np.float64))
