"""The Norman 2019 ingest (docs/NORMAN_PLAN.md section 4, items 1 to 4, 12 and 13): order-independent and strict
labels, the gene-grouped split with held-out categories, modality and per-perturbation records, gene selection after
the split, the ingest conveniences and external split entries. Each runs on synthetic files, and each new behaviour
is checked to leave a single-target bundle built without the new options exactly as before."""
import hashlib
import json
import random

import numpy as np
import pytest

from test_real_data_celleval import fake_screen

from genemila.data.bundle import make_gene_splits, make_splits, split_id_for, verify_bundle


def screen(tmp_path, spec, n_genes=60, n_control=400, seed=0, var=None, fname="screen.h5ad"):
    """An scPerturb-style file from spec [(label, cells, {gene index: count multiplier})]: raw counts around a common
    base, the listed genes scaled in that label's cells; a multiplier on a gene whose base is 0 adds a mean of
    that many counts instead, so a gene silent in control can be switched on."""
    ad = pytest.importorskip("anndata")
    import pandas as pd
    import scipy.sparse as sp
    rng = np.random.default_rng(seed)
    base = rng.gamma(2.0, 2.0, n_genes)
    base[n_genes - 5:] = 0.0                       # the last five genes are silent in control
    rows, labels = [rng.poisson(base, size=(n_control, n_genes))], ["control"] * n_control
    for label, n, effect in spec:
        mu = base.copy()
        for g, m in effect.items():
            mu[g] = mu[g] * m if mu[g] > 0 else m
        rows.append(rng.poisson(mu, size=(n, n_genes)))
        labels += [label] * n
    X = sp.csr_matrix(np.vstack(rows).astype(np.float32))
    obs = pd.DataFrame({"perturbation": labels}, index=[f"c{i}" for i in range(len(labels))])
    path = tmp_path / fname
    ad.AnnData(X=X, obs=obs, var=var if var is not None else pd.DataFrame(index=[f"G{i}" for i in range(n_genes)])
               ).write_h5ad(path)
    return path


def norman_like_targets(n_singles=105, n_pairs=131, seed=0):
    """Synthetic Norman-shaped labels (singles and random pairs of their genes, a few genes only in pairs)."""
    r = random.Random(seed)
    genes = [f"GENE{i:03d}" for i in range(n_singles + 6)]
    targets = {g: [g] for g in genes[:n_singles]}
    while len(targets) < n_singles + n_pairs:
        a, b = sorted(r.sample(genes, 2))
        targets[f"{a}+{b}"] = [a, b]
    return targets


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


# ---- item 1: order-independent, strict labels -----------------------------------------------------------------

def test_parse_label_sorts_targets_and_names_unknown_tokens():
    from genemila.data.real import canonical_key, parse_label, parse_targets, perturbation_key
    genes = {"CEBPE", "KLF1", "SGK1", "G1"}
    assert parse_label("KLF1_CEBPE", genes) == (["CEBPE", "KLF1"], [])
    assert parse_label("CEBPE_KLF1", genes) == (["CEBPE", "KLF1"], [])
    assert parse_label("CEBPE_X", genes) == (["CEBPE"], ["X"])                 # pooled into CEBPE unless strict
    assert parse_label("CEBPE_guide2", genes) == (["CEBPE"], [])               # a guide suffix is no unknown token
    assert parse_label("CEBPE+ctrl", genes) == (["CEBPE"], [])
    assert parse_label("CEBPE_NegCtrl0", genes) == parse_label("control_CEBPE", genes) == (["CEBPE"], [])
    assert parse_targets("G1_guide1", genes) == ["G1"]                           # singles as before
    assert perturbation_key(["KLF1", "CEBPE"]) == "CEBPE+KLF1"
    assert canonical_key("KLF1+CEBPE", genes) == "CEBPE+KLF1" and canonical_key("CEBPE+ctrl", genes) == "CEBPE"
    assert canonical_key("SGK1+ctrl", genes) == "SGK1"                          # a gene the suffix rule would take
    assert canonical_key("ctrl", genes) is None and canonical_key("CEBPE_X", genes) is None


def test_either_order_pools_and_strict_labels_drop_unknown_tokens(tmp_path):
    from genemila.data.real import ingest_h5ad
    path = fake_screen(tmp_path, norman_labels=True)
    kw = dict(n_hvg=50, max_control_cells=200, max_eval_cells=25)
    loose = ingest_h5ad(path, tmp_path / "loose", "fake", **kw)
    strict = ingest_h5ad(path, tmp_path / "strict", "fake", strict_labels=True, **kw)
    for out in (loose, strict):
        rec = json.loads((out / "private" / "perturbations.json").read_text())["perturbations"]
        assert rec["G2+G3"]["labels"] == ["G2+G3", "G3_G2"] and rec["G2+G3"]["n_cells"] == 60
        assert rec["G2+G3"]["n_targets"] == 2
        assert json.loads((out / "knowledge" / "targets.json").read_text())["G2+G3"] == ["G2", "G3"]
        assert "G3+G2" not in rec and len(rec) == 21
    lr = json.loads((loose / "private" / "perturbations.json").read_text())
    sr = json.loads((strict / "private" / "perturbations.json").read_text())
    assert lr["perturbations"]["G4"]["n_cells"] == 60 and lr["partial_labels"] == {"G4_NOTAGENE": ["NOTAGENE"]}
    assert sr["perturbations"]["G4"]["n_cells"] == 30 and sr["perturbations"]["G4"]["labels"] == ["G4_guide1"]
    assert sr["dropped"]["unknown_token"] == {"G4_NOTAGENE": ["NOTAGENE"]}
    lm, sm = (json.loads((o / "manifest.json").read_text()) for o in (loose, strict))
    assert lm["partial_labels"] == {"G4_NOTAGENE": ["NOTAGENE"]} and lm["n_partial_labels"] == 1  # listed either way
    assert not lm["strict_labels"] and lm["n_strict_dropped_labels"] == 0
    assert sm["strict_labels"] and sm["strict_dropped_labels"] == {"G4_NOTAGENE": ["NOTAGENE"]}
    assert sm["n_partial_labels"] == 0 and sm["n_dropped_labels"] == lm["n_dropped_labels"] == 1


def test_a_gene_symbol_starting_with_sg_is_no_guide_unless_a_guide_form():
    """The suffix rule's sg... form reads sgATF6 as a guide; a token like SGK1 that is not measured is a gene the
    screen missed, an unknown token, never a guide, so its label is not pooled silently into the other gene. A token
    sg, sg plus a number, sg plus a measured gene or sg plus a control label stays a guide, and every token that does
    not start with sg reads exactly as the rule did before."""
    import re
    from genemila.data.external_screen import _SUFFIX
    from genemila.data.real import _NEG_CTRL, CONTROL_LABELS, _is_suffix, canonical_key, parse_label
    assert parse_label("SGK1_TBX2", {"TBX2"}) == (["TBX2"], ["SGK1"])
    assert parse_label("SGK1_TBX2", {"TBX2", "SGK1"}) == (["SGK1", "TBX2"], [])
    for unmeasured in ("SGPL1", "SGMS1", "SGTA", "sgRNA"):
        assert parse_label(f"CEBPE_{unmeasured}", {"CEBPE"}) == (["CEBPE"], [unmeasured])
    for guide in ("sg", "sg2", "SG12", "(sg1)", "sgATF6", "sgNT", "sgNegCtrl3", "sgcontrol"):
        assert parse_label(f"CEBPE_{guide}", {"CEBPE", "ATF6"}) == (["CEBPE"], []), guide
    assert canonical_key("SGK1+ctrl", {"CEBPE"}) is None and canonical_key("SGK1+ctrl", {"SGK1"}) == "SGK1"
    # without a token starting with sg, the rule is the one before this change, token for token
    tokens = ["guide1", "g2", "p1p2", "1", "ctrl", "KD", "ko", "tss3", "CRISPRi", "(guide2)", "[p1]", "control",
              "NegCtrl0", "nt", "NOTAGENE", "X", "ATF6", "pMJ144-2", "Guide", "TSS", "crispr"]
    for t in tokens:
        before = bool(_SUFFIX.match(t)) or t.lower() in CONTROL_LABELS or bool(_NEG_CTRL.match(t))
        assert _is_suffix(t, {"ATF6"}) == _is_suffix(t) == before, t
    assert all(not re.match("[(\\[]?sg", t, re.I) for t in tokens)


def test_strict_labels_drop_and_loose_labels_list_an_unmeasured_sg_symbol(tmp_path):
    """SGK1_TBX2 with SGK1 not measured: a strict ingest drops the label (TBX2 keeps only its own cells), a loose one
    pools it into TBX2 but lists it as a partial label, in the manifest and the private record alike."""
    import pandas as pd
    from genemila.data.real import ingest_h5ad
    names = [f"G{i}" for i in range(60)]
    names[1], names[2] = "TBX2", "CEBPE"                         # SGK1 is not among them
    spec = [("TBX2", 30, {1: 0.2}), ("SGK1_TBX2", 30, {1: 0.2}), ("CEBPE_NOTAGENE", 30, {2: 0.2})]
    spec += [(f"G{g}", 25, {g: 0.2}) for g in range(3, 15)]
    path = screen(tmp_path, spec, var=pd.DataFrame(index=names))
    kw = dict(n_hvg=20, max_control_cells=200, max_eval_cells=10)
    strict = ingest_h5ad(path, tmp_path / "strict", "x", strict_labels=True, **kw)
    loose = ingest_h5ad(path, tmp_path / "loose", "x", **kw)
    sm, lm = (json.loads((o / "manifest.json").read_text()) for o in (strict, loose))
    sr, lr = (json.loads((o / "private" / "perturbations.json").read_text()) for o in (strict, loose))
    assert sm["strict_dropped_labels"] == {"CEBPE_NOTAGENE": ["NOTAGENE"], "SGK1_TBX2": ["SGK1"]}
    assert sm["partial_labels"] == {} and sr["dropped"]["unknown_token"] == sm["strict_dropped_labels"]
    assert sr["perturbations"]["TBX2"]["labels"] == ["TBX2"] and sr["perturbations"]["TBX2"]["n_cells"] == 30
    assert "CEBPE" not in sr["perturbations"]
    assert lm["partial_labels"] == {"CEBPE_NOTAGENE": ["NOTAGENE"], "SGK1_TBX2": ["SGK1"]}
    assert lm["n_partial_labels"] == 2 and lm["n_strict_dropped_labels"] == 0 and lr["partial_labels"] == \
        lm["partial_labels"]
    assert lr["perturbations"]["TBX2"]["labels"] == ["SGK1_TBX2", "TBX2"] and lr["perturbations"]["TBX2"]["n_cells"] == 60


# ---- item 2: gene-grouped split ----------------------------------------------------------------------------------

def test_gene_split_holds_out_genes_and_categories_match_a_recount():
    targets = norman_like_targets()
    s = make_gene_splits(targets, seed=0)
    order = ("train", "val1", "val2")
    gs = s["gene_sets"]
    assert s["mode"] == "gene" and s["seed"] == 0 and s["gene_frac"] == [0.7, 0.15, 0.15]
    assert s["seen2_holdout"] == 0.2 and set(gs) == {g for ts in targets.values() for g in ts}
    assert sorted(s["train"] + s["val1"] + s["val2"]) == sorted(targets)
    assert not set(s["train"]) & set(s["val1"]) and not set(s["val1"]) & set(s["val2"])
    for p in s["train"]:                     # no held-out gene's single or combination is trained on
        assert all(gs[g] == "train" for g in targets[p])
    seen2_held = 0
    for part in ("val1", "val2"):
        for p in s[part]:
            most = max((gs[g] for g in targets[p]), key=order.index)
            if most == "train":              # a held-out combination of two training genes
                assert len(targets[p]) > 1
                seen2_held += 1
            else:                            # otherwise the most held-out set among its genes
                assert most == part
    seen_pairs = [p for p, ts in targets.items() if len(ts) > 1 and all(gs[g] == "train" for g in ts)]
    assert seen2_held == int(round(0.2 * len(seen_pairs))) and seen2_held > 0
    singles_train = {targets[p][0] for p in s["train"] if len(targets[p]) == 1}
    recount = {}
    for p in s["val1"] + s["val2"]:
        recount[p] = "single" if len(targets[p]) == 1 else \
            f"pair_seen{sum(g in singles_train for g in targets[p])}"
    assert s["categories"] == recount
    assert {"single", "pair_seen0", "pair_seen1", "pair_seen2"} <= set(recount.values())
    for part in ("val1", "val2"):            # both held-out sets hold every category
        assert {recount[p] for p in s[part]} >= {"single", "pair_seen1", "pair_seen2"}


def test_gene_split_id_is_reproducible_and_hashes_categories():
    targets = norman_like_targets()
    a, b = make_gene_splits(targets, seed=0), make_gene_splits(dict(reversed(list(targets.items()))), seed=0)
    assert a == b and a["split_id"] == split_id_for(a)
    assert make_gene_splits(targets, seed=1)["split_id"] != a["split_id"]
    changed = {**a, "categories": {**a["categories"], next(iter(a["categories"])): "relabelled"}}
    assert split_id_for(changed) != a["split_id"]          # the categories are part of the identifier
    with pytest.raises(ValueError):
        make_gene_splits(targets, seed=0, gene_frac=(0.7, 0.2, 0.2))


def test_split_without_categories_keeps_its_split_id():
    perts = [f"P{i}" for i in range(50)] + ["A+B", "C+D"]
    s = make_splits(perts, seed=0)
    old = json.dumps({k: sorted(s[k]) for k in ("train", "val1", "val2")}, sort_keys=True)  # the formula before
    assert s["split_id"] == "split_" + hashlib.sha256(old.encode()).hexdigest()[:16] == "split_ec45388268a7ab9c"
    assert make_splits(perts, seed=7)["split_id"] == "split_f6c444b9b8649c27"


def test_gene_split_bundle_records_mode_categories_and_modality(tmp_path):
    from genemila.data.real import ingest_h5ad
    spec = [(f"G{g}", 25, {g: 0.2}) for g in range(1, 21)]
    spec += [(f"G{a}_G{b}", 25, {a: 0.2, b: 0.2}) for a, b in ((1, 2), (4, 3), (5, 6), (7, 8), (9, 10), (12, 11),
                                                                (13, 14), (15, 16), (17, 18), (20, 19), (1, 5))]
    out = ingest_h5ad(screen(tmp_path, spec), tmp_path / "b", "normanish", n_hvg=20, max_control_cells=200,
                      max_eval_cells=10, split_mode="gene", gene_frac=(0.6, 0.2, 0.2), seen2_holdout=0.5,
                      modality="CRISPRa", strict_labels=True)
    assert verify_bundle(out) == []
    s = json.loads((out / "splits.json").read_text())
    targets = json.loads((out / "knowledge" / "targets.json").read_text())
    assert s == make_gene_splits(targets, seed=0, gene_frac=(0.6, 0.2, 0.2), seen2_holdout=0.5)
    assert set(s["categories"]) == set(s["val1"]) | set(s["val2"])
    assert targets["G3+G4"] == ["G3", "G4"] and "G4+G3" not in targets      # G4_G3 keyed in sorted order
    m = json.loads((out / "manifest.json").read_text())
    assert m["modality"] == "CRISPRa" and m["split_mode"] == "gene" and m["split_id"] == s["split_id"]
    held = set(s["val1"]) | set(s["val2"])
    assert not held & set(walk_keys(m))                 # no held-out perturbation is named, let alone counted
    rec = json.loads((out / "private" / "perturbations.json").read_text())["perturbations"]
    assert set(rec) == set(targets) and all(rec[p]["n_cells"] == 25 for p in rec)
    assert all(rec[p]["category"] == s["categories"].get(p) for p in rec)
    assert all(rec[p]["set"] == next(k for k in ("train", "val1", "val2") if p in s[k]) for p in rec)
    z = np.load(out / "public.npz", allow_pickle=False)
    assert set(map(str, z["train_perts"])) == set(s["train"])


# ---- item 3: modality and records ---------------------------------------------------------------------------------

def test_manifest_records_without_held_out_counts_and_no_modality_by_default(tmp_path):
    from genemila.data.real import ingest_h5ad
    spec = [(f"G{g}_guide1", 25, {g: 0.2}) for g in range(1, 16)] + [("G16_guide1", 8, {16: 0.2})]
    path = screen(tmp_path, spec)
    out = ingest_h5ad(path, tmp_path / "b", "plain", n_hvg=20, max_control_cells=200, max_eval_cells=10)
    m = json.loads((out / "manifest.json").read_text())
    assert "modality" not in m                           # an old-style bundle states no modality
    assert m["dropped_min_cells"] == {"G16": 8} and m["min_cells"] == 20
    assert m["source_md5"] == [hashlib.md5(path.read_bytes()).hexdigest()]
    assert m["split_mode"] == "perturbation" and m["gene_selection"] == "control"
    assert "sample_seed" not in m and "seed" not in m   # the split seed would rebuild the split from public files
    assert "code_commit" in m and "private/perturbations.json" in m["file_sha256"]
    s = json.loads((out / "splits.json").read_text())
    assert "categories" not in s and "mode" not in s
    held = set(s["val1"]) | set(s["val2"])
    assert not held & set(walk_keys(m))
    rec = json.loads((out / "private" / "perturbations.json").read_text())
    assert held <= set(rec["perturbations"]) and rec["dropped"]["min_cells"] == {"G16": 8}
    assert rec["sample_seed"] == 0                       # the effective sample seed, kept private


def test_sample_seed_moves_only_the_cell_samples(tmp_path):
    from genemila.data.real import ingest_h5ad
    path = fake_screen(tmp_path)
    kw = dict(n_hvg=50, max_control_cells=200, max_eval_cells=25)
    a = ingest_h5ad(path, tmp_path / "a", "fake", **kw)
    same = ingest_h5ad(path, tmp_path / "same", "fake", sample_seed=0, **kw)
    other = ingest_h5ad(path, tmp_path / "other", "fake", sample_seed=5, **kw)
    za, zs, zo = (np.load(o / "public.npz", allow_pickle=False) for o in (a, same, other))
    for k in za.files:
        assert np.array_equal(za[k], zs[k])
    assert (a / "splits.json").read_text() == (other / "splits.json").read_text()
    assert not np.array_equal(za["control_cells"], zo["control_cells"])
    assert json.loads((other / "manifest.json").read_text())["sample_seed"] == 5
    # a sample seed equal to the split seed, or none, leaves the manifest without one: it would be the split seed
    for out in (a, same):
        assert "sample_seed" not in json.loads((out / "manifest.json").read_text())
    for out, want in ((a, 0), (same, 0), (other, 5)):
        assert json.loads((out / "private" / "perturbations.json").read_text())["sample_seed"] == want


# ---- item 4: gene selection after the split ----------------------------------------------------------------------

def test_control_plus_train_selection_keeps_genes_induced_in_training_only(tmp_path):
    from genemila.data.real import ingest_h5ad
    n = 60
    train_on, held_on = n - 2, n - 1                 # silent in control (screen() zeroes the last five genes)
    spec = [(f"G{g}", 30, {g: 0.2}) for g in range(1, 13)]
    spec[0] = ("G1", 30, {1: 0.2, train_on: 60.0})   # a training perturbation switches train_on on
    spec[11] = ("G12", 30, {12: 0.2, held_on: 60.0})  # a sealed one switches held_on on
    path = screen(tmp_path, spec, n_genes=n)
    split = {"train": [f"G{g}" for g in range(1, 9)], "val1": ["G9", "G10"], "test": ["G11", "G12"]}
    (tmp_path / "s.json").write_text(json.dumps(split))
    kw = dict(n_hvg=15, max_control_cells=200, max_eval_cells=10, splits_file=tmp_path / "s.json")
    genes = {}
    for sel in ("control", "control+train"):
        out = ingest_h5ad(path, tmp_path / sel.replace("+", "_"), "sel", gene_selection=sel, **kw)
        genes[sel] = set(map(str, np.load(out / "public.npz", allow_pickle=False)["genes"]))
        assert json.loads((out / "manifest.json").read_text())["gene_selection"] == sel
        assert {f"G{g}" for g in range(1, 13)} <= genes[sel]     # every target is kept, held-out ones included
    assert f"G{train_on}" in genes["control+train"] and f"G{train_on}" not in genes["control"]
    assert f"G{held_on}" not in genes["control+train"] and f"G{held_on}" not in genes["control"]


def test_column_variance_matches_numpy():
    import scipy.sparse as sp
    from genemila.data.real import _column_var
    rng = np.random.default_rng(0)
    X = sp.random(500, 40, density=0.2, format="csr", random_state=1, dtype=np.float32)
    rows = rng.choice(500, 300, replace=False)
    want = X[np.sort(rows)].toarray().astype(np.float64).var(axis=0)
    assert np.allclose(_column_var(lambda r: X[r], rows, 40, chunk=64), want)
    assert np.allclose(_column_var(lambda r: X[r].toarray(), rows, 40, chunk=64), want)


# ---- item 12: ingest conveniences --------------------------------------------------------------------------------

def test_gene_name_key_and_a_clear_error_when_no_label_names_a_gene(tmp_path):
    import pandas as pd
    from genemila.data.real import ingest_h5ad
    n = 60
    var = pd.DataFrame({"symbol": [f"G{i}" for i in range(n)]}, index=[f"ENSG{i:011d}" for i in range(n)])
    path = screen(tmp_path, [(f"G{g}", 25, {g: 0.2}) for g in range(1, 13)], n_genes=n, var=var)
    with pytest.raises(ValueError, match="gene-name-key"):        # Ensembl var_names: nothing parses
        ingest_h5ad(path, tmp_path / "b0", "x", n_hvg=20, max_control_cells=200)
    with pytest.raises(ValueError, match="no column 'gene_symbol'"):
        ingest_h5ad(path, tmp_path / "b1", "x", n_hvg=20, gene_name_key="gene_symbol")
    out = ingest_h5ad(path, tmp_path / "b", "x", n_hvg=20, gene_name_key="symbol", max_control_cells=150,
                      max_eval_cells=7)
    m = json.loads((out / "manifest.json").read_text())
    assert m["gene_name_key"] == "symbol" and m["n_control_cells"] == 150 and m["n_perturbations"] == 12
    from genemila.benchmark import celleval
    X, labels = celleval.load_real_cells(out, "val2")
    assert (labels == "control").sum() == 7 and all((labels == p).sum() == 7 for p in set(labels))
    with pytest.raises(ValueError, match="min_cells"):
        ingest_h5ad(path, tmp_path / "b2", "x", n_hvg=20, gene_name_key="symbol", min_cells=100)


def test_backed_reading_gives_the_same_bundle(tmp_path):
    from genemila.data.real import ingest_h5ad
    path = fake_screen(tmp_path, norman_labels=True)
    kw = dict(n_hvg=50, max_control_cells=200, max_eval_cells=25, gene_selection="control+train")
    mem = ingest_h5ad(path, tmp_path / "mem", "fake", **kw)
    disk = ingest_h5ad(path, tmp_path / "disk", "fake", backed=True, **kw)
    m1, m2 = (json.loads((o / "manifest.json").read_text()) for o in (mem, disk))
    assert m2["backed"] and not m1["backed"]
    assert m1["file_sha256"] == m2["file_sha256"]            # every bundle file, byte for byte


# ---- item 13: external split entries -----------------------------------------------------------------------------

def test_external_split_entries_are_canonicalised_only_for_a_bundle_with_combinations(tmp_path):
    from genemila.data.real import external_splits, ingest_h5ad
    ext = {"train": ["A+ctrl", "C", "B"], "val": ["D"], "test": ["B_A", "control", "Z+ctrl"]}
    perts = ["A", "B", "C", "D", "A+B"]
    old = external_splits(ext, perts)
    assert old["train"] == ["B", "C"] and old["val2"] == []            # unchanged without the gene list
    missed = []
    new = external_splits(ext, perts, canonical_genes={"A", "B", "C", "D"}, unmatched=missed)
    assert new["train"] == ["A", "B", "C"] and new["val1"] == ["D"] and new["val2"] == ["A+B"]
    assert missed == ["Z+ctrl"]                                        # controls are not reported
    # through the ingest: a single-target bundle maps a GEARS-style entry exactly as before (it is dropped) ...
    spec = [(f"G{g}", 25, {g: 0.2}) for g in range(1, 13)]
    split = {"train": [f"G{g}" for g in range(1, 9)] + ["G9+ctrl"], "test": ["G10", "G11", "G12+ctrl"]}
    (tmp_path / "s.json").write_text(json.dumps(split))
    out = ingest_h5ad(screen(tmp_path, spec), tmp_path / "single", "x", n_hvg=20, splits_file=tmp_path / "s.json")
    s = json.loads((out / "splits.json").read_text())
    assert "G12" not in s["val2"] and "G9" not in s["train"] + s["val1"]
    m = json.loads((out / "manifest.json").read_text())
    assert m["split_unmatched_entries"] == ["G12+ctrl", "G9+ctrl"] and m["dropped_not_in_split"] == ["G12", "G9"]
    # ... while a bundle with combinations reads it, and a combination in either order
    spec2 = spec + [("G2_G1", 25, {1: 0.2, 2: 0.2})]
    split2 = {**split, "test": split["test"] + ["G1+G2"]}
    (tmp_path / "s2.json").write_text(json.dumps(split2))
    out2 = ingest_h5ad(screen(tmp_path, spec2, fname="s2.h5ad"), tmp_path / "pairs", "x", n_hvg=20,
                       splits_file=tmp_path / "s2.json")
    s2 = json.loads((out2 / "splits.json").read_text())
    assert {"G12", "G1+G2"} <= set(s2["val2"]) and "G9" in s2["train"] + s2["val1"]


# ---- the single-target bundle stays as it was ---------------------------------------------------------------------

def test_default_ingest_of_a_single_target_style_screen_is_unchanged(tmp_path):
    """Pinned from the code before these items (commit b63491d): the fake screen's split identifier, perturbation
    sets and kept genes. Every bundle file was also compared byte for byte against that code by hand."""
    from genemila.data.real import ingest_h5ad
    out = ingest_h5ad(fake_screen(tmp_path), tmp_path / "b", "fake", n_hvg=50, max_control_cells=200,
                      max_eval_cells=25)
    s = json.loads((out / "splits.json").read_text())
    assert s["split_id"] == "split_c7b134f306be6413" and set(s) == {"train", "val1", "val2", "seed", "split_id"}
    assert s["val1"] == ["G14", "G16", "G20", "G9"] and s["val2"] == ["G10", "G18", "G3", "G4"]
    z = np.load(out / "public.npz", allow_pickle=False)
    assert hashlib.sha256(",".join(map(str, z["genes"])).encode()).hexdigest()[:16] == "9f5c240f484a02b3"
    m = json.loads((out / "manifest.json").read_text())
    assert "modality" not in m and m["n_dropped_labels"] == 1 and m["dropped_labels"] == ["NOTAGENE"]
