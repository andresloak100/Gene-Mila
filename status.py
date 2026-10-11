#!/usr/bin/env python3
"""Show the live state of a run: python status.py [--run runs/<id>]"""

import argparse
import time

from genemila.cli_common import add_run_arg, resolve_run


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    add_run_arg(ap)
    ap.add_argument("--watch", type=float, help="refresh every N seconds")
    args = ap.parse_args()
    while True:
        lab = resolve_run(args)
        db = lab.db
        run = db.query("SELECT * FROM runs LIMIT 1")[0]
        c = db.count_by_status()
        best = db.best()
        llm = db.llm_totals()
        now = time.time()
        left = (run["deadline"] or now) - now
        print(f"run {lab.run_id}  dataset {lab.dataset}  workers {run['workers']}  "
              f"{'finished' if run['finished_at'] else f'time left {max(0, left):.0f}s'}")
        print("status: " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))
        if best:
            print(f"best: {best['experiment_id']} score={best['primary_score']:.4f} "
                  f"features={best['feature_set_json']}")
        active = db.query("SELECT experiment_id, status, worker_id, hypothesis FROM experiments WHERE status IN "
                          "('claimed','implementing','testing','running') ORDER BY worker_id")
        for a in active:
            print(f"  {a['worker_id']} {a['experiment_id']} [{a['status']}] {a['hypothesis'][:70]}")
        print(f"LLM: {llm['calls']} calls, in {llm['input_tokens']} / out {llm['output_tokens']} / "
              f"cached {llm['cached_tokens']} tokens, ${llm['cost_usd']:.4f}")
        if not args.watch:
            break
        time.sleep(args.watch)
        print()


if __name__ == "__main__":
    main()
