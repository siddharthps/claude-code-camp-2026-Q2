---
name: run-mud-adventure
description: Play the tbaMUD (CircleMUD-derived) server running on localhost:4000 as the character "dummy" in a long-form adventure campaign. Use this skill to pursue extended gameplay goals like leveling up, earning gold, exploring the world, and defeating bosses. This skill maintains persistent memory files (data/player.md for character stats/goals, data/world.md for map/NPCs) to track progress across sessions.
---

# tbaMUD Adventure Campaign

This is a live, stateful telnet-style MUD (Multi-User Dungeon), a tbaMUD
variant of CircleMUD/DikuMUD, played as a long-form adventure campaign. The
connection is held open inside a tmux session — tmux survives across separate
tool calls (each invocation is a fresh shell). The Python driver (`scripts/mud.py`)
wraps that tmux session with `send-keys`/`capture-pane` for programmatic input/output.

Character credentials: username `dummy`, password `helloworld`.

## Memory System

This skill maintains two persistent memory files to track long-term progress:

- **`data/player.md`** — Character stats (level, XP, HP, equipment, skills), goals
  (level-up targets, boss defeats), and session notes. Updated after significant
  events (level up, major achievement, death).
- **`data/world.md`** — Map of discovered locations, NPCs, bosses, items, and loot.
  Tracks which areas are safe, which have dangerous enemies, and where to find
  specific quests or items.

Before starting an adventure, review these files to understand current character
state and progress. Update them after major achievements or discoveries.

## Run (agent path)

All paths below are relative to `<unit>/`, i.e. `scripts/mud.py` from the
`02_agent_skills` directory.

```bash
# 1. Open the connection (creates tmux session "mud", starts `nc`)
./scripts/mud.py start

# 2. Log in — runs the name/password/MOTD/menu sequence in one shot
./scripts/mud.py login dummy helloworld

# 3. Issue MUD commands, one per call. Prints only the output produced by
#    that command (echoed input line + server response), not the whole pane.
./scripts/mud.py cmd "look"
./scripts/mud.py cmd "north"
./scripts/mud.py cmd "score"
./scripts/mud.py cmd "inventory"
./scripts/mud.py cmd "say hello world"

# 4. Dump the full visible pane (last ~2000 lines) without sending input —
#    useful if you lost track of state or want to see more scrollback.
./scripts/mud.py read

# 5. Clean shutdown — sends `quit`, kills the tmux session.
./scripts/mud.py stop
```

Every subcommand is verified working against the live server: `start` shows
the client-detect banner and name prompt; `login` walks through name →
password → "PRESS RETURN" → the "Enter the game" menu (choice `1`) and lands
in-room; `cmd` was exercised with `look`, `score`, `inventory`, `west`,
`say`, and `east` and correctly returns just the new output each time.
`start`/`login`/`cmd "look"`/`stop` was run 3 times back-to-back with no
failures.

If a previous session was left open (e.g. a prior run didn't call `stop`),
`start` will refuse with "already running" — either reuse it (skip straight
to `cmd`) or `tmux kill-session -t mud` first.

## Gotchas

- **`start` and `login` poll for the next expected prompt instead of just
  sleeping a fixed amount** (up to `MUD_WAIT_TIMEOUT` seconds, default 10).
  This matters: an earlier version used a flat 1-second sleep, and under load
  `nc` sometimes hadn't finished connecting before the username got sent —
  which made the server treat the password as the *login name* and start
  creating a stray new character ("Did I get that right, Helloworld (Y/N)?").
  If you ever see that confirmation prompt instead of the expected next screen,
  **stop and don't send more keys blindly** — answer `no`/`n` to abort the
  accidental creation, then retry `login`.
- **`cmd`'s "only new output" trick is line-count based**, not a true diff —
  it captures the pane line count before sending input, then tails everything
  after that line count once the response arrives. This is accurate in practice
  but means don't rely on it if the pane scrollback wrapped or the terminal
  was resized between calls.
- **The server sends raw telnet IAC negotiation bytes** (`\xff\xfd\x18`
  etc.) that `nc` doesn't answer — this is fine, the tbaMUD server proceeds
  without a negotiated response, confirmed live.
- **`quit` from mid-menu vs. in-game differs** — `stop` always sends `quit`
  assuming you're in-game (the common case). If you're stuck at a menu, use
  `./scripts/mud.py cmd "0"` (exit from tbaMUD) before `stop`, or just
  `tmux kill-session -t mud` to force-close.
- **Beware the guildmaster in practice:** Over-practicing the kick skill on
  the guildmaster at the Guild of Swordsmen will result in death. The guildmaster
  is much stronger than a level 1 character. Practice sparingly or find monsters
  to fight instead.

## Troubleshooting

- `No active session 'mud'. Run: driver.sh start` — you called `cmd`/`read`/
  `stop` before `start`, or a previous `stop` already tore it down.
- `Session 'mud' already running.` from `start` — a session is already open;
  either use it directly or `tmux kill-session -t mud` to reset.
- Empty output from `cmd`/`start` in the *same* tool call chain — tmux pane
  capture can occasionally race the server's response; call
  `$DRIVER read` to see current state, it always reflects reality.
