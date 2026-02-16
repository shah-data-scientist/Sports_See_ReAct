"""
FILE: observability.py
STATUS: Active
RESPONSIBILITY: Logfire observability configuration and no-op fallback
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import contextlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import logfire as _logfire

    logfire = _logfire
except ImportError:

    class _NoOpLogfire:
        """No-op fallback when logfire is not installed."""

        def instrument(self, *args: Any, **kwargs: Any):
            """Return a pass-through decorator."""

            def decorator(func):
                return func

            if args and callable(args[0]):
                return args[0]
            return decorator

        def span(self, *args: Any, **kwargs: Any):
            """Return a no-op context manager."""
            return contextlib.nullcontext()

        def configure(self, **kwargs: Any) -> None:
            """No-op configure."""

        def info(self, *args: Any, **kwargs: Any) -> None:
            """No-op log."""

        def instrument_pydantic_ai(self, **kwargs: Any) -> None:
            """No-op Pydantic AI instrumentation."""

    logfire = _NoOpLogfire()  # type: ignore[assignment]


def configure_observability() -> None:
    """Initialize observability system (Logfire or local logging).

    Priority order:
    1. Try Logfire if enabled and token provided (external observability)
    2. Fall back to local file-based logging (no external API needed)

    Local logging provides:
    - Structured JSON logs with rotation
    - Separate files for app, api, agent, errors
    - Streamlit log viewer at /Logs page
    """
    try:
        from src.core.config import settings

        # Try Logfire first if enabled
        if getattr(settings, "logfire_enabled", False) and settings.logfire_token:
            try:
                logfire.configure(
                    token=settings.logfire_token,
                    service_name="sports-see",
                    service_version="0.1.0",
                )
                logfire.instrument_pydantic_ai()
                logger.info("✓ Logfire observability configured successfully")
                return
            except Exception as e:
                logger.warning(f"Logfire configuration failed: {e}")
                logger.info("Falling back to local logging...")

        # Fall back to local file-based logging
        from src.core.logging_config import configure_local_logging

        configure_local_logging()
        logger.info("✓ Local file-based logging configured (no external API)")

    except Exception as e:
        logger.error(f"Failed to configure observability: {e}", exc_info=True)
