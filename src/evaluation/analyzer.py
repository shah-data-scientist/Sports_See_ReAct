"""
FILE: analyzer.py
STATUS: Active
RESPONSIBILITY: Unified evaluation analysis for SQL, Vector, and Hybrid test results
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

DESCRIPTION:
Single unified analysis module consolidating:
- SQL analysis: error taxonomy, query structure/complexity, column selection, response quality
- Vector analysis: ALL 7 RAGAS metrics, source quality, retrieval performance, response patterns
- Hybrid analysis: SQL/Vector components, hybrid combination

CHANGES (2026-02-15):
- REMOVED: analyze_fallback_patterns() - Obsolete (ReAct "Always Both" architecture)
- REMOVED: analyze_routing_quality() - Obsolete (no routing decisions in new architecture)
- UPDATED: analyze_ragas_metrics() - Now handles all 7 RAGAS metrics with nuclear explanations

USAGE:
    from src.evaluation.analyzer import analyze_results

    analysis = analyze_results(results, test_cases)
    # Automatically detects test type and runs appropriate analyses
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================================
# SQL-SPECIFIC ANALYSIS FUNCTIONS
# ============================================================================

def analyze_error_taxonomy(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze error patterns in responses.

    Categorizes errors into:
    - LLM Declined: "I cannot answer" / "doesn't contain"
    - Syntax Error: SQLite error in response
    - Empty Response: No answer provided

    Args:
        results: List of evaluation result dictionaries

    Returns:
        Dictionary with error taxonomy statistics
    """
    taxonomy = {
        "llm_declined": [],
        "syntax_error": [],
        "empty_response": [],
        "total_errors": 0,
    }

    decline_patterns = [
        r"I cannot (?:answer|find|provide)",
        r"(?:database|data|schema|table) (?:does not|doesn't) contain",
        r"(?:not available|no (?:data|information))",
        r"(?:unable to|can't) (?:find|answer|provide)",
    ]

    syntax_patterns = [
        r"SQLite error",
        r"SQL syntax error",
        r"near \".*\": syntax error",
        r"no such (?:table|column)",
    ]

    for result in results:
        response = result.get("response", "").strip()
        question = result.get("question", "")

        if not response or len(response) < 5:
            taxonomy["empty_response"].append({
                "question": question,
                "response": response
            })
            taxonomy["total_errors"] += 1
            continue

        declined = False
        for pattern in decline_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                taxonomy["llm_declined"].append({
                    "question": question,
                    "response": response,
                    "pattern_matched": pattern
                })
                taxonomy["total_errors"] += 1
                declined = True
                break

        if declined:
            continue

        for pattern in syntax_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                taxonomy["syntax_error"].append({
                    "question": question,
                    "response": response,
                    "pattern_matched": pattern
                })
                taxonomy["total_errors"] += 1
                break

    return taxonomy


def analyze_response_quality(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze response quality patterns.

    Measures:
    - Completeness (e.g., asked for top 3, got 3)
    - Verbosity (response length distribution)
    - Confidence indicators ("approximately", "around", "I'm not sure")

    Args:
        results: List of evaluation result dictionaries

    Returns:
        Dictionary with response quality statistics
    """
    quality_stats = {
        "verbosity": {
            "min_length": float("inf"),
            "max_length": 0,
            "avg_length": 0.0,
            "length_distribution": defaultdict(int)
        },
        "confidence_indicators": {
            "total_with_hedging": 0,
            "hedging_patterns": defaultdict(int),
            "cases": []
        },
        "completeness": {
            "complete": 0,
            "incomplete": 0,
            "incomplete_cases": []
        }
    }

    hedging_patterns = [
        r"approximately",
        r"around",
        r"about",
        r"roughly",
        r"I(?:'m| am) not (?:sure|certain)",
        r"(?:might|may) be",
        r"I think",
        r"possibly",
        r"likely"
    ]

    total_length = 0

    for result in results:
        response = result.get("response", "")
        question = result.get("question", "")

        length = len(response)
        quality_stats["verbosity"]["min_length"] = min(
            quality_stats["verbosity"]["min_length"], length
        )
        quality_stats["verbosity"]["max_length"] = max(
            quality_stats["verbosity"]["max_length"], length
        )
        total_length += length

        if length < 50:
            quality_stats["verbosity"]["length_distribution"]["very_short"] += 1
        elif length < 100:
            quality_stats["verbosity"]["length_distribution"]["short"] += 1
        elif length < 200:
            quality_stats["verbosity"]["length_distribution"]["medium"] += 1
        elif length < 400:
            quality_stats["verbosity"]["length_distribution"]["long"] += 1
        else:
            quality_stats["verbosity"]["length_distribution"]["very_long"] += 1

        has_hedging = False
        for pattern in hedging_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                has_hedging = True
                quality_stats["confidence_indicators"]["hedging_patterns"][pattern] += 1

        if has_hedging:
            quality_stats["confidence_indicators"]["total_with_hedging"] += 1
            quality_stats["confidence_indicators"]["cases"].append({
                "question": question,
                "response": response[:200]
            })

        top_n_match = re.search(r"top\s+(\d+)", question, re.IGNORECASE)
        if top_n_match:
            requested_count = int(top_n_match.group(1))
            numbered_items = len(re.findall(r"^\s*\d+\.", response, re.MULTILINE))

            if numbered_items >= requested_count:
                quality_stats["completeness"]["complete"] += 1
            else:
                quality_stats["completeness"]["incomplete"] += 1
                quality_stats["completeness"]["incomplete_cases"].append({
                    "question": question,
                    "requested": requested_count,
                    "provided": numbered_items,
                    "response": response[:200]
                })

    if len(results) > 0:
        quality_stats["verbosity"]["avg_length"] = total_length / len(results)

    return quality_stats


def analyze_query_structure(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze SQL query structure (JOINs, aggregations, filters).

    Args:
        results: List of evaluation result dictionaries with generated_sql field

    Returns:
        Dictionary with query structure statistics
    """
    structure_stats = {
        "total_queries": 0,
        "queries_with_join": 0,
        "queries_with_aggregation": 0,
        "queries_with_filter": 0,
        "queries_with_ordering": 0,
        "queries_with_limit": 0,
        "join_types": defaultdict(int),
        "aggregation_types": defaultdict(int),
        "correctness": {
            "correct_joins": 0,
            "missing_joins": 0,
            "examples": []
        }
    }

    aggregation_patterns = [
        r"\bCOUNT\b", r"\bSUM\b", r"\bAVG\b", r"\bMAX\b", r"\bMIN\b"
    ]

    for result in results:
        sql = result.get("generated_sql")
        if not sql:
            continue

        structure_stats["total_queries"] += 1
        sql_upper = sql.upper()

        if "JOIN" in sql_upper:
            structure_stats["queries_with_join"] += 1
            if "LEFT JOIN" in sql_upper or "LEFT OUTER JOIN" in sql_upper:
                structure_stats["join_types"]["left_join"] += 1
            elif "RIGHT JOIN" in sql_upper or "RIGHT OUTER JOIN" in sql_upper:
                structure_stats["join_types"]["right_join"] += 1
            elif "INNER JOIN" in sql_upper or "JOIN" in sql_upper:
                structure_stats["join_types"]["inner_join"] += 1
            elif "FULL JOIN" in sql_upper or "FULL OUTER JOIN" in sql_upper:
                structure_stats["join_types"]["full_outer_join"] += 1

        for pattern in aggregation_patterns:
            if re.search(pattern, sql_upper):
                structure_stats["queries_with_aggregation"] += 1
                func_name = pattern.replace(r"\b", "").replace(r"\\", "")
                structure_stats["aggregation_types"][func_name.lower()] += 1
                break

        if "WHERE" in sql_upper:
            structure_stats["queries_with_filter"] += 1
        if "ORDER BY" in sql_upper:
            structure_stats["queries_with_ordering"] += 1
        if "LIMIT" in sql_upper:
            structure_stats["queries_with_limit"] += 1

        # Check JOIN correctness
        sql_lower = sql.lower()
        has_players_table = "players" in sql_lower
        has_player_stats_table = "player_stats" in sql_lower
        has_join = "JOIN" in sql_upper

        if has_players_table and has_player_stats_table and has_join:
            structure_stats["correctness"]["correct_joins"] += 1
        elif has_player_stats_table and not has_join:
            needs_player_name = any(
                kw in sql_lower for kw in ["p.name", "players.name"]
            )
            question = result.get("question", "").lower()
            asks_about_player = any(
                kw in question for kw in ["who", "player", "name", "lebron", "curry", "jokic", "embiid"]
            )
            if needs_player_name or asks_about_player:
                structure_stats["correctness"]["missing_joins"] += 1
                structure_stats["correctness"]["examples"].append({
                    "question": result.get("question"),
                    "sql": sql,
                    "issue": "Missing JOIN to players table"
                })

    return structure_stats


def analyze_query_complexity(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze SQL query complexity metrics.

    Args:
        results: List of evaluation result dictionaries with generated_sql field

    Returns:
        Dictionary with query complexity statistics
    """
    complexity_stats = {
        "total_queries": 0,
        "avg_joins_per_query": 0.0,
        "queries_with_subqueries": 0,
        "queries_with_having": 0,
        "queries_with_group_by": 0,
        "avg_where_conditions": 0.0,
        "complexity_distribution": {
            "simple": 0,
            "moderate": 0,
            "complex": 0,
            "very_complex": 0
        }
    }

    total_joins = 0
    total_where_conditions = 0

    for result in results:
        sql = result.get("generated_sql")
        if not sql:
            continue

        complexity_stats["total_queries"] += 1
        sql_upper = sql.upper()

        join_count = sql_upper.count("JOIN")
        total_joins += join_count

        subquery_count = sql_upper.count("SELECT") - 1
        if subquery_count > 0:
            complexity_stats["queries_with_subqueries"] += 1

        if "HAVING" in sql_upper:
            complexity_stats["queries_with_having"] += 1
        if "GROUP BY" in sql_upper:
            complexity_stats["queries_with_group_by"] += 1

        where_match = re.search(r"WHERE\s+(.+?)(?:ORDER BY|GROUP BY|HAVING|LIMIT|$)", sql_upper, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            condition_count = 1 + where_clause.count(" AND ") + where_clause.count(" OR ")
            total_where_conditions += condition_count
        else:
            condition_count = 0

        if subquery_count > 0 and join_count > 1:
            complexity_level = "very_complex"
        elif subquery_count > 0 or join_count > 1:
            complexity_level = "complex"
        elif join_count == 1 or condition_count > 1:
            complexity_level = "moderate"
        else:
            complexity_level = "simple"

        complexity_stats["complexity_distribution"][complexity_level] += 1

    if complexity_stats["total_queries"] > 0:
        complexity_stats["avg_joins_per_query"] = total_joins / complexity_stats["total_queries"]
        complexity_stats["avg_where_conditions"] = total_where_conditions / complexity_stats["total_queries"]

    return complexity_stats


def analyze_column_selection(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze column selection accuracy in SQL queries.

    Args:
        results: List of evaluation result dictionaries with generated_sql field

    Returns:
        Dictionary with column selection statistics
    """
    selection_stats = {
        "total_queries": 0,
        "avg_columns_selected": 0.0,
        "over_selection_rate": 0.0,
        "under_selection_rate": 0.0,
        "select_star_count": 0,
        "examples": {
            "over_selection": [],
            "under_selection": [],
            "select_star": []
        }
    }

    total_columns_selected = 0
    over_selection_count = 0
    under_selection_count = 0

    for result in results:
        sql = result.get("generated_sql")
        if not sql:
            continue

        selection_stats["total_queries"] += 1

        if re.search(r"SELECT\s+\*", sql, re.IGNORECASE):
            selection_stats["select_star_count"] += 1
            selection_stats["examples"]["select_star"].append({
                "question": result.get("question"),
                "sql": sql[:200]
            })
            continue

        select_match = re.search(r"SELECT\s+(.+?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
        if not select_match:
            continue

        select_clause = select_match.group(1)
        depth = 0
        column_count = 1
        for char in select_clause:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                column_count += 1

        total_columns_selected += column_count

        question = result.get("question", "").lower()
        is_simple_query = any(
            phrase in question
            for phrase in ["how many", "what is", "who has the highest", "who scored the most"]
        )
        if is_simple_query and column_count > 3:
            over_selection_count += 1
            selection_stats["examples"]["over_selection"].append({
                "question": result.get("question"),
                "columns_selected": column_count,
                "sql": sql[:200]
            })

        if "who" in question and "p.name" not in sql.lower() and "name" not in select_clause.lower():
            under_selection_count += 1
            selection_stats["examples"]["under_selection"].append({
                "question": result.get("question"),
                "sql": sql[:200],
                "issue": "Missing player name column"
            })

    if selection_stats["total_queries"] > 0:
        selection_stats["avg_columns_selected"] = total_columns_selected / selection_stats["total_queries"]
        selection_stats["over_selection_rate"] = (over_selection_count / selection_stats["total_queries"]) * 100
        selection_stats["under_selection_rate"] = (under_selection_count / selection_stats["total_queries"]) * 100

    return selection_stats


# ============================================================================
# VECTOR-SPECIFIC ANALYSIS FUNCTIONS
# ============================================================================

def analyze_ragas_metrics(results: list[dict]) -> dict[str, Any]:
    """Analyze ALL 7 RAGAS metrics with nuclear explanations.

    RAGAS METRICS (7 total):

    ANSWER QUALITY (use ground_truth_answer):
    1. Faithfulness - Does answer contradict sources? (0.0-1.0, higher=better)
    2. Answer Relevancy - Does answer address question? (0.0-1.0, higher=better)
    3. Answer Semantic Similarity - Similarity to expected answer (0.0-1.0, higher=better)
    4. Answer Correctness - Semantic + Factual (0.0-1.0, higher=better) ⭐ BEST OVERALL

    RETRIEVAL QUALITY (use ground_truth_vector):
    5. Context Precision - Relevant chunks ranked higher? (0.0-1.0, higher=better)
    6. Context Recall - All required chunks retrieved? (0.0-1.0, higher=better)
    7. Context Relevancy - Fraction of chunks relevant (0.0-1.0, higher=better)

    Args:
        results: List of evaluation results with RAGAS metrics

    Returns:
        Dictionary with:
        - overall: Overall averages for all 7 metrics
        - by_category: Averages by test category
        - distributions: Score distributions for each metric
        - low_scoring_queries: Queries with any metric < 0.7
        - metric_explanations: Nuclear explanations for each metric
    """
    if not results:
        return {
            "overall": {},
            "by_category": {},
            "distributions": {},
            "low_scoring_queries": [],
            "metric_explanations": _get_ragas_metric_explanations()
        }

    ragas_results = [r for r in results if r.get("success") and r.get("ragas_metrics")]

    if not ragas_results:
        return {
            "overall": {
                "avg_faithfulness": None,
                "avg_answer_relevancy": None,
                "avg_answer_semantic_similarity": None,
                "avg_answer_correctness": None,
                "avg_context_precision": None,
                "avg_context_recall": None,
                "avg_context_relevancy": None,
            },
            "by_category": {},
            "distributions": {},
            "low_scoring_queries": [],
            "metric_explanations": _get_ragas_metric_explanations()
        }

    # All 7 RAGAS metrics
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "answer_semantic_similarity",
        "answer_correctness",
        "context_precision",
        "context_recall",
        "context_relevancy"
    ]

    overall = {}
    distributions = {metric: [] for metric in metrics}

    # Calculate overall averages
    for metric in metrics:
        scores = [
            r["ragas_metrics"][metric]
            for r in ragas_results
            if r["ragas_metrics"].get(metric) is not None
        ]
        overall[f"avg_{metric}"] = sum(scores) / len(scores) if scores else None
        distributions[metric] = scores

    # Calculate by-category averages
    by_category = defaultdict(lambda: {metric: [] for metric in metrics})

    for r in ragas_results:
        category = r.get("category", "unknown")
        for metric in metrics:
            score = r["ragas_metrics"].get(metric)
            if score is not None:
                by_category[category][metric].append(score)

    category_averages = {}
    for category, scores_dict in by_category.items():
        category_averages[category] = {
            f"avg_{metric}": (sum(scores) / len(scores) if scores else None)
            for metric, scores in scores_dict.items()
        }
        category_averages[category]["count"] = len([s for s in scores_dict.values() if s])

    # Find low-scoring queries (any metric < 0.7)
    low_scoring_queries = []
    for r in ragas_results:
        ragas = r["ragas_metrics"]

        # Get all non-None scores
        all_scores = [
            score for score in [
                ragas.get("faithfulness"),
                ragas.get("answer_relevancy"),
                ragas.get("answer_semantic_similarity"),
                ragas.get("answer_correctness"),
                ragas.get("context_precision"),
                ragas.get("context_recall"),
                ragas.get("context_relevancy")
            ] if score is not None
        ]

        if all_scores:
            min_score = min(all_scores)

            if min_score < 0.7:
                low_scoring_queries.append({
                    "question": r.get("question", ""),
                    "category": r.get("category", "unknown"),
                    "faithfulness": ragas.get("faithfulness"),
                    "answer_relevancy": ragas.get("answer_relevancy"),
                    "answer_semantic_similarity": ragas.get("answer_semantic_similarity"),
                    "answer_correctness": ragas.get("answer_correctness"),
                    "context_precision": ragas.get("context_precision"),
                    "context_recall": ragas.get("context_recall"),
                    "context_relevancy": ragas.get("context_relevancy"),
                    "min_score": min_score
                })

    low_scoring_queries.sort(key=lambda x: x["min_score"])

    return {
        "overall": overall,
        "by_category": category_averages,
        "distributions": distributions,
        "low_scoring_queries": low_scoring_queries,
        "metric_explanations": _get_ragas_metric_explanations()
    }


def _get_ragas_metric_explanations() -> dict[str, str]:
    """Get nuclear explanations for all 7 RAGAS metrics.

    Returns:
        Dictionary with metric name → explanation
    """
    return {
        "faithfulness": """
FAITHFULNESS (Answer Quality - Uses ground_truth_answer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Does the answer contradict the retrieved sources?
HOW: (Supported claims) / (Total claims)
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - No hallucination detected
⚠️  0.7-0.9: GOOD - Minor hallucination, mostly grounded
⚠️  0.5-0.7: WARNING - Moderate hallucination detected
❌ 0.0-0.5: CRITICAL - High hallucination, answer not trustworthy

EXAMPLE:
Question: "Who scored the most points?"
Sources: [{"text": "Shai scored 2485 points"}]
Answer: "Shai scored 2485 points and won MVP"

Claims:
1. "Shai scored 2485 points" ✅ Supported
2. "Shai won MVP" ❌ NOT in sources (hallucination)

Faithfulness = 1/2 = 0.5 (50% hallucinated)

USE FOR: Detect hallucination, ensure answer grounded in data
        """,
        "answer_relevancy": """
ANSWER RELEVANCY (Answer Quality - Uses ground_truth_answer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Does the answer actually address the question?
HOW: Avg similarity of generated questions to original
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Answer is on-topic and focused
⚠️  0.7-0.9: GOOD - Answer is relevant with minor drift
⚠️  0.5-0.7: WARNING - Answer is somewhat off-topic
❌ 0.0-0.5: CRITICAL - Answer doesn't address question

EXAMPLE:
Question: "Who scored the most points?"
Answer: "Shai Gilgeous-Alexander scored 2485 points."

Generated questions from answer:
1. "Who is the leading scorer?" (similarity: 0.95)
2. "How many points did Shai score?" (similarity: 0.85)
3. "What are the scoring stats?" (similarity: 0.80)

Answer Relevancy = (0.95 + 0.85 + 0.80) / 3 = 0.87

USE FOR: Detect off-topic answers, ensure LLM understood question
        """,
        "answer_semantic_similarity": """
ANSWER SEMANTIC SIMILARITY (Answer Quality - Uses ground_truth_answer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: How semantically similar is answer to expected answer?
HOW: Cosine similarity between embeddings
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Nearly identical meaning
⚠️  0.7-0.9: GOOD - Similar meaning, different wording
⚠️  0.5-0.7: WARNING - Related but different information
❌ 0.0-0.5: CRITICAL - Completely different meaning

EXAMPLE:
Ground Truth: "Shai scored the most points with 2485 PTS."
Actual Answer: "Shai Gilgeous-Alexander is the leading scorer with 2,485 points."

Semantic Similarity = 0.92 (same meaning, slightly different wording)

USE FOR: Check if answer conveys same information (allows paraphrasing)
        """,
        "answer_correctness": """
ANSWER CORRECTNESS (Answer Quality - Uses ground_truth_answer) ⭐ BEST OVERALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Combined semantic similarity + factual correctness
HOW: 0.5 * Semantic Similarity + 0.5 * Factual F1
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Answer is correct
⚠️  0.7-0.9: GOOD - Mostly correct with minor issues
⚠️  0.5-0.7: WARNING - Partially correct, missing key facts
❌ 0.0-0.5: CRITICAL - Answer is incorrect

EXAMPLE:
Ground Truth: "Shai scored 2485 points, leading the league."
Actual Answer: "Shai Gilgeous-Alexander scored 2485 points."

Semantic Similarity: 0.90
Factual Overlap:
- TP: "Shai", "2485 points" ✅
- FN: "leading league" ❌ (missing)
F1 = 2*2 / (2*2 + 0 + 1) = 0.80

Answer Correctness = 0.5*0.90 + 0.5*0.80 = 0.85

USE FOR: PRIMARY METRIC for overall answer quality (best single metric)
        """,
        "context_precision": """
CONTEXT PRECISION (Retrieval Quality - Uses ground_truth_vector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Are relevant chunks ranked higher than irrelevant chunks?
HOW: Precision@K averaged across positions
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Relevant chunks ranked first
⚠️  0.7-0.9: GOOD - Most relevant chunks near top
⚠️  0.5-0.7: WARNING - Relevant chunks mixed with irrelevant
❌ 0.0-0.5: CRITICAL - Relevant chunks ranked too low

EXAMPLE:
Ground Truth Vector: "Should retrieve Reddit 3.pdf about efficiency"

Retrieved chunks (in order):
1. Reddit 3.pdf, page 2 (efficiency) ✅ Relevant
2. Reddit 1.pdf, page 1 (GOAT debate) ❌ Irrelevant
3. Reddit 3.pdf, page 5 (efficiency) ✅ Relevant
4. News article (unrelated) ❌ Irrelevant

Precision@1 = 1/1 = 1.0
Precision@2 = 1/2 = 0.5
Precision@3 = 2/3 = 0.67
Precision@4 = 2/4 = 0.5

Context Precision = (1.0 + 0.5 + 0.67 + 0.5) / 4 = 0.67

USE FOR: Optimize retrieval ranking
NOTE: SKIPPED for SQL-only queries (no vector search)
        """,
        "context_recall": """
CONTEXT RECALL (Retrieval Quality - Uses ground_truth_vector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Were all required chunks retrieved?
HOW: (Retrieved required) / (Total required)
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - All required chunks retrieved
⚠️  0.7-0.9: GOOD - Most required chunks retrieved
⚠️  0.5-0.7: WARNING - Missing some required chunks
❌ 0.0-0.5: CRITICAL - Missing most required chunks

EXAMPLE:
Ground Truth Vector: "Should retrieve Reddit 3.pdf discussing efficiency,
                      specifically mentioning Reggie Miller with 115 TS%"

Required chunks:
1. Reddit 3.pdf about efficiency ✅ Retrieved
2. Mention of Reggie Miller ✅ Retrieved
3. 115 TS% statistic ❌ NOT retrieved

Context Recall = 2/3 = 0.67 (67% of required info retrieved)

USE FOR: Check if retrieval is missing key information
NOTE: SKIPPED for SQL-only queries (no vector search)
        """,
        "context_relevancy": """
CONTEXT RELEVANCY (Retrieval Quality - Uses ground_truth_vector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: What fraction of retrieved chunks are actually relevant?
HOW: (Relevant sentences) / (Total sentences)
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - No noise, all chunks relevant
⚠️  0.7-0.9: GOOD - Low noise, mostly relevant
⚠️  0.5-0.7: WARNING - Moderate noise, half irrelevant
❌ 0.0-0.5: CRITICAL - High noise, mostly irrelevant

EXAMPLE:
Question: "What do fans think about efficiency?"

Retrieved chunks:
1. "Fans believe Reggie Miller is most efficient with 115 TS%" ✅ Relevant
2. "Miller played for the Pacers" ❌ Irrelevant (not about efficiency)
3. "Efficiency is measured by TS%" ✅ Relevant
4. "LeBron is the GOAT" ❌ Irrelevant (off-topic)

Context Relevancy = 2/4 = 0.5 (50% relevant)

USE FOR: Detect noisy retrieval (too much irrelevant content)
NOTE: SKIPPED for SQL-only queries (no vector search)
        """
    }


def analyze_source_quality(results: list[dict]) -> dict[str, Any]:
    """Analyze retrieved source quality and relevance.

    Args:
        results: List of evaluation results with sources

    Returns:
        Dictionary with retrieval_stats, source_diversity, score_analysis, empty_retrievals
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
        "top_sources": top_sources[:10],
        "sources_per_query_distribution": sources_counts
    }

    min_score = min(all_scores) if all_scores else 0
    max_score = max(all_scores) if all_scores else 0

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
        normalized = score / 100.0
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

    empty_retrievals = sum(1 for r in successful_results if len(r.get("sources", [])) == 0)

    return {
        "retrieval_stats": retrieval_stats,
        "source_diversity": source_diversity,
        "score_analysis": score_analysis,
        "empty_retrievals": empty_retrievals
    }


def analyze_response_patterns(results: list[dict]) -> dict[str, Any]:
    """Analyze response patterns (length, completeness, citations, confidence).

    Args:
        results: List of evaluation results with responses

    Returns:
        Dictionary with response_length, completeness, citation_patterns, confidence_indicators
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

    lengths = [len(r["response"]) for r in successful_results]
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)

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

    declined_patterns = [
        "i don't know", "i cannot", "i'm not sure", "no information",
        "cannot find", "unable to", "not available"
    ]

    incomplete_patterns = [
        "partially", "some information", "limited", "not enough"
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
        "incomplete_cases": incomplete_cases[:10]
    }

    citation_explicit_patterns = [
        r"according to", r"based on", r"source:", r"from", r"cit(e|ing)"
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

    hedging_patterns = [
        "might", "possibly", "probably", "perhaps", "approximately",
        "around", "roughly", "may", "could", "likely"
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
    """Analyze retrieval performance metrics (scores, K-value, processing time).

    Args:
        results: List of evaluation results with retrieval metrics

    Returns:
        Dictionary with performance_metrics, k_value_analysis, score_thresholds, by_source_type
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

    configured_k = 5
    sources_counts = [len(r.get("sources", [])) for r in successful_results]
    actual_avg_retrieved = sum(sources_counts) / len(sources_counts) if sources_counts else 0
    queries_below_k = sum(1 for count in sources_counts if count < configured_k)

    k_value_analysis = {
        "configured_k": configured_k,
        "actual_avg_retrieved": round(actual_avg_retrieved, 2),
        "queries_below_k": queries_below_k
    }

    above_08 = sum(1 for score in all_scores if score >= 80)
    between_06_08 = sum(1 for score in all_scores if 60 <= score < 80)
    below_06 = sum(1 for score in all_scores if score < 60)

    score_thresholds = {
        "above_0.8": above_08,
        "0.6_to_0.8": between_06_08,
        "below_0.6": below_06
    }

    source_type_stats = defaultdict(lambda: {"count": 0, "scores": []})

    for r in successful_results:
        for source in r.get("sources", []):
            source_name = source.get("source", "unknown").lower()

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
        Dictionary with category_breakdown, comparative_analysis, recommendations
    """
    if not results:
        return {
            "category_breakdown": {},
            "comparative_analysis": {},
            "recommendations": []
        }

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
# UNIFIED INTERFACE
# ============================================================================

def analyze_results(results: list[dict], test_cases: list = None) -> dict[str, Any]:
    """Unified analysis interface for SQL, Vector, and Hybrid evaluations.

    Automatically detects test type and runs appropriate analyses.

    Args:
        results: List of evaluation result dictionaries
        test_cases: List of test case objects (optional, for oracle building)

    Returns:
        Dictionary with comprehensive analysis based on test type
    """
    if not results:
        return {
            "overall": {
                "total_queries": 0,
                "successful": 0,
                "error": "No results to analyze"
            }
        }

    # Detect test type from results
    has_sql = any(r.get("generated_sql") for r in results)
    has_ragas = any(r.get("ragas_metrics") for r in results)
    has_routing = any(r.get("routing") for r in results)

    analysis = {
        "overall": {
            "total_queries": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
        }
    }

    # SQL-specific analyses
    if has_sql:
        analysis["error_taxonomy"] = analyze_error_taxonomy(results)
        analysis["response_quality"] = analyze_response_quality(results)
        analysis["query_structure"] = analyze_query_structure(results)
        analysis["query_complexity"] = analyze_query_complexity(results)
        analysis["column_selection"] = analyze_column_selection(results)

    # Vector-specific analyses (run for all results that have RAGAS or sources)
    if has_ragas or any(r.get("sources") for r in results):
        analysis["source_quality"] = analyze_source_quality(results)
        analysis["response_patterns"] = analyze_response_patterns(results)
        analysis["retrieval_performance"] = analyze_retrieval_performance(results)

        # RAGAS metrics analysis (ALL 7 METRICS with nuclear explanations)
        if has_ragas:
            analysis["ragas_metrics"] = analyze_ragas_metrics(results)
            analysis["category_performance"] = analyze_category_performance(results)

    return analysis
