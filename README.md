# Marketing Agent Orchestrator

A general-purpose AI agent orchestrator inspired by [dexter](https://github.com/virattt/dexter), implementing a multi-phase workflow with tool execution capabilities.

## Architecture Overview

```
src/
├── agent/
│   ├── state.py           # Pydantic models: Phase, Task, ToolCall, Understanding
│   ├── tool_executor.py   # Tool selection and execution
│   ├── prompts.py         # System prompts for each phase
│   └── types.py           # Agent configuration types
├── tools/
│   ├── registry.py        # Tool discovery and registration
│   ├── types.py           # ToolResult model and utilities
│   ├── skill.py           # LangChain tool for invoking skills
│   ├── search/            # Web search tools
│   └── description/       # Tool descriptions for prompts
├── skills/
│   ├── registry.py        # Skill discovery with caching
│   ├── loader.py          # Parse SKILL.md files
│   └── types.py           # SkillSource, SkillMetadata, Skill
├── model/
│   └── llm.py             # LLM call wrapper
├── utils/
│   ├── logger.py          # Loguru-based logging
│   ├── context.py         # Tool result persistence (disk)
│   └── message_history.py # Conversation history (memory)
└── example/
    └── example_*.py       # Usage examples
```

## Project Status

### Completed ✅

| Component | Description | File |
|-----------|-------------|------|
| **Skills System** | SKILL.md discovery with multi-source scanning | `src/skills/registry.py` |
| **Tools Registry** | LangChain tool registration with env-aware loading | `src/tools/registry.py` |
| **Tool Executor** | Tool selection/execution with cancellation support | `src/agent/tool_executor.py` |
| **Context Manager** | Persistent storage for tool results | `src/utils/context.py` |
| **Message History** | In-memory conversation tracking | `src/utils/message_history.py` |
| **Logger** | Loguru-based logging with rotation | `src/utils/logger.py` |
| **State Models** | Pydantic models for agent state | `src/agent/state.py` |

### In Progress 🚧

| Component | Description | Reference |
|-----------|-------------|-----------|
| **Prompts** | System prompts for each phase | `src/agent/prompts.py` |
| **Schemas** | Structured output schemas | `src/agent/schemas.py` |

### To Do 📋

## Next Steps

Based on the [dexter virat.3-model-approach](https://github.com/virattt/dexter/tree/virat.3-model-approach) architecture, here are the remaining components:

### 1. Complete Prompts Module (`src/agent/prompts.py`)

Reference: [`dexter/src/agent/prompts.ts`](https://raw.githubusercontent.com/virattt/dexter/virat.3-model-approach/src/agent/prompts.ts)

```python
# Needed functions:
- get_current_date() -> str
- get_understand_system_prompt() -> str
- get_plan_system_prompt() -> str
- get_tool_selection_system_prompt(tool_descriptions: str) -> str
- get_execute_system_prompt() -> str
- get_reflect_system_prompt() -> str
- get_final_answer_system_prompt() -> str
- build_understand_user_prompt(query: str, conversation_context: str) -> str
- build_plan_user_prompt(...) -> str
- build_execute_user_prompt(...) -> str
- build_reflect_user_prompt(...) -> str
- build_final_answer_user_prompt(...) -> str
```

### 2. Implement Phase Classes (`src/agent/phases/`)

Create a phases directory with individual phase implementations:

```
src/agent/phases/
├── __init__.py
├── understand.py    # Extract intent and entities
├── plan.py          # Generate task list with dependencies
├── execute.py       # Run tasks (use_tools or reason)
├── reflect.py       # Evaluate completeness, iterate if needed
└── answer.py        # Synthesize final response
```

#### Phase 1: Understand
**Input:** `query`, `conversation_history`
**Output:** `Understanding` (intent, entities)
**Model:** Standard LLM (e.g., gpt-4o-mini)

```python
class UnderstandPhase:
    async def run(self, input: UnderstandInput) -> Understanding:
        # 1. Select relevant messages from history
        # 2. Build prompt with query + context
        # 3. Call LLM with structured output
        # 4. Return Understanding {intent, entities}
```

#### Phase 2: Plan
**Input:** `query`, `understanding`, `prior_plans`, `guidance`
**Output:** `Plan` (summary, tasks with dependencies)
**Model:** Standard LLM

```python
class PlanPhase:
    async def run(self, input: PlanInput) -> Plan:
        # Create 2-5 tasks:
        # - taskType: "use_tools" | "reason"
        # - dependsOn: list of task IDs
        # Return Plan with tasks
```

#### Phase 3: Execute
**Input:** `query`, `plan`, `understanding`
**Output:** `Map[taskId, TaskResult]`
**Model:** Fast model for tools (gemini-flash), Standard for reasoning

```python
class ExecutePhase:
    async def run(self, input: ExecuteInput) -> dict[str, TaskResult]:
        # For each task in plan (respecting dependencies):
        # - if use_tools: select tools, execute via ToolExecutor
        # - if reason: call LLM with gathered context
        # Return task results
```

#### Phase 4: Reflect
**Input:** `query`, `understanding`, `completed_plans`, `task_results`
**Output:** `ReflectionResult` (isComplete, missingInfo, suggestedNextSteps)
**Model:** Standard LLM

```python
class ReflectPhase:
    async def run(self, input: ReflectInput) -> ReflectionResult:
        # Evaluate if we have enough info to answer
        # If not, provide guidance for next iteration
        # Max 2-3 iterations before answering anyway
```

#### Phase 5: Answer
**Input:** `query`, `completed_plans`, `task_results`
**Output:** Final answer string
**Model:** Smart model (gpt-4o, claude-opus)

```python
class AnswerPhase:
    async def run(self, input: AnswerInput) -> str:
        # Synthesize all task results into final answer
        # Include sources section
        # Return formatted response
```

### 3. Create Schemas (`src/agent/schemas.py`)

Pydantic models for structured LLM outputs:

```python
class EntitySchema(BaseModel):
    type: Literal["ticker", "date", "metric", "company", "period", "other"]
    value: str

class UnderstandingSchema(BaseModel):
    intent: str
    entities: list[EntitySchema]

class PlanTaskSchema(BaseModel):
    id: str
    description: str
    taskType: Literal["use_tools", "reason"]
    dependsOn: list[str] = []

class PlanSchema(BaseModel):
    summary: str
    tasks: list[PlanTaskSchema]

class ReflectionSchema(BaseModel):
    isComplete: bool
    reasoning: str
    missingInfo: list[str] = []
    suggestedNextSteps: str = ""
```

### 4. Build Orchestrator (`src/agent/orchestrator.py`)

The main agent class coordinating all phases:

```python
class Agent:
    """Multi-phase agent orchestrator."""

    def __init__(
        self,
        tools: list[StructuredTool],
        context_manager: ToolContextManager,
        models: AgentModels,  # standard, smart, fast
    ):
        self.understand = UnderstandPhase(model=models.standard)
        self.plan = PlanPhase(model=models.standard)
        self.execute = ExecutePhase(
            tool_executor=ToolExecutor(...),
            fast_model=models.fast,
            standard_model=models.standard,
        )
        self.reflect = ReflectPhase(model=models.standard)
        self.answer = AnswerPhase(model=models.smart)

    async def run(self, query: str) -> str:
        # 1. Understand
        understanding = await self.understand.run(UnderstandInput(query=query))

        # 2-4. Plan -> Execute -> Reflect (loop until complete)
        for iteration in range(MAX_ITERATIONS):
            plan = await self.plan.run(...)
            results = await self.execute.run(...)
            reflection = await self.reflect.run(...)

            if reflection.isComplete:
                break

        # 5. Answer
        return await self.answer.run(...)
```

### 5. Configuration Types (`src/agent/types.py`)

```python
class AgentModels(BaseModel):
    standard: str = "gpt-4o-mini"      # For planning, understanding
    smart: str = "gpt-4o"              # For final answer
    fast: str = "gemini-2.5-flash"     # For tool selection

class AgentCallbacks(Protocol):
    def on_phase_start(self, phase: Phase): ...
    def on_phase_complete(self, phase: Phase, output: Any): ...
    def on_task_update(self, task_id: str, status: str): ...
```

## 3-Model Approach

Following dexter's design, use different models for different purposes:

| Phase | Model | Rationale |
|-------|-------|-----------|
| Understand | Standard | Good enough for extraction |
| Plan | Standard | Planning doesn't need smartest model |
| Execute (tools) | Fast | Tool selection is simple, speed matters |
| Execute (reason) | Standard | Analysis without need for top-tier |
| Reflect | Standard | Decision making is straightforward |
| Answer | Smart | Final output quality matters most |

## Quick Start

```python
from src.agent import Agent, AgentModels, AgentCallbacks
from src.tools import get_tools
from src.utils.context import ToolContextManager

# Setup
tools = get_tools(model="gpt-4o")
context_manager = ToolContextManager()
models = AgentModels(
    standard="gpt-4o-mini",
    smart="gpt-4o",
    fast="gemini-2.5-flash",
)

agent = Agent(
    tools=tools,
    context_manager=context_manager,
    models=models,
)

# Run
response = await agent.run("What's the latest news about AAPL?")
print(response)
```

## Development Progress

- [x] Skills system (registry, loader, types)
- [x] Tools registry (LangChain integration)
- [x] Tool executor (selection, execution, cancellation)
- [x] Context manager (disk persistence)
- [x] Message history (in-memory)
- [x] Logger (loguru)
- [x] State models (Pydantic)
- [ ] Prompts (all phase prompts)
- [ ] Schemas (structured outputs)
- [ ] Phase implementations (understand, plan, execute, reflect, answer)
- [ ] Orchestrator (main agent class)

## References

- [dexter - Original TypeScript Implementation](https://github.com/virattt/dexter)
- [virat.3-model-approach Branch](https://github.com/virattt/dexter/tree/virat.3-model-approach)
