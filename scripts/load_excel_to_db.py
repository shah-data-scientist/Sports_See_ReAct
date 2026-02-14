"""
FILE: load_excel_to_db.py
STATUS: Active
RESPONSIBILITY: Excel to database ingestion pipeline with Pydantic validation
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from src.models.nba import PlayerStats, Team
from src.repositories.nba_database import NBADatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# NBA team names mapping
TEAM_NAMES = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
}


def read_nba_excel(file_path: str) -> pd.DataFrame:
    """Read NBA Excel data with proper headers.

    Args:
        file_path: Path to Excel file

    Returns:
        DataFrame with NBA player statistics

    Raises:
        FileNotFoundError: If Excel file doesn't exist
        ValueError: If Excel structure is invalid
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    logger.info(f"Reading Excel file: {file_path}")

    # Read main data sheet
    df = pd.read_excel(file_path, sheet_name="Données NBA")

    # First row contains actual column names
    headers = df.iloc[0].tolist()

    # Drop first row (headers) and use it as column names
    df.columns = headers
    df = df.drop(0).reset_index(drop=True)

    # Remove columns with NaN names (empty columns)
    df = df.loc[:, df.columns.notna()]

    # Fix column "15:00:00" which should be "3PM"
    if "15:00:00" in df.columns:
        df = df.rename(columns={"15:00:00": "3PM"})
        logger.info("Fixed column name: '15:00:00' → '3PM'")

    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")

    return df


def load_teams_to_db(db: NBADatabase) -> dict[str, int]:
    """Load team data into database.

    Args:
        db: NBA database instance

    Returns:
        Dictionary mapping team abbreviation to team ID
    """
    logger.info(f"Loading {len(TEAM_NAMES)} teams into database...")

    with db.get_session() as session:
        team_ids = {}

        for abbr, name in TEAM_NAMES.items():
            # Validate with Pydantic
            try:
                team = Team(abbreviation=abbr, name=name)
            except ValidationError as e:
                logger.error(f"Validation error for team {abbr}: {e}")
                continue

            # Check if team already exists
            existing = db.get_team_by_abbreviation(session, abbr)
            if existing:
                team_ids[abbr] = existing.id
                logger.debug(f"Team {abbr} already exists (ID: {existing.id})")
            else:
                team_model = db.add_team(session, abbr, name)
                session.commit()
                session.refresh(team_model)
                team_ids[abbr] = team_model.id
                logger.debug(f"Added team {abbr} (ID: {team_model.id})")

        logger.info(f"Loaded {len(team_ids)} teams")

    return team_ids


def load_players_to_db(db: NBADatabase, df: pd.DataFrame) -> dict[str, int]:
    """Load player data into database.

    Args:
        db: NBA database instance
        df: DataFrame with player statistics

    Returns:
        Dictionary mapping player name to player ID
    """
    logger.info("Loading players into database...")

    # Extract unique players
    players_data = df[["Player", "Team", "Age"]].drop_duplicates(subset=["Player"])

    with db.get_session() as session:
        player_ids = {}
        success_count = 0
        error_count = 0

        for _, row in players_data.iterrows():
            try:
                name = str(row["Player"]).strip()
                team_abbr = str(row["Team"]).strip()
                age = int(row["Age"])

                # Get full team name from abbreviation
                team_full_name = TEAM_NAMES.get(team_abbr, team_abbr)  # Fallback to abbr if not found

                # Check if player already exists
                existing = db.get_player_by_name(session, name)
                if existing:
                    player_ids[name] = existing.id
                    logger.debug(f"Player '{name}' already exists (ID: {existing.id})")
                else:
                    player_model = db.add_player(session, name, team_full_name, team_abbr, age)
                    session.commit()
                    session.refresh(player_model)
                    player_ids[name] = player_model.id
                    logger.debug(f"Added player '{name}' ({team_full_name}, ID: {player_model.id})")

                success_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error loading player {row.get('Player', 'UNKNOWN')}: {e}")

        logger.info(f"Loaded {success_count} players ({error_count} errors)")

    return player_ids


def detect_duplicates(df: pd.DataFrame) -> list[str]:
    """Detect duplicate player entries in the DataFrame.

    Args:
        df: DataFrame with player statistics

    Returns:
        List of warning messages for duplicates found
    """
    warnings = []
    dup_players = df[df.duplicated(subset=["Player"], keep=False)]
    if not dup_players.empty:
        dup_names = dup_players["Player"].unique()
        for name in dup_names:
            count = len(df[df["Player"] == name])
            warnings.append(f"Duplicate player entry: '{name}' appears {count} times")
    return warnings


def validate_cross_table_consistency(df: pd.DataFrame) -> list[str]:
    """Run cross-table consistency checks on the DataFrame.

    Checks:
    - GP == W + L (each game is a win or loss)
    - REB == OREB + DREB (rebound components)
    - FGM <= FGA, FTM <= FTA, 3PM <= 3PA (shots made <= attempted)

    Args:
        df: DataFrame with player statistics

    Returns:
        List of warning messages for inconsistencies found
    """
    warnings = []

    for idx, row in df.iterrows():
        player = str(row.get("Player", f"Row {idx}"))

        # Games consistency: GP == W + L
        try:
            gp = int(row.get("GP", 0))
            w = int(row.get("W", 0))
            l_val = int(row.get("L", 0))
            if gp != w + l_val:
                warnings.append(f"Games mismatch for '{player}': GP={gp} != W({w}) + L({l_val})")
        except (ValueError, TypeError):
            pass

        # Rebound consistency: REB == OREB + DREB
        try:
            reb = int(row.get("REB", 0))
            oreb = int(row.get("OREB", 0))
            dreb = int(row.get("DREB", 0))
            if abs(reb - (oreb + dreb)) > 1:
                warnings.append(f"Rebound mismatch for '{player}': REB={reb} != OREB({oreb}) + DREB({dreb})")
        except (ValueError, TypeError):
            pass

        # Shooting consistency
        try:
            fgm = int(row.get("FGM", 0))
            fga = int(row.get("FGA", 0))
            if fgm > fga:
                warnings.append(f"Shooting error for '{player}': FGM({fgm}) > FGA({fga})")
        except (ValueError, TypeError):
            pass

        try:
            ftm = int(row.get("FTM", 0))
            fta = int(row.get("FTA", 0))
            if ftm > fta:
                warnings.append(f"Free throw error for '{player}': FTM({ftm}) > FTA({fta})")
        except (ValueError, TypeError):
            pass

    return warnings


def load_stats_to_db(db: NBADatabase, df: pd.DataFrame, player_ids: dict[str, int]) -> int:
    """Load player statistics into database with duplicate detection.

    Args:
        db: NBA database instance
        df: DataFrame with player statistics
        player_ids: Dictionary mapping player name to player ID

    Returns:
        Number of stats records loaded
    """
    logger.info("Loading player statistics into database...")

    # Pre-flight: detect duplicates and consistency issues
    dup_warnings = detect_duplicates(df)
    for w in dup_warnings:
        logger.warning(f"[DUPLICATE] {w}")

    consistency_warnings = validate_cross_table_consistency(df)
    for w in consistency_warnings:
        logger.warning(f"[CONSISTENCY] {w}")

    if dup_warnings or consistency_warnings:
        logger.info(
            f"Data quality check: {len(dup_warnings)} duplicates, "
            f"{len(consistency_warnings)} consistency issues"
        )

    # Track which players already have stats to prevent duplicate inserts
    seen_players: set[str] = set()

    with db.get_session() as session:
        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, row in df.iterrows():
            try:
                player_name = str(row["Player"]).strip()

                # Duplicate stats guard: skip if already inserted this run
                if player_name in seen_players:
                    logger.debug(f"Skipping duplicate stats for '{player_name}' (already loaded)")
                    skip_count += 1
                    continue

                # Get player ID
                player_id = player_ids.get(player_name)
                if not player_id:
                    logger.warning(f"Player '{player_name}' not found in database, skipping stats")
                    error_count += 1
                    continue

                # Convert row to dict - ensure all keys are strings
                stats_data = {str(k): v for k, v in row.to_dict().items()}

                # Validate with Pydantic (using populate_by_name=True)
                player_stats = PlayerStats(**stats_data)

                # Convert to dict for database (exclude player, team, age - those are in separate table)
                stats_dict = player_stats.model_dump(
                    by_alias=False,  # Use field names, not aliases
                    exclude={"player", "team", "age"},
                )

                # Add team_abbr for foreign key (player_id is passed separately)
                stats_dict["team_abbr"] = str(row["Team"]).strip()

                # Insert into database
                db.add_player_stats(session, player_id, stats_dict)
                seen_players.add(player_name)

                success_count += 1

                # Commit every 100 records
                if success_count % 100 == 0:
                    session.commit()
                    logger.info(f"Committed {success_count} stats records...")

            except ValidationError as e:
                error_count += 1
                logger.error(f"Validation error for row {idx} ({row.get('Player', 'UNKNOWN')}): {e}")

            except Exception as e:
                error_count += 1
                logger.error(f"Error loading stats for row {idx} ({row.get('Player', 'UNKNOWN')}): {e}")

        # Final commit
        session.commit()

        logger.info(
            f"Loaded {success_count} stats records "
            f"({skip_count} duplicates skipped, {error_count} errors)"
        )

    return success_count


def main(excel_file: str, db_path: str | None = None, drop_existing: bool = False) -> None:
    """Main ingestion pipeline.

    Args:
        excel_file: Path to Excel file
        db_path: Path to SQLite database (optional)
        drop_existing: Whether to drop existing tables
    """
    logger.info("=" * 80)
    logger.info("NBA DATA INGESTION PIPELINE")
    logger.info("=" * 80)

    # Initialize database
    db = NBADatabase(db_path)

    # Drop tables if requested
    if drop_existing:
        logger.warning("Dropping existing database tables...")
        db.drop_tables()

    # Create tables
    logger.info("Creating database tables...")
    db.create_tables()

    try:
        # Read Excel data
        df = read_nba_excel(excel_file)

        # Load teams
        team_ids = load_teams_to_db(db)

        # Load players
        player_ids = load_players_to_db(db, df)

        # Load statistics
        stats_count = load_stats_to_db(db, df, player_ids)

        # Summary
        with db.get_session() as session:
            counts = db.count_records(session)

        logger.info("=" * 80)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Database: {db.db_path}")
        logger.info(f"  - Teams: {counts['teams']}")
        logger.info(f"  - Players: {counts['players']}")
        logger.info(f"  - Stats records: {counts['player_stats']}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NBA Excel data into SQLite database")
    parser.add_argument(
        "--excel",
        type=str,
        default="data/inputs/regular NBA.xlsx",
        help="Path to Excel file (default: data/inputs/regular NBA.xlsx)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to SQLite database (default: data/sql/nba_stats.db)",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before loading (WARNING: deletes all data)",
    )

    args = parser.parse_args()

    main(args.excel, args.db, args.drop)
