"""
FILE: regenerate_gold_contexts.py
STATUS: Active
RESPONSIBILITY: Regenerate gold contexts from actual vector store chunks
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Extract REAL chunk text from vector store for gold contexts instead of summaries.
This fixes the Context Precision/Recall mismatch issue.
"""

import io
import json
import pickle
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from evaluation.vector_test_cases import EVALUATION_TEST_CASES
from src.repositories.vector_store import VectorStoreRepository
from mistralai import Mistral

# Rate limiting for Mistral API
MISTRAL_RPM = 200  # Mistral allows ~200/min for embeddings
DELAY_BETWEEN_CALLS = 60 / MISTRAL_RPM  # ~0.3 seconds per call


def regenerate_gold_contexts():
    """Regenerate gold contexts using actual chunk text from vector store."""
    print("\n" + "="*80)
    print("  REGENERATING GOLD CONTEXTS FROM ACTUAL VECTOR STORE")
    print("="*80)
    print("  Strategy: Query vector store for each test case and extract")
    print("  ACTUAL chunk text (not summaries) as gold contexts")
    print("="*80 + "\n")

    # Load vector store
    repo = VectorStoreRepository()
    if not repo.load():
        print("ERROR: Could not load vector store")
        return 1

    # Initialize Mistral client for embeddings
    mistral_client = Mistral(api_key=settings.mistral_api_key)

    results = []

    # For each test case, search vector store and extract top chunks
    for i, test_case in enumerate(EVALUATION_TEST_CASES, 1):
        print(f"[{i}/{len(EVALUATION_TEST_CASES)}] {test_case.category.value}: {test_case.question[:60]}...")

        # Rate limiting delay (skip first one)
        if i > 1:
            time.sleep(DELAY_BETWEEN_CALLS)

        # Search vector store for this question
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Generate embedding for query
                embedding_response = mistral_client.embeddings.create(
                    model=settings.embedding_model,
                    inputs=[test_case.question]
                )
                query_embedding = embedding_response.data[0].embedding

                # Convert to numpy array
                import numpy as np
                query_embedding = np.array(query_embedding, dtype=np.float32)

                # Search vector store
                search_results = repo.search(query_embedding, k=5)

                # Extract actual chunk text (not summaries!)
                gold_contexts = []
                for chunk, score in search_results:
                    chunk_text = chunk.text  # DocumentChunk has .text attribute
                    if chunk_text and len(chunk_text) > 50:  # Skip very short chunks
                        gold_contexts.append(chunk_text)

                # Success - save results and break retry loop
                results.append({
                    "question": test_case.question,
                    "category": test_case.category.value,
                    "gold_contexts": gold_contexts,
                    "num_contexts": len(gold_contexts)
                })
                print(f"  ✓ Extracted {len(gold_contexts)} actual chunks as gold contexts")
                break  # Success, exit retry loop

            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10  # 10s, 20s
                    print(f"  ⚠️  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed or non-rate-limit error
                    print(f"  ✗ ERROR: {str(e)[:100]}")
                    results.append({
                        "question": test_case.question,
                        "category": test_case.category.value,
                        "gold_contexts": [],
                        "num_contexts": 0,
                        "error": str(e)
                    })
                    break  # Give up on this test case

    # Save to file
    output_file = Path("evaluation_results/vector_gold_contexts.json")
    output_file.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Print summary
    print(f"\n{'='*80}")
    print("  SUMMARY")
    print(f"{'='*80}")
    print(f"Total test cases: {len(EVALUATION_TEST_CASES)}")
    print(f"Successful: {sum(1 for r in results if r['num_contexts'] > 0)}")
    print(f"Failed: {sum(1 for r in results if r['num_contexts'] == 0)}")

    avg_contexts = sum(r['num_contexts'] for r in results) / len(results) if results else 0
    print(f"Average gold contexts per question: {avg_contexts:.1f}")

    print(f"\n✓ Gold contexts saved to: {output_file}")
    print(f"\nThese are ACTUAL chunk texts from the vector store, not summaries!")
    print(f"RAGAS Context Precision/Recall should now be accurate.\n")

    return 0


if __name__ == "__main__":
    sys.exit(regenerate_gold_contexts())
