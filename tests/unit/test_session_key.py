from src.utils.session import (
    build_agent_main_session_key,
    parse_agent_session_key,
    resolve_session_key,
    to_agent_store_session_key,
)


def test_build_agent_main_session_key_defaults_to_lowercase() -> None:
    key = build_agent_main_session_key("Main-Agent", "Default")
    assert key == "agent:main-agent:default"


def test_to_agent_store_session_key_handles_plain_session_id() -> None:
    key = to_agent_store_session_key("main", "abc-123")
    assert key == "agent:main:abc-123"


def test_resolve_session_key_prefers_explicit_session_key() -> None:
    key = resolve_session_key(agent_id="main", session_id="ignored", session_key="foo")
    assert key == "agent:main:foo"


def test_parse_agent_session_key_extracts_agent_and_rest() -> None:
    parsed = parse_agent_session_key("agent:Main:subagent:task")
    assert parsed is not None
    assert parsed.agent_id == "main"
    assert parsed.rest == "subagent:task"
