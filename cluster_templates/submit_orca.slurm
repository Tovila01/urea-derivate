#!/usr/bin/env bash
#SBATCH --job-name=orca_job
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

set -euo pipefail

INPUT="${1:-}"
if [ -z "$INPUT" ]; then
  echo "Usage: sbatch submit_orca.slurm <input.inp>"
  exit 1
fi

INPUT_ABS="$(readlink -f "$INPUT")"
JOB_DIR="$(dirname "$INPUT_ABS")"
INPUT_FILE="$(basename "$INPUT_ABS")"
BASENAME="${INPUT_FILE%.inp}"

cd "$JOB_DIR"

RWTH_ORCA_BIN="/cvmfs/restricted.hpc.rwth.de/Linux/RH9/x86_64/ISV/ORCA/5.0.4-gompi-2022a/bin/orca"

if [ -x "$RWTH_ORCA_BIN" ]; then
  ORCA_BIN="$RWTH_ORCA_BIN"
elif command -v orca >/dev/null 2>&1; then
  ORCA_BIN="$(command -v orca)"
elif [ -n "${ORCA:-}" ] && [ -x "${ORCA}" ]; then
  ORCA_BIN="${ORCA}"
else
  echo "ORCA executable not found." >&2
  exit 2
fi

"$ORCA_BIN" "$INPUT_FILE" > "$BASENAME.out"
