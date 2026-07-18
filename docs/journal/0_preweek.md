# Preweek Technical Documentation

## Technical Goal

Determine how agent architectures fit our use case of autonomous gameplay in extended, open-ended environments. Specifically, we needed to understand which architectural patterns could sustain long-form MUD gameplay (navigation, combat, inventory management, goal completion) while handling dynamic state changes, player death, and exploration of unknown worlds.

### Architecture Spectrum Considered (Simplest → Most Complex)

1. **Direct Scripting** — Hard-coded command sequences; no planning or adaptation. Fails immediately on any deviation from expected state.

2. **Single-Goal Linear Agent** — Agent executes toward one goal with basic state persistence but no mid-task replanning. Continues executing the original plan even if it fails.

3. **State-Aware Reactive Agent** — Agent reads current game state (player location, inventory, NPC positions) before each action and chooses next steps reactively. No forward planning, decisions are immediate.

4. **Adaptive Agent with Replanning** — Agent creates a plan, executes it, and replans if the world state diverges from expectations. Can recover from obstacles or failures mid-task.

5. **Hierarchical Goal Decomposition** — Complex goals broken into sub-goals with checkpoints. Agent can pause at safe breakpoints, preserve state, and resume later without timeout constraints.

6. **Online Learning Agent** — Agent tracks what strategies failed and adjust future actions based on learned patterns. Example: "death from goblins → avoid that area" or "kick works better than punch → practice kick more."

7. **Multi-Agent Orchestrator** — Multiple specialized agents (navigator, combat strategist, inventory manager) coordinating toward shared objectives, delegating sub-tasks based on expertise.

## Technical Uncertainty

1. **Is a coding harness sufficient for non-coding workloads?** — Agent skills are built for code generation. Can they handle open-ended gameplay with dynamic state and unpredictable obstacles, or do they need a different execution model?

2. **Context window bottleneck** — Does the LLM's token limit block extended gameplay (50+ actions, multiple deaths, evolving world state)?

3. **State representation at scale** — Markdown works for small state. Does it break as world complexity grows, or do we need structured storage (JSON/SQLite)?

4. **Connection stability** — Why do telnet connections timeout during long-running tasks? Is this fixable with a persistent SDK, or is it a protocol-level constraint?

5. **Can agents recover and adapt?** — Do agents adjust strategy when initial plans fail, or do they rigidly retry and repeat mistakes?

## Technical Observations

**Haiku without script:** Multiple connection attempts, recreated ad hoc sockets per action, unreliable until fallback to manual intervention.

**Haiku with script:** Reliable connections via dedicated connection driver, but hit timeout walls after 30-40 actions with no recovery mechanism.

**Model comparison:** Sonnet completed quests in iteration 1; Haiku failed after 10+ iterations. Difference was state persistence, not model capability—Haiku never updated player/world state, so had stale info each action. Sonnet reused the stable connection module and persisted state every loop.

**Memory:** Markdown-based state storage works for small tasks. Won't scale—no schema, expensive queries, no relational structure. Structured storage (JSON/SQLite) needed as world grows.

**Pathfinding:** Agent got lost attempting underleveled areas, wasted actions exploring without strategy.

**Error recovery:** Agent died in combat, respawned, repeated the same mistakes. No learning loop.

## Technical Conclusions

**Infrastructure > model capability.** Sonnet succeeded where Haiku failed not due to smarter reasoning, but because Sonnet had stable infrastructure (persistent connection module, state persistence). Same capability, different scaffolding—architecture decided the outcome.

**State storage works for small tasks, not extended gameplay.** Quest-sized tasks fit fine; scaling to complex worlds needs structured storage with schema and relational modeling.

**Linear task execution hits walls at 30-40 actions.** No mid-execution feedback, no replanning, no error recovery. Extended gameplay requires checkpoint-based execution and continuous adaptation.

**Connection stability is solvable.** A dedicated connection driver with polling-based waits proved reliable. The infrastructure works; timeout issues are a limitation of the task execution harness, not the MUD.

**Agents lack recovery mechanisms.** Without adaptive loops, agents can't learn from failure (death → same strategy) or handle exploration efficiently (pathfinding bloat).

## Key Takeaway

Solving extended, adaptive gameplay requires a shift from single linear agents to **multiple specialized agents working together in persistent loops, continuously learning from outcomes**. A navigator handles pathfinding, a combat strategist manages encounters, an inventory manager tracks state—each feeding observations back into a shared learning layer that updates strategy across deaths and respawns. This mirrors how human players evolve: they die, learn, adapt, and retry.
