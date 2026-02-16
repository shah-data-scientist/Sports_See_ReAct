"""
FILE: hybrid_quality_analysis.py
STATUS: Active
RESPONSIBILITY: Hybrid evaluation analysis coordination - unified interface analyze_results(), SQL+Vector combination analysis, report generation
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu

Comprehensive hybrid evaluation quality analysis that reuses SQL and Vector
analysis functions for detailed metrics:
- SQL: error taxonomy, query structure, complexity, column selection, fallback
- Vector: source quality, retrieval performance, response patterns
- Hybrid: routing analysis, combination quality, category performance
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.analysis.sql_quality_analysis import (
    analyze_column_selection,
    analyze_error_taxonomy,
    analyze_fallback_patterns,
    analyze_query_complexity,
    analyze_query_structure,
    analyze_response_quality,
)
from evaluation.analysis.vector_quality_analysis import (
    analyze_response_patterns,
    analyze_retrieval_performance,
    analyze_source_quality,
)


def analyze_hybrid_results(results: list[dict], test_cases: list) -> dict[str, Any]:
    """
    Analyze hybrid evaluation results with comprehensive quality metrics.

    Combines SQL and Vector analysis functions with hybrid-specific metrics.

    Args:
        results: List of evaluation results from run_hybrid_evaluation
        test_cases: List of test case objects

    Returns:
        Dictionary with comprehensive quality analysis
    """
    # Hybrid-specific analysis
    analysis = {
        "overall": _analyze_overall_performance(results),
        "routing": _analyze_routing_quality(results),
        "sql_component": _analyze_sql_component(results),
        "vector_component": _analyze_vector_component(results),
        "hybrid_combination": _analyze_hybrid_combination(results),
        "performance": _analyze_performance(results),
        "by_category": _analyze_by_category(results),
        "failures": _analyze_failures(results),
    }

    # Reuse SQL quality analysis functions
    analysis["error_taxonomy"] = analyze_error_taxonomy(results)
    analysis["fallback_patterns"] = analyze_fallback_patterns(results)
    analysis["response_quality"] = analyze_response_quality(results)
    analysis["query_structure"] = analyze_query_structure(results)
    analysis["query_complexity"] = analyze_query_complexity(results)
    analysis["column_selection"] = analyze_column_selection(results)

    # Reuse Vector quality analysis functions
    analysis["source_quality"] = analyze_source_quality(results)
    analysis["response_patterns"] = analyze_response_patterns(results)
    analysis["retrieval_performance"] = analyze_retrieval_performance(results)

    return analysis


# ---------------------------------------------------------------------------
# Hybrid-specific analysis functions
# ---------------------------------------------------------------------------

def _analyze_overall_performance(results: list[dict]) -> dict[str, Any]:
    """Analyze overall success rates and basic metrics."""
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    failed = total - successful

    has_response = sum(1 for r in results if r.get("success") and len(r.get("response", "")) > 10)
    has_sources = sum(1 for r in results if r.get("success") and r.get("sources_count", 0) > 0)

    return {
        "total_queries": total,
        "successful": successful,
        "failed": failed,
        "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
        "has_response_rate": round(has_response / successful * 100, 1) if successful > 0 else 0,
        "has_sources_rate": round(has_sources / successful * 100, 1) if successful > 0 else 0,
    }


def _analyze_routing_quality(results: list[dict]) -> dict[str, Any]:
    """Analyze routing decisions (SQL vs Vector vs Both)."""
    routing_counts = defaultdict(int)

    for result in results:
        if result.get("success"):
            routing = result.get("routing", "unknown")
            routing_counts[routing] += 1

    total_routed = sum(routing_counts.values())

    routing_analysis = {
        "sql_only": routing_counts.get("sql", 0),
        "vector_only": routing_counts.get("vector", 0),
        "both_hybrid": routing_counts.get("both", 0),
        "unknown": routing_counts.get("unknown", 0),
        "total_routed": total_routed,
    }

    if total_routed > 0:
        routing_analysis["sql_only_pct"] = round(routing_counts.get("sql", 0) / total_routed * 100, 1)
        routing_analysis["vector_only_pct"] = round(routing_counts.get("vector", 0) / total_routed * 100, 1)
        routing_analysis["both_hybrid_pct"] = round(routing_counts.get("both", 0) / total_routed * 100, 1)
        routing_analysis["unknown_pct"] = round(routing_counts.get("unknown", 0) / total_routed * 100, 1)

    return routing_analysis


def _analyze_sql_component(results: list[dict]) -> dict[str, Any]:
    """Analyze SQL component of hybrid queries."""
    sql_queries = [r for r in results if r.get("success") and r.get("routing") in ["sql", "both"]]

    if not sql_queries:
        return {"sql_queries": 0, "note": "No SQL component in results"}

    has_generated_sql = sum(1 for r in sql_queries if r.get("generated_sql"))

    analysis = {
        "sql_queries": len(sql_queries),
        "has_generated_sql": has_generated_sql,
        "sql_generation_rate": round(has_generated_sql / len(sql_queries) * 100, 1) if sql_queries else 0,
    }

    sql_statements = [r.get("generated_sql", "") for r in sql_queries if r.get("generated_sql")]
    if sql_statements:
        has_join = sum(1 for s in sql_statements if "JOIN" in s.upper())
        has_where = sum(1 for s in sql_statements if "WHERE" in s.upper())
        has_order = sum(1 for s in sql_statements if "ORDER BY" in s.upper())
        has_limit = sum(1 for s in sql_statements if "LIMIT" in s.upper())
        has_group = sum(1 for s in sql_statements if "GROUP BY" in s.upper())

        analysis["sql_complexity"] = {
            "with_join": has_join,
            "with_where": has_where,
            "with_order_by": has_order,
            "with_limit": has_limit,
            "with_group_by": has_group,
        }

    return analysis


def _analyze_vector_component(results: list[dict]) -> dict[str, Any]:
    """Analyze Vector component of hybrid queries."""
    vector_queries = [r for r in results if r.get("success") and r.get("routing") in ["vector", "both"]]

    if not vector_queries:
        return {"vector_queries": 0, "note": "No vector component in results"}

    has_sources = sum(1 for r in vector_queries if r.get("sources_count", 0) > 0)
    source_counts = [r.get("sources_count", 0) for r in vector_queries]

    analysis = {
        "vector_queries": len(vector_queries),
        "has_sources": has_sources,
        "sources_rate": round(has_sources / len(vector_queries) * 100, 1) if vector_queries else 0,
        "avg_sources": round(sum(source_counts) / len(source_counts), 1) if source_counts else 0,
        "min_sources": min(source_counts) if source_counts else 0,
        "max_sources": max(source_counts) if source_counts else 0,
    }

    unique_sources = set()
    for result in vector_queries:
        sources = result.get("sources", [])
        if sources:
            for source in sources:
                if isinstance(source, dict):
                    unique_sources.add(source.get("source", ""))
                elif isinstance(source, str):
                    unique_sources.add(source)

    if unique_sources:
        analysis["unique_sources"] = len(unique_sources)
        analysis["top_sources"] = sorted(list(unique_sources))[:10]

    return analysis


def _analyze_hybrid_combination(results: list[dict]) -> dict[str, Any]:
    """Analyze quality of hybrid queries that use BOTH SQL and Vector."""
    hybrid_queries = [r for r in results if r.get("success") and r.get("routing") == "both"]

    if not hybrid_queries:
        return {"hybrid_queries": 0, "note": "No true hybrid queries (both SQL + Vector)"}

    has_both_data = sum(
        1 for r in hybrid_queries
        if r.get("generated_sql") and r.get("sources_count", 0) > 0
    )

    response_lengths = [len(r.get("response", "")) for r in hybrid_queries]

    analysis = {
        "hybrid_queries": len(hybrid_queries),
        "has_both_data": has_both_data,
        "both_data_rate": round(has_both_data / len(hybrid_queries) * 100, 1) if hybrid_queries else 0,
        "avg_response_length": round(sum(response_lengths) / len(response_lengths), 0) if response_lengths else 0,
        "min_response_length": min(response_lengths) if response_lengths else 0,
        "max_response_length": max(response_lengths) if response_lengths else 0,
    }

    return analysis


def _analyze_performance(results: list[dict]) -> dict[str, Any]:
    """Analyze processing time and performance metrics."""
    successful = [r for r in results if r.get("success")]

    if not successful:
        return {"note": "No successful queries to analyze"}

    processing_times = [r.get("processing_time_ms", 0) for r in successful]

    analysis = {
        "avg_processing_time_ms": round(sum(processing_times) / len(processing_times), 0) if processing_times else 0,
        "min_processing_time_ms": round(min(processing_times), 0) if processing_times else 0,
        "max_processing_time_ms": round(max(processing_times), 0) if processing_times else 0,
        "median_processing_time_ms": round(_median(processing_times), 0) if processing_times else 0,
    }

    by_routing = defaultdict(list)
    for result in successful:
        routing = result.get("routing", "unknown")
        by_routing[routing].append(result.get("processing_time_ms", 0))

    analysis["by_routing"] = {}
    for routing, times in by_routing.items():
        if times:
            analysis["by_routing"][routing] = {
                "count": len(times),
                "avg_ms": round(sum(times) / len(times), 0),
                "min_ms": round(min(times), 0),
                "max_ms": round(max(times), 0),
            }

    return analysis


def _analyze_by_category(results: list[dict]) -> dict[str, Any]:
    """Analyze results grouped by test case category."""
    by_category = defaultdict(lambda: {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "routing": defaultdict(int),
        "processing_times": [],
    })

    for result in results:
        category = result.get("category", "unknown")
        by_category[category]["total"] += 1

        if result.get("success"):
            by_category[category]["successful"] += 1
            routing = result.get("routing", "unknown")
            by_category[category]["routing"][routing] += 1
            by_category[category]["processing_times"].append(result.get("processing_time_ms", 0))
        else:
            by_category[category]["failed"] += 1

    category_analysis = {}
    for category, stats in by_category.items():
        category_analysis[category] = {
            "total": stats["total"],
            "successful": stats["successful"],
            "failed": stats["failed"],
            "success_rate": round(stats["successful"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            "routing_distribution": dict(stats["routing"]),
            "avg_processing_time_ms": round(
                sum(stats["processing_times"]) / len(stats["processing_times"]), 0
            ) if stats["processing_times"] else 0,
        }

    return category_analysis


def _analyze_failures(results: list[dict]) -> dict[str, Any]:
    """Analyze failed queries and error patterns."""
    failures = [r for r in results if not r.get("success")]

    if not failures:
        return {"total_failures": 0, "note": "No failures to analyze"}

    error_types = defaultdict(int)
    error_examples = []

    for result in failures:
        error = result.get("error", "Unknown error")

        if "timeout" in error.lower():
            error_types["timeout"] += 1
        elif "rate limit" in error.lower() or "429" in error:
            error_types["rate_limit"] += 1
        elif "sql" in error.lower():
            error_types["sql_error"] += 1
        elif "vector" in error.lower() or "search" in error.lower():
            error_types["vector_error"] += 1
        else:
            error_types["other"] += 1

        if len(error_examples) < 5:
            error_examples.append({
                "question": result.get("question", "")[:80] + "...",
                "error": error[:200],
                "category": result.get("category", "unknown"),
            })

    return {
        "total_failures": len(failures),
        "failure_rate": round(len(failures) / len(results) * 100, 1) if results else 0,
        "error_types": dict(error_types),
        "error_examples": error_examples,
    }


def _median(values: list[float]) -> float:
    """Calculate median of a list of values."""
    if not values:
        return 0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    return sorted_values[n // 2]


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def generate_markdown_report(
    results: list[dict],
    analysis: dict[str, Any],
    test_cases: list,
    output_file: Path,
) -> None:
    """
    Generate comprehensive Markdown report for hybrid evaluation.

    Matches the depth of SQL and Vector evaluation reports with 11 sections.

    Args:
        results: Evaluation results
        analysis: Quality analysis dictionary from analyze_hybrid_results
        test_cases: Test case objects
        output_file: Path to output markdown file
    """
    lines = []

    # -- 1. Header -----------------------------------------------------------
    lines.append("# Hybrid Evaluation Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Dataset:** {len(test_cases)} hybrid test cases")
    lines.append(f"**Results JSON:** `{output_file.stem.replace('_report', '')}.json`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # -- 2. Executive Summary ------------------------------------------------
    overall = analysis["overall"]
    perf = analysis["performance"]
    routing = analysis["routing"]

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total Queries:** {overall['total_queries']}")
    lines.append(f"- **Successful Executions:** {overall['successful']} ({overall['success_rate']}%)")
    lines.append(f"- **Failed Executions:** {overall['failed']}")
    lines.append(f"- **Response Quality:** {overall['has_response_rate']}% have meaningful responses")
    lines.append(f"- **Source Retrieval:** {overall['has_sources_rate']}% retrieved sources")
    if "avg_processing_time_ms" in perf:
        lines.append(f"- **Avg Processing Time:** {perf['avg_processing_time_ms']}ms")
    lines.append("")
    lines.append("### Routing Summary")
    lines.append("")
    lines.append(f"- **SQL Only:** {routing.get('sql_only', 0)}")
    lines.append(f"- **Vector Only:** {routing.get('vector_only', 0)}")
    lines.append(f"- **Both (Hybrid):** {routing.get('both_hybrid', 0)}")
    lines.append(f"- **Unknown:** {routing.get('unknown', 0)}")
    lines.append("")

    # -- 3. Failure Analysis -------------------------------------------------
    lines.append("## Failure Analysis")
    lines.append("")

    lines.append("### Execution Failures")
    lines.append("")
    failures = [r for r in results if not r.get("success")]
    if failures:
        lines.append(f"**{len(failures)} queries failed:**")
        lines.append("")
        lines.append("| # | Question | Category | Error |")
        lines.append("|---|----------|----------|-------|")
        for i, f in enumerate(failures[:10], 1):
            q = f.get("question", "")[:60] + "..."
            cat = f.get("category", "unknown")
            err = f.get("error", "")[:80]
            lines.append(f"| {i} | {q} | {cat} | {err} |")
        lines.append("")
    else:
        lines.append("No execution failures detected.")
        lines.append("")

    taxonomy = analysis.get("error_taxonomy", {})
    lines.append("### Error Taxonomy")
    lines.append("")
    lines.append(f"- **Total Errors:** {taxonomy.get('total_errors', 0)}")
    lines.append(f"- **LLM Declined:** {len(taxonomy.get('llm_declined', []))}")
    lines.append(f"- **Syntax Errors:** {len(taxonomy.get('syntax_error', []))}")
    lines.append(f"- **Empty Responses:** {len(taxonomy.get('empty_response', []))}")
    lines.append("")

    lines.append("### Performance Metrics")
    lines.append("")
    if "avg_processing_time_ms" in perf:
        lines.append(f"- **Average Processing Time:** {perf['avg_processing_time_ms']}ms")
        lines.append(f"- **Median Processing Time:** {perf['median_processing_time_ms']}ms")
        lines.append(f"- **Min Processing Time:** {perf['min_processing_time_ms']}ms")
        lines.append(f"- **Max Processing Time:** {perf['max_processing_time_ms']}ms")
    lines.append("")

    # -- 4. Routing Analysis -------------------------------------------------
    lines.append("## Routing Analysis")
    lines.append("")
    lines.append("Distribution of routing decisions:")
    lines.append("")
    lines.append("| Routing Type | Count | Percentage |")
    lines.append("|--------------|-------|------------|")
    lines.append(f"| SQL Only | {routing.get('sql_only', 0)} | {routing.get('sql_only_pct', 0)}% |")
    lines.append(f"| Vector Only | {routing.get('vector_only', 0)} | {routing.get('vector_only_pct', 0)}% |")
    lines.append(f"| Both (Hybrid) | {routing.get('both_hybrid', 0)} | {routing.get('both_hybrid_pct', 0)}% |")
    lines.append(f"| Unknown | {routing.get('unknown', 0)} | {routing.get('unknown_pct', 0)}% |")
    lines.append("")

    fallback = analysis.get("fallback_patterns", {})
    lines.append("### Fallback Patterns")
    lines.append("")
    lines.append(f"- **SQL Only:** {fallback.get('sql_only', 0)} ({100 - fallback.get('fallback_rate', 0):.1f}%)")
    lines.append(f"- **Fallback to Vector:** {fallback.get('fallback_to_vector', 0)} ({fallback.get('fallback_rate', 0):.1f}%)")
    lines.append("")

    fallback_by_cat = fallback.get("by_category", {})
    if fallback_by_cat:
        lines.append("#### Fallback by Category")
        lines.append("")
        lines.append("| Category | Total | Fallbacks | Rate |")
        lines.append("|----------|-------|-----------|------|")
        for cat, stats in sorted(fallback_by_cat.items()):
            lines.append(f"| {cat} | {stats['total']} | {stats['fallbacks']} | {stats['rate']:.1f}% |")
        lines.append("")

    # -- 5. SQL Component Analysis -------------------------------------------
    lines.append("## SQL Component Analysis")
    lines.append("")

    sql_comp = analysis["sql_component"]
    if sql_comp.get("sql_queries", 0) > 0:
        lines.append(f"- **Queries with SQL:** {sql_comp['sql_queries']}")
        lines.append(f"- **SQL Generated:** {sql_comp['has_generated_sql']} ({sql_comp['sql_generation_rate']}%)")
        lines.append("")

    qs = analysis.get("query_structure", {})
    if qs.get("total_queries", 0) > 0:
        total_q = qs["total_queries"]
        lines.append("### Query Structure")
        lines.append("")
        lines.append(f"- **Total SQL Queries Generated:** {total_q}")
        lines.append(f"- **Queries with JOIN:** {qs.get('queries_with_join', 0)} ({qs.get('queries_with_join', 0) / total_q * 100:.1f}%)")
        lines.append(f"- **Queries with Aggregation:** {qs.get('queries_with_aggregation', 0)} ({qs.get('queries_with_aggregation', 0) / total_q * 100:.1f}%)")
        lines.append(f"- **Queries with Filter (WHERE):** {qs.get('queries_with_filter', 0)} ({qs.get('queries_with_filter', 0) / total_q * 100:.1f}%)")
        lines.append(f"- **Queries with ORDER BY:** {qs.get('queries_with_ordering', 0)} ({qs.get('queries_with_ordering', 0) / total_q * 100:.1f}%)")
        lines.append(f"- **Queries with LIMIT:** {qs.get('queries_with_limit', 0)} ({qs.get('queries_with_limit', 0) / total_q * 100:.1f}%)")
        lines.append("")

        correctness = qs.get("correctness", {})
        if correctness.get("correct_joins", 0) > 0 or correctness.get("missing_joins", 0) > 0:
            lines.append("#### JOIN Correctness")
            lines.append("")
            lines.append(f"- **Correct JOINs:** {correctness.get('correct_joins', 0)}")
            lines.append(f"- **Missing JOINs:** {correctness.get('missing_joins', 0)}")
            lines.append("")

    qc = analysis.get("query_complexity", {})
    if qc.get("total_queries", 0) > 0:
        lines.append("### Query Complexity")
        lines.append("")
        lines.append(f"- **Avg JOINs per Query:** {qc.get('avg_joins_per_query', 0):.2f}")
        lines.append(f"- **Avg WHERE Conditions:** {qc.get('avg_where_conditions', 0):.2f}")
        lines.append(f"- **Queries with Subqueries:** {qc.get('queries_with_subqueries', 0)}")
        lines.append(f"- **Queries with GROUP BY:** {qc.get('queries_with_group_by', 0)}")
        lines.append(f"- **Queries with HAVING:** {qc.get('queries_with_having', 0)}")
        lines.append("")

        complexity_dist = qc.get("complexity_distribution", {})
        if complexity_dist:
            total_q = qc["total_queries"]
            lines.append("#### Complexity Distribution")
            lines.append("")
            lines.append("| Level | Count | Percentage |")
            lines.append("|-------|-------|------------|")
            for level in ["simple", "moderate", "complex", "very_complex"]:
                count = complexity_dist.get(level, 0)
                pct = round(count / total_q * 100, 1) if total_q > 0 else 0
                lines.append(f"| {level.replace('_', ' ').title()} | {count} | {pct}% |")
            lines.append("")

    cs = analysis.get("column_selection", {})
    if cs.get("total_queries", 0) > 0:
        lines.append("### Column Selection")
        lines.append("")
        lines.append(f"- **Avg Columns Selected:** {cs.get('avg_columns_selected', 0):.2f}")
        lines.append(f"- **SELECT * Usage:** {cs.get('select_star_count', 0)} queries")
        lines.append(f"- **Over-selection Rate:** {cs.get('over_selection_rate', 0):.1f}%")
        lines.append(f"- **Under-selection Rate:** {cs.get('under_selection_rate', 0):.1f}%")
        lines.append("")

    if sql_comp.get("sql_queries", 0) == 0 and qs.get("total_queries", 0) == 0:
        lines.append("No SQL component detected in results.")
        lines.append("")

    # -- 6. Vector Component Analysis ----------------------------------------
    lines.append("## Vector Component Analysis")
    lines.append("")

    sq = analysis.get("source_quality", {})
    retrieval_stats = sq.get("retrieval_stats", {})
    if retrieval_stats:
        lines.append("### Source Quality")
        lines.append("")
        lines.append(f"- **Average Sources per Query:** {retrieval_stats.get('avg_sources_per_query', 0)}")
        lines.append(f"- **Total Unique Sources:** {retrieval_stats.get('total_unique_sources', 0)}")
        lines.append(f"- **Average Similarity Score:** {retrieval_stats.get('avg_similarity_score', 0):.2f}%")
        lines.append(f"- **Empty Retrievals:** {sq.get('empty_retrievals', 0)}")
        lines.append("")

    source_diversity = sq.get("source_diversity", {})
    top_sources = source_diversity.get("top_sources", [])
    if top_sources:
        lines.append("**Top Sources:**")
        lines.append("")
        lines.append("| Rank | Source | Count | Avg Score |")
        lines.append("|------|--------|-------|-----------|")
        for i, src in enumerate(top_sources[:10], 1):
            lines.append(f"| {i} | {src.get('source', '')} | {src.get('count', 0)} | {src.get('avg_score', 0):.1f}% |")
        lines.append("")

    score_analysis = sq.get("score_analysis", {})
    score_dist = score_analysis.get("score_distribution", {})
    if score_dist:
        lines.append("### Score Distribution")
        lines.append("")
        lines.append("| Score Range | Count |")
        lines.append("|-------------|-------|")
        for range_name, count in score_dist.items():
            lines.append(f"| {range_name} | {count} |")
        lines.append("")

    rp = analysis.get("retrieval_performance", {})
    perf_metrics = rp.get("performance_metrics", {})
    if perf_metrics:
        lines.append("### Retrieval Performance")
        lines.append("")
        lines.append(f"- **Average Retrieval Score:** {perf_metrics.get('avg_retrieval_score', 0):.2f}%")
        lines.append(f"- **Retrieval Success Rate:** {perf_metrics.get('retrieval_success_rate', 0) * 100:.1f}%")
        lines.append(f"- **Avg Processing Time:** {perf_metrics.get('avg_processing_time_ms', 0)}ms")
        lines.append("")

    kv = rp.get("k_value_analysis", {})
    if kv:
        lines.append("### K-Value Analysis")
        lines.append("")
        lines.append(f"- **Configured K:** {kv.get('configured_k', 5)}")
        lines.append(f"- **Actual Avg Retrieved:** {kv.get('actual_avg_retrieved', 0)}")
        lines.append(f"- **Queries Below K:** {kv.get('queries_below_k', 0)}")
        lines.append("")

    by_source_type = rp.get("by_source_type", {})
    if by_source_type:
        lines.append("### Performance by Source Type")
        lines.append("")
        lines.append("| Source Type | Count | Avg Score |")
        lines.append("|-------------|-------|-----------|")
        for stype, stats in sorted(by_source_type.items()):
            lines.append(f"| {stype} | {stats.get('count', 0)} | {stats.get('avg_score', 0):.1f}% |")
        lines.append("")

    # -- 7. Response Quality Analysis ----------------------------------------
    lines.append("## Response Quality Analysis")
    lines.append("")

    rp_data = analysis.get("response_patterns", {})
    resp_length = rp_data.get("response_length", {})
    if resp_length:
        lines.append("### Response Length")
        lines.append("")
        lines.append(f"- **Avg Response Length:** {resp_length.get('avg_length', 0):.0f} chars")
        lines.append(f"- **Min/Max Length:** {resp_length.get('min_length', 0)} / {resp_length.get('max_length', 0)} chars")
        lines.append("")

        dist = resp_length.get("distribution", {})
        if dist:
            lines.append("| Length Category | Count |")
            lines.append("|----------------|-------|")
            for cat, count in dist.items():
                lines.append(f"| {cat.replace('_', ' ').title()} | {count} |")
            lines.append("")

    completeness = rp_data.get("completeness", {})
    if completeness:
        lines.append("### Completeness")
        lines.append("")
        lines.append(f"- **Complete Answers:** {completeness.get('complete_answers', 0)}")
        lines.append(f"- **Incomplete Answers:** {completeness.get('incomplete_answers', 0)}")
        lines.append(f"- **Declined Answers:** {completeness.get('declined_answers', 0)}")
        lines.append("")

    confidence = rp_data.get("confidence_indicators", {})
    if confidence:
        lines.append("### Confidence Indicators")
        lines.append("")
        lines.append(f"- **Responses with Hedging:** {confidence.get('hedging_count', 0)}")
        lines.append(f"- **Confident Responses:** {confidence.get('confident_count', 0)}")
        hedging_patterns = confidence.get("hedging_patterns", [])
        if hedging_patterns:
            lines.append(f"- **Hedging Patterns:** {', '.join(hedging_patterns)}")
        lines.append("")

    citations = rp_data.get("citation_patterns", {})
    if citations:
        lines.append("### Citation Patterns")
        lines.append("")
        lines.append(f"- **Responses with Citations:** {citations.get('responses_with_citations', 0)}")
        lines.append(f"- **Avg Citations per Response:** {citations.get('avg_citations_per_response', 0):.2f}")
        lines.append("")

    # -- 8. Hybrid Combination Quality ---------------------------------------
    hybrid_comp = analysis["hybrid_combination"]
    lines.append("## Hybrid Combination Quality")
    lines.append("")
    if hybrid_comp.get("hybrid_queries", 0) > 0:
        lines.append(f"- **True Hybrid Queries:** {hybrid_comp['hybrid_queries']} (both SQL + Vector)")
        lines.append(f"- **Both Data Types Present:** {hybrid_comp['has_both_data']} ({hybrid_comp['both_data_rate']}%)")
        lines.append(f"- **Avg Response Length:** {hybrid_comp['avg_response_length']:.0f} chars")
        lines.append(f"- **Response Length Range:** {hybrid_comp['min_response_length']} - {hybrid_comp['max_response_length']} chars")
    else:
        lines.append(f"No true hybrid queries detected (routing={routing.get('both_hybrid', 0)} queries used both SQL + Vector).")
    lines.append("")

    # -- 9. Performance by Category ------------------------------------------
    by_cat = analysis["by_category"]
    if by_cat:
        lines.append("## Performance by Category")
        lines.append("")
        lines.append("| Category | Total | Success Rate | Routing | Avg Time |")
        lines.append("|----------|-------|--------------|---------|----------|")
        for category, stats in sorted(by_cat.items()):
            routing_dist = stats.get("routing_distribution", {})
            top_routing = max(routing_dist.items(), key=lambda x: x[1])[0] if routing_dist else "N/A"
            lines.append(
                f"| {category} | {stats['total']} | {stats['success_rate']}% | "
                f"{top_routing} | {stats['avg_processing_time_ms']}ms |"
            )
        lines.append("")

        if "by_routing" in perf:
            lines.append("### Performance by Routing Type")
            lines.append("")
            lines.append("| Routing | Count | Avg Time | Min | Max |")
            lines.append("|---------|-------|----------|-----|-----|")
            for rt, stats in perf["by_routing"].items():
                lines.append(f"| {rt} | {stats['count']} | {stats['avg_ms']}ms | {stats['min_ms']}ms | {stats['max_ms']}ms |")
            lines.append("")

    # -- 10. Key Findings ----------------------------------------------------
    lines.append("## Key Findings")
    lines.append("")
    _generate_key_findings(lines, analysis, results)
    lines.append("")

    # -- 11. Detailed Test Results -------------------------------------------
    lines.append("## Detailed Test Results")
    lines.append("")
    _generate_detailed_results(lines, results)

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## Report Sections")
    lines.append("")
    lines.append("1. Executive Summary - Overall metrics and routing summary")
    lines.append("2. Failure Analysis - Execution failures, error taxonomy, performance")
    lines.append("3. Routing Analysis - SQL vs Vector vs Both distribution, fallback patterns")
    lines.append("4. SQL Component Analysis - Query structure, complexity, column selection")
    lines.append("5. Vector Component Analysis - Source quality, retrieval performance, scores")
    lines.append("6. Response Quality Analysis - Length, completeness, confidence, citations")
    lines.append("7. Hybrid Combination Quality - True hybrid query analysis")
    lines.append("8. Performance by Category - Category and routing breakdown")
    lines.append("9. Key Findings - Actionable insights and recommendations")
    lines.append("10. Detailed Test Results - Complete query-by-query breakdown")
    lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")


def _generate_key_findings(lines: list[str], analysis: dict, results: list[dict]) -> None:
    """Generate automated key findings with actionable insights."""
    overall = analysis["overall"]
    routing = analysis["routing"]
    taxonomy = analysis.get("error_taxonomy", {})
    qs = analysis.get("query_structure", {})
    hybrid_comp = analysis["hybrid_combination"]

    success_rate = overall["success_rate"]
    if success_rate >= 95:
        lines.append(f"- **Excellent execution reliability** ({success_rate}% success rate)")
    elif success_rate >= 80:
        lines.append(f"- **Good execution reliability** ({success_rate}% success rate)")
    else:
        lines.append(f"- **Low execution reliability** ({success_rate}% success rate) - needs investigation")

    both_pct = routing.get("both_hybrid_pct", 0)
    total_routed = routing.get("total_routed", 0)
    if total_routed > 0:
        if both_pct >= 70:
            lines.append(f"- **Strong hybrid routing** ({both_pct}% queries use both SQL + Vector)")
        elif both_pct >= 40:
            lines.append(f"- **Moderate hybrid routing** ({both_pct}% queries use both SQL + Vector)")
        else:
            lines.append(f"- **Weak hybrid routing** (only {both_pct}% queries use both SQL + Vector) - review query classifier")

    total_errors = taxonomy.get("total_errors", 0)
    if total_errors == 0:
        lines.append("- **No LLM errors detected** - excellent response quality")
    else:
        declined = len(taxonomy.get("llm_declined", []))
        syntax = len(taxonomy.get("syntax_error", []))
        if declined > 0:
            lines.append(f"- **{declined} LLM declined responses** - may need prompt tuning")
        if syntax > 0:
            lines.append(f"- **{syntax} SQL syntax errors** - SQL generation needs improvement")

    correctness = qs.get("correctness", {})
    missing_joins = correctness.get("missing_joins", 0)
    if missing_joins > 0:
        lines.append(f"- **{missing_joins} queries missing required JOINs** - SQL prompt may need reinforcement")
    elif qs.get("total_queries", 0) > 0:
        lines.append(f"- **All SQL queries have correct JOINs** ({correctness.get('correct_joins', 0)} verified)")

    if hybrid_comp.get("hybrid_queries", 0) > 0:
        both_rate = hybrid_comp.get("both_data_rate", 0)
        if both_rate >= 90:
            lines.append(f"- **Excellent data integration** ({both_rate}% of hybrid queries have both SQL + Vector data)")
        elif both_rate >= 70:
            lines.append(f"- **Good data integration** ({both_rate}% of hybrid queries have both data types)")
        else:
            lines.append(f"- **Data integration needs improvement** (only {both_rate}% have both data types)")

    rp_data = analysis.get("response_patterns", {})
    declined = rp_data.get("completeness", {}).get("declined_answers", 0)
    if declined > 0:
        lines.append(f"- **{declined} declined answers** - LLM refused to answer some queries")
    else:
        lines.append("- **No declined answers** - all queries received substantive responses")


def _generate_detailed_results(lines: list[str], results: list[dict]) -> None:
    """Generate detailed per-query results grouped by category."""
    by_category = defaultdict(list)
    for result in results:
        category = result.get("category", "unknown")
        by_category[category].append(result)

    for category in sorted(by_category.keys()):
        category_results = by_category[category]
        lines.append(f"### {category.replace('_', ' ').title()} ({len(category_results)} tests)")
        lines.append("")

        for result in category_results:
            success = result.get("success", False)
            status = "+" if success else "x"
            question = result.get("question", "")

            lines.append(f"**{status} {question}**")
            lines.append("")

            if not success:
                lines.append(f"- **Error:** `{result.get('error', 'Unknown')[:200]}`")
                lines.append("")
                continue

            lines.append(f"- **Routing:** {result.get('routing', 'unknown').upper()}")
            processing_time = result.get("processing_time_ms", 0)
            lines.append(f"- **Processing Time:** {processing_time:.0f}ms")

            generated_sql = result.get("generated_sql")
            if generated_sql:
                lines.append(f"- **Generated SQL:**\n```sql\n{generated_sql}\n```")

            response = result.get("response", "")
            if response:
                lines.append(f"- **Response:**\n{response}")

            sources = result.get("sources", [])
            if sources:
                lines.append(f"- **Sources ({len(sources)}):**")
                lines.append("")
                lines.append("  | # | Source | Score |")
                lines.append("  |---|--------|-------|")
                for i, source in enumerate(sources[:5], 1):
                    if isinstance(source, dict):
                        name = source.get("source", "unknown")
                        score = source.get("score", 0)
                        lines.append(f"  | {i} | {name} | {score:.1f}% |")
                lines.append("")

            lines.append("")


# ============================================================================
# UNIFIED INTERFACE: Alias for consistency with SQL and Vector runners
# ============================================================================

def analyze_results(results: list[dict], test_cases: list) -> dict[str, Any]:
    """Unified interface: Alias for analyze_hybrid_results() for consistency.

    All three runners (SQL, Vector, Hybrid) can now call:
        from analysis_module import analyze_results
        analysis = analyze_results(results, test_cases)
    """
    return analyze_hybrid_results(results, test_cases)
