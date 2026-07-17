#!/usr/bin/env python3
"""
Driver for playing the tbaMUD instance on localhost:4000 via a tmux-held
`nc` connection. tmux gives us a persistent session that survives across
separate tool calls (each Python invocation is a fresh process), and
send-keys/capture-pane give us programmatic input/output.

Usage:
  mud.py start                 # open connection + tmux session
  mud.py login <user> <pass>   # run the name/password/menu sequence
  mud.py cmd "<command>"       # send one MUD command, print fresh output
  mud.py read                  # dump the full visible pane (no input sent)
  mud.py stop                  # send `quit`, kill the tmux session

All state lives in the tmux session named by $SESSION — nothing is written
to disk except tmux's own scrollback.
"""

import os
import sys
import subprocess
import time

SESSION = os.environ.get("MUD_SESSION", "mud")
HOST = os.environ.get("MUD_HOST", "localhost")
PORT = os.environ.get("MUD_PORT", "4000")
SETTLE = float(os.environ.get("MUD_SETTLE", "1"))
WAIT_TIMEOUT = float(os.environ.get("MUD_WAIT_TIMEOUT", "10"))


def run_tmux(*args):
    """Execute a tmux command and return stdout."""
    result = subprocess.run(
        ["tmux"] + list(args),
        capture_output=True,
        text=True
    )
    return result.stdout, result.returncode


def has_session():
    """Check if tmux session exists."""
    _, code = run_tmux("has-session", "-t", SESSION)
    return code == 0


def capture_pane():
    """Get current pane contents."""
    out, _ = run_tmux("capture-pane", "-t", SESSION, "-p", "-S", "-2000")
    return out


def send_keys(text, enter=True):
    """Send keys to tmux session."""
    if enter:
        run_tmux("send-keys", "-t", SESSION, text, "Enter")
    else:
        run_tmux("send-keys", "-t", SESSION, text)


def wait_for(needle):
    """Poll the pane until it contains needle or timeout."""
    attempts = int(WAIT_TIMEOUT * 2)
    for _ in range(attempts):
        pane = capture_pane()
        if needle in pane:
            return True
        time.sleep(0.5)
    return False


def cmd_start():
    """Start a new tmux session with nc connection."""
    if has_session():
        print(f"Session '{SESSION}' already running.", file=sys.stderr)
        sys.exit(1)

    # Create new session with nc
    run_tmux("new-session", "-d", "-s", SESSION, "-x", "200", "-y", "50",
             f"nc {HOST} {PORT}")

    if not wait_for("By what name"):
        print(f"Timed out waiting for name prompt after {WAIT_TIMEOUT} s.", file=sys.stderr)
        print(capture_pane())
        sys.exit(1)

    print(capture_pane())


def cmd_login(user, password):
    """Log in to the MUD."""
    if not has_session():
        print(f"No active session '{SESSION}'. Run: mud.py start", file=sys.stderr)
        sys.exit(1)

    send_keys(user)
    if not wait_for("Password:"):
        print("Timed out waiting for password prompt.", file=sys.stderr)
        print(capture_pane())
        sys.exit(1)

    send_keys(password)
    if not wait_for("PRESS RETURN"):
        print("Did not see the expected MOTD/PRESS RETURN prompt — check for a new-character confirmation instead:", file=sys.stderr)
        print(capture_pane())
        sys.exit(1)

    send_keys("")
    if not wait_for("Make your choice"):
        print("Timed out waiting for main menu.", file=sys.stderr)
        print(capture_pane())
        sys.exit(1)

    send_keys("1")
    time.sleep(SETTLE)
    print(capture_pane())


def cmd_cmd(mud_command):
    """Send a MUD command and print the output."""
    if not has_session():
        print(f"No active session '{SESSION}'. Run: mud.py start", file=sys.stderr)
        sys.exit(1)

    before = len(capture_pane().splitlines())
    send_keys(mud_command)
    time.sleep(SETTLE)
    after_pane = capture_pane()
    after = after_pane.splitlines()

    # Print only the lines produced since sending this command
    if before < len(after):
        print("\n".join(after[before:]))
    else:
        print("\n".join(after))


def cmd_read():
    """Dump the full visible pane."""
    if not has_session():
        print(f"No active session '{SESSION}'. Run: mud.py start", file=sys.stderr)
        sys.exit(1)

    print(capture_pane())


def cmd_stop():
    """Stop the MUD connection and close the session."""
    if not has_session():
        print(f"No active session '{SESSION}'.", file=sys.stderr)
        sys.exit(0)

    send_keys("quit")
    time.sleep(SETTLE)
    run_tmux("kill-session", "-t", SESSION)
    print(f"Session '{SESSION}' stopped.")


def main():
    if len(sys.argv) < 2:
        print("Usage: mud.py {start|login <user> <pass>|cmd \"<command>\"|read|stop}", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        cmd_start()
    elif cmd == "login":
        if len(sys.argv) < 4:
            print("Usage: mud.py login <user> <pass>", file=sys.stderr)
            sys.exit(1)
        cmd_login(sys.argv[2], sys.argv[3])
    elif cmd == "cmd":
        if len(sys.argv) < 3:
            print("Usage: mud.py cmd \"<command>\"", file=sys.stderr)
            sys.exit(1)
        cmd_cmd(sys.argv[2])
    elif cmd == "read":
        cmd_read()
    elif cmd == "stop":
        cmd_stop()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Usage: mud.py {start|login <user> <pass>|cmd \"<command>\"|read|stop}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
