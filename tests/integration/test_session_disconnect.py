"""
Integration test: verify session persistence on disconnect.

This test requires a working model/API configuration and network access.
It is skipped by default unless RUN_LIVE_TESTS=1 is set.
"""

import asyncio
import os
import uuid
from pathlib import Path

import pytest

from src.agent import Agent, AgentConfig
from src.utils.session import SessionManager


@pytest.mark.integration
def test_disconnect_during_execution(tmp_path: Path) -> None:
    if os.getenv("RUN_LIVE_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_TESTS=1 to run live integration tests.")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for live integration tests.")

    asyncio.run(_run_disconnect_case(tmp_path))


async def _run_disconnect_case(tmp_path: Path) -> None:
    session_manager = SessionManager(base_dir=str(tmp_path / "sessions"))
    agent = Agent.create(
        AgentConfig(),
        base_dir=str(tmp_path / "agent"),
        session_manager=session_manager,
    )

    session_key = f"test-disconnect-{uuid.uuid4()}"
    query = "Search for Python news"

    await session_manager.clear(session_key)

    event_count = 0
    async for _event in agent.run(query, session_key=session_key):
        event_count += 1
        if event_count >= 2:
            break

    await asyncio.sleep(0.5)
    messages = await session_manager.load(session_key)

    # At least user message should be persisted.
    assert len(messages) >= 1

    await session_manager.clear(session_key)
