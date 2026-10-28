#!/usr/bin/env python3
"""Mac checks of 17 Oct 2026 (claim #68), step 4: the adapter check's inputs, from the frozen package's metadata only.

Reads <pkg>/manifest.json (anchor_perts) and <pkg>/context/knowledge/targets.json, as verification_driver.py builds its
queries, and writes:
  single_targets.txt         the single-gene anchors' symbols in anchor order (condition id == symbol for all of them),
                             one per line: the --target list for `tools/frozen_model.py predict-targets`
  pairs_queries.json         the pair anchors, serialised exactly as tools/frozen_model.py predict_targets() serialises
  all_anchors_queries.json   all anchors in anchor order, same serialisation (expected byte-identical to the export's
                             original_target_only_queries.json, whose sha256 is the export's query_sha256)
No prediction, label or score is read.
"""
import json
import sys
from pathlib import Path


def serialise(conditions: dict) -> bytes:
    # tools/frozen_model.py predict_targets(), verbatim
    return (json.dumps({"schema_version": 1, "queries": [
        {"condition_id": c, "target_genes": list(t)} for c, t in conditions.items()]}, indent=2, sort_keys=True)
        + "\n").encode()


pkg, out = Path(sys.argv[1]), Path(sys.argv[2])
anchors = json.loads((pkg / "manifest.json").read_text())["anchor_perts"]
targets = json.loads((pkg / "context" / "knowledge" / "targets.json").read_text())
singles = [p for p in anchors if len(targets[p]) == 1]
pairs = [p for p in anchors if len(targets[p]) != 1]
assert all(p == targets[p][0] for p in singles), "a single-gene anchor's id differs from its symbol"
(out / "single_targets.txt").write_text("".join(f"{p}\n" for p in singles))
(out / "pairs_queries.json").write_bytes(serialise({p: targets[p] for p in pairs}))
(out / "all_anchors_queries.json").write_bytes(serialise({p: targets[p] for p in anchors}))
print(f"anchors {len(anchors)}: single-gene {len(singles)} (predict-targets), pairs {len(pairs)} (predict)")
