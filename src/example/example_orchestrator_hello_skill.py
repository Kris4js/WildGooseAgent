"""
Example: Using the Agent Orchestrator to test hello-skill

This demonstrates the full 5-phase agent workflow:
1. Understand - Extract intent and entities
2. Plan - Generate tasks with dependencies
3. Execute - Run tasks (use_tools or reason)
4. Reflect - Evaluate if complete
5. Answer - Synthesize final response (streaming)

Prerequisites:
    - Set OPENAI_API_KEY environment variable (for OpenRouter)
    - Set OPENAI_BASE_URL=https://openrouter.ai/api/v1 (default)

Setup:
    export OPENAI_API_KEY="your-openrouter-api-key"
    export OPENAI_BASE_URL="https://openrouter.ai/api/v1"

Usage:
    python src/example/example_orchestrator_hello_skill.py
"""

import asyncio
import os
import sys

from typing import AsyncGenerator

from src.agent.orchestrator import Agent, AgentOptions, ModelConfig
from src.utils.logger import get_logger

logger = get_logger("src.example.example_orchestrator_hello_skill")


class SimpleCallbacks:
    """Simple callbacks to observe agent execution."""

    def on_task_start(self, task_id: str) -> None:
        print(f"[Task] Starting: {task_id}")

    def on_task_complete(self, task_id: str, output: str) -> None:
        print(f"[Task] Complete: {task_id}")
        print(f"  Output: {output[:100]}..." if len(output) > 100 else f"  Output: {output}")

    def on_task_failed(self, task_id: str, error: str) -> None:
        logger.error(f"[Task] Failed: {task_id}")
        logger.error(f"  Error: {error}")

    def onPhaseStart(self, phase: str) -> None:
        print(f"[Phase] Starting: {phase}")

    def onPhaseComplete(self, phase: str) -> None:
        print(f"[Phase] Complete: {phase}")

    def onUnderstandingComplete(self, understanding) -> None:
        print(f"[Understand] Intent: {understanding.intent}")
        print(f"[Understand] Entities: {understanding.entities}")

    def onPlanCreated(self, plan, iteration: int) -> None:
        print(f"[Plan] Iteration {iteration}: {plan.summary}")
        print(f"[Plan] Tasks: {len(plan.tasks)} task(s)")
        for task in plan.tasks:
            print(f"  - {task.id}: {task.description} ({task.taskType})")

    def onReflectionComplete(self, reflection, iteration: int) -> None:
        print(f"[Reflect] Iteration {iteration}: isComplete={reflection.isComplete}")
        print(f"[Reflect] Reasoning: {reflection.reasoning}")

    def onIterationStart(self, iteration: int) -> None:
        print(f"[Agent] Starting iteration {iteration}")

    def onAnswerStart(self) -> None:
        print("[Answer] Starting answer generation...")

    async def onAnswerStream(self, stream: AsyncGenerator[str, None]) -> None:
        """Handle streaming answer."""
        print("[Answer] Response (streaming):")
        print("\n" + "=" * 60)
        print("🤖 AGENT RESPONSE:")
        print("=" * 60)

        # Stream the answer with a special marker
        full_answer = []
        async for chunk in stream:
            print(chunk, end="", flush=True)
            full_answer.append(chunk)

        print("\n" + "=" * 60)


async def main():
    """Run the agent orchestrator with hello-skill test."""
    print("=" * 60)
    print("Agent Orchestrator: Testing hello-skill")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error(
            "OPENAI_API_KEY environment variable is not set!\n"
            "Get a free key at https://openrouter.ai/ and set it with:\n"
            "  export OPENAI_API_KEY='your-key-here'"
        )
        sys.exit(1)

    # Set up base URL (default to OpenRouter)
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    print(f"Using API base URL: {base_url}")

    # Set dummy API key for Tavily (not used for hello-skill but required)
    os.environ.setdefault("TAVILY_API_KEY", "dummy_key")

    # Define model configuration
    # Using free/cheap models from OpenRouter
    model_config = ModelConfig(
        small="google/gemini-2.5-flash-lite-preview-09-2025",  # Fast, cheap
        large="google/gemini-3-flash-preview",  # Better reasoning
    )

    # Create callbacks
    callbacks = SimpleCallbacks()

    # Create agent options
    options = AgentOptions(
        model=model_config,
        callbacks=callbacks,
        maxIterations=3,
    )

    # Initialize agent
    print("Initializing agent...")
    try:
        agent = Agent(options=options)
        print("Agent initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        sys.exit(1)

    # Test queries for hello-skill
    test_queries = [
        "Say hello to me using the hello skill",
        "Use hello-skill to greet me",
        "Can you demonstrate the hello-skill?",
    ]

    # Run with first test query
    query = test_queries[0]
    print(f"\nQuery: {query}")
    print("-" * 60)

    try:
        # Run agent (response is delivered via onAnswerStream callback)
        await agent.run(query)

        # Wait a bit for streaming to complete
        await asyncio.sleep(0.1)

        print("-" * 20)
        print("Agent execution completed!")
    except Exception as e:
        logger.exception(f"Error running agent: {e}")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)
