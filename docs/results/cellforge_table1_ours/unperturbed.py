#!/usr/bin/env python3
"""The Unperturbed row of CellForge's Table 1 on our split: predict every held-out perturbation as the mean of the
export's control cells. Reads only a cellforge_bridge.py export (control and training cells, held-out list).

    python unperturbed.py --export ~/cellforge_norman_export --out ~/unperturbed_norman
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--export", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
import anndata as ad
import scipy.sparse as sp
export, out = Path(a.export), Path(a.out)
if out.exists() and any(out.iterdir()):
    sys.exit(f"{out} exists and is not empty; refusing to overwrite")
out.mkdir(parents=True, exist_ok=True)
x = ad.read_h5ad(export / "cellforge_input.h5ad")
held = json.loads((export / "heldout_perturbations.json").read_text())
ctrl = (x.obs["perturbation"].astype(str) == "control").to_numpy()
X = x.X[ctrl]
mean = np.asarray(X.mean(0)).ravel().astype(np.float64)
np.savez(out / "predictions.npz", perts=np.array(held, dtype=str), means=np.tile(mean, (len(held), 1)),
         genes=np.array(x.var_names.astype(str).tolist(), dtype=str))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
r = {"model": "Unperturbed (mean of the export's control cells)", "control_cells": int(ctrl.sum()),
     "heldout": len(held), "export_input_sha256": sha(export / "cellforge_input.h5ad"),
     "predictions_sha256": sha(out / "predictions.npz")}
(out / "receipt.json").write_text(json.dumps(r, indent=1))
print(json.dumps(r, indent=1))
