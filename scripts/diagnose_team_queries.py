"""
Diagnose why team queries fail.
Check for team name inconsistencies.
"""
import sqlite3
from pathlib import Path

db_path = Path("data/sql/nba_stats.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("TEAM QUERY DIAGNOSIS")
print("="*80)

# 1. Check team name variations in players table
print("\n" + "─"*80)
print("1. TEAM NAME VARIATIONS IN players.team")
print("─"*80)

cursor.execute("""
    SELECT DISTINCT team, team_abbr, COUNT(*) as player_count
    FROM players
    GROUP BY team, team_abbr
    ORDER BY team_abbr
""")
player_teams = cursor.fetchall()

print(f"\nFound {len(player_teams)} distinct team/abbreviation combinations:")
for team, abbr, count in player_teams[:10]:
    print(f"   {abbr:4s} → '{team}' ({count} players)")

# 2. Compare with teams table
print("\n" + "─"*80)
print("2. OFFICIAL TEAM NAMES IN teams TABLE")
print("─"*80)

cursor.execute("SELECT abbreviation, name FROM teams ORDER BY abbreviation")
official_teams = cursor.fetchall()

print(f"\nFound {len(official_teams)} official teams:")
for abbr, name in official_teams[:10]:
    print(f"   {abbr:4s} → '{name}'")

# 3. Check for mismatches
print("\n" + "─"*80)
print("3. MISMATCH DETECTION")
print("─"*80)

mismatches = []
for player_team, player_abbr, _ in player_teams:
    # Find matching official team
    official_name = None
    for abbr, name in official_teams:
        if abbr == player_abbr:
            official_name = name
            break

    if official_name and player_team != official_name:
        mismatches.append((player_abbr, player_team, official_name))

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} MISMATCHES:")
    for abbr, player_name, official_name in mismatches:
        print(f"   {abbr}: '{player_name}' ≠ '{official_name}'")
else:
    print("✅ No mismatches found")

# 4. Test team query patterns that might fail
print("\n" + "─"*80)
print("4. TESTING PROBLEMATIC TEAM QUERIES")
print("─"*80)

test_queries = [
    ("Query by full team name (players.team)", """
        SELECT COUNT(*) FROM players WHERE team = 'Los Angeles Lakers'
    """),
    ("Query by abbreviation (players.team_abbr)", """
        SELECT COUNT(*) FROM players WHERE team_abbr = 'LAL'
    """),
    ("Team stats WITH JOIN", """
        SELECT t.name, SUM(ps.pts) as total_pts
        FROM teams t
        JOIN players p ON t.abbreviation = p.team_abbr
        JOIN player_stats ps ON p.id = ps.player_id
        WHERE t.abbreviation = 'LAL'
        GROUP BY t.name
    """),
    ("Team stats WITHOUT JOIN (using players.team)", """
        SELECT p.team, SUM(ps.pts) as total_pts
        FROM players p
        JOIN player_stats ps ON p.id = ps.player_id
        WHERE p.team LIKE '%Lakers%'
        GROUP BY p.team
    """),
]

for description, query in test_queries:
    print(f"\n{description}:")
    try:
        cursor.execute(query.strip())
        result = cursor.fetchall()
        print(f"   ✅ Success: {result}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

# 5. Show team aggregation example
print("\n" + "─"*80)
print("5. TEAM STATISTICS AGGREGATION")
print("─"*80)

print("\nWithout normalization (using players.team):")
cursor.execute("""
    SELECT p.team, COUNT(p.id) as players, SUM(ps.pts) as total_pts
    FROM players p
    JOIN player_stats ps ON p.id = ps.player_id
    GROUP BY p.team
    ORDER BY total_pts DESC
    LIMIT 5
""")
for team, players, pts in cursor.fetchall():
    print(f"   {team[:30]:30s} → {players} players, {pts:,} pts")

print("\nWith normalization (using teams table):")
cursor.execute("""
    SELECT t.name, COUNT(p.id) as players, SUM(ps.pts) as total_pts
    FROM teams t
    JOIN players p ON t.abbreviation = p.team_abbr
    JOIN player_stats ps ON p.id = ps.player_id
    GROUP BY t.name
    ORDER BY total_pts DESC
    LIMIT 5
""")
for team, players, pts in cursor.fetchall():
    print(f"   {team[:30]:30s} → {players} players, {pts:,} pts")

# 6. Check for orphaned teams
print("\n" + "─"*80)
print("6. ORPHANED TEAMS (teams without players)")
print("─"*80)

cursor.execute("""
    SELECT t.abbreviation, t.name
    FROM teams t
    LEFT JOIN players p ON t.abbreviation = p.team_abbr
    WHERE p.id IS NULL
""")
orphaned = cursor.fetchall()

if orphaned:
    print(f"\n⚠️  Found {len(orphaned)} teams with no players:")
    for abbr, name in orphaned:
        print(f"   {abbr}: {name}")
else:
    print("✅ All teams have players")

conn.close()

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
