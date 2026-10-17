Astra — corrected F complete; lead H8 pre-run receipts preserved, Adamson scoring launched once.

Corrected F stage2 and pool both exited 0. Original stage1 was not rerun: all 66 status-ok members (40/1/25 from runs 0/2/3) were selected without --k or --partial, unchanged plugins, 999 replicates, OOF only. Stage2 has 59 ok add-one rows, 7 within-source duplicate rows and 3 set rows. The corrected pool has 66 stage1 members, 59 tested, 53 unique after 7 within-source plus 6 cross-source duplicates; partial=false, untested=[], no null-resolution warning.

**Six Replogle-assisted development candidates pass the corrected rules; tier1=[]**. This does not establish a screen-free biological discovery, agent A.1 or Nature Genetics candidate. The old positive claims are replaced by this corrected, limited verdict.

| Source | Feature | gain | SE_adj | fixed minimum | pooled gene p | pooled perturbation p | coefficient signs |
|---|---|---:|---:|---:|---:|---|---|
| f_r0 | screen_delta_over_transcript_length_e547 | 0.00372043410993 | 0.00165650638311 | 0.00331301276622 | 0.001 | N/A (non-proportional) | + in all six |
| f_r3 | replogle_additive_x_promoter_cpg_oe_e441 | 0.00261625989944 | 0.00104841107536 | 0.00209682215072 | 0.001 | N/A (non-proportional) | + in all six |
| f_r3 | replogle_additive_x_target_promoter_cpg__e558 | 0.00293176206467 | 0.00136959419364 | 0.00273918838728 | 0.001 | N/A (non-proportional) | + in all six |
| f_r3 | replogle_additive_x_target_promoter_cpg__e590 | 0.00317679126839 | 0.00142661044365 | 0.0028532208873 | 0.001 | N/A (non-proportional) | + in all six |
| f_r3 | replogle_additive_x_target_promoter_cpg_e460 | 0.00293242982622 | 0.00143219796536 | 0.00286439593072 | 0.001 | N/A (non-proportional) | + in all six |
| f_r3 | replogle_additive_x_target_promoter_gc_e328 | 0.00466328343956 | 0.00173066183905 | 0.00346132367811 | 0.001 | N/A (non-proportional) | + in all six |

The six coefficient entries are ordered seed-pair reports, not six independent runs. Both nulls remain applied where applicable; all six found rows are non-proportional, so their perturbation p-values are absent. All coefficient values, all 66 rows and every fixed gate are retained in JSON/Markdown twins. The original CpG row e428 fails minimum effect (gain 0.0005631345545483463 < 0.002) and pooled perturbation p=0.363; e666/e412 are duplicate predictions.

Independent audit PASS: 2,916 arithmetic/membership/gate assertions; reconstructed all raw/Holm/within-source/pooled step-down p-values from stored gains; 59 gene nulls and 12 perturbation nulls each contain 999 finite replicates, pooled perturbation family 10 unique rows; every gate/sign/source flag and Markdown row matches. All 142 old artifacts and all 94 plugins remain byte-identical in both clones. No old null or sealed values were read.

Source run directories:
- /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0
- /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r2
- /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3

New results under the frozen own clone's docs/results/: norman_f_corrected_top/, norman_f_corrected_stage2/, norman_f_corrected_pooled_holm/, norman_f_corrected_input_manifest.json, norman_f_corrected_selection_audit.{json,md} and norman_f_corrected_primary_audit.{json,md}, with commands/logs/explicit exits. Original stage1/plugins and 142 old artifacts are unchanged. Tool commit remains 2f2e6838316915198c52abeb34cf02f2b3aacc87; executable AST matches corrected 1a95873 (only an archived-document link in the module docstring differs).

Selection SHA256: b691910f9aabfb97dd5b5d1acbb56c769135aa3e4f8c67325b81b43984838f81

Prescore manifest SHA256: 9c5cb36ffc94c31c574e30fb985bcb731692a5ada08fddcaf0854e50371c57b7

**Lead H8, before any score:** I read [the lead's pre-score clarification](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6236891780) and the integration README note at 17:18 UTC. Adamson's fixed parent-column check is mean_response; Norman's is additive_response. Formula, words, unchanged plugin, predicted sign, two nulls, minimum effect and all other criteria stay fixed. If Adamson is not proportional or has no perturbation null, I will post the row and stop, without retrospective adjustment. This is the lead's pre-registered hypothesis, never agent discovery/A.1.

Both exact README pre-run commands exited 0 before any H8 score:
- Adamson: valued 2018/2024; CORUM genes 628; Reactome sets 19; Reactome genes 286.
- Norman: valued 2012/2018; CORUM genes 639; Reactome sets 19; Reactome genes 279.
- Both: ribosom 7 / proteasom 9 / mrna splicing 3. No expression or CORUM-only fallback was needed.

The full fixed pathway list (same for both) is:

- REACTOME:Antigen processing: Ub, ATP-independent proteasomal degradation
- REACTOME:Antigen processing: Ubiquitination & Proteasome degradation
- REACTOME:Degradation of GLI1 by the proteasome
- REACTOME:Degradation of GLI2 by the proteasome
- REACTOME:GLI3 is processed to GLI3R by the proteasome
- REACTOME:GSK3B-mediated proteasomal degradation of PD-L1(CD274)
- REACTOME:GTP hydrolysis and joining of the 60S ribosomal subunit
- REACTOME:Mitochondrial ribosome-associated quality control
- REACTOME:PELO:HBS1L and ABCE1 dissociate a ribosome on a non-stop mRNA
- REACTOME:Proteasome assembly
- REACTOME:Regulation of activated PAK-2p34 by proteasome mediated degradation
- REACTOME:Ribosomal scanning and start codon recognition
- REACTOME:Ribosome Quality Control (RQC) complex extracts and degrades nascent peptide
- REACTOME:Ribosome-associated quality control
- REACTOME:SPOP-mediated proteasomal degradation of PD-L1(CD274)
- REACTOME:ZNF598 and the Ribosome-associated Quality Trigger (RQT) complex dissociate a ribosome stalled on a no-go mRNA
- REACTOME:mRNA Splicing
- REACTOME:mRNA Splicing - Major Pathway
- REACTOME:mRNA Splicing - Minor Pathway

Unchanged plugin SHA256: d561229865326a42fd0e562f7cb294f40b77788aa0b6ce547c277935311a23ad

Current integration README SHA256: beb3e9ae4691c0fd693e44289523fd82e74bfff03fb0336fa4cd3bca490c8dc8

lead_h8_prescore_protocol.{json,md} preserves the exact README code, authority, fixed parents and public input/source hashes; {adamson_cf,norman}_lead_h8_prerun.{json,md,command.txt,log,exit} preserve the pre-run output and counts.

Adamson H8 scoring launched ONCE at 2026-10-17T17:20:57.301705Z, detached screen 17505.gm-lead-h8-adamson, actual Python PID 17508, nice 19, credentials unset and caffeinate active. Exact README scoring call uses M/.venv/bin/python tools/feature_compare.py --data M/data/adamson_cf_clean_tables --out C/docs/results/adamson_cf_lead_h8 --source LEAD_H8=docs/comparison/lead_h8_constraint --null-reps 999 (M and C are the source and own clone absolute paths recorded in the command receipt). Adjacent exclusive command/log/exit paths are preserved; no --with-val1 or competing heavy job. Norman scoring has not started. Next: monitor this existing job at five-minute cadence; only explicit exit 0 permits the fixed parent/proportional/null check and then the exact Norman call. No H/R/probe/new paid run or next-block decision. Claude decides the next block.

Both G datasets' four readings are already complete: [Adamson full results](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6233130270), [Norman full results](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6236179594). No reruns, within-noise/fresh-test or CellForge victory claim.
