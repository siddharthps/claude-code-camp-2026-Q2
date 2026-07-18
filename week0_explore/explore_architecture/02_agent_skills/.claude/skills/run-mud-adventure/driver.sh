#!/usr/bin/env bash
# Driver for playing the tbaMUD instance on localhost:4000 via a tmux-held
# `nc` connection. tmux gives us a persistent session that survives across
# separate tool calls (each Bash invocation is a fresh shell), and
# send-keys/capture-pane give us programmatic input/output.
#
# Usage:
#   driver.sh start                 # open connection + tmux session
#   driver.sh login <user> <pass>   # run the name/password/menu sequence
#   driver.sh cmd "<command>"       # send one MUD command, print fresh output
#   driver.sh read                  # dump the full visible pane (no input sent)
#   driver.sh stop                  # send `quit`, kill the tmux session
#
# All state lives in the tmux session named by $SESSION — nothing is written
# to disk except tmux's own scrollback.

set -euo pipefail

SESSION="${MUD_SESSION:-mud}"
HOST="${MUD_HOST:-localhost}"
PORT="${MUD_PORT:-4000}"
SETTLE="${MUD_SETTLE:-1}"     # seconds to wait for server output after input
WAIT_TIMEOUT="${MUD_WAIT_TIMEOUT:-10}"  # max seconds to poll for a prompt

require_session() {
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "No active session '$SESSION'. Run: driver.sh start" >&2
    exit 1
  fi
}

# Poll the pane until it contains $1 (a fixed substring, not a regex) or
# $WAIT_TIMEOUT seconds pass. A fixed sleep here is a race: `nc` may not have
# finished connecting, or the server may not have finished printing, before
# the next send-keys fires — which is exactly how a stray character named
# "Helloworld" almost got created (the password got sent as the login name
# because `start` moved on before the name prompt had actually arrived).
wait_for() {
  local needle="$1"
  local attempts=$(( WAIT_TIMEOUT * 2 ))
  for (( i = 0; i < attempts; i++ )); do
    if tmux capture-pane -t "$SESSION" -p -S -2000 | grep -qF "$needle"; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

cmd_start() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already running." >&2
    exit 1
  fi
  tmux new-session -d -s "$SESSION" -x 200 -y 50 "nc $HOST $PORT"
  if ! wait_for "By what name"; then
    echo "Timed out waiting for name prompt after $WAIT_TIMEOUT s." >&2
    tmux capture-pane -t "$SESSION" -p
    exit 1
  fi
  tmux capture-pane -t "$SESSION" -p
}

cmd_login() {
  local user="$1" pass="$2"
  require_session
  tmux send-keys -t "$SESSION" "$user" Enter
  wait_for "Password:" || { echo "Timed out waiting for password prompt." >&2; tmux capture-pane -t "$SESSION" -p; exit 1; }
  tmux send-keys -t "$SESSION" "$pass" Enter
  # Existing character: "*** PRESS RETURN:" after the MOTD.
  # New character (name not yet used): "Did I get that right ... (Y/N)?" —
  # if you see that in the output below, this username doesn't exist yet;
  # stop, don't blindly send more keys, and confirm with the user first.
  if ! wait_for "PRESS RETURN"; then
    echo "Did not see the expected MOTD/PRESS RETURN prompt — check for a new-character confirmation instead:" >&2
    tmux capture-pane -t "$SESSION" -p
    exit 1
  fi
  tmux send-keys -t "$SESSION" "" Enter
  wait_for "Make your choice" || { echo "Timed out waiting for main menu." >&2; tmux capture-pane -t "$SESSION" -p; exit 1; }
  # Land at the "Enter the game" menu; option 1 enters the world.
  tmux send-keys -t "$SESSION" "1" Enter
  sleep "$SETTLE"
  tmux capture-pane -t "$SESSION" -p
}

cmd_cmd() {
  local mud_command="$1"
  require_session
  local before after
  before=$(tmux capture-pane -t "$SESSION" -p -S -2000 | wc -l)
  tmux send-keys -t "$SESSION" "$mud_command" Enter
  sleep "$SETTLE"
  after=$(tmux capture-pane -t "$SESSION" -p -S -2000)
  # Print only the lines produced since sending this command.
  echo "$after" | tail -n +"$before"
}

cmd_read() {
  require_session
  tmux capture-pane -t "$SESSION" -p -S -2000
}

cmd_stop() {
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "No active session '$SESSION'." >&2
    exit 0
  fi
  tmux send-keys -t "$SESSION" "quit" Enter
  sleep "$SETTLE"
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  echo "Session '$SESSION' stopped."
}

case "${1:-}" in
  start) cmd_start ;;
  login) cmd_login "${2:?usage: driver.sh login <user> <pass>}" "${3:?usage: driver.sh login <user> <pass>}" ;;
  cmd)   cmd_cmd "${2:?usage: driver.sh cmd \"<command>\"}" ;;
  read)  cmd_read ;;
  stop)  cmd_stop ;;
  *)
    echo "Usage: driver.sh {start|login <user> <pass>|cmd \"<command>\"|read|stop}" >&2
    exit 1
    ;;
esac
