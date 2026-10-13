"""Hash-pinned numeric export and inference for an explicitly frozen linear ensemble.

Export alone deserializes trusted, hash-verified historical estimator pickles.
Prediction loads numeric arrays and trusted feature Python, never an estimator.
No labels outside the original public training context are accepted or scored.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.metadata
import json
import os
import pickle
import platform
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

from .features import builtin, registry
from .features.api import Feature, FeatureContext
from .pipeline import build_matrix


SCHEMA = 1
_PUBLIC_ARRAYS = {"genes", "control_cells", "perts", "train_perts", "train_means"}
_RUNTIME_SOURCES = ("frozen.py", "pipeline.py", "features/__init__.py", "features/api.py", "features/builtin.py", "features/registry.py")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _checked(path: Path, expected: str) -> Path:
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("an explicit SHA256 pin is required")
    if path.is_symlink() or not path.is_file() or sha256(path) != expected:
        raise ValueError(f"hash mismatch or missing regular file: {path.name}")
    return path


def _relative(root: Path, name: str) -> Path:
    rel = Path(name)
    if rel.is_absolute() or not rel.parts or any(p in (".", "..") for p in rel.parts):
        raise ValueError("unsafe receipt path")
    out = root / rel
    if any(p.is_symlink() for p in [out, *out.parents] if p != root.parent):
        raise ValueError("symlinks are not accepted in frozen inputs")
    if not out.resolve().is_relative_to(root.resolve()):
        raise ValueError("receipt path escapes its root")
    return out


def _json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _copy_checked(source: Path, pin: str, dest: Path) -> None:
    data = _checked(source, pin).read_bytes()
    if hashlib.sha256(data).hexdigest() != pin:
        raise ValueError("source changed while copying")
    dest.write_bytes(data)


def _refuse_output(out: Path, roots: list[Path], files: list[Path]) -> None:
    destination = out.resolve()
    if any(destination.is_relative_to(root.resolve()) for root in roots):
        raise ValueError("output must be outside source run/context/package roots")
    if any(destination == source.resolve() for source in files):
        raise ValueError("output must not replace an input")


def _anchor_hash(ctx: FeatureContext) -> str:
    anchors = [p for p in ctx.perts if p not in set(ctx.train_perts)]
    identity = {"perts": anchors, "targets": [ctx.target_genes(p) for p in anchors], "genes": ctx.genes,
                "public_npz_sha256": sha256(ctx.public_dir / "public.npz"),
                "targets_sha256": sha256(ctx.public_dir / "knowledge" / "targets.json")}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def runtime_receipt() -> dict:
    root = Path(__file__).resolve().parent
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
        "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "scikit-learn")},
        "source_sha256": {p: sha256(root / p) for p in _RUNTIME_SOURCES},
    }


def _names(values, what: str) -> list[str]:
    if not isinstance(values, list) or not values or any(not isinstance(x, str) or not x for x in values):
        raise ValueError(f"{what} must be a nonempty list of strings")
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate {what}")
    return values


def _finite(value, shape: tuple[int, ...], what: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != shape or not np.all(np.isfinite(arr)):
        raise ValueError(f"invalid shape or nonfinite {what}")
    return arr


def _public_context(path: Path) -> FeatureContext:
    # This allowlist accepts public training labels, never test responses.
    with np.load(path / "public.npz", allow_pickle=False) as data:
        if not _PUBLIC_ARRAYS <= set(data.files) or set(data.files) - _PUBLIC_ARRAYS - {"train_ncells"}:
            raise ValueError("public.npz has unexpected or missing arrays")
        genes = _names(data["genes"].tolist(), "genes")
        perts = _names(data["perts"].tolist(), "perturbations")
        train = _names(data["train_perts"].tolist(), "training perturbations")
        if not set(train) <= set(perts):
            raise ValueError("training perturbations outside context")
        control = np.asarray(data["control_cells"])
        if control.ndim != 2 or control.shape[0] < 1:
            raise ValueError("invalid control cells")
        _finite(control, (len(control), len(genes)), "control cells")
        _finite(data["train_means"], (len(train), len(genes)), "training means")
        if "train_ncells" in data.files:
            counts = _finite(data["train_ncells"], (len(train),), "training cell counts")
            if not (counts > 0).all():
                raise ValueError("training cell counts must be positive")
    targets = _json(path / "knowledge" / "targets.json")
    if set(targets) != set(perts):
        raise ValueError("target metadata must exactly cover context perturbations")
    for target in targets.values():
        if not isinstance(target, list) or any(not isinstance(g, str) or not g for g in target):
            raise ValueError("invalid context target metadata")
        if len(set(target)) != len(target):
            raise ValueError("duplicate context target")
    return FeatureContext(path, cache_dir=None)


@contextlib.contextmanager
def _plugins(path: Path):
    """Fresh registry/module state per member; no inherited plugin or disk cache."""
    previous, loaded = dict(registry.REGISTRY), dict(registry._LOADED)
    modules = {k: v for k, v in sys.modules.items() if k.startswith("genemila_plugin_")}
    bytecode = sys.dont_write_bytecode
    rng_state = np.random.get_state()
    sys.dont_write_bytecode = True
    registry.REGISTRY.clear()
    registry._LOADED.clear()
    for cls in vars(builtin).values():
        if isinstance(cls, type) and issubclass(cls, Feature) and cls is not Feature:
            registry.REGISTRY[cls.name] = cls
    try:
        registry.load_plugins(path)
        yield
    finally:
        registry.REGISTRY.clear()
        registry.REGISTRY.update(previous)
        registry._LOADED.clear()
        registry._LOADED.update(loaded)
        for key in list(sys.modules):
            if key.startswith("genemila_plugin_"):
                del sys.modules[key]
        sys.modules.update(modules)
        sys.dont_write_bytecode = bytecode
        np.random.set_state(rng_state)


def _model_arrays(bundle: dict, spec: dict, alpha: float) -> tuple[dict, list[str], int]:
    """Resolve a full fitted grid using the run spec, independently of predictions.npz."""
    from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge

    model_type = spec.get("model_type", "ridge")
    types = {"ridge": Ridge, "lasso": Lasso, "elasticnet": ElasticNet, "ols": LinearRegression}
    if model_type not in types:
        raise ValueError("unsupported frozen model type")
    hp = spec.get("hyperparameters", {})
    grid = [0.0] if model_type == "ols" else hp.get("alpha_grid", [hp.get("alpha", 1.0)])
    grid = _finite(grid, (len(grid),), "alpha grid")
    if (grid < 0).any() or not np.isfinite(alpha) or alpha < 0:
        raise ValueError("invalid frozen alpha")
    matches = np.flatnonzero(grid == alpha)
    if len(matches) != 1:
        raise ValueError("frozen alpha must match exactly one full-grid estimator")
    models = bundle.get("models", [])
    if len(models) != len(grid):
        raise ValueError("model count differs from full alpha grid")
    index = int(matches[0])
    model = models[index]
    if type(model) is not types[model_type]:
        raise ValueError("estimator class differs from frozen model type")
    if model_type != "ols" and float(model.alpha) != alpha:
        raise ValueError("estimator alpha differs from frozen alpha")
    columns = _names(bundle.get("columns"), "feature columns")
    n = len(columns)
    if getattr(model, "n_features_in_", None) != n:
        raise ValueError("estimator feature count differs from columns")
    arrays = {
        "coef": _finite(model.coef_, (n,), "coefficients"),
        "intercept": _finite(model.intercept_, (), "intercept"),
        "x_mean": _finite(bundle.get("x_mean"), (n,), "feature means"),
        "x_std": _finite(bundle.get("x_std"), (n,), "feature scales"),
    }
    if not (arrays["x_std"] > 0).all():
        raise ValueError("feature scales must be positive")
    return arrays, columns, index


def export_ensemble(receipt_path: Path, receipt_sha256: str, selections: list[tuple[str, float]],
                    out: Path, *, trust_pickle: bool = False) -> dict:
    """Export every explicitly named receipt member; never inspect scores or select a model.

    The pin proves byte identity, not that a pickle/plugin is safe. Callers must
    independently trust the archived source before allowing deserialization.
    """
    if not trust_pickle:
        raise ValueError("export requires explicit trust of archived estimator pickles and feature code")
    receipt_path, out = Path(receipt_path), Path(out)
    receipt = _json(_checked(receipt_path, receipt_sha256))
    members = receipt.get("frozen_members", [])
    if not members or len(selections) != len(members):
        raise ValueError("explicit selections must cover every frozen receipt member")
    _refuse_output(out, [Path(m["run_directory"]) for m in members], [receipt_path])
    desired = {name: float(alpha) for name, alpha in selections}
    if len(desired) != len(selections) or set(desired) != {m["experiment_id"] for m in members}:
        raise ValueError("explicit experiment identities differ from receipt")
    weights = np.array([m["weight"] for m in members], dtype=float)
    if (not np.all(np.isfinite(weights)) or not (weights > 0).all() or
            not np.isclose(weights.sum(), 1, atol=1e-12, rtol=0)):
        raise ValueError("receipt weights must be positive and sum to one")
    if out.exists():
        raise ValueError("export output must not already exist")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".frozen-export-", dir=out.parent) as tmp:
        stage = Path(tmp) / "package"
        stage.mkdir()
        manifest = {"schema_version": SCHEMA, "source_receipt_sha256": receipt_sha256,
                    "runtime": runtime_receipt(), "members": [],
                    "inference_recipe": "training-feature priming; original-evaluation-anchors; one new condition per feature batch",
                    "training_core_provenance": {
                        "declared_base_commits": sorted({m.get("base_commit") for m in members if m.get("base_commit")}),
                        "audit": "export pins current runtime; compare training core source and reproduce saved predictions before scientific use",
                    }}
        common_inputs = None
        for i, member in enumerate(members):
            experiment = member["experiment_id"]
            if not re.fullmatch(r"EXP_[0-9]+", experiment):
                raise ValueError("invalid experiment identity")
            alpha = desired[experiment]
            if alpha != member["selected_alpha"]:
                raise ValueError("explicit alpha differs from frozen receipt")
            run = Path(member["run_directory"])
            hashes = member["files_sha256"]
            source_names = [f"artifacts/{experiment}/models.pkl", f"artifacts/{experiment}/run_spec.json"]
            plugins = sorted(k for k in hashes if k.startswith("feature_store/") and k.endswith(".py"))
            inputs = {k: v for k, v in hashes.items() if k == "public_data/public.npz" or
                      (k.startswith("public_data/knowledge/") and k.endswith(".json"))}
            if "public_data/public.npz" not in inputs or "public_data/knowledge/targets.json" not in inputs:
                raise ValueError("receipt lacks public context hashes")
            if {p.name for p in (run / "feature_store").glob("*.py")} != {Path(p).name for p in plugins}:
                raise ValueError("receipt does not cover the complete feature source snapshot")
            if {p.name for p in (run / "public_data" / "knowledge").glob("*.json")} != {
                    Path(p).name for p in inputs if p.startswith("public_data/knowledge/")}:
                raise ValueError("receipt does not cover the complete public knowledge snapshot")
            for name in [*source_names, *plugins, *inputs]:
                _checked(_relative(run, name), hashes.get(name))
            spec = _json(run / source_names[1])
            features = _names(spec.get("feature_set"), "features")
            if spec.get("experiment_id") != experiment or features != member["features"]:
                raise ValueError("run spec differs from frozen identity/features")
            dest = stage / "members" / str(i)
            (dest / "plugins").mkdir(parents=True)
            for name in plugins:
                if Path(name).parent != Path("feature_store"):
                    raise ValueError("nested plugin paths are not supported")
                _copy_checked(run / name, hashes[name], dest / "plugins" / Path(name).name)
            if common_inputs is None:
                common_inputs = inputs
                for name in inputs:
                    target = stage / "context" / Path(name).relative_to("public_data")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    _copy_checked(run / name, hashes[name], target)
                ctx = _public_context(stage / "context")
                manifest["genes"] = ctx.genes
                manifest["context_perts"] = ctx.perts
                manifest["train_perts"] = ctx.train_perts
                manifest["anchor_perts"] = [p for p in ctx.perts if p not in set(ctx.train_perts)]
                manifest["anchor_sha256"] = _anchor_hash(ctx)
                if not manifest["anchor_perts"]:
                    raise ValueError("original context has no evaluation anchors")
            elif inputs != common_inputs:
                raise ValueError("ensemble members do not share identical public context")
            model_bytes = (run / source_names[0]).read_bytes()
            if hashlib.sha256(model_bytes).hexdigest() != hashes[source_names[0]]:
                raise ValueError("model source changed before deserialization")
            arrays, columns, index = _model_arrays(pickle.loads(model_bytes), spec, alpha)
            with _plugins(dest / "plugins"):
                for feature in features:
                    registry.get(feature)  # fail before producing an unusable package
            np.savez_compressed(dest / "numeric.npz", **arrays)
            manifest["members"].append({
                "experiment_id": experiment, "alpha": alpha, "full_grid_index": index,
                "run_directory": str(run), "base_commit": member.get("base_commit"),
                "weight": float(weights[i]), "features": features, "columns": columns,
                "feature_params": spec.get("feature_params", {}), "model_type": spec.get("model_type", "ridge"),
                "seed": spec.get("seed", 0), "source_sha256": {k: hashes[k] for k in [*source_names, *plugins, *inputs]},
            })
        manifest["files_sha256"] = {str(p.relative_to(stage)): sha256(p)
                                     for p in sorted(stage.rglob("*")) if p.is_file()}
        _write_json(stage / "manifest.json", manifest)
        stage.rename(out)
    return manifest


def load_export(package: Path, manifest_sha256: str) -> dict:
    package = Path(package)
    manifest = _json(_checked(package / "manifest.json", manifest_sha256))
    if manifest.get("schema_version") != SCHEMA or manifest.get("runtime") != runtime_receipt():
        raise ValueError("frozen schema or runtime/source receipt mismatch")
    files = manifest.get("files_sha256", {})
    actual = {str(p.relative_to(package)) for p in package.rglob("*") if p.is_file()}
    if actual != set(files) | {"manifest.json"}:
        raise ValueError("frozen package has missing or unexpected files")
    for name, pin in files.items():
        _checked(_relative(package, name), pin)
    ctx = _public_context(package / "context")
    if (ctx.genes != manifest.get("genes") or ctx.perts != manifest.get("context_perts") or
            ctx.train_perts != manifest.get("train_perts") or
            [p for p in ctx.perts if p not in set(ctx.train_perts)] != manifest.get("anchor_perts")):
        raise ValueError("frozen gene/context order mismatch")
    if _anchor_hash(ctx) != manifest.get("anchor_sha256"):
        raise ValueError("frozen evaluation anchor identity/hash mismatch")
    return manifest


def _queries(value: dict, ctx: FeatureContext) -> tuple[list[str], dict[str, list[str]]]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "queries"} or value["schema_version"] != SCHEMA:
        raise ValueError("query input accepts only schema_version and queries")
    if not isinstance(value["queries"], list) or not value["queries"]:
        raise ValueError("nonempty query list required")
    ids, targets = [], {}
    for query in value["queries"]:
        if not isinstance(query, dict) or set(query) != {"condition_id", "target_genes"}:
            raise ValueError("query accepts only condition_id and target_genes")
        condition = query["condition_id"]
        if not isinstance(condition, str) or not condition or condition in ids:
            raise ValueError("empty or duplicate query identity")
        tg = _names(query["target_genes"], "query targets")
        if not set(tg) <= set(ctx.genes):
            raise ValueError("query targets outside frozen gene universe")
        if condition in ctx.train_perts:
            raise ValueError("inference queries must be outside original training set")
        if condition in ctx.perts and tg != ctx.target_genes(condition):
            raise ValueError("query would alter original target metadata/order")
        ids.append(condition)
        targets[condition] = tg
    return ids, targets


def _matrix(ctx: FeatureContext, member: dict, perts: list[str], additions: dict[str, list[str]]) -> np.ndarray:
    # Never use FeatureContext.shared or persisted feature matrices. Each batch
    # has fresh Python/module/context caches and the original training data.
    view = _public_context(ctx.public_dir)
    view._targets.update(additions)
    view.perts = list(ctx.perts) + [p for p in additions if p not in ctx.perts]
    original_knowledge = view.knowledge
    view.knowledge = lambda name: dict(view._targets) if name == "targets" else original_knowledge(name)
    np.random.seed(int(member["seed"]))
    # pipeline.run builds the complete training feature batch before evals.
    # Some plugins memoize in ctx.cache or at module scope during that phase.
    # Reproduce that phase without fitting/standardizing/using any new labels.
    build_matrix(view, member["features"], member["feature_params"], view.train_perts, {}, cache_dir=None)
    matrix, columns = build_matrix(view, member["features"], member["feature_params"], perts, {}, cache_dir=None)
    if columns != member["columns"]:
        raise ValueError("computed feature column order differs from frozen model")
    return matrix


def predict_ensemble(package: Path, manifest_sha256: str, query_path: Path, out: Path) -> dict:
    """Write deltas and an immutable receipt from strict target-only metadata."""
    package, query_path, out = Path(package), Path(query_path), Path(out)
    _refuse_output(out, [package], [query_path])
    if out.exists():
        raise ValueError("prediction output must not already exist")
    manifest = load_export(package, manifest_sha256)
    _refuse_output(out, [package, *[Path(m["run_directory"]) for m in manifest["members"]]], [query_path])
    ctx = _public_context(package / "context")
    query_bytes = query_path.read_bytes()
    ids, targets = _queries(json.loads(query_bytes), ctx)
    anchors = manifest["anchor_perts"]
    anchor_pos = {p: j for j, p in enumerate(anchors)}
    predictions = []
    rng_state = np.random.get_state()
    try:
        for i, member in enumerate(manifest["members"]):
            with np.load(package / "members" / str(i) / "numeric.npz", allow_pickle=False) as z:
                if set(z.files) != {"coef", "intercept", "x_mean", "x_std"}:
                    raise ValueError("unexpected frozen numeric arrays")
                n = len(member["columns"])
                coef = _finite(z["coef"], (n,), "coefficients")
                mu = _finite(z["x_mean"], (n,), "feature means")
                sd = _finite(z["x_std"], (n,), "feature scales")
                intercept = _finite(z["intercept"], (), "intercept")
                if not (sd > 0).all():
                    raise ValueError("feature scales must be positive")
            result = np.empty((len(ids), ctx.n_genes), dtype=np.float32)
            with _plugins(package / "members" / str(i) / "plugins"):
                original = None
                if any(p in anchor_pos for p in ids):
                    registry.reload_plugins()
                    original = _matrix(ctx, member, anchors, {})
                for row, pert in enumerate(ids):
                    if pert in anchor_pos:
                        pos = anchor_pos[pert] * ctx.n_genes
                        matrix = original[pos:pos + ctx.n_genes]
                    else:
                        # Freeze the original batch as anchors and compute each
                        # new condition independently of other submitted queries.
                        registry.reload_plugins()
                        matrix = _matrix(ctx, member, anchors + [pert], {pert: targets[pert]})[-ctx.n_genes:]
                    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                        pred = ((matrix - mu) / sd) @ coef + intercept
                    if not np.all(np.isfinite(pred)) or not np.all(np.isfinite(pred.astype(np.float32))):
                        raise ValueError("nonfinite frozen predictions")
                    result[row] = pred.astype(np.float32)
            predictions.append(result)
    finally:
        np.random.set_state(rng_state)
    members = np.stack(predictions)
    combined = np.average(members.astype(np.float64), axis=0,
                          weights=[m["weight"] for m in manifest["members"]]).astype(np.float32)
    if not np.all(np.isfinite(combined)):
        raise ValueError("nonfinite ensemble predictions")
    if out.exists():
        raise ValueError("prediction output must not already exist")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".frozen-predict-", dir=out.parent) as tmp:
        stage = Path(tmp) / "predictions"
        stage.mkdir()
        np.savez_compressed(stage / "predictions.npz", delta=combined, member_delta=members,
                            perts=np.array(ids), genes=np.array(ctx.genes),
                            members=np.array([m["experiment_id"] for m in manifest["members"]]))
        receipt = {"schema_version": SCHEMA, "manifest_sha256": manifest_sha256,
                   "query_sha256": hashlib.sha256(query_bytes).hexdigest(),
                   "predictions_sha256": sha256(stage / "predictions.npz"),
                   "condition_ids": ids, "genes": ctx.genes,
                   "members": [{k: m[k] for k in ("experiment_id", "alpha", "weight")} for m in manifest["members"]],
                   "runtime": manifest["runtime"], "inference_recipe": manifest["inference_recipe"],
                   "anchor_sha256": manifest["anchor_sha256"],
                   "scoring": "none; predictions only, original public training context unchanged"}
        _write_json(stage / "receipt.json", receipt)
        stage.rename(out)
    return receipt
