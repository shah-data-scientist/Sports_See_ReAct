"""
FILE: test_observability.py
STATUS: Active
RESPONSIBILITY: Unit tests for observability/logfire setup and no-op fallback
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import contextlib
from unittest.mock import MagicMock, patch

import pytest


class TestNoOpLogfireFallback:
    """Test the _NoOpLogfire class by constructing it manually.

    The class is only created when logfire is not installed,
    so we build it directly to test its behaviour.
    """

    def _make_noop_logfire(self):
        """Build a _NoOpLogfire instance regardless of whether logfire is installed."""
        from typing import Any

        class _NoOpLogfire:
            def instrument(self, *args: Any, **kwargs: Any):
                def decorator(func):
                    return func
                if args and callable(args[0]):
                    return args[0]
                return decorator

            def span(self, *args: Any, **kwargs: Any):
                return contextlib.nullcontext()

            def configure(self, **kwargs: Any) -> None:
                pass

            def info(self, *args: Any, **kwargs: Any) -> None:
                pass

            def instrument_pydantic_ai(self, **kwargs: Any) -> None:
                pass

        return _NoOpLogfire()

    def test_instrument_as_decorator(self):
        noop = self._make_noop_logfire()

        @noop.instrument("test")
        def my_func():
            return 42

        assert my_func() == 42

    def test_instrument_with_callable_arg(self):
        noop = self._make_noop_logfire()

        def my_func():
            return 99

        result = noop.instrument(my_func)
        assert result is my_func

    def test_span_context_manager(self):
        noop = self._make_noop_logfire()
        with noop.span("test_span"):
            pass  # Should not raise

    def test_configure_noop(self):
        noop = self._make_noop_logfire()
        noop.configure(service_name="test")  # Should not raise

    def test_info_noop(self):
        noop = self._make_noop_logfire()
        noop.info("msg", key="val")  # Should not raise

    def test_instrument_pydantic_ai_noop(self):
        noop = self._make_noop_logfire()
        noop.instrument_pydantic_ai()  # Should not raise


class TestLogfireGlobal:
    def test_logfire_object_is_available(self):
        from src.core.observability import logfire

        assert logfire is not None

    def test_logfire_instrument_works_as_decorator(self):
        from src.core.observability import logfire

        @logfire.instrument("test")
        def decorated_func():
            return 123

        assert decorated_func() == 123


class TestConfigureObservability:
    @patch("src.core.observability.logfire")
    @patch("src.core.observability.logger")
    def test_disabled_when_setting_false(self, mock_logger, mock_logfire):
        with patch("src.core.config.settings") as mock_settings:
            mock_settings.logfire_enabled = False

            from src.core.observability import configure_observability

            configure_observability()
            mock_logfire.configure.assert_not_called()

    @patch("src.core.observability.logfire")
    def test_graceful_failure_on_exception(self, mock_logfire):
        mock_logfire.configure.side_effect = Exception("config error")

        with patch("src.core.config.settings") as mock_settings:
            mock_settings.logfire_enabled = True

            from src.core.observability import configure_observability

            # Should not raise
            configure_observability()
