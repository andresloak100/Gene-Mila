"""tools/replogle_slice_manifest.py: eligibility from obs and var only, every exclusion reason, a deterministic draw."""
import hashlib
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import replogle_slice_manifest as rsm  # noqa: E402

UNIVERSE = ["ADT", "NRT", "NEW1", "FEW", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "P2", "X1", "OLDSYM"]
LABELS = {"control": 40, "ADT": 50, "NRT": 30, "OUT": 50, "FEW": 19, "RET": 25, "E1_E2": 30, "CURSYM": 30,
          "E1": 20, "E2": 21, "E3": 22, "E4": 23, "E5": 24, "E6": 25, "E7": 26, "E8": 27}


@pytest.fixture
def cohort(tmp_path):
    labels = [lab for lab, n in LABELS.items() for _ in range(n)]
    rng = np.random.default_rng(0)
    var_genes = ["OUT", "E1", "E2", "E3", "ZZ", "CURSYM"]   # var need not cover the targets
    a = ad.AnnData(X=rng.poisson(1.0, (len(labels), len(var_genes))).astype(np.float32),
                   obs=pd.DataFrame({"perturbation": pd.Categorical(labels)},
                                    index=[f"c{i}" for i in range(len(labels))]),
                   var=pd.DataFrame(index=var_genes))
    path = tmp_path / "cohort.h5ad"
    a.write_h5ad(path)
    frozen = tmp_path / "frozen_manifest.json"
    frozen.write_text(json.dumps({"genes": UNIVERSE}))
    adamson = tmp_path / "adamson_targets.json"
    adamson.write_text(json.dumps({"ADT": ["ADT"], "P2": ["P2"]}))
    norman = tmp_path / "norman_targets.txt"
    norman.write_text("NRT\nP2\n")
    sets = tmp_path / "gene_sets.json"
    sets.write_text(json.dumps({"REACTOME:R1": ["ADT", "E1", "E2"], "CORUM:C1": ["P2", "E3", "OUT"],
                                "GOBP:G1": ["ADT", "E4"], "REACTOME:R2": ["E5", "E6"]}))
    hgnc = tmp_path / "hgnc.txt"
    hgnc.write_text("hgnc_id\tsymbol\tprev_symbol\talias_symbol\nHGNC:1\tNEW1\t\"RET\"\t\nHGNC:2\tE1\t\t\"OUT\"\n"
                    "HGNC:3\tCURSYM\t\"OLDSYM\"\t\n")
    return {"h5ad": path, "frozen": frozen, "adamson": adamson, "norman": norman, "sets": sets, "hgnc": hgnc}


def run(c, out, *extra):
    argv = ["--h5ad", str(c["h5ad"]), "--frozen-manifest", str(c["frozen"]),
            "--exclude", f"adamson={c['adamson']}", "--exclude", f"norman={c['norman']}",
            "--panel", str(c["adamson"]), "--gene-sets", str(c["sets"]), "--hgnc", str(c["hgnc"]),
            "--out", str(out), *extra]
    assert rsm.main(argv) == 0
    return json.loads((out / "manifest.json").read_text())


def test_every_exclusion_reason_and_the_in_distribution_subset(cohort, tmp_path, capsys):
    m = run(cohort, tmp_path / "m")
    rows = {t["symbol"]: t for t in m["targets"]}
    assert "control" not in rows and m["h5ad"]["control_cells"] == 40
    assert rows["ADT"]["excluded"] == ["adamson target"]
    assert rows["NRT"]["excluded"] == ["norman target"]
    assert rows["OUT"]["excluded"] == ["outside the frozen gene universe"]   # alias of E1 is never a rename
    assert rows["FEW"]["excluded"] == ["fewer than 20 cells"] and rows["FEW"]["cells"] == 19
    assert rows["E1_E2"]["excluded"] == ["label names more than one gene"]
    assert rows["NEW1"]["labels"] == ["RET"] and rows["NEW1"]["mapping"] == "retired symbol mapped to NEW1"
    assert rows["NEW1"]["eligible"] and rows["NEW1"]["cells"] == 25
    # The universe keeps Adamson's older symbols: a current cohort symbol maps back to the one the universe uses.
    assert rows["OLDSYM"]["labels"] == ["CURSYM"] and rows["OLDSYM"]["eligible"]
    assert rows["OLDSYM"]["mapping"] == "current symbol mapped to the universe's retired symbol OLDSYM"
    eligible = sorted(t["symbol"] for t in m["targets"] if t["eligible"])
    assert eligible == ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "NEW1", "OLDSYM"]
    assert all((len(t["excluded"]) > 0) == (not t["eligible"]) for t in m["targets"])
    assert m["common_gene_panel"]["genes"] == ["E1", "E2", "E3", "OLDSYM"] and m["common_gene_panel"]["n"] == 4
    # Reactome and CORUM classes of the panel (ADT, P2) only; GO classes do not count.
    assert set(m["in_distribution_classes"]) == {"REACTOME:R1", "CORUM:C1"}
    assert rows["E1"]["in_distribution"] and rows["E1"]["classes"] == ["REACTOME:R1"]
    assert rows["E3"]["in_distribution"] and rows["E3"]["classes"] == ["CORUM:C1"]
    assert not rows["E4"]["in_distribution"] and not rows["E5"]["in_distribution"]
    assert m["counts"] == {"labels": len(LABELS), "targets": 15, "eligible": 10, "eligible_in_distribution": 3,
                           "eligible_other": 7,
                           "by_reason": {"adamson target": 1, "norman target": 1, "outside the frozen gene universe": 1,
                                         "fewer than 20 cells": 1, "label names more than one gene": 1}}
    assert "draw" not in m
    text = (tmp_path / "m" / "manifest.md").read_text()
    assert "Eligible: 10 (in-distribution 3, other 7)" in text and "| adamson target | 1 |" in text
    assert "Common gene panel for scoring: 4" in text
    assert "Physical access" in text and "obs and var" in text
    printed = capsys.readouterr().out
    assert hashlib.sha256((tmp_path / "m" / "manifest.json").read_bytes()).hexdigest() in printed


def test_draw_is_deterministic_from_the_seed_and_the_halves_are_disjoint(cohort, tmp_path):
    a = run(cohort, tmp_path / "a", "--draw", "--seed", "block 000000000000000000020b1a", "--role", "both")
    b = run(cohort, tmp_path / "b", "--draw", "--seed", "block 000000000000000000020b1a", "--role", "both")
    other = run(cohort, tmp_path / "c", "--draw", "--seed", "another public value", "--role", "both")
    assert a["draw"] == b["draw"]
    assert a["draw"]["ranked"] != other["draw"]["ranked"]
    eligible = {t["symbol"] for t in a["targets"] if t["eligible"]}
    assert set(a["draw"]["ranked"]) == eligible
    r1, r2 = a["draw"]["r1"], a["draw"]["r2"]
    assert not set(r1) & set(r2) and set(r1) | set(r2) == eligible
    assert abs(len(r1) - len(r2)) <= 2
    ind = {t["symbol"] for t in a["targets"] if t["in_distribution"]}
    assert abs(len(ind & set(r1)) - len(ind & set(r2))) <= 1
    # The rank key is public: anyone with the seed recomputes the order.
    keys = {s: hashlib.sha256(f"block 000000000000000000020b1a\n{s}".encode()).hexdigest() for s in eligible}
    assert a["draw"]["ranked"] == sorted(eligible, key=keys.get)
    r2_only = run(cohort, tmp_path / "d", "--draw", "--seed", "block 000000000000000000020b1a", "--role", "r2")
    assert r2_only["draw"]["r2"] == a["draw"]["ranked"] and "r1" not in r2_only["draw"]


def test_refuses_to_touch_anything_but_obs_and_var(cohort, tmp_path):
    import h5py
    with h5py.File(cohort["h5ad"], "r") as f:
        guard = rsm.ObsVarOnly(f)
        assert "obs" in guard and "X" not in guard
        for key in ("X", "layers", "obsm", "raw", "uns"):
            with pytest.raises(PermissionError):
                guard[key]
        assert "perturbation" in guard["obs"]
    with pytest.raises(SystemExit):   # --draw without --seed
        rsm.main(["--h5ad", str(cohort["h5ad"]), "--frozen-manifest", str(cohort["frozen"]), "--draw",
                  "--out", str(tmp_path / "y")])
    run(cohort, tmp_path / "once")
    with pytest.raises(SystemExit):   # never overwritten
        run(cohort, tmp_path / "once")
