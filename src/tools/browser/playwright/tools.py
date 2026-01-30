"""
Playwright-based browser automation tools.

Implements LangChain tools for browser automation using Playwright.
"""

from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from src.tools.types import format_tool_result

# Global session manager (singleton pattern)
_session_manager = None


def get_session_manager():
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        from src.tools.browser.session import BrowserSessionManager, BrowserOptions

        _session_manager = BrowserSessionManager(
            options=BrowserOptions(
                headless=True,
                timeout=30000,
            )
        )
    return _session_manager


# ======================================================================
# Input Schemas
# ======================================================================


class NavigateInput(BaseModel):
    """Input for browser_navigate tool."""

    url: str = Field(..., description="The URL to navigate to")
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for session reuse",
    )
    wait_until: str = Field(
        "load",
        description="When to consider navigation succeeded: 'load', 'domcontentloaded', 'networkidle'",
    )


class SnapshotInput(BaseModel):
    """Input for browser_snapshot tool."""

    session_id: Optional[str] = Field(
        None,
        description="Optional session ID (uses default session if not provided)",
    )


class ClickInput(BaseModel):
    """Input for browser_click tool."""

    selector: str = Field(
        ...,
        description="CSS selector for the element to click (e.g., 'button.submit', '#submit-btn')",
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )
    button: str = Field(
        "left",
        description="Mouse button to click: 'left', 'right', or 'middle'",
    )


class TypeInput(BaseModel):
    """Input for browser_type tool."""

    selector: str = Field(
        ...,
        description="CSS selector for the input element",
    )
    text: str = Field(..., description="Text to type into the element")
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )
    clear: bool = Field(
        True,
        description="Clear existing text before typing",
    )


class FillFormInput(BaseModel):
    """Input for browser_fill_form tool."""

    fields: dict[str, str] = Field(
        ...,
        description="Dictionary mapping CSS selectors to values",
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )


class ScreenshotInput(BaseModel):
    """Input for browser_screenshot tool."""

    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )
    full_page: bool = Field(
        False,
        description="Capture the full scrollable page instead of just the viewport",
    )
    filename: Optional[str] = Field(
        None,
        description="Optional filename to save the screenshot",
    )


class WaitForInput(BaseModel):
    """Input for browser_wait_for tool."""

    selector: Optional[str] = Field(
        None,
        description="CSS selector to wait for (if None, waits for timeout)",
    )
    timeout: int = Field(
        30000,
        description="Timeout in milliseconds",
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )


class EvaluateInput(BaseModel):
    """Input for browser_evaluate tool."""

    javascript: str = Field(
        ...,
        description="JavaScript code to execute in the page context",
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )


class SelectOptionInput(BaseModel):
    """Input for browser_select_option tool."""

    selector: str = Field(
        ...,
        description="CSS selector for the select element",
    )
    value: str = Field(..., description="Option value to select")
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID",
    )


# ======================================================================
# Browser Tools
# ======================================================================


@tool(args_schema=NavigateInput)
async def browser_navigate(
    url: str,
    session_id: Optional[str] = None,
    wait_until: str = "load",
) -> str:
    """Navigate to a URL in the browser.

    Use this tool to open a webpage. Returns the page title and URL after navigation.

    Examples:
        - Navigate to homepage: "https://example.com"
        - Navigate to specific page: "https://example.com/products"

    Args:
        url: The URL to navigate to
        session_id: Optional session ID for reusing existing sessions
        wait_until: When to consider navigation succeeded

    Returns:
        JSON string with navigation result including page title and URL
    """
    manager = get_session_manager()

    # Get or create session
    if session_id:
        session = await manager.get_session(session_id)
        if not session:
            return format_tool_result(
                data={"success": False, "error": f"Session {session_id} not found"}
            )
    else:
        session = await manager.create_session()

    result = await session.navigate(url, wait_until=wait_until)
    return format_tool_result(data=result, source_urls=[url] if result.get("success") else None)


@tool(args_schema=SnapshotInput)
async def browser_snapshot(session_id: Optional[str] = None) -> str:
    """Get an accessibility snapshot of the current page.

    Returns the page structure with accessibility information, including all interactive elements.
    Use this to understand what's on the page before clicking or typing.

    Args:
        session_id: Optional session ID

    Returns:
        JSON string with page accessibility tree
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.snapshot()
    return format_tool_result(data=result)


@tool(args_schema=ClickInput)
async def browser_click(
    selector: str,
    session_id: Optional[str] = None,
    button: str = "left",
) -> str:
    """Click an element on the page.

    Use this to interact with buttons, links, and other clickable elements.

    Examples:
        - Click a button: selector="button.submit"
        - Click by ID: selector="#submit-btn"
        - Click by class: selector=".btn-primary"

    Args:
        selector: CSS selector for the element to click
        session_id: Optional session ID
        button: Mouse button to click (default: "left")

    Returns:
        JSON string with click result
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.click(selector, button=button)
    return format_tool_result(data=result)


@tool(args_schema=TypeInput)
async def browser_type(
    selector: str,
    text: str,
    session_id: Optional[str] = None,
    clear: bool = True,
) -> str:
    """Type text into an input field.

    Use this to fill in text inputs, search fields, and textareas.

    Examples:
        - Type in search box: selector="input[name='search']", text="python tutorial"
        - Type in email field: selector="#email", text="user@example.com"

    Args:
        selector: CSS selector for the input element
        text: Text to type
        session_id: Optional session ID
        clear: Clear existing text before typing (default: True)

    Returns:
        JSON string with typing result
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.type_text(selector, text, clear=clear)
    return format_tool_result(data=result)


@tool(args_schema=FillFormInput)
async def browser_fill_form(
    fields: dict[str, str],
    session_id: Optional[str] = None,
) -> str:
    """Fill multiple form fields at once.

    Use this to fill out entire forms efficiently. Provide a dictionary mapping
    CSS selectors to values.

    Examples:
        Fill login form:
        {
            "#username": "user@example.com",
            "#password": "secure_password",
            "#remember-me": "true"
        }

    Args:
        fields: Dictionary mapping CSS selectors to values
        session_id: Optional session ID

    Returns:
        JSON string with fill results for each field
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.fill_form(fields)
    return format_tool_result(data=result)


@tool(args_schema=ScreenshotInput)
async def browser_screenshot(
    session_id: Optional[str] = None,
    full_page: bool = False,
    filename: Optional[str] = None,
) -> str:
    """Take a screenshot of the current page.

    Use this to capture visual state of the page for debugging or verification.

    Args:
        session_id: Optional session ID
        full_page: Capture full scrollable page (default: False)
        filename: Optional filename to save screenshot

    Returns:
        JSON string with screenshot data (base64 encoded) and path
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.screenshot(path=filename, full_page=full_page)
    return format_tool_result(data=result)


@tool(args_schema=WaitForInput)
async def browser_wait_for(
    selector: Optional[str] = None,
    timeout: int = 30000,
    session_id: Optional[str] = None,
) -> str:
    """Wait for an element to appear or for a timeout.

    Use this to wait for dynamic content to load or for animations to complete.

    Examples:
        - Wait for element: selector=".loading-complete"
        - Wait for specific time: timeout=5000 (5 seconds)

    Args:
        selector: Optional CSS selector to wait for
        timeout: Timeout in milliseconds (default: 30000)
        session_id: Optional session ID

    Returns:
        JSON string with wait result
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.wait_for(selector=selector, timeout=timeout)
    return format_tool_result(data=result)


@tool(args_schema=EvaluateInput)
async def browser_evaluate(
    javascript: str,
    session_id: Optional[str] = None,
) -> str:
    """Execute JavaScript code in the page context.

    Use this for advanced interactions not covered by other tools.

    Examples:
        - Get page title: "document.title"
        - Scroll to bottom: "window.scrollTo(0, document.body.scrollHeight)"
        - Get element text: "document.querySelector('.text').textContent"

    Args:
        javascript: JavaScript code to execute
        session_id: Optional session ID

    Returns:
        JSON string with evaluation result
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    result = await session.evaluate(javascript)
    return format_tool_result(data=result)


@tool(args_schema=SelectOptionInput)
async def browser_select_option(
    selector: str,
    value: str,
    session_id: Optional[str] = None,
) -> str:
    """Select an option in a dropdown menu.

    Use this to interact with select elements.

    Examples:
        - Select option: selector="#country", value="USA"

    Args:
        selector: CSS selector for the select element
        value: Option value to select
        session_id: Optional session ID

    Returns:
        JSON string with selection result
    """
    manager = get_session_manager()

    session = await manager.get_session(session_id) if session_id else None
    if not session:
        return format_tool_result(
            data={"success": False, "error": "No active session. Navigate to a URL first."}
        )

    try:
        await session.page.select_option(selector, value)
        result = {"success": True, "selector": selector, "value": value}
    except Exception as e:
        result = {"success": False, "error": str(e), "selector": selector}

    return format_tool_result(data=result)


# ======================================================================
# Tool Export
# ======================================================================


def get_all_playwright_tools() -> list:
    """Get all Playwright-based browser tools.

    Returns:
        List of LangChain StructuredTool instances
    """
    return [
        browser_navigate,
        browser_snapshot,
        browser_click,
        browser_type,
        browser_fill_form,
        browser_screenshot,
        browser_wait_for,
        browser_evaluate,
        browser_select_option,
    ]
