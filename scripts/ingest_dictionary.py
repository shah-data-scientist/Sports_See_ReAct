"""
FILE: ingest_dictionary.py
STATUS: Active
RESPONSIBILITY: Populate data_dictionary table from Excel "Dictionnaire des données" sheet
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.nba_database import (
    DataDictionaryModel,
    NBADatabase,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Excel abbreviation → (English full name, SQL column name, table name)
# column_name is None for metadata fields not in player_stats
ABBREVIATION_MAP: dict[str, tuple[str, str | None, str | None]] = {
    "Player":    ("Player Name",               "name",        "players"),
    "Team":      ("Team Abbreviation",         "team_abbr",   "players"),
    "Age":       ("Player Age",                "age",         "players"),
    "GP":        ("Games Played",              "gp",          "player_stats"),
    "W":         ("Wins",                      "w",           "player_stats"),
    "L":         ("Losses",                    "l",           "player_stats"),
    "Min":       ("Minutes Per Game",          "min",         "player_stats"),
    "PTS":       ("Points",                    "pts",         "player_stats"),
    "FGM":       ("Field Goals Made",          "fgm",         "player_stats"),
    "FGA":       ("Field Goals Attempted",     "fga",         "player_stats"),
    "FG%":       ("Field Goal Percentage",     "fg_pct",      "player_stats"),
    "3PM":       ("3-Point Shots Made",        "three_pm",    "player_stats"),
    "3PA":       ("3-Point Shots Attempted",   "three_pa",    "player_stats"),
    "3P%":       ("3-Point Percentage",        "three_pct",   "player_stats"),
    "FTM":       ("Free Throws Made",          "ftm",         "player_stats"),
    "FTA":       ("Free Throws Attempted",     "fta",         "player_stats"),
    "FT%":       ("Free Throw Percentage",     "ft_pct",      "player_stats"),
    "OREB":      ("Offensive Rebounds",        "oreb",        "player_stats"),
    "DREB":      ("Defensive Rebounds",        "dreb",        "player_stats"),
    "REB":       ("Total Rebounds",            "reb",         "player_stats"),
    "AST":       ("Assists",                   "ast",         "player_stats"),
    "TOV":       ("Turnovers",                 "tov",         "player_stats"),
    "STL":       ("Steals",                    "stl",         "player_stats"),
    "BLK":       ("Blocks",                    "blk",         "player_stats"),
    "PF":        ("Personal Fouls",            "pf",          "player_stats"),
    "FP":        ("Fantasy Points",            "fp",          "player_stats"),
    "DD2":       ("Double-Doubles",            "dd2",         "player_stats"),
    "TD3":       ("Triple-Doubles",            "td3",         "player_stats"),
    "+ / -":     ("Plus-Minus",                "plus_minus",  "player_stats"),
    "OFFRTG":    ("Offensive Rating",          "off_rtg",     "player_stats"),
    "DEFRTG":    ("Defensive Rating",          "def_rtg",     "player_stats"),
    "NETRTG":    ("Net Rating",                "net_rtg",     "player_stats"),
    "AST%":      ("Assist Percentage",         "ast_pct",     "player_stats"),
    "AST/TO":    ("Assist-to-Turnover Ratio",  "ast_to",      "player_stats"),
    "AST RATIO": ("Assist Ratio",              "ast_ratio",   "player_stats"),
    "OREB%":     ("Offensive Rebound %",       "oreb_pct",    "player_stats"),
    "DREB%":     ("Defensive Rebound %",       "dreb_pct",    "player_stats"),
    "REB%":      ("Total Rebound %",           "reb_pct",     "player_stats"),
    "TO RATIO":  ("Turnover Ratio",            "to_ratio",    "player_stats"),
    "EFG%":      ("Effective Field Goal %",    "efg_pct",     "player_stats"),
    "TS%":       ("True Shooting %",           "ts_pct",      "player_stats"),
    "USG%":      ("Usage Rate",                "usg_pct",     "player_stats"),
    "PACE":      ("Pace",                      "pace",        "player_stats"),
    "PIE":       ("Player Impact Estimate",    "pie",         "player_stats"),
    "POSS":      ("Possessions",               "poss",        "player_stats"),
}

# The Excel "15:00:00" is a parsing artifact for "3PM" (Excel interpreted "3PM" as a time)
# We map it to 3PM
EXCEL_FIXES = {
    "15:00:00": "3PM",
}


def ingest_dictionary(db_path: str | None = None, excel_path: str | None = None) -> int:
    """Populate data_dictionary table from Excel sheet.

    Args:
        db_path: Path to SQLite database (default: data/sql/nba_stats.db)
        excel_path: Path to NBA Excel file (default: data/inputs/regular NBA.xlsx)

    Returns:
        Number of entries inserted
    """
    import pandas as pd

    if excel_path is None:
        excel_path = str(Path(__file__).parent.parent / "data" / "inputs" / "regular NBA.xlsx")

    # Read dictionary sheet
    logger.info(f"Reading dictionary from: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name="Dictionnaire des données")

    # Column names from Excel: "Dictionnaire des données" (abbreviation) and "Unnamed: 1" (description)
    df.columns = ["abbreviation", "description"]

    # Apply fixes for Excel parsing artifacts
    df["abbreviation"] = df["abbreviation"].astype(str).apply(
        lambda x: EXCEL_FIXES.get(x, x)
    )

    logger.info(f"Found {len(df)} entries in dictionary sheet")

    # Initialize database
    db = NBADatabase(db_path)
    db.create_tables()  # Ensures data_dictionary table exists

    session = db.get_session()
    count = 0

    try:
        # Clear existing entries
        session.query(DataDictionaryModel).delete()

        for _, row in df.iterrows():
            abbr = str(row["abbreviation"]).strip()
            desc = str(row["description"]).strip()

            if abbr in ABBREVIATION_MAP:
                full_name, column_name, table_name = ABBREVIATION_MAP[abbr]
            else:
                logger.warning(f"Unknown abbreviation: '{abbr}' - storing without column mapping")
                full_name = abbr
                column_name = None
                table_name = None

            entry = DataDictionaryModel(
                abbreviation=abbr,
                full_name=full_name,
                description=desc,
                column_name=column_name,
                table_name=table_name,
            )
            session.add(entry)
            count += 1

        session.commit()
        logger.info(f"Inserted {count} dictionary entries")

        # Verify
        total = session.query(DataDictionaryModel).count()
        mapped = session.query(DataDictionaryModel).filter(
            DataDictionaryModel.column_name.isnot(None)
        ).count()
        logger.info(f"Verification: {total} total entries, {mapped} mapped to SQL columns")

    except Exception as e:
        session.rollback()
        logger.error(f"Error ingesting dictionary: {e}")
        raise
    finally:
        session.close()
        db.close()

    return count


def main():
    """Run dictionary ingestion."""
    sys.stdout.reconfigure(encoding="utf-8")
    count = ingest_dictionary()
    print(f"\nDone! Inserted {count} dictionary entries into data_dictionary table.")


if __name__ == "__main__":
    main()
