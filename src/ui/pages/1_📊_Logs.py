"""
FILE: 1_📊_Logs.py
STATUS: Active
RESPONSIBILITY: Streamlit page for viewing and filtering application logs
LAST MAJOR UPDATE: 2026-02-16
MAINTAINER: Shahu
"""

import json
import sys
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.logging_config import get_recent_logs

st.set_page_config(
    page_title="Application Logs",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Application Logs Viewer")
st.markdown("Real-time monitoring of application logs (local files, no external API)")

# Sidebar filters
st.sidebar.header("Filters")

# Log file selection
log_files = {
    "All Logs (app.log)": "logs/app.log",
    "API Logs (api.log)": "logs/api.log",
    "Agent Logs (agent.log)": "logs/agent.log",
    "Errors Only (errors.log)": "logs/errors.log",
}
selected_log = st.sidebar.selectbox("Log File", list(log_files.keys()))
log_file = log_files[selected_log]

# Level filter
level_filter = st.sidebar.selectbox(
    "Log Level",
    ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
)

# Number of lines
num_lines = st.sidebar.slider("Number of lines", 10, 500, 100)

# Search filter
search_query = st.sidebar.text_input("Search in messages", "")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-refresh (every 5s)", value=False)

# Refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

# Auto-refresh logic
if auto_refresh:
    st.empty()  # Clear previous content
    import time
    time.sleep(5)
    st.rerun()

# Fetch logs
level = None if level_filter == "All" else level_filter
search = search_query if search_query else None

logs = get_recent_logs(
    log_file=log_file,
    lines=num_lines,
    level=level,
    search=search,
)

# Display summary
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Logs", len(logs))
with col2:
    errors = sum(1 for log in logs if log.get("level") == "ERROR")
    st.metric("Errors", errors, delta=None if errors == 0 else f"+{errors}")
with col3:
    warnings = sum(1 for log in logs if log.get("level") == "WARNING")
    st.metric("Warnings", warnings, delta=None if warnings == 0 else f"+{warnings}")
with col4:
    st.metric("Log File", Path(log_file).name)

st.divider()

# Display logs
if not logs:
    st.info("No logs found matching the filters.")
else:
    # Display logs in reverse chronological order (newest first)
    for i, log in enumerate(reversed(logs)):
        # Color-code by level
        level_colors = {
            "DEBUG": "🔵",
            "INFO": "🟢",
            "WARNING": "🟡",
            "ERROR": "🔴",
            "CRITICAL": "🟣",
        }
        level_icon = level_colors.get(log.get("level"), "⚪")

        # Expandable log entry
        with st.expander(
            f"{level_icon} **{log.get('timestamp', 'N/A')}** - "
            f"{log.get('level', 'UNKNOWN')} - "
            f"{log.get('logger', 'N/A')} - "
            f"{log.get('message', '')[:100]}..."
        ):
            # Display full log details
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Details**")
                st.markdown(f"- **Timestamp**: {log.get('timestamp', 'N/A')}")
                st.markdown(f"- **Level**: {log.get('level', 'UNKNOWN')}")
                st.markdown(f"- **Logger**: {log.get('logger', 'N/A')}")
                st.markdown(f"- **Module**: {log.get('module', 'N/A')}")
                st.markdown(f"- **Function**: {log.get('function', 'N/A')}:{log.get('line', 'N/A')}")

            with col_b:
                st.markdown("**Message**")
                st.text(log.get("message", ""))

                # Extra fields (query, conversation_id, etc.)
                extra_fields = {
                    k: v for k, v in log.items()
                    if k not in ["timestamp", "level", "logger", "message", "module", "function", "line", "exception"]
                }
                if extra_fields:
                    st.markdown("**Context**")
                    for key, value in extra_fields.items():
                        st.markdown(f"- **{key}**: {value}")

            # Exception trace
            if "exception" in log:
                st.markdown("**Exception Trace**")
                st.code(log["exception"], language="python")

            # Raw JSON
            with st.expander("View Raw JSON"):
                st.json(log)

# Footer
st.divider()
st.caption(
    f"Viewing {len(logs)} logs from `{log_file}` | "
    f"Auto-refresh: {'ON' if auto_refresh else 'OFF'}"
)
