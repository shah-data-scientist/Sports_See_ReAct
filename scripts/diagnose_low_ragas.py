"""
FILE: diagnose_low_ragas.py
STATUS: Active
RESPONSIBILITY: Diagnose why RAGAS Context Precision/Recall are so low
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Investigate the mismatch between gold contexts and actual vector store chunks.
"""

import io
import json
import pickle
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def diagnose():
    print("\n" + "="*80)
    print("  DIAGNOSING LOW RAGAS SCORES")
    print("="*80)

    # Load gold contexts
    gold_file = Path("evaluation_results/vector_gold_contexts.json")
    with open(gold_file, encoding="utf-8") as f:
        gold_data = json.load(f)

    # Load actual chunks
    chunks_file = Path("data/vector/document_chunks.pkl")
    with open(chunks_file, "rb") as f:
        chunks = pickle.load(f)

    print(f"\nGold Contexts: {len(gold_data)} test cases")
    print(f"Vector Store Chunks: {len(chunks)} total")

    # Chunks are dicts, not objects
    # Analyze Reddit chunks
    reddit_chunks = [c for c in chunks if "reddit" in c.get("metadata", {}).get("source", "").lower()]
    print(f"Reddit Chunks: {len(reddit_chunks)}")

    # Sample gold context
    if gold_data:
        sample_gold = gold_data[0]
        print(f"\n{'='*80}")
        print("SAMPLE GOLD CONTEXT:")
        print(f"{'='*80}")
        print(f"Question: {sample_gold['question']}")
        print(f"\nGold Contexts ({len(sample_gold['gold_contexts'])}):")
        for i, ctx in enumerate(sample_gold['gold_contexts'][:2], 1):
            print(f"\n  Context {i} (length {len(ctx)}):")
            print(f"  {ctx[:200]}...")

    # Sample actual chunk
    if reddit_chunks:
        sample_chunk = reddit_chunks[0]
        print(f"\n{'='*80}")
        print("SAMPLE ACTUAL REDDIT CHUNK:")
        print(f"{'='*80}")

        # Chunks are dicts
        text = sample_chunk.get('text', sample_chunk.get('content', ''))

        print(f"Chunk Text (length {len(text)}):")
        print(f"{text[:400]}...")

        print(f"\nMetadata:")
        for key, val in sorted(sample_chunk.get('metadata', {}).items()):
            print(f"  {key}: {val}")

    # Key diagnostic: Are gold contexts substring matches of actual chunks?
    print(f"\n{'='*80}")
    print("MATCHING ANALYSIS:")
    print(f"{'='*80}")

    all_chunk_texts = []
    for chunk in chunks:
        text = chunk.get('text', chunk.get('content', ''))
        all_chunk_texts.append(text.lower())

    # Check first 5 gold contexts
    for i, gold_item in enumerate(gold_data[:5], 1):
        print(f"\nTest Case {i}: {gold_item['question'][:60]}...")
        gold_contexts = gold_item.get('gold_contexts', [])

        if not gold_contexts:
            print("  ⚠️  No gold contexts")
            continue

        matches = 0
        for gold_ctx in gold_contexts:
            # Check if gold context substring appears in any chunk
            gold_lower = gold_ctx.lower()[:100]  # First 100 chars
            for chunk_text in all_chunk_texts:
                if gold_lower in chunk_text or chunk_text[:100] in gold_lower:
                    matches += 1
                    break

        print(f"  Gold Contexts: {len(gold_contexts)}")
        print(f"  Matches Found: {matches}")
        if matches == 0:
            print(f"  ❌ NO MATCHES - Gold contexts don't exist in vector store!")

if __name__ == "__main__":
    diagnose()
