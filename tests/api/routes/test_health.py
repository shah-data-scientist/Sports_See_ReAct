"""
FILE: test_health.py
STATUS: Active
RESPONSIBILITY: Unit tests for health check endpoints
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock, patch

import pytest

from src.api.routes.health import health_check, liveness_check, readiness_check


class TestHealthCheck:
    @pytest.mark.asyncio
    @patch("src.api.routes.health.get_chat_service")
    async def test_healthy_when_service_ready(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.is_ready = True
        mock_service.vector_store.index_size = 100
        mock_get_service.return_value = mock_service

        result = await health_check()
        assert result.status == "healthy"
        assert result.index_loaded is True
        assert result.index_size == 100

    @pytest.mark.asyncio
    @patch("src.api.routes.health.get_chat_service")
    async def test_degraded_when_index_not_loaded(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.is_ready = False
        mock_get_service.return_value = mock_service

        result = await health_check()
        assert result.status == "degraded"
        assert result.index_loaded is False
        assert result.index_size == 0

    @pytest.mark.asyncio
    @patch("src.api.routes.health.get_chat_service")
    async def test_unhealthy_when_service_raises(self, mock_get_service):
        mock_get_service.side_effect = RuntimeError("Service not available")

        result = await health_check()
        assert result.status == "unhealthy"
        assert result.index_loaded is False
        assert result.index_size == 0


class TestReadinessCheck:
    @pytest.mark.asyncio
    @patch("src.api.routes.health.get_chat_service")
    async def test_ready_when_service_is_ready(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.is_ready = True
        mock_get_service.return_value = mock_service

        result = await readiness_check()
        assert result == {"ready": True}

    @pytest.mark.asyncio
    @patch("src.api.routes.health.get_chat_service")
    async def test_not_ready_when_service_fails(self, mock_get_service):
        mock_get_service.side_effect = RuntimeError("boom")

        result = await readiness_check()
        assert result == {"ready": False}


class TestLivenessCheck:
    @pytest.mark.asyncio
    async def test_always_returns_alive(self):
        result = await liveness_check()
        assert result == {"alive": True}
