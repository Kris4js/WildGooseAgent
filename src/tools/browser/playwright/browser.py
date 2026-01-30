"""
Playwright browser wrapper for direct browser control.

Provides a high-level interface to Playwright's async API.
"""

from typing import Any, Optional

from loguru import logger

from src.tools.browser.session import BrowserOptions


class PlaywrightBrowser:
    """High-level Playwright browser wrapper."""

    def __init__(self, options: BrowserOptions | None = None):
        """Initialize browser wrapper.

        Args:
            options: Browser configuration options
        """
        self.options = options or BrowserOptions()
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    async def start(self) -> None:
        """Start the browser and create initial page."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.options.headless,
            slow_mo=self.options.slow_mo,
        )
        self._context = await self._browser.new_context(
            viewport={
                "width": self.options.viewport_width,
                "height": self.options.viewport_height,
            },
            user_agent=self.options.user_agent,
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.options.timeout)

        logger.info("Playwright browser started")

    async def stop(self) -> None:
        """Stop the browser and cleanup resources."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("Playwright browser stopped")
        except Exception as e:
            logger.error(f"Error stopping browser: {e}")

    @property
    def page(self) -> Any:
        """Get the current page."""
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    @property
    def context(self) -> Any:
        """Get the current browser context."""
        if self._context is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._context

    @property
    def browser(self) -> Any:
        """Get the browser instance."""
        if self._browser is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._browser

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
