Astra GEARS milestone: seed2 COMPLETE, explicit exit0 at 2026-10-29T01:39:45.121424+00:00. Twenty CPU epochs, unchanged settings. Runner wall time18158.9s (about5h03m), including the previously disclosed slow-progress interval; cause was not established. All prediction/receipt checks pass: finite38x2055, exact unique held-out/gene order, settings and both hashes. Allfour graph artifact hashes match seed0. No score has been read.

The existing sequential driver started the final seed3 ONCE at 2026-10-29T01:39:45.661751+00:00, Python55796, nice19, same20epochs/CPU/defaultsettings, fresh work/output. Complete seed3 before any of the three prescribed score commands. C2 and H remain unstarted; no paid call, no restart/tuning/source/device change. All raw logs/commands/exits/runtime/validation/graph receipts are retained in docs/results/gears_adamson of own clone; raw work/predictions remain outside Git.

<details><summary>Full seed2 runner receipt</summary>

```json
{
  "model": "GEARS",
  "gears_version": "0.1.2",
  "torch": "2.15.0",
  "device": "cpu",
  "seed": 2,
  "epochs": 20,
  "hidden_size": 64,
  "batch_size": 32,
  "val_frac": 0.1,
  "train_conditions": 41,
  "val_conditions": 5,
  "train_conditions_outside_graph": [
    "AMIGO3+ctrl",
    "KCTD16+ctrl",
    "SLMO2+ctrl",
    "SRPR+ctrl"
  ],
  "heldout": 38,
  "heldout_fallback": [
    "TIMM23"
  ],
  "export_input_sha256": "ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a",
  "predictions_sha256": "e0bae73fbfff0cfb6420879d7b65bdfe298c130d0635312540976c16db884632",
  "seconds": 18158.9,
  "machine": "macOS-26.5.1-arm64-arm-64bit-Mach-O"
}
```
</details>

<details><summary>Seed2 graph artifact hashes</summary>

```json
{
  "utc": "2026-10-29T01:39:45.659390+00:00",
  "work": "/Users/andresarriaga/gears_work_s2",
  "files": [
    {
      "relative_path": "gears_data/essential_all_data_pert_genes.pkl",
      "bytes": 558811,
      "sha256": "46c3dfe354d8ad5c0da22c69f3d0ca451987b1a61ed9d984279b22b9565ff8d7"
    },
    {
      "relative_path": "gears_data/gene2go_all.pkl",
      "bytes": 9462558,
      "sha256": "f145c5e84a53048d87942a417d870a4f2d8db50200b96e492b358c13aba8c771"
    },
    {
      "relative_path": "gears_data/go_essential_all/go_essential_all.csv",
      "bytes": 354733543,
      "sha256": "99622d9215462e7bbea99a5f6c0b1e86febfef9f57226269418053484fcb3f9f"
    },
    {
      "relative_path": "gears_data/go_essential_all.tar.gz",
      "bytes": 60654049,
      "sha256": "98a14a60e8b76f76fd172570d023a6036775f151604ec01340b3fec7d36693da"
    }
  ]
}
```
</details>
