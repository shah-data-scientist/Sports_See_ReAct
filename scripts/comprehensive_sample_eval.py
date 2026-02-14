"""
FILE: comprehensive_sample_eval.py
STATUS: Active
RESPONSIBILITY: Comprehensive sample evaluation (2 test cases each) with full report generation
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path

from src.core.observability import logger
from src.evaluation.quality_analysis import analyze_results
from src.evaluation.consolidated_test_cases import ALL_TEST_CASES
from src.evaluation.unified_model import TestType
from src.models.chat import ChatRequest
from src.services.chat import ChatService

COMPREHENSIVE_OUTPUT_DIR = Path("evaluation_results/comprehensive_sample_2026_02_12")


def generate_sql_comprehensive_report(results: list, analysis: dict, json_path: str) -> str:
    """Generate comprehensive SQL evaluation report matching full runner format."""

    # Calculate summary statistics
    total_queries = len(results)
    successful_queries = sum(1 for r in results if r.get("success", False))
    failed_queries = total_queries - successful_queries
    success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0

    # Processing times
    processing_times = [r["processing_time_ms"] for r in results if r.get("success", False)]
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    min_processing_time = min(processing_times) if processing_times else 0
    max_processing_time = max(processing_times) if processing_times else 0

    # Calculate percentiles
    if processing_times:
        sorted_times = sorted(processing_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
    else:
        p50 = p95 = p99 = 0

    error_taxonomy = analysis.get("error_taxonomy", {})
    fallback_patterns = analysis.get("fallback_patterns", {})
    response_quality = analysis.get("response_quality", {})
    query_structure = analysis.get("query_structure", {})
    query_complexity = analysis.get("query_complexity", {})

    # Generate markdown report
    report = f"""# SQL Sample Evaluation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Dataset:** {total_queries} SQL test cases (sample)

**Results JSON:** `{json_path}`

---

## Executive Summary

- **Total Queries:** {total_queries}
- **Successful Executions:** {successful_queries} ({success_rate:.1f}%)
- **Failed Executions:** {failed_queries}
- **Avg Processing Time:** {avg_processing_time:.0f}ms
- **Min Processing Time:** {min_processing_time:.0f}ms
- **Max Processing Time:** {max_processing_time:.0f}ms
- **p50 Processing Time:** {p50:.0f}ms
- **p95 Processing Time:** {p95:.0f}ms
- **p99 Processing Time:** {p99:.0f}ms

## Failure Analysis

### Execution Failures

"""

    execution_failures = [r for r in results if not r.get("success", True)]
    if execution_failures:
        report += f"**Total:** {len(execution_failures)}\n\n"
        report += "| Question | Category | Error |\n"
        report += "|----------|----------|-------|\n"
        for failure in execution_failures:
            question = failure.get("question", "")[:60]
            category = failure.get("category", "unknown")
            error = str(failure.get("response", "Unknown error"))[:50]
            report += f"| {question} | {category} | {error} |\n"
        report += "\n"
    else:
        report += "✓ No execution failures detected.\n\n"

    # Response Quality Analysis
    report += """## Response Quality Analysis

### Error Taxonomy

"""
    report += f"""- **Total Errors:** {error_taxonomy.get('total_errors', 0)}
- **LLM Declined:** {len(error_taxonomy.get('llm_declined', []))}
- **Syntax Errors:** {len(error_taxonomy.get('syntax_error', []))}
- **Empty Responses:** {len(error_taxonomy.get('empty_response', []))}

### Response Quality Metrics

"""

    verbosity = response_quality.get("verbosity", {})
    if verbosity:
        report += f"""- **Avg Response Length:** {verbosity.get('avg_length', 0):.0f} chars
- **Min/Max Length:** {verbosity.get('min_length', 0)} / {verbosity.get('max_length', 0)} chars
"""

    # Fallback Patterns
    report += f"""
### Fallback Patterns

- **SQL Only:** {fallback_patterns.get('sql_only', 0)} ({fallback_patterns.get('sql_only', 0)/total_queries*100 if total_queries else 0:.1f}%)
- **Fallback to Vector:** {fallback_patterns.get('fallback_to_vector', 0)} ({fallback_patterns.get('fallback_to_vector', 0)/total_queries*100 if total_queries else 0:.1f}%)

## Query Quality Analysis

### Query Structure

"""

    report += f"""- **Total SQL Queries Generated:** {query_structure.get('total_queries', 0)}
- **Queries with JOIN:** {query_structure.get('queries_with_join', 0)}
- **Queries with Aggregation:** {query_structure.get('queries_with_aggregation', 0)}
- **Queries with Filter (WHERE):** {query_structure.get('queries_with_filter', 0)}
- **Queries with ORDER BY:** {query_structure.get('queries_with_ordering', 0)}
- **Queries with LIMIT:** {query_structure.get('queries_with_limit', 0)}

#### JOIN Correctness

- **Correct JOINs:** {query_structure.get('correctness', {}).get('correct_joins', 0)}
- **Missing JOINs:** {query_structure.get('correctness', {}).get('missing_joins', 0)}

### Query Complexity

"""

    report += f"""- **Avg JOINs per Query:** {query_complexity.get('avg_joins_per_query', 0):.2f}
- **Avg WHERE Conditions:** {query_complexity.get('avg_where_conditions', 0):.2f}
- **Queries with Subqueries:** {query_complexity.get('queries_with_subqueries', 0)}
- **Queries with GROUP BY:** {query_complexity.get('queries_with_group_by', 0)}
- **Queries with HAVING:** {query_complexity.get('queries_with_having', 0)}

## Detailed Test Results

### Query-by-Query Breakdown

"""

    for i, result in enumerate(results, 1):
        status = "✓ SUCCESS" if result.get("success") else "✗ FAILED"
        report += f"""
#### Test {i}: {status}

**Question:** {result.get('question', 'N/A')}

**Category:** {result.get('category', 'unknown')}

**Response Time:** {result.get('processing_time_ms', 0):.0f}ms

**Response:** {result.get('response', 'No response')[:300]}{'...' if len(result.get('response', '')) > 300 else ''}

"""

    return report


def generate_vector_comprehensive_report(results: list, analysis: dict, json_path: str) -> str:
    """Generate comprehensive Vector evaluation report matching full runner format."""

    # Calculate summary statistics
    total_queries = len(results)
    successful_queries = sum(1 for r in results if r.get("success", False))
    failed_queries = total_queries - successful_queries
    success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0

    # Processing times
    processing_times = [r["processing_time_ms"] for r in results if r.get("success", False)]
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    min_processing_time = min(processing_times) if processing_times else 0
    max_processing_time = max(processing_times) if processing_times else 0

    # Calculate percentiles
    if processing_times:
        sorted_times = sorted(processing_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
    else:
        p50 = p95 = p99 = 0

    source_quality = analysis.get("source_quality", {})
    retrieval_perf = analysis.get("retrieval_performance", {})
    response_patterns = analysis.get("response_patterns", {})

    # Generate markdown report
    report = f"""# Vector Sample Evaluation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Dataset:** {total_queries} Vector test cases (sample)

**Results JSON:** `{json_path}`

---

## Executive Summary

- **Total Queries:** {total_queries}
- **Successful Executions:** {successful_queries} ({success_rate:.1f}%)
- **Failed Executions:** {failed_queries}
- **Avg Processing Time:** {avg_processing_time:.0f}ms
- **Min Processing Time:** {min_processing_time:.0f}ms
- **Max Processing Time:** {max_processing_time:.0f}ms
- **p50 Processing Time:** {p50:.0f}ms
- **p95 Processing Time:** {p95:.0f}ms
- **p99 Processing Time:** {p99:.0f}ms

## Failure Analysis

### Execution Failures

"""

    execution_failures = [r for r in results if not r.get("success", True)]
    if execution_failures:
        report += f"**Total:** {len(execution_failures)}\n\n"
        report += "| Question | Error |\n"
        report += "|----------|-------|\n"
        for failure in execution_failures:
            question = failure.get("question", "")[:60]
            error = str(failure.get("response", "Unknown error"))[:80]
            report += f"| {question} | {error} |\n"
        report += "\n"
    else:
        report += "✓ No execution failures detected.\n\n"

    # Source Quality Analysis
    report += """## Source Quality Analysis

### Retrieval Statistics

"""

    retrieval_stats = source_quality.get("retrieval_stats", {})
    report += f"""- **Avg Sources per Query:** {retrieval_stats.get('avg_sources_per_query', 0):.1f}
- **Total Unique Sources:** {retrieval_stats.get('total_unique_sources', 0)}
- **Avg Similarity Score:** {retrieval_stats.get('avg_similarity_score', 0):.3f}

### Score Analysis

"""

    score_analysis = source_quality.get("score_analysis", {})
    report += f"""- **Min Score:** {score_analysis.get('min_score', 0):.3f}
- **Max Score:** {score_analysis.get('max_score', 0):.3f}

## Retrieval Performance

### Performance Metrics

"""

    perf_metrics = retrieval_perf.get("performance_metrics", {})
    report += f"""- **Avg Retrieval Score:** {perf_metrics.get('avg_retrieval_score', 0):.3f}
- **Retrieval Success Rate:** {perf_metrics.get('retrieval_success_rate', 0):.1f}%
- **Avg Processing Time:** {perf_metrics.get('avg_processing_time_ms', 0):.0f}ms

### K-Value Analysis

"""

    k_analysis = retrieval_perf.get("k_value_analysis", {})
    report += f"""- **Configured K:** {k_analysis.get('configured_k', 5)}
- **Actual Avg Retrieved:** {k_analysis.get('actual_avg_retrieved', 0):.1f}
- **Queries Below K:** {k_analysis.get('queries_below_k', 0)}

## Response Patterns

### Response Characteristics

"""

    resp_length = response_patterns.get("response_length", {})
    report += f"""- **Avg Response Length:** {resp_length.get('avg_length', 0):.0f} chars
- **Min/Max Length:** {resp_length.get('min_length', 0)} / {resp_length.get('max_length', 0)} chars

### Completeness

"""

    completeness = response_patterns.get("completeness", {})
    report += f"""- **Complete Answers:** {completeness.get('complete_answers', 0)}
- **Incomplete Answers:** {completeness.get('incomplete_answers', 0)}
- **Declined Answers:** {completeness.get('declined_answers', 0)}

## Detailed Test Results

### Query-by-Query Breakdown

"""

    for i, result in enumerate(results, 1):
        status = "✓ SUCCESS" if result.get("success") else "✗ FAILED"
        sources = result.get("sources", [])
        num_sources = len(sources) if isinstance(sources, list) else 0

        report += f"""
#### Test {i}: {status}

**Question:** {result.get('question', 'N/A')}

**Response Time:** {result.get('processing_time_ms', 0):.0f}ms

**Sources Retrieved:** {num_sources}

**Response:** {result.get('response', 'No response')[:300]}{'...' if len(result.get('response', '')) > 300 else ''}

"""

    return report


def run_sql_sample():
    """Run 2 SQL test cases with comprehensive report."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE SQL SAMPLE EVALUATION (2 test cases)")
    logger.info("=" * 80)

    service = ChatService()
    service.ensure_ready()

    test_cases = SQL_TEST_CASES[:2]
    results = []

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n[{i}/2] Testing: {test_case.question}")
        try:
            start_time = time.time()
            request = ChatRequest(query=test_case.question)
            response = service.chat(request)
            elapsed_ms = (time.time() - start_time) * 1000

            results.append({
                "question": test_case.question,
                "category": test_case.category,
                "response": response.answer if hasattr(response, 'answer') else "",
                "success": True,
                "processing_time_ms": elapsed_ms,
            })
            logger.info(f"✓ Success ({elapsed_ms:.0f}ms)")

        except Exception as e:
            logger.error(f"✗ Error: {e}")
            results.append({
                "question": test_case.question,
                "category": test_case.category,
                "response": str(e),
                "success": False,
                "processing_time_ms": 0,
            })

    # Analyze results
    analysis = {
        "error_taxonomy": analyze_error_taxonomy(results),
        "fallback_patterns": analyze_fallback_patterns(results),
        "response_quality": analyze_response_quality(results),
        "query_structure": analyze_query_structure(results),
        "query_complexity": analyze_query_complexity(results),
        "column_selection": analyze_column_selection(results),
    }

    # Save files (only 2: results JSON + report markdown, analysis is internal only)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    COMPREHENSIVE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = COMPREHENSIVE_OUTPUT_DIR / f"sql_evaluation_{timestamp}.json"
    report_path = COMPREHENSIVE_OUTPUT_DIR / f"sql_evaluation_report_{timestamp}.md"

    # Save results JSON
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Generate report using analysis (analysis is NOT saved separately)
    report = generate_sql_comprehensive_report(results, analysis, str(json_path.name))
    report_path.write_text(report, encoding="utf-8")

    logger.info(f"\n✓ SQL evaluation complete!")
    logger.info(f"  JSON: {json_path.name}")
    logger.info(f"  Report: {report_path.name}")

    return report_path


def run_vector_sample():
    """Run 2 Vector test cases with comprehensive report."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE VECTOR SAMPLE EVALUATION (2 test cases)")
    logger.info("=" * 80)

    service = ChatService()
    service.ensure_ready()

    test_cases = EVALUATION_TEST_CASES[:2]
    results = []

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n[{i}/2] Testing: {test_case.question}")
        try:
            start_time = time.time()
            request = ChatRequest(query=test_case.question)
            response = service.chat(request)
            elapsed_ms = (time.time() - start_time) * 1000

            results.append({
                "question": test_case.question,
                "category": str(test_case.category),
                "response": response.answer if hasattr(response, 'answer') else "",
                "sources": response.sources if hasattr(response, 'sources') else [],
                "success": True,
                "processing_time_ms": elapsed_ms,
            })
            logger.info(f"✓ Success ({elapsed_ms:.0f}ms, {len(response.sources if hasattr(response, 'sources') else [])} sources)")

        except Exception as e:
            logger.error(f"✗ Error: {e}")
            results.append({
                "question": test_case.question,
                "category": str(test_case.category),
                "response": str(e),
                "sources": [],
                "success": False,
                "processing_time_ms": 0,
            })

    # Analyze results
    analysis = {
        "source_quality": analyze_source_quality(results),
        "retrieval_performance": analyze_retrieval_performance(results),
        "response_patterns": analyze_response_patterns(results),
    }

    # Save files (only 2: results JSON + report markdown, analysis is internal only)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    COMPREHENSIVE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = COMPREHENSIVE_OUTPUT_DIR / f"vector_evaluation_{timestamp}.json"
    report_path = COMPREHENSIVE_OUTPUT_DIR / f"vector_evaluation_report_{timestamp}.md"

    # Save results JSON
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Generate report using analysis (analysis is NOT saved separately)
    report = generate_vector_comprehensive_report(results, analysis, str(json_path.name))
    report_path.write_text(report, encoding="utf-8")

    logger.info(f"\n✓ Vector evaluation complete!")
    logger.info(f"  JSON: {json_path.name}")
    logger.info(f"  Report: {report_path.name}")

    return report_path


if __name__ == "__main__":
    logger.info("Starting comprehensive sample evaluations...")
    logger.info(f"Output directory: {COMPREHENSIVE_OUTPUT_DIR.absolute()}\n")

    sql_report = run_sql_sample()
    vector_report = run_vector_sample()

    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE SAMPLE EVALUATIONS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nAll files saved to: {COMPREHENSIVE_OUTPUT_DIR.absolute()}")
    logger.info("\nGenerated Reports:")
    logger.info(f"  SQL: {sql_report.name}")
    logger.info(f"  Vector: {vector_report.name}")
    logger.info("\n✓ Comprehensive reports ready for review!")
