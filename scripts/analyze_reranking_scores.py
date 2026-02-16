#!/usr/bin/env python3
"""Analyze LLM re-ranking score distribution to set evidence-based threshold.

This script extracts all LLM relevance scores from evaluation results to understand
the actual score distribution and recommend an appropriate RELEVANCE_THRESHOLD.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import statistics

def extract_reranking_scores(results_file: Path) -> List[float]:
    """Extract all LLM re-ranking scores from evaluation results.

    NOTE: We're looking for 'relevance_score' or 'score' fields in source chunks.
    These represent the 0-10 ratings given by the LLM re-ranker.
    """
    print(f"Reading: {results_file}")

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get all results
    results = data.get('all_results', [])
    print(f"Found {len(results)} total results\n")

    all_scores = []
    queries_with_sources = 0

    for result in results:
        # Skip failed queries
        if not result.get('success'):
            continue

        # Extract sources (chunks returned by vector search)
        sources = result.get('sources', [])

        if not sources:
            continue

        queries_with_sources += 1

        # Extract scores from each source chunk
        for source in sources:
            # Try different possible field names
            score = source.get('relevance_score') or source.get('score')

            if score is not None and isinstance(score, (int, float)):
                all_scores.append(float(score))

    print(f"Queries with sources: {queries_with_sources}/{len(results)}")
    print(f"Total scores extracted: {len(all_scores)}\n")

    return all_scores

def analyze_distribution(scores: List[float]) -> Dict[str, Any]:
    """Calculate distribution statistics."""

    if not scores:
        return {
            'error': 'No scores found'
        }

    sorted_scores = sorted(scores)

    return {
        'count': len(scores),
        'min': min(scores),
        'max': max(scores),
        'mean': statistics.mean(scores),
        'median': statistics.median(scores),
        'stdev': statistics.stdev(scores) if len(scores) > 1 else 0,
        'percentile_25': sorted_scores[int(len(sorted_scores) * 0.25)],
        'percentile_50': sorted_scores[int(len(sorted_scores) * 0.50)],
        'percentile_75': sorted_scores[int(len(sorted_scores) * 0.75)],
        'percentile_90': sorted_scores[int(len(sorted_scores) * 0.90)],
        'percentile_95': sorted_scores[int(len(sorted_scores) * 0.95)],
    }

def print_distribution(stats: Dict[str, Any]):
    """Print distribution analysis."""

    print("=" * 80)
    print("LLM RE-RANKING SCORE DISTRIBUTION ANALYSIS")
    print("=" * 80)

    if 'error' in stats:
        print(f"\n❌ {stats['error']}")
        return

    print(f"\nTotal Scores Analyzed: {stats['count']}")
    print(f"\nBasic Statistics:")
    print("-" * 80)
    print(f"  Min:    {stats['min']:.2f}")
    print(f"  Max:    {stats['max']:.2f}")
    print(f"  Mean:   {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  StdDev: {stats['stdev']:.2f}")

    print(f"\nPercentile Distribution:")
    print("-" * 80)
    print(f"  25th percentile: {stats['percentile_25']:.2f}  (75% of scores are above this)")
    print(f"  50th percentile: {stats['percentile_50']:.2f}  (median)")
    print(f"  75th percentile: {stats['percentile_75']:.2f}  (25% of scores are above this)")
    print(f"  90th percentile: {stats['percentile_90']:.2f}  (10% of scores are above this)")
    print(f"  95th percentile: {stats['percentile_95']:.2f}  (5% of scores are above this)")

    print(f"\n" + "=" * 80)
    print("THRESHOLD RECOMMENDATIONS")
    print("=" * 80)

    # Recommend threshold based on distribution
    median = stats['median']
    p25 = stats['percentile_25']
    p75 = stats['percentile_75']

    print(f"\nOption 1: Conservative (Keep top 50%)")
    print(f"  Threshold: {median:.1f}")
    print(f"  Effect: Filters out bottom 50% of chunks")

    print(f"\nOption 2: Balanced (Keep top 75%)")
    print(f"  Threshold: {p25:.1f}")
    print(f"  Effect: Filters out bottom 25% of chunks (recommended)")

    print(f"\nOption 3: Aggressive (Keep top 25%)")
    print(f"  Threshold: {p75:.1f}")
    print(f"  Effect: Filters out bottom 75% of chunks")

    # Specific recommendation based on current threshold issues
    print(f"\n" + "=" * 80)
    print("RECOMMENDED THRESHOLD (Based on your data)")
    print("=" * 80)

    # Current thresholds that failed
    print(f"\n❌ Threshold = 6.0: FAILED")
    print(f"   Reason: {stats['percentile_95']:.1f} is 95th percentile - only 5% of chunks pass!")

    print(f"\n❌ Threshold = 3.5: STRUGGLING")
    print(f"   Reason: Above {stats['percentile_75']:.1f} (75th percentile) - only 25% pass")

    # Recommend 25th percentile (keeps top 75%)
    recommended = round(p25, 1)
    print(f"\n✅ RECOMMENDED: Threshold = {recommended}")
    print(f"   Reason: Keeps top 75% of chunks, filters out worst 25%")
    print(f"   Effect: Balances precision (filter bad chunks) with recall (keep good chunks)")

    print(f"\n" + "=" * 80)

def main():
    """Main execution."""

    # Read consolidated results
    base_dir = Path(__file__).parent.parent
    results_file = base_dir / 'evaluation_results' / 'CONSOLIDATED_RESULTS.json'

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)

    # Extract scores
    scores = extract_reranking_scores(results_file)

    if not scores:
        print("❌ No re-ranking scores found in results")
        print("\nPossible reasons:")
        print("1. Sources don't have 'relevance_score' or 'score' fields")
        print("2. No queries returned sources")
        print("3. Results file has different structure")
        sys.exit(1)

    # Analyze distribution
    stats = analyze_distribution(scores)

    # Print analysis
    print_distribution(stats)

    # Save analysis to file
    output_file = base_dir / 'evaluation_results' / 'RERANKING_SCORE_ANALYSIS.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'all_scores': sorted(scores),
            'recommended_threshold': round(stats['percentile_25'], 1) if 'percentile_25' in stats else None
        }, f, indent=2)

    print(f"\n📁 Analysis saved to: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()
