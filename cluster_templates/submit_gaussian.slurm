#!/usr/bin/env bash
#SBATCH --job-name=gaussian_job
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

set -euo pipefail

# Adjust these for RWTH cluster policy / module names
module purge
# module load gaussian

INPUT="${1:-}"
if [ -z "$INPUT" ]; then
  echo "Usage: sbatch submit_gaussian.slurm <input.gjf>"
  exit 1
fi

BASENAME="${INPUT%.gjf}"

# Replace with the correct Gaussian launcher on RWTH, e.g. g16 or g09
g16 < "$INPUT" > "$BASENAME.log"
