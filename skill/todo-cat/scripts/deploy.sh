#!/bin/zsh
# todo-cat: redeploy after code changes (kill all instances → clear pid → restart via launchd)
set -e
cd "$HOME/.claude-todo"
python3 -m py_compile app/panel.py app/todo.py
pkill -f panel.py 2>/dev/null || true
sleep 1
rm -f state/panel.pid
launchctl kickstart "gui/$(id -u)/com.todocat.panel"
sleep 3
if pgrep -f panel.py >/dev/null; then
  echo "✅ To-Do running (pid $(pgrep -f panel.py | head -1))"
  tail -1 /tmp/claude-panel.log 2>/dev/null | cut -c1-160
else
  echo "❌ not running — log:"; tail -20 /tmp/claude-panel.log
  exit 1
fi
