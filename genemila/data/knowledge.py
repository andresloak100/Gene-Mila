"""Public biological prior knowledge for real datasets.

`download()` fetches curated, literature-derived resources once (network
needed; run where the hosts are reachable). `build()` filters them to a
bundle's genes and returns the knowledge files agents can read through
`ctx.knowledge(name)`:

  gene_sets            {set name: [genes]}  Reactome pathways, GO Biological Process, MSigDB Hallmark
  prior_network        [[tf, target, sign]] CollecTRI signed TF -> target regulation
  transcription_factors [genes]             regulators in CollecTRI
  ppi_network          [[a, b, score]]      STRING v12 physical interactions, score in (0, 1]

Only curated knowledge is used. Resources derived from perturbation screens
or expression atlases (e.g. Enrichr's GEO perturbation libraries, STRING's
co-expression channel) are deliberately excluded so prior knowledge cannot
encode the held-out responses.
"""

from __future__ import annotations

import gzip
import io
import json
import urllib.request
import zipfile
from pathlib import Path

SOURCES = {
    "reactome.gmt.zip": "https://reactome.org/download/current/ReactomePathways.gmt.zip",
    "go_bp.txt": "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=GO_Biological_Process_2023",
    "hallmark.txt": "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=MSigDB_Hallmark_2020",
    "collectri.tsv": "https://omnipathdb.org/interactions?datasets=collectri&genesymbols=yes&loops=yes",
    "string_physical.txt.gz":
        "https://stringdb-downloads.org/download/protein.physical.links.v12.0/9606.protein.physical.links.v12.0.txt.gz",
    "string_info.txt.gz": "https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz",
}
MIN_SET_SIZE = 3      # measured genes a gene set needs to be kept
MAX_SET_SIZE = 500
STRING_MIN_SCORE = 700  # STRING "high confidence"


def download(dest: Path, force: bool = False) -> dict:
    """Fetch every source into dest; return {file: 'ok' | 'cached' | error}. Failures do not stop the rest."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    status = {}
    for fname, url in SOURCES.items():
        path = dest / fname
        if path.exists() and path.stat().st_size > 0 and not force:
            status[fname] = "cached"
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gene-mila/0.1"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            tmp = path.with_suffix(path.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(path)
            status[fname] = "ok"
        except Exception as exc:  # report and continue with what is available
            status[fname] = f"{type(exc).__name__}: {exc}"
    (dest / "sources.json").write_text(json.dumps({"urls": SOURCES, "status": status}, indent=1))
    return status


def _gmt_lines(text: str):
    for line in text.splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        name = parts[0].strip()
        # standard GMT: name, description/id, genes...; Enrichr may append ",1.0" weights to genes
        yield name, [g.split(",")[0].strip() for g in parts[2:] if g.strip()]


def _read(path: Path) -> str | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    raw = path.read_bytes()
    if path.name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            raw = z.read(z.namelist()[0])
    elif path.name.endswith(".gz"):
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def gene_sets(src: Path, genes: set[str]) -> dict[str, list[str]]:
    out = {}
    for fname, prefix in (("reactome.gmt.zip", "REACTOME"), ("go_bp.txt", "GOBP"), ("hallmark.txt", "HALLMARK")):
        text = _read(Path(src) / fname)
        if text is None:
            continue
        for name, members in _gmt_lines(text):
            kept = sorted({g for g in members if g in genes})
            if MIN_SET_SIZE <= len(kept) <= MAX_SET_SIZE:
                out[f"{prefix}:{name}"] = kept
    return out


def collectri(src: Path, genes: set[str]) -> tuple[list[list], list[str]]:
    text = _read(Path(src) / "collectri.tsv")
    if text is None:
        return [], []
    lines = text.splitlines()
    head = lines[0].split("\t")
    col = {c: i for i, c in enumerate(head)}
    s_col = col.get("source_genesymbol", col.get("source"))
    t_col = col.get("target_genesymbol", col.get("target"))
    edges, tfs = {}, set()
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) < len(head):
            continue
        a, b = f[s_col], f[t_col]
        if a not in genes or b not in genes:
            continue
        stim = f[col["consensus_stimulation"]] == "1" if "consensus_stimulation" in col else True
        inhib = f[col["consensus_inhibition"]] == "1" if "consensus_inhibition" in col else False
        sign = -1.0 if inhib and not stim else 1.0
        edges[(a, b)] = sign
        tfs.add(a)
    return [[a, b, s] for (a, b), s in sorted(edges.items())], sorted(tfs)


def string_ppi(src: Path, genes: set[str], min_score: int = STRING_MIN_SCORE) -> list[list]:
    info, links = _read(Path(src) / "string_info.txt.gz"), _read(Path(src) / "string_physical.txt.gz")
    if info is None or links is None:
        return []
    name = {}
    for line in info.splitlines()[1:]:
        f = line.split("\t")
        if len(f) > 1:
            name[f[0]] = f[1]
    edges = {}
    for line in links.splitlines()[1:]:
        f = line.split()
        if len(f) < 3 or int(f[2]) < min_score:
            continue
        a, b = name.get(f[0]), name.get(f[1])
        if a in genes and b in genes and a != b:
            key = (a, b) if a < b else (b, a)
            edges[key] = max(edges.get(key, 0.0), int(f[2]) / 1000.0)
    return [[a, b, s] for (a, b), s in sorted(edges.items())]


def build(src: Path, genes: list[str]) -> dict[str, object]:
    """Knowledge files ({"<name>.json": content}) for a bundle, restricted to its measured genes
    (perturbation targets are always measured genes)."""
    g = set(genes)
    out: dict[str, object] = {}
    sets = gene_sets(src, g)
    if sets:
        out["gene_sets.json"] = sets
    net, tfs = collectri(src, g)
    if net:
        out["prior_network.json"] = net
        out["transcription_factors.json"] = tfs
    ppi = string_ppi(src, g)
    if ppi:
        out["ppi_network.json"] = ppi
    return out


def summary(files: dict[str, object]) -> dict[str, int]:
    return {k.removesuffix(".json"): len(v) for k, v in files.items()}
