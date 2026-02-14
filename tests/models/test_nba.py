"""
FILE: test_nba.py
STATUS: Active
RESPONSIBILITY: Tests for NBA models (Player, PlayerStats, Team) - validators, creation, edge cases
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import logging
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models.nba import Player, PlayerStats, Team


def _make_stats(**overrides):
    """Helper to build a valid PlayerStats dict with defaults."""
    defaults = {
        "Player": "Test Player",
        "Team": "LAL",
        "Age": 25,
        "GP": 50,
        "W": 30,
        "L": 20,
        "Min": "30.5",
        "PTS": 1000,
        "FGM": 400,
        "FGA": 800,
        "FG%": "50.0",
        "3PM": 100,
        "3PA": 250,
        "3P%": "40.0",
        "FTM": 100,
        "FTA": 120,
        "FT%": "83.3",
        "OREB": 50,
        "DREB": 200,
        "REB": 250,
        "AST": 300,
        "TOV": 100,
        "STL": 50,
        "BLK": 30,
        "PF": 100,
        "FP": "1500.0",
        "DD2": 10,
        "TD3": 2,
        "+/-": "5.5",
        "OFFRTG": "110.0",
        "DEFRTG": "105.0",
        "NETRTG": "5.0",
        "AST%": "20.0",
        "AST/TO": "3.0",
        "AST RATIO": "15.0",
        "OREB%": "5.0",
        "DREB%": "20.0",
        "REB%": "12.0",
        "TO RATIO": "10.0",
        "EFG%": "55.0",
        "TS%": "60.0",
        "USG%": "25.0",
        "PACE": "100.0",
        "PIE": "0.150",
        "POSS": 3000,
    }
    defaults.update(overrides)
    return defaults


class TestTeamValidation:
    """Tests for Team model field constraints."""

    def test_abbreviation_min_length(self):
        """Team abbreviation must be at least 2 characters."""
        with pytest.raises(ValidationError):
            Team(abbreviation="L", name="Lakers")

    def test_abbreviation_max_length(self):
        """Team abbreviation must be at most 5 characters."""
        with pytest.raises(ValidationError):
            Team(abbreviation="TOOLONG", name="Some Team")

    def test_name_min_length(self):
        """Team name must be at least 2 characters."""
        with pytest.raises(ValidationError):
            Team(abbreviation="LAL", name="L")

    def test_valid_team_boundaries(self):
        """Team with abbreviation length 2 and name length 2 is valid."""
        team = Team(abbreviation="LA", name="LA")
        assert team.abbreviation == "LA"


class TestPlayerValidation:
    """Tests for Player model field constraints."""

    def test_age_below_minimum(self):
        """Player age below 18 is rejected."""
        with pytest.raises(ValidationError):
            Player(name="Young Kid", team="LAL", age=17)

    def test_age_above_maximum(self):
        """Player age above 50 is rejected."""
        with pytest.raises(ValidationError):
            Player(name="Old Vet", team="LAL", age=51)

    def test_valid_boundary_ages(self):
        """Player age 18 and 50 are both valid boundaries."""
        p18 = Player(name="Rookie", team="OKC", age=18)
        p50 = Player(name="Legend", team="BOS", age=50)
        assert p18.age == 18
        assert p50.age == 50


class TestPercentageValidators:
    """Tests for validate_percentages and convert_to_decimal validators."""

    def test_percentage_string_stripped(self):
        """Percentage string with % symbol is converted to Decimal."""
        stats = PlayerStats(**_make_stats(**{"FG%": "52.3%"}))
        assert stats.fg_pct == Decimal("52.3")

    def test_none_percentage_stays_none(self):
        """None percentage value remains None."""
        stats = PlayerStats(**_make_stats(**{"FG%": None}))
        assert stats.fg_pct is None

    def test_nan_percentage_becomes_none(self):
        """NaN float is converted to None for percentages."""
        stats = PlayerStats(**_make_stats(**{"FG%": float("nan")}))
        assert stats.fg_pct is None

    def test_convert_to_decimal_empty_string(self):
        """Empty string decimal field becomes Decimal('0')."""
        stats = PlayerStats(**_make_stats(**{"Min": ""}))
        assert stats.min == Decimal("0")


class TestFixThreePm:
    """Tests for fix_three_pm validator handling edge cases."""

    def test_time_format_string(self):
        """Time format '15:00:00' extracts hour as integer."""
        stats = PlayerStats(**_make_stats(**{"3PM": "15:00:00"}))
        assert stats.three_pm == 15

    def test_timestamp_with_hour(self):
        """Object with .hour attribute extracts hour value."""
        class FakeTs:
            hour = 7
        stats = PlayerStats(**_make_stats(**{"3PM": FakeTs()}))
        assert stats.three_pm == 7

    def test_nan_becomes_zero(self):
        """NaN value for 3PM becomes 0."""
        stats = PlayerStats(**_make_stats(**{"3PM": float("nan")}))
        assert stats.three_pm == 0

    def test_normal_integer_passthrough(self):
        """Normal integer passes through unchanged."""
        stats = PlayerStats(**_make_stats(**{"3PM": 42}))
        assert stats.three_pm == 42


class TestCrossFieldValidators:
    """Tests for model-level cross-field consistency validators."""

    def test_games_consistency_warning(self, caplog):
        """GP != W + L logs a warning but does not raise."""
        with caplog.at_level(logging.WARNING):
            stats = PlayerStats(**_make_stats(GP=50, W=30, L=10))
        assert stats.gp == 50
        assert "Games inconsistency" in caplog.text

    def test_rebound_consistency_warning(self, caplog):
        """REB != OREB + DREB (difference > 1) logs a warning."""
        with caplog.at_level(logging.WARNING):
            stats = PlayerStats(**_make_stats(OREB=50, DREB=200, REB=300))
        assert "Rebound inconsistency" in caplog.text

    def test_shooting_consistency_warning(self, caplog):
        """FGM > FGA logs a shooting inconsistency warning."""
        with caplog.at_level(logging.WARNING):
            stats = PlayerStats(**_make_stats(FGM=900, FGA=800))
        assert "Shooting inconsistency" in caplog.text


# ═══════════════════════════════════════════════════════════════
# Model creation and basic field tests (merged from test_nba_models.py)
# ═══════════════════════════════════════════════════════════════


class TestPlayerStatsCreation:
    """Tests for basic PlayerStats model creation and field mapping."""

    def test_valid_player_stats(self):
        """Test creating a PlayerStats with all valid fields."""
        stats = PlayerStats(**_make_stats())
        assert stats.player == "Test Player"
        assert stats.team == "LAL"
        assert stats.age == 25
        assert stats.pts == 1000

    def test_empty_string_percentage_becomes_none(self):
        """Empty string percentage becomes None."""
        stats = PlayerStats(**_make_stats(**{"3P%": ""}))
        assert stats.three_pct is None

    def test_age_validation_too_young(self):
        """PlayerStats rejects age below minimum."""
        with pytest.raises(Exception):
            PlayerStats(**_make_stats(Age=10))

    def test_age_validation_too_old(self):
        """PlayerStats rejects age above maximum."""
        with pytest.raises(Exception):
            PlayerStats(**_make_stats(Age=55))


class TestTeamCreation:
    """Tests for basic Team model creation."""

    def test_valid_team_creation(self):
        """Test creating a valid Team."""
        team = Team(abbreviation="LAL", name="Los Angeles Lakers")
        assert team.abbreviation == "LAL"
        assert team.name == "Los Angeles Lakers"

    def test_whitespace_stripped(self):
        """Whitespace is stripped from Team fields."""
        team = Team(abbreviation="  LAL  ", name="  Los Angeles Lakers  ")
        assert team.abbreviation == "LAL"
        assert team.name == "Los Angeles Lakers"


class TestPlayerCreation:
    """Tests for basic Player model creation."""

    def test_valid_player(self):
        """Test creating a valid Player."""
        player = Player(name="LeBron James", team="LAL", age=39)
        assert player.name == "LeBron James"
        assert player.team == "LAL"
        assert player.age == 39
