#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ORCA_BIN="/Users/tomvincent/Applications/orca_6_1_1_macosx_arm64_openmpi411/orca"
MAX_TOTAL=4
POLL_SECONDS=10

PENDING_JOBS=(
  "$ROOT_DIR/jobs/adenine/biuret_adenine_opt_freq.inp"
  "$ROOT_DIR/jobs/adenine/semicarbazide_adenine_opt_freq.inp"
  "$ROOT_DIR/jobs/cytosine/biuret_cytosine_opt_freq.inp"
  "$ROOT_DIR/jobs/cytosine/semicarbazide_cytosine_opt_freq.inp"
  "$ROOT_DIR/jobs/guanine/biuret_guanine_opt_freq.inp"
  "$ROOT_DIR/jobs/guanine/semicarbazide_guanine_opt_freq.inp"
  "$ROOT_DIR/jobs/thymine/biuret_thymine_opt_freq.inp"
  "$ROOT_DIR/jobs/thymine/semicarbazide_thymine_opt_freq.inp"
  "$ROOT_DIR/jobs/uracil/biuret_uracil_opt_freq.inp"
  "$ROOT_DIR/jobs/uracil/semicarbazide_uracil_opt_freq.inp"
)

is_finished() {
  local out="$1"
  [ -s "$out" ] && grep -q "ORCA TERMINATED NORMALLY" "$out"
}

active_total() {
  pgrep -af 'prterun -np 2 .*_opt_freq' | wc -l | tr -d ' '
}

launch_job() {
  local inp="$1"
  local job_dir base out

  [ -f "$inp" ] || {
    echo "Missing input file: $inp"
    return 0
  }

  job_dir="$(dirname "$inp")"
  base="$(basename "$inp" .inp)"
  out="$job_dir/$base.out"

  if is_finished "$out"; then
    echo "Skipping completed job: $job_dir/$base"
    return 0
  fi

  echo "Running job: $job_dir/$base"
  (
    cd "$job_dir"
    "$ORCA_BIN" "$(basename "$inp")" > "$base.out"
  ) &
}

started=0

while :; do
  current_active="$(active_total)"
  free_slots=$((MAX_TOTAL - current_active))

  while [ "$free_slots" -gt 0 ] && [ "${#PENDING_JOBS[@]}" -gt 0 ]; do
    launch_job "${PENDING_JOBS[0]}"
    PENDING_JOBS=("${PENDING_JOBS[@]:1}")
    started=$((started + 1))
    free_slots=$((free_slots - 1))
  done

  if [ "${#PENDING_JOBS[@]}" -eq 0 ] && [ "$(active_total)" -eq 0 ]; then
    echo "All biuret and semicarbazide jobs completed."
    exit 0
  fi

  sleep "$POLL_SECONDS"
done
