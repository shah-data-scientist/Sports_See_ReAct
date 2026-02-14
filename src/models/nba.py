"""
FILE: nba.py
STATUS: Active
RESPONSIBILITY: Pydantic models for NBA player statistics and team data validation
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import logging
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class PlayerStats(BaseModel):
    """Complete NBA player statistics record with validation.

    Corresponds to a single row from the NBA data Excel file.
    All percentages are stored as decimals (0-100 range).
    """

    # Player identification
    player: str = Field(..., min_length=2, max_length=100, alias="Player", description="Player name")
    team: str = Field(..., min_length=2, max_length=5, alias="Team", description="Team abbreviation")
    age: int = Field(..., ge=18, le=50, alias="Age", description="Player age")

    # Games played
    gp: int = Field(..., ge=1, le=82, alias="GP", description="Games played")
    w: int = Field(..., ge=0, le=82, alias="W", description="Wins")
    l: int = Field(..., ge=0, le=82, alias="L", description="Losses")

    # Playing time
    min: Decimal = Field(..., ge=0, le=48, alias="Min", description="Minutes per game")

    # Scoring
    pts: int = Field(..., ge=0, alias="PTS", description="Total points")
    fgm: int = Field(..., ge=0, alias="FGM", description="Field goals made")
    fga: int = Field(..., ge=0, alias="FGA", description="Field goals attempted")
    fg_pct: Decimal | None = Field(default=None, ge=0, le=100, alias="FG%", description="Field goal percentage")

    # Three-pointers
    three_pm: int = Field(default=0, ge=0, alias="3PM", description="3-point shots made")
    three_pa: int = Field(default=0, ge=0, alias="3PA", description="3-point shots attempted")
    three_pct: Decimal | None = Field(default=None, ge=0, le=100, alias="3P%", description="3-point percentage")

    # Free throws
    ftm: int = Field(..., ge=0, alias="FTM", description="Free throws made")
    fta: int = Field(..., ge=0, alias="FTA", description="Free throws attempted")
    ft_pct: Decimal | None = Field(default=None, ge=0, le=100, alias="FT%", description="Free throw percentage")

    # Rebounds
    oreb: int = Field(..., ge=0, alias="OREB", description="Offensive rebounds")
    dreb: int = Field(..., ge=0, alias="DREB", description="Defensive rebounds")
    reb: int = Field(..., ge=0, alias="REB", description="Total rebounds")

    # Other stats
    ast: int = Field(..., ge=0, alias="AST", description="Assists")
    tov: int = Field(..., ge=0, alias="TOV", description="Turnovers")
    stl: int = Field(..., ge=0, alias="STL", description="Steals")
    blk: int = Field(..., ge=0, alias="BLK", description="Blocks")
    pf: int = Field(..., ge=0, alias="PF", description="Personal fouls")

    # Fantasy/performance
    fp: Decimal = Field(..., alias="FP", description="Fantasy points")
    dd2: int = Field(..., ge=0, alias="DD2", description="Double-doubles")
    td3: int = Field(..., ge=0, alias="TD3", description="Triple-doubles")
    plus_minus: Decimal = Field(..., alias="+/-", description="Plus/minus rating")

    # Advanced metrics
    off_rtg: Decimal = Field(..., alias="OFFRTG", description="Offensive rating")
    def_rtg: Decimal = Field(..., alias="DEFRTG", description="Defensive rating")
    net_rtg: Decimal = Field(..., alias="NETRTG", description="Net rating")

    ast_pct: Decimal = Field(..., alias="AST%", description="Assist percentage")
    ast_to: Decimal = Field(..., alias="AST/TO", description="Assist to turnover ratio")
    ast_ratio: Decimal = Field(..., alias="AST RATIO", description="Assist ratio")

    oreb_pct: Decimal = Field(..., alias="OREB%", description="Offensive rebound percentage")
    dreb_pct: Decimal = Field(..., alias="DREB%", description="Defensive rebound percentage")
    reb_pct: Decimal = Field(..., alias="REB%", description="Total rebound percentage")

    to_ratio: Decimal = Field(..., alias="TO RATIO", description="Turnover ratio")
    efg_pct: Decimal = Field(..., alias="EFG%", description="Effective field goal percentage")
    ts_pct: Decimal = Field(..., alias="TS%", description="True shooting percentage")
    usg_pct: Decimal = Field(..., alias="USG%", description="Usage percentage")

    pace: Decimal = Field(..., alias="PACE", description="Pace")
    pie: Decimal = Field(..., alias="PIE", description="Player impact estimate")
    poss: int = Field(..., ge=0, alias="POSS", description="Possessions")

    class Config:
        """Pydantic config."""

        populate_by_name = True  # Allow both field names and aliases
        str_strip_whitespace = True
        validate_assignment = True

    @field_validator("fg_pct", "three_pct", "ft_pct", mode="before")
    @classmethod
    def validate_percentages(cls, v):
        """Convert percentage strings to Decimal."""
        if v is None or v == "" or (isinstance(v, float) and v != v):  # NaN check
            return None
        if isinstance(v, str):
            v = v.strip().replace("%", "")
        return Decimal(str(v))

    @field_validator(
        "min", "fp", "plus_minus", "off_rtg", "def_rtg", "net_rtg",
        "ast_pct", "ast_to", "ast_ratio", "oreb_pct", "dreb_pct",
        "reb_pct", "to_ratio", "efg_pct", "ts_pct", "usg_pct",
        "pace", "pie",
        mode="before",
    )
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric strings to Decimal."""
        if v is None or v == "":
            return Decimal("0")
        if isinstance(v, str):
            v = v.strip().replace(",", "")
        return Decimal(str(v))

    @field_validator("three_pm", mode="before")
    @classmethod
    def fix_three_pm(cls, v):
        """Fix 3PM column which may appear as time format '15:00:00' or Timestamp."""
        if v is None or v == "" or (isinstance(v, float) and v != v):  # NaN check
            return 0
        # If it's a pandas Timestamp or datetime, extract hour
        if hasattr(v, "hour"):
            return int(v.hour)
        # If it's a time string, extract hour part
        if isinstance(v, str) and ":" in v:
            parts = v.split(":")
            return int(parts[0])
        return int(v)

    # ── Cross-field consistency validators ──────────────────────

    @model_validator(mode="after")
    def check_games_consistency(self):
        """Validate gp == w + l (each game is a win or loss)."""
        if self.gp != self.w + self.l:
            logger.warning(
                f"Games inconsistency for {self.player}: "
                f"GP={self.gp} != W({self.w}) + L({self.l}) = {self.w + self.l}"
            )
        return self

    @model_validator(mode="after")
    def check_rebound_consistency(self):
        """Validate reb == oreb + dreb (with tolerance of 1 for rounding)."""
        expected = self.oreb + self.dreb
        if abs(self.reb - expected) > 1:
            logger.warning(
                f"Rebound inconsistency for {self.player}: "
                f"REB={self.reb} != OREB({self.oreb}) + DREB({self.dreb}) = {expected}"
            )
        return self

    @model_validator(mode="after")
    def check_shooting_consistency(self):
        """Validate fgm <= fga, ftm <= fta, three_pm <= three_pa."""
        if self.fgm > self.fga:
            logger.warning(f"Shooting inconsistency for {self.player}: FGM({self.fgm}) > FGA({self.fga})")
        if self.ftm > self.fta:
            logger.warning(f"Free throw inconsistency for {self.player}: FTM({self.ftm}) > FTA({self.fta})")
        if self.three_pm > self.three_pa:
            logger.warning(f"3PT inconsistency for {self.player}: 3PM({self.three_pm}) > 3PA({self.three_pa})")
        return self


class Team(BaseModel):
    """NBA team information."""

    abbreviation: str = Field(..., min_length=2, max_length=5, description="Team abbreviation (e.g., 'LAL')")
    name: str = Field(..., min_length=2, max_length=100, description="Full team name (e.g., 'Los Angeles Lakers')")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Player(BaseModel):
    """NBA player basic information."""

    name: str = Field(..., min_length=2, max_length=100, description="Player full name")
    team: str = Field(..., min_length=2, max_length=5, description="Current team abbreviation")
    age: int = Field(..., ge=18, le=50, description="Player age")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True
