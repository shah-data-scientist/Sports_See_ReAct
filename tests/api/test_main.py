"""
FILE: test_main.py
STATUS: Active
RESPONSIBILITY: Unit tests for FastAPI application creation and configuration
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestCreateApp:
    @patch("src.api.main.ChatService")
    @patch("src.api.main.settings")
    def test_create_app_returns_fastapi_instance(self, mock_settings, mock_chat_cls):
        mock_settings.app_title = "Test App"
        mock_settings.api_cors_origins = ["*"]

        from src.api.main import create_app

        app = create_app()
        assert app is not None
        assert app.title == "Test App"

    @patch("src.api.main.ChatService")
    @patch("src.api.main.settings")
    def test_create_app_includes_health_router(self, mock_settings, mock_chat_cls):
        mock_settings.app_title = "Test App"
        mock_settings.api_cors_origins = ["*"]

        from src.api.main import create_app

        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/health" in routes

    @patch("src.api.main.ChatService")
    @patch("src.api.main.settings")
    def test_create_app_includes_api_v1_prefix(self, mock_settings, mock_chat_cls):
        mock_settings.app_title = "Test App"
        mock_settings.api_cors_origins = ["*"]

        from src.api.main import create_app

        app = create_app()
        routes = [route.path for route in app.routes]
        api_routes = [r for r in routes if r.startswith("/api/v1")]
        assert len(api_routes) > 0


class TestExceptionHandlers:
    @patch("src.api.main.ChatService")
    @patch("src.api.main.settings")
    def test_generic_exception_returns_500(self, mock_settings, mock_chat_cls):
        mock_settings.app_title = "Test App"
        mock_settings.api_cors_origins = ["*"]

        from src.api.main import create_app

        app = create_app()

        @app.get("/test-error")
        async def raise_error():
            raise Exception("test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
