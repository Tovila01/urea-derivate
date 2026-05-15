#!/usr/bin/env bash
set -eo pipefail

if [ "${1:-}" != "" ]; then
  ROOT_DIR="$(cd "$1" && pwd)"
elif [ "${DFT_PROJECT_ROOT:-}" != "" ]; then
  ROOT_DIR="$(cd "$DFT_PROJECT_ROOT" && pwd)"
else
  ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fi
ORCA_BIN="/Users/tomvincent/Applications/orca_6_1_1_macosx_arm64_openmpi411/orca"
MAX_CONCURRENT=4
POLL_SECONDS=10

export DYLD_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_LIBRARY_PATH:-}"

running_inps=()
running_pids=()
attempted_jobs=()

is_finished() {
  local out="$1"
  [ -s "$out" ] && grep -q "ORCA TERMINATED NORMALLY" "$out"
}

out_for_input() {
  printf '%s.out' "${1%.inp}"
}

scan_missing_jobs() {
  find "$ROOT_DIR/jobs" -type f -name '*_opt_freq.inp' -print0 |
    while IFS= read -r -d '' inp; do
      out="$(out_for_input "$inp")"
      if ! is_finished "$out"; then
        printf '%s\n' "$inp"
      fi
    done |
    sort
}

launch_job() {
  local inp="$1"
  local job_dir base

  job_dir="$(dirname "$inp")"
  base="$(basename "$inp" .inp)"

  echo "Running job: $job_dir/$base"
  (
    cd "$job_dir"
    "$ORCA_BIN" "$(basename "$inp")" > "$base.out"
  ) &

  running_inps+=("$inp")
  running_pids+=("$!")
  attempted_jobs+=("$inp")
}

reap_jobs() {
  local i inp pid out
  local next_inps=()
  local next_pids=()

  for i in "${!running_pids[@]}"; do
    inp="${running_inps[$i]}"
    pid="${running_pids[$i]}"
    if kill -0 "$pid" >/dev/null 2>&1; then
      next_inps+=("$inp")
      next_pids+=("$pid")
      continue
    fi

    wait "$pid" || true
    out="$(out_for_input "$inp")"
    if is_finished "$out"; then
      echo "Finished job: ${inp%.inp}"
    else
      echo "Job stopped or failed: ${inp%.inp}"
    fi
  done

  running_inps=("${next_inps[@]}")
  running_pids=("${next_pids[@]}")
}

contains_item() {
  local needle="$1"
  local item
  shift
  for item in "$@"; do
    if [ "$item" = "$needle" ]; then
      return 0
    fi
  done
  return 1
}

is_running_or_attempted() {
  local inp="$1"
  contains_item "$inp" "${running_inps[@]}" || contains_item "$inp" "${attempted_jobs[@]}"
}

while :; do
  reap_jobs

  while [ "${#running_pids[@]}" -lt "$MAX_CONCURRENT" ]; do
    next_job=""
    while IFS= read -r inp; do
      if ! is_running_or_attempted "$inp"; then
        next_job="$inp"
        break
      fi
    done < <(scan_missing_jobs)

    if [ -z "$next_job" ]; then
      break
    fi
    launch_job "$next_job"
  done

  if [ "${#running_pids[@]}" -eq 0 ]; then
    remaining_unattempted=0
    while IFS= read -r inp; do
      if ! contains_item "$inp" "${attempted_jobs[@]}"; then
        remaining_unattempted=1
        break
      fi
    done < <(scan_missing_jobs)

    if [ "$remaining_unattempted" -eq 0 ]; then
      echo "No unattempted missing calculations remain."
      exit 0
    fi
  fi

  sleep "$POLL_SECONDS"
done
