"""tools/external_loo.py on bundles with pairs (docs/NORMAN_PLAN.md section 4 item 8 and section 5): a pair's external
row is the sum of its targets' rows, present only when every target has one; a file's sign multiplies external_direct
only; protocol norman_v1 hides a held-out single's pairs, fixes its own grid, k and sign, compares external_stack
with stack_inbundle by the reading rule behind a coverage gate, and renders the same report from its JSON twin. A
single-target bundle with an unsigned file keeps exactly the rows, columns and report keys it had."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import external_loo  # noqa: E402

from genemila.data.bundle import export_public  # noqa: E402


# ------------------------------------------------------------------------------------------------ fixtures

def norman_case(n_single=24, n_pairs=16, n_genes=150, seed=0, ext_scale=-1.3, ext_noise=0.15, keep_rows=None,
                n_silent=12):
    """A CRISPRa-like bundle of singles and pairs, in the shapes load_bundle and load_external return. Each target gene
    has an effect over the genes (a module pattern its gene set names, plus its own part, plus the target itself
    raised); a pair's change is the sum of its singles' plus a little interaction. The external screen is CRISPRi-like:
    a target's row is ext_scale times its effect plus noise, every tenth gene unmeasured; keep_rows, when given, names
    the target genes that have a row. The first n_silent target genes are zero in every control cell (silent)."""
    rng = np.random.default_rng(seed)
    genes = [f"G{j:03d}" for j in range(n_genes)]
    tgenes = genes[:n_single]
    n_mod = 4
    module = {g: i % n_mod for i, g in enumerate(tgenes)}
    M = rng.normal(0, 1, (n_mod, n_genes))
    effect = {}
    for j, g in enumerate(tgenes):
        e = M[module[g]] * rng.uniform(0.3, 1.0) + rng.normal(0, 0.8, n_genes)
        e[j] += 3.0
        effect[g] = e
    targets = {g: [g] for g in tgenes}
    while len(targets) < n_single + n_pairs:
        a, b = sorted(rng.choice(tgenes, size=2, replace=False))
        targets.setdefault(f"{a}+{b}", [b, a])   # listed in reverse order: the key, not the list, is sorted
    perts = sorted(targets)
    D = np.array([sum(effect[t] for t in targets[p]) + rng.normal(0, 0.1 if len(targets[p]) == 1 else 0.3, n_genes)
                  for p in perts])
    control = rng.gamma(2.0, 1.0, (200, n_genes)) * (rng.random((200, n_genes)) < 0.5)
    control[:, :n_silent] = 0.0
    measured = np.arange(n_genes) % 10 != 3
    rows = {}
    for g in tgenes if keep_rows is None else keep_rows:
        x = ext_scale * effect[g] + rng.normal(0, ext_noise, n_genes)
        x[~measured] = np.nan
        rows[g] = x
    gene_sets = {f"M{m}": [g for g in tgenes if module[g] == m] for m in range(n_mod)}
    bundle = {"name": "norman_syn", "genes": genes, "perts": perts, "deltas": D, "control_mean": control.mean(axis=0),
              "n_cells": [40] * len(perts), "targets": {p: list(targets[p]) for p in perts}, "gene_sets": gene_sets,
              "modality": "CRISPRa", "control_nonzero": (control > 0).mean(axis=0)}
    external = {"name": "ext_norman", "description": "synthetic CRISPRi screen", "source": {"modality": "CRISPRi"},
                "measured": measured, "rows": rows, "n_cells": {g: 50 + i for i, g in enumerate(sorted(rows))},
                "n_control_cells": 500, "n_perts": len(rows), "n_bundle_targets_missing": n_single - len(rows),
                "zero_cell_targets": [], "sign": -1, "modality": "CRISPRi"}
    return bundle, external, control


def write_public(dir_, bundle, external, control, heldout_pair=True):
    """The case on disk as a public bundle (public.npz, knowledge/targets.json and gene_sets.json, manifest.json with
    the modality) plus the external file in the builder's format with --modality, and a sealed directory the tool
    must never open."""
    dir_ = Path(dir_)
    (dir_ / "knowledge").mkdir(parents=True)
    perts = bundle["perts"]
    targets = dict(bundle["targets"])
    if heldout_pair:
        targets["G000+G001"] = ["G000", "G001"] if "G000+G001" not in targets else targets["G000+G001"]
    np.savez_compressed(dir_ / "public.npz", genes=np.array(bundle["genes"]), control_cells=control.astype(np.float32),
                        perts=np.array(sorted(targets)), train_perts=np.array(perts),
                        train_means=(bundle["control_mean"] + bundle["deltas"]).astype(np.float32),
                        train_ncells=np.array(bundle["n_cells"]))
    (dir_ / "knowledge" / "targets.json").write_text(json.dumps(targets))
    (dir_ / "knowledge" / "gene_sets.json").write_text(json.dumps(bundle["gene_sets"]))
    (dir_ / "manifest.json").write_text(json.dumps({"name": bundle["name"], "modality": "CRISPRa"}))
    measured = [bool(m) for m in external["measured"]]

    def masked(v):
        return [round(float(x), 6) if m else None for m, x in zip(measured, v)]

    rec = {"description": "CRISPRi screen deltas, sign -1 (this bundle is CRISPRa): synthetic", "sign": -1,
           "source": {"file": "x.h5ad", "modality": "CRISPRi", "bundle_modality": "CRISPRa"},
           "genes": bundle["genes"], "measured": measured,
           "control": {"n_cells": 500, "mean": masked(np.zeros(len(bundle["genes"])))},
           "perts": {g: {"n_cells": external["n_cells"][g], "labels": [g], "delta": masked(r)}
                     for g, r in external["rows"].items()},
           "bundle_targets_missing": []}
    (dir_ / "knowledge" / "ext_norman.json").write_text(json.dumps(rec))
    (dir_ / "private").mkdir()
    (dir_ / "private" / "val2.npz").write_bytes(b"sealed")
    return dir_


@pytest.fixture(scope="module")
def case():
    return norman_case()


@pytest.fixture(scope="module")
def report(case):
    bundle, external, _ = case
    return external_loo.analyse_norman_v1(bundle, external, inputs={"public.npz": "abc"})


# ------------------------------------------------------------------------- item 8: pair rows and the sign

def _old_prepare_rows(bundle, external):
    """_prepare's external rows as they were before pairs: the first target gene with a row."""
    n, g = bundle["deltas"].shape
    E, has, tgt = np.full((n, g), np.nan), np.zeros(n, dtype=bool), [None] * n
    for i, p in enumerate(bundle["perts"]):
        for t in bundle["targets"][p]:
            if t in external["rows"]:
                E[i], has[i], tgt[i] = external["rows"][t], True, t
                break
    return E, has, tgt


def test_single_target_bundle_keeps_its_rows_columns_and_report_keys(dataset, tmp_path):
    """Adamson's kind (one target per perturbation, a file without sign): the rows, the four columns of every fold
    and the report keys are exactly those of the rule before pairs, and the report says what it always said."""
    from test_external_loo import _write_external
    pub = export_public(dataset, tmp_path / "pub")
    bundle = external_loo.load_bundle(pub)
    drop = {bundle["targets"][p][0] for p in bundle["perts"][::3]}
    name = _write_external(pub, "ext_single", bundle, "signal", drop=drop)
    external = external_loo.load_external(pub, name, bundle["genes"])
    assert external["sign"] == 1 and external["modality"] is None
    S = external_loo._prepare(bundle, external)
    E, has, tgt = _old_prepare_rows(bundle, external)
    assert np.array_equal(S["ext"], E, equal_nan=True) and np.array_equal(S["has_ext"], has) and S["ext_target"] == tgt
    assert S["sign"] == 1 and S["ext_cells"] == [external["n_cells"].get(t) if t else None for t in tgt]
    for i in (0, 1, 4):
        avail = np.ones(len(bundle["perts"]), dtype=bool)
        avail[i] = False
        cols = external_loo._features(i, avail, S, 5)[0]
        mr = bundle["deltas"][avail].mean(axis=0)
        assert np.array_equal(cols[2], np.where(np.isfinite(E[i]), E[i], mr) if has[i] else mr)
    rep = external_loo.analyse(bundle, external, k=5)
    assert not {"n_multi_target", "external_sign", "protocol"} & set(rep)
    assert "(their first target gene with one)" in external_loo.render(rep)


def test_pair_row_is_the_sum_of_its_targets_rows(case):
    bundle, external, _ = case
    S = external_loo._prepare(bundle, external)
    rows, perts = external["rows"], bundle["perts"]
    pairs = [i for i, p in enumerate(perts) if "+" in p]
    assert pairs and all(len(bundle["targets"][perts[i]]) == 2 for i in pairs)
    for i in pairs:
        a, b = sorted(bundle["targets"][perts[i]])
        assert np.array_equal(S["ext"][i], rows[a] + rows[b], equal_nan=True)   # NaN where either is unmeasured
        assert S["has_ext"][i] and S["ext_target"][i] == f"{a}+{b}" == perts[i]
        assert S["ext_cells"][i] == min(external["n_cells"][a], external["n_cells"][b])
        # the unit row of kernel ridge is that of the sum, not the sum of the unit rows
        x = S["ext"][i][np.isfinite(S["ext"][i])]
        np.testing.assert_allclose(S["krr_z"][i][np.isfinite(S["ext"][i])], (x - x.mean()) / np.linalg.norm(x - x.mean()))
    # the order the targets are listed in does not matter; another row of B changes the pair's row
    i = pairs[0]
    a, b = sorted(bundle["targets"][perts[i]])
    flipped = {**bundle, "targets": {**bundle["targets"], perts[i]: [a, b]}}
    assert np.array_equal(external_loo._prepare(flipped, external)["ext"][i], S["ext"][i], equal_nan=True)
    moved = {**external, "rows": {**rows, b: rows[b] + 1.0}}
    assert not np.array_equal(external_loo._prepare(bundle, moved)["ext"][i], S["ext"][i], equal_nan=True)
    # a pair has a row only when every target has one, and a single keeps its own row
    gone = {**external, "rows": {g: r for g, r in rows.items() if g != b}}
    S2 = external_loo._prepare(bundle, gone)
    for j, p in enumerate(perts):
        assert S2["has_ext"][j] == all(t != b for t in bundle["targets"][p])
        if len(bundle["targets"][p]) == 1 and S2["has_ext"][j]:
            assert np.array_equal(S2["ext"][j], rows[p], equal_nan=True)


def test_default_protocol_reads_pairs_and_the_files_sign(case):
    bundle, external, _ = case
    S = external_loo._prepare(bundle, external)
    assert S["sign"] == -1
    plus = external_loo._prepare(bundle, {**external, "sign": 1})
    i = bundle["perts"].index(next(p for p in bundle["perts"] if "+" in p))
    avail = np.ones(len(bundle["perts"]), dtype=bool)
    avail[i] = False
    cols, flags = external_loo._features(i, avail, S, 5)
    cols_plus = external_loo._features(i, avail, plus, 5)[0]
    mr = bundle["deltas"][avail].mean(axis=0)
    m = np.isfinite(S["ext"][i])
    assert np.array_equal(cols[2], np.where(m, -S["ext"][i], mr)) and np.array_equal(cols_plus[2], np.where(m, S["ext"][i], mr))
    assert np.array_equal(cols[3], cols_plus[3]) and np.array_equal(S["ext_corr"], plus["ext_corr"], equal_nan=True)
    assert np.array_equal(S["krr_z"], plus["krr_z"])                                   # similarities are sign-free
    small = norman_case(n_single=8, n_pairs=6, n_genes=60)
    rep = external_loo.analyse(small[0], small[1], k=3)
    assert rep["n_multi_target"] == 6 and rep["external_sign"] == -1
    md = external_loo.render(rep)
    assert "(the sum of their target genes' rows, present only when every target has one)" in md
    assert "The file's sign is -1" in md and "The agreement is of the unsigned rows" in md
    pair = next(r for r in rep["per_perturbation"] if "+" in r["pert"])
    a, b = pair["external_target"].split("+")
    assert pair["n_cells_external"] == min(small[1]["n_cells"][a], small[1]["n_cells"][b])


def test_load_external_reads_and_checks_the_sign(tmp_path):
    (tmp_path / "knowledge").mkdir()
    base = {"genes": ["A", "B", "C"], "measured": [True, True, True], "perts": {"A": {"n_cells": 5, "delta": [1, 2, 3]}}}
    for sign, ok in ((None, 1), (-1, -1), (1, 1), (2, None), ("-1", None), (True, None)):
        rec = dict(base) if sign is None else {**base, "sign": sign}
        (tmp_path / "knowledge" / "e.json").write_text(json.dumps(rec))
        if ok is None:
            with pytest.raises(ValueError, match="sign"):
                external_loo.load_external(tmp_path, "e", ["A", "B", "C"])
        else:
            assert external_loo.load_external(tmp_path, "e", ["A", "B", "C"])["sign"] == ok


# ------------------------------------------------------------------------------------------ norman_v1

def test_hiding_rule(case):
    bundle, external, _ = case
    S = external_loo._nv1_prepare(bundle, external)
    perts, tg = bundle["perts"], S["targets_sorted"]
    for i, p in enumerate(perts):
        hidden = {perts[j] for j in np.flatnonzero(S["hide"][i])}
        if len(tg[i]) == 1:
            assert hidden == {p} | {q for q in perts if "+" in q and p in q.split("+")}
        else:
            assert hidden == {p}
    assert S["sign"] == external_loo.NV1_SIGN == -1
    assert {"single", "pair"} == set(S["kind"]) and "silent" in S["expression"] and "expressed" in S["expression"]


def test_fold_never_sees_the_labels_its_rule_hides(case):
    bundle, external, _ = case
    S = external_loo._nv1_prepare(bundle, external)
    i = next(j for j, p in enumerate(bundle["perts"]) if "+" not in p and S["hide"][j].sum() >= 3)
    base = external_loo._nv1_fold(i, S)
    D2 = S["deltas"].copy()
    noise = np.random.default_rng(1).normal(0, 5, D2.shape)
    D2[S["hide"][i]] = noise[S["hide"][i]]            # the held-out single and every pair containing its gene
    moved = external_loo._nv1_fold(i, {**S, "deltas": D2})
    assert i not in base["train"] and not set(base["train"]) & set(np.flatnonzero(S["hide"][i]).tolist())
    for key in ("cols", "unsigned", "stack_inbundle", "external_stack"):
        assert np.array_equal(base[key], moved[key]), key
    assert base["alpha_inbundle"] == moved["alpha_inbundle"] and base["alpha_external"] == moved["alpha_external"]
    assert all(np.array_equal(a, b) for a, b in zip(base["train_cols"], moved["train_cols"]))
    # the check has teeth: an available perturbation's label does reach the fold
    D3 = S["deltas"].copy()
    D3[base["train"][0]] = noise[0]
    other = external_loo._nv1_fold(i, {**S, "deltas": D3})
    assert not np.array_equal(other["cols"][0], base["cols"][0])


def test_additive_singles_and_signed_direct_columns(case):
    bundle, external, _ = case
    S = external_loo._nv1_prepare(bundle, external)
    perts, D = bundle["perts"], S["deltas"]
    i = next(j for j, p in enumerate(perts) if "+" in p)
    a, b = S["targets_sorted"][i]
    avail = ~S["hide"][i]
    cols, unsigned, flags, _ = external_loo._nv1_columns(i, avail, S)
    assert np.array_equal(cols[2], D[perts.index(a)] + D[perts.index(b)]) and flags["additive_singles"] is None
    mr = D[avail].mean(axis=0)
    m = np.isfinite(S["ext"][i])
    assert np.array_equal(cols[0], mr)
    assert np.array_equal(cols[3], np.where(m, -S["ext"][i], mr)) and np.array_equal(unsigned, np.where(m, S["ext"][i], mr))
    # a pair whose single is not available, and a single: geneset_knn
    avail2 = avail.copy()
    avail2[perts.index(a)] = False
    cols2, _, flags2, _ = external_loo._nv1_columns(i, avail2, S)
    assert np.array_equal(cols2[2], cols2[1]) and flags2["additive_singles"] == "a single not available"
    j = perts.index(a)
    cols3, _, flags3, _ = external_loo._nv1_columns(j, ~S["hide"][j], S)
    assert np.array_equal(cols3[2], cols3[1]) and flags3["additive_singles"] == "not a pair"
    # the order targets.json lists a pair in changes nothing
    S_r = external_loo._nv1_prepare({**bundle, "targets": {**bundle["targets"], perts[i]: [b, a]}}, external)
    assert np.array_equal(external_loo._nv1_columns(i, avail, S_r)[0], cols)


def test_norman_v1_reads_a_signal_screen(report, case):
    bundle, external, _ = case
    rep = report
    n = rep["n_train"]
    assert rep["protocol"] == "norman_v1" and rep["k"] == 5 and rep["inputs_md5"] == {"public.npz": "abc"}
    assert rep["alpha_grid"] == [0.1, 1.0, 10.0, 100.0, 1e3, 1e4, 1e5, 1e6, 1e7]
    assert rep["sign"] == {"used": -1, "file": -1, "file_modality": "CRISPRi", "bundle_modality": "CRISPRa"}
    assert rep["gate"]["passed"] and rep["gate"]["singles"] == 24 and rep["gate"]["pairs"] == 16
    P = {p["name"]: p for p in rep["predictors"]}
    assert [p["name"] for p in rep["predictors"]] == external_loo.NV1_PREDICTORS + [external_loo.NV1_DIAGNOSTIC]
    # the signed direct row is the truth up to scale; with s = +1 it is anti-correlated, below the floor
    assert P["external_direct"]["mean"] > 0.9 and P["external_direct_unsigned"]["mean"] < P["mean_response"]["mean"]
    assert rep["agreement_without_targets"]["singles"]["median"] < -0.5
    # pairs: the additive rule is near the truth when both singles train
    pairs = [r for r in rep["per_perturbation"] if r["kind"] == "pair"]
    assert np.mean([r["scores"]["additive_singles"] for r in pairs]) > 0.9
    assert P["additive_singles"]["coverage"] == sum(1 for r in pairs if r["fallbacks"]["additive_singles"] is None) > 0
    # held-out singles have no in-bundle copy, so the screen carries the primary comparison
    v = rep["primary"]
    assert v["verdict"] == "ahead" and v["mean_diff"] > 2 * v["se_diff"] and v["wins"] > n / 2
    assert v == {**external_loo._paired(rep["per_perturbation"], "external_stack", "stack_inbundle"), "verdict": "ahead"}
    assert set(rep["strata"]) >= {"single", "pair", "expressed", "silent"}
    assert rep["strata"]["single"]["n"] == 24 and rep["strata"]["pair"]["n"] == 16
    for r in rep["per_perturbation"]:
        assert r["alpha_inbundle"] in external_loo.NV1_ALPHA_GRID and r["alpha_external"] in external_loo.NV1_ALPHA_GRID
        assert len(r["weights_inbundle"]) == 3 and len(r["weights_external"]) == 6
        assert set(r["scores"]) == set(r["scores_without_targets"]) == set(P)
        assert 0 <= r["target_share"] <= 1
    assert sum(rep["alphas_chosen_external"].values()) == n == sum(rep["alphas_chosen_inbundle"].values())
    md = external_loo.render(rep)
    assert md.startswith("# External screen leave-one-out, protocol norman_v1")
    assert "The external screen adds information beyond the in-bundle predictors on this check" in md
    assert "the gate holds." in md and "| external_direct_unsigned (diagnostic, s = +1) |" in md
    for phrase in ("added after", "second look", "Added after", "best"):   # no second-look text, no best-of-two
        assert phrase not in md, phrase


def test_gate_failure_is_inconclusive():
    keep = [f"G{j:03d}" for j in range(6)]           # 6 singles with a row, and the pairs of two of them
    bundle, external, _ = norman_case(n_single=16, n_pairs=10, n_genes=80, keep_rows=keep)
    rep = external_loo.analyse_norman_v1(bundle, external)
    assert not rep["gate"]["passed"] and rep["gate"]["singles_with_external_row"] == 6
    assert rep["primary"]["verdict"] == rep["primary_without_targets"]["verdict"] == "inconclusive"
    md = external_loo.render(rep)
    assert "the gate fails and the result is inconclusive" in md
    assert "Inconclusive: the gate fails, so external_stack against stack_inbundle is not read." in md
    assert "adds information beyond" not in md and "No clear difference" not in md
    # the rule: half the perturbations and 10 singles
    assert external_loo.nv1_verdict({"n": 10, "wins": 6, "losses": 4, "mean_diff": 0.1, "se_diff": 0.04}) == "ahead"
    assert external_loo.nv1_verdict({"n": 10, "wins": 5, "losses": 5, "mean_diff": 0.1, "se_diff": 0.04}) != "ahead"
    assert external_loo.nv1_verdict({"n": 10, "wins": 9, "losses": 1, "mean_diff": 0.1, "se_diff": 0.06}) != "ahead"
    assert external_loo.nv1_verdict({"n": 10, "wins": 2, "losses": 8, "mean_diff": -0.1, "se_diff": 0.01}) == "behind"


_WATCHED: list[str] = []
_OPENED: list[str] = []


def _audit(event, args):
    if event != "open" or not _WATCHED:
        return
    try:
        path = os.fsdecode(args[0]) if isinstance(args[0], (str, bytes, os.PathLike)) else None
    except Exception:
        return
    if path and any(path.startswith(w) for w in _WATCHED):
        _OPENED.append(path)


def test_cli_norman_v1_records_its_inputs_and_rerenders_byte_identical(tmp_path):
    bundle, external, control = norman_case(n_single=12, n_pairs=8, n_genes=60)
    pub = write_public(tmp_path / "norman", bundle, external, control)
    out = tmp_path / "loo.md"
    if not getattr(sys, "_external_loo_norman_audit", False):
        sys.addaudithook(_audit)
        sys._external_loo_norman_audit = True
    _OPENED.clear()
    _WATCHED[:] = [str(pub), str(pub.resolve())]
    try:
        assert external_loo.main(["--bundle", str(pub), "--knowledge", "ext_norman", "--protocol", "norman_v1",
                                  "--out", str(out)]) == 0
    finally:
        _WATCHED.clear()
    opened = {os.path.relpath(x, pub.resolve() if x.startswith(str(pub.resolve())) else pub) for x in _OPENED}
    assert "public.npz" in opened and not [x for x in opened if x.split(os.sep)[0] == "private"], sorted(opened)
    rep = json.loads(out.with_suffix(".json").read_text())
    assert rep["protocol"] == "norman_v1" and rep["n_train"] == 20 and rep["bundle"] == "norman_syn"
    assert set(rep["inputs_md5"]) == {"public.npz", "knowledge/targets.json", "knowledge/gene_sets.json",
                                      "knowledge/ext_norman.json"}
    assert rep["inputs_md5"]["public.npz"] == external_loo._md5(pub / "public.npz")
    assert rep["sign"]["file"] == -1 and rep["sign"]["bundle_modality"] == "CRISPRa" and "runtime_s" in rep
    again = tmp_path / "again.md"
    subprocess.run([sys.executable, external_loo.__file__, "--from-json", str(out.with_suffix(".json")),
                    "--out", str(again)], check=True, capture_output=True)
    assert again.read_bytes() == out.read_bytes()
    # the protocol fixes its own grid and k
    for extra in (["--alpha-grid", "1", "10"], ["--k", "3"]):
        with pytest.raises(SystemExit):
            external_loo.main(["--bundle", str(pub), "--knowledge", "ext_norman", "--protocol", "norman_v1",
                               "--out", str(tmp_path / "x.md")] + extra)
    # the default protocol on the same bundle still runs, reads the pair rows and the file's sign, records no protocol
    assert external_loo.main(["--bundle", str(pub), "--knowledge", "ext_norman", "--out", str(tmp_path / "d.md")]) == 0
    d = json.loads((tmp_path / "d.json").read_text())
    assert "protocol" not in d and d["n_multi_target"] == 8 and d["external_sign"] == -1


def test_file_sign_other_than_the_protocols_is_flagged():
    bundle, external, _ = norman_case(n_single=12, n_pairs=6, n_genes=60)
    rep = external_loo.analyse_norman_v1(bundle, {**external, "sign": 1})
    assert rep["sign"]["used"] == -1 and rep["sign"]["file"] == 1
    S = external_loo._nv1_prepare(bundle, {**external, "sign": 1})
    assert S["sign"] == -1                                       # the protocol's sign, whatever the file says
    assert "The file's sign is not the protocol's" in external_loo.render(rep)
