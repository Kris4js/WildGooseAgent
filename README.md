# Wild Goose Agent

一个基于 FastAPI + LangChain 的可扩展 Agent 系统，配套 Tauri + React 桌面端，支持工具调用、会话持久化、流式响应、技能扩展与资源浏览。

## 当前状态

项目已实现一个可用的“简单但完整”的 Agent 主链路：

- 流式 SSE 对话（`thinking/tool_start/tool_end/answer_chunk/done`）
- 会话管理（创建、切换、重命名、删除）
- 工具调用与结果内联展示
- 对话历史持久化（JSONL）
- 工具上下文持久化（JSON）
- 技能发现与调用
- 资源页（Tools/Skills 浏览）

## 技术栈

- Backend: Python 3.12+, FastAPI, LangChain, LangGraph, Playwright
- Frontend: React 19, TypeScript, Vite, Tauri
- Tooling: uv, bun, ruff, pytest

## 快速开始

### 1) 安装依赖

```bash
uv sync
cd app && bun install
```

如需浏览器自动化工具：

```bash
playwright install
```

### 2) 配置环境变量

项目根目录 `.env`：

```bash
OPENAI_API_KEY=your_openrouter_or_openai_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
TAVILY_API_KEY=optional_for_web_search
```

说明：当前默认是 `ChatOpenAI` 兼容模式，`OPENAI_BASE_URL` 可指向 OpenRouter。

### 3) 启动开发环境

后端：

```bash
uv run -m src.router
```

桌面端（Tauri）：

```bash
cd app && bun run tauri dev
```

或一键：

```bash
./scripts/dev.sh
```

## Agent 架构设计（重点）

### 1. 核心执行器：`Agent.run()`

文件：`src/agent/agent.py`

`run()` 是一个异步生成器，负责完整的 ReAct 风格循环：

1. 解析并规范化 `session_key`
2. 加载会话历史（`SessionManager`）与记忆检索（`MemoryManager`）
3. 构建 prompt 并调用 LLM
4. 若返回工具调用：执行工具并写入 `Scratchpad`
5. 若无工具调用：进入答案流式阶段
6. 通过事件持续向上游输出状态
7. 结束后保存 assistant 消息与记忆

### 2. 事件流契约（后端 -> 前端）

事件类型定义：`src/agent/types.py`

- `thinking`
- `tool_start`
- `tool_end`
- `tool_error`
- `tool_limit`
- `answer_start`
- `answer_chunk`
- `done`

路由层在 `src/router/chat.py` 将事件序列化为 SSE：

- 端点：`POST /api/chat`
- 协议：`text/event-stream`
- 单事件格式：`data: {...}\n\n`

### 3. 单查询真相源：`Scratchpad`

文件：`src/agent/scratchpad.py`

每次 query 对应一个 append-only JSONL scratchpad，记录：

- 思考信息（thinking）
- 工具调用与参数
- 工具结果与 LLM summary
- 工具调用次数与软限流告警

它是 Agent 在循环中的“单一事实源”，用于后续 prompt 迭代与收敛。

### 4. 持久化层拆分

- 会话消息：`src/utils/session.py`
  - JSONL 持久化，append-only
  - 内存缓存 + 文件恢复
  - session_key 规范化与安全编码

- 工具上下文：`src/utils/context.py`
  - 将完整工具输出落盘
  - 通过 pointer 引用避免上下文膨胀

- 长期记忆：`src/utils/memory.py`
  - 存储问答摘要
  - 关键词检索 + 时间衰减

### 5. 工具系统

文件：`src/tools/registry.py`

- 内置工具：读写改查、命令执行等
- 搜索工具：Tavily（按环境变量注册）
- 浏览器工具：Playwright（可用时注册）
- 技能工具：动态加载 Skill 并注入执行说明

## 前端架构

### 对话页

文件：`app/src/pages/Chat.tsx` + `app/src/hooks/useChat.ts`

- `useChat` 负责 SSE 消费、消息状态、会话切换
- 按 session 维护独立 UI 状态，避免切换会话导致流式气泡丢失
- `MessageBubble` 支持 Markdown + GFM 表格渲染

### 资源页

文件：`app/src/pages/Resources.tsx`

- 浏览工具分组与技能详情
- 支持搜索、分组筛选、详情预览

## API 概览

- `POST /api/chat`：流式聊天
- `GET /api/sessions`：会话列表
- `GET /api/sessions/{session_key}`：会话详情
- `PATCH /api/sessions/{session_key}`：更新会话名
- `DELETE /api/sessions/{session_key}`：删除会话
- `GET /api/tools` / `GET /api/tools/{name}`：工具信息
- `GET /api/skills` / `GET /api/skills/{name}`：技能信息

## 项目结构

```text
wild-goose-agent/
├── src/
│   ├── agent/          # Agent 循环、事件、prompt、scratchpad
│   ├── model/          # LLM 调用与流式适配
│   ├── router/         # FastAPI 路由层
│   ├── tools/          # 工具实现与注册
│   ├── skills/         # Skill 发现与加载
│   └── utils/          # session/context/memory/logger
├── app/
│   ├── src/            # React 页面、组件、hooks
│   └── src-tauri/      # Tauri Rust 壳层
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
└── CLAUDE.md
```

## 测试与质量

Python 静态检查：

```bash
ruff check src tests
```

测试：

```bash
.venv/bin/python -m pytest -q
```

说明：

- `tests/integration/` 下的实时用例默认跳过
- 运行实时测试需设置：`RUN_LIVE_TESTS=1`

## 开发建议

- 先保证事件流契约稳定，再调整前端展示逻辑
- 新工具优先在 `src/tools/registry.py` 完成注册与描述同步
- 任何会话/流式相关变更，都要同时验证“切会话再切回”场景
