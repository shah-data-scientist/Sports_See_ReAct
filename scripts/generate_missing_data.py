"""Generate complete ground_truth_data for the 9 HYBRID test cases."""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "sql" / "nba_stats.db"

# Test cases with their SQL queries (from validator output)
TEST_CASES = {
    161: {
        "question": "Who are the most efficient scorers by true shooting percentage?",
        "sql": "SELECT p.name, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.ts_pct DESC LIMIT 5"
    },
    163: {
        "question": "Who has the best assist-to-turnover ratio among high-volume passers?",
        "sql": "SELECT p.name, ps.ast, ps.tov, ROUND(ps.ast*1.0/ps.tov, 2) as ratio FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ast > 300 ORDER BY ratio DESC LIMIT 5"
    },
    165: {
        "question": "Which players have high scoring but low efficiency?",
        "sql": "SELECT p.name, ps.pts, ps.fg_pct, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1500 AND ps.ts_pct < 60 ORDER BY ps.pts DESC LIMIT 5"
    },
    169: {
        "question": "Compare advanced efficiency metrics (PIE, TS%) for MVP candidates",
        "sql": "SELECT p.name, ps.pie, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 2000 AND ps.pie > 15 ORDER BY ps.pie DESC LIMIT 5"
    },
    170: {
        "question": "How do young players (high stats) compare to established stars?",
        "sql": "SELECT p.name, p.age, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1800 ORDER BY p.age ASC LIMIT 5"
    },
    188: {
        "question": "Which current players match the historical playoff dominance?",
        "sql": "SELECT p.name, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 2000 ORDER BY ps.pie DESC LIMIT 5"
    },
    191: {
        "question": "Are there players with modest scoring but exceptional all-around impact?",
        "sql": "SELECT p.name, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts BETWEEN 1500 AND 2500 AND ps.pie > 15 ORDER BY ps.pie DESC LIMIT 5"
    },
    193: {
        "question": "Why do fans on Reddit consider him an MVP favorite?",
        "sql": "SELECT p.name, ps.pie, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name = 'Shai Gilgeous-Alexander'"
    },
    196: {
        "question": "What do fans think about their chances of repeating as champions?",
        "sql": "SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'BOS' ORDER BY ps.pts DESC LIMIT 3"
    }
}


def execute_sql(sql: str):
    """Execute SQL and return results."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 80)
    print("GENERATING COMPLETE ground_truth_data FOR 9 HYBRID TEST CASES")
    print("=" * 80)

    for test_num, test_info in TEST_CASES.items():
        print(f"\n[Test #{test_num}] {test_info['question']}")
        print(f"\nSQL:\n{test_info['sql']}\n")

        result = execute_sql(test_info['sql'])

        # Format as Python code
        if isinstance(result, list) and len(result) == 1:
            print(f"ground_truth_data={json.dumps(result[0], indent=4)}")
        else:
            print(f"ground_truth_data={json.dumps(result, indent=4)}")
        print("-" * 80)
