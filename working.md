Overview

  The week1_baseline/python folder is a progressive tutorial that builds a framework called Boukensha — an AI agent framework designed to play MUD (Multi-User Dungeon) games. It's structured as 12 incremental steps,
  each adding a new capability.

  Think of it as a "from scratch" guide to building an agentic system that can:
  - Connect to LLM APIs (Anthropic, OpenAI, Gemini, Ollama)
  - Make tool calls and handle responses
  - Maintain conversation state
  - Log everything for inspection
  - Provide a nice terminal UI

  ---
  The 12-Step Progression

  Step 0: Configuration

  - What: Load settings from ~/.boukensha/settings.yaml and .env
  - Key class: Config
  - Why: Externalize all configuration so the same code works anywhere

  Step 1: Struct Skeleton

  - What: Define the basic data structures (Message, Context, etc.)
  - Foundation building: Sets up the core types everything else uses

  Step 2: The Registry

  - What: A tool registry that stores and dispatches function calls
  - Key class: Registry
  - How it works: Agent says "call move with direction='north'" → Registry looks up "move" → dispatches it → returns result

  Step 3: Prompt Builder

  - What: Assembles a complete LLM request from the message history
  - Key class: PromptBuilder
  - Handles: Converting messages into provider-specific wire formats

  Step 4: API Client

  - What: Makes HTTP requests to LLM endpoints
  - Key class: Client
  - Uses: Only Python stdlib (urllib, no third-party HTTP libs)
  - Features: Retries on transient failures, handles all 5 major providers

  Step 5: Agent Loop ⭐ (Most Important)

  - What: The core agentic loop that keeps running until done
  - Key class: Agent
  - The loop:
    a. Check if we've hit iteration limits
    b. Call the LLM via the client
    c. Parse the response
    d. If the LLM requests tool calls → dispatch them via registry → save results
    e. If the LLM returns a final answer → return it
    f. Loop until done

  # From agent.py
  def run(self):
      while True:
          if self._iteration_limit_reached():
              return self._wrap_up()  # Summarize what happened

          parsed = self.client.call()

          if parsed["stop_reason"] == "tool_use":
              self._handle_tool_calls(parsed["content"])  # Execute tools
          else:
              return self._extract_text(parsed["content"])  # Done!

  Step 6: Logger

  - What: Records every turn to structured JSON Lines
  - Key class: Logger
  - Writes to: .boukensha/sessions/<session-id>.jsonl
  - Records: iterations, API responses, tool calls, costs, tokens

  Step 7: The run DSL ⭐ (High-level API)

  - What: A simple one-shot entry point
  - Usage:
  from boukensha import run
  
  def register_tools(dsl):
      @dsl.tool("read_file", ...)
      def read_file(path):
          return Path(path).read_text()
  
  result = run(task="Summarize README.md", configure=register_tools)
  print(result)
  - Why: Hides the 6 lower-level classes behind a single function

  Step 8: REPL Loop

  - What: An interactive shell where each turn remembers prior turns
  - Key class: Repl
  - Commands: /help, /quiet, /loud, /clear, /exit
  - Difference from run: run is one shot; repl keeps state across multiple tasks

  Step 10: Standard Tool Library (MCP Integration)

  - What: Instead of hardcoding tools, Boukensha becomes an MCP host
  - MCP = Model Context Protocol (Anthropic standard)
  - How it works:
    - Define MCP servers in settings.yaml (e.g., a filesystem server, a MUD daemon)
    - Boukensha spawns them, discovers their tools, and the agent can call them
  - Why: Tools come from config, not code → add capabilities without rebuilding

  Step 11: Terminal UI (TUI)

  - What: A full terminal UI built with Textual (like VS Code but in the terminal)
  - Layout:
  ┌─ Conversation (scrollable) ─────┐
  ├─ Progress line (spinner, stats) ─┤
  ├─ Input box (boukensha> prompt)  ─┤
  ├─ Status bar (version, tokens)   ─┤
  - Features: Live token counter, iteration counter, tool call tracking, background agent thread

  Step 12: Context Management

  - What: Proper token tracking and automatic context compaction
  - Problems it solves:
    - Know when you're approaching the context limit
    - Auto-compact old messages when you hit 85% full
    - Accurate token counts per API call
    - Support for reasoning/thinking blocks (Claude, Gemini)
  - Visual feedback: Color-coded context usage (green → yellow → red)

  ---
  Core Components You'll See

  Config — Settings management

  - Looks for BOUKENSHA_DIR env var, then ~/.boukensha
  - Reads settings.yaml and .env
  - Returns task settings, MUD credentials, etc.

  Context — Conversation state

  - Holds the message history
  - Tracks token counts
  - Knows the working directory

  Registry — Tool dispatcher

  - Stores functions registered as tools
  - dispatch(name, args) → looks up tool → calls it

  PromptBuilder — Request assembly

  - Takes the message history
  - Converts it to the provider's wire format
  - Includes tools definitions

  Client — HTTP layer

  - POST to the LLM API
  - Handle retries + transient failures
  - Parse the response

  Agent — The loop

  - Orchestrates everything
  - Stops at iteration or token limits
  - Handles tool results

  Logger — JSON audit trail

  - One line = one event (JSON)
  - Immediately flushed (safe with tail)
  - Includes costs, tokens, timing

  ---
  The Configuration System

  All settings live in ~/.boukensha/settings.yaml. Example:

  tasks:
    player:                    # The "player" agent task
      provider: anthropic      # Use Claude
      model: claude-haiku-4-5
      prompt_override:
        system: true           # Use .boukensha/prompts/player/system.md

  agent:
    max_iterations: 25         # Stop after 25 tool calls
    max_output_tokens: 1024    # Per-response token limit
    max_turn_tokens: 60000     # Total tokens this turn
    compaction_threshold: 0.85 # Compact when 85% full

  mcp_servers:
    mud:
      command: mud-manager
      args: [--mcp]
      env:
        MUD_HOST: localhost
        MUD_NAME: Gandalf

    filesystem:
      command: npx
      args: [-y, "@modelcontextprotocol/server-filesystem", /tmp]
      required: false

  ---
  Multi-Provider Support

  Each step can target different LLM backends. Step 4+ support:
  - Anthropic (Claude 3 / Claude 4 family)
  - OpenAI (GPT-4 / GPT-5)
  - Gemini (Google) 
  - Ollama (local LLM)
  - Ollama Cloud

  Each backend normalizes responses to the same shape, so the Agent loop doesn't care which one you use.

  ---
  Why This Structure?

  Each step adds one concern:
  1. Config (externalize settings)
  2. Data structures
  3. Tool storage & dispatch
  4. Request formatting
  5. HTTP & looping (the hard part)
  6. Logging
  7. Simple API
  8. Interactive REPL
  9. (skipped)
  10. MCP tool integration
  11. Nice UI
  12. Token management

  This lets you understand each piece before seeing how they fit together. By step 12, you have a production-ready agent framework.

  ---
  What You'd Actually Use

  For a real project, you'd probably skip straight to:
  - Step 7 (run) for one-shot tasks
  - Step 8 (repl) for interactive loops
  - Step 10 (MCP) for tool integration
  - Step 11 (TUI) for a nice interface
  - Step 12 (context) for token management

  The earlier steps are educational — they show you how to build each piece from scratch.

---

# Step 1: Struct Skeleton - Python Implementation Deep Dive

## Overview
This is the actual implementation of the three core data structures from the guide. They're **intentionally simple** — just containers holding data. No validation, no logic. That comes later.

---

## 1. Tool — A Callable with Metadata

**File:** `boukensha/tool.py` (20 lines)

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    block: Callable[..., Any] | None = None

    def __str__(self):
        return (
            f"#<Tool name={self.name} "
            f"description={str(self.description)[:43]} "
            f"params={list(self.parameters.keys())}>"
        )

    __repr__ = __str__
```

### Breakdown

**Fields:**
- `name: str` — Tool identifier (e.g., `"move"`, `"look"`)
- `description: str` — Human-readable explanation for the LLM
- `parameters: dict` — Schema of arguments. Example:
  ```python
  {
      "direction": {
          "type": "string",
          "description": "north, south, east, west, up, down"
      }
  }
  ```
- `block: Callable[..., Any] | None` — The actual function to call (default: `None`)

**Key insight:** The `block` field holds a lambda or function. When Step 2 (Registry) wants to invoke this tool, it calls `tool.block(...)` with the arguments the LLM specified.

**String representation:**
```
#<Tool name=move description=Move the player in a direction... params=['direction']>
```

This is Ruby-style output for easy debugging and comparison with the reference implementation.

---

## 2. Message — A Single Conversation Turn

**File:** `boukensha/message.py` (14 lines)

```python
@dataclass
class Message:
    role: str
    content: str
    tool_use_id: str | None = None

    def __str__(self):
        id_tag = f" [{self.tool_use_id}]" if self.tool_use_id else ""
        return f"#<Message role={self.role}{id_tag} content={str(self.content)[:61]}...>"

    __repr__ = __str__
```

### Breakdown

**Fields:**
- `role: str` — Either `"user"`, `"assistant"`, or `"tool_result"`
- `content: str` — The actual text
- `tool_use_id: str | None` — Links tool results back to the tool call that produced them

**Role meanings:**
- `"user"` — What the human says
- `"assistant"` — What the LLM says (may include tool calls)
- `"tool_result"` — The result of executing a tool

**String representation:**
```
# User message:
#<Message role=user content=Explore north and tell me what you find....>

# Tool result (with ID):
#<Message role=tool_result [call_abc123] content=You move north into a...>
```

The `[call_abc123]` is the `tool_use_id` that links it back to the original tool call.

---

## 3. Context — The State Holder

**File:** `boukensha/context.py` (31 lines)

```python
class Context:
    def __init__(self, task, system=None):
        self.task = task
        self.system = system
        self.messages = []
        self.tools = {}

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def add_message(self, role, content, tool_use_id=None):
        self.messages.append(Message(role, content, tool_use_id))

    @property
    def tool_count(self):
        return len(self.tools)

    @property
    def turn_count(self):
        return len(self.messages)

    def __str__(self):
        task_name = self.task.task_name() if hasattr(self.task, "task_name") else self.task
        return f"#<Context task={task_name} turns={self.turn_count} tools={self.tool_count}>"

    __repr__ = __str__
```

### Breakdown

**Constructor:**
- `task` — Reference to the task class (e.g., `Player`). Used to get task-specific config.
- `system` — The system prompt string for the LLM.

**State:**
- `messages: list` — All conversation turns in order. Built by calling `add_message()`.
- `tools: dict` — Registered tools, keyed by name. Built by calling `register_tool()`.

**Methods:**
- `register_tool(tool)` — Add a tool to this context
  ```python
  ctx.register_tool(Tool(...))
  # Tools are stored by name for fast lookup
  ```

- `add_message(role, content, tool_use_id=None)` — Create and append a Message
  ```python
  ctx.add_message("user", "What's here?")
  ctx.add_message("assistant", "Let me look around...")
  ctx.add_message("tool_result", "You see a torch-lit corridor.", tool_use_id="call_123")
  ```

**Properties:**
- `tool_count` — How many tools are registered
- `turn_count` — How many messages we've exchanged

**String representation:**
```
#<Context task=player turns=2 tools=1>
```

---

## How They Work Together

### The Example (simplified flow)

```python
# 1. Load config (Step 0)
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(...)

# 2. Create context
ctx = Context(task=Player, system=system_prompt)

# 3. Register tools
ctx.register_tool(Tool(
    name="move",
    description="Move the player in a direction",
    parameters={"direction": {"type": "string"}},
    block=lambda direction: f"You move {direction}."
))

# 4. Add conversation
ctx.add_message("user", "Explore north and tell me what you find.")
ctx.add_message("assistant", "Sure, let me head north and take a look.")

# 5. Inspect the state
print(ctx)  # #<Context task=player turns=2 tools=1>
print(ctx.tools["move"])  # #<Tool name=move ...>
```

### What This Represents

```
Context (the whole conversation state)
├── task: Player (tells us which task this is)
├── system: "You are a MUD player assistant..."
├── tools (what the agent can do):
│   └── "move" → Tool(name="move", block=lambda...)
└── messages (conversation history):
    ├── Message(role="user", content="Explore north...")
    └── Message(role="assistant", content="Sure, let me...")
```

---

## Key Implementation Details

### 1. Dataclasses for Tool and Message
- Python 3.7+ feature
- Automatically generates `__init__`, `__eq__`, etc.
- Clean and concise for simple record types

### 2. Context is NOT a Dataclass
- Needs methods (`register_tool`, `add_message`)
- Mutable state (tools and messages accumulate)
- Regular class is clearer here

### 3. Ruby-style `__str__` Methods
```python
def __str__(self):
    return f"#<ClassName field=value ...>"

__repr__ = __str__  # Make repr() use the same format
```

This makes debugging easy and lets you compare output with the Ruby baseline.

### 4. Tools Stored in a Dict
- `self.tools[name]` enables O(1) lookup by name
- Later (Step 2), the Registry will iterate this dict to find tools

### 5. Messages Stored in a List
- Order matters (conversation history is sequential)
- Appended in chronological order
- Later (Step 5), the LLM API will iterate this list to build the prompt

---

## What's NOT Here

- **No validation** — Can you create a Message with role="invalid"? Yes. Should you? No, but Step 1 doesn't stop you.
- **No serialization** — Can't save/load from JSON yet
- **No API handling** — These are pure Python objects
- **No tool invocation** — The `block` is stored but never called
- **No error handling** — No try/except anywhere

All these come in later steps. Step 1 is scaffolding only.

---

## Running the Example

```bash
cd week1_baseline/python/01_struct_skeleton
python examples/example.py
```

**Expected output:**
```
=== Boukensha Step 1: Struct Skeleton ===

Config:   #<Boukensha::Config dir=/home/.../.boukensha tasks=player>
Context:  #<Context task=player turns=2 tools=1>
Tool:     #<Tool name=move description=Move the player in a direction... params=['direction']>
Messages:
  #<Message role=user content=Explore north and tell me what you find....>
  #<Message role=assistant content=Sure, let me head north and take a look....>
```

---

## Memory Model

When you create a Context and add data:

```python
ctx = Context(task=Player, system="You are...")

# After register_tool():
ctx.tools = {
    "move": Tool(name="move", ...)
}

# After add_message():
ctx.messages = [
    Message(role="user", ...),
    Message(role="assistant", ...)
]
```

Each tool is stored by **name** (fast lookup).
Each message is stored in **order** (chronological).

This design lets Step 2 (Registry) look up tools quickly, and Step 5 (Agent Loop) iterate messages to build the prompt.

---

## Comparison: Python vs Ruby

| Aspect | Python | Ruby |
|--------|--------|------|
| Tool dataclass | `@dataclass` | `class Tool < Struct` |
| String format | `#<Tool ...>` | `#<Tool ...>` |
| Dict lookup | `dict[key]` | `hash[key]` |
| List append | `list.append()` | `array << element` |
| Property | `@property` decorator | `attr_reader` |

The Ruby baseline uses `Struct` and accessor methods; Python uses `@dataclass`. Functionally identical.

---

---

# Step 2: The Registry - Python Implementation Deep Dive

## Overview

Step 2 introduces **the Registry**, which solves a critical problem: *How do we safely look up and invoke tools by name?*

The registry is the **dispatcher** that converts:
- "LLM says: call move with direction='north'"
- Into: Look up "move" → find the function → call it with direction='north' → return result

---

## The Three New Components

### 1. Registry — The Tool Dispatcher

**File:** `boukensha/registry.py` (23 lines)

```python
class Registry:
    def __init__(self, context):
        self.context = context

    def tool(self, name, description, parameters=None):
        def decorator(block):
            registered = Tool(str(name), description, parameters or {}, block)
            self.context.register_tool(registered)
            return block
        return decorator

    def dispatch(self, name, args=None):
        tool = self.context.tools.get(str(name))
        if tool is None:
            raise UnknownToolError(f"No tool registered as '{name}'")
        return tool.block(**(args or {}))
```

### Breakdown

**Constructor:**
- `context` — Reference to a Context object (from Step 1)
- The registry doesn't store tools itself; it delegates to context.tools

**Method 1: `tool()` — A Decorator for Registration**
```python
@registry.tool("move", description="...", parameters={...})
def move(direction):
    return f"You move {direction}."
```

What happens:
1. `tool("move", ...)` returns a decorator function
2. The decorator receives `move` (the actual function)
3. Inside the decorator:
   - Create a Tool object with the function as `block`
   - Call `context.register_tool()` to add it to context.tools
   - Return the function (so it can still be called normally)

Result: The function is registered AND usable directly.

**Method 2: `dispatch()` — Call a Tool by Name**
```python
result = registry.dispatch("move", {"direction": "north"})
```

What happens:
1. Look up "move" in context.tools
2. If not found → raise UnknownToolError
3. If found → call tool.block with args as kwargs: `tool.block(**{"direction": "north"})`
4. Return the result

Key: **args are unpacked as kwargs**, so `{"direction": "north"}` becomes `direction="north"`.

---

### 2. UnknownToolError — Custom Exception

**File:** `boukensha/errors.py` (2 lines)

```python
class UnknownToolError(Exception):
    pass
```

Raised when `dispatch()` tries to call a tool that doesn't exist.

---

## How It All Flows Together

### The Example Walkthrough

```python
# 1. Create context and registry
ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

# 2. Register tools using the decorator
@registry.tool("move", description="...", parameters={...})
def move(direction):
    return f"You move {direction} into a torch-lit corridor."

@registry.tool("shout", description="...", parameters={...})
def shout(message):
    return message.upper()

# Now ctx.tools contains:
# {
#     "move": Tool(name="move", block=<function move>, ...),
#     "shout": Tool(name="shout", block=<function shout>, ...)
# }

# 3. Dispatch tools by name
result = registry.dispatch("shout", {"message": "dragon spotted"})
# → Looks up "shout" in ctx.tools
# → Calls shout(message="dragon spotted")
# → Returns "DRAGON SPOTTED"

result = registry.dispatch("move", {"direction": "north"})
# → Looks up "move" in ctx.tools
# → Calls move(direction="north")
# → Returns "You move north into a torch-lit corridor."

# 4. Error handling
try:
    registry.dispatch("flee")  # No such tool!
except UnknownToolError as e:
    print(f"Error: {e}")  # "No tool registered as 'flee'"
```

### Mental Model

```
Input from LLM: "call move with direction='north'"
    ↓
Registry.dispatch("move", {"direction": "north"})
    ↓
Lookup: ctx.tools["move"] → Tool(block=<function move>)
    ↓
Call: move(direction="north")
    ↓
Return: "You move north into a torch-lit corridor."
```

---

## Key Design Decisions

### 1. Registry Holds a Context Reference (Not Tools)
- **Why?** Keep the registry lightweight. All state lives in Context.
- Context is the single source of truth for tools
- Registry is just the dispatcher / interface

### 2. Decorator Pattern for Registration
```python
@registry.tool("move", ...)
def move(direction):
    pass
```

- **Why?** Clean, Pythonic syntax
- Close to where the function is defined
- The function remains callable directly if needed
- Similar to Flask/FastAPI route decorators

### 3. Args as Kwargs
```python
registry.dispatch("move", {"direction": "north"})
# Becomes: move(direction="north")
```

- **Why?** Named arguments are safer than positional
- Matches the LLM's JSON tool call format
- No ambiguity about argument order

### 4. Raise UnknownToolError
- **Why?** Fail fast and explicitly
- Lets the agent loop know something went wrong
- Better than silently returning None

---

## What Gets Registered?

The `@registry.tool()` decorator does NOT store:
- The function itself (it's not kept in a separate registry)
- It only stores a **Tool object** in context.tools

The Tool object contains:
- `name` — the tool's identifier
- `description` — for the LLM to understand what it does
- `parameters` — schema of arguments (for the LLM)
- `block` — the actual function to call

So when you call `registry.dispatch("move", {...})`:
1. Look up context.tools["move"] → gets the Tool
2. Call tool.block(...) → calls the function

---

## Running the Example

```bash
cd week1_baseline/python/02_the_registry
python examples/example.py
```

**Expected output:**
```
=== BOUKENSHA Step 2: Tool Registry ===

Config:  #<Boukensha::Config dir=/home/.../.boukensha tasks=player>
Context: #<Context task=player turns=0 tools=2>
Tools:
  #<Tool name=move description=Move the player in a direction... params=['direction']>
  #<Tool name=shout description=Shout a message so everyone... params=['message']>

Dispatching 'shout' with message='dragon spotted'...
Result: DRAGON SPOTTED

Dispatching 'move' with direction='north'...
Result: You move north into a torch-lit corridor.

UnknownToolError caught: No tool registered as 'flee'
```

---

## Comparison to Step 1

| Aspect | Step 1 | Step 2 |
|--------|--------|--------|
| How tools registered | Manual: `ctx.register_tool(Tool(...))` | Decorator: `@registry.tool(...)` |
| How tools invoked | Manual: `tool.block(direction="north")` | Dispatch: `registry.dispatch("move", {...})` |
| Tool lookup | Manual: `ctx.tools["move"]` | Automatic: `registry.dispatch()` |
| Error handling | None (KeyError if tool missing) | UnknownToolError raised |
| Purpose | Store tools | Dispatch tools safely |

---

## Data Flow Summary

```
Step 0: Config loads settings
    ↓
Step 1: Context and Tool hold conversation state
    ↓
Step 2: Registry dispatches tools by name
    ↓ (in future steps)
Step 3: PromptBuilder formats messages for LLM
Step 4: Client sends to LLM API
Step 5: Agent loop calls registry.dispatch() when LLM requests tools
```

---

## Why This Pattern?

The registry pattern is used across:
- Web frameworks (Flask, FastAPI) — `@app.route("/move")`
- Task queues (Celery) — `@app.task`
- Test frameworks (pytest) — `@pytest.fixture`

It's a proven way to:
1. Let developers define things close to where they're used
2. Register them centrally without boilerplate
3. Retrieve them by name later

In our case: define tools near where they're implemented, but dispatch them by name from anywhere (especially from the agent loop in Step 5).

---

## What's Next: Step 3

Step 3 introduces **PromptBuilder**, which:
- Takes the message history from Context
- Formats it into a request body for the LLM API
- Includes the tool definitions (from Registry)
- Handles provider-specific formatting (Anthropic, OpenAI, Gemini, etc.)

This is what converts our Python objects into the JSON that the LLM API understands.

---

# Step 3: Prompt Builder - Python Implementation Deep Dive

## Overview

Step 3 solves the **serialization problem**: "How do we convert our Python Message and Tool objects into the provider-specific JSON that each LLM API expects?"

Different LLM providers have different wire formats:
- **Anthropic**: `{"role": "assistant", "content": "...", "tools": [...]}`
- **OpenAI**: `{"role": "assistant", "content": "...", "tools": [{"type": "function", "function": {...}}]}`
- **Gemini**: `{"role": "model", "parts": [{"text": "..."}], "tools": [{"functionDeclarations": [...]}]}`

The solution: **Backend pattern**. Each provider gets its own backend class that knows how to format data for that provider.

---

## The Architecture

```
Context (Python objects)
   ↓
PromptBuilder (delegator)
   ↓
Backend (provider-specific formatter)
   ↓
API Payload (JSON ready for wire)
```

### 1. PromptBuilder — The Simple Delegator

**File:** `boukensha/prompt_builder.py` (20 lines)

```python
class PromptBuilder:
    def __init__(self, context, backend):
        self.context = context
        self.backend = backend

    def to_messages(self):
        return self.backend.to_messages(self.context.messages)

    def to_tools(self):
        return self.backend.to_tools(self.context.tools)

    def to_api_payload(self, max_output_tokens=1024):
        return self.backend.to_payload(self.context, max_output_tokens=max_output_tokens)

    def headers(self):
        return self.backend.headers()

    def url(self):
        return self.backend.url()
```

**Key insight:** PromptBuilder doesn't do any formatting itself. It's just a pass-through to the backend. The backend knows how to format for its provider.

---

### 2. Base Backend — Common Interface and Metadata

**File:** `boukensha/backends/base.py` (59 lines)

Defines the interface that all backends must implement:

```python
class Base:
    @classmethod
    def models(cls):
        return cls.MODELS  # Each subclass defines this

    @classmethod
    def model_info(cls, model):
        return cls.models().get(str(model))

    @classmethod
    def validate_model(cls, model):
        # Verify the model is supported, raise UnsupportedModelError if not
        pass

    @property
    def context_window(self):
        return self._model_info["context_window"]

    @property
    def input_token_cost_per_million(self):
        return self._model_info["cost_per_million"]["input"]

    @property
    def output_token_cost_per_million(self):
        return self._model_info["cost_per_million"]["output"]

    def estimate_cost(self, input_tokens, output_tokens):
        # Calculate API call cost based on token usage
        pass
```

**Each subclass must implement:**
- `MODELS` — dict of model info (context window, costs, etc.)
- `to_messages(messages)` — convert Message objects to provider format
- `to_tools(tools)` — convert Tool objects to provider format
- `to_payload(context, max_output_tokens)` — assemble complete API request
- `headers()` — HTTP headers (authentication, etc.)
- `url()` — API endpoint URL

---

### 3. Anthropic Backend — Example Implementation

**File:** `boukensha/backends/anthropic.py` (81 lines)

```python
class Anthropic(Base):
    BASE_URL = "https://api.anthropic.com/v1/messages"
    MODELS = {
        "claude-haiku-4-5": {
            "context_window": 200_000,
            "cost_per_million": {"input": 1.0, "output": 5.0},
            "usage_unit": "tokens",
        },
        "claude-haiku-4-5-20251001": {...},
        "claude-sonnet-4-6": {...},
        "claude-opus-4-8": {...},
    }

    def __init__(self, api_key, model):
        self.api_key = api_key
        self._configure_model(model)  # From Base, validates and stores model info

    def to_messages(self, messages):
        result = []
        for msg in messages:
            if msg.role == "tool_result":
                # Special case: tool results go in a content block with tool_use_id
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_use_id,
                        "content": msg.content,
                    }],
                })
            else:
                # Regular user/assistant messages
                result.append({"role": msg.role, "content": msg.content})
        return result

    def to_tools(self, tools):
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": list(tool.parameters.keys()),
                },
            }
            for tool in tools.values()
        ]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "model": self.model,
            "system": context.system,
            "max_tokens": max_output_tokens,
            "tools": self.to_tools(context.tools),
            "messages": self.to_messages(context.messages),
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def url(self):
        return self.BASE_URL
```

**Key insight:** Anthropic uses:
- `"role": "user"` for regular messages (not just user queries)
- Tool results wrap in a `"content"` array with `"type": "tool_result"`
- System prompt as a top-level `"system"` field
- Token limit called `"max_tokens"`

---

### 4. OpenAI Backend — Different Wire Format

**File:** `boukensha/backends/openai.py` (71 lines)

OpenAI has a **different** format:

```python
class OpenAI(Base):
    BASE_URL = "https://api.openai.com/v1/chat/completions"
    MODELS = {...}  # GPT models with costs

    def to_messages(self, system, messages):
        # System message as FIRST message in array
        system_message = [{"role": "system", "content": system}]
        conversation = []
        for msg in messages:
            if msg.role == "tool_result":
                # OpenAI calls it "tool", not "tool_result"
                conversation.append({"role": "tool", "tool_call_id": msg.tool_use_id, "content": msg.content})
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system_message + conversation

    def to_tools(self, tools):
        # OpenAI wraps each tool in {"type": "function", "function": {...}}
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                },
            }
            for tool in tools.values()
        ]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "model": self.model,
            "messages": self.to_messages(context.system, context.messages),
            "tools": self.to_tools(context.tools),
            "max_completion_tokens": max_output_tokens,  # Different name!
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def url(self):
        return self.BASE_URL
```

**Differences from Anthropic:**
- System message goes **inside** the messages array (as first element)
- Tool result role is `"tool"` (not wrapped in content)
- Tool field is called `"tool_call_id"` (not `"tool_use_id"`)
- Each tool wrapped in `{"type": "function", "function": {...}}`
- Token limit called `"max_completion_tokens"` (not `"max_tokens"`)

---

### 5. Gemini Backend — Another Variation

**File:** `boukensha/backends/gemini.py` (92 lines)

Gemini's format is **radically different**:

```python
class Gemini(Base):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODELS = {...}  # Gemini models

    def to_messages(self, messages):
        result = []
        for msg in messages:
            if msg.role == "assistant":
                # Gemini calls assistant role "model"
                result.append({"role": "model", "parts": [{"text": msg.content}]})
            elif msg.role == "tool_result":
                # Tool responses are complex objects
                result.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.tool_use_id,  # Uses tool_use_id as function name
                            "response": {"content": msg.content},
                        }
                    }],
                })
            else:
                # User messages wrap in "parts"
                result.append({"role": msg.role, "parts": [{"text": msg.content}]})
        return result

    def to_tools(self, tools):
        if not tools:
            return []
        # Tools wrapped in "functionDeclarations" inside a single element
        return [{
            "functionDeclarations": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                }
                for tool in tools.values()
            ]
        }]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "systemInstruction": {"parts": [{"text": context.system}]},
            "contents": self.to_messages(context.messages),  # Field is "contents"
            "tools": self.to_tools(context.tools),
            "generationConfig": {"maxOutputTokens": max_output_tokens},
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

    def url(self):
        return f"{self.BASE_URL}/{self.model}:generateContent"
```

**Differences:**
- Assistant role is `"model"` (not `"assistant"`)
- Content wrapped in `"parts"` array (not direct string)
- System prompt is `"systemInstruction"` with parts
- Messages field is `"contents"` (not `"messages"`)
- Tools wrapped in `"functionDeclarations"` inside a dict
- Token limit field is `"maxOutputTokens"` (in `generationConfig`)
- URL includes model name as parameter

---

## The Task System

### Base Task Class

**File:** `boukensha/tasks/base.py` (74 lines)

A **stateless** configuration holder that extracts task-specific settings:

```python
class Base:
    """All behavior expressed as classmethods. No instances created."""

    @classmethod
    def task_name(cls):
        raise NotImplementedError(f"{cls} must define task_name()")

    @classmethod
    def provider(cls, settings):
        value = cls._fetch(settings, "provider")
        if value is None:
            raise ValueError(f"tasks.{cls.task_name()}.provider is required")
        return value

    @classmethod
    def model(cls, settings):
        value = cls._fetch(settings, "model")
        if value is None:
            raise ValueError(f"tasks.{cls.task_name()}.model is required")
        return value

    @classmethod
    def is_prompt_override(cls, settings, prompt="system"):
        node = cls._fetch(settings, "prompt_override")
        if not isinstance(node, dict):
            return False
        return node.get(prompt) is True

    @classmethod
    def system_prompt(cls, settings, user_prompts_dir=None, default_prompts_dir=None):
        if cls.is_prompt_override(settings, "system"):
            text = cls._read_user_prompt("system", user_prompts_dir=user_prompts_dir)
            if text:
                return text
        return cls._read_default_prompt("system", default_prompts_dir=default_prompts_dir)
```

**Key pattern:** Every method is a `@classmethod`. No instance state. Just configuration extraction.

### Player Task Class

**File:** `boukensha/tasks/player.py` (8 lines)

```python
class Player(Base):
    @classmethod
    def task_name(cls):
        return "player"
```

That's it! Concrete task just provides the task name. Everything else comes from Base.

**Usage:**
```python
player_settings = config.tasks("player")  # Get settings from YAML
provider = Player.provider(player_settings)  # "anthropic"
model = Player.model(player_settings)  # "claude-haiku-4-5"
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR
)
```

---

## How It All Flows Together

### The Example Walkthrough

```python
# 1. Load config and settings
config = Config()
player_settings = config.tasks("player")

# 2. Get task configuration
system_prompt = Player.system_prompt(player_settings, ...)
provider = Player.provider(player_settings)  # "anthropic"
model = Player.model(player_settings)  # "claude-haiku-4-5"

# 3. Create context and register tools
ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

@registry.tool("look", description="...", parameters={})
def look():
    return "A damp stone corridor..."

@registry.tool("move", description="...", parameters={"direction": {...}})
def move(direction):
    return f"You move {direction}..."

# 4. Add conversation
ctx.add_message("user", "What's around me?")
ctx.add_message("assistant", "Let me look around.")
ctx.add_message("tool_result", "A damp stone corridor...", tool_use_id="toolu_01X")

# 5. Create backend based on provider
if provider == "anthropic":
    backend = backends.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model=model)
elif provider == "openai":
    backend = backends.OpenAI(api_key=os.environ["OPENAI_API_KEY"], model=model)
# ... etc

# 6. Create builder and generate payload
builder = PromptBuilder(ctx, backend)
payload = builder.to_api_payload(max_output_tokens=1024)

# Result: payload is ready to POST to backend.url() with backend.headers()
```

### Mental Model

```
settings.yaml
   ↓
Config.tasks("player")
   ↓
Player.provider(), Player.model(), Player.system_prompt()
   ↓
Context(system=...) + Registry
   ↓
register tools → Context.tools
add messages → Context.messages
   ↓
PromptBuilder(context, backend)
   ↓
backend.to_messages() → Anthropic format
backend.to_tools() → Anthropic format
backend.to_payload() → {"model": "...", "system": "...", "messages": [...], "tools": [...]}
backend.headers() → {"x-api-key": "...", ...}
backend.url() → "https://api.anthropic.com/v1/messages"
   ↓
Ready to POST: requests.post(backend.url(), json=payload, headers=backend.headers())
```

---

## Key Design Decisions

### 1. Backend Pattern (Polymorphism)
- **Why?** Each provider has a different wire format. Rather than if/elif chains everywhere, each backend encapsulates its format.
- **Benefit:** Adding a new provider is adding a new backend class, not changing existing code.

### 2. Base Class for Common Behavior
- **Why?** Model metadata (costs, context windows) is the same interface for all providers.
- **Benefit:** `backend.context_window`, `backend.estimate_cost()` work for any provider.

### 3. Task Classes Are Stateless
- **Why?** Settings come from YAML; don't hardcode them in code.
- **Benefit:** Change settings.yaml, change behavior. No code changes.

### 4. PromptBuilder Delegates to Backend
- **Why?** PromptBuilder's job is coordination, not formatting.
- **Benefit:** Easy to test; PromptBuilder just calls backend methods.

---

## What Gets Passed to the LLM

After `builder.to_api_payload()`, the JSON looks like:

**Anthropic:**
```json
{
  "model": "claude-haiku-4-5",
  "system": "You are a MUD player...",
  "max_tokens": 1024,
  "tools": [
    {
      "name": "move",
      "description": "Move the player in a direction",
      "input_schema": {
        "type": "object",
        "properties": {"direction": {"type": "string"}},
        "required": ["direction"]
      }
    }
  ],
  "messages": [
    {"role": "user", "content": "What's around me?"},
    {"role": "assistant", "content": "Let me look around."},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_01X", "content": "A damp corridor..."}]}
  ]
}
```

**OpenAI (different structure, same semantics):**
```json
{
  "model": "gpt-5.4",
  "messages": [
    {"role": "system", "content": "You are a MUD player..."},
    {"role": "user", "content": "What's around me?"},
    {"role": "assistant", "content": "Let me look around."},
    {"role": "tool", "tool_call_id": "toolu_01X", "content": "A damp corridor..."}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "move",
        "description": "Move the player in a direction",
        "parameters": {
          "type": "object",
          "properties": {"direction": {"type": "string"}},
          "required": ["direction"]
        }
      }
    }
  ],
  "max_completion_tokens": 1024
}
```

The structure is different, but the **content** is the same. That's the beauty of the backend pattern.

---

## Running the Example

```bash
cd week1_baseline/python/03_prompt_builder
python examples/example.py
```

**Expected output:** Pretty-printed JSON payload ready to send to the LLM API.

---

## Supported Providers

At this step, we have:
- **Anthropic** — Claude models
- **OpenAI** — GPT models
- **Gemini** — Google's Gemini models
- **Ollama** — Local LLMs
- **Ollama Cloud** — Ollama hosted

Each is a backend implementing the same interface, different wire format.

---

## What's NOT Here

- **No HTTP calls** — We just build the payload. Client makes the request (Step 4).
- **No response parsing** — We send, but don't handle responses yet.
- **No retries** — Client handles that (Step 4).
- **No token counting** — Context handles that (Step 12).

---

## Comparison: Python vs Ruby

| Aspect | Python | Ruby |
|--------|--------|------|
| Backend inheritance | `class Anthropic(Base)` | `class Anthropic < Base` |
| Models metadata | Class variable `MODELS = {...}` | Class variable `MODELS = {...}` |
| Delegation | Methods call `self.backend.*` | Methods call `@backend.*` |
| Classmethods for tasks | `@classmethod` decorator | `self.class` methods |

The Ruby baseline follows the same pattern. Functionally identical.

---

## Data Flow Summary

```
Step 0: Config loads YAML
   ↓
Step 1: Context holds messages and tools
   ↓
Step 2: Registry dispatches tools by name
   ↓
Step 3: PromptBuilder + Backend format for the wire
   ├─ Different backends for different providers
   └─ Payload ready for HTTP
   ↓ (in future steps)
Step 4: Client sends HTTP request + parses response
Step 5: Agent loop orchestrates everything
```

---

# Step 4: API Client - Python Implementation Deep Dive

## Overview

Step 4 introduces the **Client**, which solves the **HTTP problem**: "How do we safely send requests to LLM APIs, handle failures, and parse responses?"

The Client handles:
- Serializing the payload from PromptBuilder into JSON
- Making HTTPS requests to the LLM endpoint
- **Retrying on transient failures** (network hiccups, temporary rate limits)
- Parsing the JSON response
- Raising clear errors on permanent failures

All using **only Python stdlib** (`urllib`, `json`, `time`, `socket`, `ssl`). No third-party HTTP libraries.

---

## The Client Class

**File:** `boukensha/client.py` (77 lines)

```python
import json
import socket
import ssl
import time
import urllib.error
import urllib.request

from .errors import ApiError


class Client:
    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
    TRANSIENT_ERRORS = (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError,
        ssl.SSLError,
        EOFError,
        socket.gaierror,
    )
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def __init__(self, builder):
        self.builder = builder

    def call(self, max_output_tokens=1024):
        # ... implementation
        pass
```

### Class-Level Configuration

**Retryable Status Codes:**
```python
RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
```

These HTTP status codes indicate transient failures that we should retry:
- `408` — Request Timeout
- `409` — Conflict (usually temporary during rate limits)
- `429` — Too Many Requests (rate limited; wait and retry)
- `500`, `502`, `503`, `504` — Server errors (usually temporary)

We do **not** retry `4xx` errors like `400 (Bad Request)` or `401 (Unauthorized)` — those are permanent.

**Transient Network Errors:**
```python
TRANSIENT_ERRORS = (
    urllib.error.URLError,        # Network unreachable, host not found
    TimeoutError,                 # Connection timed out
    ConnectionError,              # Connection refused, reset by peer
    ssl.SSLError,                 # SSL handshake failed
    EOFError,                      # Premature EOF
    socket.gaierror,              # DNS resolution failed
)
```

These are network-level errors that we should retry (unlike application-level errors like `ValueError`).

**Retry Strategy:**
```python
MAX_RETRIES = 3                   # Try up to 4 times (1 initial + 3 retries)
BASE_RETRY_DELAY = 0.5            # Start with 0.5 second delay
```

---

### The `call()` Method — The Core Logic

**Signature:**
```python
def call(self, max_output_tokens=1024):
    """Make an API call and return the parsed JSON response."""
```

**Flow:**

1. **Prepare the request:**
   ```python
   url = self.builder.url()
   headers = self.builder.headers()
   body = json.dumps(
       self.builder.to_api_payload(max_output_tokens=max_output_tokens)
   ).encode("utf-8")
   ```
   
   - Get URL from backend (e.g., `https://api.anthropic.com/v1/messages`)
   - Get headers from backend (e.g., `{"x-api-key": "...", ...}`)
   - Serialize the payload to JSON bytes

2. **Retry loop:**
   ```python
   attempts = 0
   status = None
   response_body = None

   while True:
       attempts += 1
       request = urllib.request.Request(url, data=body, headers=headers, method="POST")
       
       try:
           with urllib.request.urlopen(request) as response:
               status = response.status
               response_body = response.read()
       except urllib.error.HTTPError as e:
           status = e.code
           response_body = e.read()
       except self.TRANSIENT_ERRORS as e:
           # Network error — retry if we haven't hit the limit
           if attempts > self.MAX_RETRIES:
               raise ApiError(f"API request failed after {attempts} attempts: {type(e).__name__}: {e}")
           time.sleep(self._retry_delay(attempts))
           continue
       
       # Got a response (success or HTTP error). Check if it's retryable.
       if self._retryable_response(status) and attempts <= self.MAX_RETRIES:
           time.sleep(self._retry_delay(attempts))
           continue
       
       break  # Either success or permanent error; stop retrying
   ```

   **What's happening:**
   - Catch both network errors (`TRANSIENT_ERRORS`) and HTTP errors (`HTTPError`)
   - For network errors: if we haven't exceeded `MAX_RETRIES`, wait and retry
   - For HTTP errors: if the status is retryable AND we haven't exceeded retries, wait and retry
   - Otherwise: break out of loop (success or permanent error)

3. **Check final status:**
   ```python
   if not (200 <= status < 300):
       plural = "" if attempts == 1 else "s"
       raise ApiError(
           f"API request failed after {attempts} attempt{plural} "
           f"({status}): {response_body.decode('utf-8', errors='replace')}"
       )
   ```

   If the final status is not 2xx, raise `ApiError` with details.

4. **Parse and return:**
   ```python
   return json.loads(response_body)
   ```

   Return the parsed JSON response object.

---

### Retry Delay — Exponential Backoff

**Method:**
```python
def _retry_delay(self, attempt):
    return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
```

**Example delays:**
- Attempt 1: `0.5 * 2^0 = 0.5s`
- Attempt 2: `0.5 * 2^1 = 1.0s`
- Attempt 3: `0.5 * 2^2 = 2.0s`
- Attempt 4: `0.5 * 2^3 = 4.0s`

**Why exponential backoff?**
- Initial failure → wait 0.5s (maybe service is restarting)
- Still failing → wait 1s (give it more time)
- Still failing → wait 2s (clearly something's wrong)
- Still failing → wait 4s (almost giving up)

This prevents hammering a struggling service.

---

### Retryable Response Check

**Method:**
```python
def _retryable_response(self, status):
    return status in self.RETRYABLE_STATUS_CODES
```

Simple check: is this status code in our retryable set?

---

## Error Handling

**File:** `boukensha/errors.py` (11 lines)

Step 4 adds a new exception:

```python
class ApiError(Exception):
    pass
```

Raised when:
- Network error persists after retries
- HTTP error status (not 2xx) after retries
- Failed to parse JSON response

---

## How It Integrates With PromptBuilder

### The Pipeline

```
Context (messages + tools)
   ↓
PromptBuilder (delegates to backend)
   ↓
Backend (Anthropic/OpenAI/etc)
   └─ to_payload() → dict
   └─ headers() → dict
   └─ url() → string
   ↓
Client (takes builder)
   └─ call() makes HTTP POST request
   └─ returns parsed JSON response
```

### The Example

```python
# 1. Build the context and register tools
ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

@registry.tool("read_file", description="...", parameters={...})
def read_file(path):
    return Path(path).read_text()

# 2. Add a user query
ctx.add_message("user", "What files are in the current directory?")

# 3. Create the backend (provider-specific)
backend = backends.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model="claude-haiku-4-5")

# 4. Create builder (wraps backend)
builder = PromptBuilder(ctx, backend)

# 5. Create client (makes HTTP request)
client = Client(builder)

# 6. Make the call
response = client.call(max_output_tokens=1024)

# Result:
# {
#   "id": "msg_...",
#   "type": "message",
#   "role": "assistant",
#   "content": [
#     {"type": "text", "text": "Let me read that directory..."},
#     {"type": "tool_use", "id": "toolu_...", "name": "read_file", "input": {"path": "."}}
#   ],
#   "model": "claude-haiku-4-5",
#   "stop_reason": "tool_use",
#   "usage": {"input_tokens": 123, "output_tokens": 45}
# }
```

---

## What's in a Response?

The response structure varies by provider, but all contain:

**Anthropic Response:**
```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {"type": "text", "text": "..."},
    {"type": "tool_use", "id": "toolu_...", "name": "move", "input": {"direction": "north"}}
  ],
  "model": "claude-haiku-4-5",
  "stop_reason": "tool_use",
  "usage": {
    "input_tokens": 123,
    "output_tokens": 45
  }
}
```

**Key fields:**
- `content` — List of text blocks and tool calls
- `stop_reason` — Either `"tool_use"` (agent wants to call a tool) or `"end_turn"` (agent is done)
- `usage.input_tokens`, `usage.output_tokens` — Token counts for billing

---

## Retry Examples

### Example 1: Temporary Network Error

```
Attempt 1: URLError (network unreachable) → wait 0.5s → retry
Attempt 2: URLError (network unreachable) → wait 1.0s → retry
Attempt 3: URLError (network unreachable) → wait 2.0s → retry
Attempt 4: URLError → MAX_RETRIES exceeded → raise ApiError
```

### Example 2: Rate Limited

```
Attempt 1: HTTP 429 (Too Many Requests) → wait 0.5s → retry
Attempt 2: HTTP 429 → wait 1.0s → retry
Attempt 3: HTTP 429 → wait 2.0s → retry
Attempt 4: HTTP 429 → MAX_RETRIES exceeded → raise ApiError
```

### Example 3: Permanent Error

```
Attempt 1: HTTP 401 (Unauthorized, bad API key)
           → NOT in RETRYABLE_STATUS_CODES
           → break immediately
           → raise ApiError("API request failed after 1 attempt (401): Invalid API key")
```

### Example 4: Success

```
Attempt 1: HTTP 200 (OK) → return parsed JSON response
```

---

## Why Stdlib Only?

The entire HTTP layer uses only `urllib`, `json`, `time`, `socket`, `ssl` from Python's standard library.

**Why not use `requests`?**
- Standard library is always available
- No external dependencies to manage
- Smaller surface area (fewer bugs, fewer security updates)
- Educational: you see how urllib works

**Drawback:**
- `urllib` API is more verbose than `requests`
- Error handling is more manual
- But it's a reasonable trade-off for an educational framework

---

## Key Design Decisions

### 1. Retryable Status Codes Are Explicit
```python
RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
```

**Why?** Easy to understand which errors trigger retries. No magic.

### 2. Exponential Backoff
```python
def _retry_delay(self, attempt):
    return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
```

**Why?** Prevents hammering a struggling service. Standard practice.

### 3. Transient Errors Are Explicit
```python
TRANSIENT_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, ...)
```

**Why?** Easy to understand which network errors are retryable. Excludes application-level errors.

### 4. ApiError on Final Failure
```python
raise ApiError(f"API request failed after {attempts} attempts...")
```

**Why?** Caller knows the request ultimately failed, and for how long we tried.

### 5. Client Takes a Builder (Not Separate URL/Headers/Payload)
```python
def __init__(self, builder):
    self.builder = builder
```

**Why?** Single source of truth. Builder encapsulates the whole request. Easy to swap builders for testing.

---

## Integration With Step 5 (Agent Loop)

In Step 5, the Agent will use the Client like this:

```python
class Agent:
    def __init__(self, context, registry, client):
        self.context = context
        self.registry = registry
        self.client = client

    def run(self):
        iteration = 0
        while True:
            # Check iteration limit
            if iteration >= max_iterations:
                break
            iteration += 1

            # Make API call
            response = self.client.call()  # ← Uses Client.call()

            # Parse stop_reason
            if response["stop_reason"] == "tool_use":
                # Agent wants to call a tool
                for content in response["content"]:
                    if content["type"] == "tool_use":
                        result = self.registry.dispatch(content["name"], content["input"])
                        self.context.add_message("tool_result", result, tool_use_id=content["id"])
            else:
                # Agent is done
                return self._extract_text(response["content"])
```

The Client is the **HTTP layer** that Agent orchestrates.

---

## Error Messages

When things go wrong, you get clear context:

```
ApiError: API request failed after 4 attempts (429): {
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limit exceeded. Please retry after 60 seconds."
  }
}
```

or

```
ApiError: API request failed after 3 attempts: TimeoutError: _ssl.c:913: The handshake operation timed out
```

---

## What's NOT Here

- **No request queuing** — Client just makes one request. Agent loop decides what to send.
- **No caching** — Each call is fresh.
- **No streaming** — We get the full response at once.
- **No custom retry strategies** — Fixed exponential backoff.
- **No request signing** — Backends handle auth (headers, API keys).

All these could come later or as customizations.

---

## Running the Example

```bash
cd week1_baseline/python/04_api_client
python examples/example.py
```

**Expected output:**
```
=== BOUKENSHA Step 4: API Client ===

Config: #<Boukensha::Config dir=...>
Provider: anthropic
Model: claude-haiku-4-5
Sending request to https://api.anthropic.com/v1/messages...

Raw response:
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I can help you with that..."
    },
    {
      "type": "tool_use",
      "id": "toolu_123",
      "name": "list_directory",
      "input": {
        "path": "."
      }
    }
  ],
  "model": "claude-haiku-4-5",
  "stop_reason": "tool_use",
  "usage": {
    "input_tokens": 234,
    "output_tokens": 89
  }
}
```

---

## Comparison: Python vs Ruby

| Aspect | Python | Ruby |
|--------|--------|------|
| HTTP library | `urllib` (stdlib) | `Net::HTTP` (stdlib) |
| JSON parsing | `json.loads()` | `JSON.parse()` |
| Retry backoff | `BASE_RETRY_DELAY * (2 ** (attempt - 1))` | `BASE_RETRY_DELAY * (2 ** (attempt - 1))` |
| Error types | `urllib.error.HTTPError`, etc. | Similar HTTP error hierarchy |
| Status codes | `response.status` | `response.code` |

The Ruby baseline follows the same retry strategy and error handling.

---

## Token Tracking (Preview of Step 12)

The Client returns token counts in `response["usage"]`:
```python
{
  "input_tokens": 234,
  "output_tokens": 89
}
```

Step 12 (Context Management) will use this to track token usage and warn when approaching context limits.

---

## Data Flow Summary

```
Step 0: Config loads YAML
   ↓
Step 1: Context holds messages and tools
   ↓
Step 2: Registry dispatches tools by name
   ↓
Step 3: PromptBuilder + Backend format for the wire
   ├─ Different backends for different providers
   └─ Payload ready for HTTP
   ↓
Step 4: Client sends HTTP request with retries
   ├─ Handles transient failures (network, rate limits)
   ├─ Exponential backoff
   └─ Returns parsed JSON response
   ↓
Step 5: Agent loop orchestrates everything
Step 6: Logger records everything
```

---

# Step 5: Agent Loop - Python Implementation Deep Dive

## Overview

Step 5 introduces the **Agent**, which orchestrates all previous components into a **loop** that keeps running until the task is complete.

The Agent Loop is the **heart of the framework**. It:
1. Calls the LLM via Client
2. Parses the response via Backend
3. If the LLM wants to call a tool, dispatches it via Registry
4. Adds the tool result to Context
5. Loops back to step 1 (with the tool result added)
6. Stops when the LLM returns a final answer or iteration limit is reached

---

## The Agent Class

**File:** `boukensha/agent.py` (96 lines)

```python
class Agent:
    MAX_ITERATIONS = 25
    WRAP_UP_OUTPUT_TOKENS = 400
    WRAP_UP_DIRECTIVE = (
        "You have reached your action limit for this turn. Do not call any more tools.\n"
        "Briefly summarize what you accomplished, what is still unfinished, and the\n"
        "single next action you would take."
    )

    def __init__(
        self, context, registry, builder, client, task_settings=None,
        max_iterations=None, max_output_tokens=None,
    ):
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.max_iterations = self._resolve_max_iterations(task_settings, max_iterations)
        self.max_output_tokens = self._resolve_max_output_tokens(task_settings, max_output_tokens)
        self.iteration = 0
```

### Constructor Parameters

- `context` — The Context object holding messages and tools
- `registry` — The Registry for dispatching tools
- `builder` — The PromptBuilder for formatting requests
- `client` — The Client for making HTTP calls
- `task_settings` — Optional dict from config.tasks() (provides max_iterations, max_output_tokens)
- `max_iterations` — Override max iterations (or None to use task settings)
- `max_output_tokens` — Override token limit (or None to use task settings)

**Class constants:**
- `MAX_ITERATIONS = 25` — Default max iterations
- `WRAP_UP_OUTPUT_TOKENS = 400` — Token limit for final summary when hitting iteration limit
- `WRAP_UP_DIRECTIVE` — Prompt to use when summarizing

---

## The Main Loop: `run()`

```python
def run(self):
    while True:
        # 1. Check if we've hit the iteration limit
        if self._iteration_limit_reached():
            return self._wrap_up("max_iterations")

        # 2. Increment counter and log
        self.iteration += 1
        print(f"[iteration {self.iteration}/{self.max_iterations}]")

        # 3. Prepare options for LLM
        options = {}
        if self.max_output_tokens is not None:
            options["max_output_tokens"] = self.max_output_tokens

        # 4. Call LLM (via Client) and parse response (via Backend)
        parsed = self.builder.parse_response(self.client.call(**options))

        # 5. Check stop reason
        if parsed["stop_reason"] == "tool_use":
            # LLM wants to call a tool
            self._handle_tool_calls(parsed["content"])
        else:
            # LLM returned a final answer
            return self._extract_text(parsed["content"])
```

### The Loop Flow

**Iteration 1:**
```
Check limit? No → Call LLM with [user message]
LLM says: "I'll look around" (tool_use: "look")
  → Execute "look" → get result
  → Add tool_result to Context
Loop back
```

**Iteration 2:**
```
Check limit? No → Call LLM with [user message, assistant response, tool result]
LLM says: "I found a torch" (tool_use: "move", direction="north")
  → Execute "move" → get result
  → Add tool_result to Context
Loop back
```

**Iteration 3:**
```
Check limit? No → Call LLM with [user, assistant, tool_result, assistant, tool_result]
LLM says: "I moved north and found a dragon. Here's what I learned..."
         (stop_reason: "end_turn", no tool_use)
  → Extract text and return
```

---

## Handling Tool Calls

```python
def _handle_tool_calls(self, content):
    # Add the LLM's response (which includes tool calls) to context
    self.context.add_message("assistant", content)

    # Iterate through content blocks
    for block in content:
        if block.get("type") != "tool_use":
            continue

        # Extract tool name and args
        name = block["name"]
        args = block["input"]
        print(f"  tool call → {name}({args})")

        # Dispatch the tool via registry
        result = self.registry.dispatch(name, args)
        result_text = str(result)
        print(f"  tool result → {result_text[:61]}")

        # Add the tool result to context for the next iteration
        self.context.add_message(
            "tool_result", result_text, tool_use_id=block["id"]
        )
```

**What happens:**
1. Save the assistant's response (with tool calls) to Context
2. For each tool call block in the response:
   - Extract name and args
   - Print for debugging
   - Call `registry.dispatch(name, args)` to execute
   - Convert result to string
   - Save result to Context with the tool call's ID

**Key:** The tool result is added to Context, which means the next LLM call will see it.

---

## Extracting Final Text

```python
@staticmethod
def _extract_text(content):
    return "".join(
        block.get("text", "") for block in content if block.get("type") == "text"
    )
```

When the LLM returns `"end_turn"` (no more tool calls), extract all text blocks and concatenate them.

**Example:**
```
content = [
    {"type": "text", "text": "I explored "},
    {"type": "text", "text": "the dungeon "},
    {"type": "other", "data": "..."},
]

→ "I explored the dungeon "
```

---

## Iteration Limits

### Checking Limits

```python
def _iteration_limit_reached(self):
    return self.max_iterations > 0 and self.iteration >= self.max_iterations
```

Returns `True` when:
- `max_iterations > 0` (limit is set, not unlimited)
- AND `iteration >= max_iterations` (we've reached it)

**Example:** If `max_iterations=3` and `iteration=3`, we've reached the limit.

### Resolving Max Iterations

```python
def _resolve_max_iterations(self, task_settings, explicit):
    if explicit is not None:
        return int(explicit)
    task = self.context.task
    if task_settings is not None and hasattr(task, "max_iterations"):
        return task.max_iterations(task_settings)
    return self.MAX_ITERATIONS
```

**Priority (highest to lowest):**
1. Explicit parameter: `Agent(..., max_iterations=10)`
2. Task method: `Player.max_iterations(task_settings)`
3. Class default: `Agent.MAX_ITERATIONS` (25)

### Resolving Max Output Tokens

```python
def _resolve_max_output_tokens(self, task_settings, explicit):
    if explicit is not None:
        return explicit
    task = self.context.task
    if task_settings is not None and hasattr(task, "max_output_tokens"):
        return task.max_output_tokens(task_settings)
    return None
```

Same priority system. If no override, `None` means no limit.

---

## Wrapping Up When Limit Reached

```python
def _wrap_up(self, reason):
    # Add a directive to the LLM
    self.context.add_message("user", self.WRAP_UP_DIRECTIVE)

    try:
        # Call the LLM ONE MORE TIME with tools disabled
        response = self.client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
        text = self._extract_text(self.builder.parse_response(response)["content"])
        return text if text.strip() else self._fallback_message(reason)
    except ApiError:
        # If the wrap-up call fails, use fallback
        return self._fallback_message(reason)
```

**When iteration limit is reached:**
1. Add `WRAP_UP_DIRECTIVE` to context (tells LLM it's out of actions)
2. Call LLM ONE MORE TIME with `tools=[]` (no tools available)
3. LLM should respond with a summary
4. Extract and return the text
5. If that fails, use a fallback message

**Fallback message:**
```python
def _fallback_message(self, reason):
    return (
        f"I reached my {self.max_iterations}-action limit for this turn before finishing "
        f"({reason}). Ask me to continue and I'll pick up from here."
    )
```

---

## Integration With the Backend

### Response Parsing

Step 5 adds a new method to the backend: `parse_response()`.

**In Anthropic backend:**
```python
def parse_response(self, response):
    return {
        "stop_reason": (
            "tool_use" if response.get("stop_reason") == "tool_use" else "end_turn"
        ),
        "content": response.get("content") or [],
    }
```

**Why?** Normalize different providers' response formats into a common structure.

**The normalized structure:**
```python
{
    "stop_reason": "tool_use" or "end_turn",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
    ]
}
```

### Client Enhancement

Step 5 updates Client to accept tool options:

```python
def call(self, max_output_tokens=1024, tools=None):
    url = self.builder.url()
    headers = self.builder.headers()
    body = json.dumps(
        self.builder.to_api_payload(
            max_output_tokens=max_output_tokens, tools=tools
        )
    ).encode("utf-8")
```

**Why?** When wrapping up (iteration limit), Agent passes `tools=[]` to disable tool calling.

---

## Complete Example Flow

```python
# Setup
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(player_settings, ...)

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

@registry.tool("read_file", ...)
def read_file(path):
    return Path(path).read_text()

@registry.tool("list_directory", ...)
def list_directory(path):
    return "\n".join(sorted(...))

# Create the agent
backend = backends.Anthropic(api_key=..., model=...)
builder = PromptBuilder(ctx, backend)
client = Client(builder)
agent = Agent(
    context=ctx,
    registry=registry,
    builder=builder,
    client=client,
    task_settings=player_settings,
)

# Add initial query
ctx.add_message("user", "Read README.md and summarize it.")

# Run the agent
result = agent.run()
```

**Execution trace:**
```
[iteration 1/25]
  tool call → read_file({"path": "README.md"})
  tool result → # Boukensha: An AI Agent Framework...

[iteration 2/25]
  (LLM sees: user message + assistant response + tool result)
  (LLM says: "I read the README. Here's the summary...")
  (stop_reason: "end_turn")

Final result:
"Boukensha is a framework for building AI agents that play MUD games. 
It provides components for: configuration (Step 0), data structures (Step 1),
tool dispatch (Step 2), prompt building (Step 3), HTTP client (Step 4),
agentic loop (Step 5), logging (Step 6)..."
```

---

## Key Design Decisions

### 1. Iteration Counter and Limits
```python
def _iteration_limit_reached(self):
    return self.max_iterations > 0 and self.iteration >= self.max_iterations
```

**Why?** Prevent infinite loops. If the LLM keeps calling tools without making progress, we stop it.

### 2. Three-Level Configuration
```python
# Priority: explicit > task_settings > class default
max_iter = self._resolve_max_iterations(task_settings, explicit)
```

**Why?** Flexibility. Use class defaults, override per task, override per call.

### 3. Wrap-Up With Fresh LLM Call
```python
response = self.client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
```

**Why?** When hitting iteration limit, we want the LLM to summarize, not just cut it off. By calling once more with no tools, the LLM provides a summary.

### 4. Tool Results Link to Tool Calls
```python
self.context.add_message("tool_result", result_text, tool_use_id=block["id"])
```

**Why?** The LLM needs to know which result matches which call. The `tool_use_id` creates that link.

### 5. Normalized Response Parsing
```python
parsed = self.builder.parse_response(self.client.call(**options))
```

**Why?** Different providers return different response formats. Parsing normalizes to a common shape.

---

## Control Flow Diagram

```
┌─ Start Agent.run()
│
├─ Check iteration limit
│  ├─ Reached? → Wrap up and return
│  └─ Not reached? → Continue
│
├─ Increment iteration counter
│
├─ Call LLM (via Client)
│
├─ Parse response (via Backend)
│
├─ Check stop_reason
│  ├─ "tool_use"?
│  │  ├─ Handle each tool call
│  │  ├─ Dispatch via Registry
│  │  ├─ Save result to Context
│  │  └─ Loop back to iteration limit check
│  │
│  └─ "end_turn"?
│     ├─ Extract text from content
│     └─ Return to caller
```

---

## Response Format (Normalized by Backend)

**Anthropic:**
```json
{
  "stop_reason": "tool_use",
  "content": [
    {"type": "text", "text": "Let me check that..."},
    {"type": "tool_use", "id": "toolu_123", "name": "read_file", "input": {"path": "README.md"}}
  ]
}
```

**What Agent sees (normalized):**
```python
{
    "stop_reason": "tool_use",
    "content": [
        {"type": "text", "text": "Let me check that..."},
        {"type": "tool_use", "id": "toolu_123", "name": "read_file", "input": {"path": "README.md"}}
    ]
}
```

---

## Running the Example

```bash
cd week1_baseline/python/05_agent_loop
python examples/example.py
```

**Expected output:**
```
=== BOUKENSHA Step 5: Agent Loop ===

Config: #<Boukensha::Config dir=...>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: None

[iteration 1/25]
  tool call → read_file({"path": "README.md"})
  tool result → # Boukensha: An AI Agent Framework...

[iteration 2/25]
  (LLM thinks, then returns final answer)

=== FINAL RESPONSE ===
Boukensha is a progressive tutorial for building an AI agent framework...
```

---

## What Gets Logged to Context

After a single `Agent.run()` with 2 iterations:

```python
ctx.messages = [
    Message(role="user", content="Read README.md and summarize..."),
    Message(role="assistant", content=[
        {"type": "text", "text": "Let me read that..."},
        {"type": "tool_use", "id": "toolu_123", "name": "read_file", "input": {...}}
    ]),
    Message(role="tool_result", content="# Boukensha...", tool_use_id="toolu_123"),
    Message(role="assistant", content=[
        {"type": "text", "text": "Here's the summary..."}
    ]),
]
```

---

## Comparison: Python vs Ruby

| Aspect | Python | Ruby |
|--------|--------|------|
| Main loop | `while True: ... break` | `loop do ... break end` |
| Iteration counter | `self.iteration` | `@iteration` |
| Tool dispatching | `registry.dispatch(name, args)` | `registry.dispatch(name, args)` |
| Text extraction | List comprehension | `.compact.map { ... }.join` |
| Configuration resolution | Three-level if/elif chain | Three-level if/elsif chain |

Functionally identical.

---

## What Gets Passed to the Next Iteration

After handling a tool call, Context now contains:

1. Original user message
2. Assistant's response (with tool call)
3. Tool result (with link back to tool call ID)

The next LLM call sees all three, so the LLM knows:
- What the user asked
- What I decided to do
- What happened when I did it

This is how the loop "remembers" context across iterations.

---

## Error Handling

**In `_wrap_up()`:**
```python
try:
    response = self.client.call(tools=[], ...)
    ...
except ApiError:
    return self._fallback_message(reason)
```

If the wrap-up LLM call fails (network error, rate limit, etc.), we return a fallback message instead of crashing.

---

## Debugging

Agent prints iteration number and tool calls:

```
[iteration 1/25]
  tool call → read_file({"path": "README.md"})
  tool result → # Boukensha: An AI Agent Framework for...
```

This makes it easy to see:
- How many iterations it took
- Which tools were called
- What the results were (first 61 chars)

---

## Data Flow Summary (Complete)

```
Step 0: Config loads YAML
   ↓
Step 1: Context holds messages and tools
   ↓
Step 2: Registry dispatches tools by name
   ↓
Step 3: PromptBuilder + Backend format for the wire
   ├─ Different backends for different providers
   └─ Payload ready for HTTP
   ↓
Step 4: Client sends HTTP request with retries
   ├─ Handles transient failures (network, rate limits)
   ├─ Exponential backoff
   └─ Returns parsed JSON response
   ↓
Step 5: Agent loop orchestrates everything ⭐
   ├─ Iteration counter + limits
   ├─ Tool call handling via Registry
   ├─ Tool result storage in Context
   ├─ Response parsing (normalized format)
   └─ Loop until done or limit reached
   ↓ (in future steps)
Step 6: Logger records everything
Step 7+: Higher-level APIs and UI
```

---

# Step 6: The Logger - Python Implementation Deep Dive

## Overview

Step 6 introduces the **Logger**, which solves the **observability problem**: "How do we record everything that happens during an agent run so we can debug, analyze, and audit the behavior?"

The Logger writes **structured JSON Lines** to a file, with one JSON object per line. Each line is an event (iteration start, tool call, tool result, API response, etc.).

**Key features:**
- Writes to `.boukensha/sessions/<session-id>.jsonl`
- Auto-flushes after each event (safe to tail the file)
- Includes token counts, costs, timing, and metadata
- Supports multiple providers with normalized token tracking
- Optional debug mode for full API responses

---

## The Logger Class

**File:** `boukensha/logger.py` (156 lines)

```python
class Logger:
    DEFAULT_SESSION_DIR = "sessions"

    def __init__(self, session_id=None, dir=None, log=None, snapshot=None):
        self.session_id = session_id or self._generate_session_id()
        if log is not None:
            self.path = Path(log)
        else:
            if dir is None:
                from . import config
                dir = Path(config().dir) / self.DEFAULT_SESSION_DIR
            self.path = Path(dir) / f"{self.session_id}.jsonl"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._log = self.path.open("a", encoding="utf-8")
        event = {"phase": "session_start"}
        event.update(snapshot or {})
        self._write(event)
```

### Constructor

**Parameters:**
- `session_id` — Optional custom session ID. If None, auto-generates one.
- `dir` — Optional directory for log files. Defaults to `~/.boukensha/sessions/`
- `log` — Optional direct file path. If provided, ignores `dir`.
- `snapshot` — Optional dict of metadata to include in session_start event

**Initialization:**
1. Generate or use provided session ID
2. Determine log file path
3. Create parent directories if needed
4. Open file in append mode
5. Write `session_start` event

### Session ID Format

```python
@staticmethod
def _generate_session_id():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(4)}"
```

**Example:** `20260726T143022Z-a1b2c3d4`

**Why this format?**
- Timestamp makes it sortable and human-readable
- Random hex makes it collision-proof
- All in one field = easy to filter/grep

---

## Event Types

### 1. Iteration Start

```python
def iteration(self, n, max):
    self._write({"phase": "iteration", "n": n, "max": max})
```

**Example event:**
```json
{"phase": "iteration", "n": 1, "max": 25, "session_id": "...", "at": "2026-07-26T14:30:22+00:00"}
```

**When:** Agent enters a new iteration.

---

### 2. Prompt/Messages Sent

```python
def prompt(self, messages, tools):
    self._write({
        "phase": "prompt",
        "message_count": len(messages),
        "messages": [
            {"role": message.role, "content": message.content}
            for message in messages
        ],
        "tool_count": len(tools),
        "tools": list(tools.keys()),
    })
```

**Example event:**
```json
{
  "phase": "prompt",
  "message_count": 3,
  "messages": [
    {"role": "user", "content": "Read README.md"},
    {"role": "assistant", "content": "[...]"},
    {"role": "tool_result", "content": "# Boukensha..."}
  ],
  "tool_count": 2,
  "tools": ["read_file", "list_directory"],
  "session_id": "...",
  "at": "..."
}
```

**When:** Before sending the prompt to the LLM.

---

### 3. Tool Call

```python
def tool_call(self, name, args):
    self._write({"phase": "tool_call", "name": name, "args": args})
```

**Example event:**
```json
{
  "phase": "tool_call",
  "name": "read_file",
  "args": {"path": "README.md"},
  "session_id": "...",
  "at": "..."
}
```

**When:** Agent requests a tool call.

---

### 4. Tool Result

```python
def tool_result(self, name, result, ok=True, error=None):
    self._write({
        "phase": "tool_result", "name": name, "result": str(result),
        "ok": ok, "error": error,
    })
```

**Example event (success):**
```json
{
  "phase": "tool_result",
  "name": "read_file",
  "result": "# Boukensha: An AI Agent Framework...",
  "ok": true,
  "session_id": "...",
  "at": "..."
}
```

**Example event (error):**
```json
{
  "phase": "tool_result",
  "name": "read_file",
  "result": "ERROR: FileNotFoundError: [Errno 2] No such file or directory: 'MISSING.md'",
  "ok": false,
  "error": "[Errno 2] No such file or directory: 'MISSING.md'",
  "session_id": "...",
  "at": "..."
}
```

**When:** After dispatching a tool.

---

### 5. LLM Response

```python
def response(self, text, usage=None, stop_reason=None, task=None, backend=None):
    event = {
        "phase": "response", "text": str(text).strip(),
        "usage": usage, "stop_reason": stop_reason,
    }
    event.update(self._execution_metadata(task, backend, usage))
    self._write(event)
```

**Example event:**
```json
{
  "phase": "response",
  "text": "Let me read that file...",
  "usage": {"input_tokens": 234, "output_tokens": 89},
  "stop_reason": "tool_use",
  "task": "player",
  "provider": "anthropic",
  "model": "claude-haiku-4-5",
  "usage_unit": "tokens",
  "input_tokens": 234,
  "output_tokens": 89,
  "cost_usd": 0.000631,
  "session_id": "...",
  "at": "..."
}
```

**What's included:**
- `text` — The LLM's response text (or reasoning if tool_use)
- `usage` — Token counts from the API
- `stop_reason` — "tool_use" or "end_turn"
- `task`, `provider`, `model` — Execution metadata
- `input_tokens`, `output_tokens` — Extracted from usage
- `cost_usd` — Estimated cost based on model pricing

**When:** After receiving response from LLM.

---

### 6. Iteration Limit Reached

```python
def limit_reached(self, kind, n, max):
    self._write({"phase": "limit_reached", "kind": kind, "n": n, "max": max})
```

**Example event:**
```json
{
  "phase": "limit_reached",
  "kind": "max_iterations",
  "n": 25,
  "max": 25,
  "session_id": "...",
  "at": "..."
}
```

**When:** Agent hits iteration limit.

---

### 7. Turn End

```python
def turn_end(self, reason, iterations, tokens=None):
    self._write({
        "phase": "turn_end", "reason": reason,
        "iterations": iterations, "tokens": tokens,
    })
```

**Example event:**
```json
{
  "phase": "turn_end",
  "reason": "completed",
  "iterations": 2,
  "tokens": 323,
  "session_id": "...",
  "at": "..."
}
```

**Reasons:** `"completed"`, `"max_iterations"`, etc.

**When:** Agent run finishes.

---

### 8. Raw API Response (Debug Mode)

```python
def raw(self, data):
    from . import is_debug
    if is_debug():
        self._write({"phase": "raw", "data": data})
```

**Example event:**
```json
{
  "phase": "raw",
  "data": {
    "id": "msg_...",
    "type": "message",
    "role": "assistant",
    "content": [...],
    "model": "claude-haiku-4-5",
    "stop_reason": "tool_use",
    "usage": {"input_tokens": 234, "output_tokens": 89}
  },
  "session_id": "...",
  "at": "..."
}
```

**When:** After each API response (only if debug mode enabled).

---

## Token Tracking Across Providers

Different providers use different field names for token counts:

```python
@classmethod
def _usage_tokens(cls, usage):
    usage = usage if isinstance(usage, dict) else {}
    return (
        cls._first_integer(usage, "input_tokens", "prompt_tokens", "promptTokenCount", "prompt_eval_count"),
        cls._first_integer(usage, "output_tokens", "completion_tokens", "candidatesTokenCount", "eval_count"),
    )
```

**Handles:**
- **Anthropic:** `input_tokens`, `output_tokens`
- **OpenAI:** `prompt_tokens`, `completion_tokens`
- **Gemini:** `promptTokenCount`, `candidatesTokenCount`
- **Ollama:** `prompt_eval_count`, `eval_count`

The logger tries keys in order until it finds a match. This normalizes different providers to a common format.

---

## Cost Estimation

```python
@staticmethod
def _estimate_cost(backend, input_tokens, output_tokens):
    estimate = getattr(backend, "estimate_cost", None)
    if not callable(estimate) or input_tokens is None or output_tokens is None:
        return None
    return estimate(input_tokens, output_tokens)
```

The Logger calls `backend.estimate_cost()` (from Step 3/Base class) to calculate USD cost:

```
cost = (input_tokens * input_cost_per_million + output_tokens * output_cost_per_million) / 1_000_000
```

**Example:** 234 input tokens + 89 output tokens on Claude Haiku:
```
cost = (234 * 1.0 + 89 * 5.0) / 1_000_000 = 0.000631 USD
```

---

## Metadata Extraction

```python
def _execution_metadata(self, task, backend, usage):
    if task is None and backend is None and usage is None:
        return {}

    input_tokens, output_tokens = self._usage_tokens(usage)
    metadata = {
        "task": self._task_name(task),
        "provider": self._provider_name(backend),
        "model": getattr(backend, "model", None),
        "usage_unit": getattr(backend, "usage_unit", None),
        "usage_level": getattr(backend, "usage_level", None),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": self._estimate_cost(backend, input_tokens, output_tokens),
    }
    return {key: value for key, value in metadata.items() if value is not None}
```

**Provider name conversion:**
```python
@staticmethod
def _provider_name(backend):
    if backend is None:
        return None
    name = backend.__class__.__name__
    return re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name).lower()
```

**Example:** `Anthropic` → `anthropic`, `OllamaCloud` → `ollama_cloud`

---

## Writing Events

```python
def _write(self, event):
    record = dict(event)
    record["session_id"] = self.session_id
    record["at"] = datetime.now().astimezone().isoformat()
    self._log.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
    self._log.flush()
```

**What happens:**
1. Create a copy of the event
2. Add session ID
3. Add ISO 8601 timestamp (includes timezone)
4. Serialize to JSON (compact format)
5. Write newline
6. **Flush immediately** (safe for `tail -f`)

**Why flush?** So you can watch logs in real-time: `tail -f .boukensha/sessions/20260726T*.jsonl`

---

## Context Manager Support

```python
def __enter__(self):
    return self

def __exit__(self, exc_type, exc_value, traceback):
    self.close()
```

**Usage:**
```python
with Logger() as logger:
    agent = Agent(..., logger=logger)
    agent.run()
# Logger automatically closed when exiting the block
```

---

## Integration With Agent

In Step 6, Agent is updated to use Logger:

```python
def __init__(self, ..., logger=None):
    self.logger = logger if logger is not None else Logger()
    ...

def run(self):
    while True:
        if self._iteration_limit_reached():
            self.logger.limit_reached(
                kind="max_iterations", n=self.iteration, max=self.max_iterations
            )
            return self._wrap_up("max_iterations")

        self.iteration += 1
        self.logger.iteration(n=self.iteration, max=self.max_iterations)
        self.logger.prompt(messages=self.context.messages, tools=self.context.tools)
        
        response = self.client.call(**options)
        self.logger.raw(data=response)
        parsed = self.builder.parse_response(response)

        if parsed["stop_reason"] == "tool_use":
            self._handle_tool_calls(parsed["content"], response)
        else:
            text = self._extract_text(parsed["content"])
            self._log_response(text, response)
            self.logger.turn_end(reason="completed", iterations=self.iteration)
            return text
```

**Tool call handling also logs:**
```python
def _handle_tool_calls(self, content, response):
    self._log_response(reasoning, response)
    ...
    for block in tool_calls:
        name = block["name"]
        args = block["input"]
        self.logger.tool_call(name=name, args=args)
        try:
            result = self.registry.dispatch(name, args)
            self.logger.tool_result(name=name, result=result, ok=True)
        except Exception as error:
            result = f"ERROR: {error.__class__.__name__}: {error}"
            self.logger.tool_result(
                name=name, result=result, ok=False, error=str(error)
            )
```

---

## Example Log File

A single agent run produces a file like `.boukensha/sessions/20260726T143022Z-a1b2c3d4.jsonl`:

```json
{"phase":"session_start","session_id":"20260726T143022Z-a1b2c3d4","at":"2026-07-26T14:30:22+00:00"}
{"phase":"iteration","n":1,"max":25,"session_id":"...","at":"2026-07-26T14:30:22+00:00"}
{"phase":"prompt","message_count":1,"messages":[{"role":"user","content":"Read README.md"}],"tool_count":2,"tools":["read_file","list_directory"],"session_id":"...","at":"2026-07-26T14:30:22+00:00"}
{"phase":"response","text":"Let me read that file...","usage":{"input_tokens":234,"output_tokens":89},"stop_reason":"tool_use","task":"player","provider":"anthropic","model":"claude-haiku-4-5","input_tokens":234,"output_tokens":89,"cost_usd":0.000631,"session_id":"...","at":"2026-07-26T14:30:23+00:00"}
{"phase":"tool_call","name":"read_file","args":{"path":"README.md"},"session_id":"...","at":"2026-07-26T14:30:23+00:00"}
{"phase":"tool_result","name":"read_file","result":"# Boukensha...","ok":true,"session_id":"...","at":"2026-07-26T14:30:23+00:00"}
{"phase":"iteration","n":2,"max":25,"session_id":"...","at":"2026-07-26T14:30:23+00:00"}
{"phase":"prompt","message_count":3,"messages":[...],"tool_count":2,"tools":["read_file","list_directory"],"session_id":"...","at":"2026-07-26T14:30:23+00:00"}
{"phase":"response","text":"Here's a summary of the framework...","usage":{"input_tokens":456,"output_tokens":145},"stop_reason":"end_turn","task":"player","provider":"anthropic","model":"claude-haiku-4-5","input_tokens":456,"output_tokens":145,"cost_usd":0.001095,"session_id":"...","at":"2026-07-26T14:30:24+00:00"}
{"phase":"turn_end","reason":"completed","iterations":2,"session_id":"...","at":"2026-07-26T14:30:24+00:00"}
```

---

## Querying Logs

**Find all tool calls:**
```bash
grep '"phase":"tool_call"' .boukensha/sessions/*.jsonl
```

**Find all errors:**
```bash
grep '"ok":false' .boukensha/sessions/*.jsonl
```

**Total tokens used:**
```bash
grep '"phase":"response"' .boukensha/sessions/*.jsonl | jq '.input_tokens' | awk '{sum+=$1} END {print sum}'
```

**Total cost:**
```bash
grep '"phase":"response"' .boukensha/sessions/*.jsonl | jq '.cost_usd' | awk '{sum+=$1} END {print sum}'
```

**Watch logs in real-time:**
```bash
tail -f .boukensha/sessions/20260726T*.jsonl
```

---

## Running the Example

```bash
cd week1_baseline/python/06_the_logger
python examples/example.py
```

**Expected output:**
```
=== BOUKENSHA Step 6: The Logger ===

Config: #<Boukensha::Config dir=...>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: None

[iteration 1/25]
  tool call → read_file({"path": "README.md"})
  tool result → # Boukensha: An AI Agent Framework...

[iteration 2/25]
  (LLM returns final answer)

=== FINAL RESPONSE ===
Boukensha is a progressive tutorial...

# Log file created at:
# .boukensha/sessions/20260726T143022Z-a1b2c3d4.jsonl
```

---

## Key Design Decisions

### 1. JSONL Format (Not JSON)
- **Why?** One JSON object per line = streamable. Can tail/grep/pipe without loading entire file.
- **Benefit:** Safe to watch logs in real-time.

### 2. Auto-Flush After Each Event
```python
self._log.flush()
```
- **Why?** Ensures each event is written to disk immediately.
- **Benefit:** If the process crashes, you don't lose events. Can `tail -f` to watch.

### 3. Timestamp on Every Event
```python
"at": datetime.now().astimezone().isoformat()
```
- **Why?** Know when each event happened. Includes timezone.
- **Benefit:** Can correlate with system events, other logs, etc.

### 4. Normalized Token Counts Across Providers
```python
cls._first_integer(usage, "input_tokens", "prompt_tokens", "promptTokenCount", "prompt_eval_count")
```
- **Why?** Different providers use different field names.
- **Benefit:** Single field for input_tokens regardless of provider.

### 5. Cost Calculation
- **Why?** Track spending. Know which calls cost the most.
- **Benefit:** Budget visibility. Can warn if costs exceed threshold (future step).

### 6. Optional Raw API Response
```python
def raw(self, data):
    from . import is_debug
    if is_debug():
        self._write({"phase": "raw", "data": data})
```
- **Why?** Full API response can be huge. Only log if debugging.
- **Benefit:** Keeps normal logs lean, but debug data available when needed.

---

## What's NOT Logged

- **API keys** — Never logged (kept in environment variables)
- **Full message content** — Only role and first part of content (to keep logs readable)
- **Binary data** — Everything converted to strings
- **Internal state** — Only externally meaningful events

---

## Debugging With Logs

**Found a bug? Replay the interaction:**
1. Find the session ID from the log filename
2. Extract messages and tool calls from the log
3. Recreate the Context with those messages
4. Inspect what the LLM decided to do

**Example analysis:**
```bash
# What tools were called?
grep tool_call 20260726T143022Z-*.jsonl | jq '.name'

# Which calls failed?
grep '"ok":false' 20260726T143022Z-*.jsonl | jq '.{name, error}'

# How many tokens did each iteration use?
grep '"phase":"response"' 20260726T143022Z-*.jsonl | jq '.{n: .input_tokens, output_tokens}'

# Total cost?
grep '"phase":"response"' 20260726T143022Z-*.jsonl | jq '.cost_usd' | paste -sd+ | bc
```

---

## Comparison: Python vs Ruby

| Aspect | Python | Ruby |
|--------|--------|------|
| File format | JSONL (newline-delimited) | JSONL (newline-delimited) |
| Session ID | `YYYYMMDDTHHMMSSz-hexstring` | Same format |
| Auto-flush | `self._log.flush()` | File opened with `sync: true` |
| Timestamp | ISO 8601 with timezone | ISO 8601 with timezone |
| Token normalization | Multiple field names per provider | Same approach |

Functionally identical.

---

## Data Flow Summary (Complete Through Step 6)

```
Step 0: Config loads YAML
   ↓
Step 1: Context holds messages and tools
   ↓
Step 2: Registry dispatches tools by name
   ↓
Step 3: PromptBuilder + Backend format for the wire
   ├─ Different backends for different providers
   └─ Payload ready for HTTP
   ↓
Step 4: Client sends HTTP request with retries
   ├─ Handles transient failures (network, rate limits)
   ├─ Exponential backoff
   └─ Returns parsed JSON response
   ↓
Step 5: Agent loop orchestrates everything ⭐
   ├─ Iteration counter + limits
   ├─ Tool call handling via Registry
   ├─ Tool result storage in Context
   ├─ Response parsing (normalized format)
   └─ Loop until done or limit reached
   ↓
Step 6: Logger records everything ⭐
   ├─ Structured JSONL events
   ├─ Token tracking (normalized across providers)
   ├─ Cost estimation
   ├─ Real-time streaming (auto-flushed)
   └─ Debug mode for full API responses
   ↓ (in future steps)
Step 7: Simple one-shot run() API
Step 8: Interactive REPL loop
Step 10: MCP tool integration
Step 11: Terminal UI
Step 12: Context management & token limits
```

---