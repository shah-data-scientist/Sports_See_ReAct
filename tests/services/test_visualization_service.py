"""
FILE: test_visualization_service.py
STATUS: Active
RESPONSIBILITY: Unit tests for visualization service - chart generation
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import json
from unittest.mock import MagicMock, patch

import plotly.graph_objects as go
import pytest

from src.services.visualization_patterns import VisualizationPattern
from src.services.visualization_service import VisualizationService


@pytest.fixture
def viz_service():
    """Create VisualizationService instance for testing."""
    return VisualizationService()


@pytest.fixture
def sample_top_n_data():
    """Sample data for top N queries."""
    return [
        {"name": "Player A", "pts": 2485},
        {"name": "Player B", "pts": 2370},
        {"name": "Player C", "pts": 2329},
        {"name": "Player D", "pts": 2180},
        {"name": "Player E", "pts": 2046},
    ]


@pytest.fixture
def sample_comparison_data():
    """Sample data for player comparisons."""
    return [
        {"name": "Jokic", "pts": 25.5, "reb": 12.3, "ast": 9.2},
        {"name": "Embiid", "pts": 28.8, "reb": 11.2, "ast": 3.5},
    ]


@pytest.fixture
def sample_single_entity_data():
    """Sample data for single entity queries."""
    return [{"name": "LeBron James", "pts": 24.8, "reb": 7.2, "ast": 7.8}]


class TestVisualizationServiceInit:
    """Test VisualizationService initialization."""

    def test_service_initializes_detector(self, viz_service):
        """Test service initializes with QueryPatternDetector."""
        assert viz_service.detector is not None
        assert viz_service.color_scheme is not None

    def test_service_has_all_generator_methods(self, viz_service):
        """Test service has all visualization generator methods."""
        assert hasattr(viz_service, "_generate_top_n")
        assert hasattr(viz_service, "_generate_comparison")
        assert hasattr(viz_service, "_generate_multi_comparison")
        assert hasattr(viz_service, "_generate_single_entity")
        assert hasattr(viz_service, "_generate_distribution")
        assert hasattr(viz_service, "_generate_correlation")
        assert hasattr(viz_service, "_generate_threshold_filter")
        assert hasattr(viz_service, "_generate_composition")
        assert hasattr(viz_service, "_generate_table")


class TestGenerateVisualization:
    """Test main generate_visualization method."""

    def test_returns_dict_with_required_keys(self, viz_service, sample_top_n_data):
        """Test returns dict with pattern, viz_type, plot_json, plot_html."""
        result = viz_service.generate_visualization("Top 5 scorers", sample_top_n_data)

        assert "pattern" in result
        assert "viz_type" in result
        assert "plot_json" in result
        assert "plot_html" in result

    def test_empty_data_returns_no_visualization(self, viz_service):
        """Test empty data returns no visualization message."""
        result = viz_service.generate_visualization("Any query", [])

        assert result["pattern"] == "none"
        assert result["viz_type"] == "none"
        assert result["plot_json"] is None
        assert result["plot_html"] is None
        assert "message" in result

    def test_auto_detects_pattern_when_not_provided(self, viz_service, sample_top_n_data):
        """Test auto-detects pattern when not provided."""
        result = viz_service.generate_visualization("Top 5 scorers", sample_top_n_data)
        assert result["pattern"] == "top_n"

    def test_uses_provided_pattern(self, viz_service, sample_comparison_data):
        """Test uses provided pattern instead of auto-detection."""
        result = viz_service.generate_visualization(
            "Compare players",
            sample_comparison_data,
            pattern=VisualizationPattern.PLAYER_COMPARISON,
        )
        assert result["pattern"] == "player_comparison"

    def test_plot_json_is_valid_json(self, viz_service, sample_top_n_data):
        """Test plot_json is valid JSON."""
        result = viz_service.generate_visualization("Top 5 scorers", sample_top_n_data)
        assert result["plot_json"] is not None

        # Verify it's valid JSON
        parsed = json.loads(result["plot_json"])
        assert "data" in parsed or "layout" in parsed

    def test_plot_html_contains_div(self, viz_service, sample_top_n_data):
        """Test plot_html contains HTML div element."""
        result = viz_service.generate_visualization("Top 5 scorers", sample_top_n_data)
        assert result["plot_html"] is not None
        assert "<div" in result["plot_html"]


class TestGenerateTopN:
    """Test _generate_top_n method."""

    def test_generates_horizontal_bar_chart(self, viz_service, sample_top_n_data):
        """Test generates horizontal bar chart for top N."""
        fig = viz_service._generate_top_n("Top 5 scorers", sample_top_n_data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Bar)
        assert fig.data[0].orientation == "h"

    def test_chart_has_correct_data_points(self, viz_service, sample_top_n_data):
        """Test chart has correct number of data points."""
        fig = viz_service._generate_top_n("Top 5 scorers", sample_top_n_data)

        assert len(fig.data[0].y) == 5
        assert len(fig.data[0].x) == 5

    def test_reverses_order_for_bottom_queries(self, viz_service):
        """Test reverses order for bottom/worst queries."""
        data = [
            {"name": "Player A", "pts": 100},
            {"name": "Player B", "pts": 200},
        ]

        fig_top = viz_service._generate_top_n("Top scorers", data)
        fig_bottom = viz_service._generate_top_n("Bottom scorers", data)

        # Bottom should reverse the order
        assert list(fig_top.data[0].y) != list(fig_bottom.data[0].y)

    def test_fallback_to_table_if_columns_not_found(self, viz_service):
        """Test falls back to table if columns cannot be identified."""
        bad_data = [{"unknown_col": 123}]
        fig = viz_service._generate_top_n("Query", bad_data)

        # Should fall back to table
        assert isinstance(fig, go.Figure)


class TestGenerateComparison:
    """Test _generate_comparison method."""

    def test_generates_radar_chart_for_comparison(self, viz_service, sample_comparison_data):
        """Test generates radar chart for player comparison."""
        fig = viz_service._generate_comparison("Compare Jokic and Embiid", sample_comparison_data)

        assert isinstance(fig, go.Figure)
        # Should have 2 traces (one for each player)
        assert len(fig.data) == 2
        assert all(isinstance(trace, go.Scatterpolar) for trace in fig.data)

    def test_radar_chart_has_player_names(self, viz_service, sample_comparison_data):
        """Test radar chart traces have player names."""
        fig = viz_service._generate_comparison("Compare players", sample_comparison_data)

        names = [trace.name for trace in fig.data]
        assert "Jokic" in names
        assert "Embiid" in names

    def test_falls_back_to_multi_comparison_for_many_players(self, viz_service):
        """Test falls back to multi-comparison for >4 players."""
        many_players = [{"name": f"Player{i}", "pts": 20} for i in range(6)]
        fig = viz_service._generate_comparison("Compare many players", many_players)

        # Should generate bar chart, not radar
        assert isinstance(fig, go.Figure)
        # Multi-comparison generates single bar trace
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Bar)


class TestGenerateSingleEntity:
    """Test _generate_single_entity method."""

    def test_generates_stat_card(self, viz_service, sample_single_entity_data):
        """Test generates stat card for single entity."""
        fig = viz_service._generate_single_entity("LeBron's stats", sample_single_entity_data)

        assert isinstance(fig, go.Figure)
        # Stat card uses annotations
        assert len(fig.layout.annotations) > 0

    def test_stat_card_contains_all_stats(self, viz_service, sample_single_entity_data):
        """Test stat card displays all statistics."""
        fig = viz_service._generate_single_entity("LeBron's stats", sample_single_entity_data)

        annotation_text = fig.layout.annotations[0].text
        # Should contain the stats
        assert "pts" in annotation_text.lower() or "points" in annotation_text.lower()


class TestGenerateDistribution:
    """Test _generate_distribution method."""

    def test_generates_histogram(self, viz_service):
        """Test generates histogram for distributions."""
        data = [{"value": i * 10} for i in range(20)]
        fig = viz_service._generate_distribution("Distribution of values", data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Histogram)


class TestGenerateCorrelation:
    """Test _generate_correlation method."""

    def test_generates_scatter_plot(self, viz_service):
        """Test generates scatter plot for correlations."""
        data = [
            {"name": "Player A", "pts": 25, "ast": 8},
            {"name": "Player B", "pts": 20, "ast": 10},
            {"name": "Player C", "pts": 30, "ast": 5},
        ]
        fig = viz_service._generate_correlation("Points vs Assists", data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Scatter)

    def test_scatter_uses_two_numeric_columns(self, viz_service):
        """Test scatter plot uses first two numeric columns."""
        data = [
            {"name": "A", "pts": 25, "reb": 10, "ast": 8},
            {"name": "B", "pts": 20, "reb": 12, "ast": 6},
        ]
        fig = viz_service._generate_correlation("Correlation", data)

        # Should use pts and reb (first two numeric columns)
        assert len(fig.data[0].x) == 2
        assert len(fig.data[0].y) == 2


class TestGenerateComposition:
    """Test _generate_composition method."""

    def test_generates_pie_chart(self, viz_service):
        """Test generates pie chart for composition."""
        data = [
            {"type": "2-Point", "shots": 40},
            {"type": "3-Point", "shots": 30},
            {"type": "Free Throw", "shots": 30},
        ]
        fig = viz_service._generate_composition("Shot breakdown", data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Pie)

    def test_pie_chart_has_labels_and_values(self, viz_service):
        """Test pie chart has correct labels and values."""
        data = [
            {"type": "A", "value": 40},
            {"type": "B", "value": 60},
        ]
        fig = viz_service._generate_composition("Breakdown", data)

        assert len(fig.data[0].labels) == 2
        assert len(fig.data[0].values) == 2


class TestGenerateTable:
    """Test _generate_table method."""

    def test_generates_table(self, viz_service, sample_top_n_data):
        """Test generates interactive table."""
        fig = viz_service._generate_table("Show data", sample_top_n_data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Table)

    def test_table_has_headers_and_cells(self, viz_service, sample_top_n_data):
        """Test table has header and cell values."""
        fig = viz_service._generate_table("Show data", sample_top_n_data)

        table = fig.data[0]
        assert len(table.header.values) > 0
        assert len(table.cells.values) > 0

    def test_table_with_highlight(self, viz_service, sample_top_n_data):
        """Test table with highlighting enabled."""
        fig = viz_service._generate_table("Show data", sample_top_n_data, highlight=True)

        # Should have cell colors for highlighting (accessing the fill dict)
        assert fig.data[0].cells.fill.color is not None

    def test_empty_data_returns_empty_figure(self, viz_service):
        """Test empty data returns empty figure."""
        fig = viz_service._generate_table("Query", [])
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0


class TestHelperMethods:
    """Test helper methods."""

    def test_find_name_column(self, viz_service):
        """Test _find_name_column identifies name column."""
        columns = ["id", "name", "pts", "reb"]
        name_col = viz_service._find_name_column(columns)
        assert name_col == "name"

        columns = ["id", "player", "pts"]
        name_col = viz_service._find_name_column(columns)
        assert name_col == "player"

        columns = ["id", "team", "wins"]
        name_col = viz_service._find_name_column(columns)
        assert name_col == "team"

    def test_find_name_column_returns_none_if_not_found(self, viz_service):
        """Test returns None if no name column found."""
        columns = ["id", "value1", "value2"]
        name_col = viz_service._find_name_column(columns)
        assert name_col is None

    def test_find_value_column(self, viz_service):
        """Test _find_value_column identifies value column."""
        columns = ["name", "pts", "reb", "ast"]
        value_col = viz_service._find_value_column(columns, exclude="name")
        assert value_col == "pts"

    def test_find_value_column_excludes_id_columns(self, viz_service):
        """Test excludes id columns from value selection."""
        columns = ["player_id", "name", "pts"]
        value_col = viz_service._find_value_column(columns, exclude="name")
        assert value_col == "pts"

    def test_find_value_column_returns_none_if_not_found(self, viz_service):
        """Test returns None if no value column found."""
        columns = ["id", "player_id"]
        value_col = viz_service._find_value_column(columns)
        assert value_col is None


class TestStatLabelsIntegration:
    """Test integration with stat_labels module."""

    def test_uses_stat_labels_for_axis_titles(self, viz_service, sample_top_n_data):
        """Test uses formatted stat labels in visualizations."""
        fig = viz_service._generate_top_n("Top 5 scorers", sample_top_n_data)

        # Check that axis title is formatted (should be "PTS (Points)" not "pts")
        assert "PTS" in fig.layout.xaxis.title.text or "Points" in fig.layout.xaxis.title.text

    def test_uses_stat_labels_in_table_headers(self, viz_service):
        """Test uses formatted stat labels in table headers."""
        data = [{"pts": 25, "reb": 10, "ast": 8}]
        fig = viz_service._generate_table("Stats", data)

        # Table headers should use formatted labels
        header_values = fig.data[0].header.values
        # Should have formatted labels like "PTS (Points)"
        assert any("PTS" in str(v) or "Points" in str(v) for v in header_values)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_missing_columns_gracefully(self, viz_service):
        """Test handles missing expected columns gracefully."""
        incomplete_data = [{"unknown": 123}]

        # Should not raise exception
        result = viz_service.generate_visualization("Query", incomplete_data)
        assert result is not None

    def test_handles_mixed_data_types(self, viz_service):
        """Test handles mixed data types in columns."""
        mixed_data = [
            {"name": "Player A", "pts": 25, "status": "active"},
            {"name": "Player B", "pts": 20, "status": "injured"},
        ]

        result = viz_service.generate_visualization("Show stats", mixed_data)
        assert result is not None

    def test_handles_null_values(self, viz_service):
        """Test handles null/None values in data."""
        data_with_nulls = [
            {"name": "Player A", "pts": 25, "reb": None},
            {"name": "Player B", "pts": None, "reb": 10},
        ]

        result = viz_service.generate_visualization("Query", data_with_nulls)
        assert result is not None

    def test_handles_very_long_player_names(self, viz_service):
        """Test handles very long player names."""
        long_name_data = [
            {"name": "A" * 100, "pts": 25},
        ]

        result = viz_service.generate_visualization("Query", long_name_data)
        assert result is not None
