"""
Example scripts to test the tools infrastructure with hello-skill.

Each function demonstrates a specific aspect of the tools system.
Run individual examples or use main() to run all.
"""

import asyncio
import os

from src.agent.state import Task, TaskStatus, TaskType, ToolCallStatus
from src.agent.tool_executor import ToolExecutor, ToolExecutorCallbacks, ToolExecutorOptions
from src.skills import discover_skills, get_skill, build_skill_metadata_section
from src.tools.registry import get_tool_registry, build_tool_descriptions
from src.tools.skill import skill_tool
from src.utils.context import ToolContextManager
from src.utils.logger import get_logger

# Set a dummy API key for testing
os.environ.setdefault("TAVILY_API_KEY", "dummy_key")

logger = get_logger(__name__)


class ExampleCallbacks(ToolExecutorCallbacks):
    """Example callbacks for tool executor."""

    def on_tool_call_update(
        self,
        task_id: str,
        tool_index: int,
        status: str,
        output: str | None = None,
        error: str | None = None,
    ) -> None:
        """Called when a tool status updates."""
        logger.info(f"Tool {tool_index} status: {status}")
        if output:
            logger.info(f"  Output: {output[:100]}...")
        if error:
            logger.error(f"  Error: {error}")


# ======================================================================
## Skills Examples
# ======================================================================


def example_1_discover_skills():
    """Example 1: Discover all available skills."""
    logger.info("=" * 60)
    logger.info("Example 1: Discovering available skills")
    logger.info("=" * 60)

    skills = discover_skills()
    logger.info(f"Found {len(skills)} skill(s):")
    for skill in skills:
        logger.info(f"  - {skill.name}: {skill.description}")
    logger.info("")


def example_2_build_metadata_section():
    """Example 2: Build skill metadata section for system prompt."""
    logger.info("=" * 60)
    logger.info("Example 2: Building skill metadata section")
    logger.info("=" * 60)

    metadata_section = build_skill_metadata_section()
    logger.info(f"{metadata_section}")
    logger.info("")


def example_3_load_full_skill():
    """Example 3: Load full skill with instructions."""
    logger.info("=" * 60)
    logger.info("Example 3: Loading hello-skill with full instructions")
    logger.info("=" * 60)

    hello_skill = get_skill("hello-skill")
    if hello_skill:
        logger.info(f"Name: {hello_skill.name}")
        logger.info(f"Description: {hello_skill.description}")
        logger.info(f"Source: {hello_skill.source}")
        logger.info(f"Path: {hello_skill.path}")
        logger.info("\nInstructions:")
        logger.info("-" * 40)
        logger.info(f"{hello_skill.instructions}")
        logger.info("-" * 40)
    else:
        logger.error("hello-skill not found!")
    logger.info("")


# ======================================================================
## Tool Registry Examples
# ======================================================================


def example_4_get_tool_registry():
    """Example 4: Get tool registry."""
    logger.info("=" * 60)
    logger.info("Example 4: Getting tool registry")
    logger.info("=" * 60)

    tools = get_tool_registry("google/gemini-2.5-flash-lite-preview-09-2025")
    logger.info(f"Found {len(tools)} tool(s):")
    for tool in tools:
        logger.info(f"  - {tool.name}")
        desc_preview = (
            tool.description[:60] + "..."
            if len(tool.description) > 60
            else tool.description
        )
        logger.info(f"    {desc_preview}")
    logger.info("")


def example_5_build_tool_descriptions():
    """Example 5: Build tool descriptions for system prompt."""
    logger.info("=" * 60)
    logger.info("Example 5: Building tool descriptions section")
    logger.info("=" * 60)

    tool_descriptions = build_tool_descriptions("google/gemini-2.5-flash-lite-preview-09-2025")
    logger.info(f"{tool_descriptions}")
    logger.info("")


# ======================================================================
## Tool Invocation Examples
# ======================================================================


def example_6_invoke_skill_tool():
    """Example 6: Invoke skill tool directly (sync)."""
    logger.info("=" * 60)
    logger.info("Example 6: Invoking skill tool with golden-seed")
    logger.info("=" * 60)

    result = skill_tool.invoke({"skill": "golden-seed"})
    logger.info("Result:")
    logger.info("-" * 40)
    logger.info(f"{result}")
    logger.info("-" * 40)
    logger.info("")


async def example_7_skill_with_args():
    """Example 7: Invoke skill tool with arguments (async)."""
    logger.info("=" * 60)
    logger.info("Example 7: Invoking skill tool with arguments")
    logger.info("=" * 60)

    result = await skill_tool.ainvoke({"skill": "golden-seed"})
    logger.info("Result with args:")
    logger.info("-" * 40)
    logger.info(f"{result}")
    logger.info("-" * 40)
    logger.info("")


def example_8_error_handling():
    """Example 8: Error handling for non-existent skill."""
    logger.info("=" * 60)
    logger.info("Example 8: Error handling for non-existent skill")
    logger.info("=" * 60)

    result = skill_tool.invoke({"skill": "non-existent"})
    logger.info(f"Error message: {result}")
    logger.info("")


# ======================================================================
## Tool Executor Integration Examples
# ======================================================================


async def example_9_tool_executor_basic():
    """Example 9: Basic tool executor initialization and execution."""
    logger.info("=" * 60)
    logger.info("Example 9: Tool Executor Basic Usage")
    logger.info("=" * 60)

    # Get tools from registry
    tools = get_tool_registry("google/gemini-2.5-flash-lite-preview-09-2025")
    tool_instances = [t.tool for t in tools]

    # Create context manager
    context_manager = ToolContextManager()

    # Create tool executor options
    options = ToolExecutorOptions(
        tools=tool_instances,
        context_manager=context_manager,
    )

    # Create tool executor
    executor = ToolExecutor(options=options)

    logger.info(f"Tool executor initialized with {len(executor.tools)} tools")

    # Create a simple task
    task = Task(
        id="example-task-1",
        description="Test golden-seed skill",
        status=TaskStatus.PENDING,
        taskType=TaskType.USE_TOOLS,
        toolCalls=[
            ToolCallStatus(
                tool="skill_tool",
                args={"skill": "golden-seed"},
                status=TaskStatus.PENDING,
            )
        ],
        dependsOn=None,
    )

    # Execute tools
    callbacks = ExampleCallbacks()
    success = await executor.execute_tools(
        task=task,
        query_id="example-query-1",
        callbacks=callbacks,
    )

    logger.info(f"Tool execution {'succeeded' if success else 'failed'}")
    logger.info("")


async def example_10_tool_executor_format_tools():
    """Example 10: Format tool descriptions for LLM."""
    logger.info("=" * 60)
    logger.info("Example 10: Formatting Tools for LLM")
    logger.info("=" * 60)

    # Get tools from registry
    tools = get_tool_registry("google/gemini-2.5-flash-lite-preview-09-2025")
    tool_instances = [t.tool for t in tools]

    # Create context manager and executor
    context_manager = ToolContextManager()
    options = ToolExecutorOptions(
        tools=tool_instances,
        context_manager=context_manager,
    )
    executor = ToolExecutor(options=options)

    # Format tools for LLM
    formatted = executor._format_tool_descriptions()

    logger.info("Formatted tool descriptions:")
    logger.info("-" * 40)
    logger.info(f"{formatted}")
    logger.info("-" * 40)
    logger.info("")


async def example_11_tool_executor_with_context():
    """Example 11: Tool executor with context saving."""
    logger.info("=" * 60)
    logger.info("Example 11: Tool Executor with Context")
    logger.info("=" * 60)

    # Get tools from registry
    tools = get_tool_registry("google/gemini-2.5-flash-lite-preview-09-2025")
    tool_instances = [t.tool for t in tools]

    # Create context manager with custom context directory
    context_manager = ToolContextManager(context_dir=".context_test")

    options = ToolExecutorOptions(
        tools=tool_instances,
        context_manager=context_manager,
    )
    executor = ToolExecutor(options=options)

    # Create and execute task
    task = Task(
        id="example-task-2",
        description="Test skill with context",
        status=TaskStatus.PENDING,
        taskType=TaskType.USE_TOOLS,
        toolCalls=[
            ToolCallStatus(
                tool="skill_tool",
                args={"skill": "hello-skill", "args": "with context"},
                status=TaskStatus.PENDING,
            )
        ],
        dependsOn=None,
    )

    callbacks = ExampleCallbacks()
    success = await executor.execute_tools(
        task=task,
        query_id="example-query-2",
        callbacks=callbacks,
    )

    if success:
        # Retrieve context pointers
        pointers = context_manager.get_pointers_for_query("example-query-2")
        logger.info(f"Retrieved {len(pointers)} context pointer(s)")
        for ptr in pointers:
            logger.info(f"  - Tool: {ptr.tool_name}, File: {ptr.filename}")

    logger.info(f"Tool execution {'succeeded' if success else 'failed'}")
    logger.info("")


# ======================================================================
## Run All Examples
# ======================================================================


def run_sync_examples():
    """Run all synchronous examples."""
    sync_examples = [
        example_1_discover_skills,
        example_2_build_metadata_section,
        example_3_load_full_skill,
        example_4_get_tool_registry,
        example_5_build_tool_descriptions,
        example_6_invoke_skill_tool,
        example_8_error_handling,
    ]

    for example in sync_examples:
        example()

    logger.info("=" * 60)
    logger.info("Sync examples completed!")
    logger.info("=" * 60)


async def run_async_examples():
    """Run all asynchronous examples."""
    async_examples = [
        example_7_skill_with_args,
        example_9_tool_executor_basic,
        example_10_tool_executor_format_tools,
        example_11_tool_executor_with_context,
    ]

    for example in async_examples:
        await example()

    logger.info("=" * 60)
    logger.info("Async examples completed!")
    logger.info("=" * 60)


async def run_all_examples():
    """Run all examples in sequence."""
    run_sync_examples()
    await run_async_examples()


if __name__ == "__main__":
    import sys

    # Map example numbers to functions
    sync_map = {
        "1": example_1_discover_skills,
        "2": example_2_build_metadata_section,
        "3": example_3_load_full_skill,
        "4": example_4_get_tool_registry,
        "5": example_5_build_tool_descriptions,
        "6": example_6_invoke_skill_tool,
        "8": example_8_error_handling,
    }

    async_map = {
        "7": example_7_skill_with_args,
        "9": example_9_tool_executor_basic,
        "10": example_10_tool_executor_format_tools,
        "11": example_11_tool_executor_with_context,
    }

    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num in sync_map:
            sync_map[example_num]()
        elif example_num in async_map:
            asyncio.run(async_map[example_num]())
        else:
            logger.info(
                f"Invalid example number. Choose from 1-11: "
                f"1-6,8 (sync), 7,9-11 (async)"
            )
    else:
        # Run all examples
        # asyncio.run(run_all_examples())
        asyncio.run(example_9_tool_executor_basic())
