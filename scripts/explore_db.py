"""
Quick script to explore the interactions.db database.
Usage: poetry run python scripts/explore_db.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/sql/interactions.db")

def explore_database():
    """Explore the interactions database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("DATABASE: interactions.db")
    print("=" * 80)

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"\n📋 TABLES ({len(tables)}):")
    for table in tables:
        print(f"  • {table[0]}")

    # For each table, show schema and row count
    for table_name in [t[0] for t in tables]:
        print(f"\n{'=' * 80}")
        print(f"TABLE: {table_name}")
        print(f"{'=' * 80}")

        # Get schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        print("\n📐 SCHEMA:")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            pk_str = " [PRIMARY KEY]" if pk else ""
            null_str = " NOT NULL" if notnull else ""
            print(f"  • {name}: {type_}{null_str}{pk_str}")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"\n📊 ROW COUNT: {count:,}")

        # Show sample rows (first 3)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()

            print(f"\n📝 SAMPLE DATA (first 3 rows):")
            col_names = [col[1] for col in columns]

            for i, row in enumerate(rows, 1):
                print(f"\n  Row {i}:")
                for col_name, value in zip(col_names, row):
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {col_name}: {value}")

    print("\n" + "=" * 80)

    # Interactive query mode
    print("\n💬 INTERACTIVE QUERY MODE")
    print("Enter SQL queries (or 'quit' to exit):")
    print("Examples:")
    print("  SELECT * FROM conversations LIMIT 5;")
    print("  SELECT COUNT(*) FROM chat_interactions;")
    print("  SELECT rating, COUNT(*) FROM feedback GROUP BY rating;")

    while True:
        query = input("\nSQL> ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            break

        if not query:
            continue

        try:
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                # Get column names
                col_names = [desc[0] for desc in cursor.description]

                # Print header
                print("\n" + " | ".join(col_names))
                print("-" * 80)

                # Print rows
                for row in results:
                    formatted_row = []
                    for val in row:
                        if isinstance(val, str) and len(val) > 50:
                            formatted_row.append(val[:50] + "...")
                        else:
                            formatted_row.append(str(val))
                    print(" | ".join(formatted_row))

                print(f"\n({len(results)} row{'s' if len(results) != 1 else ''})")
            else:
                print("Query executed successfully (no results)")

        except Exception as e:
            print(f"❌ Error: {e}")

    conn.close()
    print("\n✅ Database connection closed")

if __name__ == "__main__":
    explore_database()
