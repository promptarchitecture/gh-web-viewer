#!/bin/zsh
set -euo pipefail

RUNTIME_DIR="$HOME/Library/Application Support/gh-web-viewer/runtime"
CONTROL_PID_FILE="$RUNTIME_DIR/gh_control_server.pid"
WORKER_PID_FILE="$RUNTIME_DIR/worker.pid"

print_status() {
  local label="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$label: not tracked"
    return
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "$label: running (pid $pid)"
  else
    echo "$label: stopped"
  fi
}

print_status "control" "$CONTROL_PID_FILE"
print_status "worker" "$WORKER_PID_FILE"

printf '\nPorts\n'
lsof -nP -iTCP:8001 -sTCP:LISTEN 2>/dev/null || true
lsof -nP -iTCP:1999 -sTCP:LISTEN 2>/dev/null || true
