#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
QUEUE_NAME="orcaqueue"
WAIT_PID="${1:-}"

if [ -n "$WAIT_PID" ]; then
  echo "Waiting for ORCA queue PID ${WAIT_PID} to end..."
  while ps -p "$WAIT_PID" >/dev/null 2>&1; do
    sleep 60
  done
else
  echo "Waiting for existing ${QUEUE_NAME} screen session to end..."
  while screen -ls 2>/dev/null | grep -q "\\.${QUEUE_NAME}[[:space:]]"; do
    sleep 60
  done
fi

echo "Launching refreshed ${QUEUE_NAME} queue..."
screen -L -dmS "${QUEUE_NAME}" "${ROOT_DIR}/scripts/run_orca_queue.sh"
