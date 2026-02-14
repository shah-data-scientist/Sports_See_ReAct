"""
Simple test to see what happens with HYBRID queries.
Tests both classification and actual API response.
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/chat"

test_queries = [
    "What do authoritative voices say about playoff basketball?",
    "Who are the top 5 scorers?",  # Statistical
    "Explain the pick and roll strategy",  # Contextual
]

print("Testing HYBRID Query Execution")
print("=" * 80)

for i, query in enumerate(test_queries, 1):
    print(f"\n[{i}] Query: {query}")
    print("-" * 80)

    # Call API
    response = requests.post(
        API_URL,
        json={"query": query, "k": 5},
        timeout=60
    )

    if response.status_code == 200:
        data = response.json()

        # Extract key fields
        query_type = data.get("query_type", "N/A")
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        processing_time = data.get("processing_time_ms", 0)

        # Analyze content
        has_stats = any(keyword in answer.lower() for keyword in
                       ['points', 'rebounds', 'assists', 'average', 'scored', 'stats', 'games'])
        has_opinion = any(keyword in answer.lower() for keyword in
                         ['discuss', 'community', 'reddit', 'fans', 'voices', 'debate'])

        print(f"Query Type: {query_type}")
        print(f"Sources: {len(sources)}")
        print(f"Processing: {processing_time:.0f}ms")
        print(f"Answer Length: {len(answer)} chars")
        print(f"\nContent Analysis:")
        print(f"  - Contains Statistics: {has_stats}")
        print(f"  - Contains Opinions: {has_opinion}")
        print(f"\nAnswer Preview:")
        print(f"  {answer[:300]}...")

        # Diagnosis
        if query_type == "hybrid":
            if has_stats and has_opinion:
                print("\n✅ TRUE HYBRID: Both SQL stats AND vector context present")
            elif has_stats and not has_opinion:
                print("\n⚠️ PARTIAL HYBRID: Only SQL stats (vector failed or irrelevant)")
            elif has_opinion and not has_stats:
                print("\n⚠️ PARTIAL HYBRID: Only vector content (SQL failed or empty)")
            else:
                print("\n❌ FAILED HYBRID: Neither SQL nor vector content detected")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"   {response.text[:200]}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("If HYBRID queries show '⚠️ PARTIAL HYBRID: Only vector content', it means:")
print("1. Query correctly routes to HYBRID")
print("2. SQL tool is called but returns no relevant results")
print("3. System falls back to vector-only response")
print("4. This is CORRECT behavior for opinion/discussion queries")
