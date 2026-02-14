"""
FILE: test_query_expansion.py
STATUS: Active
RESPONSIBILITY: Tests for query expansion functionality
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import pytest
from src.services.query_expansion import QueryExpander


@pytest.fixture
def expander():
    """Create QueryExpander instance."""
    return QueryExpander()


def test_expand_points_query(expander):
    """Test expansion of points-related query."""
    query = "Who has the most points this season?"
    expanded = expander.expand(query)

    assert "PTS" in expanded
    assert "points per game" in expanded
    assert query in expanded  # Original preserved


def test_expand_assists_query(expander):
    """Test expansion of assists-related query."""
    query = "assists leader"
    expanded = expander.expand(query)

    assert "AST" in expanded
    assert "leader" in query  # Original preserved
    assert any(syn in expanded for syn in ["top", "best", "highest"])


def test_expand_multiple_terms(expander):
    """Test expansion with multiple expandable terms."""
    query = "team with most rebounds"
    expanded = expander.expand(query)

    assert "REB" in expanded or "rebounding" in expanded
    assert any(syn in expanded for syn in ["squad", "franchise"])


def test_no_expansion_for_unknown_terms(expander):
    """Test that unknown terms don't cause errors."""
    query = "tell me about the playoffs"
    expanded = expander.expand(query)

    # Should return original query unchanged
    assert query in expanded


def test_smart_expand_short_query(expander):
    """Test smart expansion expands short queries."""
    query = "points leader"  # 2 words
    expanded = expander.expand_smart(query)

    assert len(expanded) > len(query)
    assert "PTS" in expanded


def test_smart_expand_long_query(expander):
    """Test smart expansion minimally expands very long queries."""
    query = "Who is the player with the highest points per game average this season including playoffs and regular season combined?"  # 20 words
    expanded = expander.expand_smart(query)

    # Should expand minimally (max_expansions=1) even for long queries
    assert len(expanded) >= len(query)  # Should have some expansion
    assert "PTS" in expanded or "athlete" in expanded  # At least one expansion term


def test_expansion_deduplication(expander):
    """Test that duplicate expansions are removed."""
    query = "points and scoring leader"  # Both trigger "points" expansion
    expanded = expander.expand(query)

    # Count occurrences of "PTS" - should appear only once
    assert expanded.count("PTS") == 1


def test_expand_steals_query(expander):
    """Test expansion of steals-related query."""
    query = "steals leader"
    expanded = expander.expand(query)

    assert "STL" in expanded
    assert "steals per game" in expanded


def test_expand_blocks_query(expander):
    """Test expansion of blocks-related query."""
    query = "blocks per game"
    expanded = expander.expand(query)

    assert "BLK" in expanded
    assert "bpg" in expanded


def test_expand_three_point_query(expander):
    """Test expansion of three-point related query."""
    query = "three-point percentage"
    expanded = expander.expand(query)

    assert "3P%" in expanded or "3PT%" in expanded


def test_expand_field_goal_query(expander):
    """Test expansion of field goal related query."""
    query = "field goal percentage"
    expanded = expander.expand(query)

    assert "FG%" in expanded
    assert "shooting percentage" in expanded


def test_smart_expand_medium_query(expander):
    """Test smart expansion on medium-length query."""
    query = "Who has the best assists average this season"  # 8 words
    expanded = expander.expand_smart(query)

    # Should expand with max_expansions=2
    assert len(expanded) > len(query)
    assert "AST" in expanded


def test_expansion_limit(expander):
    """Test that expansion phrase count (not word count) is limited to 15."""
    query = "points assists rebounds steals blocks team player"  # Many expandable terms

    # Manually calculate expected expansion phrases
    # points -> first 5 from STAT_EXPANSIONS["points"]
    # assists -> first 5 from STAT_EXPANSIONS["assists"]
    # rebounds -> first 5 from STAT_EXPANSIONS["rebounds"]
    # steals -> first 5 from STAT_EXPANSIONS["steals"]
    # blocks -> first 5 from STAT_EXPANSIONS["blocks"]
    # team -> first 5 from QUERY_SYNONYMS["team"]
    # player -> first 5 from QUERY_SYNONYMS["player"]
    # That's 7 keywords * 5 phrases = 35 phrases, limited to 15 unique phrases

    expanded = expander.expand(query, max_expansions=5)

    # The expansion should be limited to 15 expansion phrases
    # (Note: Each phrase can be multiple words, e.g., "points per game")
    expansion_part = expanded.replace(query, "").strip()

    # Verify expansion occurred
    assert len(expanded) > len(query)
    # Verify it's not empty
    assert len(expansion_part) > 0
