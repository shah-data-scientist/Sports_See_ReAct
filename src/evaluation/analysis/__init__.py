"""
FILE: __init__.py (analysis)
STATUS: Active
RESPONSIBILITY: Export unified analysis interface
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu
"""

from src.evaluation.analysis.quality_analysis import analyze_results

__all__ = ["analyze_results"]
