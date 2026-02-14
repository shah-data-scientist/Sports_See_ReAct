"""
FILE: read_excel_properly.py
STATUS: Active
RESPONSIBILITY: Read Excel file with proper parsing to see actual data
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Read Excel sheets the way data_loader does to see what gets vectorized.
"""

import pandas as pd
import sys
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

def main():
    excel_path = Path(__file__).parent.parent / "data" / "inputs" / "regular NBA.xlsx"

    print(f"Reading: {excel_path}")
    print("=" * 80)

    excel_file = pd.ExcelFile(excel_path)

    for sheet_name in excel_file.sheet_names:
        print(f"\n{'=' * 80}")
        print(f"SHEET: {sheet_name}")
        print("=" * 80)

        # Read using excel_file.parse() like data_loader does
        df = excel_file.parse(sheet_name)

        print(f"\nRows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"\nColumn names: {list(df.columns)}")

        # Check if truly empty
        non_empty_rows = df.dropna(how='all')
        print(f"Non-empty rows: {len(non_empty_rows)}")

        # Show first few rows
        print(f"\nFirst 5 rows:")
        print(df.head(5).to_string())

        # Get some stats
        print(f"\n\nData as string (first 500 chars of df.to_string()):")
        print("-" * 80)
        text = df.to_string()
        print(f"Total length: {len(text)} chars")
        print(text[:500])

if __name__ == "__main__":
    main()
