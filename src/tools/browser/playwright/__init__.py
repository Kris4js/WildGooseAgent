"""
Playwright-based browser automation tools.

Direct Playwright integration for maximum control and performance.
"""

from src.tools.browser.playwright.browser import PlaywrightBrowser
from src.tools.browser.playwright.tools import (
    browser_navigate,
    browser_snapshot,
    browser_click,
    browser_type,
    browser_fill_form,
    browser_screenshot,
    browser_wait_for,
    browser_evaluate,
    browser_select_option,
    get_all_playwright_tools,
)

__all__ = [
    "PlaywrightBrowser",
    "browser_navigate",
    "browser_snapshot",
    "browser_click",
    "browser_type",
    "browser_fill_form",
    "browser_screenshot",
    "browser_wait_for",
    "browser_evaluate",
    "browser_select_option",
    "get_all_playwright_tools",
]


def get_playwright_tools():
    """Get all Playwright-based browser tools."""
    return get_all_playwright_tools()
