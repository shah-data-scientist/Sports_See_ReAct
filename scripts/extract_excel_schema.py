"""
FILE: extract_excel_schema.py
STATUS: Active
RESPONSIBILITY: Extract Excel schema to JSON for Phase 2 database design
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import json
from pathlib import Path

import pandas as pd


def extract_schema(file_path: str) -> dict:
    """Extract schema information from Excel file."""
    xls = pd.ExcelFile(file_path)
    schema = {
        "file": file_path,
        "sheets": {},
    }

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)

        # Get column info
        columns_info = []
        for col in df.columns:
            if df[col].notna().any():  # Only non-empty columns
                columns_info.append({
                    "name": str(col),
                    "dtype": str(df[col].dtype),
                    "non_null_count": int(df[col].notna().sum()),
                    "total_count": len(df),
                    "unique_count": int(df[col].nunique()),
                    "sample_values": [str(v) for v in df[col].dropna().head(3).tolist()],
                })

        schema["sheets"][sheet_name] = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "non_empty_columns": len(columns_info),
            "columns_info": columns_info,
        }

    return schema


if __name__ == "__main__":
    file_path = "data/inputs/regular NBA.xlsx"
    output_path = "excel_schema.json"

    print(f"Extracting schema from: {file_path}")
    schema = extract_schema(file_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"Schema saved to: {output_path}")
    print(f"\nSheets found: {list(schema['sheets'].keys())}")
    for sheet_name, info in schema["sheets"].items():
        print(f"  - {sheet_name}: {info['rows']} rows, "
              f"{info['non_empty_columns']} non-empty columns")
