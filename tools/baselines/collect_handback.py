#!/usr/bin/env python3
"""Collect a foreign session's kept features as `tools/feature_compare.py --source` files, checked and inventoried.

    python tools/baselines/collect_handback.py --out <run out dir> --package <package dir> --dest <dir>

The kept features are the package's `runs/kept/features/*.py` (the state evaluate.py's keep rule accepted, the
hand-back the protocol scores). Without that directory, the stems whose last results.tsv row has status keep or
baseline are taken from features/; without results.tsv, every features/*.py. Each file goes through the lab guard
(genemila.guard.check_plugin_source, file <stem>.py registers feature <stem>) and the literal caps
(tools/task_package/literal.py literal_check with the package's own pair ids and names, as its evaluate.py applies
them). A file that passes both is copied to <dest>/<arm>_r<seed>/<stem>.py (the arm and seed come from
<out>/run.json); one that fails goes to <dest>/rejected/<arm>_r<seed>/<stem>.py with the reason. <dest>/manifest.json
records, per session, every file's sha256, size, literal verdict, guard verdict and destination, the session's run.json
summary (ended_by, model, task_sha256), the sha256 of results.tsv, and the sha256 of <out>/transcript.txt with the
lines in it that name a network call (http://, https://, requests, urllib, socket, curl, wget; fairness control 7 of
docs/FEATURE_COMPARISON_PROTOCOL.md). A flagged transcript is not rejected here; the operator reads the lines. The
manifest is merged, so one dest collects every session of a block.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from genemila.guard import CodeViolation, check_plugin_source  # noqa: E402
from task_package.literal import literal_check  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


NETWORK = re.compile(r"https?://|\brequests\b|\burllib\b|\bsocket\b|\bcurl\b|\bwget\b")


def transcript_flags(path: Path, limit: int = 200) -> list[dict]:
    """Lines of the transcript that name a network call, for the operator to read (at most `limit`)."""
    flags = []
    for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        m = NETWORK.search(line)
        if m:
            flags.append({"line": n, "match": m.group(0), "text": line.strip()[:200]})
            if len(flags) >= limit:
                break
    return flags


def kept_files(pkg: Path) -> tuple[list[Path], str]:
    kept = pkg / "runs" / "kept" / "features"
    if kept.is_dir():
        return sorted(kept.glob("*.py")), "runs/kept/features"
    tsv = pkg / "results.tsv"
    if tsv.is_file():
        last: dict[str, str] = {}
        for line in tsv.read_text().splitlines()[1:]:
            cells = line.split("\t")
            if len(cells) >= 6:
                for stem in cells[5].split(","):
                    last[stem.strip()] = cells[4]
        stems = {s for s, status in last.items() if status in ("keep", "baseline")}
        return sorted(p for p in (pkg / "features").glob("*.py") if p.stem in stems), "results.tsv status keep"
    return sorted((pkg / "features").glob("*.py")), "features/ (no results.tsv)"


def package_names(pkg: Path) -> tuple[list[str], list[str]]:
    """The pair ids and the names evaluate.py gives literal_check."""
    z = np.load(pkg / "data" / "public.npz", allow_pickle=False)
    genes, perts = [str(g) for g in z["genes"]], [str(p) for p in z["perts"]]
    targets = json.loads((pkg / "data" / "knowledge" / "targets.json").read_text())
    return [p for p, v in targets.items() if len(set(v or [])) > 1], genes + perts


def check(path: Path, pair_ids, names) -> dict:
    src = path.read_text(errors="replace")
    entry = {"sha256": sha256(path), "size": path.stat().st_size}
    try:
        check_plugin_source(src, path.stem)
        entry["guard"] = {"ok": True, "problems": []}
    except CodeViolation as exc:
        entry["guard"] = {"ok": False, "problems": [str(exc)[:500]]}
    lit = literal_check(src, pair_ids, names)
    entry["literal"] = {"ok": lit["ok"], "problems": lit["problems"], **lit["stats"]}
    entry["ok"] = entry["guard"]["ok"] and lit["ok"]
    return entry


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="the session's output directory (run.json from the runner)")
    ap.add_argument("--package", required=True, help="the package directory the session worked in")
    ap.add_argument("--dest", required=True, help="the collection directory (one per block; merged)")
    a = ap.parse_args(argv)
    out, pkg, dest = Path(a.out), Path(a.package), Path(a.dest)
    if not (out / "run.json").is_file():
        print(f"refusing: {out}/run.json not found", file=sys.stderr)
        return 2
    if not (pkg / "data" / "public.npz").is_file() or not (pkg / "MANIFEST.json").is_file():
        print(f"refusing: {pkg} is not a task package", file=sys.stderr)
        return 2
    run = json.loads((out / "run.json").read_text())
    label = f"{run.get('arm', 'arm')}_r{run.get('seed', 0)}"
    files, origin = kept_files(pkg)
    pair_ids, names = package_names(pkg)
    good, bad = dest / label, dest / "rejected" / label
    manifest_path = dest / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {"sessions": {}}
    session = {"package": str(pkg.resolve()), "out": str(out.resolve()), "origin": origin,
               "run": {k: run.get(k) for k in ("arm", "seed", "model", "model_served", "ended_by", "minutes",
                                               "wall_s", "exit_code", "task_sha256")},
               "results_tsv_sha256": sha256(pkg / "results.tsv") if (pkg / "results.tsv").is_file() else None,
               "manifest_sha256": sha256(pkg / "MANIFEST.json"), "files": {}}
    transcript = out / "transcript.txt"
    session["transcript_sha256"] = sha256(transcript) if transcript.is_file() else None
    session["transcript_flags"] = transcript_flags(transcript) if transcript.is_file() else None
    n_ok = 0
    for f in files:
        entry = check(f, pair_ids, names)
        target = good if entry["ok"] else bad
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, target / f.name)
        entry["copied_to"] = str((target / f.name).relative_to(dest))
        if not entry["ok"]:
            entry["rejected_reason"] = "; ".join(entry["guard"]["problems"] + entry["literal"]["problems"])
        session["files"][f.stem] = entry
        n_ok += entry["ok"]
    good.mkdir(parents=True, exist_ok=True)  # an empty source directory is a valid hand-back (nothing kept)
    manifest["sessions"][label] = session
    dest.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(f"{label}: {len(files)} kept files from {origin}; {n_ok} accepted -> {good}; {len(files) - n_ok} rejected"
          f" -> {bad if len(files) - n_ok else '-'}; manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
