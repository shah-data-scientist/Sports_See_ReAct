"""
DATABASE MIGRATION - PHASE 1: Add UNIQUE Constraint

Safe migration that adds UNIQUE constraint to teams.abbreviation.
This enables proper foreign key integrity without changing data.

BEFORE:
- teams.abbreviation has no UNIQUE constraint (but is referenced by FKs)

AFTER:
- teams.abbreviation has UNIQUE constraint ✅
- All data preserved
- All queries still work
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

def backup_database(db_path: Path) -> Path:
    """Create timestamped backup of database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def check_existing_constraint(conn: sqlite3.Connection) -> bool:
    """Check if UNIQUE constraint already exists."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA index_list(teams)")
    indexes = cursor.fetchall()

    for index in indexes:
        index_name = index[1]
        cursor.execute(f"PRAGMA index_info({index_name})")
        columns = cursor.fetchall()
        if any(col[2] == 'abbreviation' for col in columns):
            return True
    return False

def verify_no_duplicates(conn: sqlite3.Connection) -> tuple[bool, list]:
    """Verify no duplicate abbreviations exist."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT abbreviation, COUNT(*) as count
        FROM teams
        GROUP BY abbreviation
        HAVING count > 1
    """)
    duplicates = cursor.fetchall()
    return len(duplicates) == 0, duplicates

def add_unique_constraint(conn: sqlite3.Connection) -> None:
    """Add UNIQUE constraint to teams.abbreviation."""
    cursor = conn.cursor()

    # Create UNIQUE index
    cursor.execute("CREATE UNIQUE INDEX idx_teams_abbreviation ON teams(abbreviation)")
    conn.commit()
    print("✅ UNIQUE constraint added to teams.abbreviation")

def verify_constraint(conn: sqlite3.Connection) -> bool:
    """Verify UNIQUE constraint is in place."""
    cursor = conn.cursor()

    # Try to insert duplicate (should fail)
    try:
        cursor.execute("INSERT INTO teams (id, abbreviation, name) VALUES (999, 'LAL', 'Test Duplicate')")
        conn.rollback()
        print("❌ UNIQUE constraint NOT working (duplicate insert succeeded)")
        return False
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            print("✅ UNIQUE constraint verified (duplicate insert blocked)")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False

def main():
    """Execute Phase 1 migration."""
    print("="*80)
    print("DATABASE MIGRATION - PHASE 1")
    print("Add UNIQUE Constraint to teams.abbreviation")
    print("="*80)

    db_path = Path("data/sql/nba_stats.db")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    print(f"\n📂 Database: {db_path}")
    print(f"📊 Size: {db_path.stat().st_size / 1024:.1f} KB")

    # Step 1: Backup
    print("\n" + "─"*80)
    print("STEP 1: Backup Database")
    print("─"*80)
    backup_path = backup_database(db_path)

    # Step 2: Check for existing constraint
    print("\n" + "─"*80)
    print("STEP 2: Check Existing Constraints")
    print("─"*80)
    conn = sqlite3.connect(db_path)

    if check_existing_constraint(conn):
        print("✅ UNIQUE constraint already exists on teams.abbreviation")
        print("   No migration needed!")
        conn.close()
        return
    else:
        print("⚠️  No UNIQUE constraint found - migration required")

    # Step 3: Verify no duplicates
    print("\n" + "─"*80)
    print("STEP 3: Verify Data Integrity")
    print("─"*80)

    no_duplicates, duplicates = verify_no_duplicates(conn)
    if not no_duplicates:
        print(f"❌ Found {len(duplicates)} duplicate abbreviations:")
        for abbr, count in duplicates:
            print(f"   {abbr}: {count} occurrences")
        print("\n⚠️  Cannot proceed - fix duplicates first!")
        conn.close()
        return
    else:
        print("✅ No duplicate abbreviations found")

    # Step 4: Add UNIQUE constraint
    print("\n" + "─"*80)
    print("STEP 4: Add UNIQUE Constraint")
    print("─"*80)

    try:
        add_unique_constraint(conn)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"   Restore from backup: {backup_path}")
        conn.close()
        return

    # Step 5: Verify
    print("\n" + "─"*80)
    print("STEP 5: Verify Migration")
    print("─"*80)

    if verify_constraint(conn):
        print("\n" + "="*80)
        print("✅ PHASE 1 MIGRATION COMPLETE")
        print("="*80)
        print(f"\n✅ UNIQUE constraint added successfully")
        print(f"✅ Backup preserved: {backup_path}")
        print(f"✅ Database ready for Phase 2 (optional)")
    else:
        print("\n❌ Verification failed - check database manually")

    conn.close()

if __name__ == "__main__":
    main()
