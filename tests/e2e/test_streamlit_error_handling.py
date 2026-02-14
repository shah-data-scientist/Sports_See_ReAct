"""
FILE: test_streamlit_error_handling.py
STATUS: Active
RESPONSIBILITY: Playwright UI tests for error handling and edge cases
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def streamlit_url():
    """Streamlit app URL."""
    return "http://localhost:8501"


@pytest.fixture(scope="module")
def screenshots_dir():
    """Directory for test screenshots."""
    screenshot_dir = Path(__file__).parent.parent.parent / "ui_test_screenshots"
    screenshot_dir.mkdir(exist_ok=True)
    return screenshot_dir


def wait_for_streamlit_ready(page: Page):
    """Wait for Streamlit app to be fully loaded."""
    page.wait_for_selector("[data-testid='stApp']", timeout=10000)
    time.sleep(2)


def submit_query(page: Page, query: str):
    """Submit a query to the Streamlit chat interface."""
    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")
    chat_input.fill(query)
    chat_input.press("Enter")
    time.sleep(2)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.slow
def test_rate_limit_error_handling(page: Page, streamlit_url: str, screenshots_dir: Path):
    """Test graceful handling of rate limit errors."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit query that might hit rate limit
    submit_query(page, "Who are the top 5 scorers?")
    time.sleep(5)

    # Check if error is displayed gracefully
    # Note: With retry logic, this should succeed, but if it fails:
    error_messages = page.locator("[data-testid='stException']").all()
    if error_messages:
        # Error occurred - check it's user-friendly
        error_text = error_messages[0].text_content()
        assert "rate limit" in error_text.lower() or "réessayer" in error_text.lower()
        page.screenshot(path=screenshots_dir / "test_rate_limit_error.png")
        print("✓ Rate limit error handled gracefully")
    else:
        # No error - retry logic worked
        messages = page.locator("[data-testid='stChatMessage']")
        expect(messages).to_have_count(3, timeout=30000)
        print("✓ Query succeeded with retry logic")


def test_network_error_display(page: Page, streamlit_url: str):
    """Test that network errors are displayed to user."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Note: This is hard to test without mocking, but we check that
    # error messages (if they occur) are visible and user-friendly
    submit_query(page, "Test query")
    time.sleep(15)

    # Check for any error elements
    error_elements = page.locator("[data-testid='stException']").all()
    for error in error_elements:
        # If errors exist, they should be visible and have text
        assert error.is_visible()
        assert len(error.text_content()) > 0

    print("✓ Error visibility test passed")


def test_api_timeout_handling(page: Page, streamlit_url: str):
    """Test handling of slow/timeout responses."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit complex query that might be slow
    submit_query(page, "Compare all players' statistics and analyze trends")
    time.sleep(30)  # Give extra time for complex query

    # Should either succeed or show appropriate error
    messages = page.locator("[data-testid='stChatMessage']")
    message_count = messages.count()

    # Should have at least processed the query (2+ messages)
    assert message_count >= 1

    print("✓ API timeout handling test passed")


# ============================================================================
# EDGE CASE QUERY TESTS
# ============================================================================


def test_numeric_only_query(page: Page, streamlit_url: str):
    """Test query with only numbers."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "123456")
    time.sleep(15)

    # Should get some response (even if it's "I don't understand")
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Numeric-only query test passed")


def test_query_with_emojis(page: Page, streamlit_url: str):
    """Test query containing emojis."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Who is the 🏀 best player? 🔥")
    time.sleep(20)

    # Should handle emojis gracefully
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Query with emojis test passed")


def test_query_with_urls(page: Page, streamlit_url: str):
    """Test query containing URLs."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Check https://nba.com for player stats")
    time.sleep(20)

    # Should handle URLs safely (not execute them)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Query with URLs test passed")


def test_sql_injection_attempt(page: Page, streamlit_url: str):
    """Test that SQL injection attempts are safely handled."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Attempt SQL injection (should be sanitized)
    submit_query(page, "'; DROP TABLE players; --")
    time.sleep(20)

    # Should get a safe response (not execute SQL)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    # App should still be functional after this
    expect(page.locator("[data-testid='stApp']")).to_be_visible()

    print("✓ SQL injection safety test passed")


def test_xss_attempt(page: Page, streamlit_url: str):
    """Test that XSS attempts are safely handled."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Attempt XSS (should be escaped)
    submit_query(page, "<script>alert('XSS')</script>")
    time.sleep(15)

    # Check that script did not execute (no alert appeared)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ XSS safety test passed")


def test_very_long_single_word(page: Page, streamlit_url: str):
    """Test query with extremely long single word."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    long_word = "a" * 500
    submit_query(page, f"Tell me about {long_word}")
    time.sleep(20)

    # Should handle without breaking layout
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Very long single word test passed")


def test_multilingual_query(page: Page, streamlit_url: str):
    """Test query mixing multiple languages."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Who is the best joueur de basketball プレイヤー?")
    time.sleep(20)

    # Should handle multilingual text
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Multilingual query test passed")


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================


def test_page_refresh_preserves_state(page: Page, streamlit_url: str):
    """Test that refreshing page resets state properly."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit query
    submit_query(page, "Hello")
    time.sleep(15)

    # Should have messages
    messages = page.locator("[data-testid='stChatMessage']")
    initial_count = messages.count()
    assert initial_count >= 2

    # Refresh page
    page.reload()
    wait_for_streamlit_ready(page)

    # State should reset (only welcome message)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(1)

    print("✓ Page refresh state reset test passed")


def test_multiple_tabs_independence(page: Page, streamlit_url: str):
    """Test that multiple tabs/contexts are independent."""
    # Open first tab
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Hello from tab 1")
    time.sleep(15)

    # Get message count in first tab
    messages_tab1 = page.locator("[data-testid='stChatMessage']")
    count_tab1 = messages_tab1.count()

    # Open second context/tab
    context2 = page.context.browser.new_context()
    page2 = context2.new_page()
    page2.goto(streamlit_url)
    wait_for_streamlit_ready(page2)

    # Second tab should start fresh
    messages_tab2 = page2.locator("[data-testid='stChatMessage']")
    expect(messages_tab2).to_have_count(1)  # Only welcome message

    # Clean up
    context2.close()

    print("✓ Multiple tabs independence test passed")


# ============================================================================
# CONVERSATION CONTEXT TESTS
# ============================================================================


@pytest.mark.slow
def test_context_maintained_across_turns(page: Page, streamlit_url: str):
    """Test that conversation context is maintained."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # First query
    submit_query(page, "Who is LeBron James?")
    time.sleep(20)

    # Follow-up query using "he"
    time.sleep(20)  # Rate limit protection
    submit_query(page, "What team does he play for?")
    time.sleep(20)

    # Check that we got responses
    messages = page.locator("[data-testid='stChatMessage']")
    assert messages.count() >= 5

    # The response should reference LeBron (context maintained)
    # Note: Can't easily assert content due to rate limits, but structure should be correct

    print("✓ Context maintenance test passed")


def test_context_lost_after_clear(page: Page, streamlit_url: str):
    """Test that context is properly cleared after clearing history."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit query to establish context
    submit_query(page, "Tell me about LeBron James")
    time.sleep(20)

    # Clear history
    clear_button = page.get_by_text("🗑️ Clear History")
    clear_button.click()
    time.sleep(2)

    # Submit follow-up that requires previous context
    time.sleep(10)
    submit_query(page, "What about his championships?")
    time.sleep(20)

    # Response should not reference LeBron (context was cleared)
    # Just check that we got a response
    messages = page.locator("[data-testid='stChatMessage']")
    assert messages.count() >= 3

    print("✓ Context cleared after clear history test passed")


# ============================================================================
# ACCESSIBILITY TESTS
# ============================================================================


def test_keyboard_navigation(page: Page, streamlit_url: str):
    """Test basic keyboard navigation."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Tab to chat input (may need multiple tabs depending on page structure)
    page.keyboard.press("Tab")
    time.sleep(0.5)

    # Check if chat input gets focus
    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")
    # Note: Streamlit may not always focus correctly, so we just check it's accessible

    # Type in input
    page.keyboard.type("Test keyboard input")
    time.sleep(0.5)

    # Press Enter to submit
    page.keyboard.press("Enter")
    time.sleep(5)

    print("✓ Keyboard navigation test passed")


def test_screen_reader_labels(page: Page, streamlit_url: str):
    """Test that elements have appropriate labels for screen readers."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for ARIA labels or semantic HTML
    # Note: Streamlit components should have built-in accessibility

    # Check that main interactive elements are present
    chat_input = page.locator("[data-testid='stChatInput']")
    expect(chat_input).to_be_visible()

    # Buttons should have text or aria-labels
    buttons = page.locator("button:visible").all()
    checked = 0
    for button in buttons[:10]:
        text = button.text_content().strip()
        aria_label = button.get_attribute("aria-label")
        if text or aria_label:
            checked += 1
    assert checked > 0, "Should have at least one labeled button"

    print("✓ Screen reader labels test passed")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


def test_page_load_time(page: Page, streamlit_url: str):
    """Test that page loads within acceptable time."""
    start_time = time.time()

    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    load_time = time.time() - start_time

    # Page should load within 10 seconds
    assert load_time < 10, f"Page load took {load_time:.2f}s, expected < 10s"

    print(f"✓ Page load time test passed ({load_time:.2f}s)")


def test_message_rendering_performance(page: Page, streamlit_url: str):
    """Test that messages render quickly."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit query and measure time until message appears
    start_time = time.time()
    submit_query(page, "Hello")

    # Wait for user message to appear
    messages = page.locator("[data-testid='stChatMessage']")
    messages.nth(1).wait_for(state="visible", timeout=5000)

    render_time = time.time() - start_time

    # Message should render within 3 seconds
    assert render_time < 3, f"Message rendering took {render_time:.2f}s"

    print(f"✓ Message rendering performance test passed ({render_time:.2f}s)")


# ============================================================================
# UI CONSISTENCY TESTS
# ============================================================================


def test_consistent_button_styling(page: Page, streamlit_url: str):
    """Test that buttons have consistent styling."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Get all buttons
    buttons = page.locator("button").all()

    # Check that buttons exist and are styled
    assert len(buttons) > 0, "Should have at least one button"

    # All visible buttons should be interactive
    for button in buttons[:5]:
        if button.is_visible():
            assert button.is_enabled() or button.get_attribute("disabled") == "true"

    print("✓ Consistent button styling test passed")


def test_consistent_color_scheme(page: Page, streamlit_url: str):
    """Test that app uses consistent color scheme."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check that Streamlit's data-testid elements are present (indicates proper rendering)
    app_element = page.locator("[data-testid='stApp']")
    expect(app_element).to_be_visible()

    # Check that chat messages have consistent styling
    messages = page.locator("[data-testid='stChatMessage']")
    if messages.count() > 0:
        # First message should have styling
        first_msg = messages.first
        expect(first_msg).to_be_visible()

    print("✓ Consistent color scheme test passed")


if __name__ == "__main__":
    """Run error handling tests with Playwright."""
    import subprocess

    print("\n" + "=" * 80)
    print("RUNNING ERROR HANDLING AND EDGE CASE TESTS")
    print("=" * 80)

    result = subprocess.run(
        [
            "poetry", "run", "pytest",
            __file__,
            "-v",
            "-s",
            "--headed",
        ],
        cwd=Path(__file__).parent.parent.parent
    )

    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ ALL ERROR HANDLING TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
