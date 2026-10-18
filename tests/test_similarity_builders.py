"""tools/build_paralogs.py and tools/build_protein_similarity.py on toy inputs with known answers, and the clean
bundle assembler's checks on their files."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_paralogs as bp  # noqa: E402
import build_protein_similarity as bps  # noqa: E402
from genemila.data import knowledge_clean as kc  # noqa: E402

BUNDLE = ["ACTB", "ACTG1", "HBG1", "HBG2", "KLF1", "LONE", "RETIRED"]


def _public(tmp: Path, genes=BUNDLE) -> Path:
    d = tmp / "bundle"
    d.mkdir(exist_ok=True)
    np.savez(d / "public.npz", genes=np.array(genes))
    return d


# ---- paralogs: a BioMart export with display headers ---------------------------------------------------------------
_DISPLAY = ["Gene stable ID", "Gene name", "Human paralogue gene stable ID", "Human paralogue associated gene name",
            "Paralogue %id. target Human gene identical to query gene",
            "Paralogue %id. query gene identical to target Human gene", "Paralogue last common ancestor with Human",
            "Paralogue homology type"]
_INTERNAL = ["ensembl_gene_id", "external_gene_name", "hsapiens_paralog_ensembl_gene",
             "hsapiens_paralog_associated_gene_name", "hsapiens_paralog_perc_id", "hsapiens_paralog_perc_id_r1",
             "hsapiens_paralog_subtype", "hsapiens_paralog_orthology_type"]
_ROWS = [
    # gene, paralogue, %id target identical to query, %id query identical to target, lca, type
    ("ENSG1", "ACTB", "ENSG2", "ACTG1", "98.9", "98.7", "Bilateria", "within_species_paralog"),
    ("ENSG2", "ACTG1", "ENSG1", "ACTB", "98.7", "98.9", "Bilateria", "within_species_paralog"),   # the reverse row
    ("ENSG1", "ACTB", "ENSG9", "ACTA1", "93.0", "92.5", "Bilateria", "within_species_paralog"),  # ACTA1 not measured
    ("ENSG3", "HBG1", "ENSG4", "HBG2", "99.3", "99.3", "Homo sapiens", "within_species_paralog"),
    ("ENSG4", "HBG2", "ENSG3", "HBG1", "99.3", "99.3", "Homo sapiens", "within_species_paralog"),
    ("ENSG3", "HBG1", "ENSG8", "HBB", "73.5", "73.5", "Amniota", "other_paralog"),
    ("ENSG3", "HBG1", "ENSG7", "", "60.0", "55.0", "Amniota", "within_species_paralog"),         # unnamed paralogue
    ("ENSG5", "KLF1", "ENSG6", "KLF2", "45.2", "40.1", "Euteleostomi", "within_species_paralog"),
    ("ENSG5", "KLF1", "ENSG5b", "KLF1-AS", "10.0", "10.0", "Homo sapiens", "gene_split"),          # skipped
    ("ENSG6", "LONE", "", "", "", "", "", ""),                                                   # no paralogue
]


def _export(tmp: Path, header=_DISPLAY, rows=_ROWS) -> Path:
    path = tmp / "paralogues.tsv"
    path.write_text("\t".join(header) + "\n" + "".join("\t".join(r) + "\n" for r in rows))
    return path


def test_paralogs_known_values(tmp_path):
    edge_file, table = bp.build(_export(tmp_path), set(BUNDLE), "115")
    assert edge_file["columns"] == bp.EDGE_COLUMNS and table["columns"] == bp.TABLE_COLUMNS
    # each measured pair once, gene_a < gene_b, identity_a the fraction of gene_a's protein identical to gene_b's
    assert edge_file["edges"] == [["ACTB", "ACTG1", 0.987, 0.989, "Bilateria", "within_species_paralog"],
                                  ["HBG1", "HBG2", 0.993, 0.993, "Homo sapiens", "within_species_paralog"]]
    col = {c: i for i, c in enumerate(table["columns"])}
    g = table["genes"]
    assert sorted(g) == ["ACTB", "ACTG1", "HBG1", "HBG2", "KLF1", "LONE"]
    assert g["ACTB"][col["n_paralogs"]] == 2 and g["ACTB"][col["n_paralogs_measured"]] == 1
    assert g["ACTB"][col["max_identity"]] == 0.987 and g["ACTB"][col["max_identity_measured"]] == 0.987
    assert g["HBG1"][col["n_paralogs"]] == 3                       # HBG2, HBB and the unnamed one; not the measured-only
    assert g["HBG1"][col["n_within_species_paralogs"]] == 2         # HBB is other_paralog
    assert g["HBG1"][col["n_paralogs_measured"]] == 1 and g["HBG1"][col["max_identity_measured"]] == 0.993
    assert g["KLF1"] == [1, 1, 0.401, 0, 0.0]                       # KLF2 unmeasured; the gene_split row skipped
    assert g["LONE"] == [0, 0, 0.0, 0, 0.0]                         # in the export, no paralogue: zeros, not unmatched
    assert edge_file["unmatched"] == table["unmatched"] == ["RETIRED"]
    src = edge_file["source"]
    assert src["ensembl_release"] == "115" and src["n_gene_split_rows_skipped"] == 1 and src["n_rows"] == 10
    assert src["n_genes_in_export"] == 6 and len(src["sha256"]) == 64
    assert "paralog" in edge_file["description"].lower() and len(edge_file["description"]) < 900
    assert "NaN" not in json.dumps([edge_file, table], allow_nan=False)


def test_paralogs_headers_and_cli(tmp_path, capsys):
    # biomaRt's internal names are accepted; a header lacking a required column is refused and named
    edge_file, _ = bp.build(_export(tmp_path, header=_INTERNAL), set(BUNDLE), "115")
    assert len(edge_file["edges"]) == 2
    bad = tmp_path / "bad.tsv"
    bad.write_text("Gene name\tHuman paralogue associated gene name\nACTB\tACTG1\n")
    with pytest.raises(ValueError, match="pid_target"):
        bp.build(bad, set(BUNDLE), "115")
    pub = _public(tmp_path)
    rc = bp.main(["--tsv", str(_export(tmp_path)), "--release", "115", "--genes-from", str(pub),
                  "--out", str(tmp_path / "paralogs.json"), "--table-out", str(tmp_path / "paralog_annotation.json")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "2 paralog pairs among 6 matched genes" in out and "1 bundle genes unmatched" in out
    written = json.loads((tmp_path / "paralogs.json").read_text())
    assert written["edges"][0][:2] == ["ACTB", "ACTG1"]
    assert json.loads((tmp_path / "paralog_annotation.json").read_text())["genes"]["LONE"][0] == 0
    assert bp.main(["--tsv", str(bad), "--release", "115", "--genes-from", str(pub), "--out", str(tmp_path / "x")]) == 2


# ---- protein similarity: a tiny embedding file and the UniProt TSV ------------------------------------------------
_TSV_HEADER = "Entry\tGene Names (primary)\tLength\n"


def _uniprot(tmp: Path, header=_TSV_HEADER) -> Path:
    path = tmp / "uniprot.tsv"
    path.write_text(header
                    + "P1\tACTB\t375\n"
                    + "P2\tACTG1\t375\n"
                    + "P3\tHBG1\t147\n"
                    + "P4\tHBG2\t147\n"
                    + "P5\tKLF1\t362\n"
                    + "P5b\tKLF1\t400\n"      # longer, but no embedding: P5 stands for KLF1
                    + "P6\tLONE; ALIAS1\t100\n"
                    + "P7\tUNMEASURED\t50\n")
    return path


def _h5(tmp: Path, vectors: dict) -> Path:
    import h5py
    path = tmp / "per-protein.h5"
    with h5py.File(path, "w") as fh:
        for acc, v in vectors.items():
            fh.create_dataset(acc, data=np.asarray(v, dtype=np.float32))
    return path


_VECTORS = {"P1": [1, 0, 0, 0], "P2": [0.9, 0.1, 0, 0], "P3": [0, 1, 0, 0], "P4": [0, 0.95, 0.05, 0],
            "P5": [0, 0, 1, 0], "P6": [0, 0, 0, 1], "P7": [1, 1, 1, 1]}


def test_protein_similarity_known_values(tmp_path):
    edge_file, table = bps.build(_h5(tmp_path, _VECTORS), _uniprot(tmp_path), set(BUNDLE), "2025_04", k=1,
                                 n_components=2)
    assert edge_file["columns"] == bps.EDGE_COLUMNS
    # k=1: ACTB<->ACTG1 and HBG1<->HBG2 are mutual; KLF1's and LONE's nearest neighbours add two more pairs
    pairs = {(a, b): c for a, b, c in edge_file["edges"]}
    assert pairs[("ACTB", "ACTG1")] == round(0.9 / np.sqrt(0.82), 4) and pairs[("HBG1", "HBG2")] == round(0.95 / np.sqrt(0.9050), 4)
    assert all(a < b for a, b in pairs) and len(pairs) == 4
    assert ("HBG2", "KLF1") in pairs and pairs[("HBG2", "KLF1")] == round(0.05 / np.sqrt(0.9050), 4)
    assert edge_file["unmatched"] == table["unmatched"] == ["RETIRED"]
    src = edge_file["source"]
    assert src["accessions"]["KLF1"] == "P5" and src["accessions"]["LONE"] == "P6"   # the longest WITH an embedding
    assert src["n_embeddings_in_file"] == 7 and src["dimension"] == 4 and src["k"] == 1
    assert src["n_genes_with_embedding"] == 6 and src["uniprot_release"] == "2025_04"
    assert table["columns"] == ["pc1", "pc2"] and sorted(table["genes"]) == sorted(src["accessions"])
    assert len(table["source"]["explained_variance"]) == 2 and sum(table["source"]["explained_variance"]) <= 1.0001
    assert all(len(v) == 2 for v in table["genes"].values())
    assert "sequence" in edge_file["description"] and len(edge_file["description"]) < 900
    assert "NaN" not in json.dumps([edge_file, table], allow_nan=False)


def test_protein_similarity_refusals_and_cli(tmp_path, capsys):
    h5, tsv = _h5(tmp_path, _VECTORS), _uniprot(tmp_path)
    (tmp_path / "x").mkdir()
    (tmp_path / "r").mkdir()
    with pytest.raises(ValueError, match="Length"):
        bps.build(h5, _uniprot(tmp_path / "x", header="Entry\tGene Names (primary)\n"), set(BUNDLE), "r")
    ragged = _h5(tmp_path / "r", {"P1": [1, 0], "P2": [1, 0, 0]})
    with pytest.raises(ValueError, match="not a vector"):
        bps.build(ragged, tsv, set(BUNDLE), "r")
    pub = _public(tmp_path)
    rc = bps.main(["--h5", str(h5), "--tsv", str(tsv), "--release", "2025_04", "--genes-from", str(pub), "--k", "2",
                   "--out", str(tmp_path / "protein_similarity.json")])
    assert rc == 0
    assert "1 bundle genes unmatched" in capsys.readouterr().out
    written = json.loads((tmp_path / "protein_similarity.json").read_text())
    assert written["source"]["k"] == 2 and all(len(e) == 3 for e in written["edges"])
    assert {x for e in written["edges"] for x in e[:2]} <= set(BUNDLE)
    assert bps.main(["--h5", str(ragged), "--tsv", str(tsv), "--release", "r", "--genes-from", str(pub),
                     "--out", str(tmp_path / "y")]) == 2


# ---- the clean bundle assembler accepts the files and checks their genes ------------------------------------------
def test_knowledge_clean_accepts_edge_files_and_checks_endpoints(tmp_path):
    edge_file, table = bp.build(_export(tmp_path), set(BUNDLE), "115")
    (tmp_path / "paralogs.json").write_text(json.dumps(edge_file))
    src = tmp_path / "src"
    src.mkdir()
    files, prov = kc.build(src, BUNDLE, {"paralogs": tmp_path / "paralogs.json", "paralog_annotation": table},
                           allow_missing=True)
    assert files["paralogs.json"] == edge_file and files["paralog_annotation.json"] == table
    assert prov["tables"]["paralogs"]["sha256"] and prov["tables"]["paralog_annotation"]["sha256"] is None
    foreign = {**edge_file, "edges": edge_file["edges"] + [["ACTB", "NOTMEASURED", 0.5, 0.5, "x", "y"]]}
    with pytest.raises(ValueError, match="outside the bundle"):
        kc.build(src, BUNDLE, {"protein_similarity": foreign}, allow_missing=True)
    with pytest.raises(ValueError, match="edges"):
        kc.build(src, BUNDLE, {"protein_similarity": [["ACTB", "ACTG1", 0.5]]}, allow_missing=True)
    with pytest.raises(ValueError, match="unknown table"):
        kc.build(src, BUNDLE, {"sequence_similarity": edge_file}, allow_missing=True)
