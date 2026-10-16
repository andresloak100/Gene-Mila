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
    rep = json.loads(out.with_suffix(".json").read_text())
    assert rep["renames"] == {"prev": {"OLD1": {"NEW1": {"gene_sets": 1, "edges": 1, "ppi_partners": 1}}},
                              "alias": {}}
    assert rep["approved_elsewhere"] == {}


def test_approved_target_that_is_another_genes_alias_gets_no_rename(tmp_path):
    """OLD1 is itself approved; NEW1 listing it as an alias must not turn NEW1's knowledge into a 'rename'."""
    d, s = _bundle(tmp_path), _sources(tmp_path)
    hgnc = tmp_path / "hgnc.txt"
    hgnc.write_text("hgnc_id\tsymbol\tprev_symbol\talias_symbol\nHGNC:1\tNEW1\t\t\"OLD1\"\n"
                    "HGNC:2\tA\t\t\nHGNC:3\tOLD1\t\t\n")
    out = tmp_path / "cov.md"
    assert kc.main(["--data", str(d), "--hgnc", str(hgnc), "--sources", str(s), "--out", str(out)]) == 0
    rep = json.loads(out.with_suffix(".json").read_text())
    assert rep["renames"] == {"prev": {}, "alias": {}}
    assert rep["approved_elsewhere"] == {"OLD1": {"alias": ["NEW1"]}}
    text = out.read_text()
    assert "| OLD1 | approved symbol; alias of NEW1 |" in text and "| OLD1 | NEW1 |" not in text


def test_previous_and_alias_symbols_are_reported_apart(tmp_path):
    hgnc = tmp_path / "hgnc.txt"
    hgnc.write_text("hgnc_id\tsymbol\tprev_symbol\talias_symbol\n"
                    "HGNC:1\tP1\t\"R1|R3\"\t\nHGNC:2\tQ1\t\t\"L1|R3\"\nHGNC:3\tAPP\t\t\n")
    h = kc.hgnc_current(hgnc)
    assert h["approved"] == {"P1", "Q1", "APP"}
    assert dict(h["prev"]) == {"R1": {"P1"}, "R3": {"P1"}} and dict(h["alias"]) == {"L1": {"Q1"}, "R3": {"Q1"}}
    rows = [{"target": t, "unannotated": True} for t in ("R1", "L1", "R3", "APP", "NONE")]
    rows.append({"target": "P1", "unannotated": False})
    renames, approved = kc.hgnc_lookup(rows, h)
    assert renames == {"prev": {"R1": {"P1": None}, "R3": {"P1": None}},
                       "alias": {"L1": {"Q1": None}, "R3": {"Q1": None}}}
    assert approved == {}
    text = kc.render({"data": "x", "n_targets": 0, "n_genes": 0, "genes_without_set": 0, "has": {}, "screens": [],
                      "rows": [], "renames": renames, "approved_elsewhere": approved})
    prev_part, alias_part = text.split("## Unannotated targets that are only an HGNC alias")
    assert "| R1 | P1 |" in prev_part and "| L1 | Q1 |" not in prev_part
    assert "| L1 | Q1 |" in alias_part and "| R1 | P1 |" not in alias_part


def test_runs_on_a_synthetic_bundle_and_refuses_a_bad_dir(dataset, tmp_path):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "knowledge_coverage.py"), "--data", str(dataset)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.startswith("# Knowledge coverage")
    assert kc.main(["--data", str(tmp_path)]) == 2
