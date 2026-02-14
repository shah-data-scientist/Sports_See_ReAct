"""
FILE: greeting_detection_comparison.py
STATUS: Active
RESPONSIBILITY: Compare greeting detection across multiple query variations
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

from src.services.query_classifier import QueryClassifier


def test_greeting_variations():
    """Test greeting detection with various query formats."""

    classifier = QueryClassifier()

    test_cases = [
        # Pure greetings (should return True)
        ("hi", True, "Pure single-word greeting"),
        ("hello", True, "Pure greeting"),
        ("hey there", True, "Greeting with simple address"),
        ("good morning", True, "Time-based greeting"),
        ("how are you?", True, "Conversational greeting (allowed to have ?)"),
        ("what's up", True, "Casual greeting"),

        # Mixed queries (should return False)
        ("hi tell me about Lebron", False, "Greeting + action request + basketball keyword"),
        ("hello, show me stats", False, "Greeting + comma + action request"),
        ("hey, what about the Lakers?", False, "Greeting + comma + basketball keyword"),
        ("hi, who is the top scorer?", False, "Greeting + comma + statistical question"),
        ("hello LeBron fans", False, "Greeting with basketball keyword"),
        ("thanks for the stats", False, "Thanks with basketball keyword"),
        ("hi team", False, "Greeting with sports keyword 'team'"),
        ("hi, can you help me?", False, "Greeting + comma + action request"),
        ("how many teams?", False, "Statistical question (not conversational greeting)"),
        ("hi there how are you doing today my friend", False, "Too long (>6 words)"),
        ("top 5 players", False, "Basketball query with number"),

        # Edge cases
        ("HI", True, "Case insensitive pure greeting"),
        ("hello!", True, "Greeting with exclamation"),
        ("good morning!", True, "Time greeting with exclamation"),
    ]

    print("=" * 100)
    print("GREETING DETECTION COMPARISON")
    print("=" * 100)
    print(f"\n{'Query':<50} {'Expected':<10} {'Actual':<10} {'Status':<8} Description")
    print("-" * 100)

    passed = 0
    failed = 0

    for query, expected, description in test_cases:
        actual = classifier._is_greeting(query)
        status = "✅ PASS" if actual == expected else "❌ FAIL"

        if actual == expected:
            passed += 1
        else:
            failed += 1

        # Truncate long queries for display
        display_query = query if len(query) <= 47 else query[:44] + "..."

        print(f"{display_query:<50} {str(expected):<10} {str(actual):<10} {status:<8} {description}")

    print("-" * 100)
    print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print("=" * 100)

    return passed, failed


if __name__ == "__main__":
    passed, failed = test_greeting_variations()

    if failed == 0:
        print("\n🎉 All tests passed! Strict greeting detection working perfectly.")
        print("\n✅ Key achievements:")
        print("   • Pure greetings correctly identified (early return path)")
        print("   • Mixed queries (greeting + content) correctly rejected")
        print("   • Action requests detected and rejected")
        print("   • Basketball keywords detected and rejected")
        print("   • Comma-separated queries rejected")
        print("   • Long queries (>6 words) rejected")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Review greeting detection logic.")
