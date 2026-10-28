# Mac checks of 17 Oct 2026 (claim #68), step 4, EXTRA diagnostic: the generator of inputs/newbranch_queries.json, the
# code the 02:27 UTC session ran inline at 2026-10-18T02:42:15Z as
#   python3 -I - docs/results/frozen_adapter_check_20261017/inputs/single_targets.txt docs/results/frozen_adapter_check_20261017/inputs/newbranch_queries.json <<'EOF' ... EOF
# saved here verbatim afterwards (its output was re-derived byte for byte by an independent check). It prints
# "31 renamed single-target queries".
import json, sys
syms = [l.strip() for l in open(sys.argv[1]) if l.strip()]
# serialised exactly as tools/frozen_model.py predict_targets() does; ids renamed so predict_ensemble takes the
# anchors-plus-one-new-condition branch instead of the anchor branch
conds = {f"{s}__new": [s] for s in syms}
data = (json.dumps({"schema_version": 1, "queries": [{"condition_id": c, "target_genes": list(t)} for c, t in conds.items()]},
                   indent=2, sort_keys=True) + "\n").encode()
open(sys.argv[2], "wb").write(data); print(len(conds), "renamed single-target queries")
