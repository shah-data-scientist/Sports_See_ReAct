"""
FILE: demo_logfire.py
STATUS: Active
RESPONSIBILITY: Logfire RAG pipeline visualization demo
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import logging
import os

from src.core.config import settings
from src.core.observability import configure_observability, logfire
from src.models.chat import ChatRequest
from src.services.chat import ChatService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demo Logfire instrumentation of RAG pipeline.

    This demonstrates how Logfire traces a query through the entire RAG pipeline:
    1. User query → Embedding generation
    2. Vector similarity search (FAISS)
    3. Context retrieval
    4. LLM response generation
    """
    # Configure Logfire (set LOGFIRE_TOKEN in .env to see traces)
    configure_observability()

    logger.info("=" * 80)
    logger.info("LOGFIRE RAG PIPELINE DEMO")
    logger.info("=" * 80)

    # Initialize RAG pipeline components
    logger.info("\n1. Initializing RAG components...")
    chat_service = ChatService()  # Uses lazy initialization with defaults

    # Run demo queries
    queries = [
        "Who is the leading scorer in the NBA?",
        "What are LeBron James' stats?",
        "Which team has the best record?",
    ]

    logger.info("\n2. Running demo queries through instrumented pipeline...")
    logger.info("-" * 80)

    for i, query in enumerate(queries, 1):
        logger.info(f"\nQuery {i}/3: {query}")

        # Create instrumented span for the entire query
        with logfire.span("Demo Query", query=query):
            request = ChatRequest(query=query)
            response = chat_service.chat(request)

            logger.info(f"✓ Retrieved {len(response.sources)} sources")
            logger.info(f"✓ Generated response: {response.answer[:100]}...")

    logger.info("\n" + "=" * 80)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 80)

    # Check if Logfire is actually configured
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    if logfire_token:
        logger.info("\n✓ Logfire traces available at: https://logfire.pydantic.dev/")
        logger.info("  Navigate to 'sports-see' project to see:")
        logger.info("  - Query embedding generation spans")
        logger.info("  - Vector search operations")
        logger.info("  - LLM generation with token counts")
        logger.info("  - End-to-end latency waterfall")
    else:
        logger.warning("\n⚠ LOGFIRE_TOKEN not set in .env")
        logger.warning("  To enable Logfire tracing:")
        logger.warning("  1. Sign up at https://logfire.pydantic.dev/")
        logger.warning("  2. Create a project named 'sports-see'")
        logger.warning("  3. Add LOGFIRE_TOKEN=<your-token> to .env")
        logger.warning("  4. Re-run this demo")
        logger.info("\n  Pipeline still executed successfully with no-op instrumentation")


if __name__ == "__main__":
    main()
