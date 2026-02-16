"""
FILE: evaluator.py
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

from google import genai
from starlette.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_chat_service
from evaluation.test_data import ALL_TEST_CASES, get_statistics
from evaluation.models import UnifiedTestCase, TestType, UnifiedEvaluationResult
from evaluation.metrics import calculate_ragas_metrics
from src.models.feedback import ChatInteractionCreate
from src.core.config import settings

logger = logging.getLogger(__name__)

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


def _validate_sql_results(
    expected: dict | list | None,
    actual: dict | list | None,
    tolerance: float = 0.01
) -> dict[str, Any]:
    """Compare expected vs actual SQL results to detect query bugs or data changes.

    Args:
        expected: Ground truth SQL results from test case
        actual: Actual SQL results from API
        tolerance: Tolerance for numeric comparisons (default 1%)

    Returns:
        Dict with:
        - match (bool): Do results match?
        - mismatches (list): List of mismatches if any
        - error (str|None): Error message if validation failed
    """
    # Both None or empty
    if expected is None and actual is None:
        return {"match": True, "mismatches": [], "error": None}

    if expected is None or actual is None:
        return {
            "match": False,
            "mismatches": ["One result is None, other is not"],
            "error": f"Expected: {type(expected)}, Actual: {type(actual)}"
        }

    # Type mismatch
    if type(expected) != type(actual):
        return {
            "match": False,
            "mismatches": [f"Type mismatch: expected {type(expected)}, got {type(actual)}"],
            "error": "Result type differs"
        }

    mismatches = []

    # List of results (multiple rows)
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            mismatches.append(f"Row count mismatch: expected {len(expected)} rows, got {len(actual)}")

        # Compare each row
        for i, (exp_row, act_row) in enumerate(zip(expected, actual)):
            row_mismatches = _compare_sql_row(exp_row, act_row, tolerance)
            if row_mismatches:
                mismatches.append(f"Row {i}: {', '.join(row_mismatches)}")

    # Single result (dict)
    elif isinstance(expected, dict) and isinstance(actual, dict):
        row_mismatches = _compare_sql_row(expected, actual, tolerance)
        mismatches.extend(row_mismatches)

    else:
        # Scalar comparison
        if expected != actual:
            mismatches.append(f"Value mismatch: expected {expected}, got {actual}")

    return {
        "match": len(mismatches) == 0,
        "mismatches": mismatches,
        "error": None if len(mismatches) == 0 else "Results differ from ground truth"
    }


def _compare_sql_row(expected: dict, actual: dict | tuple | list, tolerance: float) -> list[str]:
    """Compare two SQL result rows.

    Handles:
    - Dict and tuple/list formats
    - Column name normalization (pts vs PTS)
    - Numeric tolerance
    - Missing columns

    Args:
        expected: Expected row (dict format)
        actual: Actual row (dict, tuple, or list format)
        tolerance: Numeric comparison tolerance

    Returns:
        List of mismatch descriptions (empty if match)
    """
    mismatches = []

    # Convert tuple/list to dict if needed
    if isinstance(actual, (tuple, list)):
        # If actual is tuple/list but expected is dict, we can't compare properly
        # unless we know the column names. Return error.
        mismatches.append(f"Type mismatch: expected dict, got {type(actual).__name__}")
        mismatches.append(f"Cannot compare dict with {type(actual).__name__} without column names")
        return mismatches

    # Normalize keys (lowercase for case-insensitive comparison)
    exp_norm = {k.lower(): v for k, v in expected.items()}
    act_norm = {k.lower(): v for k, v in actual.items()}

    # Check each expected column
    for key, exp_val in exp_norm.items():
        if key not in act_norm:
            mismatches.append(f"Missing column '{key}'")
            continue

        act_val = act_norm[key]

        # Numeric comparison with tolerance
        if isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
            diff = abs(exp_val - act_val)
            threshold = abs(exp_val * tolerance)  # Relative tolerance
            if diff > threshold:
                mismatches.append(f"{key}: expected {exp_val}, got {act_val} (diff: {diff:.2f})")
        # String comparison
        elif exp_val != act_val:
            mismatches.append(f"{key}: expected '{exp_val}', got '{act_val}'")

    # Check for extra columns in actual
    for key in act_norm:
        if key not in exp_norm:
            mismatches.append(f"Extra column '{key}' in actual results")

    return mismatches


def _generate_ground_truth_answer(
    test_case: UnifiedTestCase,
    actual_sql_results: dict | list | None,
    actual_vector_sources: list[dict] | None
) -> str:
    """Generate expected answer using judge LLM based on ACTUAL retrieval results.

    CRITICAL FIX: Judge LLM now sees the SAME context as the main LLM for fair comparison.

    WHY THIS MATTERS:
    - Previous approach: Judge saw ground_truth_data, Main LLM saw actual SQL results
    - This invalidated ALL answer quality metrics (different contexts = unfair comparison)
    - New approach: Both see identical SQL and vector results

    Args:
        test_case: Test case with question
        actual_sql_results: ACTUAL SQL results from API (not ground truth)
        actual_vector_sources: ACTUAL retrieved chunks from API (not ground truth)

    Returns:
        Expected answer generated by judge LLM from ACTUAL context (same as main LLM)
    """
    # Initialize judge LLM client (same model as main LLM for consistency)
    api_key = settings.google_api_key
    if not api_key:
        logger.warning("No Google API key found - using placeholder ground truth answer")
        return "Expected answer (API key not configured)"

    client = genai.Client(api_key=api_key)

    # Build prompt using SAME logic as ReAct agent (_build_combined_prompt)
    # CRITICAL CHANGE: Use ACTUAL results seen by main LLM, not ground truth
    # See: src/agents/react_agent.py lines 182-236

    sql_result = actual_sql_results if actual_sql_results is not None else "No results"
    vector_result = actual_vector_sources if actual_vector_sources else "No results"

    # Format results for readability (EXACTLY as main LLM sees them)
    sql_formatted = json.dumps(sql_result, indent=2) if sql_result != "No results" else "No results"

    # Format vector sources like main LLM receives them (list of dicts with text/score/source)
    if vector_result != "No results":
        vector_formatted = json.dumps(vector_result, indent=2, ensure_ascii=False)
    else:
        vector_formatted = "No results"

    # Use EXACT same prompt structure as main LLM
    judge_prompt = f"""You are an NBA statistics assistant. You have been provided with results from TWO sources:

1. SQL DATABASE (factual statistics - THIS IS YOUR SOURCE OF TRUTH FOR NUMBERS)
2. VECTOR SEARCH (contextual information, opinions, analysis)

CRITICAL RULES:
1. SQL results are ALWAYS the source of truth for statistics, scores, numbers
2. If SQL has the answer, use it (you may ignore vector if irrelevant)
3. If SQL and vector conflict on factual stats, TRUST SQL
4. Use vector results for context, opinions, "why/how" questions, background info
5. Combine both intelligently when both add value
6. If both sources are empty or irrelevant, say you don't have enough information

USER QUESTION:
{test_case.question}

SQL DATABASE RESULTS (FACTUAL STATS):
{sql_formatted}

VECTOR SEARCH RESULTS (CONTEXT & OPINIONS):
{vector_formatted}

CONVERSATION HISTORY:
None

Based on the above information, provide a complete, accurate answer to the user's question.
Focus on being helpful and concise. If the results don't answer the question, say so clearly.

Your answer:"""

    try:
        # Call judge LLM with same temperature as main LLM (0.1 for consistency)
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Same model as main LLM
            contents=judge_prompt,
            config={"temperature": 0.1},  # Same temperature as ReAct agent
        )

        generated_answer = response.text.strip()
        logger.debug(f"Judge LLM generated expected answer (length: {len(generated_answer)} chars)")
        return generated_answer

    except Exception as e:
        logger.error(f"Judge LLM failed to generate ground truth answer: {e}")
        # Fallback: return a descriptive message using actual results
        if sql_result != "No results":
            return f"Expected answer based on actual SQL: {json.dumps(sql_result)[:200]}"
        elif vector_result != "No results":
            return f"Expected answer based on actual vector context: {str(vector_result)[:200]}"
        else:
            return "Expected answer (no data available - both SQL and vector returned empty)"


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
                    # STEP 1: Build API request payload and call main LLM FIRST
                    logger.debug("Calling main LLM...")
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
                    logger.debug(f"Main LLM returned answer (length: {len(api_result.get('answer', ''))} chars)")

                    # STEP 2: NOW generate ground truth answer using judge LLM
                    # CRITICAL: Judge LLM sees SAME context (actual SQL + vector results) as main LLM
                    logger.debug("Generating ground truth answer with judge LLM (using ACTUAL results)...")
                    ground_truth_answer = _generate_ground_truth_answer(
                        test_case=test_case,
                        actual_sql_results=api_result.get("sql_results"),  # Actual SQL from API
                        actual_vector_sources=api_result.get("sources")   # Actual chunks from API
                    )
                    logger.debug(f"Judge LLM generated expected answer (length: {len(ground_truth_answer)} chars)")

                    # STEP 3: Validate SQL results (if SQL test case)
                    sql_validation = None
                    if test_case.ground_truth_data is not None:
                        logger.debug("Validating SQL results against ground truth...")
                        sql_validation = _validate_sql_results(
                            expected=test_case.ground_truth_data,
                            actual=api_result.get("sql_results"),
                            tolerance=0.01  # 1% tolerance for numeric values
                        )

                        if not sql_validation["match"]:
                            logger.warning(f"SQL validation FAILED: {sql_validation['error']}")
                            for mismatch in sql_validation["mismatches"][:3]:  # Show first 3
                                logger.warning(f"  - {mismatch}")
                        else:
                            logger.debug("SQL validation PASSED")

                    # STEP 3.5: Validate retrieval behavior based on test type
                    sources_count = len(api_result.get("sources", []))
                    retrieval_warnings = []

                    if case_type == "sql":
                        # SQL-only should NOT retrieve vector sources
                        if sources_count > 0:
                            warning = f"SQL-only query returned {sources_count} vector sources (wasteful - should be 0)"
                            retrieval_warnings.append(warning)
                            logger.warning(f"  ⚠️ {warning}")

                    elif case_type == "vector":
                        # Vector query MUST retrieve sources
                        if sources_count == 0:
                            warning = "Vector query returned 0 sources (retrieval failed)"
                            retrieval_warnings.append(warning)
                            logger.error(f"  ❌ {warning}")
                        else:
                            logger.debug(f"Vector query retrieved {sources_count} sources ✓")

                    elif case_type == "hybrid":
                        # Hybrid should retrieve sources AND have SQL results
                        if sources_count == 0:
                            warning = "Hybrid query returned 0 sources (vector search failed)"
                            retrieval_warnings.append(warning)
                            logger.warning(f"  ⚠️ {warning}")

                        has_sql = api_result.get("sql_results") is not None or api_result.get("generated_sql") is not None
                        if not has_sql:
                            warning = "Hybrid query has no SQL results (SQL search failed)"
                            retrieval_warnings.append(warning)
                            logger.warning(f"  ⚠️ {warning}")

                        if sources_count > 0 and has_sql:
                            logger.debug(f"Hybrid query: {sources_count} sources + SQL ✓")

                    # STEP 4: Calculate RAGAS metrics (now fair - both LLMs saw same context)
                    logger.debug("Calculating RAGAS metrics...")
                    ragas_metrics = calculate_ragas_metrics(
                        question=test_case.question,
                        answer=api_result.get("answer", ""),
                        sources=api_result.get("sources", []),
                        ground_truth_answer=ground_truth_answer,  # From judge LLM (same context)
                    )
                    logger.debug(f"RAGAS metrics calculated: {ragas_metrics}")

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
                        ragas_metrics=ragas_metrics,  # All 7 RAGAS metrics calculated above
                        # Ground truth fields from test case
                        ground_truth_vector=test_case.ground_truth_vector,
                        ground_truth_answer=ground_truth_answer,  # Dynamically generated by judge LLM
                        ground_truth_data=test_case.ground_truth_data,
                        sql_validation=sql_validation,  # SQL validation results (if SQL test case)
                        retrieval_warnings=retrieval_warnings,  # Retrieval validation warnings
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
    """Generate comprehensive markdown report with quality analysis and RAGAS metrics."""
    from evaluation.analyzer import analyze_results

    report_path = Path("evaluation_results") / f"evaluation_{test_type}_report_{timestamp}.md"

    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    success_rate = (successful / len(results) * 100) if results else 0

    # Calculate processing time statistics
    processing_times = [r["processing_time_ms"] for r in results if r.get("success") and "processing_time_ms" in r]
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    min_time = min(processing_times) if processing_times else 0
    max_time = max(processing_times) if processing_times else 0

    # Run comprehensive quality analysis
    logger.info("Running quality analysis...")
    analysis = analyze_results(results)

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

        # ====================================================================
        # QUALITY ANALYSIS SECTION
        # ====================================================================

        # RAGAS Metrics (if available)
        if "ragas_metrics" in analysis:
            ragas = analysis["ragas_metrics"]

            f.write("\n\n" + "=" * 80 + "\n")
            f.write("# RAGAS METRICS ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            # Overall metrics
            f.write("## Overall RAGAS Metrics\n\n")
            f.write("| Metric | Score | Interpretation |\n")
            f.write("|--------|-------|----------------|\n")

            overall = ragas.get("overall", {})
            for metric_key, metric_value in overall.items():
                if metric_value is not None:
                    metric_name = metric_key.replace("avg_", "").replace("_", " ").title()

                    # Interpretation
                    if metric_value >= 0.9:
                        interp = "✅ EXCELLENT"
                    elif metric_value >= 0.7:
                        interp = "⚠️  GOOD"
                    elif metric_value >= 0.5:
                        interp = "⚠️  WARNING"
                    else:
                        interp = "❌ CRITICAL"

                    # Mark Answer Correctness as BEST OVERALL
                    if "correctness" in metric_key:
                        metric_name += " ⭐ BEST"

                    f.write(f"| {metric_name} | {metric_value:.3f} | {interp} |\n")
            f.write("\n")

            # By category
            if ragas.get("by_category"):
                f.write("## RAGAS Metrics by Category\n\n")
                f.write("| Category | Count | Faithfulness | Answer Correctness | Context Precision | Context Recall |\n")
                f.write("|----------|-------|--------------|-------------------|-------------------|----------------|\n")

                for cat, cat_metrics in ragas["by_category"].items():
                    count = cat_metrics.get("count", 0)
                    faith = cat_metrics.get("avg_faithfulness")
                    correct = cat_metrics.get("avg_answer_correctness")
                    prec = cat_metrics.get("avg_context_precision")
                    recall = cat_metrics.get("avg_context_recall")

                    faith_str = f"{faith:.3f}" if faith is not None else "N/A"
                    correct_str = f"{correct:.3f}" if correct is not None else "N/A"
                    prec_str = f"{prec:.3f}" if prec is not None else "N/A"
                    recall_str = f"{recall:.3f}" if recall is not None else "N/A"

                    f.write(f"| {cat} | {count} | {faith_str} | {correct_str} | {prec_str} | {recall_str} |\n")
                f.write("\n")

            # Low scoring queries
            if ragas.get("low_scoring_queries"):
                low_queries = ragas["low_scoring_queries"][:10]  # Top 10 worst
                f.write(f"## Low Scoring Queries (< 0.7) - Top {len(low_queries)}\n\n")

                for i, query in enumerate(low_queries, 1):
                    f.write(f"### {i}. {query.get('category', 'unknown').upper()}\n\n")
                    f.write(f"**Question:** {query.get('question', '')[:100]}...\n\n")
                    f.write(f"**Scores:**\n")
                    f.write(f"- Min Score: {query.get('min_score', 0):.3f}\n")
                    f.write(f"- Faithfulness: {query.get('faithfulness', 'N/A')}\n")
                    f.write(f"- Answer Correctness: {query.get('answer_correctness', 'N/A')}\n")
                    f.write(f"- Answer Relevancy: {query.get('answer_relevancy', 'N/A')}\n")

                    if query.get('context_precision') is not None:
                        f.write(f"- Context Precision: {query.get('context_precision', 'N/A')}\n")
                        f.write(f"- Context Recall: {query.get('context_recall', 'N/A')}\n")

                    f.write("\n")

            # Nuclear explanations
            f.write("\n" + "=" * 80 + "\n")
            f.write("# RAGAS METRICS - NUCLEAR EXPLANATIONS\n")
            f.write("=" * 80 + "\n\n")

            explanations = ragas.get("metric_explanations", {})
            for metric_name in ["faithfulness", "answer_relevancy", "answer_semantic_similarity",
                               "answer_correctness", "context_precision", "context_recall", "context_relevancy"]:
                if metric_name in explanations:
                    f.write(f"## {metric_name.replace('_', ' ').title()}\n\n")
                    f.write("```\n")
                    f.write(explanations[metric_name].strip())
                    f.write("\n```\n\n")

        # SQL-specific analysis
        if "error_taxonomy" in analysis:
            f.write("\n" + "=" * 80 + "\n")
            f.write("# SQL ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            taxonomy = analysis["error_taxonomy"]
            f.write(f"## Error Taxonomy\n\n")
            f.write(f"- Total Errors: {taxonomy.get('total_errors', 0)}\n")
            f.write(f"- LLM Declined: {len(taxonomy.get('llm_declined', []))}\n")
            f.write(f"- Syntax Errors: {len(taxonomy.get('syntax_error', []))}\n")
            f.write(f"- Empty Responses: {len(taxonomy.get('empty_response', []))}\n\n")

        if "query_structure" in analysis:
            structure = analysis["query_structure"]
            f.write(f"## Query Structure Analysis\n\n")
            f.write(f"- Total Queries: {structure.get('total_queries', 0)}\n")
            f.write(f"- Queries with JOIN: {structure.get('queries_with_join', 0)}\n")
            f.write(f"- Queries with Aggregation: {structure.get('queries_with_aggregation', 0)}\n")
            f.write(f"- Queries with Filter: {structure.get('queries_with_filter', 0)}\n\n")

        # Vector-specific analysis
        if "source_quality" in analysis:
            f.write("\n" + "=" * 80 + "\n")
            f.write("# VECTOR SEARCH ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            source_qual = analysis["source_quality"]
            retrieval_stats = source_qual.get("retrieval_stats", {})
            f.write(f"## Retrieval Statistics\n\n")
            f.write(f"- Avg Sources per Query: {retrieval_stats.get('avg_sources_per_query', 0):.2f}\n")
            f.write(f"- Total Unique Sources: {retrieval_stats.get('total_unique_sources', 0)}\n")
            f.write(f"- Avg Similarity Score: {retrieval_stats.get('avg_similarity_score', 0):.2f}\n")
            f.write(f"- Empty Retrievals: {source_qual.get('empty_retrievals', 0)}\n\n")

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
    from evaluation.unified_test_cases import print_statistics
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
        logger.info("Mini mode: running limited test cases")

    try:
        results, json_path = run_unified_evaluation(
            test_type=args.type,
            resume=not args.no_resume,
            test_indices=test_indices
        )

        logger.info("=" * 80)
        logger.info(f"EVALUATION COMPLETE{' (MINI)' if args.mini else ''}")
        logger.info("=" * 80)
        logger.info("Results saved to:")
        logger.info(f"  - JSON: {json_path}")
        logger.info(f"  - Report: {json_path.replace('.json', '_report.md')}")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("⚠️ Evaluation interrupted by user. Re-run to resume from checkpoint.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
