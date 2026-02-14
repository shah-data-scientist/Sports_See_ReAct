"""
FILE: conftest.py
STATUS: Active
RESPONSIBILITY: Playwright fixtures for E2E tests
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest
import time
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context arguments."""
    return {
        "ignore_https_errors": True,
        "viewport": {"width": 1920, "height": 1080},
    }


@pytest.fixture
def streamlit_page(page: Page) -> Page:
    """
    Fixture that opens Streamlit app and waits for it to load.

    Args:
        page: Playwright page fixture

    Yields:
        Page object with Streamlit app loaded
    """
    # Navigate to Streamlit app (using port 8501 — standard port)
    page.goto("http://localhost:8501", wait_until="load")

    # Wait for page to be interactive
    page.wait_for_load_state("domcontentloaded")

    # Additional wait to ensure Streamlit components are rendered
    time.sleep(3)

    yield page


@pytest.fixture
def api_base_url() -> str:
    """
    Return API base URL for direct API tests.

    Returns:
        API base URL
    """
    return "http://localhost:8000/api/v1"


@pytest.fixture
def send_query(streamlit_page):
    """Fixture providing a function to send chat queries and wait for LLM response.

    Uses content-growth polling to detect when the response has appeared.
    Returns True if response appeared within timeout, False otherwise.
    """

    def _send(query: str, timeout_ms: int = 45000, min_growth: int = 200) -> bool:
        content_before = len(streamlit_page.content())

        # Use the specific chat textarea (not selectbox input)
        chat_input = streamlit_page.locator(
            "[data-testid='stChatInputTextArea']"
        )
        chat_input.fill(query)
        chat_input.press("Enter")

        elapsed = 0
        poll_ms = 2000
        while elapsed < timeout_ms:
            streamlit_page.wait_for_timeout(poll_ms)
            elapsed += poll_ms
            if len(streamlit_page.content()) - content_before > min_growth:
                return True
        return False

    return _send
