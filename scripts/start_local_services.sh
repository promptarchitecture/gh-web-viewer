#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer"
LOG_DIR="$HOME/Library/Logs/gh-web-viewer"
RUNTIME_DIR="$HOME/Library/Application Support/gh-web-viewer/runtime"
CONTROL_PID_FILE="$RUNTIME_DIR/gh_control_server.pid"
WORKER_PID_FILE="$RUNTIME_DIR/worker.pid"
CONTROL_LOG_FILE="$LOG_DIR/gh_control_server.log"
WORKER_LOG_FILE="$LOG_DIR/worker.log"
PYTHON_BIN="$(command -v python3)"
PUBLIC_API_BASE="https://gh-web-viewer-api.onrender.com"
LOCAL_API_BASE="http://127.0.0.1:8001"

mkdir -p "$LOG_DIR" "$RUNTIME_DIR"

start_if_needed() {
  local pid_file="$1"
  local log_file="$2"
  shift
  shift
  local -a cmd=("$@")

  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
      return 0
    fi
    rm -f "$pid_file"
  fi

  (
    cd "$PROJECT_ROOT"
    nohup "${cmd[@]}" >>"$log_file" 2>&1 </dev/null &
    echo $! >"$pid_file"
  )
  local new_pid
  new_pid="$(cat "$pid_file")"
  local attempts=0
  while (( attempts < 10 )); do
    if kill -0 "$new_pid" 2>/dev/null; then
      break
    fi
    sleep 1
    attempts=$(( attempts + 1 ))
  done
  if ! kill -0 "$new_pid" 2>/dev/null; then
    echo "Failed to start process for $pid_file" >&2
    if [[ -f "$log_file" ]]; then
      tail -n 40 "$log_file" >&2 || true
    fi
    return 1
  fi
}

start_if_needed \
  "$CONTROL_PID_FILE" \
  "$CONTROL_LOG_FILE" \
  "$PYTHON_BIN" \
  "$PROJECT_ROOT/scripts/gh_control_server.py"

sleep 1

start_if_needed \
  "$WORKER_PID_FILE" \
  "$WORKER_LOG_FILE" \
  "$PYTHON_BIN" \
  "$PROJECT_ROOT/runner/worker.py" \
  --api-base "$PUBLIC_API_BASE" \
  --local-api-base "$LOCAL_API_BASE" \
  --insecure

echo "Started local gh-web-viewer services."
echo "Control PID: $(cat "$CONTROL_PID_FILE")"
echo "Worker PID:  $(cat "$WORKER_PID_FILE")"
echo "Logs:"
echo "  $CONTROL_LOG_FILE"
echo "  $WORKER_LOG_FILE"
