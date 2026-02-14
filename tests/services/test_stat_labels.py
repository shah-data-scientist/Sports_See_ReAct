"""
FILE: test_stat_labels.py
STATUS: Active
RESPONSIBILITY: Unit tests for stat label mapping and formatting
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest

from src.services.stat_labels import STAT_LABELS, get_stat_label, format_stat_labels


class TestStatLabelsMapping:
    """Test the STAT_LABELS dictionary mappings."""

    def test_basic_stats_mapped(self):
        """Test basic counting stats have correct mappings."""
        assert STAT_LABELS["pts"] == "PTS (Points)"
        assert STAT_LABELS["reb"] == "REB (Rebounds)"
        assert STAT_LABELS["ast"] == "AST (Assists)"
        assert STAT_LABELS["stl"] == "STL (Steals)"
        assert STAT_LABELS["blk"] == "BLK (Blocks)"

    def test_shooting_stats_mapped(self):
        """Test shooting stats have correct mappings."""
        assert STAT_LABELS["fgm"] == "FGM (Field Goals Made)"
        assert STAT_LABELS["fga"] == "FGA (Field Goals Attempted)"
        assert STAT_LABELS["fg_pct"] == "FG% (Field Goal Percentage)"
        assert STAT_LABELS["ftm"] == "FTM (Free Throws Made)"
        assert STAT_LABELS["ft_pct"] == "FT% (Free Throw Percentage)"

    def test_three_point_stats_mapped(self):
        """Test three-point stats have correct mappings."""
        assert STAT_LABELS["3pm"] == "3PM (3-Pointers Made)"
        assert STAT_LABELS["3pa"] == "3PA (3-Pointers Attempted)"
        assert STAT_LABELS["three_pct"] == "3P% (3-Point Percentage)"
        assert STAT_LABELS["3p_pct"] == "3P% (3-Point Percentage)"

    def test_advanced_stats_mapped(self):
        """Test advanced stats have correct mappings."""
        assert STAT_LABELS["efg_pct"] == "eFG% (Effective Field Goal Percentage)"
        assert STAT_LABELS["ts_pct"] == "TS% (True Shooting Percentage)"
        assert STAT_LABELS["usg_pct"] == "USG% (Usage Percentage)"
        assert STAT_LABELS["ast_to"] == "AST/TO (Assist-to-Turnover Ratio)"

    def test_per_game_stats_mapped(self):
        """Test per-game stats have correct mappings."""
        assert STAT_LABELS["ppg"] == "PPG (Points Per Game)"
        assert STAT_LABELS["rpg"] == "RPG (Rebounds Per Game)"
        assert STAT_LABELS["apg"] == "APG (Assists Per Game)"
        assert STAT_LABELS["spg"] == "SPG (Steals Per Game)"
        assert STAT_LABELS["mpg"] == "MPG (Minutes Per Game)"

    def test_long_form_variations_mapped(self):
        """Test long-form stat names have correct mappings."""
        assert STAT_LABELS["points"] == "PTS (Points)"
        assert STAT_LABELS["rebounds"] == "REB (Rebounds)"
        assert STAT_LABELS["assists"] == "AST (Assists)"
        assert STAT_LABELS["minutes"] == "MIN (Minutes)"
        assert STAT_LABELS["games"] == "GP (Games Played)"


class TestGetStatLabel:
    """Test get_stat_label function."""

    def test_get_label_for_known_stat(self):
        """Test getting label for known stat abbreviation."""
        assert get_stat_label("pts") == "PTS (Points)"
        assert get_stat_label("reb") == "REB (Rebounds)"
        assert get_stat_label("ast") == "AST (Assists)"

    def test_get_label_case_insensitive(self):
        """Test case-insensitive stat lookup."""
        assert get_stat_label("PTS") == "PTS (Points)"
        assert get_stat_label("Pts") == "PTS (Points)"
        assert get_stat_label("pTs") == "PTS (Points)"

    def test_get_label_with_whitespace(self):
        """Test stat lookup handles leading/trailing whitespace."""
        assert get_stat_label("  pts  ") == "PTS (Points)"
        assert get_stat_label("\treb\n") == "REB (Rebounds)"

    def test_get_label_for_unknown_stat(self):
        """Test fallback for unknown stat returns uppercase."""
        assert get_stat_label("xyz") == "XYZ"
        assert get_stat_label("unknown_stat") == "UNKNOWN_STAT"
        assert get_stat_label("custom_metric") == "CUSTOM_METRIC"

    def test_get_label_empty_string(self):
        """Test empty string returns uppercase empty string."""
        assert get_stat_label("") == ""

    def test_get_label_preserves_case_for_unknown(self):
        """Test unknown stats preserve input casing when uppercased."""
        assert get_stat_label("CustomStat") == "CUSTOMSTAT"
        assert get_stat_label("my_stat") == "MY_STAT"


class TestFormatStatLabels:
    """Test format_stat_labels function."""

    def test_format_list_of_known_stats(self):
        """Test formatting list of known stat abbreviations."""
        stats = ["pts", "reb", "ast"]
        expected = [
            "PTS (Points)",
            "REB (Rebounds)",
            "AST (Assists)"
        ]
        assert format_stat_labels(stats) == expected

    def test_format_list_mixed_known_unknown(self):
        """Test formatting list with mix of known and unknown stats."""
        stats = ["pts", "xyz", "reb", "custom"]
        expected = [
            "PTS (Points)",
            "XYZ",
            "REB (Rebounds)",
            "CUSTOM"
        ]
        assert format_stat_labels(stats) == expected

    def test_format_empty_list(self):
        """Test formatting empty list returns empty list."""
        assert format_stat_labels([]) == []

    def test_format_list_preserves_order(self):
        """Test formatting preserves input order."""
        stats = ["ast", "pts", "reb", "blk", "stl"]
        result = format_stat_labels(stats)
        assert len(result) == 5
        assert result[0] == "AST (Assists)"
        assert result[1] == "PTS (Points)"
        assert result[2] == "REB (Rebounds)"

    def test_format_list_with_duplicates(self):
        """Test formatting list with duplicate stats."""
        stats = ["pts", "pts", "reb"]
        expected = [
            "PTS (Points)",
            "PTS (Points)",
            "REB (Rebounds)"
        ]
        assert format_stat_labels(stats) == expected

    def test_format_list_with_case_variations(self):
        """Test formatting handles case variations consistently."""
        stats = ["pts", "PTS", "Pts"]
        expected = [
            "PTS (Points)",
            "PTS (Points)",
            "PTS (Points)"
        ]
        assert format_stat_labels(stats) == expected


class TestStatLabelsIntegration:
    """Integration tests for stat labels module."""

    def test_all_mapped_stats_have_values(self):
        """Test all mapped stats have non-empty values."""
        for key, value in STAT_LABELS.items():
            assert value, f"Empty value for key: {key}"
            assert len(value) > 0, f"Empty string for key: {key}"

    def test_no_duplicate_values(self):
        """Test intentional duplicates for long-form variations."""
        values = list(STAT_LABELS.values())

        # Known intentional duplicates (short form + long form variations):
        # - "3P% (3-Point Percentage)" has 2 keys: "three_pct" and "3p_pct"
        # - "PTS (Points)" has 2 keys: "pts" and "points"
        # - "REB (Rebounds)" has 2 keys: "reb" and "rebounds"
        # - etc.

        # Count how many duplicates exist
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1

        # Get values that appear more than once
        duplicated = {v: count for v, count in value_counts.items() if count > 1}

        # These are intentional duplicates for user convenience
        expected_duplicates = {
            "3P% (3-Point Percentage)": 2,
            "PTS (Points)": 2,
            "REB (Rebounds)": 2,
            "AST (Assists)": 2,
            "STL (Steals)": 2,
            "BLK (Blocks)": 2,
            "TOV (Turnovers)": 2,
            "PF (Personal Fouls)": 2,
            "GP (Games Played)": 2,
            "MIN (Minutes)": 2,
        }

        # Verify only expected duplicates exist
        assert duplicated == expected_duplicates, f"Unexpected duplicates found: {duplicated}"

    def test_real_world_stat_sequence(self):
        """Test realistic sequence of stats used in queries."""
        stats = ["name", "pts", "reb", "ast", "fg_pct", "three_pct"]
        result = format_stat_labels(stats)

        assert result[0] == "NAME"  # Unknown, uppercased
        assert result[1] == "PTS (Points)"
        assert result[2] == "REB (Rebounds)"
        assert result[3] == "AST (Assists)"
        assert result[4] == "FG% (Field Goal Percentage)"
        assert result[5] == "3P% (3-Point Percentage)"
