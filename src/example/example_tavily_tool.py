"""
Example usage and test for the Tavily search tool.

Run this file to verify your Tavily integration works correctly:
    python -m src.example.example_tavily_tool
"""

import asyncio
import os

from src.tools.search.tavily import tavily_search
from src.agent.tool_executor import (
    ToolExecutor,
    ToolExecutorOptions,
    ToolExecutorCallbacks,
)
from src.agent.state import Task, Understanding, TaskType, TaskStatus
from src.utils.context import ToolContextManager
from src.utils.logger import get_logger
from src.model.llm import _get_chat_llm
from langchain.agents import create_agent
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)


logger = get_logger("src.example.example_tavily_tool")


async def example_1_direct_tool_call() -> None:
    """Example 1: Direct tool invocation with a simple query."""
    logger.info("=== Example 1: Direct Tool Call ===")

    result = await tavily_search.ainvoke({
        "query": "Latest developments in artificial intelligence 2025"
    })
    logger.info(f"Result:\n{result}\n")


async def example_2_search_with_max_results() -> None:
    """Example 2: Search with custom max_results parameter."""
    logger.info("=== Example 2: Custom Max Results ===")

    result = await tavily_search.ainvoke({
        "query": "Python async programming best practices"
    })
    logger.info(f"Result:\n{result}\n")


async def example_3_tool_metadata() -> None:
    """Example 3: Display tool metadata (name, description, args schema)."""
    logger.info("=== Example 3: Tool Metadata ===")

    logger.info(f"Tool Name: {tavily_search.name}")
    logger.info(f"Tool Description: {tavily_search.description}")
    logger.info(
        f"Args Schema: {tavily_search.args_schema.model_json_schema()}\n"
    )


async def example_4_full_executor_workflow() -> None:
    """Example 4: Full ToolExecutor workflow - select_tools and execute_tools."""
    logger.info("=== Example 4: Full ToolExecutor Workflow ===")

    # Step 1: Create ToolExecutor with options
    options = ToolExecutorOptions(
        tools=[tavily_search],
        context_manager=ToolContextManager(),
    )
    executor = ToolExecutor(options)

    # Step 2: Show formatted tool description (for LLM consumption)
    formatted = executor.format_tool(tavily_search)
    logger.info(f"Tool Description for LLM:\n{formatted}\n")

    # Step 3: Create Task and Understanding for select_tools
    task = Task(
        id="task-001",
        description="Search for latest trends in Github trending, which url is 'https://github.com/trending'",
        status=TaskStatus.PENDING,
        taskType=TaskType.USE_TOOLS,
        toolCalls=None,
        dependsOn=None,
    )

    understanding = Understanding(
        intent="Search for current information about AI developments",
        entities={
            "periods": ["2026"]
        },  # Used by build_tool_selection_prompt
    )

    logger.info(f"Task: {task.description}")
    logger.info(f"Understanding: {understanding.intent}\n")

    # Step 4: Use select_tools to get tool calls from LLM
    logger.info("Step 1: Selecting tools via LLM...")
    tool_calls = await executor.select_tools(
        task=task,
        understanding=understanding,
    )

    if not tool_calls:
        logger.info("No tools selected by LLM")
        return

    logger.info(f"LLM selected {len(tool_calls)} tool call(s):")
    for tc in tool_calls:
        logger.info(f"  - {tc.tool}: {tc.args}")

    # Step 5: Assign tool_calls to task for execution
    task.toolCalls = tool_calls

    # Step 6: Create callback implementation
    class SimpleCallbacks(ToolExecutorCallbacks):
        def __init__(self) -> None:
            self.updates: list[dict] = []

        def on_tool_call_update(
            self,
            task_id: str,
            tool_index: int,
            status: str,
            output: str | None = None,
            error: str | None = None,
        ) -> None:
            update = {
                "task_id": task_id,
                "index": tool_index,
                "status": status,
            }
            if output:
                update["output"] = (
                    output[:100] + "..." if len(output) > 100 else output
                )
            if error:
                update["error"] = error
            self.updates.append(update)
            logger.info(f"  [Tool {tool_index}] Status: {status}")

    callbacks = SimpleCallbacks()

    # Step 7: Execute tools using execute_tools
    logger.info("\nStep 2: Executing tools...")
    success = await executor.execute_tools(
        task=task,
        query_id="query-001",
        callbacks=callbacks,
    )

    # Step 8: Show results
    logger.info(
        f"\nExecution {'succeeded' if success else 'completed with errors'}"
    )
    logger.info("\n=== Tool Execution Results ===")

    for i, tool_call in enumerate(task.toolCalls):
        logger.info(f"\nTool {i}: {tool_call.tool}")
        logger.info(f"Args: {tool_call.args}")
        logger.info(f"Status: {tool_call.status.value}")
        if tool_call.output:
            preview = (
                tool_call.output[:200] + "..."
                if len(tool_call.output) > 200
                else tool_call.output
            )
            logger.info(f"Output preview: {preview}")
        if tool_call.error:
            logger.info(f"Error: {tool_call.error}")

    logger.info(f"\nAll callback updates: {callbacks.updates}\n")


async def example_5_multiple_concurrent_searches() -> None:
    """Example 5: Execute multiple searches concurrently."""
    logger.info("=== Example 5: Concurrent Searches ===")

    queries = [
        "LangChain tutorial",
        "FastAPI async patterns",
        "Python type hints guide",
    ]

    results = await asyncio.gather(*[
        tavily_search.ainvoke({"query": q}) for q in queries
    ])

    for query, result in zip(queries, results):
        logger.info(f"Query: {query}")
        logger.info(f"Result preview: {result[:200]}...\n")


async def example_6_agent_with_tool() -> None:
    """Example 6: Use LangChain create_agent for automatic tool calling."""
    logger.info(
        "=== Example 6: LLM Agent with Auto Tool Calling (Agent管理) ==="
    )

    # Step 1: Create an agent using the new LangChain API
    # The agent will automatically call tools in a loop
    agent = create_agent(
        model=_get_chat_llm(),
        tools=[tavily_search],
        system_prompt="You are a helpful assistant. Use tools to find current information when needed.",
    )

    # Step 2: Ask a question - the agent will automatically call tools and return the answer
    question = "Could you please tell what are current trendings on bilibili.com? Give me title and description in CHINESE"

    logger.info(f"User Question: {question}")
    logger.info("Agent is thinking and will automatically call tools...")

    # The agent handles: LLM -> Tool Call -> Tool Result -> LLM -> Final Answer
    result = await agent.ainvoke({"messages": [("user", question)]})

    # Extract the final answer from the last message
    final_message = result["messages"][-1]
    logger.info(f"\n=== Final Agent Answer ===\n{final_message.content}\n")


async def example_7_manual_tool_calling() -> None:
    """Example 7: Manual tool calling loop (客户端管理).

    This shows how to manually handle the tool calling process:
    1. LLM decides to use tool
    2. Client executes the tool
    3. Client sends result back to LLM
    4. LLM generates final answer
    """
    logger.info("=== Example 7: Manual Tool Calling Loop (客户端管理) ===")

    # Step 1: Create LLM with tools bound
    llm = _get_chat_llm()
    llm_with_tools = llm.bind_tools([tavily_search])

    # Step 2: Prepare the conversation
    question = "Could you please tell what are current trendings on bilibili.com? Give me title and description in CHINESE"

    logger.info(f"User Question: {question}\n")

    messages = [
        SystemMessage(
            content="You are a helpful assistant. Use the tavily_search tool to find current information when needed."
        ),
        HumanMessage(content=question),
    ]

    # Step 3: First LLM call - LLM decides whether to use tool
    logger.info("Step 1: LLM deciding whether to use tool...")
    response: AIMessage = await llm_with_tools.ainvoke(messages)

    # Step 4: Check if LLM wants to use a tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        logger.info(f"LLM decided to use tool: {response.tool_calls}\n")

        # Step 5: Execute the tool call (client side)
        for tool_call in response.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id")

            logger.info(
                f"Step 2: Executing tool '{tool_name}' with args: {tool_args}"
            )

            if tool_name == "tavily_search":
                tool_result = await tavily_search.ainvoke(tool_args)
                logger.info(
                    f"Tool result received (length: {len(tool_result)} chars)\n"
                )

                # Step 6: Append tool call and result to messages
                messages.append(response)  # AIMessage with tool_calls
                messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call_id,
                    )
                )

        # Step 7: Send results back to LLM for final answer
        logger.info(
            "Step 3: Sending tool results back to LLM for final answer..."
        )
        final_response: AIMessage = await llm.ainvoke(messages)
        logger.info(f"\n=== Final Answer ===\n{final_response.content}\n")
    else:
        logger.info("LLM did not use tool, responded directly:")
        logger.info(f"{response.content}\n")


async def main() -> None:
    """Run all examples."""
    # Check for API key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error(
            "TAVILY_API_KEY not found in environment. "
            "Please add it to your .env file."
        )
        return

    logger.info("Tavily API Key found. Starting examples...\n")

    try:
        # await example_1_direct_tool_call()
        # await example_2_search_with_max_results()
        # await example_3_tool_metadata()
        await example_4_full_executor_workflow()
        # await example_5_multiple_concurrent_searches()
        # await example_6_agent_with_tool()
        # await example_7_manual_tool_calling()

        logger.info("All examples completed successfully!")
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
