"""
FILE: test_nba_database.py
STATUS: Active
RESPONSIBILITY: Unit tests for SQLAlchemy models and NBADatabase repository
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import tempfile
from pathlib import Path

import pytest

from src.repositories.nba_database import (
    Base,
    DataDictionaryModel,
    NBADatabase,
    PlayerModel,
    PlayerStatsModel,
    TeamModel,
)


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_nba.db")
        db = NBADatabase(db_path=db_path)
        db.create_tables()
        yield db
        db.close()


class TestNBADatabaseInit:
    def test_creates_db_file(self, temp_db):
        assert Path(temp_db.db_path).parent.exists()

    def test_create_and_drop_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db = NBADatabase(db_path=db_path)
            db.create_tables()
            db.drop_tables()
            db.close()


class TestTeamOperations:
    def test_add_and_get_team(self, temp_db):
        session = temp_db.get_session()
        temp_db.add_team(session, "LAL", "Los Angeles Lakers")
        session.commit()

        team = temp_db.get_team_by_abbreviation(session, "LAL")
        assert team is not None
        assert team.name == "Los Angeles Lakers"
        assert team.abbreviation == "LAL"
        session.close()

    def test_get_all_teams(self, temp_db):
        session = temp_db.get_session()
        temp_db.add_team(session, "LAL", "Los Angeles Lakers")
        temp_db.add_team(session, "BOS", "Boston Celtics")
        session.commit()

        teams = temp_db.get_all_teams(session)
        assert len(teams) == 2
        session.close()

    def test_get_nonexistent_team(self, temp_db):
        session = temp_db.get_session()
        team = temp_db.get_team_by_abbreviation(session, "XYZ")
        assert team is None
        session.close()


class TestPlayerOperations:
    def test_add_and_get_player(self, temp_db):
        session = temp_db.get_session()
        temp_db.add_team(session, "LAL", "Los Angeles Lakers")
        session.commit()

        temp_db.add_player(session, "LeBron James", "Los Angeles Lakers", "LAL", 39)
        session.commit()

        player = temp_db.get_player_by_name(session, "LeBron James")
        assert player is not None
        assert player.name == "LeBron James"
        assert player.team_abbr == "LAL"
        assert player.age == 39
        session.close()

    def test_get_all_players(self, temp_db):
        session = temp_db.get_session()
        temp_db.add_team(session, "LAL", "Los Angeles Lakers")
        session.commit()

        temp_db.add_player(session, "Player One", "Los Angeles Lakers", "LAL", 25)
        temp_db.add_player(session, "Player Two", "Los Angeles Lakers", "LAL", 28)
        session.commit()

        players = temp_db.get_all_players(session)
        assert len(players) == 2
        session.close()


class TestCountRecords:
    def test_count_empty_tables(self, temp_db):
        session = temp_db.get_session()
        counts = temp_db.count_records(session)
        assert counts["teams"] == 0
        assert counts["players"] == 0
        assert counts["player_stats"] == 0
        assert counts["data_dictionary"] == 0
        session.close()

    def test_count_after_inserts(self, temp_db):
        session = temp_db.get_session()
        temp_db.add_team(session, "LAL", "Los Angeles Lakers")
        session.commit()

        temp_db.add_player(session, "Test Player", "Los Angeles Lakers", "LAL", 25)
        session.commit()

        counts = temp_db.count_records(session)
        assert counts["teams"] == 1
        assert counts["players"] == 1
        session.close()


class TestModelRepr:
    def test_team_repr(self):
        team = TeamModel(abbreviation="LAL", name="Los Angeles Lakers")
        r = repr(team)
        assert "LAL" in r
        assert "Los Angeles Lakers" in r

    def test_player_repr(self):
        player = PlayerModel(name="LeBron", team="Los Angeles Lakers", team_abbr="LAL", age=39)
        r = repr(player)
        assert "LeBron" in r
        assert "LAL" in r

    def test_player_stats_repr(self):
        stats = PlayerStatsModel(player_id=1, pts=100, gp=50)
        r = repr(stats)
        assert "100" in r

    def test_data_dictionary_repr(self):
        entry = DataDictionaryModel(abbreviation="PTS", column_name="pts")
        r = repr(entry)
        assert "PTS" in r
