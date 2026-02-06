"""Sessions API for managing conversation history."""

import json
from pathlib import Path

from fastapi import APIRouter, Response
from pydantic import BaseModel

from src.utils.session import SessionManager, resolve_session_key

router = APIRouter()

# Shared session manager instance (used by both session API and chat agent)
session_manager = SessionManager()

# Directory for session metadata
METADATA_DIR = Path("./.mini-agent/session_metadata")


class SessionResponse(BaseModel):
    session_key: str
    messages: list[dict]


class SessionInfo(BaseModel):
    key: str
    name: str


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


class UpdateSessionNameRequest(BaseModel):
    name: str


def _get_metadata_path(session_key: str) -> Path:
    """Get metadata file path for a session."""
    from urllib.parse import quote

    safe_key = quote(session_key, safe="")
    return METADATA_DIR / f"{safe_key}.json"


def _get_session_name(session_key: str) -> str:
    """Get custom name for a session, or derive from key if not set."""
    try:
        metadata_path = _get_metadata_path(session_key)
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                return metadata.get("name", _derive_name_from_key(session_key))
    except Exception:
        pass
    return _derive_name_from_key(session_key)


def _derive_name_from_key(session_key: str) -> str:
    """Derive display name from session key."""
    parts = session_key.split(":")
    return parts[-1] if parts else session_key


def _set_session_name(session_key: str, name: str) -> None:
    """Set custom name for a session."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = _get_metadata_path(session_key)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({"name": name}, f)


@router.get("/sessions")
async def list_sessions(response: Response) -> SessionListResponse:
    """List all available sessions with their names."""
    response.headers["Cache-Control"] = "no-store"
    session_keys = await session_manager.list_sessions()
    sessions = [
        SessionInfo(key=key, name=_get_session_name(key)) for key in session_keys
    ]
    return SessionListResponse(sessions=sessions)


@router.get("/sessions/{session_key:path}")
async def get_session(session_key: str, response: Response) -> SessionResponse:
    """Load messages for a specific session."""
    response.headers["Cache-Control"] = "no-store"
    normalized_key = resolve_session_key(session_id=session_key)
    messages = await session_manager.load(normalized_key)

    # Convert Message objects to dicts for JSON response
    message_dicts = []
    for msg in messages:
        role = str(msg.role).lower()
        if role in ("ai", "model"):
            role = "assistant"
        elif role in ("human",):
            role = "user"

        content = msg.content
        if isinstance(content, str):
            content_str = content
            tool_calls = []
        else:
            # Extract text and tool calls from content blocks
            text_parts = []
            tool_calls: list[dict] = []
            tool_call_map: dict[str, dict] = {}
            tool_results: dict[str, str] = {}

            for block in content:
                if hasattr(block, "model_dump"):
                    data = block.model_dump()
                elif isinstance(block, dict):
                    data = block
                else:
                    data = {
                        "type": getattr(block, "type", None),
                        "text": getattr(block, "text", None),
                        "id": getattr(block, "id", None),
                        "name": getattr(block, "name", None),
                        "input": getattr(block, "input", None),
                        "tool_use_id": getattr(block, "tool_use_id", None),
                        "content": getattr(block, "content", None),
                    }

                block_type = data.get("type")
                if block_type == "text" and data.get("text"):
                    text_parts.append(str(data.get("text")))
                elif block_type == "tool_use" and data.get("name"):
                    tc = {
                        "id": data.get("id") or "",
                        "tool": data.get("name"),
                        "args": data.get("input") or {},
                    }
                    tool_calls.append(tc)
                    if tc["id"]:
                        tool_call_map[tc["id"]] = tc
                elif block_type == "tool_result" and data.get("tool_use_id"):
                    tool_results[str(data.get("tool_use_id"))] = str(
                        data.get("content") or ""
                    )

            for tool_id, result in tool_results.items():
                if tool_id in tool_call_map:
                    tool_call_map[tool_id]["result"] = result

            content_str = "".join(text_parts)

        msg_dict = {
            "role": role,
            "content": content_str,
            "timestamp": msg.timestamp,
        }

        # Add tool_calls if present
        if tool_calls:
            msg_dict["tool_calls"] = tool_calls

        message_dicts.append(msg_dict)

    return SessionResponse(session_key=normalized_key, messages=message_dicts)


@router.delete("/sessions/{session_key:path}")
async def clear_session(session_key: str) -> dict:
    """Clear a session's history."""
    normalized_key = resolve_session_key(session_id=session_key)
    await session_manager.clear(normalized_key)

    # Also remove metadata
    try:
        metadata_path = _get_metadata_path(normalized_key)
        if metadata_path.exists():
            metadata_path.unlink()
    except Exception:
        pass

    return {"status": "cleared", "session_key": normalized_key}


@router.patch("/sessions/{session_key:path}")
async def update_session(session_key: str, request: UpdateSessionNameRequest) -> dict:
    """Update session metadata (e.g., custom name)."""
    normalized_key = resolve_session_key(session_id=session_key)
    _set_session_name(normalized_key, request.name)
    return {"status": "updated", "session_key": normalized_key, "name": request.name}
