#!/usr/bin/env python3
"""Write a tier-1-only ("clean") copy of a bundle: the same data, split and labels, with knowledge/ rebuilt from the
clean sources (genemila/data/knowledge_clean.py) and, optionally, the three per-gene tables.

    python tools/build_clean_bundle.py --bundle data/norman --sources data/knowledge_clean_src --out data/norman_clean
    python tools/build_clean_bundle.py --bundle data/norman --sources data/knowledge_clean_src \\
        --out data/norman_clean_tables --table gene_annotation=gene_annotation_norman.json \\
        --table gene_constraint=gene_constraint_norman.json --table protein_annotation=protein_annotation_norman.json
    python tools/build_clean_bundle.py --bundle data/norman --sources data/knowledge_clean_src \
        --out data/norman_clean_tables_similarity --name norman_clean_tables_similarity --table ... \
        --table paralogs=paralogs_norman.json --table paralog_annotation=paralog_annotation_norman.json \
        --table protein_similarity=protein_similarity_norman.json

(--from, --raw and --knowledge PATH are aliases of --bundle, --sources and --table, the names docs/mac/block_g uses;
a --table without NAME= takes the file's stem. --table also takes the similarity edge files of
tools/build_paralogs.py and tools/build_protein_similarity.py, knowledge_clean.NETWORK_NAMES, checked by their
endpoints. --name sets the manifest name; the results table groups runs by it, so a bundle whose knowledge differs
from block G's two bundles must not reuse their names.) Every file in knowledge_clean.SOURCE_FILES must be present under
--sources, or the tool refuses (--allow-missing skips absent ones, for local experiments). A table whose genes are not
all in the bundle is refused. The output directory must not exist. public.npz, private/* (copied as bytes, never read), splits.json and
knowledge/targets.json are copied byte for byte; the other knowledge files are replaced. manifest.json is the input's
manifest with the name '<name>_clean' (or '<name>_clean_tables' when tables are included), the same split_id and
counts, knowledge_files and file_sha256 recomputed, and a 'clean_knowledge' entry holding the provenance record
(source sha256s, GO evidence codes, STRING channels, table files) and the knowledge files the input had that the
clean bundle drops. The tool verifies the result (verify_bundle, added_knowledge == [], export_public + FeatureContext)
and asserts the input bundle is byte-identical to before. It prints one line per knowledge file and the planner's
knowledge-summary lines (genemila.lab.Lab.knowledge_summary) so the operator can see the planner section's size, with a
WARNING line when that size exceeds the planner's knowledge-section limit (genemila/research_state.py).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from genemila.data import knowledge_clean  # noqa: E402
from genemila.data.bundle import added_knowledge, export_public, sha256_file, verify_bundle  # noqa: E402

COPIED = ("public.npz", "splits.json", "knowledge/targets.json")


def _hash_tree(d: Path) -> dict[str, str]:
    return {str(p.relative_to(d)): sha256_file(p) for p in sorted(d.rglob("*")) if p.is_file()}


def knowledge_summary_lines(public_dir: Path) -> list[str]:
    """The lines genemila.lab.Lab.knowledge_summary joins with '; ' (copied from it; the planner reads them)."""
    parts = []
    for p in sorted((public_dir / "knowledge").glob("*.json")):
        obj = json.loads(p.read_text())
        if isinstance(obj, dict) and isinstance(obj.get("description"), str):
            parts.append(f"{p.stem}: {obj['description'][:900]} (a dict with keys {', '.join(map(str, obj))})")
        elif isinstance(obj, dict):
            k = next(iter(obj), None)
            parts.append(f"{p.stem}: dict of {len(obj)} entries, e.g. {k!r}: {str(obj[k])[:60]}")
        else:
            parts.append(f"{p.stem}: list of {len(obj)}, e.g. {str(obj[0])[:60] if obj else ''}")
    return parts


def _entries(content) -> int:
    """How many entries a knowledge file holds: edges for a self-describing edge file, else its length."""
    if isinstance(content, dict) and isinstance(content.get("edges"), list):
        return len(content["edges"])
    return len(content)


def _genes_covered(content) -> int:
    if isinstance(content, dict) and "genes" in content and isinstance(content["genes"], dict):
        return len(content["genes"])  # a per-gene table
    if isinstance(content, dict) and isinstance(content.get("edges"), list):
        return len({x for e in content["edges"] for x in e[:2]})  # a self-describing edge file
    if isinstance(content, dict):
        return len({g for members in content.values() for g in members})
    if content and isinstance(content[0], list):
        return len({x for row in content for x in row[:2]})
    return len(content)


def planner_knowledge_limit() -> int:
    """Characters the planner state gives the knowledge section (genemila/research_state.py)."""
    from genemila import research_state
    return getattr(research_state, "KNOWLEDGE_SECTION_CHARS", research_state.SECTION_CHARS)


def build_clean_bundle(bundle: Path, sources: Path, out: Path, tables: dict[str, Path] | None = None,
                       allow_missing: bool = False, name: str | None = None) -> Path:
    bundle, sources, out = Path(bundle), Path(sources), Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; a clean bundle is written to a new directory, never over one")
    before = _hash_tree(bundle)
    manifest = json.loads((bundle / "manifest.json").read_text())
    genes = [str(g) for g in np.load(bundle / "public.npz", allow_pickle=False)["genes"]]
    files, provenance = knowledge_clean.build(sources, genes, tables, allow_missing=allow_missing)

    (out / "private").mkdir(parents=True)
    (out / "knowledge").mkdir()
    for rel in COPIED:
        shutil.copyfile(bundle / rel, out / rel)
    for p in sorted((bundle / "private").iterdir()):
        if p.is_file():
            shutil.copyfile(p, out / "private" / p.name)  # bytes only
    for fname, content in files.items():
        with open(out / "knowledge" / fname, "w") as fh:
            json.dump(content, fh)

    # what the input's knowledge/ holds, not only what its manifest lists: a file added after the build (the
    # Replogle screen, tools/build_external_screen.py) is dropped too and must be recorded as dropped
    old_knowledge = [p.name for p in (bundle / "knowledge").iterdir() if p.is_file() and p.name != "targets.json"]
    hashed = {rel for rel in manifest["file_sha256"] if not rel.startswith("knowledge/")} | set(COPIED)
    hashed |= {f"knowledge/{f}" for f in files}
    new = dict(manifest)
    # the results table groups runs by this name, so a bundle with other knowledge files is named apart (--name)
    new["name"] = name or (f"{manifest['name']}_clean_tables" if tables else f"{manifest['name']}_clean")
    new["knowledge_files"] = sorted(p.name for p in (out / "knowledge").iterdir())
    new["file_sha256"] = {rel: sha256_file(out / rel) for rel in sorted(hashed)}
    if isinstance(new.get("knowledge"), dict):  # the real ingest's summary of the knowledge it wrote
        new["knowledge"] = {"source_dir": str(sources), "files": knowledge_clean.summary(files)}
    new["clean_knowledge"] = {"from_bundle": manifest["name"], "sources_dir": str(sources), "provenance": provenance,
                              "excluded_files": sorted(set(old_knowledge) - set(files)),
                              "tables": sorted(k.removesuffix(".json") for k in (tables or {}))}
    with open(out / "manifest.json", "w") as fh:
        json.dump(new, fh, indent=1)

    problems = verify_bundle(out)
    if problems:
        raise RuntimeError(f"the clean bundle does not verify: {problems}")
    if new["split_id"] != manifest["split_id"] or added_knowledge(out):
        raise RuntimeError("split_id changed or knowledge files are missing from the manifest")
    from genemila.features.api import FeatureContext
    with tempfile.TemporaryDirectory() as tmp:
        ctx = FeatureContext(export_public(out, Path(tmp)))
        for fname, content in files.items():
            if ctx.knowledge(fname.removesuffix(".json")) != json.loads(json.dumps(content)):
                raise RuntimeError(f"{fname} does not round-trip through export_public")
    after = _hash_tree(bundle)
    if after != before:
        raise RuntimeError("the input bundle changed while the clean bundle was written; it must stay byte-identical")

    print(f"{new['name']}: {out} (split {new['split_id']}, {len(genes)} genes); "
          f"dropped {', '.join(new['clean_knowledge']['excluded_files']) or 'nothing'}")
    for fname, content in files.items():
        print(f"  {fname}: {_entries(content)} entries, {_genes_covered(content)} genes covered")
    missing = [f for f, h in provenance["sources"].items() if h is None]
    if missing:
        print(f"  sources missing from {sources}: {', '.join(missing)}")
    lines = knowledge_summary_lines(out)
    total, limit = len("; ".join(lines)), planner_knowledge_limit()
    print(f"planner knowledge summary: {total} characters in {len(lines)} lines (planner section limit {limit})")
    for line in lines:
        print(f"  {len(line):5d}  {line[:100]}{'...' if len(line) > 100 else ''}")
    if total > limit:
        print(f"WARNING: the knowledge summary ({total} characters) exceeds the planner's knowledge section ({limit}); "
              "the planner would see a cut view of these files. Shorten the tables' descriptions or raise the limit "
              "before a paid run.")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", "--from", required=True, help="input bundle directory (never modified)")
    ap.add_argument("--sources", "--raw", required=True,
                    help="directory with the clean sources (knowledge_clean.SOURCE_FILES)")
    ap.add_argument("--out", required=True, help="new bundle directory; must not exist")
    ap.add_argument("--table", "--knowledge", action="append", default=[], metavar="[NAME=]PATH",
                    help="a built knowledge file to include: a per-gene table "
                         f"({', '.join(knowledge_clean.TABLE_NAMES)}) or a similarity edge file "
                         f"({', '.join(knowledge_clean.NETWORK_NAMES)}); NAME defaults to the file's stem")
    ap.add_argument("--name", help="the output bundle's manifest name (default: <input>_clean or "
                                   "<input>_clean_tables); a bundle with other knowledge files than block G's "
                                   "needs its own, since the results table groups runs by it")
    ap.add_argument("--no-tables", action="store_true", help="state explicitly that no table goes in")
    ap.add_argument("--allow-missing", action="store_true",
                    help="skip clean sources that are absent instead of refusing (local experiments only)")
    args = ap.parse_args(argv)
    if args.no_tables and args.table:
        ap.error("--no-tables and --table together")
    tables = {}
    for item in args.table:
        name, _, path = item.partition("=")
        if not path:
            name, path = Path(item).name.removesuffix(".json"), item
        tables[name] = Path(path)
    build_clean_bundle(Path(args.bundle), Path(args.sources), Path(args.out), tables or None,
                       allow_missing=args.allow_missing, name=args.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
