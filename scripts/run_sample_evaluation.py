"""
FILE: run_sample_evaluation.py
STATUS: Active
RESPONSIBILITY: Run sample evaluation (5 diverse cases per dataset) with conservative rate limiting
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu

Runs 5 diverse test cases from each dataset (SQL, Hybrid, Vector) with 60s delays.
Produces 2 files per dataset: JSON (raw results) + MD (quality report).
Total: 6 files, ~15 minutes runtime.
"""

import io
import json
import logging
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Fix Windows charmap encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from starlette.testclient import TestClient

from src.api.main import create_app
from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES
from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES
from src.evaluation.test_cases.vector_test_cases import EVALUATION_TEST_CASES
from src.evaluation.models.vector_models import TestCategory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Conservative rate limiting (60s between queries)
RATE_LIMIT_DELAY = 60
MAX_RETRIES = 2
RETRY_BACKOFF = 30

OUTPUT_DIR = Path("evaluation_results")
OUTPUT_DIR.mkdir(exist_ok=True)


def select_diverse_sql_cases() -> list[tuple[int, Any]]:
    """Select 5 SQL cases from different categories."""
    # Pick one from each major category
    selected = []
    seen_categories = set()

    # Priority order for diversity
    target_categories = [
        "simple_sql_single",      # Simple factual
        "comparison_sql_two",     # Comparison
        "aggregation_sql_count",  # Aggregation
        "complex_sql_multi",      # Complex multi-condition
        "noisy_sql_typo",         # Noisy/informal
    ]

    for target in target_categories:
        for i, tc in enumerate(SQL_TEST_CASES):
            cat = tc.category if hasattr(tc, "category") else "unknown"
            if cat.startswith(target.split("_")[0]) and cat not in seen_categories:
                selected.append((i, tc))
                seen_categories.add(cat)
                break

    # Fill remaining slots if needed (shouldn't be, but safety)
    if len(selected) < 5:
        for i, tc in enumerate(SQL_TEST_CASES):
            if i not in [s[0] for s in selected]:
                selected.append((i, tc))
                if len(selected) >= 5:
                    break

    return selected[:5]


def select_diverse_hybrid_cases() -> list[tuple[int, Any]]:
    """Select 5 Hybrid cases from different categories."""
    selected = []
    seen_prefixes = set()

    # Pick one from different hybrid category prefixes
    target_prefixes = [
        "tier1",              # Basic stat + context
        "hybrid_team",        # Team analysis
        "hybrid_young",       # Young talent
        "hybrid_noisy",       # Noisy/informal
        "hybrid_defensive",   # Defensive/advanced
    ]

    for prefix in target_prefixes:
        for i, tc in enumerate(HYBRID_TEST_CASES):
            cat = tc.category if hasattr(tc, "category") else "unknown"
            if cat.startswith(prefix) and prefix not in seen_prefixes:
                selected.append((i, tc))
                seen_prefixes.add(prefix)
                break

    if len(selected) < 5:
        for i, tc in enumerate(HYBRID_TEST_CASES):
            if i not in [s[0] for s in selected]:
                selected.append((i, tc))
                if len(selected) >= 5:
                    break

    return selected[:5]


def select_diverse_vector_cases() -> list[tuple[int, Any]]:
    """Select 5 Vector cases from different categories."""
    selected = []
    seen_categories = set()

    # One from each TestCategory + one boosting test
    for target_cat in [TestCategory.SIMPLE, TestCategory.COMPLEX, TestCategory.NOISY, TestCategory.CONVERSATIONAL]:
        for i, tc in enumerate(EVALUATION_TEST_CASES):
            if tc.category == target_cat and target_cat.value not in seen_categories:
                selected.append((i, tc))
                seen_categories.add(target_cat.value)
                break

    # Add one more (different from first simple)
    for i, tc in enumerate(EVALUATION_TEST_CASES):
        if i not in [s[0] for s in selected]:
            selected.append((i, tc))
            break

    return selected[:5]


def run_api_query(client, question: str, conversation_id: str | None = None) -> dict:
    """Run a single query through the API with retry logic."""
    payload = {
        "query": question,
        "k": 5,
        "include_sources": True,
        "conversation_id": conversation_id,
    }

    for attempt in range(MAX_RETRIES + 1):
        response = client.post("/api/v1/chat", json=payload)

        if response.status_code == 200:
            return response.json()

        is_rate_limit = (
            response.status_code == 429
            or (response.status_code == 500 and "429" in response.text)
        )

        if is_rate_limit and attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF * (attempt + 1)
            logger.warning(f"  Rate limit hit, retry {attempt + 1}/{MAX_RETRIES} after {wait}s...")
            time.sleep(wait)
        else:
            raise RuntimeError(f"API error {response.status_code}: {response.text[:300]}")

    raise RuntimeError("Max retries exhausted")


def evaluate_sql_sample(client) -> tuple[list[dict], str]:
    """Run SQL sample evaluation (5 cases)."""
    logger.info("=" * 70)
    logger.info("SQL SAMPLE EVALUATION (5 diverse cases)")
    logger.info("=" * 70)

    cases = select_diverse_sql_cases()
    results = []

    for idx, (original_idx, tc) in enumerate(cases):
        logger.info(f"  [{idx + 1}/5] [{tc.category}] {tc.question[:70]}...")

        if idx > 0:
            logger.info(f"  Waiting {RATE_LIMIT_DELAY}s...")
            time.sleep(RATE_LIMIT_DELAY)

        try:
            api_result = run_api_query(client, tc.question)

            sources = api_result.get("sources", [])
            actual_routing = "sql_only" if len(sources) == 0 else "fallback_to_vector"

            results.append({
                "question": tc.question,
                "category": tc.category,
                "response": api_result.get("answer", ""),
                "expected_routing": tc.query_type.value,
                "actual_routing": actual_routing,
                "is_misclassified": (tc.query_type.value == "sql_only" and actual_routing != "sql_only"),
                "sources_count": len(sources),
                "processing_time_ms": api_result.get("processing_time_ms", 0),
                "generated_sql": api_result.get("generated_sql"),
                "ground_truth_answer": tc.ground_truth_answer,
                "ground_truth_data": tc.ground_truth_data,
                "success": True,
            })
            logger.info(f"  OK | Routing: {actual_routing} | Time: {api_result.get('processing_time_ms', 0)}ms")

        except Exception as e:
            logger.error(f"  FAILED: {e}")
            results.append({
                "question": tc.question,
                "category": tc.category,
                "response": "",
                "expected_routing": tc.query_type.value,
                "actual_routing": "error",
                "is_misclassified": True,
                "success": False,
                "error": str(e),
            })

    # Save JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"sql_sample_evaluation_{timestamp}.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate MD report
    md_path = OUTPUT_DIR / f"sql_sample_evaluation_report_{timestamp}.md"
    _generate_sql_sample_report(results, md_path, json_path.name)

    logger.info(f"  JSON: {json_path}")
    logger.info(f"  Report: {md_path}")

    return results, str(json_path)


def evaluate_hybrid_sample(client) -> tuple[list[dict], str]:
    """Run Hybrid sample evaluation (5 cases)."""
    logger.info("=" * 70)
    logger.info("HYBRID SAMPLE EVALUATION (5 diverse cases)")
    logger.info("=" * 70)

    cases = select_diverse_hybrid_cases()
    results = []

    for idx, (original_idx, tc) in enumerate(cases):
        logger.info(f"  [{idx + 1}/5] [{tc.category}] {tc.question[:70]}...")

        if idx > 0:
            logger.info(f"  Waiting {RATE_LIMIT_DELAY}s...")
            time.sleep(RATE_LIMIT_DELAY)

        try:
            api_result = run_api_query(client, tc.question)

            sources = api_result.get("sources", [])
            generated_sql = api_result.get("generated_sql")
            has_sql = generated_sql is not None and len(generated_sql) > 0
            has_vector = len(sources) > 0

            if has_sql and has_vector:
                routing = "both"
            elif has_sql:
                routing = "sql"
            elif has_vector:
                routing = "vector"
            else:
                routing = "unknown"

            results.append({
                "question": tc.question,
                "category": tc.category,
                "response": api_result.get("answer", ""),
                "routing": routing,
                "generated_sql": generated_sql,
                "sources": sources,
                "sources_count": len(sources),
                "processing_time_ms": api_result.get("processing_time_ms", 0),
                "ground_truth_answer": tc.ground_truth_answer,
                "success": True,
            })
            logger.info(f"  OK | Routing: {routing.upper()} | Sources: {len(sources)} | Time: {api_result.get('processing_time_ms', 0)}ms")

        except Exception as e:
            logger.error(f"  FAILED: {e}")
            results.append({
                "question": tc.question,
                "category": tc.category,
                "response": "",
                "routing": "error",
                "success": False,
                "error": str(e),
            })

    # Save JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"hybrid_sample_evaluation_{timestamp}.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate MD report
    md_path = OUTPUT_DIR / f"hybrid_sample_evaluation_report_{timestamp}.md"
    _generate_hybrid_sample_report(results, md_path, json_path.name)

    logger.info(f"  JSON: {json_path}")
    logger.info(f"  Report: {md_path}")

    return results, str(json_path)


def evaluate_vector_sample(client) -> tuple[list[dict], str]:
    """Run Vector sample evaluation (5 cases)."""
    logger.info("=" * 70)
    logger.info("VECTOR SAMPLE EVALUATION (5 diverse cases)")
    logger.info("=" * 70)

    cases = select_diverse_vector_cases()
    results = []

    for idx, (original_idx, tc) in enumerate(cases):
        logger.info(f"  [{idx + 1}/5] [{tc.category.value}] {tc.question[:70]}...")

        if idx > 0:
            logger.info(f"  Waiting {RATE_LIMIT_DELAY}s...")
            time.sleep(RATE_LIMIT_DELAY)

        try:
            api_result = run_api_query(client, tc.question)

            sources = api_result.get("sources", [])
            has_vector = len(sources) > 0
            actual_routing = "vector_only" if has_vector else "unknown"

            results.append({
                "question": tc.question,
                "category": tc.category.value,
                "response": api_result.get("answer", ""),
                "actual_routing": actual_routing,
                "sources": [
                    {
                        "text": s.get("text", "")[:500],
                        "score": s.get("score", 0),
                        "source": s.get("source", "unknown"),
                    }
                    for s in sources
                ],
                "sources_count": len(sources),
                "processing_time_ms": api_result.get("processing_time_ms", 0),
                "ground_truth": tc.ground_truth,
                "success": True,
            })
            logger.info(f"  OK | Sources: {len(sources)} | Time: {api_result.get('processing_time_ms', 0)}ms")

        except Exception as e:
            logger.error(f"  FAILED: {e}")
            results.append({
                "question": tc.question,
                "category": tc.category.value,
                "response": "",
                "actual_routing": "error",
                "success": False,
                "error": str(e),
            })

    # Save JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"vector_sample_evaluation_{timestamp}.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate MD report
    md_path = OUTPUT_DIR / f"vector_sample_evaluation_report_{timestamp}.md"
    _generate_vector_sample_report(results, md_path, json_path.name)

    logger.info(f"  JSON: {json_path}")
    logger.info(f"  Report: {md_path}")

    return results, str(json_path)


# ==========================================================================
# REPORT GENERATORS
# ==========================================================================


def _generate_sql_sample_report(results: list[dict], md_path: Path, json_name: str) -> None:
    """Generate SQL sample evaluation markdown report."""
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    misclassified = sum(1 for r in results if r.get("is_misclassified"))
    times = [r["processing_time_ms"] for r in results if r.get("success")]

    lines = [
        "# SQL Sample Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Sample Size:** {total} queries (from {len(SQL_TEST_CASES)} total)",
        f"**Results JSON:** `{json_name}`",
        f"**Rate Limit Delay:** {RATE_LIMIT_DELAY}s between queries",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Queries:** {total}",
        f"- **Successful:** {successful}/{total} ({successful / total * 100:.0f}%)",
        f"- **Misclassifications:** {misclassified}",
        f"- **Avg Processing Time:** {sum(times) / len(times):.0f}ms" if times else "- **Avg Processing Time:** N/A",
        "",
        "## Query-by-Query Results",
        "",
    ]

    for i, r in enumerate(results, 1):
        status = "PASS" if r.get("success") and not r.get("is_misclassified") else "FAIL"
        lines.extend([
            f"### {i}. [{status}] {r['question']}",
            "",
            f"- **Category:** {r.get('category', 'unknown')}",
            f"- **Expected Routing:** {r.get('expected_routing', 'N/A')}",
            f"- **Actual Routing:** {r.get('actual_routing', 'N/A')}",
            f"- **Processing Time:** {r.get('processing_time_ms', 0):.0f}ms",
        ])

        if r.get("generated_sql"):
            lines.append(f"- **Generated SQL:** `{r['generated_sql'][:150]}`")

        if r.get("ground_truth_answer"):
            lines.append(f"- **Expected Answer:** {r['ground_truth_answer'][:200]}")

        lines.extend([
            f"- **Response:** {r.get('response', '')[:300]}{'...' if len(r.get('response', '')) > 300 else ''}",
            "",
        ])

        if r.get("error"):
            lines.append(f"- **Error:** {r['error']}")
            lines.append("")

    lines.extend([
        "---",
        "",
        f"*Report generated from {total}-case sample of {len(SQL_TEST_CASES)} SQL test cases*",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")


def _generate_hybrid_sample_report(results: list[dict], md_path: Path, json_name: str) -> None:
    """Generate Hybrid sample evaluation markdown report."""
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    times = [r["processing_time_ms"] for r in results if r.get("success")]

    # Routing distribution
    routing_counts = defaultdict(int)
    for r in results:
        routing_counts[r.get("routing", "unknown")] += 1

    lines = [
        "# Hybrid Sample Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Sample Size:** {total} queries (from {len(HYBRID_TEST_CASES)} total)",
        f"**Results JSON:** `{json_name}`",
        f"**Rate Limit Delay:** {RATE_LIMIT_DELAY}s between queries",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Queries:** {total}",
        f"- **Successful:** {successful}/{total} ({successful / total * 100:.0f}%)",
        f"- **Avg Processing Time:** {sum(times) / len(times):.0f}ms" if times else "- **Avg Processing Time:** N/A",
        "",
        "### Routing Distribution",
        "",
        "| Routing | Count |",
        "|---------|-------|",
    ]

    for routing, count in sorted(routing_counts.items()):
        lines.append(f"| {routing.upper()} | {count} |")

    lines.extend([
        "",
        "## Query-by-Query Results",
        "",
    ])

    for i, r in enumerate(results, 1):
        status = "PASS" if r.get("success") else "FAIL"
        lines.extend([
            f"### {i}. [{status}] {r['question'][:80]}",
            "",
            f"- **Category:** {r.get('category', 'unknown')}",
            f"- **Routing:** {r.get('routing', 'N/A').upper()}",
            f"- **Sources:** {r.get('sources_count', 0)}",
            f"- **Processing Time:** {r.get('processing_time_ms', 0):.0f}ms",
        ])

        if r.get("generated_sql"):
            lines.append(f"- **Generated SQL:** `{r['generated_sql'][:150]}`")

        if r.get("ground_truth_answer"):
            lines.append(f"- **Expected Answer:** {r['ground_truth_answer'][:200]}")

        lines.extend([
            f"- **Response:** {r.get('response', '')[:400]}{'...' if len(r.get('response', '')) > 400 else ''}",
            "",
        ])

        # Sources table
        sources = r.get("sources", [])
        if sources:
            lines.extend([
                "**Sources Retrieved:**",
                "",
                "| # | Source | Score |",
                "|---|--------|-------|",
            ])
            for si, s in enumerate(sources[:5], 1):
                source_name = s.get("source", "unknown") if isinstance(s, dict) else str(s)
                score = s.get("score", 0) if isinstance(s, dict) else 0
                lines.append(f"| {si} | {source_name[:40]} | {score:.1f}% |")
            lines.append("")

        if r.get("error"):
            lines.append(f"- **Error:** {r['error']}")
            lines.append("")

    lines.extend([
        "---",
        "",
        f"*Report generated from {total}-case sample of {len(HYBRID_TEST_CASES)} Hybrid test cases*",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")


def _generate_vector_sample_report(results: list[dict], md_path: Path, json_name: str) -> None:
    """Generate Vector sample evaluation markdown report."""
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    times = [r["processing_time_ms"] for r in results if r.get("success")]

    lines = [
        "# Vector Sample Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Sample Size:** {total} queries (from {len(EVALUATION_TEST_CASES)} total)",
        f"**Results JSON:** `{json_name}`",
        f"**Rate Limit Delay:** {RATE_LIMIT_DELAY}s between queries",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Queries:** {total}",
        f"- **Successful:** {successful}/{total} ({successful / total * 100:.0f}%)",
        f"- **Avg Processing Time:** {sum(times) / len(times):.0f}ms" if times else "- **Avg Processing Time:** N/A",
        "",
        "## Query-by-Query Results",
        "",
    ]

    for i, r in enumerate(results, 1):
        status = "PASS" if r.get("success") else "FAIL"
        lines.extend([
            f"### {i}. [{status}] {r['question'][:80]}",
            "",
            f"- **Category:** {r.get('category', 'unknown')}",
            f"- **Routing:** {r.get('actual_routing', 'N/A')}",
            f"- **Sources Retrieved:** {r.get('sources_count', 0)}",
            f"- **Processing Time:** {r.get('processing_time_ms', 0):.0f}ms",
        ])

        lines.extend([
            f"- **Response:** {r.get('response', '')[:400]}{'...' if len(r.get('response', '')) > 400 else ''}",
            "",
        ])

        # Sources table
        sources = r.get("sources", [])
        if sources:
            lines.extend([
                "**Sources Retrieved:**",
                "",
                "| # | Source | Score | Text Preview |",
                "|---|--------|-------|--------------|",
            ])
            for si, s in enumerate(sources[:5], 1):
                source_name = s.get("source", "unknown")[:30]
                score = s.get("score", 0)
                text_preview = s.get("text", "")[:60].replace("|", " ").replace("\n", " ")
                lines.append(f"| {si} | {source_name} | {score:.1f}% | {text_preview}... |")
            lines.append("")

        if r.get("ground_truth"):
            lines.append(f"- **Ground Truth:** {r['ground_truth'][:200]}...")
            lines.append("")

        if r.get("error"):
            lines.append(f"- **Error:** {r['error']}")
            lines.append("")

    lines.extend([
        "---",
        "",
        f"*Report generated from {total}-case sample of {len(EVALUATION_TEST_CASES)} Vector test cases*",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")


# ==========================================================================
# MAIN
# ==========================================================================


def main():
    """Run sample evaluation for all 3 datasets."""
    logger.info("=" * 70)
    logger.info("SAMPLE EVALUATION: 5 cases x 3 datasets = 15 queries")
    logger.info(f"Rate limit delay: {RATE_LIMIT_DELAY}s between queries")
    logger.info(f"Estimated time: ~{15 * RATE_LIMIT_DELAY / 60:.0f} minutes")
    logger.info("=" * 70)

    app = create_app()

    with TestClient(app) as client:
        # 1. SQL Sample
        sql_results, sql_json = evaluate_sql_sample(client)
        logger.info(f"SQL done: {sum(1 for r in sql_results if r['success'])}/5 successful")

        # Extra pause between datasets
        logger.info(f"Waiting {RATE_LIMIT_DELAY}s before next dataset...")
        time.sleep(RATE_LIMIT_DELAY)

        # 2. Hybrid Sample
        hybrid_results, hybrid_json = evaluate_hybrid_sample(client)
        logger.info(f"Hybrid done: {sum(1 for r in hybrid_results if r['success'])}/5 successful")

        # Extra pause between datasets
        logger.info(f"Waiting {RATE_LIMIT_DELAY}s before next dataset...")
        time.sleep(RATE_LIMIT_DELAY)

        # 3. Vector Sample
        vector_results, vector_json = evaluate_vector_sample(client)
        logger.info(f"Vector done: {sum(1 for r in vector_results if r['success'])}/5 successful")

    # Final summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("ALL SAMPLE EVALUATIONS COMPLETE")
    logger.info("=" * 70)

    total_success = (
        sum(1 for r in sql_results if r["success"])
        + sum(1 for r in hybrid_results if r["success"])
        + sum(1 for r in vector_results if r["success"])
    )
    logger.info(f"Total: {total_success}/15 successful queries")
    logger.info("")
    logger.info("Output files (6 total):")
    logger.info(f"  SQL:    {sql_json}")
    logger.info(f"          {sql_json.replace('.json', '').replace('evaluation', 'evaluation_report') + '.md'}")
    logger.info(f"  Hybrid: {hybrid_json}")
    logger.info(f"          {hybrid_json.replace('.json', '').replace('evaluation', 'evaluation_report') + '.md'}")
    logger.info(f"  Vector: {vector_json}")
    logger.info(f"          {vector_json.replace('.json', '').replace('evaluation', 'evaluation_report') + '.md'}")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)
