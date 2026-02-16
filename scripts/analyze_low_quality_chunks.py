#!/usr/bin/env python3
"""Analyze how LLM handles low-quality chunks.

This script extracts examples where chunks had low relevance scores
and shows what the LLM actually answered.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def analyze_low_quality_examples(results_file: Path, num_examples: int = 5):
    """Extract examples of queries with low-quality chunks."""

    print(f"Reading: {results_file}")

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data.get('all_results', [])
    print(f"Total results: {len(results)}\n")

    # Find examples where chunks exist (vector/hybrid queries)
    examples = []

    for result in results:
        if not result.get('success'):
            continue

        sources = result.get('sources', [])
        if not sources:
            continue

        # Check if this is a vector or hybrid query (has sources)
        if result.get('test_type') in ['vector', 'hybrid']:
            examples.append({
                'question': result.get('question'),
                'test_type': result.get('test_type'),
                'answer': result.get('answer'),
                'sources': sources[:3],  # Top 3 chunks
                'context_precision': result.get('ragas_metrics', {}).get('context_precision'),
                'context_relevancy': result.get('ragas_metrics', {}).get('context_relevancy'),
                'answer_correctness': result.get('ragas_metrics', {}).get('answer_correctness'),
            })

    # Sort by context_relevancy (lowest first to see worst cases)
    examples_sorted = sorted(
        [e for e in examples if e['context_relevancy'] is not None],
        key=lambda x: x['context_relevancy']
    )

    # Take first N examples (worst context relevancy)
    worst_examples = examples_sorted[:num_examples]

    print("=" * 100)
    print(f"TOP {num_examples} EXAMPLES: LOWEST CONTEXT RELEVANCY (Potential Hallucination Risk)")
    print("=" * 100)

    for i, example in enumerate(worst_examples, 1):
        print(f"\n{'='*100}")
        print(f"EXAMPLE {i}: Context Relevancy = {example['context_relevancy']:.3f}")
        print(f"{'='*100}")

        print(f"\n📝 QUESTION ({example['test_type'].upper()}):")
        print(f"   {example['question']}")

        print(f"\n📊 RAGAS SCORES:")
        print(f"   Context Precision:  {example['context_precision']:.3f}" if example['context_precision'] is not None else "   Context Precision:  N/A")
        print(f"   Context Relevancy:  {example['context_relevancy']:.3f}")
        print(f"   Answer Correctness: {example['answer_correctness']:.3f}")

        print(f"\n📚 TOP 3 CHUNKS RETRIEVED (Vector Similarity Scores):")
        for j, source in enumerate(example['sources'], 1):
            print(f"\n   Chunk {j} (Score: {source.get('score', 0):.2f}/100):")
            chunk_text = source.get('text', '')[:300]  # First 300 chars
            print(f"   {chunk_text}...")
            print(f"   Source: {source.get('source', 'Unknown')}")

        print(f"\n💬 FINAL LLM ANSWER:")
        answer_preview = example['answer'][:500]
        print(f"   {answer_preview}...")

        print(f"\n🔍 ANALYSIS:")
        # Analyze if answer seems hallucinated or appropriate
        if example['answer_correctness'] >= 0.8:
            print(f"   ✅ High answer correctness ({example['answer_correctness']:.3f}) - LLM handled low-quality chunks well")
        elif example['answer_correctness'] >= 0.6:
            print(f"   ⚠️  Moderate answer correctness ({example['answer_correctness']:.3f}) - Some issues but not severe")
        else:
            print(f"   ❌ Low answer correctness ({example['answer_correctness']:.3f}) - Potential hallucination!")

        if "I don't have" in example['answer'] or "cannot provide" in example['answer'] or "insufficient" in example['answer']:
            print(f"   ✅ LLM gracefully declined when chunks were irrelevant")
        elif example['context_relevancy'] < 0.3 and example['answer_correctness'] > 0.7:
            print(f"   ⚠️  LLM answered despite low relevancy - may be using general knowledge")

    # Also show some good examples (high context relevancy)
    print(f"\n\n{'='*100}")
    print(f"COMPARISON: TOP {min(2, len(examples_sorted))} EXAMPLES WITH HIGH CONTEXT RELEVANCY")
    print(f"{'='*100}")

    good_examples = sorted(
        [e for e in examples if e['context_relevancy'] is not None and e['context_relevancy'] > 0.7],
        key=lambda x: x['context_relevancy'],
        reverse=True
    )[:2]

    for i, example in enumerate(good_examples, 1):
        print(f"\n{'='*100}")
        print(f"GOOD EXAMPLE {i}: Context Relevancy = {example['context_relevancy']:.3f}")
        print(f"{'='*100}")

        print(f"\n📝 QUESTION:")
        print(f"   {example['question']}")

        print(f"\n📊 RAGAS SCORES:")
        print(f"   Context Relevancy:  {example['context_relevancy']:.3f}")
        print(f"   Answer Correctness: {example['answer_correctness']:.3f}")

        print(f"\n📚 TOP 3 CHUNKS (relevant):")
        for j, source in enumerate(example['sources'], 1):
            chunk_text = source.get('text', '')[:200]
            print(f"   Chunk {j} (Score: {source.get('score', 0):.2f}): {chunk_text}...")

        print(f"\n💬 ANSWER:")
        print(f"   {example['answer'][:300]}...")

def main():
    base_dir = Path(__file__).parent.parent
    results_file = base_dir / 'evaluation_results' / 'CONSOLIDATED_RESULTS.json'

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    analyze_low_quality_examples(results_file, num_examples=5)

    print(f"\n{'='*100}")
    print("KEY INSIGHTS:")
    print(f"{'='*100}")
    print("\n1. When context_relevancy is LOW (<0.3):")
    print("   - Check if LLM gracefully declines (\"I don't have enough information\")")
    print("   - Or if it answers using general knowledge (may not match retrieved chunks)")
    print("\n2. When answer_correctness is HIGH despite low relevancy:")
    print("   - LLM likely used its training data, not the chunks")
    print("   - This can be good (correct answer) or bad (not grounded in sources)")
    print("\n3. Risk of hallucination:")
    print("   - Look for low context_relevancy + low answer_correctness")
    print("   - These are cases where bad chunks led to bad answers")
    print(f"\n{'='*100}")

if __name__ == '__main__':
    main()
