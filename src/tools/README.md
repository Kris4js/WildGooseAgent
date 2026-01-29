# Tools System

A modular tool registry and execution framework for AI agents using LangChain. Tools are discovered, registered, and made available to LLMs with rich descriptions for proper tool selection.

## Architecture

```
src/tools/
├── __init__.py          # Public API exports
├── registry.py          # Tool discovery and registration
├── types.py             # Pydantic models (ToolResult, utilities)
├── skill.py             # LangChain tool for invoking skills
├── search/              # Web search tools
│   ├── __init__.py
│   └── tavily.py        # Tavily search integration
└── description/         # Tool descriptions for system prompts
    ├── __init__.py
    └── web_search.py    # Web search tool description
```

## Core Components

### 1. Registry (`registry.py`)

Central hub for tool registration and discovery.

| Class/Function | Purpose |
|----------------|---------|
| `RegisteredTool` | Pydantic model: `name`, `tool`, `description` |
| `get_tool_registry(model)` | Get all registered tools with descriptions |
| `get_tools(model)` | Get tool instances for LLM binding |
| `build_tool_descriptions(model)` | Format descriptions for system prompt |

**Tool Registration Pattern:**
```python
def get_tool_registry(model: str) -> list[RegisteredTool]:
    tools: list[RegisteredTool] = []

    # Conditionally add tools based on env config
    if os.getenv("TAVILY_API_KEY"):
        tools.append(RegisteredTool(
            name="web_search",
            tool=tavily_search,
            description=WEB_SEARCH_DESCRIPTION,
        ))

    if len(discover_skills()) > 0:
        tools.append(RegisteredTool(
            name="skill",
            tool=skill_tool,
            description=SKILL_TOOL_DESCRIPTION,
        ))

    return tools
```

### 2. Types (`types.py`)

Common data structures for tool results.

```python
class ToolResult(BaseModel):
    data: Any                    # Tool output data
    source_urls: list[str] | None  # Optional source citations
```

**Utility functions:**
- `format_tool_result(data, source_urls)` - Serialize to JSON
- `parse_search_results(result)` - Extract URLs from Exa/Tavily formats

### 3. Tool Definitions

Tools are defined as async functions using LangChain's `@tool` decorator:

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    query: str = Field(..., description="Search query")

@tool(args_schema=ToolInput)
async def my_tool(query: str) -> str:
    """Tool description for LLM."""
    result = await some_async_operation(query)
    return format_tool_result(data=result)
```

### 4. Tool Descriptions

Rich descriptions guide LLM tool selection:

```python
TOOL_DESCRIPTION = """
Tool one-line summary.

## When to Use
- Use case 1
- Use case 2

## When NOT to Use
- Don't use for X
- Don't use for Y

## Usage Notes
- Specific guidance
- Parameter requirements
""".strip()
```

## Available Tools

| Tool | Description | Provider |
|------|-------------|----------|
| `web_search` | Search the web for current information | Tavily |
| `skill` | Execute specialized skill workflows | Built-in |

## Usage Example

```python
from src.tools import get_tool_registry, get_tools, build_tool_descriptions

# Get tools with metadata
registry = get_tool_registry("gpt-4o")
for tool in registry:
    print(f"{tool.name}: {tool.description[:50]}...")

# Get tool instances for LangChain
tools = get_tools("gpt-4o")
# Use with: llm.bind_tools(tools)

# Build for system prompt
descriptions = build_tool_descriptions("gpt-4o")
```

## Adding a New Tool

1. **Create tool file** (e.g., `src/tools/my_tool.py`):

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.tools.types import format_tool_result

class MyToolInput(BaseModel):
    arg: str = Field(..., description="Argument description")

@tool(args_schema=MyToolInput)
async def my_tool(arg: str) -> str:
    """One-line tool description."""
    result = await do_something(arg)
    return format_tool_result(data=result)
```

2. **Add description** (e.g., `src/tools/description/my_tool.py`):

```python
MY_TOOL_DESCRIPTION = """
Tool summary.

## When to Use
- Use case 1

## When NOT to Use
- Avoid case 1

## Usage Notes
- Specific guidance
""".strip()
```

3. **Register in `registry.py`:**

```python
from src.tools.my_tool import my_tool
from src.tools.description import MY_TOOL_DESCRIPTION

# In get_tool_registry():
tools.append(RegisteredTool(
    name="my_tool",
    tool=my_tool,
    description=MY_TOOL_DESCRIPTION,
))
```

## Integration with Tool Executor

The tools integrate with `ToolExecutor` from `src/agent/tool_executor.py`:

```python
from src.agent.tool_executor import ToolExecutor, ToolExecutorOptions
from src.tools import get_tools
from src.utils.context import ToolContextManager

tools = get_tools(model="gpt-4o")
context_manager = ToolContextManager()

options = ToolExecutorOptions(
    tools=tools,
    context_manager=context_manager,
)

executor = ToolExecutor(options=options)
```

## Design Principles

1. **Environment-aware** - Tools conditionally registered based on API keys
2. **Rich descriptions** - Guides LLM on when/not to use each tool
3. **Async-first** - All tools are async for non-blocking execution
4. **Structured output** - `ToolResult` format with source URLs
5. **Pydantic validation** - Input schemas enforce type safety
6. **LangChain compatible** - Works with `bind_tools()` for function calling

## Dependencies

- `langchain-core` - Tool abstractions
- `langchain-tavily` - Tavily search client
- `pydantic` - Schema validation
- `python-dotenv` - Environment configuration
