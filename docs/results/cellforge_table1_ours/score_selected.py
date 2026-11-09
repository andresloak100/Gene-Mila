#!/usr/bin/env python3
"""CellForge's metrics for a run's already-selected model, scored once on the sealed set, for the runs whose
summary did not store them. The same path as tools/cellforge_bridge.py score --versus: open_run, the run's own
selected record (lab.db best), the run's own bundle and a QueryOracle of the tool's own capped at one query.

    python score_selected.py RUN_DIR OUT.json
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
from genemila.benchmark.oracle import QueryOracle
from genemila.lab import open_run

run, out = Path(sys.argv[1]), Path(sys.argv[2])
if out.exists():
    sys.exit(f"{out} exists; refusing to overwrite")
lab = open_run(run)
rec = lab.db.best()
z = np.load(lab.data_dir / "public.npz")
ctrl = z["control_cells"].astype(np.float64).mean(0)
o = QueryOracle(lab.data_dir, max_queries=1, selection=lab.selection)
pred, perts = lab._predict(rec, o.perts)
res = o.query(f"{run.name}:{rec['experiment_id']}", pred, perts, ctrl)
rep = {"run": str(run), "bundle": str(lab.data_dir), "experiment_id": rec["experiment_id"], "cellforge": res}
out.write_text(json.dumps(rep, indent=1, default=float))
m = res["metrics"]
print(rec["experiment_id"], {k: round(m[k], 4) for k in ("pearson_delta", "cellforge_mse", "cellforge_mse_de", "cellforge_r2_de")})
