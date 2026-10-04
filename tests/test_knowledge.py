import gzip
import io
import zipfile

from genemila.data import knowledge


def write_sources(d):
    d.mkdir(parents=True, exist_ok=True)
    gmt = "Unfolded Protein Response\tR-HSA-381119\tATF6\tXBP1\tHSPA5\tDDIT3\tNOTMEASURED\nTiny\tR-HSA-1\tATF6\tXBP1\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ReactomePathways.gmt", gmt)
    (d / "reactome.gmt.zip").write_bytes(buf.getvalue())
    (d / "go_bp.txt").write_text("response to ER stress (GO:0034976)\t\tATF6,1.0\tXBP1,1.0\tERN1,1.0\tHSPA5,1.0\n")
    (d / "collectri.tsv").write_text(
        "source\ttarget\tsource_genesymbol\ttarget_genesymbol\tis_directed\tis_stimulation\tis_inhibition\t"
        "consensus_direction\tconsensus_stimulation\tconsensus_inhibition\n"
        "P1\tP2\tATF6\tHSPA5\t1\t1\t0\t1\t1\t0\n"
        "P1\tP3\tXBP1\tDDIT3\t1\t0\t1\t1\t0\t1\n"
        "P1\tP4\tATF6\tNOTMEASURED\t1\t1\t0\t1\t1\t0\n")
    info = "#string_protein_id\tpreferred_name\tprotein_size\nE1\tATF6\t1\nE2\tXBP1\t1\nE3\tHSPA5\t1\nE4\tERN1\t1\n"
    links = "protein1 protein2 combined_score\nE1 E2 900\nE2 E1 900\nE1 E3 650\nE2 E4 750\n"
    (d / "string_info.txt.gz").write_bytes(gzip.compress(info.encode()))
    (d / "string_physical.txt.gz").write_bytes(gzip.compress(links.encode()))


def test_build_filters_to_measured_genes(tmp_path):
    write_sources(tmp_path / "src")
    genes = ["ATF6", "XBP1", "HSPA5", "DDIT3", "ERN1", "ACTB"]
    files = knowledge.build(tmp_path / "src", genes)
    sets = files["gene_sets.json"]
    assert sets["REACTOME:Unfolded Protein Response"] == ["ATF6", "DDIT3", "HSPA5", "XBP1"]
    assert "REACTOME:Tiny" not in sets                                   # fewer than 3 measured genes
    assert sets["GOBP:response to ER stress (GO:0034976)"] == ["ATF6", "ERN1", "HSPA5", "XBP1"]
    assert files["prior_network.json"] == [["ATF6", "HSPA5", 1.0], ["XBP1", "DDIT3", -1.0]]
    assert files["transcription_factors.json"] == ["ATF6", "XBP1"]
    assert files["ppi_network.json"] == [["ATF6", "XBP1", 0.9], ["ERN1", "XBP1", 0.75]]  # 650 < 700 dropped
    assert knowledge.summary(files)["gene_sets"] == 2


def test_missing_sources_are_skipped(tmp_path):
    assert knowledge.build(tmp_path, ["ATF6"]) == {}


def test_ingest_writes_knowledge(tmp_path):
    import json
    import numpy as np
    from test_real_data_celleval import fake_screen
    from genemila.data.real import ingest_h5ad
    src = tmp_path / "src"
    src.mkdir()
    (src / "go_bp.txt").write_text("set A\t\tG1\tG2\tG3\tG4\nset B\t\tG5\tG6\n")
    out = ingest_h5ad(fake_screen(tmp_path), tmp_path / "b", "fake", n_hvg=50, knowledge_dir=src)
    sets = json.loads((out / "knowledge" / "gene_sets.json").read_text())
    assert sets == {"GOBP:set A": ["G1", "G2", "G3", "G4"]}
    m = json.loads((out / "manifest.json").read_text())
    assert m["knowledge"]["files"] == {"gene_sets": 1} and "knowledge/gene_sets.json" in m["file_sha256"]
    assert np.load(out / "public.npz")["genes"].size > 0
