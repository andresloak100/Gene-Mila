#!/bin/bash
# Block H, the cap (docs/PLAN_H_COMPARISON.md, Money): written once, before anything paid, as one line
# "<cap> <ledger at the start> <UTC date>" with cap = ledger + 15.00; refuses if the file exists, so a stopped or
# resumed block never gets a fresh $15. Only after Andres's one-line confirmation on #41, isolation.txt and tier.txt.
#   bash ~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_h/block_h_cap.sh
. "$(dirname "$0")/block_h_common.sh"
read -r MODE ACCOUNT 2> /dev/null < "$H/isolation.txt"
case "$MODE" in docker|account|none) ;; *) no "$H/isolation.txt must read 'docker', 'account <name>' or 'none' first (plan, Isolation)" ;; esac
read -r TIER 2> /dev/null < "$H/tier.txt"
case "$TIER" in harness|none) ;; *) no "$H/tier.txt must read 'harness' or 'none' first: Andres's word on the harness tier (plan, The task package)" ;; esac
s=$(ledger)
num "$s" || no "ledger unreadable ('$s')"
set -o noclobber
awk -v s="$s" -v d="$(utc)" 'BEGIN { printf "%.2f %s %s\n", int((s + 15) * 100) / 100, s, d }' > "$H/block_h_cap.txt" \
  || no "block_h_cap.txt exists; the cap is written once per block"
echo "- $(utc) block H cap written: $(cat "$H/block_h_cap.txt") (cap, DeepSeek ledger at the start, UTC date); isolation $MODE $ACCOUNT, tier $TIER" >> "$L/progress.md"
cat "$H/block_h_cap.txt"
