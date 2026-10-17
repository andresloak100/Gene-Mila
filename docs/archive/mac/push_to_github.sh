#!/bin/bash
# Put the work that exists only on this Mac onto GitHub, so any agent can catch up.
# Run once, by Andres, in Terminal:   bash ~/Documents/Mila/Gene-Mila/genemila_scale_logs/push_to_github.sh
#
#   1. Secret check (aborts on any hit; prints file and line only, never the text).
#   2. Push Astra's two branches, unchanged, under their own names. No force.
#   3. Commit the Mac-only reports on a new branch made from the lab branch, in a temporary worktree
#      (the main checkout is not touched), and push it. No force.
#   4. Print every pushed ref and the md5 of every copied file.
#
# Nothing is deleted or rewritten anywhere. Pass --check-only to run step 1 alone.
set -euo pipefail

REMOTE="https://github.com/andresloak100/Gene-Mila.git"
BASE_COMMIT="8261c578"
LAB="$HOME/Documents/Mila/Gene-Mila/gene-mila"
LOGS="$HOME/Documents/Mila/Gene-Mila/genemila_scale_logs"
ASTRA="$HOME/Documents/Codex/2026-10-08/pl/work"
LAB_BRANCH="claude/autonomous-research-system-3k435s"
NEW_BRANCH="claude/mac-reports-2026-10-11"
WT="$LOGS/.push_worktree"

# repo directory | branch
ASTRA_BRANCHES=(
  "$ASTRA/gene-mila|astra/deepseek-continuation-memory"
  "$ASTRA/gene-mila-compactness|astra/compact-master-selection"
)
# source file | destination directory inside the repo
COPIES=(
  "$LOGS/noise_ceiling.md|docs/results"
  "$LOGS/noise_ceiling.json|docs/results"
  "$LOGS/refit_visible.md|docs/results"
  "$LOGS/refit_visible.json|docs/results"
  "$LOGS/STATE.md|docs/mac"
  "$LOGS/adamson_cf_ncells.json|docs/mac"
  "$LOGS/replogle_aliases.json|docs/mac"
  "$LOGS/external_replogle2022_k562_v2.md|docs/results"
  "$LOGS/external_loo_replogle2022_k562_v2.md|docs/results"
  "$LOGS/external_loo_replogle2022_k562_v2.json|docs/results"
  "$LOGS/external_loo_replogle2022_k562_v2_widegrid.md|docs/results"
  "$LOGS/external_loo_replogle2022_k562_v2_widegrid.json|docs/results"
  "$LOGS/external_stack_control.py|docs/mac"
  "$LOGS/external_stack_control.json|docs/mac"
  "$LAB/runs/control_replogle_w4_r0/config.json|docs/mac/control_replogle_w4_r0"
  "$LAB/runs/control_replogle_w4_r0/summary.json|docs/mac/control_replogle_w4_r0"
  "$LOGS/control_replogle_w4_r0.analysis.log|docs/mac/control_replogle_w4_r0"
  "$LAB/runs/control_replogle_from_opus_r0/config.json|docs/mac/control_replogle_from_opus_r0"
  "$LAB/runs/control_replogle_from_opus_r0/summary.json|docs/mac/control_replogle_from_opus_r0"
  "$LOGS/control_replogle_from_opus_r0.analysis.log|docs/mac/control_replogle_from_opus_r0"
  "$LOGS/external_loo_replogle2022_k562_v3.md|docs/results"
  "$LOGS/external_loo_replogle2022_k562_v3.json|docs/results"
  "$LAB/runs/control_replogle3_from_opus_r0/config.json|docs/mac/control_replogle3_from_opus_r0"
  "$LAB/runs/control_replogle3_from_opus_r0/summary.json|docs/mac/control_replogle3_from_opus_r0"
  "$LOGS/control_replogle3_from_opus_r0.analysis.log|docs/mac/control_replogle3_from_opus_r0"
  "$LOGS/feature_audit.md|docs/results"
  "$LOGS/feature_audit.json|docs/results"
  "$LOGS/feature_audit_feature_box.json|docs/results"
  "$LOGS/feature_audit_v3.md|docs/results"
  "$LOGS/feature_audit_v3.json|docs/results"
  "$LOGS/feature_audit_v3_feature_box.json|docs/results"
  "$LOGS/norman_check_public.txt|docs/mac/norman"
  "$LOGS/norman_replogle_aliases.json|docs/mac/norman"
  "$LOGS/external_replogle_norman_dryrun.txt|docs/mac/norman"
  "$LOGS/external_replogle2022_k562_norman.md|docs/results"
  "$LOGS/external_loo_norman_v1.md|docs/results"
  "$LOGS/external_loo_norman_v1.json|docs/results"
  "$LOGS/norman_untracked_copies/norman_splits.json|docs/mac/norman"
  "$LOGS/norman_untracked_copies/norman_manifest.json|docs/mac/norman"
  "$LAB/runs/norman_control_w4_r0/config.json|docs/mac/norman_control_w4_r0"
  "$LAB/runs/norman_control_w4_r0/summary.json|docs/mac/norman_control_w4_r0"
  "$LOGS/norman_control_w4_r0.analysis.log|docs/mac/norman_control_w4_r0"
  "$LAB/runs/norman_control_replogle_w4_r0/config.json|docs/mac/norman_control_replogle_w4_r0"
  "$LAB/runs/norman_control_replogle_w4_r0/summary.json|docs/mac/norman_control_replogle_w4_r0"
  "$LOGS/norman_control_replogle_w4_r0.analysis.log|docs/mac/norman_control_replogle_w4_r0"
  "$LOGS/norman_sealed_reading.md|docs/results"
  "$LOGS/norman_sealed_reading.json|docs/results"
  "$LOGS/external_loo_replogle2022_k562.md|docs/results"
  "$LOGS/external_loo_replogle2022_k562.json|docs/results"
  "$LOGS/ceiling_analysis.py|docs/mac"
  "$LOGS/compact_model_curve.py|docs/mac"
  "$LOGS/learned_kernel_experiment.py|docs/mac"
  "$LAB/runs/norman_ds_replogle_w4_r0/config.json|docs/mac/norman_ds_replogle_w4_r0"
  "$LAB/runs/norman_ds_replogle_w4_r0/summary.json|docs/mac/norman_ds_replogle_w4_r0"
  "$LOGS/norman_ds_replogle_w4_r0.analysis.log|docs/mac/norman_ds_replogle_w4_r0"
  "$LOGS/norman_n3_sealed_reading.md|docs/results"
  "$LOGS/norman_n3_sealed_reading.json|docs/results"
  "$LOGS/nondeterminism_scan.md|docs/results"
  "$LOGS/nondeterminism_scan.json|docs/results"
  "$LOGS/nondeterminism_scan.py|docs/mac"
  "$LOGS/feature_block_hashes.py|docs/mac"
  "$LOGS/feature_audit_v2.md|docs/results"
  "$LOGS/feature_audit_v2.json|docs/results"
  "$LOGS/feature_audit_v2_feature_box.json|docs/results"
  "$LAB/docs/cellforge_notes.md|docs/mac"
  "$LAB/docs/results/calibration_adamson_cf_val2.md|docs/mac"
  "$LAB/docs/results/calibration_adamson_cf_val2.json|docs/mac"
  "$LAB/docs/results/selection_replay.json|docs/mac"
)

# An API key shape (sk- then 16 or more letters or digits), or a quoted literal assigned to a key-like name.
PAT_KEY='sk-[A-Za-z0-9]{16,}'
PAT_ASSIGN='(api[_-]?key|secret|token|passwd|password)[A-Za-z0-9_]*["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9_/+.=-]{20,}["'"'"']'

echo "== Step 1: secret check"
hits=0
for entry in "${ASTRA_BRANCHES[@]}"; do
  repo="${entry%%|*}"; branch="${entry##*|}"
  git -C "$repo" rev-parse --verify --quiet "$branch^{commit}" >/dev/null || { echo "missing branch $branch in $repo"; exit 1; }
  git -C "$repo" merge-base --is-ancestor "$BASE_COMMIT" "$branch" || { echo "$branch does not descend from $BASE_COMMIT"; exit 1; }
  [ -z "$(git -C "$repo" status --porcelain)" ] || { echo "$repo has uncommitted changes; not pushing"; exit 1; }
  # every file of every commit added since the base (covers text added and later removed)
  for c in $(git -C "$repo" rev-list "$BASE_COMMIT..$branch"); do
    for pat in "$PAT_KEY" "$PAT_ASSIGN"; do
      found=$(git -C "$repo" grep -nIiE -e "$pat" "$c" -- . 2>/dev/null | cut -d: -f1-3 || true)
      if [ -n "$found" ]; then echo "POSSIBLE SECRET in $branch (commit:file:line):"; echo "$found"; hits=1; fi
    done
  done
  # the commit messages too
  if git -C "$repo" log --format=%B "$BASE_COMMIT..$branch" | grep -qiE -e "$PAT_KEY" -e "$PAT_ASSIGN"; then
    echo "POSSIBLE SECRET in a commit message of $branch"; hits=1
  fi
done
for entry in "${COPIES[@]}"; do
  src="${entry%%|*}"
  [ -f "$src" ] || { echo "missing file $src"; exit 1; }
  for pat in "$PAT_KEY" "$PAT_ASSIGN"; do
    found=$(grep -nIiE -e "$pat" "$src" | cut -d: -f1 || true)
    if [ -n "$found" ]; then echo "POSSIBLE SECRET in $src at line(s): $(echo $found)"; hits=1; fi
  done
done
if [ "$hits" -ne 0 ]; then echo "ABORTED: nothing was pushed. Report the lines above."; exit 2; fi
echo "no key-shaped text found"
[ "${1:-}" = "--check-only" ] && exit 0

echo "== Step 2: push Astra's branches (no force)"
PUSHED=()
for entry in "${ASTRA_BRANCHES[@]}"; do
  repo="${entry%%|*}"; branch="${entry##*|}"
  git -C "$repo" push "$REMOTE" "refs/heads/$branch:refs/heads/$branch"
  PUSHED+=("$branch $(git -C "$repo" rev-parse "$branch")")
done

echo "== Step 3: Mac-only reports on $NEW_BRANCH"
cleanup() { git -C "$LAB" worktree remove --force "$WT" 2>/dev/null || true; }
trap cleanup EXIT
[ ! -e "$WT" ] || { echo "$WT already exists; remove it with: git -C $LAB worktree remove --force $WT"; trap - EXIT; exit 1; }
git -C "$LAB" rev-parse --verify --quiet "refs/heads/$NEW_BRANCH" >/dev/null && { echo "local branch $NEW_BRANCH already exists; not overwriting it"; trap - EXIT; exit 1; }
git -C "$LAB" fetch origin "$LAB_BRANCH"
git -C "$LAB" worktree add -b "$NEW_BRANCH" "$WT" FETCH_HEAD
MD5S=()
for entry in "${COPIES[@]}"; do
  src="${entry%%|*}"; dir="${entry##*|}"
  mkdir -p "$WT/$dir"
  cp "$src" "$WT/$dir/"
  git -C "$WT" add -f "$dir/$(basename "$src")"
  MD5S+=("$(md5 -q "$src")  $dir/$(basename "$src")")
done
printf '%s\n' "${MD5S[@]}" > "$WT/docs/mac/MD5SUMS.txt"
git -C "$WT" add -f docs/mac/MD5SUMS.txt
git -C "$WT" commit -m "Mac-only reports: Adamson and Norman results, feature audits, run summaries, state log

Files that existed only on the Mac that ran the experiments. docs/results/ holds full reports; docs/mac/ holds the
running state log, run configs and summaries, helper scripts and earlier untracked notes, copied as they were,
with their md5s in docs/mac/MD5SUMS.txt. No data, run directories or databases."
git -C "$WT" push "$REMOTE" "refs/heads/$NEW_BRANCH:refs/heads/$NEW_BRANCH"
PUSHED+=("$NEW_BRANCH $(git -C "$WT" rev-parse HEAD)")
cleanup; trap - EXIT

echo "== Step 4: what was pushed to $REMOTE"
printf '%s\n' "${PUSHED[@]}"
echo "md5 of each copied file:"
printf '%s\n' "${MD5S[@]}"
echo "DONE"
