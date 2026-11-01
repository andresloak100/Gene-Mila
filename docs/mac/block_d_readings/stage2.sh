set -C
cd /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings || exit 98
{
PYTHONPATH=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings PYTHONUNBUFFERED=1 /usr/bin/caffeinate -i nice -n 19 /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/.venv/bin/python tools/feature_compare.py --data /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf_clean_tables --out /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_stage2 --null-reps 999 --source f_r0=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_top/r0 --source f_r2=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_top/r2 --source f_r3=/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_top/r3
rc=$?
printf "%s\n" "$rc" > /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_stage2.exit
exit "$rc"
} > /Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila-d-readings/docs/results/adamson_cf_d_stage2.log 2>&1
