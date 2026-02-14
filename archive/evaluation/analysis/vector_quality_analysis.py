"""
FILE: vector_quality_analysis.py
STATUS: Active
RESPONSIBILITY: Vector evaluation analysis coordination - unified interface analyze_results(), 5 comprehensive analysis functions, RAGAS metrics
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu

Provides quality analysis for vector evaluation results:
- RAGAS metrics analysis (faithfulness, answer relevancy, context precision/recall)
- Source quality analysis (retrieval statistics, diversity, scores)
- Response pattern analysis (length, completeness, citations)
- Retrieval performance analysis (K-value, thresholds, processing time)
- Category performance analysis (by test category comparison)
"""

import re
from collections import defaultdict
from typing import Any


def analyze_ragas_metrics(results: list[dict]) -> dict[str, Any]:
    """Analyze RAGAS metrics (faithfulness, answer relevancy, context precision/recall).

    Args:
        results: List of evaluation results with RAGAS metrics

    Returns:
        Dictionary with:
        - overall: Average scores across all queries
        - by_category: Scores grouped by test category
        - distributions: Score distributions for each metric
        - low_scoring_queries: Queries with scores < 0.7
    """
    if not results:
        return {
            "overall": {},
            "by_category": {},
            "distributions": {},
            "low_scoring_queries": []
        }

    # Collect successful results with RAGAS metrics
    ragas_results = [r for r in results if r.get("success") and r.get("ragas_metrics")]

    if not ragas_results:
        return {
            "overall": {
                "avg_faithfulness": None,
                "avg_answer_relevancy": None,
                "avg_context_precision": None,
                "avg_context_recall": None
            },
            "by_category": {},
            "distributions": {},
            "low_scoring_queries": []
        }

    # Calculate overall averages
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    overall = {}
    distributions = {metric: [] for metric in metrics}

    for metric in metrics:
        scores = [
            r["ragas_metrics"][metric]
            for r in ragas_results
            if r["ragas_metrics"].get(metric) is not None
        ]
        overall[f"avg_{metric}"] = sum(scores) / len(scores) if scores else None
        distributions[metric] = scores

    # Calculate by category
    by_category = defaultdict(lambda: {metric: [] for metric in metrics})

    for r in ragas_results:
        category = r.get("category", "unknown")
        for metric in metrics:
            score = r["ragas_metrics"].get(metric)
            if score is not None:
                by_category[category][metric].append(score)

    # Compute category averages
    category_averages = {}
    for category, scores_dict in by_category.items():
        category_averages[category] = {
            f"avg_{metric}": (sum(scores) / len(scores) if scores else None)
            for metric, scores in scores_dict.items()
        }
        category_averages[category]["count"] = len(scores_dict["faithfulness"])

    # Find low-scoring queries (threshold < 0.7)
    low_scoring_queries = []
    for r in ragas_results:
        ragas = r["ragas_metrics"]
        min_score = min(
            score for score in [
                ragas.get("faithfulness"),
                ragas.get("answer_relevancy"),
                ragas.get("context_precision"),
                ragas.get("context_recall")
            ] if score is not None
        )

        if min_score < 0.7:
            low_scoring_queries.append({
                "question": r.get("question", ""),
                "category": r.get("category", "unknown"),
                "faithfulness": ragas.get("faithfulness"),
                "answer_relevancy": ragas.get("answer_relevancy"),
                "context_precision": ragas.get("context_precision"),
                "context_recall": ragas.get("context_recall"),
                "min_score": min_score
            })

    # Sort by min_score (lowest first)
    low_scoring_queries.sort(key=lambda x: x["min_score"])

    return {
        "overall": overall,
        "by_category": category_averages,
        "distributions": distributions,
        "low_scoring_queries": low_scoring_queries
    }


def analyze_source_quality(results: list[dict]) -> dict[str, Any]:
    """Analyze retrieved source quality and relevance.

    Args:
        results: List of evaluation results with sources

    Returns:
        Dictionary with:
        - retrieval_stats: Average sources per query, unique sources, avg score
        - source_diversity: Top sources, distribution
        - score_analysis: Min/max scores, distribution by range
        - empty_retrievals: Count of queries with no sources
    """
    if not results:
        return {
            "retrieval_stats": {},
            "source_diversity": {},
            "score_analysis": {},
            "empty_retrievals": 0
        }

    successful_results = [r for r in results if r.get("success")]

    if not successful_results:
        return {
            "retrieval_stats": {
                "avg_sources_per_query": 0,
                "total_unique_sources": 0,
                "avg_similarity_score": 0
            },
            "source_diversity": {"top_sources": [], "sources_per_query_distribution": []},
            "score_analysis": {"min_score": 0, "max_score": 0, "score_distribution": {}},
            "empty_retrievals": 0
        }

    # Retrieval statistics
    sources_counts = []
    all_sources = []
    all_scores = []

    for r in successful_results:
        sources = r.get("sources", [])
        sources_counts.append(len(sources))

        for source in sources:
            all_sources.append(source.get("source", "unknown"))
            score = source.get("score", 0)
            all_scores.append(score)

    avg_sources_per_query = sum(sources_counts) / len(sources_counts) if sources_counts else 0
    unique_sources = list(set(all_sources))
    avg_similarity_score = sum(all_scores) / len(all_scores) if all_scores else 0

    retrieval_stats = {
        "avg_sources_per_query": round(avg_sources_per_query, 2),
        "total_unique_sources": len(unique_sources),
        "avg_similarity_score": round(avg_similarity_score, 2)
    }

    # Source diversity
    source_counts = defaultdict(int)
    source_scores = defaultdict(list)

    for source_name in all_sources:
        source_counts[source_name] += 1

    for r in successful_results:
        for source in r.get("sources", []):
            source_name = source.get("source", "unknown")
            source_scores[source_name].append(source.get("score", 0))

    top_sources = [
        {
            "source": source_name,
            "count": count,
            "avg_score": round(sum(source_scores[source_name]) / len(source_scores[source_name]), 2)
        }
        for source_name, count in source_counts.items()
    ]
    top_sources.sort(key=lambda x: x["count"], reverse=True)

    source_diversity = {
        "top_sources": top_sources[:10],  # Top 10 most frequent sources
        "sources_per_query_distribution": sources_counts
    }

    # Score analysis
    min_score = min(all_scores) if all_scores else 0
    max_score = max(all_scores) if all_scores else 0

    # Score distribution by range
    score_ranges = {
        "0.0-0.4": 0,
        "0.4-0.5": 0,
        "0.5-0.6": 0,
        "0.6-0.7": 0,
        "0.7-0.8": 0,
        "0.8-0.9": 0,
        "0.9-1.0": 0
    }

    for score in all_scores:
        normalized = score / 100.0  # Convert 0-100 to 0-1
        if normalized < 0.4:
            score_ranges["0.0-0.4"] += 1
        elif normalized < 0.5:
            score_ranges["0.4-0.5"] += 1
        elif normalized < 0.6:
            score_ranges["0.5-0.6"] += 1
        elif normalized < 0.7:
            score_ranges["0.6-0.7"] += 1
        elif normalized < 0.8:
            score_ranges["0.7-0.8"] += 1
        elif normalized < 0.9:
            score_ranges["0.8-0.9"] += 1
        else:
            score_ranges["0.9-1.0"] += 1

    score_analysis = {
        "min_score": round(min_score, 2),
        "max_score": round(max_score, 2),
        "score_distribution": score_ranges
    }

    # Empty retrievals
    empty_retrievals = sum(1 for r in successful_results if len(r.get("sources", [])) == 0)

    return {
        "retrieval_stats": retrieval_stats,
        "source_diversity": source_diversity,
        "score_analysis": score_analysis,
        "empty_retrievals": empty_retrievals
    }


def analyze_response_patterns(results: list[dict]) -> dict[str, Any]:
    """Analyze response patterns (length, completeness, citations).

    Args:
        results: List of evaluation results with responses

    Returns:
        Dictionary with:
        - response_length: Average, min, max, distribution
        - completeness: Complete, incomplete, declined answers
        - citation_patterns: Responses with citations, formats
        - confidence_indicators: Hedging vs confident language
    """
    if not results:
        return {
            "response_length": {},
            "completeness": {},
            "citation_patterns": {},
            "confidence_indicators": {}
        }

    successful_results = [r for r in results if r.get("success") and r.get("response")]

    if not successful_results:
        return {
            "response_length": {
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0,
                "distribution": {"very_short": 0, "short": 0, "medium": 0, "long": 0}
            },
            "completeness": {
                "complete_answers": 0,
                "incomplete_answers": 0,
                "declined_answers": 0,
                "incomplete_cases": []
            },
            "citation_patterns": {
                "responses_with_citations": 0,
                "avg_citations_per_response": 0,
                "citation_formats": {"explicit": 0, "implicit": 0}
            },
            "confidence_indicators": {
                "hedging_count": 0,
                "confident_count": 0,
                "hedging_patterns": []
            }
        }

    # Response length analysis
    lengths = [len(r["response"]) for r in successful_results]
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)

    # Length distribution
    length_distribution = {
        "very_short": sum(1 for l in lengths if l < 100),
        "short": sum(1 for l in lengths if 100 <= l < 200),
        "medium": sum(1 for l in lengths if 200 <= l < 400),
        "long": sum(1 for l in lengths if l >= 400)
    }

    response_length = {
        "avg_length": round(avg_length, 0),
        "min_length": min_length,
        "max_length": max_length,
        "distribution": length_distribution
    }

    # Completeness analysis
    declined_patterns = [
        "i don't know", "i cannot", "i'm not sure", "no information",
        "cannot find", "unable to", "not available", "je ne sais pas",
        "je ne peux pas", "aucune information"
    ]

    incomplete_patterns = [
        "partially", "some information", "limited", "not enough",
        "partiellement", "informations limitées"
    ]

    declined_answers = 0
    incomplete_answers = 0
    incomplete_cases = []

    for r in successful_results:
        response_lower = r["response"].lower()

        if any(pattern in response_lower for pattern in declined_patterns):
            declined_answers += 1
        elif any(pattern in response_lower for pattern in incomplete_patterns):
            incomplete_answers += 1
            incomplete_cases.append({
                "question": r.get("question", "")[:100],
                "response": r["response"][:200],
                "issue": "partial_answer"
            })

    complete_answers = len(successful_results) - declined_answers - incomplete_answers

    completeness = {
        "complete_answers": complete_answers,
        "incomplete_answers": incomplete_answers,
        "declined_answers": declined_answers,
        "incomplete_cases": incomplete_cases[:10]  # Top 10
    }

    # Citation patterns
    citation_explicit_patterns = [
        r"according to", r"based on", r"source:", r"from", r"cit(e|ing)",
        r"selon", r"d'après", r"basé sur"
    ]

    responses_with_citations = 0
    explicit_citations = 0
    citation_counts = []

    for r in successful_results:
        response_lower = r["response"].lower()
        has_citation = any(
            re.search(pattern, response_lower)
            for pattern in citation_explicit_patterns
        )

        if has_citation:
            responses_with_citations += 1
            explicit_citations += 1

            # Count citation instances
            citation_count = sum(
                len(re.findall(pattern, response_lower))
                for pattern in citation_explicit_patterns
            )
            citation_counts.append(citation_count)

    implicit_citations = responses_with_citations - explicit_citations
    avg_citations_per_response = (
        sum(citation_counts) / len(citation_counts) if citation_counts else 0
    )

    citation_patterns = {
        "responses_with_citations": responses_with_citations,
        "avg_citations_per_response": round(avg_citations_per_response, 2),
        "citation_formats": {
            "explicit": explicit_citations,
            "implicit": implicit_citations
        }
    }

    # Confidence indicators
    hedging_patterns = [
        "might", "possibly", "probably", "perhaps", "approximately",
        "around", "roughly", "may", "could", "likely",
        "peut-être", "probablement", "environ", "approximativement"
    ]

    hedging_count = 0
    hedging_found = set()

    for r in successful_results:
        response_lower = r["response"].lower()
        has_hedging = False

        for pattern in hedging_patterns:
            if pattern in response_lower:
                has_hedging = True
                hedging_found.add(pattern)

        if has_hedging:
            hedging_count += 1

    confident_count = len(successful_results) - hedging_count

    confidence_indicators = {
        "hedging_count": hedging_count,
        "confident_count": confident_count,
        "hedging_patterns": sorted(list(hedging_found))
    }

    return {
        "response_length": response_length,
        "completeness": completeness,
        "citation_patterns": citation_patterns,
        "confidence_indicators": confidence_indicators
    }


def analyze_retrieval_performance(results: list[dict]) -> dict[str, Any]:
    """Analyze retrieval performance metrics.

    Args:
        results: List of evaluation results with retrieval metrics

    Returns:
        Dictionary with:
        - performance_metrics: Avg retrieval score, success rate, processing time
        - k_value_analysis: Configured K, actual retrieved, queries below K
        - score_thresholds: Count of queries by score range
        - by_source_type: Performance grouped by source type (PDF, Reddit, etc.)
    """
    if not results:
        return {
            "performance_metrics": {},
            "k_value_analysis": {},
            "score_thresholds": {},
            "by_source_type": {}
        }

    successful_results = [r for r in results if r.get("success")]

    if not successful_results:
        return {
            "performance_metrics": {
                "avg_retrieval_score": 0,
                "retrieval_success_rate": 0,
                "avg_processing_time_ms": 0
            },
            "k_value_analysis": {
                "configured_k": 5,
                "actual_avg_retrieved": 0,
                "queries_below_k": 0
            },
            "score_thresholds": {
                "above_0.8": 0,
                "0.6_to_0.8": 0,
                "below_0.6": 0
            },
            "by_source_type": {}
        }

    # Performance metrics
    all_scores = []
    processing_times = []

    for r in successful_results:
        for source in r.get("sources", []):
            all_scores.append(source.get("score", 0))

        if r.get("processing_time_ms"):
            processing_times.append(r["processing_time_ms"])

    avg_retrieval_score = sum(all_scores) / len(all_scores) if all_scores else 0
    retrieval_success_rate = sum(
        1 for r in successful_results if len(r.get("sources", [])) > 0
    ) / len(successful_results) if successful_results else 0
    avg_processing_time_ms = sum(processing_times) / len(processing_times) if processing_times else 0

    performance_metrics = {
        "avg_retrieval_score": round(avg_retrieval_score, 2),
        "retrieval_success_rate": round(retrieval_success_rate, 3),
        "avg_processing_time_ms": round(avg_processing_time_ms, 0)
    }

    # K-value analysis (assuming K=5 from API default)
    configured_k = 5
    sources_counts = [len(r.get("sources", [])) for r in successful_results]
    actual_avg_retrieved = sum(sources_counts) / len(sources_counts) if sources_counts else 0
    queries_below_k = sum(1 for count in sources_counts if count < configured_k)

    k_value_analysis = {
        "configured_k": configured_k,
        "actual_avg_retrieved": round(actual_avg_retrieved, 2),
        "queries_below_k": queries_below_k
    }

    # Score thresholds (convert 0-100 to 0-1 for comparison)
    above_08 = sum(1 for score in all_scores if score >= 80)
    between_06_08 = sum(1 for score in all_scores if 60 <= score < 80)
    below_06 = sum(1 for score in all_scores if score < 60)

    score_thresholds = {
        "above_0.8": above_08,
        "0.6_to_0.8": between_06_08,
        "below_0.6": below_06
    }

    # By source type (PDF, Reddit, etc.)
    source_type_stats = defaultdict(lambda: {"count": 0, "scores": []})

    for r in successful_results:
        for source in r.get("sources", []):
            source_name = source.get("source", "unknown").lower()

            # Determine source type
            if "reddit" in source_name:
                source_type = "reddit"
            elif ".pdf" in source_name:
                source_type = "pdf"
            else:
                source_type = "other"

            source_type_stats[source_type]["count"] += 1
            source_type_stats[source_type]["scores"].append(source.get("score", 0))

    by_source_type = {
        source_type: {
            "count": stats["count"],
            "avg_score": round(sum(stats["scores"]) / len(stats["scores"]), 2) if stats["scores"] else 0
        }
        for source_type, stats in source_type_stats.items()
    }

    return {
        "performance_metrics": performance_metrics,
        "k_value_analysis": k_value_analysis,
        "score_thresholds": score_thresholds,
        "by_source_type": by_source_type
    }


def analyze_category_performance(results: list[dict]) -> dict[str, Any]:
    """Analyze performance by test category.

    Args:
        results: List of evaluation results with categories

    Returns:
        Dictionary with:
        - category_breakdown: Performance metrics per category
        - comparative_analysis: Best/worst categories, largest gaps
        - recommendations: Suggested improvements based on analysis
    """
    if not results:
        return {
            "category_breakdown": {},
            "comparative_analysis": {},
            "recommendations": []
        }

    # Group by category
    category_data = defaultdict(lambda: {
        "count": 0,
        "success_count": 0,
        "faithfulness_scores": [],
        "answer_relevancy_scores": [],
        "sources_counts": [],
        "retrieval_scores": []
    })

    for r in results:
        category = r.get("category", "unknown")
        category_data[category]["count"] += 1

        if r.get("success"):
            category_data[category]["success_count"] += 1
            category_data[category]["sources_counts"].append(len(r.get("sources", [])))

            for source in r.get("sources", []):
                category_data[category]["retrieval_scores"].append(source.get("score", 0))

            ragas = r.get("ragas_metrics", {})
            if ragas.get("faithfulness") is not None:
                category_data[category]["faithfulness_scores"].append(ragas["faithfulness"])
            if ragas.get("answer_relevancy") is not None:
                category_data[category]["answer_relevancy_scores"].append(ragas["answer_relevancy"])

    # Calculate category breakdown
    category_breakdown = {}

    for category, data in category_data.items():
        success_rate = data["success_count"] / data["count"] if data["count"] > 0 else 0
        avg_faithfulness = (
            sum(data["faithfulness_scores"]) / len(data["faithfulness_scores"])
            if data["faithfulness_scores"] else None
        )
        avg_answer_relevancy = (
            sum(data["answer_relevancy_scores"]) / len(data["answer_relevancy_scores"])
            if data["answer_relevancy_scores"] else None
        )
        avg_sources = (
            sum(data["sources_counts"]) / len(data["sources_counts"])
            if data["sources_counts"] else 0
        )
        avg_retrieval_score = (
            sum(data["retrieval_scores"]) / len(data["retrieval_scores"])
            if data["retrieval_scores"] else 0
        )

        category_breakdown[category] = {
            "count": data["count"],
            "success_rate": round(success_rate, 3),
            "avg_faithfulness": round(avg_faithfulness, 3) if avg_faithfulness is not None else None,
            "avg_answer_relevancy": round(avg_answer_relevancy, 3) if avg_answer_relevancy is not None else None,
            "avg_sources": round(avg_sources, 2),
            "avg_retrieval_score": round(avg_retrieval_score, 2)
        }

    # Comparative analysis
    categories_with_faithfulness = {
        cat: stats["avg_faithfulness"]
        for cat, stats in category_breakdown.items()
        if stats["avg_faithfulness"] is not None
    }

    if categories_with_faithfulness:
        best_category = max(categories_with_faithfulness.items(), key=lambda x: x[1])[0]
        worst_category = min(categories_with_faithfulness.items(), key=lambda x: x[1])[0]
        largest_gap_value = max(categories_with_faithfulness.values()) - min(categories_with_faithfulness.values())
    else:
        best_category = None
        worst_category = None
        largest_gap_value = 0

    comparative_analysis = {
        "best_category": best_category,
        "worst_category": worst_category,
        "largest_gap": {
            "metric": "faithfulness",
            "gap": round(largest_gap_value, 3)
        }
    }

    # Generate recommendations
    recommendations = []

    for category, stats in category_breakdown.items():
        if stats["success_rate"] < 0.8:
            recommendations.append(
                f"Improve reliability for '{category}' queries (success rate: {stats['success_rate']:.1%})"
            )

        if stats["avg_faithfulness"] is not None and stats["avg_faithfulness"] < 0.7:
            recommendations.append(
                f"Improve faithfulness for '{category}' queries (avg: {stats['avg_faithfulness']:.3f})"
            )

        if stats["avg_sources"] < 3:
            recommendations.append(
                f"Increase retrieval for '{category}' queries (avg sources: {stats['avg_sources']:.1f})"
            )

    if not recommendations:
        recommendations.append("All categories performing well - no major improvements needed")

    return {
        "category_breakdown": category_breakdown,
        "comparative_analysis": comparative_analysis,
        "recommendations": recommendations
    }


# ============================================================================
# UNIFIED INTERFACE: Wrapper function for consistent runner patterns
# ============================================================================

def analyze_results(results: list[dict], test_cases: list) -> dict[str, Any]:
    """Unified interface: Analyze vector evaluation results.

    Calls all analysis functions to match the pattern used by SQL and Hybrid runners.

    Args:
        results: List of evaluation result dictionaries
        test_cases: List of test case objects

    Returns:
        Dictionary with comprehensive analysis
    """
    analysis = {
        "overall": {
            "total_queries": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
        }
    }

    # Add all detailed analysis
    analysis["ragas_metrics"] = analyze_ragas_metrics(results)
    analysis["source_quality"] = analyze_source_quality(results)
    analysis["response_patterns"] = analyze_response_patterns(results)
    analysis["retrieval_performance"] = analyze_retrieval_performance(results)
    analysis["category_performance"] = analyze_category_performance(results)

    return analysis
