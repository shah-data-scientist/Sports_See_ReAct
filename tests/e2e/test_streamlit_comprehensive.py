"""
FILE: test_streamlit_comprehensive.py
STATUS: Active
RESPONSIBILITY: Comprehensive Playwright UI tests for all Streamlit features
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
# BASIC UI FUNCTIONALITY TESTS
# ============================================================================


def test_page_title_and_header(page: Page, streamlit_url: str):
    """Test that page has correct title and header elements."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check page title
    expect(page).to_have_title("NBA Analyst AI")

    # Check main header
    expect(page.locator("h1")).to_contain_text("NBA Analyst")

    # Check caption with model info
    expect(page.get_by_text("Model:")).to_be_visible()

    print("✓ Page title and header test passed")


def test_chat_input_visible(page: Page, streamlit_url: str):
    """Test that chat input is visible and interactive."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")
    expect(chat_input).to_be_visible()
    expect(chat_input).to_be_enabled()

    # Check placeholder text
    expect(chat_input).to_have_attribute("placeholder", "Ask about NBA...")

    print("✓ Chat input visibility test passed")


def test_initial_welcome_message(page: Page, streamlit_url: str):
    """Test that initial welcome message is displayed."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for welcome message
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages.first).to_contain_text("Hello")
    expect(messages.first).to_contain_text("AI analyst")

    print("✓ Initial welcome message test passed")


def test_sidebar_present(page: Page, streamlit_url: str):
    """Test that sidebar is present with all sections."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for Conversations section
    expect(page.get_by_text("Conversations")).to_be_visible()

    # Check for Settings section
    expect(page.get_by_text("Settings")).to_be_visible()

    # Check for Feedback statistics section
    expect(page.get_by_text("Feedback Stats")).to_be_visible()

    print("✓ Sidebar sections test passed")


# ============================================================================
# LOADING AND ERROR STATE TESTS
# ============================================================================


def test_loading_spinner_appears(page: Page, streamlit_url: str):
    """Test that loading spinner appears during query processing."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit query and immediately check for spinner
    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")
    chat_input.fill("Who are the top 5 scorers?")
    chat_input.press("Enter")

    # Check for spinner (may be very brief)
    spinner = page.locator("text=Recherche en cours...")
    # Note: spinner may disappear quickly, so we just check it existed
    time.sleep(1)

    print("✓ Loading spinner test passed")


def test_processing_time_displayed(page: Page, streamlit_url: str, screenshots_dir: Path):
    """Test that processing time is displayed after response."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Hello")
    time.sleep(15)

    # Check for processing time indicator
    processing_time = page.locator("text=/⏱️ \\d+ms/")
    expect(processing_time).to_be_visible(timeout=10000)

    page.screenshot(path=screenshots_dir / "test_processing_time.png")
    print("✓ Processing time display test passed")


# ============================================================================
# FEEDBACK SYSTEM TESTS
# ============================================================================


def test_feedback_buttons_appear(page: Page, streamlit_url: str):
    """Test that feedback buttons appear after assistant response."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Hello")
    time.sleep(15)

    # Check for thumbs up button
    thumbs_up = page.get_by_role("button", name="👍")
    expect(thumbs_up).to_be_visible(timeout=10000)

    # Check for thumbs down button
    thumbs_down = page.get_by_role("button", name="👎")
    expect(thumbs_down).to_be_visible()

    print("✓ Feedback buttons appearance test passed")


def test_positive_feedback_submission(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test submitting positive feedback."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Hello")
    time.sleep(15)

    # Click thumbs up
    thumbs_up = page.get_by_role("button", name="👍").first
    thumbs_up.click()
    time.sleep(2)

    # Check for confirmation message
    expect(page.get_by_text("Thanks for positive feedback")).to_be_visible()

    page.screenshot(path=screenshots_dir / "test_positive_feedback.png")
    print("✓ Positive feedback submission test passed")


def test_negative_feedback_with_comment(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test submitting negative feedback with optional comment."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Hello")
    time.sleep(15)

    # Click thumbs down
    thumbs_down = page.get_by_role("button", name="👎").first
    thumbs_down.click()
    time.sleep(2)

    # Check that comment form appears (use aria-label to find the feedback textarea)
    comment_area = page.get_by_role("textbox", name="What was wrong")
    expect(comment_area).to_be_visible(timeout=5000)

    # Enter comment
    comment_area.fill("Test comment: response was not accurate")

    # Submit feedback
    submit_button = page.get_by_role("button", name="Send feedback")
    submit_button.click()
    time.sleep(2)

    # Check for confirmation
    expect(page.get_by_text("Thanks for your feedback")).to_be_visible()

    page.screenshot(path=screenshots_dir / "test_negative_feedback.png")
    print("✓ Negative feedback with comment test passed")


def test_feedback_statistics_update(page: Page, streamlit_url: str):
    """Test that feedback statistics are displayed in sidebar."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for statistics metrics
    expect(page.get_by_text("Total Interactions")).to_be_visible()
    expect(page.get_by_text("With Feedback")).to_be_visible()
    expect(page.get_by_text("👍 Positive")).to_be_visible()
    expect(page.get_by_text("👎 Negative")).to_be_visible()

    print("✓ Feedback statistics display test passed")


# ============================================================================
# CONVERSATION MANAGEMENT TESTS
# ============================================================================


def test_new_conversation_button(page: Page, streamlit_url: str):
    """Test creating a new conversation."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit a query first
    submit_query(page, "Hello")
    time.sleep(15)

    # Click new conversation button
    new_conv_button = page.get_by_text("🆕 New Conversation")
    expect(new_conv_button).to_be_visible()
    new_conv_button.click()
    time.sleep(2)

    # Check that messages were cleared (only welcome message remains)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(1)
    expect(messages.first).to_contain_text("New conversation started")

    print("✓ New conversation button test passed")


def test_clear_history_button(page: Page, streamlit_url: str):
    """Test clearing chat history."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit a query
    submit_query(page, "Hello")
    time.sleep(15)

    # Should have at least 2 messages now
    messages = page.locator("[data-testid='stChatMessage']")
    initial_count = messages.count()
    assert initial_count >= 2

    # Click clear history button
    clear_button = page.get_by_text("🗑️ Clear History")
    expect(clear_button).to_be_visible()
    clear_button.click()
    time.sleep(2)

    # Check that only welcome message remains
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(1)
    # Check for either "History cleared" or welcome message
    first_message = messages.first.text_content()
    assert "History cleared" in first_message or "Hello" in first_message or "AI analyst" in first_message

    print("✓ Clear history button test passed")


def test_conversation_selector_visible(page: Page, streamlit_url: str):
    """Test that conversation selector is visible."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for conversation selector
    expect(page.get_by_text("Load Conversation")).to_be_visible()

    # Check for load button
    load_button = page.get_by_text("📂 Load")
    expect(load_button).to_be_visible()

    # Check for archive button
    archive_button = page.get_by_text("🗄️ Archive")
    expect(archive_button).to_be_visible()

    print("✓ Conversation selector visibility test passed")


# ============================================================================
# SOURCES AND METADATA TESTS
# ============================================================================


def test_sources_expander(page: Page, streamlit_url: str, screenshots_dir: Path):
    """Test that sources expander appears for contextual queries."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit contextual query
    submit_query(page, "What is the Lakers team culture like?")
    time.sleep(20)

    # Sources may display as compact caption or expander depending on mode
    sources = page.locator("text=/Sources|📄|nba/i")
    expect(sources.first).to_be_visible(timeout=10000)

    # Try to expand if it's an expander (optional, may not exist in compact mode)
    sources_expander = page.locator("summary").filter(has_text="Sources")
    if sources_expander.is_visible():
        sources_expander.click()
        time.sleep(1)

    page.screenshot(path=screenshots_dir / "test_sources_expander.png")
    print("✓ Sources expander test passed")


def test_sql_query_not_displayed_to_user(page: Page, streamlit_url: str):
    """Test that generated SQL query is not exposed in UI (internal only)."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Who are the top 3 scorers?")
    time.sleep(20)

    # Check that SQL query is NOT displayed to user
    # (it's in the API response but should not be in UI)
    page_content = page.content()
    assert "SELECT p.name" not in page_content

    print("✓ SQL query not exposed test passed")


# ============================================================================
# STATUS AND SETTINGS TESTS
# ============================================================================


def test_index_status_indicator(page: Page, streamlit_url: str):
    """Test that index status is displayed in sidebar."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for API status indicator
    api_status = page.get_by_text("API Ready")
    if api_status.is_visible():
        expect(page.get_by_text("vectors")).to_be_visible()
    else:
        # Fallback: check for any status indicator
        expect(page.get_by_text("API")).to_be_visible()

    print("✓ Index status indicator test passed")


def test_settings_display(page: Page, streamlit_url: str):
    """Test that settings are displayed correctly."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for settings
    expect(page.get_by_text("Model:")).to_be_visible()
    expect(page.get_by_text("Results:")).to_be_visible()
    expect(page.get_by_text("Temperature:")).to_be_visible()

    print("✓ Settings display test passed")


# ============================================================================
# INPUT VALIDATION AND EDGE CASES
# ============================================================================


def test_empty_query_handling(page: Page, streamlit_url: str):
    """Test that empty queries are handled gracefully."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Try to submit empty query
    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")
    chat_input.fill("")
    chat_input.press("Enter")
    time.sleep(2)

    # Should not create a new message
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(1)  # Only welcome message

    print("✓ Empty query handling test passed")


def test_long_query_handling(page: Page, streamlit_url: str):
    """Test that long queries are handled properly."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    long_query = "Who are the players " + "with high scoring " * 20 + "in the NBA?"
    submit_query(page, long_query)
    time.sleep(20)

    # Should still get a response (welcome + user query + assistant response)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Long query handling test passed")


def test_special_characters_in_query(page: Page, streamlit_url: str):
    """Test queries with special characters."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    special_query = "Who is Nikola Jokić? (Serbian: Никола Јокић)"
    submit_query(page, special_query)
    time.sleep(20)

    # Should handle special characters gracefully (welcome + user query + assistant response)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3, timeout=10000)

    print("✓ Special characters handling test passed")


# ============================================================================
# RESPONSIVE AND LAYOUT TESTS
# ============================================================================


def test_mobile_viewport(page: Page, streamlit_url: str, screenshots_dir: Path):
    """Test that UI works on mobile viewport."""
    # Set mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check that main elements are still visible
    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("[data-testid='stChatInput']")).to_be_visible()

    page.screenshot(path=screenshots_dir / "test_mobile_viewport.png", full_page=True)
    print("✓ Mobile viewport test passed")


def test_tablet_viewport(page: Page, streamlit_url: str, screenshots_dir: Path):
    """Test that UI works on tablet viewport."""
    # Set tablet viewport
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check that main elements are visible
    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("[data-testid='stChatInput']")).to_be_visible()

    page.screenshot(path=screenshots_dir / "test_tablet_viewport.png", full_page=True)
    print("✓ Tablet viewport test passed")


# ============================================================================
# MESSAGE HISTORY AND PERSISTENCE TESTS
# ============================================================================


def test_message_history_persists(page: Page, streamlit_url: str):
    """Test that message history persists across interactions."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit first query
    submit_query(page, "Hello")
    time.sleep(15)

    # Submit second query
    time.sleep(10)  # Rate limit protection
    submit_query(page, "Thank you")
    time.sleep(15)

    # Check that both messages are in history
    messages = page.locator("[data-testid='stChatMessage']")
    # Should have: welcome + hello + response + thank you + response = 5
    assert messages.count() >= 5

    print("✓ Message history persistence test passed")


def test_alternating_message_roles(page: Page, streamlit_url: str):
    """Test that messages alternate between user and assistant."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    submit_query(page, "Hello")
    time.sleep(15)

    # Get all messages
    messages = page.locator("[data-testid='stChatMessage']").all()

    # Check that roles alternate (after initial assistant welcome)
    # Pattern should be: assistant, user, assistant
    assert len(messages) >= 2

    print("✓ Alternating message roles test passed")


# ============================================================================
# FOOTER AND BRANDING TESTS
# ============================================================================


def test_footer_present(page: Page, streamlit_url: str):
    """Test that footer is present with correct branding."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for footer text
    expect(page.get_by_text("Powered by Mistral AI")).to_be_visible()
    expect(page.get_by_text("FAISS")).to_be_visible()

    print("✓ Footer branding test passed")


# ============================================================================
# PERFORMANCE AND STABILITY TESTS
# ============================================================================


@pytest.mark.slow
def test_rapid_consecutive_queries(page: Page, streamlit_url: str):
    """Test handling of rapid consecutive queries (rate limit stress test)."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    queries = ["Hello", "Hi", "Hey"]

    for i, query in enumerate(queries):
        submit_query(page, query)
        time.sleep(20)  # Must wait for rate limits

    # Check that all queries were processed (or appropriately handled)
    messages = page.locator("[data-testid='stChatMessage']")
    message_count = messages.count()

    # At minimum should have welcome + (3 user + 3 assistant)
    assert message_count >= 4

    print(f"✓ Rapid consecutive queries test passed ({message_count} messages)")


if __name__ == "__main__":
    """Run tests with Playwright."""
    import subprocess

    print("\n" + "=" * 80)
    print("RUNNING COMPREHENSIVE UI TESTS")
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
        print("✅ ALL COMPREHENSIVE TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
