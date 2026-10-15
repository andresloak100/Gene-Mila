#!/usr/bin/env python3
"""Export one bundle as a self-contained task package: the lab's feature-discovery problem as an autoresearch-style
task (karpathy/autoresearch), so that a single coding agent (Claude Code, Codex), Biomni or CellForge's agents work
on exactly the task the lab's agents work on and hand back feature files that tools/feature_compare.py scores
beside the lab's own (Claim issue #41, docs/PAPER_FRAMEWORK_PROPOSAL.md).

    python tools/export_task_package.py --data data/norman --out ~/pkg_norman [--prefix ar] [--fold-seeds 0,1,2]
        [--k 5] [--groups auto|none|gene] [--keep-rule noise|strict] [--eval-timeout-s 600] [--ram-mb 4096]

What the package holds, and why:
- data/: exactly the public export every lab experiment receives (genemila.data.bundle.export_public): public.npz,
  the public manifest and knowledge/. Held-out perturbation ids are public in the lab too; their labels are not, and
  private/ and splits.json are never read or copied. So the package arm sees the same information as the lab arms.
- harness/genemila/: byte-identical copies of the lab modules evaluate.py and `python -m genemila.pipeline smoke`
  import (found by importing them in a fresh interpreter, not by a hand-kept list), so the package scores with the
  lab's own fold, feature and evaluation code and needs no checkout of this repository.
- evaluate.py, literal.py, program.md: byte copies of tools/task_package/. Nothing is templated: every setting
  (prefix, fold seeds, k, groups, keep rule, alpha grid, parent features, limits) lives in MANIFEST.json, so the
  shipped files hash the same as the repository's and MANIFEST.json's sha256 list can check them.
- features/: empty except README.md, the worker prompt's own API text (genemila.prompts) and a short package note,
  so both arms learn the API from the same words. scratch/: empty, for the agent's own analysis.
- requirements.txt: the installed numpy, scipy and scikit-learn versions, which the scores depend on.

The parent model is the lab's start (Lab.queue_model_baselines): ridge on the built-in features, plus
additive_response on a bundle with pairs; the alpha grid is configs/default.toml's experiment.default_alpha_grid.
Exit 2 when the inputs are unusable or the output directory exists and is not empty.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.config import load_config  # noqa: E402
from genemila.data.bundle import export_public  # noqa: E402
from genemila.features.registry import BUILTIN_FEATURES, PAIR_BUILTIN_FEATURES  # noqa: E402
from genemila.guard import ALLOWED_IMPORT_ROOTS  # noqa: E402
from genemila.prompts import EXAMPLE_FEATURE, bundle_has_pairs, dataset_line, feature_api_doc  # noqa: E402

TEMPLATE_DIR = REPO_ROOT / "tools" / "task_package"
# what evaluate.py imports from the harness, and what the smoke subprocess runs (python -m genemila.pipeline)
ENTRY_MODULES = ("genemila.pipeline", "genemila.guard", "genemila.benchmark.evaluator", "genemila.sandbox")
LIBRARIES = ("numpy", "scipy", "scikit-learn")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def import_closure() -> list[str]:
    """The repository files (relative paths) of every genemila module a fresh interpreter loads when it imports
    ENTRY_MODULES: the harness the package needs, determined by Python itself so a new import in the lab code is
    never missed."""
    code = ("import importlib, json, sys\n"
            f"for m in {list(ENTRY_MODULES)!r}: importlib.import_module(m)\n"
            "print(json.dumps(sorted(m.__file__ for n, m in sys.modules.items()\n"
            "    if (n == 'genemila' or n.startswith('genemila.')) and getattr(m, '__file__', None))))")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT, env=env, capture_output=True, text=True,
                         check=True).stdout
    files = [Path(f).resolve().relative_to(REPO_ROOT) for f in json.loads(out)]
    return sorted(str(f) for f in files)


def resolve_groups(setting: str, manifest: dict, targets: dict) -> str | None:
    """The lab's cv_groups without splits.json: "gene" for a bundle with a perturbation of several genes or a gene
    split recorded in the public manifest (genemila.data.real writes split_mode), else None. bundle_strata, the
    lab's rule, also reads splits.json's mode, which a package must not; the manifest carries it for real bundles."""
    if setting != "auto":
        return None if setting == "none" else setting
    multi = any(len(set(v or [])) > 1 for v in targets.values())
    return "gene" if multi or manifest.get("split_mode") == "gene" else None


def dataset_text(manifest: dict, targets: dict, train: list[str]) -> str:
    """Lab.data_summary, copied (it is a method of a Lab, which needs a run): the DATASET line the lab's workers get."""
    if bundle_has_pairs(targets) or manifest.get("modality"):
        return dataset_line(manifest, targets, train)
    sizes = [len(v) for v in targets.values()] or [1]
    multi = sum(1 for n in sizes if n > 1)
    kind = "single-gene targets" if not multi else (
        f"targets of 1 to {max(sizes)} genes; {multi} of {len(sizes)} perturbations hit more than one gene")
    return (f"{manifest['name']}: {manifest['n_genes']} genes, {manifest['n_control_cells']} control cells, "
            f"{manifest['n_train']} training perturbations ({kind}); predict unseen perturbations.")


def knowledge_lines(kdir: Path) -> list[str]:
    """Lab.knowledge_summary, copied (a method of a Lab): one line per knowledge file, as the lab's workers see it."""
    parts = []
    for p in sorted(kdir.glob("*.json")):
        obj = json.loads(p.read_text())
        if isinstance(obj, dict) and isinstance(obj.get("description"), str):
            parts.append(f"{p.stem}: {obj['description'][:900]} (a dict with keys {', '.join(map(str, obj))})")
        elif isinstance(obj, dict):
            k = next(iter(obj), None)
            parts.append(f"{p.stem}: dict of {len(obj)} entries, e.g. {k!r}: {str(obj[k])[:60]}")
        else:
            parts.append(f"{p.stem}: list of {len(obj)}, e.g. {str(obj[0])[:60] if obj else ''}")
    return parts


def data_readme(manifest: dict, targets: dict, train: list[str], kdir: Path) -> str:
    lines = ["# Data", "", dataset_text(manifest, targets, train), "",
             "public.npz: genes, control_cells (control cells x genes, log-normalised), perts (every perturbation id, "
             "held-out ones included), train_perts, train_means (one mean expression profile per training "
             "perturbation; the held-out labels are not in this package), train_ncells. manifest.json: the public "
             "manifest. Feature code reads all of this through ctx (features/README.md), never from the files.", "",
             "## Knowledge files (ctx.knowledge(name))", ""]
    return "\n".join(lines + [f"- {line}" for line in knowledge_lines(kdir)]) + "\n"


def features_readme(pairs: bool, prefix: str, parent: list[str]) -> str:
    api = feature_api_doc(pairs)
    return (f"# Feature API\n\nAPI:\n```python\n{api}\n```\n\nEXAMPLE PLUGIN:\n```python\n{EXAMPLE_FEATURE}```\n\n"
            "## In this package\n\n"
            f"- One feature per file: `features/<name>.py` registers exactly one class whose `name` equals the file "
            f"stem, and every name starts with `{prefix}_` (so \"must equal the requested name\" above means: the "
            "file stem).\n"
            f"- The model is ridge regression on the parent features ({', '.join(parent)}), which are always in, "
            "plus every file here.\n"
            "- The example is the built-in `mean_response`, shown for style only: its name is taken and lacks the "
            "prefix.\n"
            "- `ctx.perts` includes the held-out perturbation ids; their labels are not in this package. "
            "`ctx.train_perts` are the perturbations with labels.\n"
            f"- Allowed imports: {', '.join(sorted(ALLOWED_IMPORT_ROOTS))} and genemila.features.api. No file, "
            "network or OS access (harness/genemila/guard.py checks this before any file runs).\n"
            "- No data tables in feature code: literal.py caps the numbers, strings and names a file may hold.\n"
            "- Another feature here can be used through `ctx.feature(name, perts)`; list it in `dependencies`.\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="a bundle directory (only its public part is read)")
    ap.add_argument("--out", required=True, help="the package directory to create (must not exist or be empty)")
    ap.add_argument("--prefix", default="ar")
    ap.add_argument("--fold-seeds", default="0,1,2")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--groups", choices=["auto", "none", "gene"], default="auto")
    ap.add_argument("--keep-rule", choices=["noise", "strict"], default="noise")
    ap.add_argument("--eval-timeout-s", type=float, default=600)
    ap.add_argument("--ram-mb", type=float, default=4096)
    args = ap.parse_args(argv)
    data, out = Path(args.data), Path(args.out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        print(f"refusing: {out} exists and is not empty", file=sys.stderr)
        return 2
    if not (data / "public.npz").is_file() or not (data / "manifest.json").is_file():
        print(f"refusing: {data} has no public.npz or manifest.json", file=sys.stderr)
        return 2
    try:
        seeds = [int(s) for s in args.fold_seeds.split(",") if s.strip()]
    except ValueError:
        seeds = []
    if not seeds or args.k < 2 or not args.prefix.isidentifier():
        print("refusing: need integer --fold-seeds, --k >= 2 and an identifier --prefix", file=sys.stderr)
        return 2

    export_public(data, out / "data")
    manifest = json.loads((out / "data" / "manifest.json").read_text())
    targets = json.loads((out / "data" / "knowledge" / "targets.json").read_text())
    train = [str(p) for p in np.load(out / "data" / "public.npz", allow_pickle=False)["train_perts"]]
    pairs = bundle_has_pairs(targets)
    parent = list(BUILTIN_FEATURES) + (list(PAIR_BUILTIN_FEATURES) if pairs else [])

    for rel in import_closure():
        (out / "harness" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, out / "harness" / rel)
    for name in ("evaluate.py", "literal.py", "program.md"):
        shutil.copyfile(TEMPLATE_DIR / name, out / name)
    (out / "features").mkdir()
    (out / "scratch").mkdir()
    (out / "features" / "README.md").write_text(features_readme(pairs, args.prefix, parent))
    (out / "data" / "README.md").write_text(data_readme(manifest, targets, train, out / "data" / "knowledge"))
    versions = {lib: importlib.metadata.version(lib) for lib in LIBRARIES}
    (out / "requirements.txt").write_text("".join(f"{lib}=={v}\n" for lib, v in versions.items()))

    fixed = [out / n for n in ("evaluate.py", "literal.py", "program.md", "requirements.txt")]
    fixed += sorted(p for d in ("harness", "data") for p in (out / d).rglob("*") if p.is_file())
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True,
                                check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    package = {
        "format": 1, "bundle": manifest.get("name"), "split_id": manifest.get("split_id"),
        "prefix": args.prefix, "fold_seeds": seeds, "k": args.k,
        "groups": resolve_groups(args.groups, manifest, targets), "groups_setting": args.groups,
        "keep_rule": args.keep_rule, "model": "ridge",
        "alphas": [float(a) for a in load_config()["experiment"]["default_alpha_grid"]],
        "parent_features": parent, "eval_timeout_s": args.eval_timeout_s, "ram_mb": args.ram_mb,
        "lab_commit": commit, "python": platform.python_version(), "libraries": versions,
        "sha256": {str(p.relative_to(out)): sha256(p) for p in fixed},
    }
    (out / "MANIFEST.json").write_text(json.dumps(package, indent=1) + "\n")
    print(f"task package for {package['bundle']} ({package['split_id']}) at {out}: parent {', '.join(parent)}; "
          f"groups {package['groups']}; keep rule {args.keep_rule}; {len(package['sha256'])} files hashed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
