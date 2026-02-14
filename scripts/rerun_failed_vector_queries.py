"""
Re-run the 8 failed vector evaluation queries with longer delays to avoid rate limits.
"""
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.main import app
from src.evaluation.test_cases.vector_test_cases import EVALUATION_TEST_CASES

# Load previous results
results_file = Path("evaluation_results/vector_evaluation_20260213_185715.json")
with open(results_file) as f:
    previous_results = json.load(f)

# Extract failed test cases
failed_results = [r for r in previous_results['results'] if 'error' in r]
failed_questions = [r['question'] for r in failed_results]

print(f"Found {len(failed_questions)} failed queries to re-run")

# Find matching test cases
test_cases_to_retry = []
for tc in EVALUATION_TEST_CASES:
    if tc.question in failed_questions:
        test_cases_to_retry.append(tc)

print(f"Matched {len(test_cases_to_retry)} test cases")

# Initialize test client
client = TestClient(app)

# Re-run with longer delays
retry_results = []
for i, test_case in enumerate(test_cases_to_retry, 1):
    print(f"\n[{i}/{len(test_cases_to_retry)}] {test_case.question[:80]}...")

    # Make API request
    try:
        response = client.post(
            "/api/v1/chat",
            json={"query": test_case.question, "k": 5}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Success - {len(result.get('sources', []))} sources")
            retry_results.append({
                "question": test_case.question,
                "category": test_case.category.value,
                "expected_routing": test_case.expected_routing.value,
                "actual_routing": result.get("query_type", "unknown"),
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "success": True
            })
        else:
            print(f"  ✗ Failed - Status {response.status_code}")
            retry_results.append({
                "question": test_case.question,
                "category": test_case.category.value,
                "error": f"API error {response.status_code}: {response.text}",
                "success": False
            })

    except Exception as e:
        print(f"  ✗ Exception: {e}")
        retry_results.append({
            "question": test_case.question,
            "category": test_case.category.value,
            "error": str(e),
            "success": False
        })

    # Long delay to avoid rate limits
    if i < len(test_cases_to_retry):
        print("  Waiting 30s to avoid rate limits...")
        time.sleep(30)

# Save retry results
output_file = Path("evaluation_results/vector_retry_results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_retries": len(test_cases_to_retry),
        "successful": sum(1 for r in retry_results if r.get('success', False)),
        "results": retry_results
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Retry complete!")
print(f"   Successful: {sum(1 for r in retry_results if r.get('success', False))}/{len(retry_results)}")
print(f"   Results saved to: {output_file}")
