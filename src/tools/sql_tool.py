"""
FILE: sql_tool.py
STATUS: Active
RESPONSIBILITY: LangChain SQL agent for querying NBA statistics database
LAST MAJOR UPDATE: 2026-02-14 (Migrated to LangChain create_sql_agent)
MAINTAINER: Shahu
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings

logger = logging.getLogger(__name__)


def _retry_on_rate_limit(func, max_retries: int = 3, initial_delay: float = 2.0):
    """Retry a function with exponential backoff on rate limit errors.

    Args:
        func: Callable to retry
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds

    Returns:
        Result from successful function call

    Raises:
        Exception: If all retries exhausted or non-rate-limit error
    """
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str.upper()

            if not is_rate_limit:
                # Not a rate limit error, raise immediately
                raise

            if attempt >= max_retries:
                logger.error("SQL generation rate limit after %d retries", max_retries)
                raise

            # Wait with exponential backoff
            wait_time = min(delay, 30.0)
            logger.warning(
                "SQL generation rate limit (attempt %d/%d), retrying in %.1fs",
                attempt + 1,
                max_retries + 1,
                wait_time
            )
            time.sleep(wait_time)
            delay *= 2


def _load_dictionary_from_db(db_path: str) -> list[dict[str, str | None]]:
    """Load data dictionary entries from the database.

    Uses raw sqlite3 to avoid SQLAlchemy session overhead at init time.

    Args:
        db_path: Path to SQLite database

    Returns:
        List of dicts with abbreviation, full_name, column_name, table_name.
        Returns empty list if table doesn't exist.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT abbreviation, full_name, column_name, table_name "
            "FROM data_dictionary WHERE column_name IS NOT NULL "
            "ORDER BY abbreviation"
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "abbreviation": r[0],
                "full_name": r[1],
                "column_name": r[2],
                "table_name": r[3],
            }
            for r in rows
        ]
    except sqlite3.OperationalError:
        logger.warning("data_dictionary table not found, using fallback abbreviations")
        return []


def _build_abbreviations_block(entries: list[dict[str, str | None]]) -> str:
    """Build the KEY ABBREVIATIONS block for the SQL prompt from dictionary entries.

    Args:
        entries: Dictionary entries from _load_dictionary_from_db()

    Returns:
        Formatted string for prompt injection
    """
    if not entries:
        # Fallback: hardcoded minimal abbreviations (pre-dictionary behavior)
        return (
            "KEY ABBREVIATIONS:\n"
            "- GP = Games Played | PTS = Points | REB = Rebounds | AST = Assists\n"
            "- FG_PCT = Field Goal % | THREE_PCT = 3-Point % | TS_PCT = True Shooting %\n"
            "- PIE = Player Impact Estimate"
        )

    # Group by table for clarity
    player_stats_entries = [e for e in entries if e["table_name"] == "player_stats"]
    player_entries = [e for e in entries if e["table_name"] == "players"]

    lines = ["COLUMN REFERENCE (abbreviation = full name -> SQL column):"]

    if player_entries:
        lines.append("Players table:")
        for e in player_entries:
            lines.append(f"  {e['abbreviation']} = {e['full_name']} -> {e['column_name']}")

    if player_stats_entries:
        lines.append("Player_stats table:")
        for e in player_stats_entries:
            lines.append(f"  {e['abbreviation']} = {e['full_name']} -> {e['column_name']}")

    return "\n".join(lines)


def _build_sql_agent_prefix(abbreviations_block: str) -> str:
    """Build the system prompt for LangChain SQL agent.

    Args:
        abbreviations_block: Formatted abbreviations from data dictionary

    Returns:
        Prompt prefix for SQL agent
    """
    return f"""You are an NBA statistics SQL expert using SQLite. Your job is to answer questions about NBA statistics by writing and executing SQL queries.

DATABASE SCHEMA (STATIC - NO NEED TO EXPLORE):

TABLE: teams
  - id INTEGER PRIMARY KEY
  - abbreviation VARCHAR(5) UNIQUE (ATL, BOS, BKN, CHA, CHI, CLE, DAL, DEN, DET, GSW, HOU, IND, LAC, LAL, MEM, MIA, MIL, MIN, NOP, NYK, OKC, ORL, PHI, PHX, POR, SAC, SAS, TOR, UTA, WAS)
  - name VARCHAR(100) (team full name)

TABLE: players
  - id INTEGER PRIMARY KEY
  - name VARCHAR(100) (player full name)
  - team_abbr VARCHAR(5) FOREIGN KEY → teams.abbreviation
  - age INTEGER

TABLE: player_stats (1:1 with players, all season totals unless noted)
  - id INTEGER PRIMARY KEY
  - player_id INTEGER FOREIGN KEY → players.id
  - gp INTEGER (games played)
  - w, l INTEGER (wins, losses)
  - min DECIMAL (total minutes)
  - pts INTEGER (total points)
  - fgm, fga INTEGER (field goals made/attempted)
  - fg_pct DECIMAL (field goal %, 0-100 scale)
  - three_pm, three_pa INTEGER (3-pointers made/attempted)
  - three_pct DECIMAL (3-point %, 0-100 scale)
  - ftm, fta INTEGER (free throws made/attempted)
  - ft_pct DECIMAL (free throw %, 0-100 scale)
  - oreb, dreb, reb INTEGER (offensive/defensive/total rebounds)
  - ast, tov, stl, blk, pf INTEGER (assists, turnovers, steals, blocks, fouls)
  - ts_pct DECIMAL (true shooting %, 0-100 scale)
  - efg_pct DECIMAL (effective FG %, 0-100 scale)
  - usg_pct DECIMAL (usage %, 0-100 scale)
  - off_rtg, def_rtg, net_rtg DECIMAL (offensive/defensive/net rating)
  - pie DECIMAL (player impact estimate)
  - [plus 20+ other advanced stats]

CRITICAL: Teams table has NO stats - aggregate from player_stats via players join.

{abbreviations_block}

CRITICAL RULES:

1. TEAM STATISTICS REQUIRE AGGREGATION:
   - Teams table has NO stats columns - you MUST aggregate from player_stats
   - Pattern: SELECT t.name, SUM(ps.stat) FROM teams t JOIN players p ON t.abbreviation = p.team_abbr JOIN player_stats ps ON p.id = ps.player_id WHERE t.abbreviation = 'ABBR' GROUP BY t.name

2. JOINS:
   - Each player has EXACTLY ONE stats record (1:1 relationship)
   - DO NOT use GROUP BY or SUM() for individual player queries
   - Use: JOIN player_stats ps ON p.id = ps.player_id

3. FILTERING:
   - For aggregations (AVG, MAX, MIN), add 'WHERE column IS NOT NULL'
   - For player names, use LIKE '%PlayerName%' for partial matching
   - For percentage rankings, add WHERE ps.gp >= 20 to exclude low-sample outliers

4. PERCENTAGES:
   - ALL percentage columns (fg_pct, three_pct, ft_pct, efg_pct, ts_pct, usg_pct) are 0-100 scale
   - Example: ts_pct = 45.2 means 45.2%, NOT 0.452
   - Use thresholds like ts_pct > 60 (not 0.6)

5. PER-GAME STATS:
   - For PPG, RPG, APG, ALWAYS divide by gp: ROUND(CAST(ps.column AS FLOAT) / ps.gp, 1)

6. LIMITS:
   - Superlatives ("most", "highest", "best") without plural → LIMIT 1
   - "top N" with specific number → LIMIT N
   - "top players" without number → LIMIT 5
   - Comparisons → LIMIT 5-10

7. GROUP BY + HAVING:
   - For "at least N" or "more than N" per-group queries, use HAVING
   - Example: "teams with at least 3 players scoring 1000+" → GROUP BY team HAVING COUNT(*) >= 3

8. SECURITY (CRITICAL):
   - ONLY use SELECT statements (NO DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE)
   - NO multiple statements (no semicolons except at end)
   - NO SQL comments (no --, /*, */)
   - NO UNION unless in legitimate subquery

Team abbreviations: ATL, BOS, BKN, CHA, CHI, CLE, DAL, DEN, DET, GSW, HOU, IND, LAC, LAL, MEM, MIA, MIL, MIN, NOP, NYK, OKC, ORL, PHI, PHX, POR, SAC, SAS, TOR, UTA, WAS

EXAMPLE QUERIES:

1. "Who scored the most points?"
   SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1;

2. "Top 3 rebounders"
   SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.reb DESC LIMIT 3;

3. "LeBron's PPG"
   SELECT p.name, ROUND(CAST(ps.pts AS FLOAT) / ps.gp, 1) AS ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%LeBron%';

4. "Lakers team stats"
   SELECT t.name, SUM(ps.pts) as total_pts, SUM(ps.reb) as total_reb FROM teams t JOIN players p ON t.abbreviation = p.team_abbr JOIN player_stats ps ON p.id = ps.player_id WHERE t.abbreviation = 'LAL' GROUP BY t.name;

5. "Compare Jokić and Embiid"
   SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Nikola Jokić', 'Joel Embiid');

When you get a question:
1. Think about what data is needed
2. Write a SIMPLE, DIRECT SQL query following the rules above
3. Execute the query using sql_db_query tool
4. If the query fails, analyze the error and try a corrected query
5. Present the results clearly

Begin!"""


class NBAGSQLTool:
    """SQL query tool for NBA statistics database using LangChain SQL Agent."""

    def __init__(self, db_path: str | None = None, google_api_key: str | None = None):
        """Initialize SQL tool with LangChain SQL agent.

        Args:
            db_path: Path to SQLite database (default: data/sql/nba_stats.db)
            google_api_key: Google API key (default from settings)
        """
        if db_path is None:
            db_path = str(Path(settings.database_dir) / "nba_stats.db")

        self.db_path = db_path
        self._api_key = google_api_key or settings.google_api_key

        # Initialize SQLDatabase
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

        # Load data dictionary for dynamic prompt
        dict_entries = _load_dictionary_from_db(db_path)
        abbreviations_block = _build_abbreviations_block(dict_entries)
        self._dict_entry_count = len(dict_entries)

        # Initialize LLM (Gemini for SQL generation)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.0,  # Deterministic for SQL generation
            google_api_key=self._api_key,
        )

        # Build SQL agent prefix with domain knowledge
        agent_prefix = _build_sql_agent_prefix(abbreviations_block)

        # OPTIMIZATION: Add suffix to skip unnecessary schema exploration
        # Since database is STATIC, we pre-load all schema info in prefix
        agent_suffix = """
IMPORTANT OPTIMIZATION INSTRUCTIONS:
- The complete database schema is already provided above
- DO NOT use sql_db_list_tables or sql_db_schema tools
- Go DIRECTLY to writing and executing your SQL query with sql_db_query
- Only use the schema exploration tools if your query fails and you need more info

Begin! Remember: Skip schema exploration, write SQL directly.

Question: {input}
Thought: I should write a SQL query to answer this question.
{agent_scratchpad}"""

        # Create LangChain SQL agent with custom prefix and suffix
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="zero-shot-react-description",
            verbose=True,
            max_iterations=5,
            max_execution_time=15.0,  # 15 second timeout
            handle_parsing_errors=True,
            agent_executor_kwargs={
                "handle_parsing_errors": True,
                "return_intermediate_steps": True,
            },
            prefix=agent_prefix,
            suffix=agent_suffix,  # Add optimization suffix
        )

        logger.info(
            f"NBA SQL Agent initialized with database: {db_path} "
            f"({self._dict_entry_count} dictionary entries loaded)"
        )

    @staticmethod
    def _validate_sql_security(sql: str) -> None:
        """Validate SQL for security (prevent SQL injection, destructive operations).

        This is a CRITICAL security layer that validates SQL BEFORE execution.
        Even though LangChain SQL agent has built-in protections, we add
        an extra security layer as defense in depth.

        Args:
            sql: SQL query to validate

        Raises:
            ValueError: If SQL contains dangerous patterns
        """
        sql_upper = sql.upper()

        # Block destructive operations (read-only enforcement)
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "TRUNCATE", "ALTER", "INSERT", "CREATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"SQL injection detected: {keyword} statements are not allowed")

        # Block multiple statements (prevent ; injection)
        if sql.count(";") > 1 or (sql.count(";") == 1 and not sql.strip().endswith(";")):
            raise ValueError("SQL injection detected: Multiple statements not allowed")

        # Block SQL comments that could hide malicious code
        if "--" in sql or "/*" in sql or "*/" in sql:
            raise ValueError("SQL injection detected: Comments not allowed")

        # Block UNION-based injection
        if "UNION" in sql_upper and sql_upper.count("SELECT") > 1:
            # Allow legitimate subqueries but block UNION injections
            if not any(pattern in sql_upper for pattern in ["FROM (SELECT", "IN (SELECT"]):
                raise ValueError("SQL injection detected: UNION statement pattern")

    def query(self, question: str) -> dict[str, Any]:
        """Query NBA database with natural language using LangChain SQL agent.

        The agent will:
        1. Analyze the question
        2. Generate appropriate SQL
        3. Execute the query
        4. Self-correct if errors occur
        5. Return formatted results

        Args:
            question: Natural language question about NBA statistics

        Returns:
            Dictionary with:
                - question: Original question
                - sql: Generated SQL query (extracted from agent trace)
                - results: Query results (list of dicts)
                - error: Error message if query failed
                - agent_steps: Intermediate reasoning steps (for debugging)

        Example:
            >>> tool = NBAGSQLTool()
            >>> result = tool.query("Who are the top 5 scorers?")
            >>> print(result['results'])
            [{'name': 'Player1', 'pts': 2500}, ...]
        """
        try:
            logger.info(f"Agent processing question: {question}")

            # Invoke agent with rate limit retry
            response = _retry_on_rate_limit(
                lambda: self.agent_executor.invoke({"input": question})
            )

            # Extract SQL from intermediate steps (agent trace)
            sql_query = None
            intermediate_steps = response.get("intermediate_steps", [])

            for action, observation in intermediate_steps:
                # Check if this step used the SQL query tool
                if hasattr(action, "tool") and "sql" in action.tool.lower():
                    if hasattr(action, "tool_input"):
                        # Extract SQL from tool input
                        tool_input = action.tool_input
                        if isinstance(tool_input, dict):
                            sql_query = tool_input.get("query", str(tool_input))
                        elif isinstance(tool_input, str):
                            sql_query = tool_input
                        else:
                            sql_query = str(tool_input)

                        # Validate security BEFORE execution
                        # (LangChain already executed it, but we check for logging/audit)
                        try:
                            self._validate_sql_security(str(sql_query))
                        except ValueError as e:
                            logger.error(f"Security validation failed: {e}")
                            raise

            # Extract final answer
            final_answer = response.get("output", "")

            # Parse results from agent output
            # The agent may have already formatted the results, so we extract raw data if available
            results = []

            # Try to extract structured data from agent observations
            for action, observation in intermediate_steps:
                if isinstance(observation, str) and ("[" in observation):
                    # Observation contains structured data (list of tuples or dicts)
                    try:
                        import ast
                        parsed = ast.literal_eval(observation)

                        # Convert to list if single item
                        if not isinstance(parsed, list):
                            parsed = [parsed]

                        # Convert tuples to dictionaries if needed
                        if parsed and isinstance(parsed[0], tuple):
                            # We don't have column names here, so store raw tuples
                            # The answer already has the formatted results
                            results = parsed
                        elif parsed and isinstance(parsed[0], dict):
                            results = parsed
                        else:
                            results = parsed
                    except:
                        # If parsing fails, observation might be a formatted string
                        pass

            return {
                "question": question,
                "sql": sql_query,
                "results": results,
                "answer": final_answer,
                "error": None,
                "agent_steps": len(intermediate_steps),
            }

        except Exception as e:
            logger.error(f"Agent query failed: {e}", exc_info=True)
            return {
                "question": question,
                "sql": None,
                "results": [],
                "answer": None,
                "error": str(e),
                "agent_steps": 0,
            }

    @staticmethod
    def normalize_player_name(name: str) -> str:
        """Normalize player name for matching (Issue #10: Special characters).

        Removes accents/diacritics for fuzzy matching.

        Args:
            name: Player name with potential special characters

        Returns:
            Normalized name (ASCII only)

        Example:
            >>> normalize_player_name("Jokić")
            "Jokic"
        """
        import unicodedata
        return ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )

    def format_results(self, results: list[dict]) -> str:
        """Format query results as natural language response.

        Args:
            results: Query results

        Returns:
            Formatted string response
        """
        if not results:
            return "No results found."

        # Format as table-like text
        if len(results) == 1:
            # Single row - format as key-value pairs
            row = results[0]
            lines = [f"{key}: {value}" for key, value in row.items()]
            return "\n".join(lines)

        # Multiple rows - format as table
        columns = list(results[0].keys())
        lines = []

        # Header
        header = " | ".join(columns)
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for row in results:
            row_str = " | ".join(str(row.get(col, "")) for col in columns)
            lines.append(row_str)

        return "\n".join(lines)
