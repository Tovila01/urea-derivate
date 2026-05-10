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
  echo "Usage: sbatch submit_orca.slurm <input.inp>" >&2
  exit 1
fi

INPUT_ABS="$(readlink -f "$INPUT")"
JOB_DIR="$(dirname "$INPUT_ABS")"
INPUT_FILE="$(basename "$INPUT_ABS")"
BASENAME="${INPUT_FILE%.inp}"

cd "$JOB_DIR"

# ORCA on RWTH needs the module-provided runtime environment.
# Submit after `module load ORCA/5.0.4` and use `sbatch --export=ALL ...`.
if command -v orca >/dev/null 2>&1; then
  ORCA_BIN="$(command -v orca)"
elif [ -n "${ORCA:-}" ] && [ -x "${ORCA}" ]; then
  ORCA_BIN="${ORCA}"
else
  echo "ORCA executable not found in batch environment. Load ORCA/5.0.4 before submission and use sbatch --export=ALL." >&2
  exit 2
fi

"$ORCA_BIN" "$INPUT_FILE" > "$BASENAME.out"
