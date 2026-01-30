"""
Browser automation tools for web interaction.

This package provides tools for browser automation including:
- Navigation and page interaction
- Form filling and submission
- Element clicking and text input
- Session management for authentication flows
- Screenshot and snapshot capabilities

Uses Playwright for local browser automation.

Usage:
    from src.tools.browser import get_browser_tools

    tools = get_browser_tools()
    agent = Agent(options=AgentOptions(extra_tools=tools))
"""

from src.tools.browser.session import BrowserSessionManager
from src.tools.browser.playwright import get_playwright_tools

__all__ = [
    "BrowserSessionManager",
    "get_browser_tools",
]


def get_browser_tools():
    """
    Get browser automation tools.

    Returns:
        List of LangChain StructuredTool instances

    Examples:
        >>> tools = get_browser_tools()
    """
    return get_playwright_tools()
