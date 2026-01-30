# Examples

This directory contains example scripts demonstrating various components of the agent orchestrator.

## Example: Orchestrator with hello-skill

### File: `example_orchestrator_hello_skill.py`

Demonstrates the full 5-phase agent workflow:
1. **Understand** - Extract intent and entities from query
2. **Plan** - Generate tasks with dependencies
3. **Execute** - Run tasks (use_tools or reason)
4. **Reflect** - Evaluate if complete, iterate if needed
5. **Answer** - Synthesize final response (streaming)

### Prerequisites

1. **Get an OpenRouter API Key** (free tier available):
   - Visit https://openrouter.ai/
   - Sign up and get your API key
   - The key will start with `sk-or-v1-`

2. **Set environment variables**:

```bash
# Set your OpenRouter API key
export OPENAI_API_KEY="sk-or-v1-your-actual-key-here"

# Set the base URL (points to OpenRouter)
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
```

Or add to your `.env` file:

```env
OPENAI_API_KEY=sk-or-v1-your-actual-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
TAVILY_API_KEY=dummy_key  # Only needed if using web search
```

### Running the Example

```bash
python src/example/example_orchestrator_hello_skill.py
```

### What to Expect

When running successfully, you'll see output like:

```
============================================================
Agent Orchestrator: Testing hello-skill
============================================================
API Key found: sk-or-v1-4...cf0e
Using API base URL: https://openrouter.ai/api/v1
Initializing agent...
Agent initialized successfully!

Query: Say hello to me using the hello skill
------------------------------------------------------------
[Phase] Starting: understand
[Phase] Complete: understand
[Understand] Intent: Use hello skill to greet
[Understand] Entities: []
[Agent] Starting iteration 1
[Phase] Starting: plan
[Phase] Complete: plan
[Plan] Iteration 1: Use hello-skill to greet the user
[Plan] Tasks: 1 task(s)
  - task_1: Use hello-skill to greet the user (use_tools)
[Phase] Starting: execute
[Task] Starting: task_1
[Task] Complete: task_1
  Output: Good morning, Kris4js
[Phase] Complete: execute
[Phase] Starting: reflect
[Phase] Complete: reflect
[Reflect] Iteration 1: isComplete=True
[Reflect] Reasoning: The hello-skill provided a greeting
[Phase] Starting: answer
[Answer] Starting answer generation...
[Answer] Response (streaming):
============================================================
AGENT RESPONSE:
============================================================
Good morning! I've greeted you using the hello-skill.
------------------------------------------------------------
Agent execution completed!
============================================================
```

### Model Configuration

The example uses these free/cheap models from OpenRouter:

```python
ModelConfig(
    small="google/gemini-2.5-flash-lite-preview-09-2025",  # Fast, cheap
    large="google/gemini-3-flash-preview",  # Better reasoning
)
```

You can modify the model configuration in the example to use other models:

```python
# Cost-optimized
model_config = ModelConfig(
    small="google/gemini-2.5-flash-lite-preview-09-2025",
    large="google/gemini-2.5-flash-preview-09-2025",
)

# Quality-focused
model_config = ModelConfig(
    small="anthropic/claude-3-haiku",
    large="anthropic/claude-3.5-sonnet",
)
```

### Troubleshooting

**Error: `OPENAI_API_KEY environment variable is not set`**
- Make sure you've set the environment variable
- Check that your `.env` file is in the project root directory

**Error: `Error code: 401 - User not found`**
- Your API key is invalid or expired
- Get a new key from https://openrouter.ai/keys

**Error: Module import errors**
- Make sure you're running from the project root directory
- Activate your virtual environment: `source .venv/bin/activate`

## Other Examples

| Example | Description |
|---------|-------------|
| `example_hello_skill.py` | Test hello-skill at tool level |
| `example_tavily_tool.py` | Test Tavily web search tool |
| `example_tool_executor.py` | Test tool executor with various tools |
| `example_context_manager.py` | Test persistent context storage |
| `example_logger.py` | Test logger configuration |
| `example_message_history.py` | Test conversation history |
