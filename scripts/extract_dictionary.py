"""
FILE: extract_dictionary.py
STATUS: Active
RESPONSIBILITY: Extract NBA data dictionary from Excel to JSON
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Extracts the "Dictionnaire des données" sheet from Excel and saves as structured JSON.
"""

import pandas as pd
import json
import sys
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

def extract_dictionary():
    """Extract dictionary from Excel to JSON."""
    excel_path = Path(__file__).parent.parent / "data" / "inputs" / "regular NBA.xlsx"
    output_path = Path(__file__).parent.parent / "data" / "reference" / "nba_dictionary.json"

    print(f"Reading dictionary from: {excel_path}")

    # Read dictionary sheet
    df = pd.read_excel(excel_path, sheet_name="Dictionnaire des données", header=0)

    print(f"\nOriginal columns: {list(df.columns)}")
    print(f"Rows: {len(df)}")

    # Rename columns for clarity
    df.columns = ['metric', 'description']

    # Convert to dictionary
    dictionary = {}
    for idx, row in df.iterrows():
        metric = str(row['metric']).strip()
        description = str(row['description']).strip()

        # Skip empty rows
        if pd.isna(row['metric']) or pd.isna(row['description']):
            continue

        dictionary[metric] = description

    print(f"\nExtracted {len(dictionary)} dictionary entries")

    # Show sample entries
    print("\nSample entries:")
    for i, (metric, desc) in enumerate(list(dictionary.items())[:10], 1):
        print(f"  {i}. {metric}: {desc[:60]}...")

    # Save to JSON
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)

    print(f"\nDictionary saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size} bytes")

    # Also save in vector-optimized format
    vector_path = Path(__file__).parent.parent / "data" / "reference" / "nba_dictionary_vectorized.txt"

    with open(vector_path, 'w', encoding='utf-8') as f:
        f.write("NBA Statistics Glossary\n")
        f.write("=" * 80 + "\n\n")

        for metric, description in dictionary.items():
            f.write(f"METRIC: {metric}\n")
            f.write(f"Description: {description}\n")
            f.write("-" * 80 + "\n\n")

    print(f"\nVector-optimized format saved to: {vector_path}")

    return dictionary

if __name__ == "__main__":
    dictionary = extract_dictionary()

    # Print full dictionary
    print("\n" + "=" * 80)
    print("FULL DICTIONARY")
    print("=" * 80)

    for metric, description in dictionary.items():
        print(f"\n{metric}")
        print(f"  → {description}")
