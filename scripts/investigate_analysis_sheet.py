"""
FILE: investigate_analysis_sheet.py
STATUS: Active
RESPONSIBILITY: Investigate "Analyse" tab content in NBA Excel file
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import pandas as pd
import sys
from pathlib import Path

def investigate_analysis_sheet():
    """Analyze the 'Analyse' sheet to determine its purpose."""

    file_path = "data/inputs/regular NBA.xlsx"

    if not Path(file_path).exists():
        print(f"ERROR: File not found: {file_path}")
        print("Please ensure the Excel file is closed and accessible.")
        return

    print("=" * 80)
    print("INVESTIGATION: 'Analyse' SHEET IN NBA EXCEL FILE")
    print("=" * 80)
    print()

    try:
        # Read the Analyse sheet
        df = pd.read_excel(file_path, sheet_name="Analyse")

        print(f"SHAPE: {df.shape[0]} rows × {df.shape[1]} columns")
        print()

        print("COLUMNS:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        print()

        print("DATA TYPES:")
        print(df.dtypes)
        print()

        print("SAMPLE DATA (first 10 rows):")
        print(df.head(10).to_string())
        print()

        print("NULL VALUE ANALYSIS:")
        null_counts = df.isnull().sum()
        print(null_counts[null_counts > 0])
        print()

        # Check if sheet is empty
        is_empty = df.empty or df.isna().all().all()

        print("=" * 80)
        print("VERDICT:")
        print("=" * 80)

        if is_empty:
            print("✅ Sheet is EMPTY or contains only NaN values")
            print()
            print("RECOMMENDATION:")
            print("  - REMOVE from vectorization pipeline")
            print("  - Add to EXCLUDED_SHEETS in data_loader.py")
        else:
            print("⚠️ Sheet contains DATA")
            print()
            print("CONTENT ANALYSIS:")

            # Try to determine content type
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            text_cols = df.select_dtypes(include=['object']).columns.tolist()

            print(f"  - Numeric columns: {len(numeric_cols)}")
            print(f"  - Text columns: {len(text_cols)}")
            print()

            if len(numeric_cols) > len(text_cols):
                print("LIKELY CONTENT TYPE: Statistical data (more numeric columns)")
                print()
                print("RECOMMENDATION:")
                print("  - ADD to SQL database (if different from main player_stats)")
                print("  - REMOVE from vectorization pipeline")
                print("  - Check if duplicate of 'Données NBA' sheet")
            else:
                print("LIKELY CONTENT TYPE: Narrative or mixed content")
                print()
                print("RECOMMENDATION:")
                print("  - KEEP in vectorization IF contains analysis/insights")
                print("  - IMPROVE chunking to extract meaningful content")
                print("  - REVIEW chunks to ensure quality")

        print()
        print("=" * 80)

    except PermissionError:
        print("ERROR: File is locked (likely open in Excel)")
        print("Please close the Excel file and try again.")
        sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    investigate_analysis_sheet()
