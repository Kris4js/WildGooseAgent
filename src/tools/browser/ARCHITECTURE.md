# Web Automation Tools Architecture

## Overview

This document outlines the architecture for implementing web automation tools in the Marketing Agent Orchestrator. The system will provide browser automation capabilities through two complementary approaches:

1. **Direct Playwright Integration** - Native Python Playwright for maximum control
2. **MCP Browser Tools Wrapper** - Abstraction layer over existing MCP Playwright tools

## Design Principles

### 1. Dual-Mode Architecture
```
                    ┌─────────────────────────┐
                    │  Browser Tool Interface │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────▼────────┐            ┌────────▼────────┐
        │  Playwright    │            │  MCP Browser    │
        │  Direct Mode   │            │  Wrapper Mode   │
        └────────────────┘            └─────────────────┘
```

### 2. Session Management
- **Browser Pool**: Reusable browser instances
- **Session State**: Cookie storage, authentication state
- **Resource Cleanup**: Automatic browser termination
- **Concurrent Sessions**: Support for multiple isolated sessions

### 3. Error Handling Strategy
- **Retry Logic**: Configurable retry attempts for transient failures
- **Timeout Management**: Per-operation timeout controls
- **Graceful Degradation**: Fallback strategies for common failures
- **Detailed Error Reporting**: Actionable error messages

## Component Architecture

```
src/tools/browser/
├── __init__.py                 # Public API exports
├── ARCHITECTURE.md             # This file
├── session.py                  # Browser session manager
├── playwright_mode/            # Direct Playwright implementation
│   ├── __init__.py
│   ├── browser.py              # Playwright browser wrapper
│   ├── tools.py                # Individual tool implementations
│   └── selectors.py            # Element selection strategies
└── mcp_mode/                   # MCP browser tools wrapper
    ├── __init__.py
    ├── client.py               # MCP client interface
    └── tools.py                # MCP tool wrappers
```

## Core Components

### 1. BrowserSessionManager

**Purpose**: Manage browser lifecycle and session state

```python
class BrowserSessionManager:
    """Manages browser sessions with automatic cleanup."""

    async def create_session(
        self,
        session_id: str,
        headless: bool = True,
        user_agent: Optional[str] = None,
    ) -> BrowserSession

    async def get_session(self, session_id: str) -> BrowserSession

    async def close_session(self, session_id: str)

    async def cleanup_all_sessions(self)
```

**Features**:
- Lazy initialization of browser instances
- Session isolation with separate browser contexts
- Automatic resource cleanup on exit
- Configurable browser options (headless, viewport, user agent)

### 2. BrowserSession

**Purpose**: Represents a single browser session with state

```python
class BrowserSession:
    """Represents an isolated browser session."""

    async def navigate(self, url: str) -> NavigationResult

    async def snapshot(self) -> PageSnapshot

    async def click(self, selector: str, **kwargs) -> ActionResult

    async def type_text(self, selector: str, text: str) -> ActionResult

    async def fill_form(self, fields: dict[str, Any]) -> ActionResult

    async def wait_for(
        self,
        selector: Optional[str] = None,
        timeout: int = 30000,
    ) -> WaitResult

    async def save_state(self) -> SessionState

    async def restore_state(self, state: SessionState)
```

**State Management**:
- Cookie storage
- Local storage
- Session storage
- Navigation history

### 3. Tool Implementations

All tools follow the LangChain tool pattern:

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class NavigateInput(BaseModel):
    url: str = Field(..., description="The URL to navigate to")
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for session reuse",
    )

@tool(args_schema=NavigateInput)
async def browser_navigate(url: str, session_id: Optional[str] = None) -> str:
    """Navigate to a URL in the browser."""
    # Implementation
```

## Tool Categories

### Category 1: Navigation & Inspection
- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Get accessibility snapshot
- `browser_screenshot` - Capture screenshot
- `browser_console_logs` - Get console messages
- `browser_network_requests` - Get network activity

### Category 2: Element Interaction
- `browser_click` - Click element
- `browser_hover` - Hover over element
- `browser_type` - Type text into element
- `browser_press_key` - Press keyboard key
- `browser_select_option` - Select dropdown option

### Category 3: Form Operations
- `browser_fill_form` - Fill multiple form fields
- `browser_upload_file` - Upload files
- `browser_drag_drop` - Drag and drop elements

### Category 4: Advanced Operations
- `browser_wait_for` - Wait for element/text/timeout
- `browser_evaluate` - Execute JavaScript
- `browser_handle_dialog` - Handle alert/confirm/prompt dialogs
- `browser_tabs` - Manage browser tabs

### Category 5: Session Management
- `browser_save_session` - Save session state (cookies, localStorage)
- `browser_restore_session` - Restore session state
- `browser_create_session` - Create new isolated session
- `browser_close_session` - Close session and cleanup

## Element Selection Strategies

The system supports multiple element selection strategies:

```python
# CSS Selector
await session.click("button.submit")

# Text-based selection
await session.click("Submit", selector_type="text")

# Accessibility role
await session.click("button[name='Submit']")

# XPath
await session.click("//button[@type='submit']", selector_type="xpath")

# Test ID (recommended for testing)
await session.click("[data-testid='submit-button']")
```

## Authentication Flow Support

### Basic Authentication
```python
# Automatically handled via page credentials
await session.navigate(
    url="https://example.com",
    credentials={"username": "user", "password": "pass"}
)
```

### Form-based Login
```python
# Use fill_form tool for multi-field login
await session.fill_form({
    "username": "user@example.com",
    "password": "secure_password",
    "remember": True,
})
await session.click("button[type='submit']")

# Save session for reuse
state = await session.save_state()
```

### OAuth/SSO Flows
```python
# Multi-step flows using task executor
tasks = [
    Task("Navigate to SSO login page"),
    Task("Click 'Sign in with Google'"),
    Task("Wait for redirect and authentication"),
    Task("Verify successful login"),
]
```

## Error Handling

### Retry Strategy
```python
@retry(
    max_attempts=3,
    backoff=exponential,
    retry_on=(TimeoutError, NetworkError),
)
async def navigate_with_retry(url: str) -> NavigationResult:
    return await session.navigate(url)
```

### Error Categories
1. **Transient Errors** - Retry with backoff
   - Network timeouts
   - Element not immediately visible
   - Page load delays

2. **Permanent Errors** - Fail fast with details
   - Invalid selectors
   - Navigation to invalid URLs
   - Permission denied

3. **Session Errors** - Recreate session
   - Browser crash
   - Context lost
   - Session expired

## Configuration

### Environment Variables
```bash
# Browser Mode Selection
BROWSER_MODE=playwright  # Options: playwright, mcp, auto

# Playwright Options
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000
PLAYWRIGHT_SLOW_MO=0

# Session Management
SESSION_TIMEOUT=3600
SESSION_STORAGE_PATH=.market/browser/sessions
```

### Tool Registry Integration
```python
# src/tools/registry.py

def get_tool_registry(model: str) -> list[RegisteredTool]:
    tools = []

    # Conditionally add browser tools
    if os.getenv("BROWSER_MODE", "auto") != "disabled":
        from src.tools.browser import get_browser_tools
        tools.extend(get_browser_tools())

    return tools
```

## Security Considerations

### Credential Storage
- Never log passwords or sensitive tokens
- Use environment variables for credentials
- Implement secure session state serialization
- Clear session data on cleanup

### Permission Control
- Restrict file upload paths
- Validate URLs before navigation
- Limit JavaScript execution context
- Sanitize user inputs before selector injection

## Performance Optimization

### Connection Pooling
- Reuse browser instances across operations
- Share browser contexts for related sessions
- Implement session timeouts for cleanup

### Resource Limits
- Maximum concurrent sessions: 10
- Maximum session lifetime: 1 hour
- Memory limit per session: 512MB

## Testing Strategy

### Unit Tests
- Mock Playwright API responses
- Test selector logic
- Validate input schemas
- Test error handling paths

### Integration Tests
- Real browser automation
- Test against staging environments
- Validate session persistence
- Test concurrent operations

## Usage Example

```python
from src.agent.orchestrator import Agent
from src.tools.browser import get_browser_tools

# Create agent with browser tools
agent = Agent(
    options=AgentOptions(
        model=model_config,
        extra_tools=get_browser_tools(),
    )
)

# Run automation task
query = """
Navigate to example.com, log in with credentials,
fill out the search form with 'Python tutorial',
and return the top 5 results.
"""
response = await agent.run(query)
```

## Future Enhancements

1. **Visual Regression Testing** - Screenshot comparison
2. **Network Interception** - Mock API responses
3. **Multi-browser Support** - Firefox, WebKit
4. **Distributed Execution** - Remote browser grids
5. **Recording & Replay** - Record actions for replay
6. **AI-Powered Selectors** - Generate robust selectors

## References

- [Playwright Python Documentation](https://playwright.dev/python/)
- [LangChain Tools Guide](https://python.langchain.com/docs/modules/tools/)
- [MCP Browser Tools](https://github.com/modelcontextprotocol/servers)
