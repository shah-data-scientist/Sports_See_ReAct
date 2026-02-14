"""
FILE: visualize_phases.py
STATUS: Active
RESPONSIBILITY: Generate comprehensive visualizations comparing RAGAS evaluation results across all phases
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import json
from pathlib import Path
from typing import Any

# Optional imports with graceful degradation
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("[WARNING] matplotlib/seaborn not installed. Charts will not be generated.")
    print("To enable visualizations, run: poetry add matplotlib seaborn numpy")


class PhaseVisualizer:
    """Generate visualizations comparing evaluation results across phases."""

    def __init__(self, output_dir: Path):
        """Initialize visualizer with output directory."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        self.categories = ["simple", "complex", "noisy", "conversational"]

        # Set consistent style if plotting available
        if PLOTTING_AVAILABLE:
            sns.set_style("whitegrid")
            sns.set_palette("husl")

    def load_results(self, results_dir: Path) -> dict[str, dict[str, Any] | None]:
        """Load all available evaluation results."""
        results = {}

        # Load baseline
        baseline_path = results_dir / "ragas_baseline.json"
        if baseline_path.exists():
            results["baseline"] = json.loads(baseline_path.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"Baseline results not found: {baseline_path}")

        # Load phase results
        for phase_name, filename in [
            ("phase2", "ragas_phase2.json"),
            ("phase4", "ragas_phase4.json"),
            ("phase5", "ragas_phase5_extended.json"),
        ]:
            phase_path = results_dir / filename
            if phase_path.exists():
                results[phase_name] = json.loads(phase_path.read_text(encoding="utf-8"))
            else:
                results[phase_name] = None
                print(f"[INFO] {phase_name} results not found (skipping)")

        return results

    def create_line_chart(self, results: dict[str, dict[str, Any] | None]) -> None:
        """Create line chart showing metric evolution across phases."""
        if not PLOTTING_AVAILABLE:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Metric Evolution Across Development Phases", fontsize=16, fontweight="bold")

        phases = ["baseline", "phase2", "phase4", "phase5"]
        phase_labels = ["Baseline", "Phase 2\n(SQL)", "Phase 4\n(Prompt+Class)", "Phase 5\n(Extended)"]

        for idx, metric in enumerate(self.metrics):
            ax = axes[idx // 2, idx % 2]

            # Collect data points
            values = []
            labels = []
            for phase, label in zip(phases, phase_labels):
                if results.get(phase) and results[phase] is not None:
                    val = results[phase]["overall_scores"].get(metric, 0) or 0
                    values.append(val)
                    labels.append(label)

            if len(values) >= 2:
                # Plot line
                ax.plot(range(len(values)), values, marker='o', linewidth=2, markersize=8)
                ax.set_xticks(range(len(values)))
                ax.set_xticklabels(labels, fontsize=9)
                ax.set_ylabel("Score", fontsize=10)
                ax.set_title(metric.replace("_", " ").title(), fontsize=12, fontweight="bold")
                ax.set_ylim(0, 1.0)
                ax.grid(True, alpha=0.3)

                # Add value labels
                for i, v in enumerate(values):
                    ax.text(i, v + 0.03, f"{v:.3f}", ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        output_path = self.output_dir / "01_metric_evolution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[SAVED] Line chart: {output_path}")

    def create_bar_chart(self, results: dict[str, dict[str, Any] | None]) -> None:
        """Create grouped bar chart for category performance by phase."""
        if not PLOTTING_AVAILABLE:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Category Performance by Phase", fontsize=16, fontweight="bold")

        phases = ["baseline", "phase2", "phase4", "phase5"]
        phase_labels = ["Baseline", "Phase 2", "Phase 4", "Phase 5"]

        for idx, metric in enumerate(self.metrics):
            ax = axes[idx // 2, idx % 2]

            # Prepare data
            category_data = {cat: [] for cat in self.categories}
            available_phases = []

            for phase in phases:
                if results.get(phase) and results[phase] is not None:
                    available_phases.append(phase)
                    for cat in self.categories:
                        cat_scores = results[phase].get("category_scores", [])
                        cat_data = next((c for c in cat_scores if c["category"] == cat), None)
                        val = cat_data.get(metric, 0) if cat_data else 0
                        category_data[cat].append(val or 0)

            # Plot grouped bars
            x = np.arange(len(self.categories))
            width = 0.2
            offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]

            for i, phase in enumerate(available_phases):
                phase_idx = phases.index(phase)
                values = [category_data[cat][i] for cat in self.categories]
                bars = ax.bar(x + offsets[phase_idx], values, width,
                            label=phase_labels[phase_idx], alpha=0.8)

                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    if height > 0.05:  # Only label if significant
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.2f}', ha='center', va='bottom', fontsize=7)

            ax.set_ylabel("Score", fontsize=10)
            ax.set_title(metric.replace("_", " ").title(), fontsize=12, fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels([c.capitalize() for c in self.categories], fontsize=9)
            ax.set_ylim(0, 1.0)
            ax.legend(fontsize=8, loc='upper right')
            ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        output_path = self.output_dir / "02_category_performance.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[SAVED] Bar chart: {output_path}")

    def create_radar_chart(self, results: dict[str, dict[str, Any] | None]) -> None:
        """Create radar chart comparing overall metrics across phases."""
        if not PLOTTING_AVAILABLE:
            return

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        fig.suptitle("Overall Metrics Comparison (Radar)", fontsize=16, fontweight="bold", y=0.98)

        # Setup angles for each metric
        angles = np.linspace(0, 2 * np.pi, len(self.metrics), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle

        metric_labels = [m.replace("_", " ").title() for m in self.metrics]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=11)
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
        ax.grid(True)

        # Plot each phase
        phases = ["baseline", "phase2", "phase4", "phase5"]
        phase_labels = ["Baseline", "Phase 2 (SQL)", "Phase 4 (Prompt+Class)", "Phase 5 (Extended)"]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

        for phase, label, color in zip(phases, phase_labels, colors):
            if results.get(phase) and results[phase] is not None:
                values = []
                for metric in self.metrics:
                    val = results[phase]["overall_scores"].get(metric, 0) or 0
                    values.append(val)
                values += values[:1]  # Complete the circle

                ax.plot(angles, values, 'o-', linewidth=2, label=label, color=color)
                ax.fill(angles, values, alpha=0.15, color=color)

        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

        plt.tight_layout()
        output_path = self.output_dir / "03_radar_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[SAVED] Radar chart: {output_path}")

    def create_heatmap(self, results: dict[str, dict[str, Any] | None]) -> None:
        """Create heatmap showing metric x phase x category."""
        if not PLOTTING_AVAILABLE:
            return

        phases = ["baseline", "phase2", "phase4", "phase5"]
        phase_labels = ["Baseline", "Phase 2", "Phase 4", "Phase 5"]

        # Create one heatmap per metric
        for metric in self.metrics:
            fig, ax = plt.subplots(figsize=(12, 6))

            # Build data matrix: rows=phases, cols=categories
            data_matrix = []
            available_phase_labels = []

            for phase in phases:
                if results.get(phase) and results[phase] is not None:
                    row = []
                    for cat in self.categories:
                        cat_scores = results[phase].get("category_scores", [])
                        cat_data = next((c for c in cat_scores if c["category"] == cat), None)
                        val = cat_data.get(metric, 0) if cat_data else 0
                        row.append(val or 0)
                    data_matrix.append(row)
                    available_phase_labels.append(phase_labels[phases.index(phase)])

            if len(data_matrix) > 0:
                data_array = np.array(data_matrix)

                # Create heatmap
                sns.heatmap(data_array, annot=True, fmt='.3f', cmap='YlOrRd',
                          xticklabels=[c.capitalize() for c in self.categories],
                          yticklabels=available_phase_labels,
                          vmin=0, vmax=1.0, cbar_kws={'label': 'Score'},
                          linewidths=0.5, ax=ax)

                ax.set_title(f"{metric.replace('_', ' ').title()} - Heatmap by Phase & Category",
                           fontsize=14, fontweight="bold", pad=20)
                ax.set_xlabel("Query Category", fontsize=12)
                ax.set_ylabel("Phase", fontsize=12)

                plt.tight_layout()
                output_path = self.output_dir / f"04_heatmap_{metric}.png"
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"[SAVED] Heatmap ({metric}): {output_path}")

    def create_improvement_chart(self, results: dict[str, dict[str, Any] | None]) -> None:
        """Create chart showing percentage improvements from baseline."""
        if not PLOTTING_AVAILABLE:
            return

        fig, ax = plt.subplots(figsize=(12, 8))
        fig.suptitle("Percentage Improvement from Baseline", fontsize=16, fontweight="bold")

        baseline = results["baseline"]["overall_scores"]
        phases = ["phase2", "phase4", "phase5"]
        phase_labels = ["Phase 2", "Phase 4", "Phase 5"]

        # Calculate improvements
        improvements = {metric: [] for metric in self.metrics}
        available_phases = []

        for phase in phases:
            if results.get(phase) and results[phase] is not None:
                available_phases.append(phase_labels[phases.index(phase)])
                for metric in self.metrics:
                    base_val = baseline.get(metric, 0) or 0
                    curr_val = results[phase]["overall_scores"].get(metric, 0) or 0

                    if base_val > 0:
                        pct_change = ((curr_val - base_val) / base_val) * 100
                    else:
                        pct_change = 0

                    improvements[metric].append(pct_change)

        # Plot grouped bars
        x = np.arange(len(self.metrics))
        width = 0.25

        for i, phase_label in enumerate(available_phases):
            values = [improvements[metric][i] for metric in self.metrics]
            offset = (i - len(available_phases)/2 + 0.5) * width
            bars = ax.bar(x + offset, values, width, label=phase_label, alpha=0.8)

            # Add value labels
            for bar in bars:
                height = bar.get_height()
                label_y = height + 1 if height > 0 else height - 2
                ax.text(bar.get_x() + bar.get_width()/2., label_y,
                       f'{height:+.1f}%', ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=9, fontweight='bold')

        ax.set_ylabel("% Change from Baseline", fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace("_", " ").title() for m in self.metrics], fontsize=10)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        output_path = self.output_dir / "05_improvement_from_baseline.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[SAVED] Improvement chart: {output_path}")

    def generate_markdown_report(self, results: dict[str, dict[str, Any] | None]) -> None:
        """Generate markdown report with embedded charts."""
        report_lines = []

        # Header
        report_lines.extend([
            "# Phase Comparison Visualization Report",
            "",
            f"**Generated:** {results['baseline'].get('timestamp', 'N/A')}",
            "",
            "## Executive Summary",
            "",
            "This report presents a comprehensive visual comparison of RAGAS evaluation metrics ",
            "across all development phases of the NBA RAG chatbot system.",
            "",
        ])

        # Phase summary table
        report_lines.extend([
            "## Available Phases",
            "",
            "| Phase | Description | Status | Sample Count |",
            "|-------|-------------|--------|--------------|",
        ])

        phase_info = [
            ("Baseline", "Vector search only (FAISS)", "baseline"),
            ("Phase 2", "SQL integration", "phase2"),
            ("Phase 4", "Prompt engineering + classification", "phase4"),
            ("Phase 5", "Extended test cases", "phase5"),
        ]

        for name, desc, key in phase_info:
            if results.get(key) and results[key] is not None:
                count = results[key].get("sample_count", "N/A")
                status = "✓ Complete"
            else:
                count = "N/A"
                status = "⏳ Pending"
            report_lines.append(f"| {name} | {desc} | {status} | {count} |")

        report_lines.append("")

        # Overall scores comparison
        report_lines.extend([
            "## Overall Scores Comparison",
            "",
            "| Metric | Baseline | Phase 2 | Phase 4 | Phase 5 |",
            "|--------|----------|---------|---------|---------|",
        ])

        for metric in self.metrics:
            row = [metric.replace("_", " ").title()]
            for phase in ["baseline", "phase2", "phase4", "phase5"]:
                if results.get(phase) and results[phase] is not None:
                    val = results[phase]["overall_scores"].get(metric, 0) or 0
                    row.append(f"{val:.3f}")
                else:
                    row.append("N/A")
            report_lines.append(f"| {' | '.join(row)} |")

        report_lines.append("")

        # Visualizations section
        report_lines.extend([
            "## Visualizations",
            "",
        ])

        if PLOTTING_AVAILABLE:
            charts = [
                ("01_metric_evolution.png", "Metric Evolution Across Phases",
                 "Line chart showing how each metric evolves from baseline through all phases."),
                ("02_category_performance.png", "Category Performance by Phase",
                 "Grouped bar chart comparing performance across query categories (simple, complex, noisy, conversational)."),
                ("03_radar_comparison.png", "Overall Metrics Radar Comparison",
                 "Radar chart providing a holistic view of all metrics across phases."),
                ("04_heatmap_faithfulness.png", "Faithfulness Heatmap",
                 "Heatmap showing faithfulness scores by phase and category."),
                ("05_improvement_from_baseline.png", "Percentage Improvement",
                 "Bar chart showing percentage changes relative to baseline."),
            ]

            for filename, title, description in charts:
                report_lines.extend([
                    f"### {title}",
                    "",
                    description,
                    "",
                    f"![{title}](charts/{filename})",
                    "",
                ])
        else:
            report_lines.extend([
                "> **Note:** Visualizations not generated. Install matplotlib and seaborn to enable:",
                "> ```bash",
                "> poetry add matplotlib seaborn numpy",
                "> ```",
                "",
            ])

        # Key findings
        report_lines.extend([
            "## Key Findings",
            "",
        ])

        # Calculate improvements for key findings
        if results.get("phase4"):
            baseline_scores = results["baseline"]["overall_scores"]
            phase4_scores = results["phase4"]["overall_scores"]

            report_lines.append("### Phase 4 Improvements (vs Baseline)")
            report_lines.append("")

            for metric in self.metrics:
                base = baseline_scores.get(metric, 0) or 0
                curr = phase4_scores.get(metric, 0) or 0
                change = curr - base
                pct = (change / base * 100) if base > 0 else 0

                symbol = "↑" if change > 0 else "↓" if change < 0 else "→"
                report_lines.append(
                    f"- **{metric.replace('_', ' ').title()}**: "
                    f"{base:.3f} → {curr:.3f} ({symbol} {pct:+.1f}%)"
                )

            report_lines.append("")

        # Recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "### High Priority",
            "",
            "1. **Address Answer Relevancy**: Remains critically low across all phases",
            "2. **Improve Faithfulness**: Current scores indicate significant hallucination risk",
            "3. **Optimize Complex Query Handling**: Consistently lowest performing category",
            "",
            "### Future Work",
            "",
            "1. Implement ML-based query classification",
            "2. Add SQL fallback mechanisms",
            "3. Expand test case coverage for edge cases",
            "4. Integrate user feedback into evaluation metrics",
            "",
        ])

        # Footer
        report_lines.extend([
            "---",
            "",
            "*Generated by `scripts/visualize_phases.py`*",
            "",
        ])

        # Write report
        report_path = self.output_dir.parent / "PHASE_COMPARISON_REPORT.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")
        print(f"[SAVED] Markdown report: {report_path}")

    def generate_all(self, results_dir: Path) -> None:
        """Generate all visualizations and report."""
        print("\n" + "=" * 80)
        print("  PHASE VISUALIZATION GENERATOR")
        print("=" * 80)

        # Load results
        print("\n[1/7] Loading evaluation results...")
        results = self.load_results(results_dir)

        available = [k for k, v in results.items() if v is not None]
        print(f"      Available: {', '.join(available)}")

        if not PLOTTING_AVAILABLE:
            print("\n[WARNING] Plotting libraries not available. Only markdown report will be generated.")
            print("          Install with: poetry add matplotlib seaborn numpy")

        # Generate visualizations
        if PLOTTING_AVAILABLE:
            print("\n[2/7] Creating line chart (metric evolution)...")
            self.create_line_chart(results)

            print("\n[3/7] Creating bar chart (category performance)...")
            self.create_bar_chart(results)

            print("\n[4/7] Creating radar chart (overall comparison)...")
            self.create_radar_chart(results)

            print("\n[5/7] Creating heatmaps (metric x phase x category)...")
            self.create_heatmap(results)

            print("\n[6/7] Creating improvement chart...")
            self.create_improvement_chart(results)
        else:
            print("\n[2-6/7] Skipping chart generation (libraries not available)")

        # Generate markdown report
        print("\n[7/7] Generating markdown report...")
        self.generate_markdown_report(results)

        print("\n" + "=" * 80)
        print("  VISUALIZATION COMPLETE")
        print("=" * 80)
        print(f"\nOutput directory: {self.output_dir.absolute()}")
        print(f"Report: {(self.output_dir.parent / 'PHASE_COMPARISON_REPORT.md').absolute()}")
        print()


def main() -> int:
    """Main entry point."""
    try:
        # Setup paths
        project_root = Path(__file__).parent.parent
        results_dir = project_root / "evaluation_results"
        charts_dir = results_dir / "charts"

        # Create visualizer
        visualizer = PhaseVisualizer(charts_dir)

        # Generate all visualizations
        visualizer.generate_all(results_dir)

        return 0

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("\nEnsure baseline evaluation exists:")
        print("  evaluation_results/ragas_baseline.json")
        return 1

    except Exception as e:
        print(f"\n[ERROR] Visualization generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
