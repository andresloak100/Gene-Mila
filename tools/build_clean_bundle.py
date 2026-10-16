#!/usr/bin/env python3
"""Write a tier-1-only ("clean") copy of a bundle: the same data, split and labels, with knowledge/ rebuilt from the
clean sources (genemila/data/knowledge_clean.py) and, optionally, the three per-gene tables.

    python tools/build_clean_bundle.py --bundle data/norman --sources data/knowledge_clean_src --out data/norman_clean
    python tools/build_clean_bundle.py --bundle data/norman --sources data/knowledge_clean_src \\
        --out data/norman_clean_tables --table gene_annotation=gene_annotation_norman.json \\
        --table gene_constraint=gene_constraint_norman.json --table protein_annotation=protein_annotation_norman.json

The output directory must not exist. public.npz, private/* (copied as bytes, never read), splits.json and
knowledge/targets.json are copied byte for byte; the other knowledge files are replaced. manifest.json is the input's
manifest with the name '<name>_clean' (or '<name>_clean_tables' when tables are included), the same split_id and
counts, knowledge_files and file_sha256 recomputed, and a 'clean_knowledge' entry holding the provenance record
(source sha256s, GO evidence codes, STRING channels, table files) and the knowledge files the input had that the
clean bundle drops. The tool verifies the result (verify_bundle, added_knowledge == [], export_public + FeatureContext)
and asserts the input bundle is byte-identical to before. It prints one line per knowledge file and the planner's
knowledge-summary lines (genemila.lab.Lab.knowledge_summary) so the operator can see the planner section's size.
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


def _genes_covered(content) -> int:
    if isinstance(content, dict) and "genes" in content and isinstance(content["genes"], dict):
        return len(content["genes"])  # a per-gene table
    if isinstance(content, dict):
        return len({g for members in content.values() for g in members})
    if content and isinstance(content[0], list):
        return len({x for row in content for x in row[:2]})
    return len(content)


def build_clean_bundle(bundle: Path, sources: Path, out: Path, tables: dict[str, Path] | None = None) -> Path:
    bundle, sources, out = Path(bundle), Path(sources), Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; a clean bundle is written to a new directory, never over one")
    before = _hash_tree(bundle)
    manifest = json.loads((bundle / "manifest.json").read_text())
    genes = [str(g) for g in np.load(bundle / "public.npz", allow_pickle=False)["genes"]]
    files, provenance = knowledge_clean.build(sources, genes, tables)

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

    old_knowledge = [n for n in manifest.get("knowledge_files", []) if n != "targets.json"]
    hashed = {rel for rel in manifest["file_sha256"] if not rel.startswith("knowledge/")} | set(COPIED)
    hashed |= {f"knowledge/{f}" for f in files}
    new = dict(manifest)
    new["name"] = f"{manifest['name']}_clean_tables" if tables else f"{manifest['name']}_clean"
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
        print(f"  {fname}: {len(content)} entries, {_genes_covered(content)} genes covered")
    missing = [f for f, h in provenance["sources"].items() if h is None]
    if missing:
        print(f"  sources missing from {sources}: {', '.join(missing)}")
    lines = knowledge_summary_lines(out)
    print(f"planner knowledge summary: {len('; '.join(lines))} characters in {len(lines)} lines")
    for line in lines:
        print(f"  {len(line):5d}  {line[:100]}{'...' if len(line) > 100 else ''}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", required=True, help="input bundle directory (never modified)")
    ap.add_argument("--sources", required=True, help="directory with the clean sources (knowledge_clean.SOURCE_FILES)")
    ap.add_argument("--out", required=True, help="new bundle directory; must not exist")
    ap.add_argument("--table", action="append", default=[], metavar="NAME=PATH",
                    help="a built table to include: gene_annotation, gene_constraint or protein_annotation")
    ap.add_argument("--no-tables", action="store_true", help="state explicitly that no table goes in")
    args = ap.parse_args(argv)
    if args.no_tables and args.table:
        ap.error("--no-tables and --table together")
    tables = {}
    for item in args.table:
        name, _, path = item.partition("=")
        if not path:
            ap.error(f"--table expects NAME=PATH, got {item!r}")
        tables[name] = Path(path)
    build_clean_bundle(Path(args.bundle), Path(args.sources), Path(args.out), tables or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
