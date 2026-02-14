"""
FILE: conftest.py
STATUS: Active
RESPONSIBILITY: Fixtures for integration tests (API contract tests, no Playwright)
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest


@pytest.fixture
def api_base_url() -> str:
    """
    Return API base URL for direct API tests.

    Returns:
        API base URL
    """
    return "http://localhost:8000/api/v1"


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "feedback: Feedback API contract tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
