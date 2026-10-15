"""tools/knowledge_coverage.py: per-target knowledge counts and the retired-symbol lookup."""
import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import knowledge_coverage as kc  # noqa: E402


def _bundle(tmp: Path) -> Path:
    """A public directory with one well-annotated target (A) and one under a retired symbol (OLD1)."""
    d = tmp / "bundle"
    (d / "knowledge").mkdir(parents=True)
    genes = ["A", "B", "C", "D", "OLD1"]
    np.savez(d / "public.npz", genes=np.array(genes), perts=np.array(["A", "OLD1"]))
    k = d / "knowledge"
    (k / "targets.json").write_text(json.dumps({"A": ["A"], "OLD1": ["OLD1"]}))
    (k / "gene_sets.json").write_text(json.dumps({"S1": ["A", "B", "C"]}))
    (k / "ppi_network.json").write_text(json.dumps([["A", "B", 0.9]]))
    (k / "prior_network.json").write_text(json.dumps([["A", "C", 1.0]]))
    (k / "screen.json").write_text(json.dumps({"description": "x", "perts": {"A": {"delta": [0.0]}}}))
    return d


def _sources(tmp: Path) -> Path:
    """Raw sources in the formats genemila.data.knowledge parses, naming the current symbol NEW1."""
    s = tmp / "sources"
    s.mkdir()
    (s / "go_bp.txt").write_text("SETX\t\tNEW1\tA\tB\n")
    (s / "collectri.tsv").write_text("source_genesymbol\ttarget_genesymbol\tconsensus_stimulation\t"
                                     "consensus_inhibition\nNEW1\tA\t1\t0\n")
    (s / "string_info.txt.gz").write_bytes(gzip.compress(b"#id\tpreferred_name\n9606.P1\tNEW1\n9606.P2\tA\n"))
    (s / "string_physical.txt.gz").write_bytes(gzip.compress(b"protein1 protein2 combined_score\n"
                                                             b"9606.P1 9606.P2 900\n"))
    return s


def test_counts_and_unannotated_target(tmp_path):
    rep = kc.coverage(_bundle(tmp_path))
    rows = {r["target"]: r for r in rep["rows"]}
    assert rows["A"] == {"target": "A", "measured": True, "gene_sets": 1, "ppi_partners": 1, "edges_out": 1,
                         "edges_in": 0, "screens": {"screen": True}, "unannotated": False}
    assert rows["OLD1"]["unannotated"] and rows["OLD1"]["screens"] == {"screen": False}
    assert rep["genes_without_set"] == 2  # D and OLD1


def test_retired_symbol_is_found_and_counted(tmp_path):
    d, s = _bundle(tmp_path), _sources(tmp_path)
    hgnc = tmp_path / "hgnc.txt"
    hgnc.write_text("hgnc_id\tsymbol\tprev_symbol\talias_symbol\nHGNC:1\tNEW1\t\"OLD1\"\t\nHGNC:2\tA\t\t\n")
    out = tmp_path / "cov.md"
    assert kc.main(["--data", str(d), "--hgnc", str(hgnc), "--sources", str(s), "--out", str(out)]) == 0
    text = out.read_text()
    assert "**OLD1**" in text and "| OLD1 | NEW1 | 1 | 1 | 1 |" in text
    assert json.loads(out.with_suffix(".json").read_text())["renames"] == {
        "OLD1": {"NEW1": {"gene_sets": 1, "edges": 1, "ppi_partners": 1}}}


def test_runs_on_a_synthetic_bundle_and_refuses_a_bad_dir(dataset, tmp_path):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "knowledge_coverage.py"), "--data", str(dataset)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.startswith("# Knowledge coverage")
    assert kc.main(["--data", str(tmp_path)]) == 2
