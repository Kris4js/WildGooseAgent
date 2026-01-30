"""
Error handling and retry logic for browser automation.

Provides decorators and utilities for robust browser interaction.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec

from loguru import logger

from src.utils.logger import get_logger

P = ParamSpec("P")
R = TypeVar("R")


class BrowserError(Exception):
    """Base exception for browser-related errors."""

    pass


class NavigationError(BrowserError):
    """Raised when navigation fails."""

    pass


class ElementNotFoundError(BrowserError):
    """Raised when an element cannot be found."""

    pass


class TimeoutError(BrowserError):
    """Raised when an operation times out."""

    pass


class SessionExpiredError(BrowserError):
    """Raised when a browser session has expired."""

    pass


def retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_base: Base for exponential backoff (seconds)
        retry_on: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @retry(max_attempts=3, retry_on=(TimeoutError, ConnectionError))
        async def navigate(url: str) -> dict:
            return await session.navigate(url)
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt < max_attempts:
                        # Calculate backoff time with exponential increase
                        backoff_time = backoff_base * (2 ** (attempt - 1))
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {backoff_time:.1f}s..."
                        )
                        await asyncio.sleep(backoff_time)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed. Last error: {e}"
                        )

            # If we get here, all retries failed
            raise last_exception  # type: ignore

        return wrapper  # type: ignore

    return decorator


async def safe_execute(
    operation: Callable[P, R],
    *args: P.args,
    error_mapping: dict[type[Exception], type[Exception]] | None = None,
    **kwargs: P.kwargs,
) -> R:
    """
    Safely execute an operation with error mapping.

    Args:
        operation: The async function to execute
        *args: Positional arguments for the operation
        error_mapping: Optional mapping from original exceptions to custom exceptions
        **kwargs: Keyword arguments for the operation

    Returns:
        Result of the operation

    Raises:
        Mapped exception if operation fails

    Example:
        result = await safe_execute(
            session.click,
            "#button",
            error_mapping={playwright.TimeoutError: TimeoutError}
        )
    """
    try:
        return await operation(*args, **kwargs)
    except Exception as e:
        # Map exception if mapping provided
        if error_mapping:
            for original_exc, custom_exc in error_mapping.items():
                if isinstance(e, original_exc):
                    raise custom_exc(str(e)) from e

        # Re-raise original exception
        raise


def handle_browser_errors(
    default_return: Any = None,
    log_errors: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to handle browser errors gracefully.

    Args:
        default_return: Value to return on error (must be provided)
        log_errors: Whether to log errors

    Returns:
        Decorated function that returns default_return on error
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")

                if default_return is None:
                    raise

                return default_return  # type: ignore

        return wrapper  # type: ignore

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for failing operations.

    Opens the circuit after consecutive failures, preventing cascading failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening
            timeout: Seconds to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, operation: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Execute operation with circuit breaker protection.

        Args:
            operation: The async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the operation

        Raises:
            Exception: If circuit is open or operation fails
        """
        # Check if circuit should be half-open
        if self.state == "open":
            if self.last_failure_time:
                elapsed = asyncio.get_event_loop().time() - self.last_failure_time
                if elapsed > self.timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise BrowserError("Circuit breaker is open")

        try:
            result = await operation(*args, **kwargs)

            # Reset on success
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed")

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )

            raise


# Preset retry decorators for common scenarios

retry_navigation = retry(
    max_attempts=3,
    backoff_base=2.0,
    retry_on=(TimeoutError, ConnectionError, NavigationError),
)

retry_interaction = retry(
    max_attempts=2,
    backoff_base=1.0,
    retry_on=(ElementNotFoundError, TimeoutError),
)

retry_transient = retry(
    max_attempts=5,
    backoff_base=0.5,
    retry_on=(TimeoutError, ConnectionError),
)
