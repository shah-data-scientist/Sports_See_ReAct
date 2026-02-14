"""
FILE: test_sql_quality_analysis.py
STATUS: Active
RESPONSIBILITY: Tests for SQL quality analysis functions
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest

from src.evaluation.analysis.sql_quality_analysis import (
    analyze_column_selection,
    analyze_error_taxonomy,
    analyze_fallback_patterns,
    analyze_query_complexity,
    analyze_query_structure,
    analyze_response_quality,
)


class TestAnalyzeErrorTaxonomy:
    """Tests for analyze_error_taxonomy function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = analyze_error_taxonomy([])
        assert result["total_errors"] == 0
        assert len(result["llm_declined"]) == 0
        assert len(result["syntax_error"]) == 0
        assert len(result["empty_response"]) == 0

    def test_llm_declined_patterns(self):
        """Test detection of LLM declined responses."""
        results = [
            {"question": "Q1", "response": "I cannot answer this question."},
            {"question": "Q2", "response": "The database doesn't contain this info."},
            {"question": "Q3", "response": "No data available for this query."},
        ]
        result = analyze_error_taxonomy(results)
        assert result["total_errors"] == 3
        assert len(result["llm_declined"]) == 3
        assert len(result["syntax_error"]) == 0
        assert len(result["empty_response"]) == 0

    def test_syntax_error_patterns(self):
        """Test detection of SQL syntax errors."""
        results = [
            {"question": "Q1", "response": "SQLite error: no such table"},
            {"question": "Q2", "response": "SQL syntax error near FROM"},
        ]
        result = analyze_error_taxonomy(results)
        assert result["total_errors"] == 2
        assert len(result["syntax_error"]) == 2
        assert len(result["llm_declined"]) == 0

    def test_empty_responses(self):
        """Test detection of empty responses."""
        results = [
            {"question": "Q1", "response": ""},
            {"question": "Q2", "response": "   "},
            {"question": "Q3", "response": "abc"},  # Too short (< 5 chars)
        ]
        result = analyze_error_taxonomy(results)
        assert result["total_errors"] == 3
        assert len(result["empty_response"]) == 3

    def test_mixed_errors(self):
        """Test with mix of different error types."""
        results = [
            {"question": "Q1", "response": "Valid response here"},
            {"question": "Q2", "response": "I cannot find this information"},
            {"question": "Q3", "response": ""},
            {"question": "Q4", "response": "SQLite error occurred"},
        ]
        result = analyze_error_taxonomy(results)
        assert result["total_errors"] == 3
        assert len(result["llm_declined"]) == 1
        assert len(result["empty_response"]) == 1
        assert len(result["syntax_error"]) == 1


class TestAnalyzeFallbackPatterns:
    """Tests for analyze_fallback_patterns function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = analyze_fallback_patterns([])
        assert result["total_queries"] == 0
        assert result["sql_only"] == 0
        assert result["fallback_to_vector"] == 0

    def test_sql_only_routing(self):
        """Test detection of SQL-only routing (no sources)."""
        results = [
            {"question": "Q1", "category": "simple", "sources_count": 0},
            {"question": "Q2", "category": "simple", "sources_count": 0},
        ]
        result = analyze_fallback_patterns(results)
        assert result["sql_only"] == 2
        assert result["fallback_to_vector"] == 0
        assert result["total_queries"] == 2

    def test_fallback_to_vector(self):
        """Test detection of fallback to vector search."""
        results = [
            {"question": "Q1", "category": "complex", "sources_count": 3},
            {"question": "Q2", "category": "complex", "sources_count": 5},
        ]
        result = analyze_fallback_patterns(results)
        assert result["sql_only"] == 0
        assert result["fallback_to_vector"] == 2
        assert result["total_queries"] == 2

    def test_fallback_by_category(self):
        """Test fallback patterns grouped by category."""
        results = [
            {"question": "Q1", "category": "simple", "sources_count": 0},
            {"question": "Q2", "category": "simple", "sources_count": 3},
            {"question": "Q3", "category": "complex", "sources_count": 0},
            {"question": "Q4", "category": "complex", "sources_count": 5},
        ]
        result = analyze_fallback_patterns(results)
        assert "by_category" in result
        assert result["by_category"]["simple"]["total"] == 2
        assert result["by_category"]["simple"]["fallbacks"] == 1
        assert result["by_category"]["complex"]["total"] == 2
        assert result["by_category"]["complex"]["fallbacks"] == 1


class TestAnalyzeResponseQuality:
    """Tests for analyze_response_quality function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = analyze_response_quality([])
        assert "verbosity" in result
        assert "confidence_indicators" in result
        assert "completeness" in result

    def test_response_length_stats(self):
        """Test calculation of response length statistics."""
        results = [
            {"response": "Short"},  # 5 chars
            {"response": "Medium length response here"},  # 29 chars
            {"response": "Very long response " * 10},  # 190 chars
        ]
        result = analyze_response_quality(results)
        assert result["verbosity"]["min_length"] == 5
        assert result["verbosity"]["max_length"] == 190
        assert result["verbosity"]["avg_length"] > 0

    def test_structure_contains_expected_keys(self):
        """Test that result contains all expected keys."""
        results = [{"response": "Test answer"}]
        result = analyze_response_quality(results)
        assert "verbosity" in result
        assert "confidence_indicators" in result
        assert "completeness" in result


class TestAnalyzeQueryStructure:
    """Tests for analyze_query_structure function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = analyze_query_structure([])
        assert result["total_queries"] == 0
        assert result["queries_with_join"] == 0

    def test_join_detection(self):
        """Test detection of JOIN clauses."""
        results = [
            {"generated_sql": "SELECT * FROM players JOIN stats ON players.id = stats.player_id"},
            {"generated_sql": "SELECT * FROM players"},
            {"generated_sql": "SELECT * FROM teams INNER JOIN players ON teams.id = players.team_id"},
        ]
        result = analyze_query_structure(results)
        assert result["total_queries"] == 3
        assert result["queries_with_join"] == 2

    def test_aggregation_detection(self):
        """Test detection of aggregation functions."""
        results = [
            {"generated_sql": "SELECT COUNT(*) FROM players"},
            {"generated_sql": "SELECT AVG(points) FROM stats"},
            {"generated_sql": "SELECT SUM(rebounds), MAX(assists) FROM stats"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_structure(results)
        assert result["queries_with_aggregation"] >= 3

    def test_where_clause_detection(self):
        """Test detection of WHERE clauses."""
        results = [
            {"generated_sql": "SELECT * FROM players WHERE points > 1000"},
            {"generated_sql": "SELECT * FROM players WHERE team = 'Lakers' AND age < 30"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_structure(results)
        assert result["queries_with_filter"] == 2

    def test_order_by_detection(self):
        """Test detection of ORDER BY clauses."""
        results = [
            {"generated_sql": "SELECT * FROM players ORDER BY points DESC"},
            {"generated_sql": "SELECT * FROM players ORDER BY name"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_structure(results)
        assert result["queries_with_ordering"] == 2

    def test_limit_detection(self):
        """Test detection of LIMIT clauses."""
        results = [
            {"generated_sql": "SELECT * FROM players LIMIT 10"},
            {"generated_sql": "SELECT * FROM players LIMIT 5"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_structure(results)
        assert result["queries_with_limit"] == 2

    def test_none_sql_handling(self):
        """Test handling of None SQL queries."""
        results = [
            {"generated_sql": None},
            {"generated_sql": "SELECT * FROM players"},
            {},  # Missing generated_sql key
        ]
        result = analyze_query_structure(results)
        assert result["total_queries"] == 1  # Only count valid SQL


class TestAnalyzeQueryComplexity:
    """Tests for analyze_query_complexity function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = analyze_query_complexity([])
        assert result["avg_joins_per_query"] == 0
        assert result["avg_where_conditions"] == 0

    def test_join_counting(self):
        """Test counting of JOIN operations."""
        results = [
            {"generated_sql": "SELECT * FROM players JOIN stats ON players.id = stats.player_id"},
            {"generated_sql": "SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_complexity(results)
        assert result["avg_joins_per_query"] > 0

    def test_where_condition_counting(self):
        """Test counting of WHERE conditions."""
        results = [
            {"generated_sql": "SELECT * FROM players WHERE age > 25"},
            {"generated_sql": "SELECT * FROM players WHERE age > 25 AND points > 1000"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_complexity(results)
        assert result["avg_where_conditions"] > 0

    def test_subquery_detection(self):
        """Test detection of subqueries."""
        results = [
            {"generated_sql": "SELECT * FROM players WHERE id IN (SELECT player_id FROM stats)"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_complexity(results)
        assert result["queries_with_subqueries"] == 1

    def test_group_by_detection(self):
        """Test detection of GROUP BY clauses."""
        results = [
            {"generated_sql": "SELECT team, COUNT(*) FROM players GROUP BY team"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_complexity(results)
        assert result["queries_with_group_by"] == 1

    def test_having_detection(self):
        """Test detection of HAVING clauses."""
        results = [
            {"generated_sql": "SELECT team, COUNT(*) FROM players GROUP BY team HAVING COUNT(*) > 5"},
            {"generated_sql": "SELECT * FROM players"},
        ]
        result = analyze_query_complexity(results)
        assert result["queries_with_having"] == 1

    def test_complexity_distribution(self):
        """Test complexity level distribution."""
        results = [
            {"generated_sql": "SELECT * FROM players"},  # Simple
            {"generated_sql": "SELECT * FROM players WHERE age > 25"},  # Moderate
            {"generated_sql": "SELECT * FROM players JOIN stats ON players.id = stats.player_id WHERE age > 25"},  # Moderate
            {"generated_sql": "SELECT team, AVG(points) FROM players GROUP BY team HAVING AVG(points) > 20"},  # Complex
        ]
        result = analyze_query_complexity(results)
        assert "complexity_distribution" in result
        assert result["complexity_distribution"]["simple"] >= 1
        assert result["complexity_distribution"]["moderate"] >= 1


class TestAnalyzeColumnSelection:
    """Tests for analyze_column_selection function."""

    def test_empty_results(self):
        """Test with empty results list."""
        result = analyze_column_selection([])
        assert result["avg_columns_selected"] == 0
        assert result["select_star_count"] == 0

    def test_select_star_detection(self):
        """Test detection of SELECT * queries."""
        results = [
            {"generated_sql": "SELECT * FROM players"},
            {"generated_sql": "SELECT * FROM teams"},
            {"generated_sql": "SELECT name, age FROM players"},
        ]
        result = analyze_column_selection(results)
        assert result["select_star_count"] == 2
        assert result["total_queries"] == 3

    def test_column_counting(self):
        """Test counting of selected columns."""
        results = [
            {"generated_sql": "SELECT name FROM players"},  # 1 column
            {"generated_sql": "SELECT name, age, team FROM players"},  # 3 columns
            {"generated_sql": "SELECT a, b, c, d, e FROM table"},  # 5 columns
        ]
        result = analyze_column_selection(results)
        assert result["avg_columns_selected"] == 3.0  # (1 + 3 + 5) / 3
        assert result["total_queries"] == 3

    def test_aggregation_in_select(self):
        """Test handling of aggregation functions in SELECT."""
        results = [
            {"generated_sql": "SELECT COUNT(*) FROM players"},
            {"generated_sql": "SELECT AVG(points), MAX(rebounds) FROM stats"},
        ]
        result = analyze_column_selection(results)
        assert result["total_queries"] == 2

    def test_none_sql_handling(self):
        """Test handling of None SQL queries."""
        results = [
            {"generated_sql": None},
            {"generated_sql": "SELECT name FROM players"},
            {},  # Missing generated_sql key
        ]
        result = analyze_column_selection(results)
        assert result["total_queries"] == 1


class TestIntegration:
    """Integration tests for all analysis functions together."""

    def test_all_functions_with_realistic_data(self):
        """Test all analysis functions with realistic evaluation data."""
        results = [
            {
                "question": "Who scored the most points?",
                "category": "simple",
                "response": "LeBron James scored 2500 points.",
                "sources_count": 0,
                "generated_sql": "SELECT name, points FROM players ORDER BY points DESC LIMIT 1",
            },
            {
                "question": "Top 5 rebounders?",
                "category": "simple",
                "response": "I cannot find this information.",
                "sources_count": 3,
                "generated_sql": None,
            },
            {
                "question": "Compare stats?",
                "category": "complex",
                "response": "",
                "sources_count": 0,
                "generated_sql": "SELECT * FROM players WHERE id IN (SELECT player_id FROM stats)",
            },
        ]

        # Test all functions don't crash
        error_tax = analyze_error_taxonomy(results)
        fallback = analyze_fallback_patterns(results)
        quality = analyze_response_quality(results)
        structure = analyze_query_structure(results)
        complexity = analyze_query_complexity(results)
        columns = analyze_column_selection(results)

        # Basic assertions
        assert error_tax["total_errors"] >= 1
        assert fallback["total_queries"] == 3
        assert "verbosity" in quality
        assert structure["total_queries"] == 2
        assert complexity["avg_joins_per_query"] >= 0
        assert columns["total_queries"] == 2
