#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <template.gjf> <job_name>"
  exit 1
fi

TEMPLATE="$1"
JOB_NAME="$2"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
JOB_DIR="$ROOT_DIR/jobs/$JOB_NAME"

mkdir -p "$JOB_DIR"
cp "$TEMPLATE" "$JOB_DIR/"

echo "Created job directory: $JOB_DIR"
echo "Copied template: $(basename "$TEMPLATE")"
