"""Read-only scan of every feature plugin in the listed runs for sources of cross-process nondeterminism:
builtin hash() / __hash__, id(), and random use without an explicit seed. Reports whether each hit feature is in a
model whose sealed score the run reports (summary.json: best, and every finalist in generalization_query_only,
ensemble members included). Opens lab.db read-only (immutable copy semantics: mode=ro)."""
import ast, json, sqlite3, sys
from pathlib import Path
RUNS = [Path(p) for p in sys.argv[1:]]
NP_OK = {"default_rng", "RandomState", "Generator", "SeedSequence", "seed", "PCG64", "MT19937", "get_state", "set_state"}

def scan(src):
    hits = []
    try: tree = ast.parse(src)
    except SyntaxError as e: return [(e.lineno or 0, "unparsable", "")]
    seeded_std = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "seed"
                     and isinstance(n.func.value, ast.Name) and n.func.value.id == "random" for n in ast.walk(tree))
    seeded_np = any(isinstance(n, ast.Call) and ast.unparse(n.func) in ("np.random.seed", "numpy.random.seed") for n in ast.walk(tree))
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr == "__hash__": hits.append((n.lineno, "__hash__", ""))
        if not isinstance(n, ast.Call): continue
        f = ast.unparse(n.func)
        if f == "hash": hits.append((n.lineno, "hash()", ""))
        elif f == "id": hits.append((n.lineno, "id()", ""))
        elif f in ("np.random.default_rng", "numpy.random.default_rng", "default_rng", "np.random.RandomState", "numpy.random.RandomState", "RandomState"):
            if not n.args and not n.keywords or (n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value is None):
                hits.append((n.lineno, "unseeded " + f.split(".")[-1], ""))
            elif any("hash(" in ast.unparse(a) for a in n.args): pass  # counted by the hash() hit
        elif "RandomState(" in f or "default_rng(" in f: pass  # a draw from a generator built in the same expression; its seed is checked above
        elif f.startswith(("np.random.", "numpy.random.")) and f.split(".")[-1] not in NP_OK:
            hits.append((n.lineno, f + ("" if not seeded_np else " (np.random.seed set in file)"), "seeded" if seeded_np else ""))
        elif f.startswith("random.") and f.split(".")[-1] not in ("seed", "Random"):
            hits.append((n.lineno, f + ("" if not seeded_std else " (random.seed set in file)"), "seeded" if seeded_std else ""))
        elif f == "random.Random" and not n.args: hits.append((n.lineno, "unseeded random.Random", ""))
    return sorted(set(hits))

def deps(src):
    out = set()
    try: tree = ast.parse(src)
    except SyntaxError: return out
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str): out.add(n.value)
    return out

rows, summary = [], []
for run in RUNS:
    store = run / "feature_store"
    files = {p.stem: p for p in sorted(store.glob("*.py"))} if store.is_dir() else {}
    src = {k: p.read_text(errors="replace") for k, p in files.items()}
    hit = {k: [h for h in scan(s) if h[2] != "seeded"] for k, s in src.items()}
    soft = {k: [h for h in scan(s) if h[2] == "seeded"] for k, s in src.items()}
    hit = {k: v for k, v in hit.items() if v}
    # models whose sealed score the run reports
    sel, ens, fin = set(), set(), set()
    sj = run / "summary.json"
    if sj.exists():
        s = json.loads(sj.read_text())
        sel = set((s.get("best") or {}).get("features") or [])
        db = sqlite3.connect(f"file:{run / 'lab.db'}?mode=ro", uri=True)
        def feats(e):
            r = db.execute("select feature_set_json from experiments where experiment_id=?", (e,)).fetchone()
            return set(json.loads(r[0])) if r and r[0] else set()
        for g in s.get("generalization_query_only") or []:
            if g.get("kind") == "baseline": continue
            if g.get("kind") == "ensemble":
                for m in g.get("members") or []: ens |= feats(m if isinstance(m, str) else m.get("experiment_id"))
                ens |= feats(g["experiment_id"])
            else: fin |= feats(g["experiment_id"])
        db.close()
    # a reported feature that computes a hit feature through ctx.feature(name)
    def reaches(f, seen=None):
        seen = seen or set()
        if f in seen or f not in src: return set()
        seen.add(f); out = set()
        for d in deps(src[f]) & set(src):
            if d == f: continue
            if d in hit: out.add(d)
            out |= reaches(d, seen)
        return out
    n_sel = 0
    for k in sorted(hit):
        where = [w for w, S in (("selected", sel), ("ensemble", ens), ("other sealed finalist", fin)) if k in S]
        via = sorted(f for f in (sel | ens | fin) if f != k and k in reaches(f))
        if "selected" in where or "ensemble" in where: n_sel += 1
        for line, kind, _ in hit[k]:
            rows.append((run.name, k, line, kind, ", ".join(where) or "no", ", ".join(via)[:120]))
    summary.append((run.name, len(files), len(hit), sum(len(v) for v in soft.values() if v), n_sel, len(sel)))
out = ["# Nondeterminism scan of feature plugins", "",
       "Read-only static scan (Python ast) of every plugin in each run's feature_store for calls whose value changes between "
       "processes: the builtin hash() and __hash__ (string hashes are salted per process), id(), and random draws without an "
       "explicit seed (np.random.* legacy functions, random.*, default_rng() or RandomState() with no seed). A draw in a file "
       "that calls np.random.seed or random.seed is counted separately as seeded and not listed. 'In a reported model' is taken "
       "from summary.json: the selected model (best), the members of its ensemble, and the other finalists scored on the sealed "
       "set. 'Reached through' names reported features that compute the hit feature through ctx.feature. Not covered: iteration "
       "over sets of strings, which is also hash-ordered, and thread timing.", "",
       "## Runs", "", "| run | plugins | plugins with a hit | seeded draws (not listed) | hit plugins in the selected model or its ensemble | selected model features |", "|---|---|---|---|---|---|"]
out += [f"| {a} | {b} | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in summary]
out += ["", "## Hits in a reported model (selected, ensemble, other sealed finalist, or reached through one)", "",
        "| run | feature | line | call | in a reported model | reached through |", "|---|---|---|---|---|---|"]
rep = [r for r in rows if r[4] != "no" or r[5]]
out += [f"| {a} | {b} | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in rep] or ["| none | | | | | |"]
out += ["", "## All other hits (features not in any reported model)", "", "| run | feature | line | call |", "|---|---|---|---|"]
out += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d, e, f in rows if e == "no" and not f]
Path(__file__).with_name("nondeterminism_scan.md").write_text("\n".join(out) + "\n")
Path(__file__).with_name("nondeterminism_scan.json").write_text(json.dumps({"runs": summary, "hits": rows}, indent=1))
print("\n".join(out[:12 + len(summary) + 6 + len(rep)]))
print("total hit lines", len(rows), "reported-model hit lines", len(rep))
