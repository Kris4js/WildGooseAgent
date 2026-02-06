# CLAUDE.md

This document is the engineering guide for agents working in this repository.

## 1. Project Snapshot

Wild Goose Agent is a desktop AI assistant stack:

- Backend: FastAPI (`src/router`) + Agent core (`src/agent`)
- Frontend: React + TypeScript (`app/src`) wrapped by Tauri (`app/src-tauri`)
- Runtime pattern: SSE streaming events from backend to frontend
- Persistence: JSONL sessions, JSON tool context, file-based long-term memory

The project is currently in a “single-agent core” phase with strong focus on:

- predictable agent loop behavior
- tool execution visibility
- session switching correctness
- streaming UI continuity

## 2. Dev Commands

## Environment setup

```bash
uv sync
cd app && bun install
playwright install
```

## Run development

```bash
# full stack
./scripts/dev.sh

# backend only
uv run -m src.router

# frontend only (Tauri)
cd app && bun run tauri dev
```

## Quality checks

```bash
ruff check src tests
.venv/bin/python -m pytest -q
cd app && bun run build
```

## Live integration test (network/model required)

```bash
RUN_LIVE_TESTS=1 .venv/bin/python -m pytest -q tests/integration/test_session_disconnect.py
```

## 3. Environment Variables

Configured in project root `.env`.

- `OPENAI_API_KEY` (required)
- `OPENAI_BASE_URL` (optional, set OpenRouter endpoint when using OpenRouter)
- `TAVILY_API_KEY` (optional, enables `web_search`)

Important:

- `src/model/llm.py` loads `.env` from project root with `override=True`.
- This is intentional to avoid stale process-level env values shadowing updated keys.

## 4. Backend Architecture

## Entry & API routing

- App entry: `src/router/__init__.py` (`app = FastAPI(...)`)
- Run module: `src/router/__main__.py`
- API groups:
  - `src/router/chat.py`
  - `src/router/sessions.py`
  - `src/router/tools.py`
  - `src/router/skills.py`

## Chat streaming contract

Endpoint: `POST /api/chat`

The response is SSE (`text/event-stream`), with `data:` JSON events.

Event types:

- `thinking`
- `tool_start`
- `tool_end`
- `tool_error`
- `tool_limit`
- `answer_start`
- `answer_chunk`
- `done`

Keep this contract stable unless frontend hook is updated together.

## Agent core

File: `src/agent/agent.py`

Main responsibilities:

- session normalization (`resolve_session_key`)
- load prior messages + memory context
- iterative model/tool loop
- tool execution events
- streamed answer generation
- finalize persistence to session and memory
- interruption handling on disconnect

Dependencies:

- `Scratchpad` (`src/agent/scratchpad.py`) as per-query truth source
- `SessionManager` (`src/utils/session.py`)
- `ToolContextManager` (`src/utils/context.py`)
- `MemoryManager` (`src/utils/memory.py`)

## LLM adapter

File: `src/model/llm.py`

- `llm_call()` for non-stream / tool calls
- `llm_stream_call()` for stream
- stream chunk normalization handles provider-specific chunk shapes

When changing this file, validate:

1. OpenRouter/OpenAI compatibility
2. chunk delta correctness
3. no regression in `answer_chunk` frequency

## 5. Frontend Architecture

## Top-level app

- `app/src/App.tsx`: tabs between Chat and Resources

## Chat flow

- `app/src/pages/Chat.tsx`: page composition
- `app/src/hooks/useChat.ts`: state machine + SSE parsing

`useChat` key behavior:

- maintains per-session UI state (messages/loading/thinking/toolcalls)
- keeps in-flight streams mapped by session key
- restores stream state when switching back to an active session

## Message rendering

- `app/src/components/MessageBubble.tsx`
- Markdown rendered with `react-markdown` + `remark-gfm`
- table style in `app/src/components/MessageBubble.css`

## Session UI

- `app/src/components/SessionList.tsx`
- supports create/delete/rename, synced with backend session APIs

## Resources page

- `app/src/pages/Resources.tsx` and `app/src/pages/resources/*`
- displays grouped tools and skills details from backend

## 6. Persistence Model

## Sessions

- files: `.mini-agent/sessions/*.jsonl`
- metadata: `.mini-agent/session_metadata/*.json`
- each message line follows `Message` schema in `src/utils/session.py`

## Tool context

- files: `.mini-agent/context/*.json`
- written by `ToolContextManager` for detailed tool outputs

## Memory

- files under `.mini-agent/memory`
- queried before each run for context augmentation

## 7. Testing Layout

Structured under `tests/`:

- `tests/unit/`: deterministic, no network
- `tests/integration/`: may require live API/network (`@pytest.mark.integration`)

Rules:

- avoid ad-hoc test scripts in repo root
- keep integration tests opt-in via env flags
- ensure `pytest` default run is stable locally and CI-friendly

## 8. Known Engineering Constraints

- Browser tools depend on Playwright runtime availability.
- Tool calls are associated into assistant history as content blocks; session API reconstructs `tool_calls` for frontend.
- Session switching and streaming are tightly coupled; changes in one side often require updating both `useChat.ts` and `src/router/sessions.py` parsing behavior.

## 9. Change Checklist

Before merging substantial changes:

1. `ruff check src tests`
2. `.venv/bin/python -m pytest -q`
3. `cd app && bun run build`
4. manual smoke test:
   - send message
   - switch session while streaming
   - switch back
   - verify bubble/tool progress continuity
