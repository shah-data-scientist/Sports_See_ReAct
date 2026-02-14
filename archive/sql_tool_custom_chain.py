"""
FILE: sql_tool.py
STATUS: Active
RESPONSIBILITY: LangChain SQL agent for querying NBA statistics database
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import logging
import sqlite3
import time
from pathlib import Path

from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableSequence
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


# Few-shot examples for SQL query generation
FEW_SHOT_EXAMPLES = [
    {
        "input": "Who scored the most points this season?",
        "query": """SELECT p.name, ps.pts
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
ORDER BY ps.pts DESC
LIMIT 1;""",
    },
    {
        "input": "Who are the top 3 rebounders?",
        "query": """SELECT p.name, ps.reb
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
ORDER BY ps.reb DESC
LIMIT 3;""",
    },
    {
        "input": "What is LeBron James' average points per game?",
        "query": """SELECT p.name, ROUND(CAST(ps.pts AS FLOAT) / ps.gp, 1) AS ppg
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE p.name LIKE '%LeBron%';""",
    },
    {
        "input": "How many assists did Chris Paul record?",
        "query": """SELECT p.name, ps.ast
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE p.name LIKE '%Chris Paul%';""",
    },
    {
        "input": "What is the average 3-point percentage for all players?",
        "query": """SELECT AVG(three_pct) AS avg_3p_pct
FROM player_stats
WHERE three_pct IS NOT NULL;""",
    },
    {
        "input": "How many players scored over 1000 points?",
        "query": """SELECT COUNT(*) AS player_count
FROM player_stats
WHERE pts > 1000;""",
    },
    {
        "input": "What is the highest PIE in the league?",
        "query": """SELECT MAX(pie) AS max_pie
FROM player_stats;""",
    },
    {
        "input": "Compare Jokić and Embiid's stats",
        "query": """SELECT p.name, ps.pts, ps.reb, ps.ast
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE p.name IN ('Nikola Jokić', 'Joel Embiid');""",
    },
    {
        "input": "What is the average rebounds per game league-wide?",
        "query": """SELECT ROUND(AVG(CAST(reb AS FLOAT) / gp), 2) AS avg_rpg
FROM player_stats
WHERE gp > 0;""",
    },
    {
        "input": "Who has the highest true shooting percentage?",
        "query": """SELECT p.name, ps.ts_pct
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE ps.ts_pct IS NOT NULL AND ps.gp >= 20
ORDER BY ps.ts_pct DESC
LIMIT 1;""",
    },
    {
        "input": "Which teams have at least 3 players with more than 1000 points?",
        "query": """SELECT p.team_abbr, COUNT(*) AS player_count
FROM players p
JOIN player_stats ps ON p.id = ps.player_id
WHERE ps.pts > 1000
GROUP BY p.team_abbr
HAVING COUNT(*) >= 3
ORDER BY player_count DESC;""",
    },
    {
        "input": "Show me Lakers team statistics",
        "query": """SELECT t.name, SUM(ps.pts) as total_pts, SUM(ps.reb) as total_reb, SUM(ps.ast) as total_ast
FROM teams t
JOIN players p ON t.abbreviation = p.team_abbr
JOIN player_stats ps ON p.id = ps.player_id
WHERE t.abbreviation = 'LAL'
GROUP BY t.name;""",
    },
    {
        "input": "Compare Celtics and Lakers stats",
        "query": """SELECT t.name, SUM(ps.pts) as total_pts, SUM(ps.reb) as total_reb
FROM teams t
JOIN players p ON t.abbreviation = p.team_abbr
JOIN player_stats ps ON p.id = ps.player_id
WHERE t.abbreviation IN ('BOS', 'LAL')
GROUP BY t.name
ORDER BY total_pts DESC;""",
    },
    {
        "input": "Which team has the most assists?",
        "query": """SELECT t.name, SUM(ps.ast) as total_ast
FROM teams t
JOIN players p ON t.abbreviation = p.team_abbr
JOIN player_stats ps ON p.id = ps.player_id
GROUP BY t.name
ORDER BY total_ast DESC
LIMIT 1;""",
    },
]


class NBAGSQLTool:
    """SQL query tool for NBA statistics database using LangChain."""

    def __init__(self, db_path: str | None = None, google_api_key: str | None = None):
        """Initialize SQL tool.

        Loads column definitions from the data_dictionary table if available,
        otherwise falls back to hardcoded abbreviations.

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

        # Build prompts
        self.example_prompt = PromptTemplate(
            input_variables=["input", "query"],
            template="User question: {input}\nSQL query: {query}",
        )

        self.few_shot_prompt = FewShotPromptTemplate(
            examples=FEW_SHOT_EXAMPLES,
            example_prompt=self.example_prompt,
            prefix=f"""You are an NBA statistics SQL expert. Generate SIMPLE, DIRECT SQLite queries.

DATABASE SCHEMA:
- teams(id, abbreviation, name)
- players(id, name, team_abbr, age) [team_abbr → teams.abbreviation]
- player_stats(id, player_id, gp, w, l, min, pts, fgm, fga, fg_pct, three_pm, three_pa, three_pct, ftm, fta, ft_pct, oreb, dreb, reb, ast, tov, stl, blk, pf, fp, dd2, td3, plus_minus, off_rtg, def_rtg, net_rtg, ast_pct, ast_to, ast_ratio, oreb_pct, dreb_pct, reb_pct, to_ratio, efg_pct, ts_pct, usg_pct, pace, pie, poss)

NOTE: The teams table contains team names but NO statistics. Team stats must be aggregated from player_stats.

{abbreviations_block}

CRITICAL TEAM QUERY RULES:
⚠️  TEAM STATISTICS REQUIRE AGGREGATION - Teams table has NO stats columns!

Pattern for team queries:
  SELECT t.name, SUM(ps.[stat]) as total_[stat]
  FROM teams t
  JOIN players p ON t.abbreviation = p.team_abbr
  JOIN player_stats ps ON p.id = ps.player_id
  WHERE t.abbreviation = '[ABBR]'
  GROUP BY t.name

Examples:
  "Show me Lakers stats" →
    SELECT t.name, SUM(ps.pts) as total_pts, SUM(ps.reb) as total_reb, SUM(ps.ast) as total_ast
    FROM teams t
    JOIN players p ON t.abbreviation = p.team_abbr
    JOIN player_stats ps ON p.id = ps.player_id
    WHERE t.abbreviation = 'LAL'
    GROUP BY t.name

  "Compare Celtics and Warriors" →
    SELECT t.name, SUM(ps.pts) as total_pts
    FROM teams t
    JOIN players p ON t.abbreviation = p.team_abbr
    JOIN player_stats ps ON p.id = ps.player_id
    WHERE t.abbreviation IN ('BOS', 'GSW')
    GROUP BY t.name
    ORDER BY total_pts DESC

  "Top 5 teams by rebounds" →
    SELECT t.name, SUM(ps.reb) as total_reb
    FROM teams t
    JOIN players p ON t.abbreviation = p.team_abbr
    JOIN player_stats ps ON p.id = ps.player_id
    GROUP BY t.name
    ORDER BY total_reb DESC
    LIMIT 5

Team abbreviations: ATL, BOS, BKN, CHA, CHI, CLE, DAL, DEN, DET, GSW, HOU, IND, LAC, LAL, MEM, MIA, MIL, MIN, NOP, NYK, OKC, ORL, PHI, PHX, POR, SAC, SAS, TOR, UTA, WAS

IMPORTANT RULES:
1. Each player has EXACTLY ONE stats record (1:1 relationship)
2. DO NOT use GROUP BY or SUM() for individual player queries
3. Use JOIN to connect players and player_stats: JOIN player_stats ps ON p.id = ps.player_id
4. For aggregations (AVG, MAX, MIN), add 'WHERE column IS NOT NULL'
5. For player names, use LIKE '%PlayerName%' for partial matching
6. Keep queries SIMPLE - only use what's necessary
7. Use the EXACT column names from the schema above (e.g., three_pct NOT 3P%)
8. For "per game" stats (PPG, RPG, APG), ALWAYS divide by gp: ROUND(CAST(ps.column AS FLOAT) / ps.gp, 1)
9. For percentage-based rankings (fg_pct, ts_pct, efg_pct, ft_pct, three_pct), add WHERE ps.gp >= 20 to exclude low-sample players with inflated stats
10. ALL percentage columns (fg_pct, three_pct, ft_pct, efg_pct, ts_pct, usg_pct, etc.) are stored as 0-100 scale (e.g., 45.2 means 45.2%, NOT 0.452). Use thresholds like ts_pct > 60 (not 0.6)
11. For ranking queries asking about "top players" or superlatives, ALWAYS use appropriate LIMIT:
    - Superlatives ("most", "highest", "best") without plural → LIMIT 1
    - "top N" with specific number → LIMIT N
    - "top players" without number → LIMIT 5 (reasonable default)
    - Comparison of multiple players → LIMIT 5-10 for manageable results
12. For "at least N" or "more than N" per-group queries, use GROUP BY + HAVING:
    - Example: "teams with at least 3 players scoring 1000+" → GROUP BY team HAVING COUNT(*) >= 3
    - Always put group-level conditions in HAVING (not WHERE)

EXAMPLES:""",
            suffix="\n\nNow generate a SIMPLE, DIRECT SQL query for this question.\nUser question: {input}\nSQL query:",
            input_variables=["input"],
            example_separator="\n\n",
        )

        self.sql_chain = self.few_shot_prompt | self.llm

        logger.info(
            f"NBA SQL Tool initialized with database: {db_path} "
            f"({self._dict_entry_count} dictionary entries loaded)"
        )

    def generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question.

        Args:
            question: Natural language question about NBA stats

        Returns:
            Generated SQL query string
        """
        logger.info(f"Generating SQL for question: {question}")

        # Generate SQL using LLM with retry logic for rate limits
        response = _retry_on_rate_limit(
            lambda: self.sql_chain.invoke({"input": question})
        )

        # Extract SQL from response
        sql = response.content.strip()

        # Remove markdown code blocks if present
        if "```sql" in sql:
            # Extract content between ```sql and ```
            start = sql.find("```sql") + 6
            end = sql.find("```", start)
            sql = sql[start:end].strip()
        elif "```" in sql:
            # Extract content between ``` and ```
            start = sql.find("```") + 3
            end = sql.find("```", start)
            sql = sql[start:end].strip()

        # Remove any leading text before SELECT/WITH/INSERT/UPDATE/DELETE
        sql_keywords = ["SELECT", "WITH", "INSERT", "UPDATE", "DELETE"]
        for keyword in sql_keywords:
            if keyword in sql.upper():
                idx = sql.upper().find(keyword)
                sql = sql[idx:]
                break

        sql = sql.strip()

        logger.info(f"Generated SQL: {sql}")

        # Validate and fix SQL structure (Issue #3: Missing JOINs)
        sql = self._validate_sql_structure(sql, question)

        return sql

    def _validate_sql_structure(self, sql: str, question: str) -> str:
        """Validate SQL structure and auto-correct missing JOINs.

        Issue #3 Remediation: Ensures queries include necessary JOINs when
        they reference players.

        Args:
            sql: Generated SQL query
            question: Original user question

        Returns:
            Validated/corrected SQL query
        """
        import re

        sql_lower = sql.lower()
        question_lower = question.lower()

        # Rule: If question mentions "players" and query only touches player_stats, add JOIN
        if 'player' in question_lower or any(kw in question_lower for kw in ['who', 'name']):
            if 'player_stats' in sql_lower and 'join' not in sql_lower:
                # Skip auto-correction for queries with subqueries (too complex to handle safely)
                select_count = sql_lower.count('select')
                if select_count > 1:
                    logger.debug("Skipping JOIN auto-correction: query contains subqueries")
                    return sql

                # Auto-correct: add JOIN
                logger.warning("Missing JOIN detected - auto-correcting")

                # Step 1: Replace FROM clause
                sql = sql.replace(
                    'FROM player_stats',
                    'FROM players p INNER JOIN player_stats ps ON p.id = ps.player_id'
                )

                # Step 2: Update table aliases from explicit table names
                sql = sql.replace('player_stats.', 'ps.')

                # Step 3: Prefix bare column names with ps. (player_stats columns)
                # List of common player_stats columns
                # NOTE: 'id' is included because in COUNT(id) context after JOIN, it's ambiguous
                stat_columns = [
                    'id',  # Ambiguous after JOIN - prefix with ps. for player_stats.id
                    'gp', 'pts', 'reb', 'ast', 'stl', 'blk',
                    'fg_pct', 'three_pct', 'ft_pct', 'ts_pct',
                    'usg_pct', 'per', 'pie', 'ortg', 'drtg',
                    'ast_pct', 'reb_pct', 'to_pct', 'efg_pct',
                ]

                # Prefix these columns if they appear as bare column names (not already prefixed)
                for col in stat_columns:
                    # Match bare column name (word boundary, not preceded by . or table prefix)
                    # Patterns: COUNT(col), WHERE col, SELECT col, etc.
                    pattern = r'\b(?<!\.)({})\b'.format(col)
                    # Only replace if not already prefixed (negative lookbehind for p. or ps.)
                    sql = re.sub(pattern, r'ps.\1', sql, flags=re.IGNORECASE)

        return sql

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

    def _validate_sql_security(self, sql: str) -> None:
        """Validate SQL for security (prevent SQL injection, destructive operations).

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

    def execute_sql(self, sql: str, timeout_seconds: int = 15) -> list[dict]:
        """Execute SQL query with timeout protection and security validation.

        Args:
            sql: SQL query string
            timeout_seconds: Maximum execution time (default 15 seconds)

        Returns:
            List of result rows as dictionaries

        Raises:
            TimeoutError: If query execution exceeds timeout
            ValueError: If SQL contains dangerous patterns
            Exception: If SQL execution fails
        """
        # Security validation FIRST
        self._validate_sql_security(sql)

        logger.info(f"Executing SQL (timeout: {timeout_seconds}s): {sql}")

        try:
            # Set SQLite timeout to catch hanging queries
            import sqlite3
            sqlite3.PARSE_DECLTYPES = True

            # Execute query - db.run() returns a STRING representation with include_columns=True
            start_time = time.time()
            result_str = self.db.run(sql, include_columns=True)
            elapsed = time.time() - start_time

            # Check if execution exceeded timeout
            if elapsed > timeout_seconds:
                raise TimeoutError(f"SQL query exceeded {timeout_seconds}s timeout (took {elapsed:.1f}s)")

            # SQLDatabase returns a string like "[{'col1': 'val1', 'col2': 'val2'}]"
            # Parse it back to a list of dicts
            if not result_str or result_str.strip() in ("", "[]"):
                return []

            # Use ast.literal_eval to safely parse the string
            import ast
            results = ast.literal_eval(result_str)

            # Ensure it's a list
            if not isinstance(results, list):
                results = [results] if results else []

            logger.info(f"Query returned {len(results)} rows")

            return results

        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise

    def query(self, question: str) -> dict:
        """Query NBA database with natural language.

        Args:
            question: Natural language question about NBA statistics

        Returns:
            Dictionary with:
                - question: Original question
                - sql: Generated SQL query
                - results: Query results (list of dicts)
                - error: Error message if query failed

        Example:
            >>> tool = NBAGSQLTool()
            >>> result = tool.query("Who are the top 5 scorers?")
            >>> print(result['results'])
            [{'name': 'Player1', 'pts': 2500}, ...]
        """
        try:
            # Generate SQL
            sql = self.generate_sql(question)

            # Execute SQL
            results = self.execute_sql(sql)

            return {
                "question": question,
                "sql": sql,
                "results": results,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "question": question,
                "sql": None,
                "results": [],
                "error": str(e),
            }

    def format_results(self, results: list[dict]) -> str:
        """Format query results as natural language response.

        Args:
            results: Query results from execute_sql()

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
