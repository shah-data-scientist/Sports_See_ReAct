"""
FILE: test_run_hybrid_evaluation.py
STATUS: Active
RESPONSIBILITY: Test hybrid evaluation runner module
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu

Tests for src.evaluation.runners.run_hybrid_evaluation module.
"""


def test_run_hybrid_evaluation_module_exists():
    """Test that run_hybrid_evaluation module can be imported."""
    from evaluation.runners import run_hybrid_evaluation

    assert run_hybrid_evaluation is not None
