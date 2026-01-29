"""
Example usage of the ToolExecutor.

This demonstrates how to use the tool executor in your application.
"""

import asyncio
import os
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from unittest.mock import AsyncMock, patch

from src.agent.tool_executor import (
    ToolExecutor,
    ToolExecutorOptions,
    ToolExecutorCallbacks,
)
from src.agent.state import (
    Task,
    ToolCallStatus,
    TaskStatus,
    TaskType,
    Understanding,
)
from src.utils.context import ToolContextManager
from src.utils.logger import get_logger

logger = get_logger("src.example.example_tool_executor")


# ======================================================================
## Example Callbacks
# ======================================================================


class SimpleCallback(ToolExecutorCallbacks):
    """Simple callback for tool executor events."""

    def __init__(self):
        self.updates = []

    def on_tool_call_update(
        self,
        task_id: str,
        tool_index: int,
        status: str,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        self.updates.append({"status": status, "output": output})
        logger.info(f"[Task {task_id}] Tool {tool_index}: {status}")


# ======================================================================
## Examples
# ======================================================================


async def example_1_basic_initialization() -> None:
    """Example 1: Basic initialization and tool formatting"""
    class SearchArgs(BaseModel):
        query: str = Field(description="Search query")

    async def search_func(query: str) -> str:
        return f"Results for: {query}"

    search_tool = StructuredTool(
        name="search",
        description="Search the web",
        func=search_func,
        coroutine=search_func,
        args_schema=SearchArgs,
    )

    options = ToolExecutorOptions(
        tools=[search_tool],
        context_manager=ToolContextManager(),
    )
    executor = ToolExecutor(options)

    # Format and display tool descriptions
    formatted = executor._format_tool_descriptions()
    logger.info(formatted)


async def example_2_mock_tool_execution() -> None:
    """Example 2: Execute tools with mock (no API key needed)"""

    class CalculatorArgs(BaseModel):
        a: int = Field(description="First number")
        b: int = Field(description="Second number")

    async def add_func(a: int, b: int) -> str:
        return str(a + b)

    calc_tool = StructuredTool(
        name="add",
        description="Add two numbers",
        func=add_func,
        coroutine=add_func,
        args_schema=CalculatorArgs,
    )

    options = ToolExecutorOptions(
        tools=[calc_tool],
        context_manager=ToolContextManager(),
    )
    executor = ToolExecutor(options)
    callback = SimpleCallback()

    # Create a task with tool calls
    task = Task(
        id="task-1",
        description="Add 5 and 3",
        status=TaskStatus.PENDING,
        taskType=TaskType.USE_TOOLS,
        toolCalls=[
            ToolCallStatus(
                tool="add",
                args={"a": 5, "b": 3},
                status=TaskStatus.PENDING,
            )
        ],
        dependsOn=None,
    )

    # Execute tools (mock, no API key needed)
    success = await executor.execute_tools(
        task=task,
        query_id="query-1",
        callbacks=callback,
    )
    logger.info(f"Execution succeeded: {success}")
    logger.info(f"Result: {task.toolCalls[0].output}")


async def example_3_tool_selection_mock() -> None:
    """Example 3: Tool selection (requires API key)"""

    class WeatherArgs(BaseModel):
        city: str = Field(description="City name")

    async def get_weather(city: str) -> str:
        return f"Weather in {city}: 22°C, Sunny"

    weather_tool = StructuredTool(
        name="get_weather",
        description="Get weather for a city",
        func=get_weather,
        coroutine=get_weather,
        args_schema=WeatherArgs,
    )

    # Mock LLM response
    mock_response = {
        "tool_calls": [
            {
                "name": "get_weather",
                "args": {"city": "Tokyo"},
            }
        ]
    }

    options = ToolExecutorOptions(
        tools=[weather_tool],
        context_manager=ToolContextManager(),
    )
    executor = ToolExecutor(options)

    with patch("src.agent.tool_executor.llm_call", new=AsyncMock(return_value=mock_response)):
        task = Task(
            id="task-2",
            description="What's the weather in Tokyo?",
            status=TaskStatus.PENDING,
            taskType=TaskType.USE_TOOLS,
            toolCalls=None,
            dependsOn=None,
        )
        understanding = Understanding(
            intent="get_weather",
            entities={"periods": []},
        )

        tool_calls = await executor.select_tools(task, understanding)
        logger.info(f"Selected {len(tool_calls)} tool(s)")
        logger.info(f"Tool: {tool_calls[0].tool}, Args: {tool_calls[0].args}")


async def example_4_real_api_execution() -> None:
    """Example 4: Execute tools with real API (requires OPENROUTER_API_KEY in .env)"""

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("Skipping: OPENAI_API_KEY not found in environment")
        return

    class SearchArgs(BaseModel):
        query: str = Field(description="Search query")

    async def search_func(query: str) -> str:
        return f"Search results for: {query}"

    search_tool = StructuredTool(
        name="search",
        description="Search the web",
        func=search_func,
        coroutine=search_func,
        args_schema=SearchArgs,
    )

    options = ToolExecutorOptions(
        tools=[search_tool],
        context_manager=ToolContextManager(),
    )
    executor = ToolExecutor(options)
    callback = SimpleCallback()

    task = Task(
        id="task-3",
        description="Search for Python tutorials",
        status=TaskStatus.PENDING,
        taskType=TaskType.USE_TOOLS,
        toolCalls=[
            ToolCallStatus(
                tool="search",
                args={"query": "Python tutorials"},
                status=TaskStatus.PENDING,
            )
        ],
        dependsOn=None,
    )

    success = await executor.execute_tools(
        task=task,
        query_id="query-2",
        callbacks=callback,
    )
    logger.info(f"Execution with real API succeeded: {success}")


async def example_5_cancellation_handling() -> None:
    """Example 5: Handle tool execution cancellation"""

    class SlowTaskArgs(BaseModel):
        duration: int = Field(description="Duration in seconds")

    async def slow_task(duration: int) -> str:
        await asyncio.sleep(duration)
        return f"Completed after {duration}s"

    slow_tool = StructuredTool(
        name="slow_task",
        description="A task that takes time",
        func=slow_task,
        coroutine=slow_task,
        args_schema=SlowTaskArgs,
    )

    options = ToolExecutorOptions(
        tools=[slow_tool],
        context_manager=ToolContextManager(),
    )
    executor = ToolExecutor(options)
    callback = SimpleCallback()

    task = Task(
        id="task-4",
        description="Run slow task",
        status=TaskStatus.PENDING,
        taskType=TaskType.USE_TOOLS,
        toolCalls=[
            ToolCallStatus(
                tool="slow_task",
                args={"duration": 5},
                status=TaskStatus.PENDING,
            )
        ],
        dependsOn=None,
    )

    # Create cancellation token
    cancel_event = asyncio.Event()

    async def run_and_cancel():
        # Cancel after 1 second
        await asyncio.sleep(1)
        cancel_event.set()
        logger.info("Cancellation requested!")

    # Run execution and cancellation in parallel
    try:
        await asyncio.gather(
            executor.execute_tools(
                task=task,
                query_id="query-3",
                callbacks=callback,
                cancellation_token=cancel_event,
            ),
            run_and_cancel(),
        )
    except asyncio.CancelledError:
        logger.info("Tool execution was cancelled successfully")


async def main() -> None:
    """Run all examples."""
    logger.info("=== Example 1: Basic Initialization ===")
    await example_1_basic_initialization()

    logger.info("=== Example 2: Mock Tool Execution ===")
    await example_2_mock_tool_execution()

    logger.info("=== Example 3: Tool Selection (Mock) ===")
    await example_3_tool_selection_mock()

    logger.info("=== Example 4: Real API Execution ===")
    await example_4_real_api_execution()

    logger.info("=== Example 5: Cancellation Handling ===")
    await example_5_cancellation_handling()


if __name__ == "__main__":
    asyncio.run(main())
