"""Hash every feature block of a run's audited pool (training + visible validation perturbations). Read-only.
Run in separate processes and compare the outputs to find features whose values change between processes."""
import hashlib, json, sys
from pathlib import Path
import numpy as np
REPO = Path.home() / "Documents/Mila/Gene-Mila/gene-mila"
sys.path.insert(0, str(REPO))
from genemila.features import registry
from genemila.features.api import FeatureContext
from genemila.pipeline import feature_blocks
run = Path(sys.argv[1]).resolve(); feats = json.loads(Path(sys.argv[2]).read_text())[run.name]
registry.load_plugins(run / "feature_store")
ctx = FeatureContext(run / "public_data")
perts = list(ctx.train_perts) + [p for p in getattr(ctx, "val_perts", []) if p not in ctx.train_perts]
out = {}
for f in feats:
    try:
        b = np.asarray(feature_blocks(ctx, [f], {}, perts, {}, None, {})[f], dtype=np.float64)
        out[f] = hashlib.md5(np.round(b, 10).tobytes()).hexdigest() + f" sum={float(np.nansum(b)):.10g}"
    except Exception as e:
        out[f] = f"ERROR {type(e).__name__}: {e}"[:160]
print(json.dumps(out, indent=0, sort_keys=True))
