#!/usr/bin/env python3
"""Recompute the cumulative spend ledger with the current price table.

Earlier versions priced calls whose served model name was missing from the
price table (e.g. "deepseek-flash") at the pessimistic default ($3 / $15 per
million tokens), which inflated the ledger and can block further runs.

    python reprice_ledger.py            # show old vs corrected totals (changes nothing)
    python reprice_ledger.py --apply    # rewrite the ledger's cost column (keeps a backup)
"""

import argparse
import shutil
import sqlite3

from genemila import REPO_ROOT
from genemila.config import load_config


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    path = REPO_ROOT / cfg["budget"]["ledger"]
    pricing = cfg["pricing"]
    con = sqlite3.connect(path)
    rows = con.execute("SELECT rowid, provider, model, input_tokens, output_tokens, cached_tokens, cost_usd "
                       "FROM spend").fetchall()
    old, new, updates = {}, {}, []
    for rowid, provider, model, tin, tout, tcached, cost in rows:
        old[provider] = old.get(provider, 0.0) + (cost or 0.0)
        if model not in pricing or provider in ("claude_cli",):  # provider-reported costs stay as they are
            new[provider] = new.get(provider, 0.0) + (cost or 0.0)
            continue
        p = pricing[model]
        c = (tcached * p["input_cache_hit"] + max(0, tin - tcached) * p["input_cache_miss"]
             + tout * p["output"]) / 1e6
        new[provider] = new.get(provider, 0.0) + c
        updates.append((c, rowid))
    for prov in sorted(old):
        print(f"{prov:12s} recorded ${old[prov]:.5f}  ->  repriced ${new[prov]:.5f}")
    if args.apply and updates:
        shutil.copy2(path, str(path) + ".bak")
        con.executemany("UPDATE spend SET cost_usd=? WHERE rowid=?", updates)
        con.commit()
        print(f"updated {len(updates)} rows (backup at {path}.bak)")


if __name__ == "__main__":
    main()
