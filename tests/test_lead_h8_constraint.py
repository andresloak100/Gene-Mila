"""docs/comparison/lead_h8_constraint: the lead's pre-registered hypothesis (PREREG_G_KNOWN_BIOLOGY family 8,
ROADMAP D4) as a feature plugin. The file passes the guard and the literal caps; on a copy of the pair bundle with a
synthetic gene_constraint table (a known linear relation to control mean plus noise) and CORUM/Reactome sets the
feature has the right shape, is zero for a perturbation whose targets have no constraint value and equals
additive_response times the hand-computed residual mean elsewhere; the Reactome word rule selects the public GMT's
ribosome, proteasome and mRNA splicing pathways and nothing else; the pipeline smoke passes; and feature_compare
reports the row as proportional to additive_response with a perturbation null."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_gene_constraint as bgc  # noqa: E402
import feature_compare as fc  # noqa: E402
from genemila.features import registry  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.guard import check_plugin_source  # noqa: E402
from task_package.literal import literal_check  # noqa: E402
from test_norman_lab import make_pair_bundle  # noqa: E402

PLUGINS = ROOT / "docs" / "comparison" / "lead_h8_constraint"
FILE = PLUGINS / "h8_constraint_residual.py"
NAME = "h8_constraint_residual"
NO_VALUE = "G23"  # a single whose gene gets no constraint value
MODULE = "genemila_plugin_h8_constraint_residual"  # the registry's module name for the plugin file


def write_h8_knowledge(bundle: Path) -> Path:
    """Add to a bundle gene_constraint in the builder's JSON shape (LOEUF a known linear function of control mean
    plus noise, null for G23 and ten non-target genes) and gene_sets with two CORUM sets, a Reactome ribosome set, a
    Reactome mRNA splicing set, two Reactome sets the word rule must not match (one of them about splicing) and a GO
    set that must be ignored."""
    z = np.load(bundle / "public.npz")
    genes = [str(g) for g in z["genes"]]
    cm = z["control_cells"].astype(np.float64).mean(axis=0)
    rng = np.random.default_rng(3)
    k = bgc.COLUMNS.index("oe_lof_upper")
    rows = {}
    for j, g in enumerate(genes):
        vals = [None] * len(bgc.COLUMNS)
        if g != NO_VALUE and not (60 <= j < 70):
            vals[k] = round(float(1.2 - 0.3 * cm[j] + 0.2 * (j % 3 == 0) + rng.normal(0, 0.05)), 6)
        rows[g] = vals
    table = {"description": "synthetic constraint", "columns": bgc.COLUMNS, "column_units": bgc.UNITS, "genes": rows,
             "flags": {}, "source": {"file": "synthetic", "sha256": "0" * 64, "url": bgc.URL, "n_rows": len(genes)}}
    kn = bundle / "knowledge"
    (kn / "gene_constraint.json").write_text(json.dumps(table))
    (kn / "gene_sets.json").write_text(json.dumps({
        "CORUM:Complex alpha": genes[0:9], "CORUM:Complex beta": genes[30:40],
        "REACTOME:Cytosolic Ribosome": genes[5:12] + genes[45:50],
        "REACTOME:mRNA Splicing - Major Pathway": genes[50:58], "REACTOME:FGFR2 alternative splicing": genes[70:76],
        "REACTOME:Signaling by WNT": genes[12:20], "GOBP:some process": genes[20:30]}))
    return bundle


@pytest.fixture(scope="module")
def h8_bundle(tmp_path_factory):
    """make_pair_bundle plus the H8 knowledge tables: the Norman-shaped case, where the parent carries
    additive_response."""
    return write_h8_knowledge(make_pair_bundle(tmp_path_factory.mktemp("h8") / "pair"))


@pytest.fixture(scope="module")
def h8_single_bundle(dataset, tmp_path_factory):
    """The synthetic single-target bundle plus the same H8 knowledge tables: the Adamson-shaped case, where the
    parent carries no additive_response column (registry.PAIR_BUILTIN_FEATURES is built in on pair bundles only)."""
    bundle = tmp_path_factory.mktemp("h8s") / "single"
    shutil.copytree(dataset, bundle)
    return write_h8_knowledge(bundle)


def _words():
    registry.load_plugins(PLUGINS)
    return sys.modules[MODULE].ESSENTIAL_WORDS


def _expected(bundle: Path) -> tuple[np.ndarray, np.ndarray]:
    """The OLS residual recomputed here, from the files, and which genes have a value."""
    words = _words()
    z = np.load(bundle / "public.npz")
    genes = [str(g) for g in z["genes"]]
    cm = z["control_cells"].astype(np.float64).mean(axis=0)
    table = json.loads((bundle / "knowledge" / "gene_constraint.json").read_text())
    sets = json.loads((bundle / "knowledge" / "gene_sets.json").read_text())
    k = table["columns"].index("oe_lof_upper")
    s = np.array([np.nan if table["genes"][g][k] is None else -table["genes"][g][k] for g in genes])
    has = np.isfinite(s)
    e = np.array([float(any(g in m for n, m in sets.items() if n.startswith("CORUM:"))) for g in genes])
    r = np.array([float(any(g in m for n, m in sets.items()
                            if n.startswith("REACTOME:") and any(w in n.lower() for w in words))) for g in genes])
    assert r[[genes.index(g) for g in sets["REACTOME:mRNA Splicing - Major Pathway"]]].all()
    decoys = sets["REACTOME:FGFR2 alternative splicing"] + sets["REACTOME:Signaling by WNT"]
    assert not r[[genes.index(g) for g in decoys]].any()
    x = np.column_stack([np.ones(len(genes)), cm, e, r])
    beta, *_ = np.linalg.lstsq(x[has], s[has], rcond=None)
    rho = np.zeros(len(genes))
    rho[has] = s[has] - x[has] @ beta
    return rho, has


def test_the_file_passes_the_guard_and_the_literal_caps(dataset, h8_bundle):
    src = FILE.read_text()
    assert check_plugin_source(src, NAME)["class_name"]
    names, pair_ids = set(), set()
    for b in (dataset, h8_bundle):
        d = fc.make_data(b)
        names |= set(d.names)
        pair_ids |= set(d.pair_ids)
    lit = literal_check(src, pair_ids, names)
    assert lit["ok"], lit["problems"]
    assert "never as GOAL_CRITERIA A.1" in src and "family 8" in src


def test_the_feature_is_additive_response_times_the_residual_mean(h8_bundle):
    registry.load_plugins(PLUGINS)
    cls = registry.get(NAME)
    assert cls.dependencies == ["additive_response"]
    ctx = FeatureContext(h8_bundle)
    perts = list(ctx.perts)
    out = cls().compute(ctx, perts, dict(cls.params))
    assert out.shape == (len(perts), ctx.n_genes, 1) and np.all(np.isfinite(out))
    rho, has = _expected(h8_bundle)
    add = ctx.feature("additive_response", perts)[:, :, 0]
    assert np.abs(add[perts.index(NO_VALUE)]).max() > 0 and np.abs(out[perts.index(NO_VALUE)]).max() == 0
    for i, p in enumerate(perts):
        idx = [ctx.gene_index[g] for g in ctx.target_genes(p) if has[ctx.gene_index[g]]]
        c = rho[idx].mean() if idx else 0.0
        assert out[i, :, 0] == pytest.approx(add[i] * c, abs=1e-12), p
    assert sum(np.abs(out[i]).max() > 0 for i in range(len(perts))) > len(perts) // 2  # not a constant feature
    # the fit is cached on the context, and a fold view (its own cache) recomputes it to the same residual
    assert "h8_residual" in ctx.cache
    view = ctx.without_train(ctx.train_perts[:3])
    assert cls().compute(view, perts[:4], dict(cls.params)).shape == (4, ctx.n_genes, 1)
    assert view.cache["h8_residual"][0] == pytest.approx(ctx.cache["h8_residual"][0])


def test_without_gene_sets_the_residual_removes_basal_expression_only(h8_bundle, tmp_path):
    bundle = tmp_path / "nosets"
    shutil.copytree(h8_bundle, bundle)
    (bundle / "knowledge" / "gene_sets.json").unlink()
    registry.load_plugins(PLUGINS)
    cls = registry.get(NAME)
    ctx = FeatureContext(bundle)
    cls().compute(ctx, ctx.perts[:2], dict(cls.params))
    rho, has = ctx.cache["h8_residual"]
    z = np.load(bundle / "public.npz")
    cm = z["control_cells"].astype(np.float64).mean(axis=0)
    assert (has == _expected(h8_bundle)[1]).all()
    x = np.column_stack([np.ones(ctx.n_genes), cm])[has]
    table = json.loads((bundle / "knowledge" / "gene_constraint.json").read_text())
    k = table["columns"].index("oe_lof_upper")
    s = np.array([-table["genes"][g][k] for g in np.array(ctx.genes)[has]])
    beta, *_ = np.linalg.lstsq(x, s, rcond=None)
    assert rho[has] == pytest.approx(s - x @ beta) and np.abs(rho[~has]).max() == 0


def test_the_word_rule_selects_the_public_reactome_sets_it_names():
    """Pathway names from the public ReactomePathways.gmt.zip (2,868 pathways, read 2026-10-17), the file
    knowledge_clean.reactome() reads. No name there contains "spliceosom": the spliceosome sets are "mRNA Splicing"."""
    words = _words()
    hit = lambda n: any(w in n.lower() for w in words)  # noqa: E731
    for name in ("GTP hydrolysis and joining of the 60S ribosomal subunit",
                 "Ribosomal scanning and start codon recognition", "Ribosome-associated quality control",
                 "Proteasome assembly",
                 "Antigen processing: Ubiquitination & Proteasome degradation", "mRNA Splicing",
                 "mRNA Splicing - Major Pathway", "mRNA Splicing - Minor Pathway"):
        assert hit(name), name
    for name in ("FGFR2 alternative splicing", "Eukaryotic Translation Elongation", "Signaling by WNT",
                 "Processing of Capped Intron-Containing Pre-mRNA"):
        assert not hit(name), name


def test_smoke_passes_on_the_bundle_with_knowledge(h8_bundle, tmp_path):
    r = subprocess.run([sys.executable, "-m", "genemila.pipeline", "smoke", "--feature", NAME, "--public",
                        str(h8_bundle), "--plugins", str(PLUGINS), "--out", str(tmp_path)],
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    res = json.loads((tmp_path / "smoke.json").read_text())
    assert res["status"] == "ok", (res["problems"], r.stderr[-500:])


def test_feature_compare_reports_a_proportional_row_with_both_nulls(h8_bundle, tmp_path):
    out = tmp_path / "out"
    assert fc.main(["--data", str(h8_bundle), "--out", str(out), "--source", f"LEAD_H8={PLUGINS}",
                    "--fold-seeds", "101,102", "--null-reps", "9"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    rows = {r["feature"]: r for r in res["rows"] if r["source"] == "LEAD_H8"}
    assert set(rows) == {NAME, "(set)"} and res["settings"]["families"]["LEAD_H8"]["add_one"] == 1
    row = rows[NAME]
    assert row["status"] == "ok", row["reason"]
    assert row["proportional"] is True and row["parent_column"] == "additive_response"
    assert row["proportional_in_folds"] is True and row["label_dependent"] is True
    pert = row["tiers"]["oof"]["null_pert"]
    assert pert is not None and pert["parent_column"] == "additive_response" and pert["reps"] == 9
    assert {"p", "p_fwer", "gains"} <= set(pert) and "coef_candidate_std" in row
    assert "null too coarse for a family of 1 (need --null-reps >= 999)" in row["failed_criteria"]


def test_on_a_singles_bundle_the_parent_column_reads_mean_response(h8_single_bundle, tmp_path):
    """On a bundle without pairs the comparison tool's parent is the three built-in features alone, so the row cannot
    name additive_response as its parent: additive_response on unique single targets is the leave-one-out mean of the
    training changes, the column mean_response, and the detector names that column. The perturbation null is still
    applied. This is the reading the README fixes for Adamson (its note of 2026-10-17)."""
    d = fc.make_data(h8_single_bundle)
    assert not d.pair_ids
    out = tmp_path / "out"
    assert fc.main(["--data", str(h8_single_bundle), "--out", str(out), "--source", f"LEAD_H8={PLUGINS}",
                    "--fold-seeds", "101,102", "--null-reps", "9"]) == 0
    res = json.loads((out / "feature_compare.json").read_text())
    row = {r["feature"]: r for r in res["rows"] if r["source"] == "LEAD_H8"}[NAME]
    assert row["status"] == "ok", row["reason"]
    assert row["proportional"] is True and row["parent_column"] == "mean_response"
    assert row["proportional_in_folds"] is True
    pert = row["tiers"]["oof"]["null_pert"]
    assert pert is not None and pert["parent_column"] == "mean_response" and pert["reps"] == 9
