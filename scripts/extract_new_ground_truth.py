"""
FILE: extract_new_ground_truth.py
STATUS: Active
RESPONSIBILITY: Extract ground truth data from NBA database for additional 21 SQL test cases
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import sqlite3
import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('data/sql/nba_stats.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('='*80)
print('EXTRACTING GROUND TRUTH FOR 21 ADDITIONAL TEST CASES')
print('='*80 + '\n')

print('SIMPLE SQL - 7 NEW CASES:')
print('-'*80)

# 8. Top assist leader
cursor.execute('SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.ast DESC LIMIT 1')
r = cursor.fetchone()
print(f'8. Top assist leader: {r["name"]} - {r["ast"]} AST')

# 9. Giannis total points
cursor.execute('SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE "%Giannis%"')
r = cursor.fetchone()
print(f'9. Giannis total points: {r["name"]} - {r["pts"]} PTS')

# 10. Nikola Jokic rebounds
cursor.execute('SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE "%Jokić%"')
r = cursor.fetchone()
print(f'10. Jokić rebounds: {r["name"]} - {r["reb"]} REB')

# 11. Best free throw percentage
cursor.execute('SELECT p.name, ps.ft_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ft_pct IS NOT NULL ORDER BY ps.ft_pct DESC LIMIT 1')
r = cursor.fetchone()
print(f'11. Best FT%: {r["name"]} - {r["ft_pct"]}%')

# 12. Top 5 in steals
cursor.execute('SELECT p.name, ps.stl FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.stl DESC LIMIT 5')
results = cursor.fetchall()
print('12. Top 5 steals:')
for i, row in enumerate(results, 1):
    print(f'    {i}. {row["name"]} - {row["stl"]} STL')

# 13. Anthony Edwards games played
cursor.execute('SELECT p.name, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE "%Anthony Edwards%"')
r = cursor.fetchone()
print(f'13. Edwards GP: {r["name"]} - {r["gp"]} GP')

# 14. Highest true shooting percentage
cursor.execute('SELECT p.name, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ts_pct IS NOT NULL AND ps.gp > 20 ORDER BY ps.ts_pct DESC LIMIT 1')
r = cursor.fetchone()
print(f'14. Highest TS%: {r["name"]} - {r["ts_pct"]}%')

print('\nCOMPARISON SQL - 7 NEW CASES:')
print('-'*80)

# 15. Shai vs Edwards scoring
cursor.execute('SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ("Shai Gilgeous-Alexander", "Anthony Edwards") ORDER BY ps.pts DESC')
results = cursor.fetchall()
print('15. Shai vs Edwards PTS:')
for row in results:
    print(f'    {row["name"]}: {row["pts"]} PTS')

# 16. Jokić vs Sabonis rebounding
cursor.execute('SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ("Nikola Jokić", "Domantas Sabonis") ORDER BY ps.reb DESC')
results = cursor.fetchall()
print('16. Jokić vs Sabonis REB:')
for row in results:
    print(f'    {row["name"]}: {row["reb"]} REB')

# 17. Compare Tatum vs Durant
cursor.execute('SELECT p.name, ps.pts, ps.fg_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ("Jayson Tatum", "Kevin Durant") ORDER BY ps.pts DESC')
results = cursor.fetchall()
print('17. Tatum vs Durant:')
for row in results:
    print(f'    {row["name"]}: {row["pts"]} PTS, {row["fg_pct"]}% FG')

# 18. Harden vs Paul assists
cursor.execute('SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE "%Harden%" OR p.name LIKE "%Chris Paul%" ORDER BY ps.ast DESC LIMIT 2')
results = cursor.fetchall()
print('18. Harden vs Paul AST:')
for row in results:
    print(f'    {row["name"]}: {row["ast"]} AST')

# 19. Compare steals: Top 2
cursor.execute('SELECT p.name, ps.stl FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.stl DESC LIMIT 2')
results = cursor.fetchall()
print('19. Top 2 steals leaders:')
for row in results:
    print(f'    {row["name"]}: {row["stl"]} STL')

# 20. Efficiency: Top 2 TS%
cursor.execute('SELECT p.name, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 20 ORDER BY ps.ts_pct DESC LIMIT 2')
results = cursor.fetchall()
print('20. Top 2 TS%:')
for row in results:
    print(f'    {row["name"]}: {row["ts_pct"]}%')

# 21. Blocks leaders: Top 2
cursor.execute('SELECT p.name, ps.blk FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.blk DESC LIMIT 2')
results = cursor.fetchall()
print('21. Top 2 blocks:')
for row in results:
    print(f'    {row["name"]}: {row["blk"]} BLK')

print('\nAGGREGATION SQL - 7 NEW CASES:')
print('-'*80)

# 22. Average rebounds per game
cursor.execute('SELECT AVG(CAST(reb AS REAL) / gp) as avg_rpg FROM player_stats WHERE gp > 0')
r = cursor.fetchone()
print(f'22. Average RPG: {r["avg_rpg"]:.2f}')

# 23. Players with >500 assists
cursor.execute('SELECT COUNT(*) as count FROM player_stats WHERE ast > 500')
r = cursor.fetchone()
print(f'23. Players >500 AST: {r["count"]}')

# 24. Average free throw percentage
cursor.execute('SELECT AVG(ft_pct) as avg FROM player_stats WHERE ft_pct IS NOT NULL')
r = cursor.fetchone()
print(f'24. Average FT%: {r["avg"]:.1f}%')

# 25. Players >50 games played
cursor.execute('SELECT COUNT(*) as count FROM player_stats WHERE gp > 50')
r = cursor.fetchone()
print(f'25. Players >50 GP: {r["count"]}')

# 26. Minimum points scored
cursor.execute('SELECT MIN(pts) as min_pts FROM player_stats WHERE pts > 0')
r = cursor.fetchone()
print(f'26. Minimum PTS (non-zero): {r["min_pts"]}')

# 27. Players with >100 blocks
cursor.execute('SELECT COUNT(*) as count FROM player_stats WHERE blk > 100')
r = cursor.fetchone()
print(f'27. Players >100 BLK: {r["count"]}')

# 28. Average PIE
cursor.execute('SELECT AVG(pie) as avg_pie FROM player_stats WHERE pie IS NOT NULL')
r = cursor.fetchone()
print(f'28. Average PIE: {r["avg_pie"]:.1f}')

print('\n' + '='*80)
conn.close()
