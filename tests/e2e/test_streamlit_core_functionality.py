"""
FILE: test_streamlit_core_functionality.py
STATUS: Active
RESPONSIBILITY: Core Streamlit UI tests with Streamlit-compatible selectors
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu

Simplified Playwright tests that work reliably with Streamlit's dynamic rendering.
Uses page content detection instead of element selectors.
"""

import time
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def streamlit_url():
    """Streamlit app URL."""
    return "http://localhost:8501"


def wait_for_streamlit_ready(page: Page, timeout: int = 15000):
    """Wait for Streamlit app to load - uses content detection."""
    # Wait for page to have meaningful content
    page.wait_for_function(
        "() => document.body.innerText.includes('NBA') || document.body.innerText.includes('Analyst')",
        timeout=timeout
    )
    time.sleep(2)


def test_ui_loads_successfully(page: Page, streamlit_url: str):
    """Test that UI loads and displays main content."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check that main content is present
    page_text = page.content()
    assert "NBA" in page_text or "Analyst" in page_text, "NBA Analyst AI content not found"

    print("✅ UI loads successfully")


def test_welcome_message_displayed(page: Page, streamlit_url: str):
    """Test that welcome message is visible."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    page_text = page.locator("body").text_content()
    assert "Welcome" in page_text, "Welcome message not found"

    print("✅ Welcome message displayed")


def test_api_health_check(page: Page):
    """Test that API is responding."""
    # This test doesn't need Streamlit, just verifies API works
    import requests
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200, "API health check failed"

    data = response.json()
    assert data["status"] == "healthy", f"API not healthy: {data['status']}"
    assert data["index_loaded"] == True, "Vector index not loaded"

    print("✅ API health check passed")


def test_sidebar_visible(page: Page, streamlit_url: str):
    """Test that sidebar is rendered."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    page_text = page.locator("body").text_content()
    # Sidebar usually contains "Settings" or similar
    assert "Settings" in page_text or "Model:" in page_text, "Sidebar content not found"

    print("✅ Sidebar visible")


def test_multiple_page_elements(page: Page, streamlit_url: str):
    """Test that all major page elements are present."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    page_text = page.locator("body").text_content()

    # Check for key elements
    required_elements = [
        "NBA",  # Title/content
        "Ask",  # Chat input prompt
        "Model:",  # Settings
    ]

    for element in required_elements:
        assert element in page_text, f"Required element '{element}' not found on page"

    print("✅ All major page elements present")


def test_page_does_not_crash(page: Page, streamlit_url: str):
    """Test that page loads without JavaScript errors."""
    errors = []

    def on_console_message(msg):
        if "error" in msg.text.lower():
            errors.append(msg.text)

    page.on("console", on_console_message)

    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Allow time for any deferred errors
    time.sleep(2)

    # Filter out expected warnings
    critical_errors = [e for e in errors if "TypeError" in e or "ReferenceError" in e]

    assert len(critical_errors) == 0, f"JavaScript errors found: {critical_errors}"

    print("✅ Page loads without critical errors")
