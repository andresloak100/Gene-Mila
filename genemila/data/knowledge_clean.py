"""Tier-1-only prior knowledge: the clean bundle's sources (docs/NOVEL_FEATURE_NEEDS.md, section 7).

The policy Andres approved on 16 October 2026: a source is allowed when it was measured or derived without perturbing
genes and holds none of the expression responses the lab predicts. The loader in `knowledge.py` already excludes
perturbation screens and STRING's co-expression channel; this module goes further and admits only sources whose
annotations are curated or experimentally measured:

  gene_sets             REACTOME: pathways (the same GMT the loader uses)
                        GOBP:/GOCC:/GOMF: Gene Ontology terms from the human GAF, restricted to curated and
                        experimental evidence codes (GO_CURATED_EVIDENCE) and propagated up is_a and part_of
                        edges of go-basic.obo; Enrichr's GO BP library (no evidence codes) is not used
                        CORUM: curated protein complexes
  prior_network         CollecTRI signed TF -> target regulation (knowledge.collectri)
  transcription_factors regulators in CollecTRI
  ppi_network           STRING physical links from the experiments and database channels only
                        (string_physical_channels); the combined score, which folds in textmining and
                        co-expression, is not used

plus, when given, the three per-gene tables built by tools/build_gene_annotation.py, tools/build_gene_constraint.py and
tools/build_protein_annotation.py (gene_annotation, gene_constraint, protein_annotation), included as built.

Left out on purpose: MSigDB Hallmark (refined with expression data), Enrichr GO BP (no evidence codes, so expression-
inferred annotations cannot be told apart), GO annotations with IEP/HEP (inferred from expression), HMP/HGI (inferred
from high-throughput mutant-phenotype and genetic-interaction screens: tier 3, "derived from perturbation screens"),
IEA (electronic) and the computational-similarity codes (ISS, ISO, ISA, ISM, IGC, IBA, IBD, IKR, IRD, RCA), STRING's
textmining and co-expression channels, and every perturbation screen (the Replogle external screen stays its own arm).
IMP and IGI (single-gene mutant phenotype and genetic interaction, curated from the literature) stay: they are the
evidence class CollecTRI's regulations rest on, which Andres approved; the block G plan states this.

Every parser takes the bundle's gene universe and keeps the loader's set-size rules (MIN_SET_SIZE..MAX_SET_SIZE
measured genes). `build` returns the knowledge files like knowledge.build, and a provenance record (source sha256s,
evidence codes, STRING channels) the clean bundle's manifest stores.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .knowledge import MAX_SET_SIZE, MIN_SET_SIZE, STRING_MIN_SCORE, _gmt_lines, _read, collectri, summary  # noqa: F401

GO_CURATED_EVIDENCE = frozenset({"EXP", "IDA", "IPI", "IMP", "IGI", "HDA", "TAS", "IC", "NAS"})
GO_PREFIX = {"biological_process": "GOBP", "cellular_component": "GOCC", "molecular_function": "GOMF"}
STRING_CHANNELS = ("experiments", "database")
TABLE_NAMES = ("gene_annotation", "gene_constraint", "protein_annotation")

# file names under the sources directory (knowledge.SOURCES names are kept where the file is the same)
SOURCE_FILES = {
    "reactome.gmt.zip": "Reactome pathways GMT (https://reactome.org/download/current/ReactomePathways.gmt.zip)",
    "goa_human.gaf.gz": "GO human annotation, GAF 2.x (http://geneontology.org/gene-associations/goa_human.gaf.gz)",
    "go-basic.obo": "GO ontology, basic release (http://purl.obolibrary.org/obo/go/go-basic.obo)",
    "corum_allComplexes.txt": "CORUM allComplexes, tab-separated (https://mips.helmholtz-muenchen.de/corum/)",
    "collectri.tsv": "CollecTRI via OmniPath (knowledge.SOURCES['collectri.tsv'])",
    "string_physical_detailed.txt.gz":
        "STRING 9606.protein.physical.links.detailed.v12.0.txt.gz (https://stringdb-downloads.org/download/)",
    "string_info.txt.gz": "STRING 9606.protein.info.v12.0.txt.gz (knowledge.SOURCES['string_info.txt.gz'])",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _keep(members, genes: set[str]) -> list[str] | None:
    kept = sorted({g for g in members if g in genes})
    return kept if MIN_SET_SIZE <= len(kept) <= MAX_SET_SIZE else None


def _header_index(head: list[str], *names: str) -> int:
    """Index of the first header column whose lower-cased, '#'-stripped text equals or starts with one of names."""
    cols = [c.strip().lstrip("#").strip().lower() for c in head]
    for exact in (True, False):  # an exact name wins over a prefix ("experiments" before "experiments_transferred")
        for n in names:
            for i, c in enumerate(cols):
                if c == n or (not exact and c.startswith(n)):
                    return i
    raise ValueError(f"none of the columns {names} found in header {head}")


# ---- Reactome -------------------------------------------------------------------------------------------------
def reactome(src_dir: Path, genes: set[str]) -> dict[str, list[str]]:
    """REACTOME:<pathway> sets from reactome.gmt.zip, the loader's Reactome file."""
    text = _read(Path(src_dir) / "reactome.gmt.zip")
    out = {}
    for name, members in _gmt_lines(text or ""):
        kept = _keep(members, genes)
        if kept:
            out[f"REACTOME:{name}"] = kept
    return out


# ---- Gene Ontology --------------------------------------------------------------------------------------------
def parse_obo(text: str) -> dict[str, dict]:
    """go-basic.obo [Term] stanzas -> {id: {"id", "name", "namespace", "parents": set(is_a and part_of ids)}};
    obsolete terms are left out and alt_ids map to their term's dict, whose "id" is the primary id."""
    terms, alt = {}, {}
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if line == "[Term]":
            cur = {"name": "", "namespace": "", "parents": set(), "alt": [], "obsolete": False}
            continue
        if line.startswith("["):  # [Typedef] or another stanza
            cur = None
            continue
        if cur is None or not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if key == "id":
            cur_id = val
            terms[cur_id] = cur
        elif key == "name":
            cur["name"] = val
        elif key == "namespace":
            cur["namespace"] = val
        elif key == "alt_id":
            cur["alt"].append(val)
        elif key == "is_obsolete":
            cur["obsolete"] = val.startswith("true")
        elif key == "is_a":
            cur["parents"].add(val.split("!")[0].strip())
        elif key == "relationship" and val.startswith("part_of "):
            cur["parents"].add(val.split()[1].strip())
    out = {}
    for tid, t in terms.items():
        if t["obsolete"]:
            continue
        out[tid] = {"id": tid, "name": t["name"], "namespace": t["namespace"], "parents": t["parents"]}
        for a in t["alt"]:
            alt[a] = tid
    return {**{a: out[t] for a, t in alt.items() if t in out}, **out}


def _ancestors(tid: str, terms: dict, memo: dict) -> set[str]:
    if tid in memo:
        return memo[tid]
    memo[tid] = set()  # guards cycles
    anc = {tid}
    for p in terms.get(tid, {}).get("parents", ()):
        if p in terms:
            anc |= _ancestors(p, terms, memo)
    memo[tid] = anc
    return anc


def go_curated(gaf_path: Path, obo_path: Path, genes: set[str],
               allowed: frozenset[str] = GO_CURATED_EVIDENCE) -> dict[str, list[str]]:
    """GO sets from a GAF 2.x file (gzip ok) restricted to the allowed evidence codes, NOT qualifiers dropped,
    propagated up is_a and part_of, named GOBP:/GOCC:/GOMF:<term name> by namespace."""
    terms = parse_obo(_read(Path(obo_path)) or "")
    direct: dict[str, set[str]] = {}
    for line in (_read(Path(gaf_path)) or "").splitlines():
        if not line or line.startswith("!"):
            continue
        f = line.split("\t")
        if len(f) < 9:
            continue
        symbol, qualifier, go_id, evidence = f[2], f[3], f[4], f[6]
        if symbol not in genes or evidence not in allowed or "NOT" in qualifier.split("|"):
            continue
        go_id = terms.get(go_id, {}).get("id", go_id)  # an alt_id is the primary term
        direct.setdefault(go_id, set()).add(symbol)
    members: dict[str, set[str]] = {}
    memo: dict = {}
    for go_id, syms in direct.items():
        for anc in _ancestors(go_id, terms, memo):
            members.setdefault(anc, set()).update(syms)
    out = {}
    for go_id, syms in members.items():
        t = terms.get(go_id)
        prefix = GO_PREFIX.get(t["namespace"]) if t else None
        if prefix is None:
            continue
        kept = _keep(syms, genes)
        if kept:
            out[f"{prefix}:{t['name']}"] = kept
    return out


# ---- CORUM ----------------------------------------------------------------------------------------------------
def corum(path: Path, genes: set[str]) -> dict[str, list[str]]:
    """CORUM:<complex> sets from the allComplexes table (columns found by header, CORUM 4 'ComplexName' /
    'subunits(Gene name)' or CORUM 5 'complex_name' / 'subunits_gene_name'; ';'-separated symbols). Only Human rows
    when an organism column exists; rows with the same complex name are merged."""
    lines = (_read(Path(path)) or "").splitlines()
    if not lines:
        return {}
    head = lines[0].split("\t")
    i_name = _header_index(head, "complexname", "complex_name", "complex name")
    i_sub = _header_index(head, "subunits(gene name)", "subunits_gene_name", "subunits (gene name)")
    try:
        i_org = _header_index(head, "organism")
    except ValueError:
        i_org = None
    members: dict[str, set[str]] = {}
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) <= max(i_name, i_sub, i_org or 0):
            continue
        if i_org is not None and f[i_org].strip().lower() != "human":
            continue
        members.setdefault(f[i_name].strip(), set()).update(s.strip() for s in f[i_sub].split(";"))
    out = {}
    for name, syms in members.items():
        kept = _keep(syms, genes)
        if kept:
            out[f"CORUM:{name}"] = kept
    return out


# ---- STRING ---------------------------------------------------------------------------------------------------
def string_physical_channels(detailed_links_path: Path, info_path: Path, genes: set[str],
                             min_score: int = STRING_MIN_SCORE) -> list[list]:
    """[[a, b, s]] from protein.physical.links.detailed: an edge is kept when the experiments and database
    channels alone, combined as s = 1 - (1 - e)(1 - d) over scores/1000, reach min_score/1000; s is the recorded
    score. The textmining and co-expression channels (and the combined_score that folds them in) are excluded
    on purpose: text can carry a published response and co-expression genes that respond together."""
    info, links = _read(Path(info_path)), _read(Path(detailed_links_path))
    if info is None or links is None:
        return []
    ilines = info.splitlines()
    ihead = ilines[0].split("\t")
    i_id, i_name = _header_index(ihead, "string_protein_id", "protein_id"), _header_index(ihead, "preferred_name")
    name = {}
    for line in ilines[1:]:
        f = line.split("\t")
        if len(f) > max(i_id, i_name):
            name[f[i_id]] = f[i_name]
    llines = links.splitlines()
    head = llines[0].split()
    i_a, i_b = _header_index(head, "protein1"), _header_index(head, "protein2")
    i_e, i_d = _header_index(head, "experiments", "experimental"), _header_index(head, "database")
    threshold = min_score / 1000.0
    edges = {}
    for line in llines[1:]:
        f = line.split()
        if len(f) <= max(i_a, i_b, i_e, i_d):
            continue
        a, b = name.get(f[i_a]), name.get(f[i_b])
        if a not in genes or b not in genes or a == b:
            continue
        e, d = int(f[i_e]) / 1000.0, int(f[i_d]) / 1000.0
        s = round(1.0 - (1.0 - e) * (1.0 - d), 4)
        if s >= threshold:
            key = (a, b) if a < b else (b, a)
            edges[key] = max(edges.get(key, 0.0), s)
    return [[a, b, s] for (a, b), s in sorted(edges.items())]


# ---- the bundle's files ---------------------------------------------------------------------------------------
def build(src: Path, genes: list[str], tables: dict[str, object] | None = None,
          allowed: frozenset[str] = GO_CURATED_EVIDENCE, allow_missing: bool = False) -> tuple[dict[str, object], dict]:
    """({"<name>.json": content}, provenance) for a bundle, restricted to its measured genes. A source missing from
    src is an error (a '_clean' bundle built without GO, CORUM or STRING would be an arm no plan describes) unless
    allow_missing, when it is skipped and recorded as null in the provenance. tables: {name: parsed JSON or path to
    a built table file}, name one of TABLE_NAMES; a table's genes must all be in the bundle (the builders restrict
    them with --genes-from), so a table built for another bundle is refused."""
    src, g = Path(src), set(genes)
    missing = sorted(f for f in SOURCE_FILES if not (src / f).exists())
    if missing and not allow_missing:
        raise FileNotFoundError(f"clean sources missing from {src}: {', '.join(missing)}")
    files: dict[str, object] = {}
    sets = {**reactome(src, g),
            **go_curated(src / "goa_human.gaf.gz", src / "go-basic.obo", g, allowed),
            **corum(src / "corum_allComplexes.txt", g)}
    if sets:
        files["gene_sets.json"] = sets
    net, tfs = collectri(src, g)
    if net:
        files["prior_network.json"] = net
        files["transcription_factors.json"] = tfs
    ppi = string_physical_channels(src / "string_physical_detailed.txt.gz", src / "string_info.txt.gz", g)
    if ppi:
        files["ppi_network.json"] = ppi
    prov_tables = {}
    for name, obj in (tables or {}).items():
        name = name.removesuffix(".json")
        if name not in TABLE_NAMES:
            raise ValueError(f"unknown table {name!r}; expected one of {TABLE_NAMES}")
        if isinstance(obj, (str, Path)):
            prov_tables[name] = {"file": Path(obj).name, "sha256": _sha256(obj)}
            obj = json.loads(Path(obj).read_text())
        else:
            prov_tables[name] = {"file": None, "sha256": None}
        foreign = sorted(set(obj.get("genes", {})) - g) if isinstance(obj, dict) else []
        if foreign:
            raise ValueError(f"table {name} has {len(foreign)} genes outside the bundle (e.g. {foreign[:3]}); "
                             "it was not built for this bundle (--genes-from)")
        files[f"{name}.json"] = obj
    provenance = {
        "policy": "tier 1 only (docs/NOVEL_FEATURE_NEEDS.md section 7; approved 2026-10-16)",
        "sources": {f: (_sha256(src / f) if (src / f).exists() else None) for f in SOURCE_FILES},
        "go_evidence_codes": sorted(allowed),
        "string_channels": list(STRING_CHANNELS),
        "string_min_score": STRING_MIN_SCORE,
        "set_size": [MIN_SET_SIZE, MAX_SET_SIZE],
        "tables": prov_tables,
    }
    return files, provenance
