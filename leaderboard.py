#!/usr/bin/env python3
"""Rank completed experiments, or show the lineage of one.

    python leaderboard.py [--run DIR] [--top 20] [--all]
    python leaderboard.py --lineage EXP_0012
"""

import argparse

from genemila.cli_common import add_run_arg, resolve_run


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_run_arg(ap)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--all", action="store_true", help="include failed/rejected experiments")
    ap.add_argument("--lineage")
    args = ap.parse_args()
    db = resolve_run(args).db
    if args.lineage:
        for i, e in enumerate(db.lineage(args.lineage)):
            score = "n/a" if e["primary_score"] is None else f"{e['primary_score']:.4f}"
            print(f"{'    ' * i}{'↳ ' if i else ''}{e['experiment_id']} [{e.get('new_feature') or e['kind']}] "
                  f"{score}  {e['hypothesis'][:80]}")
        return
    where = "" if args.all else "WHERE status='completed'"
    rows = db.query(f"SELECT * FROM experiments {where} ORDER BY primary_score IS NULL, primary_score DESC LIMIT ?",
                    (args.top,))
    print(f"{'experiment':<10} {'status':<10} {'score':>8} {'delta':>8} {'model':<7} {'cpu_s':>6} {'provider':<10} features / reason")
    for e in rows:
        s = "" if e["primary_score"] is None else f"{e['primary_score']:.4f}"
        d = "" if e["delta_from_parent"] is None else f"{e['delta_from_parent']:+.4f}"
        extra = ",".join(e["feature_set_json"] or []) if e["status"] == "completed" else (e["failure_reason"] or "")[:60]
        print(f"{e['experiment_id']:<10} {e['status']:<10} {s:>8} {d:>8} {e['model_type'] or '':<7} "
              f"{(e['cpu_s'] or 0):6.1f} {(e['provider'] or ''):<10} {extra}")


if __name__ == "__main__":
    main()
