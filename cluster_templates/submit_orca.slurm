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

module purge
module load ORCA/5.0.4

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

# Write ORCA output next to the input file.
"$ORCA" "$INPUT_FILE" > "$BASENAME.out"
