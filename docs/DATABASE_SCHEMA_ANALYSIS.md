# NBA Stats Database Schema Analysis

**Date**: 2026-02-13
**Database**: data/sql/nba_stats.db

---

## Current Schema

### 1. **teams** Table
```sql
CREATE TABLE teams (
    id INTEGER NOT NULL PRIMARY KEY,
    abbreviation VARCHAR(5) NOT NULL,
    name VARCHAR(100) NOT NULL
)
```
**Sample Data:**
- id=1, abbreviation="ATL", name="Atlanta Hawks"
- id=2, abbreviation="BOS", name="Boston Celtics"
- id=3, abbreviation="BKN", name="Brooklyn Nets"

**Issue:** ⚠️ `abbreviation` has **NO UNIQUE constraint** but is referenced by foreign keys

---

### 2. **players** Table
```sql
CREATE TABLE players (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team VARCHAR(100) NOT NULL,           -- ⚠️ REDUNDANT (can derive from teams table)
    team_abbr VARCHAR(5) NOT NULL,        -- ✅ Foreign key to teams.abbreviation
    age INTEGER NOT NULL,
    FOREIGN KEY(team_abbr) REFERENCES teams (abbreviation)
)
```
**Sample Data:**
- id=1, name="Shai Gilgeous-Alexander", team="Oklahoma City Thunder", team_abbr="OKC", age=26
- id=2, name="Anthony Edwards", team="Minnesota Timberwolves", team_abbr="MIN", age=23

**Issues:**
- ⚠️ `team` column is redundant (duplicates `teams.name`)
- ⚠️ Foreign key references `teams.abbreviation` which lacks UNIQUE constraint

---

### 3. **player_stats** Table
```sql
CREATE TABLE player_stats (
    id INTEGER NOT NULL PRIMARY KEY,
    player_id INTEGER NOT NULL,           -- ✅ Foreign key to players.id
    team_abbr VARCHAR(5) NOT NULL,        -- ⚠️ REDUNDANT (can derive from players.team_abbr)
    gp INTEGER NOT NULL,
    pts INTEGER NOT NULL,
    ... [42 more stat columns] ...
    FOREIGN KEY(player_id) REFERENCES players (id),
    FOREIGN KEY(team_abbr) REFERENCES teams (abbreviation)
)
```
**Sample Data:**
- id=1, player_id=1, team_abbr="OKC", pts=2485, ...
- id=2, player_id=2, team_abbr="MIN", pts=2180, ...

**Issues:**
- ⚠️ `team_abbr` is redundant (can derive via `players.team_abbr`)
- ⚠️ Foreign key references `teams.abbreviation` which lacks UNIQUE constraint

---

### 4. **data_dictionary** Table
```sql
CREATE TABLE data_dictionary (
    abbreviation VARCHAR(20) NOT NULL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    column_name VARCHAR(50),
    table_name VARCHAR(50)
)
```
Contains metadata/descriptions for columns.

---

## Current Foreign Key Relationships

```
player_stats.player_id  →  players.id ✅
player_stats.team_abbr  →  teams.abbreviation ⚠️ (no UNIQUE constraint)
players.team_abbr       →  teams.abbreviation ⚠️ (no UNIQUE constraint)
```

---

## Problems Identified

### 1. **Missing UNIQUE Constraint on teams.abbreviation**
**Problem:** Foreign keys reference `teams.abbreviation`, but it has no UNIQUE constraint.
**Impact:** SQLite allows this, but it's technically invalid. Foreign keys should reference PRIMARY KEY or UNIQUE columns.
**Fix:** Add UNIQUE constraint to `teams.abbreviation`

### 2. **Data Redundancy**
**Problem:** Team information is duplicated across tables:
- `players.team` duplicates `teams.name`
- `player_stats.team_abbr` duplicates `players.team_abbr`

**Impact:**
- Wastes storage
- Risk of data inconsistency (if team name changes)
- Violates database normalization (3NF)

**Fix:** Remove redundant columns OR keep them for query performance (denormalization)

### 3. **Inconsistent Team Name Storage**
**Problem:** `players.team` stores full team name, but this can differ from `teams.name`
Example:
- `players.team`: "Oklahoma City Thunder"
- `teams.name`: Could be "OKC Thunder" or "Thunder"

**Impact:** Makes it hard to join reliably on team name

---

## Recommended Fixes

### Option 1: Strict Normalization (Recommended for Data Integrity)

**Changes:**
1. Add UNIQUE constraint to `teams.abbreviation`
2. Remove `players.team` column (derive from join)
3. Remove `player_stats.team_abbr` column (derive from join)

**Result:** Clean schema, no redundancy, enforced referential integrity

```sql
-- 1. Add UNIQUE constraint to teams.abbreviation
CREATE UNIQUE INDEX idx_teams_abbreviation ON teams(abbreviation);

-- 2. Drop redundant column from players
ALTER TABLE players DROP COLUMN team;

-- 3. Drop redundant column from player_stats
ALTER TABLE player_stats DROP COLUMN team_abbr;
```

**Queries after fix:**
```sql
-- Get player with team name
SELECT p.name, t.name as team, p.age
FROM players p
JOIN teams t ON p.team_abbr = t.abbreviation
WHERE p.name LIKE '%LeBron%';

-- Get player stats with team info
SELECT p.name, t.name as team, ps.pts, ps.reb, ps.ast
FROM player_stats ps
JOIN players p ON ps.player_id = p.id
JOIN teams t ON p.team_abbr = t.abbreviation
ORDER BY ps.pts DESC
LIMIT 10;
```

---

### Option 2: Denormalized (Keep for Query Performance)

**Changes:**
1. Add UNIQUE constraint to `teams.abbreviation`
2. Keep `players.team` for fast queries (no join needed)
3. Keep `player_stats.team_abbr` for fast queries

**Result:** Faster simple queries, but risk of data inconsistency

```sql
-- Just add UNIQUE constraint
CREATE UNIQUE INDEX idx_teams_abbreviation ON teams(abbreviation);
```

**Trade-offs:**
- ✅ Faster queries (no joins needed for simple lookups)
- ❌ Risk of inconsistency (team name could differ across tables)
- ❌ More storage used

---

## Current JOIN Queries (Work with existing schema)

Even with the current schema, these JOINs work correctly:

### Query 1: Player with Full Team Name
```sql
SELECT
    p.name as player_name,
    t.name as team_name,
    p.age,
    t.abbreviation as team_abbr
FROM players p
JOIN teams t ON p.team_abbr = t.abbreviation
WHERE p.name LIKE '%Shai%';
```

### Query 2: Player Stats with Team
```sql
SELECT
    p.name as player_name,
    t.name as team_name,
    ps.pts,
    ps.reb,
    ps.ast,
    ps.gp
FROM player_stats ps
JOIN players p ON ps.player_id = p.id
JOIN teams t ON p.team_abbr = t.abbreviation
ORDER BY ps.pts DESC
LIMIT 10;
```

### Query 3: Team Aggregates
```sql
SELECT
    t.name as team_name,
    COUNT(p.id) as player_count,
    SUM(ps.pts) as total_points,
    ROUND(AVG(ps.pts), 1) as avg_points
FROM teams t
JOIN players p ON t.abbreviation = p.team_abbr
JOIN player_stats ps ON p.id = ps.player_id
GROUP BY t.name
ORDER BY total_points DESC;
```

---

## Recommendation

**Immediate Action:**
1. Add UNIQUE constraint to `teams.abbreviation` ✅ (Required for FK integrity)

**Long-term Decision (Choose One):**

**A. Strict Normalization** (if data integrity is priority):
   - Remove `players.team`
   - Remove `player_stats.team_abbr`
   - Always JOIN to get team info

**B. Keep Denormalized** (if query performance is priority):
   - Keep redundant columns
   - Add triggers to maintain consistency
   - Accept slight storage overhead

---

## Next Steps

1. Review current query patterns in the application
2. Decide: Normalization vs Denormalization
3. Create migration script
4. Test thoroughly before applying to production database

**Status**: Analysis complete, awaiting decision on approach
