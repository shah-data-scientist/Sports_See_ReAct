"""
FILE: streamlit_viz_example.py
STATUS: Experimental
RESPONSIBILITY: Example Streamlit app showing API visualization integration
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

USAGE:
    poetry run streamlit run streamlit_viz_example.py
"""

import json

import requests
import streamlit as st
import plotly.graph_objects as go

# Configuration
API_URL = "http://localhost:8002/api/v1/chat"

st.set_page_config(
    page_title="NBA Chat with Visualizations",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 NBA Sports Analysis Chatbot")
st.markdown("Ask questions about NBA stats and get visual answers!")

# Initialize session state for conversation
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "turn_number" not in st.session_state:
    st.session_state.turn_number = 1
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display visualization if present
        if "visualization" in message and message["visualization"]:
            st.markdown("---")
            st.markdown("**📊 Visualization:**")

            # Option 1: Using plot_json (recommended)
            try:
                fig = go.Figure(json.loads(message["visualization"]["plot_json"]))
                st.plotly_chart(fig, use_container_width=True, key=f"viz_{message['timestamp']}")

                # Show pattern info
                with st.expander("ℹ️ Visualization Info"):
                    st.write(f"**Pattern:** {message['visualization']['pattern']}")
                    st.write(f"**Type:** {message['visualization']['viz_type']}")
            except Exception as e:
                st.error(f"Failed to render visualization: {e}")

# Chat input
if prompt := st.chat_input("Ask about NBA stats..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": st.session_state.turn_number
    })

    # Call API
    try:
        with st.spinner("Thinking..."):
            payload = {
                "query": prompt,
                "k": 5,
                "include_sources": True,
            }

            # Include conversation context if exists
            if st.session_state.conversation_id:
                payload["conversation_id"] = st.session_state.conversation_id
                payload["turn_number"] = st.session_state.turn_number

            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            # Update conversation context
            if data.get("conversation_id"):
                st.session_state.conversation_id = data["conversation_id"]
            st.session_state.turn_number = data.get("turn_number", 1) + 1

            # Display assistant message
            with st.chat_message("assistant"):
                st.markdown(data["answer"])

                # Display visualization if present
                if "visualization" in data and data["visualization"]:
                    st.markdown("---")
                    st.markdown("**📊 Visualization:**")

                    # Render visualization
                    try:
                        fig = go.Figure(json.loads(data["visualization"]["plot_json"]))
                        st.plotly_chart(fig, use_container_width=True)

                        # Show pattern info
                        with st.expander("ℹ️ Visualization Info"):
                            st.write(f"**Pattern:** {data['visualization']['pattern']}")
                            st.write(f"**Type:** {data['visualization']['viz_type']}")
                    except Exception as e:
                        st.error(f"Failed to render visualization: {e}")

                # Show sources if present
                if data.get("sources"):
                    with st.expander(f"📚 Sources ({len(data['sources'])})"):
                        for i, source in enumerate(data["sources"], 1):
                            st.markdown(f"**{i}. {source['source']}** (Score: {source['score']:.1f}%)")
                            st.text(source["text"][:200] + "...")

                # Show processing time
                st.caption(f"⏱️ {data['processing_time_ms']:.0f}ms | 🤖 {data['model']}")

            # Add assistant message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": data["answer"],
                "visualization": data.get("visualization"),
                "timestamp": st.session_state.turn_number - 1
            })

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")

# Sidebar
with st.sidebar:
    st.header("💬 Conversation")

    if st.session_state.conversation_id:
        st.success(f"Active conversation: {st.session_state.conversation_id[:8]}...")
        st.write(f"Turn: {st.session_state.turn_number}")
    else:
        st.info("No active conversation")

    if st.button("🔄 New Conversation"):
        st.session_state.conversation_id = None
        st.session_state.turn_number = 1
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.header("📊 Example Queries")
    st.markdown("""
    **Statistical (with visualizations):**
    - Who are the top 5 scorers?
    - Compare Jokic and Embiid's stats
    - Show me players with over 25 PPG

    **Contextual (text only):**
    - What is the Lakers team culture?
    - Explain the triangle offense
    - Why is LeBron considered the GOAT?

    **Hybrid (both):**
    - Who are the top scorers and what makes them effective?
    - Compare LeBron and Durant's stats and explain who's better
    """)

    st.markdown("---")
    st.caption("Built with Streamlit + FastAPI + Plotly")
