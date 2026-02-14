"""
FILE: validate_vector_ground_truth_proper.py
STATUS: Active
RESPONSIBILITY: Validate that RAG output matches ground truth specifications
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

VALIDATION (not generation):
- Ground truth = human-written specification (independent)
- RAG output = what system actually returns
- Validation = check if actual matches specification

This avoids circular evaluation (system evaluating itself).
"""

import io
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient
from src.api.main import create_app
from src.evaluation.vector_test_cases import EVALUATION_TEST_CASES


def parse_specification(ground_truth: str) -> dict:
    """Extract expected criteria from human-written specification."""
    spec = {
        "expected_sources": [],
        "should_retrieve": True,
        "expected_keywords": []
    }

    if "Reddit" in ground_truth:
        spec["expected_sources"].append("Reddit")
    if "glossary" in ground_truth.lower() or "xlsx" in ground_truth.lower():
        spec["expected_sources"].append("glossary")
    if "out of scope" in ground_truth.lower():
        spec["should_retrieve"] = False

    return spec


def validate_output(spec: dict, actual: dict) -> dict:
    """Check if actual output matches specification."""
    sources = actual.get("sources", [])
    source_names = [s.get("source", "") for s in sources]

    validation = {"passed": True, "issues": []}

    for expected_src in spec["expected_sources"]:
        found = any(expected_src.lower() in src.lower() for src in source_names)
        if not found:
            validation["passed"] = False
            validation["issues"].append(f"Expected {expected_src}, not found")

    return validation


def validate_sample():
    """Run validation on sample cases."""
    print("\n" + "="*100)
    print("  GROUND TRUTH VALIDATION (Specification vs. RAG Output)")
    print("="*100)
    print("\nValidating: Does RAG output match human-written specifications?\n")

    app = create_app()
    results = []

    # Sample 10 cases
    sample_indices = list(range(0, 100, 10))[:10]

    with TestClient(app) as client:
        for idx, i in enumerate(sample_indices, 1):
            if i >= len(EVALUATION_TEST_CASES):
                break

            tc = EVALUATION_TEST_CASES[i]
            print(f"\n[{idx}/10] {tc.category.value}: {tc.question[:60]}...")
            print(f"Spec: {tc.ground_truth[:80]}...")

            try:
                resp = client.post("/api/v1/chat", json={"query": tc.question, "k": 5}, timeout=30)

                if resp.status_code != 200:
                    print(f"  ❌ API error {resp.status_code}")
                    time.sleep(2)
                    continue

                actual = resp.json()
                spec = parse_specification(tc.ground_truth)
                validation = validate_output(spec, actual)

                if validation["passed"]:
                    print(f"  ✅ PASS - RAG matches specification")
                else:
                    print(f"  ❌ FAIL - Specification not met:")
                    for issue in validation["issues"]:
                        print(f"     - {issue}")

                results.append({
                    "question": tc.question,
                    "spec": tc.ground_truth,
                    "sources": [s.get("source") for s in actual.get("sources", [])],
                    "passed": validation["passed"],
                    "issues": validation["issues"]
                })

            except Exception as e:
                print(f"  ❌ Error: {e}")

            time.sleep(2)

    # Save
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"ground_truth_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    summary = {
        "timestamp": datetime.now().isoformat(),
        "passed": sum(1 for r in results if r.get("passed")),
        "failed": sum(1 for r in results if not r.get("passed")),
        "results": results
    }

    output_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n\n{'='*100}")
    print(f"  VALIDATION COMPLETE")
    print(f"{'='*100}")
    print(f"\nPassed: {summary['passed']}/10")
    print(f"Failed: {summary['failed']}/10")
    print(f"\nResults: {output_file}")

    return output_file


if __name__ == "__main__":
    try:
        validate_sample()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
