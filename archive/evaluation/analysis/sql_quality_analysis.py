"""
FILE: sql_quality_analysis.py
STATUS: Active
RESPONSIBILITY: SQL evaluation analysis coordination - unified interface analyze_results(), individual analysis functions, SQL validation oracle
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import re
from collections import defaultdict
from typing import Any


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


def analyze_fallback_patterns(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze when system falls back from SQL to vector search.

    SQL-only: sources_count == 0
    SQL → Vector fallback: sources_count > 0

    Args:
        results: List of evaluation result dictionaries

    Returns:
        Dictionary with fallback statistics by category
    """
    fallback_stats = {
        "total_queries": len(results),
        "sql_only": 0,
        "fallback_to_vector": 0,
        "fallback_rate": 0.0,
        "by_category": defaultdict(lambda: {"total": 0, "fallbacks": 0, "rate": 0.0}),
        "fallback_cases": []
    }

    for result in results:
        sources_count = result.get("sources_count", 0)
        category = result.get("category", "unknown")
        question = result.get("question", "")

        fallback_stats["by_category"][category]["total"] += 1

        if sources_count == 0:
            fallback_stats["sql_only"] += 1
        else:
            fallback_stats["fallback_to_vector"] += 1
            fallback_stats["by_category"][category]["fallbacks"] += 1
            fallback_stats["fallback_cases"].append({
                "question": question,
                "category": category,
                "sources_count": sources_count,
                "response": result.get("response", "")[:200]
            })

    if fallback_stats["total_queries"] > 0:
        fallback_stats["fallback_rate"] = (
            fallback_stats["fallback_to_vector"] / fallback_stats["total_queries"]
        ) * 100

    for category, stats in fallback_stats["by_category"].items():
        if stats["total"] > 0:
            stats["rate"] = (stats["fallbacks"] / stats["total"]) * 100

    return fallback_stats


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

        # Check JOIN correctness: only flag as "missing JOIN" if the query
        # references player_stats but NOT players table AND needs player names.
        # Aggregate-only queries (COUNT, AVG, etc.) on player_stats alone are valid.
        sql_lower = sql.lower()
        has_players_table = "players" in sql_lower
        has_player_stats_table = "player_stats" in sql_lower
        has_join = "JOIN" in sql_upper

        if has_players_table and has_player_stats_table and has_join:
            structure_stats["correctness"]["correct_joins"] += 1
        elif has_player_stats_table and not has_join:
            # Check if query actually needs player names (SELECT p.name, WHERE p.name)
            # Aggregate queries on player_stats alone (AVG, COUNT, MAX, etc.) don't need JOIN
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
# UNIFIED INTERFACE: Wrapper functions for consistent runner patterns
# ============================================================================

class SQLOracle:
    """Ground truth oracle for validating SQL evaluation results."""

    def __init__(self):
        """Initialize oracle with ground truth from test cases."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES
        self.oracle = self._build_oracle(SQL_TEST_CASES)

    def _build_oracle(self, test_cases) -> dict[str, dict[str, Any]]:
        """Build oracle from test case ground truth."""
        oracle = {}
        for test_case in test_cases:
            key = test_case.question.strip().lower()
            oracle[key] = {
                "expected_answer": test_case.ground_truth_answer,
                "expected_data": test_case.ground_truth_data,
                "category": getattr(test_case, "category", "unknown"),
            }
        return oracle

    def get_oracle_entry(self, question: str) -> dict[str, Any] | None:
        """Retrieve oracle entry for a question."""
        key = question.strip().lower()
        return self.oracle.get(key)

    def validate_result(self, question: str, actual_response: str) -> bool:
        """Validate if response is semantically correct."""
        if not actual_response or not actual_response.strip():
            return False
        oracle_entry = self.get_oracle_entry(question)
        if oracle_entry is None:
            return False
        # Simple validation: check if key numeric values appear in response
        response_lower = actual_response.lower()
        expected_data = oracle_entry.get("expected_data")
        if isinstance(expected_data, dict):
            for value in expected_data.values():
                if isinstance(value, (int, float)):
                    if str(value) not in response_lower and str(int(value)) not in response_lower:
                        return False
        return True


def analyze_results(results: list[dict], test_cases: list) -> dict[str, Any]:
    """Unified interface: Analyze SQL evaluation results.

    This wrapper handles oracle creation and calls all analysis functions
    to match the pattern used by Vector and Hybrid runners.

    Args:
        results: List of evaluation result dictionaries
        test_cases: List of test case objects (for oracle building)

    Returns:
        Dictionary with comprehensive analysis
    """
    oracle = SQLOracle()

    analysis = {
        "overall": {
            "total_queries": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
        }
    }

    # Add all detailed analysis
    analysis["error_taxonomy"] = analyze_error_taxonomy(results)
    analysis["fallback_patterns"] = analyze_fallback_patterns(results)
    analysis["response_quality"] = analyze_response_quality(results)
    analysis["query_structure"] = analyze_query_structure(results)
    analysis["query_complexity"] = analyze_query_complexity(results)
    analysis["column_selection"] = analyze_column_selection(results)

    # Calculate accuracy using oracle
    successful = [r for r in results if r.get("success", False)]
    if successful:
        correct_count = sum(
            1 for r in successful
            if oracle.validate_result(r.get("question", ""), r.get("response", ""))
        )
        analysis["overall"]["accuracy_rate"] = round(correct_count / len(successful) * 100, 2)
    else:
        analysis["overall"]["accuracy_rate"] = 0

    return analysis
