#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ORCA_BIN="/Users/tomvincent/Applications/orca_6_1_1_macosx_arm64_openmpi411/orca"

job_dirs=(
  "$ROOT_DIR/jobs/adenine"
  "$ROOT_DIR/jobs/cytosine"
  "$ROOT_DIR/jobs/guanine"
  "$ROOT_DIR/jobs/thymine"
  "$ROOT_DIR/jobs/uracil urea"
)

for job_dir in "${job_dirs[@]}"; do
  [ -d "$job_dir" ] || continue

  for inp in "$job_dir"/*_opt_freq.inp; do
    [ -e "$inp" ] || continue
    base="$(basename "$inp" .inp)"
    out="$job_dir/$base.out"

    if [ -s "$out" ] && grep -q "ORCA TERMINATED NORMALLY" "$out"; then
      echo "Skipping completed job: $job_dir/$base"
      continue
    fi

    echo "Running job: $job_dir/$base"
    (
      cd "$job_dir"
      "$ORCA_BIN" "$(basename "$inp")" > "$base.out"
    )
  done
done
