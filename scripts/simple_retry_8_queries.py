"""
Simple script to retry 8 failed queries using direct HTTP requests.
Requires the API to be running on localhost:8000.
"""
import json
import time
import requests
from pathlib import Path

# The 8 failed queries
FAILED_QUERIES = [
    "What do fans debate about Reggie Miller's efficiency?",
    "Which NBA teams didn't have home court advantage in finals according to discussions?",
    "According to basketball discussions, what makes a player efficient in playoffs?",
    "Best strategy for winning in NBA 2K24 video game?",
    "How to fix my computer's blue screen error?",
    "asdfghjkl qwerty12345",
    "A" * 2100,  # Very long string (>2000 chars will be rejected)
    "Returning to home court, which teams historically lacked it?"
]

API_URL = "http://localhost:8000/api/v1/chat"

print(f"Retrying {len(FAILED_QUERIES)} failed queries...")
print("Delay: 30s between queries")
print()

results = []

for i, query in enumerate(FAILED_QUERIES, 1):
    print(f"[{i}/{len(FAILED_QUERIES)}] {query[:80]}...")

    try:
        response = requests.post(
            API_URL,
            json={"query": query, "k": 5},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Success - {len(result.get('sources', []))} sources, {result.get('processing_time_ms', 0):.0f}ms")
            results.append({
                "query": query,
                "success": True,
                "status_code": 200,
                "data": result
            })
        else:
            print(f"  ✗ Failed - Status {response.status_code}")
            print(f"    Error: {response.text[:200]}")
            results.append({
                "query": query,
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            })

    except Exception as e:
        print(f"  ✗ Exception: {e}")
        results.append({
            "query": query,
            "success": False,
            "error": str(e)
        })

    # Delay before next query
    if i < len(FAILED_QUERIES):
        print("  Waiting 30s...")
        time.sleep(30)

# Save results
output_file = Path("evaluation_results/retry_8_queries_results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(FAILED_QUERIES),
        "successful": sum(1 for r in results if r.get('success', False)),
        "failed": sum(1 for r in results if not r.get('success', True)),
        "results": results
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Retry complete!")
print(f"   Successful: {sum(1 for r in results if r.get('success', False))}/{len(results)}")
print(f"   Failed: {sum(1 for r in results if not r.get('success', True))}/{len(results)}")
print(f"   Results saved to: {output_file}")
