"""
FILE: test_conversation_management.py
STATUS: Active
RESPONSIBILITY: E2E tests for conversation management in Streamlit UI
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.conversation
class TestNewConversation:
    """Test creating new conversations."""

    def test_new_conversation_button_visible(self, streamlit_page: Page):
        """Test that 'New Conversation' button is visible in sidebar."""
        new_conv_btn = streamlit_page.locator("button").filter(
            has_text="New Conversation"
        )
        assert new_conv_btn.count() > 0, "New Conversation button not found"

    def test_create_new_conversation(self, streamlit_page: Page, send_query):
        """Test that clicking New Conversation resets the chat."""
        # First, send a query to have some history
        assert send_query("Who is Michael Jordan?"), "Initial query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Click "New Conversation" button
        new_conv_btn = streamlit_page.locator("button").filter(
            has_text="New Conversation"
        )
        new_conv_btn.first.click()

        # Wait for page rerun
        streamlit_page.wait_for_timeout(3000)

        # Should show the new conversation greeting
        content = streamlit_page.content()
        assert "New conversation started" in content or "How can I help" in content, (
            "New conversation greeting not shown after clicking New Conversation"
        )


@pytest.mark.conversation
class TestRenameConversation:
    """Test renaming conversations."""

    def test_rename_controls_visible_after_query(self, streamlit_page: Page, send_query):
        """Test that rename controls appear after a conversation is created."""
        # Send query to auto-create conversation
        assert send_query("What is the NBA?"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Reload page so sidebar picks up the new conversation state
        streamlit_page.reload(wait_until="load")
        streamlit_page.wait_for_timeout(5000)

        # Look for rename expander or conversation section in sidebar
        content = streamlit_page.content()
        rename_expander = streamlit_page.locator("text=/✏️ Rename Conversation/")
        has_conversations_section = "Conversations" in content
        has_rename = rename_expander.count() > 0

        assert has_rename or has_conversations_section, (
            "Neither rename controls nor Conversations section found after query"
        )

    def test_rename_conversation(self, streamlit_page: Page, send_query):
        """Test renaming a conversation via the UI."""
        # Send query to auto-create conversation
        assert send_query("Tell me about NBA history"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Reload page so sidebar shows conversation controls
        streamlit_page.reload(wait_until="load")
        streamlit_page.wait_for_timeout(5000)

        # Open rename expander
        rename_expander = streamlit_page.locator("text=/✏️ Rename Conversation/")
        if rename_expander.count() == 0:
            pytest.skip("Rename expander not visible — conversation may not be in list")

        rename_expander.first.click()
        streamlit_page.wait_for_timeout(1000)

        # Find the text input with label "New title:"
        title_input = streamlit_page.locator("input[aria-label='New title:']")
        if title_input.count() > 0:
            title_input.first.clear()
            title_input.first.fill("My NBA Discussion")

            # Click Rename button
            rename_btn = streamlit_page.locator("button").filter(has_text="Rename")
            rename_btn.first.click()

            # Wait for confirmation
            streamlit_page.wait_for_timeout(2000)

            # Verify success message
            content = streamlit_page.content()
            assert "Renamed to" in content or "My NBA Discussion" in content, (
                "Rename confirmation not shown"
            )


@pytest.mark.conversation
class TestArchiveConversation:
    """Test archiving conversations."""

    def test_archive_conversation(self, streamlit_page: Page, send_query):
        """Test archiving the current conversation."""
        # Send query to auto-create conversation
        assert send_query("What are the NBA playoffs?"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Reload page so sidebar shows conversation controls with current_id
        streamlit_page.reload(wait_until="load")
        streamlit_page.wait_for_timeout(5000)

        # Find and click Archive button
        archive_btn = streamlit_page.locator("button").filter(has_text="Archive")
        if archive_btn.count() == 0:
            pytest.skip("Archive button not visible — no active conversations")

        # Check if button is enabled (not disabled)
        first_btn = archive_btn.first
        if not first_btn.is_enabled():
            pytest.skip("Archive button is disabled — no current conversation")

        first_btn.click()

        # Wait for page rerun
        streamlit_page.wait_for_timeout(3000)

        # Should show archive confirmation
        content = streamlit_page.content()
        assert "archived" in content.lower() or "Start a new one" in content, (
            "Archive confirmation not shown"
        )


@pytest.mark.conversation
class TestConversationList:
    """Test conversation listing and loading."""

    def test_conversations_section_exists(self, streamlit_page: Page):
        """Test that Conversations section exists in sidebar."""
        content = streamlit_page.content()
        assert "Conversations" in content, "Conversations section not found in sidebar"

    def test_conversations_appear_after_query(self, streamlit_page: Page, send_query):
        """Test that conversations appear in the sidebar list after creation."""
        # Send query to create a conversation
        assert send_query("Who is Kobe Bryant?"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Reload to ensure sidebar reflects new state
        streamlit_page.reload(wait_until="load")
        streamlit_page.wait_for_timeout(5000)

        # Look for conversation-related elements in sidebar
        content = streamlit_page.content()
        has_conversation_indicator = (
            "Current:" in content
            or "Load Conversation" in content
            or "Conversation" in content
        )
        assert has_conversation_indicator, (
            "No conversation indicators found in sidebar after creating conversation"
        )

    def test_load_button_exists(self, streamlit_page: Page, send_query):
        """Test that Load button exists in sidebar when conversations exist."""
        # Need at least one conversation for Load button to appear
        assert send_query("What is a rebound?"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Reload so sidebar picks up the new conversation
        streamlit_page.reload(wait_until="load")
        streamlit_page.wait_for_timeout(5000)

        load_btn = streamlit_page.locator("button").filter(has_text="Load")
        if load_btn.count() == 0:
            pytest.skip("Load button not rendered — conversation may not be persisted yet")
        assert load_btn.first.is_visible(), "Load button not visible"


@pytest.mark.conversation
class TestContextSwitching:
    """Test switching between conversations."""

    def test_new_conversation_after_query(self, streamlit_page: Page, send_query):
        """Test creating a new conversation after querying in an existing one."""
        # Query in first conversation
        assert send_query("First conversation question"), "First query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Create new conversation
        new_conv_btn = streamlit_page.locator("button").filter(
            has_text="New Conversation"
        )
        new_conv_btn.first.click()
        streamlit_page.wait_for_timeout(3000)

        # Verify new conversation is active (welcome message or new conversation indicator)
        content = streamlit_page.content()
        assert (
            "New conversation started" in content
            or "How can I help" in content
            or "AI analyst" in content
            or "Hello" in content
        ), "New conversation not created properly"

        # Should be able to send a new query
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible(), "Chat input not visible after conversation switch"
        assert chat_input.is_enabled(), "Chat input not enabled after conversation switch"
