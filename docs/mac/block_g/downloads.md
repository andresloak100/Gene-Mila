# Block G raw-source receipts

ROADMAP section6 step3. The original nine-download receipt from issue #47 is preserved verbatim below, followed by the separately dated alias/additional-source receipt. No raw file is committed. The sources are ready, but bundle preparation is held at the documented STRING-header preflight mismatch; no table or clean bundle has been built.

Original receipt SHA256: `cd22243dcaba2b3e4c169b08f5919ea4894b8a69881213b428d12a4f848217da`.
Roadmap addendum SHA256: `894886830abf3cf9a82033c9d1e439a90a05ea2586a5ee5f4ee57348401af30e`.

---

# Clean reference downloads

Receipt started 2026-10-16T21:40:54Z. Public downloads only; no API key, lab run, bundle build, feature scoring or Block G execution. Files are stored as served. No existing files were replaced.

## CORUM path verified

The requested [CORUM download page](https://mips.helmholtz-muenchen.de/corum/download) serves the official JavaScript application. Its [DownloadView source](https://mips.helmholtz-muenchen.de/corum/assets/DownloadView.df782fe4.js) calls `/public/file/download_current_file` on `https://mips.helmholtz-muenchen.de/fastapi-corum`. The official [file metadata](https://mips.helmholtz-muenchen.de/fastapi-corum/public/file/info) identifies `file_id=complete`, name `allComplexes`, with the `txt` format. The [current release API](https://mips.helmholtz-muenchen.de/fastapi-corum/public/releases/current) reports **5.3, dated 2026-04-14**. The verified download is the API URL in the file receipt below, not a guessed static path.

The legacy static URL `https://mips.helmholtz-muenchen.de/corum/download/releases/current/allComplexes.txt.zip` returned HTTP 200 **HTML**, 423 bytes, rather than a ZIP on 2026-10-16. The site now provides this download via its public API; HTTP 200 at the old path is not evidence of a valid data archive. Details: `corum_verification.json`.

## File receipts

Each completed transfer has a separate immutable `*.receipt.json`, HTTP header receipt, and transfer log. SHA256 values below cover the downloaded bytes (compressed where requested). Any unfinished large transfer will receive an appended completion receipt; pending entries have no claimed hash.

### `goa_human.gaf.gz`

- Requested URL: https://current.geneontology.org/annotations/goa_human.gaf.gz
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://current.geneontology.org/annotations/goa_human.gaf.gz
- UTC: 2026-10-16T21:39:20Z → 2026-10-16T21:39:21Z
- Bytes: 15041996
- SHA256: `db472faff1785878521693af62646546cea6af4a386609dd01c72c0554a46a30`

### `go-basic.obo`

- Requested URL: https://purl.obolibrary.org/obo/go/go-basic.obo
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://current.geneontology.org/ontology/go-basic.obo
- UTC: 2026-10-16T21:39:20Z → 2026-10-16T21:39:23Z
- Bytes: 32227785
- SHA256: `b08d45b268b8c24ccb2513dbbbc7d4df9f6521c099b413f79eb31e06e0fa3bcc`
- Redirect/move: requested URL resolved to the final URL above.

### `allComplexes.txt`

- Requested URL: https://mips.helmholtz-muenchen.de/fastapi-corum/public/file/download_current_file?file_id=complete&file_format=txt
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://mips.helmholtz-muenchen.de/fastapi-corum/public/file/download_current_file?file_id=complete&file_format=txt
- UTC: 2026-10-16T21:39:20Z → 2026-10-16T21:39:40Z
- Bytes: 8893038
- SHA256: `7364ae40d3f815c8fb03ce5106117255d8c110cc6a17187bb983d6ea523c352b`

### `9606.protein.physical.links.detailed.v12.0.txt.gz`

- Requested URL: https://stringdb-downloads.org/download/protein.physical.links.detailed.v12.0/9606.protein.physical.links.detailed.v12.0.txt.gz
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://stringdb-downloads.org/download/protein.physical.links.detailed.v12.0/9606.protein.physical.links.detailed.v12.0.txt.gz
- UTC: 2026-10-16T21:39:21Z → 2026-10-16T21:39:25Z
- Bytes: 11086354
- SHA256: `db1de86dc7a6e34eba78ca6e6747f9201195b0af1edb607c19bf651b0eddede5`

### `uniprot_human_reviewed.tsv`

- Requested URL: https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=organism_id:9606+AND+reviewed:true&fields=accession,gene_primary,length,ft_signal,ft_transmem,cc_subcellular_location,keyword
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=organism_id:9606+AND+reviewed:true&fields=accession,gene_primary,length,ft_signal,ft_transmem,cc_subcellular_location,keyword
- UTC: 2026-10-16T21:39:23Z → 2026-10-16T21:39:36Z
- Bytes: 9851702
- SHA256: `34bf031f82f897c307a10d51cff905464682d48b5408c13c3bc3383463561cc8`

### `gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz`

- Requested URL: https://gnomad-public-us-east-1.s3.amazonaws.com/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://gnomad-public-us-east-1.s3.amazonaws.com/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz
- UTC: 2026-10-16T21:39:25Z → 2026-10-16T21:39:25Z
- Bytes: 4609488
- SHA256: `153031d34b6794e8e99eb0306bc3c50b13b18accda8b0ffef91c2623dd3affd5`

### `gencode.v27.primary_assembly.annotation.gtf`

- Requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf
- Status: **in progress** at the initial receipt; completion/error will be appended below.

### `Homo_sapiens_assembly38.fasta`

- Requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta
- Status: **in progress** at the initial receipt; completion/error will be appended below.

### `Homo_sapiens_assembly38.fasta.fai`

- Requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta.fai
- Status: **downloaded**, HTTP 200, curl exit 0.
- Final URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta.fai
- UTC: 2026-10-16T21:39:40Z → 2026-10-16T21:39:41Z
- Bytes: 160928
- SHA256: `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b`

## Initial format checks

Only short headers were inspected, including the first ~700 decompressed bytes of compressed files; no large decompression or feature/bundle construction was performed. UniProt has all seven exact headers expected by `tools/build_protein_annotation.py`. CORUM is tab-delimited text headed `complex_id`, and the STRING file is the requested physical detailed table. GO GAF records generation 2026-05-21 (source generation 2026-04-30); the OBO records `releases/2026-07-26`. These are the versions actually served by the user-specified URLs; they are not asserted to be synchronized releases.

The UniProt requested URL is copied exactly from the docstring/`URL` constant of `tools/build_protein_annotation.py` at operator source commit `b6638c3450710c7dcc4579c0b0afd73611a7952b`. Downloading references does not authorize a Block G build or run.

## Large-transfer completion receipts

### `gencode.v27.primary_assembly.annotation.gtf` completed

- Status: **downloaded**, HTTP 200, curl exit 0.
- Requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf
- Final URL: https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf
- UTC: 2026-10-16T21:39:25Z → 2026-10-16T21:45:16Z
- Bytes: 1152183144
- SHA256: `26b81dd6e74bdc9c9c6ba0c87f1a069cf9b2b4492079b2706604ae679cc5b97c`
- No URL redirect.

First header lines (format check only):

```text
##description: evidence-based annotation of the human genome (GRCh38), version 27 (Ensembl 90)
##provider: GENCODE
##contact: gencode-help@sanger.ac.uk
##format: gtf
##date: 2017-08-01
```

### `Homo_sapiens_assembly38.fasta` completed

- Status: **downloaded**, HTTP 200, curl exit 0.
- Requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta
- Final URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta
- UTC: 2026-10-16T21:39:36Z → 2026-10-16T21:49:43Z
- Bytes: 3249912778
- SHA256: `93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564`
- No URL redirect.
- Format check: FASTA begins with the `chr1` record; its first sequence offset is 112 bytes, matching the downloaded `.fai`; the file ends in a newline. Only the first header and final byte were inspected.

## Final status — 9/9 complete

All nine requested files completed successfully by 2026-10-16T21:50:09Z. The two initial “in progress” entries above are retained as history and are resolved by their appended completion receipts. There are **no pending transfers, failed downloads or leftover partial files**.

All nine responses finished with HTTP 200, curl exit 0, successful TLS certificate verification (`ssl_verify_result=0`), and local byte counts matching curl transfer byte counts. Every file has its requested and final URL, UTC transfer dates, bytes and SHA256 recorded above and in `download_receipts.json`. No raw reference file was committed, deleted, replaced, transformed or used in a lab run. No Block G preparation beyond these explicitly requested downloads was performed.


---

# Roadmap raw input addendum

Checked 2026-10-17T01:40:09Z; raw-source plan/preparation script inspected at commit `1a958733115fb7956149828b636a99ccbb5b9fb4`. This is a separate receipt. The previous `downloads.md` remains unchanged with SHA256 `cd22243dcaba2b3e4c169b08f5919ea4894b8a69881213b428d12a4f848217da`.

**All 12 expected raw filenames are present and nonempty. This does not mean the unchanged builder is ready: the STRING column mismatch below remains unresolved. No bundle/table build, preprocessing, lab run, cap write or paid call was made.**

## Blocker observed before any build

The downloaded `string_physical_detailed.txt.gz` first line is:

```text
protein1 protein2 experimental database textmining combined_score
```

At the inspected commit, `genemila/data/knowledge_clean.py:string_physical_channels` asks `_header_index(head, "experiments")`; the served field is singular **`experimental`**. The helper accepts an exact or prefix match, so `experimental` does not match `experiments`. This is a static source/header mismatch, not a reported execution failure. Neither the source data nor the builder/preparation script was altered; the parent operator must resolve the scope before invoking the unchanged preparation script.

## Expected input inventory

| Expected filename | Bytes | SHA256 | Method |
|---|---:|---|---|
| `goa_human.gaf.gz` | 15041996 | `db472faff1785878521693af62646546cea6af4a386609dd01c72c0554a46a30` | existing verified download |
| `go-basic.obo` | 32227785 | `b08d45b268b8c24ccb2513dbbbc7d4df9f6521c099b413f79eb31e06e0fa3bcc` | existing verified download |
| `corum_allComplexes.txt` | 8893038 | `7364ae40d3f815c8fb03ce5106117255d8c110cc6a17187bb983d6ea523c352b` | hardlink alias |
| `string_physical_detailed.txt.gz` | 11086354 | `db1de86dc7a6e34eba78ca6e6747f9201195b0af1edb607c19bf651b0eddede5` | hardlink alias |
| `string_info.txt.gz` | 1970090 | `144de4b0d98c6a7dfde6ddc2591cf88657f27b989eadff4f501450c3ed1f0f1c` | new free HTTPS download |
| `collectri.tsv` | 4088085 | `91f282dd6fe739f661548599b4f5ca1f6da238e9ffc5f1cedf0476973cd7e098` | new free HTTPS download |
| `reactome.gmt.zip` | 298479 | `8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4` | byte copy from existing raw cache |
| `uniprot_human_reviewed.tsv` | 9851702 | `34bf031f82f897c307a10d51cff905464682d48b5408c13c3bc3383463561cc8` | existing verified download |
| `gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz` | 4609488 | `153031d34b6794e8e99eb0306bc3c50b13b18accda8b0ffef91c2623dd3affd5` | existing verified download |
| `gencode.v27.gtf` | 1152183144 | `26b81dd6e74bdc9c9c6ba0c87f1a069cf9b2b4492079b2706604ae679cc5b97c` | hardlink alias |
| `hg38.fasta` | 3249912778 | `93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564` | hardlink alias |
| `hg38.fasta.fai` | 160928 | `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b` | hardlink alias |

## Five aliases, originals preserved

Each missing expected filename was created with an exclusive hardlink. The source hash was recomputed and matched its original download receipt before linking. Source and alias device/inode/byte count were then confirmed equal; no copy or decompression of the large reference was needed. These are raw input aliases, not transformed data.

| Alias | Original | UTC link creation | Device / inode | SHA256 |
|---|---|---|---|---|
| `corum_allComplexes.txt` | `allComplexes.txt` | 2026-10-17T01:38:59Z | 16777230 / 252001421 | `7364ae40d3f815c8fb03ce5106117255d8c110cc6a17187bb983d6ea523c352b` |
| `string_physical_detailed.txt.gz` | `9606.protein.physical.links.detailed.v12.0.txt.gz` | 2026-10-17T01:38:59Z | 16777230 / 252001426 | `db1de86dc7a6e34eba78ca6e6747f9201195b0af1edb607c19bf651b0eddede5` |
| `gencode.v27.gtf` | `gencode.v27.primary_assembly.annotation.gtf` | 2026-10-17T01:38:59Z | 16777230 / 252001441 | `26b81dd6e74bdc9c9c6ba0c87f1a069cf9b2b4492079b2706604ae679cc5b97c` |
| `hg38.fasta` | `Homo_sapiens_assembly38.fasta` | 2026-10-17T01:39:02Z | 16777230 / 252001464 | `93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564` |
| `hg38.fasta.fai` | `Homo_sapiens_assembly38.fasta.fai` | 2026-10-17T01:39:02Z | 16777230 / 252001483 | `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b` |

`corum_allComplexes.txt` source requested URL: https://mips.helmholtz-muenchen.de/fastapi-corum/public/file/download_current_file?file_id=complete&file_format=txt
Final URL: https://mips.helmholtz-muenchen.de/fastapi-corum/public/file/download_current_file?file_id=complete&file_format=txt; original download completed 2026-10-16T21:39:40Z.

`string_physical_detailed.txt.gz` source requested URL: https://stringdb-downloads.org/download/protein.physical.links.detailed.v12.0/9606.protein.physical.links.detailed.v12.0.txt.gz
Final URL: https://stringdb-downloads.org/download/protein.physical.links.detailed.v12.0/9606.protein.physical.links.detailed.v12.0.txt.gz; original download completed 2026-10-16T21:39:25Z.

`gencode.v27.gtf` source requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf
Final URL: https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf; original download completed 2026-10-16T21:45:16Z.

`hg38.fasta` source requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta
Final URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta; original download completed 2026-10-16T21:49:43Z.

`hg38.fasta.fai` source requested URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta.fai
Final URL: https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta.fai; original download completed 2026-10-16T21:39:41Z.

## Additional free sources

### `string_info.txt.gz`

- Requested URL: https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz
- Final URL: https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz
- UTC: 2026-10-17T01:39:02Z → 2026-10-17T01:39:03Z
- Bytes: 1970090
- SHA256: `144de4b0d98c6a7dfde6ddc2591cf88657f27b989eadff4f501450c3ed1f0f1c`
- Result: downloaded; HTTP 200; curl exit 0; TLS verification result 0. Used `/usr/bin/curl`, without disabling certificate verification.
- Redirect: none.

### `collectri.tsv`

- Requested URL: https://omnipathdb.org/interactions?datasets=collectri&genesymbols=yes&loops=yes
- Final URL: https://omnipathdb.org/interactions?datasets=collectri&genesymbols=yes&loops=yes
- UTC: 2026-10-17T01:39:02Z → 2026-10-17T01:39:11Z
- Bytes: 4088085
- SHA256: `91f282dd6fe739f661548599b4f5ca1f6da238e9ffc5f1cedf0476973cd7e098`
- Result: downloaded; HTTP 200; curl exit 0; TLS verification result 0. Used `/usr/bin/curl`, without disabling certificate verification.
- Redirect: none.

### `reactome.gmt.zip`

- Source path: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/raw/knowledge/reactome.gmt.zip`
- Plan-associated source URL: https://reactome.org/download/current/ReactomePathways.gmt.zip
- Copy UTC: 2026-10-17T01:39:02Z
- Bytes: 298479
- Source and destination SHA256: `8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4`
- This is a byte copy of the existing public raw cache, not a fresh network download; no original fetch date or current-release claim is inferred. Original cache was opened read-only and is unchanged.

## Short format observations

- CORUM actual headers `complex_name`, `organism`, `subunits_gene_name` are accepted by the inspected current `corum()` parser, which supports CORUM 4/5 spellings.
- STRING info header: `#string_protein_id	preferred_name	protein_size	annotation`.
- CollecTRI header: `source	target	source_genesymbol	target_genesymbol	is_directed	is_stimulation	is_inhibition	consensus_direction	consensus_stimulation	consensus_inhibition`. It includes the source/target gene symbols and consensus sign columns used by the inspected parser.
- UniProt header: `Entry	Gene Names (primary)	Length	Signal peptide	Transmembrane	Subcellular location [CC]	Keywords`. All seven required fields from the protein builder docstring are present.
- The GTF begins `##description: evidence-based annotation of the human genome (GRCh38), version 27 (Ensembl 90)`; FASTA begins with `chr1`, and its `.fai` is the preserved matching source index.
- Reactome ZIP member is `ReactomePathways.gmt`; its first GMT row begins `2-LTR circle formation`, `R-HSA-164843`, followed by gene symbols.
- Header inspection was limited to short initial content; no builder or scientific validation was invoked.

Preparation script SHA256 at inspection: `4cf4ed0a04af9a32541e03e979b8ac1fd99731e22bc47165314ee9cbc3bf5637`. Supporting JSON: `roadmap_raw_preparation_20261017T013859Z.json` and `roadmap_raw_readiness_20261017T013859Z.json`.
