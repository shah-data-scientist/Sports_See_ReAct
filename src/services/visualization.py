"""
FILE: visualization.py
STATUS: Active
RESPONSIBILITY: LLM-driven visualization generation for NBA statistics
CREATED: 2026-02-14 (Consolidated from visualization_service.py + stat_labels.py)
MAINTAINER: Shahu

This module provides:
1. Stat label mappings (from stat_labels.py)
2. Plotly chart generation functions
3. LLM suggestion parser for visualization

Architecture: LLM suggests → Script generates (Option B1)
"""

import logging
from typing import Any

import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)

# ============================================================================
# STAT LABELS (from stat_labels.py)
# ============================================================================

STAT_LABELS = {
    # Basic counting stats
    "pts": "PTS (Points)",
    "reb": "REB (Rebounds)",
    "ast": "AST (Assists)",
    "stl": "STL (Steals)",
    "blk": "BLK (Blocks)",
    "tov": "TOV (Turnovers)",
    "pf": "PF (Personal Fouls)",
    "gp": "GP (Games Played)",
    # Shooting stats
    "fgm": "FGM (Field Goals Made)",
    "fga": "FGA (Field Goals Attempted)",
    "fg_pct": "FG% (Field Goal Percentage)",
    "ftm": "FTM (Free Throws Made)",
    "fta": "FTA (Free Throws Attempted)",
    "ft_pct": "FT% (Free Throw Percentage)",
    # Three-point stats
    "3pm": "3PM (3-Pointers Made)",
    "3pa": "3PA (3-Pointers Attempted)",
    "three_pct": "3P% (3-Point Percentage)",
    "3p_pct": "3P% (3-Point Percentage)",
    "three_pm": "3PM (3-Pointers Made)",
    "three_pa": "3PA (3-Pointers Attempted)",
    # Rebound breakdown
    "oreb": "OREB (Offensive Rebounds)",
    "dreb": "DREB (Defensive Rebounds)",
    "oreb_pct": "OREB% (Offensive Rebound Percentage)",
    "dreb_pct": "DREB% (Defensive Rebound Percentage)",
    "reb_pct": "REB% (Total Rebound Percentage)",
    # Advanced stats
    "efg_pct": "eFG% (Effective Field Goal Percentage)",
    "ts_pct": "TS% (True Shooting Percentage)",
    "usg_pct": "USG% (Usage Percentage)",
    "ast_pct": "AST% (Assist Percentage)",
    "ast_to": "AST/TO (Assist-to-Turnover Ratio)",
    "to_ratio": "TO Ratio (Turnover Ratio)",
    # Ratings
    "offrtg": "OffRtg (Offensive Rating)",
    "defrtg": "DefRtg (Defensive Rating)",
    "netrtg": "NetRtg (Net Rating)",
    "off_rtg": "OffRtg (Offensive Rating)",
    "def_rtg": "DefRtg (Defensive Rating)",
    "net_rtg": "NetRtg (Net Rating)",
    # Other stats
    "fp": "FP (Fantasy Points)",
    "dd2": "DD2 (Double-Doubles)",
    "td3": "TD3 (Triple-Doubles)",
    "pie": "PIE (Player Impact Estimate)",
    "pace": "PACE (Possessions Per 48 Minutes)",
    "poss": "POSS (Possessions)",
    "ppg": "PPG (Points Per Game)",
    "rpg": "RPG (Rebounds Per Game)",
    "apg": "APG (Assists Per Game)",
    "spg": "SPG (Steals Per Game)",
    "bpg": "BPG (Blocks Per Game)",
    "mpg": "MPG (Minutes Per Game)",
    # Common variations
    "minutes": "MIN (Minutes)",
    "min": "MIN (Minutes)",
    "points": "PTS (Points)",
    "rebounds": "REB (Rebounds)",
    "assists": "AST (Assists)",
    "steals": "STL (Steals)",
    "blocks": "BLK (Blocks)",
    "turnovers": "TOV (Turnovers)",
    "fouls": "PF (Personal Fouls)",
    "games": "GP (Games Played)",
    "name": "Player/Team",
    "team": "Team",
    "player": "Player",
    "age": "Age",
}


def get_stat_label(stat_key: str) -> str:
    """Get full descriptive label for a stat abbreviation.

    Args:
        stat_key: The stat abbreviation (e.g., "pts", "reb", "ast")

    Returns:
        Full label with description (e.g., "PTS (Points)")
        If not found, returns uppercase version of key
    """
    stat_lower = stat_key.lower().strip()
    return STAT_LABELS.get(stat_lower, stat_key.upper())


# ============================================================================
# VISUALIZATION SERVICE (simplified from visualization_service.py)
# ============================================================================


class VisualizationService:
    """Generate interactive Plotly visualizations from LLM suggestions.

    LLM suggests: "[VISUALIZATION: bar_chart | name,pts | Top 5 Scorers]"
    Service generates: Plotly bar chart with proper formatting
    """

    def __init__(self):
        """Initialize visualization service."""
        self.color_scheme = px.colors.qualitative.Plotly

    def generate_chart(
        self,
        chart_type: str,
        data: list[dict[str, Any]],
        title: str = "Chart",
    ) -> dict[str, Any]:
        """Generate chart from LLM suggestion.

        Args:
            chart_type: Type of chart (bar_chart, line_chart, radar_chart, pie_chart, table)
            data: SQL query results as list of dicts
            title: Chart title

        Returns:
            Dict with:
                - chart_type: Type of chart generated
                - plotly_json: Plotly figure as JSON
                - plotly_html: Plotly figure as HTML (for UI)
                - error: Error message if generation failed
        """
        if not data:
            return {
                "chart_type": "none",
                "plotly_json": None,
                "plotly_html": None,
                "error": "No data to visualize",
            }

        try:
            # Route to appropriate generator
            generators = {
                "bar_chart": self._generate_bar_chart,
                "horizontal_bar": self._generate_horizontal_bar,
                "line_chart": self._generate_line_chart,
                "radar_chart": self._generate_radar_chart,
                "pie_chart": self._generate_pie_chart,
                "scatter": self._generate_scatter,
                "table": self._generate_table,
            }

            generator = generators.get(chart_type, self._generate_table)
            fig = generator(data, title)

            return {
                "chart_type": chart_type,
                "plotly_json": fig.to_json(),
                "plotly_html": fig.to_html(include_plotlyjs="cdn", div_id="viz"),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Chart generation failed for type '{chart_type}': {e}")
            logger.info("Falling back to table visualization")

            # FALLBACK: If chart generation fails, try table as last resort
            try:
                fig = self._generate_table(data, title)
                return {
                    "chart_type": "table",  # Changed to table (fallback)
                    "plotly_json": fig.to_json(),
                    "plotly_html": fig.to_html(include_plotlyjs="cdn", div_id="viz"),
                    "error": f"Chart type '{chart_type}' failed, showing table instead",
                }
            except Exception as table_error:
                logger.error(f"Table fallback also failed: {table_error}")
                return {
                    "chart_type": "error",
                    "plotly_json": None,
                    "plotly_html": None,
                    "error": f"All visualization attempts failed: {str(e)}",
                }

    # ========================================================================
    # CHART GENERATORS
    # ========================================================================

    def _generate_bar_chart(self, data: list[dict], title: str) -> go.Figure:
        """Generate vertical bar chart."""
        keys = list(data[0].keys())
        name_col = self._find_name_column(keys)
        value_col = self._find_value_column(keys, name_col)

        if not name_col or not value_col:
            return self._generate_table(data, title)

        names = [row[name_col] for row in data]
        values = [row.get(value_col, 0) or 0 for row in data]

        fig = go.Figure(
            go.Bar(
                x=names,
                y=values,
                marker=dict(
                    color=values,
                    colorscale="Blues",
                    showscale=False,
                ),
                text=values,
                textposition="auto",
            )
        )

        stat_label = get_stat_label(value_col)
        fig.update_layout(
            title=title,
            xaxis_title=get_stat_label(name_col),
            yaxis_title=stat_label,
            xaxis_tickangle=-45 if len(data) > 5 else 0,
            height=500,
            template="plotly_white",
        )

        return fig

    def _generate_horizontal_bar(self, data: list[dict], title: str) -> go.Figure:
        """Generate horizontal bar chart (better for rankings)."""
        keys = list(data[0].keys())
        name_col = self._find_name_column(keys)
        value_col = self._find_value_column(keys, name_col)

        if not name_col or not value_col:
            return self._generate_table(data, title)

        names = [row[name_col] for row in data]
        values = [row.get(value_col, 0) or 0 for row in data]

        fig = go.Figure(
            go.Bar(
                y=names,
                x=values,
                orientation="h",
                marker=dict(
                    color=values,
                    colorscale="Viridis",
                    showscale=True,
                ),
                text=values,
                textposition="auto",
            )
        )

        stat_label = get_stat_label(value_col)
        fig.update_layout(
            title=title,
            xaxis_title=stat_label,
            yaxis_title=get_stat_label(name_col),
            height=max(400, len(data) * 40),
            template="plotly_white",
        )

        return fig

    def _generate_line_chart(self, data: list[dict], title: str) -> go.Figure:
        """Generate line chart (for trends)."""
        keys = list(data[0].keys())
        x_col = keys[0]  # First column as X-axis
        y_col = self._find_value_column(keys, x_col)

        if not y_col:
            return self._generate_table(data, title)

        x_values = [row[x_col] for row in data]
        y_values = [row.get(y_col, 0) or 0 for row in data]

        fig = go.Figure(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers",
                marker=dict(size=8, color="blue"),
                line=dict(width=2, color="blue"),
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title=get_stat_label(x_col),
            yaxis_title=get_stat_label(y_col),
            height=500,
            template="plotly_white",
        )

        return fig

    def _generate_radar_chart(self, data: list[dict], title: str) -> go.Figure:
        """Generate radar chart for multi-stat comparison (2-4 players)."""
        if len(data) > 4:
            # Too many entities, fall back to bar chart
            return self._generate_bar_chart(data, title)

        keys = list(data[0].keys())
        name_col = self._find_name_column(keys)
        stat_cols = [k for k in keys if k != name_col and isinstance(data[0].get(k), (int, float))]

        if not name_col or not stat_cols:
            return self._generate_table(data, title)

        fig = go.Figure()
        formatted_labels = [get_stat_label(col) for col in stat_cols]

        for i, row in enumerate(data):
            name = row[name_col]
            values = [row.get(col, 0) or 0 for col in stat_cols]

            fig.add_trace(
                go.Scatterpolar(
                    r=values,
                    theta=formatted_labels,
                    fill="toself",
                    name=name,
                    marker=dict(color=self.color_scheme[i % len(self.color_scheme)]),
                )
            )

        max_val = max(
            max((row.get(col, 0) or 0) for col in stat_cols)
            for row in data
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max_val * 1.1])),
            title=title,
            showlegend=True,
            height=600,
            template="plotly_white",
        )

        return fig

    def _generate_pie_chart(self, data: list[dict], title: str) -> go.Figure:
        """Generate pie chart for composition/breakdown."""
        keys = list(data[0].keys())
        name_col = self._find_name_column(keys)
        value_col = self._find_value_column(keys, name_col)

        if not name_col or not value_col:
            return self._generate_table(data, title)

        names = [row[name_col] for row in data]
        values = [row.get(value_col, 0) or 0 for row in data]

        fig = go.Figure(
            go.Pie(
                labels=names,
                values=values,
                hole=0.3,
                textinfo="label+percent",
                marker=dict(colors=self.color_scheme),
            )
        )

        fig.update_layout(
            title=title,
            height=500,
            template="plotly_white",
        )

        return fig

    def _generate_scatter(self, data: list[dict], title: str) -> go.Figure:
        """Generate scatter plot for correlations."""
        keys = list(data[0].keys())
        name_col = self._find_name_column(keys)
        numeric_cols = [k for k in keys if k != name_col and isinstance(data[0].get(k), (int, float))]

        if len(numeric_cols) < 2:
            return self._generate_table(data, title)

        x_col, y_col = numeric_cols[0], numeric_cols[1]
        x_values = [row.get(x_col, 0) or 0 for row in data]
        y_values = [row.get(y_col, 0) or 0 for row in data]
        names = [row.get(name_col, f"Player {i+1}") for i, row in enumerate(data)]

        fig = go.Figure(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="markers",
                marker=dict(size=10, color="blue", opacity=0.6),
                text=names,
                hovertemplate=f"<b>%{{text}}</b><br>{get_stat_label(x_col)}: %{{x}}<br>{get_stat_label(y_col)}: %{{y}}<extra></extra>",
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title=get_stat_label(x_col),
            yaxis_title=get_stat_label(y_col),
            height=500,
            template="plotly_white",
        )

        return fig

    def _generate_table(self, data: list[dict], title: str) -> go.Figure:
        """Generate interactive table."""
        if not data:
            return go.Figure()

        keys = list(data[0].keys())
        header_values = [get_stat_label(k) for k in keys]
        cell_values = [[row.get(k, "") for row in data] for k in keys]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=header_values,
                        fill_color="paleturquoise",
                        align="left",
                        font=dict(size=12, color="black"),
                    ),
                    cells=dict(
                        values=cell_values,
                        fill_color="white",
                        align="left",
                        font=dict(size=11),
                    ),
                )
            ]
        )

        fig.update_layout(
            title=title,
            height=max(300, min(800, len(data) * 30 + 100)),
            template="plotly_white",
        )

        return fig

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _find_name_column(self, columns: list[str]) -> str | None:
        """Find the column likely containing names."""
        name_keywords = ["name", "player", "team", "entity", "type", "category"]
        for col in columns:
            if any(keyword in col.lower() for keyword in name_keywords):
                return col
        return None

    def _find_value_column(self, columns: list[str], exclude: str | None = None) -> str | None:
        """Find the main value column (first numeric column)."""
        for col in columns:
            if col != exclude and col.lower() not in ["id", "player_id", "team_id", "age"]:
                return col
        return None


# ============================================================================
# LLM SUGGESTION PARSER
# ============================================================================


def parse_visualization_tag(text: str) -> dict[str, Any] | None:
    """Parse LLM visualization suggestion from response.

    Expected format: [VISUALIZATION: chart_type | title]
    Examples:
        - [VISUALIZATION: bar_chart | Top 5 Scorers]
        - [VISUALIZATION: radar_chart | Player Comparison]
        - [VISUALIZATION: pie_chart | Points Distribution]

    Args:
        text: LLM response text

    Returns:
        Dict with chart_type and title, or None if no tag found
    """
    import re

    pattern = r'\[VISUALIZATION:\s*([^|]+?)\s*\|\s*([^\]]+?)\s*\]'
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    chart_type = match.group(1).strip().lower()
    title = match.group(2).strip()

    return {
        "chart_type": chart_type,
        "title": title,
    }
