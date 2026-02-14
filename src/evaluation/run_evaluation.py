"""
FILE: run_evaluation.py
STATUS: Active
RESPONSIBILITY: Unified evaluation runner for SQL, Vector, and Hybrid test cases (206 total)
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

FEATURES:
- Single unified runner for all evaluation types
- API-based testing via TestClient
- Checkpointing for crash recovery
- Conversation thread support
- Comprehensive analysis and reporting
- Filtering by test type (--type sql|vector|hybrid|all)
"""

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from starlette.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_chat_service
from src.evaluation.consolidated_test_cases import ALL_TEST_CASES, get_statistics
from src.evaluation.unified_model import UnifiedTestCase, TestType, QueryType, UnifiedEvaluationResult
from src.models.feedback import ChatInteractionCreate
from src.core.observability import logger

# Rate limiting configuration (Gemini free tier: 15 RPM)
RATE_LIMIT_DELAY_SECONDS = 20
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 30
BATCH_SIZE = 10
BATCH_COOLDOWN_SECONDS = 30


def _load_checkpoint(checkpoint_path: Path) -> dict | None:
    """Load existing checkpoint if present."""
    if checkpoint_path.exists():
        try:
            data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            logger.info(f"Checkpoint loaded: {data['evaluated_count']}/{data['total_cases']} queries completed")
            return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None
    return None


def _save_checkpoint(checkpoint_path: Path, results: list[dict], next_index: int, total_cases: int) -> None:
    """Save checkpoint after each query (atomic write)."""
    checkpoint = {
        "checkpoint_version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "total_cases": total_cases,
        "evaluated_count": len(results),
        "remaining_count": total_cases - len(results),
        "results": results,
        "next_index": next_index
    }

    # Atomic write: write to temp file, then rename
    temp_path = checkpoint_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(checkpoint_path)  # Atomic on Windows/Unix


def _cleanup_checkpoint(checkpoint_path: Path) -> None:
    """Delete checkpoint file after successful completion."""
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        logger.info("Checkpoint file cleaned up")


def _retry_api_call(api_call_func, max_retries: int = MAX_RETRIES):
    """Retry API call with exponential backoff on 429 errors."""
    for attempt in range(max_retries + 1):
        try:
            return api_call_func()
        except Exception as e:
            error_msg = str(e)
            is_rate_limit = "429" in error_msg and ("RESOURCE_EXHAUSTED" in error_msg or "rate" in error_msg.lower())

            if is_rate_limit and attempt < max_retries:
                wait_time = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(f"  ⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                             f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                # Non-rate-limit error or final attempt - re-raise
                raise

    raise RuntimeError("Max retries exhausted")


def _determine_test_type(test_case: UnifiedTestCase) -> str:
    """Determine test type from unified test case object."""
    return test_case.test_type.value  # Returns 'sql', 'vector', or 'hybrid'


def run_unified_evaluation(
    test_type: str = "all",
    resume: bool = True,
    test_indices: list[int] | None = None
) -> tuple[list[dict], str]:
    """Run unified evaluation for specified test type(s).

    Args:
        test_type: Type of tests to run ('sql', 'vector', 'hybrid', 'all')
        resume: Whether to resume from checkpoint (default: True)
        test_indices: Optional list of test case indices to run (for mini mode)

    Returns:
        Tuple of (results list, json_path string)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)

    # Select test cases based on type
    if test_type == "all":
        test_cases = ALL_TEST_CASES
        run_label = "UNIFIED (SQL + Vector + Hybrid)"
    else:
        # Filter by test_type
        test_cases = [tc for tc in ALL_TEST_CASES if tc.test_type.value == test_type]
        run_label = f"{test_type.upper()}"

    if test_indices is not None:
        test_cases = [test_cases[i] for i in test_indices if i < len(test_cases)]
        logger.info(f"Mini mode: running {len(test_cases)} test cases")

    logger.info("=" * 80)
    logger.info(f"EVALUATION: {run_label}")
    logger.info(f"Test Cases: {len(test_cases)}")
    logger.info(f"Mode: API-based (POST /api/v1/chat)")
    logger.info("=" * 80)

    checkpoint_path = output_dir / f"evaluation_{test_type}_{timestamp}.checkpoint.json"
    json_path = output_dir / f"evaluation_{test_type}_{timestamp}.json"

    # Load checkpoint if resuming
    results = []
    start_index = 0

    if resume:
        checkpoint = _load_checkpoint(checkpoint_path)
        if checkpoint:
            results = checkpoint["results"]
            start_index = checkpoint["next_index"]
            logger.info(f"Resuming from query {start_index + 1}/{len(test_cases)}")

    total_cases = len(test_cases)

    # Initialize tracking statistics
    routing_stats = {"sql_only": 0, "vector_only": 0, "hybrid": 0, "unknown": 0, "greeting": 0}
    misclassifications = []
    type_stats = {"sql": 0, "vector": 0, "hybrid": 0, "unknown": 0}

    if start_index >= total_cases:
        logger.info(f"All {total_cases} queries already evaluated (from checkpoint)")
    else:
        logger.info(f"Starting evaluation: {len(test_cases)} test cases")
        logger.info(f"Rate limit delay: {RATE_LIMIT_DELAY_SECONDS}s between queries")

        # Run evaluation via API
        app = create_app()

        with TestClient(app) as client:
            # Access ChatService for conversation storage
            chat_service = get_chat_service()

            current_conversation_id = None
            current_turn_number = 0
            current_thread = None

            for i in range(start_index, total_cases):
                test_case = test_cases[i]
                case_type = _determine_test_type(test_case)
                type_stats[case_type] += 1

                # Get category for logging
                category_str = test_case.category or "unknown"

                logger.info(f"[{i + 1}/{total_cases}] [{case_type.upper()}] {category_str}: {test_case.question[:60]}...")

                # Rate limiting (skip for first query of batch)
                if i > start_index:
                    queries_done = i - start_index
                    if queries_done > 0 and queries_done % BATCH_SIZE == 0:
                        logger.info(f"  Batch cooldown: {BATCH_COOLDOWN_SECONDS}s (after {queries_done} queries)...")
                        time.sleep(BATCH_COOLDOWN_SECONDS)
                    logger.info(f"  Rate limit delay: {RATE_LIMIT_DELAY_SECONDS}s...")
                    time.sleep(RATE_LIMIT_DELAY_SECONDS)

                # Handle conversational test cases using conversation_thread field
                if hasattr(test_case, 'conversation_thread') and test_case.conversation_thread:
                    if test_case.conversation_thread != current_thread:
                        conv_resp = client.post("/api/v1/conversations", json={})
                        current_conversation_id = conv_resp.json()["id"]
                        current_turn_number = 1
                        current_thread = test_case.conversation_thread
                        logger.info(f"  → New conversation thread: {current_thread}")
                    else:
                        current_turn_number += 1
                        logger.info(f"  → Continue thread: {current_thread} (turn {current_turn_number})")
                else:
                    current_conversation_id = None
                    current_turn_number = 0
                    current_thread = None

                try:
                    # Build API request payload
                    payload = {
                        "query": test_case.question,
                        "k": 5,
                        "include_sources": True,
                        "conversation_id": current_conversation_id,
                        "turn_number": current_turn_number if current_conversation_id else 1,
                    }

                    # API call with retry logic
                    def api_call():
                        response = client.post("/api/v1/chat", json=payload, timeout=30)
                        if response.status_code != 200:
                            raise RuntimeError(f"API error {response.status_code}: {response.text[:300]}")
                        return response.json()

                    api_result = _retry_api_call(api_call)

                    # Store interaction for conversation context
                    if current_conversation_id:
                        interaction = ChatInteractionCreate(
                            query=test_case.question,
                            response=api_result.get("answer", ""),
                            sources=[s.get("source", "") for s in api_result.get("sources", [])],
                            processing_time_ms=int(api_result.get("processing_time_ms", 0)),
                            conversation_id=current_conversation_id,
                            turn_number=current_turn_number,
                        )
                        chat_service.feedback_repository.save_interaction(interaction)

                    # Determine actual routing from API response
                    query_type_response = api_result.get("query_type", "unknown")

                    if query_type_response == "statistical":
                        actual_routing = "sql_only"
                    elif query_type_response == "contextual":
                        actual_routing = "vector_only"
                    elif query_type_response == "hybrid":
                        actual_routing = "hybrid"
                    elif query_type_response == "greeting":
                        actual_routing = "greeting"
                    else:
                        actual_routing = "unknown"

                    routing_stats[actual_routing] += 1

                    # Determine expected routing based on test case type
                    if case_type == "sql":
                        expected_routing = "sql_only"
                    elif case_type == "vector":
                        expected_routing = "vector_only"
                    elif case_type == "hybrid":
                        expected_routing = "hybrid"
                    else:
                        expected_routing = "unknown"

                    is_misclassified = actual_routing != expected_routing and actual_routing != "hybrid" and expected_routing != "hybrid"

                    if is_misclassified:
                        misclassifications.append({
                            "question": test_case.question,
                            "category": category_str,
                            "test_type": case_type,
                            "expected": expected_routing,
                            "actual": actual_routing,
                            "response_preview": api_result.get("answer", "")[:150]
                        })

                    # Record result using UnifiedEvaluationResult
                    result_entry = UnifiedEvaluationResult(
                        question=test_case.question,
                        test_type=case_type,
                        category=category_str,
                        success=True,
                        response=api_result.get("answer", ""),
                        processing_time_ms=api_result.get("processing_time_ms", 0),
                        expected_routing=expected_routing,
                        actual_routing=actual_routing,
                        is_misclassified=is_misclassified,
                        generated_sql=api_result.get("generated_sql"),
                        sql_results=None,  # Not returned by API
                        visualization=api_result.get("visualization"),
                        sources=[
                            {
                                "text": s.get("text", "")[:500],
                                "score": s.get("score", 0),
                                "source": s.get("source", "unknown")
                            }
                            for s in api_result.get("sources", [])
                        ],
                        sources_count=len(api_result.get("sources", [])),
                        ragas_metrics=None,  # Calculated later in analysis
                        ground_truth=test_case.ground_truth,
                        ground_truth_answer=test_case.ground_truth_answer,
                        ground_truth_data=test_case.ground_truth_data,
                        conversation_id=current_conversation_id,
                        turn_number=current_turn_number,
                        timestamp=datetime.now().isoformat(),
                    )

                    results.append(result_entry.to_dict())

                    status = "[PASS]" if not is_misclassified else "[MISCLASS]"
                    logger.info(f"  {status} Expected: {expected_routing} | Actual: {actual_routing} | "
                               f"Sources: {len(api_result.get('sources', []))} | Time: {api_result.get('processing_time_ms', 0)}ms")

                except Exception as e:
                    logger.error(f"  ✗ Failed: {str(e)}")
                    error_result = UnifiedEvaluationResult(
                        question=test_case.question,
                        test_type=case_type,
                        category=category_str,
                        success=False,
                        error=str(e),
                        expected_routing=expected_routing if 'expected_routing' in locals() else "unknown",
                        actual_routing="error",
                        timestamp=datetime.now().isoformat(),
                    )
                    results.append(error_result.to_dict())

                # Save checkpoint after EACH query
                _save_checkpoint(checkpoint_path, results, i + 1, total_cases)

    # Calculate statistics
    successful = sum(1 for r in results if r.get("success"))
    failed = total_cases - successful
    success_rate = (successful / total_cases * 100) if total_cases else 0

    # Save final JSON results
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "mode": f"unified_evaluation_{test_type}",
        "total_cases": total_cases,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "routing_stats": routing_stats,
        "type_stats": type_stats,
        "misclassifications_count": len(misclassifications),
        "misclassifications": misclassifications,
        "results": results
    }

    json_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Results saved to: {json_path}")

    # Generate summary report
    logger.info("Generating summary report...")
    report_path = generate_summary_report(results, str(json_path), timestamp, test_type, routing_stats, type_stats, misclassifications)
    logger.info(f"Report saved to: {report_path}")

    # Cleanup checkpoint
    _cleanup_checkpoint(checkpoint_path)

    logger.info("=" * 80)
    logger.info("EVALUATION COMPLETE")
    logger.info(f"Successful: {successful}/{total_cases} ({success_rate:.1f}%)")
    logger.info(f"Failed: {failed}/{total_cases}")
    logger.info(f"Misclassifications: {len(misclassifications)}")
    logger.info("=" * 80)

    return results, str(json_path)


def generate_summary_report(
    results: list[dict],
    json_path: str,
    timestamp: str,
    test_type: str,
    routing_stats: dict,
    type_stats: dict,
    misclassifications: list
) -> str:
    """Generate summary markdown report."""
    report_path = Path("evaluation_results") / f"evaluation_{test_type}_report_{timestamp}.md"

    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    success_rate = (successful / len(results) * 100) if results else 0

    # Calculate processing time statistics
    processing_times = [r["processing_time_ms"] for r in results if r.get("success") and "processing_time_ms" in r]
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    min_time = min(processing_times) if processing_times else 0
    max_time = max(processing_times) if processing_times else 0

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Unified Evaluation Report - {test_type.upper()}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Dataset:** {len(results)} test cases\n\n")
        f.write(f"**Results JSON:** `{Path(json_path).name}`\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Queries:** {len(results)}\n")
        f.write(f"- **Successful Executions:** {successful} ({success_rate:.1f}%)\n")
        f.write(f"- **Failed Executions:** {failed}\n")
        f.write(f"- **Misclassifications:** {len(misclassifications)}\n")
        f.write(f"- **Avg Processing Time:** {avg_time:.0f}ms\n")
        f.write(f"- **Min/Max Processing Time:** {min_time:.0f}ms / {max_time:.0f}ms\n\n")

        # Test Type Distribution
        f.write("### Test Type Distribution\n\n")
        f.write("| Type | Count | Percentage |\n")
        f.write("|------|-------|------------|\n")
        total_typed = sum(type_stats.values())
        for t_type, count in sorted(type_stats.items()):
            pct = (count / total_typed * 100) if total_typed > 0 else 0
            f.write(f"| {t_type.upper()} | {count} | {pct:.1f}% |\n")
        f.write("\n")

        # Routing Statistics
        f.write("### Routing Statistics\n\n")
        f.write("| Routing | Count | Percentage |\n")
        f.write("|---------|-------|------------|\n")
        total_routed = sum(routing_stats.values())
        for routing, count in sorted(routing_stats.items()):
            pct = (count / total_routed * 100) if total_routed > 0 else 0
            f.write(f"| {routing} | {count} | {pct:.1f}% |\n")
        f.write("\n")

        # Misclassifications
        if misclassifications:
            f.write(f"### Misclassifications ({len(misclassifications)} queries)\n\n")
            f.write("| # | Question | Test Type | Expected | Actual | Response Preview |\n")
            f.write("|---|----------|-----------|----------|--------|------------------|\n")
            for i, misc in enumerate(misclassifications[:20], 1):
                f.write(f"| {i} | {misc['question'][:40]}... | {misc['test_type']} | "
                       f"{misc['expected']} | {misc['actual']} | {misc['response_preview'][:80]}... |\n")
            f.write("\n")

        # Performance by Category
        f.write("## Performance by Category\n\n")
        category_stats = defaultdict(lambda: {"count": 0, "success": 0, "times": []})
        for r in results:
            cat = r.get("category", "unknown")
            category_stats[cat]["count"] += 1
            if r.get("success"):
                category_stats[cat]["success"] += 1
            if "processing_time_ms" in r:
                category_stats[cat]["times"].append(r["processing_time_ms"])

        f.write("| Category | Count | Success Rate | Avg Time |\n")
        f.write("|----------|-------|--------------|----------|\n")
        for cat in sorted(category_stats.keys()):
            stats = category_stats[cat]
            success_rate = (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0
            avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
            f.write(f"| {cat} | {stats['count']} | {success_rate:.1f}% | {avg_time:.0f}ms |\n")
        f.write("\n")

        f.write("---\n\n")
        f.write(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return str(report_path)


def main():
    """Main entry point for unified evaluation."""
    parser = argparse.ArgumentParser(description="Unified evaluation runner for SQL, Vector, and Hybrid test cases")
    parser.add_argument("--type", choices=["sql", "vector", "hybrid", "all"], default="all",
                       help="Type of tests to run (default: all)")
    parser.add_argument("--mini", action="store_true",
                       help="Run mini evaluation with limited test cases")
    parser.add_argument("--no-resume", action="store_true",
                       help="Start fresh (ignore checkpoint)")
    args = parser.parse_args()

    # Print statistics
    from src.evaluation.unified_test_cases import print_statistics
    print_statistics()

    test_indices = None
    if args.mini:
        # Select 4 diverse cases per type
        if args.type == "sql" or args.type == "all":
            test_indices = [0, 13, 20, 27]  # simple, comparison, aggregation, complex
        elif args.type == "vector":
            test_indices = [0, 3, 5, 22]  # simple, noisy, conversational, complex
        elif args.type == "hybrid":
            test_indices = [0, 4, 10, 18]  # tier1, tier2, tier3, tier4
        print(f"\nMini mode: running limited test cases")

    try:
        results, json_path = run_unified_evaluation(
            test_type=args.type,
            resume=not args.no_resume,
            test_indices=test_indices
        )

        print("\n" + "="*80)
        print(f"EVALUATION COMPLETE{' (MINI)' if args.mini else ''}")
        print("="*80)
        print(f"\nResults saved to:")
        print(f"  - JSON: {json_path}")
        print(f"  - Report: {json_path.replace('.json', '_report.md')}")
        print("\n" + "="*80)

    except KeyboardInterrupt:
        print("\n\n⚠️ Evaluation interrupted by user. Re-run to resume from checkpoint.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
