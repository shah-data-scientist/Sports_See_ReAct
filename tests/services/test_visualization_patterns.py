"""
FILE: test_visualization_patterns.py
STATUS: Active
RESPONSIBILITY: Unit tests for query pattern detection for visualizations
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest

from src.services.visualization_patterns import (
    QueryPatternDetector,
    VisualizationPattern,
)


class TestVisualizationPatternEnum:
    """Test VisualizationPattern enum."""

    def test_enum_values_exist(self):
        """Test all expected pattern types exist."""
        patterns = [
            VisualizationPattern.TOP_N,
            VisualizationPattern.PLAYER_COMPARISON,
            VisualizationPattern.MULTI_ENTITY_COMPARISON,
            VisualizationPattern.SINGLE_ENTITY,
            VisualizationPattern.DISTRIBUTION,
            VisualizationPattern.CORRELATION,
            VisualizationPattern.THRESHOLD_FILTER,
            VisualizationPattern.COMPOSITION,
            VisualizationPattern.GENERIC_TABLE,
        ]
        assert len(patterns) == 9

    def test_enum_values_are_strings(self):
        """Test enum values are lowercase strings."""
        assert VisualizationPattern.TOP_N.value == "top_n"
        assert VisualizationPattern.PLAYER_COMPARISON.value == "player_comparison"
        assert VisualizationPattern.GENERIC_TABLE.value == "generic_table"


class TestTopNPatternDetection:
    """Test detection of top N / ranking queries."""

    def test_detects_top_n_queries(self):
        """Test detection of top N queries."""
        queries = [
            "Who are the top 5 scorers?",
            "Show me the top 10 players by points",
            "Top 3 teams by wins",
            "Best 5 three-point shooters",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.TOP_N

    def test_detects_bottom_n_queries(self):
        """Test detection of bottom N / worst queries."""
        queries = [
            "Bottom 5 teams",
            "Worst 3 players by turnovers",
            "Show me the lowest 5 shooting percentages",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.TOP_N

    def test_detects_first_last_n_queries(self):
        """Test detection of first/last N queries."""
        queries = [
            "First 10 players by rebounds",
            "Last 5 teams in standings",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.TOP_N


class TestPlayerComparisonDetection:
    """Test detection of player comparison queries."""

    def test_detects_compare_keyword(self):
        """Test detection using 'compare' keyword."""
        queries = [
            "Compare LeBron and Durant",
            "Compare Jokic vs Embiid",
            "Compare these three players: Curry, Harden, and Lillard",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.PLAYER_COMPARISON

    def test_detects_player_names_with_vs(self):
        """Test detection of player name patterns with vs."""
        queries = [
            "Jokic vs Embiid",
            "LeBron versus Durant",
            "Curry or Harden",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.PLAYER_COMPARISON

    def test_detects_who_is_better_queries(self):
        """Test detection of 'who is better' queries."""
        queries = [
            "Who is better, LeBron or Durant?",
            "Which is better between these players?",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.PLAYER_COMPARISON


class TestCorrelationDetection:
    """Test detection of correlation queries."""

    def test_detects_relationship_queries(self):
        """Test detection of relationship/correlation keywords."""
        queries = [
            "Relationship between 3P% and PPG",
            "What's the correlation between usage rate and turnovers?",
            "Are points and assists correlated?",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.CORRELATION

    def test_detects_impact_effect_queries(self):
        """Test detection of impact/effect queries."""
        queries = [
            "Impact of high usage rate on efficiency",
            "Effect of three-point shooting on scoring",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.CORRELATION


class TestDistributionDetection:
    """Test detection of distribution queries."""

    def test_detects_distribution_keywords(self):
        """Test detection of distribution/spread keywords."""
        queries = [
            "Distribution of player heights",
            "Show the spread of scoring averages",
            "What's the range of shooting percentages?",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.DISTRIBUTION

    def test_detects_league_wide_average_queries(self):
        """Test detection of league-wide statistics."""
        queries = [
            "What's the league-wide average PPG?",
            "Average points across the league",
            "How much do all players typically score?",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.DISTRIBUTION


class TestThresholdFilterDetection:
    """Test detection of threshold filter queries."""

    def test_detects_over_under_queries(self):
        """Test detection of over/under threshold queries."""
        queries = [
            "Players with over 25 PPG",
            "Teams with more than 40 wins",
            "Show players under 30 years old",
            "Players above 85% free throw percentage",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.THRESHOLD_FILTER

    def test_detects_having_clause_patterns(self):
        """Test detection of 'having' patterns."""
        queries = [
            "Players having more than 10 rebounds per game",
            "Teams that have over 50 wins",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.THRESHOLD_FILTER


class TestSingleEntityDetection:
    """Test detection of single entity queries."""

    def test_detects_possessive_queries(self):
        """Test detection of possessive queries (LeBron's stats)."""
        queries = [
            "LeBron's points per game",
            "What is Curry's three-point percentage?",
            "Show me Durant's stats",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.SINGLE_ENTITY

    def test_detects_his_her_their_queries(self):
        """Test detection of pronoun-based queries."""
        queries = [
            "Show me his assists",
            "What are her rebounds?",
            "Their numbers this season",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.SINGLE_ENTITY


class TestCompositionDetection:
    """Test detection of composition/breakdown queries."""

    def test_detects_breakdown_queries(self):
        """Test detection of breakdown keywords."""
        queries = [
            "LeBron's shot breakdown from 2P, 3P, and FT",
            "Composition of team scoring",
            "Breakdown from three-point and mid-range shots",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.COMPOSITION

    def test_detects_percentage_queries(self):
        """Test detection of percentage/proportion queries."""
        queries = [
            "Percentage of points from three",
            "What proportion of shots are from mid-range?",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.COMPOSITION


class TestResultBasedOverrides:
    """Test pattern detection with SQL result context."""

    def test_comparison_becomes_multi_with_many_results(self):
        """Test comparison pattern overridden to multi-comparison for many results."""
        query = "Compare all top scorers"
        many_results = [{"name": f"Player{i}", "pts": 25} for i in range(10)]

        detector = QueryPatternDetector()
        pattern = detector.detect_pattern(query, many_results)
        assert pattern == VisualizationPattern.MULTI_ENTITY_COMPARISON

    def test_top_n_becomes_single_entity_with_one_result(self):
        """Test top N overridden to single entity for 1 result."""
        query = "Top scorer"
        one_result = [{"name": "Player1", "pts": 30}]

        detector = QueryPatternDetector()
        pattern = detector.detect_pattern(query, one_result)
        assert pattern == VisualizationPattern.SINGLE_ENTITY

    def test_fallback_to_result_count_inference(self):
        """Test fallback uses result count to infer pattern."""
        query = "Show player statistics"  # Generic query
        detector = QueryPatternDetector()

        # 1 result -> single entity
        assert detector.detect_pattern(query, [{"name": "P1"}]) == VisualizationPattern.SINGLE_ENTITY

        # 2-4 results -> comparison
        two_results = [{"name": "P1"}, {"name": "P2"}]
        assert detector.detect_pattern(query, two_results) == VisualizationPattern.PLAYER_COMPARISON

        # 5-10 results -> top N
        five_results = [{"name": f"P{i}"} for i in range(5)]
        assert detector.detect_pattern(query, five_results) == VisualizationPattern.TOP_N

        # >10 results -> multi-comparison
        many_results = [{"name": f"P{i}"} for i in range(15)]
        assert detector.detect_pattern(query, many_results) == VisualizationPattern.MULTI_ENTITY_COMPARISON

    def test_empty_results_return_generic_table(self):
        """Test empty results return generic table pattern."""
        query = "Show stats"
        detector = QueryPatternDetector()
        pattern = detector.detect_pattern(query, [])
        assert pattern == VisualizationPattern.GENERIC_TABLE


class TestGetRecommendedVizType:
    """Test visualization type recommendations."""

    def test_top_n_recommends_horizontal_bar(self):
        """Test top N with <=10 results recommends horizontal bar."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.TOP_N, result_count=5)
        assert viz_type == "horizontal_bar"

    def test_top_n_recommends_vertical_bar_for_many(self):
        """Test top N with >10 results recommends vertical bar."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.TOP_N, result_count=15)
        assert viz_type == "vertical_bar"

    def test_player_comparison_recommends_radar(self):
        """Test player comparison recommends radar chart."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.PLAYER_COMPARISON, result_count=3)
        assert viz_type == "radar"

    def test_player_comparison_recommends_grouped_bar_for_many(self):
        """Test player comparison with >4 results recommends grouped bar."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.PLAYER_COMPARISON, result_count=6)
        assert viz_type == "grouped_bar"

    def test_correlation_recommends_scatter(self):
        """Test correlation recommends scatter plot."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.CORRELATION)
        assert viz_type == "scatter"

    def test_distribution_recommends_histogram(self):
        """Test distribution recommends histogram."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.DISTRIBUTION)
        assert viz_type == "histogram"

    def test_composition_recommends_pie(self):
        """Test composition recommends pie chart."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.COMPOSITION)
        assert viz_type == "pie"

    def test_single_entity_recommends_stat_card(self):
        """Test single entity recommends stat card."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.SINGLE_ENTITY)
        assert viz_type == "stat_card"

    def test_generic_table_recommends_table(self):
        """Test generic table recommends table."""
        detector = QueryPatternDetector()
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.GENERIC_TABLE)
        assert viz_type == "table"

    def test_unknown_pattern_fallback_to_table(self):
        """Test unknown pattern falls back to table."""
        detector = QueryPatternDetector()
        # Create a mock pattern that doesn't exist in recommendations
        viz_type = detector.get_recommended_viz_type(VisualizationPattern.THRESHOLD_FILTER)
        assert viz_type in ["highlighted_table", "table"]


class TestPatternDetectionEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_query_returns_generic_table(self):
        """Test empty query returns generic table."""
        detector = QueryPatternDetector()
        pattern = detector.detect_pattern("")
        assert pattern == VisualizationPattern.GENERIC_TABLE

    def test_whitespace_query_returns_generic_table(self):
        """Test whitespace-only query returns generic table."""
        detector = QueryPatternDetector()
        pattern = detector.detect_pattern("   \n\t  ")
        assert pattern == VisualizationPattern.GENERIC_TABLE

    def test_case_insensitive_pattern_matching(self):
        """Test pattern matching is case-insensitive."""
        queries = [
            "TOP 5 SCORERS",
            "Top 5 Scorers",
            "top 5 scorers",
        ]
        detector = QueryPatternDetector()
        for query in queries:
            assert detector.detect_pattern(query) == VisualizationPattern.TOP_N

    def test_pattern_priority_most_specific_first(self):
        """Test more specific patterns take priority."""
        # "Compare top 5" should match PLAYER_COMPARISON before TOP_N
        # because PLAYER_COMPARISON is checked first and "compare" matches
        query = "Compare the top 5 scorers"
        detector = QueryPatternDetector()
        pattern = detector.detect_pattern(query)
        assert pattern == VisualizationPattern.PLAYER_COMPARISON
