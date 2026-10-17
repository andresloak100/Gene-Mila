"""Block H tooling (docs/ROADMAP.md D6, docs/FEATURE_COMPARISON_PROTOCOL.md A3 and A4): the ledger proxy that holds
the key and counts spend, the two foreign-system runners (Biomni's A1 agent, an autoresearch-style Claude Code loop) on
a task package, and the hand-back collector that turns a finished session into `tools/feature_compare.py --source`
files. Nothing here is lab code: the lab's own runs never import it."""
