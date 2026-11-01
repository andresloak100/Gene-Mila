set -C
cd /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings || exit 98
{
PYTHONPATH=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings PYTHONUNBUFFERED=1 nice -n 19 /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python tools/feature_compare.py --data /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf_clean_tables --out /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_stage1 --null-reps 0 --source f_r0=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_plugins/r0 --source f_r2=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_plugins/r2 --source f_r3=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_plugins/r3 --source-run f_r0_selected=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r0_discovery --source-run f_r2_selected=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r2_discovery --source-run f_r3_selected=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_d1_ds_w4_r3_discovery
rc=$?
printf "%s\n" "$rc" > /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_stage1.exit
exit "$rc"
} > /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_stage1.log 2>&1
