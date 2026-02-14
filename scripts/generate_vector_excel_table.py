"""
Generate Excel-ready CSV table for vector evaluation results.

Columns:
- Query
- Answer
- Ground Truth
- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall
"""
import json
import csv
from pathlib import Path

def generate_vector_table():
    """Generate CSV table with vector evaluation results and RAGAS metrics."""

    # Load vector evaluation results
    json_path = Path("evaluation_results/vector_evaluation_20260213_120447.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']
    print(f"Loaded {len(results)} vector evaluation results")

    # Prepare CSV output
    csv_path = Path("evaluation_results/vector_evaluation_table.csv")

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow([
            'Query',
            'Answer',
            'Ground Truth',
            'Faithfulness',
            'Answer Relevancy',
            'Context Precision',
            'Context Recall'
        ])

        # Write data rows
        for result in results:
            query = result.get('question', '')
            answer = result.get('response', '')
            ground_truth = result.get('ground_truth', '')

            ragas = result.get('ragas_metrics', {})
            faithfulness = ragas.get('faithfulness', 0)
            answer_relevancy = ragas.get('answer_relevancy', 0)
            context_precision = ragas.get('context_precision', 0)
            context_recall = ragas.get('context_recall', 0)

            writer.writerow([
                query,
                answer,
                ground_truth,
                round(faithfulness, 4),
                round(answer_relevancy, 4),
                round(context_precision, 4),
                round(context_recall, 4)
            ])

    print(f"\n✅ CSV table generated successfully!")
    print(f"📄 Output: {csv_path}")
    print(f"📊 Rows: {len(results)} (excluding header)")

    # Calculate summary statistics
    avg_faithfulness = sum(r.get('ragas_metrics', {}).get('faithfulness', 0) for r in results) / len(results)
    avg_answer_relevancy = sum(r.get('ragas_metrics', {}).get('answer_relevancy', 0) for r in results) / len(results)
    avg_context_precision = sum(r.get('ragas_metrics', {}).get('context_precision', 0) for r in results) / len(results)
    avg_context_recall = sum(r.get('ragas_metrics', {}).get('context_recall', 0) for r in results) / len(results)

    print("\n" + "="*80)
    print("RAGAS METRICS SUMMARY")
    print("="*80)
    print(f"Average Faithfulness:      {avg_faithfulness:.4f}")
    print(f"Average Answer Relevancy:  {avg_answer_relevancy:.4f}")
    print(f"Average Context Precision: {avg_context_precision:.4f}")
    print(f"Average Context Recall:    {avg_context_recall:.4f}")
    print("="*80)

    return csv_path

if __name__ == "__main__":
    generate_vector_table()
