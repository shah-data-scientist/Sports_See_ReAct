"""
FILE: test_sql_tool.py
STATUS: Active - Updated for current NBAGSQLTool API
RESPONSIBILITY: Unit tests for NBAGSQLTool - SQL query generation and execution via LangChain
LAST MAJOR UPDATE: 2026-02-16 (Rewritten for query() API)
MAINTAINER: Shahu
"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.tools.sql_tool import NBAGSQLTool, SecureSQLDatabase, _build_abbreviations_block, _load_dictionary_from_db


class TestNBAGSQLToolInit:
    """Test NBAGSQLTool initialization."""

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SecureSQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    @patch("src.tools.sql_tool.create_sql_agent")
    def test_init_default_params(self, mock_agent, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with default parameters."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        mock_agent.return_value = MagicMock()

        tool = NBAGSQLTool()

        # Check database path
        expected_path = str(Path("data/sql") / "nba_stats.db")
        assert tool.db_path == expected_path
        mock_db_class.from_uri.assert_called_once()

        # Check LLM initialization
        mock_llm_class.assert_called_once()
        call_kwargs = mock_llm_class.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.0-flash"
        assert call_kwargs["temperature"] == 0.0

        # Check dictionary was loaded
        mock_load_dict.assert_called_once_with(expected_path)

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SecureSQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    @patch("src.tools.sql_tool.create_sql_agent")
    def test_init_custom_db_path(self, mock_agent, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with custom database path."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        mock_agent.return_value = MagicMock()

        custom_path = "/custom/path/test.db"
        tool = NBAGSQLTool(db_path=custom_path)

        assert tool.db_path == custom_path
        mock_db_class.from_uri.assert_called_once()
        mock_load_dict.assert_called_once_with(custom_path)

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SecureSQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    @patch("src.tools.sql_tool.create_sql_agent")
    def test_init_custom_api_key(self, mock_agent, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with custom API key."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        mock_agent.return_value = MagicMock()

        custom_key = "test_api_key_123"
        tool = NBAGSQLTool(google_api_key=custom_key)

        assert tool._api_key == custom_key
        call_kwargs = mock_llm_class.call_args.kwargs
        assert call_kwargs["google_api_key"] == custom_key

    @patch("src.tools.sql_tool._load_dictionary_from_db")
    @patch("src.tools.sql_tool.SecureSQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    @patch("src.tools.sql_tool.create_sql_agent")
    def test_init_with_dictionary_entries(self, mock_agent, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization loads dictionary entries and sets count."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        mock_agent.return_value = MagicMock()

        # Mock dictionary with 2 entries
        mock_dict = [
            {'abbreviation': 'PTS', 'full_name': 'Points', 'column_name': 'pts', 'table_name': 'player_stats'},
            {'abbreviation': 'AST', 'full_name': 'Assists', 'column_name': 'ast', 'table_name': 'player_stats'},
        ]
        mock_load_dict.return_value = mock_dict

        tool = NBAGSQLTool()

        # Tool stores count, not the entries themselves
        assert tool._dict_entry_count == 2

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SecureSQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    @patch("src.tools.sql_tool.create_sql_agent")
    def test_init_creates_agent_executor(self, mock_agent, mock_llm_class, mock_db_class, mock_load_dict):
        """Test that initialization creates agent executor."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_executor = MagicMock()
        mock_agent.return_value = mock_executor

        tool = NBAGSQLTool()

        # Verify create_sql_agent was called with correct params
        mock_agent.assert_called_once()
        call_kwargs = mock_agent.call_args.kwargs
        assert call_kwargs["llm"] == mock_llm
        assert call_kwargs["agent_type"] == "zero-shot-react-description"
        assert call_kwargs["max_iterations"] == 5
        assert tool.agent_executor == mock_executor


class TestQuery:
    """Test the query() method."""

    @pytest.fixture
    def mock_tool(self):
        """Create NBAGSQLTool with mocked agent executor."""
        with patch("src.tools.sql_tool.SecureSQLDatabase") as mock_db_class, \
             patch("src.tools.sql_tool.ChatGoogleGenerativeAI") as mock_llm_class, \
             patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[]), \
             patch("src.tools.sql_tool.create_sql_agent") as mock_create_agent:

            mock_db_class.from_uri.return_value = MagicMock()
            mock_llm_class.return_value = MagicMock()
            mock_agent_executor = MagicMock()
            mock_create_agent.return_value = mock_agent_executor

            tool = NBAGSQLTool()
            yield tool

    def test_query_has_correct_signature(self, mock_tool):
        """Test that query method exists and has correct signature."""
        assert hasattr(mock_tool, 'query')
        assert callable(mock_tool.query)

    def test_query_returns_dict(self, mock_tool):
        """Test that query returns a dictionary."""
        # Mock successful agent execution
        mock_tool.agent_executor.invoke.return_value = {
            "output": "LeBron James scored 2485 points",
            "intermediate_steps": []
        }

        result = mock_tool.query("Who scored the most points?")

        assert isinstance(result, dict)
        assert "answer" in result or "output" in result or "error" in result

    def test_query_calls_agent_executor(self, mock_tool):
        """Test that query() invokes the agent executor."""
        mock_tool.agent_executor.invoke.return_value = {
            "output": "Result",
            "intermediate_steps": []
        }

        mock_tool.query("Test question")

        # Verify agent executor was called
        mock_tool.agent_executor.invoke.assert_called_once()
        call_args = mock_tool.agent_executor.invoke.call_args
        # Check that input contains the question
        assert "input" in call_args[0][0] or "input" in call_args.kwargs


class TestFormatResults:
    """Test result formatting."""

    @pytest.fixture
    def mock_tool(self):
        """Create NBAGSQLTool with mocked dependencies."""
        with patch("src.tools.sql_tool.SecureSQLDatabase") as mock_db_class, \
             patch("src.tools.sql_tool.ChatGoogleGenerativeAI") as mock_llm_class, \
             patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[]), \
             patch("src.tools.sql_tool.create_sql_agent") as mock_create_agent:

            mock_db_class.from_uri.return_value = MagicMock()
            mock_llm_class.return_value = MagicMock()
            mock_create_agent.return_value = MagicMock()

            tool = NBAGSQLTool()
            yield tool

    def test_format_empty_results(self, mock_tool):
        """Test formatting empty results."""
        formatted = mock_tool.format_results([])

        assert formatted == "No results found."

    def test_format_single_row(self, mock_tool):
        """Test formatting single row result."""
        results = [{'name': 'LeBron James', 'pts': 2500, 'team': 'LAL'}]

        formatted = mock_tool.format_results(results)

        assert "name: LeBron James" in formatted
        assert "pts: 2500" in formatted
        assert "team: LAL" in formatted

    def test_format_multiple_rows(self, mock_tool):
        """Test formatting multiple rows as table."""
        results = [
            {'name': 'LeBron James', 'pts': 2500},
            {'name': 'Stephen Curry', 'pts': 2300},
            {'name': 'Kevin Durant', 'pts': 2100}
        ]

        formatted = mock_tool.format_results(results)

        # Should contain all names and points
        assert "LeBron James" in formatted
        assert "2500" in formatted
        assert "Stephen Curry" in formatted
        assert "2300" in formatted
        assert "Kevin Durant" in formatted
        assert "2100" in formatted

    def test_format_with_null_values(self, mock_tool):
        """Test formatting results with null values."""
        results = [
            {'name': 'Test Player', 'team': None, 'pts': 100}
        ]

        formatted = mock_tool.format_results(results)

        assert "Test Player" in formatted
        assert "100" in formatted

    def test_format_with_float_values(self, mock_tool):
        """Test formatting results with float values."""
        results = [
            {'name': 'Player', 'fg_pct': 45.5, 'three_pct': 38.2}
        ]

        formatted = mock_tool.format_results(results)

        assert "Player" in formatted
        assert "45.5" in formatted
        assert "38.2" in formatted


class TestLoadDictionaryFromDB:
    """Test dictionary loading from database."""

    def test_load_dictionary_empty_db(self):
        """Test loading from database without data_dictionary table."""
        with patch("src.tools.sql_tool.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = sqlite3.OperationalError("no such table: data_dictionary")
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            result = _load_dictionary_from_db("test.db")

            assert result == []

    def test_load_dictionary_with_entries(self):
        """Test loading dictionary entries from database."""
        with patch("src.tools.sql_tool.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ('PTS', 'Points', 'pts', 'player_stats'),
                ('AST', 'Assists', 'ast', 'player_stats'),
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            result = _load_dictionary_from_db("test.db")

            assert len(result) == 2
            assert result[0] == {
                'abbreviation': 'PTS',
                'full_name': 'Points',
                'column_name': 'pts',
                'table_name': 'player_stats'
            }


class TestBuildAbbreviationsBlock:
    """Test abbreviations block building."""

    def test_build_empty_dict(self):
        """Test building block with no entries."""
        block = _build_abbreviations_block([])

        assert "KEY ABBREVIATIONS" in block
        assert "GP = Games Played" in block
        assert "PTS = Points" in block

    def test_build_with_player_stats(self):
        """Test building block with player_stats entries."""
        entries = [
            {'abbreviation': 'PTS', 'full_name': 'Points', 'column_name': 'pts', 'table_name': 'player_stats'},
            {'abbreviation': 'AST', 'full_name': 'Assists', 'column_name': 'ast', 'table_name': 'player_stats'},
        ]

        block = _build_abbreviations_block(entries)

        assert "COLUMN REFERENCE" in block
        assert "Player_stats table:" in block
        assert "PTS = Points -> pts" in block
        assert "AST = Assists -> ast" in block

    def test_build_with_players_table(self):
        """Test building block with players table entries."""
        entries = [
            {'abbreviation': 'GP', 'full_name': 'Games Played', 'column_name': 'games', 'table_name': 'players'},
        ]

        block = _build_abbreviations_block(entries)

        assert "Players table:" in block
        assert "GP = Games Played -> games" in block

    def test_build_with_mixed_tables(self):
        """Test building block with entries from multiple tables."""
        entries = [
            {'abbreviation': 'NAME', 'full_name': 'Player Name', 'column_name': 'name', 'table_name': 'players'},
            {'abbreviation': 'PTS', 'full_name': 'Points', 'column_name': 'pts', 'table_name': 'player_stats'},
        ]

        block = _build_abbreviations_block(entries)

        assert "COLUMN REFERENCE" in block
        assert "Players table:" in block
        assert "Player_stats table:" in block
        assert "NAME = Player Name -> name" in block
        assert "PTS = Points -> pts" in block


class TestSQLSecurity:
    """Test SQL security validation."""

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SecureSQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    @patch("src.tools.sql_tool.create_sql_agent")
    def test_validate_sql_security_exists(self, mock_agent, mock_llm, mock_db, mock_dict):
        """Test that security validation method exists."""
        mock_db.from_uri.return_value = MagicMock()
        mock_llm.return_value = MagicMock()
        mock_agent.return_value = MagicMock()

        tool = NBAGSQLTool()

        assert hasattr(NBAGSQLTool, '_validate_sql_security')
        assert callable(NBAGSQLTool._validate_sql_security)

    def test_validate_sql_blocks_drop(self):
        """Test that DROP statements are blocked."""
        with pytest.raises(ValueError, match="DROP"):
            NBAGSQLTool._validate_sql_security("DROP TABLE players")

    def test_validate_sql_blocks_delete(self):
        """Test that DELETE statements are blocked."""
        with pytest.raises(ValueError, match="DELETE"):
            NBAGSQLTool._validate_sql_security("DELETE FROM players WHERE id=1")

    def test_validate_sql_blocks_update(self):
        """Test that UPDATE statements are blocked."""
        with pytest.raises(ValueError, match="UPDATE"):
            NBAGSQLTool._validate_sql_security("UPDATE players SET name='Test'")

    def test_validate_sql_allows_select(self):
        """Test that SELECT statements are allowed."""
        # Should not raise
        NBAGSQLTool._validate_sql_security("SELECT * FROM players LIMIT 10")
