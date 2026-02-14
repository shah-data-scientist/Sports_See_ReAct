"""
FILE: demo_weighted_expansion.py
STATUS: Active (Demo)
RESPONSIBILITY: Demonstrate weighted query expansion combining category + word count
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

from src.services.query_classifier import QueryClassifier
from src.services.query_expansion import QueryExpander


def demo_weighted_expansion():
    """Demonstrate weighted expansion formula with diverse queries."""
    classifier = QueryClassifier()
    expander = QueryExpander()

    # Test queries with different categories and word counts
    test_queries = [
        # NOISY queries (base=1)
        "yo best team lol",  # 4 words → base=1, adj=+1 → max_exp=2
        "whos da best szn???",  # 4 words → base=1, adj=+1 → max_exp=2
        "best player bro fr lmao",  # 5 words → base=1, adj=0 → max_exp=1
        # SIMPLE queries (base=4)
        "top scorers",  # 2 words → base=4, adj=+1 → max_exp=5
        "Who are the top 5 scorers?",  # 6 words → base=4, adj=0 → max_exp=4
        "Tell me about the Lakers championship history and their greatest players",  # 11 words → base=4, adj=0 → max_exp=4
        "Can you provide detailed information about the historical evolution of the Lakers franchise",  # 13 words → base=4, adj=0 → max_exp=4
        "Please provide comprehensive detailed analysis of Lakers franchise history evolution development timeline achievements",  # 12 words (long) → base=4, adj=0 → max_exp=4
        # CONVERSATIONAL queries (base=5)
        "And blocks?",  # 2 words → base=5, adj=+1 → max_exp=5 (clamped)
        "What about his assists?",  # 4 words → base=5, adj=+1 → max_exp=5 (clamped)
        "Tell me more about that player",  # 6 words → base=5, adj=0 → max_exp=5
        # COMPLEX queries (base=2)
        "Analyze patterns in playoff efficiency",  # 5 words → base=2, adj=0 → max_exp=2
        "Compare stats and explain why they're effective",  # 7 words → base=2, adj=0 → max_exp=2
        "Analyze the historical evolution of three-point shooting strategies across different NBA eras and explain",  # 14 words → base=2, adj=0 → max_exp=2
        "Can you provide a comprehensive detailed analysis of the historical evolution of three-point shooting strategies across different NBA eras",  # 20 words → base=2, adj=-1 → max_exp=1
    ]

    print("=" * 100)
    print("WEIGHTED EXPANSION DEMO: Category + Word Count Formula")
    print("=" * 100)
    print("\nFormula: max_expansions = clamp(category_base + word_count_adjustment, 1, 5)")
    print("\nCategory Base Values:")
    print("  - NOISY: 1 (minimal, avoid noise)")
    print("  - SIMPLE: 4 (balanced)")
    print("  - CONVERSATIONAL: 5 (aggressive)")
    print("  - COMPLEX: 2 (conservative)")
    print("\nWord Count Adjustments:")
    print("  - < 5 words: +1 (needs more expansion)")
    print("  - 5-15 words: 0 (use base value)")
    print("  - > 15 words: -1 (needs less expansion)")
    print("=" * 100)

    for query in test_queries:
        # Classify query
        classification = classifier.classify(query)
        category = classification.query_category

        # Get word count
        word_count = len(query.split())

        # Compute expected adjustment
        if word_count < 5:
            adjustment = 1
        elif word_count > 15:
            adjustment = -1
        else:
            adjustment = 0

        # Category base values
        category_base = {
            "noisy": 1,
            "conversational": 5,
            "simple": 4,
            "complex": 2,
        }
        base_value = category_base.get(category, 4)
        expected_max_exp = max(1, min(5, base_value + adjustment))

        # Perform expansion
        expanded = expander.expand_weighted(query, category=category)

        # Extract expansion terms (everything after original query)
        expansion_terms = expanded.replace(query, "").strip()
        num_terms = len(expansion_terms.split()) if expansion_terms else 0

        print(f"\n{'─' * 100}")
        print(f"Query: \"{query}\"")
        print(f"  Word Count: {word_count}")
        print(f"  Category: {category.upper()} (base={base_value})")
        print(f"  Adjustment: {adjustment:+d} (word count)")
        print(
            f"  Expected max_exp: {base_value} + {adjustment:+d} = {expected_max_exp} (clamped to [1, 5])"
        )
        print(f"  Expansion terms added: {num_terms}")
        if expansion_terms:
            print(f"  Expanded: \"{expanded[:150]}{'...' if len(expanded) > 150 else ''}\"")

    print("\n" + "=" * 100)
    print("DEMO COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    demo_weighted_expansion()
