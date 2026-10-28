# Replogle 2022 K562 genome-wide: eligibility manifest, 17 October 2026 (provisional universe)

The fresh-test eligibility manifest of [`docs/PLAN_R_FRESH_TEST.md`](../../PLAN_R_FRESH_TEST.md) sections 2 and 3,
built on Andres's Mac by the lab-code owner's Mac session (claim [#68](https://github.com/andresloak100/Gene-Mila/issues/68)),
free, `nice -n 19`, from the clone `gene-mila-macchecks` at `cfa8034`. Only the file's `obs` and `var` tables were read
(the tool's guard refuses every other key). No `--draw` and no `--seed`: PLAN_R section 8 has not yet named a seed, so
this manifest fixes no draw. PLAN_R sections 3 and 8 ask for the seed, the universe and the R1 file to be fixed before
the manifest is built; this is a provisional eligibility count made before that, as item 4 of the lead's handover of
17 October 18:30 UTC (HANDOFF.md section 1) asks. The final manifest is built only after section 8 is filled in.

**The gene universe is provisional.** PLAN_R section 8 fixes the universe by the `genes` list of the Adamson arm's
frozen export `manifest.json`, with that manifest's sha256. No Adamson frozen export exists yet. This run's universe
is the Adamson clean bundle's public gene list instead: `data/adamson_cf_clean/public.npz['genes']` in the main
checkout (2,055 symbols, in that order; `public.npz` sha256 `e8908ef34d851c1111556be7b8d97eb511bc7554513683a0cf3844248d153718`,
equal to the bundle manifest's record), written to
[`provisional_gene_universe.json`](provisional_gene_universe.json) (sha256
`b9eaeaaa666966f920136b9899dc4c9ede34470825a2d97277e9ac0b857c5a60`). Nothing under `private/` and no `splits.json`
was read. Once the Adamson arm's frozen export exists, the manifest is rebuilt against that export's `genes` and
the counts below are superseded. If that export comes from a different bundle (for example `data/adamson_cf`), its
universe may differ.

## The file

`~/Documents/Mila/Gene-Mila/data_downloads/replogle2022/ReplogleWeissman2022_K562_gwps.h5ad`, 8,805,466,154 bytes:

- sha256 `d3269d9c863d96555eba768b42ab330cc1b57493cd33b4ac8fe7fbab8278f104` (`nice -n 19 shasum -a 256`, 41 s; log
  [`docs/mac/mac_checks_20261017/replogle_sha256.txt`](../../mac/mac_checks_20261017/replogle_sha256.txt))
- md5 `13db594f8f1d2ccb88fec44a13e414dc`, equal to the Zenodo 13350497 record in PLAN_R section 1, so this sha256
  belongs to the recorded file (log `docs/mac/mac_checks_20261017/replogle_md5.txt`; that log writes the path as
  `<file>`, the same path as in `replogle_sha256.txt`)
- 1,989,578 cells, 8,248 measured genes; labels from `obs['perturbation']` (9,867 distinct labels, 75,328 control
  cells), symbols from `var['gene_name']`

## Inputs

| Argument | File | sha256 | Size |
|---|---|---|---|
| `--exclude adamson=` | `data/adamson_cf_clean/knowledge/targets.json` | `e0795293a743ca84d49b8a2cb74b861c30359ed890990d366f7035655fd47f3b` | 88 targets |
| `--exclude norman=` | `data/norman_clean/knowledge/targets.json` | `f02c03f13588ea93b8a14a7979e9c31b8bc317d6cb18b9c24e38362b3bb7662c` | 102 target genes |
| `--frozen-manifest` | `provisional_gene_universe.json` (above) | `b9eaeaaa…5a60` | 2,055 genes |
| `--panel` | `data/adamson_cf_clean/knowledge/targets.json` | as above | 88 targets |
| `--gene-sets` | `data/adamson_cf_clean/knowledge/gene_sets.json` | `2221426e64ee8323044a7a9e2a415ba907210aebf121b5deb49d60a984ec1d88` | 418 Reactome or CORUM classes hold a panel target |
| `--hgnc` | not given: no HGNC file in `data_downloads` (`find -iname '*hgnc*'` found nothing) | | mapping off |

The three bundle files' sha256 equal the records in their bundles' `manifest.json`. Both the tool's docstring and
PLAN_R section 3 make the training panel the bundle's whole target list ("The panel is the bundle's whole target list;
no split file is read"), so the full `targets.json` is the intended input, not a stand-in. `public.npz` also carries
a train-only list (`train_perts`), but PLAN_R does not use it.

The exact command is in [`command.txt`](command.txt), its output in [`manifest_run.log`](manifest_run.log) (8.1 s wall,
206 MB maximum resident set size, peak memory footprint 157 MB, exit 0).

## Counts ([`manifest/manifest.json`](manifest/manifest.json), sha256 `8a37ef580ed7753421456fad5b6a44bfcd9f84c57670d5fe0c468c32b1d61dc6`; reading [`manifest/manifest.md`](manifest/manifest.md))

| | |
|---|---:|
| labels | 9,867 |
| targets (labels other than the control, grouped by symbol) | 9,866 |
| **eligible** | **1,820** |
| eligible, in-distribution (a Reactome or CORUM class holding an Adamson panel target) | **1,331** |
| eligible, other | 489 |
| common gene panel (universe genes the cohort measures through exactly one column) | 1,938 (0 ambiguous) |

| Exclusion reason (a target can have several) | Targets |
|---|---:|
| outside the frozen gene universe | 7,929 |
| norman target | 85 |
| adamson target | 82 |
| fewer than 20 cells | 79 |
| label does not name exactly one gene | 11 (see the note below: all 11 are single genes outside the universe) |

Eligible targets have 20 to 1,091 cells (median 171). The Adamson and Norman matches do not overlap. Of the 88
Adamson targets, 82 appear among the cohort's labels; of the 102 Norman target genes, 85.

**The ≥ 30 rule (PLAN_R section 3): 1,331 in-distribution eligible targets before any R1 exclusion, well above 30.**
R2's own count is fixed only after `--exclude r1=` (PLAN_R section 2), so whether R2 is powered is read then. The essential-gene library file (R1) is not under `~/Documents/Mila/Gene-Mila/data_downloads` (`find
~/Documents/Mila/Gene-Mila/data_downloads -iname '*essential*'` found nothing; nothing was downloaded). If it stays absent, section 2's fallback applies:
`--role both` alternates ranks, so the two halves would hold 666 and 665 in-distribution targets, both ≥ 30.

## Notes for the lead

1. **The 11 "label does not name exactly one gene" targets are single genes.** They are SGK3, SGMS1, SGO1, SGO2,
   SGPL1, SGPP1, SGSH, SGSM2, SGSM3, SGTA and SGTB. With HGNC off, `label_tokens` in `tools/replogle_slice_manifest.py`
   drops any token that matches the guide-suffix rule `external_screen._SUFFIX` (`sg\w*`, case-insensitive) and is
   not a known gene name. These symbols are in neither the universe nor the excluded sets, so each label is left with
   no gene token. None of the 11 is in the 2,055-gene universe, so the eligible counts are unchanged: all 11 are
   ineligible either way. The by-reason line should read outside the universe 7,940, not exactly one gene 0. With
   `--hgnc` they would be known gene names and kept. The ingest (`genemila/data/real.py`, `_is_suffix`) already
   reads an `sg…` token as a guide only before nothing, a number, a measured gene or a control label; reusing that
   rule in the manifest tool would fix this without HGNC. The tool was not changed here.
2. Without HGNC, a cohort label under a current symbol whose universe gene keeps its retired 2016 symbol (PLAN_R's
   example: SRPRA in the cohort, SRPR in the universe) is counted outside the universe. A development target written
   under a different symbol than the cohort's would also escape the exclusion. The final manifest needs the HGNC
   complete set (PLAN_R section 3); it is not under `data_downloads`.
3. No draw and no `--exclude r1=`: the seed, the R1 file and the final universe are all section 8 items still open.
