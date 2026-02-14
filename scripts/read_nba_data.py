"""
FILE: read_nba_data.py
STATUS: Active
RESPONSIBILITY: Read NBA Excel data with proper headers for Phase 2 schema design
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import json
from pathlib import Path

import pandas as pd


def read_nba_data():
    """Read NBA Excel data and extract schema."""
    file_path = "data/inputs/regular NBA.xlsx"

    # Read data - first row is headers
    df = pd.read_excel(file_path, sheet_name="Données NBA")

    # First row contains actual column names
    headers = df.iloc[0].tolist()

    # Drop first row and use it as header
    df.columns = headers
    df = df.drop(0).reset_index(drop=True)

    # Remove empty columns
    df = df.loc[:, df.columns.notna()]

    print(f"Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns\n")
    print(f"Columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")

    print(f"\n\nSample data (first 3 rows):")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.head(3))

    # Save to CSV for easier inspection
    output_path = "nba_data_sample.csv"
    df.head(20).to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n\nSample saved to: {output_path}")

    # Save column info
    column_info = []
    for col in df.columns:
        # Try to infer better dtype
        sample_vals = df[col].dropna().head(5).tolist()
        column_info.append({
            "name": col,
            "pandas_dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "unique_count": int(df[col].nunique()),
            "sample_values": [str(v) for v in sample_vals],
        })

    schema = {
        "file": file_path,
        "sheet": "Données NBA",
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_info": column_info,
    }

    schema_path = "nba_data_schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"Schema saved to: {schema_path}")

    return df


if __name__ == "__main__":
    df = read_nba_data()
