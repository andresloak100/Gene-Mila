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


def test_counts_follow_the_ingest_key_rule_strict_labels_and_symbol_column(tmp_path):
    import anndata as ad
    import pandas as pd
    sys.path.insert(0, str(ROOT / "tools"))
    from count_target_cells import count_cells
    labels = ["ctrl"] * 7 + ["AAA_BBB"] * 3 + ["BBB_AAA"] * 2 + ["AAA_XYZ"] * 4 + ["AAA_1"] * 1
    obs = pd.DataFrame({"perturbation": labels}, index=[f"c{i}" for i in range(len(labels))])
    var = pd.DataFrame({"gene_symbol": ["AAA", "BBB", "CCC"]}, index=["ENSG1", "ENSG2", "ENSG3"])
    ad.AnnData(np.zeros((len(labels), 3), dtype=np.float32), obs=obs, var=var).write_h5ad(tmp_path / "src.h5ad")
    manifest = {"source": [str(tmp_path / "src.h5ad")], "condition_key": "perturbation", "control_value": ["ctrl"],
                "collapse_by_target": True, "gene_name_key": "gene_symbol"}
    assert count_cells(manifest) == {"AAA": 5, "AAA+BBB": 5}               # either order is one perturbation
    assert count_cells({**manifest, "strict_labels": True}) == {"AAA": 1, "AAA+BBB": 5}
    assert count_cells({k: v for k, v in manifest.items() if k != "gene_name_key"}) == {}  # Ensembl var_names


def test_counts_match_the_ingest_record(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    sys.path.insert(0, str(ROOT / "tests"))
    from count_target_cells import count_cells
    from test_real_data_celleval import fake_screen
    from genemila.data.real import ingest_h5ad
    for strict in (False, True):
        out = ingest_h5ad(fake_screen(tmp_path, norman_labels=True), tmp_path / f"b{strict}", "fake", n_hvg=50,
                          max_control_cells=200, max_eval_cells=25, strict_labels=strict)
        rec = json.loads((out / "private" / "perturbations.json").read_text())["perturbations"]
        counts = count_cells(json.loads((out / "manifest.json").read_text()))
        assert counts == {p: r["n_cells"] for p, r in rec.items()}
        assert counts["G2+G3"] == 60 and counts["G4"] == (30 if strict else 60)
