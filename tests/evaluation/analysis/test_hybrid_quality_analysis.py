"""
FILE: test_hybrid_quality_analysis.py
STATUS: Active
RESPONSIBILITY: Test hybrid quality analysis module
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu

Tests for src.evaluation.analysis.hybrid_quality_analysis module.
"""


def test_hybrid_quality_analysis_module_exists():
    """Test that hybrid_quality_analysis module can be imported."""
    from evaluation.analysis import hybrid_quality_analysis

    assert hybrid_quality_analysis is not None
