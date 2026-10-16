"""The task package (tools/export_task_package.py, tools/task_package/evaluate.py): it holds exactly the public export
a lab experiment receives and a byte-identical copy of the lab code it needs, its baseline equals the lab's own
out-of-fold score, and its evaluate.py keeps a helpful feature, discards a useless one and rejects attempts that
break the one-change rule, the literal caps or the guard before running them."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from genemila import frozen
from genemila.benchmark.evaluator import evaluate
from genemila.data.bundle import LabelSet, export_public
from genemila.features.api import FeatureContext
from genemila.pipeline import cross_validate
from genemila.prompts import EXAMPLE_FEATURE, feature_api_doc
from test_norman_lab import make_pair_bundle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import export_task_package as etp  # noqa: E402

_spec = importlib.util.spec_from_file_location("tp_evaluate", ROOT / "tools" / "task_package" / "evaluate.py")
tp_evaluate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp_evaluate)  # its functions only; main() is never called here

FEATURE = '''import numpy as np
from genemila.features.api import Feature, register


@register
class F(Feature):
    name = "{name}"
    description = "{description}"

    def compute(self, ctx, perts, params):
{body}
'''
HELPFUL = ("ar_target_corr", "control-cell correlation with the target genes", """\
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            if t:
                out[i, :, 0] = ctx.gene_corr[t].mean(axis=0)
        return out""")
NOISE = ("ar_noise", "a fixed pseudo-random value per gene", """\
        return np.broadcast_to(np.sin(1e3 * ctx.control_mean)[None, :, None], (len(perts), ctx.n_genes, 1)).copy()""")
PER_GENE = "        return np.broadcast_to(ctx.control_std[None, :, None], (len(perts), ctx.n_genes, 1)).copy()"


def _write(pkg: Path, name: str, description: str, body: str) -> Path:
    path = pkg / "features" / f"{name}.py"
    path.write_text(FEATURE.format(name=name, description=description, body=body))
    return path


def _export(data: Path, out: Path, *extra: str) -> Path:
    assert etp.main(["--data", str(data), "--out", str(out), *extra]) == 0
    return out


def _evaluate(pkg: Path) -> tuple[int, dict, str]:
    """Run evaluate.py as an agent does; the grep-able lines as a dict (problem lines joined)."""
    proc = subprocess.run([sys.executable, "evaluate.py"], cwd=pkg, capture_output=True, text=True, timeout=300)
    lines: dict = {}
    for line in proc.stdout.splitlines():
        key, sep, value = line.partition(": ")
        if sep:
            lines[key] = lines[key] + "\n" + value if key in lines else value
    return proc.returncode, lines, proc.stdout + proc.stderr


def _lab_oof(public: Path, features: list[str], manifest: dict) -> float:
    """What the lab's own cross_validate gives for the package's settings: per seed, the alpha with the best mean
    per-perturbation pearson_delta, averaged over the seeds."""
    from genemila.benchmark.evaluator import evaluate
    ctx = FeatureContext(public)
    truth = np.load(public / "public.npz")["train_means"].astype(np.float64)
    out = []
    for s in manifest["fold_seeds"]:
        cv = cross_validate(ctx, features, {}, "ridge", manifest["alphas"], 0, manifest["k"], s, {}, None, None, {},
                            {}, manifest["groups"])
        out.append(max(evaluate(cv[j] + ctx.control_mean, truth, ctx.control_mean, ctx.train_perts)["metrics"]
                       ["pearson_delta"] for j in range(len(manifest["alphas"]))))
    return float(np.mean(out))


@pytest.fixture(scope="module")
def pair_bundle(tmp_path_factory):
    return make_pair_bundle(tmp_path_factory.mktemp("norman") / "norman_toy")


def test_package_holds_the_public_export_only(dataset, tmp_path):
    pkg = _export(dataset, tmp_path / "pkg")
    files = sorted(str(p.relative_to(pkg)) for p in pkg.rglob("*") if p.is_file())
    assert not [f for f in files if "private" in f or "splits.json" in f]
    ref = export_public(dataset, tmp_path / "ref")
    ref_files = sorted(str(p.relative_to(ref)) for p in ref.rglob("*") if p.is_file())
    assert sorted(str(p.relative_to(pkg / "data")) for p in (pkg / "data").rglob("*") if p.is_file()) \
        == sorted(ref_files + ["README.md"])
    for rel in ref_files:
        assert (pkg / "data" / rel).read_bytes() == (ref / rel).read_bytes(), rel
    keys = set(np.load(pkg / "data" / "public.npz").files)
    assert frozen._PUBLIC_ARRAYS <= keys <= frozen._PUBLIC_ARRAYS | {"train_ncells"}
    assert sorted(p.name for p in (pkg / "features").iterdir()) == ["README.md"]
    assert (pkg / "scratch").is_dir() and not any((pkg / "scratch").iterdir())
    for name in ("evaluate.py", "literal.py", "program.md"):
        assert (pkg / name).read_bytes() == (ROOT / "tools" / "task_package" / name).read_bytes()
    m = json.loads((pkg / "MANIFEST.json").read_text())
    assert m["parent_features"] == ["control_mean", "mean_response", "is_target"] and m["groups"] is None
    assert m["alphas"] == [0.01, 0.1, 1.0, 10.0, 100.0] and m["fold_seeds"] == [0, 1, 2] and m["k"] == 5
    assert m["keep_rule"] == "noise" and m["prefix"] == "ar"
    reqs = (pkg / "requirements.txt").read_text().split()
    assert reqs == [f"{lib}=={v}" for lib, v in m["libraries"].items()] and len(reqs) == 3
    fixed = [f for f in files if f.startswith(("harness/", "data/")) or f in ("evaluate.py", "literal.py")]
    assert set(fixed) <= set(m["sha256"])
    assert all(etp.sha256(pkg / rel) == h for rel, h in m["sha256"].items())
    # the record outside the package vouches for MANIFEST.json, which nothing inside it can
    record = json.loads((tmp_path / "pkg.export.json").read_text())
    assert record["manifest_sha256"] == etp.sha256(pkg / "MANIFEST.json") and record["split_id"] == m["split_id"]
    # a second export into the same, now non-empty, directory is refused
    assert etp.main(["--data", str(dataset), "--out", str(pkg)]) == 2
    # the visible tier (the default) is the one extra file; without it the package is as before
    assert files.count("harness/val1.npz") == 1
    assert m["harness_val1"]["sha256"] == etp.sha256(pkg / "harness" / "val1.npz")
    bare = _export(dataset, tmp_path / "bare", "--no-harness-val1")
    bare_files = sorted(str(p.relative_to(bare)) for p in bare.rglob("*") if p.is_file())
    assert bare_files == [f for f in files if f != "harness/val1.npz"]
    assert json.loads((bare / "MANIFEST.json").read_text())["harness_val1"] is None


def test_harness_is_the_lab_code_and_imports_on_its_own(dataset, tmp_path):
    pkg = _export(dataset, tmp_path / "pkg")
    m = json.loads((pkg / "MANIFEST.json").read_text())
    harness = sorted(p.relative_to(pkg / "harness") for p in (pkg / "harness").rglob("*.py"))
    assert {"genemila/pipeline.py", "genemila/guard.py", "genemila/benchmark/evaluator.py",
            "genemila/features/api.py", "genemila/sandbox.py"} <= {str(h) for h in harness}
    for rel in harness:
        assert (pkg / "harness" / rel).read_bytes() == (ROOT / rel).read_bytes(), rel
        assert f"harness/{rel}" in m["sha256"]
    # a fresh interpreter that sees only the package (no repository, no PYTHONPATH, no site customisation) imports
    # everything evaluate.py and the smoke test need from the harness
    code = ("import sys; sys.path[:0] = [sys.argv[1], sys.argv[2]]\n"
            "import genemila.pipeline, genemila.guard, genemila.benchmark.evaluator, genemila.sandbox, literal\n"
            "outside = [m.__file__ for n, m in sys.modules.items() if n.split('.')[0] == 'genemila'\n"
            "           and getattr(m, '__file__', None) and not m.__file__.startswith(sys.argv[1])]\n"
            "assert not outside, outside\nprint('ok')")
    proc = subprocess.run([sys.executable, "-I", "-c", code, str(pkg / "harness"), str(pkg)], cwd=tmp_path,
                          capture_output=True, text=True)
    assert proc.returncode == 0 and proc.stdout.strip() == "ok", proc.stderr


@pytest.mark.parametrize("bundle", ["single", "pairs"])
def test_baseline_equals_the_labs_cross_validation(bundle, dataset, pair_bundle, tmp_path):
    data = dataset if bundle == "single" else pair_bundle
    pkg = _export(data, tmp_path / "pkg", "--no-harness-val1")
    m = json.loads((pkg / "MANIFEST.json").read_text())
    if bundle == "pairs":
        assert m["groups"] == "gene" and m["parent_features"][-1] == "additive_response"
    code, out, log = _evaluate(pkg)
    assert code == 0 and out["status"] == "baseline" and out["decision"] == "keep" and out["harness_ok"] == "true", log
    assert out["deciding"] == "oof" and "val1_pearson_delta" not in out and "combined_pearson_delta" not in out
    assert abs(float(out["oof_pearson_delta"]) - _lab_oof(data, m["parent_features"], m)) < 1e-6
    assert (pkg / "runs" / "kept" / "scores.json").exists()
    assert (pkg / "results.tsv").read_text().splitlines()[0].split("\t") == \
        ["n", "oof_pearson_delta", "gain", "gain_se", "status", "feature", "description"]


def test_keep_discard_and_rejections(dataset, tmp_path):
    pkg = _export(dataset, tmp_path / "pkg")
    kept = pkg / "runs" / "kept" / "features"
    assert _evaluate(pkg)[1]["status"] == "baseline"

    # a feature that carries the knockdown's module program: kept by the noise rule
    _write(pkg, *HELPFUL)
    code, out, log = _evaluate(pkg)
    assert code == 0 and out["status"] == "keep" and out["seeds_positive"] == "3/3", log
    assert float(out["gain"]) > 2 * float(out["gain_se"]) and [p.name for p in kept.iterdir()] == ["ar_target_corr.py"]
    assert json.loads((pkg / "runs" / "kept" / "scores.json").read_text())["features"][-1] == "ar_target_corr"

    # a feature without information: discarded, features/ restored, the attempt kept for the record
    _write(pkg, *NOISE)
    code, out, log = _evaluate(pkg)
    assert code == 0 and out["status"] == "discard" and out["decision"] == "discard", log
    assert sorted(p.name for p in (pkg / "features").glob("*.py")) == ["ar_target_corr.py"]
    assert (pkg / "runs" / "attempts" / "3_ar_noise.py").exists()
    cached = {p.name.split("__")[0] for p in (pkg / "runs" / "cache").glob("*__*")}
    assert "ar_target_corr" in cached and "ar_noise" not in cached  # a discarded attempt's blocks are dropped

    # two files at once: rejected, both removed
    _write(pkg, *NOISE)
    _write(pkg, "ar_spread", "control spread", PER_GENE)
    code, out, log = _evaluate(pkg)
    assert code == 1 and out["status"] == "rejected" and "2 feature files changed" in out["problem"], log
    assert sorted(p.name for p in (pkg / "features").glob("*.py")) == ["ar_target_corr.py"]

    # a table pasted into the code: over the literal caps
    table = ", ".join(f"{0.1 * i:.1f}" for i in range(40))
    _write(pkg, "ar_table", "a pasted table", f"        w = np.array([{table}])\n" + PER_GENE)
    code, out, log = _evaluate(pkg)
    assert out["status"] == "rejected" and "literal cap" in out["problem"], log

    # a guard violation is rejected without the file ever running (it would create the marker)
    marker = tmp_path / "ran"
    path = _write(pkg, "ar_shell", "shell access", PER_GENE)
    path.write_text(f"import os\nX = os.system('touch {marker}')\n" + path.read_text())
    code, out, log = _evaluate(pkg)
    assert out["status"] == "rejected" and "guard" in out["problem"] and not marker.exists(), log

    # a feature that passes the smoke test but fails on a fold's smaller training set: a crash, restored
    _write(pkg, "ar_fragile", "breaks on fold views", """\
        out = np.broadcast_to(ctx.control_std[None, :, None], (len(perts), ctx.n_genes, 1)).copy()
        return out[:, :1] if len(ctx.train_perts) * 5 < len(ctx.perts) * 3 else out""")
    code, out, log = _evaluate(pkg)
    assert code == 1 and out["status"] == "crash" and "ValueError" in out["problem"], log
    assert sorted(p.name for p in (pkg / "features").glob("*.py")) == ["ar_target_corr.py"]

    # deleting the helpful feature loses far more than one SE: discarded, the file comes back
    (pkg / "features" / "ar_target_corr.py").unlink()
    code, out, log = _evaluate(pkg)
    assert out["status"] == "discard" and out["change"] == "deleted ar_target_corr", log
    assert (pkg / "features" / "ar_target_corr.py").exists()

    rows = [r.split("\t") for r in (pkg / "results.tsv").read_text().splitlines()[1:]]
    assert [r[4] for r in rows] == ["baseline", "keep", "discard", "rejected", "rejected", "rejected", "crash",
                                    "discard"]
    assert rows[1][6] == HELPFUL[1] and rows[7][6] == "delete: " + HELPFUL[1]
    assert len((pkg / "runs" / "evals.jsonl").read_text().splitlines()) == 8


def _lab_combined(public: Path, manifest: dict, tmp: Path) -> float:
    """What the lab's controller selects on (genemila/lab.py evaluate_artifact and _combine_visible), computed
    from the lab's own experiment output (pipeline.run: predictions.npz for the held-out perturbations and cv.npz):
    per fold seed, the alpha with the best mean pearson_delta over the visible validation and the out-of-fold
    training perturbations together; averaged over the seeds."""
    from genemila.pipeline import run
    val1 = LabelSet.load(public / "private" / "val1.npz")  # the synthetic fixture's own file
    ctx = FeatureContext(public)
    truth = np.load(public / "public.npz")["train_means"].astype(np.float64)
    n1, nt = len(val1.perts), len(ctx.train_perts)
    (tmp / "plugins").mkdir(parents=True, exist_ok=True)
    best = []
    for s in manifest["fold_seeds"]:
        spec = {"feature_set": manifest["parent_features"], "model_type": "ridge", "seed": 0,
                "hyperparameters": {"alpha_grid": manifest["alphas"], "cv_folds": manifest["k"], "cv_seed": s,
                                    "cv_groups": manifest["groups"]}}
        run(spec, public, tmp / "plugins", tmp / f"exp{s}")
        z, c = np.load(tmp / f"exp{s}" / "predictions.npz"), np.load(tmp / f"exp{s}" / "cv.npz")
        rows = [[str(p) for p in z["perts"]].index(p) for p in val1.perts]
        combined = []
        for j in range(len(manifest["alphas"])):
            v = evaluate(z["delta"][j][rows].astype(np.float64) + ctx.control_mean, val1.means, ctx.control_mean,
                         val1.perts)["metrics"]["pearson_delta"]
            o = evaluate(c["delta"][j].astype(np.float64) + ctx.control_mean, truth, ctx.control_mean,
                         ctx.train_perts)["metrics"]["pearson_delta"]
            combined.append((n1 * v + nt * o) / (n1 + nt))
        best.append(max(combined))
    return float(np.mean(best))


def test_harness_tier_is_the_visible_validation_and_the_lab_rule_decides(dataset, tmp_path):
    """The default package ships the visible validation tier under harness/ (the labels the lab's controller
    scores on, from the bundle's private/val1.npz and nothing else), evaluate.py reports it beside the out-of-fold
    score, and its deciding score is what the lab's own selection computes from the lab's own experiment output."""
    pkg = _export(dataset, tmp_path / "pkg")
    m = json.loads((pkg / "MANIFEST.json").read_text())
    tier = np.load(pkg / "harness" / "val1.npz", allow_pickle=False)
    val1 = LabelSet.load(dataset / "private" / "val1.npz")
    assert [str(p) for p in tier["perts"]] == val1.perts and np.array_equal(tier["means"], val1.means)
    assert m["harness_val1"]["n_perts"] == len(val1.perts) == m["harness_val1"]["n_perts"]
    assert "harness/val1.npz" in m["sha256"] and m["harness_val1"]["rule"].startswith("combined:")
    assert "Lab._combine_visible" in m["harness_val1"]["rule"]
    assert not any("val2" in str(p) or "splits" in str(p) for p in pkg.rglob("*"))
    code, out, log = _evaluate(pkg)
    assert code == 0 and out["status"] == "baseline" and out["deciding"] == "combined", log
    v, o, c = (float(out[k]) for k in ("val1_pearson_delta", "oof_pearson_delta", "combined_pearson_delta"))
    n1, nt = len(val1.perts), len(FeatureContext(dataset).train_perts)
    assert abs(c - (n1 * v + nt * o) / (n1 + nt)) < 1e-9 and out["wins"].endswith(f"/{n1 + nt}")
    assert abs(c - _lab_combined(dataset, m, tmp_path / "lab")) < 1e-6
    # a helpful feature: kept on the combined set, with both parts reported
    _write(pkg, *HELPFUL)
    code, out, log = _evaluate(pkg)
    assert code == 0 and out["status"] == "keep" and out["deciding"] == "combined", log
    assert abs(float(out["parent"]) - c) < 1e-9 and float(out["gain"]) > 0
    assert abs(float(out["gain"]) - (n1 * float(out["val1_gain"]) + nt * float(out["oof_gain"])) / (n1 + nt)) < 2e-6
    kept = json.loads((pkg / "runs" / "kept" / "scores.json").read_text())
    assert set(kept["val1_per_seed"]) == {"0", "1", "2"} and "combined_pearson_delta" in kept
    # a file whose source names the tier is rejected before it runs
    _write(pkg, "ar_peek", "reads harness/val1.npz", "        import numpy  # harness/val1.npz\n" + PER_GENE)
    code, out, log = _evaluate(pkg)
    assert code == 1 and out["status"] == "rejected" and "visible validation tier" in out["problem"], log


def test_keep_rule_matches_the_lab_on_a_hand_made_case():
    """evaluate.py's combined score is Lab._combine_visible's primary, and its keep rule on the combined vector
    keeps a case the out-of-fold vector alone would discard."""
    from genemila.lab import Lab
    fake = SimpleNamespace(_val1=SimpleNamespace(perts=list("abcdef")), selection="pearson_delta", cv_folds=5,
                           _train=SimpleNamespace(perts=list("ghijklmnopqrstuvwx")))
    metrics, cv_metrics = {"pearson_delta": 0.64}, {"pearson_delta": 0.61}
    Lab._combine_visible(fake, metrics, cv_metrics)
    assert abs(tp_evaluate.combined_primary(0.64, 0.61, 6, 18) - metrics["primary"]) < 1e-12
    assert metrics["n_visible"] == 24
    rng = np.random.default_rng(0)
    old = rng.normal(0.6, 0.05, size=(3, 24))
    cur = old.copy()
    cur[:, :6] += 0.03   # the six validation perturbations gain clearly
    cur[:, 6:] += 0.001  # the eighteen out-of-fold ones barely move
    genes_of = [{p} for p in "abcdefghijklmnopqrstuvwx"]
    oof = tp_evaluate.keep_decision("noise", "added", cur[:, 6:], old[:, 6:], genes_of[6:])
    both = tp_evaluate.keep_decision("noise", "added", cur, old, genes_of)
    assert not oof["keep"] and abs(oof["gain"] - 0.001) < 1e-12  # under the 0.002 floor
    assert both["keep"] and abs(both["gain"] - (6 * 0.03 + 18 * 0.001) / 24) < 1e-12
    assert both["wins"] == 24 and both["seeds_positive"] == 3 and both["gain"] > 2 * both["gain_se"]
    assert tp_evaluate.keep_decision("strict", "added", cur, old, genes_of)["keep"]
    assert tp_evaluate.keep_decision("noise", "deleted", old, cur, genes_of)["keep"] is False


def test_smoke_limit_and_changed_harness_are_reported(dataset, tmp_path):
    pkg = _export(dataset, tmp_path / "pkg")
    spec = pkg / "harness" / "genemila" / "spec.py"
    spec.write_text(spec.read_text() + "\n")
    (pkg / "harness" / "sitecustomize.py").write_text("")  # unlisted, and imported by every harness process
    code, out, log = _evaluate(pkg)
    assert out["harness_ok"] == "false" and out["harness_changed"].split("\n") == \
        ["harness/genemila/spec.py", "harness/sitecustomize.py"], log
    m = json.loads((pkg / "MANIFEST.json").read_text())
    m["eval_timeout_s"] = 9  # the smoke test gets a third of it
    (pkg / "MANIFEST.json").write_text(json.dumps(m))
    _write(pkg, "ar_spin", "never returns", "        while True:\n            pass")
    code, out, log = _evaluate(pkg)
    assert code == 1 and out["status"] == "rejected" and "smoke" in out["problem"], log
    assert "MANIFEST.json" in out["harness_changed"]  # it no longer matches the export record
    assert not (pkg / "features" / "ar_spin.py").exists()
    rows = [json.loads(r) for r in (pkg / "runs" / "evals.jsonl").read_text().splitlines()]
    assert [r["manifest_sha256"] == etp.sha256(pkg / "MANIFEST.json") for r in rows] == [False, True]


def test_feature_dependencies_must_be_listed(dataset, tmp_path):
    """The feature cache keys a block by the source of the features in `dependencies` only, so a ctx.feature call
    must name a listed feature; otherwise deleting or changing the feature it uses would be scored from stale
    blocks and could leave a kept state that no longer computes."""
    pkg = _export(dataset, tmp_path / "pkg", "--keep-rule", "strict")
    assert _evaluate(pkg)[1]["status"] == "baseline"
    _write(pkg, *HELPFUL)
    assert _evaluate(pkg)[1]["status"] == "keep"
    square = '        a = ctx.feature("ar_target_corr", perts)\n        return a + 0.5 * a ** 2'
    _write(pkg, "ar_square", "square of the target correlation", square)
    code, out, log = _evaluate(pkg)
    assert out["status"] == "rejected" and "lists in dependencies" in out["problem"], log
    path = _write(pkg, "ar_square", "square of the target correlation", square)
    path.write_text(path.read_text().replace("    def compute", '    dependencies = ["ar_target_corr"]\n\n    def compute'))
    code, out, log = _evaluate(pkg)
    assert out["status"] == "keep", log  # strict: a positive gain under the first fold seed
    (pkg / "features" / "ar_target_corr.py").unlink()  # ar_square lists it
    code, out, log = _evaluate(pkg)
    assert out["status"] == "rejected" and "ar_target_corr in dependencies, which is not a feature here" in \
        out["problem"] and (pkg / "features" / "ar_target_corr.py").exists(), log
    path = _write(pkg, "ar_cube", "cube", '        return ctx.feature("ar_square", perts) ** 3')
    path.write_text(path.read_text().replace("    def compute", '    dependencies = ["ar_square"]\n\n    def compute'))
    code, out, log = _evaluate(pkg)
    assert out["status"] == "rejected" and "list ar_target_corr in dependencies too" in out["problem"], log


def test_feature_readme_carries_the_lab_api_text(dataset, pair_bundle, tmp_path):
    single = (_export(dataset, tmp_path / "a") / "features" / "README.md").read_text()
    pairs = (_export(pair_bundle, tmp_path / "b") / "features" / "README.md").read_text()
    assert feature_api_doc(False) in single and EXAMPLE_FEATURE in single and "every name starts with `ar_`" in single
    assert feature_api_doc(True) in pairs and feature_api_doc(True) != feature_api_doc(False)
    data_readme = (tmp_path / "b" / "data" / "README.md").read_text()
    assert "pairs of two genes" in data_readme and "- targets: dict of" in data_readme


def test_a_kept_package_feature_is_scored_by_feature_compare(dataset, tmp_path):
    """The round trip the comparison protocol relies on: a feature an agent keeps in the package goes, unchanged, to
    tools/feature_compare.py as a source and comes back as an ok row with the same name."""
    pkg = _export(dataset, tmp_path / "pkg")
    assert _evaluate(pkg)[1]["status"] == "baseline"
    _write(pkg, *HELPFUL)
    assert _evaluate(pkg)[1]["status"] == "keep"
    out = tmp_path / "fc"
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "feature_compare.py"), "--data", str(dataset),
                           "--out", str(out), "--source", f"ar={pkg / 'runs' / 'kept' / 'features'}",
                           "--fold-seeds", "101,102", "--null-reps", "19"], capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rows = json.loads((out / "feature_compare.json").read_text())["rows"]
    mine = [r for r in rows if r.get("source") == "ar" and r.get("feature") == "ar_target_corr"]
    assert mine and all(r["status"] == "ok" for r in mine)
