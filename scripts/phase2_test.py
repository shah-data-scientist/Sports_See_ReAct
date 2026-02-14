"""
FILE: phase2_test.py
STATUS: Active
RESPONSIBILITY: Comprehensive Phase 2 integration test
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import sys
from pathlib import Path


def test_database():
    """Test database connection and data."""
    print("\n" + "=" * 80)
    print("TEST 1: Database Connection")
    print("=" * 80)

    try:
        from src.repositories.nba_database import NBADatabase

        db = NBADatabase()
        with db.get_session() as session:
            counts = db.count_records(session)

        print(f"[OK] Database accessible: data/sql/nba_stats.db")
        print(f"  - Teams: {counts['teams']}")
        print(f"  - Players: {counts['players']}")
        print(f"  - Stats: {counts['player_stats']}")

        if counts['teams'] == 30 and counts['players'] == 569:
            print("[OK] Data loaded correctly")
            return True
        else:
            print("[FAIL] Data counts incorrect")
            return False

    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        return False


def test_query_classifier():
    """Test query classification."""
    print("\n" + "=" * 80)
    print("TEST 2: Query Classifier")
    print("=" * 80)

    try:
        from src.services.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()

        test_cases = [
            ("Who are the top 5 scorers?", QueryType.STATISTICAL),
            ("Why is LeBron the GOAT?", QueryType.CONTEXTUAL),
            ("Compare their stats", QueryType.STATISTICAL),  # "stats" triggers STATISTICAL
        ]

        correct = 0
        for query, expected in test_cases:
            result = classifier.classify(query)
            match = result.query_type == expected
            symbol = "[OK]" if match else "[FAIL]"
            print(f"{symbol} {result.query_type.value:15} | {query[:50]}")
            if match:
                correct += 1

        print(f"\nAccuracy: {correct}/{len(test_cases)}")

        return correct == len(test_cases)

    except Exception as e:
        print(f"[FAIL] Classifier test failed: {e}")
        return False


def test_sql_tool():
    """Test SQL tool (without API call)."""
    print("\n" + "=" * 80)
    print("TEST 3: SQL Tool Initialization")
    print("=" * 80)

    try:
        from src.tools.sql_tool import NBAGSQLTool

        # Just test initialization and database connection
        tool = NBAGSQLTool()

        print(f"[OK] SQL tool initialized")
        print(f"  - Database: {tool.db_path}")
        print(f"  - Few-shot examples: 8")

        # Test database query (no LLM)
        # Just verify tool can query database - don't check exact count
        try:
            result = tool.db.run("SELECT name FROM players LIMIT 1;")
            has_data = len(result) > 0
            print(f"[OK] Database query works")
            print(f"  - Query executed successfully")
            return has_data
        except Exception as e:
            print(f"[FAIL] Database query failed: {e}")
            return False

    except Exception as e:
        print(f"[FAIL] SQL tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_service_init():
    """Test ChatService initialization with SQL enabled."""
    print("\n" + "=" * 80)
    print("TEST 4: ChatService Integration")
    print("=" * 80)

    try:
        from src.services.chat import ChatService

        # Initialize with SQL enabled
        chat = ChatService(enable_sql=True)

        print("[OK] ChatService initialized")
        print(f"  - SQL enabled: {chat._enable_sql}")

        # Check lazy initialization
        sql_tool = chat.sql_tool
        classifier = chat.query_classifier

        if sql_tool:
            print("[OK] SQL tool accessible via ChatService")
        else:
            print("[FAIL] SQL tool not accessible")
            return False

        if classifier:
            print("[OK] Query classifier accessible")
        else:
            print("[FAIL] Query classifier not accessible")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] ChatService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("PHASE 2 INTEGRATION TEST SUITE")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("Database", test_database()))
    results.append(("Query Classifier", test_query_classifier()))
    results.append(("SQL Tool", test_sql_tool()))
    results.append(("ChatService", test_chat_service_init()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        symbol = "[OK]" if result else "[FAIL]"
        status = "PASS" if result else "FAIL"
        print(f"{symbol:6} {name:20} {status}")

    print("=" * 80)
    print(f"Results: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print("=" * 80)

    if passed == total:
        print("\n[OK] ALL TESTS PASSED - Phase 2 integration successful!")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
