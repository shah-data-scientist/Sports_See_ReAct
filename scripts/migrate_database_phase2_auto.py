"""
DATABASE MIGRATION - PHASE 2: Remove Redundant Columns (AUTO-CONFIRM)

Recreates database using SQLAlchemy models (normalized schema).
This removes redundant columns: players.team and player_stats.team_abbr

⚠️ WARNING: This script recreates the database from scratch!
Ensure you have a backup before running.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.nba_database import NBADatabase, DataDictionaryModel

def backup_database(db_path: Path) -> Path:
    """Create timestamped backup of database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_phase2_backup_{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def export_data(db_path: Path) -> dict:
    """Export all data from current database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    data = {}

    # Export teams
    cursor.execute("SELECT id, abbreviation, name FROM teams ORDER BY id")
    data['teams'] = cursor.fetchall()

    # Export players
    cursor.execute("SELECT id, name, team_abbr, age FROM players ORDER BY id")
    data['players'] = cursor.fetchall()

    # Export player_stats (all 45 columns)
    cursor.execute("SELECT * FROM player_stats ORDER BY id")
    columns = [desc[0] for desc in cursor.description]
    data['player_stats'] = cursor.fetchall()
    data['player_stats_columns'] = columns

    # Export data_dictionary
    cursor.execute("SELECT * FROM data_dictionary ORDER BY abbreviation")
    data['data_dictionary'] = cursor.fetchall()

    conn.close()

    print(f"✅ Exported data:")
    print(f"   Teams: {len(data['teams'])}")
    print(f"   Players: {len(data['players'])}")
    print(f"   Player Stats: {len(data['player_stats'])}")
    print(f"   Dictionary: {len(data['data_dictionary'])}")

    return data

def import_data(db: NBADatabase, data: dict) -> None:
    """Import data into new database."""
    session = db.get_session()

    try:
        # Import teams
        print("\n📥 Importing teams...")
        for team_id, abbreviation, name in data['teams']:
            db.add_team(session, abbreviation, name)
        session.commit()
        print(f"   ✅ {len(data['teams'])} teams imported")

        # Import players (normalized schema - no 'team' field)
        print("\n📥 Importing players...")
        for player_id, name, team_abbr, age in data['players']:
            db.add_player(session, name, team_abbr, age)
        session.commit()
        print(f"   ✅ {len(data['players'])} players imported")

        # Import player_stats
        print("\n📥 Importing player stats...")
        columns = data['player_stats_columns']
        for row in data['player_stats']:
            stats_dict = dict(zip(columns, row))

            # Remove id (will be auto-generated)
            stats_dict.pop('id', None)

            # Extract player_id
            player_id = stats_dict.pop('player_id')

            # Remove team_abbr (no longer in normalized schema)
            stats_dict.pop('team_abbr', None)

            db.add_player_stats(session, player_id, stats_dict)

        session.commit()
        print(f"   ✅ {len(data['player_stats'])} player stats imported")

        # Import data_dictionary
        print("\n📥 Importing data dictionary...")
        for abbr, full_name, desc, col_name, table_name in data['data_dictionary']:
            entry = DataDictionaryModel(
                abbreviation=abbr,
                full_name=full_name,
                description=desc,
                column_name=col_name,
                table_name=table_name
            )
            session.add(entry)
        session.commit()
        print(f"   ✅ {len(data['data_dictionary'])} dictionary entries imported")

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def verify_migration(db_path: Path, original_data: dict) -> bool:
    """Verify migration preserved data correctly."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "─"*80)
    print("VERIFICATION")
    print("─"*80)

    all_ok = True

    # Check teams count
    cursor.execute("SELECT COUNT(*) FROM teams")
    teams_count = cursor.fetchone()[0]
    expected_teams = len(original_data['teams'])
    if teams_count == expected_teams:
        print(f"✅ Teams: {teams_count}/{expected_teams}")
    else:
        print(f"❌ Teams: {teams_count}/{expected_teams}")
        all_ok = False

    # Check players count
    cursor.execute("SELECT COUNT(*) FROM players")
    players_count = cursor.fetchone()[0]
    expected_players = len(original_data['players'])
    if players_count == expected_players:
        print(f"✅ Players: {players_count}/{expected_players}")
    else:
        print(f"❌ Players: {players_count}/{expected_players}")
        all_ok = False

    # Check player_stats count
    cursor.execute("SELECT COUNT(*) FROM player_stats")
    stats_count = cursor.fetchone()[0]
    expected_stats = len(original_data['player_stats'])
    if stats_count == expected_stats:
        print(f"✅ Player Stats: {stats_count}/{expected_stats}")
    else:
        print(f"❌ Player Stats: {stats_count}/{expected_stats}")
        all_ok = False

    # Check UNIQUE constraint
    cursor.execute("PRAGMA index_list(teams)")
    indexes = cursor.fetchall()
    has_unique = any('abbreviation' in str(idx) for idx in indexes)
    if has_unique:
        print("✅ UNIQUE constraint on teams.abbreviation")
    else:
        print("❌ UNIQUE constraint missing")
        all_ok = False

    # Test sample query
    cursor.execute("""
        SELECT t.name, SUM(ps.pts) as total_pts
        FROM teams t
        JOIN players p ON t.abbreviation = p.team_abbr
        JOIN player_stats ps ON p.id = ps.player_id
        WHERE t.abbreviation = 'LAL'
        GROUP BY t.name
    """)
    result = cursor.fetchone()
    if result and result[1] > 0:
        print(f"✅ Team query works: Lakers have {result[1]:,} total points")
    else:
        print("❌ Team query failed")
        all_ok = False

    conn.close()
    return all_ok

def main():
    """Execute Phase 2 migration (AUTO-CONFIRM)."""
    print("="*80)
    print("DATABASE MIGRATION - PHASE 2 (AUTO-CONFIRM)")
    print("Recreate Database with Normalized Schema")
    print("="*80)

    db_path = Path("data/sql/nba_stats.db")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    print(f"\n📂 Database: {db_path}")

    # Step 1: Backup
    print("\n" + "─"*80)
    print("STEP 1: Backup Current Database")
    print("─"*80)
    backup_path = backup_database(db_path)

    # Step 2: Export data
    print("\n" + "─"*80)
    print("STEP 2: Export Existing Data")
    print("─"*80)
    try:
        data = export_data(db_path)
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return

    # Step 3: Drop and recreate tables
    print("\n" + "─"*80)
    print("STEP 3: Recreate Database Schema")
    print("─"*80)

    try:
        db = NBADatabase(str(db_path))
        print("⚠️  Dropping existing tables...")
        db.drop_tables()
        print("✅ Tables dropped")

        print("📝 Creating new tables from SQLAlchemy models...")
        db.create_tables()
        print("✅ Tables created with normalized schema")

    except Exception as e:
        print(f"❌ Schema recreation failed: {e}")
        print(f"   Restore from backup: {backup_path}")
        return

    # Step 4: Import data
    print("\n" + "─"*80)
    print("STEP 4: Import Data")
    print("─"*80)

    try:
        import_data(db, data)
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print(f"   Restore from backup: {backup_path}")
        db.close()
        return

    db.close()

    # Step 5: Verify
    if verify_migration(db_path, data):
        print("\n" + "="*80)
        print("✅ PHASE 2 MIGRATION COMPLETE")
        print("="*80)
        print(f"\n✅ Database normalized successfully")
        print(f"✅ Backup preserved: {backup_path}")
        print(f"✅ Team queries should now work correctly")
    else:
        print("\n❌ Verification failed - check database manually")
        print(f"   Backup available: {backup_path}")

if __name__ == "__main__":
    main()
