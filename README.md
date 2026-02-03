# Wild Goose Agent

> 一个功能强大的 AI 智能代理系统，配备现代化的桌面图形界面

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Wild Goose Agent 是一个基于 LangChain/LangGraph 构建的智能代理系统，具有精美的 PySide6 桌面用户界面。该系统采用异步生成器模式实现实时流式输出，支持工具调用、技能扩展和长期记忆管理。

## ✨ 核心功能

- **🤖 智能对话**：基于大语言模型的自然语言交互
- **🔧 工具系统**：内置丰富的工具集，支持文件操作、代码执行、网络搜索等
- **🎯 技能扩展**：通过 Markdown 文件定义自定义技能，轻松扩展代理能力
- **💾 长期记忆**：基于关键词搜索和时间衰减的智能记忆系统
- **🖥️ 精美 UI**：Cherry Studio 风格的现代化桌面界面，支持亮色/暗色主题
- **🌐 浏览器自动化**：基于 Playwright 的浏览器操作工具
- **📊 实时反馈**：事件流架构实现毫秒级 UI 更新

## 🛠️ 技术栈

### 核心框架
- **Python 3.12+**：现代 Python 特性
- **LangChain/LangGraph**：LLM 应用开发框架
- **PySide6**：Qt 官方 Python 绑定，用于桌面 UI

### AI 模型支持
- **OpenAI GPT 系列**：GPT-4、GPT-3.5 等
- **Google Gemini**：Google 最新 AI 模型
- **Anthropic Claude**：Claude 3.5 Sonnet 等

### 浏览器自动化
- **Playwright**：现代化浏览器自动化框架

### 开发工具
- **uv**：极速 Python 包管理器
- **ruff**：超快速的代码检查和格式化工具
- **pytest**：功能强大的测试框架

## 📦 安装

### 环境要求

- Python 3.12 或更高版本
- macOS / Linux / Windows

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/wild-goose-agent.git
cd wild-goose-agent
```

2. **安装依赖**
```bash
# 使用 uv 安装所有依赖
uv sync
```

3. **安装浏览器驱动**
```bash
# 安装 Playwright 浏览器（用于浏览器自动化工具）
playwright install
```

4. **配置 API 密钥**

创建环境变量文件或直接在 UI 的设置中配置：

```bash
# OpenAI API（必需）
export OPENAI_API_KEY="your-openai-api-key"

# Tavily 搜索 API（可选，用于网络搜索功能）
export TAVILY_API_KEY="your-tavily-api-key"
```

## 🚀 快速开始

### 启动桌面应用

```bash
# 启动 PySide6 桌面 UI
python -m app.main
```

### 命令行使用

```bash
# 运行基础示例
python examples/basic_use.py
```

### 创建自定义技能

在 `~/.dexter/skills/` 或项目 `.dexter/skills/` 目录下创建技能：

```markdown
---
name: "my-skill"
description: "我的自定义技能"
---

# 技能说明

这是技能的详细说明文档，会被加载到系统中。
```

## 📁 项目结构

```
wild-goose-agent/
├── src/                          # 核心源代码
│   ├── agent/                    # 代理系统
│   │   ├── agent.py              # 主代理引擎（异步生成器）
│   │   ├── scratchpad.py         # 查询执行的单一数据源
│   │   ├── types.py              # 事件类型定义
│   │   └── prompts.py            # 系统提示词
│   ├── tools/                    # 工具系统
│   │   ├── registry.py          # 工具注册中心
│   │   ├── buildin.py            # 内置工具
│   │   ├── skill.py              # 技能工具
│   │   └── browser/              # 浏览器自动化
│   ├── skills/                   # 技能系统
│   ├── utils/                    # 实用工具
│   │   ├── session.py            # 会话管理
│   │   ├── context.py            # 上下文管理
│   │   └── memory.py             # 长期记忆
│   └── model/                    # 模型接口
│
├── app/                          # 桌面应用
│   ├── main.py                   # 应用入口
│   ├── bridge/                   # Qt 桥接层
│   ├── pages/                    # UI 页面
│   ├── components/               # 可复用组件
│   └── themes/                   # 主题样式
│
├── examples/                     # 使用示例
├── tests/                        # 测试代码
├── pyproject.toml                # 项目配置
└── CLAUDE.md                     # 开发指南
```

## 💡 使用指南

### 核心概念

#### 1. 代理工作流程

```
用户查询
    ↓
创建 Scratchpad
    ↓
加载会话历史 + 搜索记忆
    ↓
LLM 推理 → 工具调用
    ↓
执行工具 → 持久化结果 → LLM 总结
    ↓
循环直到完成
    ↓
生成最终答案
    ↓
保存会话和记忆
```

#### 2. 事件流架构

代理使用异步生成器模式，实时输出事件：

- `ThinkingEvent`：代理思考过程
- `ToolStartEvent`：工具开始执行
- `ToolEndEvent`：工具执行完成
- `DoneEvent`：查询完成

UI 通过信号槽机制订阅这些事件，实现毫秒级实时更新。

#### 3. 技能系统

技能从三个位置发现（后者覆盖前者）：

1. **内置技能**：`src/skills/`
2. **用户技能**：`~/.dexter/skills/`
3. **项目技能**：`.dexter/skills/`

每个技能是一个包含 `SKILL.md` 的目录，使用 YAML 前言定义元数据。

### 内置工具

- **文件操作**：`read`、`write`、`edit`、`list`、`grep`
- **代码执行**：`exec`
- **网络搜索**：`web_search`（需要 Tavily API）
- **浏览器自动化**：`browser_navigate`、`browser_click`、`browser_type` 等
- **技能调用**：`skill`

## 🔧 开发指南

### 代码检查

```bash
# 运行代码检查
ruff check

# 自动修复问题
ruff check --fix
```

### 代码格式化

```bash
# 格式化代码
ruff format
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单个测试
pytest tests/unit/test_file.py::test_function

# 查看覆盖率
pytest --cov=src tests/
```

### 扩展指南

#### 添加新工具

在 `src/tools/buildin.py` 中定义新工具函数，添加到工具注册表。

#### 添加新技能

创建技能目录和 `SKILL.md` 文件，系统会自动发现。

#### 自定义 UI 主题

在 `app/themes/` 目录下创建 `.qss` 样式文件。

## 🎨 界面预览

桌面应用提供以下功能页面：

- **聊天页面**：与 AI 代理对话，查看流式响应
- **工具页面**：查看和管理可用工具
- **技能页面**：浏览和启用自定义技能
- **提示词页面**：管理自定义提示词模板
- **资源页面**：整合工具、技能和提示词管理
- **设置页面**：配置 API 密钥和模型参数

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 使用 ruff 进行代码格式化
- 为新功能添加测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的 LLM 应用框架
- [PySide6](https://wiki.qt.io/Qt_for_Python) - Qt 官方 Python 绑定
- [Playwright](https://playwright.dev/) - 现代化浏览器自动化

## 📮 联系方式

- 作者：Kris
- 项目链接：[https://github.com/yourusername/wild-goose-agent](https://github.com/yourusername/wild-goose-agent)
- 问题反馈：[Issues](https://github.com/yourusername/wild-goose-agent/issues)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
