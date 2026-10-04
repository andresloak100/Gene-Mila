#!/usr/bin/env python3
"""Results table in CellForge's Table 1 layout, and the metric calibration behind it.

    python results_table.py build --runs runs/adamson_* --out docs/results
    python results_table.py build --runs runs/adamson_w4_* runs/adamson_w8_* --part val2 --dataset-key adamson
    python results_table.py calibrate --data data/adamson_cf --dataset-key adamson --out docs/results

`build` reads each run's summary.json (best model and starting model, CellForge
metrics on the held-out perturbations), refits the paper's simple baselines on
the same split, adds the paper's reported rows and writes results_table.md
and results_table.json. Re-run it after every run to refresh the table.
`calibrate` scores the simple baselines under several candidate metric
definitions and says which one reproduces the paper's rows.
"""

import argparse
import json
from pathlib import Path

from genemila import REPO_ROOT

PAPER = REPO_ROOT / "docs" / "results" / "cellforge_table1.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--runs", nargs="+", required=True, help="run directories (each with summary.json)")
    b.add_argument("--part", default="val2", choices=("val1", "val2"))
    b.add_argument("--dataset-key", help="paper dataset to quote: adamson | norman | srivatsan (auto from the name)")
    b.add_argument("--paper", default=str(PAPER))
    b.add_argument("--label", default="Gene-Mila")
    b.add_argument("--out", default=str(REPO_ROOT / "docs" / "results"))
    c = sub.add_parser("calibrate")
    c.add_argument("--data", required=True, help="dataset bundle directory")
    c.add_argument("--part", default="val2", choices=("val1", "val2"))
    c.add_argument("--dataset-key", help="paper dataset whose rows to compare against")
    c.add_argument("--paper", default=str(PAPER))
    c.add_argument("--out", default=str(REPO_ROOT / "docs" / "results"))
    args = ap.parse_args()

    from genemila.benchmark import table
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.cmd == "build":
        t = table.build([Path(r) for r in args.runs], Path(args.paper), args.dataset_key, args.part, args.label)
        md = table.render(t)
        (out / "results_table.md").write_text(md)
        (out / "results_table.json").write_text(json.dumps(t, indent=1, default=str))
        print(md)
        print(f"\nwritten to {out / 'results_table.md'}")
    else:
        cal = table.calibration(Path(args.data), args.part)
        paper = json.loads(Path(args.paper).read_text()) if Path(args.paper).exists() else {}
        key = args.dataset_key or next((k for k in paper.get("datasets", {}) if k in Path(args.data).name.lower()), None)
        rows = paper.get("datasets", {}).get(key, {}).get("rows") if key else None
        md = table.render_calibration(cal, rows)
        name = f"calibration_{Path(args.data).name}_{args.part}"
        (out / f"{name}.md").write_text(md)
        (out / f"{name}.json").write_text(json.dumps(cal, indent=1))
        print(md)
        print(f"\nwritten to {out / (name + '.md')}")


if __name__ == "__main__":
    main()
