#!/usr/bin/env python3
"""The fixed evaluation of a Gene-Mila task package. Do not edit it: its sha256 is in MANIFEST.json.

    python evaluate.py > run.log 2>&1

The model is ridge regression on the parent features (MANIFEST.json "parent_features", the lab's starting model)
plus every feature file in features/. Each run scores that model out of fold on the training perturbations, with
the lab's own code (harness/genemila: pipeline.cross_validate and benchmark.evaluator), and compares it with the
kept state in runs/kept/. Why it works this way:

- One change per run. Between runs exactly one features/*.py may be added, modified or deleted, so every score
  difference belongs to one feature, the unit the comparison of systems is about (the lab's max_new_features=1). The
  first run (no runs/kept/scores.json) is the baseline: it scores features/ as it is, normally empty.
- Static checks before any plugin code runs: the lab's guard (genemila/guard.py: imports, I/O, reflection),
  literal.py's caps (no data tables pasted into code) and the dependency rule below on every file, then the lab's
  smoke test of the changed file in a limited subprocess (shape, finiteness, determinism, own-label leakage).
- Every ctx.feature(name, ...) call names a feature listed in the file's `dependencies`, and that list includes
  what the listed package features use in turn. The feature cache keys a block by the source of the features listed
  there and no others, so an unlisted one would let a changed or deleted feature be scored from another feature's
  stale cached blocks, and leave a kept state that can no longer be computed.
- Honest out-of-fold scores: for every fold seed in MANIFEST.json, cross_validate recomputes every feature on each
  fold's view (label_dep={}, the lab's rule for code whose label reads it cannot trace), so a feature never sees
  the labels it is scored on; runs/cache makes unchanged features cheap. The alpha is chosen per seed by the mean
  per-perturbation pearson_delta, the lab's selection metric. These are the agent's selection scores: hundreds of
  attempts are chosen on the same folds of the same labels, so the kept state's score is optimistic and is never
  reported as evidence. Results come from tools/feature_compare.py on new fold seeds and from held-out tiers.
- A noise-aware keep rule (MANIFEST.json "keep_rule"). "noise": keep when the gain over the kept state, averaged over
  the seeds, exceeds max(2 SE, 0.002) with an SE widened for perturbations sharing a gene, wins on more than half
  the perturbations and is positive under every seed; a deletion is kept when it loses less than one plain SE
  (gain_se_plain). "strict" (autoresearch as published, one evaluation): keep when the gain under the first fold
  seed is above zero.
- The visible validation tier (MANIFEST.json "harness_val1", harness/val1.npz, when the exporter shipped it): the
  labels the lab's own controller scores every experiment on. Each run also fits the model on all training rows at
  every alpha, as the lab's experiment does (pipeline.run), and scores those perturbations; then, as the lab selects
  (genemila/lab.py, Lab.evaluate_artifact and Lab._combine_visible), the alpha per fold seed and the keep rule go by
  the mean pearson_delta over the visible validation and the out-of-fold training perturbations together, each
  weighing the same (combined_primary below). oof_pearson_delta and val1_pearson_delta are reported beside the
  combined score, and gain is the combined gain (oof_gain and val1_gain its parts). The file is readable from the
  shell and the agent is told so (program.md); feature code cannot open it (the guard), cannot paste it (literal.py),
  and a file whose source names the tier is rejected. Without the tier the deciding score is the out-of-fold one.
- The decision is applied here, not left to the agent: kept means the files evaluated become runs/kept/features;
  discarded, rejected or crashed means features/ is restored from it. Every attempt is copied to runs/attempts/ and
  logged in results.tsv and runs/evals.jsonl. The files are read once, into runs/work/features, and everything runs
  from that copy, so an edit made while an evaluation runs is never kept unchecked; it is the next run's change.
  One evaluation at a time per package (a lock in runs/).
- harness_ok: false when a file MANIFEST.json lists has changed, an unlisted file sits in harness/, data/ or the
  package root, or MANIFEST.json differs from the export record beside the package (<package>.export.json, written
  by the exporter). Each row records MANIFEST.json's sha256; the hand-back is checked against that record.

The script re-runs itself as a subprocess under PYTHONHASHSEED=0 (the lab's experiment processes' seed, so plugin
values match the lab's) with the time and memory limits of MANIFEST.json; it never replaces its own process, so it
also runs from an agent that executes Python inside its own interpreter. The evaluation also gets eval_timeout_s
CPU seconds as a kernel limit, so it ends even when this process is killed and nothing watches it any more. Exit 0 when the attempt was scored
(baseline, keep, discard), 1 when it was rejected or crashed. Grep-able lines: status:, decision:,
oof_pearson_delta:, parent:, gain:, gain_se:, gain_se_plain:, wins:, seeds_positive:, harness_ok:, cpu_s:, and
with the visible tier val1_pearson_delta:, combined_pearson_delta:, deciding:, oof_gain:, val1_gain:.
"""
from __future__ import annotations

import ast
import fcntl
import hashlib
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

PKG = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
FEATURES, RUNS = PKG / "features", PKG / "runs"
KEPT, WORK = RUNS / "kept", RUNS / "work" / "features"
TSV_HEADER = "n\toof_pearson_delta\tgain\tgain_se\tstatus\tfeature\tdescription\n"
MIN_GAIN = 0.002  # the lab's helpful-feature threshold (genemila/research_state.py)


# ------------------------------------------------------------------ bookkeeping (standard library only)
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_files(folder: Path) -> dict[str, bytes]:
    return {p.stem: p.read_bytes() for p in sorted(folder.glob("*.py"))} if folder.is_dir() else {}


def changes(now: dict[str, bytes]) -> list[tuple[str, str]]:
    """(kind, stem) for every feature file in `now` added, modified or deleted since the kept snapshot."""
    kept = py_files(KEPT / "features")
    out = [("added" if s not in kept else "modified", s) for s in now if now[s] != kept.get(s)]
    return out + [("deleted", s) for s in kept if s not in now]


def restore() -> None:
    """features/*.py back to the kept snapshot (nothing to restore before the baseline)."""
    if not (KEPT / "features").is_dir():
        return
    FEATURES.mkdir(exist_ok=True)
    for p in FEATURES.glob("*.py"):
        p.unlink()
    for p in (KEPT / "features").glob("*.py"):
        shutil.copyfile(p, FEATURES / p.name)


def describe(source: bytes | None) -> str:
    """The `description` class attribute of a feature file, read statically (the file may never be imported)."""
    try:
        for node in ast.walk(ast.parse(source or b"")):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "description"
                                                    for t in node.targets) and isinstance(node.value, ast.Constant):
                return " ".join(str(node.value.value).split())[:200]
    except (SyntaxError, ValueError):
        pass
    return ""


def describe_attempt(baseline: bool, attempt: list[tuple[str, str]], files: dict[str, bytes]) -> str:
    if baseline:
        return "baseline"
    if len(attempt) != 1:
        return ""
    kind, stem = attempt[0]
    if kind == "deleted":
        return "delete: " + describe(py_files(KEPT / "features").get(stem))
    return describe(files[stem])


def next_n() -> int:
    log = RUNS / "evals.jsonl"
    return 1 + (sum(1 for line in log.read_text().splitlines() if line.strip()) if log.exists() else 0)


def record(row: dict, attempt: list[tuple[str, str]], files: dict[str, bytes]) -> None:
    """Copy the attempt's files to runs/attempts/, append to results.tsv and runs/evals.jsonl."""
    (RUNS / "attempts").mkdir(parents=True, exist_ok=True)
    for kind, stem in attempt:
        if stem in files and kind != "deleted":
            (RUNS / "attempts" / f"{row['n']}_{stem}.py").write_bytes(files[stem])
    tsv = PKG / "results.tsv"
    if not tsv.exists():
        tsv.write_text(TSV_HEADER)
    cells = [row["n"], f"{row.get('oof_pearson_delta') or 0:.6f}", f"{row.get('gain') or 0:.6f}",
             f"{row.get('gain_se') or 0:.6f}", row["status"], row["feature"], row["description"]]
    with tsv.open("a") as fh:
        fh.write("\t".join(" ".join(str(c).split()) for c in cells) + "\n")
    with (RUNS / "evals.jsonl").open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def report(row: dict) -> None:
    print(f"status: {row['status']}")
    print(f"decision: {row['decision']}")
    print(f"change: {row['change']}")
    for problem in row.get("problems") or []:
        print(f"problem: {problem}")
    if row.get("oof_pearson_delta") is not None:
        print(f"oof_pearson_delta: {row['oof_pearson_delta']:.6f}")
        if row.get("val1_pearson_delta") is not None:
            print(f"val1_pearson_delta: {row['val1_pearson_delta']:.6f}")
            print(f"combined_pearson_delta: {row['combined_pearson_delta']:.6f}")
        print(f"deciding: {row['deciding']}")
        print(f"parent: {row['parent']:.6f}" if row.get("parent") is not None else "parent: none")
        print(f"gain: {row['gain']:.6f}")
        print(f"gain_se: {row['gain_se']:.6f}")
        print(f"gain_se_plain: {row['gain_se_plain']:.6f}")
        if row.get("val1_gain") is not None:
            print(f"oof_gain: {row['oof_gain']:.6f}")
            print(f"val1_gain: {row['val1_gain']:.6f}")
        print(f"wins: {row['wins']}/{row['n_perts']}")
        print(f"seeds_positive: {row['seeds_positive']}/{len(row['seed_gains'])}")
    print(f"harness_ok: {str(row['harness_ok']).lower()}")
    print(f"cpu_s: {row['cpu_s']:.1f}")


# ------------------------------------------------------------------ the outer process: limits and hash seed
def outer(manifest: dict) -> int:
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(PKG / "harness"))
    from genemila.sandbox import run_limited

    lock = (RUNS / "lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # released by the kernel however this process ends
    except OSError:
        print("status: rejected\nproblem: another evaluate.py is running in this package; run one at a time")
        return 1
    n = next_n()
    if WORK.exists():
        shutil.rmtree(WORK)
    limit = float(manifest["eval_timeout_s"])
    res = run_limited([sys.executable, str(PKG / "evaluate.py"), "--inner"], PKG, RUNS / "logs",
                      limit, float(manifest["ram_mb"]), limit,
                      env={"PYTHONPATH": str(PKG / "harness"), "PYTHONDONTWRITEBYTECODE": "1"}, name="evaluate")
    for stream in ("stdout", "stderr"):
        text = (RUNS / "logs" / f"evaluate.{stream}").read_text(errors="replace")
        print(text, end="", file=sys.stdout if stream == "stdout" else sys.stderr, flush=True)
    if next_n() > n:
        return res.returncode
    # the inner process died before it recorded the attempt (time or memory limit, a crash in the interpreter)
    files = py_files(WORK) if WORK.is_dir() else py_files(FEATURES)  # what the inner process evaluated
    baseline = not (KEPT / "scores.json").exists()
    attempt = [("baseline", s) for s in files] if baseline else changes(files)
    row = {"n": n, "time": time.time(), "status": "crash", "decision": "discard",
           "change": ", ".join(f"{k} {s}" for k, s in attempt) or "none",
           "feature": ",".join(s for _, s in attempt) or "-",
           "description": describe_attempt(baseline, attempt, files),
           "problems": [res.killed_reason or f"evaluation process exited with {res.returncode} "
                        "(killed at the CPU limit?)"],
           "harness_ok": None, "cpu_s": res.cpu_s}
    record(row, attempt, files)
    restore()
    report(row)
    return 1


# ------------------------------------------------------------------ the inner process: checks, scores, decision
def overlap_ratio(d, genes_of) -> float:
    """How much perturbations sharing a target gene widen the paired SE of a mean difference: with e = d - mean(d),
    sqrt(sum of e_p e_q over ordered pairs whose targets overlap, p = q included, / sum of e_p^2); exactly 1 when no
    two perturbations share a gene (tools/sealed_reading.py _cluster_ratio, the same few lines)."""
    import numpy as np
    e = d - d.mean()
    plain = float(e @ e)
    if len(d) < 3 or plain <= 0:
        return 1.0
    overlap = np.array([[bool(a & b) for b in genes_of] for a in genes_of], dtype=np.float64)
    return float(np.sqrt(max(0.0, float(e @ overlap @ e)) / plain))


def combined_primary(val1_mean: float, oof_mean: float, n_val1: int, n_train: int) -> float:
    """The lab's selection score (genemila/lab.py, Lab._combine_visible, selection rule pearson_delta): the metric
    averaged over the visible validation and the out-of-fold training perturbations, each weighing the same."""
    return (n_val1 * val1_mean + n_train * oof_mean) / (n_val1 + n_train)


def keep_decision(rule: str, kind: str, cur, old, genes_of) -> dict:
    """The keep rule on per-perturbation scores cur and old of shape (n_seeds, n_perts), the deciding tier's (the
    combined vector with the visible tier, else the out-of-fold one). "noise": the gain averaged over the seeds
    beats max(2 SE_adj, MIN_GAIN), wins on more than half the perturbations and is positive under every seed; a
    deletion is kept when it loses less than one plain SE; "strict": the first seed's gain is above zero."""
    import numpy as np
    d_seed = cur - old
    d = d_seed.mean(axis=0)
    gain, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))
    se_adj = se * max(1.0, overlap_ratio(d, genes_of))
    wins, seed_gains = int((d > 0).sum()), [float(g) for g in d_seed.mean(axis=1)]
    if rule == "strict":
        keep = seed_gains[0] > 0
    elif kind == "deleted":
        keep = -gain < se
    else:
        keep = gain > max(2 * se_adj, MIN_GAIN) and wins > len(d) / 2 and all(g > 0 for g in seed_gains)
    return {"gain": gain, "gain_se": se_adj, "gain_se_plain": se, "wins": wins, "seed_gains": seed_gains,
            "seeds_positive": sum(g > 0 for g in seed_gains), "keep": bool(keep)}


def val1_scores(ctx, feats: list[str], alphas: list[float], val1_perts: list[str], val1_means, cache) -> list[dict]:
    """Per alpha, the visible validation perturbations' pearson_delta from a ridge fitted on every training row,
    as pipeline.run fits the lab's experiment: the features of every held-out perturbation in one batch, the
    columns standardised by the training rows' mean and sd, the val1 rows scored by the lab's evaluator."""
    import numpy as np
    from genemila.benchmark.evaluator import evaluate
    from genemila.pipeline import build_matrix, make_model
    train = list(ctx.train_perts)
    evals = [p for p in ctx.perts if p not in set(train)]
    timings: dict = {}
    X_tr, _ = build_matrix(ctx, feats, {}, train, timings, cache, {}, {})
    X_ev, _ = build_matrix(ctx, feats, {}, evals, timings, cache, {}, {})
    _, d_tr = ctx.train_delta()
    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    sd[sd == 0] = 1.0
    X_tr, X_ev = (X_tr - mu) / sd, (X_ev - mu) / sd
    rows = [evals.index(p) for p in val1_perts]
    out = []
    for a in alphas:
        model = make_model("ridge", a, 0)
        model.fit(X_tr, d_tr.reshape(-1))
        pred = model.predict(X_ev).reshape(len(evals), ctx.n_genes)[rows]
        if not np.all(np.isfinite(pred)):
            raise ValueError(f"model produced non-finite visible-validation predictions at alpha={a}")
        res = evaluate(pred + ctx.control_mean, val1_means, ctx.control_mean, val1_perts)
        out.append({p: float(v["pearson_delta"]) for p, v in res["per_perturbation"].items()})
    return out


def dependencies(source: bytes) -> tuple[set[str], list[str]]:
    """The features a file lists in `dependencies`, and the problems with its ctx.feature calls: each one must name,
    as a string constant, a feature listed there (getattr is banned by the guard, so every use is a `.feature`
    attribute this sees). A file that does not parse returns nothing; the guard reports it."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set(), []
    listed, problems, named = set(), [], set()
    for node in ast.walk(tree):
        target = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) \
            else []
        if any(isinstance(t, ast.Name) and t.id == "dependencies" for t in target) and node.value is not None:
            try:
                names = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                names = None
            if isinstance(names, (list, tuple)) and all(isinstance(x, str) for x in names):
                listed |= set(names)
            else:
                problems.append("dependencies must be a literal list of feature names")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "feature":
            arg = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "name"), None)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value in listed:
                named.add(id(node.func))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "feature" and id(node) not in named:
            problems.append(f"line {node.lineno}: ctx.feature must be called with a feature name, as a string, "
                            "that the class lists in dependencies")
    return listed, problems


def inner(manifest: dict) -> int:
    t0 = time.process_time()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(PKG / "harness"), str(PKG)]
    bad = [rel for rel, h in manifest["sha256"].items() if not (PKG / rel).is_file() or sha256(PKG / rel) != h]
    bad += [rel for p in [*PKG.glob("*.py"), *(PKG / "harness").rglob("*"), *(PKG / "data").rglob("*")]
            if p.is_file() and "__pycache__" not in p.parts
            and (rel := str(p.relative_to(PKG))) not in manifest["sha256"]]  # e.g. harness/sitecustomize.py
    manifest_sha = sha256(PKG / "MANIFEST.json")
    export_record = PKG.parent / f"{PKG.name}.export.json"
    if export_record.is_file() and json.loads(export_record.read_text()).get("manifest_sha256") != manifest_sha:
        bad.append("MANIFEST.json")
    for rel in bad:
        print(f"harness_changed: {rel}")
    import numpy as np
    from genemila.features.registry import ALL_BUILTIN_FEATURES
    from genemila.guard import CodeViolation, check_plugin_source
    from genemila.sandbox import run_limited
    from literal import literal_check

    data = PKG / "data"
    z = np.load(data / "public.npz", allow_pickle=False)
    genes, perts = [str(g) for g in z["genes"]], [str(p) for p in z["perts"]]
    train, train_means = [str(p) for p in z["train_perts"]], z["train_means"].astype(np.float64)
    targets = json.loads((data / "knowledge" / "targets.json").read_text())
    pair_ids = [p for p, v in targets.items() if len(set(v or [])) > 1]
    prefix, seeds = manifest["prefix"], [int(s) for s in manifest["fold_seeds"]]
    tier = manifest.get("harness_val1")  # the visible validation tier, when the exporter shipped it
    if tier:
        v = np.load(PKG / tier["file"], allow_pickle=False)
        val1_perts, val1_means = [str(p) for p in v["perts"]], v["means"].astype(np.float64)
    else:
        val1_perts, val1_means = [], None

    baseline = not (KEPT / "scores.json").exists()
    current = py_files(FEATURES)  # read once: every later step uses this copy, never features/
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    for stem, src in current.items():
        (WORK / f"{stem}.py").write_bytes(src)
    attempt = [("baseline", s) for s in current] if baseline else changes(current)
    n = next_n()
    row = {"n": n, "time": time.time(), "change": ", ".join(f"{k} {s}" for k, s in attempt) or "none",
           "feature": ",".join(s for _, s in attempt) or "-",
           "description": describe_attempt(baseline, attempt, current), "harness_ok": not bad,
           "keep_rule": manifest["keep_rule"], "deciding": "combined" if tier else "oof",
           "manifest_sha256": manifest_sha,
           "sha256": {s: hashlib.sha256(src).hexdigest() for s, src in current.items()}}
    deps: dict[str, set[str]] = {}
    cache, cache_before = RUNS / "cache", None  # the cache files that existed before the scores were computed

    def prune_cache(decision: str) -> None:
        """Drop the cached blocks no later run reads: a discarded attempt's (everything this run wrote), or on a keep
        the old blocks of the changed feature and of the features that list it (their cache keys changed)."""
        now = {p for p in cache.glob("*__*") if p.is_file()}
        changed = {s for _, s in attempt}
        changed |= {s for s, d in deps.items() if d & changed}
        gone = now - cache_before if decision == "discard" else \
            {p for p in cache_before if p.name.split("__")[0] in changed}
        for p in gone:
            p.unlink(missing_ok=True)

    def finish(status: str, problems=(), smoke_cpu: float = 0.0, **scores) -> int:
        decision = "keep" if status in ("baseline", "keep") else "discard"
        row.update(status=status, decision=decision, problems=list(problems),
                   cpu_s=time.process_time() - t0 + smoke_cpu, **scores)
        record(row, attempt, current)
        if decision == "discard":
            restore()
        else:
            if (KEPT / "features").exists():
                shutil.rmtree(KEPT / "features")
            (KEPT / "features").mkdir(parents=True)
            for stem, src in current.items():
                (KEPT / "features" / f"{stem}.py").write_bytes(src)
            (KEPT / "scores.json").write_text(json.dumps(
                {k: row[k] for k in ("n", "features", "oof_pearson_delta", "alphas", "per_seed", "val1_per_seed",
                                     "val1_pearson_delta", "combined_pearson_delta") if k in row}))
        if cache_before is not None:
            prune_cache(decision)
        report(row)
        return 0 if status in ("baseline", "keep", "discard") else 1

    # 1. the one-change rule and static checks, before any plugin code runs
    problems = []
    if not baseline and len(attempt) != 1:
        problems.append(f"{len(attempt)} feature files changed since the kept state; exactly one may be added, "
                        "modified or deleted per run")
    for stem, src in current.items():
        if not stem.startswith(prefix + "_"):
            problems.append(f"{stem}.py: feature names must start with {prefix}_")
        try:
            check_plugin_source(src.decode(errors="replace"), expected_name=stem)
        except CodeViolation as exc:
            problems.append(f"{stem}.py: guard: {exc}")
        lit = literal_check(src.decode(errors="replace"), pair_ids, genes + perts)
        problems += [f"{stem}.py: literal cap: {p}" for p in lit["problems"]]
        if tier and (b"val1" in src or b"harness" in src):
            problems.append(f"{stem}.py: names the visible validation tier (val1, harness); feature code computes "
                            "from ctx only")
        deps[stem], found = dependencies(src)
        problems += [f"{stem}.py: {p}" for p in found]
    for stem in current:  # every listed feature exists, and the list includes what listed package features use
        for d in sorted(deps[stem]):
            missing = {x for x in deps.get(d, ()) if x in current and x != stem} - deps[stem]
            if d not in current and d not in ALL_BUILTIN_FEATURES:
                problems.append(f"{stem}.py lists {d} in dependencies, which is not a feature here")
            elif missing:
                problems.append(f"{stem}.py: list {', '.join(sorted(missing))} in dependencies too (used by {d})")
    if problems:
        return finish("rejected", problems)

    # 2. the smoke test of the new or changed file, in a limited subprocess. It runs in a session of its own, which a
    # kill of this process would not reach, so it gets a third of the evaluation's time and as many CPU seconds.
    smoke_cpu, limit = 0.0, float(manifest["eval_timeout_s"]) / 3
    for kind, stem in attempt:
        if kind == "deleted":
            continue
        out = RUNS / "smoke" / stem
        if out.exists():
            shutil.rmtree(out)
        res = run_limited([sys.executable, "-m", "genemila.pipeline", "smoke", "--feature", stem, "--public",
                           str(data), "--plugins", str(WORK), "--out", str(out)], PKG, out,
                          limit, float(manifest["ram_mb"]), limit,
                          env={"PYTHONPATH": str(PKG / "harness"), "PYTHONDONTWRITEBYTECODE": "1"}, name="smoke")
        smoke_cpu += res.cpu_s
        if res.returncode != 0:
            if (out / "smoke.json").exists():
                found = json.loads((out / "smoke.json").read_text())["problems"]
            elif (out / "error.json").exists():
                found = [json.loads((out / "error.json").read_text())["error"]]
            else:
                found = [res.killed_reason or res.stderr_tail[-500:].strip() or f"exit status {res.returncode} "
                         "(killed at the CPU limit?)"]
            problems += [f"{stem}.py: smoke: {p}" for p in found]
    if problems:
        return finish("rejected", problems, smoke_cpu)

    # 3. out-of-fold scores of the parent plus every feature file, per fold seed
    try:
        from genemila.benchmark.evaluator import evaluate
        from genemila.features import registry
        from genemila.features.api import FeatureContext
        from genemila.pipeline import cross_validate

        np.random.seed(0)  # as pipeline.run seeds before it loads plugins
        registry.load_plugins(WORK)
        ctx = FeatureContext(data, RUNS / "cache" / "shared")
        feats = list(manifest["parent_features"]) + sorted(current)
        alphas = [float(a) for a in manifest["alphas"]]
        per_seed, val1_per_seed, chosen = {}, {}, {}
        cache_before = {p for p in cache.glob("*__*") if p.is_file()}
        v1 = val1_scores(ctx, feats, alphas, val1_perts, val1_means, cache) if tier else None
        for s in seeds:
            cv = cross_validate(ctx, feats, {}, "ridge", alphas, 0, int(manifest["k"]), s, {}, cache,
                                None, {}, {}, manifest["groups"])
            evals = [evaluate(cv[j] + ctx.control_mean, train_means, ctx.control_mean, train)
                     for j in range(len(alphas))]
            oof_means = [e["metrics"]["pearson_delta"] for e in evals]
            if tier:  # the lab's alpha choice: the combined score (Lab.evaluate_artifact)
                j = int(np.argmax([combined_primary(float(np.mean(list(v1[j].values()))), oof_means[j],
                                                    len(val1_perts), len(train)) for j in range(len(alphas))]))
                val1_per_seed[str(s)] = v1[j]
            else:
                j = int(np.argmax(oof_means))
            chosen[str(s)] = alphas[j]
            per_seed[str(s)] = {p: float(v["pearson_delta"]) for p, v in evals[j]["per_perturbation"].items()}
    except Exception as exc:  # a feature that fails on a fold view, a deleted dependency ...
        traceback.print_exc()
        return finish("crash", [f"{type(exc).__name__}: {str(exc)[:500]}"], smoke_cpu)
    cur = np.array([[per_seed[str(s)][p] for p in train] for s in seeds])
    oof = float(cur.mean())
    scores = {"features": feats, "alphas": chosen, "per_seed": per_seed, "oof_pearson_delta": oof,
              "val1_per_seed": val1_per_seed, "n_perts": len(train)}
    deciding_perts, dec = list(train), cur
    if tier:  # the deciding vector is the lab's: visible validation and out-of-fold training perturbations together
        vcur = np.array([[val1_per_seed[str(s)][p] for p in val1_perts] for s in seeds])
        scores.update(val1_pearson_delta=float(vcur.mean()),
                      combined_pearson_delta=combined_primary(float(vcur.mean()), oof, len(val1_perts), len(train)),
                      n_perts=len(val1_perts) + len(train))
        deciding_perts, dec = val1_perts + list(train), np.concatenate([vcur, cur], axis=1)
    if baseline:
        return finish("baseline", (), smoke_cpu, parent=None, gain=0.0, gain_se=0.0, gain_se_plain=0.0,
                      wins=0, seed_gains=[0.0] * len(seeds), seeds_positive=0,
                      **({"oof_gain": 0.0, "val1_gain": 0.0} if tier else {}), **scores)

    # 4. paired comparison with the kept state and the keep rule, on the deciding tier
    kept = json.loads((KEPT / "scores.json").read_text())
    old = np.array([[kept["per_seed"][str(s)][p] for p in train] for s in seeds])
    parent = float(kept["oof_pearson_delta"])
    parts = {}
    if tier:
        vold = np.array([[kept["val1_per_seed"][str(s)][p] for p in val1_perts] for s in seeds])
        parts = {"oof_gain": float((cur - old).mean()), "val1_gain": float((vcur - vold).mean())}
        old, parent = np.concatenate([vold, old], axis=1), float(kept["combined_pearson_delta"])
    dec = keep_decision(manifest["keep_rule"], attempt[0][0], dec, old,
                        [set(targets.get(p) or [p]) for p in deciding_perts])
    keep = dec.pop("keep")
    return finish("keep" if keep else "discard", (), smoke_cpu, parent=parent, **dec, **parts, **scores)


def main(argv: list[str]) -> int:
    manifest = json.loads((PKG / "MANIFEST.json").read_text())
    RUNS.mkdir(exist_ok=True)
    return inner(manifest) if "--inner" in argv else outer(manifest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
