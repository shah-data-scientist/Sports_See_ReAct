"""
FILE: demo_logfire_visual.py
STATUS: Active
RESPONSIBILITY: Visual demonstration of Logfire instrumentation
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import logging
import os
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MockSpan:
    """Mock Logfire span for visualization when Logfire is not configured."""

    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
        self.start_time = time.time()
        self.children = []
        self.level = 0

    def __enter__(self):
        indent = "  " * self.level
        logger.info(f"{indent}▶ START SPAN: {self.name}")
        if self.attributes:
            for key, value in self.attributes.items():
                logger.info(f"{indent}  • {key}={value}")
        return self

    def __exit__(self, *args):
        duration = time.time() - self.start_time
        indent = "  " * self.level
        logger.info(f"{indent}◀ END SPAN: {self.name} [{duration*1000:.1f}ms]\n")


def simulate_rag_pipeline():
    """Simulate a RAG pipeline query with instrumented spans."""

    print("\n" + "=" * 80)
    print("LOGFIRE INSTRUMENTATION DEMONSTRATION")
    print("Showing how Logfire traces a RAG query through the system")
    print("=" * 80 + "\n")

    query = "Who is the leading scorer in the NBA this season?"
    print(f"USER QUERY: {query}\n")

    # Main pipeline span
    with MockSpan("ChatService.chat", query=query, method="POST /chat") as main_span:
        main_span.level = 0
        time.sleep(0.1)  # Simulate processing

        # 1. Query embedding generation
        with MockSpan(
            "EmbeddingService.embed_batch",
            texts_count=1,
            model="mistral-embed",
        ) as embed_span:
            embed_span.level = 1
            time.sleep(0.3)  # Simulate API call

            with MockSpan(
                "Mistral API Call", endpoint="/v1/embeddings", method="POST"
            ) as api_span:
                api_span.level = 2
                time.sleep(0.25)

            logger.info("  Result: embedding vector [1024 dimensions]")

        # 2. Vector similarity search
        with MockSpan(
            "ChatService.search",
            query=query,
            k=5,
            vector_store="FAISS",
        ) as search_span:
            search_span.level = 1
            time.sleep(0.18)

            with MockSpan(
                "FAISS Index Search", total_vectors=302, similarity="cosine"
            ) as faiss_span:
                faiss_span.level = 2
                time.sleep(0.15)

            logger.info("  Result: 5 document chunks retrieved")
            logger.info("    • Similarity scores: [0.92, 0.89, 0.85, 0.82, 0.78]")

        # 3. Context assembly
        with MockSpan("Context Assembly", chunks=5) as context_span:
            context_span.level = 1
            time.sleep(0.05)
            logger.info("  Result: 1,245 tokens of context")

        # 4. LLM response generation
        with MockSpan(
            "ChatService.generate_response",
            model="mistral-small-latest",
            temperature=0.7,
        ) as llm_span:
            llm_span.level = 1
            time.sleep(1.5)  # Simulate LLM call

            with MockSpan(
                "Mistral API Call", endpoint="/v1/chat/completions", method="POST"
            ) as llm_api_span:
                llm_api_span.level = 2
                time.sleep(1.4)

                logger.info("    • Input tokens: 1,456")
                logger.info("    • Output tokens: 127")
                logger.info("    • Tokens per second: 91")

            logger.info(
                "  Result: Based on the latest statistics, Luka Dončić leads..."
            )

    print("\n" + "=" * 80)
    print("TRACE SUMMARY")
    print("=" * 80)
    print(f"""
Total Request Time: ~2.13 seconds

Pipeline Breakdown:
├─ Query Embedding          [320ms]  (15% of total)
│  └─ Mistral API call     [250ms]
├─ Vector Search            [180ms]  (8% of total)
│  └─ FAISS index search   [150ms]
├─ Context Assembly         [50ms]   (2% of total)
└─ LLM Generation          [1,500ms] (70% of total) ← BOTTLENECK
   └─ Mistral API call    [1,400ms]

Performance Insights:
• 70% of time spent in LLM generation
• Embedding and search are fast (<500ms combined)
• Potential optimization: Use faster LLM model for simple queries
• Cache frequent queries to avoid LLM calls
""")


def show_logfire_features():
    """Explain what Logfire provides."""

    print("\n" + "=" * 80)
    print("WHAT DOES LOGFIRE DO?")
    print("=" * 80 + "\n")

    print("""
1. **Distributed Tracing** (shown above)
   - Tracks a request through multiple services/functions
   - Shows parent-child span relationships
   - Calculates accurate timing for each operation
   - Visualizes waterfall timeline

2. **Performance Monitoring**
   - Real-time latency metrics (P50, P95, P99)
   - Identifies slow operations automatically
   - Tracks trends over time
   - Alerts on performance degradation

3. **Error Tracking**
   - Captures full stack traces
   - Shows which span failed
   - Links errors to specific requests
   - Tracks error rates and patterns

4. **Cost Monitoring**
   - Tracks API calls and token usage
   - Shows LLM costs per query
   - Identifies expensive operations
   - Helps optimize spending

5. **Query Analytics**
   - Most common queries
   - Success/failure rates
   - Retrieval quality (similarity scores)
   - User behavior patterns

6. **A/B Testing**
   - Compare different models
   - Test prompt variations
   - Measure impact of changes
   - Data-driven optimization
""")

    print("\n" + "=" * 80)
    print("REAL LOGFIRE DASHBOARD")
    print("=" * 80 + "\n")

    logfire_token = os.getenv("LOGFIRE_TOKEN")

    if logfire_token:
        print("✓ Logfire is CONFIGURED")
        print("  View your traces at: https://logfire.pydantic.dev/sports-see")
        print("\n  What you'll see:")
        print("  • Interactive trace waterfall (like above, but clickable)")
        print("  • Real-time performance charts")
        print("  • Error rates and stack traces")
        print("  • Token usage over time")
        print("  • Custom dashboards and alerts")
    else:
        print("⚠ Logfire is NOT configured (running in no-op mode)")
        print("\n  To enable full tracing:")
        print("  1. Sign up at https://logfire.pydantic.dev/")
        print("  2. Create a project: 'sports-see'")
        print("  3. Get your write token")
        print("  4. Add to .env file:")
        print("     LOGFIRE_TOKEN=your_token_here")
        print("  5. Set in config:")
        print("     logfire_enabled=True")
        print("\n  Then re-run this demo to see actual traces!")


    print("\n" + "=" * 80)
    print("EXAMPLE: DEBUGGING WITH LOGFIRE")
    print("=" * 80 + "\n")

    print("""
Scenario: User complains "Search results are slow"

Without Logfire:
❌ Don't know which part is slow
❌ Can't reproduce the issue
❌ Have to add logging manually
❌ Guessing at the problem

With Logfire:
✓ See exact trace for that request
✓ Waterfall shows LLM took 5.2s (usually 1.5s)
✓ Click to see full request/response
✓ Compare with other requests (P95: 1.8s)
✓ Identify: Specific query caused large context
✓ Root cause: Query returned 15 chunks instead of 5
✓ Fix: Add better relevance filtering

Time to identify: 2 minutes vs. 2 hours
""")


def main():
    """Run the demonstration."""
    simulate_rag_pipeline()
    show_logfire_features()

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80 + "\n")

    print("""
1. Review baseline metrics:
   → evaluation_results/ragas_baseline.json
   → docs/RAGAS_BASELINE_REPORT.md

2. Configure Logfire (optional but recommended):
   → Add LOGFIRE_TOKEN to .env
   → Set logfire_enabled=True in settings

3. Run a real query through the system:
   → poetry run python demo_logfire.py

4. Implement improvements from baseline report:
   → Start with Phase 1 (prompt engineering)
   → Re-evaluate after each phase
   → Track progress with Logfire

5. Monitor in production:
   → Set up alerts for slow requests (>3s)
   → Track token costs
   → Identify common failure patterns
""")


if __name__ == "__main__":
    main()
