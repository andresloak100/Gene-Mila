#!/usr/bin/env python3
"""Make ONE minimal DeepSeek API request to verify connectivity and pricing math.

    python deepseek_check.py

Reads DEEPSEEK_API_KEY from the environment. Never prints the key. The call
is recorded in the cumulative spend ledger and counts against the budget.
"""

import json
import os
import sys

from genemila import REPO_ROOT
from genemila.config import load_config
from genemila.llm import LLMGateway, SpendLedger
from genemila.db import Database
from genemila.providers.openai_compat import DeepSeekProvider


def main():
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY is not set in this environment.")
        return 2
    cfg = load_config()
    (REPO_ROOT / "runs").mkdir(exist_ok=True)
    db = Database(REPO_ROOT / "runs" / "api_checks.db")
    gw = LLMGateway(db, cfg, "deepseek_check", SpendLedger(REPO_ROOT / cfg["budget"]["ledger"]))
    prov = DeepSeekProvider(model=cfg["worker"]["model"], timeout_s=60)
    resp = gw.call(prov, "complete", role="worker", max_tokens=5, est_input_tokens=30,
                   system="Reply with one word.", user="Say OK.")
    cost = gw.cost(resp.model, resp.usage)
    print(json.dumps({"ok": True, "model": resp.model, "reply": resp.text.strip()[:20],
                      "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
                      "cached_tokens": resp.usage.cached_tokens, "estimated_cost_usd": round(cost, 8),
                      "cumulative_deepseek_spend_usd": round(gw.ledger.total("deepseek"), 6)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
