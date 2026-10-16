"""tools/build_gene_constraint.py and tools/build_protein_annotation.py on toy inputs with known answers."""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_gene_constraint as bgc  # noqa: E402
import build_protein_annotation as bpa  # noqa: E402

# ---- gnomAD: three rows in the real 77-column layout (only the columns read are filled) -------------------------
_GNOMAD_HEADER = ("gene transcript obs_mis exp_mis oe_mis mu_mis possible_mis obs_mis_pphen exp_mis_pphen oe_mis_pphen "
                  "possible_mis_pphen obs_syn exp_syn oe_syn mu_syn possible_syn obs_lof mu_lof possible_lof exp_lof pLI "
                  "pNull pRec oe_lof oe_syn_lower oe_syn_upper oe_mis_lower oe_mis_upper oe_lof_lower oe_lof_upper "
                  "constraint_flag syn_z mis_z lof_z oe_lof_upper_rank oe_lof_upper_bin oe_lof_upper_bin_6 n_sites "
                  "classic_caf max_af no_lofs obs_het_lof obs_hom_lof defined p exp_hom_lof classic_caf_afr "
                  "classic_caf_amr classic_caf_asj classic_caf_eas classic_caf_fin classic_caf_nfe classic_caf_oth "
                  "classic_caf_sas p_afr p_amr p_asj p_eas p_fin p_nfe p_oth p_sas transcript_type gene_id "
                  "transcript_level cds_length num_coding_exons gene_type gene_length exac_pLI exac_obs_lof exac_exp_lof "
                  "exac_oe_lof brain_expression chromosome start_position end_position").split()


def _gnomad_row(**v):
    return "\t".join(v.get(c, "NA") for c in _GNOMAD_HEADER)


def _gnomad_table(tmp: Path, gz: bool = True) -> Path:
    """CONSTR: a constrained gene; TOLER: tolerant, with a missing oe_mis_upper and a syn_outlier flag; DUP: one clean
    row and one no_exp_lof row with all values missing, as gnomAD lists 46 symbols twice."""
    rows = [
        _gnomad_row(gene="CONSTR", transcript="ENST1", oe_lof="0.1", oe_lof_lower="0.05", oe_lof_upper="0.25",
                    pLI="0.99", pNull="0.0", pRec="0.01", oe_mis="0.5", oe_mis_upper="0.6", mis_z="3.5", syn_z="0.1",
                    lof_z="6.0", obs_lof="2", exp_lof="20", oe_lof_upper_bin="0", constraint_flag=""),
        _gnomad_row(gene="TOLER", transcript="ENST2", oe_lof="1.2", oe_lof_lower="0.9", oe_lof_upper="1.6",
                    pLI="1e-10", pNull="0.9", pRec="0.1", oe_mis="1.1", oe_mis_upper="NA", mis_z="-1.0", syn_z="-4.0",
                    lof_z="-0.5", obs_lof="30", exp_lof="25", oe_lof_upper_bin="9", constraint_flag="syn_outlier"),
        _gnomad_row(gene="DUP", transcript="ENST4", constraint_flag="no_exp_lof"),
        _gnomad_row(gene="DUP", transcript="ENST3", oe_lof="0.5", oe_lof_lower="0.3", oe_lof_upper="0.8", pLI="0.2",
                    pNull="0.3", pRec="0.5", oe_mis="0.9", oe_mis_upper="1.0", mis_z="0.0", syn_z="0.0", lof_z="1.0",
                    obs_lof="5", exp_lof="10", oe_lof_upper_bin="4", constraint_flag=""),
    ]
    text = "\t".join(_GNOMAD_HEADER) + "\n" + "\n".join(rows) + "\n"
    if gz:
        path = tmp / "lof_metrics.by_gene.txt.bgz"
        with gzip.open(path, "wt") as fh:
            fh.write(text)
    else:
        path = tmp / "lof_metrics.txt"
        path.write_text(text)
    return path


def test_gene_constraint_known_values(tmp_path):
    t = bgc.build(_gnomad_table(tmp_path), None)
    col = {c: i for i, c in enumerate(t["columns"])}
    assert sorted(t["genes"]) == ["CONSTR", "DUP", "TOLER"]
    c, tol = t["genes"]["CONSTR"], t["genes"]["TOLER"]
    assert c[col["pLI"]] == 0.99 and c[col["oe_lof_upper"]] == 0.25 and c[col["obs_lof"]] == 2
    assert c[col["oe_lof_upper_bin"]] == 0 and tol[col["oe_lof_upper_bin"]] == 9
    assert tol[col["oe_mis_upper"]] is None and tol[col["pLI"]] == 0.0  # 1e-10 rounds to 0 at 6 decimals
    assert tol[col["syn_z"]] == -4.0
    assert t["flags"] == {"TOLER": "syn_outlier"}  # the flagged row is kept, and marked; clean genes are absent
    assert t["genes"]["DUP"][col["exp_lof"]] == 10 and "DUP" not in t["flags"]  # the clean duplicate wins
    assert t["source"]["n_rows"] == 4 and t["source"]["n_genes_in_table"] == 3 and len(t["source"]["sha256"]) == 64
    assert t["source"]["url"].startswith("https://gnomad-public")
    assert t["description"].startswith("gnomAD v2.1.1") and len(t["description"]) < 900
    assert "LOEUF" in t["description"] and "pLI" in t["description"] and "v19" in t["description"]


def test_gene_constraint_genes_from_and_cli(tmp_path):
    table = _gnomad_table(tmp_path, gz=False)  # plain text works too
    pub = tmp_path / "pub"
    pub.mkdir()
    np.savez(pub / "public.npz", genes=np.array(["TOLER", "DUP", "SELENOP"]))
    out = tmp_path / "gc.json"
    assert bgc.main(["--table", str(table), "--genes-from", str(pub), "--out", str(out)]) == 0
    t = json.loads(out.read_text())
    assert sorted(t["genes"]) == ["DUP", "TOLER"] and t["unmatched"] == ["SELENOP"]
    assert t["flags"] == {"TOLER": "syn_outlier"}
    # a table that is not gnomAD's: exit 2, nothing written
    bad = tmp_path / "bad.txt"
    bad.write_text("gene\ttranscript\tpLI\nX\tT\t0.5\n")
    assert bgc.main(["--table", str(bad), "--out", str(tmp_path / "no.json")]) == 2
    assert not (tmp_path / "no.json").exists()
    with pytest.raises(SystemExit) as e:  # argparse: --table and --out are required
        bgc.main(["--out", str(out)])
    assert e.value.code == 2


# ---- UniProt ---------------------------------------------------------------------------------------------------
def _uniprot_tsv(tmp: Path, header=None) -> Path:
    header = header or list(bpa.HEADERS.values())
    rows = [
        # a secreted/ER protein with a signal peptide and two membrane spans
        ["P00001", "SECR", "300", "SIGNAL 1..22; /evidence=\"ECO:0000255\"",
         "TRANSMEM 40..60; /note=\"Helical\"; /evidence=\"ECO:0000255\"; TRANSMEM 100..120; /note=\"Helical\"",
         "SUBCELLULAR LOCATION: Endoplasmic reticulum membrane; Single-pass membrane protein. Secreted.",
         "Endoplasmic reticulum;Membrane;Signal;Transmembrane"],
        # two primary gene names on one entry, a nuclear protein with neither feature
        ["P00002", "NUCA; NUCB", "150", "", "", "SUBCELLULAR LOCATION: Nucleus, nucleolus. Cytoplasm.",
         "Nucleus;Nucleotide-binding"],
        # a shorter entry for SECR: the longer one above must win
        ["P00003", "SECR", "120", "", "", "SUBCELLULAR LOCATION: Cytoplasm.", "Cytoplasm"],
        # mitochondrial protein whose signal peptide has an open end
        ["P00004", "MITO", "80", "SIGNAL 1..?", "", "SUBCELLULAR LOCATION: Mitochondrion matrix.", "Mitochondrion"],
    ]
    tmp.mkdir(exist_ok=True)
    path = tmp / "uniprot.tsv"
    path.write_text("\t".join(header) + "\n" + "\n".join("\t".join(r) for r in rows) + "\n")
    return path


def test_protein_annotation_known_values(tmp_path):
    t = bpa.build(_uniprot_tsv(tmp_path), None)
    col = {c: i for i, c in enumerate(t["columns"])}
    assert sorted(t["genes"]) == ["MITO", "NUCA", "NUCB", "SECR"]
    s = t["genes"]["SECR"]
    assert s[col["protein_length"]] == 300  # the longest of the two SECR entries
    assert s[col["has_signal_peptide"]] == 1 and s[col["signal_peptide_length"]] == 22 and s[col["n_transmembrane"]] == 2
    assert s[col["secreted"]] == s[col["membrane"]] == s[col["endoplasmic_reticulum"]] == 1
    assert s[col["nucleus"]] == s[col["cytoplasm"]] == s[col["golgi"]] == 0
    assert t["genes"]["NUCA"] == t["genes"]["NUCB"]
    n = t["genes"]["NUCA"]
    assert n[col["protein_length"]] == 150 and n[col["has_signal_peptide"]] == 0 and n[col["signal_peptide_length"]] == 0
    assert n[col["n_transmembrane"]] == 0 and n[col["nucleus"]] == 1 and n[col["cytoplasm"]] == 1
    assert n[col["membrane"]] == 0 and n[col["secreted"]] == 0
    m = t["genes"]["MITO"]
    assert m[col["has_signal_peptide"]] == 1 and m[col["signal_peptide_length"]] is None and m[col["mitochondrion"]] == 1
    assert t["source"]["n_entries"] == 4 and t["source"]["n_genes_in_table"] == 4 and len(t["source"]["sha256"]) == 64
    assert t["source"]["url"].startswith("https://rest.uniprot.org/uniprotkb/stream?")
    assert t["description"].startswith("Protein features from UniProt") and len(t["description"]) < 900


def test_parse_signal_forms():
    assert bpa.parse_signal("") == (0, 0)
    assert bpa.parse_signal("SIGNAL 1..19; /evidence=\"ECO:0000255\"") == (1, 19)
    assert bpa.parse_signal("SIGNAL 1..>30") == (1, None)
    assert bpa.parse_signal("SIGNAL <1..25") == (1, 25)


def test_protein_annotation_genes_from_and_cli(tmp_path):
    tsv = _uniprot_tsv(tmp_path)
    pub = tmp_path / "pub"
    pub.mkdir()
    np.savez(pub / "public.npz", genes=np.array(["SECR", "NUCB", "GONE"]))
    out = tmp_path / "pa.json"
    assert bpa.main(["--tsv", str(tsv), "--genes-from", str(pub), "--out", str(out)]) == 0
    t = json.loads(out.read_text())
    assert sorted(t["genes"]) == ["NUCB", "SECR"] and t["unmatched"] == ["GONE"]
    # an export with other column names (the field names are to be verified at run time): exit 2, names them
    bad = _uniprot_tsv(tmp_path / "b", header=["Entry", "Gene names", "Length", "Signal", "TM", "Location", "Keywords"])
    assert bpa.main(["--tsv", str(bad), "--out", str(tmp_path / "no.json")]) == 2
    assert not (tmp_path / "no.json").exists()
    with pytest.raises(SystemExit) as e:
        bpa.main(["--tsv", str(tsv)])
    assert e.value.code == 2
