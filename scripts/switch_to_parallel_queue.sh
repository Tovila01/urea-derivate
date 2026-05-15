#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CURRENT_OUT="$ROOT_DIR/jobs/adenine/thiourea_adenine_opt_freq.out"
CURRENT_SCREEN="34599.orcaqueue"

echo "Waiting for current calculation to finish: $CURRENT_OUT"
while ! grep -q "ORCA TERMINATED NORMALLY" "$CURRENT_OUT" 2>/dev/null; do
  sleep 5
done

echo "Stopping current queue: $CURRENT_SCREEN"
screen -S "$CURRENT_SCREEN" -X quit || true
echo "Queue stopped after current calculation."
