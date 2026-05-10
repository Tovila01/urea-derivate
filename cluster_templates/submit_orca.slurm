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

# Expect ORCA to be loaded before submission, e.g.:
#   module load ORCA/5.0.4
if command -v orca >/dev/null 2>&1; then
  ORCA_BIN="$(command -v orca)"
elif [ -n "${ORCA:-}" ] && [ -x "${ORCA}" ]; then
  ORCA_BIN="${ORCA}"
else
  echo "ORCA executable not found. Load ORCA before sbatch, e.g. module load ORCA/5.0.4" >&2
  exit 2
fi

"$ORCA_BIN" "$INPUT_FILE" > "$BASENAME.out"
