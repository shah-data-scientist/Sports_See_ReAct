"""
FILE: investigate_database.py
STATUS: Active
RESPONSIBILITY: Investigate NBA database structure for duplicate records
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import sqlite3
import sys
from pathlib import Path

# UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    """Investigate database structure."""
    conn = sqlite3.connect("data/sql/nba_stats.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("DATABASE STRUCTURE INVESTIGATION")
    print("=" * 80 + "\n")

    # 1. Check players table
    print("1. PLAYERS TABLE:")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) as count FROM players")
    player_count = cursor.fetchone()["count"]
    print(f"Total players: {player_count}")

    cursor.execute("SELECT COUNT(DISTINCT name) as unique_names FROM players")
    unique_names = cursor.fetchone()["unique_names"]
    print(f"Unique player names: {unique_names}")

    if player_count != unique_names:
        print(f"⚠️  DUPLICATE NAMES: {player_count - unique_names} duplicates found")
        cursor.execute("""
            SELECT name, COUNT(*) as count
            FROM players
            GROUP BY name
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 5
        """)
        print("\nTop 5 duplicated names:")
        for row in cursor.fetchall():
            print(f"  - {row['name']}: {row['count']} records")

    # 2. Check player_stats table
    print("\n2. PLAYER_STATS TABLE:")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) as count FROM player_stats")
    stats_count = cursor.fetchone()["count"]
    print(f"Total player_stats records: {stats_count}")

    cursor.execute("SELECT COUNT(DISTINCT player_id) as unique_players FROM player_stats")
    unique_players = cursor.fetchone()["unique_players"]
    print(f"Unique player_ids: {unique_players}")

    # 3. Check for players with multiple stat records
    print("\n3. MULTI-STATS PLAYERS:")
    print("-" * 80)
    cursor.execute("""
        SELECT player_id, COUNT(*) as stat_count
        FROM player_stats
        GROUP BY player_id
        HAVING COUNT(*) > 1
        ORDER BY stat_count DESC
        LIMIT 5
    """)
    multi_stats = cursor.fetchall()

    if multi_stats:
        print(f"Found {len(multi_stats)} players with multiple stat records:")
        for row in multi_stats:
            cursor.execute("SELECT name FROM players WHERE id = ?", (row["player_id"],))
            player = cursor.fetchone()
            if player:
                print(f"  - {player['name']}: {row['stat_count']} stat records")
    else:
        print("✓ Each player has exactly 1 stat record")

    # 4. Example: LeBron James
    print("\n4. EXAMPLE: LeBron James:")
    print("-" * 80)
    cursor.execute("""
        SELECT p.id, p.name, p.team_abbr, ps.pts, ps.gp, ps.reb, ps.ast
        FROM players p
        LEFT JOIN player_stats ps ON p.id = ps.player_id
        WHERE p.name LIKE '%LeBron%'
        ORDER BY p.id
        LIMIT 10
    """)

    lebron_records = cursor.fetchall()
    print(f"Found {len(lebron_records)} LeBron records:")
    for row in lebron_records:
        pts = row['pts'] if row['pts'] else 'NULL'
        gp = row['gp'] if row['gp'] else 'NULL'
        print(f"  ID: {row['id']:3} | Team: {row['team_abbr']:3} | PTS: {str(pts):4} | GP: {str(gp):2} | Name: {row['name']}")

    # 5. Top scorer analysis
    print("\n5. TOP SCORER QUERY:")
    print("-" * 80)
    print("Current Gemini SQL: SELECT p.name, SUM(ps.pts) ... GROUP BY p.name")
    print("Expected SQL:       SELECT p.name, ps.pts ... ORDER BY ps.pts DESC LIMIT 1\n")

    cursor.execute("""
        SELECT p.name, ps.pts, ps.gp, p.team_abbr
        FROM players p
        JOIN player_stats ps ON p.id = ps.player_id
        ORDER BY ps.pts DESC
        LIMIT 5
    """)

    print("Actual top 5 scorers (correct approach):")
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"  {i}. {row['name']:25} | {row['pts']:4} PTS | {row['gp']:2} GP | {row['team_abbr']}")

    # 6. Check average queries
    print("\n6. AGGREGATION QUERY ISSUE:")
    print("-" * 80)

    # Wrong approach (what Gemini is doing)
    cursor.execute("SELECT AVG(three_pct) as avg FROM player_stats")
    wrong_avg = cursor.fetchone()["avg"]

    # Correct approach (filter NULL values)
    cursor.execute("SELECT AVG(three_pct) as avg FROM player_stats WHERE three_pct IS NOT NULL")
    correct_avg = cursor.fetchone()["avg"]

    print(f"Gemini SQL:     SELECT AVG(three_pct) FROM player_stats")
    print(f"Result:         {wrong_avg:.2f}% (includes NULL values)")
    print(f"\nExpected SQL:   SELECT AVG(three_pct) FROM player_stats WHERE three_pct IS NOT NULL")
    print(f"Result:         {correct_avg:.2f}% (excludes NULL values)")

    # 7. Summary
    print("\n" + "=" * 80)
    print("FINDINGS SUMMARY:")
    print("-" * 80)
    print(f"1. Database has {player_count} player records, {unique_names} unique names")
    print(f"2. Database has {stats_count} player_stats records for {unique_players} unique players")

    if player_count > unique_players:
        print(f"3. ⚠️  {player_count - unique_players} duplicate player entries exist")
        print("4. Recommendation: Queries should NOT use GROUP BY or SUM unless specifically needed")
    else:
        print("3. ✓ Each player appears once in the database")

    print(f"\n5. AGGREGATION ISSUE: Gemini generates queries that include NULL values")
    print("   Fix: Add 'WHERE column IS NOT NULL' for all AVG/MIN/MAX queries")

    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
