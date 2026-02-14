"""
FILE: extract_ground_truth.py
STATUS: Active
RESPONSIBILITY: Extract ground truth data from NBA database for original 21 SQL test cases
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import sqlite3
import sys
from pathlib import Path

# UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect("data/sql/nba_stats.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("="*80)
print("EXTRACTING GROUND TRUTH FROM DATABASE")
print("="*80 + "\n")

# SIMPLE SQL (7 cases)
print("SIMPLE SQL CASES:")
print("-"*80)

# 1. Top scorer
cursor.execute("SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1")
r = cursor.fetchone()
print(f"1. Top scorer: {r['name']} - {r['pts']} PTS")

# 2. LeBron PPG
cursor.execute("SELECT p.name, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%LeBron%'")
r = cursor.fetchone()
print(f"2. LeBron PPG: {r['name']} - {r['ppg']} PPG")

# 3. Chris Paul assists
cursor.execute("SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Chris Paul%'")
r = cursor.fetchone()
print(f"3. Chris Paul AST: {r['name']} - {r['ast']} AST")

# 4. Curry 3P%
cursor.execute("SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Curry%'")
r = cursor.fetchone()
print(f"4. Curry 3P%: {r['name']} - {r['three_pct']}%")

# 5. Top 3 rebounders
cursor.execute("SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.reb DESC LIMIT 3")
results = cursor.fetchall()
print("5. Top 3 rebounders:")
for i, row in enumerate(results, 1):
    print(f"   {i}. {row['name']} - {row['reb']} REB")

# 6. Lillard GP
cursor.execute("SELECT p.name, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Lillard%'")
r = cursor.fetchone()
print(f"6. Lillard GP: {r['name']} - {r['gp']} GP")

# 7. Durant FG%
cursor.execute("SELECT p.name, ps.fg_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Durant%'")
r = cursor.fetchone()
print(f"7. Durant FG%: {r['name']} - {r['fg_pct']}%\n")

# COMPARISON SQL (7 cases)
print("COMPARISON SQL CASES:")
print("-"*80)

# 8. Jokić vs Embiid
cursor.execute("SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Nikola Jokić', 'Joel Embiid') ORDER BY ps.pts DESC")
results = cursor.fetchall()
print("8. Jokić vs Embiid:")
for row in results:
    print(f"   {row['name']}: {row['pts']} PTS, {row['reb']} REB, {row['ast']} AST")

# 9. Giannis vs AD rebounds
cursor.execute("SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Giannis Antetokounmpo', 'Anthony Davis') ORDER BY ps.reb DESC")
results = cursor.fetchall()
print("9. Giannis vs AD rebounds:")
for row in results:
    print(f"   {row['name']}: {row['reb']} REB")

# 10. LeBron vs Durant scoring
cursor.execute("SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('LeBron James', 'Kevin Durant') ORDER BY ps.pts DESC")
results = cursor.fetchall()
print("10. LeBron vs Durant scoring:")
for row in results:
    print(f"   {row['name']}: {row['pts']} PTS")

# 11. Curry vs Lillard 3P%
cursor.execute("SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Stephen Curry', 'Damian Lillard') ORDER BY ps.three_pct DESC")
results = cursor.fetchall()
print("11. Curry vs Lillard 3P%:")
for row in results:
    print(f"   {row['name']}: {row['three_pct']}%")

# 12. Trae vs Luka assists
cursor.execute("SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Trae Young', 'Luka Dončić') ORDER BY ps.ast DESC")
results = cursor.fetchall()
print("12. Trae vs Luka assists:")
for row in results:
    print(f"   {row['name']}: {row['ast']} AST")

# 13. Jokić vs Embiid efficiency (PIE)
cursor.execute("SELECT p.name, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Nikola Jokić', 'Joel Embiid') ORDER BY ps.pie DESC")
results = cursor.fetchall()
print("13. Jokić vs Embiid PIE:")
for row in results:
    print(f"   {row['name']}: {row['pie']}")

# 14. Giannis vs Jaren blocks
cursor.execute("SELECT p.name, ps.blk FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Giannis Antetokounmpo', 'Jaren Jackson Jr.') ORDER BY ps.blk DESC")
results = cursor.fetchall()
print("14. Giannis vs Jaren blocks:")
for row in results:
    print(f"   {row['name']}: {row['blk']} BLK\n")

# AGGREGATION SQL (7 cases)
print("AGGREGATION SQL CASES:")
print("-"*80)

# 15. Average 3P%
cursor.execute("SELECT AVG(three_pct) as avg FROM player_stats WHERE three_pct IS NOT NULL")
r = cursor.fetchone()
print(f"15. Average 3P%: {r['avg']:.1f}%")

# 16. Players >1000 PTS
cursor.execute("SELECT COUNT(*) as count FROM player_stats WHERE pts > 1000")
r = cursor.fetchone()
print(f"16. Players >1000 PTS: {r['count']}")

# 17. Average FG%
cursor.execute("SELECT AVG(fg_pct) as avg FROM player_stats WHERE fg_pct IS NOT NULL")
r = cursor.fetchone()
print(f"17. Average FG%: {r['avg']:.1f}%")

# 18. Players >20 PPG
cursor.execute("SELECT COUNT(*) as count FROM player_stats WHERE pts*1.0/gp > 20")
r = cursor.fetchone()
print(f"18. Players >20 PPG: {r['count']}")

# 19. Highest PIE
cursor.execute("SELECT MAX(pie) as max FROM player_stats")
r = cursor.fetchone()
print(f"19. Highest PIE: {r['max']}")

# 20. Players TS% >60%
cursor.execute("SELECT COUNT(*) as count FROM player_stats WHERE ts_pct > 60")
r = cursor.fetchone()
print(f"20. Players TS% >60%: {r['count']}")

# 21. Average APG
cursor.execute("SELECT AVG(ast*1.0/gp) as avg FROM player_stats WHERE gp > 0")
r = cursor.fetchone()
print(f"21. Average APG: {r['avg']:.2f}")

print("\n" + "="*80)
conn.close()
