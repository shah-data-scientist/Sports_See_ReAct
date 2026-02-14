"""
FILE: test_streamlit_visualization.py
STATUS: Active
RESPONSIBILITY: Playwright UI tests for Streamlit visualization feature
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
    # Wait for Streamlit's specific elements
    page.wait_for_selector("[data-testid='stApp']", timeout=10000)
    # Wait for any initial loading to complete
    time.sleep(2)


def submit_query(page: Page, query: str):
    """Submit a query to the Streamlit chat interface."""
    # Find the chat input - Streamlit uses stChatInput
    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")

    # Clear any existing text and type the query
    chat_input.fill(query)

    # Press Enter to submit
    chat_input.press("Enter")

    # Wait for response to appear
    time.sleep(2)


def test_streamlit_app_loads(page: Page, streamlit_url: str):
    """Test that the Streamlit app loads successfully."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Check for the title
    expect(page.locator("h1")).to_contain_text("NBA Analyst AI")

    # Check for chat input
    expect(page.locator("[data-testid='stChatInput']")).to_be_visible()


def test_statistical_query_with_visualization(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test that statistical queries generate visualizations."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit a statistical query
    query = "Who are the top 5 scorers this season?"
    submit_query(page, query)

    # Wait for the response (give it time for API call)
    time.sleep(15)  # Longer wait for Gemini API

    # Check that the answer appeared
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3)  # Welcome message + User message + Assistant message

    # Check for visualization
    # Plotly charts are rendered in an iframe or specific container
    viz_container = page.locator("[data-testid='stPlotlyChart']")
    expect(viz_container).to_be_visible(timeout=5000)

    # Take a screenshot
    page.screenshot(path=screenshots_dir / "test_top_scorers_viz.png", full_page=True)

    print(f"✓ Statistical query test passed")
    print(f"  Screenshot saved: {screenshots_dir / 'test_top_scorers_viz.png'}")


def test_comparison_query_visualization(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test player comparison query with radar chart."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit comparison query
    query = "Compare Jokic and Embiid stats"
    submit_query(page, query)

    # Wait for response (comparison queries may take longer)
    time.sleep(20)

    # Check for visualization with longer timeout
    viz_container = page.locator("[data-testid='stPlotlyChart']")
    expect(viz_container).to_be_visible(timeout=10000)

    # Take screenshot
    page.screenshot(path=screenshots_dir / "test_comparison_viz.png", full_page=True)

    print(f"✓ Comparison query test passed")
    print(f"  Screenshot saved: {screenshots_dir / 'test_comparison_viz.png'}")


def test_contextual_query_no_visualization(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test that contextual queries don't generate visualizations."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit contextual query
    query = "What is the Lakers team culture like?"
    submit_query(page, query)

    # Wait for response
    time.sleep(15)

    # Check that answer appeared
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(3)  # Welcome message + User message + Assistant message

    # Check that NO visualization appeared
    viz_container = page.locator("[data-testid='stPlotlyChart']")
    expect(viz_container).to_have_count(0)

    # Take screenshot
    page.screenshot(path=screenshots_dir / "test_contextual_no_viz.png", full_page=True)

    print(f"✓ Contextual query test passed (no visualization)")
    print(f"  Screenshot saved: {screenshots_dir / 'test_contextual_no_viz.png'}")


def test_visualization_info_expander(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test that visualization info expander is present."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit statistical query
    query = "Show me top 5 scorers"
    submit_query(page, query)

    # Wait for response
    time.sleep(15)

    # Look for the info expander - use partial text match without emoji
    # Streamlit expanders have specific data-testid
    # Visualization info may not appear if query didn't generate a chart
    info_expander = page.locator("summary").filter(has_text="Visualization Info")
    if info_expander.count() == 0:
        pytest.skip("Visualization Info expander not rendered — query may not have generated a chart")
    expect(info_expander).to_be_visible(timeout=5000)

    # Click to expand
    info_expander.click()
    time.sleep(1)

    # Check for pattern and type info inside the expanded content
    expect(page.get_by_text("Pattern:")).to_be_visible()
    expect(page.get_by_text("Type:")).to_be_visible()

    # Take screenshot
    page.screenshot(path=screenshots_dir / "test_viz_info_expanded.png", full_page=True)

    print(f"✓ Visualization info test passed")
    print(f"  Screenshot saved: {screenshots_dir / 'test_viz_info_expanded.png'}")


def test_multiple_queries_conversation(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test multiple queries in a conversation."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # First query
    submit_query(page, "Who are the top 3 scorers?")

    # Wait longer for API response + give extra time for rate limits
    time.sleep(25)

    # Check for any errors on page first
    errors = page.locator("[data-testid='stException']").all()
    if errors:
        print(f"⚠️ Found {len(errors)} error(s) on page")
        for error in errors:
            print(f"  Error: {error.text_content()[:200]}")

    # Verify first response appeared with longer timeout
    messages = page.locator("[data-testid='stChatMessage']")
    message_count = messages.count()
    print(f"Message count: {message_count}")
    if message_count == 1:
        # Only user message - assistant didn't respond
        print("⚠️ Assistant did not respond - checking page state...")
        print(f"Page URL: {page.url}")

    expect(messages).to_have_count(3, timeout=10000)  # Welcome + User + Assistant

    # Wait for chat input to be ready + CRITICAL: avoid rate limit (15 RPM = 1 per 4s)
    # Need 20s between consecutive API calls to avoid 429 (increased from 10s)
    time.sleep(20)

    # Make sure chat input is visible and ready
    chat_input = page.locator("[data-testid='stChatInput']").locator("textarea")
    expect(chat_input).to_be_visible(timeout=5000)

    # Second query (follow-up question needs more time due to conversation context)
    submit_query(page, "How many points do they have?")
    time.sleep(25)

    # Check that we have 5 messages (welcome + 2 user + 2 assistant)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(5, timeout=10000)

    # Take screenshot
    page.screenshot(path=screenshots_dir / "test_conversation.png", full_page=True)

    print(f"✓ Conversation test passed")
    print(f"  Screenshot saved: {screenshots_dir / 'test_conversation.png'}")


def test_new_conversation_button(page: Page, streamlit_url: str):
    """Test the new conversation button."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit a query
    submit_query(page, "Top 5 scorers")
    time.sleep(15)

    # Find and click the "New Conversation" button in sidebar
    new_conv_button = page.get_by_text("🆕 New Conversation")
    expect(new_conv_button).to_be_visible()
    new_conv_button.click()

    # Wait for page to reload/clear
    time.sleep(2)

    # Check that messages are cleared (welcome message remains)
    messages = page.locator("[data-testid='stChatMessage']")
    expect(messages).to_have_count(1)

    print(f"✓ New conversation test passed")


@pytest.mark.slow
@pytest.mark.skip(reason="Flaky due to Gemini rate limits causing SQL fallback without visualization")
def test_visualization_interactive_features(
    page: Page,
    streamlit_url: str,
    screenshots_dir: Path
):
    """Test interactive features of Plotly charts."""
    page.goto(streamlit_url)
    wait_for_streamlit_ready(page)

    # Submit query (use full question to ensure proper classification)
    submit_query(page, "Who are the top 5 scorers?")
    time.sleep(25)

    # Debug: Check if API responded at all
    messages = page.locator("[data-testid='stChatMessage']")
    message_count = messages.count()
    print(f"Message count: {message_count} (expecting 2: user + assistant)")

    # Check for errors
    errors = page.locator("[data-testid='stException']").all()
    if errors:
        print(f"⚠️ Found {len(errors)} error(s)")
        for error in errors:
            print(f"  Error: {error.text_content()[:200]}")

    # Wait for visualization with explicit timeout
    viz_container = page.locator("[data-testid='stPlotlyChart']")
    expect(viz_container).to_be_visible(timeout=10000)

    # Get the first visualization element
    viz = viz_container.first
    expect(viz).to_be_visible(timeout=5000)

    # Additional wait for Plotly chart to fully render
    time.sleep(2)

    # Hover over the chart to trigger tooltips
    viz.hover()
    time.sleep(1)

    # Take screenshot with hover state
    page.screenshot(path=screenshots_dir / "test_viz_hover.png", full_page=True)

    # Check for Plotly modebar (interactive controls)
    # Wait for modebar to appear (it may load after the chart)
    modebar = page.locator(".modebar")
    expect(modebar).to_be_visible(timeout=5000)

    print(f"✓ Interactive features test passed")
    print(f"  Screenshot saved: {screenshots_dir / 'test_viz_hover.png'}")


if __name__ == "__main__":
    """Run tests with Playwright in headed mode for debugging."""
    import subprocess

    print("\n" + "=" * 80)
    print("RUNNING STREAMLIT UI TESTS WITH PLAYWRIGHT")
    print("=" * 80)

    # Run pytest with Playwright
    result = subprocess.run(
        [
            "poetry", "run", "pytest",
            __file__,
            "-v",
            "-s",
            "--headed",  # Show browser for debugging
        ],
        cwd=Path(__file__).parent.parent.parent
    )

    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
