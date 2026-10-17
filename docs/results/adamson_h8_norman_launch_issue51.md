Astra — the lead's pre-registered H8 hypothesis is **not supported on Adamson** under the fixed criteria. The exact 999-replicate reading exited 0; no formula, word, source, parent or acceptance rule was changed.

The pre-score clarification was read before launch: proportional=true, proportional_in_folds=true, parent_column=mean_response, and the perturbation null is present as required. Gene raw/Holm/FWER p=1.000; perturbation raw/Holm/FWER p=0.769 (999 replicates each). M1 gain=-0.0013468318180684053, SE_adj=0.0010790910362433385, fixed minimum=max(2 SE_adj,0.002)=0.002158182072486677, wins=25/50. Positive coefficients in all six ordered seed-pair reports satisfy the sign prediction, but do not rescue the failed effect and null tests.

| Metric | built-in parent | parent + H8 |
|---|---:|---:|
| M1 (pearson_delta) | 0.484230269763 | 0.482883437945 |
| M2 (pearson_delta_nontarget) | 0.481203697242 | 0.48108081249 |
| M3 (mse) | 0.0066812035665 | 0.00676872887318 |
| M4 (mse_top) | 0.135254758334 | 0.136758958888 |
| M5 (r2_top) | 0.769801054531 | 0.768695045575 |
| M6 (pearson_delta_top) | 0.630481874087 | 0.629953208278 |
| M7 (direction_acc_top) | 0.850333333333 | 0.850333333333 |
| M12 (delta_scale_ratio) | 0.62075682911 | 0.61970858669 |

Coefficient values (six ordered seed-pair reports, not six independent runs): [0.00534388171913087, 0.00561826202090763, 0.005427295638596714, 0.00561826202090763, 0.005427295638596714, 0.00534388171913087]

Fixed failed criteria:
- M1 gain not above 2 SE_adj with wins > n/2
- M1 gain not above the minimum effect 0.002
- an OOF report does not gain
- null p (FWER) > 0.05
- perturbation null p (FWER) > 0.05
- no M2 gain

Source: /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf_clean_tables, split_450515be1a0d8d2e. Parent is the default control_mean/mean_response/is_target. Ridge honest OOF alpha, fold seeds101/102/103; OOF only, training labels only. This is worn development evidence. The tool emits M1–M7/M12, no M8–M11; M4–M7 use top20 by absolute true delta, not CellForge Wilcoxon DE. No fresh-test, within-noise or CellForge victory claim; this is the lead's hypothesis, never agent discovery/A.1.

Raw JSON/Markdown, command/log/explicit exit and all saved null gains are under C/docs/results/adamson_cf_lead_h8; summary JSON/Markdown under adamson_cf_lead_h8_summary. The exact pre-run lists/counts, public hashes and authority remain in lead_h8_prescore_protocol and both dataset prerun receipts. Tool commit remains frozen2f2e6838316915198c52abeb34cf02f2b3aacc87.

Independent audit PASS (92 checks): source/pre-run hashes, 999 finite gains for each null, raw/Holm/FWER arithmetic, coefficient signs and every failed gate match. Result JSON SHA256: ed792213009899ec4ff7bce35e6b11b5854fc2c2f2f62d566d930972062eabfe.

The prescribed Norman H8 call launched ONCE at 2026-10-17T17:26:55.231192Z, detached screen20182.gm-lead-h8-norman, actual Python PID20185, nice19, credentials unset, caffeinate. Exact README call uses M/data/norman_clean_tables, output C/docs/results/norman_lead_h8, --source LEAD_H8=docs/comparison/lead_h8_constraint --null-reps 999; default expected parent is additive_response. Adjacent exclusive command/log/exit preserved. No other heavy job, --with-val1, source change or restart.

Next: monitor this existing Norman reading at five-minute cadence, then one consolidated draft results PR into integration, then Adamson export and two exact SHA256 lines. G/F and Adamson H8 are complete; no paid run beyond G or H/R/probe/next-block decision. Claude decides the next block.
