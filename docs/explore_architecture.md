# MUD Agent Exploration: Model Comparison

## Haiku

- Failed to connect via `nc`, so wrote `mud_interact.py` (telnetlib) as a connection script — but kept recreating ad hoc sockets/temp files instead of reusing it.
- Didn't update `data/player.md` / `data/world.md` each loop, so had no persisted state across iterations.
- I tried till it did 10 iterations, quest never completed. Stayed on-task but couldn't turn MUD responses into a plan.

## Sonnet

- Reused `mud_interact.py` as a persistent interface; read/wrote `data/player.md` and `data/world.md` every loop.
- Completed the quest on iteration 1, using persisted state from the haiku model to decide next commands.

**Why Sonnet won:** it closed the two gaps that stalled Haiku — persistent connection code instead of regenerating it, and actually following the state-update instruction.

## Conclusions

**Connection handling** — don't let the agent author connection code ad hoc each run. Ship a stable `mud_interact.py`-style module (or a small SDK / long-lived connection service) as part of the environment. Removes dropped-connection and one-off-socket failures that have nothing to do with solving the quest.

**State storage** — markdown (`data/player.md`, `data/world.md`) worked here because the state was small, but won't scale:
- No schema — nothing enforces a consistent shape across writes.
- Costly to query — no way to fetch just "current room" without re-parsing the whole file.
- No relationships — MUD worlds are graph-shaped (rooms, items, NPCs); markdown can't represent that natively.
For small, short-lived runs, markdown is fine. As world/state complexity grows, use a structured store (JSON/SQLite) for state, keeping markdown only for human-readable summaries.


