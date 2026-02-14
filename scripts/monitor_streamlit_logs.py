"""
FILE: monitor_streamlit_logs.py
STATUS: Active
RESPONSIBILITY: Real-time Streamlit session monitoring and diagnostics
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu

Monitors Streamlit session state and logs for debugging UI hanging issues.
Captures session rerun events, widget interactions, and rendering state.

Usage:
    poetry run python scripts/monitor_streamlit_logs.py
    Then interact with UI and watch for session state changes.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

import requests

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class StreamlitMonitor:
    """Monitor Streamlit session state and interactions."""

    STREAMLIT_URL = "http://localhost:8501"
    API_URL = "http://localhost:8002"

    def __init__(self):
        self.last_check = time.time()
        self.session_state = {}
        self.interaction_count = 0

    def check_streamlit_api(self) -> dict:
        """Check Streamlit API endpoints if available."""
        logger.info("\n" + "=" * 60)
        logger.info("STREAMLIT SESSION DIAGNOSTICS")
        logger.info("=" * 60)

        try:
            # Try to access Streamlit's internal state (if exposed)
            response = requests.get(
                f"{self.STREAMLIT_URL}/_stcore/session_state",
                timeout=5,
            )

            if response.status_code == 200:
                state = response.json()
                logger.info("✅ Streamlit session state:")
                logger.info(json.dumps(state, indent=2)[:500])
                return state
            else:
                logger.debug(
                    f"Session state endpoint returned {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            logger.debug(f"Cannot access session state endpoint: {e}")

        return {}

    def test_api_endpoint_directly(self):
        """Test the chat endpoint directly to verify API works."""
        logger.info("\n" + "=" * 60)
        logger.info("DIRECT API ENDPOINT TEST")
        logger.info("=" * 60)

        queries_to_test = [
            ("top 5 scorers", "SQL"),
            ("high in the chart", "HYBRID"),
            ("discuss winning strategies", "VECTOR"),
        ]

        for query, expected_type in queries_to_test:
            logger.info(f"\n→ Testing: '{query}' (expected type: {expected_type})")

            payload = {
                "query": query,
                "k": 5,
                "include_sources": True,
                "conversation_id": None,
            }

            try:
                start = time.time()
                response = requests.post(
                    f"{self.API_URL}/api/v1/chat",
                    json=payload,
                    timeout=30,
                )
                elapsed = time.time() - start

                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        f"✅ Success ({elapsed:.2f}s) | Type: {data.get('chat_type')}"
                    )
                    logger.info(
                        f"   Message: {data.get('message', '')[:80]}..."
                    )
                else:
                    logger.error(
                        f"❌ Status {response.status_code}: "
                        f"{response.text[:100]}"
                    )

            except requests.exceptions.Timeout:
                logger.error("⏱️ Request timed out (30s)")
            except Exception as e:
                logger.error(f"❌ Error: {e}")

            time.sleep(2)  # Rate limiting

    def capture_ui_interaction_flow(self):
        """Guide user through capturing the hanging behavior."""
        logger.info("\n" + "=" * 60)
        logger.info("INTERACTIVE CAPTURE INSTRUCTIONS")
        logger.info("=" * 60)

        instructions = """
STEP-BY-STEP DEBUGGING PROCESS:

Step 1: Open Developer Tools
   → Press F12 in the browser while viewing http://localhost:8501
   → Go to "Network" tab
   → Enable network logging

Step 2: Type the Problematic Query
   → In the chat input, type: "high in the chart"
   → Submit the query
   → Watch the Network tab for requests

Step 3: Look for These Patterns
   ✓ POST request to /api/v1/chat (or similar)
   ✓ Check response time - does API respond?
   ✓ Check response status code (should be 200)
   ✓ Check response body - is there a message?

Step 4: If UI hangs but API responds:
   → The issue is in Streamlit's rendering/state management
   → Go to "Console" tab to check for JavaScript errors
   → Look for red errors (not just warnings)

Step 5: Streamlit-Specific Checks
   → Check Streamlit server logs (terminal running `streamlit run`)
   → Look for Python exceptions or warnings
   → Check if chat message component is re-rendering infinitely

WHAT TYPICALLY CAUSES HANGING:
   • Infinite rerun loops (component keeps triggering reruns)
   • Unhandled exceptions in callbacks
   • Race conditions between UI state and API responses
   • Missing error handling for specific query types
   • Widget state not updating properly after API response

NEXT DEBUGGING ACTIONS:
   1. Add explicit logging to app.py chat handling
   2. Check if query classification is causing issues
   3. Look for any conditional rendering based on query content
   4. Test with query that works to compare code paths
        """

        logger.info(instructions)

    def suggest_app_modifications(self):
        """Suggest code modifications for debugging."""
        logger.info("\n" + "=" * 60)
        logger.info("SUGGESTED CODE MODIFICATIONS FOR DEBUGGING")
        logger.info("=" * 60)

        logger.info("""
Add this to src/ui/app.py in the chat handling section:

```python
# Add detailed logging to debug hanging
import time as time_module

if user_query := st.chat_input("Ask about NBA..."):
    # Log query submission
    st.session_state.query_submitted_time = time_module.time()
    logger.info(f"Query submitted: '{user_query}'")

    with st.chat_message("user"):
        st.write(user_query)

    # Log API call start
    api_call_start = time_module.time()
    logger.info(f"Sending query to API at {api_call_start}")

    try:
        response = requests.post(
            "http://localhost:8002/api/v1/chat",
            json={
                "message": user_query,
                "conversation_id": st.session_state.current_conversation_id,
                "chat_type": "both"
            },
            timeout=30
        )

        api_call_elapsed = time_module.time() - api_call_start
        logger.info(f"API responded in {api_call_elapsed:.2f}s")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Got response: {len(data.get('message', ''))} chars")

            # Display assistant message
            with st.chat_message("assistant"):
                st.write(data.get("message", "No response"))
        else:
            logger.error(f"API error: {response.status_code}")
            st.error(f"API error: {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        st.error("Request timed out - API took more than 30 seconds")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        st.error(f"Error: {e}")
```

This will help identify:
   ✓ Exact time when query is submitted
   ✓ Exact time when API responds
   ✓ Which exceptions are occurring (if any)
   ✓ Response content length
        """)

    def run_diagnostics(self):
        """Run all diagnostics."""
        logger.info(f"\n{'=' * 60}")
        logger.info("STREAMLIT UI HANGING DIAGNOSTICS")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'=' * 60}\n")

        # Check if services are running
        logger.info("Checking service availability...")

        try:
            streamlit_ok = requests.get(
                self.STREAMLIT_URL, timeout=5
            ).status_code in [200, 304]
            logger.info(f"✅ Streamlit UI: {'OK' if streamlit_ok else 'FAILED'}")
        except Exception as e:
            logger.info(f"❌ Streamlit UI: FAILED ({e})")
            streamlit_ok = False

        try:
            api_ok = requests.get(
                f"{self.API_URL}/health", timeout=5
            ).status_code == 200
            logger.info(f"✅ API: {'OK' if api_ok else 'FAILED'}")
        except Exception as e:
            logger.info(f"❌ API: FAILED ({e})")
            api_ok = False

        if not streamlit_ok or not api_ok:
            logger.error("\n❌ One or more services are not running")
            logger.error("Start both with:")
            logger.error("  Terminal 1: poetry run streamlit run src/ui/app.py")
            logger.error("  Terminal 2: poetry run uvicorn src.api.main:app --reload")
            return

        # Run diagnostics
        self.test_api_endpoint_directly()
        self.check_streamlit_api()
        self.capture_ui_interaction_flow()
        self.suggest_app_modifications()

        logger.info(f"\n{'=' * 60}")
        logger.info("DIAGNOSTICS COMPLETE")
        logger.info(f"{'=' * 60}")
        logger.info("""
Next Steps:
1. Review the suggestions above
2. Implement logging in app.py
3. Reproduce the hanging issue
4. Check the logs to see where it hangs
5. Share the logs for further analysis

Key file to check: src/ui/app.py (chat input handling section)
        """)


def main():
    """Main entry point."""
    monitor = StreamlitMonitor()
    monitor.run_diagnostics()


if __name__ == "__main__":
    main()
