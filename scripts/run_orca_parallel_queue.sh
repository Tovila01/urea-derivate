#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ORCA_BIN="/Users/tomvincent/Applications/orca_6_1_1_macosx_arm64_openmpi411/orca"

find \
  "$ROOT_DIR/jobs/adenine" \
  "$ROOT_DIR/jobs/cytosine" \
  "$ROOT_DIR/jobs/guanine" \
  "$ROOT_DIR/jobs/thymine" \
  "$ROOT_DIR/jobs/uracil urea" \
  -maxdepth 1 -type f -name '*_opt_freq.inp' -print0 |
  xargs -0 -n 1 -P 4 bash -lc '
    set -euo pipefail
    ORCA_BIN="$1"
    inp="$2"
    job_dir="$(dirname "$inp")"
    base="$(basename "$inp" .inp)"
    out="$job_dir/$base.out"

    if [ -s "$out" ] && grep -q "ORCA TERMINATED NORMALLY" "$out"; then
      echo "Skipping completed job: $job_dir/$base"
      exit 0
    fi

    echo "Running job: $job_dir/$base"
    cd "$job_dir"
    "$ORCA_BIN" "$(basename "$inp")" > "$base.out"
  ' _ "$ORCA_BIN"
