# autorun, attempt 1, killed

Started 2026-11-05T00:33:22Z. CellForge's autorun split the training export (`splits/ood20_val10_seed42`), and the
Codex agent wrote `result_T01.py` by 00:40Z (last proxy call 00:40:44Z). The script trained on the CPU from 00:40Z
(pid 21314, `/opt/anaconda3/bin/python3.12`; 212 % CPU, 6.8 GB resident at 02:12Z, 47 GB by 03:10Z: macOS
`/Library/Logs/DiagnosticReports/JetsamEvent-2026-11-04-221057.ips` and `-221315.ips`, largest process
`python3.12` pid 21314, 46.91 and 46.93 GB). At 03:13:27Z the launching session ended and the run script, CellForge,
the trainer and the proxy received SIGTERM (`launch_cf_norman_s42.log`). No metrics were written. The step is rerun
under the 12 GB memory cap (`block_u_run.sh`, `MEM_CAP_MB`).
