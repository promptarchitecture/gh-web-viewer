#!/bin/zsh
set -euo pipefail

RUNTIME_DIR="$HOME/Library/Application Support/gh-web-viewer/runtime"
CONTROL_PID_FILE="$RUNTIME_DIR/gh_control_server.pid"
WORKER_PID_FILE="$RUNTIME_DIR/worker.pid"

stop_pid_file() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 0
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
}

stop_pid_file "$CONTROL_PID_FILE"
stop_pid_file "$WORKER_PID_FILE"

echo "Stopped local gh-web-viewer services."
