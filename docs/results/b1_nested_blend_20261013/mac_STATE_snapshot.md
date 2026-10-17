# Dated snapshot before negative-result publication

Current HANDOFF supersedes this historical overview. Source: ~/Documents/Mila/Gene-Mila/genemila_scale_logs/STATE.md.

<!-- CURRENT_STATE_BEGIN -->
# Current Gene-Mila Mac state

Verified 2026-10-14 01:21 UTC (13 October local), Astra/Codex chat1. Current HANDOFF section1 is authoritative;
old notes below are history.

- New Claim30/PR31: user explicitly requests further model improvement; own astra/b1-nested-blend/gene-mila-nested-blend.
- Plan21f50d9 before outcomes; reviewedsource1238dac scanned/published before fitting. Full490passed,8warnings648.89s; focused8passed3.73s.
- One free run starting in own gene-mila-nested-blend/runs/b1_nested_blend_20261013; rootowns sole process,120fits/7200s.
- No other model/controller run or code edits; no duplicate.
- One lambda blends fixed r1/r2 average with additive, learned on INNER gene-hidden OOF predictions only.
- Outer6/7/8 x5, inner3 withseed1000+100*outerseed+fold, originalrecipes/alphas/seeds,120sharedfits/max7200s.
- Gates: MSE improves all3/mean>SD vsfixedE; MSE/top20 mean ratios<=1.01additive; top20<=1.01E;
  Pearson difference>=-.01 eachseed and mean>=-.002. No alternate objective/grid/subset/extra seeds.
- Next: wait soleprocess, independently verify all15learnedweights/inner/outerarrays/metrics/gates/hashes, archive every outcome.
- Then current docs/Claude handoff; keep originalB1, no extra objective/weight/seed/alpha or paidcall.
- Root owns launcher/plan/Git/docs/sharedstate; child owns newrunner/tests; reviewer read-only, no fitting/API.
- Claims26/28 closed; PR27/29 merged0db04e42/6e17ff8c. Their original data/results/closed grids are preserved.
- Delivered frozenB1 unchanged. New reused-cohort calibration is development, not independent validation/CellForge evidence.
- Main ~/Documents/Mila/Gene-Mila/gene-mila stays4562af5b; STOP present. No protected/data/private/split/account changes.
- SharedDeepSeek ledger43.599822392/cap48, provider-filtered; no paid calls authorized/needed for Claim30.
- Evaluatoraccount/cohort work remainsdeferred. B3 and negativeClaim24 grid stayclosed.
<!-- CURRENT_STATE_END -->
