#!/bin/bash
# Block D, the cap (docs/PLAN_D_DISCOVERY_ADAMSON.md, Money): written once, before anything paid, as one line
# "<cap> <ledger at the start> <UTC date>" with cap = ledger + <amount>; refuses if the file exists, so a stopped or
# resumed block never gets a fresh amount. Only after Andres's typed words naming the amount (his "go discovery, cap
# $10" of 2026-10-18 02:41 UTC in the project chat), copied into the plan's dated note.
#   bash ~/Documents/Mila/Gene-Mila/genemila_scale_logs/block_d/block_d_cap.sh 10
AMOUNT="${1:-10}"
case "$AMOUNT" in ''|*[!0-9.]*|*.*.*) echo "usage: $0 <dollars over the ledger, e.g. 10>"; exit 1 ;; esac
L="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"; LEDGER="$HOME/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite"
s=$(sqlite3 "$LEDGER" "select round(coalesce(sum(cost_usd),0),6) from spend where provider='deepseek'")
case "$s" in ''|*[!0-9.]*|*.*.*) echo "NOT DONE: ledger unreadable ('$s')"; exit 1 ;; esac
mkdir -p "$L/block_d"
set -o noclobber
awk -v s="$s" -v a="$AMOUNT" -v d="$(date -u +%Y-%m-%dT%H:%MZ)" 'BEGIN { printf "%.2f %s %s\n", int((s + a) * 100) / 100, s, d }' \
  > "$L/block_d/block_d_cap.txt" || { echo "NOT DONE: block_d_cap.txt exists; the cap is written once per block"; exit 1; }
echo "- $(date -u +%Y-%m-%dT%H:%MZ) block D cap written: $(cat "$L/block_d/block_d_cap.txt") (cap, DeepSeek ledger at the start, UTC date; Andres's amount \$$AMOUNT)" >> "$L/progress.md"
cat "$L/block_d/block_d_cap.txt"
