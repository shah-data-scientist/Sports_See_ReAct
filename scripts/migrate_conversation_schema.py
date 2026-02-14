"""
FILE: migrate_conversation_schema.py
STATUS: Active
RESPONSIBILITY: Migrate feedback database to add conversation support
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import sys
import io
import sqlite3
from pathlib import Path

# Force UTF-8 encoding for stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from src.core.config import settings
from src.repositories.feedback import FeedbackRepository
from src.repositories.conversation import ConversationRepository

def migrate_database():
    """Migrate database to add conversation support."""

    print("=" * 80)
    print("  DATABASE MIGRATION: CONVERSATION SCHEMA")
    print("=" * 80)

    # Get database path (uses interactions.db, not feedback.db)
    db_path = Path(settings.database_dir) / "interactions.db"

    print(f"\nDatabase: {db_path}")
    print(f"Exists: {db_path.exists()}")

    if not db_path.exists():
        print("\n[INFO] Database doesn't exist yet - will be created fresh")
        print("[1/3] Creating new database with full schema...")

        # Initialize repositories (creates tables)
        feedback_repo = FeedbackRepository()
        conversation_repo = ConversationRepository()

        print("  [+] Tables created")
        return True

    # Check if migration needed
    print("\n[INFO] Checking if migration needed...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check chat_interactions table
    cursor.execute("PRAGMA table_info(chat_interactions)")
    columns = {col[1] for col in cursor.fetchall()}

    needs_migration = False

    if "conversation_id" not in columns:
        print("  [-] conversation_id column missing")
        needs_migration = True
    else:
        print("  [+] conversation_id column exists")

    if "turn_number" not in columns:
        print("  [-] turn_number column missing")
        needs_migration = True
    else:
        print("  [+] turn_number column exists")

    # Check conversations table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
    conversations_table_exists = cursor.fetchone() is not None

    if not conversations_table_exists:
        print("  [-] conversations table missing")
        needs_migration = True
    else:
        print("  [+] conversations table exists")

    if not needs_migration:
        print("\n[SUCCESS] Database schema is up-to-date")
        conn.close()
        return True

    # Perform migration
    print("\n[2/3] Performing schema migration...")

    try:
        # Add conversation_id column if missing
        if "conversation_id" not in columns:
            print("  Adding conversation_id column...")
            cursor.execute("""
                ALTER TABLE chat_interactions
                ADD COLUMN conversation_id TEXT
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_id
                ON chat_interactions(conversation_id)
            """)
            print("    [+] conversation_id column added")

        # Add turn_number column if missing
        if "turn_number" not in columns:
            print("  Adding turn_number column...")
            cursor.execute("""
                ALTER TABLE chat_interactions
                ADD COLUMN turn_number INTEGER
            """)
            print("    [+] turn_number column added")

        # Create conversations table if missing
        if not conversations_table_exists:
            print("  Creating conversations table...")
            cursor.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON conversations(status)
            """)
            print("    [+] conversations table created")

        conn.commit()
        print("\n[+] Migration successful")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        return False
    finally:
        conn.close()

    # Verify migration
    print("\n[3/3] Verifying migration...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check columns
    cursor.execute("PRAGMA table_info(chat_interactions)")
    columns = {col[1] for col in cursor.fetchall()}

    verification_passed = True

    if "conversation_id" in columns:
        print("  [+] conversation_id column verified")
    else:
        print("  [-] conversation_id column verification FAILED")
        verification_passed = False

    if "turn_number" in columns:
        print("  [+] turn_number column verified")
    else:
        print("  [-] turn_number column verification FAILED")
        verification_passed = False

    # Check conversations table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
    if cursor.fetchone():
        print("  [+] conversations table verified")
    else:
        print("  [-] conversations table verification FAILED")
        verification_passed = False

    conn.close()

    if verification_passed:
        print("\n" + "=" * 80)
        print("  MIGRATION COMPLETE - Database ready for conversation history")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("  MIGRATION FAILED - Please check errors above")
        print("=" * 80)

    return verification_passed

if __name__ == "__main__":
    try:
        success = migrate_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
