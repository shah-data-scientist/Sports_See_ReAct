"""
FILE: generate_phase_comparison_charts.py
STATUS: Active
RESPONSIBILITY: Generate comprehensive visualization charts for phase metric comparison
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

def load_phase_data():
    """Load all phase evaluation results."""
    eval_dir = Path("evaluation_results")

    phases = {}
    for phase_num in [6, 7, 8, 9]:
        file_path = eval_dir / f"ragas_phase{phase_num}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                phases[phase_num] = json.load(f)

    return phases

def create_output_dir():
    """Create output directory for charts."""
    output_dir = Path("evaluation_results/phase_comparison_charts")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def chart1_metrics_evolution(phases, output_dir):
    """Chart 1: Overall Metrics Evolution Across Phases."""
    fig, ax = plt.subplots(figsize=(12, 6))

    phase_nums = sorted(phases.keys())
    metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
    metric_labels = ['Faithfulness', 'Answer Relevancy', 'Context Precision', 'Context Recall']

    for i, metric in enumerate(metrics):
        values = [phases[p]['overall_scores'][metric] for p in phase_nums]
        ax.plot(phase_nums, values, marker='o', linewidth=2, markersize=8, label=metric_labels[i])

    # Add target line for faithfulness
    ax.axhline(y=0.65, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='Target (Faithfulness)')

    ax.set_xlabel('Phase', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Overall Metrics Evolution Across Phases', fontsize=14, fontweight='bold')
    ax.set_xticks(phase_nums)
    ax.set_xticklabels([f'Phase {p}' for p in phase_nums])
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_dir / '01_metrics_evolution.png')
    plt.close()
    print("[OK] Chart 1: Metrics Evolution saved")

def chart2_faithfulness_by_category(phases, output_dir):
    """Chart 2: Faithfulness by Category Across Phases."""
    fig, ax = plt.subplots(figsize=(12, 7))

    phase_nums = sorted(phases.keys())
    categories = ['simple', 'complex', 'noisy', 'conversational']
    category_labels = ['SIMPLE', 'COMPLEX', 'NOISY', 'CONVERSATIONAL']

    x = np.arange(len(categories))
    width = 0.2

    for i, phase in enumerate(phase_nums):
        # Get category results (handle both 'category_results' and 'category_scores' keys)
        category_data = phases[phase].get('category_results') or phases[phase].get('category_scores', [])
        cat_results = {cat['category']: cat.get('avg_faithfulness') or cat.get('faithfulness', 0)
                      for cat in category_data}
        values = [cat_results.get(cat, 0) for cat in categories]

        offset = (i - len(phase_nums)/2 + 0.5) * width
        ax.bar(x + offset, values, width, label=f'Phase {phase}')

    # Add target line
    ax.axhline(y=0.65, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='Target')

    ax.set_xlabel('Category', fontsize=12, fontweight='bold')
    ax.set_ylabel('Faithfulness Score', fontsize=12, fontweight='bold')
    ax.set_title('Faithfulness by Category Across Phases', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(category_labels)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_dir / '02_faithfulness_by_category.png')
    plt.close()
    print("[OK] Chart 2: Faithfulness by Category saved")

def chart3_phase9_radar(phases, output_dir):
    """Chart 3: Phase 9 Category Performance (Radar Chart)."""
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    categories = ['simple', 'complex', 'noisy', 'conversational']
    category_labels = ['SIMPLE', 'COMPLEX', 'NOISY', 'CONVERSATIONAL']

    # Get Phase 9 category results (handle both formats)
    category_data = phases[9].get('category_results') or phases[9].get('category_scores', [])
    cat_results = {cat['category']: cat.get('avg_faithfulness') or cat.get('faithfulness', 0)
                  for cat in category_data}
    values = [cat_results.get(cat, 0) for cat in categories]

    # Number of variables
    num_vars = len(categories)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # The plot is circular, so we need to "complete the loop"
    values += values[:1]
    angles += angles[:1]

    ax.plot(angles, values, 'o-', linewidth=2, label='Phase 9')
    ax.fill(angles, values, alpha=0.25)

    # Add target reference circle
    target_values = [0.65] * (num_vars + 1)
    ax.plot(angles, target_values, '--', linewidth=1.5, color='red', alpha=0.5, label='Target (0.65)')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(category_labels, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8'], fontsize=9)
    ax.set_title('Phase 9: Faithfulness by Category\n(Radar Chart)', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(output_dir / '03_phase9_radar.png', bbox_inches='tight')
    plt.close()
    print("[OK] Chart 3: Phase 9 Radar Chart saved")

def chart4_heatmap(phases, output_dir):
    """Chart 4: Phase Comparison Heatmap (All Metrics x All Phases)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    phase_nums = sorted(phases.keys())
    metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
    metric_labels = ['Faithfulness', 'Answer\nRelevancy', 'Context\nPrecision', 'Context\nRecall']

    # Build data matrix
    data = []
    for metric in metrics:
        row = [phases[p]['overall_scores'][metric] for p in phase_nums]
        data.append(row)

    # Create heatmap
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    # Set ticks
    ax.set_xticks(np.arange(len(phase_nums)))
    ax.set_yticks(np.arange(len(metrics)))
    ax.set_xticklabels([f'Phase {p}' for p in phase_nums])
    ax.set_yticklabels(metric_labels)

    # Add text annotations
    for i in range(len(metrics)):
        for j in range(len(phase_nums)):
            text = ax.text(j, i, f'{data[i][j]:.3f}',
                         ha="center", va="center", color="black", fontsize=10, fontweight='bold')

    ax.set_title('Phase Comparison Heatmap: All Metrics', fontsize=14, fontweight='bold')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Score', rotation=270, labelpad=20, fontsize=11)

    plt.tight_layout()
    plt.savefig(output_dir / '04_phase_heatmap.png')
    plt.close()
    print("[OK] Chart 4: Phase Heatmap saved")

def chart5_distance_from_target(phases, output_dir):
    """Chart 5: Distance from Target for Each Phase."""
    fig, ax = plt.subplots(figsize=(10, 6))

    phase_nums = sorted(phases.keys())
    target = 0.65

    # Calculate gaps
    gaps = []
    for p in phase_nums:
        faithfulness = phases[p]['overall_scores']['faithfulness']
        gap = ((faithfulness / target) - 1) * 100  # Percentage gap
        gaps.append(gap)

    # Create bar chart
    colors = ['green' if g >= 0 else 'red' for g in gaps]
    bars = ax.bar(range(len(phase_nums)), gaps, color=colors, alpha=0.7, edgecolor='black')

    # Add value labels on bars
    for i, (bar, gap) in enumerate(zip(bars, gaps)):
        height = bar.get_height()
        label_y = height + 1 if height >= 0 else height - 3
        ax.text(bar.get_x() + bar.get_width()/2., label_y,
               f'{gap:.1f}%',
               ha='center', va='bottom' if height >= 0 else 'top',
               fontsize=11, fontweight='bold')

    # Add target line at 0%
    ax.axhline(y=0, color='black', linestyle='-', linewidth=2, label='Target (0.65 faithfulness)')

    ax.set_xlabel('Phase', fontsize=12, fontweight='bold')
    ax.set_ylabel('Gap from Target (%)', fontsize=12, fontweight='bold')
    ax.set_title('Faithfulness: Distance from Target (0.65)', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(phase_nums)))
    ax.set_xticklabels([f'Phase {p}' for p in phase_nums])
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_dir / '05_distance_from_target.png')
    plt.close()
    print("[OK] Chart 5: Distance from Target saved")

def chart6_answer_relevancy_by_category(phases, output_dir):
    """Chart 6: Answer Relevancy by Category Across Phases."""
    fig, ax = plt.subplots(figsize=(12, 7))

    phase_nums = sorted(phases.keys())
    categories = ['simple', 'complex', 'noisy', 'conversational']
    category_labels = ['SIMPLE', 'COMPLEX', 'NOISY', 'CONVERSATIONAL']

    x = np.arange(len(categories))
    width = 0.2

    for i, phase in enumerate(phase_nums):
        # Get category results (handle both formats)
        category_data = phases[phase].get('category_results') or phases[phase].get('category_scores', [])
        cat_results = {cat['category']: cat.get('avg_answer_relevancy') or cat.get('answer_relevancy', 0)
                      for cat in category_data}
        values = [cat_results.get(cat, 0) for cat in categories]

        offset = (i - len(phase_nums)/2 + 0.5) * width
        ax.bar(x + offset, values, width, label=f'Phase {phase}')

    ax.set_xlabel('Category', fontsize=12, fontweight='bold')
    ax.set_ylabel('Answer Relevancy Score', fontsize=12, fontweight='bold')
    ax.set_title('Answer Relevancy by Category Across Phases', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(category_labels)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 0.5)

    plt.tight_layout()
    plt.savefig(output_dir / '06_answer_relevancy_by_category.png')
    plt.close()
    print("[OK] Chart 6: Answer Relevancy by Category saved")

def main():
    """Generate all comparison charts."""
    print("\n" + "="*60)
    print("  PHASE COMPARISON VISUALIZATION GENERATOR")
    print("="*60 + "\n")

    # Load data
    print("Loading phase evaluation data...")
    phases = load_phase_data()
    print(f"[OK] Loaded {len(phases)} phases: {sorted(phases.keys())}\n")

    # Create output directory
    output_dir = create_output_dir()
    print(f"[OK] Output directory: {output_dir}\n")

    # Generate charts
    print("Generating charts...")
    chart1_metrics_evolution(phases, output_dir)
    chart2_faithfulness_by_category(phases, output_dir)
    chart3_phase9_radar(phases, output_dir)
    chart4_heatmap(phases, output_dir)
    chart5_distance_from_target(phases, output_dir)
    chart6_answer_relevancy_by_category(phases, output_dir)

    print(f"\n{'='*60}")
    print(f"[OK] All charts saved to: {output_dir}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
