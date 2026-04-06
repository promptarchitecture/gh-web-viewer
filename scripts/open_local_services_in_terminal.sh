#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer"
CONTROL_CMD="cd '$PROJECT_ROOT' && python3 '$PROJECT_ROOT/scripts/gh_control_server.py'"
WORKER_CMD="cd '$PROJECT_ROOT' && python3 '$PROJECT_ROOT/runner/worker.py' --api-base https://gh-web-viewer-api.onrender.com --local-api-base http://127.0.0.1:8001 --insecure"

osascript <<EOF
tell application "Terminal"
    activate
    do script "$CONTROL_CMD"
    delay 0.8
    do script "$WORKER_CMD"
end tell
EOF

echo "Opened Terminal windows for gh_control_server and worker."
