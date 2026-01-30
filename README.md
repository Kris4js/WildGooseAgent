# Marketing Agent Orchestrator

A general-purpose AI agent orchestrator inspired by [dexter](https://github.com/virattt/dexter), implementing a multi-phase workflow with tool execution capabilities.

## Architecture Overview

```
src/
├── agent/
│   ├── state.py           # Pydantic/dataclass models: Phase, Task, ToolCall, Understanding
│   ├── orchestrator.py    # Main Agent class coordinating all phases
│   ├── task_executor.py   # Task execution with dependency management
│   ├── tool_executor.py   # Tool selection and execution
│   ├── prompts.py         # System prompts for each phase
│   └── phases/
│       ├── __init__.py    # Phase exports
│       ├── base.py        # Base Phase class and EntitySchema
│       ├── understand.py  # Phase 1: Extract intent and entities
│       ├── plan.py        # Phase 2: Generate task list with dependencies
│       ├── execute.py     # Phase 3: Execute tasks (use_tools or reason)
│       ├── reflect.py     # Phase 4: Evaluate completeness
│       └── answer.py      # Phase 5: Synthesize final response
├── tools/
│   ├── registry.py        # Tool discovery and registration
│   ├── types.py           # ToolResult model and utilities
│   ├── skill.py           # LangChain tool for invoking skills
│   ├── search/            # Web search tools (tavily)
│   └── description/       # Tool descriptions for prompts
├── skills/
│   ├── registry.py        # Skill discovery with multi-source scanning
│   ├── loader.py          # Parse SKILL.md files
│   └── types.py           # SkillSource, SkillMetadata, Skill
├── model/
│   └── llm.py             # LLM call wrappers (standard, structured, streaming)
├── utils/
│   ├── __init__.py        # Utility exports
│   ├── logger.py          # Loguru-based logging with rotation
│   ├── context.py         # Tool result persistence (disk)
│   └── message_history.py # Conversation history (memory)
└── config.ini             # Agent configuration
```

## Project Status

### Completed ✅

| Component | Description | File |
|-----------|-------------|------|
| **Skills System** | SKILL.md discovery with multi-source scanning | `src/skills/registry.py` |
| **Tools Registry** | LangChain tool registration with env-aware loading | `src/tools/registry.py` |
| **Tool Executor** | Tool selection/execution with cancellation support | `src/agent/tool_executor.py` |
| **Task Executor** | Dependency-aware parallel task execution | `src/agent/task_executor.py` |
| **Context Manager** | Persistent storage for tool results | `src/utils/context.py` |
| **Message History** | In-memory conversation tracking | `src/utils/message_history.py` |
| **Logger** | Loguru-based logging with rotation | `src/utils/logger.py` |
| **State Models** | Pydantic/dataclass models for agent state | `src/agent/state.py` |
| **Prompts** | System/user prompts for all phases | `src/agent/prompts.py` |
| **Schemas** | Structured output schemas for LLM validation | `src/agent/phases/*.py` |
| **Phase: Understand** | Extract intent and entities from query | `src/agent/phases/understand.py` |
| **Phase: Plan** | Generate task list with dependencies | `src/agent/phases/plan.py` |
| **Phase: Execute** | Execute tasks (use_tools or reason) | `src/agent/phases/execute.py` |
| **Phase: Reflect** | Evaluate completeness, suggest next steps | `src/agent/phases/reflect.py` |
| **Phase: Answer** | Synthesize final response with streaming | `src/agent/phases/answer.py` |
| **Orchestrator** | Main Agent class coordinating all phases | `src/agent/orchestrator.py` |

## Implementation Details

### Phase Architecture

The agent implements a 5-phase workflow with iterative reflection:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent.run(query)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Understand                                            │
│  - Extract intent and entities from query                       │
│  - Model: Standard (e.g., gemini-2.5-flash-lite)               │
│  - Output: Understanding {intent, entities}                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Iterative Loop (max N iterations)                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Phase 2: Plan                                             │ │
│  │ - Generate 2-5 tasks with dependencies                    │ │
│  │ - Model: Standard                                         │ │
│  │ - Output: Plan {summary, tasks}                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Phase 3: Execute                                          │ │
│  │ - Run tasks in parallel (respect dependencies)            │ │
│  │ - taskType: "use_tools" or "reason"                       │ │
│  │ - Model: Standard                                         │ │
│  │ - Output: Map[taskId, TaskResult]                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Phase 4: Reflect                                          │ │
│  │ - Evaluate if sufficient data gathered                    │ │
│  │ - If not, provide guidance for next iteration             │ │
│  │ - Model: Standard                                         │ │
│  │ - Output: ReflectionResult {isComplete, reasoning}        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                    ┌─────────┴─────────┐                       │
│                    │                   │                        │
│              isComplete=True     isComplete=False              │
│                    │                   │                        │
│                    ▼                   ▼                        │
│              break loop        continue to next iteration      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 5: Answer                                                │
│  - Synthesize all task results into final answer               │
│  - Stream response in real-time                                 │
│  - Model: Smart (e.g., gemini-2.5-pro)                         │
│  - Output: AsyncGenerator[str] (streaming)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Schema System

The agent uses a dual-schema system:

1. **Pydantic Schemas** - For LLM structured output validation:
   - `EntitySchema` - Entity type and value
   - `UnderstandingSchema` - Intent and entities
   - `TaskSchema` - Individual task definition
   - `PlanSchema` - Complete plan with tasks
   - `ReflectionSchema` - Reflection decision and reasoning

2. **Dataclass Schemas** - For internal state management:
   - `UnderstandInput`, `PlanInput`, `ExecuteInput`, `ReflectInput`, `AnswerInput`
   - `Understanding`, `Plan`, `TaskResult`, `ReflectionResult`

### Task Execution

The `TaskExecutor` manages parallel task execution with dependency awareness:

```python
# Tasks with dependencies
Task(id="1", description="Search for AAPL news", dependsOn=[])
Task(id="2", description="Search for TSLA news", dependsOn=[])
Task(id="3", description="Compare stock prices", dependsOn=["1", "2"])

# Execution order:
# Iteration 1: Tasks 1 and 2 run in parallel
# Iteration 2: Task 3 runs after 1 and 2 complete
```

## Configuration

The agent uses `src/agent/config.ini` for model configuration:

```ini
[understand]
model = google/gemini-2.5-flash-lite-preview-09-2025

[plan]
model = google/gemini-2.5-flash-lite-preview-09-2025

[execute]
model = google/gemini-2.5-flash-lite-preview-09-2025

[reflect]
model = google/gemini-2.5-flash-lite-preview-09-2025

[answer]
model = google/gemini-3-flash-preview
```

## Quick Start

```python
from src.agent.orchestrator import Agent, AgentOptions, ModelConfig, AgentCallbacks
from src.tools import get_tools
from src.utils.context import ToolContextManager
from typing import AsyncGenerator

# Define model configuration
model_config = ModelConfig(
    small="google/gemini-2.5-flash-lite-preview-09-2025",  # For tool selection
    large="google/gemini-3-flash-preview",        # For planning/reasoning
)

# Optional: Define callbacks
class Callbacks(AgentCallbacks):
    def onPhaseStart(self, phase: str):
        print(f"Starting phase: {phase}")

    def onAnswerStream(self, stream: AsyncGenerator[str, None]):
        async def print_stream():
            async for chunk in stream:
                print(chunk, end="", flush=True)
            print()
        import asyncio
        asyncio.create_task(print_stream())

# Create agent
agent = Agent(
    options=AgentOptions(
        model=model_config,
        callbacks=Callbacks(),
        maxIterations=3,
    )
)

# Run agent
query = "What's the latest news about AAPL stock?"
response = await agent.run(query)
```

## 3-Model Approach

Following dexter's design, the architecture supports different models for different purposes:

| Phase | Model Config | Rationale |
|-------|--------------|-----------|
| Understand | `small` | Simple extraction task |
| Plan | `large` | Planning benefits from reasoning capability |
| Execute (tools) | `small` | Tool selection is straightforward |
| Execute (reason) | `large` | Analysis without needing top-tier |
| Reflect | `large` | Decision making benefits from reasoning |
| Answer | `large` | Final output quality matters most |

**Recommended model configurations:**

- **Cost-optimized**: `small=google/gemini-2.5-flash-lite-preview-09-2025`, `large=google/gemini-3-flash-preview`
- **Quality-focused**: `small=google/gemini-2.5-flash-lite-preview-09-2025`, `large=google/gemini-3-pro`
- **Mixed-provider**: `small=google/gemini-2.5-flash-lite-preview-09-2025`, `large=gpt-4o`

## API Reference

### Agent Class

```python
class Agent:
    def __init__(self, options: AgentOptions):
        """Initialize agent with configuration.

        Args:
            options: AgentOptions containing model config, callbacks, and max iterations
        """

    async def run(
        self,
        query: str,
        messageHistory: Optional[MessageHistory] = None
    ) -> str:
        """Run agent with iterative reflection.

        Args:
            query: User's query
            messageHistory: Optional conversation history

        Returns:
            Empty string (actual response delivered via onAnswerStream callback)
        """
```

### AgentOptions

```python
class ModelConfig(BaseModel):
    small: str  # Model for simple tasks
    large: str  # Model for complex tasks

class AgentOptions(BaseModel):
    model: ModelConfig                    # Model configuration
    callbacks: Optional[Any] = None       # AgentCallbacks protocol
    maxIterations: Optional[int] = 5      # Max reflection iterations
```

### AgentCallbacks

```python
class AgentCallbacks(Protocol):
    # Phase lifecycle
    onPhaseStart: Optional[Callable[[Phase], None]]
    onPhaseComplete: Optional[Callable[[Phase], None]]

    # Understanding phase
    onUnderstandingComplete: Optional[Callable[[Understanding], None]]

    # Planning phase
    onPlanCreated: Optional[Callable[[Plan, int], None]]

    # Reflection phase
    onReflectionComplete: Optional[Callable[[ReflectionResult, int], None]]
    onIterationStart: Optional[Callable[[int], None]]

    # Answer phase
    onAnswerStart: Optional[Callable[[], None]]
    onAnswerStream: Optional[Callable[[AsyncGenerator[str, None]], None]]
```

## Development Progress

- [x] Skills system (registry, loader, types)
- [x] Tools registry (LangChain integration)
- [x] Tool executor (selection, execution, cancellation)
- [x] Task executor (dependency-aware parallel execution)
- [x] Context manager (disk persistence)
- [x] Message history (in-memory)
- [x] Logger (loguru)
- [x] State models (Pydantic/dataclass)
- [x] Prompts (all phase prompts)
- [x] Schemas (embedded in phase files)
- [x] Phase implementations (understand, plan, execute, reflect, answer)
- [x] Orchestrator (main agent class)

## References

- [dexter - Original TypeScript Implementation](https://github.com/virattt/dexter)
- [virat.3-model-approach Branch](https://github.com/virattt/dexter/tree/virat.3-model-approach)

## License

MIT
