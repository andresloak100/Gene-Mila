"""genemila/data/knowledge_clean.py and tools/build_clean_bundle.py on toy sources with known answers."""
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from genemila.data import knowledge_clean as kc  # noqa: E402
from genemila.data.bundle import added_knowledge, export_public, verify_bundle  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
import build_clean_bundle as bcb  # noqa: E402

OBO = """format-version: 1.2

[Term]
id: GO:0008150
name: biological_process
namespace: biological_process

[Term]
id: GO:0006950
name: response to stress
namespace: biological_process
is_a: GO:0008150 ! biological_process

[Term]
id: GO:0034976
name: response to endoplasmic reticulum stress
namespace: biological_process
is_a: GO:0006950 ! response to stress

[Term]
id: GO:0005575
name: cellular_component
namespace: cellular_component

[Term]
id: GO:0005783
name: endoplasmic reticulum
namespace: cellular_component
is_a: GO:0005575 ! cellular_component

[Term]
id: GO:0005789
name: endoplasmic reticulum membrane
namespace: cellular_component
is_a: GO:0005575 ! cellular_component
relationship: part_of GO:0005783 ! endoplasmic reticulum

[Term]
id: GO:0000001
name: gone
namespace: biological_process
is_obsolete: true

[Term]
id: GO:0099999
name: alt-bearing term
namespace: biological_process
alt_id: GO:0088888
is_a: GO:0008150 ! biological_process

[Typedef]
id: part_of
name: part of
"""


def _gaf(rows):
    head = "!gaf-version: 2.2\n"
    body = ""
    for symbol, qualifier, go, evidence, aspect in rows:
        f = ["UniProtKB", "P0", symbol, qualifier, go, "PMID:1", evidence, "", aspect, "", "", "protein", "taxon:9606",
             "20240101", "UniProt", "", ""]
        body += "\t".join(f) + "\n"
    return head + body


def write_sources(d: Path, genes_for_bundle=None):
    """Toy clean sources. With genes_for_bundle (synthetic names G0000...) the sets use those genes."""
    d.mkdir(parents=True, exist_ok=True)
    g = genes_for_bundle or ["ATF6", "XBP1", "HSPA5", "DDIT3", "ERN1", "ACTB", "TXT1", "TXT2"]
    gmt = f"Unfolded Protein Response\tR-HSA-381119\t{g[0]}\t{g[1]}\t{g[2]}\t{g[3]}\tNOTMEASURED\nTiny\tR-HSA-1\t{g[0]}\t{g[1]}\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ReactomePathways.gmt", gmt)
    (d / "reactome.gmt.zip").write_bytes(buf.getvalue())
    rows = [
        (g[0], "involved_in", "GO:0034976", "IDA", "P"),
        (g[1], "involved_in", "GO:0034976", "IMP", "P"),
        (g[4], "involved_in", "GO:0034976", "TAS", "P"),
        (g[2], "involved_in", "GO:0034976", "IEP", "P"),       # inferred from expression: dropped
        (g[3], "NOT|involved_in", "GO:0034976", "IDA", "P"),   # NOT qualifier: dropped
        (g[3], "involved_in", "GO:0006950", "IDA", "P"),       # direct on the parent only
        (g[5], "involved_in", "GO:0006950", "IEA", "P"),       # electronic: dropped
        (g[0], "located_in", "GO:0005789", "IDA", "C"),
        (g[1], "located_in", "GO:0005789", "HDA", "C"),
        (g[2], "located_in", "GO:0005783", "IDA", "C"),
        (g[5], "located_in", "GO:0000001", "IDA", "C"),        # obsolete term: ignored
        ("NOTMEASURED", "involved_in", "GO:0034976", "IDA", "P"),
    ]
    (d / "goa_human.gaf.gz").write_bytes(gzip.compress(_gaf(rows).encode()))
    (d / "go-basic.obo").write_text(OBO)
    (d / "corum_allComplexes.txt").write_text(
        "ComplexID\tComplexName\tOrganism\tsubunits(UniProt IDs)\tsubunits(Gene name)\tGO ID\n"
        f"1\tIRE1-XBP1 complex\tHuman\tP1;P2;P3\t{g[0]};{g[1]};{g[4]}\tGO:1\n"
        f"2\tDimer\tHuman\tP1;P2\t{g[0]};{g[1]}\tGO:2\n"
        f"3\tUnmeasured\tHuman\tP1;P2;P3\tNOTMEASURED;X;Y\tGO:3\n")
    (d / "collectri.tsv").write_text(
        "source\ttarget\tsource_genesymbol\ttarget_genesymbol\tis_directed\tis_stimulation\tis_inhibition\t"
        "consensus_direction\tconsensus_stimulation\tconsensus_inhibition\n"
        f"P1\tP2\t{g[0]}\t{g[2]}\t1\t1\t0\t1\t1\t0\n"
        f"P1\tP3\t{g[1]}\t{g[3]}\t1\t0\t1\t1\t0\t1\n"
        f"P1\tP4\t{g[0]}\tNOTMEASURED\t1\t1\t0\t1\t1\t0\n")
    info = ("#string_protein_id\tpreferred_name\tprotein_size\tannotation\n"
            + "".join(f"E{i}\t{s}\t1\tx\n" for i, s in enumerate(g)))
    links = ("protein1 protein2 neighborhood neighborhood_transferred fusion cooccurence homology coexpression "
             "coexpression_transferred experiments experiments_transferred database database_transferred "
             "textmining textmining_transferred combined_score\n"
             "E0 E1 0 0 0 0 0 0 0 900 0 0 0 0 0 900\n"      # experiments alone
             "E1 E0 0 0 0 0 0 0 0 900 0 0 0 0 0 900\n"
             "E0 E2 0 0 0 0 0 0 0 600 0 500 0 0 0 800\n"    # e+d: 1-(0.4)(0.5)=0.8
             "E1 E3 0 0 0 0 0 0 0 600 0 0 0 0 0 950\n"      # 600 alone, combined_score high: dropped
             "E0 E3 0 0 0 0 0 900 0 0 0 0 0 950 0 990\n"    # textmining + co-expression only: dropped
             "E0 E4 0 0 0 0 0 0 0 0 0 900 0 0 0 900\n"      # database alone
             "E0 E5 0 0 0 0 0 0 0 950 0 0 0 0 0 950\n")     # ACTB-like gene outside the universe below
    (d / "string_info.txt.gz").write_bytes(gzip.compress(info.encode()))
    (d / "string_physical_detailed.txt.gz").write_bytes(gzip.compress(links.encode()))
    return d


GENES = {"ATF6", "XBP1", "HSPA5", "DDIT3", "ERN1"}  # ACTB (g[5]) is not measured


def test_go_curated_filters_and_propagates(tmp_path):
    src = write_sources(tmp_path / "src")
    sets = kc.go_curated(src / "goa_human.gaf.gz", src / "go-basic.obo", GENES)
    # IEP (HSPA5) and NOT (DDIT3) rows dropped; ATF6, XBP1, ERN1 stay
    assert sets["GOBP:response to endoplasmic reticulum stress"] == ["ATF6", "ERN1", "XBP1"]
    # propagated up is_a: the parent gets the three plus DDIT3 (direct IDA on the parent); IEA ACTB dropped
    assert sets["GOBP:response to stress"] == ["ATF6", "DDIT3", "ERN1", "XBP1"]
    assert sets["GOBP:biological_process"] == ["ATF6", "DDIT3", "ERN1", "XBP1"]
    # part_of: ER membrane (ATF6, XBP1) propagates into ER with HSPA5 -> 3 genes kept; the membrane itself has 2
    assert sets["GOCC:endoplasmic reticulum"] == ["ATF6", "HSPA5", "XBP1"]
    assert "GOCC:endoplasmic reticulum membrane" not in sets  # below MIN_SET_SIZE
    assert not any(name.startswith("GOMF") for name in sets)
    assert "GOBP:gone" not in sets
    # a stricter code set
    strict = kc.go_curated(src / "goa_human.gaf.gz", src / "go-basic.obo", GENES, allowed=frozenset({"IDA"}))
    assert strict == {}  # no term reaches three IDA-annotated measured genes


def test_go_curated_serialization_is_stable_across_hash_seeds(tmp_path):
    src = write_sources(tmp_path / "src")
    script = ("import json, sys; from pathlib import Path; "
              "from genemila.data.knowledge_clean import go_curated; "
              "print(json.dumps(go_curated(Path(sys.argv[1]), Path(sys.argv[2]), set(json.loads(sys.argv[3])))))")
    outputs = []
    for seed in (0, 1, 42):
        env = {k: v for k, v in os.environ.items() if k not in ("API_KEY", "DEEPSEEK_API_KEY")}
        env["PYTHONHASHSEED"] = str(seed)
        result = subprocess.run([sys.executable, "-c", script, str(src / "goa_human.gaf.gz"),
                                 str(src / "go-basic.obo"), json.dumps(sorted(GENES))], cwd=ROOT,
                                env=env, capture_output=True, text=True, check=True)
        outputs.append(result.stdout)
    expected = kc.go_curated(src / "goa_human.gaf.gz", src / "go-basic.obo", GENES)
    assert all(json.loads(output) == expected for output in outputs)
    assert len(set(outputs)) == 1  # compare serialized order, not only mapping equality


def test_set_size_limits(tmp_path, monkeypatch):
    src = write_sources(tmp_path / "src")
    monkeypatch.setattr(kc, "MAX_SET_SIZE", 3)
    sets = kc.go_curated(src / "goa_human.gaf.gz", src / "go-basic.obo", GENES)
    assert "GOBP:response to stress" not in sets and "GOBP:response to endoplasmic reticulum stress" in sets
    assert kc.reactome(src, GENES) == {}  # the 4-gene pathway is above the cap, Tiny below the floor


def test_reactome_and_corum(tmp_path):
    src = write_sources(tmp_path / "src")
    assert kc.reactome(src, GENES) == {"REACTOME:Unfolded Protein Response": ["ATF6", "DDIT3", "HSPA5", "XBP1"]}
    assert kc.corum(src / "corum_allComplexes.txt", GENES) == {"CORUM:IRE1-XBP1 complex": ["ATF6", "ERN1", "XBP1"]}


def test_string_channels(tmp_path):
    src = write_sources(tmp_path / "src")
    ppi = kc.string_physical_channels(src / "string_physical_detailed.txt.gz", src / "string_info.txt.gz", GENES)
    assert ppi == [["ATF6", "ERN1", 0.9], ["ATF6", "HSPA5", 0.8], ["ATF6", "XBP1", 0.9]]
    # ATF6-DDIT3 (textmining + co-expression only, combined 990) and XBP1-DDIT3 (experiments 600) are dropped
    assert all({a, b} != {"ATF6", "DDIT3"} and {a, b} != {"XBP1", "DDIT3"} for a, b, _ in ppi)
    assert kc.string_physical_channels(src / "string_physical_detailed.txt.gz", src / "string_info.txt.gz", GENES,
                                       min_score=850) == [["ATF6", "ERN1", 0.9], ["ATF6", "XBP1", 0.9]]


@pytest.mark.parametrize("experimental_header", ["experimental", "experiments"])
@pytest.mark.parametrize("with_transferred_prefix", [False, True])
def test_string_physical_header_preserves_direct_channels(tmp_path, experimental_header, with_transferred_prefix):
    src = write_sources(tmp_path / "src")
    # The served v12 physical file has these six columns, with singular "experimental".
    head = ["protein1", "protein2", experimental_header, "database", "textmining", "combined_score"]
    rows = [["E0", "E1", "900", "0", "0", "900"],       # experiment alone
            ["E0", "E4", "0", "900", "0", "900"],       # database alone
            ["E0", "E2", "600", "500", "0", "800"],     # combined direct channels reach 0.8
            ["E0", "E3", "0", "0", "950", "990"],       # textmining alone must not pass
            ["E1", "E3", "600", "0", "0", "950"]]       # combined_score must not rescue 0.6
    if with_transferred_prefix:
        head.insert(2, "experiments_transferred")
        for row in rows:
            row.insert(2, "950")  # a prefix before the exact channel must not replace direct evidence
    links = "\n".join(" ".join(row) for row in [head, *rows]) + "\n"
    (src / "string_physical_detailed.txt.gz").write_bytes(gzip.compress(links.encode()))
    assert kc.string_physical_channels(src / "string_physical_detailed.txt.gz", src / "string_info.txt.gz", GENES) == [
        ["ATF6", "ERN1", 0.9], ["ATF6", "HSPA5", 0.8], ["ATF6", "XBP1", 0.9]]


def test_build_and_provenance(tmp_path):
    src = write_sources(tmp_path / "src")
    table = {"description": "toy table", "columns": ["x"], "genes": {"ATF6": [1]}}
    (tmp_path / "gene_constraint.json").write_text(json.dumps(table))
    files, prov = kc.build(src, sorted(GENES), {"gene_annotation": table, "gene_constraint.json": tmp_path / "gene_constraint.json"})
    assert set(files) == {"gene_sets.json", "prior_network.json", "transcription_factors.json", "ppi_network.json",
                          "gene_annotation.json", "gene_constraint.json"}
    assert files["prior_network.json"] == [["ATF6", "HSPA5", 1.0], ["XBP1", "DDIT3", -1.0]]
    assert files["transcription_factors.json"] == ["ATF6", "XBP1"]
    assert files["gene_constraint.json"] == table
    assert prov["go_evidence_codes"] == sorted(kc.GO_CURATED_EVIDENCE) and prov["string_channels"] == ["experiments", "database"]
    assert prov["sources"]["go-basic.obo"] == hashlib.sha256(OBO.encode()).hexdigest()
    assert prov["tables"]["gene_constraint"]["sha256"] and prov["tables"]["gene_annotation"]["sha256"] is None
    with pytest.raises(ValueError):
        kc.build(src, sorted(GENES), {"replogle_screen": table})
    with pytest.raises(ValueError, match="outside the bundle"):  # a table built for another bundle's gene list
        kc.build(src, sorted(GENES), {"gene_annotation": {"description": "x", "columns": ["x"], "genes": {"ATF6": [1], "G0001": [2]}}})
    (tmp_path / "empty").mkdir()
    with pytest.raises(FileNotFoundError, match="goa_human.gaf.gz"):  # an incomplete source directory is refused
        kc.build(tmp_path / "empty", sorted(GENES))
    files, prov = kc.build(tmp_path / "empty", sorted(GENES), allow_missing=True)
    assert files == {} and set(prov["sources"].values()) == {None}
    assert not {"HMP", "HGI", "IEP", "HEP", "IEA"} & kc.GO_CURATED_EVIDENCE  # screen- and expression-derived codes


def test_go_alt_id_merges_with_primary(tmp_path):
    src = write_sources(tmp_path / "src")
    rows = [("ATF6", "involved_in", "GO:0099999", "IDA", "P"), ("XBP1", "involved_in", "GO:0099999", "IDA", "P"),
            ("ERN1", "involved_in", "GO:0088888", "IDA", "P"), ("DDIT3", "involved_in", "GO:0088888", "IDA", "P")]
    (src / "goa_human.gaf.gz").write_bytes(gzip.compress(_gaf(rows).encode()))
    sets = kc.go_curated(src / "goa_human.gaf.gz", src / "go-basic.obo", GENES)
    assert sets["GOBP:alt-bearing term"] == ["ATF6", "DDIT3", "ERN1", "XBP1"]
    assert kc.parse_obo(OBO)["GO:0088888"]["id"] == "GO:0099999"


def test_corum_snake_case_header_organism_and_duplicates(tmp_path):
    f = tmp_path / "corum_allComplexes.txt"
    f.write_text("complex_id\tcomplex_name\torganism\tsynonyms\tsubunits_uniprot_id\tsubunits_gene_name\n"
                 "1\tC\tHuman\t\tP1;P2\tATF6;XBP1\n"          # merged with the next Human row of the same name
                 "2\tC\tHuman\t\tP3\tERN1\n"
                 "3\tC\tMouse\t\tP4\tDDIT3\n"                # not Human: ignored
                 "4\tM\tMouse\t\tP1;P2;P3\tATF6;XBP1;ERN1\n")  # a Mouse complex of measured-looking symbols: ignored
    assert kc.corum(f, GENES) == {"CORUM:C": ["ATF6", "ERN1", "XBP1"]}
    g = tmp_path / "no_organism.txt"
    g.write_text("ComplexName\tsubunits(Gene name)\nC\tATF6;XBP1;ERN1\n")
    assert kc.corum(g, GENES) == {"CORUM:C": ["ATF6", "ERN1", "XBP1"]}


def test_added_knowledge_file_is_recorded_as_dropped(tmp_path, dataset):
    import shutil
    import numpy as np
    bundle = tmp_path / "bundle"
    shutil.copytree(dataset, bundle)
    (bundle / "knowledge" / "replogle2022_k562.json").write_text(json.dumps({"description": "a screen", "genes": {}}))
    genes = [str(g) for g in np.load(bundle / "public.npz", allow_pickle=False)["genes"]]
    src = write_sources(tmp_path / "src", genes_for_bundle=genes[:8])
    out = bcb.build_clean_bundle(bundle, src, tmp_path / "clean")
    m = json.loads((out / "manifest.json").read_text())
    assert "replogle2022_k562.json" in m["clean_knowledge"]["excluded_files"]
    assert not (out / "knowledge" / "replogle2022_k562.json").exists() and added_knowledge(out) == []


def _tree(d: Path) -> dict:
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}


@pytest.mark.parametrize("with_table", [False, True])
def test_bundle_round_trip(tmp_path, dataset, with_table):
    import numpy as np
    genes = [str(g) for g in np.load(dataset / "public.npz", allow_pickle=False)["genes"]]
    src = write_sources(tmp_path / "src", genes_for_bundle=genes[:8])
    before = _tree(dataset)
    original = json.loads((dataset / "manifest.json").read_text())
    out = tmp_path / "clean"
    argv = ["--bundle", str(dataset), "--sources", str(src), "--out", str(out)]
    if with_table:
        table = {"description": "toy per-gene table", "columns": ["x"], "genes": {g: [i] for i, g in enumerate(genes)}}
        (tmp_path / "ga.json").write_text(json.dumps(table))
        argv += ["--table", f"gene_annotation={tmp_path / 'ga.json'}"]
    else:
        argv += ["--no-tables"]
    assert bcb.main(argv) == 0
    assert _tree(dataset) == before                       # the input bundle is untouched
    assert verify_bundle(out) == [] and added_knowledge(out) == []
    m = json.loads((out / "manifest.json").read_text())
    assert m["split_id"] == original["split_id"] and m["n_perturbations"] == original["n_perturbations"]
    assert m["name"] == "synthetic_clean_tables" if with_table else m["name"] == "synthetic_clean"
    assert m["clean_knowledge"]["excluded_files"] == []   # the synthetic files keep their names, replaced in content
    assert set(m["file_sha256"]) >= {"public.npz", "splits.json", "knowledge/targets.json", "private/val1.npz"}
    for rel in ("public.npz", "splits.json", "knowledge/targets.json"):
        assert m["file_sha256"][rel] == original["file_sha256"][rel]
    ctx = FeatureContext(export_public(out, tmp_path / "pub"))
    sets = ctx.knowledge("gene_sets")
    assert sets["REACTOME:Unfolded Protein Response"] == sorted(genes[:4])
    assert sets["CORUM:IRE1-XBP1 complex"] == sorted([genes[0], genes[1], genes[4]])
    assert not any(n.startswith("MODULE_") for n in sets)  # the synthetic generator's sets are gone
    assert ctx.knowledge("ppi_network") == [[genes[0], genes[1], 0.9], [genes[0], genes[2], 0.8],
                                            [genes[0], genes[4], 0.9], [genes[0], genes[5], 0.95]]
    assert ctx.knowledge("prior_network") == [[genes[0], genes[2], 1.0], [genes[1], genes[3], -1.0]]
    assert (ctx.knowledge("gene_annotation") is not None) is with_table
    assert m["clean_knowledge"]["tables"] == (["gene_annotation"] if with_table else [])
    with pytest.raises(FileExistsError):
        bcb.main(argv)


def test_bundle_with_similarity_files_and_its_own_name(tmp_path, dataset):
    """The paralog and protein-similarity edge files go in like the tables, are checked by their endpoints, round-trip
    through export_public, and the bundle takes the --name the operator gives it (the results table groups by it)."""
    import numpy as np
    genes = [str(g) for g in np.load(dataset / "public.npz", allow_pickle=False)["genes"]]
    src = write_sources(tmp_path / "src", genes_for_bundle=genes[:8])
    edges = {"description": "toy paralog pairs", "columns": ["gene_a", "gene_b", "identity_a", "identity_b", "lca", "t"],
             "edges": [[genes[0], genes[1], 0.9, 0.8, "Homo sapiens", "within_species_paralog"]], "source": {"x": 1}}
    sim = {"description": "toy similarity", "columns": ["gene_a", "gene_b", "cosine"],
           "edges": [[genes[2], genes[3], 0.7]], "source": {}}
    table = {"description": "toy paralog table", "columns": ["n_paralogs"], "genes": {g: [0] for g in genes}}
    for name, obj in (("paralogs", edges), ("protein_similarity", sim), ("paralog_annotation", table)):
        (tmp_path / f"{name}.json").write_text(json.dumps(obj))
    out = tmp_path / "clean_sim"
    argv = ["--bundle", str(dataset), "--sources", str(src), "--out", str(out), "--name", "synthetic_clean_similarity",
            "--table", str(tmp_path / "paralogs.json"), "--table", str(tmp_path / "protein_similarity.json"),
            "--table", f"paralog_annotation={tmp_path / 'paralog_annotation.json'}"]
    assert bcb.main(argv) == 0
    assert verify_bundle(out) == [] and added_knowledge(out) == []
    m = json.loads((out / "manifest.json").read_text())
    assert m["name"] == "synthetic_clean_similarity"
    assert m["clean_knowledge"]["tables"] == ["paralog_annotation", "paralogs", "protein_similarity"]
    assert m["clean_knowledge"]["provenance"]["tables"]["paralogs"]["sha256"]
    ctx = FeatureContext(export_public(out, tmp_path / "pub_sim"))
    assert ctx.knowledge("paralogs") == edges and ctx.knowledge("protein_similarity") == sim
    assert bcb._genes_covered(edges) == 2 and bcb._entries(edges) == 1
    # an edge file whose endpoint is not a measured gene is refused before anything is written
    foreign = {**sim, "edges": [[genes[2], "NOTMEASURED", 0.7]]}
    (tmp_path / "protein_similarity.json").write_text(json.dumps(foreign))
    with pytest.raises(ValueError, match="outside the bundle"):
        bcb.main(["--bundle", str(dataset), "--sources", str(src), "--out", str(tmp_path / "clean_bad"),
                  "--table", str(tmp_path / "protein_similarity.json")])
    assert not (tmp_path / "clean_bad").exists()


def test_cli_aliases_and_warning(tmp_path, dataset, capsys):
    """The names docs/mac/block_g uses (--from/--raw/--knowledge PATH) work, and an oversized summary warns."""
    import numpy as np
    genes = [str(g) for g in np.load(dataset / "public.npz", allow_pickle=False)["genes"]]
    src = write_sources(tmp_path / "src", genes_for_bundle=genes[:8])
    table = {"description": "x" * 900, "columns": ["x"], "genes": {g: [i] for i, g in enumerate(genes)}}
    paths = []
    for name in kc.TABLE_NAMES:
        (tmp_path / f"{name}.json").write_text(json.dumps(table))
        paths += ["--knowledge", str(tmp_path / f"{name}.json")]
    assert bcb.main(["--from", str(dataset), "--raw", str(src), "--out", str(tmp_path / "clean"), *paths]) == 0
    m = json.loads((tmp_path / "clean" / "manifest.json").read_text())
    assert m["clean_knowledge"]["tables"] == sorted(kc.TABLE_NAMES) and m["name"] == "synthetic_clean_tables"
    text = capsys.readouterr().out
    lines = bcb.knowledge_summary_lines(tmp_path / "clean")
    assert ("WARNING" in text) == (len("; ".join(lines)) > bcb.planner_knowledge_limit())
    with pytest.raises(FileNotFoundError):
        bcb.main(["--bundle", str(dataset), "--sources", str(tmp_path / "nothing"), "--out", str(tmp_path / "c2")])
    assert not (tmp_path / "c2").exists()
