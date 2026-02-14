"""
FILE: test_sql_tool.py
STATUS: Active
RESPONSIBILITY: Unit tests for NBAGSQLTool - SQL query generation and execution
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.tools.sql_tool import NBAGSQLTool, _build_abbreviations_block, _load_dictionary_from_db


class TestNBAGSQLToolInit:
    """Test NBAGSQLTool initialization."""

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    def test_init_default_params(self, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with default parameters."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()

        tool = NBAGSQLTool()

        # Check database path
        expected_path = str(Path("data/sql") / "nba_stats.db")
        assert tool.db_path == expected_path
        mock_db_class.from_uri.assert_called_once_with(f"sqlite:///{expected_path}")

        # Check LLM initialization
        mock_llm_class.assert_called_once()
        call_kwargs = mock_llm_class.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.0-flash"
        assert call_kwargs["temperature"] == 0.0

        # Check dictionary was loaded
        mock_load_dict.assert_called_once_with(expected_path)

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    def test_init_custom_db_path(self, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with custom database path."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()

        custom_path = "/custom/path/test.db"
        tool = NBAGSQLTool(db_path=custom_path)

        assert tool.db_path == custom_path
        mock_db_class.from_uri.assert_called_once_with(f"sqlite:///{custom_path}")
        mock_load_dict.assert_called_once_with(custom_path)

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    def test_init_custom_api_key(self, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with custom API key."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()

        custom_key = "test_api_key_123"
        tool = NBAGSQLTool(google_api_key=custom_key)

        assert tool._api_key == custom_key
        call_kwargs = mock_llm_class.call_args.kwargs
        assert call_kwargs["google_api_key"] == custom_key

    @patch("src.tools.sql_tool._load_dictionary_from_db")
    @patch("src.tools.sql_tool.SQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    def test_init_with_dictionary_entries(self, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization loads dictionary entries and sets count."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        mock_load_dict.return_value = [
            {"abbreviation": "PTS", "full_name": "Points", "column_name": "pts", "table_name": "player_stats"},
            {"abbreviation": "AST", "full_name": "Assists", "column_name": "ast", "table_name": "player_stats"},
        ]

        tool = NBAGSQLTool()

        assert tool._dict_entry_count == 2

    @patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[])
    @patch("src.tools.sql_tool.SQLDatabase")
    @patch("src.tools.sql_tool.ChatGoogleGenerativeAI")
    def test_init_no_dictionary_uses_fallback(self, mock_llm_class, mock_db_class, mock_load_dict):
        """Test initialization with empty dictionary uses fallback abbreviations."""
        mock_db_class.from_uri.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()

        tool = NBAGSQLTool()

        assert tool._dict_entry_count == 0


class TestGenerateSQL:
    """Test SQL query generation."""

    @pytest.fixture
    def mock_tool(self):
        """Create NBAGSQLTool with mocked dependencies."""
        with patch("src.tools.sql_tool.SQLDatabase") as mock_db_class, \
             patch("src.tools.sql_tool.ChatGoogleGenerativeAI") as mock_llm_class, \
             patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[]):

            mock_db_class.from_uri.return_value = MagicMock()
            mock_llm_class.return_value = MagicMock()

            tool = NBAGSQLTool()

            # Mock the sql_chain
            tool.sql_chain = MagicMock()

            yield tool

    def test_generate_sql_simple(self, mock_tool):
        """Test simple SQL generation."""
        mock_response = Mock()
        mock_response.content = "SELECT * FROM players WHERE name = 'LeBron James';"
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("Who is LeBron James?")

        assert sql == "SELECT * FROM players WHERE name = 'LeBron James';"
        mock_tool.sql_chain.invoke.assert_called_once_with({"input": "Who is LeBron James?"})

    def test_generate_sql_with_sql_markdown(self, mock_tool):
        """Test SQL generation with ```sql markdown blocks."""
        mock_response = Mock()
        mock_response.content = """Here's the query:
```sql
SELECT p.name, ps.pts FROM players p
JOIN player_stats ps ON p.id = ps.player_id
ORDER BY ps.pts DESC LIMIT 5;
```
This will get the top 5 scorers."""
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("Top 5 scorers?")

        expected = """SELECT p.name, ps.pts FROM players p
JOIN player_stats ps ON p.id = ps.player_id
ORDER BY ps.pts DESC LIMIT 5;"""
        assert sql == expected

    def test_generate_sql_with_plain_markdown(self, mock_tool):
        """Test SQL generation with plain ``` markdown blocks."""
        mock_response = Mock()
        mock_response.content = """```
SELECT COUNT(*) FROM players
```"""
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("How many players?")

        assert sql == "SELECT COUNT(*) FROM players"

    def test_generate_sql_with_extra_text(self, mock_tool):
        """Test SQL generation with extra text before SELECT."""
        mock_response = Mock()
        mock_response.content = "Sure! Here's the query: SELECT name FROM players WHERE age > 30"
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("Players over 30?")

        assert sql == "SELECT name FROM players WHERE age > 30"

    def test_generate_sql_with_insert(self, mock_tool):
        """Test SQL generation recognizes INSERT keyword."""
        mock_response = Mock()
        mock_response.content = "First, let me explain: INSERT INTO players (name) VALUES ('Test');"
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("Add test player")

        assert sql == "INSERT INTO players (name) VALUES ('Test');"

    def test_generate_sql_with_update(self, mock_tool):
        """Test SQL generation recognizes UPDATE keyword."""
        mock_response = Mock()
        mock_response.content = "Explanation: UPDATE players SET age = 35 WHERE name = 'LeBron';"
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("Update LeBron age")

        assert sql == "UPDATE players SET age = 35 WHERE name = 'LeBron';"

    def test_generate_sql_whitespace_handling(self, mock_tool):
        """Test SQL generation handles extra whitespace."""
        mock_response = Mock()
        mock_response.content = "\n\n  SELECT * FROM players  \n\n"
        mock_tool.sql_chain.invoke.return_value = mock_response

        sql = mock_tool.generate_sql("Get all players")

        assert sql == "SELECT * FROM players"


class TestExecuteSQL:
    """Test SQL execution."""

    @pytest.fixture
    def mock_tool(self):
        """Create NBAGSQLTool with mocked dependencies."""
        with patch("src.tools.sql_tool.SQLDatabase") as mock_db_class, \
             patch("src.tools.sql_tool.ChatGoogleGenerativeAI") as mock_llm_class, \
             patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[]):

            mock_db = MagicMock()
            mock_db_class.from_uri.return_value = mock_db
            mock_llm_class.return_value = MagicMock()

            tool = NBAGSQLTool()
            tool.db = mock_db  # Store reference for assertions

            yield tool

    def test_execute_sql_success(self, mock_tool):
        """Test successful SQL execution."""
        mock_tool.db.run.return_value = "[{'name': 'LeBron James', 'pts': 2500}]"

        results = mock_tool.execute_sql("SELECT name, pts FROM players")

        assert results == [{'name': 'LeBron James', 'pts': 2500}]
        mock_tool.db.run.assert_called_once_with(
            "SELECT name, pts FROM players",
            include_columns=True
        )

    def test_execute_sql_multiple_rows(self, mock_tool):
        """Test SQL execution with multiple rows."""
        mock_tool.db.run.return_value = """[
            {'name': 'LeBron James', 'pts': 2500},
            {'name': 'Stephen Curry', 'pts': 2300},
            {'name': 'Kevin Durant', 'pts': 2100}
        ]"""

        results = mock_tool.execute_sql("SELECT name, pts FROM players LIMIT 3")

        assert len(results) == 3
        assert results[0]['name'] == 'LeBron James'
        assert results[1]['name'] == 'Stephen Curry'
        assert results[2]['name'] == 'Kevin Durant'

    def test_execute_sql_empty_result(self, mock_tool):
        """Test SQL execution with no results."""
        mock_tool.db.run.return_value = "[]"

        results = mock_tool.execute_sql("SELECT * FROM players WHERE age > 100")

        assert results == []

    def test_execute_sql_empty_string(self, mock_tool):
        """Test SQL execution returning empty string."""
        mock_tool.db.run.return_value = ""

        results = mock_tool.execute_sql("SELECT COUNT(*) FROM players WHERE 1=0")

        assert results == []

    def test_execute_sql_whitespace_only(self, mock_tool):
        """Test SQL execution returning whitespace."""
        mock_tool.db.run.return_value = "   "

        results = mock_tool.execute_sql("SELECT * FROM nonexistent")

        assert results == []

    def test_execute_sql_single_dict_not_list(self, mock_tool):
        """Test SQL execution returning single dict instead of list."""
        mock_tool.db.run.return_value = "{'count': 569}"

        results = mock_tool.execute_sql("SELECT COUNT(*) as count FROM players")

        # Should wrap single dict in list
        assert results == [{'count': 569}]

    def test_execute_sql_with_nulls(self, mock_tool):
        """Test SQL execution with NULL values."""
        mock_tool.db.run.return_value = "[{'name': 'Test Player', 'age': None}]"

        results = mock_tool.execute_sql("SELECT name, age FROM players")

        assert results == [{'name': 'Test Player', 'age': None}]

    def test_execute_sql_with_floats(self, mock_tool):
        """Test SQL execution with float values."""
        mock_tool.db.run.return_value = "[{'name': 'Stephen Curry', 'three_pct': 42.7}]"

        results = mock_tool.execute_sql("SELECT name, three_pct FROM players")

        assert results == [{'name': 'Stephen Curry', 'three_pct': 42.7}]

    def test_execute_sql_error(self, mock_tool):
        """Test SQL execution error handling."""
        mock_tool.db.run.side_effect = Exception("SQL syntax error")

        with pytest.raises(Exception, match="SQL syntax error"):
            mock_tool.execute_sql("INVALID SQL QUERY")

    def test_execute_sql_malformed_string(self, mock_tool):
        """Test SQL execution with malformed result string."""
        mock_tool.db.run.return_value = "Not valid Python literal"

        with pytest.raises(Exception):
            mock_tool.execute_sql("SELECT * FROM players")


class TestQuery:
    """Test end-to-end query method."""

    @pytest.fixture
    def mock_tool(self):
        """Create NBAGSQLTool with mocked methods."""
        with patch("src.tools.sql_tool.SQLDatabase") as mock_db_class, \
             patch("src.tools.sql_tool.ChatGoogleGenerativeAI") as mock_llm_class, \
             patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[]):

            mock_db_class.from_uri.return_value = MagicMock()
            mock_llm_class.return_value = MagicMock()

            tool = NBAGSQLTool()

            # Mock generate_sql and execute_sql
            tool.generate_sql = MagicMock()
            tool.execute_sql = MagicMock()

            yield tool

    def test_query_success(self, mock_tool):
        """Test successful end-to-end query."""
        mock_tool.generate_sql.return_value = "SELECT name FROM players LIMIT 1"
        mock_tool.execute_sql.return_value = [{'name': 'LeBron James'}]

        result = mock_tool.query("Who is a famous player?")

        assert result['question'] == "Who is a famous player?"
        assert result['sql'] == "SELECT name FROM players LIMIT 1"
        assert result['results'] == [{'name': 'LeBron James'}]
        assert result['error'] is None

    def test_query_empty_results(self, mock_tool):
        """Test query with no results."""
        mock_tool.generate_sql.return_value = "SELECT * FROM players WHERE age > 100"
        mock_tool.execute_sql.return_value = []

        result = mock_tool.query("Players over 100 years old?")

        assert result['question'] == "Players over 100 years old?"
        assert result['sql'] == "SELECT * FROM players WHERE age > 100"
        assert result['results'] == []
        assert result['error'] is None

    def test_query_generation_error(self, mock_tool):
        """Test query with SQL generation error."""
        mock_tool.generate_sql.side_effect = Exception("LLM API error")

        result = mock_tool.query("Who are the top scorers?")

        assert result['question'] == "Who are the top scorers?"
        assert result['sql'] is None
        assert result['results'] == []
        assert "LLM API error" in result['error']

    def test_query_execution_error(self, mock_tool):
        """Test query with SQL execution error."""
        mock_tool.generate_sql.return_value = "INVALID SQL"
        mock_tool.execute_sql.side_effect = Exception("SQL syntax error")

        result = mock_tool.query("Invalid query")

        assert result['question'] == "Invalid query"
        assert result['sql'] is None
        assert result['results'] == []
        assert "SQL syntax error" in result['error']


class TestFormatResults:
    """Test result formatting."""

    @pytest.fixture
    def mock_tool(self):
        """Create NBAGSQLTool with mocked dependencies."""
        with patch("src.tools.sql_tool.SQLDatabase") as mock_db_class, \
             patch("src.tools.sql_tool.ChatGoogleGenerativeAI") as mock_llm_class, \
             patch("src.tools.sql_tool._load_dictionary_from_db", return_value=[]):

            mock_db_class.from_uri.return_value = MagicMock()
            mock_llm_class.return_value = MagicMock()

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
        assert "|" not in formatted  # Should not be table format

    def test_format_multiple_rows(self, mock_tool):
        """Test formatting multiple rows as table."""
        results = [
            {'name': 'LeBron James', 'pts': 2500},
            {'name': 'Stephen Curry', 'pts': 2300},
            {'name': 'Kevin Durant', 'pts': 2100}
        ]

        formatted = mock_tool.format_results(results)

        # Should be table format with pipes
        assert "name | pts" in formatted
        assert "LeBron James | 2500" in formatted
        assert "Stephen Curry | 2300" in formatted
        assert "Kevin Durant | 2100" in formatted
        assert "---" in formatted  # Header separator

    def test_format_with_null_values(self, mock_tool):
        """Test formatting with NULL values."""
        results = [
            {'name': 'Player1', 'age': 30},
            {'name': 'Player2', 'age': None}
        ]

        formatted = mock_tool.format_results(results)

        assert "Player1" in formatted
        assert "Player2" in formatted
        assert "None" in formatted

    def test_format_with_float_values(self, mock_tool):
        """Test formatting with float values."""
        results = [{'name': 'Curry', 'three_pct': 42.7, 'fg_pct': 48.3}]

        formatted = mock_tool.format_results(results)

        assert "42.7" in formatted
        assert "48.3" in formatted

    def test_format_single_column(self, mock_tool):
        """Test formatting with single column."""
        results = [
            {'count': 569}
        ]

        formatted = mock_tool.format_results(results)

        assert "count: 569" in formatted

    def test_format_many_columns(self, mock_tool):
        """Test formatting with many columns."""
        results = [
            {
                'name': 'LeBron James',
                'pts': 2500,
                'reb': 800,
                'ast': 700,
                'fg_pct': 54.2,
                'team': 'LAL'
            },
            {
                'name': 'Stephen Curry',
                'pts': 2300,
                'reb': 400,
                'ast': 600,
                'fg_pct': 48.3,
                'team': 'GSW'
            }
        ]

        formatted = mock_tool.format_results(results)

        # Check header contains all columns
        assert "name" in formatted
        assert "pts" in formatted
        assert "reb" in formatted
        assert "ast" in formatted
        assert "fg_pct" in formatted
        assert "team" in formatted

        # Check both rows present
        assert "LeBron James" in formatted
        assert "Stephen Curry" in formatted


class TestLoadDictionaryFromDB:
    """Test _load_dictionary_from_db function."""

    def test_load_from_existing_table(self, tmp_path):
        """Test loading dictionary from a database with data_dictionary table."""
        import sqlite3

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE data_dictionary ("
            "abbreviation TEXT PRIMARY KEY, full_name TEXT, "
            "description TEXT, column_name TEXT, table_name TEXT)"
        )
        conn.execute(
            "INSERT INTO data_dictionary VALUES ('PTS', 'Points', 'Points scored', 'pts', 'player_stats')"
        )
        conn.execute(
            "INSERT INTO data_dictionary VALUES ('AST', 'Assists', 'Total assists', 'ast', 'player_stats')"
        )
        conn.execute(
            "INSERT INTO data_dictionary VALUES ('Player', 'Player Name', 'Name', 'name', 'players')"
        )
        # Entry with NULL column_name (should be filtered out)
        conn.execute(
            "INSERT INTO data_dictionary VALUES ('HEADER', 'Header Row', 'Not a stat', NULL, NULL)"
        )
        conn.commit()
        conn.close()

        entries = _load_dictionary_from_db(db_path)

        # Should only return entries with column_name IS NOT NULL
        assert len(entries) == 3
        abbrevs = [e["abbreviation"] for e in entries]
        assert "PTS" in abbrevs
        assert "AST" in abbrevs
        assert "Player" in abbrevs
        assert "HEADER" not in abbrevs

    def test_load_returns_correct_fields(self, tmp_path):
        """Test that returned dicts have correct keys and values."""
        import sqlite3

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE data_dictionary ("
            "abbreviation TEXT PRIMARY KEY, full_name TEXT, "
            "description TEXT, column_name TEXT, table_name TEXT)"
        )
        conn.execute(
            "INSERT INTO data_dictionary VALUES ('PTS', 'Points', 'Points scored', 'pts', 'player_stats')"
        )
        conn.commit()
        conn.close()

        entries = _load_dictionary_from_db(db_path)

        assert len(entries) == 1
        entry = entries[0]
        assert entry["abbreviation"] == "PTS"
        assert entry["full_name"] == "Points"
        assert entry["column_name"] == "pts"
        assert entry["table_name"] == "player_stats"

    def test_load_missing_table_returns_empty(self, tmp_path):
        """Test that missing data_dictionary table returns empty list."""
        import sqlite3

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE players (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        entries = _load_dictionary_from_db(db_path)

        assert entries == []

    def test_load_empty_table_returns_empty(self, tmp_path):
        """Test that empty data_dictionary table returns empty list."""
        import sqlite3

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE data_dictionary ("
            "abbreviation TEXT PRIMARY KEY, full_name TEXT, "
            "description TEXT, column_name TEXT, table_name TEXT)"
        )
        conn.commit()
        conn.close()

        entries = _load_dictionary_from_db(db_path)

        assert entries == []

    def test_load_ordered_by_abbreviation(self, tmp_path):
        """Test that results are ordered by abbreviation."""
        import sqlite3

        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE data_dictionary ("
            "abbreviation TEXT PRIMARY KEY, full_name TEXT, "
            "description TEXT, column_name TEXT, table_name TEXT)"
        )
        conn.execute("INSERT INTO data_dictionary VALUES ('REB', 'Rebounds', 'desc', 'reb', 'player_stats')")
        conn.execute("INSERT INTO data_dictionary VALUES ('AST', 'Assists', 'desc', 'ast', 'player_stats')")
        conn.execute("INSERT INTO data_dictionary VALUES ('PTS', 'Points', 'desc', 'pts', 'player_stats')")
        conn.commit()
        conn.close()

        entries = _load_dictionary_from_db(db_path)

        abbrevs = [e["abbreviation"] for e in entries]
        assert abbrevs == ["AST", "PTS", "REB"]


class TestBuildAbbreviationsBlock:
    """Test _build_abbreviations_block function."""

    def test_empty_entries_returns_fallback(self):
        """Test that empty entries returns hardcoded fallback."""
        result = _build_abbreviations_block([])

        assert "KEY ABBREVIATIONS:" in result
        assert "GP = Games Played" in result
        assert "PTS = Points" in result

    def test_player_stats_entries(self):
        """Test formatting player_stats entries."""
        entries = [
            {"abbreviation": "PTS", "full_name": "Points", "column_name": "pts", "table_name": "player_stats"},
            {"abbreviation": "AST", "full_name": "Assists", "column_name": "ast", "table_name": "player_stats"},
        ]

        result = _build_abbreviations_block(entries)

        assert "COLUMN REFERENCE" in result
        assert "Player_stats table:" in result
        assert "PTS = Points -> pts" in result
        assert "AST = Assists -> ast" in result

    def test_players_table_entries(self):
        """Test formatting players table entries."""
        entries = [
            {"abbreviation": "Player", "full_name": "Player Name", "column_name": "name", "table_name": "players"},
        ]

        result = _build_abbreviations_block(entries)

        assert "Players table:" in result
        assert "Player = Player Name -> name" in result

    def test_mixed_tables(self):
        """Test formatting entries from both tables."""
        entries = [
            {"abbreviation": "Player", "full_name": "Player Name", "column_name": "name", "table_name": "players"},
            {"abbreviation": "PTS", "full_name": "Points", "column_name": "pts", "table_name": "player_stats"},
        ]

        result = _build_abbreviations_block(entries)

        assert "Players table:" in result
        assert "Player_stats table:" in result
        assert "Player = Player Name -> name" in result
        assert "PTS = Points -> pts" in result

    def test_no_player_stats_entries(self):
        """Test formatting with only players table entries."""
        entries = [
            {"abbreviation": "Age", "full_name": "Player Age", "column_name": "age", "table_name": "players"},
        ]

        result = _build_abbreviations_block(entries)

        assert "Players table:" in result
        assert "Player_stats table:" not in result
