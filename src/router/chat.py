"""Chat API with SSE streaming."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent import Agent, AgentConfig
from src.router.sessions import session_manager as shared_session_manager
from src.agent.types import (
    ThinkingEvent,
    ToolStartEvent,
    ToolEndEvent,
    ToolErrorEvent,
    ToolLimitEvent,
    AnswerStartEvent,
    AnswerChunkEvent,
    DoneEvent,
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_key: str = "default"


async def event_generator(
    agent: Agent, message: str, session_key: str
) -> AsyncGenerator[str, None]:
    """Generate SSE events from agent execution."""
    async for event in agent.run(message, session_key=session_key):
        data = None

        match event:
            case ThinkingEvent():
                data = {"type": "thinking", "message": event.message}
            case ToolStartEvent():
                data = {
                    "type": "tool_start",
                    "tool": event.tool,
                    "args": event.args,
                }
            case ToolEndEvent():
                data = {
                    "type": "tool_end",
                    "tool": event.tool,
                    "result": event.result[:1000] if event.result else "",
                    "duration_ms": event.duration,  # Backend uses 'duration'
                }
            case ToolErrorEvent():
                data = {
                    "type": "tool_error",
                    "tool": event.tool,
                    "error": event.error,
                }
            case ToolLimitEvent():
                data = {
                    "type": "tool_limit",
                    "tool": event.tool,
                    "message": event.warning,  # Backend uses 'warning'
                }
            case AnswerStartEvent():
                data = {"type": "answer_start"}
            case AnswerChunkEvent():
                data = {"type": "answer_chunk", "chunk": event.chunk}
            case DoneEvent():
                data = {
                    "type": "done",
                    "answer": event.answer,
                    "iterations": event.iterations,
                    "tool_calls": [
                        {"tool": tc.tool, "args": tc.args} for tc in event.tool_calls
                    ],
                }

        if data:
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with SSE streaming response."""
    agent = Agent.create(AgentConfig(), session_manager=shared_session_manager)

    return StreamingResponse(
        event_generator(agent, request.message, request.session_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
