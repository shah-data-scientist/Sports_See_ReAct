"""
FILE: test_vector_quality_analysis.py
STATUS: Active
RESPONSIBILITY: Tests for vector quality analysis functions
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu

Tests all 5 analysis functions with various scenarios.
"""

import pytest

from evaluation.analysis.vector_quality_analysis import (
    analyze_category_performance,
    analyze_ragas_metrics,
    analyze_response_patterns,
    analyze_retrieval_performance,
    analyze_source_quality,
)


class TestRAGASMetricsAnalysis:
    """Tests for RAGAS metrics analysis."""

    def test_analyze_ragas_metrics_basic(self):
        """Test RAGAS metrics analysis with basic data."""
        results = [
            {
                "success": True,
                "ragas_metrics": {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.85,
                    "context_precision": 0.8,
                    "context_recall": 0.75
                },
                "category": "simple"
            },
            {
                "success": True,
                "ragas_metrics": {
                    "faithfulness": 0.7,
                    "answer_relevancy": 0.65,
                    "context_precision": 0.6,
                    "context_recall": 0.55
                },
                "category": "complex"
            }
        ]

        analysis = analyze_ragas_metrics(results)

        assert "overall" in analysis
        assert "by_category" in analysis
        assert "distributions" in analysis
        assert "low_scoring_queries" in analysis

        # Check overall averages
        assert analysis["overall"]["avg_faithfulness"] == pytest.approx(0.8, abs=0.01)
        assert analysis["overall"]["avg_answer_relevancy"] == pytest.approx(0.75, abs=0.01)

    def test_analyze_ragas_metrics_empty_results(self):
        """Test RAGAS metrics with empty results."""
        analysis = analyze_ragas_metrics([])

        assert analysis["overall"] == {}
        assert analysis["by_category"] == {}
        assert analysis["low_scoring_queries"] == []

    def test_analyze_ragas_metrics_no_ragas_data(self):
        """Test RAGAS metrics when no results have RAGAS data."""
        results = [
            {"success": True, "category": "simple"},  # No ragas_metrics
            {"success": False}
        ]

        analysis = analyze_ragas_metrics(results)

        assert analysis["overall"]["avg_faithfulness"] is None

    def test_analyze_ragas_metrics_by_category(self):
        """Test category breakdown in RAGAS analysis."""
        results = [
            {
                "success": True,
                "ragas_metrics": {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.9,
                    "context_precision": 0.9,
                    "context_recall": 0.9
                },
                "category": "simple"
            },
            {
                "success": True,
                "ragas_metrics": {
                    "faithfulness": 0.5,
                    "answer_relevancy": 0.5,
                    "context_precision": 0.5,
                    "context_recall": 0.5
                },
                "category": "complex"
            }
        ]

        analysis = analyze_ragas_metrics(results)

        assert "simple" in analysis["by_category"]
        assert "complex" in analysis["by_category"]
        assert analysis["by_category"]["simple"]["avg_faithfulness"] == pytest.approx(0.9)
        assert analysis["by_category"]["complex"]["avg_faithfulness"] == pytest.approx(0.5)

    def test_analyze_ragas_metrics_low_scoring_detection(self):
        """Test detection of low-scoring queries (< 0.7)."""
        results = [
            {
                "success": True,
                "question": "Low scoring query",
                "category": "noisy",
                "ragas_metrics": {
                    "faithfulness": 0.5,
                    "answer_relevancy": 0.6,
                    "context_precision": 0.55,
                    "context_recall": 0.65
                }
            }
        ]

        analysis = analyze_ragas_metrics(results)

        assert len(analysis["low_scoring_queries"]) == 1
        assert analysis["low_scoring_queries"][0]["min_score"] < 0.7


class TestSourceQualityAnalysis:
    """Tests for source quality analysis."""

    def test_analyze_source_quality_basic(self):
        """Test source quality analysis with basic data."""
        results = [
            {
                "success": True,
                "sources": [
                    {"source": "doc1.pdf", "score": 85},
                    {"source": "doc2.pdf", "score": 75}
                ]
            },
            {
                "success": True,
                "sources": [
                    {"source": "doc1.pdf", "score": 90}
                ]
            }
        ]

        analysis = analyze_source_quality(results)

        assert analysis["retrieval_stats"]["avg_sources_per_query"] == 1.5
        assert analysis["retrieval_stats"]["total_unique_sources"] == 2
        assert analysis["empty_retrievals"] == 0

    def test_analyze_source_quality_empty_results(self):
        """Test source quality with empty results."""
        analysis = analyze_source_quality([])

        assert "retrieval_stats" in analysis
        assert "source_diversity" in analysis
        assert analysis["empty_retrievals"] == 0

    def test_analyze_source_quality_empty_retrievals(self):
        """Test detection of empty retrievals."""
        results = [
            {"success": True, "sources": []},
            {"success": True, "sources": []},
            {"success": True, "sources": [{"source": "doc1.pdf", "score": 80}]}
        ]

        analysis = analyze_source_quality(results)

        assert analysis["empty_retrievals"] == 2

    def test_analyze_source_quality_score_distribution(self):
        """Test score distribution calculation."""
        results = [
            {
                "success": True,
                "sources": [
                    {"source": "doc1", "score": 95},  # 0.9-1.0 range
                    {"source": "doc2", "score": 45},  # 0.4-0.5 range
                    {"source": "doc3", "score": 65}   # 0.6-0.7 range
                ]
            }
        ]

        analysis = analyze_source_quality(results)

        score_dist = analysis["score_analysis"]["score_distribution"]
        assert score_dist["0.9-1.0"] == 1
        assert score_dist["0.4-0.5"] == 1
        assert score_dist["0.6-0.7"] == 1

    def test_analyze_source_quality_top_sources(self):
        """Test top sources ranking."""
        results = [
            {"success": True, "sources": [{"source": "popular.pdf", "score": 80}]},
            {"success": True, "sources": [{"source": "popular.pdf", "score": 85}]},
            {"success": True, "sources": [{"source": "rare.pdf", "score": 70}]}
        ]

        analysis = analyze_source_quality(results)

        top_sources = analysis["source_diversity"]["top_sources"]
        assert len(top_sources) >= 2
        assert top_sources[0]["source"] == "popular.pdf"
        assert top_sources[0]["count"] == 2


class TestResponsePatternsAnalysis:
    """Tests for response patterns analysis."""

    def test_analyze_response_patterns_basic(self):
        """Test response pattern analysis with basic data."""
        results = [
            {
                "success": True,
                "response": "This is a medium length response that should fall in the short-to-medium category based on character count."
            },
            {
                "success": True,
                "response": "Short response."
            }
        ]

        analysis = analyze_response_patterns(results)

        assert "response_length" in analysis
        assert "completeness" in analysis
        assert "citation_patterns" in analysis
        assert "confidence_indicators" in analysis

    def test_analyze_response_patterns_empty_results(self):
        """Test response patterns with empty results."""
        analysis = analyze_response_patterns([])

        assert "response_length" in analysis
        assert "completeness" in analysis
        assert "citation_patterns" in analysis
        assert "confidence_indicators" in analysis

    def test_analyze_response_patterns_length_distribution(self):
        """Test response length distribution."""
        results = [
            {"success": True, "response": "a" * 50},   # very_short
            {"success": True, "response": "a" * 150},  # short
            {"success": True, "response": "a" * 300},  # medium
            {"success": True, "response": "a" * 500}   # long
        ]

        analysis = analyze_response_patterns(results)

        dist = analysis["response_length"]["distribution"]
        assert dist["very_short"] == 1
        assert dist["short"] == 1
        assert dist["medium"] == 1
        assert dist["long"] == 1

    def test_analyze_response_patterns_completeness(self):
        """Test completeness detection."""
        results = [
            {"success": True, "response": "Complete answer with details."},
            {"success": True, "response": "I don't know the answer to this question."},
            {"success": True, "response": "This is partially correct but limited information."}
        ]

        analysis = analyze_response_patterns(results)

        completeness = analysis["completeness"]
        assert completeness["declined_answers"] == 1
        assert completeness["incomplete_answers"] == 1
        assert completeness["complete_answers"] == 1

    def test_analyze_response_patterns_citation_detection(self):
        """Test citation pattern detection."""
        results = [
            {"success": True, "response": "According to the source document, the answer is X."},
            {"success": True, "response": "Based on the data, we can conclude Y."},
            {"success": True, "response": "No citation in this response."}
        ]

        analysis = analyze_response_patterns(results)

        citations = analysis["citation_patterns"]
        assert citations["responses_with_citations"] >= 2

    def test_analyze_response_patterns_hedging_detection(self):
        """Test hedging language detection."""
        results = [
            {"success": True, "response": "This might be correct, possibly around 50%."},
            {"success": True, "response": "The answer is definitely 42."},
        ]

        analysis = analyze_response_patterns(results)

        confidence = analysis["confidence_indicators"]
        assert confidence["hedging_count"] == 1
        assert confidence["confident_count"] == 1


class TestRetrievalPerformanceAnalysis:
    """Tests for retrieval performance analysis."""

    def test_analyze_retrieval_performance_basic(self):
        """Test retrieval performance analysis with basic data."""
        results = [
            {
                "success": True,
                "sources": [
                    {"score": 85},
                    {"score": 75}
                ],
                "processing_time_ms": 1000
            }
        ]

        analysis = analyze_retrieval_performance(results)

        assert "performance_metrics" in analysis
        assert "k_value_analysis" in analysis
        assert "score_thresholds" in analysis
        assert "by_source_type" in analysis

    def test_analyze_retrieval_performance_empty_results(self):
        """Test retrieval performance with empty results."""
        analysis = analyze_retrieval_performance([])

        assert "performance_metrics" in analysis
        assert "k_value_analysis" in analysis
        assert "score_thresholds" in analysis
        assert "by_source_type" in analysis

    def test_analyze_retrieval_performance_k_value_analysis(self):
        """Test K-value analysis."""
        results = [
            {"success": True, "sources": [{"score": 80}] * 5},  # Exactly K=5
            {"success": True, "sources": [{"score": 80}] * 3},  # Below K
            {"success": True, "sources": [{"score": 80}] * 2}   # Below K
        ]

        analysis = analyze_retrieval_performance(results)

        k_analysis = analysis["k_value_analysis"]
        assert k_analysis["configured_k"] == 5
        assert k_analysis["queries_below_k"] == 2

    def test_analyze_retrieval_performance_score_thresholds(self):
        """Test score threshold categorization."""
        results = [
            {
                "success": True,
                "sources": [
                    {"score": 90},  # above 0.8
                    {"score": 70},  # 0.6-0.8
                    {"score": 50}   # below 0.6
                ]
            }
        ]

        analysis = analyze_retrieval_performance(results)

        thresholds = analysis["score_thresholds"]
        assert thresholds["above_0.8"] == 1
        assert thresholds["0.6_to_0.8"] == 1
        assert thresholds["below_0.6"] == 1

    def test_analyze_retrieval_performance_by_source_type(self):
        """Test performance breakdown by source type."""
        results = [
            {
                "success": True,
                "sources": [
                    {"source": "doc.pdf", "score": 85},
                    {"source": "reddit_post.txt", "score": 75}
                ]
            }
        ]

        analysis = analyze_retrieval_performance(results)

        by_type = analysis["by_source_type"]
        assert "pdf" in by_type
        assert "reddit" in by_type


class TestCategoryPerformanceAnalysis:
    """Tests for category performance analysis."""

    def test_analyze_category_performance_basic(self):
        """Test category performance analysis with basic data."""
        results = [
            {
                "success": True,
                "category": "simple",
                "sources": [{"score": 90}],
                "ragas_metrics": {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.85
                }
            },
            {
                "success": True,
                "category": "complex",
                "sources": [{"score": 70}],
                "ragas_metrics": {
                    "faithfulness": 0.7,
                    "answer_relevancy": 0.65
                }
            }
        ]

        analysis = analyze_category_performance(results)

        assert "category_breakdown" in analysis
        assert "comparative_analysis" in analysis
        assert "recommendations" in analysis

    def test_analyze_category_performance_empty_results(self):
        """Test category performance with empty results."""
        analysis = analyze_category_performance([])

        assert analysis["category_breakdown"] == {}
        assert analysis["recommendations"] == []

    def test_analyze_category_performance_breakdown(self):
        """Test category breakdown calculation."""
        results = [
            {
                "success": True,
                "category": "simple",
                "sources": [{"score": 90}],
                "ragas_metrics": {"faithfulness": 0.95, "answer_relevancy": 0.9}
            },
            {
                "success": True,
                "category": "simple",
                "sources": [{"score": 85}],
                "ragas_metrics": {"faithfulness": 0.85, "answer_relevancy": 0.8}
            }
        ]

        analysis = analyze_category_performance(results)

        breakdown = analysis["category_breakdown"]
        assert "simple" in breakdown
        assert breakdown["simple"]["count"] == 2
        assert breakdown["simple"]["success_rate"] == 1.0
        assert breakdown["simple"]["avg_faithfulness"] == pytest.approx(0.9, abs=0.01)

    def test_analyze_category_performance_comparative_analysis(self):
        """Test comparative analysis between categories."""
        results = [
            {
                "success": True,
                "category": "simple",
                "sources": [],
                "ragas_metrics": {"faithfulness": 0.95, "answer_relevancy": 0.9}
            },
            {
                "success": True,
                "category": "complex",
                "sources": [],
                "ragas_metrics": {"faithfulness": 0.65, "answer_relevancy": 0.6}
            }
        ]

        analysis = analyze_category_performance(results)

        comparative = analysis["comparative_analysis"]
        assert comparative["best_category"] == "simple"
        assert comparative["worst_category"] == "complex"
        assert comparative["largest_gap"]["gap"] > 0

    def test_analyze_category_performance_recommendations(self):
        """Test recommendation generation."""
        results = [
            {
                "success": False,
                "category": "noisy",
                "sources": []
            },
            {
                "success": False,
                "category": "noisy",
                "sources": []
            },
            {
                "success": True,
                "category": "noisy",
                "sources": [{"score": 50}],
                "ragas_metrics": {"faithfulness": 0.5, "answer_relevancy": 0.5}
            }
        ]

        analysis = analyze_category_performance(results)

        recommendations = analysis["recommendations"]
        assert len(recommendations) > 0
        # Should recommend improving noisy queries (low success rate + low faithfulness)
        assert any("noisy" in rec.lower() for rec in recommendations)
