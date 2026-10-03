#!/usr/bin/env python3
"""Scaling report for a run: worker independence, throughput, tokens, cost,
bottlenecks, duplicated work, and cost projections for larger runs.

    python analyze_run.py [--run DIR] [--json]
"""

import argparse
import json

from genemila.analysis import analyze, render
from genemila.cli_common import add_run_arg, resolve_run


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_run_arg(ap)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    lab = resolve_run(args)
    a = analyze(lab)
    (lab.run_dir / "analysis.json").write_text(json.dumps(a, indent=1))
    text = render(a)
    (lab.run_dir / "analysis.md").write_text(text)
    print(json.dumps(a, indent=1) if args.json else text)


if __name__ == "__main__":
    main()
