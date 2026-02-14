"""
FILE: investigate_faithfulness.py
STATUS: Active
RESPONSIBILITY: Investigate faithfulness drop in Phase 7 vs Phase 5
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import logging
from pathlib import Path

from src.core.config import settings
from src.evaluation.vector_test_cases import EVALUATION_TEST_CASES
from src.services.chat import ChatService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def analyze_expansion_impact():
    """Compare retrieval with and without query expansion for sample queries."""

    # Load Phase 5 and Phase 7 results
    phase5_path = Path("evaluation_results/ragas_phase5.json")
    phase7_path = Path("evaluation_results/ragas_phase7.json")

    phase5_data = json.loads(phase5_path.read_text(encoding="utf-8"))
    phase7_data = json.loads(phase7_path.read_text(encoding="utf-8"))

    # Load checkpoint to get actual samples
    checkpoint_path = Path("evaluation_checkpoint_phase7.json")
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        samples = checkpoint.get("samples", [])
    else:
        logger.warning("No checkpoint found, will test on subset")
        samples = None

    print("\n" + "=" * 80)
    print("  FAITHFULNESS DROP INVESTIGATION")
    print("=" * 80)

    print(f"\nPhase 5 Faithfulness: {phase5_data['overall_scores']['faithfulness']:.3f}")
    print(f"Phase 7 Faithfulness: {phase7_data['overall_scores']['faithfulness']:.3f}")
    print(f"Drop: {(phase7_data['overall_scores']['faithfulness'] - phase5_data['overall_scores']['faithfulness']):.3f} ({((phase7_data['overall_scores']['faithfulness'] / phase5_data['overall_scores']['faithfulness']) - 1) * 100:.1f}%)")

    print("\n" + "=" * 80)
    print("  CATEGORY BREAKDOWN")
    print("=" * 80)

    for cat5, cat7 in zip(phase5_data["category_scores"], phase7_data["category_scores"]):
        if cat5["category"] == cat7["category"]:
            cat_name = cat5["category"]
            f5 = cat5["faithfulness"]
            f7 = cat7["faithfulness"]
            change = ((f7 / f5) - 1) * 100 if f5 > 0 else 0

            print(f"\n{cat_name.upper()}: {f5:.3f} -> {f7:.3f} ({change:+.1f}%)")

    # Analyze expansion characteristics
    print("\n" + "=" * 80)
    print("  QUERY EXPANSION ANALYSIS")
    print("=" * 80)

    chat_service = ChatService(enable_sql=True)
    chat_service.ensure_ready()

    # Test sample queries with different expansion levels
    test_cases = [
        ("Simple", EVALUATION_TEST_CASES[1]),  # LeBron stats
        ("Complex", EVALUATION_TEST_CASES[12]),  # Compare teams
        ("Noisy", EVALUATION_TEST_CASES[27]),  # Vague query
        ("Conversational", EVALUATION_TEST_CASES[40]),  # Follow-up
    ]

    for category, tc in test_cases:
        query = tc.question
        word_count = len(query.split())

        # Get expansion
        expanded = chat_service.query_expander.expand_smart(query)
        expansion_terms = expanded.replace(query, "").strip().split()

        # Get embeddings
        original_embedding = chat_service.embedding_service.embed_query(query)
        expanded_embedding = chat_service.embedding_service.embed_query(expanded)

        # Search with both
        original_results = chat_service.vector_store.search(original_embedding, k=5, metadata_filters=None)
        expanded_results = chat_service.vector_store.search(expanded_embedding, k=5, metadata_filters=None)

        print(f"\n[{category}] {query[:60]}...")
        print(f"  Words: {word_count} | Expansion terms: {len(expansion_terms)} | Terms: {' '.join(expansion_terms[:5])}{'...' if len(expansion_terms) > 5 else ''}")

        # Compare top results
        print(f"  Original top-3 sources: {', '.join([r[0].metadata.get('source', 'unknown')[:20] for r in original_results[:3]])}")
        print(f"  Expanded top-3 sources: {', '.join([r[0].metadata.get('source', 'unknown')[:20] for r in expanded_results[:3]])}")

        # Check overlap
        original_ids = {r[0].id for r in original_results}
        expanded_ids = {r[0].id for r in expanded_results}
        overlap = len(original_ids & expanded_ids)
        print(f"  Overlap: {overlap}/5 chunks")

    print("\n" + "=" * 80)


def main():
    """Run faithfulness investigation."""
    analyze_expansion_impact()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
