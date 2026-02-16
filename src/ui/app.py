"""
FILE: app.py
STATUS: Active
RESPONSIBILITY: Streamlit chat interface with feedback collection and statistics
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import logging
import sys
from pathlib import Path

import streamlit as st
import requests

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.models.conversation import ConversationStatus
from src.ui.api_client import APIClient, ChatRequest as APIClientChatRequest

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@st.cache_data(ttl=60)
def get_cached_feedback_stats(_client: APIClient) -> dict:
    """Get cached feedback statistics (refreshes every 60 seconds).

    Args:
        _client: API client (prefixed with _ so Streamlit doesn't hash it)

    Returns:
        Feedback statistics dictionary
    """
    return _client.get_feedback_stats()


@st.cache_data(ttl=30)
def get_cached_health_status(_client: APIClient) -> dict:
    """Get cached health status (refreshes every 30 seconds).

    Args:
        _client: API client (prefixed with _ so Streamlit doesn't hash it)

    Returns:
        Health status dictionary
    """
    return _client.health_check()


@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client for HTTP communication with backend.

    Returns:
        Initialized APIClient
    """
    logger.info("Initializing API client...")
    return APIClient()


def render_message(role: str, content: str) -> None:
    """Render a chat message.

    Args:
        role: Message role (user or assistant)
        content: Message content
    """
    with st.chat_message(role):
        st.write(content)


def render_sources(sources: list, compact: bool = True) -> None:
    """Render source documents.

    Args:
        sources: List of source dicts with 'source', 'score', 'text'
        compact: If True, show compact format at bottom. If False, show expander with full details.
    """
    if not sources:
        return

    # Extract unique source names (handles duplicates)
    source_names = []
    seen = set()
    for source in sources:
        source_name = source.get("source") if isinstance(source, dict) else getattr(source, "source", "Unknown")
        # Clean up source name (remove .pdf, file paths, etc.)
        clean_name = source_name.replace(".pdf", "").replace("_", " ").strip()
        if clean_name and clean_name not in seen:
            source_names.append(clean_name)
            seen.add(clean_name)

    if compact:
        # Compact format: single line with small text at bottom
        sources_text = ", ".join(source_names)
        st.caption(f"📚 Sources: {sources_text}")
    else:
        # Detailed format: expander with full information
        with st.expander(f"📚 Sources ({len(sources)})"):
            for i, source in enumerate(sources, 1):
                # Handle both dict and object responses
                source_name = source.get("source") if isinstance(source, dict) else getattr(source, "source", "Unknown")
                score = source.get("score", 0) if isinstance(source, dict) else getattr(source, "score", 0)
                text = source.get("text", "") if isinstance(source, dict) else getattr(source, "text", "")

                st.markdown(f"**{i}. {source_name}** (Score: {score:.1f}%)")
                st.caption(text[:300] + "..." if len(text) > 300 else text)
                st.divider()


def get_user_friendly_error_message(error: Exception) -> str:
    """Convert API errors to user-friendly messages.

    Args:
        error: The exception that occurred

    Returns:
        User-friendly error message
    """
    error_str = str(error).lower()

    if "429" in error_str or "rate limit" in error_str:
        return "⚠️ The AI service is busy due to high demand. Please try again in 1 minute."

    if "500" in error_str or "internal server error" in error_str:
        return "⚠️ The AI service encountered an issue. Please try again in a moment."

    if "timeout" in error_str:
        return "⏱️ Request took too long. Please try again with a simpler question."

    if "connection" in error_str:
        return "❌ Cannot connect to the API server. Make sure it's running on http://localhost:8000"

    if "404" in error_str:
        return "❌ API endpoint not found. Check server configuration."

    return f"⚠️ An error occurred. Please try again: {str(error)[:100]}"


def render_feedback_buttons(interaction_id: str, index: int, client: APIClient) -> None:
    """Render feedback buttons for an interaction.

    Args:
        interaction_id: ID of the chat interaction
        index: Index for unique key generation
        client: API client for submitting feedback
    """
    feedback_key = f"feedback_{interaction_id}"
    comment_key = f"comment_{interaction_id}"

    # Check if feedback already given
    if feedback_key in st.session_state:
        existing = st.session_state[feedback_key]
        if existing == "positive":
            st.success("👍 Thanks for positive feedback!")
        else:
            st.info("👎 Thanks for your feedback.")
        return

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("👍", key=f"pos_{index}_{interaction_id}", help="Good answer"):
            try:
                client.submit_feedback(
                    interaction_id=interaction_id,
                    rating="POSITIVE",
                )
                st.session_state[feedback_key] = "positive"
                st.rerun()
            except Exception as e:
                logger.warning("Feedback error: %s", e)
                st.error("Failed to submit feedback")

    with col2:
        if st.button("👎", key=f"neg_{index}_{interaction_id}", help="Bad answer"):
            st.session_state[f"show_comment_{interaction_id}"] = True
            st.rerun()

    # Show comment input for negative feedback
    if st.session_state.get(f"show_comment_{interaction_id}"):
        with st.form(key=f"comment_form_{interaction_id}"):
            comment = st.text_area(
                "What was wrong with this answer? (optional)",
                key=comment_key,
                max_chars=2000,
            )
            submitted = st.form_submit_button("Send feedback")

            if submitted:
                try:
                    client.submit_feedback(
                        interaction_id=interaction_id,
                        rating="NEGATIVE",
                        comment=comment if comment.strip() else None,
                    )
                    st.session_state[feedback_key] = "negative"
                    st.session_state.pop(f"show_comment_{interaction_id}", None)
                    st.rerun()
                except Exception as e:
                    logger.warning("Feedback error: %s", e)
                    st.error("Failed to submit feedback")


def render_conversation_controls(client: APIClient) -> None:
    """Render conversation management controls in sidebar.

    Args:
        client: API client for conversation management
    """
    st.subheader("Conversations")

    # New Conversation button
    if st.button("🆕 New Conversation", use_container_width=True):
        try:
            new_conv = client.start_conversation()
            st.session_state.current_conversation_id = new_conv["id"]
            st.session_state.turn_number = 1
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "New conversation started! How can I help?",
                    "interaction_id": None,
                }
            ]
            st.rerun()
        except Exception as e:
            logger.error("Error creating conversation: %s", e)
            st.error("Failed to create conversation")
            return

    # Load existing conversations
    try:
        conversations = client.list_conversations(
            status="active",
            limit=20
        )

        if conversations:
            # Current conversation indicator + rename option
            current_id = st.session_state.get("current_conversation_id")
            if current_id:
                # Find current conversation from list (avoid N+1 query)
                current_conv = next(
                    (c for c in conversations if (c.get("id") if isinstance(c, dict) else c.id) == current_id),
                    None
                )
                if current_conv:
                    title = current_conv.get("title", "Untitled") if isinstance(current_conv, dict) else getattr(current_conv, "title", "Untitled")
                    st.caption(f"📌 Current: {title}")

                    # Rename conversation
                    with st.expander("✏️ Rename Conversation"):
                        new_title = st.text_input(
                            "New title:",
                            value=title if title != "Untitled" else "",
                            placeholder="Give this conversation a name..."
                        )
                        if st.button("Rename", key="rename_btn"):
                            try:
                                client.update_conversation(current_id, title=new_title)
                                st.success(f"✅ Renamed to: {new_title}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to rename: {e}")

            # Conversation selector
            st.selectbox(
                "Load Conversation",
                options=[""] + [c["id"] if isinstance(c, dict) else c.id for c in conversations],
                format_func=lambda x: "Select..." if x == "" else next(
                    (
                        (c["title"] or f"Conversation {c['id'][:8]}..." if isinstance(c, dict) else c.title or f"Conversation {c.id[:8]}...")
                        for c in conversations
                        if (c["id"] if isinstance(c, dict) else c.id) == x
                    ),
                    x,
                ),
                key="conversation_selector",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📂 Load", disabled=not st.session_state.get("conversation_selector")):
                    conv_id = st.session_state.conversation_selector
                    try:
                        history = client.get_conversation_history(conv_id)
                        if history:
                            # Load conversation messages
                            st.session_state.current_conversation_id = conv_id
                            messages_list = history.get("messages", []) if isinstance(history, dict) else getattr(history, "messages", [])
                            st.session_state.turn_number = len(messages_list) + 1
                            title = history.get("title", "Untitled") if isinstance(history, dict) else getattr(history, "title", "Untitled")
                            st.session_state.messages = [
                                {
                                    "role": "assistant",
                                    "content": f"Conversation loaded: {title}",
                                    "interaction_id": None,
                                }
                            ]
                            # Add all previous messages
                            for msg in messages_list:
                                query = msg.get("query") if isinstance(msg, dict) else getattr(msg, "query", "")
                                response = msg.get("response") if isinstance(msg, dict) else getattr(msg, "response", "")
                                msg_id = msg.get("id") if isinstance(msg, dict) else getattr(msg, "id", None)

                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": query,
                                    "interaction_id": None,
                                })
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response,
                                    "interaction_id": msg_id,
                                })
                            st.rerun()
                    except Exception as e:
                        logger.error("Error loading conversation: %s", e)
                        st.error("Failed to load conversation")

            with col2:
                if st.button("🗄️ Archive", disabled=not current_id):
                    if current_id:
                        try:
                            client.archive_conversation(current_id)
                            st.session_state.pop("current_conversation_id", None)
                            st.session_state.turn_number = 1
                            st.session_state.messages = [
                                {
                                    "role": "assistant",
                                    "content": "Conversation archived. Start a new one!",
                                    "interaction_id": None,
                                }
                            ]
                            st.rerun()
                        except Exception as e:
                            logger.error("Error archiving conversation: %s", e)
                            st.error("Failed to archive conversation")

    except Exception as e:
        logger.error("Error loading conversations: %s", e)
        st.error("Error loading conversations")


def main() -> None:
    """Main Streamlit application."""
    # Page configuration
    st.set_page_config(
        page_title=settings.app_title,
        page_icon="🏀",
        layout="centered",
    )

    # Header
    st.title(f"🏀 {settings.app_title}")
    st.caption(f"AI Assistant for {settings.app_name} | Model: {settings.chat_model}")

    # Welcome message
    st.markdown(
        """
    ---
    **Welcome! 🎉**

    Drop your {app_name} questions anytime - we'll dig up the stats, the drama, the highlights.
    No question too random. (Well, *almost* no question too random.) 😎
    """.format(app_name=settings.app_name)
    )
    st.markdown("---")

    # Get API client
    client = get_api_client()

    # Check API health (cached, refreshes every 30 seconds)
    try:
        health = get_cached_health_status(client)
        is_healthy = health.get("status") == "healthy"
        index_size = health.get("index_size", 0)
    except Exception as e:
        logger.error("API health check failed: %s", e)
        st.error(f"❌ Cannot connect to API. Is it running on http://localhost:8000?")
        st.stop()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Hello! I'm your AI analyst for {settings.app_name}. "
                "Ask me about teams, players, or statistics.",
                "interaction_id": None,
            }
        ]

    # Initialize conversation tracking
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    if "turn_number" not in st.session_state:
        st.session_state.turn_number = 1

    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        render_message(message["role"], message["content"])

        # Show feedback buttons for assistant messages with interaction_id
        if message["role"] == "assistant" and message.get("interaction_id"):
            render_feedback_buttons(message["interaction_id"], i, client)

    # Chat input
    if prompt := st.chat_input(f"Ask about {settings.app_name}..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "interaction_id": None,
        })
        render_message("user", prompt)

        # Check if index is loaded
        # TEMPORARY: Health check disabled - API is working despite false health report
        # TODO: Fix health endpoint to correctly report vector store status
        # if not is_healthy:
        #     error_msg = "⚠️ Vector index not loaded. Run `poetry run python src/indexer.py` to build the knowledge base."
        #     st.session_state.messages.append({
        #         "role": "assistant",
        #         "content": error_msg,
        #         "interaction_id": None,
        #     })
        #     render_message("assistant", error_msg)
        #     st.stop()

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                try:
                    import time as time_module

                    # Auto-create conversation on first message
                    if st.session_state.current_conversation_id is None:
                        try:
                            new_conv = client.start_conversation()
                            st.session_state.current_conversation_id = new_conv["id"]
                            st.session_state.turn_number = 1
                            logger.info(f"Created new conversation: {new_conv['id']}")
                        except Exception as e:
                            logger.warning(f"Could not create conversation: {e}")

                    # Create request
                    api_request = APIClientChatRequest(
                        query=prompt,
                        k=settings.search_k,
                        include_sources=True,
                        conversation_id=st.session_state.current_conversation_id,
                        turn_number=st.session_state.turn_number,
                    )

                    # Get response from API
                    logger.info(f"[UI-DEBUG] Calling API /chat for query: '{prompt}'")
                    start_time = time_module.time()
                    response = client.chat(api_request)
                    elapsed = time_module.time() - start_time
                    logger.info(f"[UI-DEBUG] API /chat returned in {elapsed:.2f}s")

                    # Extract response data
                    answer = response.get("answer", "") if isinstance(response, dict) else getattr(response, "answer", "")
                    sources = response.get("sources", []) if isinstance(response, dict) else getattr(response, "sources", [])
                    processing_time_ms = response.get("processing_time_ms", 0) if isinstance(response, dict) else getattr(response, "processing_time_ms", 0)
                    visualization = response.get("visualization") if isinstance(response, dict) else getattr(response, "visualization", None)

                    logger.info(f"[UI-DEBUG] Response answer length: {len(answer)}")
                    logger.info(f"[UI-DEBUG] Response sources count: {len(sources)}")
                    logger.info(f"[UI-DEBUG] Has visualization: {visualization is not None}")

                    # Display answer (Phase 18: Use markdown to render superscript citations)
                    logger.info(f"[UI-DEBUG] About to display answer")
                    st.markdown(answer, unsafe_allow_html=True)
                    logger.info(f"[UI-DEBUG] Answer displayed successfully")

                    # Display visualization if available (statistical queries)
                    if visualization:
                        logger.info(f"[UI-DEBUG] Displaying visualization")
                        try:
                            viz_data = visualization if isinstance(visualization, dict) else {
                                "plot_json": getattr(visualization, "plot_json", None),
                                "plot_html": getattr(visualization, "plot_html", None),
                                "pattern": getattr(visualization, "pattern", "unknown"),
                                "viz_type": getattr(visualization, "viz_type", "unknown"),
                            }

                            # Try to display interactive Plotly chart
                            if viz_data.get("plot_json"):
                                import plotly.io as pio
                                import json

                                # Parse JSON if it's a string
                                plot_data = viz_data["plot_json"]
                                if isinstance(plot_data, str):
                                    plot_data = json.loads(plot_data)

                                # Create and display Plotly figure
                                fig = pio.from_json(json.dumps(plot_data))
                                st.plotly_chart(fig, use_container_width=True)
                                logger.info(f"[UI-DEBUG] Visualization displayed successfully ({viz_data.get('viz_type', 'unknown')})")
                            elif viz_data.get("plot_html"):
                                # Fallback: display as HTML
                                st.components.v1.html(viz_data["plot_html"], height=500)
                                logger.info(f"[UI-DEBUG] Visualization (HTML) displayed successfully")
                        except Exception as e:
                            logger.warning(f"[UI-DEBUG] Could not display visualization: {e}")
                            # Continue without visualization - don't break the response

                    # Display ReAct agent reasoning trace
                    reasoning_trace = response.get("reasoning_trace", []) if isinstance(response, dict) else getattr(response, "reasoning_trace", [])
                    tools_used = response.get("tools_used", []) if isinstance(response, dict) else getattr(response, "tools_used", [])

                    if reasoning_trace:
                        with st.expander("🧠 View Agent Reasoning", expanded=False):
                            st.markdown("**Agent Reasoning Steps:**")

                            for i, step in enumerate(reasoning_trace, 1):
                                st.markdown(f"### Step {i}")
                                st.markdown(f"**💭 Thought**: {step.get('thought', 'N/A')}")
                                st.markdown(f"**⚡ Action**: `{step.get('action', 'N/A')}`")

                                # Display action input
                                action_input = step.get('action_input', {})
                                if action_input:
                                    import json
                                    st.code(json.dumps(action_input, indent=2), language="json")

                                # Display observation (truncated)
                                observation = step.get('observation', 'N/A')
                                if len(observation) > 500:
                                    observation = observation[:500] + "..."
                                st.markdown(f"**👁️ Observation**: {observation}")
                                st.divider()

                            # Show tools used summary
                            if tools_used:
                                st.info(f"🛠️ **Tools used**: {', '.join(tools_used)}")

                    # Display sources
                    logger.info(f"[UI-DEBUG] About to render sources")
                    render_sources(sources)
                    logger.info(f"[UI-DEBUG] Sources rendered successfully")

                    # Display processing time
                    logger.info(f"[UI-DEBUG] About to display processing time")
                    st.caption(f"⏱️ {processing_time_ms:.0f}ms")
                    logger.info(f"[UI-DEBUG] Processing time displayed successfully")

                    # Log interaction to database
                    logger.info(f"[UI-DEBUG] About to log interaction to database")
                    source_names = [s.get("source") if isinstance(s, dict) else getattr(s, "source", "") for s in sources]
                    try:
                        interaction = client.log_interaction(
                            query=prompt,
                            response=answer,
                            sources=source_names,
                            processing_time_ms=int(processing_time_ms),
                        )
                        interaction_id = interaction.get("id") if isinstance(interaction, dict) else getattr(interaction, "id", None)
                        logger.info(f"[UI-DEBUG] Interaction logged with id: {interaction_id}")
                    except Exception as e:
                        logger.warning(f"Could not log interaction: {e}")
                        interaction_id = None

                    # Increment turn number for next message
                    st.session_state.turn_number += 1
                    logger.info(f"[UI-DEBUG] Turn number incremented to {st.session_state.turn_number}")

                    # Add to history with interaction_id
                    logger.info(f"[UI-DEBUG] About to add message to session state")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "interaction_id": interaction_id,
                    })
                    logger.info(f"[UI-DEBUG] Message added to session state")

                    # Display feedback buttons
                    logger.info(f"[UI-DEBUG] About to render feedback buttons")
                    if interaction_id:
                        render_feedback_buttons(interaction_id, len(st.session_state.messages) - 1, client)
                    logger.info(f"[UI-DEBUG] Feedback buttons rendered successfully")

                except requests.exceptions.Timeout:
                    logger.error("API timeout - request took too long")
                    error_msg = "⏱️ Request timed out. The server is taking too long to respond. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "interaction_id": None,
                except requests.exceptions.ConnectionError:
                    logger.error("API connection error - cannot reach server")
                    error_msg = "🔌 Cannot reach the API server. Please check your connection and try again."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "interaction_id": None,
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from API: {e}")
                    error_msg = "⚠️ Received invalid response from server. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "interaction_id": None,
                except Exception as e:
                    logger.exception(f"Unexpected API error: {e}")
                    error_msg = get_user_friendly_error_message(e)
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "interaction_id": None,
                    })

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # Display service status
        if is_healthy:
            st.success(f"✅ API Ready ({index_size} vectors)")
        else:
            st.warning("⚠️ API Degraded")

        st.divider()

        # Conversation controls
        render_conversation_controls(client)

        st.divider()

        # Settings display
        st.subheader("Settings")
        st.text(f"Model: {settings.chat_model}")
        st.text(f"Results: {settings.search_k}")
        st.text(f"Temperature: {settings.temperature}")
        st.text(f"API: http://localhost:8000")

        st.divider()

        # Feedback statistics (cached, refreshes every 60 seconds)
        st.subheader("Feedback Stats")
        try:
            stats = get_cached_feedback_stats(client)
            total_interactions = stats.get("total_interactions", 0) if isinstance(stats, dict) else getattr(stats, "total_interactions", 0)
            total_feedback = stats.get("total_feedback", 0) if isinstance(stats, dict) else getattr(stats, "total_feedback", 0)
            positive_count = stats.get("positive_count", 0) if isinstance(stats, dict) else getattr(stats, "positive_count", 0)
            negative_count = stats.get("negative_count", 0) if isinstance(stats, dict) else getattr(stats, "negative_count", 0)
            positive_rate = stats.get("positive_rate", 0) if isinstance(stats, dict) else getattr(stats, "positive_rate", 0)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Interactions", total_interactions)
                st.metric("👍 Positive", positive_count)
            with col2:
                st.metric("With Feedback", total_feedback)
                st.metric("👎 Negative", negative_count)

            if total_feedback > 0:
                st.progress(positive_rate / 100, text=f"Positive Rate: {positive_rate}%")
        except Exception as e:
            logger.error("Error getting feedback stats: %s", e)
            st.warning("Could not load feedback stats")

        st.divider()

        # Clear chat button
        if st.button("🗑️ Clear History"):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "History cleared. How can I help?",
                    "interaction_id": None,
                }
            ]
            st.rerun()

    # Footer
    st.markdown("---")
    st.caption("🔗 Connected to API | Powered by Mistral AI & FAISS")


if __name__ == "__main__":
    main()
