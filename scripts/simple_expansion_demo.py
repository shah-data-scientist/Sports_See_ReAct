"""Quick demo of weighted expansion formula."""
from src.services.query_classifier import QueryClassifier
from src.services.query_expansion import QueryExpander

# Initialize
classifier = QueryClassifier()
expander = QueryExpander()

# Test queries
queries = [
    "yo best scorer lol",           # 4 words, NOISY
    "Who are the top scorers?",     # 5 words, SIMPLE
    "What about his blocks?",       # 4 words, CONVERSATIONAL
    "Analyze shooting patterns in playoff games and explain the trends",  # 10 words, COMPLEX
]

print("=" * 80)
print("WEIGHTED EXPANSION FORMULA EXAMPLES")
print("=" * 80)

for query in queries:
    # Classify
    result = classifier.classify(query)
    category = result.query_category

    # Get word count
    word_count = len(query.split())

    # Compute expected values
    base_values = {"noisy": 1, "conversational": 5, "simple": 4, "complex": 2}
    base = base_values[category]

    if word_count < 5:
        adj = 1
    elif word_count > 15:
        adj = -1
    else:
        adj = 0

    max_exp = max(1, min(5, base + adj))

    # Expand
    expanded = expander.expand_weighted(query, category=category)

    # Display
    print(f"\n{'─' * 80}")
    print(f"Query: \"{query}\"")
    print(f"  Words: {word_count}")
    print(f"  Category: {category.upper()}")
    print(f"  Formula: base({base}) + adjustment({adj:+d}) = {max_exp}")
    print(f"  Expanded: \"{expanded[:120]}{'...' if len(expanded) > 120 else ''}\"")

print(f"\n{'=' * 80}")
