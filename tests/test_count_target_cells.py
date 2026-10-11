import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def test_counts_group_labels_like_the_ingestion(tmp_path):
    import anndata as ad
    import pandas as pd
    labels = ["ctrl"] * 7 + ["AAA_1"] * 3 + ["AAA_2"] * 2 + ["BBB"] * 4 + ["ZZZ_not_a_gene"] * 5
    obs = pd.DataFrame({"perturbation": labels}, index=[f"c{i}" for i in range(len(labels))])
    var = pd.DataFrame({"gene_name": ["AAA", "BBB", "CCC"]}, index=["g1", "g2", "g3"])
    ad.AnnData(np.zeros((len(labels), 3), dtype=np.float32), obs=obs, var=var).write_h5ad(tmp_path / "src.h5ad")
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({
        "source": [str(tmp_path / "src.h5ad")], "condition_key": "perturbation", "control_value": ["ctrl"],
        "collapse_by_target": True}))
    out = tmp_path / "ncells.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "count_target_cells.py"), "--bundle", str(bundle),
                        "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    counts = json.loads(out.read_text())
    assert counts["BBB"] == 4 and counts["AAA"] == 5 and "ctrl" not in counts
    assert all(not k.startswith("ZZZ") for k in counts)
