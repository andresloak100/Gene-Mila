# External screen ReplogleWeissman2022_K562_gwps.h5ad

CRISPRi screen deltas, sign -1 (this bundle is CRISPRa): perts[gene].delta = mean over cells of log1p(10,000 x counts / cell total) of that screen's cells of the perturbation minus its own control mean, over this bundle's genes in bundle order (null where unmeasured there); source: CRISPRi Perturb-seq screen ReplogleWeissman2022_K562_gwps.h5ad. The screen's modality (CRISPRi) differs from this bundle's (CRISPRa), so a target's response here is expected to point the other way: multiply a target's delta by sign (-1) before using it as that target's predicted change; correlations between rows do not depend on the sign. A perturbation of several genes has a row only when every target has one: the sum of its targets' deltas.

Source: 1,989,578 cells x 8,248 genes (dense X, 8.81 GB, md5 13db594f8f1d2ccb88fec44a13e414dc), labels from obs['perturbation'] (9867 distinct), gene symbols from var['gene_name'], built 2026-10-11 in 249 s. Control labels ['control'] (75,328 cells); raw counts normalised: mean over cells of log1p(10,000 x counts / cell total). Screen modality CRISPRi, bundle modality CRISPRa: sign -1, since the two differ: a target's response in the bundle is expected to point against the screen's, so a consumer multiplies a target's own delta by -1 before using it as that target's predicted change (correlations between rows do not depend on the sign).

Bundle genes measured in the screen: 2,028 of 2,083. Bundle targets with an external response: 85; missing: 17 (ATL1, CDKN1A, CKS1B, CNNM4, COL1A1, IGDCC3, MAML2, MAP2K6, PRTG, PTPN13, RUNX1T1, S1PR2, SLC4A1, SLC6A9, TGFBR2, UBASH3A, UBASH3B). Labels naming two or more genes were skipped: 0; labels naming a bundle target plus an unrecognised token were skipped as ambiguous: 0; labels matching no bundle target: 9781. Aliases (bundle symbol = screen symbol): AC006262.5=IGFL2-AS1, AES=TLE5, AP001171.1=LINC02573, APOA1BP=NAXE, ASNA1=GET3, ATP5A1=ATP5F1A, ATP5B=ATP5F1B, ATP5C1=ATP5F1C, ATP5D=ATP5F1D, ATP5F1=ATP5PB, ATP5G1=ATP5MC1, ATP5G3=ATP5MC3, ATP5H=ATP5PD, ATP5J2=ATP5MF, ATP5O=ATP5PO, ATPIF1=ATP5IF1, C11orf31=SELENOH, C11orf73=HIKESHI, C14orf166=RTRAF, C14orf2=ATP5MPL, C16orf13=METTL26, C17orf89=NDUFAF8, C19orf24=FAM174C, C19orf43=TRIR, C19orf60=REX1BD, C19orf70=MICOS13, C20orf24=RAB5IF, C22orf29=RTL10, C6orf48=SNHG32, C7orf73=STMP1, C8orf59=RBIS, C9orf142=PAXX, CCDC109B=MCUB, FAM173A=ANTKMT, FAM195A=MCRIP2, FAM60A=SINHCAF, FAM96A=CIAO2A, FAM96B=CIAO2B, GLTSCR2=NOP53, HN1=JPT1, ILF3-AS1=ILF3-DT, KIAA0101=PCLAF, LINC00152=CYTOR, LINC00493=SMIM26, LINC00657=NORAD, LINC00998=SMIM30, LINC01420=NBDY, MESDC2=MESD, MINOS1=MICOS10, MUM1=PWWP3A, MYEOV2=COPS9, NCBP2-AS2=NCBP2AS2, RP11-1094M14.11=SNHG30, RP11-301G19.1=AL713998.1, RP11-544A12.8=AL157938.3, RP11-620J15.3=GIHCG, RP11-717F1.1=AC079801.1, RP5-1171I10.5=AC004687.1, RTFDC1=RTF2, SELK=SELENOK, SEP15=SELENOF, SEPP1=SELENOP, SEPT11=SEPTIN11, SEPT2=SEPTIN2, SEPT6=SEPTIN6, SEPT7=SEPTIN7, SEPT9=SEPTIN9, SEPW1=SELENOW, SGOL1=SGO1, SHFM1=SEM1, SKIV2L2=MTREX, SSSCA1=ZNRD2, STRA13=CENPX, TCEB1=ELOC, TOPORS-AS1=SMIM27, TROVE2=RO60, UFD1L=UFD1, USMG5=ATP5MD, UTP11L=UTP11, VIMP=SELENOS, WBP5=TCEAL9, WBSCR22=BUD23, WHSC1L1=NSD3, ZCCHC11=TUT4; targets matched through one: none; genes measured through one: AC006262.5, AES, AP001171.1, APOA1BP, ASNA1, ATP5A1, ATP5B, ATP5C1, ATP5D, ATP5F1, ATP5G1, ATP5G3, ATP5H, ATP5J2, ATP5O, ATPIF1, C11orf31, C11orf73, C14orf166, C14orf2, C16orf13, C17orf89, C19orf24, C19orf43, C19orf60, C19orf70, C20orf24, C22orf29, C6orf48, C7orf73, C8orf59, C9orf142, CCDC109B, FAM173A, FAM195A, FAM60A, FAM96A, FAM96B, GLTSCR2, HN1, ILF3-AS1, KIAA0101, LINC00152, LINC00493, LINC00657, LINC00998, LINC01420, MESDC2, MINOS1, MUM1, MYEOV2, NCBP2-AS2, RP11-1094M14.11, RP11-301G19.1, RP11-544A12.8, RP11-620J15.3, RP11-717F1.1, RP5-1171I10.5, RTFDC1, SELK, SEP15, SEPP1, SEPT11, SEPT2, SEPT6, SEPT7, SEPT9, SEPW1, SGOL1, SHFM1, SKIV2L2, SSSCA1, STRA13, TCEB1, TOPORS-AS1, TROVE2, UFD1L, USMG5, UTP11L, VIMP, WBP5, WBSCR22, WHSC1L1, ZCCHC11. Targets with fewer than 20 cells in the screen get no row: none.

Per target: cells pooled, external labels pooled, mean absolute delta over the measured genes, the delta of the target gene itself (a knockdown should be negative), and the largest absolute deltas.

| target | cells | labels | mean abs delta | own delta | largest deltas |
|---|---|---|---|---|---|
| AHR | 128 | AHR | 0.0380 | n/a | MCM3 -0.19, PPP1CC -0.18, MBD4 -0.17, CKS1B -0.16, PPIB -0.16 |
| ARID1A | 271 | ARID1A | 0.0331 | -0.158 | C1QBP -1.02, HBG2 +0.46, HBZ +0.35, MRPS15 +0.23, TXNIP -0.23 |
| ARRDC3 | 129 | ARRDC3 | 0.0382 | n/a | HBZ -0.31, ODC1 +0.23, HBG2 -0.19, MDK +0.18, CYC1 +0.17 |
| BAK1 | 92 | BAK1 | 0.0438 | -0.105 | DDX52 +0.20, TXNIP +0.18, LSM10 -0.18, TMEM14C -0.18, ETF1 +0.18 |
| BCL2L11 | 252 | BCL2L11 | 0.0277 | -0.067 | ADRM1 -0.18, PSMD11 +0.14, PSMB4 +0.13, TUBA1C +0.12, CCT4 +0.12 |
| BCORL1 | 212 | BCORL1 | 0.0288 | +0.004 | MCTS1 -0.25, PSMA5 -0.12, RNASEH1 +0.12, SLBP -0.11, ATP5B -0.11 |
| BPGM | 167 | BPGM | 0.0324 | -0.100 | SPATC1L -0.36, BTG1 -0.21, SLC25A6 +0.14, HBG1 -0.13, PLK1 -0.12 |
| CBFA2T3 | 305 | CBFA2T3 | 0.0353 | -0.154 | HBZ +1.03, HBG2 +0.89, VIM -0.58, HBG1 +0.57, APOE -0.43 |
| CBL | 206 | CBL | 0.0365 | -0.175 | HBZ -0.46, HBG2 -0.33, MYL4 -0.28, APOE -0.25, PIM1 +0.25 |
| CDKN1B | 222 | CDKN1B | 0.0283 | -0.118 | HBG2 -0.34, HBZ -0.19, HBG1 -0.18, ATP6V0B -0.13, SDHC -0.12 |
| CDKN1C | 153 | CDKN1C | 0.0343 | -0.158 | HIST1H4C +0.22, KIAA0101 +0.17, CDKN1C -0.16, DUT +0.15, GUK1 -0.15 |
| CEBPA | 89 | CEBPA | 0.0444 | n/a | HBG2 +0.31, PRSS57 -0.22, PMF1 +0.20, ATF4 -0.19, AC079466.1 -0.19 |
| CEBPB | 172 | CEBPB | 0.0370 | -0.216 | DNMT1 -0.25, CEBPB -0.22, CKB -0.21, HBD -0.19, MALAT1 -0.18 |
| CEBPE | 166 | CEBPE | 0.0308 | n/a | TBX1 +0.17, PYCR1 +0.15, RBM17 +0.15, PRDX4 +0.14, XPO1 -0.12 |
| CELF2 | 217 | CELF2 | 0.0297 | -0.660 | CELF2 -0.66, NDUFV2 +0.13, GNL3 +0.12, HBG2 +0.12, TFRC +0.11 |
| CITED1 | 166 | CITED1 | 0.0327 | n/a | HBZ -0.23, PUM1 -0.14, YWHAH -0.14, TUBA1C +0.14, MRPL27 +0.13 |
| CLDN6 | 101 | CLDN6 | 0.0383 | -0.080 | C19orf24 +0.17, ALYREF +0.16, C16orf13 -0.15, LCP1 +0.15, PPP1CB +0.14 |
| CNN1 | 432 | CNN1 | 0.0200 | n/a | GAL -0.15, SMARCA5 +0.10, MTCH1 +0.10, RNASEH2B +0.09, DTD1 +0.08 |
| COL2A1 | 121 | COL2A1 | 0.0374 | -0.259 | COL2A1 -0.26, HBG2 -0.24, CD164 +0.23, SEPT7 +0.18, BIRC5 -0.18 |
| CSRNP1 | 216 | CSRNP1 | 0.0294 | n/a | OSTC +0.12, FABP5 -0.12, TXNIP +0.12, DPH3 -0.12, RAC3 -0.12 |
| DLX2 | 311 | DLX2 | 0.0267 | n/a | APOE -0.58, APOC1 -0.42, GYPC -0.38, TMEM219 -0.33, HBG2 -0.27 |
| DUSP9 | 1,351 | DUSP9 | 0.0122 | n/a | HBG2 -0.08, HBG1 -0.07, HBZ -0.06, SEC11A -0.05, ZBTB8OS -0.05 |
| EGR1 | 374 | EGR1 | 0.0281 | -0.050 | HBZ +0.32, HBG2 +0.15, HBD +0.15, TYMS +0.14, PHF19 +0.14 |
| ELMSAN1 | 551 | ELMSAN1 | 0.0184 | -0.020 | APOE -0.11, SNRPC +0.08, PDE4DIP +0.08, PPP1R14A +0.07, TOP2B +0.07 |
| ETS2 | 91 | ETS2 | 0.0580 | -0.117 | APOE +0.27, FAM136A -0.27, HBZ +0.25, PSMC3 -0.23, HIC2 +0.23 |
| FEV | 314 | FEV | 0.0231 | -0.071 | BCL2L12 -0.16, HBG2 -0.11, SNHG8 -0.10, VIM +0.10, TIMM8B -0.10 |
| FOSB | 311 | FOSB | 0.0239 | n/a | HBG1 -0.16, SMYD3 -0.12, HBG2 -0.12, AHCY -0.10, CST3 -0.09 |
| FOXA1 | 240 | FOXA1 | 0.0250 | n/a | HBZ +0.26, HBG2 +0.22, HBG1 +0.14, APOE +0.12, LYPLA1 +0.11 |
| FOXA3 | 183 | FOXA3 | 0.0290 | n/a | HBG1 +0.18, HBG2 +0.17, HBZ +0.14, SNRNP70 -0.13, CHCHD10 +0.13 |
| FOXF1 | 240 | FOXF1 | 0.0254 | n/a | TOP2A +0.14, HIST1H4C +0.14, B2M -0.13, YDJC +0.11, EIF2AK1 +0.11 |
| FOXL2 | 375 | FOXL2 | 0.0241 | -0.162 | HBZ +0.35, HBG2 +0.34, HIST1H1C +0.32, HBG1 +0.22, FOXL2 -0.16 |
| FOXO4 | 293 | FOXO4 | 0.0268 | n/a | CD63 -0.31, ENSA -0.20, TNNT1 -0.18, RHOC -0.17, MYL4 +0.16 |
| GLB1L2 | 196 | GLB1L2 | 0.0294 | n/a | CDC37 -0.18, HIST1H4C -0.17, ZFR +0.14, RTN4 -0.14, TGFB1 -0.13 |
| HES7 | 117 | HES7 | 0.0374 | n/a | HBG2 -0.23, HBG1 -0.21, GAR1 +0.15, ZNF428 +0.14, GYPA +0.14 |
| HK2 | 229 | HK2 | 0.0288 | -0.064 | TXNIP -0.33, MTDH -0.21, FKBP4 -0.19, DNAJA1 -0.19, HIST1H1C -0.14 |
| HNF4A | 347 | HNF4A | 0.0243 | n/a | CFD -0.19, HIST1H1C +0.14, ATAD2 +0.13, UBE2S +0.11, TKT +0.11 |
| HOXA13 | 156 | HOXA13 | 0.0318 | n/a | HBG2 -0.23, ATP5G1 -0.15, ATPIF1 +0.14, MTRNR2L8 -0.14, PURA +0.13 |
| HOXB9 | 273 | HOXB9 | 0.0298 | -0.551 | HOXB9 -0.55, HBG2 -0.34, VIM +0.16, C8orf59 -0.15, HBG1 -0.14 |
| HOXC13 | 103 | HOXC13 | 0.0392 | n/a | HBZ +0.19, KPNB1 -0.18, DDX3X +0.17, RRP1 -0.16, DNAJC9 -0.16 |
| IER5L | 216 | IER5L | 0.0289 | n/a | PRDX2 -0.14, RABL6 -0.13, DDX1 -0.13, H2AFY -0.12, SAP18 -0.12 |
| IKZF3 | 75 | IKZF3 | 0.0475 | -0.144 | GSTP1 -0.38, KRT18 +0.32, KRT8 +0.30, HBG2 -0.30, HBG1 -0.29 |
| IRF1 | 274 | IRF1 | 0.0259 | n/a | HIST1H4C -0.21, HBZ -0.16, TMEM50A +0.12, TRIM44 -0.12, HIST1H1C -0.11 |
| ISL2 | 181 | ISL2 | 0.0321 | -0.035 | HBZ +0.24, HBG2 +0.21, HBG1 +0.18, HIST1H1C +0.18, TYW3 -0.14 |
| JUN | 216 | JUN | 0.0311 | -0.128 | HIST1H4C -0.29, TUBB -0.19, C2orf88 -0.16, TUBA1C -0.16, BTG1 +0.16 |
| KIF18B | 141 | KIF18B | 0.0469 | -0.048 | HBZ +0.48, HBG2 -0.44, HBG1 -0.26, RAD23A +0.24, DYNLL1 +0.23 |
| KIF2C | 209 | KIF2C | 0.0284 | -0.434 | KIF2C -0.43, SNRPA1 +0.13, IGFBP2 -0.11, TMBIM6 +0.11, ITM2B -0.11 |
| KLF1 | 157 | KLF1 | 0.0406 | -0.275 | HBG2 -0.53, PRRC2C -0.52, HBZ -0.49, HBG1 -0.36, HIST1H4C -0.28 |
| KMT2A | 205 | KMT2A | 0.0331 | -0.535 | KMT2A -0.53, DUT -0.41, APOE +0.17, APOC1 +0.16, CTSL +0.16 |
| LHX1 | 177 | LHX1 | 0.0335 | n/a | HBG2 -0.25, BTG1 -0.19, SH3BGRL3 -0.15, CD81 +0.15, MALAT1 -0.14 |
| LYL1 | 87 | LYL1 | 0.0579 | -0.745 | LYL1 -0.75, LAPTM5 +0.50, AIF1 +0.43, LST1 +0.39, ITM2B +0.36 |
| MAP2K3 | 174 | MAP2K3 | 0.0374 | n/a | TOMM5 -0.18, GAL -0.17, HIST1H1C -0.17, TSC22D1 +0.17, PYCARD +0.17 |
| MAP4K3 | 148 | MAP4K3 | 0.0340 | -0.079 | HIST1H1C +0.18, APOE +0.15, MDK +0.14, RPS19BP1 -0.14, IGFBP2 +0.13 |
| MAP4K5 | 167 | MAP4K5 | 0.0336 | -0.105 | HBG2 +0.26, HBG1 +0.21, BTG1 -0.20, SH3BGRL3 +0.19, KRT10 +0.19 |
| MAP7D1 | 62 | MAP7D1 | 0.0508 | -0.137 | HIST1H4C +0.27, HBG2 -0.25, VCP +0.24, SF3A3 +0.23, DNAJA1 +0.22 |
| MAPK1 | 305 | MAPK1 | 0.0304 | -0.958 | MAPK1 -0.96, GYPB +0.30, CD47 -0.21, GYPA +0.20, HBZ +0.19 |
| MEIS1 | 284 | MEIS1 | 0.0238 | n/a | HBZ +0.16, CLSPN -0.12, GYPB -0.11, GGCT +0.11, UBE2M -0.10 |
| MIDN | 568 | MIDN | 0.0174 | -0.085 | TMSB10 +0.14, CRKL -0.14, HNRNPUL1 -0.11, MIDN -0.09, POLR1D +0.07 |
| NCL | 443 | NCL | 0.0291 | -0.739 | NCL -0.74, HBZ +0.38, HBG2 +0.27, APOE +0.19, EEF1D -0.18 |
| NIT1 | 237 | NIT1 | 0.0256 | -0.091 | PFDN2 -0.18, CDT1 +0.11, PSMA5 +0.10, LEPROT +0.10, ECI1 -0.10 |
| OSR2 | 109 | OSR2 | 0.0377 | n/a | HBG2 -0.34, ODC1 -0.17, HBG1 -0.17, BEX2 -0.17, YME1L1 -0.17 |
| PLK4 | 43 | PLK4 | 0.0758 | -0.101 | HIST1H1C +0.61, HBZ +0.44, UQCRQ -0.37, LYPLA1 -0.33, HIST1H2BJ +0.33 |
| POU3F2 | 102 | POU3F2 | 0.0373 | n/a | COX7A2L -0.20, APOE +0.20, TAF1D +0.20, CYC1 +0.17, APOC1 +0.16 |
| PRDM1 | 216 | PRDM1 | 0.0285 | n/a | HIST1H4C +0.15, ZC3H15 -0.13, C8orf59 -0.12, PAK2 +0.11, SF3B1 -0.11 |
| PTPN1 | 371 | PTPN1 | 0.0776 | -0.364 | LST1 +1.23, HBG2 -1.02, APOE -0.94, LGALS1 +0.91, AIF1 +0.91 |
| PTPN12 | 252 | PTPN12 | 0.0264 | -0.243 | PTPN12 -0.24, PRSS57 +0.16, VIM -0.15, LYL1 +0.13, MACF1 +0.12 |
| PTPN9 | 78 | PTPN9 | 0.0468 | -0.024 | CKS1B -0.22, GYPA +0.20, EIF3H -0.19, FDX1 -0.19, CCNA2 -0.19 |
| RHOXF2 | 87 | RHOXF2 | 0.0489 | n/a | HBZ +0.27, ACTR2 +0.27, MALAT1 -0.24, APOE +0.22, KIF2A -0.22 |
| RREB1 | 151 | RREB1 | 0.0358 | -0.029 | RP11-301G19.1 -0.51, HBG2 +0.34, HBZ +0.25, HBG1 +0.21, BLVRB +0.20 |
| SAMD1 | 196 | SAMD1 | 0.0307 | -0.087 | APOC1 -0.21, BLVRB -0.19, HBZ -0.17, STRA13 +0.15, IGFBP2 +0.14 |
| SET | 54 | SET | 0.0573 | -0.614 | SET -0.61, HIST1H1C -0.27, KCNH2 -0.24, SPN -0.24, GYPA +0.24 |
| SGK1 | 142 | SGK1 | 0.0357 | -0.047 | POLR2H -0.18, EIF6 +0.16, SCP2 -0.16, HBG2 +0.15, HBG1 +0.15 |
| SLC38A2 | 140 | SLC38A2 | 0.0413 | -0.370 | SLC38A2 -0.37, HBZ +0.29, PRSS57 +0.20, PPDPF -0.19, HIST1H4C -0.19 |
| SNAI1 | 178 | SNAI1 | 0.0324 | n/a | PDE4DIP -0.18, HBG2 +0.17, APOE -0.17, GSTP1 +0.17, LAPTM4B -0.15 |
| SPI1 | 82 | SPI1 | 0.0521 | -0.176 | APOE -0.56, PRSS57 +0.42, PYCARD -0.33, CYBA -0.33, IFITM2 -0.29 |
| STIL | 345 | STIL | 0.0319 | -0.154 | UQCC2 -0.27, HIST1H4C -0.19, HNRNPDL -0.18, HIST1H1C +0.17, TFRC -0.16 |
| TBX2 | 207 | TBX2 | 0.0307 | n/a | PSMD2 +0.15, HBZ -0.14, CDC123 +0.13, EMP3 +0.13, UBAC1 -0.12 |
| TBX3 | 263 | TBX3 | 0.0251 | n/a | MDH1 +0.12, HIST1H4C -0.12, MBNL1 -0.11, ILF2 +0.11, SNX3 +0.11 |
| TMSB4X | 173 | TMSB4X | 0.0303 | -1.216 | TMSB4X -1.22, C22orf39 +0.14, SNRPC +0.13, BRIX1 -0.13, G3BP1 -0.13 |
| TP73 | 196 | TP73 | 0.0384 | n/a | AC079466.1 -0.42, GAL -0.37, HBG2 +0.25, HBZ +0.20, TMSB10 +0.20 |
| TSC22D1 | 120 | TSC22D1 | 0.0373 | -0.327 | TSC22D1 -0.33, HIST1H1C +0.29, MDK +0.17, PSMB1 -0.17, SKIV2L2 -0.16 |
| ZBTB1 | 283 | ZBTB1 | 0.0278 | -0.067 | TMSB10 +0.33, HBG2 -0.22, HBZ -0.21, VIM -0.18, COMT +0.18 |
| ZBTB10 | 134 | ZBTB10 | 0.0385 | -0.114 | BLVRB +0.39, AIF1 +0.27, RAC3 +0.25, HBG2 +0.21, FADS1 +0.19 |
| ZBTB25 | 62 | ZBTB25 | 0.0509 | n/a | HIST1H2AC +0.26, HIST1H1C +0.24, PDLIM1 +0.24, PSMB3 -0.22, VIM -0.22 |
| ZC3HAV1 | 183 | ZC3HAV1 | 0.0310 | -0.396 | ZC3HAV1 -0.40, CIRBP +0.30, PIM1 -0.15, NDUFC2 +0.15, HIST1H4C -0.14 |
| ZNF318 | 80 | ZNF318 | 0.0442 | -0.182 | STMN1 +0.19, CD63 +0.19, ZNF318 -0.18, IPO7 -0.18, C7orf73 -0.17 |

## Reading

A target whose own delta is clearly negative was knocked down in the external screen as it was in the bundle; a target with a small mean absolute delta had little effect there, and transferring its response adds little. The deltas are differences within the external screen (its perturbed cells minus its own controls), so batch differences between the two screens cancel only to the extent they are additive in log space. The screen is CRISPRi and the bundle CRISPRa, so a target's own change in the bundle is expected to point against its delta here: the file's sign of -1 records that, and a perturbation of several genes is read as the sum of its targets' rows, present only when every target has one.
