"""
Batch Evaluation Script - Run 10 queries at a time with balanced mix

Usage:
    python scripts/run_batch_evaluation.py --batch 1
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import time

# P1 ISSUE #6 FIX: Add retry logic for transient failures
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.test_data import ALL_TEST_CASES
from src.evaluation.models import TestType, UnifiedTestCase
from src.services.chat import ChatService
from src.models.chat import ChatRequest
from src.evaluation.metrics import calculate_ragas_metrics
from src.repositories.feedback import FeedbackRepository
from src.models.feedback import ChatInteractionCreate


def select_batch_queries(batch_num: int, queries_per_batch: int = 10) -> List[tuple]:
    """
    Select balanced batch of queries (4 SQL + 4 Vector + 2 Hybrid).

    Returns list of (index, test_case) tuples.
    """
    # Group test cases by type
    sql_cases = [(i, tc) for i, tc in enumerate(ALL_TEST_CASES) if tc.test_type == TestType.SQL]
    vector_cases = [(i, tc) for i, tc in enumerate(ALL_TEST_CASES) if tc.test_type == TestType.VECTOR]
    hybrid_cases = [(i, tc) for i, tc in enumerate(ALL_TEST_CASES) if tc.test_type == TestType.HYBRID]

    # Calculate batch distribution (4 SQL, 4 Vector, 2 Hybrid per batch)
    sql_per_batch = 4
    vector_per_batch = 4
    hybrid_per_batch = 2

    # Calculate starting indices for this batch
    batch_offset = (batch_num - 1) * queries_per_batch
    sql_start = ((batch_num - 1) * sql_per_batch) % len(sql_cases)
    vector_start = ((batch_num - 1) * vector_per_batch) % len(vector_cases)
    hybrid_start = ((batch_num - 1) * hybrid_per_batch) % len(hybrid_cases)

    # Select queries
    selected = []

    # Add SQL queries
    for i in range(sql_per_batch):
        idx = (sql_start + i) % len(sql_cases)
        selected.append(sql_cases[idx])

    # Add Vector queries
    for i in range(vector_per_batch):
        idx = (vector_start + i) % len(vector_cases)
        selected.append(vector_cases[idx])

    # Add Hybrid queries
    for i in range(hybrid_per_batch):
        idx = (hybrid_start + i) % len(hybrid_cases)
        selected.append(hybrid_cases[idx])

    return selected


def analyze_sql_complexity(sql: str) -> dict:
    """Analyze SQL query complexity."""
    import re

    sql_upper = sql.upper()

    # Count structural elements
    join_count = len(re.findall(r'\bJOIN\b', sql_upper))
    filter_count = sql_upper.count('WHERE') + sql_upper.count(' AND ')
    has_aggregation = any(word in sql_upper for word in ['GROUP BY', 'AVG', 'SUM', 'COUNT', 'MAX', 'MIN'])
    has_subqueries = sql.count('SELECT') > 1
    has_window_functions = any(word in sql_upper for word in ['OVER', 'PARTITION BY', 'ROW_NUMBER', 'RANK'])

    # Calculate complexity score
    complexity_score = (
        join_count * 2 +
        filter_count +
        (3 if has_aggregation else 0) +
        (2 if has_subqueries else 0) +
        (3 if has_window_functions else 0)
    )

    # Determine complexity level
    if complexity_score == 0:
        complexity_level = "Trivial"
    elif complexity_score <= 3:
        complexity_level = "Simple"
    elif complexity_score <= 8:
        complexity_level = "Moderate"
    else:
        complexity_level = "Complex"

    return {
        "level": complexity_level,
        "score": complexity_score,
        "joins": join_count,
        "filters": filter_count,
        "aggregation": has_aggregation,
        "subqueries": has_subqueries,
        "window_functions": has_window_functions,
    }


def detect_issues(result: dict) -> list:
    """Detect issues in evaluation result."""
    issues = []

    # Check RAGAS metrics
    if result.get("ragas_metrics"):
        for metric, score in result["ragas_metrics"].items():
            if score is not None:
                if score < 0.5:
                    issues.append({
                        "severity": "critical",
                        "type": "low_metric",
                        "message": f"{metric} score is {score:.3f} (below 0.7 threshold)"
                    })
                elif score < 0.7:
                    issues.append({
                        "severity": "warning",
                        "type": "low_metric",
                        "message": f"{metric} score is {score:.3f} (below 0.7 threshold)"
                    })

    # Check for short responses
    answer = result.get("answer", "")
    if len(answer) < 20:
        issues.append({
            "severity": "warning",
            "type": "short_response",
            "message": f"Response is only {len(answer)} characters"
        })

    # Check for SQL errors
    if result.get("sql_error"):
        issues.append({
            "severity": "critical",
            "type": "sql_error",
            "message": result["sql_error"]
        })

    return issues


def run_batch_evaluation(batch_num: int):
    """Run evaluation for a specific batch."""
    print(f"\n{'='*100}")
    print(f"BATCH #{batch_num} EVALUATION")
    print(f"{'='*100}\n")

    # Select queries for this batch
    batch_queries = select_batch_queries(batch_num)

    print(f"Selected {len(batch_queries)} queries:")
    sql_count = sum(1 for _, tc in batch_queries if tc.test_type == TestType.SQL)
    vector_count = sum(1 for _, tc in batch_queries if tc.test_type == TestType.VECTOR)
    hybrid_count = sum(1 for _, tc in batch_queries if tc.test_type == TestType.HYBRID)
    print(f"  - SQL: {sql_count}")
    print(f"  - Vector: {vector_count}")
    print(f"  - Hybrid: {hybrid_count}\n")

    # Initialize services
    print("Initializing services...\n")
    chat_service = ChatService(enable_sql=True)

    # Run evaluation
    results = []
    start_time = datetime.now()

    for i, (original_idx, test_case) in enumerate(batch_queries, 1):
        print(f"[{i}/{len(batch_queries)}] Testing: '{test_case.question[:70]}...'")

        try:
            # P1 ISSUE #6 FIX: Run query with retry logic
            response = evaluate_query_with_retry(chat_service, test_case.question)

            # Extract sources
            sources = []
            if response.sources:
                for src in response.sources:
                    sources.append({
                        "text": src.text,
                        "score": src.score,
                        "source": src.source
                    })

            # Prepare for RAGAS
            # CONTEXT METRICS FIX: Don't pass fake sources for SQL-only queries
            # Empty sources list will cause calculate_ragas_metrics to skip context metrics (return None)
            ragas_sources = sources  # Don't provide fake sources!

            # Generate ground truth answer
            if test_case.ground_truth_data:
                if isinstance(test_case.ground_truth_data, dict):
                    ground_truth_answer = f"{test_case.ground_truth_data}"
                else:
                    ground_truth_answer = str(test_case.ground_truth_data)
            else:
                ground_truth_answer = "Expected answer based on test case"

            # RATE LIMIT FIX: Add delay before RAGAS to avoid 429 errors
            time.sleep(2)  # 2 second delay before RAGAS evaluation

            # P1 ISSUE #6 FIX: Calculate RAGAS metrics with graceful degradation
            ragas_metrics = calculate_ragas_safe(
                question=test_case.question,
                answer=response.answer,
                sources=ragas_sources,
                ground_truth=ground_truth_answer
            )

            # Analyze SQL complexity if applicable
            sql_complexity = None
            if response.generated_sql:
                sql_complexity = analyze_sql_complexity(response.generated_sql)

            # Build result
            result = {
                "batch_num": batch_num,
                "query_num": i,
                "original_index": original_idx,
                "question": test_case.question,
                "test_type": test_case.test_type.value,
                "category": test_case.category,
                "answer": response.answer,
                "generated_sql": response.generated_sql,
                "sql_complexity": sql_complexity,
                "tools_used": response.tools_used if hasattr(response, 'tools_used') else [],
                "sources": sources,
                "ragas_metrics": ragas_metrics,
                "processing_time_ms": response.processing_time_ms,
                "success": True,
            }

            # Detect issues
            issues = detect_issues(result)
            result["issues"] = issues

            results.append(result)

            # Print status
            if issues:
                critical = sum(1 for iss in issues if iss["severity"] == "critical")
                if critical > 0:
                    print(f"  ✗ Success (time: {response.processing_time_ms:.0f}ms)")
                    for issue in issues:
                        if issue["severity"] == "critical":
                            print(f"    ❌ {issue['message']}")
                else:
                    print(f"  ⚠ Success (time: {response.processing_time_ms:.0f}ms)")
            else:
                print(f"  ✓ Success (time: {response.processing_time_ms:.0f}ms)")

        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
            results.append({
                "batch_num": batch_num,
                "query_num": i,
                "original_index": original_idx,
                "question": test_case.question,
                "test_type": test_case.test_type.value,
                "category": test_case.category,
                "success": False,
                "error": str(e),
                "processing_time_ms": 0,  # Add default value for failed queries
            })

        # RATE LIMIT FIX: Add delay between queries to avoid 429 errors
        # Skip delay after last query
        if i < len(batch_queries):
            time.sleep(3)  # 3 second delay between queries

    end_time = datetime.now()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("evaluation_results/batches") / f"batch_{batch_num:02d}"
    results_dir.mkdir(parents=True, exist_ok=True)

    json_path = results_dir / f"batch_{batch_num:02d}_eval_{timestamp}.json"
    md_path = results_dir / f"batch_{batch_num:02d}_eval_{timestamp}.md"

    # Save JSON
    output_data = {
        "batch_num": batch_num,
        "timestamp": timestamp,
        "queries_tested": len(batch_queries),
        "results": results,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Generate markdown report
    generate_markdown_report(results, batch_num, timestamp, md_path)

    print(f"\n{'='*100}")
    print(f"✓ Batch #{batch_num} completed")
    print(f"✓ Results saved to: {json_path}")
    print(f"✓ Report saved to: {md_path}")
    print(f"{'='*100}\n")

    return md_path, json_path


def generate_markdown_report(results: list, batch_num: int, timestamp: str, output_path: Path):
    """Generate markdown report using the flexible eval template."""

    # Calculate summary statistics
    total_queries = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    failed = total_queries - successful
    success_rate = (successful / total_queries * 100) if total_queries > 0 else 0

    # Calculate average processing time
    processing_times = [r.get("processing_time_ms", 0) for r in results if r.get("success", False)]
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0

    # Calculate RAGAS averages
    ragas_sums = {}
    ragas_counts = {}

    for result in results:
        if result.get("ragas_metrics"):
            for metric, score in result["ragas_metrics"].items():
                if score is not None:
                    ragas_sums[metric] = ragas_sums.get(metric, 0) + score
                    ragas_counts[metric] = ragas_counts.get(metric, 0) + 1

    ragas_averages = {
        metric: ragas_sums[metric] / ragas_counts[metric]
        for metric in ragas_sums
    }

    # Count SQL complexity distribution
    complexity_dist = {}
    for result in results:
        if result.get("sql_complexity"):
            level = result["sql_complexity"]["level"]
            complexity_dist[level] = complexity_dist.get(level, 0) + 1

    # Collect all issues
    all_issues = []
    for result in results:
        if result.get("issues"):
            all_issues.extend(result["issues"])

    critical_issues = [iss for iss in all_issues if iss["severity"] == "critical"]
    warning_issues = [iss for iss in all_issues if iss["severity"] == "warning"]

    # Generate markdown
    lines = []
    lines.append(f"# Batch #{batch_num} Evaluation Report")
    lines.append(f"")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")
    lines.append(f"**Test Cases:** {total_queries}")
    lines.append(f"")
    lines.append(f"**Results JSON:** `batch_{batch_num:02d}_eval_{timestamp}.json`")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Executive Summary")
    lines.append(f"")
    lines.append(f"- **Total Queries:** {total_queries}")
    lines.append(f"- **Successful Executions:** {successful} ({success_rate:.1f}%)")
    lines.append(f"- **Failed Executions:** {failed}")
    lines.append(f"- **Average Processing Time:** {avg_time:.0f}ms")
    lines.append(f"")

    # RAGAS Metrics
    lines.append(f"### RAGAS Metrics (Averaged)")
    lines.append(f"")
    lines.append(f"| Metric | Score | Status |")
    lines.append(f"|--------|-------|--------|")

    for metric, score in sorted(ragas_averages.items()):
        status = "✅" if score >= 0.7 else ("⚠️" if score >= 0.5 else "❌")
        lines.append(f"| {metric} | {score:.3f} | {status} |")

    if not ragas_averages:
        lines.append(f"")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Issue Monitoring
    lines.append(f"## Issue Monitoring")
    lines.append(f"")
    lines.append(f"**Total Issues Detected:** {len(all_issues)}")
    lines.append(f"")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| ❌ Critical | {len(critical_issues)} |")
    lines.append(f"| ⚠️ Warning | {len(warning_issues)} |")
    lines.append(f"| ℹ️ Info | 0 |")
    lines.append(f"")

    if critical_issues:
        lines.append(f"### Critical Issues")
        lines.append(f"")
        for issue in critical_issues:
            lines.append(f"- **{issue['type']}**: {issue['message']}")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # SQL Complexity Distribution
    if complexity_dist:
        lines.append(f"## SQL Query Complexity Distribution")
        lines.append(f"")
        lines.append(f"| Complexity Level | Count |")
        lines.append(f"|------------------|-------|")
        for level in ["Trivial", "Simple", "Moderate", "Complex"]:
            count = complexity_dist.get(level, 0)
            if count > 0:
                lines.append(f"| {level} | {count} |")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    # Detailed Per-Query Results
    lines.append(f"## Detailed Per-Query Results")
    lines.append(f"")

    for result in results:
        query_num = result["query_num"]
        question = result["question"]
        test_type = result["test_type"]
        category = result.get("category", "unknown")

        lines.append(f"")
        lines.append(f"### Query #{query_num}: {question}")
        lines.append(f"")
        lines.append(f"**Type:** {test_type} | **Category:** {category}")
        lines.append(f"")

        if result.get("success"):
            answer = result["answer"]
            if len(answer) > 500:
                answer = answer[:500] + "..."

            lines.append(f"**Complete Answer:**")
            lines.append(f"```")
            lines.append(answer)
            lines.append(f"```")
            lines.append(f"")

            # SQL Query
            if result.get("generated_sql"):
                lines.append(f"**SQL Query:**")
                lines.append(f"```sql")
                lines.append(result["generated_sql"])
                lines.append(f"```")
                lines.append(f"")

                # SQL Complexity
                if result.get("sql_complexity"):
                    comp = result["sql_complexity"]
                    lines.append(f"**SQL Complexity:** {comp['level']} (score: {comp['score']})")
                    lines.append(f"- Joins: {comp['joins']}")
                    lines.append(f"- Filters: {comp['filters']}")
                    lines.append(f"- Aggregation: {'Yes' if comp['aggregation'] else 'No'}")
                    lines.append(f"- Subqueries: {'Yes' if comp['subqueries'] else 'No'}")
                    lines.append(f"")

            # Tools Used
            if result.get("tools_used"):
                lines.append(f"**Tools Used:** {', '.join(result['tools_used'])}")
                lines.append(f"")

            # RAGAS Metrics
            if result.get("ragas_metrics"):
                lines.append(f"**RAGAS Metrics:**")
                lines.append(f"")
                lines.append(f"| Metric | Score |")
                lines.append(f"|--------|-------|")

                for metric, score in sorted(result["ragas_metrics"].items()):
                    if score is not None:
                        status = "✅" if score >= 0.7 else ("⚠️" if score >= 0.5 else "❌")
                        lines.append(f"| {metric} | {score:.3f} {status} |")

                lines.append(f"")

            # Processing Time
            lines.append(f"**Processing Time:** {result['processing_time_ms']:.0f}ms")
            lines.append(f"")

            # Issues
            if result.get("issues"):
                lines.append(f"**Issues Detected:**")
                for issue in result["issues"]:
                    emoji = "❌" if issue["severity"] == "critical" else "⚠️"
                    lines.append(f"- {emoji} {issue['message']}")
                lines.append(f"")
        else:
            lines.append(f"**Error:** {result.get('error', 'Unknown error')}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    lines.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# P1 ISSUE #6 FIX: Retry logic for query evaluation
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
def evaluate_query_with_retry(chat_service: ChatService, query: str) -> dict:
    """Evaluate query with retry logic for transient failures.

    Retries up to 3 times with exponential backoff (4s, 8s, 16s) for:
    - ConnectionError
    - TimeoutError

    Rate limit errors (429) are handled internally by the agent with backoff.
    """
    request = ChatRequest(query=query)
    return chat_service.chat(request)


def calculate_ragas_safe(question: str, answer: str, sources: list, ground_truth: str) -> Optional[dict]:
    """Calculate RAGAS metrics with graceful degradation.

    Returns None if RAGAS calculation fails (e.g., rate limits),
    allowing the evaluation to continue with partial results.
    """
    try:
        return calculate_ragas_metrics(
            question=question,
            answer=answer,
            sources=sources,
            ground_truth_answer=ground_truth
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"RAGAS calculation failed: {e}. Continuing with None metrics.")
        # Return default None metrics
        return {
            "answer_correctness": None,
            "answer_relevancy": None,
            "answer_semantic_similarity": None,
            "context_precision": None,
            "context_relevancy": None,
            "faithfulness": None,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch evaluation")
    parser.add_argument("--batch", type=int, required=True, help="Batch number to run")

    args = parser.parse_args()

    run_batch_evaluation(args.batch)
