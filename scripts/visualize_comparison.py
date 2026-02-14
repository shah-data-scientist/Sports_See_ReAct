"""
FILE: visualize_comparison.py
STATUS: Active
RESPONSIBILITY: Generate comparison visualizations for Phase 5 vs Phase 7
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_results():
    """Load all evaluation results."""
    base_path = Path("evaluation_results")

    phase5_original = json.loads((base_path / "ragas_phase5_original.json").read_text(encoding="utf-8"))
    phase5_rerun = json.loads((base_path / "ragas_phase5.json").read_text(encoding="utf-8"))
    phase7 = json.loads((base_path / "ragas_phase7.json").read_text(encoding="utf-8"))

    return phase5_original, phase5_rerun, phase7


def plot_overall_metrics(p5_orig, p5_rerun, p7, output_path):
    """Create bar chart comparing overall metrics."""
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    metric_labels = ["Faithfulness", "Answer\nRelevancy", "Context\nPrecision", "Context\nRecall"]

    p5_orig_scores = [p5_orig["overall_scores"][m] for m in metrics]
    p5_rerun_scores = [p5_rerun["overall_scores"][m] for m in metrics]
    p7_scores = [p7["overall_scores"][m] for m in metrics]

    x = np.arange(len(metrics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    bars1 = ax.bar(x - width, p5_orig_scores, width, label="Phase 5 Original", color="#3498db", alpha=0.8)
    bars2 = ax.bar(x, p5_rerun_scores, width, label="Phase 5 Re-run", color="#2ecc71", alpha=0.8)
    bars3 = ax.bar(x + width, p7_scores, width, label="Phase 7 (Query Expansion)", color="#e74c3c", alpha=0.8)

    ax.set_xlabel("Metric", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title("RAGAS Metrics: Phase 5 vs Phase 7 Comparison", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.0)

    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {output_path}")
    plt.close()


def plot_category_faithfulness(p5_orig, p5_rerun, p7, output_path):
    """Create grouped bar chart for faithfulness by category."""
    categories = ["simple", "complex", "noisy", "conversational"]
    category_labels = ["Simple", "Complex", "Noisy", "Conversational"]

    def get_category_scores(data, metric):
        scores = []
        for cat in categories:
            cat_data = next((c for c in data["category_scores"] if c["category"] == cat), None)
            scores.append(cat_data[metric] if cat_data else 0)
        return scores

    p5_orig_scores = get_category_scores(p5_orig, "faithfulness")
    p5_rerun_scores = get_category_scores(p5_rerun, "faithfulness")
    p7_scores = get_category_scores(p7, "faithfulness")

    x = np.arange(len(categories))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    bars1 = ax.bar(x - width, p5_orig_scores, width, label="Phase 5 Original", color="#3498db", alpha=0.8)
    bars2 = ax.bar(x, p5_rerun_scores, width, label="Phase 5 Re-run", color="#2ecc71", alpha=0.8)
    bars3 = ax.bar(x + width, p7_scores, width, label="Phase 7", color="#e74c3c", alpha=0.8)

    ax.set_xlabel("Query Category", fontsize=12, fontweight="bold")
    ax.set_ylabel("Faithfulness Score", fontsize=12, fontweight="bold")
    ax.set_title("Faithfulness by Query Category: Shows Variance and Real Drop", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(category_labels)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.0)

    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {output_path}")
    plt.close()


def plot_variance_analysis(p5_orig, p5_rerun, output_path):
    """Create bar chart showing evaluation variance."""
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    metric_labels = ["Faithfulness", "Answer\nRelevancy", "Context\nPrecision", "Context\nRecall"]

    variances = []
    for metric in metrics:
        orig = p5_orig["overall_scores"][metric]
        rerun = p5_rerun["overall_scores"][metric]
        variance_pct = abs((rerun - orig) / orig * 100) if orig > 0 else 0
        variances.append(variance_pct)

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ['#2ecc71' if v < 10 else '#f39c12' if v < 20 else '#e74c3c' for v in variances]
    bars = ax.bar(metric_labels, variances, color=colors, alpha=0.8)

    ax.set_xlabel("Metric", fontsize=12, fontweight="bold")
    ax.set_ylabel("Variance (%)", fontsize=12, fontweight="bold")
    ax.set_title("RAGAS Evaluation Variance: Phase 5 Original vs Re-run", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    # Add threshold lines
    ax.axhline(10, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Low (<10%)')
    ax.axhline(20, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Moderate (<20%)')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 1,
               f'{height:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {output_path}")
    plt.close()


def plot_category_heatmap(p5_orig, p5_rerun, p7, output_path):
    """Create heatmap showing all metrics across categories."""
    categories = ["simple", "complex", "noisy", "conversational"]
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

    def build_matrix(data):
        matrix = []
        for cat in categories:
            cat_data = next((c for c in data["category_scores"] if c["category"] == cat), None)
            if cat_data:
                row = [cat_data[m] for m in metrics]
                matrix.append(row)
            else:
                matrix.append([0, 0, 0, 0])
        return np.array(matrix)

    p5_orig_matrix = build_matrix(p5_orig)
    p5_rerun_matrix = build_matrix(p5_rerun)
    p7_matrix = build_matrix(p7)

    # Calculate change from Phase 5 Re-run to Phase 7
    change_matrix = ((p7_matrix - p5_rerun_matrix) / p5_rerun_matrix) * 100

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))

    # Phase 5 Original
    im1 = axes[0].imshow(p5_orig_matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    axes[0].set_title("Phase 5 Original", fontsize=12, fontweight='bold')
    axes[0].set_xticks(range(len(metrics)))
    axes[0].set_xticklabels([m.replace('_', '\n') for m in metrics], fontsize=9)
    axes[0].set_yticks(range(len(categories)))
    axes[0].set_yticklabels([c.capitalize() for c in categories])

    # Phase 5 Re-run
    im2 = axes[1].imshow(p5_rerun_matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    axes[1].set_title("Phase 5 Re-run", fontsize=12, fontweight='bold')
    axes[1].set_xticks(range(len(metrics)))
    axes[1].set_xticklabels([m.replace('_', '\n') for m in metrics], fontsize=9)
    axes[1].set_yticks(range(len(categories)))
    axes[1].set_yticklabels([c.capitalize() for c in categories])

    # Phase 7
    im3 = axes[2].imshow(p7_matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    axes[2].set_title("Phase 7", fontsize=12, fontweight='bold')
    axes[2].set_xticks(range(len(metrics)))
    axes[2].set_xticklabels([m.replace('_', '\n') for m in metrics], fontsize=9)
    axes[2].set_yticks(range(len(categories)))
    axes[2].set_yticklabels([c.capitalize() for c in categories])

    # Change (P5 Re-run → P7)
    im4 = axes[3].imshow(change_matrix, cmap='RdYlGn_r', vmin=-50, vmax=50, aspect='auto')
    axes[3].set_title("P5→P7 Change (%)", fontsize=12, fontweight='bold')
    axes[3].set_xticks(range(len(metrics)))
    axes[3].set_xticklabels([m.replace('_', '\n') for m in metrics], fontsize=9)
    axes[3].set_yticks(range(len(categories)))
    axes[3].set_yticklabels([c.capitalize() for c in categories])

    # Add colorbars
    cbar1 = plt.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
    cbar2 = plt.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
    cbar3 = plt.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)
    cbar4 = plt.colorbar(im4, ax=axes[3], fraction=0.046, pad=0.04)

    # Add value annotations
    for ax, matrix in zip(axes[:3], [p5_orig_matrix, p5_rerun_matrix, p7_matrix]):
        for i in range(len(categories)):
            for j in range(len(metrics)):
                text = ax.text(j, i, f'{matrix[i, j]:.2f}', ha='center', va='center',
                              color='black' if matrix[i, j] > 0.5 else 'white', fontsize=8)

    for i in range(len(categories)):
        for j in range(len(metrics)):
            val = change_matrix[i, j]
            text = axes[3].text(j, i, f'{val:+.0f}%', ha='center', va='center',
                               color='black' if abs(val) < 25 else 'white', fontsize=8)

    plt.suptitle("RAGAS Metrics Heatmap: Category-Level Comparison", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {output_path}")
    plt.close()


def main():
    """Generate all comparison visualizations."""
    print("\n" + "=" * 60)
    print("  GENERATING COMPARISON VISUALIZATIONS")
    print("=" * 60 + "\n")

    # Load data
    print("Loading evaluation results...")
    p5_orig, p5_rerun, p7 = load_results()

    # Create output directory
    output_dir = Path("evaluation_results/visualizations")
    output_dir.mkdir(exist_ok=True, parents=True)

    # Generate plots
    print("\nGenerating visualizations...")

    plot_overall_metrics(p5_orig, p5_rerun, p7, output_dir / "overall_metrics_comparison.png")
    plot_category_faithfulness(p5_orig, p5_rerun, p7, output_dir / "faithfulness_by_category.png")
    plot_variance_analysis(p5_orig, p5_rerun, output_dir / "evaluation_variance.png")
    plot_category_heatmap(p5_orig, p5_rerun, p7, output_dir / "category_heatmap.png")

    print("\n" + "=" * 60)
    print(f"  All visualizations saved to: {output_dir}")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
