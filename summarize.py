#!/usr/bin/env python3
"""(Re)generate the research summary for a run.

    python summarize.py [--run DIR]             # regenerate the summary (keeps stored query-only scores)
    python summarize.py --query-only            # also evaluate new winners on the query-only set (capped)
    python summarize.py --state                 # print the compressed research state the planner sees
"""

import argparse

from genemila.cli_common import add_run_arg, resolve_run
from genemila.report import finalize, render_markdown
from genemila.research_state import build_state, render_state


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_run_arg(ap)
    ap.add_argument("--query-only", action="store_true")
    ap.add_argument("--state", action="store_true")
    args = ap.parse_args()
    lab = resolve_run(args)
    if args.state:
        print(render_state(build_state(lab)))
        return
    print(render_markdown(finalize(lab, query=args.query_only)))


if __name__ == "__main__":
    main()
